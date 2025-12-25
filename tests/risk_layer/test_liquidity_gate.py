"""
Tests for Liquidity Gate

Verifies:
- Disabled → OK
- Missing metrics → OK (or WARN if require_micro_metrics)
- Spread thresholds (WARN/BLOCK)
- Slippage thresholds (WARN/BLOCK)
- Depth requirements
- Order to ADV limits
- Market vs Limit order strictness
- Limit order exception for wide spreads
- Multiple triggers
"""

import pytest
from src.risk_layer.liquidity_gate import (
    LiquidityGate,
    LiquidityGateConfig,
    LiquiditySeverity,
    liquidity_gate_status_to_dict,
)


class TestLiquidityGateDisabled:
    """Test disabled gate behavior."""

    def test_disabled_always_ok(self):
        """Test that disabled gate always returns OK."""
        config = LiquidityGateConfig(enabled=False)
        gate = LiquidityGate(config)

        order = {"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"}
        context = {"micro": {"spread_pct": 0.99}}  # Extremely wide spread

        status = gate.evaluate(order, context)
        assert not status.enabled
        assert status.severity == LiquiditySeverity.OK
        assert status.reason == "Liquidity gate disabled"
        assert status.triggered_by == []


class TestLiquidityGateMissingMetrics:
    """Test behavior with missing/invalid metrics."""

    def test_missing_metrics_ok_by_default(self):
        """Test that missing metrics → OK when require_micro_metrics=False."""
        config = LiquidityGateConfig(enabled=True, require_micro_metrics=False)
        gate = LiquidityGate(config)

        order = {"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"}
        context = {}  # No metrics

        status = gate.evaluate(order, context)
        assert status.enabled
        assert status.severity == LiquiditySeverity.OK
        assert "passed" in status.reason.lower()

    def test_missing_metrics_warn_when_required(self):
        """Test that missing metrics → WARN when require_micro_metrics=True."""
        config = LiquidityGateConfig(enabled=True, require_micro_metrics=True)
        gate = LiquidityGate(config)

        order = {"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"}
        context = {}  # No metrics

        status = gate.evaluate(order, context)
        assert status.enabled
        assert status.severity == LiquiditySeverity.WARN
        assert "missing_micro_metrics" in status.triggered_by
        assert "missing" in status.reason.lower()


class TestLiquidityGateSpread:
    """Test spread checks."""

    def test_spread_ok(self):
        """Test spread below threshold → OK."""
        config = LiquidityGateConfig(enabled=True, max_spread_pct=0.01)
        gate = LiquidityGate(config)

        order = {"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"}
        context = {"micro": {"spread_pct": 0.005, "last_price": 100.0}}

        status = gate.evaluate(order, context)
        assert status.severity == LiquiditySeverity.OK
        assert "spread" not in status.triggered_by

    def test_spread_warn(self):
        """Test spread at warn threshold → WARN."""
        config = LiquidityGateConfig(
            enabled=True,
            max_spread_pct=0.01,
            warn_spread_pct=0.008,
        )
        gate = LiquidityGate(config)

        # Use LIMIT order to avoid market order strictness (0.7x)
        order = {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 100,
            "order_type": "LIMIT",
            "limit_price": 100.0,
        }
        context = {"micro": {"spread_pct": 0.009, "last_price": 100.0}}

        status = gate.evaluate(order, context)
        assert status.severity == LiquiditySeverity.WARN
        assert "spread" in status.triggered_by
        assert "warn" in status.reason.lower()

    def test_spread_block(self):
        """Test spread at block threshold → BLOCK."""
        config = LiquidityGateConfig(enabled=True, max_spread_pct=0.01)
        gate = LiquidityGate(config)

        order = {"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"}
        context = {"micro": {"spread_pct": 0.015, "last_price": 100.0}}

        status = gate.evaluate(order, context)
        assert status.severity == LiquiditySeverity.BLOCK
        assert "spread" in status.triggered_by
        assert "0.015" in status.reason

    def test_spread_stricter_for_market_orders(self):
        """Test that market orders use stricter thresholds (0.7x)."""
        config = LiquidityGateConfig(
            enabled=True,
            max_spread_pct=0.01,
            strict_for_market_orders=True,
        )
        gate = LiquidityGate(config)

        # Spread at 0.008 (> 0.01 * 0.7 = 0.007) should BLOCK market
        order = {"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"}
        context = {"micro": {"spread_pct": 0.008, "last_price": 100.0}}

        status = gate.evaluate(order, context)
        assert status.severity == LiquiditySeverity.BLOCK
        assert "spread" in status.triggered_by

        # But OK for limit order (no strictness)
        order_limit = {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 100,
            "order_type": "LIMIT",
            "limit_price": 100.0,
        }
        status_limit = gate.evaluate(order_limit, context)
        assert status_limit.severity == LiquiditySeverity.OK

    def test_spread_limit_order_exception(self):
        """Test that limit orders can bypass wide spread BLOCK (if configured)."""
        config = LiquidityGateConfig(
            enabled=True,
            max_spread_pct=0.01,
            allow_limit_orders_when_spread_wide=True,
        )
        gate = LiquidityGate(config)

        # Wide spread should BLOCK market order
        order_market = {"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"}
        context = {"micro": {"spread_pct": 0.02, "last_price": 100.0}}

        status_market = gate.evaluate(order_market, context)
        assert status_market.severity == LiquiditySeverity.BLOCK

        # But only WARN for limit order (exception)
        order_limit = {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 100,
            "order_type": "LIMIT",
            "limit_price": 100.0,
        }
        status_limit = gate.evaluate(order_limit, context)
        assert status_limit.severity == LiquiditySeverity.WARN
        assert "spread" in status_limit.triggered_by
        assert "limit order allowed" in status_limit.reason.lower()


