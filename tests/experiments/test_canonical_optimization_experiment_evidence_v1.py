"""Tests for optimization experiment evidence v1 and M5 return chain."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    CLASS_FAILURE_EVIDENCE,
    CLASS_SEARCH_EVIDENCE,
    REQUIRED_EVIDENCE_CLASSES,
    SCHEMA_VERSION as EVIDENCE_SCHEMA_VERSION,
    build_optimization_experiment_evidence_from_plane_v1,
)
from src.experiments.canonical_optimization_universe_experiment_plane_v1 import (
    PLANE_STATUS_COMPLETE,
    run_optimization_universe_experiment_plane_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from src.experiments.canonical_self_learning_optimization_return_input_v1 import (
    AUTHORIZED_PRODUCTIVE_SURFACES,
    LEARNING_STATE_MUTATION_PERFORMED,
    META_LEARNING_INGEST_PERFORMED,
    STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT,
    STATUS_REJECTED_MALFORMED,
    STATUS_REJECTED_OUT_OF_ORDER,
    STATUS_REJECTED_STALE_CONTRACT,
    SelfLearningOptimizationReturnInputError,
    SelfLearningOptimizationReturnInputRequestV1,
    validate_self_learning_optimization_return_input_v1,
)
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _plane_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state

REPO_ROOT = Path(__file__).resolve().parents[2]
RETURN_MODULE = (
    REPO_ROOT / "src" / "experiments" / "canonical_self_learning_optimization_return_input_v1.py"
)


def _complete_plane(tmp_path: Path):
    state = _learning_state(tmp_path)
    evidence = export_learning_evidence_from_state_v1(state)
    return run_optimization_universe_experiment_plane_v1(_plane_request(evidence))


def test_evidence_identity_and_slices_deterministic(tmp_path: Path) -> None:
    plane = _complete_plane(tmp_path)
    assert plane["status"] == PLANE_STATUS_COMPLETE
    first = build_optimization_experiment_evidence_from_plane_v1(plane)
    second = build_optimization_experiment_evidence_from_plane_v1(plane)
    assert first["record_id"] == second["record_id"]
    assert first["content_hash"] == second["content_hash"]
    assert first["reproducibility_digest"] == second["reproducibility_digest"]
    assert frozenset(first["evidence_slices"].keys()) == REQUIRED_EVIDENCE_CLASSES
    assert (
        first["evidence_slices"][CLASS_SEARCH_EVIDENCE]["search_identity"]
        == plane["chain"]["search_identity"]
    )


def test_m5_return_ack_without_learning_state_mutation(tmp_path: Path) -> None:
    plane = _complete_plane(tmp_path)
    opt_evidence = build_optimization_experiment_evidence_from_plane_v1(plane)
    ack = validate_self_learning_optimization_return_input_v1(
        SelfLearningOptimizationReturnInputRequestV1(
            optimization_experiment_evidence=opt_evidence,
            expected_plane_identity=str(plane["plane_identity"]),
        )
    )
    assert ack["status"] == STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT
    assert ack["learning_state_mutation_performed"] is False
    assert ack["meta_learning_ingest_performed"] is False
    assert LEARNING_STATE_MUTATION_PERFORMED is False
    assert META_LEARNING_INGEST_PERFORMED is False
    assert AUTHORIZED_PRODUCTIVE_SURFACES == 0


def test_failure_evidence_preserved(tmp_path: Path) -> None:
    plane = _complete_plane(tmp_path)
    opt_evidence = build_optimization_experiment_evidence_from_plane_v1(plane)
    failure_slice = opt_evidence["evidence_slices"][CLASS_FAILURE_EVIDENCE]
    assert failure_slice["failure_evidence_count"] == plane["chain"]["failure_evidence_count"]


def test_rejects_stale_evidence_schema_version(tmp_path: Path) -> None:
    plane = _complete_plane(tmp_path)
    opt_evidence = build_optimization_experiment_evidence_from_plane_v1(plane)
    ack = validate_self_learning_optimization_return_input_v1(
        SelfLearningOptimizationReturnInputRequestV1(
            optimization_experiment_evidence=opt_evidence,
            expected_evidence_schema_version="canonical_optimization_experiment_evidence_v0",
        )
    )
    assert ack["status"] == STATUS_REJECTED_STALE_CONTRACT


def test_rejects_out_of_order_plane_identity(tmp_path: Path) -> None:
    plane = _complete_plane(tmp_path)
    opt_evidence = build_optimization_experiment_evidence_from_plane_v1(plane)
    ack = validate_self_learning_optimization_return_input_v1(
        SelfLearningOptimizationReturnInputRequestV1(
            optimization_experiment_evidence=opt_evidence,
            expected_plane_identity="0" * 64,
        )
    )
    assert ack["status"] == STATUS_REJECTED_OUT_OF_ORDER


def test_rejects_malformed_evidence() -> None:
    ack = validate_self_learning_optimization_return_input_v1(
        SelfLearningOptimizationReturnInputRequestV1(
            optimization_experiment_evidence={"schema_version": EVIDENCE_SCHEMA_VERSION}
        )
    )
    assert ack["status"] == STATUS_REJECTED_MALFORMED


def test_forbidden_learning_state_mutation_request() -> None:
    with pytest.raises(SelfLearningOptimizationReturnInputError):
        validate_self_learning_optimization_return_input_v1(
            SelfLearningOptimizationReturnInputRequestV1(
                optimization_experiment_evidence={},
                requested_learning_state_mutation=True,
            )
        )


def test_return_boundary_does_not_import_learning_state_ingest() -> None:
    source = RETURN_MODULE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden = {
        "src.learning.deterministic_decision_outcome_v0.learning_outcome_evidence_ingest_v1",
        "src.learning.deterministic_decision_outcome_v0.learning_state_record_v0",
        "src.experiments.canonical_meta_learning_v1",
        "src.experiments.canonical_advanced_search_v1",
        "src.governance.promotion_loop.engine",
        "src.execution",
        "src.trading",
        "src.trading.master_v2",
    }
    assert forbidden.isdisjoint(imported)
    assert "ingest_evaluation_bundle_into_learning_state_v1" not in source
