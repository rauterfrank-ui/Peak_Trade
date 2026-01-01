"""
Test: WP0D Reconciliation Summary & Observability (Phase 0)

Verifies:
- ReconSummary aggregates counts by severity and diff_type (deterministic)
- AuditLog emits RECON_SUMMARY + RECON_DIFF events
- Top-N diff selection is stable (deterministic ordering)
- No external APIs, SIM/PAPER only
"""

from decimal import Decimal
from datetime import datetime

import pytest

from src.execution.reconciliation import ReconciliationEngine, ExternalSnapshot
from src.execution.position_ledger import PositionLedger
from src.execution.order_ledger import OrderLedger
from src.execution.contracts import Fill, OrderSide, ReconSummary
from src.execution.audit_log import AuditLog


def test_recon_summary_counts_by_severity():
    """ReconSummary should correctly count diffs by severity"""

    # Create ledgers
    position_ledger = PositionLedger(initial_cash=Decimal("10000.00"))
    order_ledger = OrderLedger()

    # Add multiple positions (use larger quantities to exceed absolute tolerance)
    fills = [
        Fill(
            fill_id="fill_001",
            client_order_id="order_001",
            exchange_order_id="exch_001",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            quantity=Decimal("1.0"),  # Larger qty for absolute delta > 0.01
            price=Decimal("50000.00"),
            fee=Decimal("5.00"),
        ),
        Fill(
            fill_id="fill_002",
            client_order_id="order_002",
            exchange_order_id="exch_002",
            symbol="ETH/EUR",
            side=OrderSide.BUY,
            quantity=Decimal("10.0"),  # Larger qty for absolute delta > 0.01
            price=Decimal("3000.00"),
            fee=Decimal("3.00"),
        ),
    ]

    for fill in fills:
        position_ledger.apply_fill(fill)

    # Create recon engine
    recon_engine = ReconciliationEngine(
        position_ledger=position_ledger,
        order_ledger=order_ledger,
    )

    # Mock external snapshot with divergences
    # BTC: 5% drift (FAIL), ETH: 2% drift (FAIL)
    external_snapshot = ExternalSnapshot(
        timestamp=datetime.utcnow(),
        positions={
            "BTC/EUR": Decimal("0.95"),  # 5% less than internal (1.0), delta=0.05 > 0.01
            "ETH/EUR": Decimal("9.8"),  # 2% less than internal (10.0), delta=0.2 > 0.01
        },
        open_orders=[],
        fills=[],
        cash_balance=position_ledger.get_cash_balance(),  # No cash diff
    )

    # Reconcile
    diffs = recon_engine.reconcile(external_snapshot=external_snapshot)

    # Create summary
    summary = recon_engine.create_summary(
        diffs=diffs,
        session_id="test_session",
        strategy_id="test_strategy",
        top_n=10,
    )

    # Assertions
    assert isinstance(summary, ReconSummary)
    assert summary.total_diffs == 2
    assert summary.counts_by_severity["FAIL"] == 2  # BTC + ETH (both >1%)
    assert summary.counts_by_type["POSITION"] == 2
    assert summary.has_fail is True
    assert summary.has_critical is False
    assert summary.max_severity == "FAIL"
    assert summary.session_id == "test_session"
    assert summary.strategy_id == "test_strategy"