class TestLiquidityGateSlippage:
    """Test slippage checks."""

    def test_slippage_ok(self):
        """Test slippage below threshold → OK."""
        config = LiquidityGateConfig(enabled=True, max_slippage_estimate_pct=0.02)
        gate = LiquidityGate(config)

        order = {"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"}
        context = {"micro": {"slippage_estimate_pct": 0.01, "last_price": 100.0}}

        status = gate.evaluate(order, context)
        assert status.severity == LiquiditySeverity.OK
        assert "slippage" not in status.triggered_by

    def test_slippage_warn(self):
        """Test slippage at warn threshold → WARN."""
        config = LiquidityGateConfig(
            enabled=True,
            max_slippage_estimate_pct=0.02,
            warn_slippage_estimate_pct=0.015,
        )
        gate = LiquidityGate(config)

        # Use LIMIT order to avoid market order strictness (0.7x)
        order = {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 100,
            "order_type": "LIMIT",
            "limit_price": 100.0,
        }
        context = {"micro": {"slippage_estimate_pct": 0.018, "last_price": 100.0}}

        status = gate.evaluate(order, context)
        assert status.severity == LiquiditySeverity.WARN
        assert "slippage" in status.triggered_by

    def test_slippage_block(self):
        """Test slippage at block threshold → BLOCK."""
        config = LiquidityGateConfig(enabled=True, max_slippage_estimate_pct=0.02)
        gate = LiquidityGate(config)

        order = {"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"}
        context = {"micro": {"slippage_estimate_pct": 0.025, "last_price": 100.0}}

        status = gate.evaluate(order, context)
        assert status.severity == LiquiditySeverity.BLOCK
        assert "slippage" in status.triggered_by
        assert "0.025" in status.reason

    def test_slippage_stricter_for_market_orders(self):
        """Test that market orders use stricter slippage thresholds."""
        config = LiquidityGateConfig(
            enabled=True,
            max_slippage_estimate_pct=0.02,
            strict_for_market_orders=True,
        )
        gate = LiquidityGate(config)

        # Slippage at 0.015 (> 0.02 * 0.7 = 0.014) should BLOCK market
        order_market = {"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"}
        context = {"micro": {"slippage_estimate_pct": 0.015, "last_price": 100.0}}

        status_market = gate.evaluate(order_market, context)
        assert status_market.severity == LiquiditySeverity.BLOCK

        # But OK for limit order
        order_limit = {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 100,
            "order_type": "LIMIT",
            "limit_price": 100.0,
        }
        status_limit = gate.evaluate(order_limit, context)
        assert status_limit.severity == LiquiditySeverity.OK


