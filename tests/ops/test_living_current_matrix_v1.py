"""Tests for Living CURRENT Matrix orchestration and diff."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ops.living_current_matrix_v1.diff_v1 import diff_living_current_matrix_v1
from scripts.ops.living_current_matrix_v1.constants_v1 import MANIFEST_SCHEMA

REPO_ROOT = Path(__file__).resolve().parents[2]


def _manifest(*, sha: str, snapshot: str = "snap1") -> dict:
    return {
        "schema_version": MANIFEST_SCHEMA,
        "authority": "NONE",
        "git_sha": sha,
        "MATRIX_STATUS": "PARTIAL",
        "snapshot_id": snapshot,
        "preserved_coverage_gaps": [
            {"reason": "empty_stage_to_cfi_mapping", "KNOWN_GAP": True},
        ],
        "known_coverage_gaps": [],
        "artifact_sha256": {},
    }


def _composed(*, nodes: list, edges: list, snapshot: str = "snap1") -> dict:
    return {
        "snapshot_id": snapshot,
        "GRAPH_MODE": "NAVIGATION_ONLY",
        "CURRENT_GRAPH_VERIFIED": False,
        "nodes": nodes,
        "edges": edges,
        "unresolved_edges": [],
    }


def _write_matrix_tree(root: Path, *, sha: str, composed: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "living_current_matrix_manifest.v1.json").write_text(
        json.dumps(_manifest(sha=sha, snapshot=str(composed.get("snapshot_id")))),
        encoding="utf-8",
    )
    wp1 = root / "wp1"
    wp1.mkdir(parents=True, exist_ok=True)
    (wp1 / "composed_forensic_graph.v1.json").write_text(json.dumps(composed), encoding="utf-8")


def test_diff_detects_node_and_edge_changes(tmp_path: Path) -> None:
    base = tmp_path / "base"
    cand = tmp_path / "cand"
    n1 = {
        "canonical_id": "CFI/v1/COMPONENT/snap1/SYS/A",
        "source_system": "CURRENT_SYSTEM_CENSUS",
        "source_native_id": "A",
        "current_relevance": {"CURRENT_RELEVANCE_STATE": "CURRENT_VERIFIED"},
    }
    n2 = {
        "canonical_id": "CFI/v1/COMPONENT/snap1/SYS/B",
        "source_system": "CURRENT_SYSTEM_CENSUS",
        "source_native_id": "B",
        "current_relevance": {"CURRENT_RELEVANCE_STATE": "CURRENT_VERIFIED"},
    }
    e1 = {
        "edge_id": "census:E1",
        "source_native_id": "A",
        "target_native_id": "B",
        "typed_edge": {"edge_type": "PRODUCES", "causal_propagation_allowed": True},
        "current_relevance": {"CURRENT_RELEVANCE_STATE": "CURRENT_VERIFIED"},
    }
    _write_matrix_tree(base, sha="a" * 40, composed=_composed(nodes=[n1], edges=[]))
    _write_matrix_tree(
        cand,
        sha="b" * 40,
        composed=_composed(nodes=[n1, n2], edges=[e1]),
    )
    result = diff_living_current_matrix_v1(
        baseline_dir=base,
        candidate_dir=cand,
        git_changed_paths=["scripts/ops/example.py"],
    )
    assert result.ok
    assert "CFI/v1/COMPONENT/snap1/SYS/B" in result.report["components_added"]
    assert "census:E1" in result.report["relationships_added"]
    assert result.report["GLOBAL_CAUSAL_CLOSURE_PROVEN"] is False


def test_diff_fail_closed_on_identical_sha(tmp_path: Path) -> None:
    base = tmp_path / "base"
    sha = "c" * 40
    _write_matrix_tree(base, sha=sha, composed=_composed(nodes=[], edges=[]))
    cand = tmp_path / "cand"
    _write_matrix_tree(cand, sha=sha, composed=_composed(nodes=[], edges=[]))
    result = diff_living_current_matrix_v1(baseline_dir=base, candidate_dir=cand)
    assert not result.ok
    assert result.failure_semantic == "SNAPSHOT_BINDING_FAILURE"


def test_generate_matrix_smoke(tmp_path: Path) -> None:
    pytest.importorskip("yaml")
    from scripts.ops.living_current_matrix_v1.generate_v1 import (
        generate_living_current_matrix_v1,
    )

    out = tmp_path / "matrix_out"
    result = generate_living_current_matrix_v1(
        repo_root=REPO_ROOT,
        output_dir=out,
        include_atlas=False,
    )
    assert result.matrix_status in ("COMPLETE", "PARTIAL", "UNAVAILABLE")
    manifest_path = out / "living_current_matrix_manifest.v1.json"
    if result.ok:
        assert manifest_path.is_file()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest.get("GHV_RUNTIME_CORRELATION") == "NOT_IMPLEMENTED"
        assert manifest.get("GLOBAL_CAUSAL_CLOSURE_PROVEN") is False


def test_truth_gates_docs_drift_only_contract() -> None:
    text = (REPO_ROOT / ".github" / "workflows" / "truth_gates_pr.yml").read_text(encoding="utf-8")
    assert "check_docs_drift_guard.py" in text
    assert "validate_system_atlas_v1.py" not in text
    periodic = (REPO_ROOT / ".github" / "workflows" / "governance_atlas_periodic_v1.yml").read_text(
        encoding="utf-8"
    )
    assert "validate_system_atlas_v1.py" in periodic


def test_current_matrix_workflow_informational_marker() -> None:
    wf = (REPO_ROOT / ".github" / "workflows" / "current_matrix_check_v1.yml").read_text(
        encoding="utf-8"
    )
    assert "INFORMATIONAL ONLY" in wf
    assert "CURRENT Matrix Check" in wf
