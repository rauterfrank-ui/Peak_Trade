"""Cross-sectional open-interest delta rank v0 score and single-leg selection primitives.

Pure offline, deterministic open-interest-delta ranking for long-min-delta / short-max-delta
single-slot rotation. Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_SCORING_V0=true"

SCORE_FORMULA_VERSION = "cross_sectional_open_interest_delta_rank_v0"
SCORE_FORMULA_EXPRESSION = (
    "delta_i(t) = open_interest_i[t-lag] - open_interest_i[t-lag-K]; "
    "long_leg = instrument with minimum delta; "
    "short_leg = instrument with maximum delta; "
    "single_slot selects leg with larger absolute delta"
)
OPEN_INTEREST_DELTA_LOOKBACK_K = 4
OPEN_INTEREST_SIGNAL_LAG = 1


class OpenInterestDeltaScoreStatusV0(str, Enum):
    COMPUTE_OK = "COMPUTE_OK"
    WARMUP_INCOMPLETE = "WARMUP_INCOMPLETE"
    MISSING_REQUIRED_OPEN_INTEREST_HISTORY = "MISSING_REQUIRED_OPEN_INTEREST_HISTORY"
    NON_FINITE_INPUT = "NON_FINITE_INPUT"


class OpenInterestDeltaLeg(str, Enum):
    FLAT = "FLAT"
    LONG_MIN_DELTA = "LONG_MIN_DELTA"
    SHORT_MAX_DELTA = "SHORT_MAX_DELTA"


@dataclass(frozen=True)
class OpenInterestDeltaScoreResultV0:
    instrument_id: str
    open_interest_lag: float
    open_interest_lookback: float
    open_interest_delta: float
    warmup_complete: bool
    score_status: OpenInterestDeltaScoreStatusV0 = OpenInterestDeltaScoreStatusV0.COMPUTE_OK
    signal_eligible: bool = True


@dataclass(frozen=True)
class OpenInterestDeltaExtremeSelectionV0:
    leg: OpenInterestDeltaLeg
    instrument_id: str | None
    min_delta_instrument_id: str | None
    max_delta_instrument_id: str | None
    min_open_interest_delta: float | None
    max_open_interest_delta: float | None


def _is_bitcoin_instrument(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return any(token in lowered for token in ("btc", "xbt", "bitcoin"))


def _parse_open_interest(value: float | str | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except ValueError:
        return None


def compute_instrument_open_interest_delta_score_v0(
    instrument_id: str,
    open_interest_values: Sequence[float | str | None],
    *,
    open_interest_delta_lookback_k: int = OPEN_INTEREST_DELTA_LOOKBACK_K,
    signal_lag_bars: int = OPEN_INTEREST_SIGNAL_LAG,
    epoch_index: int,
) -> OpenInterestDeltaScoreResultV0 | None:
    if _is_bitcoin_instrument(instrument_id):
        return None
    lag_idx = epoch_index - signal_lag_bars
    lookback_idx = lag_idx - open_interest_delta_lookback_k
    if lag_idx < 0 or lookback_idx < 0:
        return None
    raw_lag = _parse_open_interest(open_interest_values[lag_idx])
    raw_lookback = _parse_open_interest(open_interest_values[lookback_idx])
    if raw_lag is None or raw_lookback is None:
        return OpenInterestDeltaScoreResultV0(
            instrument_id=instrument_id,
            open_interest_lag=float("nan"),
            open_interest_lookback=float("nan"),
            open_interest_delta=float("nan"),
            warmup_complete=False,
            score_status=OpenInterestDeltaScoreStatusV0.MISSING_REQUIRED_OPEN_INTEREST_HISTORY,
            signal_eligible=False,
        )
    if not math.isfinite(raw_lag) or not math.isfinite(raw_lookback):
        return OpenInterestDeltaScoreResultV0(
            instrument_id=instrument_id,
            open_interest_lag=raw_lag,
            open_interest_lookback=raw_lookback,
            open_interest_delta=float("nan"),
            warmup_complete=False,
            score_status=OpenInterestDeltaScoreStatusV0.NON_FINITE_INPUT,
            signal_eligible=False,
        )
    delta = raw_lag - raw_lookback
    if not math.isfinite(delta):
        return OpenInterestDeltaScoreResultV0(
            instrument_id=instrument_id,
            open_interest_lag=raw_lag,
            open_interest_lookback=raw_lookback,
            open_interest_delta=delta,
            warmup_complete=False,
            score_status=OpenInterestDeltaScoreStatusV0.NON_FINITE_INPUT,
            signal_eligible=False,
        )
    return OpenInterestDeltaScoreResultV0(
        instrument_id=instrument_id,
        open_interest_lag=raw_lag,
        open_interest_lookback=raw_lookback,
        open_interest_delta=delta,
        warmup_complete=True,
        score_status=OpenInterestDeltaScoreStatusV0.COMPUTE_OK,
        signal_eligible=True,
    )


def rank_open_interest_deltas_for_long_min_v0(
    scores: Sequence[OpenInterestDeltaScoreResultV0],
) -> tuple[OpenInterestDeltaScoreResultV0, ...]:
    return tuple(sorted(scores, key=lambda item: (item.open_interest_delta, item.instrument_id)))


def rank_open_interest_deltas_for_short_max_v0(
    scores: Sequence[OpenInterestDeltaScoreResultV0],
) -> tuple[OpenInterestDeltaScoreResultV0, ...]:
    return tuple(sorted(scores, key=lambda item: (-item.open_interest_delta, item.instrument_id)))


def select_open_interest_delta_extreme_single_leg_v0(
    scores: Sequence[OpenInterestDeltaScoreResultV0],
) -> OpenInterestDeltaExtremeSelectionV0:
    if not scores:
        return OpenInterestDeltaExtremeSelectionV0(
            leg=OpenInterestDeltaLeg.FLAT,
            instrument_id=None,
            min_delta_instrument_id=None,
            max_delta_instrument_id=None,
            min_open_interest_delta=None,
            max_open_interest_delta=None,
        )
    long_ranked = rank_open_interest_deltas_for_long_min_v0(scores)
    short_ranked = rank_open_interest_deltas_for_short_max_v0(scores)
    min_item = long_ranked[0]
    max_item = short_ranked[0]
    min_abs = abs(min_item.open_interest_delta)
    max_abs = abs(max_item.open_interest_delta)
    if min_abs > max_abs or (
        min_abs == max_abs and min_item.instrument_id <= max_item.instrument_id
    ):
        leg = OpenInterestDeltaLeg.LONG_MIN_DELTA
        selected_id = min_item.instrument_id
    else:
        leg = OpenInterestDeltaLeg.SHORT_MAX_DELTA
        selected_id = max_item.instrument_id
    return OpenInterestDeltaExtremeSelectionV0(
        leg=leg,
        instrument_id=selected_id,
        min_delta_instrument_id=min_item.instrument_id,
        max_delta_instrument_id=max_item.instrument_id,
        min_open_interest_delta=min_item.open_interest_delta,
        max_open_interest_delta=max_item.open_interest_delta,
    )


def score_input_provenance_marker_v0() -> str:
    return "open_interest_delta_score_input_lagged_observation_v0"
