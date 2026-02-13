"""Tests for P35 report artifact bundle v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.backtest.p35.bundle_v1 import (
    BundleIntegrityError,
    read_report_bundle_v1,
    verify_report_bundle_v1,
    write_report_bundle_v1,
)


def _sample_report_dict() -> dict[str, Any]:
    try:
        from src.backtest.p33.report_artifacts_v1 import (
            BacktestReportV1DTO,
            FillRecordDTO,
            PositionCashStateV2DTO,
            report_to_dict,
        )

        dto = BacktestReportV1DTO(
            schema_version=1,
            fills=[
                FillRecordDTO(
                    order_id="o1",
                    side="BUY",
                    qty=1.0,
                    price=100.0,
                    fee=0.1,
                    symbol="MOCK",
                )
            ],
            state=PositionCashStateV2DTO(
                cash=999.9,
                positions_qty={"MOCK": 1.0},
                avg_cost={"MOCK": 100.0},
                realized_pnl=0.0,
            ),
            equity=[1000.0, 1000.0],
            metrics={
                "total_return": 0.0,
                "max_drawdown": 0.0,
                "sharpe": 0.0,
                "n_steps": 2.0,
            },
        )
        return report_to_dict(dto)
    except Exception:
        return {
            "schema_version": 1,
            "fills": [
                {
                    "order_id": "o1",
                    "side": "BUY",
                    "qty": 1.0,
                    "price": 100.0,
                    "fee": 0.1,
                    "symbol": "MOCK",
                }
            ],
            "state": {
                "cash": 999.9,
                "positions_qty": {"MOCK": 1.0},
                "avg_cost": {"MOCK": 100.0},
                "realized_pnl": 0.0,
            },
            "equity": [1000.0, 1000.0],
            "metrics": {
                "total_return": 0.0,
                "max_drawdown": 0.0,
                "sharpe": 0.0,
                "n_steps": 2.0,
            },
        }


def test_roundtrip_bundle_read(tmp_path: Path) -> None:
    report = _sample_report_dict()
    write_report_bundle_v1(tmp_path, report, include_metrics_summary=True)
    out = read_report_bundle_v1(tmp_path)
    assert out["schema_version"] == 1
    assert isinstance(out["fills"], list)
    assert out["equity"] == [1000.0, 1000.0]


def test_manifest_deterministic(tmp_path: Path) -> None:
    report = _sample_report_dict()
    write_report_bundle_v1(tmp_path, report, include_metrics_summary=True)
    m1 = (tmp_path / "manifest.json").read_text(encoding="utf-8")
    write_report_bundle_v1(tmp_path, report, include_metrics_summary=True)
    m2 = (tmp_path / "manifest.json").read_text(encoding="utf-8")
    assert m1 == m2


def test_verify_detects_tamper(tmp_path: Path) -> None:
    report = _sample_report_dict()
    write_report_bundle_v1(tmp_path, report, include_metrics_summary=True)

    report_path = tmp_path / "report.json"
    d = json.loads(report_path.read_text(encoding="utf-8"))
    d["equity"] = [999.0, 999.0]
    report_path.write_text(json.dumps(d, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(BundleIntegrityError):
        verify_report_bundle_v1(tmp_path)


def test_verify_missing_file(tmp_path: Path) -> None:
    report = _sample_report_dict()
    write_report_bundle_v1(tmp_path, report, include_metrics_summary=True)
    (tmp_path / "report.json").unlink()
    with pytest.raises(BundleIntegrityError):
        verify_report_bundle_v1(tmp_path)


def test_verify_missing_manifest(tmp_path: Path) -> None:
    report = _sample_report_dict()
    write_report_bundle_v1(tmp_path, report, include_metrics_summary=True)
    (tmp_path / "manifest.json").unlink()
    with pytest.raises(BundleIntegrityError):
        verify_report_bundle_v1(tmp_path)
