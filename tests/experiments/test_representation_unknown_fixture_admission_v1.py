"""An unknown pattern is not a positive offline representation evaluation."""

import pytest

from src.experiments.canonical_learning_representation_offline_evaluation_v1 import (
    LearningRepresentationOfflineEvaluationRequestV1,
    run_learning_representation_offline_evaluation_v1,
)
from tests.experiments.test_canonical_learning_representation_offline_evaluation_v1 import _plan


@pytest.mark.parametrize(
    "pattern",
    ["pattern.real.versioned.ref", "FIXTURE_FEATURE_USEFULNES", "FIXTURE_UNDEFINED_POSITIVE_CASE"],
)
def test_valid_plan_with_unknown_fixture_cannot_default_to_supported(pattern):
    plan = _plan(pattern)
    result = run_learning_representation_offline_evaluation_v1(
        LearningRepresentationOfflineEvaluationRequestV1(research_plan=plan)
    )
    assert result["evaluation_outcome"] == "FAIL_CLOSED_NO_EVALUATION"
    assert result["evaluation_status"] == "EVALUATION_SKIPPED_UNSUPPORTED_FIXTURE"
    assert result["rejection_is_typed_evidence"] is True
    assert result["productive_apply_performed"] is False


@pytest.mark.parametrize(
    "pattern",
    [
        "FIXTURE_FEATURE_USEFULNESS",
        "FIXTURE_REGIME_CONDITIONALITY",
        "FIXTURE_CONTEXT_FAMILY_USEFULNESS",
    ],
)
def test_existing_explicit_success_fixtures_remain_supported(pattern):
    result = run_learning_representation_offline_evaluation_v1(
        LearningRepresentationOfflineEvaluationRequestV1(research_plan=_plan(pattern))
    )
    assert result["evaluation_outcome"] == "RESEARCH_EVIDENCE_SUPPORTED"
