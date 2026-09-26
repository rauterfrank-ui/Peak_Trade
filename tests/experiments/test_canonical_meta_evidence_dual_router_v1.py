"""Phase 23 meta-evidence dual routing tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from src.experiments.canonical_meta_evidence_dual_router_v1 import (
    ROUTE_LEARNING_RESEARCH,
    ROUTE_NONE_FAIL_CLOSED,
    ROUTE_OPTIMIZATION_RESEARCH,
    ROUTING_STATUS_FAIL_CLOSED,
    ROUTING_STATUS_REJECTED_WRONG_CONSUMER,
    ROUTING_STATUS_ROUTED,
    MetaEvidenceDualRouterError,
    MetaEvidenceDualRouterRequestV1,
    assert_meta_dual_routing_authority_invariants_v1,
    classify_and_build_meta_evidence_v1,
    route_meta_evidence_v1,
    run_meta_evidence_dual_routing_cycle_v1,
)
from src.experiments.canonical_meta_learning_ingest_v1 import (
    MetaLearningIngestRequestV1,
    ingest_meta_learning_evidence_from_return_input_v1,
)
from src.experiments.canonical_meta_to_learning_research_adaptation_input_v1 import (
    MetaToLearningResearchAdaptationInputError,
    MetaToLearningResearchAdaptationInputRequestV1,
    validate_meta_to_learning_research_adaptation_input_v1,
)
from src.experiments.canonical_meta_to_optimization_feedback_v1 import (
    MetaToOptimizationFeedbackInputRequestV1,
    validate_meta_to_optimization_feedback_input_v1,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    build_optimization_experiment_evidence_from_plane_v1,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    PLANE_STATUS_COMPLETE,
    run_optimization_universe_experiment_plane_v1,
)
from src.experiments.canonical_self_learning_optimization_return_input_v1 import (
    SelfLearningOptimizationReturnInputRequestV1,
    validate_self_learning_optimization_return_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.learning.deterministic_decision_outcome_v0.meta_evidence_v1 import (
    PROVENANCE_LINEAGE_REF_KEY,
    SemanticRoutingClass,
    build_meta_evidence_v1,
)
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _plane_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state

REPO_ROOT = Path(__file__).resolve().parents[2]


def _optimization_meta(tmp_path: Path) -> dict:
    state = _learning_state(tmp_path)
    learning_evidence = export_learning_evidence_from_state_v1(state)
    plane = run_optimization_universe_experiment_plane_v1(_plane_request(learning_evidence))
    assert plane["status"] == PLANE_STATUS_COMPLETE
    opt_evidence = build_optimization_experiment_evidence_from_plane_v1(plane)
    ack = validate_self_learning_optimization_return_input_v1(
        SelfLearningOptimizationReturnInputRequestV1(
            optimization_experiment_evidence=opt_evidence,
            expected_plane_identity=str(plane["plane_identity"]),
        )
    )
    ingest = ingest_meta_learning_evidence_from_return_input_v1(
        MetaLearningIngestRequestV1(
            return_input_ack=ack,
            optimization_experiment_evidence=opt_evidence,
        )
    )
    assert ingest["status"] == "META_LEARNING_INGEST_COMPLETE"
    return dict(ingest["meta_learning_evidence"])


def _learning_representation_meta(tmp_path: Path) -> dict:
    meta = _optimization_meta(tmp_path)
    body = deepcopy(meta)
    prov = dict(body.get("provenance") or {})
    prov[PROVENANCE_LINEAGE_REF_KEY] = "mi.learning_representation.lineage.test.v1"
    body["provenance"] = prov
    return body


def test_research_choice_routes_to_optimization_only(tmp_path: Path) -> None:
    meta = _optimization_meta(tmp_path)
    cycle = run_meta_evidence_dual_routing_cycle_v1(
        MetaEvidenceDualRouterRequestV1(
            meta_learning_evidence=meta,
            semantic_routing_class=SemanticRoutingClass.RESEARCH_CHOICE.value,
        )
    )
    routed = cycle["routing_result"]
    assert routed["status"] == ROUTING_STATUS_ROUTED
    assert routed["route"] == ROUTE_OPTIMIZATION_RESEARCH
    assert routed["optimization_consumer_invoked"] is True
    assert routed["learning_consumer_invoked"] is False
    with pytest.raises(MetaToLearningResearchAdaptationInputError):
        validate_meta_to_learning_research_adaptation_input_v1(
            MetaToLearningResearchAdaptationInputRequestV1(
                meta_learning_evidence=meta,
                requested_learning_state_mutation=True,
            )
        )


def test_learning_representation_routes_to_learning_only(tmp_path: Path) -> None:
    meta = _learning_representation_meta(tmp_path)
    cycle = run_meta_evidence_dual_routing_cycle_v1(
        MetaEvidenceDualRouterRequestV1(
            meta_learning_evidence=meta,
            semantic_routing_class=SemanticRoutingClass.LEARNING_REPRESENTATION.value,
        )
    )
    routed = cycle["routing_result"]
    assert routed["status"] == ROUTING_STATUS_ROUTED
    assert routed["route"] == ROUTE_LEARNING_RESEARCH
    assert routed["learning_consumer_invoked"] is True
    assert routed["optimization_consumer_invoked"] is False


def test_unknown_and_mixed_fail_closed_without_consumers(tmp_path: Path) -> None:
    meta = _optimization_meta(tmp_path)
    for routing_class in (SemanticRoutingClass.UNKNOWN.value, SemanticRoutingClass.MIXED.value):
        record = build_meta_evidence_v1(
            meta_learning_evidence=meta,
            semantic_routing_class=routing_class,
        )
        routed = route_meta_evidence_v1(record)
        assert routed["status"] == ROUTING_STATUS_FAIL_CLOSED
        assert routed["route"] == ROUTE_NONE_FAIL_CLOSED
        assert routed["optimization_consumer_invoked"] is False
        assert routed["learning_consumer_invoked"] is False


def test_wrong_consumer_rejected(tmp_path: Path) -> None:
    meta = _optimization_meta(tmp_path)
    record = classify_and_build_meta_evidence_v1(
        MetaEvidenceDualRouterRequestV1(
            meta_learning_evidence=meta,
            semantic_routing_class=SemanticRoutingClass.RESEARCH_CHOICE.value,
        )
    )
    routed = route_meta_evidence_v1(
        record,
        requested_consumer="LEARNING_RESEARCH",
    )
    assert routed["status"] == ROUTING_STATUS_REJECTED_WRONG_CONSUMER


def test_deterministic_routing_replay(tmp_path: Path) -> None:
    meta = _optimization_meta(tmp_path)
    req = MetaEvidenceDualRouterRequestV1(
        meta_learning_evidence=meta,
        semantic_routing_class=SemanticRoutingClass.RESEARCH_CHOICE.value,
    )
    first = run_meta_evidence_dual_routing_cycle_v1(req)
    second = run_meta_evidence_dual_routing_cycle_v1(req)
    assert (
        first["meta_evidence"]["meta_evidence_record_id"]
        == second["meta_evidence"]["meta_evidence_record_id"]
    )
    assert first["meta_evidence"]["route_identity"] == second["meta_evidence"]["route_identity"]
    assert first["cycle_digest"] == second["cycle_digest"]


def test_research_choice_cannot_use_learning_route_directly(tmp_path: Path) -> None:
    meta = _optimization_meta(tmp_path)
    record = build_meta_evidence_v1(
        meta_learning_evidence=meta,
        semantic_routing_class=SemanticRoutingClass.RESEARCH_CHOICE.value,
    )
    routed = route_meta_evidence_v1(record, requested_consumer="LEARNING_RESEARCH")
    assert routed["status"] == ROUTING_STATUS_REJECTED_WRONG_CONSUMER
    assert routed["optimization_consumer_invoked"] is False
    assert routed["learning_consumer_invoked"] is False


def test_malformed_routing_class_fails_closed() -> None:
    with pytest.raises(Exception):
        build_meta_evidence_v1(
            meta_learning_evidence={"schema_version": "meta_learning_evidence_v1"},
            semantic_routing_class="BROADCAST_BOTH",
        )


def test_authority_negative_invariants() -> None:
    terminal = assert_meta_dual_routing_authority_invariants_v1()
    assert terminal["NO_META_BROADCAST"] is True
    assert terminal["OPTIMIZATION_PROMOTION_AUTHORITY"] == "NONE"


def test_optimization_feedback_rejects_promotion_request(tmp_path: Path) -> None:
    meta = _optimization_meta(tmp_path)
    with pytest.raises(Exception):
        validate_meta_to_optimization_feedback_input_v1(
            MetaToOptimizationFeedbackInputRequestV1(
                meta_learning_evidence=meta,
                requested_promotion=True,
            )
        )
