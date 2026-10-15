"""Orchestrate WP1 → WP2-A → WP2-B-A1 into a versioned Living CURRENT Matrix."""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.compose_v1 import (
    run_forensic_crosswalk_v1,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.graph_mode_v1 import GraphMode
from scripts.ops.ghv_forensic_whole_system_causal_integration_v1.integrate_v1 import (
    run_causal_integration_v1,
)
from scripts.ops.ghv_forensic_whole_system_causal_ghv_adapter_v1.inspect_graph_v1 import (
    run_offline_graph_inspection_v1,
)
from scripts.ops.living_current_matrix_v1.constants_v1 import (
    KNOWN_COVERAGE_GAP_IDS,
    MANIFEST_SCHEMA,
    MATRIX_AUTHORITY,
    MATRIX_STATUS_COMPLETE,
    MATRIX_STATUS_PARTIAL,
    MATRIX_STATUS_UNAVAILABLE,
    WP1_RULES_REL,
)


@dataclass
class MatrixGenerationResultV1:
    ok: bool
    matrix_status: str
    failure_semantic: str | None = None
    errors: list[str] = field(default_factory=list)
    output_dir: Path | None = None
    manifest: dict[str, Any] = field(default_factory=dict)
    wp1_graph_mode: str = ""
    git_sha: str = ""


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _git_head(repo_root: Path) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def _inventory_from_wp1(composed: dict[str, Any]) -> dict[str, Any]:
    nodes = composed.get("nodes") or []
    edges = composed.get("edges") or []
    return {
        "schema_version": "canonical_current_inventory.v1",
        "authority": MATRIX_AUTHORITY,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "snapshot_id": composed.get("snapshot_id"),
        "graph_mode": composed.get("GRAPH_MODE"),
        "current_graph_verified": composed.get("CURRENT_GRAPH_VERIFIED"),
        "unresolved_edge_count": len(composed.get("unresolved_edges") or []),
    }


def generate_living_current_matrix_v1(
    *,
    repo_root: Path,
    output_dir: Path,
    git_sha: str | None = None,
    include_atlas: bool = True,
) -> MatrixGenerationResultV1:
    out = MatrixGenerationResultV1(ok=False, matrix_status=MATRIX_STATUS_UNAVAILABLE)
    repo_root = repo_root.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if "pl_c1_p510a_entry_exit_alignment" in str(repo_root):
        out.failure_semantic = "C1_WORKTREE_NOT_ALLOWED"
        out.errors.append("c1_overlay_worktree_forbidden")
        return out

    sha = git_sha or _git_head(repo_root)
    if not sha:
        out.failure_semantic = "GIT_IDENTITY_UNAVAILABLE"
        out.errors.append("git_head_unavailable")
        return out
    out.git_sha = sha

    rules = repo_root / WP1_RULES_REL
    if not rules.is_file():
        out.failure_semantic = "WP1_RULES_MISSING"
        out.errors.append(f"missing_rules:{rules}")
        return out

    wp1_dir = output_dir / "wp1"
    wp2a_dir = output_dir / "wp2a"
    wp2b_dir = output_dir / "wp2b"
    status_reasons: list[str] = []
    matrix_status = MATRIX_STATUS_UNAVAILABLE

    crosswalk = run_forensic_crosswalk_v1(
        repo_root=repo_root,
        output_dir=wp1_dir,
        rules_path=rules,
        include_atlas=include_atlas,
        graph_mode=GraphMode.STRICT_CURRENT,
    )
    graph_mode = GraphMode.STRICT_CURRENT
    if not crosswalk.ok:
        status_reasons.append("strict_current_crosswalk_failed")
        crosswalk = run_forensic_crosswalk_v1(
            repo_root=repo_root,
            output_dir=wp1_dir,
            rules_path=rules,
            include_atlas=include_atlas,
            graph_mode=GraphMode.NAVIGATION_ONLY,
        )
        graph_mode = GraphMode.NAVIGATION_ONLY
        status_reasons.append("fallback_navigation_only")

    composed_path = wp1_dir / "composed_forensic_graph.v1.json"
    if not composed_path.is_file():
        out.failure_semantic = "WP1_OUTPUT_MISSING"
        out.errors.append("composed_forensic_graph_missing")
        out.manifest = _build_manifest(
            sha=sha,
            status=MATRIX_STATUS_UNAVAILABLE,
            reasons=status_reasons + ["wp1_no_output"],
            hashes={},
            wp1_mode="",
            snapshot_id="",
            gaps=[],
        )
        _write_manifest(output_dir, out.manifest)
        return out

    composed = json.loads(composed_path.read_text(encoding="utf-8"))
    out.wp1_graph_mode = str(composed.get("GRAPH_MODE") or graph_mode.value)
    inventory = _inventory_from_wp1(composed)
    (output_dir / "canonical_current_inventory.v1.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    wp2a = run_causal_integration_v1(wp1_output_dir=wp1_dir, output_dir=wp2a_dir)
    if not wp2a.ok:
        out.failure_semantic = wp2a.failure_semantic
        out.errors.extend(wp2a.errors)
        out.manifest = _build_manifest(
            sha=sha,
            status=MATRIX_STATUS_UNAVAILABLE,
            reasons=status_reasons + ["wp2a_integration_failed"],
            hashes={},
            wp1_mode=out.wp1_graph_mode,
            snapshot_id=str(composed.get("snapshot_id") or ""),
            gaps=[],
        )
        _write_manifest(output_dir, out.manifest)
        return out

    inspect = run_offline_graph_inspection_v1(
        wp2a_output_dir=wp2a_dir,
        output_dir=wp2b_dir,
        repo_root=repo_root,
    )
    if not inspect.ok:
        out.failure_semantic = inspect.failure_semantic
        out.errors.extend(inspect.errors)
        out.manifest = _build_manifest(
            sha=sha,
            status=MATRIX_STATUS_UNAVAILABLE,
            reasons=status_reasons + ["wp2b_inspection_failed"],
            hashes={},
            wp1_mode=out.wp1_graph_mode,
            snapshot_id=str(composed.get("snapshot_id") or ""),
            gaps=[],
        )
        _write_manifest(output_dir, out.manifest)
        return out

    coverage_gaps: list[dict[str, Any]] = []
    gaps_path = wp2a_dir / "causal_coverage_gaps.v1.json"
    if gaps_path.is_file():
        gaps_doc = json.loads(gaps_path.read_text(encoding="utf-8"))
        coverage_gaps = list(gaps_doc.get("gaps") or [])
        if gaps_doc.get("wp1_unresolved_edges"):
            coverage_gaps.append(
                {
                    "reason": "unresolved_wp1_census_edges",
                    "KNOWN_GAP": True,
                    "count": len(gaps_doc.get("wp1_unresolved_edges") or []),
                }
            )
    coverage_gaps.append(
        {
            "reason": "empty_stage_to_cfi_mapping",
            "KNOWN_GAP": True,
            "GHV_RUNTIME_CORRELATION": "NOT_IMPLEMENTED",
        }
    )

    verified = bool(composed.get("CURRENT_GRAPH_VERIFIED"))
    if graph_mode == GraphMode.NAVIGATION_ONLY or not verified:
        matrix_status = MATRIX_STATUS_PARTIAL
        if "navigation_only_snapshot_drift" not in status_reasons:
            status_reasons.append("navigation_only_or_unverified_graph")
    else:
        matrix_status = MATRIX_STATUS_COMPLETE

    out.manifest = _build_manifest(
        sha=sha,
        status=matrix_status,
        reasons=status_reasons,
        hashes=_collect_hashes(output_dir),
        wp1_mode=out.wp1_graph_mode,
        snapshot_id=str(composed.get("snapshot_id") or crosswalk.snapshot_id),
        gaps=coverage_gaps,
        inspection_bundle=inspect.bundle_doc,
        integration_manifest=wp2a.manifest,
    )
    _write_manifest(output_dir, out.manifest)
    (output_dir / "living_current_matrix_terminal_report.v1.json").write_text(
        json.dumps(
            {
                "schema_version": "living_current_matrix_terminal_report.v1",
                "authority": MATRIX_AUTHORITY,
                "git_sha": sha,
                "matrix_status": matrix_status,
                "wp1_graph_mode": out.wp1_graph_mode,
                "CURRENT_CAUSAL_GRAPH_VERIFIED": wp2a.current_causal_graph_verified,
                "GLOBAL_CAUSAL_CLOSURE_PROVEN": False,
                "GHV_RUNTIME_CORRELATION": "NOT_IMPLEMENTED",
                "coverage_gap_count": len(coverage_gaps),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    out.manifest["artifact_sha256"] = _collect_hashes(output_dir)
    _write_manifest(output_dir, out.manifest)

    out.ok = matrix_status in (MATRIX_STATUS_COMPLETE, MATRIX_STATUS_PARTIAL)
    out.matrix_status = matrix_status
    out.output_dir = output_dir
    if not out.ok:
        out.failure_semantic = "MATRIX_UNAVAILABLE"
    return out


def _collect_hashes(output_dir: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(output_dir.rglob("*.json")):
        rel = path.relative_to(output_dir).as_posix()
        if path.name.startswith("."):
            continue
        hashes[rel] = _sha256_file(path)
    return hashes


def _build_manifest(
    *,
    sha: str,
    status: str,
    reasons: list[str],
    hashes: dict[str, str],
    wp1_mode: str,
    snapshot_id: str,
    gaps: list[dict[str, Any]],
    inspection_bundle: dict[str, Any] | None = None,
    integration_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    known = [g for g in gaps if g.get("KNOWN_GAP") or g.get("reason") in KNOWN_COVERAGE_GAP_IDS]
    return {
        "schema_version": MANIFEST_SCHEMA,
        "authority": MATRIX_AUTHORITY,
        "GHV_AUTHORITY": MATRIX_AUTHORITY,
        "git_sha": sha,
        "MATRIX_STATUS": status,
        "status_reasons": reasons,
        "snapshot_id": snapshot_id,
        "wp1_graph_mode": wp1_mode,
        "GLOBAL_CAUSAL_CLOSURE_PROVEN": False,
        "GLOBAL_NON_INTERFERENCE_PROVEN": False,
        "GHV_RUNTIME_CORRELATION": "NOT_IMPLEMENTED",
        "STAGE_TO_CFI_MAPPING": "UNPOPULATED",
        "artifact_sha256": hashes,
        "known_coverage_gaps": known,
        "preserved_coverage_gaps": gaps,
        "integration_manifest_summary": {
            "RUNTIME_EVIDENCE_BINDING": (integration_manifest or {}).get(
                "RUNTIME_EVIDENCE_BINDING"
            ),
            "CURRENT_CAUSAL_GRAPH_VERIFIED": (integration_manifest or {}).get(
                "CURRENT_CAUSAL_GRAPH_VERIFIED"
            ),
        },
        "inspection_authority_assessment": (inspection_bundle or {}).get("authority_assessment"),
    }


def _write_manifest(output_dir: Path, manifest: dict[str, Any]) -> None:
    (output_dir / "living_current_matrix_manifest.v1.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
