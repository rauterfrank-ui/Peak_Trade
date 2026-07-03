"""Cross-sectional relative-strength v0 score computation.

Pure offline, deterministic score primitives for volatility-normalized
fixed-lookback log-return ranking. Reuses formula semantics aligned with
``momentum.MomentumStrategy`` (lookback return) and ``vol_regime_filter`` (rolling
log-return std) without importing strategy runtime paths.

Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

PACKAGE_MARKER = "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_SCORE_V0=true"

SCORE_FORMULA_VERSION = "volatility_normalized_fixed_lookback_log_return_v0"
SCORE_FORMULA_EXPRESSION = (
    "score_i = log_return_N(i) / max(vol_V(i), vol_epsilon); "
    "log_return_N(i) = ln(close_i[t-lag] / close_i[t-lag-N]); "
    "vol_V(i) = sample_stdev(ln(close_i[j]/close_i[j-1]) for j in (t-lag-V+1..t-lag]); "
    "lag = signal_lag_bars"
)


@dataclass(frozen=True)
class CrossSectionalScoreResultV0:
    instrument_id: str
    score: float
    log_return_n: float
    rolling_vol: float
    warmup_complete: bool


def _is_bitcoin_instrument(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return any(token in lowered for token in ("btc", "xbt", "bitcoin"))


def compute_log_return_n_v0(
    closes: Sequence[float],
    *,
    lookback_n: int,
    signal_lag_bars: int,
    epoch_index: int,
) -> float | None:
    """Fixed-lookback log return at epoch_index with signal lag applied."""
    lag_idx = epoch_index - signal_lag_bars
    base_idx = lag_idx - lookback_n
    if base_idx < 0 or lag_idx < 0 or lag_idx >= len(closes):
        return None
    base = closes[base_idx]
    current = closes[lag_idx]
    if base <= 0 or current <= 0:
        return None
    return math.log(current / base)


def compute_rolling_log_return_vol_v0(
    closes: Sequence[float],
    *,
    vol_window_v: int,
    signal_lag_bars: int,
    epoch_index: int,
) -> float | None:
    """Sample stdev of one-period log returns over vol_window_V ending at lagged index."""
    lag_idx = epoch_index - signal_lag_bars
    start = lag_idx - vol_window_v + 1
    if start < 1 or lag_idx >= len(closes):
        return None
    log_returns: list[float] = []
    for j in range(start, lag_idx + 1):
        prev_close = closes[j - 1]
        cur_close = closes[j]
        if prev_close <= 0 or cur_close <= 0:
            return None
        log_returns.append(math.log(cur_close / prev_close))
    if len(log_returns) < vol_window_v:
        return None
    mean = sum(log_returns) / len(log_returns)
    variance = sum((value - mean) ** 2 for value in log_returns) / len(log_returns)
    return math.sqrt(variance)


def compute_volatility_normalized_score_v0(
    closes: Sequence[float],
    *,
    lookback_n: int,
    vol_window_v: int,
    vol_epsilon: float,
    signal_lag_bars: int,
    epoch_index: int,
) -> tuple[float, float, float] | None:
    """Return (score, log_return_n, rolling_vol) or None when warmup incomplete."""
    log_return_n = compute_log_return_n_v0(
        closes,
        lookback_n=lookback_n,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index,
    )
    rolling_vol = compute_rolling_log_return_vol_v0(
        closes,
        vol_window_v=vol_window_v,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index,
    )
    if log_return_n is None or rolling_vol is None:
        return None
    denominator = max(rolling_vol, vol_epsilon)
    if denominator <= 0:
        return None
    score = log_return_n / denominator
    if not math.isfinite(score):
        return None
    return score, log_return_n, rolling_vol


def compute_instrument_score_v0(
    instrument_id: str,
    closes: Sequence[float],
    *,
    lookback_n: int,
    vol_window_v: int,
    vol_epsilon: float,
    signal_lag_bars: int,
    epoch_index: int,
) -> CrossSectionalScoreResultV0 | None:
    if _is_bitcoin_instrument(instrument_id):
        return None
    result = compute_volatility_normalized_score_v0(
        closes,
        lookback_n=lookback_n,
        vol_window_v=vol_window_v,
        vol_epsilon=vol_epsilon,
        signal_lag_bars=signal_lag_bars,
        epoch_index=epoch_index,
    )
    if result is None:
        return None
    score, log_return_n, rolling_vol = result
    return CrossSectionalScoreResultV0(
        instrument_id=instrument_id,
        score=score,
        log_return_n=log_return_n,
        rolling_vol=rolling_vol,
        warmup_complete=True,
    )


def rank_scores_deterministic_v0(
    scores: Sequence[CrossSectionalScoreResultV0],
) -> tuple[CrossSectionalScoreResultV0, ...]:
    """Descending score, ascending instrument_id tie-break on unrounded internal score."""
    return tuple(
        sorted(
            scores,
            key=lambda item: (-item.score, item.instrument_id),
        )
    )
