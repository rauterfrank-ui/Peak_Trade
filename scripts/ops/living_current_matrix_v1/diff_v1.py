"""Deterministic baseline vs candidate Living CURRENT Matrix diff."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.ops.living_current_matrix_v1.constants_v1 import (
    CHANGE_REPORT_SCHEMA,
    KNOWN_COVERAGE_GAP_IDS,
    MANIFEST_SCHEMA,
    MATRIX_AUTHORITY,
)


@dataclass
class MatrixDiffResultV1:
    ok: bool
    failure_semantic: str | None = None
    errors: list[str] = field(default_factory=list)
    report: dict[str, Any] = field(default_factory=dict)


def _load_manifest(matrix_dir: Path) -> dict[str, Any]:
    path = matrix_dir / "living_current_matrix_manifest.v1.json"
    if not path.is_file():
        raise FileNotFoundError(f"missing_manifest:{path}")
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema_version") != MANIFEST_SCHEMA:
        raise ValueError("manifest_schema_mismatch")
    return doc


def _load_composed(matrix_dir: Path) -> dict[str, Any]:
    path = matrix_dir / "wp1" / "composed_forensic_graph.v1.json"
    if not path.is_file():
        raise FileNotFoundError(f"missing_composed:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _node_key(node: dict[str, Any]) -> str:
    return str(node.get("canonical_id") or "")


def _wp1_edge_key(edge: dict[str, Any]) -> str:
    return str(edge.get("edge_id") or "")


def _overlay_edge_key(edge: dict[str, Any]) -> str:
    payload = {
        "SOURCE_CFI": edge.get("SOURCE_CFI"),
        "TARGET_CFI": edge.get("TARGET_CFI"),
        "EDGE_TYPE": edge.get("EDGE_TYPE"),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _node_digest(node: dict[str, Any]) -> str:
    subset = {
        "canonical_id": node.get("canonical_id"),
        "current_relevance": node.get("current_relevance"),
        "source_system": node.get("source_system"),
        "source_native_id": node.get("source_native_id"),
    }
    return hashlib.sha256(
        json.dumps(subset, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _edge_digest(edge: dict[str, Any]) -> str:
    typed = edge.get("typed_edge") or {}
    subset = {
        "edge_id": edge.get("edge_id"),
        "source_native_id": edge.get("source_native_id"),
        "target_native_id": edge.get("target_native_id"),
        "edge_type": typed.get("edge_type"),
        "causal_propagation_allowed": typed.get("causal_propagation_allowed"),
        "current_relevance": edge.get("current_relevance"),
    }
    return hashlib.sha256(
        json.dumps(subset, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _protected_scope_touch(changed_paths: list[str]) -> dict[str, bool]:
    prefixes = (
        "src/execution/",
        "src/risk/",
        "src/trading/master_v2/double_play",
        "src/governance/master_v2_double_play",
    )
    touched = {label: False for label in ("execution", "risk", "double_play", "master_v2_core")}
    for p in changed_paths:
        if p.startswith("src/execution/"):
            touched["execution"] = True
        if p.startswith("src/risk/"):
            touched["risk"] = True
        if "double_play" in p:
            touched["double_play"] = True
        if p.startswith("src/governance/master_v2") and "double_play" not in p:
            touched["master_v2_core"] = True
    return touched


def diff_living_current_matrix_v1(
    *,
    baseline_dir: Path,
    candidate_dir: Path,
    git_changed_paths: list[str] | None = None,
) -> MatrixDiffResultV1:
    out = MatrixDiffResultV1(ok=False)
    baseline_dir = baseline_dir.resolve()
    candidate_dir = candidate_dir.resolve()

    try:
        base_m = _load_manifest(baseline_dir)
        cand_m = _load_manifest(candidate_dir)
    except (OSError, json.JSONDecodeError, ValueError, FileNotFoundError) as exc:
        out.failure_semantic = "SNAPSHOT_BINDING_FAILURE"
        out.errors.append(str(exc))
        return out

    base_sha = str(base_m.get("git_sha") or "")
    cand_sha = str(cand_m.get("git_sha") or "")
    if not base_sha or not cand_sha:
        out.failure_semantic = "SNAPSHOT_BINDING_FAILURE"
        out.errors.append("missing_git_sha_in_manifest")
        return out
    if base_sha == cand_sha:
        out.failure_semantic = "SNAPSHOT_BINDING_FAILURE"
        out.errors.append("baseline_candidate_sha_identical")
        return out

    try:
        base_c = _load_composed(baseline_dir)
        cand_c = _load_composed(candidate_dir)
    except (OSError, json.JSONDecodeError, FileNotFoundError) as exc:
        out.failure_semantic = "INCOMPLETE_MATRIX"
        out.errors.append(str(exc))
        return out

    base_nodes = {_node_key(n): n for n in base_c.get("nodes") or [] if isinstance(n, dict)}
    cand_nodes = {_node_key(n): n for n in cand_c.get("nodes") or [] if isinstance(n, dict)}
    base_edges = {_wp1_edge_key(e): e for e in base_c.get("edges") or [] if isinstance(e, dict)}
    cand_edges = {_wp1_edge_key(e): e for e in cand_c.get("edges") or [] if isinstance(e, dict)}

    added_nodes = sorted(set(cand_nodes) - set(base_nodes))
    removed_nodes = sorted(set(base_nodes) - set(cand_nodes))
    changed_nodes = sorted(
        k
        for k in set(base_nodes) & set(cand_nodes)
        if _node_digest(base_nodes[k]) != _node_digest(cand_nodes[k])
    )

    added_edges = sorted(set(cand_edges) - set(base_edges))
    removed_edges = sorted(set(base_edges) - set(cand_edges))
    changed_edges = sorted(
        k
        for k in set(base_edges) & set(cand_edges)
        if _edge_digest(base_edges[k]) != _edge_digest(cand_edges[k])
    )

    base_gaps = {json.dumps(g, sort_keys=True) for g in base_m.get("preserved_coverage_gaps") or []}
    cand_gaps = {json.dumps(g, sort_keys=True) for g in cand_m.get("preserved_coverage_gaps") or []}
    new_gaps = [json.loads(g) for g in sorted(cand_gaps - base_gaps)]
    known_new = [
        g for g in new_gaps if not (g.get("KNOWN_GAP") or g.get("reason") in KNOWN_COVERAGE_GAP_IDS)
    ]

    reproofs: list[str] = []
    if added_nodes or removed_nodes or changed_nodes:
        reproofs.append("tests/ops/test_ghv_forensic_whole_system_crosswalk_v1.py")
    if added_edges or removed_edges or changed_edges:
        reproofs.append("tests/ops/test_ghv_forensic_whole_system_causal_integration_v1.py")
    if known_new:
        reproofs.append("living_current_matrix_diff_review_required")

    report = {
        "schema_version": CHANGE_REPORT_SCHEMA,
        "authority": MATRIX_AUTHORITY,
        "baseline_git_sha": base_sha,
        "candidate_git_sha": cand_sha,
        "baseline_matrix_status": base_m.get("MATRIX_STATUS"),
        "candidate_matrix_status": cand_m.get("MATRIX_STATUS"),
        "baseline_snapshot_id": base_m.get("snapshot_id"),
        "candidate_snapshot_id": cand_m.get("snapshot_id"),
        "content_hashes": {
            "baseline_manifest": base_m.get("artifact_sha256", {}).get(
                "living_current_matrix_manifest.v1.json"
            ),
            "candidate_manifest": cand_m.get("artifact_sha256", {}).get(
                "living_current_matrix_manifest.v1.json"
            ),
        },
        "components_added": added_nodes,
        "components_removed": removed_nodes,
        "components_changed": changed_nodes,
        "relationships_added": added_edges,
        "relationships_removed": removed_edges,
        "relationships_changed": changed_edges,
        "activation_or_relevance_changes": changed_nodes + changed_edges,
        "new_coverage_gaps": new_gaps,
        "known_coverage_gaps_preserved": list(base_m.get("known_coverage_gaps") or []),
        "unverified_impacts": known_new,
        "protected_scope_touch": _protected_scope_touch(git_changed_paths or []),
        "required_targeted_reproofs": sorted(set(reproofs)),
        "GLOBAL_CAUSAL_CLOSURE_PROVEN": False,
        "GHV_RUNTIME_CORRELATION": "NOT_IMPLEMENTED",
    }

    out.ok = True
    out.report = report
    return out


def write_change_report_v1(*, report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
