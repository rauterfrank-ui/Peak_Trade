"""Independent tests for frozen-graph symbol presence. No traversal."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ops.double_play_guardian_readonly_projection_v1.constants_v1 import (
    EXPECTED_BASELINE_SHA,
    FORBIDDEN_OUTPUT_KEYS,
)
from scripts.ops.double_play_guardian_readonly_projection_v1.symbol_presence_v1 import (
    CENSUS_NATIVE_ID,
    FROZEN_SNAPSHOT_ID,
    FUNCTION_SYMBOLS,
    load_frozen_graph_v1,
    project_frozen_graph_symbol_presence_v1,
)

PACKAGE = ROOT / "scripts/ops/double_play_guardian_readonly_projection_v1"
EVIDENCE = Path("/Users/frnkhrz/Peak_Trade_Run_Evidence/guardian_current_m15_97c8c954")
COMPOSED = EVIDENCE / "wp1/composed_forensic_graph.v1.json"
INTEGRATED = EVIDENCE / "wp2a/integrated_causal_graph.v1.json"


def _graph(
    *,
    native_ids: tuple[str, ...] = (),
    edges: tuple[tuple[str, str], ...] = (),
    snapshot_id: str = FROZEN_SNAPSHOT_ID,
    head: str = EXPECTED_BASELINE_SHA,
    authority: str = "NONE",
) -> dict:
    return {
        "snapshot_id": snapshot_id,
        "authority": authority,
        "code_snapshot": {"git_head": head},
        "nodes": [
            {
                "source_native_id": native_id,
                "provenance": {"NATIVE_ID": native_id},
            }
            for native_id in native_ids
        ],
        "edges": [
            {"source_native_id": source, "target_native_id": target} for source, target in edges
        ],
    }


def _project(composed: dict | None = None, integrated: dict | None = None, **kwargs: object):
    claims = kwargs.get("claims")
    return project_frozen_graph_symbol_presence_v1(
        composed_graph=composed,
        integrated_graph=integrated,
        claims=claims if isinstance(claims, dict) else None,
    )


def test_census_node_does_not_supply_trading_symbols() -> None:
    graph = _graph(
        native_ids=(CENSUS_NATIVE_ID, "SO-OPS-PKG:double_play_archive_sibling_exporter_v1"),
        edges=(
            (
                "SO-OPS-PKG:productive_decision_host_active_archive_three_family_binding_v1",
                "SO-OPS-PKG:double_play_archive_sibling_exporter_v1",
            ),
        ),
    )
    report = _project(graph, graph)
    assert report["PROJECTION_STATUS"] == "REPORTED"
    assert report["REJECTION_REASONS"] == []
    assert [row["PRESENCE"] for row in report["SYMBOLS"]] == ["UNKNOWN", "UNKNOWN"]
    assert [row["SYMBOL"] for row in report["SYMBOLS"]] == list(FUNCTION_SYMBOLS)
    assert report["INTERNAL_DYNAMIC_SCOPE_EDGE"] == "UNKNOWN"
    assert report["CENSUS_NODE_OBSERVED"] is True
    assert report["CENSUS_NODE_IS_TRADING_SYMBOL"] is False
    assert report["ABSENT_GRAPH_SYMBOL_IS_ISOLATION_PROOF"] is False
    assert report["TRAVERSAL_EXECUTED"] is False
    assert report["GRAPH_REBUILT"] is False
    assert report["GLOBAL_CAUSAL_CLOSURE_PROVEN"] is False
    assert report["DOMAIN_COVERAGE_STATUS"] == "NOT_PROVEN"
    assert report["AUTHORITY"] == "NONE"
    assert FORBIDDEN_OUTPUT_KEYS.isdisjoint(report)


def test_fixture_without_double_play_state_keeps_internal_edge_unknown() -> None:
    graph = _graph(native_ids=("transition_state",))
    report = _project(graph, graph)
    assert report["SYMBOLS"][0] == {"SYMBOL": "double_play_state", "PRESENCE": "UNKNOWN"}
    assert report["INTERNAL_DYNAMIC_SCOPE_EDGE"] == "UNKNOWN"
    assert report["CENSUS_NODE_IS_TRADING_SYMBOL"] is False


def test_exact_symbol_is_present_without_inferring_isolation() -> None:
    graph = _graph(
        native_ids=("double_play_state", "transition_state"),
        edges=(("double_play_state", "transition_state"),),
    )
    report = _project(graph, graph)
    assert report["SYMBOLS"][0]["PRESENCE"] == "PRESENT"
    assert report["SYMBOLS"][1]["PRESENCE"] == "UNKNOWN"
    assert report["INTERNAL_DYNAMIC_SCOPE_EDGE"] == "PRESENT"
    assert report["ABSENT_GRAPH_SYMBOL_IS_ISOLATION_PROOF"] is False


def test_symbol_without_edge_stays_unknown_for_the_internal_edge() -> None:
    graph = _graph(native_ids=("double_play_state", "transition_state"))
    report = _project(graph, graph)
    assert report["SYMBOLS"][0]["PRESENCE"] == "PRESENT"
    assert report["INTERNAL_DYNAMIC_SCOPE_EDGE"] == "UNKNOWN"


def test_repeated_output_is_identical() -> None:
    graph = _graph(native_ids=(CENSUS_NATIVE_ID,))
    assert _project(graph, graph) == _project(graph, graph)


@pytest.mark.parametrize(
    ("claims", "reason"),
    [
        (
            {"treat_ops_census_node_as_trading_symbol": True},
            "OPS_CENSUS_NODE_TREATED_AS_TRADING_SYMBOL",
        ),
        (
            {"treat_missing_graph_symbol_as_isolation": True},
            "MISSING_GRAPH_SYMBOL_TREATED_AS_ISOLATION_PROOF",
        ),
    ],
)
def test_fail_closed_claims(claims: dict, reason: str) -> None:
    graph = _graph(native_ids=(CENSUS_NATIVE_ID,))
    report = _project(graph, graph, claims=claims)
    assert report["PROJECTION_STATUS"] == "REJECTED"
    assert reason in report["REJECTION_REASONS"]
    assert report["CENSUS_NODE_IS_TRADING_SYMBOL"] is False
    assert report["ABSENT_GRAPH_SYMBOL_IS_ISOLATION_PROOF"] is False


def test_snapshot_or_authority_mismatch_rejects() -> None:
    bad_snapshot = _graph(snapshot_id="0" * 32)
    bad_head = _graph(head="0" * 40)
    bad_authority = _graph(authority="LIVE")
    for graph, reason in (
        (bad_snapshot, "SNAPSHOT_ID_MISMATCH"),
        (bad_head, "BASELINE_SHA_MISMATCH"),
        (bad_authority, "UNAUTHORIZED_AUTHORITY_CLAIM"),
    ):
        report = _project(graph, graph)
        assert report["PROJECTION_STATUS"] == "REJECTED"
        assert reason in report["REJECTION_REASONS"]
        assert report["INTERNAL_DYNAMIC_SCOPE_EDGE"] == "UNKNOWN"


def test_graph_disagreement_rejects() -> None:
    left = _graph(native_ids=("double_play_state",))
    right = _graph(native_ids=())
    report = _project(left, right)
    assert report["PROJECTION_STATUS"] == "REJECTED"
    assert "GRAPH_PRESENCE_CONFLICT" in report["REJECTION_REASONS"]
    assert report["SYMBOLS"][0]["PRESENCE"] == "UNKNOWN"


def test_missing_graph_rejects() -> None:
    report = _project(None, None)
    assert report["PROJECTION_STATUS"] == "REJECTED"
    assert "MISSING_REQUIRED_EVIDENCE" in report["REJECTION_REASONS"]
    assert report["TRAVERSAL_EXECUTED"] is False


def test_reader_does_not_import_traversal_or_protected_runtimes() -> None:
    source = (PACKAGE / "symbol_presence_v1.py").read_text(encoding="utf-8")
    assert "traverse_forensic_graph_v1" not in source
    assert "write_text" not in source
    parsed = ast.parse(source)
    banned = ("trading", "execution", "risk", "scripts.ops.ghv_forensic_whole_system")
    for node in ast.walk(parsed):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert not name.startswith(banned)


@pytest.mark.skipif(
    not COMPOSED.is_file() or not INTEGRATED.is_file(),
    reason="local frozen graphs are absent",
)
def test_frozen_artifact_58f855c9_has_no_trading_function_symbols() -> None:
    composed = load_frozen_graph_v1(COMPOSED)
    integrated = load_frozen_graph_v1(INTEGRATED)
    report = project_frozen_graph_symbol_presence_v1(
        composed_graph=composed,
        integrated_graph=integrated,
    )
    assert report["PROJECTION_STATUS"] == "REPORTED"
    assert report["SNAPSHOT_ID"] == FROZEN_SNAPSHOT_ID
    assert [row["PRESENCE"] for row in report["SYMBOLS"]] == ["UNKNOWN", "UNKNOWN"]
    assert report["INTERNAL_DYNAMIC_SCOPE_EDGE"] == "UNKNOWN"
    assert report["CENSUS_NODE_OBSERVED"] is True
    assert report["CENSUS_NODE_IS_TRADING_SYMBOL"] is False
    assert report["ABSENT_GRAPH_SYMBOL_IS_ISOLATION_PROOF"] is False
    assert report["TRAVERSAL_EXECUTED"] is False
    assert report["GRAPH_REBUILT"] is False
    assert report["GLOBAL_CAUSAL_CLOSURE_PROVEN"] is False