class TestLiquidityGateDepth:
    """Test order book depth checks."""

    def test_depth_sufficient(self):
        """Test sufficient depth → OK."""
        config = LiquidityGateConfig(enabled=True, min_book_depth_multiple=1.5)
        gate = LiquidityGate(config)

        # Order notional: 100 * 100 = 10,000
        # Required depth: 10,000 * 1.5 = 15,000
        # Available depth: 20,000 (OK)
        order = {"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"}
        context = {"micro": {"order_book_depth_notional": 20000.0, "last_price": 100.0}}

        status = gate.evaluate(order, context)
        assert status.severity == LiquiditySeverity.OK
        assert "depth" not in status.triggered_by

    def test_depth_insufficient(self):
        """Test insufficient depth → BLOCK."""
        config = LiquidityGateConfig(enabled=True, min_book_depth_multiple=1.5)
        gate = LiquidityGate(config)

        # Order notional: 100 * 100 = 10,000
        # Required depth: 10,000 * 1.5 = 15,000
        # Available depth: 12,000 (insufficient)
        order = {"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"}
        context = {"micro": {"order_book_depth_notional": 12000.0, "last_price": 100.0}}

        status = gate.evaluate(order, context)
        assert status.severity == LiquiditySeverity.BLOCK
        assert "depth" in status.triggered_by
        assert "12000" in status.reason

    def test_depth_uses_limit_price(self):
        """Test that depth check uses limit_price when available."""
        config = LiquidityGateConfig(enabled=True, min_book_depth_multiple=2.0)
        gate = LiquidityGate(config)

        # Order notional: 100 * 105 = 10,500 (using limit_price)
        # Required depth: 10,500 * 2.0 = 21,000
        # Available depth: 20,000 (insufficient)
        order = {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 100,
            "order_type": "LIMIT",
            "limit_price": 105.0,
        }
        context = {"micro": {"order_book_depth_notional": 20000.0, "last_price": 100.0}}

        status = gate.evaluate(order, context)
        assert status.severity == LiquiditySeverity.BLOCK
        assert "depth" in status.triggered_by


class TestLiquidityGateOrderToADV:
    """Test order size vs ADV checks."""

    def test_order_to_adv_ok(self):
        """Test order size within ADV limit → OK."""
        config = LiquidityGateConfig(enabled=True, max_order_to_adv_pct=0.05)
        gate = LiquidityGate(config)

        # Order notional: 100 * 100 = 10,000
        # ADV: 1,000,000
        # Ratio: 0.01 (1%) < 5% (OK)
        order = {"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"}
        context = {"micro": {"adv_notional": 1_000_000.0, "last_price": 100.0}}

        status = gate.evaluate(order, context)
        assert status.severity == LiquiditySeverity.OK
        assert "order_to_adv" not in status.triggered_by

    def test_order_to_adv_too_large(self):
        """Test order size exceeds ADV limit → BLOCK."""
        config = LiquidityGateConfig(enabled=True, max_order_to_adv_pct=0.02)
        gate = LiquidityGate(config)

        # Order notional: 1000 * 100 = 100,000
        # ADV: 1,000,000
        # Ratio: 0.10 (10%) > 2% (BLOCK)
        order = {"symbol": "AAPL", "side": "BUY", "quantity": 1000, "order_type": "MARKET"}
        context = {"micro": {"adv_notional": 1_000_000.0, "last_price": 100.0}}

        status = gate.evaluate(order, context)
        assert status.severity == LiquiditySeverity.BLOCK
        assert "order_to_adv" in status.triggered_by
        assert "10.00%" in status.reason or "0.1" in status.reason


class TestLiquidityGateMultipleTriggers:
    """Test multiple simultaneous violations."""

    def test_multiple_triggers_collected(self):
        """Test that multiple triggers are collected."""
        config = LiquidityGateConfig(
            enabled=True,
            max_spread_pct=0.005,
            max_slippage_estimate_pct=0.01,
            min_book_depth_multiple=2.0,
        )
        gate = LiquidityGate(config)

        # Order notional: 100 * 100 = 10,000
        # Violations:
        # - Spread: 0.01 > 0.005
        # - Slippage: 0.02 > 0.01
        # - Depth: 15,000 < 20,000 (2.0x)
        order = {"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"}
        context = {
            "micro": {
                "spread_pct": 0.01,
                "slippage_estimate_pct": 0.02,
                "order_book_depth_notional": 15000.0,
                "last_price": 100.0,
            }
        }

        status = gate.evaluate(order, context)
        assert status.severity == LiquiditySeverity.BLOCK
        assert "spread" in status.triggered_by
        assert "slippage" in status.triggered_by
        assert "depth" in status.triggered_by
        assert len(status.triggered_by) == 3

    def test_worst_severity_wins(self):
        """Test that BLOCK > WARN > OK."""
        config = LiquidityGateConfig(
            enabled=True,
            max_spread_pct=0.01,
            warn_spread_pct=0.008,
            max_slippage_estimate_pct=0.02,  # Won't trigger
        )
        gate = LiquidityGate(config)

        # Spread triggers WARN (use LIMIT to avoid market strictness)
        order = {
            "symbol": "AAPL",
            "side": "BUY",
            "quantity": 100,
            "order_type": "LIMIT",
            "limit_price": 100.0,
        }
        context = {
            "micro": {
                "spread_pct": 0.009,
                "slippage_estimate_pct": 0.005,
                "last_price": 100.0,
            }
        }

        status = gate.evaluate(order, context)
        assert status.severity == LiquiditySeverity.WARN

        # Now add depth violation (BLOCK)
        context["micro"]["order_book_depth_notional"] = 1000.0  # Too small
        status2 = gate.evaluate(order, context)
        assert status2.severity == LiquiditySeverity.BLOCK


