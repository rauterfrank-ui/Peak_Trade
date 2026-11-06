"""Cross-sectional relative-strength momentum v1 raw trailing-return score.

Deterministic research-only score primitives for
``CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1``.

Score family: raw trailing log return over fixed lookback (no vol normalization).
Does not authorize evaluation, holdout, runtime, orders, or Master-V2/Double-Play mutation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1_SCORE_V1=true"

STRATEGY_ID = "cross_sectional_relative_strength_momentum"
STRATEGY_IDENTITY = "CROSS_SECTIONAL_RELATIVE_STRENGTH_MOMENTUM_V1"
SIGNAL_FAMILY = "CROSS_SECTIONAL_MOMENTUM"
SCORE_FORMULA_VERSION = "raw_trailing_log_return_fixed_lookback_v1"
SCORE_FORMULA_EXPRESSION = (
    "score_i(t)=sum_{k=1..lookback_N} log(close_i[t-lag-k+1]/close_i[t-lag-k]); "
    "rank by score_desc then instrument_id_asc; select single top1"
)

# Frozen non-grid defaults from preregistered measurement contract / reused RS binding.
DEFAULT_LOOKBACK_N = 20
DEFAULT_SIGNAL_LAG_BARS = 1
DEFAULT_MIN_ELIGIBLE_MEMBERS_FOR_RANK = 5
DEFAULT_SELECTION_COUNT_FIXED_N = 1
DEFAULT_REBALANCE_INTERVAL_BARS = 1
LOOKBACK_N_CANDIDATES = (10, 20, 48)
REBALANCE_INTERVAL_BARS_CANDIDATES = (1, 4, 24)
VOL_NORMALIZATION = False


@dataclass(frozen=True)
class CrossSectionalMomentumScoreResultV1:
    instrument_id: str
    score: float
    trailing_log_return: float
    warmup_complete: bool


def _is_bitcoin_instrument(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return any(token in lowered for token in ("btc", "xbt", "bitcoin"))


def compute_raw_trailing_log_return_v1(
    closes: Sequence[float],
    *,
    lookback_n: int,
    signal_lag_bars: int,
    epoch_index: int,
) -> float | None:
    """Raw fixed-lookback log return at epoch with lag (telescoping sum of bar logs)."""
    if lookback_n <= 0 or signal_lag_bars < 0:
        return None
    lag_idx = epoch_index - signal_lag_bars
    base_idx = lag_idx - lookback_n
    if base_idx < 0 or lag_idx < 0 or lag_idx >= len(closes):
        return None
    base = closes[base_idx]
    current = closes[lag_idx]
    if base <= 0 or current <= 0:
        return None
    # Equivalent to sum_{k=1..N} log(close[t-lag-k+1]/close[t-lag-k]).
    score = math.log(current / base)
    if not math.isfinite(score):
        return None
    return score


def compute_instrument_score_v1(
    instrument_id: str,
    closes: Sequence[float],
    *,
    lookback_n: int,
    signal_lag_bars: int = DEFAULT_SIGNAL_LAG_BARS,
    epoch_index: int,
) -> CrossSectionalMomentumScoreResultV1 | None:
    if _is_bitcoin_instrument(instrument_id):
        return None
    trailing = compute_raw_trailing_log_return_v1(
        closes,
        lookback_n=lookback_n,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index,
    )
    if trailing is None:
        return None
    return CrossSectionalMomentumScoreResultV1(
        instrument_id=instrument_id,
        score=trailing,
        trailing_log_return=trailing,
        warmup_complete=True,
    )


def rank_scores_deterministic_v1(
    scores: Sequence[CrossSectionalMomentumScoreResultV1],
) -> tuple[CrossSectionalMomentumScoreResultV1, ...]:
    """Descending score, ascending instrument_id tie-break."""
    return tuple(
        sorted(
            scores,
            key=lambda item: (-item.score, item.instrument_id),
        )
    )


def validate_lookback_n(lookback_n: int) -> bool:
    return lookback_n in LOOKBACK_N_CANDIDATES


def validate_rebalance_interval_bars(rebalance_interval_bars: int) -> bool:
    return rebalance_interval_bars in REBALANCE_INTERVAL_BARS_CANDIDATES
