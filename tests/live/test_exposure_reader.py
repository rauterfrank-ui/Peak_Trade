"""
Tests for src/live/exposure_reader.py — Live Runs Exposure Reader.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from src.live.exposure_reader import get_live_runs_exposure_summary


def test_empty_base_dir_returns_empty_summary(tmp_path: Path) -> None:
    """Empty base_dir returns run_count 0, no observed_exposure."""
    result = get_live_runs_exposure_summary(tmp_path)
    assert result["data_source"] == "live_runs"
    assert result["run_count"] == 0
    assert result["observed_exposure"] is None
    assert result["observed_ccy"] == "unknown"


def test_base_dir_not_exists_returns_empty(tmp_path: Path) -> None:
    """Non-existent base_dir returns empty summary."""
    result = get_live_runs_exposure_summary(tmp_path / "nonexistent")
    assert result["run_count"] == 0
    assert result["observed_exposure"] is None


def test_single_run_with_position_and_price_returns_exposure(tmp_path: Path) -> None:
    """Single run with position_size and price returns aggregated exposure."""
    run_id = "20251207_120000_shadow_ma_crossover_BTC-EUR_1m"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)

    # meta.json
    meta = {
        "run_id": run_id,
        "mode": "shadow",
        "strategy_name": "ma_crossover",
        "symbol": "BTC/EUR",
        "timeframe": "1m",
        "started_at": "2025-12-07T12:00:00Z",
    }
    with open(run_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # events.parquet with position_size and price
    events = pd.DataFrame(
        [
            {"step": 1, "position_size": 0.1, "price": 50000.0, "close": 50000.0},
            {"step": 2, "position_size": 0.1, "price": 50100.0, "close": 50100.0},
        ]
    )
    events.to_parquet(run_dir / "events.parquet", index=False)

    result = get_live_runs_exposure_summary(tmp_path)
    assert result["run_count"] == 1
    assert result["observed_exposure"] is not None
    assert result["observed_exposure"] == pytest.approx(5010.0, rel=0.01)  # 0.1 * 50100
    assert result["observed_ccy"] == "EUR"
    assert result["data_source"] == "live_runs"
    assert result["last_updated_utc"] is not None


def test_run_without_position_size_skipped(tmp_path: Path) -> None:
    """Run without position_size contributes 0."""
    run_id = "20251207_120000_shadow_ma_crossover_BTC-EUR_1m"
    run_dir = tmp_path / run_id
    run_dir.mkdir(parents=True)

    meta = {
        "run_id": run_id,
        "mode": "shadow",
        "strategy_name": "x",
        "symbol": "BTC/EUR",
        "timeframe": "1m",
    }
    with open(run_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f)

    events = pd.DataFrame([{"step": 1, "price": 50000.0}])  # no position_size
    events.to_parquet(run_dir / "events.parquet", index=False)

    result = get_live_runs_exposure_summary(tmp_path)
    assert result["run_count"] == 1
    assert result["observed_exposure"] is None


def test_multiple_runs_aggregates_exposure(tmp_path: Path) -> None:
    """Multiple runs aggregate exposure."""
    for i, (run_id, pos, price) in enumerate(
        [
            ("run1", 0.05, 50000.0),
            ("run2", 0.02, 51000.0),
        ]
    ):
        run_dir = tmp_path / run_id
        run_dir.mkdir(parents=True)
        meta = {
            "run_id": run_id,
            "mode": "shadow",
            "strategy_name": "x",
            "symbol": "BTC/EUR",
            "timeframe": "1m",
        }
        with open(run_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f)
        events = pd.DataFrame([{"step": 1, "position_size": pos, "price": price, "close": price}])
        events.to_parquet(run_dir / "events.parquet", index=False)

    result = get_live_runs_exposure_summary(tmp_path)
    assert result["run_count"] == 2
    expected = 0.05 * 50000 + 0.02 * 51000  # 2500 + 1020 = 3520
    assert result["observed_exposure"] == pytest.approx(expected, rel=0.01)
