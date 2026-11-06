"""Cross-sectional short-horizon return-reversal v1 score primitives.

Deterministic research-only score for
``CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_NON_BITCOIN_PERPETUALS_V1``.

Score family: negated raw trailing log return over frozen fixed lookback
(no vol normalization, no parameter grid).

Does not authorize evaluation, holdout, runtime, orders, or Master-V2/Double-Play
mutation. Does not consume development run slots.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1_SCORE_V1=true"

STRATEGY_ID = "cross_sectional_short_horizon_return_reversal"
STRATEGY_IDENTITY = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_V1"
SIGNAL_FAMILY = "CROSS_SECTIONAL_RETURN_REVERSAL"
HYPOTHESIS_ID = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_NON_BITCOIN_PERPETUALS_V1"
PROGRAM_ID = "CROSS_SECTIONAL_SHORT_HORIZON_RETURN_REVERSAL_RESEARCH_PROGRAM_V1"
DATASET_ID = "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_dev_pre_holdout_v1"
SCORE_FORMULA_VERSION = "negated_raw_trailing_log_return_fixed_lookback_v1"
SCORE_FORMULA_EXPRESSION = (
    "raw_i(t)=sum_{k=1..lookback_N} log(close_i[t-lag-k+1]/close_i[t-lag-k]); "
    "score_i(t)=-raw_i(t); rank by score_desc then instrument_id_asc; select single top1"
)
POLARITY = "REVERSAL_NEGATED_TRAILING_LOG_RETURN"

# Frozen non-grid parameters from preregistered measurement contract.
DEFAULT_LOOKBACK_N = 24
DEFAULT_SIGNAL_LAG_BARS = 1
DEFAULT_MIN_ELIGIBLE_MEMBERS_FOR_RANK = 5
DEFAULT_SELECTION_COUNT_FIXED_N = 1
DEFAULT_REBALANCE_INTERVAL_BARS = 4
VOL_NORMALIZATION = False
BTC_EXCLUDED = True
SPOT_EXCLUDED = True
INSTRUMENT_CLASS = "LINEAR_USDT_PERPETUAL"


@dataclass(frozen=True)
class CrossSectionalShortHorizonReturnReversalScoreResultV1:
    instrument_id: str
    score: float
    trailing_log_return: float
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


def compute_raw_trailing_log_return_v1(
    closes: Sequence[float],
    *,
    lookback_n: int,
    signal_lag_bars: int,
    epoch_index: int,
) -> float | None:
    """Raw fixed-lookback log return at epoch with lag (PIT-safe).

    Uses only closes at indices ``<= epoch_index - signal_lag_bars``.
    """
    if lookback_n <= 0 or signal_lag_bars < 0:
        return None
    lag_idx = epoch_index - signal_lag_bars
    base_idx = lag_idx - lookback_n
    if base_idx < 0 or lag_idx < 0 or lag_idx >= len(closes):
        return None
    base = closes[base_idx]
    current = closes[lag_idx]
    if not math.isfinite(base) or not math.isfinite(current):
        return None
    if base <= 0 or current <= 0:
        return None
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
) -> CrossSectionalShortHorizonReturnReversalScoreResultV1 | None:
    if not is_eligible_universe_instrument_v1(instrument_id):
        return None
    for value in closes:
        if not math.isfinite(float(value)):
            return None
    trailing = compute_raw_trailing_log_return_v1(
        closes,
        lookback_n=lookback_n,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index,
    )
    if trailing is None:
        return None
    score = -trailing
    if not math.isfinite(score):
        return None
    return CrossSectionalShortHorizonReturnReversalScoreResultV1(
        instrument_id=instrument_id,
        score=score,
        trailing_log_return=trailing,
        warmup_complete=True,
    )


def rank_scores_deterministic_v1(
    scores: Sequence[CrossSectionalShortHorizonReturnReversalScoreResultV1],
) -> tuple[CrossSectionalShortHorizonReturnReversalScoreResultV1, ...]:
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
