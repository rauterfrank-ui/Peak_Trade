"""Scope the existing GHV crosswalk pieces after the WP-A0 pin gate.

Composition uses the crosswalk current filter and edge classifier on a
caller-supplied candidate. It does not call the writing crosswalk entry, does
not read repository census files, and does not invent edges.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.edges_v1 import edge_semantics_flags
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.filter_current_v1 import (
    classify_census_edge,
    classify_census_object,
    verdict_includable_in_graph,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.impact_v1 import (
    propagate_change_impact_v1,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.traversal_v1 import (
    traverse_forensic_graph_v1,
)
from scripts.ops.pin_scope_binding_v1.bind_v1 import bind_pin_and_scope_v1
from scripts.ops.pin_scope_binding_v1.constants_v1 import (
    SCOPE_FIELDS,
    STATUS_ACCEPTED,
    STATUS_POLICY_CONFLICT,
)
from scripts.ops.scoped_ghv_crosswalk_adapter_v1.constants_v1 import (
    AUTHORITY,
    COVERAGE_PROOF,
    DEFAULT_MAX_DEPTH,
    DIRECT_DEPTH,
    EXECUTION_AUTHORITY,
    FORBIDDEN_PASS_KEYS,
    GRAPH_MATERIALIZED,
    GUARDIAN_IDENTITY,
    LIVE_GATE,
    MAX_DEPTH_LIMIT,
    NETWORK_ACCESS,
    RUNTIME_AUTHORIZATION_EFFECT,
    SAFETY_AUTHORITY,
    SCHEMA_ID,
    SCHEMA_VERSION,
    TRADING_AUTHORITY,
)

Composer = Callable[..., dict[str, Any]]


def run_scoped_ghv_v1(
    *,
    authoritative_commit_sha: str,
    authoritative_tree_sha: str,
    declared_commit_sha: str,
    declared_tree_sha: str,
    provenance: Mapping[str, Any],
    scope: Mapping[str, Any],
    candidate_nodes: list[dict[str, Any]] | None = None,
    candidate_edges: list[dict[str, Any]] | None = None,
    origin_native_id: str | None = None,
    reverse_origin_native_id: str | None = None,
    max_depth: int = DEFAULT_MAX_DEPTH,
    policies: list[Mapping[str, Any]] | None = None,
    evidence_prelude: Mapping[str, Any] | None = None,
    composer: Composer | None = None,
) -> dict[str, Any]:
    """Gate pins and scope, then evaluate only the allowed candidate subset."""
    binding = bind_pin_and_scope_v1(
        authoritative_commit_sha=authoritative_commit_sha,
        authoritative_tree_sha=authoritative_tree_sha,
        declared_commit_sha=declared_commit_sha,
        declared_tree_sha=declared_tree_sha,
        provenance=provenance,
        scope=scope,
    )
    status = str(binding["status"])
    allowed = list(binding["in_scope_nodes"])
    if status != STATUS_ACCEPTED or not allowed:
        return _result(
            status=status,
            binding=binding,
            provenance=provenance,
            composition_invoked=False,
            coverage_gap=True,
        )
    if not isinstance(max_depth, int) or not 1 <= max_depth <= MAX_DEPTH_LIMIT:
        return _result(
            status=status,
            binding=binding,
            provenance=provenance,
            composition_invoked=False,
            coverage_gap=True,
            reasons=["max_depth_rejected"],
        )
    prelude_reasons = _prelude_reasons(evidence_prelude, declared_commit_sha)
    if prelude_reasons:
        return _result(
            status="FORGED_PROVENANCE",
            binding=binding,
            provenance=provenance,
            composition_invoked=False,
            coverage_gap=True,
            reasons=prelude_reasons,
        )
    policy_conflict = _policy_conflict(policies)
    if policy_conflict:
        return _result(
            status=STATUS_POLICY_CONFLICT,
            binding=binding,
            provenance=provenance,
            composition_invoked=False,
            coverage_gap=True,
            observation_coverage_gap=True,
            reasons=policy_conflict,
        )

    checked_nodes = [_snapshot_record(node) for node in (candidate_nodes or [])]
    checked_edges = [_snapshot_record(edge) for edge in (candidate_edges or [])]
    compose = composer or compose_scoped_candidate_v1
    composed = compose(
        candidate_nodes=checked_nodes,
        candidate_edges=checked_edges,
        allowed_nodes=allowed,
        exclusions=list(binding["explicitly_out_of_scope"]),
        unassigned=list(binding["unresolved"]),
        evidence_revision=declared_commit_sha,
    )
    scope_coverage_gap = bool(binding.get("scope_coverage_gap"))
    graph_coverage_gap = _has_gap(composed)
    observation_reasons = _observation_reasons(composed, policies)
    observation_coverage_gap = bool(observation_reasons)
    forward = _walk(
        composed,
        origin_native_id,
        "FORWARD",
        DIRECT_DEPTH,
    )
    reverse = _walk(
        composed,
        reverse_origin_native_id,
        "REVERSE",
        DIRECT_DEPTH,
    )
    transitive = _walk(
        composed,
        origin_native_id,
        "FORWARD",
        max_depth,
    )
    impact = _impact(composed, origin_native_id, max_depth)
    if forward["coverage_gap"] or reverse["coverage_gap"] or transitive["coverage_gap"]:
        graph_coverage_gap = True
    if impact["coverage_gap"]:
        graph_coverage_gap = True
    ready_edge_ids, edge_rejections = _integration_ready_edges(
        checked_edges,
        list(composed["evaluated_edges"]),
    )
    handoff = dict(composed)
    handoff["evaluated_edges"] = ready_edge_ids
    handoff["edge_contract_rejections"] = edge_rejections
    if edge_rejections:
        graph_coverage_gap = True
    coverage_gap = scope_coverage_gap or graph_coverage_gap or observation_coverage_gap
    return _result(
        status=status,
        binding=binding,
        provenance=provenance,
        composition_invoked=True,
        coverage_gap=coverage_gap,
        scope_coverage_gap=scope_coverage_gap,
        graph_coverage_gap=graph_coverage_gap,
        observation_coverage_gap=observation_coverage_gap,
        composed=handoff,
        reasons=observation_reasons,
        evidence_prelude=evidence_prelude,
        checked_nodes=checked_nodes,
        checked_edges=checked_edges,
        forward=forward,
        reverse=reverse,
        transitive=transitive,
        impact=impact,
    )


def compose_scoped_candidate_v1(
    *,
    candidate_nodes: list[dict[str, Any]],
    candidate_edges: list[dict[str, Any]],
    allowed_nodes: list[str],
    exclusions: list[str],
    unassigned: list[str],
    evidence_revision: str,
) -> dict[str, Any]:
    """Filter a supplied candidate. Missing nodes and edges stay absent."""
    allowed = set(allowed_nodes)
    excluded = set(exclusions)
    open_nodes = set(unassigned)
    seen: set[str] = set()
    included: list[dict[str, Any]] = []
    verdicts: dict[str, Any] = {}
    excluded_nodes: list[str] = []
    unassigned_nodes: list[str] = []
    unknown_nodes: list[str] = []
    filtered_non_current_nodes: list[str] = []

    for obj in candidate_nodes:
        native_id = str(obj.get("object_id") or "")
        if native_id == "" or native_id in seen:
            continue
        seen.add(native_id)
        verdict = classify_census_object(obj, evidence_revision=evidence_revision)
        verdicts[native_id] = verdict
        if native_id in excluded:
            excluded_nodes.append(native_id)
            continue
        if native_id in open_nodes:
            unassigned_nodes.append(native_id)
            continue
        if native_id not in allowed:
            unknown_nodes.append(native_id)
            continue
        if obj.get("evidence_plane") == "DOMAIN_CODE_REFERENCE":
            included.append(dict(obj))
            continue
        if not verdict_includable_in_graph(verdict):
            filtered_non_current_nodes.append(native_id)
            continue
        included.append(dict(obj))

    included_ids = {str(obj["object_id"]) for obj in included}
    missing_allowed_nodes = [node for node in allowed_nodes if node not in seen]
    kept_edges: list[dict[str, Any]] = []
    dropped_edge_ids: list[str] = []
    for edge in candidate_edges:
        source = str(edge.get("source_native_id") or "")
        target = str(edge.get("target_native_id") or "")
        edge_id = str(edge.get("edge_id") or "")
        if source not in included_ids or target not in included_ids:
            if edge_id:
                dropped_edge_ids.append(edge_id)
            continue
        if edge.get("evidence_plane") == "DOMAIN_CODE_REFERENCE":
            kept_edges.append(dict(edge))
            continue
        edge_verdict = classify_census_edge(
            edge,
            evidence_revision=evidence_revision,
            endpoint_verdicts=verdicts,
        )
        if not verdict_includable_in_graph(edge_verdict):
            if edge_id:
                dropped_edge_ids.append(edge_id)
            continue
        kept_edges.append(dict(edge))

    return {
        "evaluated_nodes": [str(obj["object_id"]) for obj in included],
        "evaluated_edges": [str(edge.get("edge_id") or "") for edge in kept_edges],
        "excluded_nodes": excluded_nodes,
        "unassigned_nodes": unassigned_nodes,
        "unknown_nodes": unknown_nodes,
        "filtered_non_current_nodes": filtered_non_current_nodes,
        "missing_allowed_nodes": missing_allowed_nodes,
        "dropped_edge_ids": dropped_edge_ids,
        "census_objects": included,
        "traversal_nodes": [{"source_native_id": str(obj["object_id"])} for obj in included],
        "traversal_edges": [_traversal_edge(edge) for edge in kept_edges],
    }


def integration_edge_rejection_v1(edge: Mapping[str, Any]) -> str | None:
    """Return a fail-closed reason, or None when the CURRENT typed edge is usable.

    flow_type is not a typed_edge. Missing and unknown types stay unmapped.
    """
    typed = edge.get("typed_edge")
    if not isinstance(typed, Mapping):
        return "missing_typed_edge"
    edge_type = typed.get("edge_type")
    if not isinstance(edge_type, str) or edge_type.strip() == "":
        return "missing_typed_edge"
    try:
        expected = edge_semantics_flags(edge_type)
    except ValueError:
        return "unknown_edge_type"
    if typed.get("trading_authority_implied"):
        return "authority_implied"
    for field in ("structural_only", "causal_propagation_allowed"):
        if field in typed and typed[field] != expected[field]:
            return "contradictory_edge_attributes"
    return None


def _integration_ready_edges(
    checked_edges: list[dict[str, Any]],
    traversed_edge_ids: list[str],
) -> tuple[list[str], list[dict[str, str]]]:
    traversed = set(traversed_edge_ids)
    ready: list[str] = []
    rejections: list[dict[str, str]] = []
    for edge in checked_edges:
        edge_id = str(edge.get("edge_id") or "")
        if edge_id not in traversed:
            continue
        reason = integration_edge_rejection_v1(edge)
        if reason is None:
            ready.append(edge_id)
        else:
            rejections.append({"edge_id": edge_id, "reason": reason})
    return ready, rejections


def _traversal_edge(edge: Mapping[str, Any]) -> dict[str, Any]:
    typed = edge.get("typed_edge")
    typed_body = dict(typed) if isinstance(typed, Mapping) else {}
    return {
        "edge_id": str(edge.get("edge_id") or ""),
        "source_native_id": str(edge.get("source_native_id") or ""),
        "target_native_id": str(edge.get("target_native_id") or ""),
        "causal_traversal_eligible": bool(edge.get("causal_traversal_eligible")),
        "typed_edge": typed_body,
    }


_PROVEN_REACHABILITY = frozenset({"EXISTS", "WIRED", "REACHABLE", "ACTIVE"})


def _unproven_reachability_ids(
    composed: Mapping[str, Any],
    native_ids: list[str],
) -> list[str]:
    """UNKNOWN reachability is not causal closure, even when the walk finishes."""
    by_id: dict[str, Mapping[str, Any]] = {}
    for node in composed.get("census_objects") or []:
        if isinstance(node, Mapping):
            by_id[str(node.get("object_id") or "")] = node
    unproven: list[str] = []
    for native_id in native_ids:
        node = by_id.get(native_id)
        if node is None:
            continue
        reachability = node.get("reachability")
        relevance = node.get("current_relevance")
        relevance_state = (
            relevance.get("CURRENT_RELEVANCE_STATE") if isinstance(relevance, Mapping) else None
        )
        domain = node.get("evidence_plane") == "DOMAIN_CODE_REFERENCE"
        if reachability == "UNKNOWN" or relevance_state == "UNKNOWN":
            unproven.append(native_id)
            continue
        if domain and reachability not in _PROVEN_REACHABILITY:
            unproven.append(native_id)
    return unproven


def _traversal_view(
    *,
    completed: bool,
    reachable: list[str],
    unproven: list[str],
) -> dict[str, Any]:
    reachability_proven = completed and not unproven
    return {
        "traversal_completed": completed,
        "additional_traversable_edge_found": bool(reachable),
        "reachability_proven": reachability_proven,
        "coverage_proven": False,
        "causal_closure_proven": False,
        "unproven_reachability": unproven,
        "coverage_gap": (not completed) or bool(unproven),
    }


def _walk(
    composed: Mapping[str, Any],
    origin: str | None,
    direction: str,
    max_depth: int,
) -> dict[str, Any]:
    evaluated = set(composed["evaluated_nodes"])
    if origin is None or origin not in evaluated:
        return {
            "origin": origin,
            "direction": direction,
            "max_depth": max_depth,
            "reachable": [],
            **_traversal_view(completed=False, reachable=[], unproven=[]),
        }
    walked = traverse_forensic_graph_v1(
        nodes=list(composed["traversal_nodes"]),
        edges=list(composed["traversal_edges"]),
        origin_native_id=origin,
        direction=direction,  # type: ignore[arg-type]
        causal_only=True,
        max_depth=max_depth,
    )
    reachable = list(walked.reachable_native_ids)
    completed = not walked.unknown_endpoints
    unproven = _unproven_reachability_ids(composed, [origin, *reachable])
    return {
        "origin": origin,
        "direction": direction,
        "max_depth": max_depth,
        "reachable": reachable,
        **_traversal_view(completed=completed, reachable=reachable, unproven=unproven),
    }


def _impact(
    composed: Mapping[str, Any],
    origin: str | None,
    max_depth: int,
) -> dict[str, Any]:
    evaluated = set(composed["evaluated_nodes"])
    if origin is None or origin not in evaluated:
        return {
            "seed": origin,
            "propagation_status": "NOT_RUN",
            "impacted_native_ids": [],
            **_traversal_view(completed=False, reachable=[], unproven=[]),
        }
    propagated = propagate_change_impact_v1(
        nodes=list(composed["traversal_nodes"]),
        edges=list(composed["traversal_edges"]),
        census_objects=list(composed["census_objects"]),
        seed_native_id=origin,
        causal_only=True,
        max_depth=max_depth,
    )
    impacted = list(propagated.impacted_native_ids)
    completed = propagated.propagation_status == "IMPACT_PROPAGATED"
    others = [native_id for native_id in impacted if native_id != origin]
    unproven = _unproven_reachability_ids(composed, [origin, *impacted])
    view = _traversal_view(completed=completed, reachable=others, unproven=unproven)
    return {
        "seed": origin,
        "propagation_status": propagated.propagation_status,
        "impacted_native_ids": impacted,
        **view,
    }


def _snapshot_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Copy one supplied record. Existing typed_edge values stay unchanged."""
    body = dict(record)
    typed = body.get("typed_edge")
    if isinstance(typed, Mapping):
        body["typed_edge"] = dict(typed)
    return body


