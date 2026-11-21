"""Phase 24 Loop C representation feedback closure tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from src.experiments.canonical_learning_representation_research_adaptation_plan_v1 import (
    FIXTURE_LABEL_REDUNDANCY,
)
from src.experiments.canonical_meta_learning_ingest_v1 import (
    MetaLearningIngestRequestV1,
    ingest_meta_learning_evidence_from_return_input_v1,
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
    MetaEvidenceValidationError,
    PROVENANCE_LINEAGE_REF_KEY,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.phase_24_representation_feedback_loop_evidence_v1 import (
    EVIDENCE_CLASS,
    LoopCRepresentationFeedbackRequestV1,
    assert_phase_24_loop_c_authority_invariants_v1,
    run_loop_c_representation_feedback_closure_v1,
)
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _plane_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state

REPO_ROOT = Path(__file__).resolve().parents[2]


def _meta_learning_evidence(tmp_path: Path, *, pattern: str = "FIXTURE_FEATURE_USEFULNESS") -> dict:
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
    meta = dict(ingest["meta_learning_evidence"])
    meta["repeated_success_or_failure_pattern"] = pattern
    prov = dict(meta.get("provenance") or {})
    prov[PROVENANCE_LINEAGE_REF_KEY] = "mi.learning_representation.lineage.test.v1"
    meta["provenance"] = prov
    return meta


def test_loop_c_full_chain_generates_next_learning_evidence(tmp_path: Path) -> None:
    meta = _meta_learning_evidence(tmp_path)
    closure = run_loop_c_representation_feedback_closure_v1(
        LoopCRepresentationFeedbackRequestV1(
            meta_learning_evidence=meta,
            cycle_iteration_ref="loop_c.iteration.1",
        )
    )
    assert closure["phase_23_routing_result"]["learning_consumer_invoked"] is True
    assert closure["research_adaptation_plan"]["productive_apply_authorized"] is False
    next_evidence = closure["next_learning_evidence"]
    assert next_evidence["evidence_class"] == EVIDENCE_CLASS
    assert next_evidence["source_meta_evidence_id"] == meta["meta_evidence_id"]
    assert next_evidence["loop_c_cycle_identity"]
    assert next_evidence["learning_state_mutation_performed"] is False


def test_loop_c_deterministic_replay(tmp_path: Path) -> None:
    meta = _meta_learning_evidence(tmp_path)
    req = LoopCRepresentationFeedbackRequestV1(
        meta_learning_evidence=meta,
        cycle_iteration_ref="loop_c.iteration.replay",
    )
    first = run_loop_c_representation_feedback_closure_v1(req)
    second = run_loop_c_representation_feedback_closure_v1(req)
    assert first["loop_c_cycle_identity"] == second["loop_c_cycle_identity"]
    assert (
        first["next_learning_evidence"]["learning_representation_research_evidence_id"]
        == second["next_learning_evidence"]["learning_representation_research_evidence_id"]
    )
    assert first["content_digest"] == second["content_digest"]


@pytest.mark.parametrize("foreign_context", ["lineage", "pattern", "same_parent_pattern"])
def test_foreign_valid_router_receipt_cannot_reach_plan_or_evaluation(
    tmp_path: Path, monkeypatch, foreign_context: str
) -> None:
    from src.experiments.canonical_meta_evidence_dual_router_v1 import (
        MetaEvidenceDualRouterRequestV1,
    )
    from src.learning.deterministic_decision_outcome_v0.meta_learning_evidence_v1 import (
        derive_meta_evidence_id_v1,
    )
    from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
        compute_content_hash_v0,
    )
    from src.learning.market_intelligence_forecast_calibration_offline_stack_v1 import (
        phase_24_representation_feedback_loop_evidence_v1 as feedback,
    )

    meta = _meta_learning_evidence(tmp_path)
    foreign = deepcopy(meta)
    if foreign_context == "lineage":
        foreign["provenance"][PROVENANCE_LINEAGE_REF_KEY] += ".other"
    else:
        foreign["repeated_success_or_failure_pattern"] = FIXTURE_LABEL_REDUNDANCY
    if foreign_context != "same_parent_pattern":
        foreign["reproducibility_digest"] = compute_content_hash_v0(
            {
                k: v
                for k, v in foreign.items()
                if k not in {"reproducibility_digest", "meta_evidence_id"}
            }
        )
        foreign["meta_evidence_id"] = derive_meta_evidence_id_v1(
            reproducibility_digest=foreign["reproducibility_digest"]
        )
    # Both packets come from the real typed router. Each is valid on its own;
    # the other representation's receipt must not authorize this request's plan.
    routed = feedback.run_meta_evidence_dual_routing_cycle_v1(
        MetaEvidenceDualRouterRequestV1(
            meta_learning_evidence=foreign, semantic_routing_class="LEARNING_REPRESENTATION"
        )
    )
    assert routed["routing_result"]["learning_consumer_invoked"] is True
    # Matching parent labels alone do not bind the consumed pattern/content.
    assert (routed["meta_evidence"]["source_meta_evidence_id"] == meta["meta_evidence_id"]) == (
        foreign_context == "same_parent_pattern"
    )
    monkeypatch.setattr(feedback, "run_meta_evidence_dual_routing_cycle_v1", lambda _: routed)
    calls = []
    for name in (
        "build_learning_representation_research_adaptation_plan_v1",
        "run_learning_representation_offline_evaluation_v1",
    ):
        original = getattr(feedback, name)

        def observe(*args, _original=original, _name=name, **kwargs):
            calls.append(_name)
            return _original(*args, **kwargs)

        monkeypatch.setattr(feedback, name, observe)
    with pytest.raises(
        feedback.Phase24RepresentationFeedbackError, match="PHASE_23_LEARNING_ADMISSION_MISMATCH"
    ):
        feedback.run_loop_c_representation_feedback_closure_v1(
            LoopCRepresentationFeedbackRequestV1(meta_learning_evidence=meta)
        )
    assert calls == []


def test_rejection_path_preserves_typed_evidence(tmp_path: Path) -> None:
    meta = _meta_learning_evidence(tmp_path, pattern=FIXTURE_LABEL_REDUNDANCY)
    closure = run_loop_c_representation_feedback_closure_v1(
        LoopCRepresentationFeedbackRequestV1(meta_learning_evidence=meta)
    )
    assert closure["rejection_is_typed_evidence"] is True
    assert closure["next_learning_evidence"]["evaluation_outcome"].startswith("REJECTED_")


def test_malformed_meta_missing_lineage_fail_closed(tmp_path: Path) -> None:
    meta = _meta_learning_evidence(tmp_path)
    broken = deepcopy(meta)
    broken["provenance"] = {}
    with pytest.raises(MetaEvidenceValidationError):
        run_loop_c_representation_feedback_closure_v1(
            LoopCRepresentationFeedbackRequestV1(meta_learning_evidence=broken)
        )


def test_authority_negative_invariants() -> None:
    terminal = assert_phase_24_loop_c_authority_invariants_v1()
    assert terminal["NO_SELF_MODIFYING_LEARNING"] is True
    assert terminal["PRODUCTIVE_APPLY_AUTHORIZED"] is False
