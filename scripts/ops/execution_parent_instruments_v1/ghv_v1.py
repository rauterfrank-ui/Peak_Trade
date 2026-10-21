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
    DIRECT_DEPTH,
    FORWARD_ORIGIN,
    REVERSE_ORIGIN,
    TRANSITIVE_DEPTH,
)
from scripts.ops.scoped_ghv_crosswalk_adapter_v1.adapt_v1 import (
    _impact,
    _walk,
    compose_scoped_candidate_v1,
    integration_edge_rejection_v1,
)

_EVIDENCE_REVISION = "37e51e3c7988026d2caa8c9a83ff46a056e416a8"


def run_execution_ghv_disclosure_v1(
    *,
    admission: Mapping[str, Any],
    call_edges: list[dict[str, Any]],
    unknown_edge: Mapping[str, Any],
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
    nodes = [_node(subject_id) for subject_id in allowed]
    composed = compose_scoped_candidate_v1(
        candidate_nodes=nodes,
        candidate_edges=ready_edges,
        allowed_nodes=allowed,
        exclusions=[],
        unassigned=[],
        evidence_revision=_EVIDENCE_REVISION,
    )
    forward = _walk(composed, FORWARD_ORIGIN, "FORWARD", DIRECT_DEPTH)
    reverse = _walk(composed, REVERSE_ORIGIN, "REVERSE", DIRECT_DEPTH)
    transitive = _walk(composed, FORWARD_ORIGIN, "FORWARD", TRANSITIVE_DEPTH)
    impact = _impact(composed, FORWARD_ORIGIN, TRANSITIVE_DEPTH)
    kept = set(composed["evaluated_edges"])
    candidate_edges = [edge for edge in ready_edges if edge["edge_id"] in kept]
    coverage_gap = bool(
        forward["coverage_gap"] or reverse["coverage_gap"] or transitive["coverage_gap"]
    )
    coverage_gap = coverage_gap or bool(rejected_edges) or bool(unknown_edge)
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
        unknown_edges=[dict(unknown_edge), *rejected_edges],
        coverage_gap=coverage_gap,
    )


def _node(subject_id: str) -> dict[str, Any]:
    return {
        "object_id": subject_id,
        "evidence_plane": "DOMAIN_CODE_REFERENCE",
        "reachability": "UNKNOWN",
        "evidence_revision": _EVIDENCE_REVISION,
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
