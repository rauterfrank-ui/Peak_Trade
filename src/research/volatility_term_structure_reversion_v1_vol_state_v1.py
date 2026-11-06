"""Short/long RV term-structure ratio + percentile helpers for VTSR v1.

Authority is the preregistered measurement contract admission_mechanism.vol_estimator.
- short RV = close-to-close log-return sample stdev over exactly 8 returns
- long RV = close-to-close log-return sample stdev over exactly 48 returns
- ratio = short / long (raw stdev; no extra normalization)
- percentile = WEAK_LEQ empirical CDF of the ratio over exactly 120 finite observations
- ATR(14) reused for initial-stop sizing only (exit), not admission
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.research.volatility_contraction_expansion_breakout_v1_vol_state_v1 import (
    ATR_NORMALIZATION_V1,
    ATR_PERIOD_V1,
    ATR_SMOOTHING_V1,
    PERCENTILE_LOOKBACK_BARS_V1,
    PERCENTILE_TIE_METHOD_V1,
    RV_METHOD_V1,
    RV_NORMALIZATION_V1,
    compute_atr14_v1,
    compute_close_to_close_log_returns_v1,
    compute_normalized_atr14_v1,
    percentile_rank_weak_leq_empirical_cdf_v1,
)
from src.research.volatility_compression_breakout_v1_vol_state_v1 import (
    compute_percentile_rank_120_normalized_atr_v1,
)

RV_SHORT_HORIZON_COMPLETED_BARS_V1 = 8
RV_LONG_HORIZON_COMPLETED_BARS_V1 = 48
RATIO_METRIC_NAME_V1 = "rv_term_structure_ratio_short_over_long"
VOL_ESTIMATOR_FAMILY_V1 = "REALIZED_VOLATILITY_TERM_STRUCTURE"
VOL_STATE_OWNER = "research.volatility_term_structure_reversion_v1_vol_state_v1"


def compute_realized_volatility_period_v1(
    close: pd.Series,
    *,
    period: int,
) -> pd.Series:
    """Sample stdev of log returns over ``period`` bars; incomplete → NaN."""
    if period < 1:
        raise ValueError("rv_period_below_minimum")
    rets = compute_close_to_close_log_returns_v1(close)
    return rets.rolling(window=period, min_periods=period).std(ddof=1).astype(float)


def compute_realized_volatility_short_8_v1(close: pd.Series) -> pd.Series:
    return compute_realized_volatility_period_v1(close, period=RV_SHORT_HORIZON_COMPLETED_BARS_V1)


def compute_realized_volatility_long_48_v1(close: pd.Series) -> pd.Series:
    return compute_realized_volatility_period_v1(close, period=RV_LONG_HORIZON_COMPLETED_BARS_V1)


def compute_rv_term_structure_ratio_short_over_long_v1(close: pd.Series) -> pd.Series:
    """short_rv / long_rv; non-finite or non-positive long → NaN (fail-closed)."""
    short = compute_realized_volatility_short_8_v1(close)
    long = compute_realized_volatility_long_48_v1(close)
    short_f = short.astype(float)
    long_f = long.astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = short_f / long_f
    invalid = (
        (~np.isfinite(short_f)) | (~np.isfinite(long_f)) | (long_f <= 0.0) | (~np.isfinite(ratio))
    )
    return ratio.where(~invalid, other=np.nan).astype(float)


def compute_percentile_rank_120_rv_term_structure_ratio_v1(
    ratio: pd.Series,
    *,
    lookback: int = PERCENTILE_LOOKBACK_BARS_V1,
) -> pd.Series:
    """WEAK_LEQ rolling percentile of the term-structure ratio (exact 120 finite)."""
    if lookback != PERCENTILE_LOOKBACK_BARS_V1:
        raise ValueError("percentile_lookback_must_match_preregistration")
    return compute_percentile_rank_120_normalized_atr_v1(ratio, lookback=lookback)


def compute_vol_state_panel_column_v1(
    data: pd.DataFrame,
    *,
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> pd.DataFrame:
    """Return DataFrame with short/long RV, ratio, percentile, and ATR14 columns."""
    for col in (high_col, low_col, close_col):
        if col not in data.columns:
            raise ValueError(f"missing_column:{col}")
    close = data[close_col]
    short = compute_realized_volatility_short_8_v1(close)
    long = compute_realized_volatility_long_48_v1(close)
    ratio = compute_rv_term_structure_ratio_short_over_long_v1(close)
    rank = compute_percentile_rank_120_rv_term_structure_ratio_v1(ratio)
    atr = compute_atr14_v1(data[high_col], data[low_col], close)
    return pd.DataFrame(
        {
            "realized_volatility_short_8": short,
            "realized_volatility_long_48": long,
            "rv_term_structure_ratio_short_over_long": ratio,
            "rv_term_structure_ratio_percentile_120": rank,
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
    "RATIO_METRIC_NAME_V1",
    "RV_LONG_HORIZON_COMPLETED_BARS_V1",
    "RV_METHOD_V1",
    "RV_NORMALIZATION_V1",
    "RV_SHORT_HORIZON_COMPLETED_BARS_V1",
    "VOL_ESTIMATOR_FAMILY_V1",
    "VOL_STATE_OWNER",
    "compute_atr14_v1",
    "compute_close_to_close_log_returns_v1",
    "compute_normalized_atr14_v1",
    "compute_percentile_rank_120_rv_term_structure_ratio_v1",
    "compute_realized_volatility_long_48_v1",
    "compute_realized_volatility_period_v1",
    "compute_realized_volatility_short_8_v1",
    "compute_rv_term_structure_ratio_short_over_long_v1",
    "compute_vol_state_panel_column_v1",
    "percentile_rank_weak_leq_empirical_cdf_v1",
]
