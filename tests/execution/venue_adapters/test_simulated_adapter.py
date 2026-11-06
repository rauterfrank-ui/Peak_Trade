"""
Tests for SimulatedVenueAdapter (WP0C - Phase 0 Foundation)

Tests:
- Deterministic fills (same inputs → same outputs)
- Idempotency (duplicate orders rejected)
- Slippage/fee calculation
- Market/limit order handling
- Validation errors
"""

import pytest
from decimal import Decimal

from src.execution.contracts import Order, OrderSide, OrderType, OrderState
from src.execution.orchestrator import ExecutionEvent
from src.execution.venue_adapters.simulated import SimulatedVenueAdapter
from src.execution.venue_adapters.fill_models import (
    ImmediateFillModel,
    FixedFeeModel,
    FixedSlippageModel,
)


class TestSimulatedVenueAdapterFills:
    """Test fill generation (deterministic)."""

    def test_market_order_buy_immediate_fill(self):
        """Market BUY order should fill immediately with slippage."""
        adapter = SimulatedVenueAdapter(
            market_prices={"BTC/EUR": Decimal("50000.00")},
            slippage_model=FixedSlippageModel(slippage_bps=5),  # 0.05%
            fee_model=FixedFeeModel(fee_rate=Decimal("0.001")),  # 0.1%
        )

        order = Order(
            client_order_id="order_001",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            quantity=Decimal("0.01"),
            order_type=OrderType.MARKET,
            state=OrderState.CREATED,
        )

        event = adapter.execute_order(order, idempotency_key="idem_001")

        assert event.event_type == "FILL"
        assert event.order_id == "order_001"
        assert event.fill is not None

        fill = event.fill
        # BUY with 5bps slippage: 50000 * 1.0005 = 50025
        expected_fill_price = Decimal("50025.00")
        assert fill.price == expected_fill_price
        assert fill.quantity == Decimal("0.01")

        # Fee: 0.01 * 50025 * 0.001 = 0.50025
        expected_fee = Decimal("0.50025000")
        assert fill.fee == expected_fee

    def test_market_order_sell_immediate_fill(self):
        """Market SELL order should fill immediately with slippage."""
        adapter = SimulatedVenueAdapter(
            market_prices={"ETH/EUR": Decimal("3000.00")},
            slippage_model=FixedSlippageModel(slippage_bps=5),
            fee_model=FixedFeeModel(fee_rate=Decimal("0.001")),
        )

        order = Order(
            client_order_id="order_002",
            symbol="ETH/EUR",
            side=OrderSide.SELL,
            quantity=Decimal("0.5"),
            order_type=OrderType.MARKET,
            state=OrderState.CREATED,
        )

        event = adapter.execute_order(order, idempotency_key="idem_002")

        assert event.event_type == "FILL"
        fill = event.fill
        assert fill is not None

        # SELL with 5bps slippage: 3000 * 0.9995 = 2998.50
        expected_fill_price = Decimal("2998.50")
        assert fill.price == expected_fill_price
        assert fill.quantity == Decimal("0.5")

    def test_limit_order_buy_within_limit(self):
        """Limit BUY order should fill at best price (within limit)."""
        adapter = SimulatedVenueAdapter(
            market_prices={"BTC/EUR": Decimal("50000.00")},
            slippage_model=FixedSlippageModel(slippage_bps=10),  # 0.1%
        )

        order = Order(
            client_order_id="order_003",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            quantity=Decimal("0.01"),
            order_type=OrderType.LIMIT,
            price=Decimal("50100.00"),  # Higher than slipped market
            state=OrderState.CREATED,
        )

        event = adapter.execute_order(order, idempotency_key="idem_003")

        fill = event.fill
        assert fill is not None

        # Slipped market: 50000 * 1.001 = 50050
        # Limit: 50100
        # Fill at: min(50100, 50050) = 50050
        expected_fill_price = Decimal("50050.00")
        assert fill.price == expected_fill_price

    def test_deterministic_fills_same_input_same_output(self):
        """Same order should produce same fill (deterministic)."""
        adapter = SimulatedVenueAdapter(
            market_prices={"BTC/EUR": Decimal("50000.00")},
        )

        order = Order(
            client_order_id="order_det",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            quantity=Decimal("0.01"),
            order_type=OrderType.MARKET,
            state=OrderState.CREATED,
        )

        # Execute twice with different idempotency keys (to bypass cache)
        event1 = adapter.execute_order(order, idempotency_key="idem_det_1")
        adapter.clear_idempotency_cache()
        event2 = adapter.execute_order(order, idempotency_key="idem_det_2")

        # Should produce identical fills
        assert event1.fill.price == event2.fill.price
        assert event1.fill.quantity == event2.fill.quantity
        assert event1.fill.fee == event2.fill.fee


