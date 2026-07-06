"""Contract tests for dual-leg spread scoring v1."""

from __future__ import annotations

from src.research.cross_sectional_funding_rate_dual_leg_spread_scoring_v1 import (
    DualLegSpreadTarget,
    compute_instrument_funding_level_score_v1,
    select_dual_leg_spread_v1,
    FundingLevelScoreResultV1,
)


def test_select_dual_leg_when_spread_above_threshold() -> None:
    scores = (
        FundingLevelScoreResultV1("a", -0.001, True),
        FundingLevelScoreResultV1("b", 0.0, True),
        FundingLevelScoreResultV1("c", 0.001, True),
    )
    result = select_dual_leg_spread_v1(scores, min_spread_bps_for_entry=0.5)
    assert result.target is DualLegSpreadTarget.DUAL_LEG
    assert result.long_instrument_id == "a"
    assert result.short_instrument_id == "c"


def test_select_flat_when_spread_below_threshold() -> None:
    scores = (
        FundingLevelScoreResultV1("a", -0.00001, True),
        FundingLevelScoreResultV1("b", 0.00001, True),
    )
    result = select_dual_leg_spread_v1(scores, min_spread_bps_for_entry=0.5)
    assert result.target is DualLegSpreadTarget.FLAT


def test_compute_score_respects_signal_lag() -> None:
    rates = [0.001, 0.002, 0.003]
    assert (
        compute_instrument_funding_level_score_v1(
            "okx:linear_perpetual:ETH:USDT:USDT:perp",
            rates,
            signal_lag_bars=1,
            epoch_index=0,
        )
        is None
    )
    score = compute_instrument_funding_level_score_v1(
        "okx:linear_perpetual:ETH:USDT:USDT:perp",
        rates,
        signal_lag_bars=1,
        epoch_index=2,
    )
    assert score is not None
    assert score.funding_rate == 0.002
