"""In-memory execution graph projection. Does not call the writers."""

from __future__ import annotations

from typing import Any, Mapping

from scripts.ops.execution_parent_disclosure_v1.constants_v1 import (
    ACTIVATION,
    AUTHORITY,
    DOUBLE_PLAY_FULL_OWNER_LOCK,
)
from scripts.ops.execution_parent_instruments_v1.inventory_v1 import (
    AUTHORITY_READ_EDGE,
    DIRECT_DEPTH,
    FORWARD_ORIGIN,
    MISSION_END,
    MISSION_ID,
    MISSION_START,
    ONE_SHOT_CALL_EDGE,
    PRE_EXTERNAL_CALL_EDGE,
    REVERSE_ORIGIN,
    TRANSITIVE_DEPTH,
)
from scripts.ops.scoped_causal_graph_adapter_v1.adapt_v1 import _project_wp1
from scripts.ops.scoped_ghv_crosswalk_adapter_v1.adapt_v1 import _walk


def run_execution_graph_memory_v1(*, ghv: Mapping[str, Any]) -> dict[str, Any]:
    """Project the GHV handoff in memory and walk that projection."""
    if not ghv.get("composition_invoked"):
        return _envelope("NOT_PROJECTED", projected=False, reasons=["ghv_not_composed"])
    handoff = {
        "evaluated_nodes": list(ghv.get("evaluated_nodes") or []),
        "evaluated_edges": list(ghv.get("evaluated_edges") or []),
        "candidate_nodes": list(ghv.get("candidate_nodes") or []),
        "candidate_edges": list(ghv.get("candidate_edges") or []),
        "result_pin": str(ghv.get("baseline_commit") or ""),
        "coverage_gap": bool(ghv.get("coverage_gap")),
    }
    projected, reason = _project_wp1(
        wp_a1_result=handoff,
        declared_commit_sha=str(ghv.get("baseline_commit") or ""),
        declared_tree_sha=str(ghv.get("baseline_tree") or ""),
    )
    if projected is None:
        return _envelope("NOT_PROJECTED", projected=False, reasons=[reason or "projection_failed"])
    composed = {
        "evaluated_nodes": [str(node["source_native_id"]) for node in projected["nodes"]],
        "traversal_nodes": [
            {"source_native_id": str(node["source_native_id"])} for node in projected["nodes"]
        ],
        "traversal_edges": list(projected["edges"]),
        "census_objects": list(ghv.get("candidate_nodes") or []),
    }
    forward = _walk(composed, FORWARD_ORIGIN, "FORWARD", DIRECT_DEPTH)
    reverse = _walk(composed, REVERSE_ORIGIN, "REVERSE", DIRECT_DEPTH)
    transitive = _walk(composed, FORWARD_ORIGIN, "FORWARD", TRANSITIVE_DEPTH)
    submission_reverse = _walk(composed, MISSION_END, "REVERSE", DIRECT_DEPTH)
    submission_forward = _walk(composed, MISSION_END, "FORWARD", DIRECT_DEPTH)
    submission_transitive = _walk(composed, MISSION_END, "REVERSE", TRANSITIVE_DEPTH)
    unknown_edges = list(ghv.get("unknown_edges") or [])
    node_ids = [str(node["canonical_id"]) for node in projected["nodes"]]
    edge_ids = [str(edge["edge_id"]) for edge in projected["edges"]]
    evaluated = set(edge_ids)
    reached = set(forward.get("reachable") or [])
    decision_to_submission = "PROVEN" if MISSION_END in reached else "UNKNOWN"
    mission = {
        "mission_id": MISSION_ID,
        "start": MISSION_START,
        "end": MISSION_END,
        "forward_from_decision": list(forward.get("reachable") or []),
        "reverse_from_submission": list(submission_reverse.get("reachable") or []),
        "forward_from_submission": list(submission_forward.get("reachable") or []),
        "transitive_reverse_from_submission": list(submission_transitive.get("reachable") or []),
        "decision_to_submission": decision_to_submission,
        "pre_external_calls_decision": (
            "PROVEN" if PRE_EXTERNAL_CALL_EDGE in evaluated else "UNKNOWN"
        ),
        "one_shot_calls_submission": "PROVEN" if ONE_SHOT_CALL_EDGE in evaluated else "UNKNOWN",
        "submission_reads_external_effect_authority": (
            "PROVEN" if AUTHORITY_READ_EDGE in evaluated else "UNKNOWN"
        ),
        "unknown_edge_ids": [str(edge.get("edge_id") or "") for edge in unknown_edges],
        "coverage": "PARTIAL"
        if unknown_edges or decision_to_submission != "PROVEN"
        else "COMPLETE",
        "productive_runtime_evidence": False,
        "current_verified": False,
    }
    return _envelope(
        "ACCEPTED",
        projected=True,
        projection=projected,
        node_ids=node_ids,
        edge_ids=edge_ids,
        forward=forward,
        reverse=reverse,
        transitive=transitive,
        unknown_edges=unknown_edges,
        coverage_gap=bool(ghv.get("coverage_gap")),
        coverage_status="PARTIAL" if ghv.get("coverage_gap") else "COMPLETE",
        current_verified=bool(projected["current_verified"]),
        mission=mission,
        reasons=[],
    )


def _envelope(status: str, *, projected: bool, reasons: list[str], **extra: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "instrument_id": "PARENT_EXECUTION_CURRENT_CAUSAL_GRAPH",
        "status": status,
        "authority": AUTHORITY,
        "activation": ACTIVATION,
        "membership_ratified": False,
        "guardian_ratified": False,
        "domain_bound": False,
        "operationally_ready": False,
        "causal_closure_proven": False,
        "current_validated": False,
        "post_allowed": False,
        "external_effect_authorized": False,
        "productive_activation": False,
        "double_play_full_owner_lock": DOUBLE_PLAY_FULL_OWNER_LOCK,
        "files_written": False,
        "writer_invoked": False,
        "projected": projected,
        "global_causal_closure_proven": False,
        "reasons": reasons,
    }
    body.update(extra)
    return body
