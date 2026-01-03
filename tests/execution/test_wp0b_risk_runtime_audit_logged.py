"""
WP0B Tests - Audit Logging
"""

from decimal import Decimal

import pytest

from src.execution.contracts import Order, OrderSide, Fill
from src.execution.risk_runtime import (
    NoopPolicy,
    MaxOpenOrdersPolicy,
    RiskRuntime,
)
from src.execution.audit_log import AuditLog


def test_runtime_logs_allow_decision():
    """Test that ALLOW decisions are logged"""
    audit = AuditLog()
    runtime = RiskRuntime(policies=[NoopPolicy()], audit_log=audit)

    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    runtime.evaluate_pre_order(order)

    assert audit.get_entry_count() == 1

    entries = audit.get_entries_for_order("test_001")
    assert len(entries) == 1
    assert entries[0].event_type == "RISK_PRE_ORDER"


def test_runtime_logs_reject_decision():
    """Test that REJECT decisions are logged"""
    audit = AuditLog()
    policy = MaxOpenOrdersPolicy(max_open_orders=0)  # Always reject
    runtime = RiskRuntime(policies=[policy], audit_log=audit)

    order = Order(
        client_order_id="test_002",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    directive = runtime.evaluate_pre_order(order)

    assert directive.decision.value == "REJECT"
    assert audit.get_entry_count() == 1

    entries = audit.get_entries_for_order("test_002")
    assert len(entries) == 1
    assert "REJECT" in entries[0].details.get("decision", "")


def test_runtime_logs_pre_fill():
    """Test that pre-fill evaluations are logged"""
    audit = AuditLog()
    runtime = RiskRuntime(policies=[NoopPolicy()], audit_log=audit)

    fill = Fill(
        fill_id="fill_001",
        client_order_id="order_001",
        exchange_order_id="exch_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
        price=Decimal("50000"),
    )

    runtime.evaluate_pre_fill(fill)

    assert audit.get_entry_count() == 1

    entries = audit.get_entries_for_order("order_001")
    assert len(entries) == 1
    assert entries[0].event_type == "RISK_PRE_FILL"


def test_runtime_logs_post_fill():
    """Test that post-fill evaluations are logged"""
    audit = AuditLog()
    runtime = RiskRuntime(policies=[NoopPolicy()], audit_log=audit)

    fill = Fill(
        fill_id="fill_002",
        client_order_id="order_002",
        exchange_order_id="exch_002",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
        price=Decimal("50000"),
    )

    runtime.evaluate_post_fill(fill)

    assert audit.get_entry_count() == 1

    entries = audit.get_entries_for_order("order_002")
    assert len(entries) == 1
    assert entries[0].event_type == "RISK_POST_FILL"


def test_runtime_multiple_evaluations_all_logged():
    """Test that multiple evaluations are all logged"""
    audit = AuditLog()
    runtime = RiskRuntime(policies=[NoopPolicy()], audit_log=audit)

    # Evaluate 3 orders
    for i in range(3):
        order = Order(
            client_order_id=f"order_{i}",
            symbol="BTC-EUR",
            side=OrderSide.BUY,
            quantity=Decimal("0.001"),
        )
        runtime.evaluate_pre_order(order)

    assert audit.get_entry_count() == 3

    # Each order should have 1 entry
    for i in range(3):
        entries = audit.get_entries_for_order(f"order_{i}")
        assert len(entries) == 1


def test_audit_entries_contain_decision_details():
    """Test that audit entries contain decision details"""
    audit = AuditLog()
    policy = MaxOpenOrdersPolicy(max_open_orders=5)
    runtime = RiskRuntime(policies=[policy], audit_log=audit)

    order = Order(
        client_order_id="test_003",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    runtime.evaluate_pre_order(order)

    entries = audit.get_entries_for_order("test_003")
    assert len(entries) == 1

    entry = entries[0]
    assert "decision" in entry.details
    assert "reason" in entry.details
    assert entry.details["decision"] == "ALLOW"
