"""Early-age density support without fabricating market time or samples."""

from __future__ import annotations

from typing import Any, Sequence

from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.constants_v1 import (
    ARTIFICIAL_AGE_FORBIDDEN,
    DISTINCT_MARKET_SAMPLE_SEMANTICS_PRESERVED,
    EARLY_AGE_BUCKETS_SECONDS,
    EARLY_AGE_DENSITY_DOES_NOT_FABRICATE_MARKET_TIME,
    NETWORK_PACING_BUDGET_PRESERVED,
    NO_ZERO_INTERVAL_BURSTS,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.models_v1 import (
    MultiSessionTypedVolEvidenceError,
)


def assert_early_age_density_invariants_v1() -> None:
    if not DISTINCT_MARKET_SAMPLE_SEMANTICS_PRESERVED:
        raise MultiSessionTypedVolEvidenceError("distinct_sample_semantics_disabled")
    if not EARLY_AGE_DENSITY_DOES_NOT_FABRICATE_MARKET_TIME:
        raise MultiSessionTypedVolEvidenceError("market_time_fabrication_allowed")
    if not NETWORK_PACING_BUDGET_PRESERVED:
        raise MultiSessionTypedVolEvidenceError("network_pacing_not_preserved")
    if not NO_ZERO_INTERVAL_BURSTS:
        raise MultiSessionTypedVolEvidenceError("zero_interval_bursts_allowed")
    if not ARTIFICIAL_AGE_FORBIDDEN:
        raise MultiSessionTypedVolEvidenceError("artificial_age_allowed")


def plan_early_age_evidence_snapshots_v1(
    *,
    distinct_sample_identities: Sequence[str],
    age_seconds_by_identity: dict[str, float],
    minimum_network_interval_seconds: float,
    max_extra_snapshots_per_sample: int = 1,
) -> list[dict[str, Any]]:
    """Schedule extra Fresh-estimator reevaluations on existing distinct samples.

    Extra snapshots reuse the same market sample identity / event time and must
    not create network polls below the pacing budget.
    """
    assert_early_age_density_invariants_v1()
    if float(minimum_network_interval_seconds) <= 0:
        raise MultiSessionTypedVolEvidenceError("zero_interval_network_burst_forbidden")
    if int(max_extra_snapshots_per_sample) < 0:
        raise MultiSessionTypedVolEvidenceError("max_extra_snapshots_invalid")

    plan: list[dict[str, Any]] = []
    seen: set[str] = set()
    for identity in distinct_sample_identities:
        if identity in seen:
            # Duplicates never advance confirmation / density.
            continue
        seen.add(identity)
        age = float(age_seconds_by_identity.get(identity, -1.0))
        in_early = any(lo <= age <= hi for lo, hi, _ in EARLY_AGE_BUCKETS_SECONDS)
        plan.append(
            {
                "sample_identity": identity,
                "age_seconds": age,
                "snapshot_kind": "PRIMARY_ON_DISTINCT_SAMPLE",
                "fabricates_market_sample": False,
                "fabricates_market_time": False,
                "requires_network_poll": True,
                "minimum_interval_seconds": float(minimum_network_interval_seconds),
            }
        )
        if in_early and max_extra_snapshots_per_sample > 0:
            for i in range(int(max_extra_snapshots_per_sample)):
                plan.append(
                    {
                        "sample_identity": identity,
                        "age_seconds": age,
                        "snapshot_kind": f"EARLY_AGE_REEVALUATION_{i + 1}",
                        "fabricates_market_sample": False,
                        "fabricates_market_time": False,
                        # Reevaluation uses already-received sample; no extra poll.
                        "requires_network_poll": False,
                        "minimum_interval_seconds": float(minimum_network_interval_seconds),
                    }
                )
    return plan


def early_age_density_support_matrix_v1() -> dict[str, Any]:
    assert_early_age_density_invariants_v1()
    return {
        "EARLY_AGE_BUCKETS": [
            {"name": name, "lo": lo, "hi": hi} for lo, hi, name in EARLY_AGE_BUCKETS_SECONDS
        ],
        "DISTINCT_MARKET_SAMPLE_SEMANTICS_PRESERVED": True,
        "EARLY_AGE_DENSITY_DOES_NOT_FABRICATE_MARKET_TIME": True,
        "NETWORK_PACING_BUDGET_PRESERVED": True,
        "NO_ZERO_INTERVAL_BURSTS": True,
        "ARTIFICIAL_AGE_USED": False,
        "DUPLICATE_SAMPLES_DO_NOT_ADVANCE_CONFIRMATION": True,
    }
