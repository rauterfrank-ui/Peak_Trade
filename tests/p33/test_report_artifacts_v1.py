"""Contract tests for P33 report artifacts v1."""

from __future__ import annotations

import json

import pytest

from src.backtest.p29.accounting_v2 import PositionCashStateV2
from src.backtest.p32.report_v1 import BacktestReportV1
from src.backtest.p33 import ArtifactSchemaError, report_from_dict, report_to_dict
from src.execution.p26.adapter import FillRecord


def _mk_report() -> BacktestReportV1:
    fills = [
        FillRecord(order_id="o1", side="BUY", qty=1.0, price=100.0, fee=0.1, symbol="MOCK"),
        FillRecord(order_id="o2", side="SELL", qty=0.5, price=110.0, fee=0.05, symbol="MOCK"),
    ]
    state = PositionCashStateV2(
        cash=1000.0,
        positions_qty={"MOCK": 0.5},
        avg_cost={"MOCK": 100.0},
        realized_pnl=5.0,
    )
    equity = [1000.0, 1010.0, 1005.0]
    metrics = {"total_return": 0.005, "max_drawdown": 0.004, "sharpe": 1.2, "n_steps": 3.0}
    return BacktestReportV1(fills=fills, state=state, equity=equity, metrics=metrics)


def test_to_dict_is_jsonable_only():
    d = report_to_dict(_mk_report())
    s = json.dumps(d, sort_keys=True)
    assert isinstance(s, str)
    assert d["schema_version"] == 1


def test_roundtrip_preserves_values():
    d = report_to_dict(_mk_report())
    dto = report_from_dict(d)
    assert dto.schema_version == 1
    assert len(dto.fills) == 2
    assert dto.state.cash == 1000.0
    assert dto.state.positions_qty["MOCK"] == 0.5
    assert dto.equity == [1000.0, 1010.0, 1005.0]
    assert dto.metrics["sharpe"] == 1.2


def test_schema_version_required_and_enforced():
    d = report_to_dict(_mk_report())
    d2 = dict(d)
    d2["schema_version"] = 999
    with pytest.raises(ArtifactSchemaError):
        report_from_dict(d2)


def test_reject_non_string_keys_in_maps():
    d = report_to_dict(_mk_report())
    d["state"] = dict(d["state"])  # type: ignore[arg-type]
    d["state"]["positions_qty"] = {1: 2.0}  # type: ignore[assignment]
    with pytest.raises(ArtifactSchemaError):
        report_from_dict(d)
