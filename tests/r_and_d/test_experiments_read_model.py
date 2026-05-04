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


def test_load_experiments_from_directory_top_level_json_only(tmp_path: Path) -> None:
    """Regression: glob('*.json') is non-recursive — nested experiment JSON must not load."""
    root_good = _minimal_exp("20240301_120000", 1.0, 0.1, "root.json")
    (tmp_path / "root.json").write_text(json.dumps(root_good), encoding="utf-8")
    nested_dir = tmp_path / "nested"
    nested_dir.mkdir()
    nested_raw = _minimal_exp("20240302_120000", 9.0, 0.9, "nested.json")
    (nested_dir / "nested.json").write_text(json.dumps(nested_raw), encoding="utf-8")

    out = load_experiments_from_directory(tmp_path)
    assert len(out) == 1
    assert out[0]["_filename"] == "root.json"


def test_load_experiments_equal_timestamp_uses_deterministic_filename_order(
    tmp_path: Path,
) -> None:
    """Equal ``experiment.timestamp`` → stable sort preserves sorted-glob filename order."""

    ts = "20240601_120000"
    first = _minimal_exp(ts, 1.0, 0.1, "a_first.json")
    second = _minimal_exp(ts, 2.0, 0.2, "b_second.json")
    # Write lexicographically later file first: result order must still follow sorted(glob).
    (tmp_path / "b_second.json").write_text(json.dumps(second), encoding="utf-8")
    (tmp_path / "a_first.json").write_text(json.dumps(first), encoding="utf-8")

    out = load_experiments_from_directory(tmp_path)
    assert len(out) == 2
    assert [x["_filename"] for x in out] == ["a_first.json", "b_second.json"]
    assert out[0]["experiment"]["timestamp"] == ts == out[1]["experiment"]["timestamp"]


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


def test_sort_by_timestamp_stable_when_timestamp_ties() -> None:
    """Gleicher Timestamp → stabile Reihenfolge wie Eingabe (sorted ist stabil)."""
    first = _minimal_exp("20240101_120000", 1.0, 0.1, "first.json")
    second = _minimal_exp("20240101_120000", 9.0, 0.9, "second.json")
    assert sort_raw_experiments([first, second], sort_by="timestamp", sort_order="desc") == [
        first,
        second,
    ]
    assert sort_raw_experiments([second, first], sort_by="timestamp", sort_order="desc") == [
        second,
        first,
    ]


def test_sort_by_sharpe_stable_when_sharpe_ties() -> None:
    """Gleicher Sharpe → stabile Reihenfolge wie Eingabe."""
    a = _minimal_exp("20240101_120000", 2.0, 0.1, "a.json")
    b = _minimal_exp("20240102_120000", 2.0, 0.2, "b.json")
    assert sort_raw_experiments([a, b], sort_by="sharpe", sort_order="desc") == [a, b]
    assert sort_raw_experiments([b, a], sort_by="sharpe", sort_order="desc") == [b, a]
