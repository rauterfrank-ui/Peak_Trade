"""WP-A2 uses a real WP-A1 result and writes only under tmp_path."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.ops.pin_scope_binding_v1.constants_v1 import (
    STATUS_ACCEPTED,
    STATUS_FORGED_PROVENANCE,
    STATUS_PIN_MISMATCH,
    STATUS_SCOPE_EMPTY,
)
from tests.ops.guardian_framework_fixtures_v1 import (
    AUTHORIZED_COMMIT,
    AUTHORIZED_TREE,
    chain_scope,
    honest_provenance,
    scope_of,
)
from scripts.ops.scoped_causal_graph_adapter_v1.adapt_v1 import run_scoped_causal_graph_v1
from scripts.ops.scoped_causal_graph_adapter_v1.constants_v1 import (
    PROVENANCE_MANIFEST_NAME,
    STATUS_MISSING_CURRENT_EVIDENCE,
)
from scripts.ops.scoped_ghv_crosswalk_adapter_v1.adapt_v1 import run_scoped_ghv_v1

CURRENT_COMMIT = AUTHORIZED_COMMIT
CURRENT_TREE = AUTHORIZED_TREE
CENSUS_LEGACY_PIN = "6216201d7acbc771f84b6b6884eccc41359927cf"
LANDSCAPE_LEGACY_TREE = "6422bfde79fd5aa45d2939a821980abf9aa4e3df"
GRAPH_LEGACY_PIN = "b6ffca1d3b39b3dd8814c7c795a8aa6e04bc177a"


def _provenance(**overrides: str) -> dict[str, dict[str, str]]:
    return honest_provenance(**overrides)


def _node(native_id: str) -> dict[str, str]:
    return {
        "object_id": native_id,
        "epistemic_status": "PROVEN_CURRENT",
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
        "typed_edge": {
            "edge_type": "PRODUCES",
            "structural_only": False,
            "causal_propagation_allowed": True,
            "trading_authority_implied": False,
        },
    }


def _chain() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes = [_node(name) for name in ("node-a", "node-b", "node-c", "node-d")]
    edges = [
        _edge("e-ab", "node-a", "node-b"),
        _edge("e-bc", "node-b", "node-c"),
        _edge("e-cd", "node-c", "node-d"),
    ]
    return nodes, edges


def _wp_a1(**overrides: Any) -> dict[str, Any]:
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
    result = run_scoped_ghv_v1(**payload)
    if result.get("status") == "ACCEPTED" and result.get("composition_invoked"):
        assert result["result_pin"] == payload["declared_commit_sha"]
        assert result["result_tree"] == payload["declared_tree_sha"]
        assert result["candidate_nodes"] == payload["candidate_nodes"]
        assert result["candidate_edges"] == payload["candidate_edges"]
        assert result["scope_identity"] == payload["scope"]
        assert result["checked_provenance"] == payload["provenance"]
    return result


def _run(tmp_path: Path, **overrides: Any) -> dict[str, Any]:
    wp_a1_overrides = dict(overrides.pop("wp_a1_overrides", {}))
    result = _wp_a1(**wp_a1_overrides)
    if "wp_a1_result" in overrides:
        result = overrides.pop("wp_a1_result")
    payload: dict[str, Any] = {
        "authoritative_commit_sha": CURRENT_COMMIT,
        "authoritative_tree_sha": CURRENT_TREE,
        "declared_commit_sha": CURRENT_COMMIT,
        "declared_tree_sha": CURRENT_TREE,
        "provenance": _provenance(),
        "scope": chain_scope(),
        "wp_a1_result": result,
        "output_dir": tmp_path / "graph-out",
    }
    payload.update(overrides)
    return run_scoped_causal_graph_v1(**payload)


def test_valid_chain_reuses_integrator_without_coverage_pass(tmp_path: Path) -> None:
    result = _run(tmp_path)

    assert result["status"] == STATUS_ACCEPTED
    assert result["integrator_invoked"] is True
    assert result["inspection_ok"] is True
    assert result["authority"] == "NONE"
    assert result["guardian_identity"] is False
    assert result["coverage_proof"] is False
    assert result["integrated_authority"] == "NONE"
    assert result["global_causal_closure_proven"] is False
    assert result["overlay_edge_count"] == 0
    assert result["integrated_node_ids"] == ["node-a", "node-b", "node-c", "node-d"]
    assert result["integrated_edge_ids"] == ["e-ab", "e-bc", "e-cd"]
    assert "overall_pass" not in result
    manifest = json.loads(
        (Path(result["output_dir"]) / PROVENANCE_MANIFEST_NAME).read_text(encoding="utf-8")
    )
    assert manifest["declared_commit_sha"] == CURRENT_COMMIT
    assert manifest["declared_tree_sha"] == CURRENT_TREE
    assert manifest["result_pin"] == CURRENT_COMMIT
    assert manifest["authority"] == "NONE"
    assert manifest["coverage_proof"] is False
    assert manifest["repository_evidence_write"] is False


def test_wrong_commit_does_not_integrate(tmp_path: Path) -> None:
    calls: list[str] = []

    def _spy(**_kwargs: Any) -> Any:
        calls.append("integrated")
        raise AssertionError("integrator must not run")

    result = _run(tmp_path, declared_commit_sha=CENSUS_LEGACY_PIN, integrator=_spy)

    assert result["status"] == STATUS_PIN_MISMATCH
    assert calls == []
    assert result["coverage_proof"] is False


def test_wrong_tree_does_not_integrate(tmp_path: Path) -> None:
    result = _run(tmp_path, declared_tree_sha=LANDSCAPE_LEGACY_TREE)

    assert result["status"] == STATUS_PIN_MISMATCH
    assert result["integrator_invoked"] is False


def test_forged_graph_pin_does_not_integrate(tmp_path: Path) -> None:
    result = _run(tmp_path, provenance=_provenance(graph_pin=GRAPH_LEGACY_PIN))

    assert result["status"] == STATUS_FORGED_PROVENANCE
    assert result["integrator_invoked"] is False
    assert result["coverage_proof"] is False


def test_empty_scope_does_not_integrate(tmp_path: Path) -> None:
    empty = scope_of(members=[])
    result = _run(
        tmp_path,
        scope=empty,
        wp_a1_overrides={"scope": empty},
    )

    assert result["status"] == STATUS_SCOPE_EMPTY
    assert result["integrator_invoked"] is False
    assert result["coverage_gap"] is True


def test_exclusions_only_does_not_integrate_as_coverage(tmp_path: Path) -> None:
    scope = scope_of(members=[], excluded=["node-x"])
    result = _run(tmp_path, scope=scope, wp_a1_overrides={"scope": scope})

    assert result["status"] == STATUS_ACCEPTED
    assert result["integrator_invoked"] is False
    assert result["scope_coverage_gap"] is True
    assert result["graph_coverage_gap"] is False
    assert result["observation_coverage_gap"] is False
    assert result["coverage_gap"] is True
    assert result["coverage_proof"] is False
    assert result["integrated_node_ids"] == []
    assert result["authority"] == "NONE"


def test_missing_graph_evidence_is_a_graph_gap(tmp_path: Path) -> None:
    prepared = _wp_a1()
    del prepared["result_pin"]
    del prepared["result_tree"]
    result = _run(tmp_path, wp_a1_result=prepared)

    assert result["status"] == STATUS_MISSING_CURRENT_EVIDENCE
    assert result["graph_coverage_gap"] is True
    assert result["coverage_gap"] is True
    assert result["coverage_proof"] is False
    assert result["integrator_invoked"] is False
    assert result["authority"] == "NONE"


def test_unassigned_only_stays_unassigned(tmp_path: Path) -> None:
    scope = scope_of(members=[], unresolved=["node-a"])
    result = _run(tmp_path, scope=scope, wp_a1_overrides={"scope": scope})

    assert result["status"] == STATUS_ACCEPTED
    assert result["integrator_invoked"] is False
    assert result["integrated_node_ids"] == []
    assert result["coverage_gap"] is True
    assert result["coverage_proof"] is False


def test_unknown_and_excluded_nodes_are_omitted(tmp_path: Path) -> None:
    nodes, edges = _chain()
    nodes.extend([_node("node-x"), _node("node-y")])
    edges.append(_edge("e-ax", "node-a", "node-x"))
    scope = scope_of(["node-a", "node-b", "node-c", "node-d"], excluded=["node-x"])
    result = _run(
        tmp_path,
        scope=scope,
        wp_a1_overrides={"scope": scope, "candidate_nodes": nodes, "candidate_edges": edges},
    )

    assert "node-x" not in result["integrated_node_ids"]
    assert "node-y" not in result["integrated_node_ids"]
    assert "e-ax" not in result["integrated_edge_ids"]
    assert result["integrated_edge_ids"] == ["e-ab", "e-bc", "e-cd"]
    assert result["coverage_gap"] is True
    assert result["coverage_proof"] is False


def test_missing_result_pin_is_missing_current_evidence(tmp_path: Path) -> None:
    prepared = _wp_a1()
    del prepared["result_pin"]
    del prepared["result_tree"]
    result = _run(tmp_path, wp_a1_result=prepared)

    assert result["status"] == STATUS_MISSING_CURRENT_EVIDENCE
    assert result["integrator_invoked"] is False
    assert result["coverage_proof"] is False


def test_direct_a1_result_keeps_checked_pin_and_tree(tmp_path: Path) -> None:
    prepared = _wp_a1()
    result = _run(tmp_path, wp_a1_result=prepared)

    assert result["status"] == STATUS_ACCEPTED
    assert result["integrator_invoked"] is True
    assert prepared["result_pin"] == CURRENT_COMMIT
    assert prepared["result_tree"] == CURRENT_TREE
    assert result["integrated_node_ids"] == ["node-a", "node-b", "node-c", "node-d"]
    assert result["integrated_edge_ids"] == ["e-ab", "e-bc", "e-cd"]
    assert result["authority"] == "NONE"
    assert result["coverage_proof"] is False


def test_manipulated_provenance_is_rejected(tmp_path: Path) -> None:
    prepared = _wp_a1()
    prepared["checked_provenance"] = {
        "census": {"pin": CENSUS_LEGACY_PIN},
        "landscape": {"commit_pin": CURRENT_COMMIT, "tree_pin": CURRENT_TREE},
        "graph": {"pin": CURRENT_COMMIT},
    }
    result = _run(tmp_path, wp_a1_result=prepared)

    assert result["status"] == "INVALID_PROVENANCE"
    assert result["integrator_invoked"] is False
    assert "provenance_mismatch" in result["reasons"]
    assert result["coverage_proof"] is False


def test_divergent_result_tree_is_pin_mismatch(tmp_path: Path) -> None:
    prepared = _wp_a1()
    prepared["result_tree"] = LANDSCAPE_LEGACY_TREE
    result = _run(tmp_path, wp_a1_result=prepared)

    assert result["status"] == STATUS_PIN_MISMATCH
    assert result["integrator_invoked"] is False
    assert "result_pin_tree_mismatch" in result["reasons"]
    assert result["coverage_proof"] is False


def test_scope_identity_conflict_does_not_integrate(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        scope=scope_of(["node-a"]),
    )

    assert result["status"] == "SCOPE_CONFLICT"
    assert result["integrator_invoked"] is False
    assert "scope_identity_mismatch:domain_functional_members" in result["reasons"]
    assert result["integrated_node_ids"] == []
    assert result["coverage_proof"] is False


def test_extra_candidate_node_is_not_emitted(tmp_path: Path) -> None:
    prepared = _wp_a1()
    prepared["candidate_nodes"] = [
        *prepared["candidate_nodes"],
        _node("node-extra"),
    ]
    result = _run(tmp_path, wp_a1_result=prepared)

    assert result["status"] == STATUS_ACCEPTED
    assert result["integrated_node_ids"] == ["node-a", "node-b", "node-c", "node-d"]
    assert "node-extra" not in result["integrated_node_ids"]
    assert result["integrated_edge_ids"] == ["e-ab", "e-bc", "e-cd"]
    assert result["coverage_proof"] is False


def test_missing_typed_edge_is_not_integrated(tmp_path: Path) -> None:
    prepared = _wp_a1()
    untyped = _edge("e-missing", "node-a", "node-b")
    del untyped["typed_edge"]
    untyped["flow_type"] = "OBSERVATION_FLOW"
    prepared["candidate_edges"] = [*prepared["candidate_edges"], untyped]
    prepared["evaluated_edges"] = [*prepared["evaluated_edges"], "e-missing"]
    result = _run(tmp_path, wp_a1_result=prepared)

    assert result["status"] == STATUS_MISSING_CURRENT_EVIDENCE
    assert result["integrator_invoked"] is False
    assert result["reasons"] == ["missing_typed_edge:e-missing"]
    assert result["integrated_edge_ids"] == []
    assert result["authority"] == "NONE"
    assert result["coverage_proof"] is False


def test_unknown_typed_edge_is_not_integrated(tmp_path: Path) -> None:
    prepared = _wp_a1()
    prepared["candidate_edges"][0]["typed_edge"]["edge_type"] = "NOT_A_CURRENT_EDGE"
    result = _run(tmp_path, wp_a1_result=prepared)

    assert result["status"] == STATUS_MISSING_CURRENT_EVIDENCE
    assert result["integrator_invoked"] is False
    assert result["reasons"] == ["unknown_edge_type:e-ab"]
    assert result["coverage_proof"] is False
    assert result["authority"] == "NONE"


def test_extra_candidate_edge_is_not_emitted(tmp_path: Path) -> None:
    prepared = _wp_a1()
    prepared["candidate_edges"] = [
        *prepared["candidate_edges"],
        _edge("e-extra", "node-a", "node-d"),
    ]
    result = _run(tmp_path, wp_a1_result=prepared)

    assert result["status"] == STATUS_ACCEPTED
    assert result["integrated_edge_ids"] == ["e-ab", "e-bc", "e-cd"]
    assert "e-extra" not in result["integrated_edge_ids"]
    assert result["coverage_proof"] is False
