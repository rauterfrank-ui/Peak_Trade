"""Cross-sectional path-efficiency continuation v1 score primitives.

Deterministic research-only score for
``CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_V1``.

Score family: Kaufman path-efficiency ratio times sign(net log return) over a
frozen fixed lookback (no vol normalization, no parameter grid).

Does not authorize evaluation, holdout, runtime, orders, or Master-V2/Double-Play
mutation. Does not consume development run slots.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_V1_SCORE_V1=true"

STRATEGY_ID = "cross_sectional_path_efficiency_continuation"
STRATEGY_IDENTITY = "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_V1"
SIGNAL_FAMILY = "CROSS_SECTIONAL_PATH_EFFICIENCY"
HYPOTHESIS_ID = "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_NON_BITCOIN_PERPETUALS_V1"
PROGRAM_ID = "CROSS_SECTIONAL_PATH_EFFICIENCY_CONTINUATION_RESEARCH_PROGRAM_V1"
SCORE_FORMULA_VERSION = "path_efficiency_ratio_times_sign_net_log_return_fixed_lookback_v1"
SCORE_FORMULA_EXPRESSION = (
    "net_i(t)=sum_{k=1..lookback_N} log(close_i[t-lag-k+1]/close_i[t-lag-k]); "
    "path_sum_i(t)=sum_{k=1..lookback_N} abs(log(...)); "
    "if path_sum_i==0 or sign(net_i)==0 then ineligible; "
    "ER_i=abs(net_i)/path_sum_i; score_i=ER_i*sign(net_i); "
    "rank by score_desc then instrument_id_asc; select single top1"
)
POLARITY = "PATH_EFFICIENCY_CONTINUATION_ER_TIMES_SIGN"

# Frozen non-grid parameters from preregistered measurement contract.
DEFAULT_LOOKBACK_N = 48
DEFAULT_SIGNAL_LAG_BARS = 1
DEFAULT_MIN_ELIGIBLE_MEMBERS_FOR_RANK = 5
DEFAULT_SELECTION_COUNT_FIXED_N = 1
DEFAULT_REBALANCE_INTERVAL_BARS = 8
VOL_NORMALIZATION = False
BTC_EXCLUDED = True
SPOT_EXCLUDED = True
INSTRUMENT_CLASS = "LINEAR_USDT_PERPETUAL"


@dataclass(frozen=True)
class CrossSectionalPathEfficiencyScoreResultV1:
    instrument_id: str
    score: float
    efficiency_ratio: float
    net_log_return: float
    path_sum: float
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


def compute_net_and_path_sum_v1(
    closes: Sequence[float],
    *,
    lookback_n: int,
    signal_lag_bars: int,
    epoch_index: int,
) -> tuple[float, float] | None:
    """Bar-wise net log return and path sum at epoch with lag (PIT-safe).

    Uses only closes at indices ``<= epoch_index - signal_lag_bars``.
    """
    if lookback_n <= 0 or signal_lag_bars < 0:
        return None
    lag_idx = epoch_index - signal_lag_bars
    base_idx = lag_idx - lookback_n
    if base_idx < 0 or lag_idx < 0 or lag_idx >= len(closes):
        return None

    net = 0.0
    path_sum = 0.0
    for k in range(1, lookback_n + 1):
        c_curr = closes[lag_idx - k + 1]
        c_prev = closes[lag_idx - k]
        if c_curr <= 0.0 or c_prev <= 0.0:
            return None
        if not math.isfinite(c_curr) or not math.isfinite(c_prev):
            return None
        bar_log = math.log(c_curr / c_prev)
        if not math.isfinite(bar_log):
            return None
        net += bar_log
        path_sum += abs(bar_log)

    if not math.isfinite(net) or not math.isfinite(path_sum):
        return None
    return net, path_sum


def compute_path_efficiency_score_components_v1(
    closes: Sequence[float],
    *,
    lookback_n: int,
    signal_lag_bars: int,
    epoch_index: int,
) -> tuple[float, float, float, float] | None:
    """Return ``(score, ER, net, path_sum)`` or None if ineligible/invalid."""
    components = compute_net_and_path_sum_v1(
        closes,
        lookback_n=lookback_n,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index,
    )
    if components is None:
        return None
    net, path_sum = components
    # Fail-closed eligibility: path_sum==0 or sign(net)==0 → ineligible.
    if path_sum == 0.0 or net == 0.0:
        return None
    efficiency_ratio = abs(net) / path_sum
    if not math.isfinite(efficiency_ratio) or efficiency_ratio < 0.0:
        return None
    sign = 1.0 if net > 0.0 else -1.0
    score = efficiency_ratio * sign
    if not math.isfinite(score) or score == 0.0:
        return None
    return score, efficiency_ratio, net, path_sum


def compute_instrument_score_v1(
    instrument_id: str,
    closes: Sequence[float],
    *,
    lookback_n: int = DEFAULT_LOOKBACK_N,
    signal_lag_bars: int = DEFAULT_SIGNAL_LAG_BARS,
    epoch_index: int,
) -> CrossSectionalPathEfficiencyScoreResultV1 | None:
    if not is_eligible_universe_instrument_v1(instrument_id):
        return None
    components = compute_path_efficiency_score_components_v1(
        closes,
        lookback_n=lookback_n,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index,
    )
    if components is None:
        return None
    score, efficiency_ratio, net, path_sum = components
    return CrossSectionalPathEfficiencyScoreResultV1(
        instrument_id=instrument_id,
        score=score,
        efficiency_ratio=efficiency_ratio,
        net_log_return=net,
        path_sum=path_sum,
        warmup_complete=True,
    )


def rank_scores_deterministic_v1(
    scores: Sequence[CrossSectionalPathEfficiencyScoreResultV1],
) -> tuple[CrossSectionalPathEfficiencyScoreResultV1, ...]:
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
    "CrossSectionalPathEfficiencyScoreResultV1",
    "compute_instrument_score_v1",
    "compute_net_and_path_sum_v1",
    "compute_path_efficiency_score_components_v1",
    "is_eligible_universe_instrument_v1",
    "rank_scores_deterministic_v1",
    "validate_lookback_n",
    "validate_rebalance_interval_bars",
    "validate_signal_lag_bars",
]
