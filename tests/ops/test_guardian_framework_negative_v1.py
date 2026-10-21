"""Shared fail-closed invariants for provenance, scope, coverage, and writes."""

from __future__ import annotations

from pathlib import Path

from scripts.ops.pin_scope_binding_v1.bind_v1 import bind_pin_and_scope_v1
from scripts.ops.pin_scope_binding_v1.constants_v1 import (
    STATUS_FORGED_PROVENANCE,
    STATUS_SCOPE_CONFLICT,
)
from scripts.ops.scoped_causal_graph_adapter_v1.adapt_v1 import run_scoped_causal_graph_v1
from scripts.ops.scoped_ghv_crosswalk_adapter_v1.adapt_v1 import run_scoped_ghv_v1
from tests.ops.guardian_framework_fixtures_v1 import (
    AUTHORIZED_COMMIT,
    AUTHORIZED_TREE,
    chain_scope,
    honest_provenance,
    scope_of,
)
from tests.ops.test_scoped_causal_graph_adapter_v1 import _wp_a1

_REPO_ROOT = Path(__file__).resolve().parents[2]


def test_forged_current_census_pin_fails_closed() -> None:
    result = bind_pin_and_scope_v1(
        authoritative_commit_sha=AUTHORIZED_COMMIT,
        authoritative_tree_sha=AUTHORIZED_TREE,
        declared_commit_sha=AUTHORIZED_COMMIT,
        declared_tree_sha=AUTHORIZED_TREE,
        provenance=honest_provenance(census_pin=AUTHORIZED_COMMIT, census_currency="CURRENT"),
        scope=scope_of(),
    )

    assert result["status"] == STATUS_FORGED_PROVENANCE
    assert result["coverage_proof"] is False


def test_overlapping_scope_classes_conflict() -> None:
    result = bind_pin_and_scope_v1(
        authoritative_commit_sha=AUTHORIZED_COMMIT,
        authoritative_tree_sha=AUTHORIZED_TREE,
        declared_commit_sha=AUTHORIZED_COMMIT,
        declared_tree_sha=AUTHORIZED_TREE,
        provenance=honest_provenance(),
        scope=scope_of(members=["node-a"], references=["node-a"]),
    )

    assert result["status"] == STATUS_SCOPE_CONFLICT


def test_unknown_reachability_keeps_the_observation_gap() -> None:
    result = run_scoped_ghv_v1(
        authoritative_commit_sha=AUTHORIZED_COMMIT,
        authoritative_tree_sha=AUTHORIZED_TREE,
        declared_commit_sha=AUTHORIZED_COMMIT,
        declared_tree_sha=AUTHORIZED_TREE,
        provenance=honest_provenance(),
        scope=chain_scope(),
        candidate_nodes=[
            {
                "object_id": "node-a",
                "epistemic_status": "PROVEN_CURRENT",
                "current_status": "PROVEN_CURRENT",
                "primary_class": "OBSERVATION",
                "reachability": "UNKNOWN",
            }
        ],
        candidate_edges=[],
        origin_native_id="node-a",
        reverse_origin_native_id="node-a",
    )

    assert result["status"] == "ACCEPTED"
    assert result["observation_coverage_gap"] is True
    assert result["coverage_proof"] is False
    assert result["forward"]["traversal_completed"] is True
    assert result["forward"]["reachability_proven"] is False
    assert result["forward"]["coverage_proven"] is False
    assert result["forward"]["causal_closure_proven"] is False
    assert result["forward"]["coverage_gap"] is True
    assert result["reverse"]["reachability_proven"] is False
    assert result["reverse"]["coverage_gap"] is True


def test_repository_output_is_refused() -> None:
    prepared = _wp_a1()
    result = run_scoped_causal_graph_v1(
        authoritative_commit_sha=AUTHORIZED_COMMIT,
        authoritative_tree_sha=AUTHORIZED_TREE,
        declared_commit_sha=AUTHORIZED_COMMIT,
        declared_tree_sha=AUTHORIZED_TREE,
        provenance=honest_provenance(),
        scope=chain_scope(),
        wp_a1_result=prepared,
        output_dir=_REPO_ROOT / "config" / "governance",
    )

    assert result["integrator_invoked"] is False
    assert "output_dir_inside_repository" in result["reasons"]
    assert result["coverage_proof"] is False
