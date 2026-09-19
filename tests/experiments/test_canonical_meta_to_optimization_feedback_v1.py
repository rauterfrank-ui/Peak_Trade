"""Tests for M7 meta-to-optimization bounded research feedback."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.experiments.canonical_meta_to_optimization_feedback_v1 import (
    AUTHORIZED_PRODUCTIVE_SURFACES,
    DISPOSITION_ALLOCATE_BOUNDED_RESEARCH_BUDGET,
    DISPOSITION_PRIORITIZE_RESEARCH_EXPERIMENT,
    DISPOSITION_PROPOSE_RESEARCH_HYPOTHESIS,
    DISPOSITION_SELECT_AUTHORIZED_RESEARCH_SEARCH_METHOD,
    OUTCOME_APPLICABLE,
    OUTCOME_FAIL_CLOSED,
    REASON_SEARCH_CAPABILITY_NOT_REGISTERED,
    REASON_SEARCH_METHOD_UNKNOWN,
    SEARCH_EXECUTED,
    TRADING_SELECTION_EFFECT,
    MetaToOptimizationFeedbackError,
    MetaToOptimizationFeedbackInputRequestV1,
    validate_meta_to_optimization_feedback_input_v1,
)
from src.learning.deterministic_decision_outcome_v0.meta_learning_ingest_v1 import (
    INGEST_STATUS_COMPLETE,
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
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _plane_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state
from src.learning.deterministic_decision_outcome_v0.self_learning_optimization_return_input_v1 import (
    SelfLearningOptimizationReturnInputRequestV1,
    validate_self_learning_optimization_return_input_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_meta_to_optimization_feedback_v1.py"


def _meta_evidence(tmp_path: Path):
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
    assert ingest["status"] == INGEST_STATUS_COMPLETE
    return ingest["meta_learning_evidence"]


def test_feedback_decision_identity_deterministic(tmp_path: Path) -> None:
    meta = _meta_evidence(tmp_path)
    first = validate_meta_to_optimization_feedback_input_v1(
        MetaToOptimizationFeedbackInputRequestV1(meta_learning_evidence=meta)
    )
    second = validate_meta_to_optimization_feedback_input_v1(
        MetaToOptimizationFeedbackInputRequestV1(meta_learning_evidence=meta)
    )
    assert first["feedback_decision_identity"] == second["feedback_decision_identity"]
    assert first["search_executed"] is False
    assert SEARCH_EXECUTED is False
    assert TRADING_SELECTION_EFFECT == "NONE"


def test_m7_chain_partial_research_feedback_with_fail_closed_search_method(tmp_path: Path) -> None:
    meta = _meta_evidence(tmp_path)
    decision = validate_meta_to_optimization_feedback_input_v1(
        MetaToOptimizationFeedbackInputRequestV1(meta_learning_evidence=meta)
    )
    by_disposition = {item["disposition"]: item for item in decision["feedback_items"]}
    assert (
        by_disposition[DISPOSITION_PRIORITIZE_RESEARCH_EXPERIMENT]["outcome"] == OUTCOME_APPLICABLE
    )
    search_item = by_disposition[DISPOSITION_SELECT_AUTHORIZED_RESEARCH_SEARCH_METHOD]
    assert search_item["outcome"] == OUTCOME_FAIL_CLOSED
    assert search_item["reason"] in {
        REASON_SEARCH_METHOD_UNKNOWN,
        REASON_SEARCH_CAPABILITY_NOT_REGISTERED,
    }
    assert (
        by_disposition[DISPOSITION_ALLOCATE_BOUNDED_RESEARCH_BUDGET]["outcome"]
        == OUTCOME_APPLICABLE
    )
    assert by_disposition[DISPOSITION_PROPOSE_RESEARCH_HYPOTHESIS]["outcome"] == OUTCOME_APPLICABLE
    assert decision["authorized_productive_surfaces"] == 0
    assert AUTHORIZED_PRODUCTIVE_SURFACES == 0


def test_rejects_stale_meta_evidence_schema() -> None:
    decision = validate_meta_to_optimization_feedback_input_v1(
        MetaToOptimizationFeedbackInputRequestV1(
            meta_learning_evidence={"schema_version": "meta_learning_evidence_v0"},
            expected_meta_learning_evidence_schema_version="meta_learning_evidence_v0",
        )
    )
    assert decision["overall_disposition"] == "NO_ACTION_FAIL_CLOSED"


def test_rejects_lineage_mismatch(tmp_path: Path) -> None:
    meta = _meta_evidence(tmp_path)
    decision = validate_meta_to_optimization_feedback_input_v1(
        MetaToOptimizationFeedbackInputRequestV1(
            meta_learning_evidence=meta,
            expected_meta_evidence_id="0" * 64,
        )
    )
    assert decision["overall_reason"] == "META_EVIDENCE_LINEAGE_MISMATCH"


def test_forbidden_search_execution_and_trading_selection() -> None:
    with pytest.raises(MetaToOptimizationFeedbackError):
        validate_meta_to_optimization_feedback_input_v1(
            MetaToOptimizationFeedbackInputRequestV1(
                meta_learning_evidence={},
                requested_search_execution=True,
            )
        )
    with pytest.raises(MetaToOptimizationFeedbackError):
        validate_meta_to_optimization_feedback_input_v1(
            MetaToOptimizationFeedbackInputRequestV1(
                meta_learning_evidence={},
                requested_trading_instrument_selection=True,
            )
        )


def test_forbidden_graph_disjoint() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden = {
        "src.experiments.canonical_advanced_search_v1.build_canonical_advanced_search_v1",
        "src.governance.promotion_loop.engine",
        "src.execution",
        "src.trading",
        "src.trading.master_v2",
        "src.learning.deterministic_decision_outcome_v0.learning_outcome_evidence_ingest_v1",
        "src.learning.deterministic_decision_outcome_v0.learning_state_record_v0",
    }
    assert "build_canonical_advanced_search_v1" not in source
    assert "ingest_evaluation_bundle_into_learning_state_v1" not in source
    assert "src.experiments.canonical_advanced_search_v1" in imported
