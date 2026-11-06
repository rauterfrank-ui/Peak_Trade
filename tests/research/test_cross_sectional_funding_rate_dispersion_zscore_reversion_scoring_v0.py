"""Unit tests for dispersion z-score reversion scoring v0."""

from __future__ import annotations

import math

from src.research.cross_sectional_funding_rate_dispersion_zscore_reversion_scoring_v0 import (
    FundingZscoreLeg,
    FundingZscoreScoreResultV0,
    FundingZscoreScoreStatusV0,
    MIN_ABS_ZSCORE_FOR_ENTRY,
    MIN_PANEL_FUNDING_DISPERSION,
    compute_instrument_funding_zscore_score_v0,
    compute_panel_dispersion_snapshot_v0,
    select_funding_zscore_extreme_single_leg_v0,
)


def _panel_rates(values: dict[str, float]) -> tuple[tuple[str, float | None], ...]:
    return tuple((iid, values[iid]) for iid in sorted(values))


def test_panel_dispersion_gate_blocks_low_std() -> None:
    snapshot = compute_panel_dispersion_snapshot_v0(
        _panel_rates(
            {
                "a": 0.0001,
                "b": 0.0001000001,
                "c": 0.0000999999,
                "d": 0.0001000002,
                "e": 0.0000999998,
            }
        ),
        min_panel_funding_dispersion=MIN_PANEL_FUNDING_DISPERSION,
    )
    assert snapshot is not None
    assert snapshot.dispersion_gate_passes is False


def test_zscore_computation_and_extreme_selection() -> None:
    panel = _panel_rates(
        {
            "inst_a": 0.00020,
            "inst_b": 0.00010,
            "inst_c": 0.00015,
            "inst_d": 0.00012,
            "inst_e": 0.00018,
        }
    )
    scores = [
        score
        for iid, _ in panel
        if (
            score := compute_instrument_funding_zscore_score_v0(
                iid,
                panel,
                signal_lag_bars=1,
                min_panel_funding_dispersion=MIN_PANEL_FUNDING_DISPERSION,
                epoch_index=1,
            )
        )
        is not None
        and score.signal_eligible
    ]
    assert len(scores) == 5
    selection = select_funding_zscore_extreme_single_leg_v0(
        scores,
        min_abs_zscore_for_entry=MIN_ABS_ZSCORE_FOR_ENTRY,
        panel_dispersion_gate_passes=True,
    )
    assert selection.panel_dispersion_gate_passes is True
    assert selection.leg in {
        FundingZscoreLeg.LONG_MIN_ZSCORE,
        FundingZscoreLeg.SHORT_MAX_ZSCORE,
    }
    assert selection.instrument_id is not None


def test_flat_when_abs_zscore_below_threshold() -> None:
    scores = (
        FundingZscoreScoreResultV0(
            instrument_id="inst_a",
            funding_rate_lag=0.0001,
            panel_mean=0.00012,
            panel_std=0.00002,
            z_score=-0.5,
            warmup_complete=True,
        ),
        FundingZscoreScoreResultV0(
            instrument_id="inst_b",
            funding_rate_lag=0.00014,
            panel_mean=0.00012,
            panel_std=0.00002,
            z_score=0.5,
            warmup_complete=True,
        ),
    )
    selection = select_funding_zscore_extreme_single_leg_v0(
        scores,
        min_abs_zscore_for_entry=MIN_ABS_ZSCORE_FOR_ENTRY,
        panel_dispersion_gate_passes=True,
    )
    assert selection.leg is FundingZscoreLeg.FLAT


def test_bitcoin_instrument_excluded() -> None:
    panel = _panel_rates(
        {
            "okx:linear_perpetual:BTC:USDT:USDT:perp": 0.0001,
            "inst_b": 0.0002,
            "inst_c": 0.0003,
            "inst_d": 0.0004,
            "inst_e": 0.0005,
        }
    )
    score = compute_instrument_funding_zscore_score_v0(
        "okx:linear_perpetual:BTC:USDT:USDT:perp",
        panel,
        epoch_index=1,
    )
    assert score is None


def test_non_finite_input_rejected() -> None:
    panel = _panel_rates(
        {
            "inst_a": float("nan"),
            "inst_b": 0.0002,
            "inst_c": 0.0003,
            "inst_d": 0.0004,
            "inst_e": 0.0005,
        }
    )
    score = compute_instrument_funding_zscore_score_v0("inst_a", panel, epoch_index=1)
    assert score is not None
    assert score.score_status is FundingZscoreScoreStatusV0.MISSING_REQUIRED_FUNDING_HISTORY
    assert not score.signal_eligible
    assert math.isnan(score.z_score)
