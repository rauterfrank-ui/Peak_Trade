"""
WP0B Tests - RuntimeRiskHook Adapter
"""

from decimal import Decimal

import pytest

from src.execution.contracts import Order, OrderSide, RiskDecision
from src.execution.risk_runtime import NoopPolicy, MaxOpenOrdersPolicy, RiskRuntime
from src.execution.risk_hook_impl import RuntimeRiskHook, create_runtime_risk_hook
from src.execution.order_ledger import OrderLedger
from src.execution.position_ledger import PositionLedger


def test_runtime_risk_hook_evaluate_order_allow():
    """Test RuntimeRiskHook.evaluate_order() with ALLOW"""
    runtime = RiskRuntime(policies=[NoopPolicy()])
    hook = RuntimeRiskHook(runtime)

    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    result = hook.evaluate_order(order)

    assert result.decision == RiskDecision.ALLOW
    assert result.reason != ""


def test_runtime_risk_hook_evaluate_order_block():
    """Test RuntimeRiskHook.evaluate_order() with BLOCK"""
    policy = MaxOpenOrdersPolicy(max_open_orders=0)  # Always reject
    runtime = RiskRuntime(policies=[policy])
    hook = RuntimeRiskHook(runtime)

    order = Order(
        client_order_id="test_002",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    result = hook.evaluate_order(order)

    assert result.decision == RiskDecision.BLOCK
    assert "exceeded" in result.reason


def test_runtime_risk_hook_check_kill_switch():
    """Test RuntimeRiskHook.check_kill_switch()"""
    runtime = RiskRuntime(policies=[NoopPolicy()])
    hook = RuntimeRiskHook(runtime)

    result = hook.check_kill_switch()

    # Phase 0: No kill switch implementation
    assert result.decision == RiskDecision.ALLOW
    assert "not implemented" in result.reason


def test_runtime_risk_hook_evaluate_position_change():
    """Test RuntimeRiskHook.evaluate_position_change()"""
    runtime = RiskRuntime(policies=[NoopPolicy()])
    hook = RuntimeRiskHook(runtime)

    result = hook.evaluate_position_change(
        symbol="BTC-EUR",
        quantity=Decimal("0.001"),
        side="BUY",
    )

    assert result.decision == RiskDecision.ALLOW


def test_runtime_risk_hook_with_ledgers():
    """Test RuntimeRiskHook with OrderLedger and PositionLedger"""
    order_ledger = OrderLedger()
    position_ledger = PositionLedger(initial_cash=Decimal("10000"))

    policy = MaxOpenOrdersPolicy(max_open_orders=5)
    runtime = RiskRuntime(policies=[policy])
    hook = RuntimeRiskHook(runtime, order_ledger, position_ledger)

    # Add 4 orders to ledger
    for i in range(4):
        order = Order(
            client_order_id=f"order_{i}",
            symbol="BTC-EUR",
            side=OrderSide.BUY,
            quantity=Decimal("0.001"),
        )
        order_ledger.add_order(order)

    # Evaluate 5th order (should allow, within limit)
    new_order = Order(
        client_order_id="order_5",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    result = hook.evaluate_order(new_order)

    assert result.decision == RiskDecision.ALLOW


def test_runtime_risk_hook_factory():
    """Test create_runtime_risk_hook() factory"""
    policies = [NoopPolicy(), MaxOpenOrdersPolicy(10)]
    hook = create_runtime_risk_hook(policies)

    assert isinstance(hook, RuntimeRiskHook)

    order = Order(
        client_order_id="test_factory",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    result = hook.evaluate_order(order)
    assert result.decision == RiskDecision.ALLOW


def test_runtime_risk_hook_integrates_with_osm():
    """Test RuntimeRiskHook integration with OrderStateMachine"""
    from src.execution.order_state_machine import OrderStateMachine

    # Create hook with policy that always allows
    policy = MaxOpenOrdersPolicy(max_open_orders=100)
    hook = create_runtime_risk_hook([policy])

    # Create OSM with hook
    osm = OrderStateMachine(risk_hook=hook)

    # Create and submit order
    result = osm.create_order(
        client_order_id="osm_test_001",
        symbol="BTC-EUR",
        side="BUY",
        quantity=Decimal("0.001"),
    )

    assert result.success
    order = result.order

    # Submit order (should call risk hook)
    result = osm.submit_order(order)

    assert result.success
    assert order.state.value == "SUBMITTED"


def test_runtime_risk_hook_blocks_osm_submission():
    """Test RuntimeRiskHook blocking OSM submission"""
    from src.execution.order_state_machine import OrderStateMachine

    # Create hook with policy that always rejects
    policy = MaxOpenOrdersPolicy(max_open_orders=0)
    hook = create_runtime_risk_hook([policy])

    # Create OSM with hook
    osm = OrderStateMachine(risk_hook=hook)

    # Create order
    result = osm.create_order(
        client_order_id="osm_test_002",
        symbol="BTC-EUR",
        side="BUY",
        quantity=Decimal("0.001"),
    )

    order = result.order

    # Try to submit order (should be blocked)
    result = osm.submit_order(order)

    assert not result.success
    assert "blocked" in result.message.lower() or "risk" in result.message.lower()
    assert order.state.value == "CREATED"  # Still in CREATED (not submitted)
