"""In-memory execution GHV over admitted disclosure subjects. AUTHORITY=NONE."""

from __future__ import annotations

from typing import Any, Mapping

from scripts.ops.execution_parent_disclosure_v1.constants_v1 import (
    ACTIVATION,
    AUTHORITY,
    DOUBLE_PLAY_FULL_OWNER_LOCK,
    STATUS_ADMITTED,
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
from scripts.ops.scoped_ghv_crosswalk_adapter_v1.adapt_v1 import (
    _impact,
    _walk,
    compose_scoped_candidate_v1,
    integration_edge_rejection_v1,
)

_EVIDENCE_REVISION_KEY = "baseline_commit"


def run_execution_ghv_disclosure_v1(
    *,
    admission: Mapping[str, Any],
    call_edges: list[dict[str, Any]],
    unknown_edges: list[Mapping[str, Any]],
    policy_guards: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compose and walk only subjects the admission already accepted."""
    if admission.get("status") != STATUS_ADMITTED:
        return _envelope(str(admission.get("status") or "REJECTED"), composition_invoked=False)
    allowed = [
        str(subject["subject_id"])
        for subject in admission.get("observed_subjects") or []
        if isinstance(subject, Mapping)
    ]
    if not allowed:
        return _envelope("DISCLOSURE_SCOPE_ABSENT", composition_invoked=False)
    revision = str(admission.get(_EVIDENCE_REVISION_KEY) or "")
    if not revision:
        return _envelope("FAIL_CLOSED", composition_invoked=False)
    ready_edges: list[dict[str, Any]] = []
    rejected_edges: list[dict[str, str]] = []
    for edge in call_edges:
        if edge["source_native_id"] not in allowed or edge["target_native_id"] not in allowed:
            rejected_edges.append(
                {"edge_id": str(edge["edge_id"]), "reason": "endpoint_not_admitted"}
            )
            continue
        reason = integration_edge_rejection_v1(edge)
        if reason is not None:
            rejected_edges.append({"edge_id": str(edge["edge_id"]), "reason": reason})
            continue
        ready_edges.append(edge)
    nodes = [_node(subject_id, revision) for subject_id in allowed]
    composed = compose_scoped_candidate_v1(
        candidate_nodes=nodes,
        candidate_edges=ready_edges,
        allowed_nodes=allowed,
        exclusions=[],
        unassigned=[],
        evidence_revision=revision,
    )
    forward = _walk(composed, FORWARD_ORIGIN, "FORWARD", DIRECT_DEPTH)
    reverse = _walk(composed, REVERSE_ORIGIN, "REVERSE", DIRECT_DEPTH)
    transitive = _walk(composed, FORWARD_ORIGIN, "FORWARD", TRANSITIVE_DEPTH)
    impact = _impact(composed, FORWARD_ORIGIN, TRANSITIVE_DEPTH)
    submission_reverse = _walk(composed, MISSION_END, "REVERSE", DIRECT_DEPTH)
    submission_forward = _walk(composed, MISSION_END, "FORWARD", DIRECT_DEPTH)
    submission_transitive = _walk(composed, MISSION_END, "REVERSE", TRANSITIVE_DEPTH)
    kept = set(composed["evaluated_edges"])
    candidate_edges = [edge for edge in ready_edges if edge["edge_id"] in kept]
    coverage_gap = bool(
        forward["coverage_gap"] or reverse["coverage_gap"] or transitive["coverage_gap"]
    )
    coverage_gap = coverage_gap or bool(rejected_edges) or bool(unknown_edges)
    mission = _mission(
        evaluated_edges=kept,
        unknown_edges=unknown_edges,
        policy_guards=list(policy_guards or []),
        forward=forward,
        submission_reverse=submission_reverse,
        submission_forward=submission_forward,
        submission_transitive=submission_transitive,
    )
    return _envelope(
        "ACCEPTED",
        composition_invoked=True,
        observed_subject_ids=allowed,
        evaluated_nodes=list(composed["evaluated_nodes"]),
        evaluated_edges=list(composed["evaluated_edges"]),
        candidate_nodes=nodes,
        candidate_edges=candidate_edges,
        forward=forward,
        reverse=reverse,
        transitive=transitive,
        impact=impact,
        unknown_edges=[dict(edge) for edge in unknown_edges] + rejected_edges,
        coverage_gap=coverage_gap,
        coverage_status="PARTIAL" if coverage_gap else "COMPLETE",
        baseline_commit=revision,
        baseline_tree=str(admission.get("baseline_tree") or ""),
        mission=mission,
    )


def _mission(
    *,
    evaluated_edges: set[str],
    unknown_edges: list[Mapping[str, Any]],
    policy_guards: list[Mapping[str, Any]],
    forward: Mapping[str, Any],
    submission_reverse: Mapping[str, Any],
    submission_forward: Mapping[str, Any],
    submission_transitive: Mapping[str, Any],
) -> dict[str, Any]:
    reached = set(forward.get("reachable") or [])
    decision_to_submission = "PROVEN" if MISSION_END in reached else "UNKNOWN"
    return {
        "mission_id": MISSION_ID,
        "start": MISSION_START,
        "end": MISSION_END,
        "forward_from_decision": list(forward.get("reachable") or []),
        "reverse_from_submission": list(submission_reverse.get("reachable") or []),
        "forward_from_submission": list(submission_forward.get("reachable") or []),
        "transitive_reverse_from_submission": list(submission_transitive.get("reachable") or []),
        "decision_to_submission": decision_to_submission,
        "pre_external_calls_decision": (
            "PROVEN" if PRE_EXTERNAL_CALL_EDGE in evaluated_edges else "UNKNOWN"
        ),
        "one_shot_calls_submission": (
            "PROVEN" if ONE_SHOT_CALL_EDGE in evaluated_edges else "UNKNOWN"
        ),
        "submission_reads_external_effect_authority": (
            "PROVEN" if AUTHORITY_READ_EDGE in evaluated_edges else "UNKNOWN"
        ),
        "policy_guards": [dict(guard) for guard in policy_guards],
        "unknown_edge_ids": [str(edge.get("edge_id") or "") for edge in unknown_edges],
        "coverage": "PARTIAL"
        if unknown_edges or decision_to_submission != "PROVEN"
        else "COMPLETE",
        "productive_runtime_evidence": False,
    }


def _node(subject_id: str, revision: str) -> dict[str, Any]:
    return {
        "object_id": subject_id,
        "evidence_plane": "DOMAIN_CODE_REFERENCE",
        "reachability": "UNKNOWN",
        "evidence_revision": revision,
    }


def _envelope(status: str, *, composition_invoked: bool, **extra: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "instrument_id": "PARENT_EXECUTION_GHV",
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
        "adapters_invoked": False,
        "parent_assignment_performed": False,
        "functional_membership_derived": False,
        "domain_functional_members": [],
        "composition_invoked": composition_invoked,
        "productive_runtime_evidence": False,
    }
    body.update(extra)
    return body
