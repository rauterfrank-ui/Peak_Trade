"""Versioned additional evidence coverage plan (no session registration/execution)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    digest_excluding_keys,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.constants_v1 import (
    COVERAGE_PLAN_ARTIFACT_PATH,
    COVERAGE_PLAN_SCHEMA,
    NATURAL_7200_TARGET_SECONDS,
    PT1M_BAR_INTERVAL_SECONDS,
    RESEARCH_AGE_GRID_SECONDS,
    RESEARCH_RECOMPUTE_MINIMUM_EVENT_TIME_ELAPSED_SECONDS,
    RESEARCH_RECOMPUTE_MINIMUM_NEW_DISTINCT_OBSERVATIONS,
    RESEARCH_WIRING_LABEL,
)
from research.canonical_volatility_numeric_max_age_natural_age_progression_and_actionable_strata_evidence_plan_v1.recompute_policy_v1 import (
    build_natural_age_research_recompute_policy_v1,
)


@dataclass(frozen=True)
class AdditionalEvidenceCoveragePlanV1:
    schema: str
    plan_id: str
    plan_digest: str
    minimum_productive_sessions: int
    multiple_age_buckets_required: bool
    candidate_discrimination_required: bool
    incremental_age_only_effect_required_or_statistically_excluded: bool
    multiple_market_regimes_required: bool
    long_opportunity_required: bool
    short_opportunity_required: bool
    both_confirmed_opportunity_observed_or_explicitly_unreachable: bool
    actionable_entry_opportunity_required: bool
    counterfactual_stale_records_required: bool
    exit_risk_safety_independence_required: bool
    natural_7200_second_reachability_required: bool
    no_artificial_delay: bool
    no_timestamp_manipulation: bool
    research_recompute_wiring: Mapping[str, Any]
    session_duration_plan: Mapping[str, Any]
    session_execution_authorized: bool
    authorization_issuance_authorized: bool
    numeric_max_age_selected: bool
    numeric_max_age_enforcing: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "actionable_entry_opportunity_required": self.actionable_entry_opportunity_required,
            "authorization_issuance_authorized": self.authorization_issuance_authorized,
            "both_confirmed_opportunity_observed_or_explicitly_unreachable": (
                self.both_confirmed_opportunity_observed_or_explicitly_unreachable
            ),
            "candidate_discrimination_required": self.candidate_discrimination_required,
            "counterfactual_stale_records_required": self.counterfactual_stale_records_required,
            "exit_risk_safety_independence_required": self.exit_risk_safety_independence_required,
            "incremental_age_only_effect_required_or_statistically_excluded": (
                self.incremental_age_only_effect_required_or_statistically_excluded
            ),
            "long_opportunity_required": self.long_opportunity_required,
            "minimum_productive_sessions": self.minimum_productive_sessions,
            "multiple_age_buckets_required": self.multiple_age_buckets_required,
            "multiple_market_regimes_required": self.multiple_market_regimes_required,
            "natural_7200_second_reachability_required": (
                self.natural_7200_second_reachability_required
            ),
            "no_artificial_delay": self.no_artificial_delay,
            "no_timestamp_manipulation": self.no_timestamp_manipulation,
            "numeric_max_age_enforcing": self.numeric_max_age_enforcing,
            "numeric_max_age_selected": self.numeric_max_age_selected,
            "plan_digest": self.plan_digest,
            "plan_id": self.plan_id,
            "research_recompute_wiring": dict(self.research_recompute_wiring),
            "schema": self.schema,
            "session_duration_plan": dict(self.session_duration_plan),
            "session_execution_authorized": self.session_execution_authorized,
            "short_opportunity_required": self.short_opportunity_required,
        }


def build_additional_evidence_coverage_plan_v1() -> AdditionalEvidenceCoveragePlanV1:
    policy = build_natural_age_research_recompute_policy_v1()
    # Plan session wall/event span to exceed recompute floor so 7200s age is reachable
    # before the next research recompute. No session is registered or executed here.
    planned_event_span = max(
        RESEARCH_RECOMPUTE_MINIMUM_EVENT_TIME_ELAPSED_SECONDS,
        NATURAL_7200_TARGET_SECONDS + PT1M_BAR_INTERVAL_SECONDS,
    )
    session_plan = {
        "planned_independent_sessions": 2,
        "planned_event_time_span_seconds_per_late_age_session": planned_event_span,
        "planned_minimum_distinct_observations_after_first_estimate": (
            RESEARCH_RECOMPUTE_MINIMUM_NEW_DISTINCT_OBSERVATIONS
        ),
        "pt1m_cadence_seconds": PT1M_BAR_INTERVAL_SECONDS,
        "research_age_grid_seconds": list(RESEARCH_AGE_GRID_SECONDS),
        "natural_7200_mechanism": (
            "Retain first valid estimate until research recompute floor; "
            "age advances solely via later distinct market event times."
        ),
        "session_registration_in_this_capability": False,
        "session_execution_in_this_capability": False,
        "notes": [
            "Session 02 must not be retried by this plan.",
            "Future sessions require a separate authorization step.",
            f"Recompute wiring label={RESEARCH_WIRING_LABEL}",
        ],
    }
    payload = {
        "actionable_entry_opportunity_required": True,
        "authorization_issuance_authorized": False,
        "both_confirmed_opportunity_observed_or_explicitly_unreachable": True,
        "candidate_discrimination_required": True,
        "counterfactual_stale_records_required": True,
        "exit_risk_safety_independence_required": True,
        "incremental_age_only_effect_required_or_statistically_excluded": True,
        "long_opportunity_required": True,
        "minimum_productive_sessions": 2,
        "multiple_age_buckets_required": True,
        "multiple_market_regimes_required": True,
        "natural_7200_second_reachability_required": True,
        "no_artificial_delay": True,
        "no_timestamp_manipulation": True,
        "numeric_max_age_enforcing": False,
        "numeric_max_age_selected": False,
        "plan_id": "cv_maxage_natural_age_additional_evidence_coverage_plan_v1",
        "research_recompute_wiring": policy.to_dict(),
        "schema": COVERAGE_PLAN_SCHEMA,
        "session_duration_plan": session_plan,
        "session_execution_authorized": False,
        "short_opportunity_required": True,
    }
    digest = digest_excluding_keys(payload, exclude=("plan_digest",))
    return AdditionalEvidenceCoveragePlanV1(
        schema=COVERAGE_PLAN_SCHEMA,
        plan_id=str(payload["plan_id"]),
        plan_digest=digest,
        minimum_productive_sessions=2,
        multiple_age_buckets_required=True,
        candidate_discrimination_required=True,
        incremental_age_only_effect_required_or_statistically_excluded=True,
        multiple_market_regimes_required=True,
        long_opportunity_required=True,
        short_opportunity_required=True,
        both_confirmed_opportunity_observed_or_explicitly_unreachable=True,
        actionable_entry_opportunity_required=True,
        counterfactual_stale_records_required=True,
        exit_risk_safety_independence_required=True,
        natural_7200_second_reachability_required=True,
        no_artificial_delay=True,
        no_timestamp_manipulation=True,
        research_recompute_wiring=policy.to_dict(),
        session_duration_plan=session_plan,
        session_execution_authorized=False,
        authorization_issuance_authorized=False,
        numeric_max_age_selected=False,
        numeric_max_age_enforcing=False,
    )


def render_additional_evidence_coverage_plan_v1() -> dict[str, Any]:
    return build_additional_evidence_coverage_plan_v1().to_dict()


def verify_additional_evidence_coverage_plan_artifact_v1(
    *,
    artifact_path: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    path = artifact_path or (root / COVERAGE_PLAN_ARTIFACT_PATH)
    expected = build_additional_evidence_coverage_plan_v1().to_dict()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("plan_digest") != expected["plan_digest"]:
        raise ValueError("coverage_plan_digest_mismatch")
    for key, value in expected.items():
        if key == "plan_digest":
            continue
        if payload.get(key) != value:
            raise ValueError(f"coverage_plan_field_drift:{key}")
    if payload.get("session_execution_authorized") is not False:
        raise ValueError("coverage_plan_must_not_authorize_session_execution")
    if payload.get("authorization_issuance_authorized") is not False:
        raise ValueError("coverage_plan_must_not_authorize_issuance")
    if payload.get("minimum_productive_sessions", 0) < 2:
        raise ValueError("coverage_plan_minimum_sessions_insufficient")
    return payload
