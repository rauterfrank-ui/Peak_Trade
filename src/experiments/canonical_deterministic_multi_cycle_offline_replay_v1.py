"""M8 — Deterministic multi-cycle offline replay of M1→M7 evidence loop.

Orchestrates existing contract seams only. Does not unify universe state,
execute search, mutate learning_state_record_v0, or authorize productive surfaces.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

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
    build_optimization_experiment_evidence_from_plane_v1,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    PLANE_STATUS_COMPLETE,
    OptimizationUniverseExperimentPlaneRequestV1,
    SCHEMA_VERSION as M4_PLANE_SCHEMA_VERSION,
    run_optimization_universe_experiment_plane_v1,
)
from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    SCHEMA_VERSION as M1_INPUT_SCHEMA_VERSION,
    CanonicalOptimizationUniverseLearningInputRequestV1,
    validate_canonical_optimization_universe_learning_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.meta_learning_evidence_v1 import (
    SCHEMA_VERSION as M6_EVIDENCE_SCHEMA_VERSION,
)
from src.experiments.canonical_meta_learning_ingest_v1 import (
    INGEST_STATUS_COMPLETE,
    SCHEMA_VERSION as M6_INGEST_SCHEMA_VERSION,
    MetaLearningIngestRequestV1,
    ingest_meta_learning_evidence_from_return_input_v1,
)
from src.experiments.canonical_self_learning_optimization_return_input_v1 import (
    SCHEMA_VERSION as M5_RETURN_SCHEMA_VERSION,
    STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT,
    SelfLearningOptimizationReturnInputRequestV1,
    validate_self_learning_optimization_return_input_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

SCHEMA_VERSION: Final[str] = "canonical_deterministic_multi_cycle_offline_replay_v1"
REPLAY_DOMAIN: Final[str] = "peak_trade.canonical_deterministic_multi_cycle_offline_replay.v1"
MINIMUM_CYCLE_COUNT: Final[int] = 2

REPLAY_STATUS_COMPLETE: Final[str] = "OFFLINE_MULTI_CYCLE_REPLAY_COMPLETE"
REPLAY_STATUS_REJECTED_STALE: Final[str] = "OFFLINE_REPLAY_REJECTED_STALE_CONTRACT"
REPLAY_STATUS_REJECTED_LINEAGE: Final[str] = "OFFLINE_REPLAY_REJECTED_LINEAGE"
REPLAY_STATUS_REJECTED_CYCLE_ORDER: Final[str] = "OFFLINE_REPLAY_REJECTED_CYCLE_ORDER"

LEARNING_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
OPTIMIZATION_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
META_EVIDENCE_AUTHORITY: Final[str] = "NONE"
AUTHORIZED_PRODUCTIVE_SURFACES: Final[int] = 0
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
LEARNING_STATE_MUTATION_PERFORMED: Final[bool] = False
SEARCH_EXECUTED: Final[bool] = False

BOUND_CONTRACT_VERSIONS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "m1_optimization_learning_input": M1_INPUT_SCHEMA_VERSION,
        "m4_experiment_plane": M4_PLANE_SCHEMA_VERSION,
        "m5_return_input": M5_RETURN_SCHEMA_VERSION,
        "m5_optimization_experiment_evidence": M5_EVIDENCE_SCHEMA_VERSION,
        "m6_meta_learning_ingest": M6_INGEST_SCHEMA_VERSION,
        "m6_meta_learning_evidence": M6_EVIDENCE_SCHEMA_VERSION,
        "m7_meta_to_optimization_feedback": M7_FEEDBACK_SCHEMA_VERSION,
        "m8_replay": SCHEMA_VERSION,
    }
)

_LOGGER = logging.getLogger(__name__)


class OfflineMultiCycleReplayError(ValueError):
    """Fail-closed offline multi-cycle replay error."""


@dataclass(frozen=True)
class OfflineReplayCycleInputV1:
    cycle_index: int
    learning_evidence: Mapping[str, Any]
    plane_request: OptimizationUniverseExperimentPlaneRequestV1
    replay_seed: int
    prior_feedback_decision: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class DeterministicMultiCycleOfflineReplayRequestV1:
    cycles: Sequence[OfflineReplayCycleInputV1]
    expected_contract_versions: Mapping[str, str] | None = None
    requested_search_execution: bool = False
    requested_learning_state_mutation: bool = False


def run_offline_evidence_cycle_v1(
    cycle_input: OfflineReplayCycleInputV1,
) -> MappingProxyType[str, Any]:
    if cycle_input.cycle_index < 0:
        raise OfflineMultiCycleReplayError("CYCLE_INDEX_INVALID")
    if cycle_input.cycle_index > 0 and cycle_input.prior_feedback_decision is None:
        raise OfflineMultiCycleReplayError("PRIOR_FEEDBACK_DECISION_REQUIRED")

    prior = cycle_input.prior_feedback_decision
    cycle_n_plus_1_semantics: dict[str, Any] | None = None
    if prior is not None:
        if prior.get("schema_version") != M7_FEEDBACK_SCHEMA_VERSION:
            raise OfflineMultiCycleReplayError("PRIOR_FEEDBACK_SCHEMA_STALE")
        cycle_n_plus_1_semantics = _extract_cycle_n_plus_1_semantics(prior)

    learning_input = validate_canonical_optimization_universe_learning_input_v1(
        CanonicalOptimizationUniverseLearningInputRequestV1(
            learning_evidence=cycle_input.learning_evidence
        )
    )
    plane = run_optimization_universe_experiment_plane_v1(cycle_input.plane_request)
    if plane.get("status") != PLANE_STATUS_COMPLETE:
        raise OfflineMultiCycleReplayError("M4_PLANE_NOT_COMPLETE")
    opt_evidence = build_optimization_experiment_evidence_from_plane_v1(plane)
    return_ack = validate_self_learning_optimization_return_input_v1(
        SelfLearningOptimizationReturnInputRequestV1(
            optimization_experiment_evidence=opt_evidence,
            expected_plane_identity=str(plane.get("plane_identity")),
        )
    )
    if return_ack.get("status") != STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT:
        raise OfflineMultiCycleReplayError("M5_RETURN_ACK_NOT_ACCEPTED")
    m6_ingest = ingest_meta_learning_evidence_from_return_input_v1(
        MetaLearningIngestRequestV1(
            return_input_ack=return_ack,
            optimization_experiment_evidence=opt_evidence,
        )
    )
    if m6_ingest.get("status") != INGEST_STATUS_COMPLETE:
        raise OfflineMultiCycleReplayError("M6_INGEST_NOT_COMPLETE")
    meta_evidence = m6_ingest.get("meta_learning_evidence")
    if meta_evidence is None:
        raise OfflineMultiCycleReplayError("M6_META_EVIDENCE_MISSING")
    feedback = validate_meta_to_optimization_feedback_input_v1(
        MetaToOptimizationFeedbackInputRequestV1(meta_learning_evidence=meta_evidence)
    )
    search_item = _feedback_item(feedback, DISPOSITION_SELECT_AUTHORIZED_RESEARCH_SEARCH_METHOD)
    if search_item is None or search_item.get("outcome") != OUTCOME_FAIL_CLOSED:
        raise OfflineMultiCycleReplayError("M7_SEARCH_METHOD_FAIL_CLOSED_NOT_PRESERVED")

    cycle_body = {
        "cycle_index": cycle_input.cycle_index,
        "replay_seed": cycle_input.replay_seed,
        "contract_versions": dict(BOUND_CONTRACT_VERSIONS),
        "cycle_n_plus_1_input_semantics": cycle_n_plus_1_semantics,
        "learning_input_digest": learning_input.get("result_digest"),
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
        "learning_evidence_digest": learning_input.get("learning_evidence_digest"),
    }
    cycle_digest = compute_content_sha256(_json_safe(cycle_body))
    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "cycle_index": cycle_input.cycle_index,
            "cycle_digest": cycle_digest,
            "cycle_body": cycle_body,
            "learning_input_validation": dict(learning_input),
            "experiment_plane_result": dict(plane),
            "optimization_experiment_evidence": dict(opt_evidence),
            "return_input_ack": dict(return_ack),
            "meta_learning_ingest": dict(m6_ingest),
            "meta_learning_evidence": dict(meta_evidence),
            "bounded_research_feedback_decision": dict(feedback),
            "search_method_selection_outcome": search_item.get("outcome"),
            "learning_state_mutation_performed": False,
            "search_executed": False,
        }
    )


def run_deterministic_multi_cycle_offline_replay_v1(
    request: DeterministicMultiCycleOfflineReplayRequestV1,
) -> MappingProxyType[str, Any]:
    if request.requested_search_execution:
        raise OfflineMultiCycleReplayError("SEARCH_EXECUTION_FORBIDDEN")
    if request.requested_learning_state_mutation:
        raise OfflineMultiCycleReplayError("LEARNING_STATE_MUTATION_FORBIDDEN")

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
        raise OfflineMultiCycleReplayError("MINIMUM_CYCLE_COUNT_NOT_MET")

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
        cycle = run_offline_evidence_cycle_v1(
            OfflineReplayCycleInputV1(
                cycle_index=spec.cycle_index,
                learning_evidence=spec.learning_evidence,
                plane_request=spec.plane_request,
                replay_seed=spec.replay_seed,
                prior_feedback_decision=effective_prior if spec.cycle_index > 0 else None,
            )
        )
        completed.append(cycle)
        prior_feedback = cycle["bounded_research_feedback_decision"]

    replay_identity = derive_multi_cycle_replay_identity_v1(
        cycles=completed,
        contract_versions=dict(BOUND_CONTRACT_VERSIONS),
    )
    return _replay_payload(
        status=REPLAY_STATUS_COMPLETE,
        reason="DETERMINISTIC_OFFLINE_MULTI_CYCLE_REPLAY",
        cycles=tuple(completed),
        replay_identity=replay_identity,
    )


def derive_multi_cycle_replay_identity_v1(
    *,
    cycles: Sequence[Mapping[str, Any]],
    contract_versions: Mapping[str, str],
) -> str:
    body = {
        "schema_version": SCHEMA_VERSION,
        "domain": REPLAY_DOMAIN,
        "contract_versions": dict(contract_versions),
        "cycle_digests": [str(item.get("cycle_digest")) for item in cycles],
    }
    return compute_content_sha256(_json_safe(body))


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
        "status": status,
        "reason": reason,
        "replay_identity": replay_identity,
        "cycle_count": len(cycles),
        "cycles": cycles,
        "contract_versions": dict(BOUND_CONTRACT_VERSIONS),
        "learning_productive_authority": LEARNING_PRODUCTIVE_AUTHORITY,
        "optimization_productive_authority": OPTIMIZATION_PRODUCTIVE_AUTHORITY,
        "meta_evidence_authority": META_EVIDENCE_AUTHORITY,
        "authorized_productive_surfaces": AUTHORIZED_PRODUCTIVE_SURFACES,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "learning_state_mutation_performed": LEARNING_STATE_MUTATION_PERFORMED,
        "search_executed": SEARCH_EXECUTED,
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
