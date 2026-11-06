"""Phase 24 offline representation evaluation tests."""

from __future__ import annotations

import pytest

from src.experiments.canonical_learning_representation_offline_evaluation_v1 import (
    LearningRepresentationOfflineEvaluationRequestV1,
    OfflineEvaluationOutcome,
    run_learning_representation_offline_evaluation_v1,
)
from src.experiments.canonical_learning_representation_research_adaptation_plan_v1 import (
    FIXTURE_LABEL_COVERAGE_WEAKNESS,
    FIXTURE_LABEL_REDUNDANCY,
    LearningRepresentationResearchAdaptationPlanError,
    LearningRepresentationResearchAdaptationPlanRequestV1,
    build_learning_representation_research_adaptation_plan_v1,
)
from src.experiments.canonical_meta_to_learning_research_adaptation_input_v1 import (
    DISPOSITION_PROPOSE_REPRESENTATION_RESEARCH_CONTEXT,
    SCHEMA_VERSION,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256


def _plan(pattern: str) -> dict:
    from tests.experiments.test_canonical_learning_representation_research_adaptation_plan_v1 import _applicable_decision
    decision = _applicable_decision(pattern=pattern)
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


def test_changed_fixture_cannot_reuse_the_old_plan_identity_and_digest() -> None:
    plan = _plan(FIXTURE_LABEL_REDUNDANCY)
    plan["evaluation_fixture_label"] = "FIXTURE_FEATURE_USEFULNESS"
    with pytest.raises(LearningRepresentationResearchAdaptationPlanError, match="IDENTITY_MISMATCH"):
        run_learning_representation_offline_evaluation_v1(
            LearningRepresentationOfflineEvaluationRequestV1(research_plan=plan)
        )


def test_changed_parent_cannot_be_hidden_by_rehashing_only_the_outer_result() -> None:
    plan = _plan("FIXTURE_FEATURE_USEFULNESS")
    plan["source_meta_evidence_id"] = "d" * 64
    plan["result_digest"] = compute_content_sha256(
        {key: value for key, value in plan.items() if key != "result_digest"}
    )
    with pytest.raises(LearningRepresentationResearchAdaptationPlanError, match="IDENTITY_MISMATCH"):
        run_learning_representation_offline_evaluation_v1(
            LearningRepresentationOfflineEvaluationRequestV1(research_plan=plan)
        )


def test_changed_nonidentity_lineage_is_rejected_by_the_result_digest() -> None:
    plan = _plan("FIXTURE_FEATURE_USEFULNESS")
    plan["learning_representation_lineage_ref"] = "different.context"
    with pytest.raises(
        LearningRepresentationResearchAdaptationPlanError, match="RESULT_DIGEST_MISMATCH"
    ):
        run_learning_representation_offline_evaluation_v1(
            LearningRepresentationOfflineEvaluationRequestV1(research_plan=plan)
        )


@pytest.mark.parametrize(
    "field",
    [
        "learning_state_mutation_authorized",
        "productive_feature_mutation_authorized",
        "trading_configuration_mutation_authorized",
        "promotion_authorized",
    ],
)
def test_plan_cannot_claim_additional_authority_even_with_a_fresh_outer_digest(field: str) -> None:
    plan = _plan("FIXTURE_FEATURE_USEFULNESS")
    plan[field] = True
    plan["result_digest"] = compute_content_sha256(
        {key: value for key, value in plan.items() if key != "result_digest"}
    )
    with pytest.raises(LearningRepresentationResearchAdaptationPlanError, match="AUTHORITY"):
        run_learning_representation_offline_evaluation_v1(
            LearningRepresentationOfflineEvaluationRequestV1(research_plan=plan)
        )
