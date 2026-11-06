"""Cross-sectional open-interest level rank v0 score and single-leg selection primitives.

Pure offline, deterministic point-in-time open-interest level ranking for long-min-level /
short-max-level single-slot rotation. Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_OPEN_INTEREST_LEVEL_RANK_SCORING_V0=true"

SCORE_FORMULA_VERSION = "cross_sectional_open_interest_level_rank_v0"
SCORE_FORMULA_EXPRESSION = (
    "level_i(t) = open_interest_i[t-lag]; "
    "long_leg = instrument with minimum level; "
    "short_leg = instrument with maximum level; "
    "single_slot selects leg with larger absolute deviation from cross-sectional median level"
)
OPEN_INTEREST_SIGNAL_LAG = 1


class OpenInterestLevelScoreStatusV0(str, Enum):
    COMPUTE_OK = "COMPUTE_OK"
    WARMUP_INCOMPLETE = "WARMUP_INCOMPLETE"
    MISSING_REQUIRED_OPEN_INTEREST = "MISSING_REQUIRED_OPEN_INTEREST"
    NON_FINITE_INPUT = "NON_FINITE_INPUT"


class OpenInterestLevelLeg(str, Enum):
    FLAT = "FLAT"
    LONG_MIN_LEVEL = "LONG_MIN_LEVEL"
    SHORT_MAX_LEVEL = "SHORT_MAX_LEVEL"


@dataclass(frozen=True)
class OpenInterestLevelScoreResultV0:
    instrument_id: str
    open_interest_level: float
    warmup_complete: bool
    score_status: OpenInterestLevelScoreStatusV0 = OpenInterestLevelScoreStatusV0.COMPUTE_OK
    signal_eligible: bool = True


@dataclass(frozen=True)
class OpenInterestLevelExtremeSelectionV0:
    leg: OpenInterestLevelLeg
    instrument_id: str | None
    min_level_instrument_id: str | None
    max_level_instrument_id: str | None
    min_open_interest_level: float | None
    max_open_interest_level: float | None


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


def compute_instrument_open_interest_level_score_v0(
    instrument_id: str,
    open_interest_values: Sequence[float | str | None],
    *,
    signal_lag_bars: int = OPEN_INTEREST_SIGNAL_LAG,
    epoch_index: int,
) -> OpenInterestLevelScoreResultV0 | None:
    if _is_bitcoin_instrument(instrument_id):
        return None
    lag_idx = epoch_index - signal_lag_bars
    if lag_idx < 0:
        return None
    raw_level = _parse_open_interest(open_interest_values[lag_idx])
    if raw_level is None:
        return OpenInterestLevelScoreResultV0(
            instrument_id=instrument_id,
            open_interest_level=float("nan"),
            warmup_complete=False,
            score_status=OpenInterestLevelScoreStatusV0.MISSING_REQUIRED_OPEN_INTEREST,
            signal_eligible=False,
        )
    if not math.isfinite(raw_level):
        return OpenInterestLevelScoreResultV0(
            instrument_id=instrument_id,
            open_interest_level=raw_level,
            warmup_complete=False,
            score_status=OpenInterestLevelScoreStatusV0.NON_FINITE_INPUT,
            signal_eligible=False,
        )
    return OpenInterestLevelScoreResultV0(
        instrument_id=instrument_id,
        open_interest_level=raw_level,
        warmup_complete=True,
        score_status=OpenInterestLevelScoreStatusV0.COMPUTE_OK,
        signal_eligible=True,
    )


def rank_open_interest_levels_for_long_min_v0(
    scores: Sequence[OpenInterestLevelScoreResultV0],
) -> tuple[OpenInterestLevelScoreResultV0, ...]:
    return tuple(sorted(scores, key=lambda item: (item.open_interest_level, item.instrument_id)))


def rank_open_interest_levels_for_short_max_v0(
    scores: Sequence[OpenInterestLevelScoreResultV0],
) -> tuple[OpenInterestLevelScoreResultV0, ...]:
    return tuple(sorted(scores, key=lambda item: (-item.open_interest_level, item.instrument_id)))


def _cross_sectional_median_level(
    scores: Sequence[OpenInterestLevelScoreResultV0],
) -> float:
    values = sorted(item.open_interest_level for item in scores)
    mid = len(values) // 2
    if len(values) % 2 == 1:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2.0


def select_open_interest_level_extreme_single_leg_v0(
    scores: Sequence[OpenInterestLevelScoreResultV0],
) -> OpenInterestLevelExtremeSelectionV0:
    if not scores:
        return OpenInterestLevelExtremeSelectionV0(
            leg=OpenInterestLevelLeg.FLAT,
            instrument_id=None,
            min_level_instrument_id=None,
            max_level_instrument_id=None,
            min_open_interest_level=None,
            max_open_interest_level=None,
        )
    median_level = _cross_sectional_median_level(scores)
    long_ranked = rank_open_interest_levels_for_long_min_v0(scores)
    short_ranked = rank_open_interest_levels_for_short_max_v0(scores)
    min_item = long_ranked[0]
    max_item = short_ranked[0]
    min_dev = abs(min_item.open_interest_level - median_level)
    max_dev = abs(max_item.open_interest_level - median_level)
    if min_dev > max_dev or (
        min_dev == max_dev and min_item.instrument_id <= max_item.instrument_id
    ):
        leg = OpenInterestLevelLeg.LONG_MIN_LEVEL
        selected_id = min_item.instrument_id
    else:
        leg = OpenInterestLevelLeg.SHORT_MAX_LEVEL
        selected_id = max_item.instrument_id
    return OpenInterestLevelExtremeSelectionV0(
        leg=leg,
        instrument_id=selected_id,
        min_level_instrument_id=min_item.instrument_id,
        max_level_instrument_id=max_item.instrument_id,
        min_open_interest_level=min_item.open_interest_level,
        max_open_interest_level=max_item.open_interest_level,
    )


def score_input_provenance_marker_v0() -> str:
    return "open_interest_level_score_input_lagged_observation_v0"
