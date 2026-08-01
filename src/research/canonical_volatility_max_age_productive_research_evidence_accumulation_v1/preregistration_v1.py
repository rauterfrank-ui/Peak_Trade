"""Machine-readable productive evidence-accumulation preregistration v1.

Binds before any productive evidence write. Research age candidates are a
diagnostic grid only — never a recommendation, default, or promotion target.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.models_v1 import (
    ProductiveEvidenceAccumulationError,
    digest_excluding_keys,
)
from research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    AGE_REFERENCE_CLOCK as DESIGN_AGE_REFERENCE_CLOCK,
    EMBARGO_POLICY_V1,
    MINIMUM_EVIDENCE_REQUIREMENTS_V1,
    PREREGISTERED_LEAKAGE_CONTROLS,
    PREREGISTERED_REJECTION_CRITERIA,
    PREREGISTERED_ROBUSTNESS_REQUIREMENTS,
    PREREGISTERED_STRESS_CONTROLS,
    PURGED_SPLIT_POLICY_V1,
    THRESHOLD_STATUS,
    build_ratified_max_age_research_design_contract_v1,
)

PRODUCTIVE_PREREGISTRATION_CONTRACT_VERSION = (
    "canonical_volatility_numeric_max_age_productive_research_evidence_preregistration/v1"
)

RESEARCH_QUESTION_V1 = (
    "Which, if any, robust event-time maximum_observation_age region for "
    "canonical VolatilityEstimateV1 can later be considered — using only "
    "productive research evidence accumulated under this preregistration — "
    "without selecting, recommending, or enforcing a numeric threshold here?"
)

# Research grid only. Identical argument domain as research-execution; never a
# productive default and never an automatic recommendation.
RESEARCH_AGE_CANDIDATE_GRID_SECONDS: tuple[int, ...] = tuple(
    int(x) for x in OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS
)

ESTIMATE_AGE_DEFINITION_V1 = (
    "estimate_age_seconds = reference_market_event_time - volatility_as_of_event_time; "
    "AGE_REFERENCE_CLOCK=MARKET_EVENT_TIME; "
    "receive_time_and_wallclock_are_not_age_authority"
)

FRESH_VOLATILITY_DEFINITION_V1 = (
    "estimate_present=true AND clock_trust=TRUSTED AND data_trust=TRUSTED AND "
    "fallback_used=false AND estimate_age_seconds <= candidate_max_age_seconds "
    "(counterfactual diagnostic only)"
)

STALE_VOLATILITY_DEFINITION_V1 = (
    "estimate_present=true AND estimate_age_seconds > candidate_max_age_seconds "
    "(counterfactual diagnostic only; no enforcement)"
)

MISSING_VOLATILITY_DEFINITION_V1 = (
    "estimate_present=false OR presence ABSENT/UNKNOWN; entry remains fail-closed"
)

UNTRUSTED_VOLATILITY_DEFINITION_V1 = (
    "clock_trust!=TRUSTED OR data_trust!=TRUSTED OR fallback_used=true; "
    "not counterfactual-eligible productive research truth"
)

DISTINCT_OBSERVATION_SEMANTICS_V1 = (
    "Distinct observation identity = "
    "(source_estimate_id, as_of_event_time, volatility_source_digest, market_sample_id); "
    "runtime cycle index is never a market sample; "
    "duplicate identical identity does not advance distinct_observation_count"
)

DUPLICATE_SAMPLE_POLICY_V1 = (
    "Identical estimate identity across distinct cycles → DUPLICATE_SAMPLE_REUSE; "
    "observation_count may include polls; distinct_observation_count does not increase; "
    "ledger append is idempotent on evidence_record_id with matching digest"
)

OUT_OF_ORDER_POLICY_V1 = (
    "Event-time out-of-order samples labeled OUT_OF_ORDER_REJECTED_REUSE when "
    "producer/binding declares them; deterministic reject; never invent synthetic "
    "observations to fill gaps"
)

STALE_SAMPLE_POLICY_V1 = (
    "Stale is counterfactual-only versus research age grid; productive threshold "
    "remains UNRESOLVED_MAX_AGE; transitions are diagnostic ledger metrics"
)

WARMUP_INSUFFICIENT_DATA_POLICY_V1 = (
    "Warm-up / insufficient history maps to INSUFFICIENT_DATA regime metadata; "
    "no synthetic estimate; no age-based entry permission invented"
)

ABORT_CRITERIA_V1: tuple[str, ...] = (
    "PREREGISTRATION_DIGEST_MISMATCH",
    "EVIDENCE_SCHEMA_MISMATCH",
    "LEDGER_CHAIN_DIGEST_MISMATCH",
    "JOIN_COMPATIBILITY_FAILURE",
    "ENFORCEMENT_OR_THRESHOLD_SELECTION_ATTEMPT",
    "LEGACY_FALLBACK_AS_RESEARCH_TRUTH",
    "SYNTHETIC_OR_FIXTURE_COUNTED_AS_PRODUCTIVE_EVIDENCE",
)

PREREGISTERED_METRICS_V1: tuple[str, ...] = (
    "observation_count",
    "distinct_observation_count",
    "estimate_age_seconds",
    "estimator_observation_count",
    "estimate_refresh_interval",
    "data_gap_seconds",
    "duplicate_rate",
    "out_of_order_rate",
    "stale_transition_count",
    "unknown_transition_count",
    "trusted_to_untrusted_transition_count",
    "candidate_age_bucket",
    "entry_eligibility_counterfactual",
    "exit_path_preservation",
    "regime",
    "volatility_regime",
    "session_id",
    "source_digest",
    "config_digest",
    "code_sha",
)

NON_PROMOTION_INVARIANT_V1 = (
    "NON_PROMOTION:"
    "COUNTERFACTUAL_ONLY=true;"
    "THRESHOLD_SELECTED=false;"
    "ENFORCEMENT_APPLIED=false;"
    "NO_AUTOMATIC_PRODUCTIVE_VALUE_RECOMMENDATION;"
    "INSUFFICIENT_COVERAGE_YIELDS_BLOCKED_FOR_PARAMETER_DECISION"
)

MINIMUM_PRODUCTIVE_EVIDENCE_REQUIREMENTS_V1: Mapping[str, Any] = {
    **dict(MINIMUM_EVIDENCE_REQUIREMENTS_V1),
    "minimum_independent_sessions": int(
        MINIMUM_EVIDENCE_REQUIREMENTS_V1["minimum_distinct_sessions"]
    ),
    "minimum_distinct_observations_per_age_bucket": 1,
    "minimum_market_regimes": 2,
    "minimum_volatility_regimes": 1,
    "parameter_decision_forbidden_in_this_capability": True,
    "research_age_grid_is_not_recommendation": True,
}


@dataclass(frozen=True)
class ProductiveEvidenceAccumulationPreregistrationV1:
    """Versioned, digested preregistration bound before productive evidence writes."""

    productive_preregistration_contract_version: str
    research_question: str
    design_preregistration_digest: str
    research_age_candidate_grid_seconds: tuple[int, ...]
    age_reference_clock: str
    estimate_age_definition: str
    fresh_volatility_definition: str
    stale_volatility_definition: str
    missing_volatility_definition: str
    untrusted_volatility_definition: str
    distinct_observation_semantics: str
    duplicate_sample_policy: str
    out_of_order_policy: str
    stale_sample_policy: str
    warmup_insufficient_data_policy: str
    market_and_volatility_regime_stratification: tuple[str, ...]
    minimum_evidence_requirements: Mapping[str, Any]
    leakage_controls: tuple[str, ...]
    purged_split_policy: str
    embargo_policy: str
    abort_criteria: tuple[str, ...]
    preregistered_metrics: tuple[str, ...]
    stress_controls: tuple[str, ...]
    robustness_controls: tuple[str, ...]
    rejection_criteria: tuple[str, ...]
    non_promotion_invariant: str
    threshold_status: str
    counterfactual_only: bool
    enforcement_applied: bool
    threshold_selected: bool
    productive_preregistration_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "abort_criteria": list(self.abort_criteria),
            "age_reference_clock": self.age_reference_clock,
            "counterfactual_only": self.counterfactual_only,
            "design_preregistration_digest": self.design_preregistration_digest,
            "distinct_observation_semantics": self.distinct_observation_semantics,
            "duplicate_sample_policy": self.duplicate_sample_policy,
            "embargo_policy": self.embargo_policy,
            "enforcement_applied": self.enforcement_applied,
            "estimate_age_definition": self.estimate_age_definition,
            "fresh_volatility_definition": self.fresh_volatility_definition,
            "leakage_controls": list(self.leakage_controls),
            "market_and_volatility_regime_stratification": list(
                self.market_and_volatility_regime_stratification
            ),
            "minimum_evidence_requirements": dict(self.minimum_evidence_requirements),
            "missing_volatility_definition": self.missing_volatility_definition,
            "non_promotion_invariant": self.non_promotion_invariant,
            "out_of_order_policy": self.out_of_order_policy,
            "preregistered_metrics": list(self.preregistered_metrics),
            "productive_preregistration_contract_version": (
                self.productive_preregistration_contract_version
            ),
            "productive_preregistration_digest": self.productive_preregistration_digest,
            "purged_split_policy": self.purged_split_policy,
            "rejection_criteria": list(self.rejection_criteria),
            "research_age_candidate_grid_seconds": list(self.research_age_candidate_grid_seconds),
            "research_question": self.research_question,
            "robustness_controls": list(self.robustness_controls),
            "stale_sample_policy": self.stale_sample_policy,
            "stale_volatility_definition": self.stale_volatility_definition,
            "stress_controls": list(self.stress_controls),
            "threshold_selected": self.threshold_selected,
            "threshold_status": self.threshold_status,
            "untrusted_volatility_definition": self.untrusted_volatility_definition,
            "warmup_insufficient_data_policy": self.warmup_insufficient_data_policy,
        }


def _digest_v1(payload: Mapping[str, Any]) -> str:
    return digest_excluding_keys(payload, exclude=("productive_preregistration_digest",))


def build_productive_evidence_accumulation_preregistration_v1() -> (
    ProductiveEvidenceAccumulationPreregistrationV1
):
    design = build_ratified_max_age_research_design_contract_v1()
    if design.age_reference_clock != DESIGN_AGE_REFERENCE_CLOCK:
        raise ProductiveEvidenceAccumulationError("design_age_clock_drift")
    if not RESEARCH_AGE_CANDIDATE_GRID_SECONDS:
        raise ProductiveEvidenceAccumulationError("research_age_grid_empty")
    if any(x <= 0 for x in RESEARCH_AGE_CANDIDATE_GRID_SECONDS):
        raise ProductiveEvidenceAccumulationError("research_age_grid_non_positive")

    provisional: dict[str, Any] = {
        "abort_criteria": list(ABORT_CRITERIA_V1),
        "age_reference_clock": DESIGN_AGE_REFERENCE_CLOCK,
        "counterfactual_only": True,
        "design_preregistration_digest": design.preregistration_digest,
        "distinct_observation_semantics": DISTINCT_OBSERVATION_SEMANTICS_V1,
        "duplicate_sample_policy": DUPLICATE_SAMPLE_POLICY_V1,
        "embargo_policy": EMBARGO_POLICY_V1,
        "enforcement_applied": False,
        "estimate_age_definition": ESTIMATE_AGE_DEFINITION_V1,
        "fresh_volatility_definition": FRESH_VOLATILITY_DEFINITION_V1,
        "leakage_controls": list(PREREGISTERED_LEAKAGE_CONTROLS),
        "market_and_volatility_regime_stratification": [
            "MARKET_REGIME_FROM_TYPED_FEATURE_REGIME_METADATA",
            "VOLATILITY_REGIME_FROM_TYPED_OR_EXPLICIT_RESEARCH_LABEL",
        ],
        "minimum_evidence_requirements": dict(MINIMUM_PRODUCTIVE_EVIDENCE_REQUIREMENTS_V1),
        "missing_volatility_definition": MISSING_VOLATILITY_DEFINITION_V1,
        "non_promotion_invariant": NON_PROMOTION_INVARIANT_V1,
        "out_of_order_policy": OUT_OF_ORDER_POLICY_V1,
        "preregistered_metrics": list(PREREGISTERED_METRICS_V1),
        "productive_preregistration_contract_version": PRODUCTIVE_PREREGISTRATION_CONTRACT_VERSION,
        "purged_split_policy": PURGED_SPLIT_POLICY_V1,
        "rejection_criteria": list(PREREGISTERED_REJECTION_CRITERIA),
        "research_age_candidate_grid_seconds": list(RESEARCH_AGE_CANDIDATE_GRID_SECONDS),
        "research_question": RESEARCH_QUESTION_V1,
        "robustness_controls": list(PREREGISTERED_ROBUSTNESS_REQUIREMENTS),
        "stale_sample_policy": STALE_SAMPLE_POLICY_V1,
        "stale_volatility_definition": STALE_VOLATILITY_DEFINITION_V1,
        "stress_controls": list(PREREGISTERED_STRESS_CONTROLS),
        "threshold_selected": False,
        "threshold_status": THRESHOLD_STATUS,
        "untrusted_volatility_definition": UNTRUSTED_VOLATILITY_DEFINITION_V1,
        "warmup_insufficient_data_policy": WARMUP_INSUFFICIENT_DATA_POLICY_V1,
    }
    digest = _digest_v1(provisional)
    return ProductiveEvidenceAccumulationPreregistrationV1(
        productive_preregistration_contract_version=PRODUCTIVE_PREREGISTRATION_CONTRACT_VERSION,
        research_question=RESEARCH_QUESTION_V1,
        design_preregistration_digest=design.preregistration_digest,
        research_age_candidate_grid_seconds=RESEARCH_AGE_CANDIDATE_GRID_SECONDS,
        age_reference_clock=DESIGN_AGE_REFERENCE_CLOCK,
        estimate_age_definition=ESTIMATE_AGE_DEFINITION_V1,
        fresh_volatility_definition=FRESH_VOLATILITY_DEFINITION_V1,
        stale_volatility_definition=STALE_VOLATILITY_DEFINITION_V1,
        missing_volatility_definition=MISSING_VOLATILITY_DEFINITION_V1,
        untrusted_volatility_definition=UNTRUSTED_VOLATILITY_DEFINITION_V1,
        distinct_observation_semantics=DISTINCT_OBSERVATION_SEMANTICS_V1,
        duplicate_sample_policy=DUPLICATE_SAMPLE_POLICY_V1,
        out_of_order_policy=OUT_OF_ORDER_POLICY_V1,
        stale_sample_policy=STALE_SAMPLE_POLICY_V1,
        warmup_insufficient_data_policy=WARMUP_INSUFFICIENT_DATA_POLICY_V1,
        market_and_volatility_regime_stratification=(
            "MARKET_REGIME_FROM_TYPED_FEATURE_REGIME_METADATA",
            "VOLATILITY_REGIME_FROM_TYPED_OR_EXPLICIT_RESEARCH_LABEL",
        ),
        minimum_evidence_requirements=dict(MINIMUM_PRODUCTIVE_EVIDENCE_REQUIREMENTS_V1),
        leakage_controls=tuple(PREREGISTERED_LEAKAGE_CONTROLS),
        purged_split_policy=PURGED_SPLIT_POLICY_V1,
        embargo_policy=EMBARGO_POLICY_V1,
        abort_criteria=ABORT_CRITERIA_V1,
        preregistered_metrics=PREREGISTERED_METRICS_V1,
        stress_controls=tuple(PREREGISTERED_STRESS_CONTROLS),
        robustness_controls=tuple(PREREGISTERED_ROBUSTNESS_REQUIREMENTS),
        rejection_criteria=tuple(PREREGISTERED_REJECTION_CRITERIA),
        non_promotion_invariant=NON_PROMOTION_INVARIANT_V1,
        threshold_status=THRESHOLD_STATUS,
        counterfactual_only=True,
        enforcement_applied=False,
        threshold_selected=False,
        productive_preregistration_digest=digest,
    )


def verify_productive_preregistration_v1(
    contract: ProductiveEvidenceAccumulationPreregistrationV1,
) -> None:
    expected = build_productive_evidence_accumulation_preregistration_v1()
    if contract.productive_preregistration_digest != expected.productive_preregistration_digest:
        raise ProductiveEvidenceAccumulationError("productive_preregistration_digest_mismatch")
    if contract.threshold_selected or contract.enforcement_applied:
        raise ProductiveEvidenceAccumulationError("preregistration_authority_drift")
    if not contract.counterfactual_only:
        raise ProductiveEvidenceAccumulationError("preregistration_must_be_counterfactual_only")
    if list(contract.research_age_candidate_grid_seconds) != list(
        RESEARCH_AGE_CANDIDATE_GRID_SECONDS
    ):
        raise ProductiveEvidenceAccumulationError("research_age_grid_mutation_forbidden")


def assert_preregistration_before_evidence_v1(
    *,
    expected_digest: str | None = None,
) -> ProductiveEvidenceAccumulationPreregistrationV1:
    """Fail-closed binder invoked before productive evidence production."""
    contract = build_productive_evidence_accumulation_preregistration_v1()
    verify_productive_preregistration_v1(contract)
    if (
        expected_digest is not None
        and expected_digest != contract.productive_preregistration_digest
    ):
        raise ProductiveEvidenceAccumulationError("caller_preregistration_digest_mismatch")
    return contract


def preregistration_matrix_v1(
    contract: ProductiveEvidenceAccumulationPreregistrationV1 | None = None,
) -> dict[str, Any]:
    bound = contract or build_productive_evidence_accumulation_preregistration_v1()
    return {
        "abort_criteria": list(bound.abort_criteria),
        "design_preregistration_digest": bound.design_preregistration_digest,
        "metrics": list(bound.preregistered_metrics),
        "minimum_evidence_requirements": dict(bound.minimum_evidence_requirements),
        "non_promotion_invariant": bound.non_promotion_invariant,
        "productive_preregistration_digest": bound.productive_preregistration_digest,
        "research_age_candidate_grid_seconds": list(bound.research_age_candidate_grid_seconds),
        "research_question": bound.research_question,
        "robustness_controls": list(bound.robustness_controls),
        "stress_controls": list(bound.stress_controls),
        "threshold_status": bound.threshold_status,
        "version": bound.productive_preregistration_contract_version,
    }


def require_research_grid_only_v1(candidates: Sequence[int]) -> tuple[int, ...]:
    """Accept only the preregistered research grid; never invent/promote values."""
    grid = tuple(int(x) for x in candidates)
    if grid != RESEARCH_AGE_CANDIDATE_GRID_SECONDS:
        raise ProductiveEvidenceAccumulationError("research_grid_deviation_forbidden")
    return grid
