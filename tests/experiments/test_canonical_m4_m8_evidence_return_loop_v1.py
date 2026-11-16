"""Tests for canonical M4–M8 single-cycle evidence return loop orchestrator."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Mapping

import pytest

from src.experiments.canonical_deterministic_multi_cycle_offline_replay_v1 import (
    OfflineMultiCycleReplayError,
)
from src.experiments.canonical_m4_m8_evidence_return_loop_v1 import (
    LOOP_STATUS_COMPLETE,
    M4M8EvidenceReturnLoopError,
    M4M8EvidenceReturnLoopRequestV1,
    P5_PRODUCER_BRIDGE_PERFORMED,
    SEARCH_EXECUTED,
    run_m4_m8_evidence_return_loop_v1,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import CLASS_ECONOMIC_EVIDENCE
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _plane_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_m4_m8_evidence_return_loop_v1.py"


def assert_original_g2_evidence_reaches_offline_feedback(evidence: Mapping[str, Any]) -> None:
    """Exercise the bounded experiment fixture with the verified G2 input unchanged."""
    loop = run_m4_m8_evidence_return_loop_v1(
        M4M8EvidenceReturnLoopRequestV1(
            learning_evidence=evidence,
            plane_request=_plane_request(evidence, created_at=evidence["observed_at_utc"]),
            replay_seed=19,
        )
    )
    assert loop["status"] == LOOP_STATUS_COMPLETE
    assert loop["search_executed"] is False
    assert loop["p5_producer_bridge_performed"] is False
    cycle = loop["cycle"]
    digest = evidence["content_hash"]
    assert cycle["cycle_body"]["learning_evidence_digest"] == digest
    plane = cycle["experiment_plane_result"]
    assert plane["learning_input_validation"]["learning_evidence_digest"] == digest
    optimization = cycle["optimization_experiment_evidence"]
    economic = optimization["evidence_slices"][CLASS_ECONOMIC_EVIDENCE]
    assert economic["source_learning_evidence_digest"] == digest
    assert economic["numeric_calibration_authority"] == "NONE"
    meta = cycle["meta_learning_evidence"]
    assert meta["source_optimization_experiment_evidence_digest"] == optimization["content_hash"]
    assert meta["meta_evidence_authority"] == "NONE"
    assert cycle["bounded_research_feedback_decision"]["feedback_decision_identity"]


def test_single_cycle_loop_deterministic_and_closed(tmp_path: Path) -> None:
    state = _learning_state(tmp_path)
    evidence = export_learning_evidence_from_state_v1(state)
    plane = _plane_request(evidence)
    request = M4M8EvidenceReturnLoopRequestV1(
        learning_evidence=evidence,
        plane_request=plane,
        replay_seed=7,
    )
    first = run_m4_m8_evidence_return_loop_v1(request)
    second = run_m4_m8_evidence_return_loop_v1(request)
    assert first["status"] == LOOP_STATUS_COMPLETE
    assert first["forward_return_loop_closed"] is True
    assert first["loop_identity"] == second["loop_identity"]
    assert first["result_digest"] == second["result_digest"]
    assert first["search_executed"] is False
    assert SEARCH_EXECUTED is False
    assert first["p5_producer_bridge_performed"] is False
    assert P5_PRODUCER_BRIDGE_PERFORMED is False
    cycle = first["cycle"]
    assert cycle["meta_learning_evidence"]["meta_evidence_authority"] == "NONE"
    assert first["trading_selection_effect"] == "NONE"


def test_forbidden_p5_bridge_request(tmp_path: Path) -> None:
    state = _learning_state(tmp_path)
    evidence = export_learning_evidence_from_state_v1(state)
    plane = _plane_request(evidence)
    with pytest.raises(M4M8EvidenceReturnLoopError):
        run_m4_m8_evidence_return_loop_v1(
            M4M8EvidenceReturnLoopRequestV1(
                learning_evidence=evidence,
                plane_request=plane,
                requested_p5_producer_bridge=True,
            )
        )


def test_experiment_cannot_use_a_different_learning_evidence_record(tmp_path: Path) -> None:
    state = _learning_state(tmp_path)
    evidence = export_learning_evidence_from_state_v1(state)
    other = export_learning_evidence_from_state_v1(state, event_time_utc="2026-09-01T16:00:00Z")
    assert evidence["content_hash"] != other["content_hash"]

    with pytest.raises(
        OfflineMultiCycleReplayError, match="M4_LEARNING_EVIDENCE_DIGEST_LINEAGE_MISMATCH"
    ):
        run_m4_m8_evidence_return_loop_v1(
            M4M8EvidenceReturnLoopRequestV1(
                learning_evidence=evidence, plane_request=_plane_request(other), replay_seed=7
            )
        )


def test_invalid_cycle_learning_input_cannot_borrow_a_valid_experiment(tmp_path: Path) -> None:
    evidence = export_learning_evidence_from_state_v1(_learning_state(tmp_path))
    with pytest.raises(OfflineMultiCycleReplayError, match="CYCLE_LEARNING_INPUT_REJECTED"):
        run_m4_m8_evidence_return_loop_v1(
            M4M8EvidenceReturnLoopRequestV1(
                learning_evidence={"content_hash": evidence["content_hash"]},
                plane_request=_plane_request(evidence),
                replay_seed=7,
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
        "src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1",
        "src.execution",
        "src.trading",
        "src.governance.promotion_loop.engine",
    }
    assert forbidden.isdisjoint(imported)
