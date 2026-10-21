"""Scoped GHV adapter tests. Fixtures use the pinned mainline and legacy pins."""

from __future__ import annotations

from typing import Any

from scripts.ops.pin_scope_binding_v1.constants_v1 import (
    STATUS_ACCEPTED,
    STATUS_FORGED_PROVENANCE,
    STATUS_PIN_MISMATCH,
    STATUS_SCOPE_EMPTY,
)
from scripts.ops.scoped_ghv_crosswalk_adapter_v1.adapt_v1 import run_scoped_ghv_v1
from tests.ops.guardian_framework_fixtures_v1 import (
    AUTHORIZED_COMMIT,
    AUTHORIZED_TREE,
    CENSUS_EMBEDDED_PIN,
    GRAPH_LEGACY_PIN,
    LANDSCAPE_EMBEDDED_COMMIT,
    LANDSCAPE_EMBEDDED_TREE,
    chain_scope,
    honest_provenance,
    scope_of,
)

CURRENT_COMMIT = AUTHORIZED_COMMIT
CURRENT_TREE = AUTHORIZED_TREE
CENSUS_LEGACY_PIN = CENSUS_EMBEDDED_PIN
LANDSCAPE_LEGACY_COMMIT = LANDSCAPE_EMBEDDED_COMMIT
LANDSCAPE_LEGACY_TREE = LANDSCAPE_EMBEDDED_TREE


def _provenance(**overrides: str) -> dict[str, dict[str, str]]:
    return honest_provenance(**overrides)


def _node(native_id: str, *, epistemic: str = "PROVEN_CURRENT") -> dict[str, str]:
    return {
        "object_id": native_id,
        "epistemic_status": epistemic,
        "current_status": "PROVEN_CURRENT",
        "primary_class": "OBSERVATION",
    }


def _edge(edge_id: str, source: str, target: str) -> dict[str, Any]:
    return {
        "edge_id": edge_id,
        "source_native_id": source,
        "target_native_id": target,
        "epistemic_status": "PROVEN_CURRENT",
        "causal_traversal_eligible": True,
        "flow_type": "OBSERVATION_FLOW",
    }


def _chain() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = [_node(name) for name in ("node-a", "node-b", "node-c", "node-d")]
    edges = [
        _edge("e-ab", "node-a", "node-b"),
        _edge("e-bc", "node-b", "node-c"),
        _edge("e-cd", "node-c", "node-d"),
    ]
    return nodes, edges


def _run(**overrides: Any) -> dict[str, Any]:
    nodes, edges = _chain()
    payload: dict[str, Any] = {
        "authoritative_commit_sha": CURRENT_COMMIT,
        "authoritative_tree_sha": CURRENT_TREE,
        "declared_commit_sha": CURRENT_COMMIT,
        "declared_tree_sha": CURRENT_TREE,
        "provenance": _provenance(),
        "scope": chain_scope(),
        "candidate_nodes": nodes,
        "candidate_edges": edges,
        "origin_native_id": "node-a",
        "reverse_origin_native_id": "node-d",
        "max_depth": 2,
    }
    payload.update(overrides)
    return run_scoped_ghv_v1(**payload)


def test_valid_fixture_traverses_without_coverage_pass() -> None:
    result = _run()

    assert result["status"] == STATUS_ACCEPTED
    assert result["composition_invoked"] is True
    assert result["graph_materialized"] is False
    assert result["coverage_proof"] is False
    assert result["authority"] == "NONE"
    assert result["guardian_identity"] is False
    assert "overall_pass" not in result
    assert "coverage_pass" not in result
    assert result["forward"]["reachable"] == ["node-b"]
    assert result["reverse"]["reachable"] == ["node-c"]
    assert result["transitive"]["reachable"] == ["node-b", "node-c"]
    assert "node-d" not in result["transitive"]["reachable"]
    assert result["impact"]["impacted_native_ids"] == ["node-a", "node-b", "node-c"]
    assert result["evaluated_edges"] == []
    assert result["edge_contract_rejections"] == [
        {"edge_id": "e-ab", "reason": "missing_typed_edge"},
        {"edge_id": "e-bc", "reason": "missing_typed_edge"},
        {"edge_id": "e-cd", "reason": "missing_typed_edge"},
    ]
    assert result["coverage_gap"] is True
    assert result["result_pin"] == CURRENT_COMMIT
    assert result["result_tree"] == CURRENT_TREE
    assert result["scope_identity"] == chain_scope()
    assert result["checked_provenance"]["census"]["pin"] == CENSUS_LEGACY_PIN
    assert result["checked_provenance"]["landscape"]["tree_pin"] == LANDSCAPE_LEGACY_TREE
    assert result["coverage_gaps"]["coverage_gap"] is result["coverage_gap"]
    assert [edge["edge_id"] for edge in result["candidate_edges"]] == [
        "e-ab",
        "e-bc",
        "e-cd",
    ]
    assert "typed_edge" not in result["candidate_edges"][0]
    assert result["candidate_edges"][0]["flow_type"] == "OBSERVATION_FLOW"


