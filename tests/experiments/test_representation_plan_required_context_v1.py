"""A research plan cannot synthesize a successful fixture from absent adaptation facts."""
from copy import deepcopy

import pytest

from src.experiments.canonical_learning_representation_research_adaptation_plan_v1 import (
    LearningRepresentationResearchAdaptationPlanError, LearningRepresentationResearchAdaptationPlanRequestV1,
    build_learning_representation_research_adaptation_plan_v1,
)
from tests.experiments.test_canonical_learning_representation_research_adaptation_plan_v1 import _applicable_decision


@pytest.mark.parametrize("items", [None, [], [None], [{"payload": {}}], [{"payload": "bad"}],
    [{"payload": {"pattern_ref": "", "learning_representation_lineage_ref": "lineage"}}],
    [{"payload": {"pattern_ref": True, "learning_representation_lineage_ref": "lineage"}}],
    [{"payload": {"pattern_ref": "FIXTURE_FEATURE_USEFULNESS"}}],
    [{"payload": {"pattern_ref": "FIXTURE_FEATURE_USEFULNESS", "learning_representation_lineage_ref": " "}}],
])
def test_absent_or_malformed_context_cannot_become_a_default_fixture_plan(items):
    decision = deepcopy(_applicable_decision())
    decision["adaptation_items"] = items
    with pytest.raises(LearningRepresentationResearchAdaptationPlanError, match="ADAPTATION_.*REQUIRED|ADAPTATION_ITEM_CARDINALITY_INVALID|ADAPTATION_DECISION_INVALID"):
        build_learning_representation_research_adaptation_plan_v1(LearningRepresentationResearchAdaptationPlanRequestV1(adaptation_input_decision=decision))


def test_multiple_items_cannot_be_silently_reduced_to_first():
    decision = deepcopy(_applicable_decision())
    decision["adaptation_items"].append(deepcopy(decision["adaptation_items"][0]))
    with pytest.raises(LearningRepresentationResearchAdaptationPlanError, match="ADAPTATION_ITEM_CARDINALITY_INVALID|ADAPTATION_DECISION_INVALID"):
        build_learning_representation_research_adaptation_plan_v1(LearningRepresentationResearchAdaptationPlanRequestV1(adaptation_input_decision=decision))


@pytest.mark.parametrize("field", ["pattern_ref", "learning_representation_lineage_ref"])
def test_complete_resealed_decision_still_requires_the_actual_context_fact(field):
    from src.experiments.canonical_meta_to_learning_research_adaptation_input_v1 import derive_learning_adaptation_decision_identity_v1
    from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

    decision = _applicable_decision()
    decision["adaptation_items"][0]["payload"].pop(field)
    decision["adaptation_decision_identity"] = derive_learning_adaptation_decision_identity_v1(
        meta_evidence_id=decision["source_meta_evidence_id"], adaptation_items=decision["adaptation_items"],
    )
    decision["result_digest"] = compute_content_sha256({k:v for k,v in decision.items() if k != "result_digest"})
    with pytest.raises(LearningRepresentationResearchAdaptationPlanError, match="ADAPTATION_PATTERN_REF_REQUIRED|ADAPTATION_REPRESENTATION_LINEAGE_REQUIRED"):
        build_learning_representation_research_adaptation_plan_v1(LearningRepresentationResearchAdaptationPlanRequestV1(adaptation_input_decision=decision))
