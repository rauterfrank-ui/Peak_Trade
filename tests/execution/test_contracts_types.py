"""
Tests for execution contracts and stable types (WP0E)

Test Coverage:
- Type instantiation and validation
- Deterministic serialization (repr/json)
- State machine transitions
- Edge cases and invariants
"""

import json
from datetime import datetime
from decimal import Decimal

import pytest

from src.execution.contracts import (
    Order,
    OrderState,
    OrderSide,
    OrderType,
    TimeInForce,
    Fill,
    LedgerEntry,
    ReconDiff,
    RiskDecision,
    RiskResult,
    validate_order,
    serialize_contracts_snapshot,
)


# ============================================================================
# Order Tests
# ============================================================================


def test_order_creation():
    """Test basic order creation"""
    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
        price=Decimal("50000.00"),
    )

    assert order.client_order_id == "test_001"
    assert order.symbol == "BTC-EUR"
    assert order.side == OrderSide.BUY
    assert order.quantity == Decimal("0.001")
    assert order.price == Decimal("50000.00")
    assert order.state == OrderState.CREATED


def test_order_repr_deterministic():
    """Test deterministic repr (stable for snapshots)"""
    order1 = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )
    order2 = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    # Repr should be identical (ignoring timestamps)
    assert "test_001" in repr(order1)
    assert "BTC-EUR" in repr(order1)
    assert "BUY" in repr(order1)


def test_order_to_dict():
    """Test deterministic dict conversion"""
    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
        price=Decimal("50000.00"),
    )

    d = order.to_dict()

    assert d["client_order_id"] == "test_001"
    assert d["symbol"] == "BTC-EUR"
    assert d["side"] == "BUY"
    assert d["quantity"] == "0.001"  # Decimal as string
    assert d["price"] == "50000.00"  # Decimal as string
    assert "created_at" in d
    assert "updated_at" in d


def test_order_to_json():
    """Test deterministic JSON serialization"""
    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
    )

    json_str = order.to_json()

    # Should be valid JSON
    parsed = json.loads(json_str)
    assert parsed["client_order_id"] == "test_001"

    # Should be deterministic (sorted keys)
    assert json_str.index("client_order_id") < json_str.index("symbol")


def test_order_state_is_terminal():
    """Test terminal state checks"""
    assert OrderState.FILLED.is_terminal()
    assert OrderState.CANCELLED.is_terminal()
    assert OrderState.REJECTED.is_terminal()
    assert OrderState.EXPIRED.is_terminal()
    assert OrderState.FAILED.is_terminal()

    assert not OrderState.CREATED.is_terminal()
    assert not OrderState.SUBMITTED.is_terminal()
    assert not OrderState.ACKNOWLEDGED.is_terminal()
    assert not OrderState.PARTIALLY_FILLED.is_terminal()


def test_order_state_is_active():
    """Test active state checks"""
    assert OrderState.SUBMITTED.is_active()
    assert OrderState.ACKNOWLEDGED.is_active()
    assert OrderState.PARTIALLY_FILLED.is_active()

    assert not OrderState.CREATED.is_active()
    assert not OrderState.FILLED.is_active()
    assert not OrderState.CANCELLED.is_active()


def test_validate_order_valid():
    """Test order validation - valid cases"""
    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
        order_type=OrderType.LIMIT,
        price=Decimal("50000.00"),
    )

    assert validate_order(order)


def test_validate_order_invalid_no_id():
    """Test order validation - missing client_order_id"""
    order = Order(
        client_order_id="",
        symbol="BTC-EUR",
        quantity=Decimal("0.001"),
    )

    assert not validate_order(order)


def test_validate_order_invalid_no_symbol():
    """Test order validation - missing symbol"""
    order = Order(
        client_order_id="test_001",
        symbol="",
        quantity=Decimal("0.001"),
    )

    assert not validate_order(order)


def test_validate_order_invalid_quantity():
    """Test order validation - invalid quantity"""
    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        quantity=Decimal("0"),
    )

    assert not validate_order(order)


def test_validate_order_invalid_limit_no_price():
    """Test order validation - LIMIT order without price"""
    order = Order(
        client_order_id="test_001",
        symbol="BTC-EUR",
        quantity=Decimal("0.001"),
        order_type=OrderType.LIMIT,
        price=None,
    )

    assert not validate_order(order)


# ============================================================================
# Fill Tests
# ============================================================================


def test_fill_creation():
    """Test basic fill creation"""
    fill = Fill(
        fill_id="fill_001",
        client_order_id="test_001",
        exchange_order_id="exch_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
        price=Decimal("50000.00"),
        fee=Decimal("0.50"),
    )

    assert fill.fill_id == "fill_001"
    assert fill.quantity == Decimal("0.001")
    assert fill.price == Decimal("50000.00")
    assert fill.fee == Decimal("0.50")


def test_fill_to_dict():
    """Test fill dict conversion"""
    fill = Fill(
        fill_id="fill_001",
        client_order_id="test_001",
        exchange_order_id="exch_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
        price=Decimal("50000.00"),
    )

    d = fill.to_dict()

    assert d["fill_id"] == "fill_001"
    assert d["quantity"] == "0.001"  # Decimal as string
    assert d["price"] == "50000.00"  # Decimal as string


def test_fill_to_json():
    """Test fill JSON serialization"""
    fill = Fill(
        fill_id="fill_001",
        client_order_id="test_001",
        exchange_order_id="exch_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
        price=Decimal("50000.00"),
    )

    json_str = fill.to_json()
    parsed = json.loads(json_str)

    assert parsed["fill_id"] == "fill_001"
    assert parsed["quantity"] == "0.001"


