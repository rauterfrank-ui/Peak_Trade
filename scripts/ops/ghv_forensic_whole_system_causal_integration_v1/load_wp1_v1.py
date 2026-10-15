"""Read-only WP1 crosswalk artifact loader and validator."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.ops.ghv_forensic_whole_system_causal_integration_v1.constants_v1 import (
    ALLOWED_CURRENT_RELEVANCE,
    COMPOSED_GRAPH_SCHEMA,
    FAILURE_CURRENT_RELEVANCE,
    FAILURE_IDENTITY_BINDING,
    FAILURE_INPUT_VALIDATION,
    FAILURE_SNAPSHOT_BINDING,
    MANIFEST_SCHEMA,
    WP1_ARTIFACT_NAMES,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.constants_v1 import (
    CROSSWALK_AUTHORITY,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.edges_v1 import assert_known_edge_type


@dataclass
class Wp1ArtifactBundleV1:
    output_dir: Path
    composed: dict[str, Any]
    manifest: dict[str, Any]
    coverage: dict[str, Any]
    ambiguity: dict[str, Any]
    excluded: dict[str, Any]
    snapshot_id: str
    graph_mode: str
    graph_authority: str


@dataclass
class Wp1ValidationResultV1:
    ok: bool
    failure_semantic: str | None = None
    errors: list[str] = field(default_factory=list)
    endpoint_index: dict[tuple[str, str], str] = field(default_factory=dict)
    cfi_to_node: dict[str, dict[str, Any]] = field(default_factory=dict)


def _read_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"expected_object:{path.name}")
    return raw


def load_wp1_artifacts_v1(
    *, wp1_output_dir: Path
) -> tuple[Wp1ArtifactBundleV1 | None, Wp1ValidationResultV1]:
    result = Wp1ValidationResultV1(ok=False)
    if not wp1_output_dir.is_dir():
        result.failure_semantic = FAILURE_INPUT_VALIDATION
        result.errors.append(f"missing_wp1_output_dir:{wp1_output_dir}")
        return None, result

    missing = [name for name in WP1_ARTIFACT_NAMES if not (wp1_output_dir / name).is_file()]
    if missing:
        result.failure_semantic = FAILURE_INPUT_VALIDATION
        result.errors.append(f"missing_required_artifacts:{','.join(missing)}")
        return None, result

    try:
        composed = _read_json(wp1_output_dir / "composed_forensic_graph.v1.json")
        manifest = _read_json(wp1_output_dir / "crosswalk_manifest.v1.json")
        coverage = _read_json(wp1_output_dir / "coverage_report.v1.json")
        ambiguity = _read_json(wp1_output_dir / "ambiguity_report.v1.json")
        excluded = _read_json(wp1_output_dir / "excluded_non_current_report.v1.json")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result.failure_semantic = FAILURE_INPUT_VALIDATION
        result.errors.append(f"artifact_parse_error:{exc}")
        return None, result

    bundle = Wp1ArtifactBundleV1(
        output_dir=wp1_output_dir,
        composed=composed,
        manifest=manifest,
        coverage=coverage,
        ambiguity=ambiguity,
        excluded=excluded,
        snapshot_id=str(composed.get("snapshot_id") or ""),
        graph_mode=str(composed.get("GRAPH_MODE") or coverage.get("GRAPH_MODE") or ""),
        graph_authority=str(
            composed.get("GRAPH_AUTHORITY") or coverage.get("GRAPH_AUTHORITY") or ""
        ),
    )
    validation = validate_wp1_bundle_v1(bundle)
    if not validation.ok:
        return bundle, validation
    return bundle, validation


def validate_wp1_bundle_v1(bundle: Wp1ArtifactBundleV1) -> Wp1ValidationResultV1:
    result = Wp1ValidationResultV1(ok=False)
    c = bundle.composed
    m = bundle.manifest
    cov = bundle.coverage
    ex = bundle.excluded

    if c.get("schema_version") != COMPOSED_GRAPH_SCHEMA:
        result.failure_semantic = FAILURE_INPUT_VALIDATION
        result.errors.append("composed_schema_version_mismatch")
        return result
    if m.get("schema_version") != MANIFEST_SCHEMA:
        result.failure_semantic = FAILURE_INPUT_VALIDATION
        result.errors.append("manifest_schema_version_mismatch")
        return result
    if c.get("authority") != CROSSWALK_AUTHORITY:
        result.failure_semantic = FAILURE_INPUT_VALIDATION
        result.errors.append("composed_authority_must_be_NONE")

    snap = str(c.get("snapshot_id") or "")
    if not snap:
        result.failure_semantic = FAILURE_SNAPSHOT_BINDING
        result.errors.append("missing_snapshot_id_in_composed")
        return result
    if str(m.get("snapshot_id") or "") != snap:
        result.failure_semantic = FAILURE_SNAPSHOT_BINDING
        result.errors.append("manifest_snapshot_id_mismatch")
        return result

    hist_e = int(
        ex.get("historical_entities_ingested") or cov.get("HISTORICAL_ENTITIES_INGESTED") or 0
    )
    hist_ed = int(ex.get("historical_edges_ingested") or cov.get("HISTORICAL_EDGES_INGESTED") or 0)
    if hist_e or hist_ed:
        result.failure_semantic = FAILURE_CURRENT_RELEVANCE
        result.errors.append("historical_ingestion_nonzero")
        return result

    nodes = c.get("nodes") or []
    edges = c.get("edges") or []
    if not isinstance(nodes, list) or not isinstance(edges, list):
        result.failure_semantic = FAILURE_INPUT_VALIDATION
        result.errors.append("nodes_or_edges_not_list")
        return result

    for node in nodes:
        if not isinstance(node, dict):
            result.failure_semantic = FAILURE_INPUT_VALIDATION
            result.errors.append("invalid_node_record")
            return result
        cfi = node.get("canonical_id")
        if not cfi or not isinstance(cfi, str):
            result.failure_semantic = FAILURE_IDENTITY_BINDING
            result.errors.append("node_missing_canonical_id")
            return result
        rel = node.get("current_relevance") or {}
        state = rel.get("CURRENT_RELEVANCE_STATE")
        if state in ("UNKNOWN", "NON_CURRENT", "HISTORICAL"):
            result.failure_semantic = FAILURE_CURRENT_RELEVANCE
            result.errors.append(f"forbidden_node_relevance:{cfi}:{state}")
            return result
        if state not in ALLOWED_CURRENT_RELEVANCE:
            result.failure_semantic = FAILURE_CURRENT_RELEVANCE
            result.errors.append(f"unknown_node_relevance:{cfi}:{state}")
            return result
        if state == "CURRENT_CONDITIONAL" and not rel.get("ACTIVATION_CONDITION"):
            result.failure_semantic = FAILURE_CURRENT_RELEVANCE
            result.errors.append(f"conditional_missing_activation:{cfi}")
            return result
        if not node.get("provenance"):
            result.failure_semantic = FAILURE_INPUT_VALIDATION
            result.errors.append(f"node_missing_provenance:{cfi}")
            return result
        sys_name = str(node.get("source_system") or "")
        native = str(node.get("source_native_id") or "")
        if sys_name and native:
            result.endpoint_index[(sys_name, native)] = cfi
        result.cfi_to_node[cfi] = node

    for edge in edges:
        if not isinstance(edge, dict):
            result.failure_semantic = FAILURE_INPUT_VALIDATION
            result.errors.append("invalid_edge_record")
            return result
        rel = edge.get("current_relevance") or {}
        state = rel.get("CURRENT_RELEVANCE_STATE")
        if state not in ALLOWED_CURRENT_RELEVANCE:
            result.failure_semantic = FAILURE_CURRENT_RELEVANCE
            result.errors.append(f"forbidden_edge_relevance:{edge.get('edge_id')}:{state}")
            return result
        typed = edge.get("typed_edge") or {}
        edge_type = typed.get("edge_type")
        if not edge_type:
            result.failure_semantic = FAILURE_INPUT_VALIDATION
            result.errors.append(f"edge_missing_type:{edge.get('edge_id')}")
            return result
        try:
            assert_known_edge_type(str(edge_type))
        except ValueError:
            result.failure_semantic = FAILURE_INPUT_VALIDATION
            result.errors.append(f"unknown_edge_type:{edge_type}")
            return result
        if typed.get("trading_authority_implied"):
            result.failure_semantic = FAILURE_AUTHORITY_BOUNDARY
            result.errors.append("trading_authority_implied_must_be_false")
            return result
        sys_name = str(edge.get("source_system") or "")
        src_native = str(edge.get("source_native_id") or "")
        tgt_native = str(edge.get("target_native_id") or "")
        if not result.endpoint_index.get((sys_name, src_native)):
            result.failure_semantic = FAILURE_IDENTITY_BINDING
            result.errors.append(f"unresolved_edge_source:{edge.get('edge_id')}:{src_native}")
            return result
        if not result.endpoint_index.get((sys_name, tgt_native)):
            result.failure_semantic = FAILURE_IDENTITY_BINDING
            result.errors.append(f"unresolved_edge_target:{edge.get('edge_id')}:{tgt_native}")
            return result
        if edge_type == "OBSERVES" and typed.get("causal_propagation_allowed"):
            result.failure_semantic = FAILURE_AUTHORITY_BOUNDARY
            result.errors.append("observes_must_not_propagate")
            return result

    if bundle.ambiguity.get("collisions"):
        result.failure_semantic = FAILURE_IDENTITY_BINDING
        result.errors.append("wp1_collisions_present")
        return result

    result.ok = True
    result.failure_semantic = None
    return result


def wp1_current_graph_verified(bundle: Wp1ArtifactBundleV1) -> bool:
    c = bundle.composed
    if bundle.graph_mode == "NAVIGATION_ONLY":
        return False
    return bool(c.get("CURRENT_GRAPH_VERIFIED") and c.get("CURRENT_ONLY_GRAPH"))
