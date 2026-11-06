"""Phase 10 Canonical Automated Offline Research Loop v1 (research evidence only).

Orchestrates existing Phase 1-7 research owners for one selected hypothesis.
This layer does not invent identity, robustness, comparability, or gap truth.
It does not mutate runtime, write config, promote, fund, or submit orders.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

from src.experiments.canonical_champion_challenger_v1 import (
    CanonicalChampionChallengerRequestV1,
    evaluate_canonical_champion_challenger_v1,
)
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
    CanonicalExperimentIdentityRequestV1,
    build_canonical_experiment_identity_v1,
    validate_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_store_v1 import CanonicalExperimentMemoryStoreV1
from src.experiments.canonical_experiment_memory_v1 import (
    ExperimentRecordConflictError,
    derive_experiment_id_v1,
)
from src.experiments.canonical_identity_bound_offline_observation_binding_v1 import (
    BINDING_DOMAIN as OBSERVATION_BINDING_DOMAIN,
    CanonicalIdentityBoundOfflineObservationBindingError,
    CanonicalIdentityBoundOfflineObservationBindingRequestV1,
    OBSERVATION_OWNER_OFFLINE_EXPERIMENT_OBSERVATIONS_V1,
    SCHEMA_VERSION as OBSERVATION_BINDING_SCHEMA_VERSION,
    STATUS_BOUND,
    STATUS_REJECTED_DIVERGENT_DUPLICATE,
    bind_canonical_identity_bound_offline_observation_v1,
)
from src.experiments.canonical_failure_memory_store_v1 import CanonicalFailureMemoryStoreV1
from src.experiments.canonical_failure_memory_v1 import (
    CanonicalFailureMemoryRecordRequestV1,
    FAILURE_CLASS_TO_FAILED_GATE,
    assess_duplicate_hypothesis_v1,
    build_canonical_failure_memory_record_v1,
    derive_hypothesis_fingerprint_v1,
)
from src.experiments.canonical_reality_gap_store_persist_v1 import CanonicalRealityGapStoreV1
from src.experiments.canonical_reality_gap_store_v1 import (
    CanonicalRealityGapRecordRequestV1,
    DISPOSITION_REJECTED_REALITY_GAP,
    RealityGapDimensionV1,
    build_canonical_reality_gap_record_v1,
)
from src.experiments.canonical_robustness_suite_v1 import (
    CanonicalRobustnessSuiteRequestV1,
    METRIC_DEFINITION_VERSION,
    SCHEMA_VERSION as ROBUSTNESS_SUITE_VERSION,
    STATUS_FAIL,
    build_canonical_robustness_evidence_v1,
    build_failure_records_for_failed_gates_v1,
    canonical_robustness_policy_v1,
    derive_robustness_policy_digest_v1,
)
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    is_valid_sha256_hex,
)

SCHEMA_VERSION: Final[str] = "canonical_automated_offline_research_loop_v1"
RESEARCH_LOOP_DOMAIN: Final[str] = "peak_trade.canonical_automated_offline_research_loop.v1"
DIGEST_ALGORITHM: Final[str] = "sha256"
RECORD_COMPLETENESS_COMPLETE: Final[str] = "COMPLETE"
SELECTION_POLICY_EXPLICIT_HYPOTHESIS_ID: Final[str] = "EXPLICIT_HYPOTHESIS_ID"
REF_KIND_IDENTITY_DIGEST_BOUND: Final[str] = "IDENTITY_DIGEST_BOUND"
EVIDENCE_KIND_EXPERIMENT_RECORD: Final[str] = "EXPERIMENT_RECORD"
CANDIDATE_ROLE_RESEARCH: Final[str] = "RESEARCH"
DISPOSITION_RESEARCH_ONLY: Final[str] = "RESEARCH_ONLY"
COMPARISON_STATUS_NOT_COMPARED: Final[str] = "NOT_COMPARED"
FAILURE_CLASS_COMPARABILITY: Final[str] = "REJECTED_COMPARABILITY"
FAILURE_CLASS_REALITY_GAP: Final[str] = "REJECTED_REALITY_GAP"

AUTOMATED_OFFLINE_RESEARCH_LOOP: Final[bool] = True
AUTOMATED_RUNTIME_AUTHORITY: Final[bool] = False
RESEARCH_LOOP_PRESENT: Final[bool] = True
RESEARCH_LOOP_HAS_RUNTIME_AUTHORITY: Final[bool] = False
RESEARCH_LOOP_CAN_MUTATE_LIVE_CONFIG: Final[bool] = False
RESEARCH_LOOP_CAN_WRITE_LIVE_CONFIG: Final[bool] = False
RESEARCH_LOOP_CAN_PROMOTE: Final[bool] = False
RESEARCH_LOOP_CAN_PROMOTE_TO_LIVE: Final[bool] = False
RESEARCH_LOOP_CAN_INCREASE_RISK: Final[bool] = False
RESEARCH_LOOP_CAN_INCREASE_LEVERAGE: Final[bool] = False
RESEARCH_LOOP_CAN_FUND: Final[bool] = False
RESEARCH_LOOP_CAN_SUBMIT_ORDER: Final[bool] = False
RESEARCH_LOOP_CAN_ARM: Final[bool] = False
RESEARCH_LOOP_CAN_ENABLE: Final[bool] = False
RESEARCH_LOOP_CAN_CREATE_CONFIRM_TOKEN: Final[bool] = False
RESEARCH_LOOP_CAN_USE_CONFIRM_TOKEN: Final[bool] = False
RESEARCH_LOOP_CAN_AUTHORIZE_CANARY: Final[bool] = False
AUTONOMOUS_CHAMPION_SWAP: Final[bool] = False
AUTONOMOUS_PROMOTION: Final[bool] = False
LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC: Final[bool] = False
SELF_LEARNING_SELF_AUTHORIZING_SEPARATION: Final[bool] = True
PROMOTION_AUTHORITY: Final[str] = "NONE"
RUNTIME_AUTHORITY_IMPACT: Final[str] = "NONE"

STEP_HYPOTHESIS_SELECTION: Final[str] = "HYPOTHESIS_SELECTION"
STEP_HYPOTHESIS_PREPARATION: Final[str] = "RESEARCH_HYPOTHESIS_PREPARATION"
STEP_OFFLINE_EXPERIMENT: Final[str] = "OFFLINE_EXPERIMENT_EXECUTION"
STEP_ROBUSTNESS: Final[str] = "CANONICAL_ROBUSTNESS_EXECUTION"
STEP_COMPARABILITY: Final[str] = "COMPARABILITY_CHECK"
STEP_CHALLENGER_REPORT: Final[str] = "CHALLENGER_REPORT_GENERATION"
STEP_FAILURE_MEMORY: Final[str] = "FAILURE_MEMORY_UPDATE"
STEP_REALITY_GAP: Final[str] = "REALITY_GAP_REPORT_GENERATION"
STEP_METADATA: Final[str] = "RESEARCH_METADATA_AGGREGATION"
CANONICAL_LOOP_STEPS: Final[tuple[str, ...]] = (
    STEP_HYPOTHESIS_SELECTION,
    STEP_HYPOTHESIS_PREPARATION,
    STEP_OFFLINE_EXPERIMENT,
    STEP_ROBUSTNESS,
    STEP_COMPARABILITY,
    STEP_CHALLENGER_REPORT,
    STEP_FAILURE_MEMORY,
    STEP_REALITY_GAP,
    STEP_METADATA,
)
STEP_STATUS_COMPLETE: Final[str] = "COMPLETE"
STEP_STATUS_FAILED: Final[str] = "FAILED"
LOOP_COMPLETE: Final[str] = "LOOP_COMPLETE"
LOOP_FAILED: Final[str] = "LOOP_FAILED"

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


class AutomatedOfflineResearchLoopValidationError(ValueError):
    """Fail-closed Canonical Automated Offline Research Loop v1 validation error."""


@dataclass(frozen=True)
class ResearchHypothesisCandidateV1:
    hypothesis_id: str
    identity_request: CanonicalExperimentIdentityRequestV1
    parameter_region: Mapping[str, Any]
    regime: str
    candidate_ref: str
    strategy_family: str
    time_horizon: Mapping[str, str]
    market_universe: Sequence[str]


@dataclass(frozen=True)
class OfflineExperimentObservationsV1:
    metrics: Mapping[str, Any]
    robustness_results: Mapping[str, Any]
    regime_results: Mapping[str, Any]
    artifacts: Sequence[Mapping[str, Any]]
    robustness_observations: Mapping[str, Any]
    robustness_policy: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class CanonicalAutomatedOfflineResearchLoopRequestV1:
    hypotheses: Sequence[ResearchHypothesisCandidateV1]
    selected_hypothesis_id: str
    created_at: str
    experiment_observations: OfflineExperimentObservationsV1
    champion: ComparisonCandidateV1
    champion_score: float
    challenger_score: float
    gap_dimensions: Sequence[RealityGapDimensionV1]
    observed_surface: str
    threshold_policy_digest: str
    selection_policy: str = SELECTION_POLICY_EXPLICIT_HYPOTHESIS_ID
    existing_failure_records: Sequence[Mapping[str, Any]] = ()
    retest_reason: str | None = None
    parent_experiment: str | None = None
    candidate_role: str = CANDIDATE_ROLE_RESEARCH
    disposition: str = DISPOSITION_RESEARCH_ONLY
    rejection_reason: str | None = None
    compatibility_contract: ComparisonCompatibilityContractV1 | None = None
    experiment_memory_store: CanonicalExperimentMemoryStoreV1 | None = None
    failure_memory_store: CanonicalFailureMemoryStoreV1 | None = None
    reality_gap_store: CanonicalRealityGapStoreV1 | None = None
    metric_definitions: str = METRIC_DEFINITION_VERSION
    robustness_suite_version: str = ROBUSTNESS_SUITE_VERSION


def run_canonical_automated_offline_research_loop_v1(
    request: CanonicalAutomatedOfflineResearchLoopRequestV1,
) -> Mapping[str, Any]:
    created_at = _require_created_at(request.created_at)
    metric_definitions = _require_token("metric_definitions", request.metric_definitions)
    if metric_definitions != METRIC_DEFINITION_VERSION:
        raise AutomatedOfflineResearchLoopValidationError(
            "metric_definitions must reuse the Phase 4 token"
        )
    robustness_suite_version = _require_token(
        "robustness_suite_version", request.robustness_suite_version
    )
    if robustness_suite_version != ROBUSTNESS_SUITE_VERSION:
        raise AutomatedOfflineResearchLoopValidationError(
            "robustness_suite_version must reuse the Phase 4 token"
        )
    _require_finite("champion_score", request.champion_score)
    _require_finite("challenger_score", request.challenger_score)

    selected = _select_hypothesis(request)
    identity = _prepare_identity(selected)
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    parent_lineage_ref = _parent_lineage_ref(identity)
    policy = selected_policy(request.experiment_observations.robustness_policy)
    policy_digest = derive_robustness_policy_digest_v1(policy)
    fingerprint = derive_hypothesis_fingerprint_v1(
        identity_digest=str(identity["identity_digest"]),
        hypothesis_id=selected.hypothesis_id,
        parameter_region=selected.parameter_region,
        regime=selected.regime,
        robustness_policy_digest=policy_digest,
        parent_lineage_ref=parent_lineage_ref,
    )
    duplicate_assessment = assess_duplicate_hypothesis_v1(
        request.existing_failure_records,
        hypothesis_fingerprint=fingerprint,
        parameter_region=selected.parameter_region,
    )
    if duplicate_assessment["detected"] and not _optional_token(request.retest_reason):
        raise AutomatedOfflineResearchLoopValidationError(
            "duplicate hypothesis requires explicit retest_reason"
        )

    experiment_record, observation_binding = _bind_experiment_memory(
        request=request,
        identity=identity,
        experiment_id=experiment_id,
        fingerprint=fingerprint,
        selected=selected,
        created_at=created_at,
    )
    experiment_persisted = _binding_persist_id(observation_binding)
    robustness_evidence = _run_robustness(
        request=request,
        identity=identity,
        experiment_id=experiment_id,
        selected=selected,
        policy=policy,
        created_at=created_at,
    )
    challenger_candidate = ComparisonCandidateV1(
        experiment_identity=identity,
        robustness_suite_version=robustness_suite_version,
        metric_definitions=metric_definitions,
        time_horizon=dict(selected.time_horizon),
        market_universe=list(selected.market_universe),
        experiment_id=experiment_id,
        evidence_refs=(
            {
                "kind": EVIDENCE_KIND_EXPERIMENT_RECORD,
                "ref": experiment_id,
                "digest": str(identity["identity_digest"]),
            },
        ),
    )
    comparison_result = build_canonical_comparison_result_v1(
        CanonicalComparisonRequestV1(
            left=request.champion,
            right=challenger_candidate,
            created_at=created_at,
            compatibility_contract=request.compatibility_contract,
        )
    )
    champion_id = str(comparison_result["left_experiment_id"])
    scores = {champion_id: request.champion_score, experiment_id: request.challenger_score}
    challenger_report = evaluate_canonical_champion_challenger_v1(
        CanonicalChampionChallengerRequestV1(
            champion=request.champion,
            challengers=(challenger_candidate,),
            scores=scores,
            created_at=created_at,
            compatibility_contract=request.compatibility_contract,
        )
    )
    reality_gap_record = build_canonical_reality_gap_record_v1(
        CanonicalRealityGapRecordRequestV1(
            experiment_identity=identity,
            observed_surface=request.observed_surface,
            metric_definitions=metric_definitions,
            threshold_policy_digest=request.threshold_policy_digest,
            gap_dimensions=request.gap_dimensions,
            evidence_refs=[
                {
                    "kind": EVIDENCE_KIND_EXPERIMENT_RECORD,
                    "ref": experiment_id,
                    "digest": str(identity["identity_digest"]),
                }
            ],
            created_at=created_at,
            experiment_id=experiment_id,
        )
    )
    failure_records = _collect_failure_records(
        robustness_evidence=robustness_evidence,
        comparison_result=comparison_result,
        reality_gap_record=reality_gap_record,
        identity=identity,
        experiment_id=experiment_id,
        selected=selected,
        policy_digest=policy_digest,
        created_at=created_at,
        retest_reason=request.retest_reason,
    )
    failure_persisted_ids = _append_failure_records(request.failure_memory_store, failure_records)
    reality_gap_persisted = _optional_append(
        request.reality_gap_store, reality_gap_record, "reality_gap_record_id"
    )

    robustness_status = (
        STEP_STATUS_FAILED
        if robustness_evidence["aggregate_status"] == STATUS_FAIL
        else STEP_STATUS_COMPLETE
    )
    comparability_status = (
        STEP_STATUS_COMPLETE
        if comparison_result["overall_comparability"] == OVERALL_COMPARABLE
        else STEP_STATUS_FAILED
    )
    reality_gap_status = (
        STEP_STATUS_FAILED
        if reality_gap_record["overall_disposition"] == DISPOSITION_REJECTED_REALITY_GAP
        else STEP_STATUS_COMPLETE
    )
    step_results = [
        _step(STEP_HYPOTHESIS_SELECTION, STEP_STATUS_COMPLETE, selected.hypothesis_id),
        _step(STEP_HYPOTHESIS_PREPARATION, STEP_STATUS_COMPLETE, experiment_id),
        _step(STEP_OFFLINE_EXPERIMENT, STEP_STATUS_COMPLETE, experiment_id),
        _step(STEP_ROBUSTNESS, robustness_status, str(robustness_evidence["aggregate_status"])),
        _step(
            STEP_COMPARABILITY,
            comparability_status,
            str(comparison_result["overall_comparability"]),
        ),
        _step(
            STEP_CHALLENGER_REPORT,
            STEP_STATUS_COMPLETE,
            str(challenger_report["research_recommendation"]),
        ),
        _step(STEP_FAILURE_MEMORY, STEP_STATUS_COMPLETE, str(len(failure_records))),
        _step(
            STEP_REALITY_GAP,
            reality_gap_status,
            str(reality_gap_record["overall_disposition"]),
        ),
        _step(STEP_METADATA, STEP_STATUS_COMPLETE, SCHEMA_VERSION),
    ]
    failed_steps = [
        item["step_id"] for item in step_results if item["status"] == STEP_STATUS_FAILED
    ]
    overall_status = LOOP_FAILED if failed_steps else LOOP_COMPLETE
    research_metadata = {
        "champion_experiment_id": champion_id,
        "comparison_ssot_version": COMPARISON_SSOT_VERSION,
        "duplicate_detected": bool(duplicate_assessment["detected"]),
        "experiment_id": experiment_id,
        "failed_steps": failed_steps,
        "hypothesis_fingerprint": fingerprint,
        "hypothesis_id": selected.hypothesis_id,
        "identity_digest": identity["identity_digest"],
        "metric_definitions": metric_definitions,
        "robustness_suite_version": robustness_suite_version,
        "step_ids": list(CANONICAL_LOOP_STEPS),
    }
    body = {
        "automated_offline_research_loop": AUTOMATED_OFFLINE_RESEARCH_LOOP,
        "automated_runtime_authority": AUTOMATED_RUNTIME_AUTHORITY,
        "autonomous_champion_swap": AUTONOMOUS_CHAMPION_SWAP,
        "autonomous_promotion": AUTONOMOUS_PROMOTION,
        "canonical_trading_decision_core_bound": True,
        "challenger_report": _plain_mapping(challenger_report),
        "champion_experiment_id": champion_id,
        "comparison_result": _plain_mapping(comparison_result),
        "completeness": RECORD_COMPLETENESS_COMPLETE,
        "created_at": created_at,
        "digest_algorithm": DIGEST_ALGORITHM,
        "duplicate_assessment": _plain_mapping(duplicate_assessment),
        "experiment_record": _plain_mapping(experiment_record),
        "observation_binding": _observation_binding_evidence(observation_binding),
        "failure_records": [_plain_mapping(item) for item in failure_records],
        "hypothesis_preparation": {
            "experiment_id": experiment_id,
            "hypothesis_fingerprint": fingerprint,
            "identity_digest": identity["identity_digest"],
            "robustness_policy_digest": policy_digest,
        },
        "hypothesis_selection": {
            "candidate_hypothesis_ids": _candidate_ids(request.hypotheses),
            "selected_hypothesis_id": selected.hypothesis_id,
            "selection_policy": SELECTION_POLICY_EXPLICIT_HYPOTHESIS_ID,
        },
        "learning_may_autonomously_replace_core_logic": (
            LEARNING_MAY_AUTONOMOUSLY_REPLACE_CORE_LOGIC
        ),
        "persist": {
            "experiment_record_id": experiment_persisted,
            "failure_record_ids": failure_persisted_ids,
            "reality_gap_record_id": reality_gap_persisted,
        },
        "promotion_authority": PROMOTION_AUTHORITY,
        "reality_gap_record": _plain_mapping(reality_gap_record),
        "research_loop_can_arm": RESEARCH_LOOP_CAN_ARM,
        "research_loop_can_authorize_canary": RESEARCH_LOOP_CAN_AUTHORIZE_CANARY,
        "research_loop_can_create_confirm_token": RESEARCH_LOOP_CAN_CREATE_CONFIRM_TOKEN,
        "research_loop_can_enable": RESEARCH_LOOP_CAN_ENABLE,
        "research_loop_can_fund": RESEARCH_LOOP_CAN_FUND,
        "research_loop_can_increase_leverage": RESEARCH_LOOP_CAN_INCREASE_LEVERAGE,
        "research_loop_can_increase_risk": RESEARCH_LOOP_CAN_INCREASE_RISK,
        "research_loop_can_mutate_live_config": RESEARCH_LOOP_CAN_MUTATE_LIVE_CONFIG,
        "research_loop_can_promote": RESEARCH_LOOP_CAN_PROMOTE,
        "research_loop_can_promote_to_live": RESEARCH_LOOP_CAN_PROMOTE_TO_LIVE,
        "research_loop_can_submit_order": RESEARCH_LOOP_CAN_SUBMIT_ORDER,
        "research_loop_can_use_confirm_token": RESEARCH_LOOP_CAN_USE_CONFIRM_TOKEN,
        "research_loop_can_write_live_config": RESEARCH_LOOP_CAN_WRITE_LIVE_CONFIG,
        "research_loop_domain": RESEARCH_LOOP_DOMAIN,
        "research_loop_has_runtime_authority": RESEARCH_LOOP_HAS_RUNTIME_AUTHORITY,
        "research_loop_present": RESEARCH_LOOP_PRESENT,
        "research_metadata": research_metadata,
        "robustness_evidence": _plain_mapping(robustness_evidence),
        "runtime_authority_impact": RUNTIME_AUTHORITY_IMPACT,
        "schema_version": SCHEMA_VERSION,
        "selected_experiment_id": experiment_id,
        "selected_hypothesis_id": selected.hypothesis_id,
        "self_learning_self_authorizing_separation": SELF_LEARNING_SELF_AUTHORIZING_SEPARATION,
        "step_results": step_results,
        "overall_status": overall_status,
    }
    loop_identity = derive_loop_identity_v1(body)
    record = dict(body)
    record["loop_identity"] = loop_identity
    record["integrity"] = {
        "content_sha256": compute_content_sha256(
            {key: value for key, value in record.items() if key != "integrity"}
        )
    }
    validate_canonical_automated_offline_research_loop_v1(record)
    frozen = _freeze(record)
    _LOGGER.info(
        "canonical_automated_offline_research_loop_v1 built identity=%s status=%s",
        loop_identity,
        overall_status,
    )
    return frozen


def derive_loop_identity_v1(record_without_ids: Mapping[str, Any]) -> str:
    payload = _plain_mapping(record_without_ids)
    envelope = {
        "digest_algorithm": DIGEST_ALGORITHM,
        "digest_domain": f"{RESEARCH_LOOP_DOMAIN}.loop_identity",
        "payload": {
            "champion_experiment_id": payload.get("champion_experiment_id"),
            "overall_status": payload.get("overall_status"),
            "research_metadata": payload.get("research_metadata"),
            "selected_experiment_id": payload.get("selected_experiment_id"),
            "selected_hypothesis_id": payload.get("selected_hypothesis_id"),
            "step_results": payload.get("step_results"),
        },
        "schema_version": SCHEMA_VERSION,
    }
    return compute_content_sha256(envelope)


def canonical_record_payload_v1(record: Mapping[str, Any]) -> dict[str, Any]:
    return _plain_mapping(record)


def validate_canonical_automated_offline_research_loop_v1(record: Mapping[str, Any]) -> None:
    if not isinstance(record, Mapping):
        raise AutomatedOfflineResearchLoopValidationError("loop record must be a mapping")
    payload = _plain_mapping(record)
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise AutomatedOfflineResearchLoopValidationError("schema_version mismatch")
    if payload.get("research_loop_domain") != RESEARCH_LOOP_DOMAIN:
        raise AutomatedOfflineResearchLoopValidationError("research_loop_domain mismatch")
    if payload.get("completeness") != RECORD_COMPLETENESS_COMPLETE:
        raise AutomatedOfflineResearchLoopValidationError("non-COMPLETE loop records are forbidden")
    if payload.get("automated_offline_research_loop") is not True:
        raise AutomatedOfflineResearchLoopValidationError(
            "automated_offline_research_loop must be true"
        )
    if payload.get("automated_runtime_authority") is not False:
        raise AutomatedOfflineResearchLoopValidationError(
            "automated_runtime_authority must be false"
        )
    if payload.get("research_loop_present") is not True:
        raise AutomatedOfflineResearchLoopValidationError("research_loop_present must be true")
    if payload.get("research_loop_has_runtime_authority") is not False:
        raise AutomatedOfflineResearchLoopValidationError(
            "research_loop_has_runtime_authority must be false"
        )
    if payload.get("research_loop_can_mutate_live_config") is not False:
        raise AutomatedOfflineResearchLoopValidationError(
            "research_loop_can_mutate_live_config must be false"
        )
    if payload.get("research_loop_can_write_live_config") is not False:
        raise AutomatedOfflineResearchLoopValidationError(
            "research_loop_can_write_live_config must be false"
        )
    if payload.get("research_loop_can_promote") is not False:
        raise AutomatedOfflineResearchLoopValidationError("research_loop_can_promote must be false")
    if payload.get("research_loop_can_promote_to_live") is not False:
        raise AutomatedOfflineResearchLoopValidationError(
            "research_loop_can_promote_to_live must be false"
        )
    if payload.get("research_loop_can_increase_risk") is not False:
        raise AutomatedOfflineResearchLoopValidationError(
            "research_loop_can_increase_risk must be false"
        )
    if payload.get("research_loop_can_increase_leverage") is not False:
        raise AutomatedOfflineResearchLoopValidationError(
            "research_loop_can_increase_leverage must be false"
        )
    if payload.get("research_loop_can_fund") is not False:
        raise AutomatedOfflineResearchLoopValidationError("research_loop_can_fund must be false")
    if payload.get("research_loop_can_submit_order") is not False:
        raise AutomatedOfflineResearchLoopValidationError(
            "research_loop_can_submit_order must be false"
        )
    if payload.get("research_loop_can_arm") is not False:
        raise AutomatedOfflineResearchLoopValidationError("research_loop_can_arm must be false")
    if payload.get("research_loop_can_enable") is not False:
        raise AutomatedOfflineResearchLoopValidationError("research_loop_can_enable must be false")
    if payload.get("research_loop_can_create_confirm_token") is not False:
        raise AutomatedOfflineResearchLoopValidationError(
            "research_loop_can_create_confirm_token must be false"
        )
    if payload.get("research_loop_can_use_confirm_token") is not False:
        raise AutomatedOfflineResearchLoopValidationError(
            "research_loop_can_use_confirm_token must be false"
        )
    if payload.get("research_loop_can_authorize_canary") is not False:
        raise AutomatedOfflineResearchLoopValidationError(
            "research_loop_can_authorize_canary must be false"
        )
    if payload.get("autonomous_champion_swap") is not False:
        raise AutomatedOfflineResearchLoopValidationError("autonomous_champion_swap must be false")
    if payload.get("autonomous_promotion") is not False:
        raise AutomatedOfflineResearchLoopValidationError("autonomous_promotion must be false")
    if payload.get("learning_may_autonomously_replace_core_logic") is not False:
        raise AutomatedOfflineResearchLoopValidationError(
            "learning_may_autonomously_replace_core_logic must be false"
        )
    if payload.get("self_learning_self_authorizing_separation") is not True:
        raise AutomatedOfflineResearchLoopValidationError(
            "self_learning_self_authorizing_separation must be true"
        )
    if payload.get("promotion_authority") != PROMOTION_AUTHORITY:
        raise AutomatedOfflineResearchLoopValidationError("promotion_authority must be NONE")
    if payload.get("runtime_authority_impact") != RUNTIME_AUTHORITY_IMPACT:
        raise AutomatedOfflineResearchLoopValidationError("runtime_authority_impact must be NONE")
    if payload.get("canonical_trading_decision_core_bound") is not True:
        raise AutomatedOfflineResearchLoopValidationError(
            "canonical_trading_decision_core_bound must be true"
        )
    if payload.get("overall_status") not in {LOOP_COMPLETE, LOOP_FAILED}:
        raise AutomatedOfflineResearchLoopValidationError("overall_status is not a canonical value")
    _require_created_at(payload.get("created_at"))
    _require_token("selected_hypothesis_id", payload.get("selected_hypothesis_id"))
    _require_sha256("selected_experiment_id", payload.get("selected_experiment_id"))
    _require_sha256("champion_experiment_id", payload.get("champion_experiment_id"))
    _require_sha256("loop_identity", payload.get("loop_identity"))
    step_results = payload.get("step_results")
    if not isinstance(step_results, list) or len(step_results) != len(CANONICAL_LOOP_STEPS):
        raise AutomatedOfflineResearchLoopValidationError("step_results must cover every loop step")
    seen: list[str] = []
    for item in step_results:
        if not isinstance(item, Mapping):
            raise AutomatedOfflineResearchLoopValidationError("step_results items must be mappings")
        step_id = item.get("step_id")
        if step_id not in CANONICAL_LOOP_STEPS:
            raise AutomatedOfflineResearchLoopValidationError(f"unknown loop step_id: {step_id}")
        if step_id in seen:
            raise AutomatedOfflineResearchLoopValidationError(f"duplicate loop step_id: {step_id}")
        seen.append(str(step_id))
        if item.get("status") not in {STEP_STATUS_COMPLETE, STEP_STATUS_FAILED}:
            raise AutomatedOfflineResearchLoopValidationError(f"invalid status for {step_id}")
    if tuple(seen) != CANONICAL_LOOP_STEPS:
        raise AutomatedOfflineResearchLoopValidationError("loop step order is not canonical")
    failed_steps = [
        item["step_id"] for item in step_results if item["status"] == STEP_STATUS_FAILED
    ]
    if failed_steps and payload.get("overall_status") != LOOP_FAILED:
        raise AutomatedOfflineResearchLoopValidationError("FAILED steps require LOOP_FAILED")
    if not failed_steps and payload.get("overall_status") != LOOP_COMPLETE:
        raise AutomatedOfflineResearchLoopValidationError(
            "LOOP_COMPLETE requires every step COMPLETE"
        )
    identity = payload.get("experiment_record", {}).get("experiment_identity")
    _require_identity(identity)
    _require_observation_binding(
        payload.get("observation_binding"),
        identity=identity,
        experiment_id=str(payload.get("selected_experiment_id")),
    )
    challenger_state = payload.get("challenger_report", {}).get("champion_state", {})
    if challenger_state.get("swapped") is True or challenger_state.get("mutated") is True:
        raise AutomatedOfflineResearchLoopValidationError("champion state mutation is forbidden")
    if payload.get("challenger_report", {}).get("autonomous_champion_swap") is not False:
        raise AutomatedOfflineResearchLoopValidationError("autonomous_champion_swap must be false")
    integrity = payload.get("integrity")
    if not isinstance(integrity, Mapping) or not is_valid_sha256_hex(
        str(integrity.get("content_sha256", ""))
    ):
        raise AutomatedOfflineResearchLoopValidationError("integrity.content_sha256 is required")


def _select_hypothesis(
    request: CanonicalAutomatedOfflineResearchLoopRequestV1,
) -> ResearchHypothesisCandidateV1:
    if request.selection_policy != SELECTION_POLICY_EXPLICIT_HYPOTHESIS_ID:
        raise AutomatedOfflineResearchLoopValidationError("selection_policy mismatch")
    selected_id = _require_token("selected_hypothesis_id", request.selected_hypothesis_id)
    if not request.hypotheses:
        raise AutomatedOfflineResearchLoopValidationError("hypotheses must not be empty")
    matches = [
        item
        for item in request.hypotheses
        if _require_token("hypothesis_id", item.hypothesis_id) == selected_id
    ]
    if len(matches) != 1:
        raise AutomatedOfflineResearchLoopValidationError(
            "selected_hypothesis_id must match exactly one candidate"
        )
    return matches[0]


def _prepare_identity(selected: ResearchHypothesisCandidateV1) -> Mapping[str, Any]:
    try:
        identity = build_canonical_experiment_identity_v1(selected.identity_request)
    except CanonicalExperimentIdentityError as exc:
        raise AutomatedOfflineResearchLoopValidationError(
            f"research hypothesis preparation failed: {exc}"
        ) from exc
    return identity


def _bind_experiment_memory(
    *,
    request: CanonicalAutomatedOfflineResearchLoopRequestV1,
    identity: Mapping[str, Any] | None,
    experiment_id: str,
    fingerprint: str,
    selected: ResearchHypothesisCandidateV1,
    created_at: str,
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    try:
        binding = bind_canonical_identity_bound_offline_observation_v1(
            CanonicalIdentityBoundOfflineObservationBindingRequestV1(
                phase1_identity=identity,
                observation_owner=OBSERVATION_OWNER_OFFLINE_EXPERIMENT_OBSERVATIONS_V1,
                observations=request.experiment_observations,
                claimed_identity_digest=_optional_identity_field(identity, "identity_digest"),
                claimed_experiment_id=experiment_id,
                claimed_parent_lineage_ref=(
                    None if identity is None else _parent_lineage_ref(identity)
                ),
                hypothesis_id=selected.hypothesis_id,
                hypothesis_fingerprint=fingerprint,
                strategy_family=selected.strategy_family,
                created_at=created_at,
                parent_experiment=request.parent_experiment,
                candidate_role=request.candidate_role,
                disposition=request.disposition,
                rejection_reason=request.rejection_reason,
                claimed_dataset_digest=_optional_identity_field(identity, "dataset_digest"),
                claimed_cost_model_digest=_optional_identity_field(identity, "cost_model_digest"),
                claimed_risk_policy_digest=_optional_identity_field(identity, "risk_policy_digest"),
                claimed_portfolio_digest=_optional_identity_field(identity, "portfolio_digest"),
                requested_apply=False,
                requested_bounded_auto=False,
                experiment_memory_store=request.experiment_memory_store,
            )
        )
    except CanonicalIdentityBoundOfflineObservationBindingError as exc:
        raise AutomatedOfflineResearchLoopValidationError(
            f"offline experiment observation binding failed: {exc}"
        ) from exc
    if binding.get("status") == STATUS_REJECTED_DIVERGENT_DUPLICATE:
        raise ExperimentRecordConflictError(
            str(
                binding.get("rejection_reason")
                or "divergent canonical content for existing experiment_id is forbidden"
            )
        )
    if binding.get("status") != STATUS_BOUND:
        raise AutomatedOfflineResearchLoopValidationError(
            "offline experiment observation binding rejected: "
            f"{binding.get('status')}: {binding.get('rejection_reason')}"
        )
    record = binding.get("experiment_record")
    if not isinstance(record, Mapping):
        raise AutomatedOfflineResearchLoopValidationError(
            "offline experiment observation binding did not return a Phase-2 record"
        )
    bound_id = str(record.get("experiment_id") or "")
    if bound_id != experiment_id:
        raise AutomatedOfflineResearchLoopValidationError(
            "bound experiment_id does not match the Phase-1 identity digest binding"
        )
    bound_identity = record.get("experiment_identity")
    if not isinstance(bound_identity, Mapping):
        raise AutomatedOfflineResearchLoopValidationError(
            "bound experiment_record is missing experiment_identity"
        )
    source_digest = _optional_identity_field(identity, "identity_digest")
    bound_digest = str(bound_identity.get("identity_digest") or "")
    if source_digest is None or bound_digest != source_digest:
        raise AutomatedOfflineResearchLoopValidationError("bound identity_digest was reinterpreted")
    return record, binding


def _run_robustness(
    *,
    request: CanonicalAutomatedOfflineResearchLoopRequestV1,
    identity: Mapping[str, Any],
    experiment_id: str,
    selected: ResearchHypothesisCandidateV1,
    policy: Mapping[str, Any],
    created_at: str,
) -> Mapping[str, Any]:
    observations = request.experiment_observations
    return build_canonical_robustness_evidence_v1(
        CanonicalRobustnessSuiteRequestV1(
            experiment_identity=identity,
            candidate_ref=selected.candidate_ref,
            dataset_ref=_bound_ref(str(identity["dataset_digest"])),
            split_policy_ref=_bound_ref(str(identity["split_policy_digest"])),
            cost_model_ref=_bound_ref(str(identity["cost_model_digest"])),
            risk_policy_ref=_bound_ref(str(identity["risk_policy_digest"])),
            seed=int(identity["seed"]),
            created_at=created_at,
            robustness_policy=policy,
            observations=observations.robustness_observations,
            hypothesis_id=selected.hypothesis_id,
            regime=selected.regime,
            parameter_region=selected.parameter_region,
            metric_definition_version=METRIC_DEFINITION_VERSION,
            experiment_id=experiment_id,
            promotion_intent="FORBIDDEN",
        )
    )


def _collect_failure_records(
    *,
    robustness_evidence: Mapping[str, Any],
    comparison_result: Mapping[str, Any],
    reality_gap_record: Mapping[str, Any],
    identity: Mapping[str, Any],
    experiment_id: str,
    selected: ResearchHypothesisCandidateV1,
    policy_digest: str,
    created_at: str,
    retest_reason: str | None,
) -> tuple[Mapping[str, Any], ...]:
    records = list(build_failure_records_for_failed_gates_v1(robustness_evidence))
    if comparison_result["overall_comparability"] != OVERALL_COMPARABLE:
        records.append(
            _failure_record(
                identity=identity,
                experiment_id=experiment_id,
                selected=selected,
                policy_digest=policy_digest,
                created_at=created_at,
                failure_class=FAILURE_CLASS_COMPARABILITY,
                retest_reason=retest_reason,
                cost_sensitivity={"comparison_rejected": 1},
            )
        )
    if reality_gap_record["overall_disposition"] == DISPOSITION_REJECTED_REALITY_GAP:
        records.append(
            _failure_record(
                identity=identity,
                experiment_id=experiment_id,
                selected=selected,
                policy_digest=policy_digest,
                created_at=created_at,
                failure_class=FAILURE_CLASS_REALITY_GAP,
                retest_reason=retest_reason,
                cost_sensitivity={"reality_gap_rejected": 1},
            )
        )
    unique: dict[str, Mapping[str, Any]] = {}
    for item in records:
        unique[str(item["failure_record_id"])] = item
    return tuple(unique[key] for key in sorted(unique))


def _failure_record(
    *,
    identity: Mapping[str, Any],
    experiment_id: str,
    selected: ResearchHypothesisCandidateV1,
    policy_digest: str,
    created_at: str,
    failure_class: str,
    retest_reason: str | None,
    cost_sensitivity: Mapping[str, Any],
) -> Mapping[str, Any]:
    return build_canonical_failure_memory_record_v1(
        CanonicalFailureMemoryRecordRequestV1(
            experiment_identity=identity,
            hypothesis_id=selected.hypothesis_id,
            failure_class=failure_class,
            failed_gate=FAILURE_CLASS_TO_FAILED_GATE[failure_class],
            rejection_reason=failure_class,
            regime=selected.regime,
            parameter_region=selected.parameter_region,
            cost_sensitivity=dict(cost_sensitivity),
            instability_indicators={"loop_identity_pending": 1},
            evidence_refs=[
                {
                    "kind": EVIDENCE_KIND_EXPERIMENT_RECORD,
                    "ref": experiment_id,
                    "digest": str(identity["identity_digest"]),
                }
            ],
            created_at=created_at,
            robustness_policy_digest=policy_digest,
            experiment_id=experiment_id,
            retest_reason=retest_reason,
        )
    )


def _optional_append(store: Any, record: Mapping[str, Any], id_field: str) -> str | None:
    if store is None:
        return None
    stored = store.append(record)
    return str(stored[id_field])


def _append_failure_records(
    store: CanonicalFailureMemoryStoreV1 | None,
    records: Sequence[Mapping[str, Any]],
) -> list[str]:
    if store is None:
        return []
    persisted: list[str] = []
    for item in records:
        stored = store.append(item)
        persisted.append(str(stored["failure_record_id"]))
    return persisted


def selected_policy(policy: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if policy is None:
        return canonical_robustness_policy_v1()
    if not isinstance(policy, Mapping) or not policy:
        raise AutomatedOfflineResearchLoopValidationError("robustness_policy must be a mapping")
    return dict(policy)


def _candidate_ids(hypotheses: Sequence[ResearchHypothesisCandidateV1]) -> list[str]:
    return sorted(_require_token("hypothesis_id", item.hypothesis_id) for item in hypotheses)


def _step(step_id: str, status: str, detail: str) -> dict[str, str]:
    return {"detail": detail, "status": status, "step_id": step_id}


def _bound_ref(digest: str) -> dict[str, str]:
    return {"digest": digest, "kind": REF_KIND_IDENTITY_DIGEST_BOUND}


def _parent_lineage_ref(identity: Mapping[str, Any]) -> str | None:
    parent_lineage = identity.get("parent_lineage")
    if isinstance(parent_lineage, Mapping):
        value = parent_lineage.get("parent_lineage_ref")
        return value if isinstance(value, str) else None
    return None


def _optional_identity_field(identity: Mapping[str, Any] | None, field_name: str) -> str | None:
    if not isinstance(identity, Mapping):
        return None
    value = identity.get(field_name)
    return str(value) if isinstance(value, str) and value else None


def _binding_persist_id(binding: Mapping[str, Any]) -> str | None:
    persist = binding.get("persist")
    if not isinstance(persist, Mapping):
        return None
    value = persist.get("experiment_record_id")
    return str(value) if isinstance(value, str) and value else None


def _observation_binding_evidence(binding: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "binding_domain": binding.get("binding_domain"),
        "bounded_auto_allowed": False,
        "experiment_id": binding.get("experiment_id"),
        "identity_digest": binding.get("identity_digest"),
        "identity_reinterpreted": False,
        "observation_owner": binding.get("observation_owner"),
        "persist": {"experiment_record_id": _binding_persist_id(binding)},
        "promotion_apply_allowed": False,
        "runtime_authority_effect": False,
        "schema_version": binding.get("schema_version"),
        "status": binding.get("status"),
    }


def _require_observation_binding(
    value: Any,
    *,
    identity: Mapping[str, Any],
    experiment_id: str,
) -> None:
    if not isinstance(value, Mapping):
        raise AutomatedOfflineResearchLoopValidationError("observation_binding is required")
    if value.get("schema_version") != OBSERVATION_BINDING_SCHEMA_VERSION:
        raise AutomatedOfflineResearchLoopValidationError(
            "observation_binding schema_version mismatch"
        )
    if value.get("binding_domain") != OBSERVATION_BINDING_DOMAIN:
        raise AutomatedOfflineResearchLoopValidationError("observation_binding domain mismatch")
    if value.get("status") != STATUS_BOUND:
        raise AutomatedOfflineResearchLoopValidationError(
            "observation_binding status must be BOUND"
        )
    if value.get("observation_owner") != OBSERVATION_OWNER_OFFLINE_EXPERIMENT_OBSERVATIONS_V1:
        raise AutomatedOfflineResearchLoopValidationError("observation_binding owner mismatch")
    if value.get("identity_reinterpreted") is not False:
        raise AutomatedOfflineResearchLoopValidationError("identity reinterpretation is forbidden")
    if value.get("promotion_apply_allowed") is not False:
        raise AutomatedOfflineResearchLoopValidationError("observation_binding cannot allow apply")
    if value.get("bounded_auto_allowed") is not False:
        raise AutomatedOfflineResearchLoopValidationError(
            "observation_binding cannot allow bounded_auto"
        )
    if value.get("runtime_authority_effect") is not False:
        raise AutomatedOfflineResearchLoopValidationError(
            "observation_binding runtime_authority_effect must be false"
        )
    if str(value.get("experiment_id") or "") != experiment_id:
        raise AutomatedOfflineResearchLoopValidationError(
            "observation_binding experiment_id does not match selected_experiment_id"
        )
    if str(value.get("identity_digest") or "") != str(identity.get("identity_digest") or ""):
        raise AutomatedOfflineResearchLoopValidationError(
            "observation_binding identity_digest does not match Phase-1 identity"
        )
    persist = value.get("persist")
    if persist is not None:
        if not isinstance(persist, Mapping):
            raise AutomatedOfflineResearchLoopValidationError(
                "observation_binding persist must be a mapping"
            )
        persisted_id = persist.get("experiment_record_id")
        if persisted_id is not None and str(persisted_id) != experiment_id:
            raise AutomatedOfflineResearchLoopValidationError(
                "observation_binding persist experiment_record_id does not match selected_experiment_id"
            )


def _require_identity(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise AutomatedOfflineResearchLoopValidationError(
            "experiment_identity present and valid is required"
        )
    identity = _plain_mapping(value)
    try:
        validate_canonical_experiment_identity_v1(identity)
    except CanonicalExperimentIdentityError as exc:
        raise AutomatedOfflineResearchLoopValidationError(
            f"experiment_identity is not a valid Phase 1 Canonical Experiment Identity: {exc}"
        ) from exc
    return identity


def _require_created_at(value: Any) -> str:
    token = _require_token("created_at", value)
    if _CREATED_AT_RE.fullmatch(token) is None:
        raise AutomatedOfflineResearchLoopValidationError("created_at must be an RFC3339 UTC token")
    return token


def _require_token(field_name: str, value: Any) -> str:
    if not isinstance(value, str):
        raise AutomatedOfflineResearchLoopValidationError(f"{field_name} must be a token")
    token = value.strip()
    if token.lower() in _UNAVAILABLE_TOKENS or _TOKEN_RE.fullmatch(token) is None:
        raise AutomatedOfflineResearchLoopValidationError(f"{field_name} must be a canonical token")
    return token


def _optional_token(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _require_sha256(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not is_valid_sha256_hex(value):
        raise AutomatedOfflineResearchLoopValidationError(
            f"{field_name} must be a sha256 hex digest"
        )
    return value


def _require_finite(field_name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AutomatedOfflineResearchLoopValidationError(f"{field_name} must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        raise AutomatedOfflineResearchLoopValidationError(
            f"non-finite numeric values are forbidden in {field_name}"
        )
    return number


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
    "AUTOMATED_OFFLINE_RESEARCH_LOOP",
    "AUTOMATED_RUNTIME_AUTHORITY",
    "AUTONOMOUS_PROMOTION",
    "CANONICAL_LOOP_STEPS",
    "CanonicalAutomatedOfflineResearchLoopRequestV1",
    "LOOP_COMPLETE",
    "LOOP_FAILED",
    "OfflineExperimentObservationsV1",
    "PROMOTION_AUTHORITY",
    "RESEARCH_LOOP_CAN_MUTATE_LIVE_CONFIG",
    "RESEARCH_LOOP_CAN_PROMOTE",
    "RESEARCH_LOOP_HAS_RUNTIME_AUTHORITY",
    "RESEARCH_LOOP_PRESENT",
    "ResearchHypothesisCandidateV1",
    "AutomatedOfflineResearchLoopValidationError",
    "canonical_record_payload_v1",
    "run_canonical_automated_offline_research_loop_v1",
    "validate_canonical_automated_offline_research_loop_v1",
]