class TestLiquidityGateStatusSerialization:
    """Test status serialization for audit trail."""

    def test_status_to_dict_complete(self):
        """Test that status serializes to stable dict."""
        config = LiquidityGateConfig(enabled=True)
        gate = LiquidityGate(config)

        order = {"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"}
        context = {"micro": {"spread_pct": 0.002, "last_price": 100.0}}

        status = gate.evaluate(order, context)
        result = liquidity_gate_status_to_dict(status)

        # Check required keys
        assert "enabled" in result
        assert "severity" in result
        assert "reason" in result
        assert "triggered_by" in result
        assert "micro_metrics_snapshot" in result
        assert "order_snapshot" in result
        assert "thresholds" in result
        assert "timestamp_utc" in result

        # Check types
        assert isinstance(result["enabled"], bool)
        assert isinstance(result["severity"], str)
        assert isinstance(result["triggered_by"], list)
        assert isinstance(result["micro_metrics_snapshot"], dict)
        assert isinstance(result["order_snapshot"], dict)
        assert isinstance(result["thresholds"], dict)

    def test_status_to_dict_json_serializable(self):
        """Test that serialized status is JSON-serializable."""
        import json

        config = LiquidityGateConfig(enabled=True, max_spread_pct=0.01)
        gate = LiquidityGate(config)

        order = {"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"}
        context = {"micro": {"spread_pct": 0.02, "last_price": 100.0}}

        status = gate.evaluate(order, context)
        result = liquidity_gate_status_to_dict(status)

        # Should not raise
        json_str = json.dumps(result)
        assert json_str

        # Round-trip
        parsed = json.loads(json_str)
        assert parsed["severity"] == "BLOCK"

    def test_triggered_by_sorted(self):
        """Test that triggered_by list is sorted (deterministic)."""
        config = LiquidityGateConfig(
            enabled=True,
            max_spread_pct=0.005,
            max_slippage_estimate_pct=0.01,
        )
        gate = LiquidityGate(config)

        order = {"symbol": "AAPL", "side": "BUY", "quantity": 100, "order_type": "MARKET"}
        context = {
            "micro": {
                "spread_pct": 0.01,
                "slippage_estimate_pct": 0.02,
                "last_price": 100.0,
            }
        }

        status = gate.evaluate(order, context)
        result = liquidity_gate_status_to_dict(status)

        # triggered_by should be sorted
        assert result["triggered_by"] == sorted(result["triggered_by"])


class TestLiquidityGateEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_quantity_order(self):
        """Test that zero quantity orders are handled gracefully."""
        config = LiquidityGateConfig(enabled=True)
        gate = LiquidityGate(config)

        order = {"symbol": "AAPL", "side": "BUY", "quantity": 0, "order_type": "MARKET"}
        context = {"micro": {"spread_pct": 0.002, "last_price": 100.0}}

        # Should not crash
        status = gate.evaluate(order, context)
        assert status.enabled

    def test_negative_quantity(self):
        """Test that negative quantities use abs() value."""
        config = LiquidityGateConfig(enabled=True, min_book_depth_multiple=1.5)
        gate = LiquidityGate(config)

        # Negative quantity (sell)
        order = {"symbol": "AAPL", "side": "SELL", "quantity": -100, "order_type": "MARKET"}
        context = {"micro": {"order_book_depth_notional": 20000.0, "last_price": 100.0}}

        # Should use abs(quantity) = 100
        status = gate.evaluate(order, context)
        assert status.severity == LiquiditySeverity.OK

    def test_missing_order_type_defaults(self):
        """Test that missing order_type is handled gracefully."""
        config = LiquidityGateConfig(enabled=True)
        gate = LiquidityGate(config)

        order = {"symbol": "AAPL", "side": "BUY", "quantity": 100}  # No order_type
        context = {"micro": {"spread_pct": 0.002, "last_price": 100.0}}

        # Should not crash (defaults to treating as non-market)
        status = gate.evaluate(order, context)
        assert status.enabled

    def test_empty_order_snapshot_stable(self):
        """Test that order snapshot is stable even with minimal order."""
        config = LiquidityGateConfig(enabled=True)
        gate = LiquidityGate(config)

        order = {}  # Empty order
        context = {}

        status = gate.evaluate(order, context)

        # Order snapshot should have default values
        assert isinstance(status.order_snapshot, dict)
        assert "symbol" in status.order_snapshot
        assert "side" in status.order_snapshot
        assert "quantity" in status.order_snapshot
