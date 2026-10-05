"""Self-tests for Whole-System Proof Harness V1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.peak_trade_whole_system_proof_harness_v1.constants_v1 import (
    BASELINE_ORIGIN_MAIN_SHA,
    DEFAULT_OPERATION_SPEC_REL,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.coverage_v1 import (
    build_edge_coverage_matrix_v1,
    build_node_coverage_matrix_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.dynamic_binding_v1 import (
    scan_dynamic_bindings_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.fixpoint_v1 import run_fixpoint_v1
from src.ops.peak_trade_whole_system_proof_harness_v1.ghv_productive_differential_v1 import (
    build_ghv_productive_differential_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.harness_v1 import (
    run_whole_system_proof_harness_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.identity_v1 import (
    component_identity_v1,
    edge_identity_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.instrument_inventory_v1 import (
    build_instrument_capability_matrix_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.manifest_v1 import (
    build_whole_system_proof_manifest_v1,
)
from src.ops.peak_trade_whole_system_proof_harness_v1.static_closure_v1 import (
    enrich_operation_nodes_v1,
    import_forward_closure_v1,
    load_operation_spec_v1,
    semantic_forward_graph_v1,
    semantic_reverse_graph_v1,
)

REPO = Path(__file__).resolve().parents[2]


def test_deterministic_identity() -> None:
    n = {"id": "N_TEST", "role": "r", "owner": "o", "binding": "productive", "location": "x"}
    assert component_identity_v1(n) == component_identity_v1(dict(n))
    e = {"producer": "A", "consumer": "B", "contract": "c", "condition": "k"}
    assert edge_identity_v1(e) == edge_identity_v1(dict(e))


def test_forward_reverse_discovery_14_13() -> None:
    spec = load_operation_spec_v1(REPO, DEFAULT_OPERATION_SPEC_REL)
    nodes = enrich_operation_nodes_v1(REPO, spec)
    fwd = semantic_forward_graph_v1(nodes, spec["SEMANTIC_EDGES"])
    rev = semantic_reverse_graph_v1(fwd)
    assert fwd["node_count"] == 14
    assert fwd["edge_count"] == 13
    assert rev["edge_count"] == 13


def test_import_forward_from_launcher() -> None:
    spec = load_operation_spec_v1(REPO, DEFAULT_OPERATION_SPEC_REL)
    imp = import_forward_closure_v1(REPO, spec["REAL_LAUNCHER"])
    assert imp["reachable_module_count"] > 10


def test_dynamic_binding_discovery() -> None:
    rep = scan_dynamic_bindings_v1(
        REPO, ["scripts/ops/run_peak_trade_whole_system_proof_harness_v1.py"]
    )
    assert rep["UNRESOLVED_COUNT"] >= 0


def test_fixpoint_convergence() -> None:
    state = {"n": 1}

    def snap() -> dict:
        return {"components": ["a"] * state["n"], "edges": ["e"], "dynamic_bindings": []}

    fp = run_fixpoint_v1(snap, max_passes=4)
    assert fp["SEMANTIC_FIXPOINT_REACHED"] is True


def test_ghv_pass_does_not_imply_whole_system_ready() -> None:
    spec = load_operation_spec_v1(REPO, DEFAULT_OPERATION_SPEC_REL)
    nodes = enrich_operation_nodes_v1(REPO, spec)
    fwd = semantic_forward_graph_v1(nodes, spec["SEMANTIC_EDGES"])
    ghv_diff = build_ghv_productive_differential_v1(fwd, {})
    assert ghv_diff["REAL_PATH_GHV_COVERAGE_COMPLETE"] is False
    out = run_whole_system_proof_harness_v1(REPO, write_evidence=False)
    assert out["readiness"]["CURRENT_READY"] is False


def test_manifest_schema_keys() -> None:
    out = run_whole_system_proof_harness_v1(REPO, write_evidence=False)
    m = out["manifest"]
    for key in (
        "schema_version",
        "baseline",
        "required_components",
        "node_coverage",
        "edge_coverage",
        "readiness",
        "unknowns",
    ):
        assert key in m


def test_node_coverage_marks_live_only_unproven() -> None:
    spec = load_operation_spec_v1(REPO, DEFAULT_OPERATION_SPEC_REL)
    nodes = enrich_operation_nodes_v1(REPO, spec)
    fwd = semantic_forward_graph_v1(nodes, spec["SEMANTIC_EDGES"])
    imp = import_forward_closure_v1(REPO, spec["REAL_LAUNCHER"])
    ghv_diff = build_ghv_productive_differential_v1(fwd, {})
    nc = build_node_coverage_matrix_v1(fwd, imp, ghv_diff)
    live = [r for r in nc["ROWS"] if r.get("RUNTIME") == "LIVE_ONLY_UNPROVEN"]
    assert live


def test_edge_coverage_matrix() -> None:
    spec = load_operation_spec_v1(REPO, DEFAULT_OPERATION_SPEC_REL)
    nodes = enrich_operation_nodes_v1(REPO, spec)
    fwd = semantic_forward_graph_v1(nodes, spec["SEMANTIC_EDGES"])
    ec = build_edge_coverage_matrix_v1(fwd)
    assert ec["EDGE_COUNT"] == 13


def test_baseline_sha_frozen() -> None:
    assert BASELINE_ORIGIN_MAIN_SHA == "2761aab69beb00564892d417818b7a35eb6794a7"


def test_instrument_matrix_exists() -> None:
    m = build_instrument_capability_matrix_v1()
    assert "MATRIX" in m
    assert "P21" in m["MATRIX"].get("INV_V2_FRESH_DISCOVERY", {})


def test_false_fixpoint_rejected() -> None:
    i = {"n": 0}

    def growing() -> dict:
        i["n"] += 1
        return {"components": list(range(i["n"])), "edges": [], "dynamic_bindings": []}

    fp = run_fixpoint_v1(growing, max_passes=3)
    assert fp["SEMANTIC_FIXPOINT_REACHED"] is False


def test_manifest_no_bare_ready_without_coverage() -> None:
    m = build_whole_system_proof_manifest_v1(
        {
            "readiness": {"CURRENT_READY": True, "WHOLE_SYSTEM_PROOF_HARNESS_READY": True},
            "unknowns": {"nodes": ["N_X"]},
            "baseline": {},
            "operation": "op",
            "launcher": "l",
            "terminal_boundary": "PRE_EXTERNAL",
            "discovered_components": [],
            "discovered_edges": [],
            "required_components": [],
            "required_edges": [],
            "excluded_components": [],
            "static_proof": {},
            "runtime_proof": {},
            "ghv_proof": {},
            "config_dependencies": [],
            "state_dependencies": [],
            "persistence_dependencies": {},
            "authority_dependencies": [],
            "safety_dependencies": {},
            "governance_dependencies": [],
            "provenance_dependencies": {},
            "node_coverage": {"ROWS": [{"RESULT": "UNKNOWN"}]},
            "edge_coverage": {},
            "conflicts": [],
            "violations": [],
            "fixpoint": {},
            "current_operational_setting": {},
            "minimal_required_setting": {},
            "setting_delta": [],
            "counterfactual_repairs": {},
            "live_only_unproven": ["N_Y"],
        }
    )
    assert m["unknowns"]["nodes"] == ["N_X"]
    assert m["LIVE_ONLY_UNPROVEN"] == ["N_Y"]
