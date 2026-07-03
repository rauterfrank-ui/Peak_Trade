"""Cross-sectional funding-rate delta momentum v0 score and single-leg selection primitives.

Pure offline, deterministic funding-delta ranking for long-min-delta / short-max-delta
mean-reversion rotation. Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_FUNDING_RATE_DELTA_MOMENTUM_SCORING_V0=true"

SCORE_FORMULA_VERSION = "cross_sectional_funding_rate_delta_rank_v0"
SCORE_FORMULA_EXPRESSION = (
    "delta_i(t) = funding_rate_i[t-lag] - funding_rate_i[t-lag-K]; "
    "long_leg = instrument with minimum delta; "
    "short_leg = instrument with maximum delta; "
    "single_slot selects leg with larger absolute delta"
)
FUNDING_DELTA_LOOKBACK_K = 4
FUNDING_SIGNAL_LAG = 1


class FundingDeltaLeg(str, Enum):
    FLAT = "FLAT"
    LONG_MIN_DELTA = "LONG_MIN_DELTA"
    SHORT_MAX_DELTA = "SHORT_MAX_DELTA"


@dataclass(frozen=True)
class FundingDeltaScoreResultV0:
    instrument_id: str
    funding_rate_lag: float
    funding_rate_lookback: float
    funding_delta: float
    warmup_complete: bool


@dataclass(frozen=True)
class FundingDeltaExtremeSelectionV0:
    leg: FundingDeltaLeg
    instrument_id: str | None
    min_delta_instrument_id: str | None
    max_delta_instrument_id: str | None
    min_funding_delta: float | None
    max_funding_delta: float | None


def _is_bitcoin_instrument(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return any(token in lowered for token in ("btc", "xbt", "bitcoin"))


def compute_instrument_funding_delta_score_v0(
    instrument_id: str,
    funding_rates: Sequence[float],
    *,
    funding_delta_lookback_k: int = FUNDING_DELTA_LOOKBACK_K,
    signal_lag_bars: int = FUNDING_SIGNAL_LAG,
    epoch_index: int,
) -> FundingDeltaScoreResultV0 | None:
    if _is_bitcoin_instrument(instrument_id):
        return None
    lag_idx = epoch_index - signal_lag_bars
    lookback_idx = lag_idx - funding_delta_lookback_k
    if lag_idx < 0 or lookback_idx < 0:
        return None
    raw_lag = funding_rates[lag_idx]
    raw_lookback = funding_rates[lookback_idx]
    if not math.isfinite(raw_lag) or not math.isfinite(raw_lookback):
        return None
    delta = raw_lag - raw_lookback
    if not math.isfinite(delta):
        return None
    return FundingDeltaScoreResultV0(
        instrument_id=instrument_id,
        funding_rate_lag=raw_lag,
        funding_rate_lookback=raw_lookback,
        funding_delta=delta,
        warmup_complete=True,
    )


def rank_funding_deltas_for_long_min_v0(
    scores: Sequence[FundingDeltaScoreResultV0],
) -> tuple[FundingDeltaScoreResultV0, ...]:
    return tuple(sorted(scores, key=lambda item: (item.funding_delta, item.instrument_id)))


def rank_funding_deltas_for_short_max_v0(
    scores: Sequence[FundingDeltaScoreResultV0],
) -> tuple[FundingDeltaScoreResultV0, ...]:
    return tuple(sorted(scores, key=lambda item: (-item.funding_delta, item.instrument_id)))


def select_funding_delta_extreme_single_leg_v0(
    scores: Sequence[FundingDeltaScoreResultV0],
) -> FundingDeltaExtremeSelectionV0:
    if not scores:
        return FundingDeltaExtremeSelectionV0(
            leg=FundingDeltaLeg.FLAT,
            instrument_id=None,
            min_delta_instrument_id=None,
            max_delta_instrument_id=None,
            min_funding_delta=None,
            max_funding_delta=None,
        )
    long_ranked = rank_funding_deltas_for_long_min_v0(scores)
    short_ranked = rank_funding_deltas_for_short_max_v0(scores)
    min_item = long_ranked[0]
    max_item = short_ranked[0]
    min_abs = abs(min_item.funding_delta)
    max_abs = abs(max_item.funding_delta)
    if min_abs > max_abs or (
        min_abs == max_abs and min_item.instrument_id <= max_item.instrument_id
    ):
        leg = FundingDeltaLeg.LONG_MIN_DELTA
        selected_id = min_item.instrument_id
    else:
        leg = FundingDeltaLeg.SHORT_MAX_DELTA
        selected_id = max_item.instrument_id
    return FundingDeltaExtremeSelectionV0(
        leg=leg,
        instrument_id=selected_id,
        min_delta_instrument_id=min_item.instrument_id,
        max_delta_instrument_id=max_item.instrument_id,
        min_funding_delta=min_item.funding_delta,
        max_funding_delta=max_item.funding_delta,
    )


def score_input_provenance_marker_v0() -> str:
    return "funding_delta_score_input_lagged_observation_v0"


def funding_cashflow_provenance_marker_v0() -> str:
    return "funding_cashflow_interval_settlement_v1"
