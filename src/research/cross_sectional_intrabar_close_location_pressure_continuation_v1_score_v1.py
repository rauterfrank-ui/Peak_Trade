"""Cross-sectional intrabar CLV pressure continuation v1 score primitives.

Deterministic research-only score for
``CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_V1``.

Score family: mean intrabar close-location value over a frozen fixed lookback
(no vol normalization, no parameter grid).

Does not authorize evaluation, holdout, runtime, orders, or Master-V2/Double-Play
mutation. Does not consume development run slots.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_V1_SCORE_V1=true"

STRATEGY_ID = "cross_sectional_intrabar_close_location_pressure_continuation"
STRATEGY_IDENTITY = "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_V1"
SIGNAL_FAMILY = "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE"
HYPOTHESIS_ID = (
    "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
)
PROGRAM_ID = "CROSS_SECTIONAL_INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION_RESEARCH_PROGRAM_V1"
SCORE_FORMULA_VERSION = "mean_intrabar_close_location_value_fixed_lookback_v1"
SCORE_FORMULA_EXPRESSION = (
    "for each lagged bar b in lookback_N: range=high-low; "
    "clv_b=0 if range==0 else (2*close-high-low)/range; "
    "if any OHLC non-finite then ineligible; score_i=mean(clv_b); "
    "if score_i==0 then ineligible; "
    "rank by score_desc then instrument_id_asc; select single top1"
)
POLARITY = "INTRABAR_CLOSE_LOCATION_PRESSURE_CONTINUATION"

# Frozen non-grid parameters from preregistered measurement contract.
DEFAULT_LOOKBACK_N = 36
DEFAULT_SIGNAL_LAG_BARS = 1
DEFAULT_MIN_ELIGIBLE_MEMBERS_FOR_RANK = 5
DEFAULT_SELECTION_COUNT_FIXED_N = 1
DEFAULT_REBALANCE_INTERVAL_BARS = 6
VOL_NORMALIZATION = False
BTC_EXCLUDED = True
SPOT_EXCLUDED = True
INSTRUMENT_CLASS = "LINEAR_USDT_PERPETUAL"


@dataclass(frozen=True)
class CrossSectionalIntrabarClvScoreResultV1:
    instrument_id: str
    score: float
    mean_clv: float
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


def compute_bar_clv_v1(*, high: float, low: float, close: float) -> float | None:
    """Single-bar close-location value; None if any OHLC non-finite."""
    if not (math.isfinite(high) and math.isfinite(low) and math.isfinite(close)):
        return None
    bar_range = high - low
    if bar_range == 0.0:
        return 0.0
    clv = (2.0 * close - high - low) / bar_range
    if not math.isfinite(clv):
        return None
    return clv


def compute_mean_clv_over_lookback_v1(
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    *,
    lookback_n: int,
    signal_lag_bars: int,
    epoch_index: int,
) -> float | None:
    """Mean CLV over lagged lookback window (PIT-safe).

    Uses only OHLC at indices ``<= epoch_index - signal_lag_bars``.
    Zero-range bars contribute CLV=0. Non-finite OHLC → ineligible (None).
    """
    if lookback_n <= 0 or signal_lag_bars < 0:
        return None
    if not (len(highs) == len(lows) == len(closes)):
        return None
    lag_idx = epoch_index - signal_lag_bars
    first_idx = lag_idx - lookback_n + 1
    if first_idx < 0 or lag_idx < 0 or lag_idx >= len(closes):
        return None

    clvs: list[float] = []
    for idx in range(first_idx, lag_idx + 1):
        clv = compute_bar_clv_v1(high=highs[idx], low=lows[idx], close=closes[idx])
        if clv is None:
            return None
        clvs.append(clv)

    if len(clvs) != lookback_n:
        return None
    mean_clv = sum(clvs) / float(lookback_n)
    if not math.isfinite(mean_clv):
        return None
    return mean_clv


def compute_instrument_score_v1(
    instrument_id: str,
    highs: Sequence[float],
    lows: Sequence[float],
    closes: Sequence[float],
    *,
    lookback_n: int = DEFAULT_LOOKBACK_N,
    signal_lag_bars: int = DEFAULT_SIGNAL_LAG_BARS,
    epoch_index: int,
) -> CrossSectionalIntrabarClvScoreResultV1 | None:
    if not is_eligible_universe_instrument_v1(instrument_id):
        return None
    mean_clv = compute_mean_clv_over_lookback_v1(
        highs,
        lows,
        closes,
        lookback_n=lookback_n,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index,
    )
    if mean_clv is None:
        return None
    # Fail-closed: score_zero_ineligible.
    if mean_clv == 0.0:
        return None
    return CrossSectionalIntrabarClvScoreResultV1(
        instrument_id=instrument_id,
        score=mean_clv,
        mean_clv=mean_clv,
        lookback_bars_used=lookback_n,
        warmup_complete=True,
    )


def rank_scores_deterministic_v1(
    scores: Sequence[CrossSectionalIntrabarClvScoreResultV1],
) -> tuple[CrossSectionalIntrabarClvScoreResultV1, ...]:
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
    "CrossSectionalIntrabarClvScoreResultV1",
    "compute_bar_clv_v1",
    "compute_instrument_score_v1",
    "compute_mean_clv_over_lookback_v1",
    "is_eligible_universe_instrument_v1",
    "rank_scores_deterministic_v1",
    "validate_lookback_n",
    "validate_rebalance_interval_bars",
    "validate_signal_lag_bars",
]
