"""Phase 24 offline representation evaluation tests."""

from __future__ import annotations

from src.experiments.canonical_learning_representation_offline_evaluation_v1 import (
    LearningRepresentationOfflineEvaluationRequestV1,
    OfflineEvaluationOutcome,
    run_learning_representation_offline_evaluation_v1,
)
from src.experiments.canonical_learning_representation_research_adaptation_plan_v1 import (
    FIXTURE_LABEL_COVERAGE_WEAKNESS,
    FIXTURE_LABEL_REDUNDANCY,
    LearningRepresentationResearchAdaptationPlanRequestV1,
    build_learning_representation_research_adaptation_plan_v1,
)
from src.experiments.canonical_meta_to_learning_research_adaptation_input_v1 import (
    DISPOSITION_PROPOSE_REPRESENTATION_RESEARCH_CONTEXT,
    SCHEMA_VERSION,
)


def _plan(pattern: str) -> dict:
    decision = {
        "schema_version": SCHEMA_VERSION,
        "overall_disposition": DISPOSITION_PROPOSE_REPRESENTATION_RESEARCH_CONTEXT,
        "source_meta_evidence_id": "a" * 64,
        "adaptation_decision_identity": "b" * 64,
        "adaptation_items": [
            {"payload": {"pattern_ref": pattern, "learning_representation_lineage_ref": "x"}}
        ],
        "result_digest": "c" * 64,
    }
    return dict(
        build_learning_representation_research_adaptation_plan_v1(
            LearningRepresentationResearchAdaptationPlanRequestV1(
                adaptation_input_decision=decision
            )
        )
    )


def test_supported_fixture_outcome() -> None:
    evaluation = run_learning_representation_offline_evaluation_v1(
        LearningRepresentationOfflineEvaluationRequestV1(
            research_plan=_plan("FIXTURE_FEATURE_USEFULNESS")
        )
    )
    assert (
        evaluation["evaluation_outcome"]
        == OfflineEvaluationOutcome.RESEARCH_EVIDENCE_SUPPORTED.value
    )


def test_rejection_typed_evidence_redundancy() -> None:
    evaluation = run_learning_representation_offline_evaluation_v1(
        LearningRepresentationOfflineEvaluationRequestV1(
            research_plan=_plan(FIXTURE_LABEL_REDUNDANCY)
        )
    )
    assert evaluation["evaluation_outcome"] == OfflineEvaluationOutcome.REJECTED_REDUNDANCY.value
    assert evaluation["rejection_is_typed_evidence"] is True


def test_rejection_coverage_failure() -> None:
    evaluation = run_learning_representation_offline_evaluation_v1(
        LearningRepresentationOfflineEvaluationRequestV1(
            research_plan=_plan(FIXTURE_LABEL_COVERAGE_WEAKNESS)
        )
    )
    assert (
        evaluation["evaluation_outcome"] == OfflineEvaluationOutcome.REJECTED_COVERAGE_FAILURE.value
    )
