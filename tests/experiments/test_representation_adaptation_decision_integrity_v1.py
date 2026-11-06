"""A plan must consume the existing producer's whole decision witness and authority contract."""

from copy import deepcopy

import pytest

from src.experiments.canonical_learning_representation_research_adaptation_plan_v1 import (
    LearningRepresentationResearchAdaptationPlanError,
    LearningRepresentationResearchAdaptationPlanRequestV1,
    build_learning_representation_research_adaptation_plan_v1,
)
from tests.experiments.test_canonical_learning_representation_research_adaptation_plan_v1 import (
    _applicable_decision,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_meta_evidence_id", "d" * 64),
        ("adaptation_decision_identity", "d" * 64),
        ("result_digest", "d" * 64),
        ("domain", "other.domain"),
        ("decision_schema_version", "unknown"),
    ],
)
def test_changed_decision_witness_cannot_mint_valid_plan(field, value):
    decision = _applicable_decision()
    decision[field] = value
    with pytest.raises(
        LearningRepresentationResearchAdaptationPlanError, match="ADAPTATION_DECISION_INVALID"
    ):
        build_learning_representation_research_adaptation_plan_v1(
            LearningRepresentationResearchAdaptationPlanRequestV1(
                adaptation_input_decision=decision
            )
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("learning_productive_authority", "LIVE"),
        ("external_effect_authorized", True),
        ("learning_state_mutation_performed", True),
        ("no_self_modifying_learning", False),
    ],
)
def test_rehashed_authority_contradiction_is_rejected(field, value):
    decision = _applicable_decision()
    decision[field] = value
    decision["result_digest"] = compute_content_sha256(
        {k: v for k, v in decision.items() if k != "result_digest"}
    )
    with pytest.raises(
        LearningRepresentationResearchAdaptationPlanError, match="ADAPTATION_DECISION_INVALID"
    ):
        build_learning_representation_research_adaptation_plan_v1(
            LearningRepresentationResearchAdaptationPlanRequestV1(
                adaptation_input_decision=decision
            )
        )


def test_changed_item_cannot_reuse_parent_decision_identity():
    decision = deepcopy(_applicable_decision())
    decision["adaptation_items"][0]["payload"]["pattern_ref"] = "FIXTURE_REPRESENTATION_REDUNDANCY"
    decision["result_digest"] = compute_content_sha256(
        {k: v for k, v in decision.items() if k != "result_digest"}
    )
    with pytest.raises(
        LearningRepresentationResearchAdaptationPlanError, match="ADAPTATION_DECISION_INVALID"
    ):
        build_learning_representation_research_adaptation_plan_v1(
            LearningRepresentationResearchAdaptationPlanRequestV1(
                adaptation_input_decision=decision
            )
        )
