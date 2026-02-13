"""Contract tests for P34 JSON IO v1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.backtest.p33.report_artifacts_v1 import ArtifactSchemaError
from src.backtest.p34.json_io_v1 import read_report_json_v1, write_report_json_v1


def _min_report_dict_v1() -> dict:
    """Minimal schema v1 report dict (matches P33 expectations)."""
    return {
        "schema_version": 1,
        "fills": [],
        "state": {"cash": 0.0, "positions_qty": {}, "avg_cost": {}, "realized_pnl": 0.0},
        "equity": [1.0],
        "metrics": {"total_return": 0.0, "max_drawdown": 0.0, "sharpe": 0.0, "n_steps": 1.0},
    }


def test_write_read_roundtrip(tmp_path: Path) -> None:
    d = _min_report_dict_v1()
    p = tmp_path / "report.json"
    write_report_json_v1(p, d)
    d2 = read_report_json_v1(p)
    assert d2 == d


def test_write_is_deterministic(tmp_path: Path) -> None:
    d = _min_report_dict_v1()
    p1 = tmp_path / "a.json"
    p2 = tmp_path / "b.json"
    write_report_json_v1(p1, d)
    write_report_json_v1(p2, d)
    assert p1.read_text(encoding="utf-8") == p2.read_text(encoding="utf-8")


def test_invalid_json_raises(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("{ not-json", encoding="utf-8")
    with pytest.raises(ArtifactSchemaError):
        read_report_json_v1(p)


def test_wrong_schema_version_raises(tmp_path: Path) -> None:
    d = _min_report_dict_v1()
    d["schema_version"] = 999
    p = tmp_path / "wrong.json"
    p.write_text(json.dumps(d), encoding="utf-8")
    with pytest.raises(ArtifactSchemaError):
        read_report_json_v1(p)


def test_missing_keys_raises(tmp_path: Path) -> None:
    d = _min_report_dict_v1()
    del d["metrics"]
    p = tmp_path / "missing.json"
    write_report_json_v1(p, d)
    with pytest.raises(ArtifactSchemaError):
        read_report_json_v1(p)
