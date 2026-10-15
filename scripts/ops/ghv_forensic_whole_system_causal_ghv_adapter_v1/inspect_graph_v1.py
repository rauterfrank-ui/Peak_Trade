"""Validate and inspect WP2-A integrated causal graph artifacts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.ops.ghv_forensic_whole_system_causal_integration_v1.constants_v1 import (
    ALLOWED_CURRENT_RELEVANCE,
    FORBIDDEN_CURRENT_RELEVANCE,
)
from scripts.ops.ghv_forensic_whole_system_causal_ghv_adapter_v1.contracts_v1 import (
    ADAPTER_AUTHORITY,
    AUTHORITY_BOUNDARY_FAILURE,
    EXPECTED_INTEGRATED_AUTHORITY,
    EXPECTED_SCHEMAS,
    HISTORICAL_CONTAMINATION,
    IDENTITY_BINDING_FAILURE,
    INSUFFICIENT_CAUSAL_EVIDENCE,
    INVALID_INPUT,
    PROVENANCE_FAILURE,
    SNAPSHOT_BINDING_FAILURE,
    UNSAFE_OUTPUT_PATH,
)
from scripts.ops.ghv_forensic_whole_system_causal_ghv_adapter_v1.load_integrated_graph_v1 import (
    Wp2aArtifactBundleV1,
    load_wp2a_artifacts_v1,
)
from scripts.ops.ghv_forensic_whole_system_causal_ghv_adapter_v1.types_v1 import (
    InspectionResultV1,
)


def _is_overlay_edge(edge: dict[str, Any]) -> bool:
    return "SOURCE_CFI" in edge and "TARGET_CFI" in edge


def _overlay_edge_binding_digest(edge: dict[str, Any]) -> str:
    """Canonical overlay identity per WP2-A overlay edge fields (integrate_v1._validate_overlay_edge)."""
    payload: dict[str, Any] = {}
    for key in (
        "SOURCE_CFI",
        "TARGET_CFI",
        "EDGE_TYPE",
        "CURRENT_EVIDENCE",
        "PROOF_CLASS",
        "CAUSAL_PROPAGATION_ALLOWED",
        "temporal",
        "PROVENANCE",
    ):
        if key in edge:
            payload[key] = edge[key]
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _overlay_edge_multiset(edges: list[dict[str, Any]]) -> Counter[str]:
    return Counter(_overlay_edge_binding_digest(e) for e in edges if isinstance(e, dict))


def _assert_wp1_current_relevance(
    result: InspectionResultV1,
    *,
    kind: str,
    entity_id: str,
    rel: Any,
) -> InspectionResultV1 | None:
    """Mirror WP2-A load_wp1_v1 current_relevance fail-closed semantics."""
    if not isinstance(rel, dict):
        return _fail(
            result,
            HISTORICAL_CONTAMINATION,
            f"missing_{kind}_current_relevance:{entity_id}",
        )
    state = rel.get("CURRENT_RELEVANCE_STATE")
    if state in FORBIDDEN_CURRENT_RELEVANCE:
        return _fail(
            result,
            HISTORICAL_CONTAMINATION,
            f"forbidden_{kind}_relevance:{entity_id}:{state}",
        )
    if state not in ALLOWED_CURRENT_RELEVANCE:
        return _fail(
            result,
            HISTORICAL_CONTAMINATION,
            f"invalid_{kind}_relevance:{entity_id}:{state}",
        )
    if state == "CURRENT_CONDITIONAL" and not rel.get("ACTIVATION_CONDITION"):
        return _fail(
            result,
            HISTORICAL_CONTAMINATION,
            f"conditional_{kind}_missing_activation:{entity_id}",
        )
    return None


def _fail(result: InspectionResultV1, semantic: str, msg: str) -> InspectionResultV1:
    result.ok = False
    result.failure_semantic = semantic
    result.errors.append(msg)
    return result


def validate_wp2a_bundle_v1(bundle: Wp2aArtifactBundleV1) -> InspectionResultV1:
    out = InspectionResultV1(ok=False)
    integrated = bundle.integrated
    manifest = bundle.manifest
    gaps = bundle.gaps
    overlay = bundle.overlay

    if integrated.get("schema_version") != EXPECTED_SCHEMAS["integrated"]:
        return _fail(out, INVALID_INPUT, "integrated_schema_version_mismatch")
    if manifest.get("schema_version") != EXPECTED_SCHEMAS["manifest"]:
        return _fail(out, INVALID_INPUT, "manifest_schema_version_mismatch")
    if gaps.get("schema_version") != EXPECTED_SCHEMAS["gaps"]:
        return _fail(out, INVALID_INPUT, "gaps_schema_version_mismatch")
    if overlay.get("schema_version") != EXPECTED_SCHEMAS["overlay"]:
        return _fail(out, INVALID_INPUT, "overlay_schema_version_mismatch")

    for label, doc in (
        ("integrated", integrated),
        ("manifest", manifest),
        ("overlay", overlay),
    ):
        if doc.get("authority") != EXPECTED_INTEGRATED_AUTHORITY:
            return _fail(
                out,
                AUTHORITY_BOUNDARY_FAILURE,
                f"{label}_authority_must_be_NONE",
            )

    snap_i = str(integrated.get("snapshot_id") or "")
    snap_m = str(manifest.get("snapshot_id") or "")
    snap_o = str(overlay.get("snapshot_id") or "")
    if not snap_i:
        return _fail(out, SNAPSHOT_BINDING_FAILURE, "integrated_missing_snapshot_id")
    if snap_m != snap_i or snap_o != snap_i:
        return _fail(out, SNAPSHOT_BINDING_FAILURE, "snapshot_id_cross_artifact_mismatch")

    for flag in (
        "CURRENT_CAUSAL_GRAPH_VERIFIED",
        "TEMPORAL_CAUSALITY_PROVEN",
        "CROSS_UNIVERSE_CAUSALITY_PROVEN",
        "GLOBAL_CAUSAL_CLOSURE_PROVEN",
    ):
        if integrated.get(flag) != manifest.get(flag):
            return _fail(out, SNAPSHOT_BINDING_FAILURE, f"manifest_integrated_{flag}_mismatch")

    if manifest.get("GLOBAL_NON_INTERFERENCE_PROVEN") is not False:
        return _fail(out, AUTHORITY_BOUNDARY_FAILURE, "global_non_interference_must_be_false")
    if integrated.get("GLOBAL_CAUSAL_CLOSURE_PROVEN") is not False:
        return _fail(out, AUTHORITY_BOUNDARY_FAILURE, "global_causal_closure_must_be_false")

    wp1_mode_overlay = str(overlay.get("wp1_graph_mode") or "")
    wp1_mode_integrated = str(integrated.get("wp1_graph_authority") or "")
    if wp1_mode_overlay and wp1_mode_integrated and wp1_mode_overlay != wp1_mode_integrated:
        return _fail(
            out,
            SNAPSHOT_BINDING_FAILURE,
            "wp1_graph_mode_authority_cross_artifact_mismatch",
        )
    wp1_mode = wp1_mode_integrated or wp1_mode_overlay
    if wp1_mode == "NAVIGATION_ONLY" and integrated.get("CURRENT_CAUSAL_GRAPH_VERIFIED"):
        return _fail(
            out,
            AUTHORITY_BOUNDARY_FAILURE,
            "navigation_only_cannot_be_current_causal_verified",
        )

    overlay_count_manifest = int(manifest.get("overlay_edge_count") or 0)
    overlay_count_integrated = int(integrated.get("overlay_edge_count") or 0)
    overlay_edges_list = overlay.get("overlay_edges") or []
    if not isinstance(overlay_edges_list, list):
        return _fail(out, INVALID_INPUT, "overlay_edges_not_list")
    if len(overlay_edges_list) != overlay_count_manifest:
        return _fail(out, INVALID_INPUT, "overlay_file_count_manifest_mismatch")
    if overlay_count_integrated != overlay_count_manifest:
        return _fail(out, INVALID_INPUT, "overlay_count_integrated_manifest_mismatch")

    nodes = integrated.get("nodes") or []
    edges = integrated.get("edges") or []
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return _fail(out, INVALID_INPUT, "nodes_or_edges_not_list")

    cfi_set: set[str] = set()
    endpoint_index: dict[tuple[str, str], str] = {}
    node_inventory: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            return _fail(out, INVALID_INPUT, "invalid_node_record")
        cfi = node.get("canonical_id")
        if not cfi or not isinstance(cfi, str):
            return _fail(out, IDENTITY_BINDING_FAILURE, "node_missing_canonical_id")
        if cfi in cfi_set:
            return _fail(out, IDENTITY_BINDING_FAILURE, f"duplicate_canonical_id:{cfi}")
        cfi_set.add(cfi)
        rel_err = _assert_wp1_current_relevance(
            out, kind="node", entity_id=cfi, rel=node.get("current_relevance")
        )
        if rel_err is not None:
            return rel_err
        rel = node.get("current_relevance") or {}
        state = rel.get("CURRENT_RELEVANCE_STATE")
        if not node.get("provenance"):
            return _fail(out, PROVENANCE_FAILURE, f"node_missing_provenance:{cfi}")
        sys_name = str(node.get("source_system") or "")
        native = str(node.get("source_native_id") or "")
        if sys_name and native:
            endpoint_index[(sys_name, native)] = cfi
        node_inventory.append(
            {
                "canonical_id": cfi,
                "entity_type": node.get("entity_type"),
                "current_relevance_state": state,
                "source_system": sys_name,
                "source_native_id": native,
            }
        )

    wp1_edge_count = int(integrated.get("wp1_edge_count") or 0)
    overlay_in_edges = 0
    integrated_overlay_edges: list[dict[str, Any]] = []
    edge_inventory: list[dict[str, Any]] = []
    for edge in edges:
        if not isinstance(edge, dict):
            return _fail(out, INVALID_INPUT, "invalid_edge_record")
        if _is_overlay_edge(edge):
            overlay_in_edges += 1
            integrated_overlay_edges.append(edge)
            src = edge.get("SOURCE_CFI")
            tgt = edge.get("TARGET_CFI")
            if not src or not tgt:
                return _fail(out, IDENTITY_BINDING_FAILURE, "overlay_missing_cfi_endpoint")
            if src not in cfi_set or tgt not in cfi_set:
                return _fail(out, IDENTITY_BINDING_FAILURE, "overlay_endpoint_not_in_node_set")
            if not edge.get("PROVENANCE"):
                return _fail(out, PROVENANCE_FAILURE, "overlay_missing_provenance")
            edge_inventory.append(
                {
                    "kind": "OVERLAY",
                    "source_cfi": src,
                    "target_cfi": tgt,
                    "edge_type": edge.get("EDGE_TYPE"),
                    "proof_class": edge.get("PROOF_CLASS"),
                }
            )
            continue
        eid = str(edge.get("edge_id") or "unknown")
        rel_err = _assert_wp1_current_relevance(
            out, kind="edge", entity_id=eid, rel=edge.get("current_relevance")
        )
        if rel_err is not None:
            return rel_err
        sys_name = str(edge.get("source_system") or "")
        src_n = str(edge.get("source_native_id") or "")
        tgt_n = str(edge.get("target_native_id") or "")
        if not endpoint_index.get((sys_name, src_n)) or not endpoint_index.get((sys_name, tgt_n)):
            return _fail(
                out, IDENTITY_BINDING_FAILURE, f"wp1_edge_unresolved_endpoint:{edge.get('edge_id')}"
            )
        if not edge.get("provenance"):
            return _fail(
                out, PROVENANCE_FAILURE, f"wp1_edge_missing_provenance:{edge.get('edge_id')}"
            )
        typed = edge.get("typed_edge") or {}
        if typed.get("trading_authority_implied"):
            return _fail(out, AUTHORITY_BOUNDARY_FAILURE, "trading_authority_implied_on_edge")
        edge_inventory.append(
            {
                "kind": "WP1",
                "edge_id": edge.get("edge_id"),
                "edge_type": typed.get("edge_type"),
                "causal_propagation_allowed": typed.get("causal_propagation_allowed"),
            }
        )

    if overlay_in_edges != overlay_count_integrated:
        return _fail(out, INVALID_INPUT, "integrated_edges_overlay_count_mismatch")
    if len(edges) != wp1_edge_count + overlay_in_edges:
        return _fail(out, INVALID_INPUT, "integrated_edge_total_count_mismatch")

    overlay_file_records = [e for e in overlay_edges_list if isinstance(e, dict)]
    if _overlay_edge_multiset(overlay_file_records) != _overlay_edge_multiset(
        integrated_overlay_edges
    ):
        return _fail(out, IDENTITY_BINDING_FAILURE, "overlay_file_integrated_edge_binding_mismatch")

    temporal_proven = bool(integrated.get("TEMPORAL_CAUSALITY_PROVEN"))
    if temporal_proven:
        if not integrated_overlay_edges:
            return _fail(out, INSUFFICIENT_CAUSAL_EVIDENCE, "temporal_proven_without_overlay_edges")
        for oe in integrated_overlay_edges:
            temporal = oe.get("temporal")
            if not isinstance(temporal, dict) or not str(temporal.get("state_owner") or "").strip():
                return _fail(
                    out, INSUFFICIENT_CAUSAL_EVIDENCE, "temporal_proven_but_state_owner_missing"
                )

    structural_valid = bool(nodes) and all(
        not _is_overlay_edge(e) or e.get("SOURCE_CFI") in cfi_set
        for e in edges
        if isinstance(e, dict)
    )

    out.ok = True
    out.failure_semantic = None
    out.bundle_doc = {
        "schema_version": "ghv_cfi_graph_inspection_bundle.v1",
        "authority": ADAPTER_AUTHORITY,
        "GHV_AUTHORITY": ADAPTER_AUTHORITY,
        "PRODUCTIVE_TRADING_AUTHORITY": False,
        "snapshot_id": snap_i,
        "wp1_graph_mode": wp1_mode,
        "input_artifact_sha256": dict(sorted(bundle.artifact_sha256.items())),
        "authority_assessment": {
            "CURRENT_CAUSAL_GRAPH_VERIFIED": bool(integrated.get("CURRENT_CAUSAL_GRAPH_VERIFIED")),
            "TEMPORAL_CAUSALITY_PROVEN": temporal_proven,
            "GLOBAL_CAUSAL_CLOSURE_PROVEN": False,
            "GLOBAL_NON_INTERFERENCE_PROVEN": False,
            "CAUSAL_ANALYSIS_COMPLETE": False,
        },
        "semantic_assessment": {
            "STRUCTURAL_GRAPH_VALIDITY": structural_valid,
            "OBSERVATION_RELATION": any(
                (e.get("typed_edge") or {}).get("edge_type") == "OBSERVES"
                for e in edges
                if isinstance(e, dict) and not _is_overlay_edge(e)
            ),
            "EVIDENCE_FLOW": overlay_in_edges > 0,
            "TEMPORAL_ORDERING": temporal_proven,
            "CAUSAL_DEPENDENCY": False,
            "PROVEN_CAUSAL_EFFECT": False,
        },
        "canonical_node_inventory": sorted(node_inventory, key=lambda x: x["canonical_id"]),
        "typed_edge_inventory": sorted(
            edge_inventory,
            key=lambda x: (x.get("kind", ""), x.get("edge_id") or x.get("source_cfi") or ""),
        ),
        "runtime_context_assessment": {
            "RUNTIME_EVIDENCE_BINDING": manifest.get("RUNTIME_EVIDENCE_BINDING"),
            "code_snapshot": integrated.get("code_snapshot"),
            "evidence_snapshot": integrated.get("evidence_snapshot"),
        },
        "preserved_coverage_gaps": gaps.get("gaps") or [],
        "wp1_unresolved_edges": gaps.get("wp1_unresolved_edges") or [],
        "limitations": [
            "Adapter does not correlate GHV runtime stages.",
            "Adapter does not prove whole-system causal closure.",
            "Structural validity does not imply productive causal effect.",
        ],
    }
    return out


def assert_safe_output_dir(*, output_dir: Path, repo_root: Path) -> InspectionResultV1:
    out = InspectionResultV1(ok=False)
    try:
        resolved = output_dir.resolve()
        repo = repo_root.resolve()
        if resolved == repo or repo in resolved.parents:
            return _fail(out, UNSAFE_OUTPUT_PATH, "output_dir_must_not_be_inside_repository")
    except OSError as exc:
        return _fail(out, INVALID_INPUT, f"output_path_resolve_failed:{exc}")
    out.ok = True
    return out


def run_offline_graph_inspection_v1(
    *,
    wp2a_output_dir: Path,
    output_dir: Path,
    repo_root: Path,
) -> InspectionResultV1:
    safe = assert_safe_output_dir(output_dir=output_dir, repo_root=repo_root)
    if not safe.ok:
        return safe

    loaded = load_wp2a_artifacts_v1(wp2a_output_dir=wp2a_output_dir)
    if not loaded.ok or loaded.bundle is None:
        return InspectionResultV1(
            ok=False,
            failure_semantic=loaded.failure_semantic,
            errors=loaded.errors,
        )

    inspected = validate_wp2a_bundle_v1(loaded.bundle)
    if not inspected.ok:
        return inspected

    from scripts.ops.ghv_forensic_whole_system_causal_ghv_adapter_v1.emit_bundle_v1 import (
        emit_inspection_bundle_v1,
    )

    return emit_inspection_bundle_v1(
        inspection=inspected,
        wp2a_output_dir=wp2a_output_dir,
        output_dir=output_dir,
    )
