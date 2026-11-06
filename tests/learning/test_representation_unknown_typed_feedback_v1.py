"""Valid but unevaluable plans retain deterministic evidence, without success."""

from pathlib import Path

import pytest

from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.phase_24_representation_feedback_loop_evidence_v1 import (
    LoopCRepresentationFeedbackRequestV1,
    run_loop_c_representation_feedback_closure_v1,
)
from tests.learning.test_phase_24_representation_feedback_loop_evidence_v1 import (
    _meta_learning_evidence,
)


@pytest.mark.parametrize(
    "pattern",
    ["pattern.real.versioned.ref", "FIXTURE_FEATURE_USEFULNES", "FIXTURE_UNDEFINED_POSITIVE_CASE"],
)
def test_unknown_pattern_preserves_non_evaluation_through_actual_loop_c(
    tmp_path: Path, pattern: str
) -> None:
    meta = _meta_learning_evidence(tmp_path, pattern=pattern)
    request = LoopCRepresentationFeedbackRequestV1(
        meta_learning_evidence=meta, cycle_iteration_ref="loop_c.unknown.bounded"
    )
    first = run_loop_c_representation_feedback_closure_v1(request)
    second = run_loop_c_representation_feedback_closure_v1(request)
    evaluation = first["offline_evaluation"]
    next_evidence = first["next_learning_evidence"]
    assert evaluation["evaluation_outcome"] == "FAIL_CLOSED_NO_EVALUATION"
    assert evaluation["evaluation_status"] == "EVALUATION_SKIPPED_UNSUPPORTED_FIXTURE"
    assert evaluation["evaluation_fixture_label"] == pattern
    assert evaluation["rejection_is_typed_evidence"] is True
    assert first["rejection_is_typed_evidence"] is True
    assert next_evidence["evaluation_outcome"] == evaluation["evaluation_outcome"]
    assert next_evidence["offline_evaluation_identity"] == evaluation["evaluation_identity"]
    assert next_evidence["source_meta_evidence_id"] == meta["meta_evidence_id"]
    assert next_evidence["learning_state_mutation_performed"] is False
    assert evaluation["productive_apply_performed"] is False
    assert evaluation["learning_state_mutation_performed"] is False
    assert first["content_digest"] == second["content_digest"]
    assert next_evidence == second["next_learning_evidence"]
