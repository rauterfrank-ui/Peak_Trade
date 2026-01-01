"""
Tests for WP1B - Paper Broker

Tests:
- Deterministic fills for fixed seed
- Slippage/fee calculations
- Partial fills
- Limit order fills
"""

from decimal import Decimal

import pytest

from src.execution.contracts import Order, OrderSide, OrderState, OrderType
from src.execution.paper.broker import FillSimulationConfig, PaperBroker


class TestPaperBrokerDeterministic:
    """Test deterministic fill simulation."""

    def test_market_order_full_fill_deterministic(self):
        """Test market order full fill is deterministic."""
        config = FillSimulationConfig(
            slippage_bps=Decimal("5"),
            fee_bps=Decimal("10"),
            random_seed=42,
            partial_fill_prob=0.0,  # No partials
        )
        broker = PaperBroker(config)

        order = Order(
            client_order_id="test_001",
            symbol="BTC/USD",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("1.0"),
        )

        state, fills = broker.submit_order(order, current_price=Decimal("50000"))

        assert state == OrderState.FILLED
        assert len(fills) == 1

        fill = fills[0]
        # BUY: slippage increases price (50000 * 1.0005 = 50025)
        expected_price = Decimal("50000") * Decimal("1.0005")
        assert fill.price == expected_price
        assert fill.quantity == Decimal("1.0")

        # Fee: (50025 * 1.0) * 0.001 = 50.025
        expected_fee = expected_price * Decimal("1.0") * Decimal("0.001")
        assert fill.fee == expected_fee

    def test_market_order_sell_slippage(self):
        """Test SELL order has negative slippage."""
        config = FillSimulationConfig(
            slippage_bps=Decimal("5"),
            fee_bps=Decimal("10"),
            random_seed=42,
        )
        broker = PaperBroker(config)

        order = Order(
            client_order_id="test_002",
            symbol="BTC/USD",
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.5"),
        )

        state, fills = broker.submit_order(order, current_price=Decimal("50000"))

        assert state == OrderState.FILLED
        assert len(fills) == 1

        fill = fills[0]
        # SELL: slippage decreases price (50000 * 0.9995 = 49975)
        expected_price = Decimal("50000") * Decimal("0.9995")
        assert fill.price == expected_price

    def test_limit_order_favorable_price(self):
        """Test limit order fills when price is favorable."""
        config = FillSimulationConfig(random_seed=42)
        broker = PaperBroker(config)

        # BUY limit at 50000, market at 49000 (favorable)
        order = Order(
            client_order_id="test_003",
            symbol="BTC/USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1.0"),
            price=Decimal("50000"),
        )

        state, fills = broker.submit_order(order, current_price=Decimal("49000"))

        assert state == OrderState.FILLED
        assert len(fills) == 1

        fill = fills[0]
        # Limit fills at limit price (no slippage)
        assert fill.price == Decimal("50000")

    def test_limit_order_unfavorable_price(self):
        """Test limit order does NOT fill when price is unfavorable."""
        config = FillSimulationConfig(random_seed=42)
        broker = PaperBroker(config)

        # BUY limit at 50000, market at 51000 (unfavorable)
        order = Order(
            client_order_id="test_004",
            symbol="BTC/USD",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("1.0"),
            price=Decimal("50000"),
        )

        state, fills = broker.submit_order(order, current_price=Decimal("51000"))

        assert state == OrderState.ACKNOWLEDGED  # Not filled
        assert len(fills) == 0

    def test_partial_fills_deterministic(self):
        """Test partial fills are deterministic with seed."""
        config = FillSimulationConfig(
            random_seed=42,
            partial_fill_prob=1.0,  # Always partial
        )
        broker = PaperBroker(config)

        order = Order(
            client_order_id="test_005",
            symbol="BTC/USD",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("10.0"),
        )

        state1, fills1 = broker.submit_order(order, current_price=Decimal("50000"))

        # Reset broker with same seed
        broker2 = PaperBroker(config)
        state2, fills2 = broker2.submit_order(order, current_price=Decimal("50000"))

        # Should be identical
        assert state1 == state2
        assert len(fills1) == len(fills2)
        assert fills1[0].quantity == fills2[0].quantity
        assert fills1[0].price == fills2[0].price


class TestPaperBrokerValidation:
    """Test order validation."""

    def test_invalid_quantity_rejected(self):
        """Test order with invalid quantity is rejected."""
        config = FillSimulationConfig()
        broker = PaperBroker(config)

        order = Order(
            client_order_id="test_006",
            symbol="BTC/USD",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0"),  # Invalid
        )

        state, fills = broker.submit_order(order, current_price=Decimal("50000"))

        assert state == OrderState.REJECTED
        assert len(fills) == 0


class TestPaperBrokerStats:
    """Test broker statistics."""

    def test_stats_tracking(self):
        """Test broker tracks statistics correctly."""
        config = FillSimulationConfig(random_seed=42)
        broker = PaperBroker(config)

        # Submit 3 orders
        for i in range(3):
            order = Order(
                client_order_id=f"test_{i}",
                symbol="BTC/USD",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=Decimal("1.0"),
            )
            broker.submit_order(order, current_price=Decimal("50000"))

        stats = broker.get_stats()

        assert stats["orders_submitted"] == 3
        assert stats["fills_generated"] == 3
        assert Decimal(stats["total_fees"]) > 0


class TestFillSimulationConfig:
    """Test fill simulation config validation."""

    def test_negative_slippage_rejected(self):
        """Test negative slippage is rejected."""
        with pytest.raises(ValueError, match="slippage_bps must be >= 0"):
            FillSimulationConfig(slippage_bps=Decimal("-1"))

    def test_negative_fee_rejected(self):
        """Test negative fee is rejected."""
        with pytest.raises(ValueError, match="fee_bps must be >= 0"):
            FillSimulationConfig(fee_bps=Decimal("-1"))
