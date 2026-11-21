"""Loop C must bind the evaluator's complete return before minting next evidence."""

import json

import pytest

from src.experiments import canonical_learning_representation_offline_evaluation_v1 as owner
from src.experiments.canonical_learning_representation_research_adaptation_plan_v1 import (
    FIXTURE_LABEL_REDUNDANCY,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
    phase_24_representation_feedback_loop_evidence_v1 as loop,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from tests.experiments.test_canonical_learning_representation_offline_evaluation_v1 import _plan
from tests.learning.test_phase_24_representation_feedback_loop_evidence_v1 import (
    _meta_learning_evidence,
)


def _reseal(evaluation, *, keep_identity=False):
    if not keep_identity:
        # Preserve the original identity formula even for contradictory claims.
        evaluation["evaluation_identity"] = compute_content_sha256(
            {
                key: evaluation[key]
                for key in (
                    "schema_version",
                    "domain",
                    "plan_identity",
                    "evaluation_fixture_label",
                    "research_purpose",
                    "evaluation_outcome",
                    "evaluation_status",
                )
            }
        )
    evaluation["result_digest"] = compute_content_sha256(
        {key: value for key, value in evaluation.items() if key != "result_digest"}
    )
    return evaluation


@pytest.mark.parametrize(
    "fault",
    [
        "foreign_plan",
        "same_identity_foreign_plan_content",
        "outcome",
        "status",
        "fixture",
        "purpose",
        "productive_apply",
        "numeric_mutation_flag",
        "evidence_authority",
        "rejection_flag",
        "domain",
        "stale_inner_identity",
    ],
)
def test_evaluation_return_cannot_create_unbound_next_evidence(tmp_path, monkeypatch, fault):
    meta = _meta_learning_evidence(tmp_path, pattern=FIXTURE_LABEL_REDUNDANCY)
    emitted = []
    original_evidence = loop.build_learning_representation_research_evidence_v1

    def replace_return(request):
        original = dict(owner.run_learning_representation_offline_evaluation_v1(request))
        if fault == "foreign_plan":
            # A complete, independently valid evaluation from the original owner.
            return owner.run_learning_representation_offline_evaluation_v1(
                owner.LearningRepresentationOfflineEvaluationRequestV1(
                    research_plan=_plan("FIXTURE_FEATURE_USEFULNESS")
                )
            )
        if fault == "same_identity_foreign_plan_content":
            foreign_plan = dict(request.research_plan)
            foreign_plan["learning_representation_lineage_ref"] += ".other"
            foreign_plan["result_digest"] = compute_content_sha256(
                {key: value for key, value in foreign_plan.items() if key != "result_digest"}
            )
            foreign = owner.run_learning_representation_offline_evaluation_v1(
                owner.LearningRepresentationOfflineEvaluationRequestV1(research_plan=foreign_plan)
            )
            assert foreign["evaluation_identity"] == original["evaluation_identity"]
            assert foreign["plan_identity"] == original["plan_identity"]
            assert foreign["source_plan_result_digest"] != original["source_plan_result_digest"]
            return foreign
        changes = {
            "outcome": ("evaluation_outcome", "RESEARCH_EVIDENCE_SUPPORTED"),
            "status": ("evaluation_status", "EVALUATION_SKIPPED_UNSUPPORTED_FIXTURE"),
            "fixture": ("evaluation_fixture_label", "FIXTURE_FEATURE_USEFULNESS"),
            "purpose": ("research_purpose", "INVESTIGATE_FEATURE_USEFULNESS"),
            "productive_apply": ("productive_apply_performed", True),
            "numeric_mutation_flag": ("learning_state_mutation_performed", 0),
            "evidence_authority": ("evaluation_is_evidence_not_authority", False),
            "rejection_flag": ("rejection_is_typed_evidence", False),
            "domain": ("domain", "foreign.representation.evaluation"),
            "stale_inner_identity": ("evaluation_outcome", "RESEARCH_EVIDENCE_SUPPORTED"),
        }
        field, value = changes[fault]
        original[field] = value
        return _reseal(original, keep_identity=fault == "stale_inner_identity")

    def observe(**kwargs):
        emitted.append(kwargs)
        return original_evidence(**kwargs)

    monkeypatch.setattr(loop, "run_learning_representation_offline_evaluation_v1", replace_return)
    monkeypatch.setattr(loop, "build_learning_representation_research_evidence_v1", observe)
    with pytest.raises(
        owner.LearningRepresentationOfflineEvaluationError,
        match="EVALUATION_PLAN_BINDING_MISMATCH",
    ):
        loop.run_loop_c_representation_feedback_closure_v1(
            loop.LoopCRepresentationFeedbackRequestV1(meta_learning_evidence=meta)
        )
    assert emitted == []


@pytest.mark.parametrize(
    "pattern",
    [
        "FIXTURE_FEATURE_USEFULNESS",
        FIXTURE_LABEL_REDUNDANCY,
        "opaque.real.pattern",
        "FIXTURE_OTHER_UNSTABLE_OOS",
    ],
)
def test_original_json_return_preserves_the_complete_loop_c_closure(tmp_path, monkeypatch, pattern):
    request = loop.LoopCRepresentationFeedbackRequestV1(
        meta_learning_evidence=_meta_learning_evidence(tmp_path, pattern=pattern),
        cycle_iteration_ref="return-binding-json-control",
    )
    original = dict(loop.run_loop_c_representation_feedback_closure_v1(request))

    def json_return(evaluation_request):
        result = owner.run_learning_representation_offline_evaluation_v1(evaluation_request)
        return json.loads(json.dumps(dict(result)))

    monkeypatch.setattr(loop, "run_learning_representation_offline_evaluation_v1", json_return)
    restored = dict(loop.run_loop_c_representation_feedback_closure_v1(request))
    assert restored == original
    assert restored["next_learning_evidence"]["productive_apply_authorized"] is False
    assert restored["next_learning_evidence"]["learning_state_mutation_performed"] is False
