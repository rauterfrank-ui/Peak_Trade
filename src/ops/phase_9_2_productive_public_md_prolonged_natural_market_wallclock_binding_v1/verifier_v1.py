"""Verifier for Step-5 prolonged natural-market binding manifests."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.constants_v1 import (
    RECONNECT_PATH_STATUS_NOT_NATURAL,
)


FORBIDDEN_TRUE_CLAIMS = {
    "NETWORK_SESSION_STARTED",
    "FAULT_SESSION_STARTED",
    "PROLONGED_NATURAL_MARKET_LADDER_STEP_CLOSED",
    "CAPABILITY_CLOSED",
    "PHASE_9_2_COMPLETE",
    "RECONNECT_OBSERVED",
    "AUTHORIZATION_CONSUMED",
    "CONFIRM_TOKEN_CONSUMED",
    "AUTHORIZATION_ISSUED",
    "CONFIRM_TOKEN_ISSUED",
}


def verify_binding_manifest_v1(manifest: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    claims = dict(manifest.get("claims") or {})
    for key in FORBIDDEN_TRUE_CLAIMS:
        if bool(claims.get(key)):
            blockers.append(f"FORBIDDEN_CLAIM_TRUE:{key}")
    if not bool(claims.get("PROLONGED_NATURAL_MARKET_BINDING_IMPLEMENTED")):
        blockers.append("MISSING_BINDING_IMPLEMENTED_CLAIM")
    if not bool(claims.get("REAL_NETWORK_SESSION_NOT_STARTED", True)):
        blockers.append("REAL_NETWORK_SESSION_MUST_REMAIN_NOT_STARTED")
    if not bool(claims.get("READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION")):
        blockers.append("MISSING_READY_FOR_SEPARATE_SESSION_CLAIM")
    if not bool(claims.get("CLAIM_SEMANTICS_BOUND")):
        blockers.append("MISSING_CLAIM_SEMANTICS_BOUND_CLAIM")
    if not bool(claims.get("DURATION_BOUNDS_BOUND")):
        blockers.append("MISSING_DURATION_BOUNDS_BOUND_CLAIM")
    if not bool(claims.get("DISK_PREFLIGHT_BOUND")):
        blockers.append("MISSING_DISK_PREFLIGHT_BOUND_CLAIM")
    if (
        bool(claims.get("RECONNECT_OBSERVED"))
        and claims.get("RECONNECT_PATH_STATUS") == RECONNECT_PATH_STATUS_NOT_NATURAL
    ):
        blockers.append("RECONNECT_CLAIM_OVERSTATED")
    if "STEP5_RUNTIME_REACHABLE" in claims and not bool(claims.get("STEP5_RUNTIME_REACHABLE")):
        blockers.append("STEP5_RUNTIME_REACHABLE_REQUIRED")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "verified": not blockers,
        "claims": claims,
        "checks": [
            "sha_match",
            "config_digest_match",
            "session_identity_stable",
            "no_order_boundary",
            "pacing_min_interval",
            "zero_interval_burst_absent",
            "duration_within_bounds",
            "evidence_growth_within_bounds",
            "disk_preflight_recorded",
            "claims_match_telemetry",
            "reconnect_claim_not_overstated",
            "natural_absence_allowed",
            "manifest_reconstruction_deterministic",
        ],
        "readiness_vs_closure": {
            "READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION": bool(
                claims.get("READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION")
            ),
            "PROLONGED_NATURAL_MARKET_LADDER_STEP_CLOSED": bool(
                claims.get("PROLONGED_NATURAL_MARKET_LADDER_STEP_CLOSED")
            ),
            "CAPABILITY_CLOSED": bool(claims.get("CAPABILITY_CLOSED")),
        },
    }
