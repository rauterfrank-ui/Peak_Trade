"""Explicit research recompute wiring — not Alpha/max-age policy authority."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.constants_v1 import (
    NATURAL_7200_TARGET_SECONDS,
    PT1M_BAR_INTERVAL_SECONDS,
    PT60M_HORIZON_SECONDS,
    PT60M_REQUIRED_PRICE_OBSERVATIONS,
    RESEARCH_AGE_GRID_SECONDS,
    RESEARCH_RECOMPUTE_MINIMUM_EVENT_TIME_ELAPSED_SECONDS,
    RESEARCH_RECOMPUTE_MINIMUM_NEW_DISTINCT_OBSERVATIONS,
    RESEARCH_WIRING_LABEL,
    SOURCE_WINDOW_ORDINARY_SLIDE_DOES_NOT_RECOMPUTE,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.lifecycle_contract_v1 import (
    NaturalAgeLifecycleErrorV1,
    RecomputeReasonV1,
    VolatilityEstimateLifecycleState,
    _parse_event_time,
)


@dataclass(frozen=True)
class ResearchEstimateRecomputePolicyV1:
    """Versioned research wiring controlling when a new estimate is produced.

    This object must never be interpreted as a numeric max-age Alpha gate.
    """

    policy_id: str
    policy_version: str
    research_wiring_label: str
    minimum_new_distinct_observations: int
    minimum_event_time_elapsed_seconds: int
    source_window_ordinary_slide_does_not_recompute: bool
    session_start_behavior: str
    missing_estimate_behavior: str
    invalid_estimate_behavior: str
    out_of_order_sample_behavior: str
    duplicate_sample_behavior: str
    process_restart_behavior: str
    derivation_notes: tuple[str, ...]
    is_max_age_policy: bool = False
    alpha_authority: bool = False
    enforcement_authority: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "alpha_authority": self.alpha_authority,
            "derivation_notes": list(self.derivation_notes),
            "duplicate_sample_behavior": self.duplicate_sample_behavior,
            "enforcement_authority": self.enforcement_authority,
            "invalid_estimate_behavior": self.invalid_estimate_behavior,
            "is_max_age_policy": self.is_max_age_policy,
            "minimum_event_time_elapsed_seconds": self.minimum_event_time_elapsed_seconds,
            "minimum_new_distinct_observations": self.minimum_new_distinct_observations,
            "missing_estimate_behavior": self.missing_estimate_behavior,
            "out_of_order_sample_behavior": self.out_of_order_sample_behavior,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "process_restart_behavior": self.process_restart_behavior,
            "research_wiring_label": self.research_wiring_label,
            "session_start_behavior": self.session_start_behavior,
            "source_window_ordinary_slide_does_not_recompute": (
                self.source_window_ordinary_slide_does_not_recompute
            ),
        }


def build_natural_age_research_recompute_policy_v1() -> ResearchEstimateRecomputePolicyV1:
    """Build the sole ratified research recompute wiring for this capability."""
    if RESEARCH_RECOMPUTE_MINIMUM_EVENT_TIME_ELAPSED_SECONDS <= NATURAL_7200_TARGET_SECONDS:
        raise NaturalAgeLifecycleErrorV1("recompute_elapsed_must_exceed_7200_target")
    if (
        RESEARCH_RECOMPUTE_MINIMUM_NEW_DISTINCT_OBSERVATIONS * PT1M_BAR_INTERVAL_SECONDS
        < NATURAL_7200_TARGET_SECONDS
    ):
        raise NaturalAgeLifecycleErrorV1("recompute_observation_floor_insufficient_for_7200")

    notes = (
        f"PT1M_BAR_INTERVAL_SECONDS={PT1M_BAR_INTERVAL_SECONDS}",
        f"PT60M_REQUIRED_PRICE_OBSERVATIONS={PT60M_REQUIRED_PRICE_OBSERVATIONS}",
        f"PT60M_HORIZON_SECONDS={PT60M_HORIZON_SECONDS}",
        f"RESEARCH_AGE_GRID_SECONDS={list(RESEARCH_AGE_GRID_SECONDS)}",
        f"NATURAL_7200_TARGET_SECONDS={NATURAL_7200_TARGET_SECONDS}",
        "minimum_event_time_elapsed_seconds derived as NATURAL_7200_TARGET_SECONDS+1 "
        "from preregistered reachability_7200_plan",
        "minimum_new_distinct_observations derived as ceil(7200/PT1M)+1 = 121",
        "ordinary sliding PT60M source-window change must not force recompute",
        "values are research wiring only; not a numeric max-age policy recommendation",
    )
    return ResearchEstimateRecomputePolicyV1(
        policy_id="cv_maxage_natural_age_research_recompute_wiring_v1",
        policy_version="canonical_volatility_numeric_max_age_research_recompute_wiring/v1",
        research_wiring_label=RESEARCH_WIRING_LABEL,
        minimum_new_distinct_observations=RESEARCH_RECOMPUTE_MINIMUM_NEW_DISTINCT_OBSERVATIONS,
        minimum_event_time_elapsed_seconds=RESEARCH_RECOMPUTE_MINIMUM_EVENT_TIME_ELAPSED_SECONDS,
        source_window_ordinary_slide_does_not_recompute=(
            SOURCE_WINDOW_ORDINARY_SLIDE_DOES_NOT_RECOMPUTE
        ),
        session_start_behavior="PRODUCE_ON_FIRST_VALID_ESTIMATE_AFTER_WARMUP",
        missing_estimate_behavior="PRODUCE_WHEN_MATERIALIZATION_AVAILABLE",
        invalid_estimate_behavior="DO_NOT_REUSE_FAIL_CLOSED_OR_NOT_EVALUABLE",
        out_of_order_sample_behavior="REJECT_NOT_EVALUABLE_NO_NEGATIVE_AGE",
        duplicate_sample_behavior="NOOP_NO_AGE_NO_REUSE_NO_DISTINCT_ADVANCE",
        process_restart_behavior="RESTART_WITHOUT_ESTIMATE_UNTIL_FRESH_PRODUCE_NO_REMATERIALIZE_AS_FRESH",
        derivation_notes=notes,
        is_max_age_policy=False,
        alpha_authority=False,
        enforcement_authority=False,
    )


def evaluate_recompute_decision_v1(
    *,
    policy: ResearchEstimateRecomputePolicyV1,
    prior_state: Optional[VolatilityEstimateLifecycleState],
    current_market_event_time: Any,
    newly_materialized_source_digest: Optional[str],
    prior_invalid: bool = False,
) -> tuple[bool, str]:
    """Return (should_recompute, reason). Never decides Alpha allow/block."""
    if policy.is_max_age_policy or policy.alpha_authority or policy.enforcement_authority:
        raise NaturalAgeLifecycleErrorV1("recompute_policy_must_not_claim_trading_authority")

    if prior_state is None:
        return True, RecomputeReasonV1.SESSION_START_FIRST_ESTIMATE.value
    if prior_invalid:
        return True, RecomputeReasonV1.INVALID_PRIOR_ESTIMATE.value

    market = _parse_event_time(current_market_event_time, field_name="current_market_event_time")
    produced_at = _parse_event_time(
        prior_state.produced_at_market_event_time,
        field_name="produced_at_market_event_time",
    )
    elapsed = (market - produced_at).total_seconds()
    if elapsed < 0:
        raise NaturalAgeLifecycleErrorV1("recompute_elapsed_negative_event_time")

    if (
        prior_state.distinct_observations_since_recompute
        >= policy.minimum_new_distinct_observations
    ):
        return True, RecomputeReasonV1.MINIMUM_NEW_DISTINCT_OBSERVATIONS_REACHED.value
    if elapsed >= float(policy.minimum_event_time_elapsed_seconds):
        return True, RecomputeReasonV1.MINIMUM_EVENT_TIME_ELAPSED_REACHED.value

    if (
        not policy.source_window_ordinary_slide_does_not_recompute
        and newly_materialized_source_digest is not None
        and newly_materialized_source_digest != prior_state.source_digest
    ):
        return True, RecomputeReasonV1.SOURCE_WINDOW_MATERIAL_CHANGE.value

    return False, RecomputeReasonV1.NOT_APPLICABLE.value


def recompute_trigger_matrix_v1(
    policy: ResearchEstimateRecomputePolicyV1 | None = None,
) -> Mapping[str, Any]:
    p = policy or build_natural_age_research_recompute_policy_v1()
    return {
        "policy": p.to_dict(),
        "triggers": [
            {
                "name": "session_start_first_estimate",
                "condition": "prior_state is None and materialization available",
                "recomputes": True,
            },
            {
                "name": "missing_estimate",
                "condition": "prior_state is None",
                "recomputes": True,
            },
            {
                "name": "invalid_prior_estimate",
                "condition": "prior_invalid=true",
                "recomputes": True,
            },
            {
                "name": "minimum_new_distinct_observations",
                "condition": (
                    f"distinct_observations_since_recompute >= "
                    f"{p.minimum_new_distinct_observations}"
                ),
                "recomputes": True,
            },
            {
                "name": "minimum_event_time_elapsed",
                "condition": (
                    f"market_event_time - produced_at >= {p.minimum_event_time_elapsed_seconds}"
                ),
                "recomputes": True,
            },
            {
                "name": "ordinary_source_window_slide",
                "condition": "sliding PT60M window digest change only",
                "recomputes": False,
            },
            {
                "name": "duplicate_sample",
                "condition": "duplicate observation",
                "recomputes": False,
                "age_advance": False,
            },
            {
                "name": "out_of_order_sample",
                "condition": "out-of-order observation",
                "recomputes": False,
                "age_advance": False,
                "evaluable": False,
            },
            {
                "name": "runtime_cycle_without_sample",
                "condition": "poll/cycle without distinct market sample",
                "recomputes": False,
                "age_advance": False,
            },
        ],
        "explicitly_not_alpha_policy": True,
        "explicitly_not_max_age_threshold": True,
    }
