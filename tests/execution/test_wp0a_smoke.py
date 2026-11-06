"""
WP0A Smoke Tests - Execution Core v1

Quick verification that all WP0A modules work together.
"""

from decimal import Decimal

import pytest

from src.execution.contracts import Order, OrderSide, OrderType, Fill
from src.execution.order_state_machine import OrderStateMachine
from src.execution.order_ledger import OrderLedger
from src.execution.position_ledger import PositionLedger
from src.execution.audit_log import AuditLog
from src.execution.retry_policy import RetryPolicy, RetryConfig
from src.execution.risk_hook import NullRiskHook


# ============================================================================
# Order State Machine Smoke Tests
# ============================================================================


def test_osm_basic_workflow():
    """Test basic order lifecycle through state machine"""
    osm = OrderStateMachine(risk_hook=NullRiskHook())

    # Create order
    result = osm.create_order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side="BUY",
        quantity=Decimal("0.001"),
    )

    assert result.success
    order = result.order
    assert order.state.value == "CREATED"

    # Submit order
    result = osm.submit_order(order)
    assert result.success
    assert order.state.value == "SUBMITTED"

    # Acknowledge order
    result = osm.acknowledge_order(order, exchange_order_id="exch_001")
    assert result.success
    assert order.state.value == "ACKNOWLEDGED"
    assert order.exchange_order_id == "exch_001"


def test_osm_fill_workflow():
    """Test fill application through state machine"""
    osm = OrderStateMachine()

    # Create and submit order
    result = osm.create_order(
        client_order_id="test_002",
        symbol="BTC-EUR",
        side="BUY",
        quantity=Decimal("0.01"),
    )
    order = result.order

    osm.submit_order(order)
    osm.acknowledge_order(order, exchange_order_id="exch_002")

    # Apply fill
    fill = Fill(
        fill_id="fill_001",
        client_order_id=order.client_order_id,
        exchange_order_id=order.exchange_order_id,
        symbol=order.symbol,
        side=order.side,
        quantity=Decimal("0.01"),
        price=Decimal("50000"),
    )

    result = osm.apply_fill(order, fill)
    assert result.success
    assert order.state.value == "FILLED"


# ============================================================================
# Order Ledger Smoke Tests
# ============================================================================


def test_order_ledger_basic():
    """Test basic order ledger operations"""
    ledger = OrderLedger()

    order = Order(
        client_order_id="test_003",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    # Add order
    added = ledger.add_order(order)
    assert added

    # Retrieve order
    retrieved = ledger.get_order("test_003")
    assert retrieved is not None
    assert retrieved.client_order_id == "test_003"

    # Update order
    order.exchange_order_id = "exch_003"
    updated = ledger.update_order(order)
    assert updated

    # Query by exchange ID
    retrieved = ledger.get_order_by_exchange_id("exch_003")
    assert retrieved is not None
    assert retrieved.client_order_id == "test_003"


def test_order_ledger_queries():
    """Test order ledger query methods"""
    ledger = OrderLedger()

    # Add multiple orders
    for i in range(5):
        order = Order(
            client_order_id=f"test_{i:03d}",
            symbol="BTC-EUR",
            side=OrderSide.BUY,
            quantity=Decimal("0.001"),
        )
        ledger.add_order(order)

    # Query all orders
    all_orders = ledger.get_all_orders()
    assert len(all_orders) == 5

    # Query active orders
    active_orders = ledger.get_active_orders()
    assert len(active_orders) == 0  # All in CREATED state (not active)

    # Get state counts
    counts = ledger.get_state_counts()
    assert counts.get("CREATED", 0) >= 5


# ============================================================================
# Position Ledger Smoke Tests
# ============================================================================


def test_position_ledger_basic():
    """Test basic position ledger operations"""
    ledger = PositionLedger(initial_cash=Decimal("10000"))

    # Apply BUY fill
    fill = Fill(
        fill_id="fill_001",
        client_order_id="test_001",
        exchange_order_id="exch_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.1"),
        price=Decimal("50000"),
        fee=Decimal("5"),
    )

    position = ledger.apply_fill(fill)

    assert position.symbol == "BTC-EUR"
    assert position.quantity == Decimal("0.1")
    assert position.is_long()
    assert not position.is_flat()

    # Check cash
    cash = ledger.get_cash_balance()
    assert cash < Decimal("10000")  # Cash reduced by fill


def test_position_ledger_round_trip():
    """Test position ledger buy/sell round trip"""
    ledger = PositionLedger(initial_cash=Decimal("10000"))

    # BUY
    buy_fill = Fill(
        fill_id="fill_buy",
        client_order_id="test_001",
        exchange_order_id="exch_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.1"),
        price=Decimal("50000"),
    )
    ledger.apply_fill(buy_fill)

    # SELL (close position)
    sell_fill = Fill(
        fill_id="fill_sell",
        client_order_id="test_002",
        exchange_order_id="exch_002",
        symbol="BTC-EUR",
        side=OrderSide.SELL,
        quantity=Decimal("0.1"),
        price=Decimal("51000"),
    )
    position = ledger.apply_fill(sell_fill)

    # Position should be flat
    assert position.is_flat()

    # Realized PnL should be positive
    assert position.realized_pnl > 0


