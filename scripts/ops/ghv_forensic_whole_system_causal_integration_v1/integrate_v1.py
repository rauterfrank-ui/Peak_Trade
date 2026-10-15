"""WP2-A integration orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.ops.ghv_forensic_whole_system_causal_integration_v1.constants_v1 import (
    CAUSAL_OVERLAY_SCHEMA,
    COVERAGE_GAPS_SCHEMA,
    FAILURE_AUTHORITY_BOUNDARY,
    FAILURE_CAUSAL_EDGE,
    FAILURE_OUTPUT_WRITE,
    INTEGRATED_GRAPH_SCHEMA,
    INTEGRATION_AUTHORITY,
    INTEGRATION_MANIFEST_SCHEMA,
    PROOF_CLASS_RUNTIME,
)
from scripts.ops.ghv_forensic_whole_system_causal_integration_v1.load_wp1_v1 import (
    Wp1ArtifactBundleV1,
    load_wp1_artifacts_v1,
    validate_wp1_bundle_v1,
    wp1_current_graph_verified,
)
from scripts.ops.ghv_forensic_whole_system_causal_integration_v1.runtime_evidence_v1 import (
    RuntimeEvidenceRequestV1,
    bind_runtime_evidence_v1,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.edges_v1 import assert_known_edge_type


@dataclass
class IntegrationResultV1:
    ok: bool
    failure_semantic: str | None = None
    errors: list[str] = field(default_factory=list)
    output_dir: Path | None = None
    manifest: dict[str, Any] = field(default_factory=dict)
    coverage_gaps: list[dict[str, Any]] = field(default_factory=list)
    current_causal_graph_verified: bool = False
    temporal_causality_proven: bool = False
    cross_universe_causality_proven: bool = False


def _validate_overlay_edge(edge: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    for key in (
        "SOURCE_CFI",
        "TARGET_CFI",
        "EDGE_TYPE",
        "CURRENT_EVIDENCE",
        "PROVENANCE",
        "PROOF_CLASS",
    ):
        if not edge.get(key):
            errs.append(f"overlay_missing_{key.lower()}")
    edge_type = str(edge.get("EDGE_TYPE") or "")
    try:
        assert_known_edge_type(edge_type)
    except ValueError:
        errs.append(f"unknown_overlay_edge_type:{edge_type}")
    if edge_type == "OBSERVES" and edge.get("CAUSAL_PROPAGATION_ALLOWED"):
        errs.append("observes_non_propagating")
    if edge.get("PROOF_CLASS") == PROOF_CLASS_RUNTIME and not edge.get("PROVENANCE"):
        errs.append("runtime_edge_missing_provenance")
    return errs


def run_causal_integration_v1(
    *,
    wp1_output_dir: Path,
    output_dir: Path,
    runtime_evidence: RuntimeEvidenceRequestV1 | None = None,
) -> IntegrationResultV1:
    out = IntegrationResultV1(ok=False, output_dir=output_dir)
    bundle, load_result = load_wp1_artifacts_v1(wp1_output_dir=wp1_output_dir)
    if bundle is None or not load_result.ok:
        out.failure_semantic = load_result.failure_semantic
        out.errors = load_result.errors
        return out

    validation = validate_wp1_bundle_v1(bundle)
    if not validation.ok:
        out.failure_semantic = validation.failure_semantic
        out.errors = validation.errors
        return out

    overlay_edges: list[dict[str, Any]] = []
    runtime_binding_status = "NOT_REQUESTED"
    if runtime_evidence is not None:
        code_rev = str((bundle.composed.get("code_snapshot") or {}).get("git_head") or "")
        if runtime_evidence.code_revision != code_rev:
            out.failure_semantic = FAILURE_CAUSAL_EDGE
            out.errors.append("runtime_code_revision_mismatch_with_wp1")
            return out
        if runtime_evidence.snapshot_id != bundle.snapshot_id:
            out.failure_semantic = FAILURE_CAUSAL_EDGE
            out.errors.append("runtime_snapshot_id_mismatch_with_wp1")
            return out
        rt = bind_runtime_evidence_v1(
            request=runtime_evidence,
            endpoint_cfi_by_key=validation.endpoint_index,
        )
        runtime_binding_status = rt.binding_status
        out.coverage_gaps.extend(rt.gaps)
        if not rt.ok:
            out.failure_semantic = rt.failure_semantic
            out.errors = rt.errors
            return out
        overlay_edges.extend(rt.proposed_edges)

    for edge in overlay_edges:
        edge_errs = _validate_overlay_edge(edge)
        if edge_errs:
            out.failure_semantic = FAILURE_CAUSAL_EDGE
            out.errors.extend(edge_errs)
            return out
        src = edge["SOURCE_CFI"]
        tgt = edge["TARGET_CFI"]
        if src not in validation.cfi_to_node or tgt not in validation.cfi_to_node:
            out.failure_semantic = FAILURE_AUTHORITY_BOUNDARY
            out.errors.append("overlay_endpoint_not_in_wp1_graph")
            return out

    wp1_verified = wp1_current_graph_verified(bundle)
    overlay_accepted = len(overlay_edges)
    temporal_proven = bool(
        overlay_edges
        and all(
            (e.get("temporal") or {}).get("state_owner") for e in overlay_edges if e.get("temporal")
        )
    )
    if overlay_edges and not temporal_proven:
        out.coverage_gaps.append(
            {"reason": "temporal_fields_incomplete", "TEMPORAL_CAUSALITY_PROVEN": False}
        )

    current_causal_verified = bool(wp1_verified)
    if bundle.graph_mode == "NAVIGATION_ONLY":
        current_causal_verified = False

    overlay_doc = {
        "schema_version": CAUSAL_OVERLAY_SCHEMA,
        "authority": INTEGRATION_AUTHORITY,
        "snapshot_id": bundle.snapshot_id,
        "wp1_graph_mode": bundle.graph_mode,
        "wp1_current_graph_verified": wp1_verified,
        "overlay_edges": overlay_edges,
        "RUNTIME_EVIDENCE_BINDING": runtime_binding_status,
    }

    integrated = {
        "schema_version": INTEGRATED_GRAPH_SCHEMA,
        "authority": INTEGRATION_AUTHORITY,
        "snapshot_id": bundle.snapshot_id,
        "wp1_graph_authority": bundle.graph_authority,
        "CURRENT_CAUSAL_GRAPH_VERIFIED": current_causal_verified,
        "TEMPORAL_CAUSALITY_PROVEN": temporal_proven,
        "CROSS_UNIVERSE_CAUSALITY_PROVEN": False,
        "GLOBAL_CAUSAL_CLOSURE_PROVEN": False,
        "code_snapshot": bundle.composed.get("code_snapshot"),
        "evidence_snapshot": bundle.composed.get("evidence_snapshot"),
        "nodes": bundle.composed.get("nodes"),
        "edges": list(bundle.composed.get("edges") or []) + overlay_edges,
        "wp1_edge_count": len(bundle.composed.get("edges") or []),
        "overlay_edge_count": len(overlay_edges),
    }

    gaps_doc = {
        "schema_version": COVERAGE_GAPS_SCHEMA,
        "gaps": out.coverage_gaps,
        "wp1_unresolved_edges": bundle.composed.get("unresolved_edges") or [],
        "wp1_excluded_count": len(bundle.excluded.get("excluded") or []),
    }

    manifest = {
        "schema_version": INTEGRATION_MANIFEST_SCHEMA,
        "authority": INTEGRATION_AUTHORITY,
        "snapshot_id": bundle.snapshot_id,
        "wp1_output_dir": str(wp1_output_dir.resolve()),
        "CURRENT_CAUSAL_GRAPH_VERIFIED": current_causal_verified,
        "TEMPORAL_CAUSALITY_PROVEN": temporal_proven,
        "CROSS_UNIVERSE_CAUSALITY_PROVEN": False,
        "GLOBAL_CAUSAL_CLOSURE_PROVEN": False,
        "GLOBAL_NON_INTERFERENCE_PROVEN": False,
        "overlay_edge_count": len(overlay_edges),
        "RUNTIME_EVIDENCE_BINDING": runtime_binding_status,
    }

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "causal_overlay.v1.json").write_text(
            json.dumps(overlay_doc, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (output_dir / "integrated_causal_graph.v1.json").write_text(
            json.dumps(integrated, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (output_dir / "causal_coverage_gaps.v1.json").write_text(
            json.dumps(gaps_doc, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (output_dir / "causal_integration_manifest.v1.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        out.failure_semantic = FAILURE_OUTPUT_WRITE
        out.errors.append(f"output_write_failed:{exc}")
        return out

    out.ok = True
    out.manifest = manifest
    out.current_causal_graph_verified = current_causal_verified
    out.temporal_causality_proven = temporal_proven
    out.cross_universe_causality_proven = False
    return out
