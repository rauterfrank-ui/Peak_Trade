"""Independent tests for the Double Play causal-graph binding verifier."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ops.double_play_guardian_binding_verifier_v1.graph_track_v1 import (
    EXPECTED_BASELINE_SHA,
    EXPECTED_BASELINE_TREE,
    FROZEN_SNAPSHOT_ID,
    FUNCTION_SYMBOLS,
    SOURCE_FILES,
    verify_double_play_graph_v1,
)

MODULE = ROOT / "scripts/ops/double_play_guardian_binding_verifier_v1/graph_track_v1.py"
EVIDENCE = Path("/Users/frnkhrz/Peak_Trade_Run_Evidence/guardian_current_m15_97c8c954")


def _graph(*native_ids: str) -> dict:
    return {
        "snapshot_id": FROZEN_SNAPSHOT_ID,
        "authority": "NONE",
        "code_snapshot": {"git_head": EXPECTED_BASELINE_SHA},
        "nodes": [
            {"source_native_id": native_id, "provenance": {"NATIVE_ID": native_id}}
            for native_id in native_ids
        ],
        "edges": [],
    }


def _sources() -> dict[str, str]:
    return {
        "cycle": (
            "def run_current_productive_master_v2_runtime_cycle_v1():\n"
            "    if ddo_binding is not None:\n"
            "        return None\n"
            "    else:\n"
            "        run_integrated_offline_trading_logic_replay_v1()\n"
        ),
        "replay": (
            "def run_integrated_offline_trading_logic_replay_v1():\n"
            "    if delegated_ctx is not None:\n"
            "        return None\n"
            "    else:\n"
            "        transition_state()\n"
            "        update_dynamic_boundaries()\n"
            "    evaluate_double_play_entry_exit_policy_v0()\n"
        ),
        "double_play_state": (
            "class RuntimeScopeState:\n"
            "    pass\n"
            "def transition_state():\n"
            "    return None\n"
            "def update_dynamic_boundaries():\n"
            "    return None\n"
        ),
        "entry_exit_policy": (
            "def evaluate_double_play_entry_exit_policy_v0():\n    return None\n"
        ),
        "host_binding": (
            "def commit_host_dynamic_scope_after_replay_v1():\n"
            "    if persist and binding.state_root:\n"
            "        persist_dynamic_scope_state_atomic_v1()\n"
        ),
        "persistence": ("def persist_dynamic_scope_state_atomic_v1():\n    return None\n"),
        "bridge": (
            "def run_bridge_cycle_v1():\n"
            "    commit_host_dynamic_scope_after_replay_v1(\n"
            "        persist=persist_dynamic_scope and state.dynamic_scope_state_root\n"
            "    )\n"
        ),
    }


def _verify(sources: dict[str, str] | None = None, **kwargs: object):
    claims = kwargs.get("claims")
    composed = kwargs.get("composed", _graph("SO-OPS-PKG:double_play"))
    integrated = kwargs.get("integrated", _graph("SO-OPS-PKG:double_play"))
    return verify_double_play_graph_v1(
        current_sha=str(kwargs.get("current_sha", EXPECTED_BASELINE_SHA)),
        current_tree=str(kwargs.get("current_tree", EXPECTED_BASELINE_TREE)),
        sources=sources if sources is not None else _sources(),
        composed_graph=composed if isinstance(composed, dict) else None,
        integrated_graph=integrated if isinstance(integrated, dict) else None,
        claims=claims if isinstance(claims, dict) else None,
    )


def _pairs(report: dict) -> set[tuple[str, str]]:
    return {(row["SOURCE"], row["TARGET"]) for row in report["VERIFIED_EDGES"]}


def test_fixture_edges_keep_conditions_and_unknown_snapshot_symbols() -> None:
    report = _verify()
    assert report["VERIFICATION_STATUS"] == "REPORTED"
    assert report["GRAPH_READY"] is False
    assert report["LOGICAL_EDGE_COUNT"] == 6
    assert report["MISSING_EDGES"] == []
    assert report["CONFIRMED_SYMBOLS"] == list(FUNCTION_SYMBOLS)
    assert _pairs(report) == {
        (
            "run_current_productive_master_v2_runtime_cycle_v1",
            "run_integrated_offline_trading_logic_replay_v1",
        ),
        ("run_integrated_offline_trading_logic_replay_v1", "update_dynamic_boundaries"),
        ("run_integrated_offline_trading_logic_replay_v1", "transition_state"),
        (
            "run_integrated_offline_trading_logic_replay_v1",
            "evaluate_double_play_entry_exit_policy_v0",
        ),
        (
            "commit_host_dynamic_scope_after_replay_v1",
            "persist_dynamic_scope_state_atomic_v1",
        ),
        ("run_bridge_cycle_v1", "commit_host_dynamic_scope_after_replay_v1"),
    }
    by_target = {row["TARGET"]: row for row in report["VERIFIED_EDGES"]}
    assert by_target["transition_state"]["CONDITION"] == "delegated_ctx is None"
    assert by_target["transition_state"]["EDGE_TYPE"] == "CALLS"
    assert by_target["transition_state"]["EVIDENCE_CLASS"] == "CURRENT_CODE"
    assert by_target["transition_state"]["REACHABILITY"] == "NOT_ASSESSED"
    persist = by_target["persist_dynamic_scope_state_atomic_v1"]
    assert persist["CONDITION"] == "persist and binding.state_root"
    assert persist["PRODUCTIVE_PERSISTENCE"] == "CONDITIONAL"
    commit = by_target["commit_host_dynamic_scope_after_replay_v1"]
    assert commit["CONDITION"] == "DIRECT"
    assert commit["PRODUCTIVE_PERSISTENCE"] == "CONDITIONAL"
    assert all(row["PRESENCE"] == "UNKNOWN" for row in report["FROZEN_GRAPH_SYMBOLS"])
    assert report["CENSUS_NODE_IS_TRADING_SYMBOL"] is False
    assert report["ABSENT_GRAPH_SYMBOL_IS_ISOLATION_PROOF"] is False
    assert report["TRAVERSAL_EXECUTED"] is False
    assert report["GRAPH_REBUILT"] is False


def test_current_sources_verify_six_edges_without_graph_membership() -> None:
    sources = {
        role: (ROOT / path).read_text(encoding="utf-8") for role, path in SOURCE_FILES.items()
    }
    composed = json.loads((EVIDENCE / "wp1/composed_forensic_graph.v1.json").read_text())
    integrated = json.loads((EVIDENCE / "wp2a/integrated_causal_graph.v1.json").read_text())
    report = _verify(sources, composed=composed, integrated=integrated)
    assert report["VERIFICATION_STATUS"] == "REPORTED"
    assert report["LOGICAL_EDGE_COUNT"] == 6
    assert len(report["VERIFIED_EDGES"]) == 7
    assert report["GRAPH_READY"] is False
    updates = [
        row for row in report["VERIFIED_EDGES"] if row["TARGET"] == "update_dynamic_boundaries"
    ]
    assert [row["LINE"] for row in updates] == [1725, 1936]
    assert {row["CONDITION"] for row in updates} == {"delegated_ctx is None"}
    transition = next(
        row for row in report["VERIFIED_EDGES"] if row["TARGET"] == "transition_state"
    )
    assert transition["LINE"] == 1928
    assert transition["CONDITION"] == "delegated_ctx is None"
    replay = next(
        row
        for row in report["VERIFIED_EDGES"]
        if row["TARGET"] == "run_integrated_offline_trading_logic_replay_v1"
    )
    assert replay["CONDITION"] == "ddo_binding is None"
    assert replay["REACHABILITY"] == "NOT_ASSESSED"
    assert all(row["PRESENCE"] == "UNKNOWN" for row in report["FROZEN_GRAPH_SYMBOLS"])
    assert report["CENSUS_NODE_OBSERVED"] is True
    assert report["CENSUS_NODE_IS_TRADING_SYMBOL"] is False


def test_missing_call_rejects() -> None:
    sources = _sources()
    sources["replay"] = sources["replay"].replace(
        "        transition_state()\n",
        "",
    )
    report = _verify(sources)
    assert report["VERIFICATION_STATUS"] == "REJECTED"
    assert "MISSING_CALL" in report["REJECTION_REASONS"]
    assert report["MISSING_EDGES"] == [
        {
            "SOURCE": "run_integrated_offline_trading_logic_replay_v1",
            "TARGET": "transition_state",
            "VERIFICATION_STATUS": "MISSING",
        }
    ]
    assert report["GRAPH_READY"] is False


def test_changed_target_is_not_emitted() -> None:
    sources = _sources()
    sources["replay"] = sources["replay"].replace("transition_state()", "transition_state_other()")
    report = _verify(sources)
    assert "MISSING_CALL" in report["REJECTION_REASONS"]
    assert all(row["TARGET"] != "transition_state_other" for row in report["VERIFIED_EDGES"])


def test_census_substitution_and_persists_claim_reject() -> None:
    census = _verify(claims={"treat_ops_census_node_as_trading_symbol": True})
    persists = _verify(claims={"persists_edge_requested": True})
    isolation = _verify(claims={"treat_missing_graph_symbol_as_isolation": True})
    assert "OPS_CENSUS_NODE_TREATED_AS_TRADING_SYMBOL" in census["REJECTION_REASONS"]
    assert census["CENSUS_NODE_IS_TRADING_SYMBOL"] is False
    assert "UNSUPPORTED_PERSISTS_CLAIM" in persists["REJECTION_REASONS"]
    assert all(row["EDGE_TYPE"] == "CALLS" for row in persists["VERIFIED_EDGES"])
    assert isolation["ABSENT_GRAPH_SYMBOL_IS_ISOLATION_PROOF"] is False
    assert "MISSING_GRAPH_SYMBOL_TREATED_AS_ISOLATION_PROOF" in isolation["REJECTION_REASONS"]


def test_malformed_ast_rejects_without_edges() -> None:
    sources = _sources()
    sources["cycle"] = "def ("
    report = _verify(sources)
    assert report["VERIFICATION_STATUS"] == "REJECTED"
    assert "MALFORMED_AST" in report["REJECTION_REASONS"]
    assert report["VERIFIED_EDGES"] == []
    assert report["TRAVERSAL_EXECUTED"] is False


def test_track_does_not_import_traversal() -> None:
    text = MODULE.read_text(encoding="utf-8")
    assert "traverse_forensic_graph_v1" not in text
    assert "write_text" not in text
    parsed = ast.parse(text)
    for node in ast.walk(parsed):
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("trading")
            assert not (node.module or "").startswith("execution")
