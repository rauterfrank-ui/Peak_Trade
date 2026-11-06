"""Cross-sectional funding-rate carry v0 score and single-leg selection primitives.

Pure offline, deterministic funding-rate ranking for long-low / short-high rotation.
Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_FUNDING_RATE_CARRY_SCORING_V0=true"

SCORE_FORMULA_VERSION = "cross_sectional_funding_rate_rank_long_low_short_high_v0"
SCORE_FORMULA_EXPRESSION = (
    "score_i = -funding_rate_i[t-lag] after optional smoothing over funding_smoothing_window_bars; "
    "long_leg = instrument with minimum funding_rate; "
    "short_leg = instrument with maximum funding_rate; "
    "single_slot selects leg with larger absolute funding extremeness"
)


class FundingCarryLeg(str, Enum):
    FLAT = "FLAT"
    LONG_LOW = "LONG_LOW"
    SHORT_HIGH = "SHORT_HIGH"


@dataclass(frozen=True)
class FundingCarryScoreResultV0:
    instrument_id: str
    funding_rate: float
    smoothed_funding_rate: float
    warmup_complete: bool


@dataclass(frozen=True)
class FundingExtremeSelectionV0:
    leg: FundingCarryLeg
    instrument_id: str | None
    min_funding_instrument_id: str | None
    max_funding_instrument_id: str | None
    min_funding_rate: float | None
    max_funding_rate: float | None


def _is_bitcoin_instrument(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return any(token in lowered for token in ("btc", "xbt", "bitcoin"))


def _smooth_funding_rates(
    rates: Sequence[float],
    *,
    window: int,
    epoch_index: int,
    signal_lag_bars: int,
) -> float | None:
    lag_idx = epoch_index - signal_lag_bars
    if lag_idx < 0:
        return None
    start = lag_idx - window + 1
    if start < 0:
        return None
    window_values = rates[start : lag_idx + 1]
    if not window_values or any(not math.isfinite(value) for value in window_values):
        return None
    return sum(window_values) / len(window_values)


def compute_instrument_funding_score_v0(
    instrument_id: str,
    funding_rates: Sequence[float],
    *,
    funding_smoothing_window_bars: int,
    signal_lag_bars: int,
    epoch_index: int,
) -> FundingCarryScoreResultV0 | None:
    if _is_bitcoin_instrument(instrument_id):
        return None
    smoothed = _smooth_funding_rates(
        funding_rates,
        window=funding_smoothing_window_bars,
        epoch_index=epoch_index,
        signal_lag_bars=signal_lag_bars,
    )
    if smoothed is None or not math.isfinite(smoothed):
        return None
    lag_idx = epoch_index - signal_lag_bars
    raw = funding_rates[lag_idx]
    if not math.isfinite(raw):
        return None
    return FundingCarryScoreResultV0(
        instrument_id=instrument_id,
        funding_rate=raw,
        smoothed_funding_rate=smoothed,
        warmup_complete=True,
    )


def rank_funding_scores_for_long_low_v0(
    scores: Sequence[FundingCarryScoreResultV0],
) -> tuple[FundingCarryScoreResultV0, ...]:
    return tuple(sorted(scores, key=lambda item: (item.smoothed_funding_rate, item.instrument_id)))


def rank_funding_scores_for_short_high_v0(
    scores: Sequence[FundingCarryScoreResultV0],
) -> tuple[FundingCarryScoreResultV0, ...]:
    return tuple(sorted(scores, key=lambda item: (-item.smoothed_funding_rate, item.instrument_id)))


def select_funding_extreme_single_leg_v0(
    scores: Sequence[FundingCarryScoreResultV0],
) -> FundingExtremeSelectionV0:
    if not scores:
        return FundingExtremeSelectionV0(
            leg=FundingCarryLeg.FLAT,
            instrument_id=None,
            min_funding_instrument_id=None,
            max_funding_instrument_id=None,
            min_funding_rate=None,
            max_funding_rate=None,
        )
    long_ranked = rank_funding_scores_for_long_low_v0(scores)
    short_ranked = rank_funding_scores_for_short_high_v0(scores)
    min_item = long_ranked[0]
    max_item = short_ranked[0]
    if abs(min_item.smoothed_funding_rate) >= abs(max_item.smoothed_funding_rate):
        return FundingExtremeSelectionV0(
            leg=FundingCarryLeg.LONG_LOW,
            instrument_id=min_item.instrument_id,
            min_funding_instrument_id=min_item.instrument_id,
            max_funding_instrument_id=max_item.instrument_id,
            min_funding_rate=min_item.smoothed_funding_rate,
            max_funding_rate=max_item.smoothed_funding_rate,
        )
    return FundingExtremeSelectionV0(
        leg=FundingCarryLeg.SHORT_HIGH,
        instrument_id=max_item.instrument_id,
        min_funding_instrument_id=min_item.instrument_id,
        max_funding_instrument_id=max_item.instrument_id,
        min_funding_rate=min_item.smoothed_funding_rate,
        max_funding_rate=max_item.smoothed_funding_rate,
    )
