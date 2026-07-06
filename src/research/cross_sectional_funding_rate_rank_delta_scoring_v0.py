"""Cross-sectional funding-rate rank-delta v0 score and single-leg selection primitives.

Pure offline, deterministic cross-sectional rank migration scoring for long-min-rank-delta /
short-max-rank-delta rotation. Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_FUNDING_RATE_RANK_DELTA_SCORING_V0=true"

SCORE_FORMULA_VERSION = "cross_sectional_funding_rate_rank_delta_v0"
SCORE_FORMULA_EXPRESSION = (
    "rank_delta_i(t) = cross_sectional_rank_i(t) - cross_sectional_rank_i(t-K); "
    "long_leg = instrument with minimum rank_delta (largest rank improvement); "
    "short_leg = instrument with maximum rank_delta (largest rank decline); "
    "single_slot selects leg with larger absolute rank_delta"
)
RANK_LOOKBACK_K = 4
FUNDING_SIGNAL_LAG = 1
MIN_RANK_DELTA_FOR_ENTRY = 1


class FundingRankDeltaScoreStatusV0(str, Enum):
    COMPUTE_OK = "COMPUTE_OK"
    WARMUP_INCOMPLETE = "WARMUP_INCOMPLETE"
    MISSING_REQUIRED_FUNDING_HISTORY = "MISSING_REQUIRED_FUNDING_HISTORY"
    NON_FINITE_INPUT = "NON_FINITE_INPUT"


class FundingRankDeltaLeg(str, Enum):
    FLAT = "FLAT"
    LONG_MIN_RANK_DELTA = "LONG_MIN_RANK_DELTA"
    SHORT_MAX_RANK_DELTA = "SHORT_MAX_RANK_DELTA"


@dataclass(frozen=True)
class FundingRankDeltaScoreResultV0:
    instrument_id: str
    cross_sectional_rank_lag: float
    cross_sectional_rank_lookback: float
    rank_delta: float
    warmup_complete: bool
    score_status: FundingRankDeltaScoreStatusV0 = FundingRankDeltaScoreStatusV0.COMPUTE_OK
    signal_eligible: bool = True


@dataclass(frozen=True)
class FundingRankDeltaExtremeSelectionV0:
    leg: FundingRankDeltaLeg
    instrument_id: str | None
    min_rank_delta_instrument_id: str | None
    max_rank_delta_instrument_id: str | None
    min_rank_delta: float | None
    max_rank_delta: float | None


def _is_bitcoin_instrument(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return any(token in lowered for token in ("btc", "xbt", "bitcoin"))


def compute_cross_sectional_ranks_v0(
    funding_rates: Sequence[tuple[str, float | None]],
) -> dict[str, float]:
    eligible = [
        (instrument_id, rate)
        for instrument_id, rate in funding_rates
        if rate is not None and math.isfinite(rate)
    ]
    if not eligible:
        return {}
    sorted_items = sorted(eligible, key=lambda item: (item[1], item[0]))
    n = len(sorted_items)
    if n == 1:
        return {sorted_items[0][0]: 1.0}
    ranks: dict[str, float] = {}
    for index, (instrument_id, _rate) in enumerate(sorted_items):
        ranks[instrument_id] = float(index + 1)
    return ranks


def compute_instrument_funding_rank_delta_score_v0(
    instrument_id: str,
    panel_funding_rates: Sequence[tuple[str, float | None]],
    historical_panel_funding_rates: Sequence[tuple[str, float | None]],
    *,
    rank_lookback_k: int = RANK_LOOKBACK_K,
    signal_lag_bars: int = FUNDING_SIGNAL_LAG,
    epoch_index: int,
) -> FundingRankDeltaScoreResultV0 | None:
    if _is_bitcoin_instrument(instrument_id):
        return None
    if epoch_index < rank_lookback_k + signal_lag_bars:
        return None

    current_ranks = compute_cross_sectional_ranks_v0(panel_funding_rates)
    lookback_ranks = compute_cross_sectional_ranks_v0(historical_panel_funding_rates)
    if instrument_id not in current_ranks or instrument_id not in lookback_ranks:
        return FundingRankDeltaScoreResultV0(
            instrument_id=instrument_id,
            cross_sectional_rank_lag=float("nan"),
            cross_sectional_rank_lookback=float("nan"),
            rank_delta=float("nan"),
            warmup_complete=False,
            score_status=FundingRankDeltaScoreStatusV0.MISSING_REQUIRED_FUNDING_HISTORY,
            signal_eligible=False,
        )

    rank_lag = current_ranks[instrument_id]
    rank_lookback = lookback_ranks[instrument_id]
    rank_delta = rank_lag - rank_lookback
    if not math.isfinite(rank_delta):
        return FundingRankDeltaScoreResultV0(
            instrument_id=instrument_id,
            cross_sectional_rank_lag=rank_lag,
            cross_sectional_rank_lookback=rank_lookback,
            rank_delta=rank_delta,
            warmup_complete=False,
            score_status=FundingRankDeltaScoreStatusV0.NON_FINITE_INPUT,
            signal_eligible=False,
        )
    return FundingRankDeltaScoreResultV0(
        instrument_id=instrument_id,
        cross_sectional_rank_lag=rank_lag,
        cross_sectional_rank_lookback=rank_lookback,
        rank_delta=rank_delta,
        warmup_complete=True,
        score_status=FundingRankDeltaScoreStatusV0.COMPUTE_OK,
        signal_eligible=True,
    )


def rank_funding_rank_deltas_for_long_min_v0(
    scores: Sequence[FundingRankDeltaScoreResultV0],
) -> tuple[FundingRankDeltaScoreResultV0, ...]:
    return tuple(sorted(scores, key=lambda item: (item.rank_delta, item.instrument_id)))


def rank_funding_rank_deltas_for_short_max_v0(
    scores: Sequence[FundingRankDeltaScoreResultV0],
) -> tuple[FundingRankDeltaScoreResultV0, ...]:
    return tuple(sorted(scores, key=lambda item: (-item.rank_delta, item.instrument_id)))


def select_funding_rank_delta_extreme_single_leg_v0(
    scores: Sequence[FundingRankDeltaScoreResultV0],
    *,
    min_rank_delta_for_entry: float = MIN_RANK_DELTA_FOR_ENTRY,
) -> FundingRankDeltaExtremeSelectionV0:
    if not scores:
        return FundingRankDeltaExtremeSelectionV0(
            leg=FundingRankDeltaLeg.FLAT,
            instrument_id=None,
            min_rank_delta_instrument_id=None,
            max_rank_delta_instrument_id=None,
            min_rank_delta=None,
            max_rank_delta=None,
        )
    long_ranked = rank_funding_rank_deltas_for_long_min_v0(scores)
    short_ranked = rank_funding_rank_deltas_for_short_max_v0(scores)
    min_item = long_ranked[0]
    max_item = short_ranked[0]
    if (
        abs(min_item.rank_delta) < min_rank_delta_for_entry
        and abs(max_item.rank_delta) < min_rank_delta_for_entry
    ):
        return FundingRankDeltaExtremeSelectionV0(
            leg=FundingRankDeltaLeg.FLAT,
            instrument_id=None,
            min_rank_delta_instrument_id=min_item.instrument_id,
            max_rank_delta_instrument_id=max_item.instrument_id,
            min_rank_delta=min_item.rank_delta,
            max_rank_delta=max_item.rank_delta,
        )
    min_abs = abs(min_item.rank_delta)
    max_abs = abs(max_item.rank_delta)
    if min_abs > max_abs or (
        min_abs == max_abs and min_item.instrument_id <= max_item.instrument_id
    ):
        leg = FundingRankDeltaLeg.LONG_MIN_RANK_DELTA
        selected_id = min_item.instrument_id
    else:
        leg = FundingRankDeltaLeg.SHORT_MAX_RANK_DELTA
        selected_id = max_item.instrument_id
    return FundingRankDeltaExtremeSelectionV0(
        leg=leg,
        instrument_id=selected_id,
        min_rank_delta_instrument_id=min_item.instrument_id,
        max_rank_delta_instrument_id=max_item.instrument_id,
        min_rank_delta=min_item.rank_delta,
        max_rank_delta=max_item.rank_delta,
    )


def score_input_provenance_marker_v0() -> str:
    return "funding_rank_delta_score_input_lagged_observation_v0"


def funding_cashflow_provenance_marker_v0() -> str:
    return "funding_cashflow_interval_settlement_v1"
