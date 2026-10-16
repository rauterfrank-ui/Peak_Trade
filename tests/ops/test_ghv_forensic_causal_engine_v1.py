"""Traversal and cross-universe impact tests for forensic causal engine v1."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.compose_v1 import (
    run_forensic_crosswalk_v1,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.edges_v1 import (
    census_flow_to_typed_edge,
    edge_semantics_flags,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.graph_mode_v1 import GraphMode
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.census_endpoint_resolve_v1 import (
    build_alias_target_fanin,
    build_census_endpoint_alias_index,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.impact_v1 import (
    propagate_change_impact_v1,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.load_sources_v1 import (
    load_sources_v1,
)
from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.traversal_v1 import (
    traverse_forensic_graph_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RULES = (
    REPO_ROOT
    / "scripts"
    / "ops"
    / "ghv_forensic_whole_system_crosswalk_v1"
    / "crosswalk_rules.v1.json"
)
_STRICT = {"strict_repo_invariants": True, "graph_mode": GraphMode.STRICT_CURRENT}


def _strict_graph():
    out = Path("/tmp/ghv_causal_engine_strict_graph")
    result = run_forensic_crosswalk_v1(
        repo_root=REPO_ROOT,
        output_dir=out,
        rules_path=RULES,
        include_atlas=False,
        **_STRICT,
    )
    composed = json.loads((out / "composed_forensic_graph.v1.json").read_text(encoding="utf-8"))
    sources = load_sources_v1(repo_root=REPO_ROOT, rules_path=RULES)
    return result, composed, sources


def _impact_kwargs(result, composed, sources):
    included = {str(n["source_native_id"]) for n in composed["nodes"] if n.get("source_native_id")}
    alias_index = build_census_endpoint_alias_index(
        repo_root=REPO_ROOT,
        census_objects=sources.census.get("census_objects") or [],
        included_native_ids=included,
    )
    return {
        "crosswalk_coverage": dict(result.coverage),
        "alias_index": alias_index,
    }


def test_constraint_and_presentation_flow_typing() -> None:
    constraint, _ = census_flow_to_typed_edge({"flow_type": "CONSTRAINT_FLOW"})
    assert constraint == "BLOCKS"
    promo, _ = census_flow_to_typed_edge({"flow_type": "PROMOTION_FLOW"})
    assert promo == "AUTHORIZES"
    pres, _ = census_flow_to_typed_edge({"flow_type": "PRESENTATION"})
    assert pres == "OBSERVES"
    assert edge_semantics_flags(pres)["causal_propagation_allowed"] is False


def test_forward_and_reverse_traversal_deterministic() -> None:
    _, composed, _ = _strict_graph()
    nodes = composed["nodes"]
    edges = composed["edges"]
    origin = "SO-OPS-PKG:governed_futures_universe_producer_v1"
    fwd1 = traverse_forensic_graph_v1(
        nodes=nodes, edges=edges, origin_native_id=origin, direction="FORWARD"
    )
    fwd2 = traverse_forensic_graph_v1(
        nodes=nodes, edges=edges, origin_native_id=origin, direction="FORWARD"
    )
    assert fwd1.reachable_native_ids == fwd2.reachable_native_ids
    rev = traverse_forensic_graph_v1(
        nodes=nodes, edges=edges, origin_native_id=origin, direction="REVERSE"
    )
    assert origin not in rev.reachable_native_ids or rev.reachable_native_ids == []


def test_traversal_missing_origin_unknown() -> None:
    _, composed, _ = _strict_graph()
    result = traverse_forensic_graph_v1(
        nodes=composed["nodes"],
        edges=composed["edges"],
        origin_native_id="missing-node-id",
        direction="FORWARD",
    )
    assert "missing-node-id" in result.unknown_endpoints


def test_traversal_cycle_records_path_without_infinite_loop() -> None:
    nodes = [
        {"source_native_id": "A", "source_system": "CURRENT_SYSTEM_CENSUS"},
        {"source_native_id": "B", "source_system": "CURRENT_SYSTEM_CENSUS"},
    ]
    edges = [
        {
            "edge_id": "e1",
            "source_native_id": "A",
            "target_native_id": "B",
            "causal_traversal_eligible": True,
            "typed_edge": {"edge_type": "PRODUCES", "causal_propagation_allowed": True},
        },
        {
            "edge_id": "e2",
            "source_native_id": "B",
            "target_native_id": "A",
            "causal_traversal_eligible": True,
            "typed_edge": {"edge_type": "PRODUCES", "causal_propagation_allowed": True},
        },
    ]
    result = traverse_forensic_graph_v1(
        nodes=nodes, edges=edges, origin_native_id="A", direction="FORWARD", max_depth=4
    )
    assert "B" in result.reachable_native_ids
    assert len(result.paths) >= 2


def test_cross_universe_impact_propagation() -> None:
    result, composed, sources = _strict_graph()
    assert result.ok is True
    kw = _impact_kwargs(result, composed, sources)
    impact = propagate_change_impact_v1(
        nodes=composed["nodes"],
        edges=composed["edges"],
        census_objects=sources.census.get("census_objects") or [],
        seed_native_id="SO-OPS-PKG:governed_futures_universe_producer_v1",
        **kw,
    )
    assert impact.propagation_status in {
        "IMPACT_PROPAGATED",
        "UNKNOWN",
        "NO_DOWNSTREAM_CAUSAL_IMPACT",
    }
    if impact.propagation_status == "IMPACT_PROPAGATED":
        assert len(impact.impacted_native_ids) >= 1


def test_strict_current_zero_unresolved_edges() -> None:
    result, _, _ = _strict_graph()
    assert result.coverage["SNAPSHOT_BINDING_VERIFIED"] is True
    assert result.coverage["unresolved_edge_count"] == 0
    assert result.coverage["CURRENT_GRAPH_VERIFIED"] is True
    assert result.ok is True


def test_edge_coverage_is_not_causal_or_component_closure() -> None:
    result, _, _ = _strict_graph()
    assert result.coverage["EDGE_COVERAGE_COMPLETE"] is True
    assert result.coverage["CAUSAL_CLOSURE_PROVEN"] is False
    assert result.coverage["CURRENT_COMPONENT_COVERAGE_COMPLETE"] is False
    assert result.coverage["IDENTITY_COVERAGE_COMPLETE"] is False


def test_proof_eligibility_decoupled_from_current_graph_verified() -> None:
    result, _, _ = _strict_graph()
    assert result.coverage["CURRENT_GRAPH_VERIFIED"] is True
    report_path = Path(
        "/tmp/ghv_causal_engine_strict_graph/forensic_source_provenance_report.v1.json"
    )
    if report_path.is_file():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["record"]["PROOF_ELIGIBILITY"] is False


def test_dashboard_presentation_edge_non_causal() -> None:
    _, composed, _ = _strict_graph()
    dashboard = next(e for e in composed["edges"] if e.get("edge_id") == "census:dashboard_read")
    assert dashboard["typed_edge"]["edge_type"] == "OBSERVES"
    assert dashboard["causal_traversal_eligible"] is False
    blocked = traverse_forensic_graph_v1(
        nodes=composed["nodes"],
        edges=composed["edges"],
        origin_native_id=dashboard["source_native_id"],
        direction="FORWARD",
        causal_only=True,
    )
    assert "census:dashboard_read" in blocked.blocked_non_causal


def test_alias_resolution_preserves_original_endpoint_ref() -> None:
    _, composed, _ = _strict_graph()
    aliased = [
        e
        for e in composed["edges"]
        if e.get("target_endpoint_ref")
        and e.get("target_native_id") != e.get("target_endpoint_ref")
    ]
    assert aliased, "expected at least one alias-resolved census edge"
    sample = aliased[0]
    assert sample["target_endpoint_ref"]
    assert sample["target_native_id"].startswith("SO-")


def test_impact_unknown_fail_closed_for_missing_seed() -> None:
    result, composed, sources = _strict_graph()
    impact = propagate_change_impact_v1(
        nodes=composed["nodes"],
        edges=composed["edges"],
        census_objects=sources.census.get("census_objects") or [],
        seed_native_id="definitely-not-in-graph",
        **_impact_kwargs(result, composed, sources),
    )
    assert impact.propagation_status == "UNKNOWN"
    assert impact.unknown is True


def test_coarse_governance_hub_never_false_no_impact() -> None:
    result, composed, sources = _strict_graph()
    kw = _impact_kwargs(result, composed, sources)
    fanin = build_alias_target_fanin(kw["alias_index"])
    assert fanin.get("SO-SRC-PKG:governance", 0) >= 2
    impact = propagate_change_impact_v1(
        nodes=composed["nodes"],
        edges=composed["edges"],
        census_objects=sources.census.get("census_objects") or [],
        seed_native_id="SO-SRC-PKG:governance",
        **kw,
    )
    assert impact.propagation_status != "NO_DOWNSTREAM_CAUSAL_IMPACT"
    assert impact.unknown is True
    assert impact.conservative_no_impact_blocked is True


def test_two_domain_refs_one_package_alias_forces_unknown_no_impact() -> None:
    nodes = [
        {
            "source_native_id": "SO-OPS-PKG:pkg_a",
            "source_system": "CURRENT_SYSTEM_CENSUS",
            "metadata": {"positive_membership": "TD-A"},
        }
    ]
    edges: list[dict] = []
    census_objects = [
        {
            "object_id": "SO-OPS-PKG:pkg_a",
            "positive_membership": "TD-A",
            "primary_class": "POSITIVE_UNIVERSE_MEMBER",
        }
    ]
    alias_index = {"domain_x": "SO-OPS-PKG:pkg_a", "domain_y": "SO-OPS-PKG:pkg_a"}
    coverage = {
        "CURRENT_COMPONENT_COVERAGE_COMPLETE": False,
        "EDGE_COVERAGE_COMPLETE": True,
        "unresolved_edge_count": 0,
    }
    impact = propagate_change_impact_v1(
        nodes=nodes,
        edges=edges,
        census_objects=census_objects,
        seed_native_id="SO-OPS-PKG:pkg_a",
        alias_index=alias_index,
        crosswalk_coverage=coverage,
    )
    assert impact.propagation_status == "UNKNOWN"
    assert "seed_coarse_alias_hub" in ",".join(impact.coverage_gaps)


def test_no_false_no_impact_when_component_coverage_incomplete() -> None:
    result, composed, sources = _strict_graph()
    assert result.coverage["CURRENT_COMPONENT_COVERAGE_COMPLETE"] is False
    kw = _impact_kwargs(result, composed, sources)
    for seed in ("SO-SRC-PKG:governance", "SO-SRC-PKG:infra"):
        impact = propagate_change_impact_v1(
            nodes=composed["nodes"],
            edges=composed["edges"],
            census_objects=sources.census.get("census_objects") or [],
            seed_native_id=seed,
            **kw,
        )
        if impact.impacted_native_ids == [seed]:
            assert impact.propagation_status == "UNKNOWN"
            assert impact.propagation_status != "NO_DOWNSTREAM_CAUSAL_IMPACT"


def test_proven_coverage_allows_no_downstream_on_isolated_node() -> None:
    nodes = [{"source_native_id": "SO-OPS-PKG:isolated", "source_system": "X"}]
    census_objects = [
        {
            "object_id": "SO-OPS-PKG:isolated",
            "positive_membership": "TD-ISO",
            "primary_class": "POSITIVE_UNIVERSE_MEMBER",
        }
    ]
    coverage = {
        "CURRENT_COMPONENT_COVERAGE_COMPLETE": True,
        "EDGE_COVERAGE_COMPLETE": True,
        "unresolved_edge_count": 0,
    }
    impact = propagate_change_impact_v1(
        nodes=nodes,
        edges=[],
        census_objects=census_objects,
        seed_native_id="SO-OPS-PKG:isolated",
        alias_index={"SO-OPS-PKG:isolated": "SO-OPS-PKG:isolated"},
        crosswalk_coverage=coverage,
    )
    assert impact.propagation_status == "NO_DOWNSTREAM_CAUSAL_IMPACT"
    assert impact.unknown is False


def test_package_alias_multiple_consumer_edges_incident() -> None:
    result, composed, sources = _strict_graph()
    kw = _impact_kwargs(result, composed, sources)
    hub_edges = [
        e
        for e in composed["edges"]
        if e.get("target_native_id") == "SO-OPS-PKG:single_selected_future_runtime_binding_v1"
        and e.get("target_endpoint_ref")
        and e.get("target_endpoint_ref") != e.get("target_native_id")
    ]
    assert hub_edges
    impact = propagate_change_impact_v1(
        nodes=composed["nodes"],
        edges=composed["edges"],
        census_objects=sources.census.get("census_objects") or [],
        seed_native_id=hub_edges[0]["target_native_id"],
        **kw,
    )
    if impact.impacted_native_ids == [hub_edges[0]["target_native_id"]]:
        assert impact.propagation_status == "UNKNOWN"


def test_presentation_archive_path_non_causal_not_false_no_impact() -> None:
    result, composed, sources = _strict_graph()
    kw = _impact_kwargs(result, composed, sources)
    read_model = "SO-OPS-PKG:canonical_derived_public_md_read_model_v1"
    impact = propagate_change_impact_v1(
        nodes=composed["nodes"],
        edges=composed["edges"],
        census_objects=sources.census.get("census_objects") or [],
        seed_native_id=read_model,
        **kw,
    )
    assert impact.propagation_status != "NO_DOWNSTREAM_CAUSAL_IMPACT" or impact.unknown


def test_disconnected_graph_partial_coverage_unknown() -> None:
    nodes = [
        {"source_native_id": "SO-OPS-PKG:orphan_a", "source_system": "X"},
        {"source_native_id": "SO-OPS-PKG:orphan_b", "source_system": "X"},
    ]
    census_objects = [
        {
            "object_id": "SO-OPS-PKG:orphan_a",
            "candidate_or_related_universe": "TD-X",
            "primary_class": "UNASSIGNED_CURRENT",
        },
        {
            "object_id": "SO-OPS-PKG:orphan_b",
            "candidate_or_related_universe": "TD-Y",
            "primary_class": "UNASSIGNED_CURRENT",
        },
    ]
    coverage = {
        "CURRENT_COMPONENT_COVERAGE_COMPLETE": False,
        "EDGE_COVERAGE_COMPLETE": False,
        "unresolved_edge_count": 1,
    }
    impact = propagate_change_impact_v1(
        nodes=nodes,
        edges=[],
        census_objects=census_objects,
        seed_native_id="SO-OPS-PKG:orphan_a",
        alias_index={},
        crosswalk_coverage=coverage,
    )
    assert impact.propagation_status == "UNKNOWN"


def test_multigraph_parallel_edges_distinct_ids() -> None:
    _, composed, _ = _strict_graph()
    pairs: dict[tuple[str, str], list[str]] = {}
    for edge in composed["edges"]:
        key = (edge["source_native_id"], edge["target_native_id"])
        pairs.setdefault(key, []).append(str(edge["edge_id"]))
    parallel = {k: v for k, v in pairs.items() if len(v) > 1}
    assert parallel
    for edge_ids in parallel.values():
        assert len(edge_ids) == len(set(edge_ids))
