"""Phase 23 — deterministic Meta-Learning dual routing (AUTHORITY=NONE).

Routes typed META_EVIDENCE_V1 to exactly one bounded consumer seam:
RESEARCH_CHOICE → Optimization research feedback (M7 reuse)
LEARNING_REPRESENTATION → Learning research adaptation input
UNKNOWN/MIXED → fail-closed persistence without automatic consumer feedback
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_meta_to_learning_research_adaptation_input_v1 import (
    MetaToLearningResearchAdaptationInputRequestV1,
    validate_meta_to_learning_research_adaptation_input_v1,
)
from src.experiments.canonical_meta_to_optimization_feedback_v1 import (
    MetaToOptimizationFeedbackInputRequestV1,
    validate_meta_to_optimization_feedback_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.meta_evidence_v1 import (
    META_EVIDENCE_AUTHORITY,
    SCHEMA_VERSION as META_EVIDENCE_SCHEMA_VERSION,
    SemanticRoutingClass,
    build_meta_evidence_v1,
    validate_meta_evidence_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

SCHEMA_VERSION: Final[str] = "canonical_meta_evidence_dual_router_v1"
ROUTER_DOMAIN: Final[str] = "peak_trade.canonical_meta_evidence_dual_router.v1"

ROUTE_OPTIMIZATION_RESEARCH: Final[str] = "OPTIMIZATION_RESEARCH_FEEDBACK"
ROUTE_LEARNING_RESEARCH: Final[str] = "LEARNING_RESEARCH_ADAPTATION_INPUT"
ROUTE_NONE_FAIL_CLOSED: Final[str] = "NONE_FAIL_CLOSED"

ROUTING_STATUS_ROUTED: Final[str] = "META_EVIDENCE_ROUTED"
ROUTING_STATUS_FAIL_CLOSED: Final[str] = "META_EVIDENCE_FAIL_CLOSED_NO_AUTO_FEEDBACK"
ROUTING_STATUS_REJECTED_WRONG_CONSUMER: Final[str] = "META_EVIDENCE_REJECTED_WRONG_CONSUMER"

OPTIMIZATION_PROMOTION_AUTHORITY: Final[str] = "NONE"
OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE: Final[str] = "FORBIDDEN"
NO_AUTOMATIC_PROMOTION: Final[bool] = True
NO_SELF_DEPLOY: Final[bool] = True
NO_META_BROADCAST: Final[bool] = True


class MetaEvidenceDualRouterError(ValueError):
    """Fail-closed dual-router error."""


@dataclass(frozen=True)
class MetaEvidenceDualRouterRequestV1:
    meta_learning_evidence: Mapping[str, Any]
    semantic_routing_class: str
    classification_provenance: Mapping[str, Any] | None = None
    requested_consumer_override: str | None = None
    requested_promotion: bool = False
    requested_productive_write: bool = False
    requested_learning_state_mutation: bool = False


def classify_and_build_meta_evidence_v1(
    request: MetaEvidenceDualRouterRequestV1,
) -> MappingProxyType[str, Any]:
    if request.requested_promotion or request.requested_productive_write:
        raise MetaEvidenceDualRouterError("PRODUCTIVE_AUTHORITY_FORBIDDEN")
    if request.requested_learning_state_mutation:
        raise MetaEvidenceDualRouterError("LEARNING_STATE_MUTATION_FORBIDDEN")
    return build_meta_evidence_v1(
        meta_learning_evidence=request.meta_learning_evidence,
        semantic_routing_class=request.semantic_routing_class,
        classification_provenance=request.classification_provenance,
    )


def route_meta_evidence_v1(
    meta_evidence: Mapping[str, Any],
    *,
    requested_consumer: str | None = None,
) -> MappingProxyType[str, Any]:
    """Deliver meta evidence to at most one consumer; reject wrong-consumer delivery."""
    record = validate_meta_evidence_v1(meta_evidence)
    routing_class = str(record["semantic_routing_class"])
    intended = str(record["intended_semantic_consumer"])

    if requested_consumer is not None and requested_consumer != intended:
        return MappingProxyType(
            _routing_payload(
                status=ROUTING_STATUS_REJECTED_WRONG_CONSUMER,
                route=ROUTE_NONE_FAIL_CLOSED,
                routing_class=routing_class,
                intended_consumer=intended,
                meta_evidence=record,
                optimization_consumer=None,
                learning_consumer=None,
                reason="WRONG_CONSUMER_REQUEST",
            )
        )

    if routing_class in {
        SemanticRoutingClass.UNKNOWN.value,
        SemanticRoutingClass.MIXED.value,
    }:
        return MappingProxyType(
            _routing_payload(
                status=ROUTING_STATUS_FAIL_CLOSED,
                route=ROUTE_NONE_FAIL_CLOSED,
                routing_class=routing_class,
                intended_consumer=intended,
                meta_evidence=record,
                optimization_consumer=None,
                learning_consumer=None,
                reason="UNKNOWN_OR_MIXED_NO_AUTO_FEEDBACK",
            )
        )

    nested = record["meta_learning_evidence"]
    optimization_result = None
    learning_result = None
    route = ROUTE_NONE_FAIL_CLOSED

    if routing_class == SemanticRoutingClass.RESEARCH_CHOICE.value:
        route = ROUTE_OPTIMIZATION_RESEARCH
        optimization_result = validate_meta_to_optimization_feedback_input_v1(
            MetaToOptimizationFeedbackInputRequestV1(
                meta_learning_evidence=nested,
                expected_meta_evidence_id=str(nested["meta_evidence_id"]),
            )
        )
    elif routing_class == SemanticRoutingClass.LEARNING_REPRESENTATION.value:
        route = ROUTE_LEARNING_RESEARCH
        learning_result = validate_meta_to_learning_research_adaptation_input_v1(
            MetaToLearningResearchAdaptationInputRequestV1(
                meta_learning_evidence=nested,
                expected_meta_evidence_id=str(nested["meta_evidence_id"]),
            )
        )
    else:
        raise MetaEvidenceDualRouterError("UNSUPPORTED_ROUTING_CLASS")

    if optimization_result is not None and learning_result is not None:
        raise MetaEvidenceDualRouterError("META_BROADCAST_FORBIDDEN")

    return MappingProxyType(
        _routing_payload(
            status=ROUTING_STATUS_ROUTED,
            route=route,
            routing_class=routing_class,
            intended_consumer=intended,
            meta_evidence=record,
            optimization_consumer=optimization_result,
            learning_consumer=learning_result,
            reason="TYPED_SINGLE_CONSUMER_ROUTE",
        )
    )


def run_meta_evidence_dual_routing_cycle_v1(
    request: MetaEvidenceDualRouterRequestV1,
) -> MappingProxyType[str, Any]:
    """Classify → route → bounded consumer research input (deterministic replay chain)."""
    meta_evidence = classify_and_build_meta_evidence_v1(request)
    routed = route_meta_evidence_v1(meta_evidence)
    body = {
        "schema_version": SCHEMA_VERSION,
        "domain": ROUTER_DOMAIN,
        "meta_evidence": dict(meta_evidence),
        "routing_result": dict(routed),
        "meta_evidence_authority": META_EVIDENCE_AUTHORITY,
        "optimization_promotion_authority": OPTIMIZATION_PROMOTION_AUTHORITY,
        "optimization_direct_productive_write": OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE,
        "no_automatic_promotion": NO_AUTOMATIC_PROMOTION,
        "no_meta_broadcast": NO_META_BROADCAST,
    }
    body["cycle_digest"] = compute_content_sha256(body)
    return MappingProxyType(body)


def assert_meta_dual_routing_authority_invariants_v1() -> Mapping[str, Any]:
    terminal = {
        "META_EVIDENCE_AUTHORITY": META_EVIDENCE_AUTHORITY,
        "OPTIMIZATION_PROMOTION_AUTHORITY": OPTIMIZATION_PROMOTION_AUTHORITY,
        "OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE": OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE,
        "NO_AUTOMATIC_PROMOTION": NO_AUTOMATIC_PROMOTION,
        "NO_SELF_DEPLOY": NO_SELF_DEPLOY,
        "NO_META_BROADCAST": NO_META_BROADCAST,
        "META_ROUTING_TYPED": True,
        "UNKNOWN_MIXED_FAIL_CLOSED": True,
    }
    if terminal["OPTIMIZATION_PROMOTION_AUTHORITY"] != "NONE":
        raise MetaEvidenceDualRouterError("OPTIMIZATION_PROMOTION_AUTHORITY_EXPANSION")
    return MappingProxyType(terminal)


def _routing_payload(
    *,
    status: str,
    route: str,
    routing_class: str,
    intended_consumer: str,
    meta_evidence: Mapping[str, Any],
    optimization_consumer: Mapping[str, Any] | None,
    learning_consumer: Mapping[str, Any] | None,
    reason: str,
) -> dict[str, Any]:
    body = {
        "schema_version": SCHEMA_VERSION,
        "domain": ROUTER_DOMAIN,
        "status": status,
        "route": route,
        "semantic_routing_class": routing_class,
        "intended_semantic_consumer": intended_consumer,
        "meta_evidence_record_id": meta_evidence.get("meta_evidence_record_id"),
        "route_identity": meta_evidence.get("route_identity"),
        "source_meta_evidence_id": meta_evidence.get("source_meta_evidence_id"),
        "optimization_consumer_result_digest": (
            optimization_consumer.get("result_digest") if optimization_consumer else None
        ),
        "learning_consumer_result_digest": (
            learning_consumer.get("result_digest") if learning_consumer else None
        ),
        "optimization_consumer_invoked": optimization_consumer is not None,
        "learning_consumer_invoked": learning_consumer is not None,
        "meta_broadcast_forbidden": True,
        "reason": reason,
        "meta_evidence_schema_version": META_EVIDENCE_SCHEMA_VERSION,
    }
    body["result_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "result_digest"}
    )
    return body


__all__ = [
    "META_EVIDENCE_SCHEMA_VERSION",
    "MetaEvidenceDualRouterError",
    "MetaEvidenceDualRouterRequestV1",
    "NO_META_BROADCAST",
    "ROUTE_LEARNING_RESEARCH",
    "ROUTE_NONE_FAIL_CLOSED",
    "ROUTE_OPTIMIZATION_RESEARCH",
    "ROUTING_STATUS_FAIL_CLOSED",
    "ROUTING_STATUS_REJECTED_WRONG_CONSUMER",
    "ROUTING_STATUS_ROUTED",
    "SCHEMA_VERSION",
    "assert_meta_dual_routing_authority_invariants_v1",
    "classify_and_build_meta_evidence_v1",
    "route_meta_evidence_v1",
    "run_meta_evidence_dual_routing_cycle_v1",
]
