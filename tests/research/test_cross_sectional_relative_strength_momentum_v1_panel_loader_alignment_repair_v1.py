"""Regression: panel loader alignment must ignore auxiliary warmup NaNs.

Implementation-only. Does not authorize/execute development evaluation or mutate
run counters / run slots.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.panel_loader_v1 import (
    REQUIRED_PANEL_BAR_COLUMNS,
    _require_ohlcv_alignment,
    load_instrument_panel_series_from_development_archive_v1,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    MEASUREMENT_CONTRACT_REL_PATH,
    PROGRAM_REL_PATH,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.entry_point_v1 import (
    run_preflight_only,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.guards_v1 import (
    read_run_counters,
)

REPO = Path(__file__).resolve().parents[2]


def _synthetic_frame_with_volatility_warmup_nans() -> pd.DataFrame:
    idx = pd.date_range("2022-06-01T04:00:00Z", periods=8, freq="h", tz="UTC")
    frame = pd.DataFrame(
        {
            "open": [1.0] * 8,
            "high": [1.1] * 8,
            "low": [0.9] * 8,
            "close": [1.05] * 8,
            "volume": [10.0] * 8,
            "volatility_estimate": [float("nan")] * 3 + [0.2] * 5,
            "warmup_status": ["WARMUP"] * 3 + ["READY"] * 5,
        },
        index=idx,
    )
    return frame


def test_required_panel_bar_columns_are_ohlcv_only() -> None:
    assert REQUIRED_PANEL_BAR_COLUMNS == ("open", "high", "low", "close", "volume")


def test_alignment_ignores_auxiliary_volatility_warmup_nans() -> None:
    frame = _synthetic_frame_with_volatility_warmup_nans()
    # Legacy-all-columns check would fail-closed on volatility_estimate NaNs.
    assert bool(frame.isna().any().any())
    required = _require_ohlcv_alignment(frame, instrument_id="synth:perp")
    assert list(required.columns) == list(REQUIRED_PANEL_BAR_COLUMNS)
    assert not bool(required.isna().any().any())


def test_alignment_still_fail_closed_on_true_ohlcv_gap() -> None:
    frame = _synthetic_frame_with_volatility_warmup_nans()
    frame.loc[frame.index[0], "close"] = float("nan")
    with pytest.raises(ValueError, match="ALIGNMENT_GAP:synth:perp"):
        _require_ohlcv_alignment(frame, instrument_id="synth:perp")


def test_load_validate_development_archive_without_evaluation() -> None:
    """Load/validate only. Must not execute evaluation or consume/alter run budget."""
    before = read_run_counters(REPO)
    assert before["contract_development_run_count"] == 1
    assert before["contract_runner_start_count"] == 1

    from src.research.regime_gated_standaside_mr_development_evaluation_v1.dev_panel_bars_v1 import (
        resolve_development_archive_root,
    )

    archive = resolve_development_archive_root(None)
    series, timestamps, digest = load_instrument_panel_series_from_development_archive_v1(archive)
    assert len(series) >= 1
    assert len(timestamps) == len(series[0].bars)
    assert digest
    # First instrument previously failed with ALIGNMENT_GAP under all-column NaN checks.
    assert any(s.instrument_id.endswith(":1INCH:USDT:USDT:perp") for s in series)

    after = read_run_counters(REPO)
    assert after == before

    # Preflight remains read-only and must not start evaluate.
    pre = run_preflight_only(REPO)
    assert pre["evaluation_executed"] is False
    assert pre["runner_started"] is False
    assert pre["holdout_accessed"] is False
    assert pre["dataset_id"] == DATASET_ID
    assert read_run_counters(REPO) == before

    mc = json.loads((REPO / MEASUREMENT_CONTRACT_REL_PATH).read_text(encoding="utf-8"))
    prog = json.loads((REPO / PROGRAM_REL_PATH).read_text(encoding="utf-8"))
    assert mc["development_run_count"] == 1
    assert mc["runner_start_count"] == 1
    assert prog["development_run_count"] == 1
    assert prog["runner_start_count"] == 1
