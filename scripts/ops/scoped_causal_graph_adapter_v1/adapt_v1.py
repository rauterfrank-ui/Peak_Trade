"""Project a checked WP-A1 result through the existing causal-graph integrator.

The integrator and inspector are called unchanged. This module does not add
nodes or edges, and it refuses to write inside the repository.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping

from scripts.ops.ghv_forensic_whole_system_causal_ghv_adapter_v1.inspect_graph_v1 import (
    run_offline_graph_inspection_v1,
)
from scripts.ops.ghv_forensic_whole_system_causal_integration_v1.constants_v1 import (
    INTEGRATED_GRAPH_SCHEMA,
    INTEGRATION_AUTHORITY,
)
from scripts.ops.ghv_forensic_whole_system_causal_integration_v1.integrate_v1 import (
    run_causal_integration_v1,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.constants_v1 import (
    COMPOSED_GRAPH_SCHEMA,
    MANIFEST_SCHEMA,
)
from scripts.ops.scoped_ghv_crosswalk_adapter_v1.adapt_v1 import integration_edge_rejection_v1
from scripts.ops.pin_scope_binding_v1.bind_v1 import bind_pin_and_scope_v1
from scripts.ops.pin_scope_binding_v1.constants_v1 import (
    AUTHORITY,
    COVERAGE_PROOF,
    EXECUTION_AUTHORITY,
    GUARDIAN_IDENTITY,
    LIVE_GATE,
    NETWORK_ACCESS,
    RUNTIME_AUTHORIZATION_EFFECT,
    SAFETY_AUTHORITY,
    SCOPE_FIELDS,
    STATUS_ACCEPTED,
    STATUS_INVALID_PROVENANCE,
    TRADING_AUTHORITY,
)
from scripts.ops.scoped_causal_graph_adapter_v1.constants_v1 import (
    GRAPH_MODE,
    PROVENANCE_MANIFEST_NAME,
    SCHEMA_ID,
    SCHEMA_VERSION,
    SOURCE_SYSTEM,
    STATUS_MISSING_CURRENT_EVIDENCE,
)

Integrator = Callable[..., Any]
Inspector = Callable[..., Any]
_REPO_ROOT = Path(__file__).resolve().parents[3]
_PROTECTED_NAMES = (
    "integrated_causal_graph.v1.json",
    "composed_forensic_graph.v1.json",
    "causal_overlay.v1.json",
    "causal_coverage_gaps.v1.json",
    "causal_integration_manifest.v1.json",
    PROVENANCE_MANIFEST_NAME,
)


def run_scoped_causal_graph_v1(
    *,
    authoritative_commit_sha: str,
    authoritative_tree_sha: str,
    declared_commit_sha: str,
    declared_tree_sha: str,
    provenance: Mapping[str, Any],
    scope: Mapping[str, Any],
    wp_a1_result: Mapping[str, Any],
    output_dir: Path,
    integrator: Integrator | None = None,
    inspector: Inspector | None = None,
) -> dict[str, Any]:
    """Integrate the checked WP-A1 handoff without adding nodes or edges."""
    binding = bind_pin_and_scope_v1(
        authoritative_commit_sha=authoritative_commit_sha,
        authoritative_tree_sha=authoritative_tree_sha,
        declared_commit_sha=declared_commit_sha,
        declared_tree_sha=declared_tree_sha,
        provenance=provenance,
        scope=scope,
    )
    status = str(binding["status"])
    if status != STATUS_ACCEPTED:
        return _closed(status, integrator_invoked=False, binding=binding)

    if str(wp_a1_result.get("status") or "") != STATUS_ACCEPTED:
        return _closed(
            str(wp_a1_result.get("status") or STATUS_MISSING_CURRENT_EVIDENCE),
            integrator_invoked=False,
            binding=binding,
            graph_coverage_gap=True,
        )
    if not wp_a1_result.get("composition_invoked") or not binding["in_scope_nodes"]:
        return _closed(STATUS_ACCEPTED, integrator_invoked=False, binding=binding)

    evidence_reasons = _evidence_reasons(
        wp_a1_result=wp_a1_result,
        declared_commit_sha=declared_commit_sha,
        declared_tree_sha=declared_tree_sha,
        provenance=provenance,
        binding=binding,
    )
    if evidence_reasons:
        closed_status = STATUS_MISSING_CURRENT_EVIDENCE
        if any(
            reason in {"result_pin_commit_mismatch", "result_pin_tree_mismatch"}
            for reason in evidence_reasons
        ):
            closed_status = "PIN_MISMATCH"
        if any(reason.startswith("provenance_") for reason in evidence_reasons):
            closed_status = STATUS_INVALID_PROVENANCE
        if any(reason.startswith("scope_") for reason in evidence_reasons):
            closed_status = "SCOPE_CONFLICT"
        return _closed(
            closed_status,
            integrator_invoked=False,
            binding=binding,
            graph_coverage_gap=closed_status == STATUS_MISSING_CURRENT_EVIDENCE,
            reasons=evidence_reasons,
        )

    safe_reason = _unsafe_output(output_dir)
    if safe_reason is not None:
        return _closed(
            STATUS_MISSING_CURRENT_EVIDENCE,
            integrator_invoked=False,
            binding=binding,
            graph_coverage_gap=True,
            reasons=[safe_reason],
        )

    prelude_reason = _domain_prelude_reason(wp_a1_result)
    if prelude_reason is not None:
        return _closed(
            STATUS_MISSING_CURRENT_EVIDENCE,
            integrator_invoked=False,
            binding=binding,
            graph_coverage_gap=True,
            reasons=[prelude_reason],
        )

    projected, projection_reason = _project_wp1(
        wp_a1_result=wp_a1_result,
        declared_commit_sha=declared_commit_sha,
        declared_tree_sha=declared_tree_sha,
    )
    if projected is None:
        return _closed(
            STATUS_MISSING_CURRENT_EVIDENCE,
            integrator_invoked=False,
            binding=binding,
            graph_coverage_gap=True,
            reasons=[projection_reason or "projection_missing_current_edge_type"],
        )

    wp1_dir = output_dir / "wp1"
    integrated_dir = output_dir / "integrated"
    _write_wp1(wp1_dir, projected)
    integrate = integrator or run_causal_integration_v1
    integrated = integrate(wp1_output_dir=wp1_dir, output_dir=integrated_dir)
    if not integrated.ok:
        return _closed(
            str(integrated.failure_semantic or STATUS_MISSING_CURRENT_EVIDENCE),
            integrator_invoked=True,
            binding=binding,
            graph_coverage_gap=True,
            reasons=list(integrated.errors),
            output_dir=str(wp1_dir),
        )

    _write_provenance_manifest(
        integrated_dir=integrated_dir,
        declared_commit_sha=declared_commit_sha,
        declared_tree_sha=declared_tree_sha,
        result_pin=str(wp_a1_result["result_pin"]),
        result_tree=str(wp_a1_result["result_tree"]),
        projected=projected,
        unassigned=list(binding["unresolved"]),
        exclusions=list(binding["explicitly_out_of_scope"]),
        unknown_nodes=list(wp_a1_result.get("unknown_nodes") or []),
    )
    inspect = inspector or run_offline_graph_inspection_v1
    inspection = inspect(
        wp2a_output_dir=integrated_dir,
        output_dir=output_dir / "inspection",
        repo_root=_REPO_ROOT,
    )
    integrated_doc = json.loads(
        (integrated_dir / "integrated_causal_graph.v1.json").read_text(encoding="utf-8")
    )
    scope_coverage_gap = bool(wp_a1_result.get("scope_coverage_gap")) or bool(
        binding.get("scope_coverage_gap")
    )
    graph_coverage_gap = bool(wp_a1_result.get("graph_coverage_gap")) or not inspection.ok
    observation_coverage_gap = bool(wp_a1_result.get("observation_coverage_gap"))
    coverage_gap = (
        scope_coverage_gap
        or graph_coverage_gap
        or observation_coverage_gap
        or bool(wp_a1_result.get("coverage_gap"))
        or not inspection.ok
    )
    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_ACCEPTED,
        "authority": AUTHORITY,
        "trading_authority": TRADING_AUTHORITY,
        "safety_authority": SAFETY_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "runtime_authorization_effect": RUNTIME_AUTHORIZATION_EFFECT,
        "guardian_identity": GUARDIAN_IDENTITY,
        "live_gate": LIVE_GATE,
        "network_access": NETWORK_ACCESS,
        "integrator_invoked": True,
        "inspector_invoked": True,
        "inspection_ok": bool(inspection.ok),
        "scope_coverage_gap": scope_coverage_gap,
        "graph_coverage_gap": graph_coverage_gap,
        "observation_coverage_gap": observation_coverage_gap,
        "coverage_gap": coverage_gap,
        "coverage_proof": COVERAGE_PROOF,
        "graph_schema": INTEGRATED_GRAPH_SCHEMA,
        "integrated_authority": integrated_doc.get("authority"),
        "integrated_node_ids": [
            str(node.get("source_native_id") or "") for node in integrated_doc.get("nodes") or []
        ],
        "integrated_edge_ids": [
            str(edge.get("edge_id") or "")
            for edge in integrated_doc.get("edges") or []
            if edge.get("edge_id")
        ],
        "overlay_edge_count": integrated_doc.get("overlay_edge_count"),
        "global_causal_closure_proven": integrated_doc.get("GLOBAL_CAUSAL_CLOSURE_PROVEN"),
        "output_dir": str(integrated_dir),
        "reasons": [],
    }


def _evidence_reasons(
    *,
    wp_a1_result: Mapping[str, Any],
    declared_commit_sha: str,
    declared_tree_sha: str,
    provenance: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> list[str]:
    reasons: list[str] = []
    result_pin = wp_a1_result.get("result_pin")
    result_tree = wp_a1_result.get("result_tree")
    if not isinstance(result_pin, str) or not isinstance(result_tree, str):
        reasons.append("result_pin_missing")
    else:
        if result_pin != declared_commit_sha:
            reasons.append("result_pin_commit_mismatch")
        if result_tree != declared_tree_sha:
            reasons.append("result_pin_tree_mismatch")
    checked_provenance = wp_a1_result.get("checked_provenance")
    if not isinstance(checked_provenance, Mapping):
        reasons.append("provenance_missing")
    elif not _provenance_equal(checked_provenance, provenance):
        reasons.append("provenance_mismatch")
    scope_identity = wp_a1_result.get("scope_identity")
    expected_scope = {field: list(binding[field]) for field in SCOPE_FIELDS}
    if not isinstance(scope_identity, Mapping):
        reasons.append("scope_identity_missing")
    else:
        for field, expected in expected_scope.items():
            value = scope_identity.get(field)
            if not isinstance(value, list) or list(value) != expected:
                reasons.append(f"scope_identity_mismatch:{field}")
    coverage_gaps = wp_a1_result.get("coverage_gaps")
    if not isinstance(coverage_gaps, Mapping) or not isinstance(
        coverage_gaps.get("coverage_gap"), bool
    ):
        reasons.append("coverage_gaps_missing")
    elif coverage_gaps["coverage_gap"] != bool(wp_a1_result.get("coverage_gap")):
        reasons.append("coverage_gaps_contradict_result")
    caller_scope_gap = bool(binding.get("scope_coverage_gap"))
    if not isinstance(wp_a1_result.get("scope_coverage_gap"), bool):
        reasons.append("coverage_dimension_missing:scope_coverage_gap")
    elif caller_scope_gap and not wp_a1_result["scope_coverage_gap"]:
        reasons.append("scope_coverage_gap_cleared")
    for field in ("graph_coverage_gap", "observation_coverage_gap"):
        if not isinstance(wp_a1_result.get(field), bool):
            reasons.append(f"coverage_dimension_missing:{field}")
    evaluated = wp_a1_result.get("evaluated_nodes")
    evaluated_edges = wp_a1_result.get("evaluated_edges")
    candidate_nodes = wp_a1_result.get("candidate_nodes")
    candidate_edges = wp_a1_result.get("candidate_edges")
    if not isinstance(evaluated, list) or not isinstance(evaluated_edges, list):
        reasons.append("evaluated_graph_missing")
    if not isinstance(candidate_nodes, list) or not isinstance(candidate_edges, list):
        reasons.append("candidate_graph_missing")
    if not isinstance(evaluated, list):
        return reasons
    allowed = set(binding["in_scope_nodes"])
    excluded = set(binding["explicitly_out_of_scope"])
    open_nodes = set(binding["unresolved"])
    unknown = set(wp_a1_result.get("unknown_nodes") or [])
    for native_id in evaluated:
        if native_id not in allowed or native_id in excluded or native_id in open_nodes:
            reasons.append(f"scope_evaluated_outside_allowed:{native_id}")
        if native_id in unknown:
            reasons.append(f"scope_unknown_evaluated:{native_id}")
    return reasons


def _provenance_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    if set(map(str, left)) != set(map(str, right)):
        return False
    for role, body in left.items():
        other = right[role]
        if isinstance(body, Mapping) and isinstance(other, Mapping):
            if dict(body) != dict(other):
                return False
        elif body != other:
            return False
    return True


def _project_wp1(
    *,
    wp_a1_result: Mapping[str, Any],
    declared_commit_sha: str,
    declared_tree_sha: str,
) -> tuple[dict[str, Any] | None, str | None]:
    evaluated = set(wp_a1_result["evaluated_nodes"])
    evaluated_edge_ids = set(wp_a1_result["evaluated_edges"])
    nodes: list[dict[str, Any]] = []
    for candidate in wp_a1_result["candidate_nodes"]:
        native_id = str(candidate.get("object_id") or "")
        if native_id not in evaluated:
            continue
        nodes.append(_projected_node(candidate, native_id, declared_commit_sha))
    node_ids = {str(node["source_native_id"]) for node in nodes}
    if node_ids != evaluated:
        return None, "projection_missing_current_edge_type"
    edges: list[dict[str, Any]] = []
    seen_edge_ids: set[str] = set()
    for candidate in wp_a1_result["candidate_edges"]:
        edge_id = str(candidate.get("edge_id") or "")
        if edge_id not in evaluated_edge_ids or edge_id in seen_edge_ids:
            continue
        source = str(candidate.get("source_native_id") or "")
        target = str(candidate.get("target_native_id") or "")
        if source not in evaluated or target not in evaluated:
            continue
        rejection = integration_edge_rejection_v1(candidate)
        if rejection is not None:
            return None, f"{rejection}:{edge_id}"
        edges.append(_projected_edge(candidate, declared_commit_sha))
        seen_edge_ids.add(edge_id)
    if seen_edge_ids != evaluated_edge_ids:
        return None, "projection_missing_current_edge_type"
    return {
        "snapshot_id": declared_commit_sha,
        "git_head": str(wp_a1_result["result_pin"]),
        "git_tree": declared_tree_sha,
        "current_verified": not bool(wp_a1_result.get("coverage_gap")),
        "nodes": nodes,
        "edges": edges,
    }, None


def _projected_node(
    candidate: Mapping[str, Any],
    native_id: str,
    commit_sha: str,
) -> dict[str, Any]:
    source_system = _source_system(candidate)
    canonical_id = f"CFI/v1/COMPONENT/{commit_sha}/{source_system}/{native_id}"
    return {
        "canonical_id": canonical_id,
        "entity_type": "COMPONENT",
        "source_system": source_system,
        "source_native_id": native_id,
        "metadata": {"reachability": candidate.get("reachability", "UNKNOWN")},
        "current_relevance": _relevance(candidate, commit_sha, "wp_a1_evaluated_node"),
        "provenance": _provenance(native_id, canonical_id, commit_sha),
    }


def _projected_edge(candidate: Mapping[str, Any], commit_sha: str) -> dict[str, Any]:
    typed = dict(candidate["typed_edge"])
    typed["trading_authority_implied"] = False
    edge_id = str(candidate.get("edge_id") or "")
    return {
        "edge_id": edge_id,
        "source_native_id": str(candidate.get("source_native_id") or ""),
        "target_native_id": str(candidate.get("target_native_id") or ""),
        "source_system": _source_system(candidate),
        "typed_edge": typed,
        "causal_traversal_eligible": bool(candidate.get("causal_traversal_eligible")),
        "current_relevance": _relevance(candidate, commit_sha, "wp_a1_evaluated_edge"),
        "provenance": _provenance(edge_id, f"CFI/v1/EDGE/{commit_sha}/{edge_id}", commit_sha),
    }


def _provenance(native_id: str, canonical_id: str, commit_sha: str) -> dict[str, Any]:
    return {
        "SOURCE_TOOL": SCHEMA_ID,
        "SOURCE_ARTIFACT": "wp_a1_result",
        "SOURCE_REVISION": commit_sha,
        "CODE_REVISION": commit_sha,
        "NATIVE_ID": native_id,
        "CANONICAL_ID": canonical_id,
        "EVIDENCE_TYPE": "CONTRACT_EVIDENCE",
        "PROOF_CLASS": "CONTRACT_CONFIRMED",
        "OBSERVED_OR_INFERRED": "OBSERVED",
        "ACTIVATION_CONDITIONS": [],
        "VALIDATION_STATUS": "PASS",
        "LIMITATIONS": ["coverage_proof_false"],
        "SCHEMA": "peak_trade.forensic_canonical_identity.v1",
    }


def _write_wp1(wp1_dir: Path, projected: Mapping[str, Any]) -> None:
    verified = bool(projected["current_verified"])
    authority = {
        "GRAPH_MODE": GRAPH_MODE,
        "GRAPH_AUTHORITY": GRAPH_MODE,
        "SNAPSHOT_BINDING_VERIFIED": verified,
        "CURRENT_ONLY_FILTER_APPLIED": True,
        "CURRENT_GRAPH_VERIFIED": verified,
        "CURRENT_ONLY_GRAPH": verified,
        "SOURCE_VALIDATION_PASS": True,
        "CAUSAL_CLOSURE_PROVEN": False,
        "GLOBAL_NON_INTERFERENCE_PROVEN": False,
    }
    composed = {
        "schema_version": COMPOSED_GRAPH_SCHEMA,
        "authority": INTEGRATION_AUTHORITY,
        "snapshot_id": projected["snapshot_id"],
        "source_validation_pass": True,
        **authority,
        "code_snapshot": {
            "kind": "CODE_SNAPSHOT",
            "git_head": projected["git_head"],
            "tree": projected["git_tree"],
        },
        "evidence_snapshot": {"kind": "EVIDENCE_SNAPSHOT", "evidence_root": None},
        "nodes": projected["nodes"],
        "edges": projected["edges"],
        "unresolved_edges": [],
    }
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "authority": INTEGRATION_AUTHORITY,
        "snapshot_id": projected["snapshot_id"],
        "node_count": len(projected["nodes"]),
        "edge_count": len(projected["edges"]),
        **authority,
    }
    coverage = {
        **authority,
        "HISTORICAL_ENTITIES_INGESTED": 0,
        "HISTORICAL_EDGES_INGESTED": 0,
    }
    documents = {
        "composed_forensic_graph.v1.json": composed,
        "crosswalk_manifest.v1.json": manifest,
        "coverage_report.v1.json": coverage,
        "ambiguity_report.v1.json": {"collisions": [], "ambiguous": [], "unresolved_edges": []},
        "excluded_non_current_report.v1.json": {
            "excluded": [],
            "historical_entities_ingested": 0,
            "historical_edges_ingested": 0,
        },
    }
    wp1_dir.mkdir(parents=True, exist_ok=False)
    for name, document in documents.items():
        (wp1_dir / name).write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _write_provenance_manifest(
    *,
    integrated_dir: Path,
    declared_commit_sha: str,
    declared_tree_sha: str,
    result_pin: str,
    result_tree: str,
    projected: Mapping[str, Any],
    unassigned: list[str],
    exclusions: list[str],
    unknown_nodes: list[str],
) -> None:
    document = {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "authority": AUTHORITY,
        "trading_authority": TRADING_AUTHORITY,
        "safety_authority": SAFETY_AUTHORITY,
        "guardian_identity": GUARDIAN_IDENTITY,
        "coverage_proof": COVERAGE_PROOF,
        "repository_evidence_write": False,
        "declared_commit_sha": declared_commit_sha,
        "declared_tree_sha": declared_tree_sha,
        "result_pin": result_pin,
        "result_tree": result_tree,
        "node_ids": [str(node["source_native_id"]) for node in projected["nodes"]],
        "edge_ids": [str(edge["edge_id"]) for edge in projected["edges"]],
        "unassigned": unassigned,
        "exclusions": exclusions,
        "unknown_nodes": unknown_nodes,
    }
    (integrated_dir / PROVENANCE_MANIFEST_NAME).write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _unsafe_output(output_dir: Path) -> str | None:
    try:
        resolved = output_dir.resolve()
    except OSError:
        return "output_path_unresolved"
    repo = _REPO_ROOT.resolve()
    if resolved == repo or repo in resolved.parents:
        return "output_dir_inside_repository"
    if resolved.exists():
        for name in _PROTECTED_NAMES:
            if (resolved / name).exists() or (resolved / "integrated" / name).exists():
                return f"existing_graph_artifact:{name}"
    return None


def _closed(
    status: str,
    *,
    integrator_invoked: bool,
    binding: Mapping[str, Any] | None = None,
    graph_coverage_gap: bool = False,
    observation_coverage_gap: bool = False,
    coverage_gap: bool = True,
    reasons: list[str] | None = None,
    output_dir: str | None = None,
) -> dict[str, Any]:
    scope_coverage_gap = bool((binding or {}).get("scope_coverage_gap"))
    coverage_gap = (
        coverage_gap or scope_coverage_gap or graph_coverage_gap or observation_coverage_gap
    )
    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "authority": AUTHORITY,
        "trading_authority": TRADING_AUTHORITY,
        "safety_authority": SAFETY_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "runtime_authorization_effect": RUNTIME_AUTHORIZATION_EFFECT,
        "guardian_identity": GUARDIAN_IDENTITY,
        "live_gate": LIVE_GATE,
        "network_access": NETWORK_ACCESS,
        "integrator_invoked": integrator_invoked,
        "inspector_invoked": False,
        "inspection_ok": False,
        "scope_coverage_gap": scope_coverage_gap,
        "graph_coverage_gap": graph_coverage_gap,
        "observation_coverage_gap": observation_coverage_gap,
        "coverage_gap": coverage_gap,
        "coverage_proof": COVERAGE_PROOF,
        "graph_schema": INTEGRATED_GRAPH_SCHEMA,
        "integrated_authority": None,
        "integrated_node_ids": [],
        "integrated_edge_ids": [],
        "overlay_edge_count": 0,
        "global_causal_closure_proven": False,
        "output_dir": output_dir,
        "reasons": list(reasons or []),
    }


def _source_system(record: Mapping[str, Any]) -> str:
    if record.get("evidence_plane") == "DOMAIN_CODE_REFERENCE":
        return "DOMAIN_EVIDENCE"
    return SOURCE_SYSTEM


def _relevance(record: Mapping[str, Any], commit_sha: str, evidence: str) -> dict[str, Any]:
    domain = record.get("evidence_plane") == "DOMAIN_CODE_REFERENCE"
    unknown = domain or record.get("reachability") == "UNKNOWN"
    if unknown:
        return {
            "CURRENT_RELEVANCE_STATE": "UNKNOWN",
            "CURRENT_RELEVANCE_EVIDENCE": "reachability_unknown",
            "EVIDENCE_SOURCE": SCHEMA_ID,
            "EVIDENCE_REVISION": commit_sha,
            "VALIDATION_STATUS": "UNKNOWN",
            "ACTIVATION_CONDITION": None,
        }
    return {
        "CURRENT_RELEVANCE_STATE": "CURRENT_VERIFIED",
        "CURRENT_RELEVANCE_EVIDENCE": evidence,
        "EVIDENCE_SOURCE": SCHEMA_ID,
        "EVIDENCE_REVISION": commit_sha,
        "VALIDATION_STATUS": "PASS",
        "ACTIVATION_CONDITION": None,
    }


def _domain_prelude_reason(wp_a1_result: Mapping[str, Any]) -> str | None:
    candidates = list(wp_a1_result.get("candidate_nodes") or [])
    domain = any(
        isinstance(node, Mapping) and node.get("evidence_plane") == "DOMAIN_CODE_REFERENCE"
        for node in candidates
    )
    prelude = wp_a1_result.get("evidence_prelude")
    if not domain:
        if prelude is None:
            return None
        if not isinstance(prelude, Mapping) or prelude.get("current_verified") is not False:
            return "prelude_current_verified_forged"
        return None
    if not isinstance(prelude, Mapping):
        return "evidence_prelude_missing"
    if prelude.get("current_verified") is not False:
        return "prelude_current_verified_forged"
    if prelude.get("reachability") != "UNKNOWN":
        return "prelude_reachability_not_unknown"
    return None