def _copy_provenance(provenance: Mapping[str, Any]) -> dict[str, Any]:
    copied: dict[str, Any] = {}
    for role, body in provenance.items():
        if isinstance(body, Mapping):
            copied[str(role)] = dict(body)
        else:
            copied[str(role)] = body
    return copied


def _checked_handoff(
    *,
    binding: Mapping[str, Any],
    provenance: Mapping[str, Any],
    coverage_gap: bool,
    scope_coverage_gap: bool,
    graph_coverage_gap: bool,
    observation_coverage_gap: bool,
    composed: Mapping[str, Any],
    checked_nodes: list[dict[str, Any]] | None,
    checked_edges: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Derive the WP-A2 handoff from the binding that already passed."""
    return {
        "result_pin": binding["declared_commit_sha"],
        "result_tree": binding["declared_tree_sha"],
        "candidate_nodes": list(checked_nodes or []),
        "candidate_edges": list(checked_edges or []),
        "scope_identity": {field: list(binding[field]) for field in SCOPE_FIELDS},
        "checked_provenance": _copy_provenance(provenance),
        "coverage_gaps": {
            "coverage_gap": coverage_gap,
            "scope_coverage_gap": scope_coverage_gap,
            "graph_coverage_gap": graph_coverage_gap,
            "observation_coverage_gap": observation_coverage_gap,
            "excluded_nodes": list(composed.get("excluded_nodes") or []),
            "unassigned_nodes": list(composed.get("unassigned_nodes") or []),
            "unknown_nodes": list(composed.get("unknown_nodes") or []),
            "filtered_non_current_nodes": list(composed.get("filtered_non_current_nodes") or []),
            "missing_allowed_nodes": list(composed.get("missing_allowed_nodes") or []),
            "dropped_edge_ids": list(composed.get("dropped_edge_ids") or []),
            "edge_contract_rejections": list(composed.get("edge_contract_rejections") or []),
        },
    }


def _copy_prelude(prelude: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if prelude is None:
        return None
    return json_copy(prelude)


def json_copy(value: Mapping[str, Any]) -> dict[str, Any]:
    copied: dict[str, Any] = {}
    for key, item in value.items():
        if isinstance(item, Mapping):
            copied[str(key)] = json_copy(item)
        elif isinstance(item, list):
            copied[str(key)] = list(item)
        else:
            copied[str(key)] = item
    return copied


def _prelude_reasons(
    prelude: Mapping[str, Any] | None,
    declared_commit_sha: str,
) -> list[str]:
    if prelude is None:
        return []
    reasons: list[str] = []
    if prelude.get("current_verified") is not False:
        reasons.append("prelude_current_verified_forged")
    if prelude.get("reachability") != "UNKNOWN":
        reasons.append("prelude_reachability_not_unknown")
    if prelude.get("declared_commit_sha") != declared_commit_sha:
        reasons.append("prelude_pin_mismatch")
    return reasons


def _policy_conflict(policies: list[Mapping[str, Any]] | None) -> list[str]:
    if policies is None:
        return []
    reasons: list[str] = []
    if not policies:
        return ["policies_empty"]
    for index, policy in enumerate(policies):
        label = f"policies[{index}]"
        if not isinstance(policy, Mapping):
            reasons.append(f"{label}_not_object")
            continue
        for field in (
            "policy_id",
            "subject_node",
            "attribute",
            "expected",
            "observed",
            "evidence_ref",
        ):
            if (
                field not in policy
                or not isinstance(policy[field], str)
                or policy[field].strip() == ""
            ):
                reasons.append(f"{label}_missing:{field}")
        if reasons:
            continue
        if policy["observed"] != policy["expected"]:
            reasons.append(f"policy_conflict:{policy['policy_id']}:{policy['attribute']}")
    return reasons


def _observation_reasons(
    composed: Mapping[str, Any],
    policies: list[Mapping[str, Any]] | None,
) -> list[str]:
    reasons: list[str] = []
    if policies is not None and not policies:
        reasons.append("policies_empty")
    for node in composed.get("census_objects") or []:
        if not isinstance(node, Mapping):
            continue
        reachability = node.get("reachability")
        native_id = str(node.get("object_id") or "")
        if reachability == "UNKNOWN":
            reasons.append(f"reachability_unknown:{native_id}")
        elif node.get("evidence_plane") == "DOMAIN_CODE_REFERENCE" and reachability not in {
            "EXISTS",
            "WIRED",
            "REACHABLE",
            "ACTIVE",
        }:
            reasons.append(f"reachability_unknown:{native_id}")
    return reasons


def _has_gap(composed: Mapping[str, Any]) -> bool:
    return bool(
        composed["unknown_nodes"]
        or composed["missing_allowed_nodes"]
        or composed["filtered_non_current_nodes"]
        or composed["unassigned_nodes"]
        or composed["dropped_edge_ids"]
    )


def _result(
    *,
    status: str,
    binding: Mapping[str, Any],
    composition_invoked: bool,
    coverage_gap: bool,
    scope_coverage_gap: bool | None = None,
    graph_coverage_gap: bool = False,
    observation_coverage_gap: bool = False,
    provenance: Mapping[str, Any] | None = None,
    composed: Mapping[str, Any] | None = None,
    checked_nodes: list[dict[str, Any]] | None = None,
    checked_edges: list[dict[str, Any]] | None = None,
    forward: Mapping[str, Any] | None = None,
    reverse: Mapping[str, Any] | None = None,
    transitive: Mapping[str, Any] | None = None,
    impact: Mapping[str, Any] | None = None,
    reasons: list[str] | None = None,
    evidence_prelude: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    body = composed or {}
    if scope_coverage_gap is None:
        scope_coverage_gap = bool(binding.get("scope_coverage_gap"))
    coverage_gap = (
        bool(coverage_gap) or scope_coverage_gap or graph_coverage_gap or observation_coverage_gap
    )
    result = {
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
        "graph_materialized": GRAPH_MATERIALIZED,
        "implicit_scope_expansion": False,
        "composition_invoked": composition_invoked,
        "scope_coverage_gap": scope_coverage_gap,
        "graph_coverage_gap": graph_coverage_gap,
        "observation_coverage_gap": observation_coverage_gap,
        "coverage_gap": coverage_gap,
        "coverage_proof": COVERAGE_PROOF,
        "binding_reasons": list(binding.get("reasons") or []),
        "reasons": list(reasons or []),
        "evaluated_nodes": list(body.get("evaluated_nodes") or []),
        "evaluated_edges": list(body.get("evaluated_edges") or []),
        "excluded_nodes": list(body.get("excluded_nodes") or []),
        "unassigned_nodes": list(body.get("unassigned_nodes") or []),
        "unknown_nodes": list(body.get("unknown_nodes") or []),
        "filtered_non_current_nodes": list(body.get("filtered_non_current_nodes") or []),
        "missing_allowed_nodes": list(body.get("missing_allowed_nodes") or []),
        "edge_contract_rejections": list(body.get("edge_contract_rejections") or []),
        "forward": dict(forward or {}),
        "reverse": dict(reverse or {}),
        "transitive": dict(transitive or {}),
        "impact": dict(impact or {}),
        "evidence_prelude": _copy_prelude(evidence_prelude),
    }
    if status == STATUS_ACCEPTED and provenance is not None:
        result.update(
            _checked_handoff(
                binding=binding,
                provenance=provenance,
                coverage_gap=coverage_gap,
                scope_coverage_gap=scope_coverage_gap,
                graph_coverage_gap=graph_coverage_gap,
                observation_coverage_gap=observation_coverage_gap,
                composed=body,
                checked_nodes=checked_nodes,
                checked_edges=checked_edges,
            )
        )
    overlap = FORBIDDEN_PASS_KEYS & set(result)
    if overlap:
        raise RuntimeError(f"forbidden_pass_key:{sorted(overlap)}")
    return result
