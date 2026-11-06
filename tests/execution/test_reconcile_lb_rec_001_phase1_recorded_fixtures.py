"""
LB-REC-001 — recorded JSON fixtures for ReconciliationEngine (phase 1+2+3+4+5+6+7).

Loads repo-stable cases from tests/fixtures/reconciliation/lb_rec_001_phase1/.
Mock-only, deterministic, no network. Reduces LB-REC-001 harness coverage;
does not close live readiness or imply live-approved reconciliation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from src.execution.contracts import Fill, OrderSide
from src.execution.order_ledger import OrderLedger
from src.execution.position_ledger import PositionLedger
from src.execution.reconciliation import ExternalSnapshot, ReconciliationEngine

FIXTURE_DIR = (
    Path(__file__).resolve().parents[1] / "fixtures" / "reconciliation" / "lb_rec_001_phase1"
)


def _parse_as_of(raw: str) -> datetime:
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _side(name: str) -> OrderSide:
    return OrderSide[name.upper()]


def _apply_fill_spec(pl: PositionLedger, f: dict) -> None:
    pl.apply_fill(
        Fill(
            fill_id=f["fill_id"],
            client_order_id=f["client_order_id"],
            exchange_order_id=f["exchange_order_id"],
            symbol=f["symbol"],
            side=_side(f["side"]),
            quantity=Decimal(f["quantity"]),
            price=Decimal(f["price"]),
            fee=Decimal(f.get("fee", "0")),
        )
    )


def _engine_from_case(data: dict) -> tuple[ReconciliationEngine, datetime]:
    assert data.get("schema") == "lb_rec_001_phase1_v1"
    as_of = _parse_as_of(data["as_of_time"])
    inn = data["internal"]
    pl = PositionLedger(initial_cash=Decimal(inn["initial_cash"]))
    ol = OrderLedger()
    fills_spec = inn.get("fills")
    if fills_spec is not None:
        for f in fills_spec:
            _apply_fill_spec(pl, f)
    else:
        _apply_fill_spec(pl, inn["fill"])
    return ReconciliationEngine(position_ledger=pl, order_ledger=ol), as_of


def _external_snapshot(
    eng: ReconciliationEngine,
    ext: dict,
    as_of: datetime,
) -> ExternalSnapshot:
    cash_spec = ext["cash_balance"]
    if cash_spec["mode"] == "match_internal":
        cash = eng.position_ledger.get_cash_balance()
    elif cash_spec["mode"] == "fixed":
        cash = Decimal(cash_spec["value"])
    else:
        raise ValueError(f"unknown cash_balance mode: {cash_spec!r}")

    positions = {k: Decimal(v) for k, v in ext["positions"].items()}
    return ExternalSnapshot(
        timestamp=as_of,
        positions=positions,
        open_orders=[],
        fills=[],
        cash_balance=cash,
    )


@pytest.mark.parametrize(
    "fixture_path",
    sorted(FIXTURE_DIR.glob("case_*.json")),
    ids=lambda p: p.stem,
)
def test_lb_rec_001_phase1_recorded_fixture_contract(fixture_path: Path) -> None:
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    eng, as_of = _engine_from_case(raw)
    snap = _external_snapshot(eng, raw["external"], as_of)
    diffs = eng.reconcile(external_snapshot=snap, as_of_time=as_of)

    exp = raw["expect"]
    assert len(diffs) == exp["diff_count"]
    fail_n = sum(1 for d in diffs if d.severity == "FAIL")
    assert fail_n >= exp["min_fail"]
    if "min_warn" in exp:
        warn_n = sum(1 for d in diffs if d.severity == "WARN")
        assert warn_n >= exp["min_warn"]
    if "min_info" in exp:
        info_n = sum(1 for d in diffs if d.severity == "INFO")
        assert info_n >= exp["min_info"]

    if "all_diff_types" in exp:
        assert [d.diff_type for d in diffs] == exp["all_diff_types"]
    if "first_diff_type" in exp:
        assert diffs[0].diff_type == exp["first_diff_type"]
    if "first_severity" in exp:
        assert diffs[0].severity == exp["first_severity"]


def test_lb_rec_001_phase1_fixture_dir_has_cases() -> None:
    cases = list(FIXTURE_DIR.glob("case_*.json"))
    assert len(cases) >= 13, "expected at least thirteen recorded cases (phase 1–6 + phase 7 slice)"
