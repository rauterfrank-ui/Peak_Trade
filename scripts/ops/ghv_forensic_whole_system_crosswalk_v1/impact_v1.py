"""Cross-universe impact propagation over composed CURRENT forensic graphs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.census_endpoint_resolve_v1 import (
    build_alias_target_fanin,
    native_id_is_coarse_alias_hub,
    static_alias_native_ids,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.traversal_v1 import (
    traverse_forensic_graph_v1,
)


@dataclass
class ImpactPropagationResultV1:
    seed_native_id: str
    seed_universe: str | None
    impacted_native_ids: list[str] = field(default_factory=list)
    impacted_universes: list[str] = field(default_factory=list)
    cross_universe_hops: list[dict[str, str]] = field(default_factory=list)
    coverage_gaps: list[str] = field(default_factory=list)
    unknown: bool = False
    propagation_status: str = "UNKNOWN"
    conservative_no_impact_blocked: bool = False


def build_native_universe_index(
    census_objects: list[dict[str, Any]],
    *,
    included_native_ids: set[str],
) -> tuple[dict[str, str], dict[str, str]]:
    """Return (universe_index, universe_assignment_kind per native id)."""
    index: dict[str, str] = {}
    assignment_kind: dict[str, str] = {}
    for obj in census_objects:
        oid = str(obj.get("object_id") or "")
        if oid not in included_native_ids:
            continue
        if obj.get("positive_membership"):
            index[oid] = str(obj["positive_membership"])
            assignment_kind[oid] = "positive_membership"
        elif obj.get("candidate_or_related_universe"):
            index[oid] = str(obj["candidate_or_related_universe"])
            assignment_kind[oid] = "candidate_or_related_universe"
        elif obj.get("primary_class"):
            index[oid] = str(obj["primary_class"])
            assignment_kind[oid] = "primary_class_fallback"
    return index, assignment_kind


def _edge_uses_alias_resolution(edge: dict[str, Any]) -> bool:
    for side in ("source", "target"):
        ref = edge.get(f"{side}_endpoint_ref")
        native = edge.get(f"{side}_native_id")
        if ref is not None and native is not None and str(ref) != str(native):
            return True
    return False


def _conservative_block_no_downstream_impact(
    *,
    seed_native_id: str,
    edges: list[dict[str, Any]],
    crosswalk_coverage: dict[str, Any] | None,
    alias_index: dict[str, str] | None,
    universe_assignment_kind: dict[str, str],
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if crosswalk_coverage:
        if not crosswalk_coverage.get("CURRENT_COMPONENT_COVERAGE_COMPLETE"):
            reasons.append("component_coverage_incomplete")
        if crosswalk_coverage.get("unresolved_edge_count", 0) > 0:
            reasons.append("unresolved_current_edges_present")
        if not crosswalk_coverage.get("EDGE_COVERAGE_COMPLETE"):
            reasons.append("edge_coverage_incomplete")
    else:
        reasons.append("crosswalk_coverage_not_provided")

    if universe_assignment_kind.get(seed_native_id) == "primary_class_fallback":
        reasons.append("seed_universe_primary_class_fallback")

    fanin = build_alias_target_fanin(alias_index or {})
    if native_id_is_coarse_alias_hub(seed_native_id, fanin):
        reasons.append("seed_coarse_alias_hub")
    if seed_native_id in static_alias_native_ids():
        reasons.append("seed_static_alias_target")

    for edge in edges:
        if (
            edge.get("source_native_id") != seed_native_id
            and edge.get("target_native_id") != seed_native_id
        ):
            continue
        if _edge_uses_alias_resolution(edge):
            reasons.append("seed_incident_alias_resolved_edge")
            break

    return bool(reasons), reasons


def propagate_change_impact_v1(
    *,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    census_objects: list[dict[str, Any]],
    seed_native_id: str,
    causal_only: bool = True,
    max_depth: int = 32,
    crosswalk_coverage: dict[str, Any] | None = None,
    alias_index: dict[str, str] | None = None,
) -> ImpactPropagationResultV1:
    included = {str(n.get("source_native_id")) for n in nodes if n.get("source_native_id")}
    universe_index, universe_assignment_kind = build_native_universe_index(
        census_objects, included_native_ids=included
    )
    result = ImpactPropagationResultV1(
        seed_native_id=seed_native_id,
        seed_universe=universe_index.get(seed_native_id),
    )
    if seed_native_id not in included:
        result.unknown = True
        result.coverage_gaps.append(f"seed_not_in_graph:{seed_native_id}")
        result.propagation_status = "UNKNOWN"
        return result
    if result.seed_universe is None:
        result.coverage_gaps.append(f"seed_universe_unmapped:{seed_native_id}")
        result.unknown = True

    traversal = traverse_forensic_graph_v1(
        nodes=nodes,
        edges=edges,
        origin_native_id=seed_native_id,
        direction="FORWARD",
        causal_only=causal_only,
        max_depth=max_depth,
    )
    if traversal.unknown_endpoints:
        result.coverage_gaps.extend([f"unknown_endpoint:{u}" for u in traversal.unknown_endpoints])
        result.unknown = True

    impacted = [seed_native_id, *traversal.reachable_native_ids]
    result.impacted_native_ids = sorted(set(impacted))

    universes: set[str] = set()
    for native_id in result.impacted_native_ids:
        uni = universe_index.get(native_id)
        if uni:
            universes.add(uni)
        else:
            result.coverage_gaps.append(f"universe_unmapped:{native_id}")
            result.unknown = True

    result.impacted_universes = sorted(universes)
    if result.seed_universe and len(result.impacted_universes) > 1:
        for uni in result.impacted_universes:
            if uni != result.seed_universe:
                result.cross_universe_hops.append(
                    {
                        "from_universe": result.seed_universe,
                        "to_universe": uni,
                        "via_seed": seed_native_id,
                    }
                )

    if result.unknown:
        result.propagation_status = "UNKNOWN"
    elif result.impacted_native_ids == [seed_native_id]:
        blocked, block_reasons = _conservative_block_no_downstream_impact(
            seed_native_id=seed_native_id,
            edges=edges,
            crosswalk_coverage=crosswalk_coverage,
            alias_index=alias_index,
            universe_assignment_kind=universe_assignment_kind,
        )
        if blocked:
            result.conservative_no_impact_blocked = True
            result.unknown = True
            result.propagation_status = "UNKNOWN"
            result.coverage_gaps.append(
                "conservative_no_impact_blocked:" + ",".join(sorted(set(block_reasons)))
            )
        else:
            result.propagation_status = "NO_DOWNSTREAM_CAUSAL_IMPACT"
    else:
        result.propagation_status = "IMPACT_PROPAGATED"

    return result
