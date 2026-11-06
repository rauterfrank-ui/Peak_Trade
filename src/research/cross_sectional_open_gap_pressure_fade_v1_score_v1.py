"""Cross-sectional open-gap pressure fade v1 score primitives.

Deterministic research-only score for
``CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1``.

Score family: negated mean open-to-prior-close gap over a frozen fixed lookback
(no vol normalization, no parameter grid, no quantile selection).

Does not authorize evaluation, holdout, runtime, orders, or Master-V2/Double-Play
mutation. Does not consume development run slots.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1_SCORE_V1=true"

STRATEGY_ID = "cross_sectional_open_gap_pressure_fade"
STRATEGY_IDENTITY = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1"
SIGNAL_FAMILY = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE"
HYPOTHESIS_ID = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_NON_BITCOIN_PERPETUALS_V1"
PROGRAM_ID = "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_RESEARCH_PROGRAM_V1"
SCORE_FORMULA_VERSION = "negated_mean_open_gap_fixed_lookback_v1"
SCORE_FORMULA_EXPRESSION = (
    "for each lagged bar b in lookback_N requiring prior close c_prev: "
    "if any of open_b,c_prev non-finite or c_prev<=0 then ineligible; "
    "gap_b=log(open_b/c_prev); score_i=-mean(gap_b); "
    "if score_i==0 then ineligible; "
    "rank by score_desc then instrument_id_asc; select single top1"
)
POLARITY = "OPEN_GAP_PRESSURE_FADE_NEGATED_MEAN_GAP"

# Frozen non-grid parameters from preregistered measurement contract.
DEFAULT_LOOKBACK_N = 30
DEFAULT_SIGNAL_LAG_BARS = 1
DEFAULT_MIN_ELIGIBLE_MEMBERS_FOR_RANK = 5
DEFAULT_SELECTION_COUNT_FIXED_N = 1
DEFAULT_REBALANCE_INTERVAL_BARS = 5
VOL_NORMALIZATION = False
BTC_EXCLUDED = True
SPOT_EXCLUDED = True
INSTRUMENT_CLASS = "LINEAR_USDT_PERPETUAL"


@dataclass(frozen=True)
class CrossSectionalOpenGapScoreResultV1:
    instrument_id: str
    score: float
    mean_open_gap: float
    lookback_bars_used: int
    warmup_complete: bool


def _is_bitcoin_instrument(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return any(token in lowered for token in ("btc", "xbt", "bitcoin"))


def _is_spot_instrument(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return "spot" in lowered or ":spot:" in lowered


def is_eligible_universe_instrument_v1(instrument_id: str) -> bool:
    """Non-BTC linear USDT perpetual universe binding (fail-closed)."""
    if not instrument_id:
        return False
    lowered = instrument_id.lower()
    if BTC_EXCLUDED and _is_bitcoin_instrument(instrument_id):
        return False
    if SPOT_EXCLUDED and _is_spot_instrument(instrument_id):
        return False
    if "linear_perpetual" not in lowered:
        return False
    if "usdt" not in lowered:
        return False
    return True


def compute_bar_open_gap_v1(*, open_b: float, close_prev: float) -> float | None:
    """Single-bar open gap ``log(open_b / close_{b-1})``; None if ineligible."""
    if not (math.isfinite(open_b) and math.isfinite(close_prev)):
        return None
    if close_prev <= 0.0 or open_b <= 0.0:
        return None
    gap = math.log(open_b / close_prev)
    if not math.isfinite(gap):
        return None
    return gap


def compute_negated_mean_open_gap_v1(
    opens: Sequence[float],
    closes: Sequence[float],
    *,
    lookback_n: int,
    signal_lag_bars: int,
    epoch_index: int,
) -> tuple[float, float] | None:
    """Return ``(score, mean_gap)`` over lagged lookback, or None if ineligible.

    PIT-safe: uses only opens/closes at indices ``<= epoch_index - signal_lag_bars``.
    Each gap uses ``close[b-1]`` (prior close), never the current bar close as prior.
    """
    if lookback_n <= 0 or signal_lag_bars < 0:
        return None
    if len(opens) != len(closes):
        return None
    lag_idx = epoch_index - signal_lag_bars
    first_idx = lag_idx - lookback_n + 1
    # Prior close for first gap requires index first_idx - 1 >= 0.
    if first_idx < 1 or lag_idx < 0 or lag_idx >= len(opens) or lag_idx >= len(closes):
        return None

    gaps: list[float] = []
    for bar_idx in range(first_idx, lag_idx + 1):
        gap = compute_bar_open_gap_v1(
            open_b=opens[bar_idx],
            close_prev=closes[bar_idx - 1],
        )
        if gap is None:
            return None
        gaps.append(gap)

    if len(gaps) != lookback_n:
        return None
    mean_gap = sum(gaps) / float(lookback_n)
    if not math.isfinite(mean_gap):
        return None
    score = -mean_gap
    if not math.isfinite(score):
        return None
    # Fail-closed: score_zero_ineligible.
    if score == 0.0:
        return None
    return score, mean_gap


def compute_instrument_score_v1(
    instrument_id: str,
    opens: Sequence[float],
    closes: Sequence[float],
    *,
    lookback_n: int = DEFAULT_LOOKBACK_N,
    signal_lag_bars: int = DEFAULT_SIGNAL_LAG_BARS,
    epoch_index: int,
) -> CrossSectionalOpenGapScoreResultV1 | None:
    if not is_eligible_universe_instrument_v1(instrument_id):
        return None
    components = compute_negated_mean_open_gap_v1(
        opens,
        closes,
        lookback_n=lookback_n,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index,
    )
    if components is None:
        return None
    score, mean_gap = components
    return CrossSectionalOpenGapScoreResultV1(
        instrument_id=instrument_id,
        score=score,
        mean_open_gap=mean_gap,
        lookback_bars_used=lookback_n,
        warmup_complete=True,
    )


def rank_scores_deterministic_v1(
    scores: Sequence[CrossSectionalOpenGapScoreResultV1],
) -> tuple[CrossSectionalOpenGapScoreResultV1, ...]:
    """Descending score, ascending instrument_id tie-break."""
    return tuple(
        sorted(
            scores,
            key=lambda item: (-item.score, item.instrument_id),
        )
    )


def validate_lookback_n(lookback_n: int) -> bool:
    return lookback_n == DEFAULT_LOOKBACK_N


def validate_rebalance_interval_bars(rebalance_interval_bars: int) -> bool:
    return rebalance_interval_bars == DEFAULT_REBALANCE_INTERVAL_BARS


def validate_signal_lag_bars(signal_lag_bars: int) -> bool:
    return signal_lag_bars == DEFAULT_SIGNAL_LAG_BARS


__all__ = [
    "BTC_EXCLUDED",
    "DEFAULT_LOOKBACK_N",
    "DEFAULT_MIN_ELIGIBLE_MEMBERS_FOR_RANK",
    "DEFAULT_REBALANCE_INTERVAL_BARS",
    "DEFAULT_SELECTION_COUNT_FIXED_N",
    "DEFAULT_SIGNAL_LAG_BARS",
    "HYPOTHESIS_ID",
    "INSTRUMENT_CLASS",
    "PACKAGE_MARKER",
    "POLARITY",
    "PROGRAM_ID",
    "SCORE_FORMULA_EXPRESSION",
    "SCORE_FORMULA_VERSION",
    "SIGNAL_FAMILY",
    "SPOT_EXCLUDED",
    "STRATEGY_ID",
    "STRATEGY_IDENTITY",
    "VOL_NORMALIZATION",
    "CrossSectionalOpenGapScoreResultV1",
    "compute_bar_open_gap_v1",
    "compute_instrument_score_v1",
    "compute_negated_mean_open_gap_v1",
    "is_eligible_universe_instrument_v1",
    "rank_scores_deterministic_v1",
    "validate_lookback_n",
    "validate_rebalance_interval_bars",
    "validate_signal_lag_bars",
]