class TestSimulatedVenueAdapterIdempotency:
    """Test idempotency enforcement."""

    def test_duplicate_idempotency_key_returns_cached_result(self):
        """Duplicate idempotency_key should return cached ExecutionEvent."""
        adapter = SimulatedVenueAdapter()

        order = Order(
            client_order_id="order_idem",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            quantity=Decimal("0.01"),
            order_type=OrderType.MARKET,
            state=OrderState.CREATED,
        )

        # First execution
        event1 = adapter.execute_order(order, idempotency_key="idem_same")

        # Second execution with same idempotency_key
        event2 = adapter.execute_order(order, idempotency_key="idem_same")

        # Should be identical (same object from cache)
        assert event1 is event2
        assert event1.fill.fill_id == event2.fill.fill_id

    def test_different_idempotency_keys_same_order(self):
        """Different idempotency_keys for same order should be idempotent."""
        adapter = SimulatedVenueAdapter()

        order = Order(
            client_order_id="order_idem2",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            quantity=Decimal("0.01"),
            order_type=OrderType.MARKET,
            state=OrderState.CREATED,
        )

        event1 = adapter.execute_order(order, idempotency_key="idem_1")
        # Second call with different idempotency_key BUT same order
        event2 = adapter.execute_order(order, idempotency_key="idem_2")

        # Same fill_id (deterministic based on order_id, not idempotency_key)
        # This is correct: same order → same fill (idempotency by order, not by key)
        assert event1.fill.fill_id == event2.fill.fill_id
        assert event1.fill.price == event2.fill.price  # Deterministic


class TestSimulatedVenueAdapterValidation:
    """Test order validation."""

    def test_unknown_symbol_rejected(self):
        """Order with unknown symbol should be rejected."""
        adapter = SimulatedVenueAdapter(
            market_prices={"BTC/EUR": Decimal("50000.00")},
        )

        order = Order(
            client_order_id="order_bad_symbol",
            symbol="UNKNOWN/EUR",
            side=OrderSide.BUY,
            quantity=Decimal("0.01"),
            order_type=OrderType.MARKET,
            state=OrderState.CREATED,
        )

        event = adapter.execute_order(order, idempotency_key="idem_bad_symbol")

        assert event.event_type == "REJECT"
        assert event.reject_reason == "Unknown symbol: UNKNOWN/EUR"

    def test_zero_quantity_rejected(self):
        """Order with quantity <= 0 should be rejected."""
        adapter = SimulatedVenueAdapter()

        order = Order(
            client_order_id="order_zero_qty",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            quantity=Decimal("0"),
            order_type=OrderType.MARKET,
            state=OrderState.CREATED,
        )

        event = adapter.execute_order(order, idempotency_key="idem_zero_qty")

        assert event.event_type == "REJECT"
        assert "Invalid quantity" in event.reject_reason

    def test_limit_order_without_price_rejected(self):
        """LIMIT order without price should be rejected."""
        adapter = SimulatedVenueAdapter()

        order = Order(
            client_order_id="order_no_limit",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            quantity=Decimal("0.01"),
            order_type=OrderType.LIMIT,
            price=None,  # Missing!
            state=OrderState.CREATED,
        )

        event = adapter.execute_order(order, idempotency_key="idem_no_limit")

        assert event.event_type == "REJECT"
        assert "requires price" in event.reject_reason


class TestSimulatedVenueAdapterDisabledFills:
    """Test adapter with fills disabled (ACK only)."""

    def test_ack_only_no_fill_when_disabled(self):
        """Adapter with enable_fills=False should ACK but not fill."""
        adapter = SimulatedVenueAdapter(enable_fills=False)

        order = Order(
            client_order_id="order_no_fill",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            quantity=Decimal("0.01"),
            order_type=OrderType.MARKET,
            state=OrderState.CREATED,
        )

        event = adapter.execute_order(order, idempotency_key="idem_no_fill")

        assert event.event_type == "ACK"
        assert event.fill is None
        assert event.exchange_order_id.startswith("sim_ack_")


class TestSimulatedVenueAdapterMarketPrices:
    """Test market price management."""

    def test_set_market_price_updates_price(self):
        """set_market_price should update market price."""
        adapter = SimulatedVenueAdapter(
            market_prices={"BTC/EUR": Decimal("50000.00")},
        )

        # Update price
        adapter.set_market_price("BTC/EUR", Decimal("60000.00"))

        order = Order(
            client_order_id="order_updated_price",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            quantity=Decimal("0.01"),
            order_type=OrderType.MARKET,
            state=OrderState.CREATED,
        )

        event = adapter.execute_order(order, idempotency_key="idem_updated")

        # Fill price should reflect new market price (60000 * 1.0005 = 60030)
        expected_price = Decimal("60030.00")
        assert event.fill.price == expected_price
