"""Unified Blueprint Phase 10 — MI-crossing bounded multi-cycle offline replay (d02_multi_cycle_replay_m8).

Per cycle: MI offline orchestrator (Phase 8/9 MI-enriched M4 closure) → M5 evidence return
→ M6 meta-learning ingest/export → M7 bounded research feedback, with deterministic lineage
and prior-cycle feedback carry-forward. Does not execute search, mutate learning state,
grant promotion authority, or touch productive trading surfaces.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping as AbcMapping
from typing import Any, Final, Mapping, Sequence

from src.experiments.canonical_meta_learning_ingest_v1 import (
    INGEST_STATUS_COMPLETE,
    SCHEMA_VERSION as M6_INGEST_SCHEMA_VERSION,
    MetaLearningIngestRequestV1,
    ingest_meta_learning_evidence_from_return_input_v1,
)
from src.experiments.canonical_meta_to_optimization_feedback_v1 import (
    DISPOSITION_SELECT_AUTHORIZED_RESEARCH_SEARCH_METHOD,
    OUTCOME_APPLICABLE,
    OUTCOME_FAIL_CLOSED,
    SCHEMA_VERSION as M7_FEEDBACK_SCHEMA_VERSION,
    MetaToOptimizationFeedbackInputRequestV1,
    validate_meta_to_optimization_feedback_input_v1,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    SCHEMA_VERSION as M5_EVIDENCE_SCHEMA_VERSION,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    PLANE_STATUS_COMPLETE,
    SCHEMA_VERSION as M4_PLANE_SCHEMA_VERSION,
)
from src.experiments.canonical_optimization_universe_mi_enriched_m4_intake_v1 import (
    SCHEMA_VERSION as MI_ENRICHED_M4_INTAKE_SCHEMA_VERSION,
)
from src.experiments.canonical_self_learning_optimization_return_input_v1 import (
    SCHEMA_VERSION as M5_RETURN_SCHEMA_VERSION,
    STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT,
    SelfLearningOptimizationReturnInputRequestV1,
    validate_self_learning_optimization_return_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.meta_learning_evidence_v1 import (
    SCHEMA_VERSION as M6_EVIDENCE_SCHEMA_VERSION,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.mi_offline_durable_evidence_record_v1 import (
    SCHEMA_VERSION as MI_OFFLINE_DURABLE_EVIDENCE_SCHEMA_VERSION,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.offline_orchestrator_v1 import (
    ORCHESTRATOR_SCHEMA,
    OfflineOrchestratorInputV1,
    run_market_intelligence_offline_orchestrator_cycle_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

SCHEMA_VERSION: Final[str] = (
    "canonical_unified_blueprint_mi_crossing_bounded_multi_cycle_offline_replay_v1"
)
REPLAY_DOMAIN: Final[str] = (
    "peak_trade.canonical_unified_blueprint_mi_crossing_bounded_multi_cycle_offline_replay.v1"
)
WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_PHASE_10_MI_CROSSING_MULTI_CYCLE_OFFLINE_REPLAY_V1"
MINIMUM_CYCLE_COUNT: Final[int] = 2

REPLAY_STATUS_COMPLETE: Final[str] = "MI_CROSSING_OFFLINE_MULTI_CYCLE_REPLAY_COMPLETE"
REPLAY_STATUS_REJECTED_STALE: Final[str] = "MI_CROSSING_OFFLINE_REPLAY_REJECTED_STALE_CONTRACT"
REPLAY_STATUS_REJECTED_LINEAGE: Final[str] = "MI_CROSSING_OFFLINE_REPLAY_REJECTED_LINEAGE"
REPLAY_STATUS_REJECTED_CYCLE_ORDER: Final[str] = "MI_CROSSING_OFFLINE_REPLAY_REJECTED_CYCLE_ORDER"
REPLAY_STATUS_REJECTED_MI_CLOSURE: Final[str] = "MI_CROSSING_OFFLINE_REPLAY_REJECTED_MI_CLOSURE"

LEARNING_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
META_EVIDENCE_AUTHORITY: Final[str] = "NONE"
PROMOTION_AUTHORITY: Final[str] = "NONE"
AUTHORIZED_PRODUCTIVE_SURFACES: Final[int] = 0
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
LEARNING_STATE_MUTATION_PERFORMED: Final[bool] = False
SEARCH_EXECUTED: Final[bool] = False
MI_CROSSING_REPLAY_PERFORMED: Final[bool] = True

BOUND_CONTRACT_VERSIONS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "mi_offline_orchestrator": ORCHESTRATOR_SCHEMA,
        "mi_enriched_m4_intake": MI_ENRICHED_M4_INTAKE_SCHEMA_VERSION,
        "m4_experiment_plane": M4_PLANE_SCHEMA_VERSION,
        "m5_return_input": M5_RETURN_SCHEMA_VERSION,
        "m5_optimization_experiment_evidence": M5_EVIDENCE_SCHEMA_VERSION,
        "m6_meta_learning_ingest": M6_INGEST_SCHEMA_VERSION,
        "m6_meta_learning_evidence": M6_EVIDENCE_SCHEMA_VERSION,
        "m7_meta_to_optimization_feedback": M7_FEEDBACK_SCHEMA_VERSION,
        "m10_mi_crossing_replay": SCHEMA_VERSION,
        "mi_offline_durable_evidence": MI_OFFLINE_DURABLE_EVIDENCE_SCHEMA_VERSION,
    }
)

_LOGGER = logging.getLogger(__name__)


class MiCrossingOfflineMultiCycleReplayError(ValueError):
    """Fail-closed MI-crossing offline multi-cycle replay error."""


@dataclass(frozen=True)
class MiCrossingOfflineReplayCycleInputV1:
    cycle_index: int
    orchestrator_input: OfflineOrchestratorInputV1
    replay_seed: int
    prior_feedback_decision: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class MiCrossingDeterministicMultiCycleOfflineReplayRequestV1:
    cycles: Sequence[MiCrossingOfflineReplayCycleInputV1]
    expected_contract_versions: Mapping[str, str] | None = None
    requested_search_execution: bool = False
    requested_learning_state_mutation: bool = False
    requested_promotion: bool = False
    requested_productive_join: bool = False


def run_mi_crossing_offline_evidence_cycle_v1(
    cycle_input: MiCrossingOfflineReplayCycleInputV1,
) -> MappingProxyType[str, Any]:
    if cycle_input.cycle_index < 0:
        raise MiCrossingOfflineMultiCycleReplayError("CYCLE_INDEX_INVALID")
    if cycle_input.cycle_index > 0 and cycle_input.prior_feedback_decision is None:
        raise MiCrossingOfflineMultiCycleReplayError("PRIOR_FEEDBACK_DECISION_REQUIRED")

    orch_req = cycle_input.orchestrator_input
    if not orch_req.run_mi_enriched_m4_closure:
        raise MiCrossingOfflineMultiCycleReplayError("MI_ENRICHED_M4_CLOSURE_REQUIRED")
    if orch_req.m4_experiment_plane_request is None:
        raise MiCrossingOfflineMultiCycleReplayError("M4_PLANE_REQUEST_REQUIRED")
    if orch_req.learning_state_record is None:
        raise MiCrossingOfflineMultiCycleReplayError("LEARNING_STATE_RECORD_REQUIRED")

    prior = cycle_input.prior_feedback_decision
    cycle_n_plus_1_semantics: dict[str, Any] | None = None
    if prior is not None:
        if prior.get("schema_version") != M7_FEEDBACK_SCHEMA_VERSION:
            raise MiCrossingOfflineMultiCycleReplayError("PRIOR_FEEDBACK_SCHEMA_STALE")
        cycle_n_plus_1_semantics = _extract_cycle_n_plus_1_semantics(prior)

    orchestrator_result = run_market_intelligence_offline_orchestrator_cycle_v1(orch_req)
    mi_closure = orchestrator_result.get("mi_enriched_m4_closure")
    if not isinstance(mi_closure, AbcMapping):
        raise MiCrossingOfflineMultiCycleReplayError("MI_ENRICHED_M4_CLOSURE_MISSING")

    plane = mi_closure.get("plane_result")
    if not isinstance(plane, AbcMapping):
        raise MiCrossingOfflineMultiCycleReplayError("M4_PLANE_RESULT_MISSING")
    if plane.get("status") != PLANE_STATUS_COMPLETE:
        raise MiCrossingOfflineMultiCycleReplayError("M4_PLANE_NOT_COMPLETE")

    opt_evidence = mi_closure.get("optimization_experiment_evidence")
    if not isinstance(opt_evidence, AbcMapping):
        raise MiCrossingOfflineMultiCycleReplayError("M5_OPTIMIZATION_EVIDENCE_MISSING")

    mi_lineage = _extract_mi_lineage_refs(opt_evidence)
    if mi_lineage.get("forecast_evidence_id") in (None, ""):
        raise MiCrossingOfflineMultiCycleReplayError("MI_LINEAGE_FORECAST_EVIDENCE_ID_MISSING")

    return_ack = validate_self_learning_optimization_return_input_v1(
        SelfLearningOptimizationReturnInputRequestV1(
            optimization_experiment_evidence=opt_evidence,
            expected_plane_identity=str(plane.get("plane_identity")),
        )
    )
    if return_ack.get("status") != STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT:
        raise MiCrossingOfflineMultiCycleReplayError("M5_RETURN_ACK_NOT_ACCEPTED")

    m6_ingest = ingest_meta_learning_evidence_from_return_input_v1(
        MetaLearningIngestRequestV1(
            return_input_ack=return_ack,
            optimization_experiment_evidence=opt_evidence,
        )
    )
    if m6_ingest.get("status") != INGEST_STATUS_COMPLETE:
        raise MiCrossingOfflineMultiCycleReplayError("M6_INGEST_NOT_COMPLETE")
    meta_evidence = m6_ingest.get("meta_learning_evidence")
    if meta_evidence is None:
        raise MiCrossingOfflineMultiCycleReplayError("M6_META_EVIDENCE_MISSING")

    feedback = validate_meta_to_optimization_feedback_input_v1(
        MetaToOptimizationFeedbackInputRequestV1(meta_learning_evidence=meta_evidence)
    )
    search_item = _feedback_item(feedback, DISPOSITION_SELECT_AUTHORIZED_RESEARCH_SEARCH_METHOD)
    if search_item is None or search_item.get("outcome") != OUTCOME_FAIL_CLOSED:
        raise MiCrossingOfflineMultiCycleReplayError("M7_SEARCH_METHOD_FAIL_CLOSED_NOT_PRESERVED")

    failure_memory_replay = orchestrator_result.get("failure_memory_replay")
    durable_persist = list(orchestrator_result.get("mi_offline_durable_evidence_persist") or ())
    if orch_req.mi_offline_durable_evidence_store_root is not None and not durable_persist:
        raise MiCrossingOfflineMultiCycleReplayError("MI_OFFLINE_DURABLE_EVIDENCE_PERSIST_MISSING")
    durable_ids = [str(item.get("durable_evidence_id")) for item in durable_persist]
    durable_digests = [str(item.get("content_digest")) for item in durable_persist]

    cycle_body = {
        "cycle_index": cycle_input.cycle_index,
        "replay_seed": cycle_input.replay_seed,
        "workpackage_id": WORKPACKAGE_ID,
        "contract_versions": dict(BOUND_CONTRACT_VERSIONS),
        "cycle_n_plus_1_input_semantics": cycle_n_plus_1_semantics,
        "mi_orchestrator_schema": orchestrator_result.get("schema_name"),
        "mi_closure_digest": mi_closure.get("closure_digest"),
        "mi_lineage_refs": mi_lineage,
        "plane_identity": plane.get("plane_identity"),
        "plane_result_digest": plane.get("result_digest"),
        "optimization_experiment_evidence_digest": opt_evidence.get("content_hash"),
        "return_ack_digest": return_ack.get("result_digest"),
        "meta_evidence_id": meta_evidence.get("meta_evidence_id"),
        "meta_reproducibility_digest": meta_evidence.get("reproducibility_digest"),
        "feedback_decision_identity": feedback.get("feedback_decision_identity"),
        "prior_feedback_decision_identity": (
            prior.get("feedback_decision_identity") if prior is not None else None
        ),
        "candidate_experiment_id": opt_evidence.get("candidate_experiment_id"),
        "failure_memory_replay_digest": (
            compute_content_sha256(_json_safe(failure_memory_replay))
            if failure_memory_replay is not None
            else None
        ),
        "mi_offline_durable_evidence_ids": durable_ids,
        "mi_offline_durable_evidence_digests": durable_digests,
    }
    cycle_digest = compute_content_sha256(_json_safe(cycle_body))
    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "cycle_index": cycle_input.cycle_index,
            "cycle_digest": cycle_digest,
            "cycle_body": cycle_body,
            "mi_orchestrator_result": orchestrator_result,
            "mi_enriched_m4_closure": dict(mi_closure),
            "experiment_plane_result": dict(plane),
            "optimization_experiment_evidence": dict(opt_evidence),
            "return_input_ack": dict(return_ack),
            "meta_learning_ingest": dict(m6_ingest),
            "meta_learning_evidence": dict(meta_evidence),
            "bounded_research_feedback_decision": dict(feedback),
            "failure_memory_replay": failure_memory_replay,
            "mi_offline_durable_evidence_persist": durable_persist,
            "search_method_selection_outcome": search_item.get("outcome"),
            "learning_state_mutation_performed": False,
            "search_executed": False,
            "mi_crossing_replay_performed": True,
            "meta_evidence_authority": META_EVIDENCE_AUTHORITY,
            "promotion_authority": PROMOTION_AUTHORITY,
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
    )


def run_mi_crossing_deterministic_multi_cycle_offline_replay_v1(
    request: MiCrossingDeterministicMultiCycleOfflineReplayRequestV1,
) -> MappingProxyType[str, Any]:
    if request.requested_search_execution:
        raise MiCrossingOfflineMultiCycleReplayError("SEARCH_EXECUTION_FORBIDDEN")
    if request.requested_learning_state_mutation:
        raise MiCrossingOfflineMultiCycleReplayError("LEARNING_STATE_MUTATION_FORBIDDEN")
    if request.requested_promotion:
        raise MiCrossingOfflineMultiCycleReplayError("PROMOTION_FORBIDDEN")
    if request.requested_productive_join:
        raise MiCrossingOfflineMultiCycleReplayError("PRODUCTIVE_JOIN_FORBIDDEN")

    expected = request.expected_contract_versions or BOUND_CONTRACT_VERSIONS
    for key, version in BOUND_CONTRACT_VERSIONS.items():
        if expected.get(key) not in (None, version):
            return _replay_payload(
                status=REPLAY_STATUS_REJECTED_STALE,
                reason=f"CONTRACT_VERSION_STALE:{key}",
                cycles=(),
                replay_identity=None,
            )

    if len(request.cycles) < MINIMUM_CYCLE_COUNT:
        raise MiCrossingOfflineMultiCycleReplayError("MINIMUM_CYCLE_COUNT_NOT_MET")

    indices = [item.cycle_index for item in request.cycles]
    if indices != list(range(len(indices))):
        return _replay_payload(
            status=REPLAY_STATUS_REJECTED_CYCLE_ORDER,
            reason="CYCLE_INDEX_OUT_OF_ORDER",
            cycles=(),
            replay_identity=None,
        )

    completed: list[MappingProxyType[str, Any]] = []
    prior_feedback: Mapping[str, Any] | None = None
    for spec in request.cycles:
        if spec.cycle_index > 0:
            if prior_feedback is None:
                return _replay_payload(
                    status=REPLAY_STATUS_REJECTED_LINEAGE,
                    reason="MISSING_PRIOR_CYCLE_FEEDBACK",
                    cycles=tuple(completed),
                    replay_identity=None,
                )
            if spec.prior_feedback_decision is not None:
                if spec.prior_feedback_decision.get(
                    "feedback_decision_identity"
                ) != prior_feedback.get("feedback_decision_identity"):
                    return _replay_payload(
                        status=REPLAY_STATUS_REJECTED_LINEAGE,
                        reason="PRIOR_FEEDBACK_DECISION_MISMATCH",
                        cycles=tuple(completed),
                        replay_identity=None,
                    )
        elif spec.prior_feedback_decision is not None:
            return _replay_payload(
                status=REPLAY_STATUS_REJECTED_LINEAGE,
                reason="CYCLE_ZERO_MUST_NOT_HAVE_PRIOR_FEEDBACK",
                cycles=tuple(completed),
                replay_identity=None,
            )

        effective_prior = spec.prior_feedback_decision or prior_feedback
        try:
            cycle = run_mi_crossing_offline_evidence_cycle_v1(
                MiCrossingOfflineReplayCycleInputV1(
                    cycle_index=spec.cycle_index,
                    orchestrator_input=spec.orchestrator_input,
                    replay_seed=spec.replay_seed,
                    prior_feedback_decision=effective_prior if spec.cycle_index > 0 else None,
                )
            )
        except MiCrossingOfflineMultiCycleReplayError as exc:
            return _replay_payload(
                status=REPLAY_STATUS_REJECTED_MI_CLOSURE,
                reason=str(exc),
                cycles=tuple(completed),
                replay_identity=None,
            )
        completed.append(cycle)
        prior_feedback = cycle["bounded_research_feedback_decision"]

    replay_identity = derive_mi_crossing_multi_cycle_replay_identity_v1(
        cycles=completed,
        contract_versions=dict(BOUND_CONTRACT_VERSIONS),
    )
    return _replay_payload(
        status=REPLAY_STATUS_COMPLETE,
        reason="DETERMINISTIC_MI_CROSSING_OFFLINE_MULTI_CYCLE_REPLAY",
        cycles=tuple(completed),
        replay_identity=replay_identity,
    )


def derive_mi_crossing_multi_cycle_replay_identity_v1(
    *,
    cycles: Sequence[Mapping[str, Any]],
    contract_versions: Mapping[str, str],
) -> str:
    body = {
        "schema_version": SCHEMA_VERSION,
        "domain": REPLAY_DOMAIN,
        "workpackage_id": WORKPACKAGE_ID,
        "contract_versions": dict(contract_versions),
        "cycle_digests": [str(item.get("cycle_digest")) for item in cycles],
        "mi_lineage_digests": [
            str((item.get("cycle_body") or {}).get("mi_lineage_refs")) for item in cycles
        ],
    }
    return compute_content_sha256(_json_safe(body))


def _extract_mi_lineage_refs(
    optimization_experiment_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    provenance = optimization_experiment_evidence.get("provenance")
    if not isinstance(provenance, Mapping):
        return {}
    mi_refs = provenance.get("mi_lineage_refs")
    if isinstance(mi_refs, Mapping):
        return dict(mi_refs)
    return {}


def _extract_cycle_n_plus_1_semantics(
    prior_feedback: Mapping[str, Any],
) -> dict[str, Any]:
    applicable = [
        item
        for item in prior_feedback.get("feedback_items") or ()
        if item.get("outcome") == OUTCOME_APPLICABLE
    ]
    search_items = [
        item
        for item in prior_feedback.get("feedback_items") or ()
        if item.get("disposition") == DISPOSITION_SELECT_AUTHORIZED_RESEARCH_SEARCH_METHOD
    ]
    search_outcome = search_items[0].get("outcome") if search_items else OUTCOME_FAIL_CLOSED
    return {
        "carried_forward_applicable_dispositions": applicable,
        "search_method_selection_outcome": search_outcome,
        "search_execution_authorized": False,
        "proposal_not_authority": True,
        "meta_evidence_is_not_authority": True,
    }


def _feedback_item(decision: Mapping[str, Any], disposition: str) -> Mapping[str, Any] | None:
    for item in decision.get("feedback_items") or ():
        if item.get("disposition") == disposition:
            return item
    return None


def _replay_payload(
    *,
    status: str,
    reason: str,
    cycles: Sequence[Mapping[str, Any]],
    replay_identity: str | None,
) -> MappingProxyType[str, Any]:
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "domain": REPLAY_DOMAIN,
        "workpackage_id": WORKPACKAGE_ID,
        "status": status,
        "reason": reason,
        "replay_identity": replay_identity,
        "cycle_count": len(cycles),
        "cycles": cycles,
        "contract_versions": dict(BOUND_CONTRACT_VERSIONS),
        "learning_productive_authority": LEARNING_PRODUCTIVE_AUTHORITY,
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "meta_evidence_authority": META_EVIDENCE_AUTHORITY,
        "promotion_authority": PROMOTION_AUTHORITY,
        "authorized_productive_surfaces": AUTHORIZED_PRODUCTIVE_SURFACES,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "learning_state_mutation_performed": LEARNING_STATE_MUTATION_PERFORMED,
        "search_executed": SEARCH_EXECUTED,
        "mi_crossing_replay_performed": MI_CROSSING_REPLAY_PERFORMED,
        "multi_cycle_loop_closed": status == REPLAY_STATUS_COMPLETE
        and len(cycles) >= MINIMUM_CYCLE_COUNT,
    }
    body["result_digest"] = compute_content_sha256(
        _json_safe({key: value for key, value in body.items() if key != "result_digest"})
    )
    return MappingProxyType(body)


def _json_safe(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value
