"""RV(24) + percentile-rank and ATR14 helpers for VEFCF v1.

Reuses the frozen VCEB RV/percentile/ATR helpers (identical estimator contract).
Authority remains the VEFCF preregistered measurement contract.
"""

from __future__ import annotations

import pandas as pd

from src.research.volatility_contraction_expansion_breakout_v1_vol_state_v1 import (
    ATR_NORMALIZATION_V1,
    ATR_PERIOD_V1,
    ATR_SMOOTHING_V1,
    PERCENTILE_LOOKBACK_BARS_V1,
    PERCENTILE_TIE_METHOD_V1,
    RV_METHOD_V1,
    RV_NORMALIZATION_V1,
    RV_PERIOD_V1,
    compute_atr14_v1,
    compute_close_to_close_log_returns_v1,
    compute_normalized_atr14_v1,
    compute_percentile_rank_120_realized_vol_v1,
    compute_realized_volatility_24_v1,
    compute_vol_state_panel_column_v1,
    percentile_rank_weak_leq_empirical_cdf_v1,
)

VOL_STATE_OWNER = "research.volatility_expansion_failed_continuation_fade_v1_vol_state_v1"

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
    "compute_vol_state_panel_column_v1",
    "percentile_rank_weak_leq_empirical_cdf_v1",
]


def _assert_frame(data: pd.DataFrame) -> None:
    if not isinstance(data, pd.DataFrame):
        raise TypeError("expected_dataframe")
