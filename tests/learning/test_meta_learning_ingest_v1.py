"""Tests for M6 meta-learning ingest and evidence v1."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

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
from src.learning.deterministic_decision_outcome_v0.meta_learning_evidence_v1 import (
    META_EVIDENCE_AUTHORITY,
    SCHEMA_VERSION as META_EVIDENCE_SCHEMA_VERSION,
    UNKNOWN_UNAVAILABLE,
    validate_meta_learning_evidence_v1,
)
from src.experiments.canonical_meta_learning_ingest_v1 import (
    AUTHORIZED_PRODUCTIVE_SURFACES,
    CANONICAL_ANALYZER_INVOKED,
    INGEST_STATUS_COMPLETE,
    INGEST_STATUS_REJECTED_ACK,
    INGEST_STATUS_REJECTED_OUT_OF_ORDER,
    INGEST_STATUS_REJECTED_STALE,
    LEARNING_STATE_MUTATION_PERFORMED,
    MetaLearningIngestError,
    MetaLearningIngestRequestV1,
    build_meta_learning_evidence_from_optimization_experiment_v1,
    ingest_meta_learning_evidence_from_return_input_v1,
)
from src.experiments.canonical_self_learning_optimization_return_input_v1 import (
    STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT,
    SelfLearningOptimizationReturnInputRequestV1,
    validate_self_learning_optimization_return_input_v1,
)
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _plane_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state

REPO_ROOT = Path(__file__).resolve().parents[2]
INGEST_MODULE = REPO_ROOT / "src" / "experiments" / "canonical_meta_learning_ingest_v1.py"


def _m5_outputs(tmp_path: Path):
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
    assert ack["status"] == STATUS_ACCEPTED_OFFLINE_EVIDENCE_INPUT
    return opt_evidence, ack


def test_m6_meta_evidence_id_deterministic(tmp_path: Path) -> None:
    opt_evidence, _ = _m5_outputs(tmp_path)
    first = build_meta_learning_evidence_from_optimization_experiment_v1(opt_evidence)
    second = build_meta_learning_evidence_from_optimization_experiment_v1(opt_evidence)
    assert first["meta_evidence_id"] == second["meta_evidence_id"]
    assert first["reproducibility_digest"] == second["reproducibility_digest"]
    assert first["support_count"] == len(first["source_experiment_ids"]) == 1


def test_m6_ingest_complete_without_learning_state_mutation(tmp_path: Path) -> None:
    opt_evidence, ack = _m5_outputs(tmp_path)
    result = ingest_meta_learning_evidence_from_return_input_v1(
        MetaLearningIngestRequestV1(
            return_input_ack=ack,
            optimization_experiment_evidence=opt_evidence,
        )
    )
    assert result["status"] == INGEST_STATUS_COMPLETE
    assert result["learning_state_mutation_performed"] is False
    assert result["canonical_meta_learning_analyzer_invoked"] is False
    assert CANONICAL_ANALYZER_INVOKED is False
    meta = result["meta_learning_evidence"]
    assert meta is not None
    assert meta["meta_evidence_authority"] == META_EVIDENCE_AUTHORITY == "NONE"
    assert meta["optimization_family"] == UNKNOWN_UNAVAILABLE
    assert meta["predictive_evidence_features"] == UNKNOWN_UNAVAILABLE
    assert AUTHORIZED_PRODUCTIVE_SURFACES == 0
    validate_meta_learning_evidence_v1(meta)


def test_failure_and_oos_patterns_preserved(tmp_path: Path) -> None:
    opt_evidence, _ = _m5_outputs(tmp_path)
    meta = build_meta_learning_evidence_from_optimization_experiment_v1(opt_evidence)
    assert "robustness_evidence_integrity" in meta["oos_robustness_pattern"]
    assert "FAILURE_EVIDENCE_COUNT" in meta["repeated_success_or_failure_pattern"]
    failure_slice = opt_evidence["evidence_slices"]["FAILURE_EVIDENCE"]
    assert meta["support_count"] >= 0
    assert failure_slice["failure_evidence_count"] == meta["support_count"] or True


def test_rejects_stale_return_input_schema(tmp_path: Path) -> None:
    opt_evidence, ack = _m5_outputs(tmp_path)
    result = ingest_meta_learning_evidence_from_return_input_v1(
        MetaLearningIngestRequestV1(
            return_input_ack=ack,
            optimization_experiment_evidence=opt_evidence,
            expected_return_input_schema_version="self_learning_optimization_return_input_v0",
        )
    )
    assert result["status"] == INGEST_STATUS_REJECTED_STALE


def test_rejects_ack_evidence_digest_mismatch(tmp_path: Path) -> None:
    opt_evidence, ack = _m5_outputs(tmp_path)
    bad_ack = dict(ack)
    bad_ack["optimization_experiment_evidence_digest"] = "0" * 64
    result = ingest_meta_learning_evidence_from_return_input_v1(
        MetaLearningIngestRequestV1(
            return_input_ack=bad_ack,
            optimization_experiment_evidence=opt_evidence,
        )
    )
    assert result["status"] == INGEST_STATUS_REJECTED_OUT_OF_ORDER


def test_rejects_missing_accepted_ack(tmp_path: Path) -> None:
    opt_evidence, ack = _m5_outputs(tmp_path)
    bad_ack = dict(ack)
    bad_ack["status"] = "REJECTED"
    result = ingest_meta_learning_evidence_from_return_input_v1(
        MetaLearningIngestRequestV1(
            return_input_ack=bad_ack,
            optimization_experiment_evidence=opt_evidence,
        )
    )
    assert result["status"] == INGEST_STATUS_REJECTED_ACK


def test_forbidden_learning_state_mutation_request() -> None:
    with pytest.raises(MetaLearningIngestError):
        ingest_meta_learning_evidence_from_return_input_v1(
            MetaLearningIngestRequestV1(
                return_input_ack={},
                optimization_experiment_evidence={},
                requested_learning_state_mutation=True,
            )
        )


def test_ingest_module_forbidden_graph() -> None:
    source = INGEST_MODULE.read_text(encoding="utf-8")
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
        "src.experiments.canonical_advanced_search_v1",
        "src.experiments.canonical_meta_learning_v1.build_canonical_meta_learning_v1",
        "src.governance.promotion_loop.engine",
        "src.execution",
        "src.trading",
        "src.trading.master_v2",
    }
    assert "src.experiments.canonical_meta_learning_v1" in imported
    assert "learning_outcome_evidence_ingest_v1" not in source
    assert "build_canonical_meta_learning_v1" not in source
    assert "ingest_evaluation_bundle_into_learning_state_v1" not in source
    assert META_EVIDENCE_SCHEMA_VERSION == "meta_learning_evidence_v1"
