"""Forensic crosswalk composition pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.constants_v1 import (
    COMPOSED_GRAPH_SCHEMA,
    CROSSWALK_AUTHORITY,
    MANIFEST_SCHEMA,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.edges_v1 import (
    atlas_relation_to_typed_edge,
    census_flow_to_typed_edge,
    edge_semantics_flags,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.filter_current_v1 import (
    CurrentRelevanceState,
    build_census_anchor_index,
    classify_atlas_entity,
    classify_atlas_relation,
    classify_census_edge,
    classify_census_object,
    classify_landscape_surface,
    exclusion_reason_from_verdict,
    verdict_includable_in_graph,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.identity_v1 import (
    ProvenanceRecordV1,
    build_cfi_v1,
    snapshot_id_from_bindings,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.load_sources_v1 import (
    load_sources_v1,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.snapshot_v1 import (
    build_code_snapshot_v1,
    build_evidence_snapshot_v1,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.graph_mode_v1 import (
    GraphMode,
    build_graph_authority_coverage,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.snapshot_drift_report_v1 import (
    build_snapshot_drift_report_v1,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.source_validation_v1 import (
    validate_sources_v1,
)


@dataclass
class CrosswalkResultV1:
    ok: bool
    snapshot_id: str
    nodes: list[dict[str, Any]] = field(default_factory=list)
    edges: list[dict[str, Any]] = field(default_factory=list)
    unresolved_edges: list[dict[str, Any]] = field(default_factory=list)
    collisions: list[dict[str, Any]] = field(default_factory=list)
    ambiguous: list[dict[str, Any]] = field(default_factory=list)
    excluded: list[dict[str, Any]] = field(default_factory=list)
    coverage: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    _seen_cfi: dict[str, str] = field(default_factory=dict)


def _provenance(
    *,
    tool: str,
    artifact: str,
    revision: str,
    code_revision: str,
    native_id: str,
    canonical_id: str,
    evidence_type: str,
    proof_class: str = "CONTRACT_CONFIRMED",
    observed: str = "OBSERVED",
    validation: str = "PASS",
    limitations: tuple[str, ...] = (),
    activation_conditions: tuple[str, ...] = (),
) -> dict[str, Any]:
    return ProvenanceRecordV1(
        source_tool=tool,
        source_artifact=artifact,
        source_revision=revision,
        code_revision=code_revision,
        native_id=native_id,
        canonical_id=canonical_id,
        evidence_type=evidence_type,
        proof_class=proof_class,
        observed_or_inferred=observed,
        activation_conditions=activation_conditions,
        validation_status=validation,
        limitations=limitations,
    ).to_dict()


def _add_node(
    result: CrosswalkResultV1,
    *,
    entity_type: str,
    source_system: str,
    native_id: str,
    snapshot_id: str,
    code_revision: str,
    artifact: str,
    revision: str,
    evidence_type: str,
    metadata: dict[str, Any],
    current_relevance: dict[str, Any],
) -> str | None:
    cfi = build_cfi_v1(
        entity_type=entity_type,
        snapshot_id=snapshot_id,
        source_system=source_system,
        source_native_id=native_id,
    )
    if cfi in result._seen_cfi:
        if result._seen_cfi[cfi] != entity_type:
            result.collisions.append(
                {
                    "canonical_id": cfi,
                    "entity_type_a": result._seen_cfi[cfi],
                    "entity_type_b": entity_type,
                }
            )
            return None
        return cfi
    result._seen_cfi[cfi] = entity_type
    act = current_relevance.get("ACTIVATION_CONDITION")
    result.nodes.append(
        {
            "canonical_id": cfi,
            "entity_type": entity_type,
            "source_system": source_system,
            "source_native_id": native_id,
            "metadata": metadata,
            "current_relevance": current_relevance,
            "provenance": _provenance(
                tool="ghv_forensic_whole_system_crosswalk_v1",
                artifact=artifact,
                revision=revision,
                code_revision=code_revision,
                native_id=native_id,
                canonical_id=cfi,
                evidence_type=evidence_type,
                activation_conditions=((act,) if act else ()),
            ),
        }
    )
    return cfi


def _apply_explicit_rules(
    result: CrosswalkResultV1,
    rules: dict[str, Any],
) -> None:
    for rule in rules.get("rules") or []:
        if rule.get("VALIDATION_STATUS") != "APPROVED":
            result.ambiguous.append({"rule": rule, "reason": "rule_not_approved"})
            continue
        if not rule.get("CONTRACT_JUSTIFICATION"):
            result.ambiguous.append({"rule": rule, "reason": "missing_contract_justification"})
            continue
        result.coverage.setdefault("explicit_rules_applied", []).append(rule.get("SOURCE_ID"))


def _write_outputs(
    *,
    output_dir: Path,
    result: CrosswalkResultV1,
    composed: dict[str, Any],
    manifest: dict[str, Any],
    excluded_report: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "composed_forensic_graph.v1.json").write_text(
        json.dumps(composed, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "crosswalk_manifest.v1.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "coverage_report.v1.json").write_text(
        json.dumps(result.coverage, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "ambiguity_report.v1.json").write_text(
        json.dumps(
            {
                "collisions": result.collisions,
                "ambiguous": result.ambiguous,
                "unresolved_edges": result.unresolved_edges,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "excluded_non_current_report.v1.json").write_text(
        json.dumps(excluded_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_forensic_crosswalk_v1(
    *,
    repo_root: Path,
    output_dir: Path,
    rules_path: Path,
    evidence_root: Path | None = None,
    include_atlas: bool = True,
    strict_repo_invariants: bool = True,
    graph_mode: GraphMode = GraphMode.STRICT_CURRENT,
    pt_launcher: Path | None = None,
) -> CrosswalkResultV1:
    output_dir.mkdir(parents=True, exist_ok=True)
    sources = load_sources_v1(repo_root=repo_root, rules_path=rules_path)
    code_snap = build_code_snapshot_v1(
        repo_root=repo_root,
        census_doc=sources.census,
        landscape_doc=sources.landscape,
        atlas_meta=sources.atlas_meta,
    )
    evidence_snap = build_evidence_snapshot_v1(evidence_root=evidence_root)
    snapshot_id = snapshot_id_from_bindings(code_snap.bindings_for_snapshot_id())

    result = CrosswalkResultV1(ok=True, snapshot_id=snapshot_id)
    code_rev = code_snap.git_head
    pt = pt_launcher or (repo_root / "scripts/pt")

    drift_report = build_snapshot_drift_report_v1(
        repo_root=repo_root,
        git_head=code_rev,
        census_baseline=str(sources.census.get("source_baseline_head") or ""),
        landscape_baseline=str(
            sources.landscape.get("evidence_baseline_sha")
            or sources.landscape.get("universe_map_consolidation_v1", {}).get(
                "consolidation_baseline_sha", ""
            )
            or ""
        ),
    )

    validation = validate_sources_v1(
        repo_root=repo_root,
        census_doc=sources.census,
        landscape_doc=sources.landscape,
        git_head=code_rev,
        strict_repo_invariants=strict_repo_invariants,
        pt_launcher=pt if strict_repo_invariants else None,
    )
    snapshot_binding_verified = len(validation.snapshot_errors) == 0
    if graph_mode == GraphMode.NAVIGATION_ONLY:
        validation.snapshot_errors = []
        validation.ok = (
            not validation.census_errors
            and not validation.landscape_errors
            and validation.every_required_validator_executed_and_passed
        )
        snapshot_binding_verified = False

    if graph_mode == GraphMode.STRICT_CURRENT and validation.snapshot_errors:
        validation.ok = False

    if not validation.ok:
        result.ok = False
        result.errors = validation.all_errors()
    validation_contract_ok = (
        validation.ok and validation.every_required_validator_executed_and_passed
    )

    counts = {
        "CURRENT_ENTITIES_INCLUDED": 0,
        "CURRENT_EDGES_INCLUDED": 0,
        "NON_CURRENT_ENTITIES_EXCLUDED": 0,
        "NON_CURRENT_EDGES_EXCLUDED": 0,
        "UNKNOWN_ENTITIES_EXCLUDED": 0,
        "UNKNOWN_EDGES_EXCLUDED": 0,
        "HISTORICAL_ENTITIES_INGESTED": 0,
        "HISTORICAL_EDGES_INGESTED": 0,
    }

    if not validation.ok:
        authority = build_graph_authority_coverage(
            graph_mode=graph_mode,
            source_validation_pass=validation_contract_ok,
            snapshot_binding_verified=snapshot_binding_verified,
            current_only_filter_applied=False,
            current_graph_verified=False,
        )
        result.coverage.update(
            {
                **authority,
                "CROSSWALK_EXECUTION_SUCCESS": False,
                **counts,
                "EVERY_REQUIRED_VALIDATOR_EXECUTED_AND_PASSED": (
                    validation.every_required_validator_executed_and_passed
                ),
                "SOURCE_VALIDATION_PASS": validation_contract_ok,
                "CENSUS_SUBPROCESS_EXECUTED": validation.census_subprocess_executed,
                "LANDSCAPE_SUBPROCESS_EXECUTED": validation.landscape_subprocess_executed,
                "CENSUS_VALIDATOR_CONNECTED": validation.census_validator_connected,
                "LANDSCAPE_VALIDATOR_CONNECTED": validation.landscape_validator_connected,
                "ATLAS_CURRENT_ANCHOR_ENFORCED": True,
                "CARTOGRAPHY_CURRENT_ANCHOR_ENFORCED": True,
                "validation_errors": result.errors,
                "snapshot_drift_root_cause": drift_report.get("snapshot_drift_root_cause"),
            }
        )
        (output_dir / "snapshot_drift_report.v1.json").write_text(
            json.dumps(drift_report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _write_outputs(
            output_dir=output_dir,
            result=result,
            composed={
                "schema_version": COMPOSED_GRAPH_SCHEMA,
                "authority": CROSSWALK_AUTHORITY,
                "snapshot_id": snapshot_id,
                "source_validation_pass": False,
                "errors": result.errors,
                **authority,
            },
            manifest={
                "schema_version": MANIFEST_SCHEMA,
                "snapshot_id": snapshot_id,
                "node_count": 0,
                **authority,
            },
            excluded_report={"excluded": [], "historical_edges_ingested": 0},
        )
        return result

    census_revision = code_snap.census_revision
    landscape_revision = code_snap.landscape_revision
    atlas_revision = code_snap.atlas_revision

    endpoint_verdicts: dict[str, Any] = {}
    for obj in sources.census.get("census_objects", []):
        endpoint_verdicts[str(obj["object_id"])] = classify_census_object(
            obj, evidence_revision=census_revision
        )

    census_ids, census_paths = build_census_anchor_index(
        sources.census.get("census_objects", []),
        evidence_revision=census_revision,
    )

    census_included = 0
    for obj in sources.census.get("census_objects", []):
        verdict = endpoint_verdicts[str(obj["object_id"])]
        if not verdict_includable_in_graph(verdict):
            bucket = (
                "UNKNOWN_ENTITIES_EXCLUDED"
                if verdict.state == CurrentRelevanceState.UNKNOWN
                else "NON_CURRENT_ENTITIES_EXCLUDED"
            )
            counts[bucket] += 1
            result.excluded.append(
                {
                    "kind": "census_object",
                    "id": obj.get("object_id"),
                    "relevance_state": verdict.state.value,
                    "reason": exclusion_reason_from_verdict(verdict),
                }
            )
            continue
        cfi = _add_node(
            result,
            entity_type="COMPONENT",
            source_system="CURRENT_SYSTEM_CENSUS",
            native_id=str(obj["object_id"]),
            snapshot_id=snapshot_id,
            code_revision=code_rev,
            artifact="config/governance/current_system_census_graph_v1/source_v1.json",
            revision=census_revision,
            evidence_type="STATIC_SOURCE_EVIDENCE",
            metadata={
                "primary_class": obj.get("primary_class"),
                "paths": obj.get("paths"),
            },
            current_relevance=verdict.to_record(),
        )
        if cfi:
            census_included += 1
            counts["CURRENT_ENTITIES_INCLUDED"] += 1

    surface_included = 0
    for surface in sources.landscape.get("surfaces", []):
        verdict = classify_landscape_surface(surface, evidence_revision=landscape_revision)
        if not verdict_includable_in_graph(verdict):
            counts["NON_CURRENT_ENTITIES_EXCLUDED"] += 1
            result.excluded.append(
                {
                    "kind": "landscape_surface",
                    "id": surface.get("surface_id"),
                    "relevance_state": verdict.state.value,
                    "reason": exclusion_reason_from_verdict(verdict),
                }
            )
            continue
        sid = str(surface.get("surface_id"))
        _add_node(
            result,
            entity_type="SURFACE",
            source_system="CURRENT_UNIVERSE_LANDSCAPE",
            native_id=sid,
            snapshot_id=snapshot_id,
            code_revision=code_rev,
            artifact="config/governance/current_universe_landscape_snapshot_v1/source_v1.json",
            revision=landscape_revision,
            evidence_type="STATIC_SOURCE_EVIDENCE",
            metadata={"responsibility": surface.get("responsibility")},
            current_relevance=verdict.to_record(),
        )
        counts["CURRENT_ENTITIES_INCLUDED"] += 1
        pm = surface.get("positive_membership")
        if pm:
            _add_node(
                result,
                entity_type="UNIVERSE",
                source_system="CURRENT_UNIVERSE_LANDSCAPE",
                native_id=str(pm),
                snapshot_id=snapshot_id,
                code_revision=code_rev,
                artifact="config/governance/current_universe_landscape_snapshot_v1/source_v1.json",
                revision=landscape_revision,
                evidence_type="STATIC_SOURCE_EVIDENCE",
                metadata={"surface_id": sid},
                current_relevance=verdict.to_record(),
            )
            counts["CURRENT_ENTITIES_INCLUDED"] += 1
        surface_included += 1

    included_atlas_ids: set[str] = set()
    atlas_included = 0
    if include_atlas:
        for ent in sources.atlas_catalog:
            if not isinstance(ent, dict) or not ent.get("id"):
                continue
            verdict = classify_atlas_entity(
                ent,
                evidence_revision=atlas_revision,
                census_object_ids=census_ids,
                census_paths=census_paths,
            )
            if not verdict_includable_in_graph(verdict):
                bucket = (
                    "UNKNOWN_ENTITIES_EXCLUDED"
                    if verdict.state == CurrentRelevanceState.UNKNOWN
                    else "NON_CURRENT_ENTITIES_EXCLUDED"
                )
                counts[bucket] += 1
                result.excluded.append(
                    {
                        "kind": "atlas_entity",
                        "id": ent.get("id"),
                        "relevance_state": verdict.state.value,
                        "reason": exclusion_reason_from_verdict(verdict),
                    }
                )
                continue
            kind = str(ent.get("kind") or "COMPONENT")
            entity_type = "CONTRACT" if kind == "CONTRACT" else "COMPONENT"
            _add_node(
                result,
                entity_type=entity_type,
                source_system="SYSTEM_ATLAS",
                native_id=str(ent["id"]),
                snapshot_id=snapshot_id,
                code_revision=code_rev,
                artifact="docs/system_atlas/entities/catalog.yaml",
                revision=atlas_revision,
                evidence_type="CONTRACT_EVIDENCE",
                metadata={"kind": kind, "name": ent.get("name")},
                current_relevance=verdict.to_record(),
            )
            included_atlas_ids.add(str(ent["id"]))
            atlas_included += 1
            counts["CURRENT_ENTITIES_INCLUDED"] += 1

        for rel in sources.atlas_structural_relations:
            verdict = classify_atlas_relation(
                rel,
                evidence_revision=atlas_revision,
                included_entity_ids=included_atlas_ids,
            )
            if not verdict_includable_in_graph(verdict):
                bucket = (
                    "UNKNOWN_EDGES_EXCLUDED"
                    if verdict.state == CurrentRelevanceState.UNKNOWN
                    else "NON_CURRENT_EDGES_EXCLUDED"
                )
                counts[bucket] += 1
                result.excluded.append(
                    {
                        "kind": "atlas_relation",
                        "id": rel.get("id"),
                        "relevance_state": verdict.state.value,
                        "reason": exclusion_reason_from_verdict(verdict),
                    }
                )
                continue
            edge_type, _ = atlas_relation_to_typed_edge(rel)
            flags = edge_semantics_flags(edge_type)
            act = verdict.activation_condition
            result.edges.append(
                {
                    "edge_id": f"atlas:{rel.get('id')}",
                    "source_native_id": rel.get("source"),
                    "target_native_id": rel.get("target"),
                    "typed_edge": flags,
                    "source_system": "SYSTEM_ATLAS",
                    "current_relevance": verdict.to_record(),
                    "causal_traversal_eligible": flags["causal_propagation_allowed"],
                    "provenance": _provenance(
                        tool="ghv_forensic_whole_system_crosswalk_v1",
                        artifact="docs/system_atlas/relations/structural.yaml",
                        revision=atlas_revision,
                        code_revision=code_rev,
                        native_id=str(rel.get("id")),
                        canonical_id=str(rel.get("id")),
                        evidence_type="CONTRACT_EVIDENCE",
                        activation_conditions=((act,) if act else ()),
                    ),
                }
            )
            counts["CURRENT_EDGES_INCLUDED"] += 1

    census_edges_included = 0
    included_census_native_ids: set[str] = {
        str(n.get("source_native_id"))
        for n in result.nodes
        if n.get("source_system") == "CURRENT_SYSTEM_CENSUS" and n.get("source_native_id")
    }
    for edge in sources.census.get("semantic_edges", []):
        edge_verdict = classify_census_edge(
            edge,
            evidence_revision=census_revision,
            endpoint_verdicts=endpoint_verdicts,
        )
        if edge_verdict.state == CurrentRelevanceState.NON_CURRENT:
            counts["NON_CURRENT_EDGES_EXCLUDED"] += 1
            result.excluded.append(
                {
                    "kind": "census_edge",
                    "id": edge.get("edge_id"),
                    "relevance_state": edge_verdict.state.value,
                    "reason": exclusion_reason_from_verdict(edge_verdict),
                }
            )
            continue
        if edge_verdict.state == CurrentRelevanceState.UNKNOWN:
            counts["UNKNOWN_EDGES_EXCLUDED"] += 1
            result.excluded.append(
                {
                    "kind": "census_edge",
                    "id": edge.get("edge_id"),
                    "relevance_state": edge_verdict.state.value,
                    "reason": exclusion_reason_from_verdict(edge_verdict),
                }
            )
            continue
        edge_type, note = census_flow_to_typed_edge(edge)
        if edge_type is None:
            result.unresolved_edges.append(
                {
                    "edge_id": edge.get("edge_id"),
                    "source_system": "CURRENT_SYSTEM_CENSUS",
                    "reason": note,
                    "current_relevance": edge_verdict.to_record(),
                    "source_native_id": edge.get("source_object"),
                    "target_native_id": edge.get("target_object"),
                }
            )
            continue
        src_ref = edge.get("source_object")
        tgt_ref = edge.get("target_object")
        src_ok = bool(src_ref) and str(src_ref) in included_census_native_ids
        tgt_ok = bool(tgt_ref) and str(tgt_ref) in included_census_native_ids
        if not src_ok or not tgt_ok:
            missing: list[str] = []
            if not src_ok:
                missing.append(f"unresolved_source_object:{src_ref}")
            if not tgt_ok:
                missing.append(f"unresolved_target_object:{tgt_ref}")
            result.unresolved_edges.append(
                {
                    "edge_id": edge.get("edge_id"),
                    "source_system": "CURRENT_SYSTEM_CENSUS",
                    "reason": "unresolved_census_edge_endpoints",
                    "missing_endpoints": missing,
                    "source_native_id": src_ref,
                    "target_native_id": tgt_ref,
                    "current_relevance": edge_verdict.to_record(),
                    "provenance": _provenance(
                        tool="ghv_forensic_whole_system_crosswalk_v1",
                        artifact="config/governance/current_system_census_graph_v1/source_v1.json",
                        revision=census_revision,
                        code_revision=code_rev,
                        native_id=str(edge.get("edge_id")),
                        canonical_id=str(edge.get("edge_id")),
                        evidence_type="CONTRACT_EVIDENCE",
                        activation_conditions=(
                            (edge_verdict.activation_condition,)
                            if edge_verdict.activation_condition
                            else ()
                        ),
                    ),
                }
            )
            continue
        flags = edge_semantics_flags(edge_type)
        act = edge_verdict.activation_condition
        result.edges.append(
            {
                "edge_id": f"census:{edge.get('edge_id')}",
                "source_native_id": edge.get("source_object"),
                "target_native_id": edge.get("target_object"),
                "typed_edge": flags,
                "source_system": "CURRENT_SYSTEM_CENSUS",
                "contract_or_payload": edge.get("contract_or_payload"),
                "current_relevance": edge_verdict.to_record(),
                "causal_traversal_eligible": flags["causal_propagation_allowed"],
                "provenance": _provenance(
                    tool="ghv_forensic_whole_system_crosswalk_v1",
                    artifact="config/governance/current_system_census_graph_v1/source_v1.json",
                    revision=census_revision,
                    code_revision=code_rev,
                    native_id=str(edge.get("edge_id")),
                    canonical_id=str(edge.get("edge_id")),
                    evidence_type="CONTRACT_EVIDENCE",
                    activation_conditions=((act,) if act else ()),
                ),
            }
        )
        census_edges_included += 1
        counts["CURRENT_EDGES_INCLUDED"] += 1

    _apply_explicit_rules(result, sources.crosswalk_rules)

    if evidence_root and evidence_root.is_dir():
        manifest_path = evidence_root / "ghv_pre_external_runtime_capture_manifest_v1.json"
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            repo_sha = str(manifest.get("repository_sha") or "")
            if not repo_sha.strip():
                result.excluded.append(
                    {
                        "kind": "ghv_evidence_bundle",
                        "reason": "missing_repository_sha_in_capture_manifest",
                    }
                )
            elif repo_sha != code_rev:
                result.excluded.append(
                    {
                        "kind": "ghv_evidence_bundle",
                        "reason": "historical_or_stale_ghv_evidence_repository_sha_mismatch",
                        "evidence_sha": repo_sha,
                        "code_head": code_rev,
                    }
                )
            else:
                result.coverage["ghv_evidence_attached"] = True
        else:
            result.excluded.append(
                {"kind": "ghv_evidence_bundle", "reason": "missing_capture_manifest"}
            )

    if not result.coverage.get("ghv_evidence_attached"):
        evidence_snap = build_evidence_snapshot_v1(evidence_root=None)

    included_states = {
        n.get("current_relevance", {}).get("CURRENT_RELEVANCE_STATE") for n in result.nodes
    } | {e.get("current_relevance", {}).get("CURRENT_RELEVANCE_STATE") for e in result.edges}
    filters_ok = (
        counts["HISTORICAL_ENTITIES_INGESTED"] == 0
        and counts["HISTORICAL_EDGES_INGESTED"] == 0
        and CurrentRelevanceState.UNKNOWN.value not in included_states
        and None not in included_states
        and all(
            s
            in (
                CurrentRelevanceState.CURRENT_VERIFIED.value,
                CurrentRelevanceState.CURRENT_CONDITIONAL.value,
            )
            for s in included_states
            if s
        )
    )
    current_graph_verified = (
        graph_mode == GraphMode.STRICT_CURRENT
        and validation_contract_ok
        and snapshot_binding_verified
        and filters_ok
        and len(result.unresolved_edges) == 0
        and len(result.collisions) == 0
    )
    authority = build_graph_authority_coverage(
        graph_mode=graph_mode,
        source_validation_pass=validation_contract_ok,
        snapshot_binding_verified=snapshot_binding_verified,
        current_only_filter_applied=True,
        current_graph_verified=current_graph_verified,
    )

    total_census = len(sources.census.get("census_objects", []))
    total_edges = len(sources.census.get("semantic_edges", []))
    result.coverage.update(
        {
            **authority,
            "SOURCE_VALIDATION_PASS": validation_contract_ok,
            "EVERY_REQUIRED_VALIDATOR_EXECUTED_AND_PASSED": (
                validation.every_required_validator_executed_and_passed
            ),
            "CENSUS_SUBPROCESS_EXECUTED": validation.census_subprocess_executed,
            "LANDSCAPE_SUBPROCESS_EXECUTED": validation.landscape_subprocess_executed,
            "CURRENT_RELEVANCE_VERIFIED": counts["CURRENT_ENTITIES_INCLUDED"]
            + counts["CURRENT_EDGES_INCLUDED"],
            "CURRENT_RELEVANCE_UNKNOWN": counts["UNKNOWN_ENTITIES_EXCLUDED"]
            + counts["UNKNOWN_EDGES_EXCLUDED"],
            "NON_CURRENT_EXCLUDED": counts["NON_CURRENT_ENTITIES_EXCLUDED"]
            + counts["NON_CURRENT_EDGES_EXCLUDED"],
            "CROSSWALK_EXECUTION_SUCCESS": True,
            "IDENTITY_COVERAGE_COMPLETE": False,
            "EDGE_COVERAGE_COMPLETE": len(result.unresolved_edges) == 0,
            "CURRENT_COMPONENT_COVERAGE_COMPLETE": False,
            "census_objects_total": total_census,
            "census_objects_included": census_included,
            "landscape_surfaces_included": surface_included,
            "atlas_entities_included": atlas_included,
            "census_edges_included": census_edges_included,
            "census_edges_total": total_edges,
            "unresolved_edge_count": len(result.unresolved_edges),
            "collision_count": len(result.collisions),
            "ambiguous_count": len(result.ambiguous),
            "excluded_count": len(result.excluded),
            "historical_graph_ingestion": False,
            "CENSUS_VALIDATOR_CONNECTED": validation.census_validator_connected,
            "LANDSCAPE_VALIDATOR_CONNECTED": validation.landscape_validator_connected,
            "ATLAS_CURRENT_ANCHOR_ENFORCED": True,
            "CARTOGRAPHY_CURRENT_ANCHOR_ENFORCED": True,
            "snapshot_drift_root_cause": drift_report.get("snapshot_drift_root_cause"),
            **counts,
        }
    )
    if graph_mode == GraphMode.STRICT_CURRENT and not snapshot_binding_verified:
        result.ok = False

    composed = {
        "schema_version": COMPOSED_GRAPH_SCHEMA,
        "authority": CROSSWALK_AUTHORITY,
        "snapshot_id": snapshot_id,
        "source_validation_pass": True,
        **authority,
        "code_snapshot": code_snap.to_dict(),
        "evidence_snapshot": evidence_snap.to_dict(),
        "nodes": result.nodes,
        "edges": result.edges,
        "unresolved_edges": result.unresolved_edges,
    }
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "snapshot_id": snapshot_id,
        "node_count": len(result.nodes),
        "edge_count": len(result.edges),
        "explicit_rules_count": len(sources.crosswalk_rules.get("rules") or []),
        **authority,
    }
    (output_dir / "snapshot_drift_report.v1.json").write_text(
        json.dumps(drift_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    excluded_report = {
        "excluded": result.excluded,
        "historical_entities_ingested": counts["HISTORICAL_ENTITIES_INGESTED"],
        "historical_edges_ingested": counts["HISTORICAL_EDGES_INGESTED"],
    }

    _write_outputs(
        output_dir=output_dir,
        result=result,
        composed=composed,
        manifest=manifest,
        excluded_report=excluded_report,
    )

    return result
