"""Verifier for binding + productive executor wiring manifests.

Strictly separates:
  READY_FOR_PRODUCTIVE_SESSION_EXECUTION=true
from:
  RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED=true
"""

from __future__ import annotations

from typing import Any, Mapping


FORBIDDEN_TRUE_CLAIMS = {
    "NETWORK_SESSION_STARTED",
    "FAULT_SESSION_STARTED",
    "RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED",
    "PHASE_9_2_COMPLETE",
    "REAL_RATE_LIMIT_OBSERVED",
    "RATE_LIMIT_PATH_PRODUCTIVELY_OBSERVED",
    "RECONNECT_PATH_PRODUCTIVELY_OBSERVED",
}


def verify_binding_manifest_v1(manifest: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    claims = dict(manifest.get("claims") or {})
    for key in FORBIDDEN_TRUE_CLAIMS:
        if bool(claims.get(key)):
            blockers.append(f"FORBIDDEN_CLAIM_TRUE:{key}")
    if not bool(claims.get("RATE_LIMIT_RECONNECT_BINDING_IMPLEMENTED")):
        blockers.append("MISSING_BINDING_IMPLEMENTED_CLAIM")
    if not bool(claims.get("REAL_NETWORK_SESSION_NOT_STARTED", True)):
        blockers.append("REAL_NETWORK_SESSION_MUST_REMAIN_NOT_STARTED")
    if not bool(claims.get("READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION")):
        blockers.append("MISSING_READY_FOR_SEPARATE_SESSION_CLAIM")
    if not bool(claims.get("GOVERNED_FAULT_PATH_BOUND")):
        blockers.append("MISSING_GOVERNED_FAULT_PATH_BOUND_CLAIM")
    # Wiring readiness is required once executor evidence is present.
    if "READY_FOR_PRODUCTIVE_SESSION_EXECUTION" in claims:
        if not bool(claims.get("READY_FOR_PRODUCTIVE_SESSION_EXECUTION")):
            blockers.append("READY_FOR_PRODUCTIVE_SESSION_EXECUTION_MUST_BE_TRUE")
        if bool(claims.get("RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED")):
            blockers.append("LADDER_STEP_MUST_REMAIN_OPEN_IN_WIRING")
        if not bool(claims.get("EXECUTOR_CODE_EXISTS", True)):
            blockers.append("EXECUTOR_CODE_EXISTS_REQUIRED")
        if not bool(claims.get("EXECUTOR_PRODUCTIVELY_BOUND")):
            blockers.append("EXECUTOR_PRODUCTIVELY_BOUND_REQUIRED")
        if not bool(claims.get("PRODUCTIVE_SESSION_REACHABLE")):
            blockers.append("PRODUCTIVE_SESSION_REACHABLE_REQUIRED")
        if "PRODUCTIVE_STEP_4_SESSION_PATH_RUNTIME_REACHABLE" in claims:
            if not bool(claims.get("PRODUCTIVE_STEP_4_SESSION_PATH_RUNTIME_REACHABLE")):
                blockers.append("PRODUCTIVE_STEP_4_SESSION_PATH_RUNTIME_REACHABLE_REQUIRED")
        if "PRODUCTIVE_CALL_GRAPH_COMPLETE" in claims:
            if not bool(claims.get("PRODUCTIVE_CALL_GRAPH_COMPLETE")):
                blockers.append("PRODUCTIVE_CALL_GRAPH_COMPLETE_REQUIRED")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "verified": not blockers,
        "claims": claims,
        "readiness_vs_closure": {
            "READY_FOR_PRODUCTIVE_SESSION_EXECUTION": bool(
                claims.get("READY_FOR_PRODUCTIVE_SESSION_EXECUTION")
            ),
            "RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED": bool(
                claims.get("RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED")
            ),
        },
    }
