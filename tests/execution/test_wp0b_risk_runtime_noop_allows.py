"""
WP0B Tests - Noop Policy (always allows)
"""

from decimal import Decimal

import pytest

from src.execution.contracts import Order, OrderSide
from src.execution.risk_runtime import (
    NoopPolicy,
    RiskRuntime,
    RiskDecision,
    build_empty_snapshot,
)
from src.execution.audit_log import AuditLog


def test_noop_policy_allows_everything():
    """Test that NoopPolicy always allows"""
    policy = NoopPolicy()
    snapshot = build_empty_snapshot()

    directive = policy.evaluate(snapshot)

    assert directive.decision == RiskDecision.ALLOW
    assert "NoopPolicy" in directive.reason


def test_noop_policy_with_order():
    """Test NoopPolicy with actual order"""
    policy = NoopPolicy()

    from src.execution.risk_runtime.context import RiskContextSnapshot

    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    snapshot = RiskContextSnapshot(order=order)
    directive = policy.evaluate(snapshot)

    assert directive.decision == RiskDecision.ALLOW


def test_runtime_with_noop_policy():
    """Test RiskRuntime with NoopPolicy"""
    audit = AuditLog()
    runtime = RiskRuntime(policies=[NoopPolicy()], audit_log=audit)

    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    directive = runtime.evaluate_pre_order(order)

    assert directive.decision == RiskDecision.ALLOW
    assert audit.get_entry_count() == 1  # Decision logged


def test_runtime_no_policies_allows():
    """Test RiskRuntime with no policies (default ALLOW)"""
    runtime = RiskRuntime(policies=[])

    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    directive = runtime.evaluate_pre_order(order)

    assert directive.decision == RiskDecision.ALLOW
    assert "No policies" in directive.reason
