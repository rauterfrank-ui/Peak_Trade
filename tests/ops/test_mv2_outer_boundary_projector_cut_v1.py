"""WP2 classification and depth-1 cut tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.ops.mv2_outer_boundary_projector_v1.boundary_cut_v1 import cut_outer_edges_v1
from scripts.ops.mv2_outer_boundary_projector_v1.classification_v1 import (
    classify_membership_candidate_v1,
    derive_owner_relation_class_v1,
)
from scripts.ops.mv2_outer_boundary_projector_v1.constants_v1 import (
    FORBIDDEN_BOUNDARY_STATUSES,
    REPLAY_COMPONENT_ID,
)
from scripts.ops.mv2_outer_boundary_projector_v1.input_contract_v1 import ProjectorRequestV1
from scripts.ops.mv2_outer_boundary_projector_v1.output_contract_v1 import (
    canonical_json_v1,
    decide_boundary_status_v1,
)
from scripts.ops.mv2_outer_boundary_projector_v1.run_v1 import (
    run_mv2_outer_boundary_projector_v1,
)

REPO = Path(__file__).resolve().parents[2]
PIN_COMMIT = "7628005ae495c115ff341d32fa932b7f4642f456"
PIN_TREE = "e652f8d7b86c469311a068c34b0fb3f708c87d73"


def _mapper(edge: dict[str, object]) -> tuple[str | None, str]:
    flow = str(edge.get("flow_type") or "")
    if flow == "DATA_FLOW":
        return "PRODUCES", "GHV_NORMALIZATION"
    if flow == "DECISION_FLOW" and edge.get("contract_or_payload"):
        return "HANDOFF", "GHV_NORMALIZATION"
    if flow == "EVIDENCE_FLOW":
        return "OBSERVES", "GHV_NORMALIZATION"
    if flow == "PROMOTION_FLOW":
        return "AUTHORIZES", "GHV_NORMALIZATION"
    return None, "UNRESOLVED"


def test_rejected_bases_do_not_grant_membership() -> None:
    for basis in (
        "FILENAME",
        "DIRECTORY",
        "CENSUS_TAXONOMY",
        "LANDSCAPE_LABEL",
        "GRAPH_NEIGHBORHOOD",
    ):
        classified = classify_membership_candidate_v1(
            {
                "component_id": f"candidate:{basis}",
                "basis": basis,
                "exists_on_pin": True,
                "owner_places_in_joint_core": True,
                "code_confirms_role": True,
                "diff_empty": True,
            }
        )
        assert classified["classification"] == "POSSIBLE_MV2_MEMBER_UNCLASSIFIED"
        assert classified["universe_ratification"] is False
        assert classified["automatic_promotion"] is False


def test_missing_endpoint_and_unknown_semantics_stay_unresolved() -> None:
    cut = cut_outer_edges_v1(
        [
            {
                "edge_id": "missing-end",
                "source_id": "symbol:a",
                "target_id": "",
                "original_flow_type": "DATA",
                "endpoint_resolution": "COMPONENT",
                "corroboration": "CONTRACT:data",
                "baseline": PIN_COMMIT,
                "current_proof": True,
            },
            {
                "edge_id": "unknown-flow",
                "source_id": "symbol:a",
                "target_id": "symbol:b",
                "original_flow_type": "",
                "endpoint_resolution": "COMPONENT",
                "corroboration": "CONTRACT:data",
                "baseline": PIN_COMMIT,
                "current_proof": True,
            },
            {
                "edge_id": "decision-flow-kept",
                "source_id": "symbol:a",
                "target_id": "symbol:b",
                "original_flow_type": "DECISION_FLOW",
                "contract_or_payload": "SomeContract",
                "endpoint_resolution": "COMPONENT",
                "corroboration": "HANDOFF",
                "baseline": PIN_COMMIT,
                "current_proof": True,
            },
            {
                "edge_id": "authorizes-not-authority",
                "source_id": "symbol:a",
                "target_id": "symbol:b",
                "original_flow_type": "PROMOTION_FLOW",
                "endpoint_resolution": "COMPONENT",
                "corroboration": "AUTHORIZES",
                "baseline": PIN_COMMIT,
                "current_proof": True,
            },
        ],
        proven_member_ids=set(),
        proven_external_ids=set(),
        flow_mapper=_mapper,
    )
    by_id = {item["edge_id"]: item for item in cut["unresolved"]}
    assert by_id["missing-end"]["classification"] == "UNRESOLVED_EDGE"
    assert "UNRESOLVED_ENDPOINT" in str(by_id["missing-end"]["uncertainty"])
    assert by_id["unknown-flow"]["original_flow_type"] == "UNKNOWN"
    assert by_id["unknown-flow"]["owner_relation_class"] == "UNKNOWN"
    kept = by_id["decision-flow-kept"]
    assert kept["original_flow_type"] == "DECISION_FLOW"
    assert kept["ghv_edge_type"] == "HANDOFF"
    assert kept["ghv_edge_type_replaces_flow"] is False
    assert kept["owner_relation_class"] == "UNKNOWN"
    assert by_id["authorizes-not-authority"]["ghv_edge_type"] == "AUTHORIZES"
    assert by_id["authorizes-not-authority"]["owner_relation_class"] == "UNKNOWN"
    assert cut["inbound"] == []
    assert cut["outbound"] == []


def test_owner_class_does_not_equate_flow_names() -> None:
    assert derive_owner_relation_class_v1("DATA_FLOW", "CONTRACT:x") == "UNKNOWN"
    assert derive_owner_relation_class_v1("DECISION_FLOW", "CONTRACT:x") == "UNKNOWN"
    assert derive_owner_relation_class_v1("HANDOFF", "CONTRACT:x") == "UNKNOWN"
    assert derive_owner_relation_class_v1("AUTHORIZES", "CONTRACT:x") == "UNKNOWN"
    assert derive_owner_relation_class_v1("DATA", None) == "UNKNOWN"
    assert derive_owner_relation_class_v1("DATA", "CONTRACT:x") == "DATA"
    assert derive_owner_relation_class_v1("AUTHORITY", "HANDOFF") == "UNKNOWN"


def test_status_vocabulary_cannot_ratify() -> None:
    assert (
        decide_boundary_status_v1(
            causal_graph_verified=False,
            proven_count=1,
            resolved_count=1,
        )
        == "BLOCKED_BY_EVIDENCE"
    )
    assert (
        decide_boundary_status_v1(
            causal_graph_verified=True,
            proven_count=0,
            resolved_count=0,
        )
        == "NOT_PROVEN"
    )
    assert (
        decide_boundary_status_v1(
            causal_graph_verified=True,
            proven_count=1,
            resolved_count=0,
        )
        == "PARTIAL"
    )
    assert FORBIDDEN_BOUNDARY_STATUSES.isdisjoint({"PARTIAL", "NOT_PROVEN", "BLOCKED_BY_EVIDENCE"})


@pytest.fixture(scope="module")
def pinned_report() -> dict[str, object]:
    return run_mv2_outer_boundary_projector_v1(
        ProjectorRequestV1(commit=PIN_COMMIT, tree=PIN_TREE),
        repo_root=REPO,
    )


def test_pinned_run_keeps_partial_results_while_blocked(pinned_report: dict[str, object]) -> None:
    assert pinned_report["BOUNDARY_VERIFICATION_STATUS"] == "BLOCKED_BY_EVIDENCE"
    assert pinned_report["UNIVERSE_RATIFICATION"] is False
    assert pinned_report["BOUNDARY_VERIFICATION_STATUS"] not in FORBIDDEN_BOUNDARY_STATUSES
    proven = pinned_report["PROVEN_MEMBERS"]
    assert isinstance(proven, list)
    assert [item["component_id"] for item in proven] == [REPLAY_COMPONENT_ID]
    member = proven[0]
    assert member["automatic_promotion"] is False
    assert member["universe_ratification"] is False
    assert member["equated_to_census_id"] is False
    assert member["scope"] == "DECISION_START_SYMBOL_ONLY"
    unclassified = pinned_report["UNCLASSIFIED_CANDIDATES"]
    assert isinstance(unclassified, list)
    census_ids = [
        item["component_id"]
        for item in unclassified
        if str(item["component_id"]).startswith("census:")
    ]
    assert "census:SO-SRC-PKG:trading" in census_ids
    assert all(item["classification"] != "PROVEN_MV2_MEMBER" for item in unclassified)
    double_play = next(
        item
        for item in unclassified
        if item["component_id"] == "role:DOUBLE_PLAY_INTERNAL_FUNCTIONAL_AREA"
    )
    assert double_play["separate_universe"] is False
    historical = next(
        item
        for item in pinned_report["SOURCE_PROVENANCE"]
        if item["source_id"] == "S_HISTORICAL_COMPOSED_GRAPHS"
    )
    assert historical["graphs"]
    assert all(graph["current_proof"] is False for graph in historical["graphs"])
    assert all(
        graph["edges_used_as_current_boundary_proof"] is False for graph in historical["graphs"]
    )
    unresolved = pinned_report["UNRESOLVED_EDGES"]
    assert isinstance(unresolved, list) and unresolved
    data_edges = [item for item in unresolved if item["original_flow_type"] == "DATA_FLOW"]
    assert data_edges
    assert all(item["owner_relation_class"] == "UNKNOWN" for item in data_edges)
    assert any(item["ghv_edge_type"] == "PRODUCES" for item in data_edges)
    assert all(item["ghv_edge_type_replaces_flow"] is False for item in unresolved)
    decision_edges = [item for item in unresolved if item["original_flow_type"] == "DECISION_FLOW"]
    assert decision_edges
    assert all(item["owner_relation_class"] == "UNKNOWN" for item in decision_edges)
    assert any(item["ghv_edge_type"] == "HANDOFF" for item in decision_edges)
    assert pinned_report["INBOUND_BOUNDARY_EDGES"] == []
    assert pinned_report["OUTBOUND_BOUNDARY_EDGES"] == []
    causal = next(
        item
        for item in pinned_report["SOURCE_PROVENANCE"]
        if item["source_id"] == "S_CAUSAL_INTEGRATION"
    )
    assert causal["invoked"] is False
    assert causal["current_causal_graph"] == "NOT_MATERIALIZED"
    ghosv = next(
        item
        for item in pinned_report["SOURCE_PROVENANCE"]
        if item["source_id"] == "S_CURRENT_CAUSAL_GRAPH_GHOSV"
    )
    assert ghosv["status"] == "NOT_IN_TREE"


def test_blocked_run_still_emits_a_resolved_fixture_edge() -> None:
    report = run_mv2_outer_boundary_projector_v1(
        ProjectorRequestV1(
            commit=PIN_COMMIT,
            tree=PIN_TREE,
            extra_external_partners=(
                {
                    "component_id": "symbol:fixture.external",
                    "outside_evidence": "OWNER_AUTHORITY_NON_TRANSFER",
                },
            ),
            extra_edges=(
                {
                    "edge_id": "fixture-resolved-in",
                    "source_id": "symbol:fixture.external",
                    "target_id": REPLAY_COMPONENT_ID,
                    "original_flow_type": "DATA",
                    "corroboration": "CONTRACT:fixture-data",
                    "endpoint_resolution": "COMPONENT",
                    "baseline": PIN_COMMIT,
                },
                {
                    "edge_id": "historical-neighbor",
                    "source_id": "symbol:old",
                    "target_id": REPLAY_COMPONENT_ID,
                    "original_flow_type": "DATA",
                    "corroboration": "CONTRACT:old",
                    "endpoint_resolution": "COMPONENT",
                    "baseline": "b6ffca1d3b39b3dd8814c7c795a8aa6e04bc177a",
                },
            ),
            extra_candidates=(
                {
                    "component_id": "name:master_v2_neighbor",
                    "basis": "GRAPH_NEIGHBORHOOD",
                    "exists_on_pin": True,
                    "owner_places_in_joint_core": True,
                    "code_confirms_role": True,
                    "diff_empty": True,
                },
            ),
        ),
        repo_root=REPO,
    )
    assert report["BOUNDARY_VERIFICATION_STATUS"] == "BLOCKED_BY_EVIDENCE"
    assert [item["edge_id"] for item in report["INBOUND_BOUNDARY_EDGES"]] == ["fixture-resolved-in"]
    inbound = report["INBOUND_BOUNDARY_EDGES"][0]
    assert inbound["original_flow_type"] == "DATA"
    assert inbound["owner_relation_class"] == "DATA"
    assert inbound["classification"] == "RESOLVED_CROSS_BOUNDARY_EDGE"
    historical = next(
        item for item in report["UNRESOLVED_EDGES"] if item["edge_id"] == "historical-neighbor"
    )
    assert historical["provenance"]["current_proof"] is False
    assert "name:master_v2_neighbor" not in {
        item["component_id"] for item in report["PROVEN_MEMBERS"]
    }
    partners = {item["component_id"] for item in report["EXTERNAL_BOUNDARY_PARTNERS"]}
    assert partners == {"symbol:fixture.external"}


def test_pinned_report_is_deterministic(pinned_report: dict[str, object]) -> None:
    again = run_mv2_outer_boundary_projector_v1(
        ProjectorRequestV1(commit=PIN_COMMIT, tree=PIN_TREE),
        repo_root=REPO,
    )
    assert canonical_json_v1(pinned_report) == canonical_json_v1(again)
    parsed = json.loads(canonical_json_v1(pinned_report))
    assert parsed["PROJECTOR_ID"] == "MV2_OUTER_BOUNDARY_PROJECTOR_V1"