def test_recon_summary_top_n_deterministic_ordering():
    """Top-N diffs should be selected deterministically (severity, timestamp, diff_id)"""

    # Create ledgers
    position_ledger = PositionLedger(initial_cash=Decimal("10000.00"))
    order_ledger = OrderLedger()

    # Add 5 positions
    symbols = ["BTC/EUR", "ETH/EUR", "SOL/EUR", "ADA/EUR", "DOT/EUR"]
    for i, symbol in enumerate(symbols):
        fill = Fill(
            fill_id=f"fill_{i:03d}",
            client_order_id=f"order_{i:03d}",
            exchange_order_id=f"exch_{i:03d}",
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=Decimal("1.0"),
            price=Decimal("1000.00"),
            fee=Decimal("1.00"),
        )
        position_ledger.apply_fill(fill)

    # Create recon engine
    recon_engine = ReconciliationEngine(
        position_ledger=position_ledger,
        order_ledger=order_ledger,
    )

    # Mock external with divergences (varying severity)
    # Note: tolerance_abs = 0.01, so diffs must be > 0.01 to be detected
    external_snapshot = ExternalSnapshot(
        timestamp=datetime.utcnow(),
        positions={
            "BTC/EUR": Decimal("0.98"),  # 2% drift (FAIL)
            "ETH/EUR": Decimal("0.985"),  # 1.5% drift (FAIL)
            "SOL/EUR": Decimal("0.988"),  # 1.2% drift (FAIL)
            "ADA/EUR": Decimal("0.90"),  # 10% drift (FAIL)
            "DOT/EUR": Decimal("0.992"),  # 0.8% drift (WARN)
        },
        open_orders=[],
        fills=[],
        cash_balance=position_ledger.get_cash_balance(),
    )

    # Reconcile
    diffs = recon_engine.reconcile(external_snapshot=external_snapshot)

    # Create summary (top_n=3)
    summary1 = recon_engine.create_summary(diffs=diffs, top_n=3)
    summary2 = recon_engine.create_summary(diffs=diffs, top_n=3)

    # Top-N should be deterministic (same every time)
    assert len(summary1.top_diffs) == 3
    assert len(summary2.top_diffs) == 3

    # Extract diff_ids
    top_ids_1 = [d.diff_id for d in summary1.top_diffs]
    top_ids_2 = [d.diff_id for d in summary2.top_diffs]

    assert top_ids_1 == top_ids_2  # Deterministic ordering

    # All top-3 should be FAIL (sorted by severity first)
    assert summary1.top_diffs[0].severity == "FAIL"
    assert summary1.top_diffs[1].severity == "FAIL"
    assert summary1.top_diffs[2].severity == "FAIL"


def test_recon_summary_empty_diffs():
    """ReconSummary should handle empty diffs list"""

    # Create ledgers
    position_ledger = PositionLedger(initial_cash=Decimal("10000.00"))
    order_ledger = OrderLedger()

    # Create recon engine
    recon_engine = ReconciliationEngine(
        position_ledger=position_ledger,
        order_ledger=order_ledger,
    )

    # Reconcile with empty/matching external snapshot
    diffs = recon_engine.reconcile()  # Uses mock (no diffs)

    # Create summary
    summary = recon_engine.create_summary(diffs=diffs)

    # Assertions
    assert summary.total_diffs == 0
    assert summary.counts_by_severity == {}
    assert summary.counts_by_type == {}
    assert summary.top_diffs == []
    assert summary.has_fail is False
    assert summary.has_critical is False
    assert summary.max_severity == "INFO"


def test_audit_log_recon_summary_emission():
    """AuditLog should emit RECON_SUMMARY + RECON_DIFF events"""

    # Create ledgers
    position_ledger = PositionLedger(initial_cash=Decimal("10000.00"))
    order_ledger = OrderLedger()

    # Add position with divergence (use larger qty for absolute delta > 0.01)
    fill = Fill(
        fill_id="fill_001",
        client_order_id="order_001",
        exchange_order_id="exch_001",
        symbol="BTC/EUR",
        side=OrderSide.BUY,
        quantity=Decimal("1.0"),  # Larger qty
        price=Decimal("50000.00"),
        fee=Decimal("5.00"),
    )
    position_ledger.apply_fill(fill)

    # Create recon engine
    recon_engine = ReconciliationEngine(
        position_ledger=position_ledger,
        order_ledger=order_ledger,
    )

    # Mock external with divergence (5% drift, delta=0.05 > 0.01)
    external_snapshot = ExternalSnapshot(
        timestamp=datetime.utcnow(),
        positions={"BTC/EUR": Decimal("0.95")},  # 5% drift, delta=0.05
        open_orders=[],
        fills=[],
        cash_balance=position_ledger.get_cash_balance(),
    )

    # Reconcile
    diffs = recon_engine.reconcile(external_snapshot=external_snapshot)

    # Create summary
    summary = recon_engine.create_summary(diffs=diffs, top_n=5)

    # Emit to audit log
    audit_log = AuditLog()
    audit_log.append_recon_summary(summary)

    # Assertions
    all_entries = audit_log.get_all_entries()

    # Should have 1 RECON_SUMMARY + 1 RECON_DIFF (top-N)
    assert len(all_entries) == 2

    summary_entry = all_entries[0]
    diff_entry = all_entries[1]

    # Check summary entry
    assert summary_entry.event_type == "RECON_SUMMARY"
    assert summary_entry.details["run_id"] == summary.run_id
    assert summary_entry.details["total_diffs"] == 1
    assert summary_entry.details["has_fail"] is True

    # Check diff entry
    assert diff_entry.event_type == "RECON_DIFF"
    assert diff_entry.details["run_id"] == summary.run_id
    assert diff_entry.details["diff_type"] == "POSITION"
    assert diff_entry.details["severity"] == "FAIL"


