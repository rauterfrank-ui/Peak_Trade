"""
Risk Layer Smoke Tests - Phase 0
=================================

Validates that the risk layer architecture is properly set up:
- All canonical exports can be imported
- No implementation logic tested (Phase 0 = structure only)
"""

import pytest

# Test Phase 0 canonical exports from risk_layer
from src.risk_layer import (
    KillSwitchLayer,
    KillSwitchStatus,
    order_to_dict,
    to_order,
)


class TestPhase0Imports:
    """Test that all Phase 0 canonical exports can be imported."""

    def test_kill_switch_import(self):
        """Kill Switch components are importable."""
        assert KillSwitchLayer is not None
        assert KillSwitchStatus is not None

    def test_order_adapters_import(self):
        """Order adapter functions are importable."""
        assert order_to_dict is not None
        assert to_order is not None


class TestKillSwitchStatus:
    """Test that KillSwitchStatus works."""

    def test_status_instantiation(self):
        """KillSwitchStatus can be instantiated."""
        status = KillSwitchStatus(armed=False)
        assert status.armed is False
        assert status.enabled is True


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
