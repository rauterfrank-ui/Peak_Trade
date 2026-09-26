"""Unified Blueprint D01/D02 topology adjudication tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.governance.unified_blueprint_d01_d02_topology_adjudication_v1 import (
    ADJUDICATION_CONFIG,
    WORKPACKAGE_ID,
    build_adjudication_summary_v1,
    prove_unified_blueprint_d01_d02_topology_adjudication_v1,
    validate_d01_census,
    validate_d02_edges,
    validate_authority_invariants,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _doc() -> dict:
    return json.loads((REPO_ROOT / ADJUDICATION_CONFIG).read_text(encoding="utf-8"))


def test_adjudication_proof_passes_on_current_repo() -> None:
    assert prove_unified_blueprint_d01_d02_topology_adjudication_v1(repo_root=REPO_ROOT)


def test_d01_census_and_d02_edges_validate() -> None:
    doc = _doc()
    assert doc["workpackage_id"] == WORKPACKAGE_ID
    assert not validate_d01_census(doc, REPO_ROOT)
    assert not validate_d02_edges(doc, REPO_ROOT)
    assert not validate_authority_invariants(doc)


def test_mi_to_learning_cannot_be_marked_implemented() -> None:
    doc = _doc()
    edges = {e["edge_id"]: e for e in doc["d02_inter_loop_edges"]}
    assert edges["d02_mi_to_learning"]["implementation_status"] == "NOT_IMPLEMENTED"
    assert edges["d02_mi_to_learning"]["missing_dependency"]


def test_phase_8_edge_not_complete_in_summary() -> None:
    summary = build_adjudication_summary_v1(repo_root=REPO_ROOT)
    assert "d02_mi_to_learning" in summary["MISSING_EDGES"]
    assert "Phase 8" in str(summary["first_unproven_dependency_after_closure"])


def test_cannot_represent_missing_edge_as_implemented() -> None:
    doc = _doc()
    mutated_edges = []
    for edge in doc["d02_inter_loop_edges"]:
        if edge["edge_id"] == "d02_mi_to_learning":
            mutated_edges.append(
                {
                    **edge,
                    "implementation_status": "IMPLEMENTED",
                    "missing_dependency": None,
                }
            )
        else:
            mutated_edges.append(edge)
    mutated = dict(doc)
    mutated["d02_inter_loop_edges"] = mutated_edges
    errors = validate_d02_edges(mutated, REPO_ROOT)
    assert any("d02_mi_to_learning must remain NOT_IMPLEMENTED" in e for e in errors)


def test_mi_to_optimization_intake_not_m4_execution() -> None:
    doc = _doc()
    edges = {e["edge_id"]: e for e in doc["d02_inter_loop_edges"]}
    mi_opt = edges["d02_mi_to_optimization"]
    assert mi_opt["implementation_status"] == "PARTIAL"
    assert "M4" in str(mi_opt.get("missing_dependency") or "")


@pytest.mark.parametrize(
    "edge_id,expected_status",
    [
        ("d02_loop_a_productive_learning_outcome", "IMPLEMENTED"),
        ("d02_learning_to_optimization", "IMPLEMENTED"),
        ("d02_optimization_to_meta_learning", "IMPLEMENTED"),
        ("d02_meta_to_optimization", "IMPLEMENTED"),
        ("d02_failure_memory", "IMPLEMENTED"),
    ],
)
def test_proven_edges_classified(edge_id: str, expected_status: str) -> None:
    doc = _doc()
    edges = {e["edge_id"]: e for e in doc["d02_inter_loop_edges"]}
    assert edges[edge_id]["implementation_status"] == expected_status