def _produces(**overrides: Any) -> dict[str, Any]:
    typed = {
        "edge_type": "PRODUCES",
        "structural_only": False,
        "causal_propagation_allowed": True,
        "trading_authority_implied": False,
    }
    typed.update(overrides)
    return typed


def test_typed_current_edge_stays_integration_ready() -> None:
    nodes, edges = _chain()
    edges = [
        _edge(edge["edge_id"], edge["source_native_id"], edge["target_native_id"]) for edge in edges
    ]
    for edge in edges:
        edge["typed_edge"] = _produces()
    result = _run(candidate_nodes=nodes, candidate_edges=edges)

    assert result["evaluated_edges"] == ["e-ab", "e-bc", "e-cd"]
    assert result["edge_contract_rejections"] == []
    assert result["forward"]["reachable"] == ["node-b"]
    assert result["reverse"]["reachable"] == ["node-c"]
    assert result["transitive"]["reachable"] == ["node-b", "node-c"]
    assert result["authority"] == "NONE"
    assert result["coverage_proof"] is False


def test_unknown_typed_edge_is_not_integration_ready() -> None:
    nodes, edges = _chain()
    edges[0]["typed_edge"] = _produces(edge_type="NOT_A_CURRENT_EDGE")
    edges[1]["typed_edge"] = _produces()
    edges[2]["typed_edge"] = _produces()
    result = _run(candidate_nodes=nodes, candidate_edges=edges)

    assert result["evaluated_edges"] == ["e-bc", "e-cd"]
    assert result["edge_contract_rejections"] == [
        {"edge_id": "e-ab", "reason": "unknown_edge_type"}
    ]
    assert "e-ab" not in result["evaluated_edges"]
    assert result["candidate_edges"][0]["typed_edge"]["edge_type"] == "NOT_A_CURRENT_EDGE"
    assert result["coverage_gap"] is True
    assert result["coverage_proof"] is False


def test_contradictory_edge_attributes_are_rejected() -> None:
    nodes, edges = _chain()
    for edge in edges:
        edge["typed_edge"] = _produces()
    edges[0]["typed_edge"] = _produces(structural_only=True, causal_propagation_allowed=True)
    result = _run(candidate_nodes=nodes, candidate_edges=edges)

    assert result["evaluated_edges"] == ["e-bc", "e-cd"]
    assert result["edge_contract_rejections"] == [
        {"edge_id": "e-ab", "reason": "contradictory_edge_attributes"}
    ]
    assert result["authority"] == "NONE"
    assert result["coverage_proof"] is False


def test_authority_implied_edge_is_not_handed_off() -> None:
    nodes, edges = _chain()
    for edge in edges:
        edge["typed_edge"] = _produces()
    edges[0]["typed_edge"] = _produces(trading_authority_implied=True)
    result = _run(candidate_nodes=nodes, candidate_edges=edges)

    assert "e-ab" not in result["evaluated_edges"]
    assert result["edge_contract_rejections"][0] == {
        "edge_id": "e-ab",
        "reason": "authority_implied",
    }
    assert result["authority"] == "NONE"
    assert result["trading_authority"] == "NONE"
    assert result["coverage_proof"] is False


def test_forged_census_does_not_compose() -> None:
    result = _run(provenance=_provenance(census_pin=CURRENT_COMMIT, census_currency="CURRENT"))

    assert result["status"] == STATUS_FORGED_PROVENANCE
    assert result["composition_invoked"] is False
    assert result["coverage_proof"] is False
    assert result["evaluated_nodes"] == []


def test_forged_landscape_does_not_compose() -> None:
    result = _run(provenance=_provenance(landscape_currency="CURRENT"))

    assert result["status"] == STATUS_FORGED_PROVENANCE
    assert result["composition_invoked"] is False
    assert result["coverage_proof"] is False


