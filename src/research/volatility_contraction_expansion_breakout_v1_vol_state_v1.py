"""RV(24) + percentile-rank and ATR14 helpers for VCEB v1.

Authority is the preregistered measurement contract.
- Realized vol = close-to-close log-return sample stdev over exactly 24 returns
- Percentile = WEAK_LEQ empirical CDF over exactly 120 finite RV observations
- ATR(14)/close is used only for initial-stop sizing (exit), not admission
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.research.volatility_compression_breakout_v1_vol_state_v1 import (
    compute_atr20_v1,
    compute_percentile_rank_120_normalized_atr_v1,
    compute_true_range_v1,
    percentile_rank_weak_leq_empirical_cdf_v1,
)

RV_PERIOD_V1 = 24
PERCENTILE_LOOKBACK_BARS_V1 = 120
PERCENTILE_TIE_METHOD_V1 = "WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF"
RV_METHOD_V1 = "CLOSE_TO_CLOSE_LOG_RETURN_STDEV"
RV_NORMALIZATION_V1 = "NONE_RAW_STDEV"
ATR_PERIOD_V1 = 14
ATR_SMOOTHING_V1 = "SIMPLE_MOVING_AVERAGE_OF_TRUE_RANGE"
ATR_NORMALIZATION_V1 = "ATR_DIV_CLOSE"
VOL_STATE_OWNER = "research.volatility_contraction_expansion_breakout_v1_vol_state_v1"


def compute_close_to_close_log_returns_v1(close: pd.Series) -> pd.Series:
    """Natural log returns; first bar is NaN (no prior close)."""
    close_f = close.astype(float)
    prev = close_f.shift(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.log(close_f / prev)
    invalid = (~np.isfinite(close_f)) | (~np.isfinite(prev)) | (close_f <= 0.0) | (prev <= 0.0)
    out = out.where(~invalid, other=np.nan)
    return out.astype(float)


def compute_realized_volatility_24_v1(
    close: pd.Series,
    *,
    period: int = RV_PERIOD_V1,
) -> pd.Series:
    """Sample stdev of log returns over ``period`` bars; incomplete → NaN."""
    if period != RV_PERIOD_V1:
        raise ValueError("rv_period_must_match_preregistration")
    rets = compute_close_to_close_log_returns_v1(close)
    # pandas rolling std uses ddof=1 (sample); incomplete windows stay NaN.
    return rets.rolling(window=period, min_periods=period).std(ddof=1).astype(float)


def compute_percentile_rank_120_realized_vol_v1(
    realized_vol: pd.Series,
    *,
    lookback: int = PERCENTILE_LOOKBACK_BARS_V1,
) -> pd.Series:
    """Reuse the shared WEAK_LEQ rolling percentile helper on RV series."""
    if lookback != PERCENTILE_LOOKBACK_BARS_V1:
        raise ValueError("percentile_lookback_must_match_preregistration")
    return compute_percentile_rank_120_normalized_atr_v1(realized_vol, lookback=lookback)


def compute_atr14_v1(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    *,
    period: int = ATR_PERIOD_V1,
) -> pd.Series:
    """ATR as SMA of True Range over 14 bars (stop sizing only)."""
    if period != ATR_PERIOD_V1:
        raise ValueError("atr_period_must_match_preregistration")
    return compute_atr20_v1(high, low, close, period=period)


def compute_normalized_atr14_v1(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    *,
    period: int = ATR_PERIOD_V1,
) -> pd.Series:
    """normalized_atr14 = atr14 / close; fail-closed for non-positive close."""
    if period != ATR_PERIOD_V1:
        raise ValueError("atr_period_must_match_preregistration")
    atr = compute_atr14_v1(high, low, close, period=period)
    close_f = close.astype(float)
    out = atr / close_f
    invalid_close = (~np.isfinite(close_f)) | (close_f <= 0.0)
    out = out.where(~invalid_close, other=np.nan)
    out = out.where(np.isfinite(out), other=np.nan)
    return out.astype(float)


def compute_vol_state_panel_column_v1(
    data: pd.DataFrame,
    *,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> pd.DataFrame:
    """Return DataFrame with RV24, percentile_rank_120, and ATR14 columns."""
    for col in (high_col, low_col, close_col):
        if col not in data.columns:
            raise ValueError(f"missing_column:{col}")
    rv = compute_realized_volatility_24_v1(data[close_col])
    rank = compute_percentile_rank_120_realized_vol_v1(rv)
    atr = compute_atr14_v1(data[high_col], data[low_col], data[close_col])
    return pd.DataFrame(
        {
            "realized_volatility_24": rv,
            "percentile_rank_120": rank,
            "atr14": atr,
        },
        index=data.index,
    )


__all__ = [
    "ATR_NORMALIZATION_V1",
    "ATR_PERIOD_V1",
    "ATR_SMOOTHING_V1",
    "PERCENTILE_LOOKBACK_BARS_V1",
    "PERCENTILE_TIE_METHOD_V1",
    "RV_METHOD_V1",
    "RV_NORMALIZATION_V1",
    "RV_PERIOD_V1",
    "VOL_STATE_OWNER",
    "compute_atr14_v1",
    "compute_close_to_close_log_returns_v1",
    "compute_normalized_atr14_v1",
    "compute_percentile_rank_120_realized_vol_v1",
    "compute_realized_volatility_24_v1",
    "compute_true_range_v1",
    "compute_vol_state_panel_column_v1",
    "percentile_rank_weak_leq_empirical_cdf_v1",
]
