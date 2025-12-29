"""
WP0B Tests - MaxOpenOrdersPolicy
"""

from decimal import Decimal

import pytest

from src.execution.contracts import Order, OrderSide, OrderState
from src.execution.risk_runtime import (
    MaxOpenOrdersPolicy,
    RiskRuntime,
    RiskDecision,
    build_context_snapshot,
)
from src.execution.order_ledger import OrderLedger
from src.execution.audit_log import AuditLog


def test_max_open_orders_allows_within_limit():
    """Test MaxOpenOrdersPolicy allows when within limit"""
    policy = MaxOpenOrdersPolicy(max_open_orders=5)

    # Create snapshot with 3 open orders
    from src.execution.risk_runtime.context import RiskContextSnapshot
    snapshot = RiskContextSnapshot(open_orders_count=3)

    directive = policy.evaluate(snapshot)

    assert directive.decision == RiskDecision.ALLOW
    assert "within limit" in directive.reason


def test_max_open_orders_rejects_at_limit():
    """Test MaxOpenOrdersPolicy rejects at limit"""
    policy = MaxOpenOrdersPolicy(max_open_orders=5)

    # Create snapshot with 5 open orders (at limit)
    from src.execution.risk_runtime.context import RiskContextSnapshot
    snapshot = RiskContextSnapshot(open_orders_count=5)

    directive = policy.evaluate(snapshot)

    assert directive.decision == RiskDecision.REJECT
    assert "exceeded" in directive.reason
    assert "5" in directive.reason


def test_max_open_orders_rejects_above_limit():
    """Test MaxOpenOrdersPolicy rejects above limit"""
    policy = MaxOpenOrdersPolicy(max_open_orders=3)

    from src.execution.risk_runtime.context import RiskContextSnapshot
    snapshot = RiskContextSnapshot(open_orders_count=10)

    directive = policy.evaluate(snapshot)

    assert directive.decision == RiskDecision.REJECT


def test_max_open_orders_with_real_ledger():
    """Test MaxOpenOrdersPolicy with real OrderLedger"""
    policy = MaxOpenOrdersPolicy(max_open_orders=2)
    runtime = RiskRuntime(policies=[policy])

    ledger = OrderLedger()

    # Add 2 orders (at limit)
    for i in range(2):
        order = Order(
            client_order_id=f"order_{i}",
            symbol="BTC-EUR",
            side=OrderSide.BUY,
            quantity=Decimal("0.001"),
            state=OrderState.CREATED,
        )
        ledger.add_order(order)

    # Try to create 3rd order
    new_order = Order(
        client_order_id="order_3",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    directive = runtime.evaluate_pre_order(new_order, order_ledger=ledger)

    assert directive.decision == RiskDecision.REJECT
    assert "exceeded" in directive.reason


def test_max_open_orders_terminal_orders_not_counted():
    """Test that terminal orders are not counted as open"""
    policy = MaxOpenOrdersPolicy(max_open_orders=2)
    runtime = RiskRuntime(policies=[policy])

    ledger = OrderLedger()

    # Add 5 FILLED orders (terminal, not open)
    for i in range(5):
        order = Order(
            client_order_id=f"filled_{i}",
            symbol="BTC-EUR",
            side=OrderSide.BUY,
            quantity=Decimal("0.001"),
            state=OrderState.FILLED,
        )
        ledger.add_order(order)

    # Add 1 CREATED order (open)
    open_order = Order(
        client_order_id="open_1",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
        state=OrderState.CREATED,
    )
    ledger.add_order(open_order)

    # Try to create another order (should allow, only 1 open)
    new_order = Order(
        client_order_id="new_order",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    directive = runtime.evaluate_pre_order(new_order, order_ledger=ledger)

    assert directive.decision == RiskDecision.ALLOW