def test_forged_graph_does_not_compose() -> None:
    result = _run(provenance=_provenance(graph_pin=GRAPH_LEGACY_PIN))

    assert result["status"] == STATUS_FORGED_PROVENANCE
    assert result["composition_invoked"] is False
    assert result["graph_materialized"] is False


def test_empty_scope_does_not_compose() -> None:
    result = _run(scope=scope_of(members=[]))

    assert result["status"] == STATUS_SCOPE_EMPTY
    assert result["composition_invoked"] is False
    assert result["coverage_gap"] is True
    assert result["coverage_proof"] is False


def test_exclusions_only_does_not_compose_or_prove_coverage() -> None:
    result = _run(scope=scope_of(members=[], excluded=["node-x"]))

    assert result["status"] == STATUS_ACCEPTED
    assert result["composition_invoked"] is False
    assert result["scope_coverage_gap"] is True
    assert result["graph_coverage_gap"] is False
    assert result["observation_coverage_gap"] is False
    assert result["coverage_gap"] is True
    assert result["coverage_proof"] is False
    assert result["evaluated_nodes"] == []


def test_unknown_node_remains_a_graph_gap() -> None:
    nodes, edges = _chain()
    for edge in edges:
        edge["typed_edge"] = _produces()
    nodes.append(_node("node-y"))
    result = _run(candidate_nodes=nodes, candidate_edges=edges)

    assert result["unknown_nodes"] == ["node-y"]
    assert "node-y" not in result["evaluated_nodes"]
    assert result["scope_coverage_gap"] is False
    assert result["graph_coverage_gap"] is True
    assert result["observation_coverage_gap"] is False
    assert result["coverage_gap"] is True
    assert result["implicit_scope_expansion"] is False
    assert result["coverage_proof"] is False


def test_unassigned_only_is_not_auto_assigned() -> None:
    result = _run(scope=scope_of(members=[], unresolved=["node-a"]))

    assert result["status"] == STATUS_ACCEPTED
    assert result["composition_invoked"] is False
    assert result["evaluated_nodes"] == []
    assert result["coverage_gap"] is True
    assert result["coverage_proof"] is False


def test_excluded_and_unknown_nodes_stay_outside_scope() -> None:
    nodes, edges = _chain()
    nodes.extend([_node("node-x"), _node("node-y"), _node("node-z", epistemic="HISTORICAL")])
    edges.append(_edge("e-ax", "node-a", "node-x"))
    result = _run(
        candidate_nodes=nodes,
        candidate_edges=edges,
        scope=scope_of(
            ["node-a", "node-b", "node-c", "node-d", "node-z"],
            excluded=["node-x"],
        ),
    )

    assert "node-x" in result["excluded_nodes"]
    assert "node-x" not in result["evaluated_nodes"]
    assert "e-ax" not in result["evaluated_edges"]
    assert "node-x" not in result["forward"]["reachable"]
    assert result["unknown_nodes"] == ["node-y"]
    assert "node-y" not in result["evaluated_nodes"]
    assert result["filtered_non_current_nodes"] == ["node-z"]
    assert "node-z" not in result["evaluated_nodes"]
    assert result["coverage_proof"] is False
    assert result["coverage_gap"] is True


def test_completed_traversal_does_not_prove_coverage_or_closure() -> None:
    nodes, edges = _chain()
    for node in nodes:
        node["reachability"] = "EXISTS"
    for edge in edges:
        edge["typed_edge"] = _produces()
    result = _run(candidate_nodes=nodes, candidate_edges=edges)

    assert result["forward"]["traversal_completed"] is True
    assert result["forward"]["additional_traversable_edge_found"] is True
    assert result["forward"]["reachability_proven"] is True
    assert result["forward"]["coverage_proven"] is False
    assert result["forward"]["causal_closure_proven"] is False
    assert result["forward"]["coverage_gap"] is False
    assert result["coverage_proof"] is False
    assert result["reverse"]["causal_closure_proven"] is False


def test_invalid_pin_does_not_call_composer() -> None:
    calls: list[str] = []

    def _spy(**_kwargs: Any) -> dict[str, Any]:
        calls.append("composed")
        raise AssertionError("composer must not run")

    result = _run(declared_commit_sha=CENSUS_LEGACY_PIN, composer=_spy)

    assert result["status"] == STATUS_PIN_MISMATCH
    assert calls == []
    assert result["composition_invoked"] is False
    assert result["coverage_proof"] is False
    assert "result_pin" not in result
    assert "result_tree" not in result
