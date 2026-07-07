"""Absolute funding extreme binding for extreme carry/reversion v0 research scope.

Owner-bound readiness surface for panel z-score and percentile dislocation gates.
Reuses carry scoring and dispersion z-score primitives. Research-only; no authority effect.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from src.research.cross_sectional_funding_rate_carry_scoring_v0 import (
    FundingCarryLeg,
    FundingCarryScoreResultV0,
    compute_instrument_funding_score_v0,
    select_funding_extreme_single_leg_v0,
)
from src.research.cross_sectional_funding_rate_dispersion_zscore_reversion_scoring_v0 import (
    MIN_ABS_ZSCORE_FOR_ENTRY,
    MIN_PANEL_FUNDING_DISPERSION,
    compute_instrument_funding_zscore_score_v0,
    compute_panel_dispersion_snapshot_v0,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUNDING_RATE_EXTREME_CARRY_REVERSION_ABSOLUTE_FUNDING_EXTREME_BINDING_V0=true"
)
BINDING_OWNER = (
    "cross_sectional_funding_rate_extreme_carry_reversion_absolute_funding_extreme_binding_v0"
)
BINDING_VERSION = "v0"
STRATEGY_ID = "cross_sectional_funding_rate_extreme_carry_reversion"
STRATEGY_VERSION = "v0"

MIN_ABS_ZSCORE_FOR_DISLOCATION = MIN_ABS_ZSCORE_FOR_ENTRY
MIN_PERCENTILE_DISLOCATION = 0.90
FUNDING_SIGNAL_LAG = 1
FUNDING_SMOOTHING_WINDOW_BARS = 1

REUSED_CARRY_SCORING_OWNER = "cross_sectional_funding_rate_carry_scoring_v0"
REUSED_DISPERSION_ZSCORE_OWNER = (
    "cross_sectional_funding_rate_dispersion_zscore_reversion_scoring_v0"
)


class AbsoluteFundingExtremeBindingStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class AbsoluteFundingExtremeBindingResultV0:
    status: AbsoluteFundingExtremeBindingStatus
    reason_code: str
    selected_instrument_id: str | None
    selected_abs_zscore: float | None
    selected_percentile_dislocation: float | None
    min_abs_zscore_for_dislocation: float
    min_percentile_dislocation: float


def _percentile_dislocation(rank: int, count: int) -> float:
    if count <= 1:
        return 1.0
    return max(rank, count - rank + 1) / count


def materialize_absolute_funding_extreme_binding_v0() -> dict[str, object]:
    return {
        "binding_owner": BINDING_OWNER,
        "binding_version": BINDING_VERSION,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "feature_kind": "absolute_funding_extreme",
        "status": "BOUND",
        "dislocation_semantics": {
            "z_score_gate": True,
            "percentile_dislocation_gate": True,
            "rank_delta_forbidden": True,
            "absolute_funding_delta_forbidden": True,
        },
        "thresholds": {
            "min_abs_zscore_for_dislocation": MIN_ABS_ZSCORE_FOR_DISLOCATION,
            "min_percentile_dislocation": MIN_PERCENTILE_DISLOCATION,
            "min_panel_funding_dispersion": MIN_PANEL_FUNDING_DISPERSION,
        },
        "reuse_owners": {
            "carry_scoring_owner": REUSED_CARRY_SCORING_OWNER,
            "dispersion_zscore_owner": REUSED_DISPERSION_ZSCORE_OWNER,
        },
        "authority_effect": "NONE",
        "runtime_effect": "NONE",
        "order_effect": "NONE",
    }


def evaluate_absolute_funding_extreme_binding_v0(
    panel_funding_rates: Sequence[tuple[str, float | None]],
    *,
    epoch_index: int,
    binding: Mapping[str, object] | None = None,
) -> AbsoluteFundingExtremeBindingResultV0:
    """Fail-closed absolute funding dislocation gate for one panel epoch."""
    _ = binding or materialize_absolute_funding_extreme_binding_v0()
    if not panel_funding_rates:
        return AbsoluteFundingExtremeBindingResultV0(
            status=AbsoluteFundingExtremeBindingStatus.BLOCKED,
            reason_code="missing_panel_funding_rates",
            selected_instrument_id=None,
            selected_abs_zscore=None,
            selected_percentile_dislocation=None,
            min_abs_zscore_for_dislocation=MIN_ABS_ZSCORE_FOR_DISLOCATION,
            min_percentile_dislocation=MIN_PERCENTILE_DISLOCATION,
        )

    snapshot = compute_panel_dispersion_snapshot_v0(panel_funding_rates)
    if snapshot is None or not snapshot.dispersion_gate_passes:
        return AbsoluteFundingExtremeBindingResultV0(
            status=AbsoluteFundingExtremeBindingStatus.BLOCKED,
            reason_code="unknown_or_insufficient_panel_dispersion",
            selected_instrument_id=None,
            selected_abs_zscore=None,
            selected_percentile_dislocation=None,
            min_abs_zscore_for_dislocation=MIN_ABS_ZSCORE_FOR_DISLOCATION,
            min_percentile_dislocation=MIN_PERCENTILE_DISLOCATION,
        )

    zscore_scores = []
    carry_scores: list[FundingCarryScoreResultV0] = []
    for instrument_id, rate in panel_funding_rates:
        zscore = compute_instrument_funding_zscore_score_v0(
            instrument_id,
            panel_funding_rates,
            epoch_index=epoch_index,
        )
        if zscore is not None and zscore.signal_eligible and math.isfinite(zscore.z_score):
            zscore_scores.append(zscore)
        if rate is None or not math.isfinite(rate):
            continue
        series_len = max(epoch_index + 1, FUNDING_SIGNAL_LAG + 1)
        instrument_series = [rate] * series_len
        carry_score = compute_instrument_funding_score_v0(
            instrument_id,
            instrument_series,
            funding_smoothing_window_bars=FUNDING_SMOOTHING_WINDOW_BARS,
            signal_lag_bars=FUNDING_SIGNAL_LAG,
            epoch_index=epoch_index,
        )
        if carry_score is not None:
            carry_scores.append(carry_score)

    if not zscore_scores or not carry_scores:
        return AbsoluteFundingExtremeBindingResultV0(
            status=AbsoluteFundingExtremeBindingStatus.BLOCKED,
            reason_code="missing_or_unknown_dislocation_inputs",
            selected_instrument_id=None,
            selected_abs_zscore=None,
            selected_percentile_dislocation=None,
            min_abs_zscore_for_dislocation=MIN_ABS_ZSCORE_FOR_DISLOCATION,
            min_percentile_dislocation=MIN_PERCENTILE_DISLOCATION,
        )

    carry_selection = select_funding_extreme_single_leg_v0(carry_scores)
    if carry_selection.leg is FundingCarryLeg.FLAT or carry_selection.instrument_id is None:
        return AbsoluteFundingExtremeBindingResultV0(
            status=AbsoluteFundingExtremeBindingStatus.FAIL,
            reason_code="absolute_dislocation_below_threshold",
            selected_instrument_id=None,
            selected_abs_zscore=None,
            selected_percentile_dislocation=None,
            min_abs_zscore_for_dislocation=MIN_ABS_ZSCORE_FOR_DISLOCATION,
            min_percentile_dislocation=MIN_PERCENTILE_DISLOCATION,
        )

    selected_id = carry_selection.instrument_id
    selected_zscore = next(
        (item for item in zscore_scores if item.instrument_id == selected_id),
        None,
    )
    if selected_zscore is None:
        return AbsoluteFundingExtremeBindingResultV0(
            status=AbsoluteFundingExtremeBindingStatus.BLOCKED,
            reason_code="selected_instrument_dislocation_unknown",
            selected_instrument_id=selected_id,
            selected_abs_zscore=None,
            selected_percentile_dislocation=None,
            min_abs_zscore_for_dislocation=MIN_ABS_ZSCORE_FOR_DISLOCATION,
            min_percentile_dislocation=MIN_PERCENTILE_DISLOCATION,
        )

    abs_zscores = sorted((abs(item.z_score) for item in zscore_scores), reverse=True)
    selected_abs_zscore = abs(selected_zscore.z_score)
    rank = abs_zscores.index(selected_abs_zscore) + 1
    percentile_dislocation = _percentile_dislocation(rank, len(abs_zscores))

    if selected_abs_zscore < MIN_ABS_ZSCORE_FOR_DISLOCATION:
        return AbsoluteFundingExtremeBindingResultV0(
            status=AbsoluteFundingExtremeBindingStatus.FAIL,
            reason_code="absolute_dislocation_below_threshold",
            selected_instrument_id=selected_id,
            selected_abs_zscore=selected_abs_zscore,
            selected_percentile_dislocation=percentile_dislocation,
            min_abs_zscore_for_dislocation=MIN_ABS_ZSCORE_FOR_DISLOCATION,
            min_percentile_dislocation=MIN_PERCENTILE_DISLOCATION,
        )

    if percentile_dislocation < MIN_PERCENTILE_DISLOCATION:
        return AbsoluteFundingExtremeBindingResultV0(
            status=AbsoluteFundingExtremeBindingStatus.FAIL,
            reason_code="percentile_dislocation_below_threshold",
            selected_instrument_id=selected_id,
            selected_abs_zscore=selected_abs_zscore,
            selected_percentile_dislocation=percentile_dislocation,
            min_abs_zscore_for_dislocation=MIN_ABS_ZSCORE_FOR_DISLOCATION,
            min_percentile_dislocation=MIN_PERCENTILE_DISLOCATION,
        )

    return AbsoluteFundingExtremeBindingResultV0(
        status=AbsoluteFundingExtremeBindingStatus.PASS,
        reason_code="absolute_funding_extreme_pass",
        selected_instrument_id=selected_id,
        selected_abs_zscore=selected_abs_zscore,
        selected_percentile_dislocation=percentile_dislocation,
        min_abs_zscore_for_dislocation=MIN_ABS_ZSCORE_FOR_DISLOCATION,
        min_percentile_dislocation=MIN_PERCENTILE_DISLOCATION,
    )
