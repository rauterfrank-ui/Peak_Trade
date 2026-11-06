"""Age-grid coverage tracking and LATE_AGE_HOLD exit predicate (R1 research only)."""

from __future__ import annotations

from typing import Mapping, MutableMapping, Optional, Sequence

from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.actionable_strata_v1 import (
    assign_age_bucket_v1,
)
from research.canonical_volatility_numeric_max_age_retained_estimate_late_age_carrier_v1.models_v1 import (
    RetainedEstimateLateAgeCarrierError,
)


def empty_age_bucket_observation_counts_v1(
    grid_seconds: Sequence[int],
) -> dict[str, int]:
    return {str(int(g)): 0 for g in grid_seconds}


def age_bucket_slot_from_age_seconds_v1(
    age_seconds: Optional[float],
    *,
    grid_seconds: Sequence[int],
) -> Optional[str]:
    """Map natural age to a prereg grid slot key, or None if outside LE_* slots."""
    label = assign_age_bucket_v1(None if age_seconds is None else float(age_seconds))
    if not label.startswith("AGE_LE_") or not label.endswith("_S"):
        return None
    slot = label[len("AGE_LE_") : -len("_S")]
    if slot not in {str(int(g)) for g in grid_seconds}:
        return None
    return slot


def record_age_bucket_observation_v1(
    counts: MutableMapping[str, int],
    *,
    age_seconds: Optional[float],
    grid_seconds: Sequence[int],
) -> Optional[str]:
    slot = age_bucket_slot_from_age_seconds_v1(age_seconds, grid_seconds=grid_seconds)
    if slot is None:
        return None
    counts[slot] = int(counts.get(slot, 0) or 0) + 1
    return slot


def prereg_age_grid_coverage_complete_v1(
    counts: Mapping[str, int],
    *,
    grid_seconds: Sequence[int],
    minimum_distinct_observations_per_age_bucket: int,
) -> bool:
    if minimum_distinct_observations_per_age_bucket < 1:
        raise RetainedEstimateLateAgeCarrierError(
            "minimum_distinct_observations_per_age_bucket_invalid"
        )
    if not grid_seconds:
        raise RetainedEstimateLateAgeCarrierError("research_age_grid_empty")
    for boundary in grid_seconds:
        key = str(int(boundary))
        if int(counts.get(key, 0) or 0) < int(minimum_distinct_observations_per_age_bucket):
            return False
    return True


def assert_non_regressing_age_v1(
    *,
    prior_age_seconds: Optional[float],
    current_age_seconds: float,
) -> None:
    if current_age_seconds < 0:
        raise RetainedEstimateLateAgeCarrierError("negative_age_seconds")
    if prior_age_seconds is not None and current_age_seconds < float(prior_age_seconds):
        raise RetainedEstimateLateAgeCarrierError("regressing_age_seconds")
