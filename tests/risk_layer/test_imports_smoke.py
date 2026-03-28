"""
Risk Layer Smoke Tests - Phase 0
=================================

Validates that the risk layer architecture is properly set up:
- All canonical exports can be imported
- No implementation logic tested (Phase 0 = structure only)
"""

# Test Phase 0 canonical exports from risk_layer
from src.risk_layer import order_to_dict, to_order
from src.risk_layer.kill_switch import KillSwitch


class TestPhase0Imports:
    """Test that all Phase 0 canonical exports can be imported."""

    def test_kill_switch_import(self):
        """Kill Switch state machine is importable."""
        assert KillSwitch is not None

    def test_kill_switch_constructible(self):
        """KillSwitch can be constructed with minimal config (no legacy adapter)."""
        ks = KillSwitch(
            {
                "enabled": True,
                "mode": "active",
                "recovery_cooldown_seconds": 1,
                "require_approval_code": False,
            }
        )
        assert ks.check_and_block() is False

    def test_order_adapters_import(self):
        """Order adapter functions are importable."""
        assert order_to_dict is not None
        assert to_order is not None


class TestOrderAdapters:
    """Test that order adapters have basic functionality."""

    def test_to_order_minimal(self):
        """to_order can be called with minimal dict."""
        order_dict = {
            "symbol": "BTC/USD",
            "side": "buy",
            "order_type": "limit",
            "quantity": 1.0,
            "price": 50000.0,
        }
        order = to_order(order_dict)
        assert order is not None
        assert order.symbol == "BTC/USD"
        assert order.side == "buy"

    def test_order_to_dict_roundtrip(self):
        """order_to_dict and to_order work together."""
        order_dict = {
            "symbol": "ETH/USD",
            "side": "sell",
            "order_type": "market",
            "quantity": 2.0,
        }
        order = to_order(order_dict)
        result_dict = order_to_dict(order)
        assert result_dict["symbol"] == "ETH/USD"
        assert result_dict["side"] == "sell"
        assert result_dict["quantity"] == 2.0
