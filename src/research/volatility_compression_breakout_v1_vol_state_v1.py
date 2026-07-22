"""ATR20/close and percentile-rank vol-state helpers for VCB v1.

Authority is the preregistered measurement contract, NOT vol_breakout._rolling_last_pct_rank.

ATR smoothing bound by operator implementation GO:
- True Range = max(high-low, |high-prev_close|, |low-prev_close|)
- atr20 = simple mean of TR over exactly 20 valid bars (incomplete window → invalid)
- normalized_atr20 = atr20 / close; close <= 0 or non-finite → invalid

Percentile:
- window size exactly 120 valid normalized_atr20 observations including current
- rank = count(window_values <= current_value) / 120
- tie method WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF
- midrank / strict-less-than / historical-only window forbidden
"""

from __future__ import annotations

import math
from typing import Optional, Sequence

import numpy as np
import pandas as pd

ATR_PERIOD_V1 = 20
PERCENTILE_LOOKBACK_BARS_V1 = 120
PERCENTILE_TIE_METHOD_V1 = "WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF"
ATR_SMOOTHING_V1 = "SIMPLE_MOVING_AVERAGE_OF_TRUE_RANGE"
ATR_NORMALIZATION_V1 = "ATR_DIV_CLOSE"
VOL_STATE_OWNER = "research.volatility_compression_breakout_v1_vol_state_v1"


def compute_true_range_v1(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
) -> pd.Series:
    """Canonical True Range; first bar uses high-low only (no prior close)."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    # Bar 0: only high-low is defined; abs(diff to missing prev) is NaN → use high-low.
    if len(tr) > 0 and pd.isna(prev_close.iloc[0]):
        tr.iloc[0] = (
            float(high.iloc[0] - low.iloc[0])
            if np.isfinite(high.iloc[0]) and np.isfinite(low.iloc[0])
            else float("nan")
        )
    return tr.astype(float)


def compute_atr20_v1(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    *,
    period: int = ATR_PERIOD_V1,
) -> pd.Series:
    """ATR as SMA of True Range over ``period`` bars; incomplete → NaN."""
    if period < 1:
        raise ValueError("atr_period_below_minimum")
    tr = compute_true_range_v1(high.astype(float), low.astype(float), close.astype(float))
    return tr.rolling(window=period, min_periods=period).mean()


def compute_normalized_atr20_v1(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    *,
    period: int = ATR_PERIOD_V1,
) -> pd.Series:
    """normalized_atr20 = atr20 / close; fail-closed for non-positive/non-finite close."""
    atr = compute_atr20_v1(high, low, close, period=period)
    close_f = close.astype(float)
    out = atr / close_f
    invalid_close = (~np.isfinite(close_f)) | (close_f <= 0.0)
    out = out.where(~invalid_close, other=np.nan)
    out = out.where(np.isfinite(out), other=np.nan)
    return out.astype(float)


def percentile_rank_weak_leq_empirical_cdf_v1(
    window_values: Sequence[float],
    *,
    current_value: float,
) -> Optional[float]:
    """count(window <= current) / len(window); requires exact finite window."""
    if len(window_values) == 0:
        return None
    if not math.isfinite(current_value):
        return None
    values = list(window_values)
    if any(not math.isfinite(v) for v in values):
        return None
    count_leq = sum(1 for v in values if v <= current_value)
    return float(count_leq) / float(len(values))


def compute_percentile_rank_120_normalized_atr_v1(
    normalized_atr: pd.Series,
    *,
    lookback: int = PERCENTILE_LOOKBACK_BARS_V1,
) -> pd.Series:
    """Rolling percentile rank with current value included and <= tie semantics.

    Requires exactly ``lookback`` finite observations in the inclusive window
    ending at the current bar. No imputation.
    """
    if lookback < 1:
        raise ValueError("percentile_lookback_below_minimum")
    values = normalized_atr.to_numpy(dtype=np.float64, copy=False)
    n = len(values)
    out = np.full(n, np.nan, dtype=np.float64)
    for end in range(n):
        start = end - lookback + 1
        if start < 0:
            continue
        window = values[start : end + 1]
        if window.shape[0] != lookback:
            continue
        if not np.isfinite(window).all():
            continue
        current = float(window[-1])
        count_leq = int(np.sum(window <= current))
        out[end] = float(count_leq) / float(lookback)
    return pd.Series(out, index=normalized_atr.index, dtype=np.float64, name="percentile_rank_120")


def compute_vol_state_panel_column_v1(
    data: pd.DataFrame,
    *,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> pd.DataFrame:
    """Return DataFrame with normalized_atr20 and percentile_rank_120 columns."""
    for col in (high_col, low_col, close_col):
        if col not in data.columns:
            raise ValueError(f"missing_column:{col}")
    norm = compute_normalized_atr20_v1(data[high_col], data[low_col], data[close_col])
    rank = compute_percentile_rank_120_normalized_atr_v1(norm)
    return pd.DataFrame(
        {"normalized_atr20": norm, "percentile_rank_120": rank},
        index=data.index,
    )


__all__ = [
    "ATR_NORMALIZATION_V1",
    "ATR_PERIOD_V1",
    "ATR_SMOOTHING_V1",
    "PERCENTILE_LOOKBACK_BARS_V1",
    "PERCENTILE_TIE_METHOD_V1",
    "VOL_STATE_OWNER",
    "compute_atr20_v1",
    "compute_normalized_atr20_v1",
    "compute_percentile_rank_120_normalized_atr_v1",
    "compute_true_range_v1",
    "compute_vol_state_panel_column_v1",
    "percentile_rank_weak_leq_empirical_cdf_v1",
]
