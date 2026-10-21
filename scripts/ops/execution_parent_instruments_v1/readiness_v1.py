"""Derive read-only readiness without promoting guardian or trading state."""

from __future__ import annotations

from typing import Any, Mapping

from scripts.ops.execution_parent_disclosure_v1.constants_v1 import (
    ACTIVATION,
    AUTHORITY,
    DOUBLE_PLAY_FULL_OWNER_LOCK,
    STATUS_ADMITTED,
)


def derive_execution_readiness_v1(
    *,
    admission: Mapping[str, Any],
    ghv: Mapping[str, Any],
    graph: Mapping[str, Any],
    ghosv: Mapping[str, Any],
) -> dict[str, Any]:
    """Readiness follows the three instrument results. It does not activate anything."""
    locks_hold = _locks(admission) and _locks(ghv) and _locks(graph) and _locks(ghosv)
    admission_ready = admission.get("status") == STATUS_ADMITTED and bool(
        admission.get("observed_subjects")
    )
    ghv_ready = (
        locks_hold
        and ghv.get("status") == "ACCEPTED"
        and ghv.get("composition_invoked") is True
        and ghv.get("files_written") is False
        and ghv.get("causal_closure_proven") is False
        and _walk_present(ghv)
    )
    graph_ready = (
        locks_hold
        and graph.get("status") == "ACCEPTED"
        and graph.get("projected") is True
        and graph.get("files_written") is False
        and graph.get("writer_invoked") is False
        and graph.get("causal_closure_proven") is False
        and graph.get("current_validated") is False
        and bool(graph.get("node_ids"))
        and bool(graph.get("edge_ids"))
    )
    ghosv_ready = (
        locks_hold
        and ghosv.get("status") == "ACCEPTED"
        and ghosv.get("findings_evaluated") is True
        and ghosv.get("files_written") is False
        and ghosv.get("safety_escalation_enabled") is False
        and ghosv.get("counts_as_proof") is False
    )
    toolchain_ready = admission_ready and ghv_ready and graph_ready and ghosv_ready
    return {
        "ADMISSION_READY": admission_ready,
        "GHV_READ_ONLY_READY": ghv_ready,
        "GRAPH_READ_ONLY_READY": graph_ready,
        "GHOSV_READ_ONLY_READY": ghosv_ready,
        "TOOLCHAIN_READ_ONLY_READY": toolchain_ready,
        "CURRENT_VALIDATED": False,
        "CAUSAL_CLOSURE_PROVEN": False,
        "GUARDIAN_ACTIVE": False,
        "authority": AUTHORITY,
        "activation": ACTIVATION,
        "membership_ratified": False,
        "guardian_ratified": False,
        "domain_bound": False,
        "operationally_ready": False,
        "post_allowed": False,
        "external_effect_authorized": False,
        "productive_activation": False,
        "double_play_full_owner_lock": DOUBLE_PLAY_FULL_OWNER_LOCK,
        "fixture_only": False,
        "productive_runtime_evidence": False,
        "evidence_mode": "PIN_BOUND_SOURCE_NOT_PRODUCTIVE_RUNTIME",
        "coverage_status": "PARTIAL" if ghv.get("coverage_gap") else "COMPLETE",
    }


def _locks(result: Mapping[str, Any]) -> bool:
    return (
        result.get("authority") == AUTHORITY
        and result.get("activation") == ACTIVATION
        and result.get("membership_ratified") is False
        and result.get("guardian_ratified") is False
        and result.get("domain_bound") is False
        and result.get("operationally_ready") is False
        and result.get("causal_closure_proven") is False
    )


def _walk_present(ghv: Mapping[str, Any]) -> bool:
    return all(isinstance(ghv.get(name), Mapping) for name in ("forward", "reverse", "transitive"))
