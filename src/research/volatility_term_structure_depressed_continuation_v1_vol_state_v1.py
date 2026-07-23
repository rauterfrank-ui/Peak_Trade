"""Short/long RV term-structure helpers for VTDC v1.

Reuses the same short/long RV ratio + percentile estimators as VTSR (identical
vol family / horizons). Owner surface is VTDC-specific.
"""

from __future__ import annotations

from src.research.volatility_term_structure_reversion_v1_vol_state_v1 import (
    ATR_NORMALIZATION_V1,
    ATR_PERIOD_V1,
    ATR_SMOOTHING_V1,
    PERCENTILE_LOOKBACK_BARS_V1,
    PERCENTILE_TIE_METHOD_V1,
    RATIO_METRIC_NAME_V1,
    RV_LONG_HORIZON_COMPLETED_BARS_V1,
    RV_METHOD_V1,
    RV_NORMALIZATION_V1,
    RV_SHORT_HORIZON_COMPLETED_BARS_V1,
    VOL_ESTIMATOR_FAMILY_V1,
    compute_atr14_v1,
    compute_close_to_close_log_returns_v1,
    compute_normalized_atr14_v1,
    compute_percentile_rank_120_rv_term_structure_ratio_v1,
    compute_realized_volatility_long_48_v1,
    compute_realized_volatility_period_v1,
    compute_realized_volatility_short_8_v1,
    compute_rv_term_structure_ratio_short_over_long_v1,
    compute_vol_state_panel_column_v1,
    percentile_rank_weak_leq_empirical_cdf_v1,
)

VOL_STATE_OWNER = "research.volatility_term_structure_depressed_continuation_v1_vol_state_v1"

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
