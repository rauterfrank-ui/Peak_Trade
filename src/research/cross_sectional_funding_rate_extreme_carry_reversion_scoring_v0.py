"""Cross-sectional funding-rate extreme carry/reversion v0 scoring primitives.

Reuse-first shim over carry scoring and absolute-funding-extreme dislocation gates.
Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

from src.research.cross_sectional_funding_rate_carry_scoring_v0 import (
    SCORE_FORMULA_EXPRESSION,
    SCORE_FORMULA_VERSION,
    FundingCarryLeg,
    FundingCarryScoreResultV0,
    FundingExtremeSelectionV0,
    compute_instrument_funding_score_v0,
    rank_funding_scores_for_long_low_v0,
    rank_funding_scores_for_short_high_v0,
    select_funding_extreme_single_leg_v0,
)
from src.research.cross_sectional_funding_rate_dispersion_zscore_reversion_scoring_v0 import (
    FUNDING_SIGNAL_LAG,
    MIN_PANEL_FUNDING_DISPERSION,
    compute_instrument_funding_zscore_score_v0,
    compute_panel_dispersion_snapshot_v0,
    select_funding_zscore_extreme_single_leg_v0,
)
from src.research.cross_sectional_funding_rate_extreme_carry_reversion_absolute_funding_extreme_binding_v0 import (
    MIN_ABS_ZSCORE_FOR_DISLOCATION,
    MIN_PERCENTILE_DISLOCATION,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_FUNDING_RATE_EXTREME_CARRY_REVERSION_SCORING_V0=true"

MIN_ABS_ZSCORE_FOR_ENTRY = MIN_ABS_ZSCORE_FOR_DISLOCATION
FUNDING_SMOOTHING_WINDOW_BARS = 1

__all__ = [
    "SCORE_FORMULA_EXPRESSION",
    "SCORE_FORMULA_VERSION",
    "FundingCarryLeg",
    "FundingCarryScoreResultV0",
    "FundingExtremeSelectionV0",
    "FUNDING_SIGNAL_LAG",
    "FUNDING_SMOOTHING_WINDOW_BARS",
    "MIN_ABS_ZSCORE_FOR_ENTRY",
    "MIN_ABS_ZSCORE_FOR_DISLOCATION",
    "MIN_PERCENTILE_DISLOCATION",
    "MIN_PANEL_FUNDING_DISPERSION",
    "compute_instrument_funding_score_v0",
    "compute_instrument_funding_zscore_score_v0",
    "compute_panel_dispersion_snapshot_v0",
    "rank_funding_scores_for_long_low_v0",
    "rank_funding_scores_for_short_high_v0",
    "select_funding_extreme_single_leg_v0",
    "select_funding_zscore_extreme_single_leg_v0",
]