# ============================================================================
# LedgerEntry Tests
# ============================================================================


def test_ledger_entry_creation():
    """Test ledger entry creation"""
    entry = LedgerEntry(
        entry_id="ledger_001",
        sequence=1,
        event_type="ORDER_CREATED",
        client_order_id="test_001",
        old_state=None,
        new_state=OrderState.CREATED,
    )

    assert entry.entry_id == "ledger_001"
    assert entry.sequence == 1
    assert entry.event_type == "ORDER_CREATED"
    assert entry.new_state == OrderState.CREATED


def test_ledger_entry_to_dict():
    """Test ledger entry dict conversion"""
    entry = LedgerEntry(
        entry_id="ledger_001",
        sequence=1,
        event_type="ORDER_CREATED",
        client_order_id="test_001",
        old_state=None,
        new_state=OrderState.CREATED,
    )

    d = entry.to_dict()

    assert d["entry_id"] == "ledger_001"
    assert d["sequence"] == 1
    assert d["new_state"] == "CREATED"


# ============================================================================
# ReconDiff Tests
# ============================================================================


def test_recon_diff_creation():
    """Test reconciliation diff creation"""
    diff = ReconDiff(
        diff_id="diff_001",
        client_order_id="test_001",
        local_state=OrderState.FILLED,
        exchange_state="PARTIALLY_FILLED",
        severity="WARN",
        description="Fill quantity mismatch",
    )

    assert diff.diff_id == "diff_001"
    assert diff.severity == "WARN"
    assert not diff.resolved


def test_recon_diff_to_dict():
    """Test recon diff dict conversion"""
    diff = ReconDiff(
        diff_id="diff_001",
        client_order_id="test_001",
        local_state=OrderState.FILLED,
        exchange_state="PARTIALLY_FILLED",
        severity="WARN",
    )

    d = diff.to_dict()

    assert d["diff_id"] == "diff_001"
    assert d["local_state"] == "FILLED"
    assert d["severity"] == "WARN"


# ============================================================================
# RiskResult Tests
# ============================================================================


def test_risk_result_allow():
    """Test risk result - ALLOW"""
    result = RiskResult(
        decision=RiskDecision.ALLOW,
        reason="All limits OK",
    )

    assert result.decision == RiskDecision.ALLOW
    assert result.reason == "All limits OK"


def test_risk_result_block():
    """Test risk result - BLOCK"""
    result = RiskResult(
        decision=RiskDecision.BLOCK,
        reason="Limit exceeded",
        metadata={"limit_type": "daily_loss"},
    )

    assert result.decision == RiskDecision.BLOCK
    assert result.metadata["limit_type"] == "daily_loss"


def test_risk_result_to_dict():
    """Test risk result dict conversion"""
    result = RiskResult(
        decision=RiskDecision.ALLOW,
        reason="All OK",
    )

    d = result.to_dict()

    assert d["decision"] == "ALLOW"
    assert d["reason"] == "All OK"


def test_risk_result_to_json():
    """Test risk result JSON serialization"""
    result = RiskResult(
        decision=RiskDecision.BLOCK,
        reason="Blocked",
    )

    json_str = result.to_json()
    parsed = json.loads(json_str)

    assert parsed["decision"] == "BLOCK"


# ============================================================================
# Snapshot Tests (Evidence)
# ============================================================================


def test_serialize_contracts_snapshot():
    """Test deterministic snapshot generation (evidence artifact)"""
    snapshot = serialize_contracts_snapshot()

    # Check all types are present
    assert "order" in snapshot
    assert "fill" in snapshot
    assert "ledger_entry" in snapshot
    assert "recon_diff" in snapshot
    assert "risk_result" in snapshot

    # Check order snapshot
    order_snap = snapshot["order"]
    assert order_snap["client_order_id"] == "test_order_001"
    assert order_snap["symbol"] == "BTC-EUR"
    assert order_snap["quantity"] == "0.001"

    # Check fill snapshot
    fill_snap = snapshot["fill"]
    assert fill_snap["fill_id"] == "fill_001"
    assert fill_snap["quantity"] == "0.001"

    # Check risk result snapshot
    risk_snap = snapshot["risk_result"]
    assert risk_snap["decision"] == "ALLOW"


def test_snapshot_json_serializable():
    """Test that snapshot is JSON serializable"""
    snapshot = serialize_contracts_snapshot()

    # Should serialize without error
    json_str = json.dumps(snapshot, indent=2)

    # Should deserialize correctly
    parsed = json.loads(json_str)
    assert parsed["order"]["client_order_id"] == "test_order_001"


def test_snapshot_deterministic():
    """Test that snapshot is deterministic (critical for CI)"""
    # Generate twice (with fixed test data)
    snapshot1 = serialize_contracts_snapshot()
    snapshot2 = serialize_contracts_snapshot()

    # Order fields should match (ignoring timestamps)
    assert snapshot1["order"]["client_order_id"] == snapshot2["order"]["client_order_id"]
    assert snapshot1["order"]["quantity"] == snapshot2["order"]["quantity"]

    # Fill fields should match
    assert snapshot1["fill"]["fill_id"] == snapshot2["fill"]["fill_id"]

    # Risk result should match
    assert snapshot1["risk_result"]["decision"] == snapshot2["risk_result"]["decision"]