# ============================================================================
# Audit Log Smoke Tests
# ============================================================================


def test_audit_log_basic():
    """Test basic audit log operations"""
    audit = AuditLog()

    from src.execution.contracts import LedgerEntry, OrderState

    # Append entry
    entry = LedgerEntry(
        entry_id="entry_001",
        event_type="ORDER_CREATED",
        client_order_id="test_001",
        old_state=None,
        new_state=OrderState.CREATED,
    )

    audit.append(entry)

    # Check count
    assert audit.get_entry_count() == 1

    # Query entries
    entries = audit.get_all_entries()
    assert len(entries) == 1
    assert entries[0].client_order_id == "test_001"


def test_audit_log_queries():
    """Test audit log query methods"""
    audit = AuditLog()

    from src.execution.contracts import LedgerEntry, OrderState

    # Add multiple entries
    for i in range(5):
        entry = LedgerEntry(
            entry_id=f"entry_{i:03d}",
            event_type="ORDER_CREATED" if i % 2 == 0 else "ORDER_SUBMITTED",
            client_order_id=f"test_{i:03d}",
            old_state=None,
            new_state=OrderState.CREATED,
        )
        audit.append(entry)

    # Query by order ID
    entries = audit.get_entries_for_order("test_000")
    assert len(entries) == 1

    # Query by event type
    created_entries = audit.get_entries_by_event_type("ORDER_CREATED")
    assert len(created_entries) == 3  # i=0,2,4


# ============================================================================
# Retry Policy Smoke Tests
# ============================================================================


def test_retry_policy_success():
    """Test retry policy with successful operation"""
    policy = RetryPolicy()

    call_count = [0]

    def operation():
        call_count[0] += 1
        return "success"

    result = policy.retry(operation)

    assert result == "success"
    assert call_count[0] == 1  # No retries needed


def test_retry_policy_transient_failure():
    """Test retry policy with transient failure"""
    config = RetryConfig(max_retries=3, initial_delay=0.01)
    policy = RetryPolicy(config)

    call_count = [0]

    def operation():
        call_count[0] += 1
        if call_count[0] < 3:
            raise ConnectionError("Transient error")
        return "success"

    result = policy.retry(operation)

    assert result == "success"
    assert call_count[0] == 3  # 2 retries + 1 success


def test_retry_policy_non_retryable():
    """Test retry policy with non-retryable error"""
    policy = RetryPolicy()

    call_count = [0]

    def operation():
        call_count[0] += 1
        raise ValueError("Invalid order")  # Non-retryable

    with pytest.raises(ValueError):
        policy.retry(operation)

    assert call_count[0] == 1  # No retries


# ============================================================================
# Integration Smoke Test
# ============================================================================


def test_wp0a_integration():
    """Integration test: Full order lifecycle with all components"""
    # Initialize components
    osm = OrderStateMachine(risk_hook=NullRiskHook())
    order_ledger = OrderLedger()
    position_ledger = PositionLedger(initial_cash=Decimal("10000"))
    audit = AuditLog()

    # Create order
    result = osm.create_order(
        client_order_id="integration_001",
        symbol="BTC-EUR",
        side="BUY",
        quantity=Decimal("0.01"),
    )
    assert result.success
    order = result.order

    # Add to order ledger
    order_ledger.add_order(order)

    # Add audit entries
    audit.append_many(result.ledger_entries)

    # Submit order
    result = osm.submit_order(order)
    order_ledger.update_order(order, event="ORDER_SUBMITTED")
    audit.append_many(result.ledger_entries)

    # Acknowledge
    result = osm.acknowledge_order(order, exchange_order_id="exch_int_001")
    order_ledger.update_order(order, event="ORDER_ACKNOWLEDGED")
    audit.append_many(result.ledger_entries)

    # Fill
    fill = Fill(
        fill_id="fill_int_001",
        client_order_id=order.client_order_id,
        exchange_order_id=order.exchange_order_id,
        symbol=order.symbol,
        side=order.side,
        quantity=order.quantity,
        price=Decimal("50000"),
        fee=Decimal("5"),
    )

    result = osm.apply_fill(order, fill)
    order_ledger.update_order(order, event="ORDER_FILLED")
    audit.append_many(result.ledger_entries)

    # Apply fill to position ledger
    position = position_ledger.apply_fill(fill)

    # Verify final state
    assert order.state.value == "FILLED"
    assert position.quantity == Decimal("0.01")
    assert position.is_long()
    assert audit.get_entry_count() > 0

    # Verify ledgers
    retrieved_order = order_ledger.get_order("integration_001")
    assert retrieved_order.state.value == "FILLED"

    retrieved_position = position_ledger.get_position("BTC-EUR")
    assert retrieved_position.quantity == Decimal("0.01")
