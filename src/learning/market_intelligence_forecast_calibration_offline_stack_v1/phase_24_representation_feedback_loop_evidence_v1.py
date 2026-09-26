"""Phase 24 — Loop C representation feedback closure (AUTHORITY=NONE).

Chains Phase-23 dual routing → bounded research plan → offline evaluation → typed
next Learning evidence. Does not mutate productive learning, features, or trading config.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_learning_representation_offline_evaluation_v1 import (
    LearningRepresentationOfflineEvaluationRequestV1,
    OfflineEvaluationOutcome,
    run_learning_representation_offline_evaluation_v1,
)
from src.experiments.canonical_learning_representation_research_adaptation_plan_v1 import (
    LearningRepresentationResearchAdaptationPlanRequestV1,
    build_learning_representation_research_adaptation_plan_v1,
)
from src.experiments.canonical_meta_evidence_dual_router_v1 import (
    ROUTE_LEARNING_RESEARCH,
    ROUTING_STATUS_ROUTED,
    MetaEvidenceDualRouterRequestV1,
    run_meta_evidence_dual_routing_cycle_v1,
)
from src.experiments.canonical_meta_to_learning_research_adaptation_input_v1 import (
    SCHEMA_VERSION as ADAPTATION_INPUT_SCHEMA,
)
from src.learning.deterministic_decision_outcome_v0.meta_evidence_v1 import (
    SemanticRoutingClass,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    STACK_DOMAIN,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

PHASE_24_SCHEMA: Final[str] = "phase_24_representation_feedback_loop_evidence_v1"
LEARNING_REPRESENTATION_EVIDENCE_SCHEMA: Final[str] = "learning_representation_research_evidence_v1"
EVIDENCE_CLASS: Final[str] = "LEARNING_REPRESENTATION_RESEARCH_EVIDENCE"
LEARNING_EVIDENCE_AUTHORITY: Final[str] = "NONE"
PRODUCTIVE_APPLY_AUTHORIZED: Final[bool] = False
NO_SELF_MODIFYING_LEARNING: Final[bool] = True


class Phase24RepresentationFeedbackError(ValueError):
    """Fail-closed Phase 24 Loop C closure."""


@dataclass(frozen=True)
class LoopCRepresentationFeedbackRequestV1:
    meta_learning_evidence: Mapping[str, Any]
    cycle_iteration_ref: str | None = None
    requested_productive_apply: bool = False
    requested_learning_state_mutation: bool = False


def derive_loop_c_cycle_identity_v1(*, lineage_body: Mapping[str, Any]) -> str:
    return compute_content_sha256(dict(lineage_body))


def build_learning_representation_research_evidence_v1(
    *,
    source_meta_evidence_id: str,
    route_identity: str,
    adaptation_decision_identity: str | None,
    plan_identity: str | None,
    evaluation_identity: str | None,
    evaluation_outcome: str,
    learning_representation_lineage_ref: str | None,
    cycle_iteration_ref: str | None,
    loop_c_cycle_identity: str,
    phase_23_routing_result_digest: str | None,
) -> MappingProxyType[str, Any]:
    body = {
        "schema_version": LEARNING_REPRESENTATION_EVIDENCE_SCHEMA,
        "domain": STACK_DOMAIN,
        "evidence_class": EVIDENCE_CLASS,
        "learning_representation_research_authority": LEARNING_EVIDENCE_AUTHORITY,
        "productive_apply_authorized": PRODUCTIVE_APPLY_AUTHORIZED,
        "learning_state_mutation_performed": False,
        "no_self_modifying_learning": NO_SELF_MODIFYING_LEARNING,
        "source_meta_evidence_id": source_meta_evidence_id,
        "route_identity": route_identity,
        "adaptation_decision_identity": adaptation_decision_identity,
        "research_plan_identity": plan_identity,
        "offline_evaluation_identity": evaluation_identity,
        "evaluation_outcome": evaluation_outcome,
        "learning_representation_lineage_ref": learning_representation_lineage_ref,
        "cycle_iteration_ref": cycle_iteration_ref,
        "loop_c_cycle_identity": loop_c_cycle_identity,
        "phase_23_routing_result_digest": phase_23_routing_result_digest,
        "plan_separate_from_productive_apply": True,
        "meta_to_learning_evidence_only": True,
        "promotion_authorized": False,
        "trading_gate_from_meta": False,
    }
    digest = compute_content_sha256({key: body[key] for key in sorted(body)})
    evidence_id = f"mi.lrepr.{digest[:48]}"
    body["learning_representation_research_evidence_id"] = evidence_id
    body["content_digest"] = digest
    return MappingProxyType(body)


def run_loop_c_representation_feedback_closure_v1(
    request: LoopCRepresentationFeedbackRequestV1,
) -> MappingProxyType[str, Any]:
    if request.requested_productive_apply or request.requested_learning_state_mutation:
        raise Phase24RepresentationFeedbackError("PRODUCTIVE_OR_STATE_MUTATION_FORBIDDEN")

    routing_cycle = run_meta_evidence_dual_routing_cycle_v1(
        MetaEvidenceDualRouterRequestV1(
            meta_learning_evidence=request.meta_learning_evidence,
            semantic_routing_class=SemanticRoutingClass.LEARNING_REPRESENTATION.value,
        )
    )
    routing_result = routing_cycle["routing_result"]
    if routing_result.get("status") != ROUTING_STATUS_ROUTED:
        raise Phase24RepresentationFeedbackError("PHASE_23_ROUTING_NOT_ROUTED")
    if routing_result.get("route") != ROUTE_LEARNING_RESEARCH:
        raise Phase24RepresentationFeedbackError("PHASE_23_ROUTE_NOT_LEARNING_RESEARCH")

    learning_consumer = routing_result.get("learning_consumer_result_digest")
    meta_evidence = routing_cycle["meta_evidence"]

    from src.experiments.canonical_meta_to_learning_research_adaptation_input_v1 import (
        MetaToLearningResearchAdaptationInputRequestV1,
        validate_meta_to_learning_research_adaptation_input_v1,
    )

    learning_decision = validate_meta_to_learning_research_adaptation_input_v1(
        MetaToLearningResearchAdaptationInputRequestV1(
            meta_learning_evidence=request.meta_learning_evidence,
            expected_meta_evidence_id=str(request.meta_learning_evidence.get("meta_evidence_id")),
        )
    )
    learning_decision_raw = dict(learning_decision)
    if learning_decision_raw.get("schema_version") != ADAPTATION_INPUT_SCHEMA:
        raise Phase24RepresentationFeedbackError("ADAPTATION_INPUT_BOUNDARY_BROKEN")

    plan = build_learning_representation_research_adaptation_plan_v1(
        LearningRepresentationResearchAdaptationPlanRequestV1(
            adaptation_input_decision=learning_decision_raw,
        )
    )
    evaluation = run_learning_representation_offline_evaluation_v1(
        LearningRepresentationOfflineEvaluationRequestV1(research_plan=dict(plan))
    )

    source_meta_id = str(meta_evidence.get("source_meta_evidence_id") or "")
    route_identity = str(meta_evidence.get("route_identity") or "")
    cycle_identity_body = {
        "source_meta_evidence_id": source_meta_id,
        "route_identity": route_identity,
        "adaptation_decision_identity": plan.get("adaptation_decision_identity"),
        "plan_identity": plan.get("plan_identity"),
        "evaluation_identity": evaluation.get("evaluation_identity"),
        "cycle_iteration_ref": request.cycle_iteration_ref,
    }
    loop_c_cycle_identity = derive_loop_c_cycle_identity_v1(lineage_body=cycle_identity_body)

    next_evidence = build_learning_representation_research_evidence_v1(
        source_meta_evidence_id=source_meta_id,
        route_identity=route_identity,
        adaptation_decision_identity=learning_decision_raw.get("adaptation_decision_identity"),
        plan_identity=str(plan.get("plan_identity") or ""),
        evaluation_identity=str(evaluation.get("evaluation_identity") or ""),
        evaluation_outcome=str(evaluation.get("evaluation_outcome") or ""),
        learning_representation_lineage_ref=plan.get("learning_representation_lineage_ref"),
        cycle_iteration_ref=request.cycle_iteration_ref,
        loop_c_cycle_identity=loop_c_cycle_identity,
        phase_23_routing_result_digest=str(routing_result.get("result_digest") or ""),
    )

    closure_body = {
        "schema_version": PHASE_24_SCHEMA,
        "domain": STACK_DOMAIN,
        "phase_23_routing_cycle_digest": routing_cycle.get("cycle_digest"),
        "phase_23_routing_result": dict(routing_result),
        "learning_adaptation_input_decision": learning_decision_raw,
        "research_adaptation_plan": dict(plan),
        "offline_evaluation": dict(evaluation),
        "next_learning_evidence": dict(next_evidence),
        "loop_c_cycle_identity": loop_c_cycle_identity,
        "learning_consumer_result_digest": learning_consumer,
        "loop_c_provenance_preserved": True,
        "no_self_modifying_learning": NO_SELF_MODIFYING_LEARNING,
        "no_direct_productive_mutation": True,
        "meta_to_learning_evidence_only": True,
        "research_adaptation_plan_separate_from_productive_apply": True,
        "rejection_is_typed_evidence": str(evaluation.get("evaluation_outcome") or "").startswith(
            "REJECTED_"
        )
        or evaluation.get("evaluation_outcome")
        == OfflineEvaluationOutcome.FAIL_CLOSED_NO_EVALUATION.value,
    }
    closure_body["content_digest"] = compute_content_sha256(closure_body)
    return MappingProxyType(closure_body)


def assert_phase_24_loop_c_authority_invariants_v1() -> Mapping[str, Any]:
    terminal = {
        "LEARNING_EVIDENCE_AUTHORITY": LEARNING_EVIDENCE_AUTHORITY,
        "PRODUCTIVE_APPLY_AUTHORIZED": PRODUCTIVE_APPLY_AUTHORIZED,
        "NO_SELF_MODIFYING_LEARNING": NO_SELF_MODIFYING_LEARNING,
        "META_TO_LEARNING_EVIDENCE_ONLY": True,
        "NO_DIRECT_PRODUCTIVE_MUTATION": True,
        "NO_TRADING_GATE_FROM_META": True,
        "PROMOTION_AUTHORIZED": False,
    }
    if terminal["LEARNING_EVIDENCE_AUTHORITY"] != "NONE":
        raise Phase24RepresentationFeedbackError("AUTHORITY_EXPANSION")
    return MappingProxyType(terminal)


__all__ = [
    "EVIDENCE_CLASS",
    "LEARNING_REPRESENTATION_EVIDENCE_SCHEMA",
    "PHASE_24_SCHEMA",
    "LoopCRepresentationFeedbackRequestV1",
    "Phase24RepresentationFeedbackError",
    "assert_phase_24_loop_c_authority_invariants_v1",
    "build_learning_representation_research_evidence_v1",
    "run_loop_c_representation_feedback_closure_v1",
]
