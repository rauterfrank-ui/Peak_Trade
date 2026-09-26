"""Tests for canonical M4–M8 single-cycle evidence return loop orchestrator."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from src.experiments.canonical_m4_m8_evidence_return_loop_v1 import (
    LOOP_STATUS_COMPLETE,
    M4M8EvidenceReturnLoopError,
    M4M8EvidenceReturnLoopRequestV1,
    P5_PRODUCER_BRIDGE_PERFORMED,
    SEARCH_EXECUTED,
    run_m4_m8_evidence_return_loop_v1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    export_learning_evidence_from_state_v1,
)
from tests.experiments.test_canonical_optimization_universe_experiment_plane_v1 import (
    _plane_request,
)
from tests.learning.test_learning_evidence_export_v1 import _learning_state

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "src" / "experiments" / "canonical_m4_m8_evidence_return_loop_v1.py"


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
