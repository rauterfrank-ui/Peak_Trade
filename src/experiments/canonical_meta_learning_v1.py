"""Phase 11 Canonical Meta-Learning v1 (research evidence only).

Analyzes existing Phase 1-7 research evidence to describe recurrent or
associative properties of the research process. This layer does not invent
identity, robustness, comparability, failure, or reality-gap truth. It does
not mutate historical records, write config, promote, fund, or submit orders.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.experiments.canonical_comparison_ssot_v1 import (
    CanonicalComparisonRequestV1,
    ComparisonCandidateV1,
    ComparisonCompatibilityContractV1,
    OVERALL_COMPARABLE,
    SCHEMA_VERSION as COMPARISON_SSOT_VERSION,
    build_canonical_comparison_result_v1,
)
from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityError,
    validate_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.experiments.canonical_failure_memory_v1 import (
    SCHEMA_VERSION as FAILURE_MEMORY_VERSION,
    validate_canonical_failure_memory_record_v1,
)
from src.experiments.canonical_reality_gap_store_v1 import (
    DIMENSION_EXCEEDS_THRESHOLD,
    SCHEMA_VERSION as REALITY_GAP_VERSION,
    validate_canonical_reality_gap_record_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    is_valid_sha256_hex,
)

SCHEMA_VERSION: Final[str] = "canonical_meta_learning_v1"
META_LEARNING_DOMAIN: Final[str] = "peak_trade.canonical_meta_learning.v1"
DIGEST_ALGORITHM: Final[str] = "sha256"
RECORD_COMPLETENESS_COMPLETE: Final[str] = "COMPLETE"
EVALUATION_POLICY_VERSION: Final[str] = "canonical_meta_learning_policy_v1"
METRIC_DEFINITION_VERSION: Final[str] = "canonical_robustness_metrics_v1"
ROBUSTNESS_SUITE_VERSION: Final[str] = "canonical_robustness_suite_v1"
IDENTITY_SCHEMA_VERSION: Final[str] = "canonical_experiment_identity_v1"
EXPERIMENT_MEMORY_SCHEMA_VERSION: Final[str] = "canonical_experiment_memory_v1"

META_LEARNING_PRESENT: Final[bool] = True
META_LEARNING_AUTHORITY: Final[str] = "RESEARCH_ONLY"
META_LEARNING_HAS_RUNTIME_AUTHORITY: Final[bool] = False
META_LEARNING_CAN_MUTATE_LIVE_CONFIG: Final[bool] = False
META_LEARNING_CAN_WRITE_LIVE_CONFIG: Final[bool] = False
META_LEARNING_CAN_PROMOTE: Final[bool] = False
META_LEARNING_CAN_PROMOTE_TO_LIVE: Final[bool] = False
META_LEARNING_CAN_INCREASE_RISK: Final[bool] = False
META_LEARNING_CAN_INCREASE_LEVERAGE: Final[bool] = False
META_LEARNING_CAN_FUND: Final[bool] = False
META_LEARNING_CAN_SUBMIT_ORDER: Final[bool] = False
META_LEARNING_CAN_ARM: Final[bool] = False
META_LEARNING_CAN_ENABLE: Final[bool] = False
META_LEARNING_CAN_CREATE_CONFIRM_TOKEN: Final[bool] = False
META_LEARNING_CAN_USE_CONFIRM_TOKEN: Final[bool] = False
META_LEARNING_CAN_AUTHORIZE_CANARY: Final[bool] = False
AUTONOMOUS_CHAMPION_SWAP: Final[bool] = False
AUTONOMOUS_PROMOTION: Final[bool] = False
LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC: Final[bool] = False
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION: Final[bool] = True
SELF_LEARNING_NOT_SELF_AUTHORIZING: Final[bool] = True
HISTORICAL_RECORD_MUTATION: Final[bool] = False
PRODUCTIVE_CONFIG_MUTATION: Final[bool] = False
CORRELATION_IS_NOT_CAUSALITY: Final[bool] = True
NO_LOOKAHEAD: Final[bool] = True
NO_SILENT_ZERO_DEFAULT: Final[bool] = True
PROMOTION_AUTHORITY: Final[str] = "NONE"
RUNTIME_AUTHORITY_IMPACT: Final[str] = "NONE"
PHASE_12_STARTED: Final[bool] = False

STATUS_PASS: Final[str] = "PASS"
STATUS_FAIL: Final[str] = "FAIL"
STATUS_BLOCKED: Final[str] = "BLOCKED"
STATUS_NOT_APPLICABLE: Final[str] = "NOT_APPLICABLE"
STATUS_NOT_EVALUATED: Final[str] = "NOT_EVALUATED"
STATUS_BLOCKED_MISSING_CAPABILITY: Final[str] = "BLOCKED_MISSING_CAPABILITY"
TEST_STATUSES: Final[tuple[str, ...]] = (
    STATUS_PASS,
    STATUS_FAIL,
    STATUS_BLOCKED,
    STATUS_NOT_APPLICABLE,
    STATUS_NOT_EVALUATED,
    STATUS_BLOCKED_MISSING_CAPABILITY,
)
OOS_TEST_IDS: Final[tuple[str, ...]] = ("WALK_FORWARD", "ROLLING_OOS")
INSAMPLE_TEST_ID: Final[str] = "TRAIN_VALIDATION_HOLDOUT"
COST_GAP_DIMENSIONS: Final[tuple[str, ...]] = ("fee", "slippage", "funding")
COST_DIMENSION_DIGEST_FIELDS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "fee": "fee_model_digest",
        "slippage": "slippage_model_digest",
        "funding": "funding_model_digest",
    }
)

QUESTION_STRATEGY_FAMILY_OOS_SURVIVAL: Final[str] = "STRATEGY_FAMILY_OOS_SURVIVAL"
QUESTION_PARAMETER_REGION_REPEATED_OVERFIT: Final[str] = "PARAMETER_REGION_REPEATED_OVERFIT"
QUESTION_SEARCH_SPACE_FALSE_POSITIVES: Final[str] = "SEARCH_SPACE_FALSE_POSITIVES"
QUESTION_ROBUSTNESS_REALITY_GAP_ASSOCIATION: Final[str] = "ROBUSTNESS_REALITY_GAP_ASSOCIATION"
QUESTION_BACKTEST_METRIC_PREDICTIVE_ASSOCIATION: Final[str] = (
    "BACKTEST_METRIC_PREDICTIVE_ASSOCIATION"
)
QUESTION_COST_MODEL_REALITY_UNDERESTIMATION: Final[str] = "COST_MODEL_REALITY_UNDERESTIMATION"
QUESTION_REGIME_RECURRING_FAILURE_MODES: Final[str] = "REGIME_RECURRING_FAILURE_MODES"
QUESTION_PARAMETER_INSTABILITY: Final[str] = "PARAMETER_INSTABILITY"
QUESTION_HYPOTHESIS_KIND_POOR_RESULTS: Final[str] = "HYPOTHESIS_KIND_POOR_RESULTS"
QUESTION_RESEARCH_PATH_INFORMATION_GAIN: Final[str] = "RESEARCH_PATH_INFORMATION_GAIN"
CANONICAL_QUESTIONS: Final[tuple[str, ...]] = (
    QUESTION_STRATEGY_FAMILY_OOS_SURVIVAL,
    QUESTION_PARAMETER_REGION_REPEATED_OVERFIT,
    QUESTION_SEARCH_SPACE_FALSE_POSITIVES,
    QUESTION_ROBUSTNESS_REALITY_GAP_ASSOCIATION,
    QUESTION_BACKTEST_METRIC_PREDICTIVE_ASSOCIATION,
    QUESTION_COST_MODEL_REALITY_UNDERESTIMATION,
    QUESTION_REGIME_RECURRING_FAILURE_MODES,
    QUESTION_PARAMETER_INSTABILITY,
    QUESTION_HYPOTHESIS_KIND_POOR_RESULTS,
    QUESTION_RESEARCH_PATH_INFORMATION_GAIN,
)

EVIDENCE_COMPUTED: Final[str] = "COMPUTED"
EVIDENCE_INSUFFICIENT_EVIDENCE: Final[str] = "INSUFFICIENT_EVIDENCE"
EVIDENCE_REJECTED_COMPARABILITY: Final[str] = "REJECTED_COMPARABILITY"
EVIDENCE_INSUFFICIENT_SAMPLE: Final[str] = "INSUFFICIENT_SAMPLE"
CLAIM_TYPE_NONE: Final[str] = "NONE"
CLAIM_TYPE_DESCRIPTIVE: Final[str] = "DESCRIPTIVE"
CLAIM_TYPE_ASSOCIATION: Final[str] = "ASSOCIATION"
CLAIM_STRENGTH_NONE: Final[str] = "NONE"
CLAIM_STRENGTH_WEAK: Final[str] = "WEAK"
OOS_SURVIVED: Final[str] = "SURVIVED"
OOS_FAILED: Final[str] = "FAILED"
OOS_UNKNOWN: Final[str] = "UNKNOWN"
PROPOSAL_PRIORITIZE_RESEARCH: Final[str] = "PRIORITIZE_RESEARCH"
PROPOSAL_DEPRIORITIZE_RESEARCH: Final[str] = "DEPRIORITIZE_RESEARCH"
PROPOSAL_INVESTIGATE: Final[str] = "INVESTIGATE"
PROPOSAL_RETEST: Final[str] = "RETEST_WITH_EXPLICIT_REASON"
CANONICAL_PROPOSAL_KINDS: Final[tuple[str, ...]] = (
    PROPOSAL_PRIORITIZE_RESEARCH,
    PROPOSAL_DEPRIORITIZE_RESEARCH,
    PROPOSAL_INVESTIGATE,
    PROPOSAL_RETEST,
)
OVERALL_COMPLETE: Final[str] = "META_LEARNING_COMPLETE"
OBSERVED_SURFACES: Final[tuple[str, ...]] = (
    "SHADOW",
    "PAPER_EXCHANGE",
    "TESTNET",
    "LIVE",
)

_CREATED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_UNAVAILABLE_TOKENS = frozenset(
    {
        "",
        "unknown",
        "unavailable",
        "n/a",
        "na",
        "none",
        "null",
        "implicit",
        "default",
        "compatible",
        "zero",
    }
)

_LOGGER = logging.getLogger(__name__)


class MetaLearningValidationError(ValueError):
    """Fail-closed Canonical Meta-Learning v1 validation error."""


@dataclass(frozen=True)
class MetaLearningLaterOutcomeV1:
    observed_surface: str
    metric_name: str
    value: float
    observed_at: str


@dataclass(frozen=True)
class MetaLearningExperimentUnitV1:
    experiment_identity: Mapping[str, Any]
    evidence_created_at: str
    strategy_family: str
    hypothesis_id: str
    hypothesis_kind: str
    search_space_id: str
    parameter_region: Mapping[str, Any]
    regime: str
    time_horizon: Mapping[str, str]
    market_universe: Sequence[str]
    robustness_test_statuses: Mapping[str, str]
    backtest_metrics: Mapping[str, float]
    research_path_id: str | None = None
    parameter_stability: float | None = None
    later_outcome: MetaLearningLaterOutcomeV1 | None = None
    robustness_suite_version: str = ROBUSTNESS_SUITE_VERSION
    metric_definitions: str = METRIC_DEFINITION_VERSION


@dataclass(frozen=True)
class MetaLearningPolicyV1:
    min_sample_size_descriptive: int
    min_sample_size_associative: int
    min_recurrence_count: int
    min_parameter_stability: float
    evaluation_policy_version: str = EVALUATION_POLICY_VERSION


@dataclass(frozen=True)
class CanonicalMetaLearningRequestV1:
    units: Sequence[MetaLearningExperimentUnitV1]
    created_at: str
    policy: MetaLearningPolicyV1
    failure_records: Sequence[Mapping[str, Any]] = ()
    reality_gap_records: Sequence[Mapping[str, Any]] = ()
    compatibility_contract: ComparisonCompatibilityContractV1 | None = None
    metric_definitions: str = METRIC_DEFINITION_VERSION
    robustness_suite_version: str = ROBUSTNESS_SUITE_VERSION


def canonical_meta_learning_policy_v1() -> MetaLearningPolicyV1:
    return MetaLearningPolicyV1(
        evaluation_policy_version=EVALUATION_POLICY_VERSION,
        min_sample_size_descriptive=3,
        min_sample_size_associative=8,
        min_recurrence_count=2,
        min_parameter_stability=0.5,
    )


def build_canonical_meta_learning_v1(
    request: CanonicalMetaLearningRequestV1,
) -> Mapping[str, Any]:
    created_at = _require_created_at(request.created_at)
    metric_definitions = _require_phase4_token(
        "metric_definitions", request.metric_definitions, METRIC_DEFINITION_VERSION
    )
    robustness_suite_version = _require_phase4_token(
        "robustness_suite_version",
        request.robustness_suite_version,
        ROBUSTNESS_SUITE_VERSION,
    )
    policy = _canonicalize_policy(request.policy)
    bound_units = _canonicalize_units(
        request.units,
        created_at=created_at,
        metric_definitions=metric_definitions,
        robustness_suite_version=robustness_suite_version,
    )
    failure_records = _canonicalize_failure_records(request.failure_records, bound_units)
    gap_records = _canonicalize_gap_records(request.reality_gap_records, bound_units)
    pair_results, cohorts = _partition_comparable_cohorts(
        bound_units, request.compatibility_contract, created_at
    )
    questions = _evaluate_questions(
        bound_units=bound_units,
        cohorts=cohorts,
        failure_records=failure_records,
        gap_records=gap_records,
        policy=policy,
    )
    research_proposals = _collect_proposals(questions)
    input_lineage = {
        "contract_versions": {
            "comparison_ssot": COMPARISON_SSOT_VERSION,
            "experiment_identity": IDENTITY_SCHEMA_VERSION,
            "experiment_memory": EXPERIMENT_MEMORY_SCHEMA_VERSION,
            "failure_memory": FAILURE_MEMORY_VERSION,
            "meta_learning": SCHEMA_VERSION,
            "metric_definitions": metric_definitions,
            "reality_gap_store": REALITY_GAP_VERSION,
            "robustness_suite": robustness_suite_version,
        },
        "experiment_ids": [item["experiment_id"] for item in bound_units],
        "failure_record_ids": [item["failure_record_id"] for item in failure_records],
        "identity_digests": [item["identity_digest"] for item in bound_units],
        "reality_gap_record_ids": [item["reality_gap_record_id"] for item in gap_records],
    }
    body = {
        "autonomous_champion_swap": AUTONOMOUS_CHAMPION_SWAP,
        "autonomous_promotion": AUTONOMOUS_PROMOTION,
        "champion_experiment_id": None,
        "comparable_cohorts": [
            {
                "cohort_id": cohort["cohort_id"],
                "experiment_ids": list(cohort["experiment_ids"]),
            }
            for cohort in cohorts
        ],
        "comparison_pair_results": pair_results,
        "completeness": RECORD_COMPLETENESS_COMPLETE,
        "correlation_is_not_causality": CORRELATION_IS_NOT_CAUSALITY,
        "created_at": created_at,
        "digest_algorithm": DIGEST_ALGORITHM,
        "evaluation_policy": policy,
        "historical_record_mutation": HISTORICAL_RECORD_MUTATION,
        "input_lineage": input_lineage,
        "learning_may_autonomously_replace_core_logic": (
            LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC
        ),
        "meta_learning_authority": META_LEARNING_AUTHORITY,
        "meta_learning_can_arm": META_LEARNING_CAN_ARM,
        "meta_learning_can_authorize_canary": META_LEARNING_CAN_AUTHORIZE_CANARY,
        "meta_learning_can_create_confirm_token": META_LEARNING_CAN_CREATE_CONFIRM_TOKEN,
        "meta_learning_can_enable": META_LEARNING_CAN_ENABLE,
        "meta_learning_can_fund": META_LEARNING_CAN_FUND,
        "meta_learning_can_increase_leverage": META_LEARNING_CAN_INCREASE_LEVERAGE,
        "meta_learning_can_increase_risk": META_LEARNING_CAN_INCREASE_RISK,
        "meta_learning_can_mutate_live_config": META_LEARNING_CAN_MUTATE_LIVE_CONFIG,
        "meta_learning_can_promote": META_LEARNING_CAN_PROMOTE,
        "meta_learning_can_promote_to_live": META_LEARNING_CAN_PROMOTE_TO_LIVE,
        "meta_learning_can_submit_order": META_LEARNING_CAN_SUBMIT_ORDER,
        "meta_learning_can_use_confirm_token": META_LEARNING_CAN_USE_CONFIRM_TOKEN,
        "meta_learning_can_write_live_config": META_LEARNING_CAN_WRITE_LIVE_CONFIG,
        "meta_learning_domain": META_LEARNING_DOMAIN,
        "meta_learning_has_runtime_authority": META_LEARNING_HAS_RUNTIME_AUTHORITY,
        "meta_learning_present": META_LEARNING_PRESENT,
        "no_lookahead": NO_LOOKAHEAD,
        "no_silent_zero_default": NO_SILENT_ZERO_DEFAULT,
        "overall_status": OVERALL_COMPLETE,
        "phase_12_started": PHASE_12_STARTED,
        "productive_config_mutation": PRODUCTIVE_CONFIG_MUTATION,
        "promotion_authority": PROMOTION_AUTHORITY,
        "questions": questions,
        "ranked_experiment_ids": [],
        "research_proposals": research_proposals,
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "schema_version": SCHEMA_VERSION,
        "self_learning_not_self_authorizing": SELF_LEARNING_NOT_SELF_AUTHORIZING,
        "self_learning_self_authorizing_separation": SELF_LEARNING_SELF_AUTHORIZING_SEPARATION,
    }
    meta_learning_identity = derive_meta_learning_identity_v1(body)
    record = dict(body)
    record["meta_learning_identity"] = meta_learning_identity
    record["integrity"] = {
        "content_sha256": compute_content_sha256(
            {key: value for key, value in record.items() if key != "integrity"}
        )
    }
    validate_canonical_meta_learning_v1(record)
    frozen = _freeze(record)
    _LOGGER.info(
        "canonical_meta_learning_v1 built identity=%s experiments=%s authority=%s",
        meta_learning_identity,
        input_lineage["experiment_ids"],
        META_LEARNING_AUTHORITY,
    )
    return frozen


def derive_meta_learning_identity_v1(record_without_ids: Mapping[str, Any]) -> str:
    payload = {
        key: value
        for key, value in _plain_mapping(record_without_ids).items()
        if key not in {"meta_learning_identity", "integrity"}
    }
    envelope = {
        "digest_algorithm": DIGEST_ALGORITHM,
        "digest_domain": f"{META_LEARNING_DOMAIN}.meta_learning_identity",
        "payload": payload,
        "schema_version": SCHEMA_VERSION,
    }
    return compute_content_sha256(envelope)


def canonical_record_payload_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    return _plain_mapping(record)


def validate_canonical_meta_learning_v1(record: Mapping[str, Any]) -> None:
    if not isinstance(record, Mapping):
        raise MetaLearningValidationError("meta-learning record must be a mapping")
    payload = _plain_mapping(record)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise MetaLearningValidationError("schema_version mismatch")
    if payload.get("meta_learning_domain") != META_LEARNING_DOMAIN:
        raise MetaLearningValidationError("meta_learning_domain mismatch")
    if payload.get("completeness") != RECORD_COMPLETENESS_COMPLETE:
        raise MetaLearningValidationError("non-COMPLETE meta-learning records are forbidden")
    if payload.get("meta_learning_authority") != META_LEARNING_AUTHORITY:
        raise MetaLearningValidationError("meta_learning_authority must be RESEARCH_ONLY")
    if payload.get("promotion_authority") != PROMOTION_AUTHORITY:
        raise MetaLearningValidationError("promotion_authority must be NONE")
    if payload.get("ranked_experiment_ids") != []:
        raise MetaLearningValidationError("ranked_experiment_ids must remain empty")
    if payload.get("champion_experiment_id") is not None:
        raise MetaLearningValidationError("champion_experiment_id must be null")
    if payload.get("causal_claim") is True:
        raise MetaLearningValidationError("causal claims are forbidden")
    if payload.get("historical_record_mutation") is not False:
        raise MetaLearningValidationError("historical_record_mutation must be false")
    if payload.get("phase_12_started") is not False:
        raise MetaLearningValidationError("phase_12_started must be false")
    questions = payload.get("questions")
    if not isinstance(questions, list) or [item.get("question_id") for item in questions] != list(
        CANONICAL_QUESTIONS
    ):
        raise MetaLearningValidationError("canonical questions must be complete and ordered")
    for question in questions:
        if question.get("causal_claim") is not False:
            raise MetaLearningValidationError("causal_claim must be false")
        if question.get("claim_type") == "CAUSAL":
            raise MetaLearningValidationError("CAUSAL claim_type is forbidden")
        if question.get("claim_strength") not in {CLAIM_STRENGTH_NONE, CLAIM_STRENGTH_WEAK}:
            raise MetaLearningValidationError("claim_strength must be NONE or WEAK")
        if question.get("claim_strength") == "STRONG":
            raise MetaLearningValidationError("STRONG claim_strength is forbidden")
    for proposal in payload.get("research_proposals") or []:
        if proposal.get("kind") not in CANONICAL_PROPOSAL_KINDS:
            raise MetaLearningValidationError("research proposal kind is not canonical")
        if proposal.get("authority") != META_LEARNING_AUTHORITY:
            raise MetaLearningValidationError("research proposal authority must be RESEARCH_ONLY")
        if proposal.get("promotion_authority") != PROMOTION_AUTHORITY:
            raise MetaLearningValidationError("research proposal cannot promote")
    expected_identity = derive_meta_learning_identity_v1(
        {key: value for key, value in payload.items() if key != "integrity"}
    )
    if payload.get("meta_learning_identity") != expected_identity:
        raise MetaLearningValidationError(
            "meta_learning_identity is not bound to canonical content"
        )
    expected_integrity = compute_content_sha256(
        {key: value for key, value in payload.items() if key != "integrity"}
    )
    integrity = payload.get("integrity")
    if not isinstance(integrity, Mapping) or integrity.get("content_sha256") != expected_integrity:
        raise MetaLearningValidationError("integrity.content_sha256 mismatch")


def _canonicalize_policy(policy: MetaLearningPolicyV1) -> dict[str, Any]:
    version = _require_token("evaluation_policy_version", policy.evaluation_policy_version)
    if version != EVALUATION_POLICY_VERSION:
        raise MetaLearningValidationError("evaluation_policy_version mismatch")
    descriptive = _require_positive_int(
        "min_sample_size_descriptive", policy.min_sample_size_descriptive
    )
    associative = _require_positive_int(
        "min_sample_size_associative", policy.min_sample_size_associative
    )
    if associative < descriptive:
        raise MetaLearningValidationError(
            "min_sample_size_associative must be >= min_sample_size_descriptive"
        )
    return {
        "evaluation_policy_version": version,
        "min_parameter_stability": _require_finite_number(
            "min_parameter_stability", policy.min_parameter_stability
        ),
        "min_recurrence_count": _require_positive_int(
            "min_recurrence_count", policy.min_recurrence_count
        ),
        "min_sample_size_associative": associative,
        "min_sample_size_descriptive": descriptive,
    }


def _canonicalize_units(
    units: Sequence[MetaLearningExperimentUnitV1],
    *,
    created_at: str,
    metric_definitions: str,
    robustness_suite_version: str,
) -> list[dict[str, Any]]:
    if not units:
        raise MetaLearningValidationError("units must not be empty")
    bound: list[dict[str, Any]] = []
    seen: set[str] = set()
    for unit in units:
        identity = _require_identity(unit.experiment_identity)
        experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
        if experiment_id in seen:
            raise MetaLearningValidationError("units must have unique experiment_id values")
        seen.add(experiment_id)
        unit_metrics = _require_phase4_token(
            "metric_definitions", unit.metric_definitions, metric_definitions
        )
        unit_robustness = _require_phase4_token(
            "robustness_suite_version",
            unit.robustness_suite_version,
            robustness_suite_version,
        )
        evidence_created_at = _require_created_at(unit.evidence_created_at)
        if evidence_created_at > created_at:
            raise MetaLearningValidationError("evidence_created_at lookahead is forbidden")
        later = _canonicalize_later_outcome(unit.later_outcome, evidence_created_at, created_at)
        bound.append(
            {
                "backtest_metrics": _canonicalize_metrics(unit.backtest_metrics),
                "evidence_created_at": evidence_created_at,
                "experiment_id": experiment_id,
                "experiment_identity": identity,
                "hypothesis_id": _require_token("hypothesis_id", unit.hypothesis_id),
                "hypothesis_kind": _require_token("hypothesis_kind", unit.hypothesis_kind),
                "identity_digest": str(identity["identity_digest"]),
                "later_outcome": later,
                "market_universe": list(unit.market_universe),
                "metric_definitions": unit_metrics,
                "parameter_region": _canonicalize_numeric_tree(
                    "parameter_region", unit.parameter_region
                ),
                "parameter_stability": _optional_finite_number(
                    "parameter_stability", unit.parameter_stability
                ),
                "regime": _require_token("regime", unit.regime),
                "research_path_id": _optional_token("research_path_id", unit.research_path_id),
                "robustness_suite_version": unit_robustness,
                "robustness_test_statuses": _canonicalize_test_statuses(
                    unit.robustness_test_statuses
                ),
                "search_space_id": _require_token("search_space_id", unit.search_space_id),
                "strategy_family": _require_token("strategy_family", unit.strategy_family),
                "time_horizon": dict(unit.time_horizon),
            }
        )
    bound.sort(key=lambda item: str(item["experiment_id"]))
    return bound


def _canonicalize_later_outcome(
    outcome: MetaLearningLaterOutcomeV1 | None,
    evidence_created_at: str,
    created_at: str,
) -> dict[str, Any] | None:
    if outcome is None:
        return None
    observed_at = _require_created_at(outcome.observed_at)
    if observed_at < evidence_created_at or observed_at > created_at:
        raise MetaLearningValidationError("later_outcome lookahead is forbidden")
    return {
        "metric_name": _require_token("later_outcome.metric_name", outcome.metric_name),
        "observed_at": observed_at,
        "observed_surface": _require_enum(
            "later_outcome.observed_surface", outcome.observed_surface, OBSERVED_SURFACES
        ),
        "value": _require_finite_number("later_outcome.value", outcome.value),
    }


def _canonicalize_failure_records(
    records: Sequence[Mapping[str, Any]],
    bound_units: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    known_ids = {item["experiment_id"] for item in bound_units}
    bound: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        payload = _plain_mapping(record)
        validate_canonical_failure_memory_record_v1(payload)
        experiment_id = str(payload["experiment_id"])
        if experiment_id not in known_ids:
            raise MetaLearningValidationError(
                "failure record experiment_id is not in the input experiment set"
            )
        record_id = str(payload["failure_record_id"])
        if record_id in seen:
            raise MetaLearningValidationError("failure_record_id values must be unique")
        seen.add(record_id)
        bound.append(payload)
    bound.sort(key=lambda item: str(item["failure_record_id"]))
    return bound


def _canonicalize_gap_records(
    records: Sequence[Mapping[str, Any]],
    bound_units: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    known_ids = {item["experiment_id"] for item in bound_units}
    bound: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        payload = _plain_mapping(record)
        validate_canonical_reality_gap_record_v1(payload)
        experiment_id = str(payload["experiment_id"])
        if experiment_id not in known_ids:
            raise MetaLearningValidationError(
                "reality-gap record experiment_id is not in the input experiment set"
            )
        record_id = str(payload["reality_gap_record_id"])
        if record_id in seen:
            raise MetaLearningValidationError("reality_gap_record_id values must be unique")
        seen.add(record_id)
        bound.append(payload)
    bound.sort(key=lambda item: str(item["reality_gap_record_id"]))
    return bound


def _partition_comparable_cohorts(
    bound_units: Sequence[Mapping[str, Any]],
    contract: ComparisonCompatibilityContractV1 | None,
    created_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pair_results: list[dict[str, Any]] = []
    comparable_pairs: set[tuple[str, str]] = set()
    for index, left in enumerate(bound_units[:-1]):
        for right in bound_units[index + 1 :]:
            pair = build_canonical_comparison_result_v1(
                CanonicalComparisonRequestV1(
                    left=_as_candidate(left),
                    right=_as_candidate(right),
                    created_at=created_at,
                    compatibility_contract=contract,
                )
            )
            left_id = str(pair["left_experiment_id"])
            right_id = str(pair["right_experiment_id"])
            pair_results.append(
                {
                    "left_experiment_id": left_id,
                    "overall_comparability": pair["overall_comparability"],
                    "rejection_reasons": list(pair["rejection_reasons"]),
                    "right_experiment_id": right_id,
                }
            )
            if pair["overall_comparability"] == OVERALL_COMPARABLE:
                comparable_pairs.add(tuple(sorted((left_id, right_id))))
    remaining = list(bound_units)
    cohorts: list[dict[str, Any]] = []
    while remaining:
        seed = remaining.pop(0)
        members = [seed]
        leftover: list[dict[str, Any]] = []
        for item in remaining:
            if all(
                tuple(sorted((str(item["experiment_id"]), str(member["experiment_id"]))))
                in comparable_pairs
                for member in members
            ):
                members.append(item)
            else:
                leftover.append(item)
        experiment_ids = [str(item["experiment_id"]) for item in members]
        cohort_id = compute_content_sha256(
            {
                "digest_algorithm": DIGEST_ALGORITHM,
                "digest_domain": f"{META_LEARNING_DOMAIN}.cohort",
                "payload": {"experiment_ids": experiment_ids},
                "schema_version": SCHEMA_VERSION,
            }
        )
        cohorts.append(
            {
                "cohort_id": cohort_id,
                "experiment_ids": experiment_ids,
                "units": members,
            }
        )
        remaining = leftover
    pair_results.sort(
        key=lambda item: (str(item["left_experiment_id"]), str(item["right_experiment_id"]))
    )
    return pair_results, cohorts


def _evaluate_questions(
    *,
    bound_units: Sequence[Mapping[str, Any]],
    cohorts: Sequence[Mapping[str, Any]],
    failure_records: Sequence[Mapping[str, Any]],
    gap_records: Sequence[Mapping[str, Any]],
    policy: Mapping[str, Any],
) -> list[dict[str, Any]]:
    failures_by_experiment = _index_by_experiment(failure_records)
    gaps_by_experiment = _index_by_experiment(gap_records)
    evaluators = (
        _question_oos_survival,
        _question_repeated_overfit,
        _question_false_positives,
        _question_robustness_gap_association,
        _question_metric_predictive_association,
        _question_cost_underestimation,
        _question_regime_failures,
        _question_parameter_instability,
        _question_hypothesis_kind,
        _question_research_path,
    )
    return [
        evaluator(
            bound_units=bound_units,
            cohorts=cohorts,
            failures_by_experiment=failures_by_experiment,
            gaps_by_experiment=gaps_by_experiment,
            policy=policy,
        )
        for evaluator in evaluators
    ]


def _question_oos_survival(**kwargs: Any) -> dict[str, Any]:
    def collect(units: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        missing = 0
        counts: dict[str, dict[str, int]] = {}
        for unit in units:
            status = _oos_status(unit)
            if status == OOS_UNKNOWN:
                missing += 1
                continue
            family = str(unit["strategy_family"])
            bucket = counts.setdefault(family, {"failed": 0, "survived": 0})
            if status == OOS_SURVIVED:
                bucket["survived"] += 1
            else:
                bucket["failed"] += 1
        findings = [
            {
                "failed": counts[family]["failed"],
                "strategy_family": family,
                "survived": counts[family]["survived"],
            }
            for family in sorted(counts)
        ]
        return findings, missing

    return _cohort_descriptive_question(
        QUESTION_STRATEGY_FAMILY_OOS_SURVIVAL,
        collect,
        kwargs["cohorts"],
        kwargs["policy"],
        proposal_builder=_oos_proposals,
    )


def _question_repeated_overfit(**kwargs: Any) -> dict[str, Any]:
    def collect(units: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        missing = 0
        counts: dict[str, int] = {}
        regions: dict[str, Mapping[str, Any]] = {}
        for unit in units:
            failures = kwargs["failures_by_experiment"].get(unit["experiment_id"], [])
            overfit = [item for item in failures if item.get("failure_class") == "REJECTED_OVERFIT"]
            if not overfit:
                if not failures:
                    missing += 1
                continue
            key = compute_content_sha256(
                {
                    "digest_algorithm": DIGEST_ALGORITHM,
                    "digest_domain": f"{META_LEARNING_DOMAIN}.parameter_region",
                    "payload": unit["parameter_region"],
                    "schema_version": SCHEMA_VERSION,
                }
            )
            counts[key] = counts.get(key, 0) + len(overfit)
            regions[key] = unit["parameter_region"]
        min_recurrence = int(kwargs["policy"]["min_recurrence_count"])
        findings = [
            {
                "occurrence_count": counts[key],
                "parameter_region": regions[key],
                "parameter_region_digest": key,
                "recurring": counts[key] >= min_recurrence,
            }
            for key in sorted(counts)
            if counts[key] >= min_recurrence
        ]
        return findings, missing

    return _cohort_descriptive_question(
        QUESTION_PARAMETER_REGION_REPEATED_OVERFIT,
        collect,
        kwargs["cohorts"],
        kwargs["policy"],
        proposal_builder=_overfit_proposals,
    )


def _question_false_positives(**kwargs: Any) -> dict[str, Any]:
    def collect(units: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        missing = 0
        counts: dict[str, int] = {}
        for unit in units:
            statuses = unit["robustness_test_statuses"]
            in_sample = statuses.get(INSAMPLE_TEST_ID)
            oos_statuses = [statuses.get(test_id) for test_id in OOS_TEST_IDS]
            if in_sample not in {STATUS_PASS, STATUS_FAIL} or any(
                status not in {STATUS_PASS, STATUS_FAIL} for status in oos_statuses
            ):
                missing += 1
                continue
            if in_sample == STATUS_PASS and STATUS_FAIL in oos_statuses:
                search_space = str(unit["search_space_id"])
                counts[search_space] = counts.get(search_space, 0) + 1
        findings = [
            {"false_positive_count": counts[key], "search_space_id": key} for key in sorted(counts)
        ]
        return findings, missing

    return _cohort_descriptive_question(
        QUESTION_SEARCH_SPACE_FALSE_POSITIVES,
        collect,
        kwargs["cohorts"],
        kwargs["policy"],
        proposal_builder=_false_positive_proposals,
    )


def _question_robustness_gap_association(**kwargs: Any) -> dict[str, Any]:
    def collect(units: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        missing = 0
        stats: dict[str, dict[str, int]] = {}
        for unit in units:
            gaps = kwargs["gaps_by_experiment"].get(unit["experiment_id"], [])
            statuses = unit["robustness_test_statuses"]
            if not gaps or not statuses:
                missing += 1
                continue
            exceeds = any(
                item.get("overall_disposition") == "REJECTED_REALITY_GAP" for item in gaps
            )
            for test_id, status in statuses.items():
                if status not in {STATUS_PASS, STATUS_FAIL}:
                    continue
                bucket = stats.setdefault(
                    test_id,
                    {
                        "n_fail_and_gap_exceeds": 0,
                        "n_fail_and_gap_within": 0,
                        "n_paired": 0,
                        "n_pass_and_gap_exceeds": 0,
                        "n_pass_and_gap_within": 0,
                    },
                )
                bucket["n_paired"] += 1
                if status == STATUS_FAIL and exceeds:
                    bucket["n_fail_and_gap_exceeds"] += 1
                elif status == STATUS_FAIL:
                    bucket["n_fail_and_gap_within"] += 1
                elif exceeds:
                    bucket["n_pass_and_gap_exceeds"] += 1
                else:
                    bucket["n_pass_and_gap_within"] += 1
        findings = [
            {
                "causal_claim": False,
                "claim_type": CLAIM_TYPE_ASSOCIATION,
                "test_id": test_id,
                **stats[test_id],
            }
            for test_id in sorted(stats)
        ]
        return findings, missing

    return _cohort_associative_question(
        QUESTION_ROBUSTNESS_REALITY_GAP_ASSOCIATION,
        collect,
        kwargs["cohorts"],
        kwargs["policy"],
        sample_key="n_paired",
        proposal_builder=_association_proposals,
    )


def _question_metric_predictive_association(**kwargs: Any) -> dict[str, Any]:
    def collect(units: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        missing = 0
        stats: dict[str, dict[str, int]] = {}
        for unit in units:
            later = unit["later_outcome"]
            metrics = unit["backtest_metrics"]
            if later is None:
                missing += 1
                continue
            metric_name = str(later["metric_name"])
            if metric_name not in metrics:
                missing += 1
                continue
            bucket = stats.setdefault(
                metric_name, {"n_pairs": 0, "n_same_sign": 0, "n_opposite_sign": 0}
            )
            bucket["n_pairs"] += 1
            backtest_value = float(metrics[metric_name])
            later_value = float(later["value"])
            if backtest_value == 0.0 or later_value == 0.0:
                continue
            if (backtest_value > 0.0) == (later_value > 0.0):
                bucket["n_same_sign"] += 1
            else:
                bucket["n_opposite_sign"] += 1
        findings = [
            {
                "causal_claim": False,
                "claim_type": CLAIM_TYPE_ASSOCIATION,
                "metric_name": metric_name,
                **stats[metric_name],
            }
            for metric_name in sorted(stats)
        ]
        return findings, missing

    return _cohort_associative_question(
        QUESTION_BACKTEST_METRIC_PREDICTIVE_ASSOCIATION,
        collect,
        kwargs["cohorts"],
        kwargs["policy"],
        sample_key="n_pairs",
        proposal_builder=_metric_proposals,
    )


def _question_cost_underestimation(**kwargs: Any) -> dict[str, Any]:
    def collect(units: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        missing = 0
        counts: dict[tuple[str, str], dict[str, Any]] = {}
        for unit in units:
            gaps = kwargs["gaps_by_experiment"].get(unit["experiment_id"], [])
            if not gaps:
                missing += 1
                continue
            identity = unit["experiment_identity"]
            for gap in gaps:
                for dimension in gap.get("dimension_results") or []:
                    name = str(dimension.get("name"))
                    if name not in COST_GAP_DIMENSIONS:
                        continue
                    digest_field = COST_DIMENSION_DIGEST_FIELDS[name]
                    digest = str(identity[digest_field])
                    key = (name, digest)
                    bucket = counts.setdefault(
                        key,
                        {
                            "cost_model_digest": digest,
                            "dimension": name,
                            "sample_size": 0,
                            "underestimation_count": 0,
                            "within_or_overestimate_count": 0,
                        },
                    )
                    bucket["sample_size"] += 1
                    observed = float(dimension["observed"])
                    expected = float(dimension["expected"])
                    if observed > expected:
                        bucket["underestimation_count"] += 1
                    else:
                        bucket["within_or_overestimate_count"] += 1
        findings = [counts[key] for key in sorted(counts)]
        return findings, missing

    return _cohort_descriptive_question(
        QUESTION_COST_MODEL_REALITY_UNDERESTIMATION,
        collect,
        kwargs["cohorts"],
        kwargs["policy"],
        proposal_builder=_cost_proposals,
    )


def _question_regime_failures(**kwargs: Any) -> dict[str, Any]:
    def collect(units: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        missing = 0
        counts: dict[tuple[str, str], int] = {}
        for unit in units:
            failures = kwargs["failures_by_experiment"].get(unit["experiment_id"], [])
            if not failures:
                missing += 1
                continue
            for failure in failures:
                key = (str(failure["regime"]), str(failure["failure_class"]))
                counts[key] = counts.get(key, 0) + 1
        min_recurrence = int(kwargs["policy"]["min_recurrence_count"])
        findings = [
            {
                "failure_class": failure_class,
                "occurrence_count": counts[(regime, failure_class)],
                "recurring": counts[(regime, failure_class)] >= min_recurrence,
                "regime": regime,
            }
            for regime, failure_class in sorted(counts)
            if counts[(regime, failure_class)] >= min_recurrence
        ]
        return findings, missing

    return _cohort_descriptive_question(
        QUESTION_REGIME_RECURRING_FAILURE_MODES,
        collect,
        kwargs["cohorts"],
        kwargs["policy"],
        proposal_builder=_regime_proposals,
    )


def _question_parameter_instability(**kwargs: Any) -> dict[str, Any]:
    def collect(units: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        missing = 0
        unstable: dict[str, int] = {}
        for unit in units:
            stability = unit["parameter_stability"]
            if stability is None:
                missing += 1
                continue
            if float(stability) < float(kwargs["policy"]["min_parameter_stability"]):
                family = str(unit["strategy_family"])
                unstable[family] = unstable.get(family, 0) + 1
        findings = [
            {"strategy_family": family, "unstable_count": unstable[family]}
            for family in sorted(unstable)
        ]
        return findings, missing

    return _cohort_descriptive_question(
        QUESTION_PARAMETER_INSTABILITY,
        collect,
        kwargs["cohorts"],
        kwargs["policy"],
        proposal_builder=_instability_proposals,
    )


def _question_hypothesis_kind(**kwargs: Any) -> dict[str, Any]:
    def collect(units: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        missing = 0
        counts: dict[str, dict[str, int]] = {}
        for unit in units:
            kind = str(unit["hypothesis_kind"])
            bucket = counts.setdefault(kind, {"failed": 0, "observed": 0})
            bucket["observed"] += 1
            failures = kwargs["failures_by_experiment"].get(unit["experiment_id"], [])
            oos = _oos_status(unit)
            if failures or oos == OOS_FAILED:
                bucket["failed"] += 1
            elif oos == OOS_UNKNOWN and not failures:
                missing += 1
        findings = [
            {
                "failed_count": counts[kind]["failed"],
                "hypothesis_kind": kind,
                "observed_count": counts[kind]["observed"],
            }
            for kind in sorted(counts)
        ]
        return findings, missing

    return _cohort_descriptive_question(
        QUESTION_HYPOTHESIS_KIND_POOR_RESULTS,
        collect,
        kwargs["cohorts"],
        kwargs["policy"],
        proposal_builder=_hypothesis_kind_proposals,
    )


def _question_research_path(**kwargs: Any) -> dict[str, Any]:
    def collect(units: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        missing = 0
        paths: dict[str, dict[str, Any]] = {}
        for unit in units:
            path_id = unit["research_path_id"]
            if path_id is None:
                missing += 1
                continue
            bucket = paths.setdefault(
                str(path_id),
                {
                    "distinct_failure_classes": set(),
                    "experiment_count": 0,
                    "failure_count": 0,
                },
            )
            bucket["experiment_count"] += 1
            failures = kwargs["failures_by_experiment"].get(unit["experiment_id"], [])
            bucket["failure_count"] += len(failures)
            for failure in failures:
                bucket["distinct_failure_classes"].add(str(failure["failure_class"]))
        findings = [
            {
                "distinct_failure_classes": len(paths[path_id]["distinct_failure_classes"]),
                "experiment_count": paths[path_id]["experiment_count"],
                "failure_count": paths[path_id]["failure_count"],
                "research_path_id": path_id,
            }
            for path_id in sorted(paths)
        ]
        findings.sort(
            key=lambda item: (-int(item["distinct_failure_classes"]), str(item["research_path_id"]))
        )
        return findings, missing

    return _cohort_descriptive_question(
        QUESTION_RESEARCH_PATH_INFORMATION_GAIN,
        collect,
        kwargs["cohorts"],
        kwargs["policy"],
        proposal_builder=_path_proposals,
    )


def _cohort_descriptive_question(
    question_id: str,
    collector: Any,
    cohorts: Sequence[Mapping[str, Any]],
    policy: Mapping[str, Any],
    *,
    proposal_builder: Any,
) -> dict[str, Any]:
    return _cohort_question(
        question_id,
        collector,
        cohorts,
        policy,
        associative=False,
        sample_key=None,
        proposal_builder=proposal_builder,
    )


def _cohort_associative_question(
    question_id: str,
    collector: Any,
    cohorts: Sequence[Mapping[str, Any]],
    policy: Mapping[str, Any],
    *,
    sample_key: str,
    proposal_builder: Any,
) -> dict[str, Any]:
    return _cohort_question(
        question_id,
        collector,
        cohorts,
        policy,
        associative=True,
        sample_key=sample_key,
        proposal_builder=proposal_builder,
    )


def _cohort_question(
    question_id: str,
    collector: Any,
    cohorts: Sequence[Mapping[str, Any]],
    policy: Mapping[str, Any],
    *,
    associative: bool,
    sample_key: str | None,
    proposal_builder: Any,
) -> dict[str, Any]:
    comparable_n = sum(len(cohort["units"]) for cohort in cohorts)
    missing = 0
    findings: list[dict[str, Any]] = []
    proposals: list[dict[str, Any]] = []
    statuses: list[str] = []
    for cohort in cohorts:
        units = list(cohort["units"])
        cohort_findings, cohort_missing = collector(units)
        missing += cohort_missing
        sample_size = (
            len(units) if sample_key is None else _finding_sample(cohort_findings, sample_key)
        )
        evidence_status, claim_type, _claim_strength = _claim_gate(
            sample_size=sample_size,
            findings=cohort_findings,
            policy=policy,
            associative=associative,
        )
        statuses.append(evidence_status)
        if evidence_status != EVIDENCE_COMPUTED:
            continue
        wrapped = [
            {
                "causal_claim": False,
                "cohort_id": cohort["cohort_id"],
                "experiment_ids": list(cohort["experiment_ids"]),
                **item,
            }
            for item in cohort_findings
        ]
        findings.extend(wrapped)
        proposals.extend(proposal_builder(wrapped, question_id=question_id, claim_type=claim_type))
    if findings:
        evidence_status = EVIDENCE_COMPUTED
        claim_type = CLAIM_TYPE_ASSOCIATION if associative else CLAIM_TYPE_DESCRIPTIVE
        claim_strength = CLAIM_STRENGTH_WEAK if associative else CLAIM_STRENGTH_NONE
    elif EVIDENCE_INSUFFICIENT_SAMPLE in statuses:
        evidence_status = EVIDENCE_INSUFFICIENT_SAMPLE
        claim_type = CLAIM_TYPE_NONE
        claim_strength = CLAIM_STRENGTH_NONE
    else:
        evidence_status = EVIDENCE_INSUFFICIENT_EVIDENCE
        claim_type = CLAIM_TYPE_NONE
        claim_strength = CLAIM_STRENGTH_NONE
    return {
        "causal_claim": False,
        "claim_strength": claim_strength,
        "claim_type": claim_type,
        "comparable_sample_size": comparable_n,
        "correlation_is_not_causality": True,
        "evidence_status": evidence_status,
        "findings": findings,
        "missing_evidence_count": missing,
        "question_id": question_id,
        "rejected_comparability_count": comparable_n if len(cohorts) > 1 else 0,
        "research_proposals": proposals,
        "sample_size": comparable_n,
    }


def _claim_gate(
    *,
    sample_size: int,
    findings: Sequence[Mapping[str, Any]],
    policy: Mapping[str, Any],
    associative: bool,
) -> tuple[str, str, str]:
    if not findings:
        return EVIDENCE_INSUFFICIENT_EVIDENCE, CLAIM_TYPE_NONE, CLAIM_STRENGTH_NONE
    if sample_size < int(policy["min_sample_size_descriptive"]):
        return EVIDENCE_INSUFFICIENT_SAMPLE, CLAIM_TYPE_NONE, CLAIM_STRENGTH_NONE
    if associative and sample_size < int(policy["min_sample_size_associative"]):
        return EVIDENCE_INSUFFICIENT_SAMPLE, CLAIM_TYPE_NONE, CLAIM_STRENGTH_NONE
    if associative:
        return EVIDENCE_COMPUTED, CLAIM_TYPE_ASSOCIATION, CLAIM_STRENGTH_WEAK
    return EVIDENCE_COMPUTED, CLAIM_TYPE_DESCRIPTIVE, CLAIM_STRENGTH_NONE


def _finding_sample(findings: Sequence[Mapping[str, Any]], sample_key: str) -> int:
    return sum(int(item.get(sample_key, 0)) for item in findings)


def _oos_status(unit: Mapping[str, Any]) -> str:
    statuses = [unit["robustness_test_statuses"].get(test_id) for test_id in OOS_TEST_IDS]
    if any(status not in {STATUS_PASS, STATUS_FAIL} for status in statuses):
        return OOS_UNKNOWN
    if STATUS_FAIL in statuses:
        return OOS_FAILED
    return OOS_SURVIVED


def _oos_proposals(findings: Sequence[Mapping[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    for item in findings:
        survived = int(item["survived"])
        failed = int(item["failed"])
        if failed > survived:
            proposals.append(
                _proposal(
                    PROPOSAL_DEPRIORITIZE_RESEARCH,
                    target_kind="strategy_family",
                    target=str(item["strategy_family"]),
                    reason="OOS_FAILURE_DOMINATES",
                    **kwargs,
                )
            )
        elif survived > failed:
            proposals.append(
                _proposal(
                    PROPOSAL_PRIORITIZE_RESEARCH,
                    target_kind="strategy_family",
                    target=str(item["strategy_family"]),
                    reason="OOS_SURVIVAL_DOMINATES",
                    **kwargs,
                )
            )
    return proposals


def _overfit_proposals(
    findings: Sequence[Mapping[str, Any]], **kwargs: Any
) -> list[dict[str, Any]]:
    return [
        _proposal(
            PROPOSAL_DEPRIORITIZE_RESEARCH,
            target_kind="parameter_region",
            target=str(item["parameter_region_digest"]),
            reason="REPEATED_OVERFIT",
            **kwargs,
        )
        for item in findings
        if item.get("recurring") is True
    ]


def _false_positive_proposals(
    findings: Sequence[Mapping[str, Any]], **kwargs: Any
) -> list[dict[str, Any]]:
    return [
        _proposal(
            PROPOSAL_DEPRIORITIZE_RESEARCH,
            target_kind="search_space",
            target=str(item["search_space_id"]),
            reason="SEARCH_SPACE_FALSE_POSITIVES",
            **kwargs,
        )
        for item in findings
        if int(item["false_positive_count"]) > 0
    ]


def _association_proposals(
    findings: Sequence[Mapping[str, Any]], **kwargs: Any
) -> list[dict[str, Any]]:
    return [
        _proposal(
            PROPOSAL_INVESTIGATE,
            target_kind="robustness_test",
            target=str(item["test_id"]),
            reason="ROBUSTNESS_GAP_ASSOCIATION",
            **kwargs,
        )
        for item in findings
        if int(item["n_fail_and_gap_exceeds"]) > 0
    ]


def _metric_proposals(findings: Sequence[Mapping[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
    return [
        _proposal(
            PROPOSAL_INVESTIGATE,
            target_kind="backtest_metric",
            target=str(item["metric_name"]),
            reason="METRIC_LATER_ASSOCIATION",
            **kwargs,
        )
        for item in findings
        if int(item["n_pairs"]) > 0
    ]


def _cost_proposals(findings: Sequence[Mapping[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
    return [
        _proposal(
            PROPOSAL_INVESTIGATE,
            target_kind="cost_model",
            target=str(item["cost_model_digest"]),
            reason="COST_MODEL_UNDERESTIMATION",
            **kwargs,
        )
        for item in findings
        if int(item["underestimation_count"]) > 0
    ]


def _regime_proposals(findings: Sequence[Mapping[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
    return [
        _proposal(
            PROPOSAL_INVESTIGATE,
            target_kind="regime",
            target=str(item["regime"]),
            reason="RECURRING_FAILURE_MODE",
            **kwargs,
        )
        for item in findings
        if item.get("recurring") is True
    ]


def _instability_proposals(
    findings: Sequence[Mapping[str, Any]], **kwargs: Any
) -> list[dict[str, Any]]:
    return [
        _proposal(
            PROPOSAL_DEPRIORITIZE_RESEARCH,
            target_kind="strategy_family",
            target=str(item["strategy_family"]),
            reason="PARAMETER_INSTABILITY",
            **kwargs,
        )
        for item in findings
        if int(item["unstable_count"]) > 0
    ]


def _hypothesis_kind_proposals(
    findings: Sequence[Mapping[str, Any]], **kwargs: Any
) -> list[dict[str, Any]]:
    return [
        _proposal(
            PROPOSAL_DEPRIORITIZE_RESEARCH,
            target_kind="hypothesis_kind",
            target=str(item["hypothesis_kind"]),
            reason="REPEATED_POOR_RESULTS",
            **kwargs,
        )
        for item in findings
        if int(item["failed_count"]) > 0
    ]


def _path_proposals(findings: Sequence[Mapping[str, Any]], **kwargs: Any) -> list[dict[str, Any]]:
    if not findings:
        return []
    best = findings[0]
    return [
        _proposal(
            PROPOSAL_PRIORITIZE_RESEARCH,
            target_kind="research_path",
            target=str(best["research_path_id"]),
            reason="HIGHEST_INFORMATION_GAIN",
            **kwargs,
        )
    ]


def _proposal(
    kind: str,
    *,
    target_kind: str,
    target: str,
    reason: str,
    question_id: str,
    claim_type: str,
) -> dict[str, Any]:
    body = {
        "applies_to_champion": False,
        "authority": META_LEARNING_AUTHORITY,
        "claim_type": claim_type,
        "kind": kind,
        "promotion_authority": PROMOTION_AUTHORITY,
        "question_id": question_id,
        "reason": reason,
        "target": target,
        "target_kind": target_kind,
    }
    return {
        **body,
        "proposal_id": compute_content_sha256(
            {
                "digest_algorithm": DIGEST_ALGORITHM,
                "digest_domain": f"{META_LEARNING_DOMAIN}.proposal",
                "payload": body,
                "schema_version": SCHEMA_VERSION,
            }
        ),
    }


def _collect_proposals(questions: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    seen: set[str] = set()
    for question in questions:
        for proposal in question.get("research_proposals") or []:
            proposal_id = str(proposal["proposal_id"])
            if proposal_id in seen:
                continue
            seen.add(proposal_id)
            proposals.append(dict(proposal))
    proposals.sort(key=lambda item: str(item["proposal_id"]))
    return proposals


def _index_by_experiment(
    records: Sequence[Mapping[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    indexed: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        indexed.setdefault(str(record["experiment_id"]), []).append(dict(record))
    return indexed


def _as_candidate(unit: Mapping[str, Any]) -> ComparisonCandidateV1:
    return ComparisonCandidateV1(
        experiment_identity=unit["experiment_identity"],
        robustness_suite_version=unit["robustness_suite_version"],
        metric_definitions=unit["metric_definitions"],
        time_horizon=unit["time_horizon"],
        market_universe=unit["market_universe"],
        experiment_id=unit["experiment_id"],
    )


def _canonicalize_test_statuses(value: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise MetaLearningValidationError("robustness_test_statuses must be a mapping")
    statuses: dict[str, str] = {}
    for raw_key, raw_status in value.items():
        test_id = _require_token("robustness_test_id", raw_key)
        status = _require_enum("robustness_test_status", raw_status, TEST_STATUSES)
        if test_id in statuses:
            raise MetaLearningValidationError("duplicate robustness_test_id")
        statuses[test_id] = status
    return dict(sorted(statuses.items()))


def _canonicalize_metrics(value: Mapping[str, float]) -> dict[str, float]:
    if not isinstance(value, Mapping):
        raise MetaLearningValidationError("backtest_metrics must be a mapping")
    metrics: dict[str, float] = {}
    for raw_key, raw_value in value.items():
        name = _require_token("backtest_metric", raw_key)
        metrics[name] = _require_finite_number(f"backtest_metrics.{name}", raw_value)
    return dict(sorted(metrics.items()))


def _canonicalize_numeric_tree(field_name: str, value: Any) -> Any:
    if isinstance(value, Mapping):
        if not value:
            raise MetaLearningValidationError(f"{field_name} must not be empty")
        return {
            _require_token(f"{field_name}.key", str(key)): _canonicalize_numeric_tree(
                f"{field_name}.{key}", item
            )
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        return _require_finite_number(field_name, value)
    if isinstance(value, str):
        return _require_token(field_name, value)
    raise MetaLearningValidationError(f"{field_name} has an unsupported value type")


def _require_identity(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise MetaLearningValidationError("experiment_identity present and valid is required")
    identity = _plain_mapping(value)
    try:
        validate_canonical_experiment_identity_v1(identity)
    except CanonicalExperimentIdentityError as exc:
        raise MetaLearningValidationError(
            f"experiment_identity is not a valid Phase 1 Canonical Experiment Identity: {exc}"
        ) from exc
    return identity


def _require_phase4_token(field_name: str, value: Any, expected: str) -> str:
    token = _require_token(field_name, value)
    if token != expected:
        raise MetaLearningValidationError(f"{field_name} must reuse the Phase 4 token")
    return token


def _require_created_at(value: Any) -> str:
    if not isinstance(value, str) or not _CREATED_AT_RE.fullmatch(value):
        raise MetaLearningValidationError(
            "created_at must be an explicit UTC timestamp ending with Z"
        )
    return value


def _require_token(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not _TOKEN_RE.fullmatch(value):
        raise MetaLearningValidationError(f"{field_name} is missing or malformed")
    if value.strip().lower() in _UNAVAILABLE_TOKENS:
        raise MetaLearningValidationError(f"{field_name} cannot use implicit unavailable tokens")
    return value


def _optional_token(field_name: str, value: Any) -> str | None:
    if value is None:
        return None
    return _require_token(field_name, value)


def _require_enum(field_name: str, value: Any, allowed: Sequence[str]) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise MetaLearningValidationError(f"{field_name} is not a canonical value")
    return value


def _require_positive_int(field_name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise MetaLearningValidationError(f"{field_name} must be a positive int")
    return value


def _require_finite_number(field_name: str, value: Any) -> float:
    if value is None:
        raise MetaLearningValidationError(
            f"{field_name} is missing; silent zero defaults are forbidden"
        )
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MetaLearningValidationError(f"{field_name} must be an explicit finite number")
    number = float(value)
    if not math.isfinite(number):
        raise MetaLearningValidationError(
            f"non-finite numeric values are forbidden in {field_name}"
        )
    return number


def _optional_finite_number(field_name: str, value: Any) -> float | None:
    if value is None:
        return None
    return _require_finite_number(field_name, value)


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return [_freeze(item) for item in value]
    return value


def _plain_mapping(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain_mapping(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain_mapping(item) for item in value]
    return value


__all__ = [
    "AUTONOMOUS_CHAMPION_SWAP",
    "AUTONOMOUS_PROMOTION",
    "CANONICAL_QUESTIONS",
    "CanonicalMetaLearningRequestV1",
    "CLAIM_STRENGTH_NONE",
    "CLAIM_STRENGTH_WEAK",
    "CLAIM_TYPE_ASSOCIATION",
    "CLAIM_TYPE_DESCRIPTIVE",
    "CLAIM_TYPE_NONE",
    "CORRELATION_IS_NOT_CAUSALITY",
    "EVIDENCE_INSUFFICIENT_EVIDENCE",
    "EVIDENCE_INSUFFICIENT_SAMPLE",
    "EVIDENCE_REJECTED_COMPARABILITY",
    "HISTORICAL_RECORD_MUTATION",
    "META_LEARNING_AUTHORITY",
    "META_LEARNING_CAN_MUTATE_LIVE_CONFIG",
    "META_LEARNING_CAN_PROMOTE",
    "META_LEARNING_HAS_RUNTIME_AUTHORITY",
    "META_LEARNING_PRESENT",
    "MetaLearningExperimentUnitV1",
    "MetaLearningLaterOutcomeV1",
    "MetaLearningPolicyV1",
    "MetaLearningValidationError",
    "PHASE_12_STARTED",
    "PROMOTION_AUTHORITY",
    "build_canonical_meta_learning_v1",
    "canonical_meta_learning_policy_v1",
    "canonical_record_payload_v1",
    "validate_canonical_meta_learning_v1",
]
