"""
LB-REC-001 — deterministischer Reconciliation-Harness (Phase 0, mock-only).

Fest codierte Fixture-Sätze (interner Ledger + ExternalSnapshot) mit fester
`as_of_time` für reproduzierbare ReconDiff-Ergebnisse. Kein Netzwerk, kein
Exchange-API — ersetzt keine operative Live-Parität und begründet kein
live-approved (vgl. Audit: LB-REC-001 reduziert, schließt Live Readiness nicht).
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from src.execution.contracts import Fill, OrderSide
from src.execution.order_ledger import OrderLedger
from src.execution.position_ledger import PositionLedger
from src.execution.reconciliation import ExternalSnapshot, ReconciliationEngine

# Fixed clock: deterministic diff_id suffixes and ordering
AS_OF = datetime(2026, 4, 8, 12, 0, 0, tzinfo=timezone.utc)


def _engine_with_btc_position(qty: Decimal) -> ReconciliationEngine:
    pl = PositionLedger(initial_cash=Decimal("100000.00"))
    ol = OrderLedger()
    pl.apply_fill(
        Fill(
            fill_id="lbrec_fill_1",
            client_order_id="lbrec_co_1",
            exchange_order_id="lbrec_ex_1",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            quantity=qty,
            price=Decimal("50000.00"),
            fee=Decimal("5.00"),
        )
    )
    return ReconciliationEngine(position_ledger=pl, order_ledger=ol)


@pytest.mark.parametrize(
    "internal_qty,external_qty,expected_diffs,min_fail",
    [
        # Aligned within tolerance
        (Decimal("1.0"), Decimal("1.0"), 0, 0),
        # ~5 % drift on 1.0 base → FAIL path
        (Decimal("1.0"), Decimal("0.94"), 1, 1),
    ],
)
def test_lb_rec_001_position_snapshot_contract(
    internal_qty: Decimal,
    external_qty: Decimal,
    expected_diffs: int,
    min_fail: int,
) -> None:
    eng = _engine_with_btc_position(internal_qty)
    snap = ExternalSnapshot(
        timestamp=AS_OF,
        positions={"BTC/EUR": external_qty},
        open_orders=[],
        fills=[],
        cash_balance=eng.position_ledger.get_cash_balance(),
    )
    diffs = eng.reconcile(external_snapshot=snap, as_of_time=AS_OF)
    assert len(diffs) == expected_diffs
    fail_n = sum(1 for d in diffs if d.severity == "FAIL")
    assert fail_n >= min_fail
    if diffs:
        assert all(d.diff_type == "POSITION" for d in diffs)


def test_lb_rec_001_cash_mismatch_contract() -> None:
    eng = _engine_with_btc_position(Decimal("0.5"))
    snap = ExternalSnapshot(
        timestamp=AS_OF,
        positions={"BTC/EUR": Decimal("0.5")},
        open_orders=[],
        fills=[],
        # Must exceed cash tolerance (max(1.0, |external| * 0.5 %)); near-miss can be absorbed.
        cash_balance=Decimal("0"),
    )
    diffs = eng.reconcile(external_snapshot=snap, as_of_time=AS_OF)
    assert len(diffs) == 1
    assert diffs[0].diff_type == "CASH"
    assert diffs[0].severity == "FAIL"


def test_lb_rec_001_summary_contract_stable_ordering() -> None:
    """create_summary ordering is deterministic for identical inputs (severity / time / id)."""
    eng = _engine_with_btc_position(Decimal("1.0"))
    snap = ExternalSnapshot(
        timestamp=AS_OF,
        positions={"BTC/EUR": Decimal("0.90")},
        open_orders=[],
        fills=[],
        cash_balance=eng.position_ledger.get_cash_balance(),
    )
    diffs = eng.reconcile(external_snapshot=snap, as_of_time=AS_OF)
    s1 = eng.create_summary(diffs, session_id="s", strategy_id="z", top_n=5)
    s2 = eng.create_summary(diffs, session_id="s", strategy_id="z", top_n=5)
    assert s1.total_diffs == s2.total_diffs == 1
    assert s1.max_severity == s2.max_severity == "FAIL"
    assert [d.diff_id for d in s1.top_diffs] == [d.diff_id for d in s2.top_diffs]
