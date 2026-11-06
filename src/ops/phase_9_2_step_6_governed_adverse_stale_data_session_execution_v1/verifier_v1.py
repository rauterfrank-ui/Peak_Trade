"""Verifiers for Step-6 governed session execution binding manifests."""

from __future__ import annotations

from typing import Any, Mapping


FORBIDDEN_TRUE_BINDING_CLAIMS = {
    "NETWORK_SESSION_STARTED",
    "SESSION_EXECUTED",
    "AUTHORIZATION_CONSUMED",
    "CONFIRM_TOKEN_CONSUMED",
    "ADVERSE_STALE_DATA_LADDER_STEP_CLOSED",
    "CAPABILITY_CLOSED",
    "PHASE_9_2_COMPLETE",
    "STEP4_TRANSPORT_FAULT_SEMANTICS_CHANGED",
    "CORE_LOGIC_CHANGED",
}


REQUIRED_TRUE_BINDING_CLAIMS = {
    "PRODUCTIVE_CALLER_BOUND",
    "RUNTIME_REACHABLE",
    "GOVERNED_STALE_CONTROL_PRODUCTIVELY_BOUND",
    "WALLCLOCK_RECEIVE_PATH_BOUND",
    "STALE_CONTROL_DEFAULT_DISABLED",
    "GOVERNED_EXECUTION_NETWORK_SESSION_GATE_EXISTS",
    "REAL_TTY_REQUIRED",
    "CANONICAL_CONFIRM_HANDOFF_BOUND",
    "PUBLIC_MD_ONLY_BOUNDARY_PRESERVED",
    "READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION",
}


def verify_execution_binding_manifest_v1(manifest: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    claims = dict(manifest.get("claims") or {})
    for key in FORBIDDEN_TRUE_BINDING_CLAIMS:
        if bool(claims.get(key)):
            blockers.append(f"FORBIDDEN_CLAIM_TRUE:{key}")
    for key in REQUIRED_TRUE_BINDING_CLAIMS:
        if not bool(claims.get(key)):
            blockers.append(f"REQUIRED_TRUE_MISSING:{key}")
    if str(claims.get("PHASE_9_2_STEP_6_STATUS") or "") != "OPEN":
        blockers.append("STEP6_STATUS_MUST_REMAIN_OPEN")
    if bool(manifest.get("network_session_started")):
        blockers.append("NETWORK_SESSION_STARTED_IN_BINDING_MANIFEST")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "verified": not blockers,
        "claims": claims,
        "domain": "EXECUTION_BINDING_PROOF",
    }
