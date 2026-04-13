"""Unit tests for src.r_and_d.experiments_read_model (filesystem read-only)."""

from __future__ import annotations

import json
from pathlib import Path

from src.r_and_d.experiments_read_model import (
    load_experiment_json_file,
    load_experiments_from_directory,
    sort_raw_experiments,
)


def _minimal_exp(timestamp: str, sharpe: float, total_return: float, name: str) -> dict:
    return {
        "experiment": {
            "preset_id": "p",
            "strategy": "s",
            "symbol": "X",
            "timeframe": "1h",
            "tag": "t",
            "timestamp": timestamp,
        },
        "results": {
            "total_return": total_return,
            "sharpe": sharpe,
            "max_drawdown": 0.0,
            "total_trades": 1,
            "win_rate": 0.5,
        },
        "meta": {},
        "_filename": name,
    }


def test_load_experiment_json_file_invalid_returns_none(tmp_path: Path) -> None:
    bad = tmp_path / "x.json"
    bad.write_text("not json", encoding="utf-8")
    assert load_experiment_json_file(bad) is None


def test_load_experiment_json_file_ok(tmp_path: Path) -> None:
    p = tmp_path / "a.json"
    raw = _minimal_exp("20240101_120000", 1.0, 0.1, "a.json")
    p.write_text(json.dumps(raw), encoding="utf-8")
    loaded = load_experiment_json_file(p)
    assert loaded is not None
    assert loaded["_filename"] == "a.json"
    assert loaded["experiment"]["timestamp"] == "20240101_120000"


def test_load_experiments_skips_bad_file(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")
    good_raw = _minimal_exp("20240201_120000", 2.0, 0.2, "good.json")
    (tmp_path / "good.json").write_text(json.dumps(good_raw), encoding="utf-8")
    out = load_experiments_from_directory(tmp_path)
    assert len(out) == 1
    assert out[0]["_filename"] == "good.json"


def test_load_experiments_empty_dir(tmp_path: Path) -> None:
    assert load_experiments_from_directory(tmp_path) == []


def test_load_experiments_missing_dir(tmp_path: Path) -> None:
    assert load_experiments_from_directory(tmp_path / "nope") == []


def test_sort_by_sharpe_desc() -> None:
    a = _minimal_exp("20240101_120000", 1.0, 0.5, "a.json")
    b = _minimal_exp("20240102_120000", 3.0, 0.1, "b.json")
    c = _minimal_exp("20240103_120000", 2.0, 0.2, "c.json")
    got = sort_raw_experiments([a, b, c], sort_by="sharpe", sort_order="desc")
    assert [x["_filename"] for x in got] == ["b.json", "c.json", "a.json"]


def test_sort_by_return_asc() -> None:
    a = _minimal_exp("20240101_120000", 1.0, 0.1, "a.json")
    b = _minimal_exp("20240102_120000", 1.0, 0.3, "b.json")
    got = sort_raw_experiments([a, b], sort_by="return", sort_order="asc")
    assert [x["_filename"] for x in got] == ["a.json", "b.json"]


def test_sort_invalid_sort_by_falls_back_to_timestamp() -> None:
    a = _minimal_exp("20240101_120000", 1.0, 0.1, "a.json")
    b = _minimal_exp("20240102_120000", 1.0, 0.1, "b.json")
    got = sort_raw_experiments([a, b], sort_by="bogus", sort_order="desc")
    assert [x["_filename"] for x in got] == ["b.json", "a.json"]
