"""Verifier for binding manifests (implementation evidence only)."""

from __future__ import annotations

from typing import Any, Mapping


FORBIDDEN_TRUE_CLAIMS = {
    "NETWORK_SESSION_STARTED",
    "FAULT_SESSION_STARTED",
    "RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED",
    "PHASE_9_2_COMPLETE",
    "REAL_RATE_LIMIT_OBSERVED",
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
    return {
        "ok": not blockers,
        "blockers": blockers,
        "verified": not blockers,
        "claims": claims,
    }