def test_audit_log_recon_summary_multiple_diffs():
    """AuditLog should emit top-N diffs as individual entries"""

    # Create ledgers
    position_ledger = PositionLedger(initial_cash=Decimal("10000.00"))
    order_ledger = OrderLedger()

    # Add 3 positions
    for i, symbol in enumerate(["BTC/EUR", "ETH/EUR", "SOL/EUR"]):
        fill = Fill(
            fill_id=f"fill_{i}",
            client_order_id=f"order_{i}",
            exchange_order_id=f"exch_{i}",
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=Decimal("1.0"),
            price=Decimal("1000.00"),
            fee=Decimal("1.00"),
        )
        position_ledger.apply_fill(fill)

    # Create recon engine
    recon_engine = ReconciliationEngine(
        position_ledger=position_ledger,
        order_ledger=order_ledger,
    )

    # Mock external with divergences (all > 1% for FAIL)
    external_snapshot = ExternalSnapshot(
        timestamp=datetime.utcnow(),
        positions={
            "BTC/EUR": Decimal("0.98"),  # 2% drift (FAIL)
            "ETH/EUR": Decimal("0.985"),  # 1.5% drift (FAIL)
            "SOL/EUR": Decimal("0.90"),  # 10% drift (FAIL)
        },
        open_orders=[],
        fills=[],
        cash_balance=position_ledger.get_cash_balance(),
    )

    # Reconcile
    diffs = recon_engine.reconcile(external_snapshot=external_snapshot)

    # Create summary (top_n=2)
    summary = recon_engine.create_summary(diffs=diffs, top_n=2)

    # Emit to audit log
    audit_log = AuditLog()
    audit_log.append_recon_summary(summary)

    # Assertions
    all_entries = audit_log.get_all_entries()

    # Should have 1 RECON_SUMMARY + 2 RECON_DIFF (top_n=2)
    assert len(all_entries) == 3

    summary_entry = all_entries[0]
    assert summary_entry.event_type == "RECON_SUMMARY"

    diff_entries = all_entries[1:]
    assert all(e.event_type == "RECON_DIFF" for e in diff_entries)

    # All diffs should reference same run_id
    run_ids = {e.details["run_id"] for e in all_entries}
    assert len(run_ids) == 1
    assert run_ids.pop() == summary.run_id


def test_recon_summary_to_dict_deterministic():
    """ReconSummary.to_dict() should be deterministic (stable field ordering)"""

    # Create minimal summary
    position_ledger = PositionLedger(initial_cash=Decimal("10000.00"))
    order_ledger = OrderLedger()

    recon_engine = ReconciliationEngine(
        position_ledger=position_ledger,
        order_ledger=order_ledger,
    )

    diffs = recon_engine.reconcile()
    summary = recon_engine.create_summary(diffs=diffs)

    # Convert to dict multiple times
    dict1 = summary.to_dict()
    dict2 = summary.to_dict()

    # Should be identical
    assert dict1 == dict2

    # Keys should be sorted (deterministic)
    assert list(dict1["counts_by_severity"].keys()) == sorted(dict1["counts_by_severity"].keys())
    assert list(dict1["counts_by_type"].keys()) == sorted(dict1["counts_by_type"].keys())


def test_recon_summary_to_json_deterministic():
    """ReconSummary.to_json() should be deterministic (stable JSON output)"""

    # Create minimal summary
    position_ledger = PositionLedger(initial_cash=Decimal("10000.00"))
    order_ledger = OrderLedger()

    recon_engine = ReconciliationEngine(
        position_ledger=position_ledger,
        order_ledger=order_ledger,
    )

    diffs = recon_engine.reconcile()
    summary = recon_engine.create_summary(diffs=diffs)

    # Convert to JSON multiple times
    json1 = summary.to_json()
    json2 = summary.to_json()

    # Should be identical
    assert json1 == json2

    # JSON should be valid
    import json

    parsed = json.loads(json1)
    assert "run_id" in parsed
    assert "total_diffs" in parsed
    assert "counts_by_severity" in parsed
