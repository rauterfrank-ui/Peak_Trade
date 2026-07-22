"""ATR14/close and percentile-rank vol-state helpers for VDB v1.

Reuses the parameterized True-Range / SMA-ATR and WEAK_LEQ empirical-CDF
percentile helpers from the shared VCB vol-state module (math authority only).
ATR period is frozen at 14 by the VDB measurement contract.
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

ATR_PERIOD_V1 = 14
PERCENTILE_LOOKBACK_BARS_V1 = 120
PERCENTILE_TIE_METHOD_V1 = "WEAK_LESS_THAN_OR_EQUAL_EMPIRICAL_CDF"
ATR_SMOOTHING_V1 = "SIMPLE_MOVING_AVERAGE_OF_TRUE_RANGE"
ATR_NORMALIZATION_V1 = "ATR_DIV_CLOSE"
VOL_STATE_OWNER = "research.volatility_decay_breakout_v1_vol_state_v1"


def compute_atr14_v1(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    *,
    period: int = ATR_PERIOD_V1,
) -> pd.Series:
    """ATR as SMA of True Range over ``period`` bars (default 14); incomplete → NaN."""
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
    """normalized_atr = atr14 / close; fail-closed for non-positive/non-finite close."""
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
    """Return DataFrame with normalized_atr14 and percentile_rank_120 columns."""
    for col in (high_col, low_col, close_col):
        if col not in data.columns:
            raise ValueError(f"missing_column:{col}")
    norm = compute_normalized_atr14_v1(data[high_col], data[low_col], data[close_col])
    rank = compute_percentile_rank_120_normalized_atr_v1(norm)
    return pd.DataFrame(
        {"normalized_atr14": norm, "percentile_rank_120": rank},
        index=data.index,
    )


__all__ = [
    "ATR_NORMALIZATION_V1",
    "ATR_PERIOD_V1",
    "ATR_SMOOTHING_V1",
    "PERCENTILE_LOOKBACK_BARS_V1",
    "PERCENTILE_TIE_METHOD_V1",
    "VOL_STATE_OWNER",
    "compute_atr14_v1",
    "compute_normalized_atr14_v1",
    "compute_percentile_rank_120_normalized_atr_v1",
    "compute_true_range_v1",
    "compute_vol_state_panel_column_v1",
    "percentile_rank_weak_leq_empirical_cdf_v1",
]
