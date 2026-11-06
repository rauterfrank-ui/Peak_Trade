"""Phase 24 representation research adaptation plan tests."""

from __future__ import annotations

import pytest

from src.experiments.canonical_learning_representation_research_adaptation_plan_v1 import (
    FIXTURE_LABEL_REDUNDANCY,
    LearningRepresentationResearchAdaptationPlanError,
    LearningRepresentationResearchAdaptationPlanRequestV1,
    RepresentationResearchPurpose,
    build_learning_representation_research_adaptation_plan_v1,
    classify_representation_research_purpose_v1,
)
from src.experiments.canonical_meta_to_learning_research_adaptation_input_v1 import (
    DISPOSITION_NO_ACTION_FAIL_CLOSED,
    DISPOSITION_PROPOSE_REPRESENTATION_RESEARCH_CONTEXT,
    SCHEMA_VERSION,
)


def _applicable_decision(*, pattern: str = "FIXTURE_FEATURE_USEFULNESS") -> dict:
    from src.experiments.canonical_meta_to_learning_research_adaptation_input_v1 import (
        _adaptation_item, _decision_payload, OUTCOME_APPLICABLE,
    )
    return dict(_decision_payload(
        meta_evidence={"meta_evidence_id": "a" * 64, "reproducibility_digest": "c" * 64},
        adaptation_items=(_adaptation_item(
            disposition=DISPOSITION_PROPOSE_REPRESENTATION_RESEARCH_CONTEXT,
            outcome=OUTCOME_APPLICABLE, reason="REPRESENTATION_RESEARCH_CONTEXT_ONLY",
            payload={"pattern_ref": pattern, "learning_representation_lineage_ref": "mi.lineage.test",
                     "learning_state_mutation_authorized": False, "productive_apply_authorized": False},
        ),),
        overall_disposition=DISPOSITION_PROPOSE_REPRESENTATION_RESEARCH_CONTEXT,
        overall_reason="BOUNDED_LEARNING_RESEARCH_ADAPTATION_INPUT_ONLY",
    ))


def test_plan_separate_from_productive_apply() -> None:
    plan = build_learning_representation_research_adaptation_plan_v1(
        LearningRepresentationResearchAdaptationPlanRequestV1(
            adaptation_input_decision=_applicable_decision(),
        )
    )
    assert plan["productive_apply_authorized"] is False
    assert plan["plan_not_authority"] is True
    assert plan["offline_evaluation_required"] is True
    with pytest.raises(LearningRepresentationResearchAdaptationPlanError):
        build_learning_representation_research_adaptation_plan_v1(
            LearningRepresentationResearchAdaptationPlanRequestV1(
                adaptation_input_decision=_applicable_decision(),
                requested_productive_apply=True,
            )
        )


def test_purpose_classification_deterministic() -> None:
    assert (
        classify_representation_research_purpose_v1(pattern_ref=FIXTURE_LABEL_REDUNDANCY)
        == RepresentationResearchPurpose.ASSESS_REDUNDANCY.value
    )


def test_fail_closed_input_yields_no_action_plan() -> None:
    from src.experiments.canonical_meta_to_learning_research_adaptation_input_v1 import (
        MetaToLearningResearchAdaptationInputRequestV1, validate_meta_to_learning_research_adaptation_input_v1,
    )
    decision = validate_meta_to_learning_research_adaptation_input_v1(
        MetaToLearningResearchAdaptationInputRequestV1(meta_learning_evidence=None),
    )
    plan = build_learning_representation_research_adaptation_plan_v1(
        LearningRepresentationResearchAdaptationPlanRequestV1(adaptation_input_decision=decision)
    )
    assert plan["research_purpose"] == RepresentationResearchPurpose.NO_ACTION_FAIL_CLOSED.value
    assert plan["offline_evaluation_required"] is False
