"""Orchestrate the read-only outer-boundary projection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scripts.ops.mv2_outer_boundary_projector_v1.boundary_cut_v1 import (
    cut_outer_edges_v1,
    traversal_crosscheck_v1,
)
from scripts.ops.mv2_outer_boundary_projector_v1.classification_v1 import (
    classify_membership_candidate_v1,
    replay_membership_candidate_v1,
)
from scripts.ops.mv2_outer_boundary_projector_v1.constants_v1 import (
    CAUSAL_INTEGRATION_PATH,
    CENSUS_PATH,
    DECISION_SPEC_PATH,
    LANDSCAPE_PATH,
    MAX_OUTER_DEPTH,
    PROJECTOR_ID,
    REPLAY_COMPONENT_ID,
    REPLAY_SYMBOL,
    RESOLVER_ID,
    SCOPE,
    TARGET_IDENTITY,
)
from scripts.ops.mv2_outer_boundary_projector_v1.countercheck_v1 import (
    build_countercheck_v1,
)
from scripts.ops.mv2_outer_boundary_projector_v1.input_contract_v1 import (
    ProjectorFailClosedV1,
    ProjectorRequestV1,
    validate_request_v1,
)
from scripts.ops.mv2_outer_boundary_projector_v1.output_contract_v1 import (
    assemble_report_v1,
    canonical_json_v1,
    decide_boundary_status_v1,
)
from scripts.ops.mv2_outer_boundary_projector_v1.source_pins_v1 import (
    load_pinned_sources_v1,
    validate_pin_v1,
)
from scripts.ops.mv2_outer_boundary_projector_v1.symbol_endpoint_resolver_v1 import (
    load_pinned_symbol_texts_v1,
    resolve_symbol_endpoints_v1,
)

_PACKAGE_DIR = Path(__file__).resolve().parent


def _assert_output_outside_repo(path: Path, repo_root: Path) -> None:
    resolved = path.resolve()
    root = repo_root.resolve()
    if resolved == root or root in resolved.parents:
        raise ProjectorFailClosedV1("OUTPUT_INSIDE_REPO", str(resolved))


def _prepare_extra_edge(raw: dict[str, object], commit: str) -> dict[str, Any]:
    edge = dict(raw)
    baseline = str(edge.get("baseline") or commit)
    edge["baseline"] = baseline
    edge["current_proof"] = bool(edge.get("current_proof", True)) and baseline == commit
    edge.setdefault("source_kind", "EXPLICIT_OBSERVATION")
    edge.setdefault("endpoint_resolution", "COMPONENT")
    edge.setdefault("authority", "NONE")
    edge.setdefault("artifact", "request.extra_edges")
    return edge


def _sort_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=lambda item: str(item.get("component_id") or item.get("edge_id")))


def run_mv2_outer_boundary_projector_v1(
    request: ProjectorRequestV1,
    *,
    repo_root: Path,
    output_path: Path | None = None,
) -> dict[str, Any]:
    validate_request_v1(request)
    validate_pin_v1(repo_root, request.commit, request.tree)
    if output_path is not None:
        _assert_output_outside_repo(output_path, repo_root)
    sources = load_pinned_sources_v1(repo_root, request.commit)
    if not sources.reference_is_ancestor:
        raise ProjectorFailClosedV1(
            "DECISION_BASELINE_NOT_ANCESTOR",
            sources.reference_baseline,
        )
    if not sources.code_diff_empty:
        raise ProjectorFailClosedV1(
            "ANCHOR_SEMANTIC_DIFF",
            sources.reference_baseline,
        )
    if not sources.replay_defined or not sources.cycle_owner_cites_replay:
        raise ProjectorFailClosedV1("ANCHOR_CITATION_ABSENT", REPLAY_SYMBOL)
    if not sources.double_play_role_confirmed:
        raise ProjectorFailClosedV1("ANCHOR_CITATION_ABSENT", "DOUBLE_PLAY_ROLE")

    proven_members: list[dict[str, Any]] = []
    unclassified: list[dict[str, Any]] = []
    replay = classify_membership_candidate_v1(
        replay_membership_candidate_v1(
            exists_on_pin=sources.replay_defined,
            owner_places_in_joint_core=True,
            code_confirms_role=sources.cycle_owner_cites_replay,
            diff_empty=sources.code_diff_empty,
        )
    )
    cfi = sources.ghv.build_cfi_v1(
        entity_type="SYMBOL",
        snapshot_id=request.commit[:32],
        source_system="PINNED_GIT",
        source_native_id=REPLAY_SYMBOL,
    )
    provenance = sources.ghv.provenance_record_v1(
        source_tool=PROJECTOR_ID,
        source_artifact=DECISION_SPEC_PATH,
        source_revision=sources.reference_baseline,
        code_revision=request.commit,
        native_id=REPLAY_SYMBOL,
        canonical_id=cfi,
        evidence_type="OWNER_DECISION_AND_CODE",
        proof_class="SYMBOL_ROLE",
        observed_or_inferred="OBSERVED",
        activation_conditions=("PINNED_TREE",),
        validation_status="GATES_PASSED"
        if replay["classification"] == "PROVEN_MV2_MEMBER"
        else "GATES_FAILED",
        limitations=("FULL_UNIVERSE_BOUNDARY_UNRATIFIED",),
    ).to_dict()
    replay["canonical_forensic_identity"] = cfi
    replay["equated_to_census_id"] = False
    replay["provenance"] = provenance
    replay["baseline"] = request.commit
    replay["evidence"] = [
        DECISION_SPEC_PATH,
        "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
        "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py",
    ]
    if replay["classification"] == "PROVEN_MV2_MEMBER":
        proven_members.append(replay)
    else:
        unclassified.append(replay)

    for raw in request.extra_candidates:
        classified = classify_membership_candidate_v1(dict(raw))
        classified["baseline"] = request.commit
        classified["equated_to_census_id"] = False
        if classified["classification"] == "PROVEN_MV2_MEMBER":
            proven_members.append(classified)
        else:
            unclassified.append(classified)

    for item in sources.census_candidates:
        classified = classify_membership_candidate_v1(
            {
                "component_id": item["component_id"],
                "basis": "CENSUS_TAXONOMY",
                "exists_on_pin": True,
                "owner_places_in_joint_core": False,
                "code_confirms_role": False,
                "diff_empty": False,
                "scope": "CENSUS_LABEL",
            }
        )
        classified["census_object_id"] = item["census_object_id"]
        classified["paths"] = item["paths"]
        classified["baseline"] = request.commit
        classified["equated_to_census_id"] = False
        unclassified.append(classified)

    unclassified.append(
        {
            "component_id": "role:DOUBLE_PLAY_INTERNAL_FUNCTIONAL_AREA",
            "classification": "POSSIBLE_MV2_MEMBER_UNCLASSIFIED",
            "basis": "OWNER_DECLARES_INTERNAL_AREA_WITHOUT_COMPONENT_ROSTER",
            "separate_universe": False,
            "membership_granted": False,
            "universe_ratification": False,
            "automatic_promotion": False,
            "proof_status": "NOT_PROVEN",
            "uncertainty": "COMPONENT_ROSTER_ABSENT",
            "baseline": request.commit,
        }
    )
    symbol_resolution = resolve_symbol_endpoints_v1(
        commit=request.commit,
        tree=request.tree,
        texts=load_pinned_symbol_texts_v1(repo_root, request.commit),
        census_edges=sources.census_outer_edges,
        candidates=unclassified,
        flow_mapper=sources.ghv.census_flow_to_typed_edge,
        ignored_observations=[
            {"edge_id": str(item.get("path") or ""), "kind": "HISTORICAL_GRAPH"}
            for item in sources.historical_graphs
        ],
        causal_graph_status=sources.causal_graph_status,
    )

    proven_ids = {str(item["component_id"]) for item in proven_members}
    candidate_external: dict[str, dict[str, Any]] = {}
    unresolved_components: list[dict[str, Any]] = list(sources.non_transfer_components)
    for raw in request.extra_external_partners:
        partner = dict(raw)
        component_id = str(partner.get("component_id") or "")
        if partner.get("outside_evidence") != "OWNER_AUTHORITY_NON_TRANSFER" or component_id == "":
            unresolved_components.append(
                {
                    "component_id": component_id or "missing-external-partner",
                    "classification": "UNRESOLVED_COMPONENT",
                    "proof_status": "NOT_PROVEN",
                    "uncertainty": "OUTSIDE_EVIDENCE_ABSENT",
                    "baseline": request.commit,
                }
            )
            continue
        candidate_external[component_id] = partner

    observed_edges = list(sources.census_outer_edges)
    observed_edges.extend(
        _prepare_extra_edge(dict(item), request.commit) for item in request.extra_edges
    )
    cut = cut_outer_edges_v1(
        observed_edges,
        proven_member_ids=proven_ids,
        proven_external_ids=set(candidate_external),
        flow_mapper=sources.ghv.census_flow_to_typed_edge,
    )
    used_endpoints = {
        endpoint
        for record in (*cut["inbound"], *cut["outbound"])
        for endpoint in (record["source_id"], record["target_id"])
    }
    external_partners: list[dict[str, Any]] = []
    for component_id, partner in sorted(candidate_external.items()):
        if component_id in used_endpoints and component_id not in proven_ids:
            external_partners.append(
                {
                    "component_id": component_id,
                    "classification": "PROVEN_EXTERNAL_BOUNDARY_PARTNER",
                    "outside_evidence": partner.get("outside_evidence"),
                    "universe_ratification": False,
                    "proof_status": "DIRECT_EDGE_TO_PROVEN_MEMBER",
                    "uncertainty": "PARTNER_ONLY_NOT_A_UNIVERSE_BOUNDARY",
                    "baseline": request.commit,
                }
            )
        else:
            unresolved_components.append(
                {
                    "component_id": component_id,
                    "classification": "UNRESOLVED_COMPONENT",
                    "proof_status": "NOT_PROVEN",
                    "uncertainty": "NO_RESOLVED_DIRECT_EDGE",
                    "baseline": request.commit,
                }
            )

    crosscheck = traversal_crosscheck_v1(
        cut["unresolved"],
        sources.ghv.traverse_forensic_graph_v1,
    )
    proven_members = _sort_records(proven_members)
    unclassified = _sort_records(unclassified)
    external_partners = _sort_records(external_partners)
    unresolved_components = _sort_records(unresolved_components)
    resolved_count = len(cut["inbound"]) + len(cut["outbound"])
    status = decide_boundary_status_v1(
        causal_graph_verified=sources.causal_graph_verified,
        proven_count=len(proven_members),
        resolved_count=resolved_count,
    )
    countercheck = build_countercheck_v1(
        repo_root=repo_root,
        commit=request.commit,
        package_dir=_PACKAGE_DIR,
        historical_graphs=sources.historical_graphs,
        causal_graph_verified=sources.causal_graph_verified,
        universe_ratification=False,
    )
    countercheck["ghv_traversal"] = crosscheck
    preservation = symbol_resolution["ORIGINAL_FLOW_PRESERVATION"]
    countercheck["symbol_resolver_synthetic_edges"] = preservation["synthetic_edge_count"]
    countercheck["historical_graph_edges_admitted_by_resolver"] = preservation[
        "historical_graph_edges_admitted"
    ]
    report = assemble_report_v1(
        {
            "commit": request.commit,
            "tree": request.tree,
            "boundary_status": status,
            "scope_manifest": {
                "projector_id": PROJECTOR_ID,
                "target_identity": TARGET_IDENTITY,
                "scope": SCOPE,
                "max_outer_depth": MAX_OUTER_DEPTH,
                "double_play": "INTERNAL_FUNCTIONAL_AREA",
                "full_universe_boundary_ratified": False,
                "current_boundary_implementation_proven": False,
                "automatic_universe_ratification": False,
                "starting_anchors": [
                    {
                        "component_id": REPLAY_COMPONENT_ID,
                        "role": "DECISION_START",
                        "automatic_member": False,
                    }
                ],
                "excluded": [
                    "INTERNAL_MV2_DEPTH",
                    "OTHER_UNIVERSES_EXCEPT_ADJACENT_PARTNERS",
                    "EXECUTION_GHOSV_MUTATION",
                    "CURRENT_CAUSAL_GRAPH_GHOSV",
                ],
            },
            "proven_members": proven_members,
            "unclassified_candidates": unclassified,
            "external_boundary_partners": external_partners,
            "inbound_boundary_edges": cut["inbound"],
            "outbound_boundary_edges": cut["outbound"],
            "unresolved_edges": cut["unresolved"],
            "unresolved_components": unresolved_components,
            "source_provenance": [
                {
                    "source_id": "S_OWNER_MV2_DECISION_PATH_BOUNDARY_V1",
                    "path": DECISION_SPEC_PATH,
                    "blob": sources.decision_blob,
                    "reference_baseline": sources.reference_baseline,
                    "authority": "REPOSITORY_REFERENCE_OF_RATIFIED_OWNER_DECISION",
                },
                {
                    "source_id": "S_CENSUS_NAV",
                    "path": CENSUS_PATH,
                    "blob": sources.census_blob,
                    "source_baseline_head": sources.census_pin,
                    "source_baseline_is_ancestor": sources.census_pin_is_ancestor,
                    "authority": "NONE",
                    "used_as_membership_proof": False,
                },
                {
                    "source_id": "S_LANDSCAPE_NAV",
                    "path": LANDSCAPE_PATH,
                    "authority_effect": sources.landscape_authority.get("authority_effect"),
                    "not_a_universe_ratification": sources.landscape_authority.get(
                        "not_a_universe_ratification"
                    ),
                    "labels_used_as_membership": False,
                },
                {
                    "source_id": "S_GHV_PINNED_HELPERS",
                    "loaded_from": sources.ghv.loaded_from,
                    "blob_ids": sources.ghv.blob_ids,
                    "worktree_drift_non_authoritative": sources.worktree_ghv_drift,
                    "authority": "NONE",
                },
                {
                    "source_id": "S_CAUSAL_INTEGRATION",
                    "path": CAUSAL_INTEGRATION_PATH,
                    "blob": sources.causal_integration_blob,
                    "invoked": False,
                    "current_causal_graph": sources.causal_graph_status,
                    "current_causal_graph_verified": sources.causal_graph_verified,
                },
                {
                    "source_id": "S_HISTORICAL_COMPOSED_GRAPHS",
                    "graphs": sources.historical_graphs,
                },
                {
                    "source_id": "S_GHOSV_EXECUTION",
                    "blob": sources.ghosv_execution_blob,
                    "modified": False,
                    "imported": False,
                },
                {
                    "source_id": "S_CURRENT_CAUSAL_GRAPH_GHOSV",
                    "paths": sources.current_graph_ghosv_paths,
                    "status": "NOT_IN_TREE" if not sources.current_graph_ghosv_paths else "PRESENT",
                },
                {
                    "source_id": "S_SYMBOL_ENDPOINT_RESOLVER",
                    "resolver_id": RESOLVER_ID,
                    "authority": "NONE",
                    "texts_loaded_from": "PINNED_COMMIT_BLOBS",
                    "historical_graphs_excluded": True,
                    "execution_ghosv_imported": False,
                    "causal_integration_invoked": False,
                },
            ],
            "coverage": {
                "max_outer_depth": MAX_OUTER_DEPTH,
                "proven_member_count": len(proven_members),
                "unclassified_candidate_count": len(unclassified),
                "resolved_boundary_edge_count": resolved_count,
                "unresolved_edge_count": len(cut["unresolved"]),
                "census_outer_edge_count": len(sources.census_outer_edges),
                "historical_graph_count": len(sources.historical_graphs),
                "current_causal_graph": sources.causal_graph_status,
                "internal_depth_included": False,
                "resolved_symbol_endpoint_count": len(
                    symbol_resolution["RESOLVED_SYMBOL_ENDPOINTS"]
                ),
                "proven_symbol_relation_count": len(symbol_resolution["PROVEN_SYMBOL_RELATIONS"]),
                "unresolved_symbol_endpoint_count": len(
                    symbol_resolution["UNRESOLVED_SYMBOL_ENDPOINTS"]
                ),
            },
            "uncertainties": sorted(
                [
                    "CURRENT_CAUSAL_GRAPH_NOT_MATERIALIZED",
                    "HISTORICAL_COMPOSED_GRAPHS_ARE_NOT_CURRENT_PROOF",
                    "CENSUS_AND_LANDSCAPE_ARE_NON_AUTHORITATIVE",
                    "PACKAGE_ENDPOINTS_ARE_UNRESOLVED",
                    "OWNER_RELATION_CLASS_UNKNOWN_WHERE_FLOW_IS_NOT_CORROBORATED",
                    "FULL_UNIVERSE_BOUNDARY_UNRATIFIED",
                    "DECISION_PATH_ANCHOR_IS_NOT_A_COMPLETE_ROSTER",
                    "SYMBOL_CLASS_UNKNOWN_WHERE_ONLY_A_NAME_IS_PRESENT",
                    "CRS_ATTACHMENT_IS_CONDITIONAL",
                    "ACTIVE_RUNTIME_OF_SYMBOL_RELATIONS_NOT_PROVEN",
                ]
            ),
            "countercheck_results": countercheck,
            "resolver_id": symbol_resolution["RESOLVER_ID"],
            "input_scope": symbol_resolution["INPUT_SCOPE"],
            "resolved_symbol_endpoints": symbol_resolution["RESOLVED_SYMBOL_ENDPOINTS"],
            "proven_symbol_relations": symbol_resolution["PROVEN_SYMBOL_RELATIONS"],
            "unresolved_symbol_endpoints": symbol_resolution["UNRESOLVED_SYMBOL_ENDPOINTS"],
            "original_flow_preservation": preservation,
        }
    )
    if output_path is not None:
        output_path.write_text(canonical_json_v1(report), encoding="utf-8")
    return report
