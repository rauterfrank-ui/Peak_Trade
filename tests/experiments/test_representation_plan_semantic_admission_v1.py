"""Resealed plan contradictions must stop before fixture evaluation or next evidence."""

import json

import pytest

from src.experiments import canonical_learning_representation_offline_evaluation_v1 as evaluation
from src.experiments import canonical_learning_representation_research_adaptation_plan_v1 as owner
from src.experiments.canonical_meta_to_learning_research_adaptation_input_v1 import (
    MetaToLearningResearchAdaptationInputRequestV1,
    validate_meta_to_learning_research_adaptation_input_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from tests.experiments.test_canonical_learning_representation_offline_evaluation_v1 import _plan


def _fail_closed_plan():
    decision = validate_meta_to_learning_research_adaptation_input_v1(
        MetaToLearningResearchAdaptationInputRequestV1(meta_learning_evidence=None)
    )
    return dict(
        owner.build_learning_representation_research_adaptation_plan_v1(
            owner.LearningRepresentationResearchAdaptationPlanRequestV1(
                adaptation_input_decision=decision
            )
        )
    )


def _reseal(plan):
    plan["plan_identity"] = owner.derive_representation_research_plan_identity_v1(
        identity_body={field: plan[field] for field in owner._PLAN_IDENTITY_FIELDS}
    )
    plan["result_digest"] = compute_content_sha256(
        {key: value for key, value in plan.items() if key != "result_digest"}
    )
    return plan


@pytest.mark.parametrize(
    "closed,changes",
    [
        (False, {"plan_status": "PLAN_UNDECLARED"}),
        (False, {"plan_status": "PLAN_FAIL_CLOSED"}),
        (False, {"research_purpose": "INVESTIGATE_FEATURE_USEFULNESS"}),
        (False, {"offline_evaluation_required": False}),
        (False, {"offline_evaluation_required": 0}),
        (False, {"offline_evaluation_required": "false"}),
        (False, {"offline_evaluation_required": None}),
        (False, {"learning_representation_lineage_ref": None}),
        (False, {"learning_representation_lineage_ref": " "}),
        (False, {"evaluation_fixture_label": ""}),
        (False, {"evaluation_fixture_label": True}),
        (False, {"domain": "foreign.representation.plan"}),
        (True, {"offline_evaluation_required": True}),
        (True, {"evaluation_fixture_label": "FIXTURE_FEATURE_USEFULNESS"}),
        (True, {"research_purpose": "INVESTIGATE_FEATURE_USEFULNESS"}),
        (True, {"learning_representation_lineage_ref": "invented.context"}),
        (True, {"offline_evaluation_required": 0}),
    ],
)
def test_resealed_contradictory_plan_stops_before_fixture_evaluation(closed, changes, monkeypatch):
    plan = _fail_closed_plan() if closed else _plan(owner.FIXTURE_LABEL_REDUNDANCY)
    plan.update(changes)
    _reseal(plan)
    calls = []
    original = evaluation._outcome_for_fixture

    def observe(**kwargs):
        calls.append(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(evaluation, "_outcome_for_fixture", observe)
    with pytest.raises(
        owner.LearningRepresentationResearchAdaptationPlanError,
        match="PLAN_SEMANTIC_CONTEXT_MISMATCH|PLAN_DOMAIN_MISMATCH",
    ):
        evaluation.run_learning_representation_offline_evaluation_v1(
            evaluation.LearningRepresentationOfflineEvaluationRequestV1(research_plan=plan)
        )
    assert calls == []


@pytest.mark.parametrize(
    "pattern",
    [None, "FIXTURE_FEATURE_USEFULNESS", owner.FIXTURE_LABEL_REDUNDANCY, "opaque.real.pattern"],
)
def test_original_plan_and_json_roundtrip_preserve_complete_evaluation(pattern):
    plan = _fail_closed_plan() if pattern is None else _plan(pattern)
    before = dict(
        evaluation.run_learning_representation_offline_evaluation_v1(
            evaluation.LearningRepresentationOfflineEvaluationRequestV1(research_plan=plan)
        )
    )
    restored = json.loads(json.dumps(plan))
    after = dict(
        evaluation.run_learning_representation_offline_evaluation_v1(
            evaluation.LearningRepresentationOfflineEvaluationRequestV1(research_plan=restored)
        )
    )
    assert after == before
    assert after["productive_apply_performed"] is False
    assert after["learning_state_mutation_performed"] is False


def test_inconsistent_plan_cannot_become_loop_c_next_evidence(tmp_path, monkeypatch):
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
        phase_24_representation_feedback_loop_evidence_v1 as loop,
    )
    from tests.learning.test_phase_24_representation_feedback_loop_evidence_v1 import (
        _meta_learning_evidence,
    )

    original_plan = loop.build_learning_representation_research_adaptation_plan_v1
    original_evidence = loop.build_learning_representation_research_evidence_v1
    emitted = []

    def contradict(request):
        plan = dict(original_plan(request))
        plan["plan_status"] = "PLAN_FAIL_CLOSED"
        return _reseal(plan)

    def observe(**kwargs):
        emitted.append(kwargs)
        return original_evidence(**kwargs)

    monkeypatch.setattr(
        loop, "build_learning_representation_research_adaptation_plan_v1", contradict
    )
    monkeypatch.setattr(loop, "build_learning_representation_research_evidence_v1", observe)
    with pytest.raises(
        owner.LearningRepresentationResearchAdaptationPlanError,
        match="PLAN_SEMANTIC_CONTEXT_MISMATCH",
    ):
        loop.run_loop_c_representation_feedback_closure_v1(
            loop.LoopCRepresentationFeedbackRequestV1(
                meta_learning_evidence=_meta_learning_evidence(tmp_path)
            )
        )
    assert emitted == []
