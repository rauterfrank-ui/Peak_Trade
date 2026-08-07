"""Verifiers for Step-6 productive Real-Network execution path manifests."""

from __future__ import annotations

from typing import Any, Mapping


FORBIDDEN_TRUE_PATH_CLAIMS = {
    "NETWORK_SESSION_STARTED",
    "SESSION_EXECUTED",
    "AUTHORIZATION_CONSUMED",
    "CONFIRM_TOKEN_CONSUMED",
    "CONFIRM_TOKEN_MINTED",
    "HIDDEN_CONFIRM_HANDOFF_USED",
    "ADVERSE_STALE_DATA_LADDER_STEP_CLOSED",
    "CAPABILITY_CLOSED",
    "PHASE_9_2_COMPLETE",
    "CORE_LOGIC_CHANGED",
    "TRADING_LOGIC_CHANGED",
    "STEP7_STARTED",
    "STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_ABSENT",
}

REQUIRED_TRUE_PATH_CLAIMS = {
    "STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT",
    "STEP6_BINDING_ONLY_EXECUTOR_PRESERVED",
    "PRODUCTIVE_REAL_NETWORK_EXECUTOR_IMPLEMENTED",
    "PRODUCTIVE_EXECUTOR_REQUIRES_SEPARATE_OWNER_GO_SESSION",
    "REAL_TTY_REQUIRED",
    "HIDDEN_CONFIRM_HANDOFF_BOUND_FOR_LATER_SESSION",
    "EXPLICIT_SESSION_OWNER_GO_REQUIRED",
    "PUBLIC_MD_ONLY_ENFORCED",
    "ORDERS_DISABLED",
    "GOVERNED_STALE_CONTROL_BOUND",
    "FAILURE_INJECTION_BOUND",
    "WALLCLOCK_OWNER_REUSED",
    "STEP6_VERIFIER_BOUND",
    "READY_FOR_SEPARATE_OWNER_GO_REAL_TTY_SESSION",
}


def verify_productive_execution_path_manifest_v1(
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    claims = dict(manifest.get("claims") or {})
    for key in FORBIDDEN_TRUE_PATH_CLAIMS:
        if bool(claims.get(key)):
            blockers.append(f"FORBIDDEN_CLAIM_TRUE:{key}")
    for key in REQUIRED_TRUE_PATH_CLAIMS:
        if not bool(claims.get(key)):
            blockers.append(f"REQUIRED_TRUE_MISSING:{key}")
    if str(claims.get("PHASE_9_2_STEP_6_STATUS") or "") != "OPEN":
        blockers.append("STEP6_STATUS_MUST_REMAIN_OPEN")
    if str(claims.get("PHASE_9_2_STEP_7_STATUS") or "") != "OPEN":
        blockers.append("STEP7_STATUS_MUST_REMAIN_OPEN")
    if int(claims.get("MAX_NETWORK_SESSION_COUNT") or 0) != 1:
        blockers.append("MAX_NETWORK_SESSION_COUNT_MUST_BE_ONE")
    network_calls = claims.get("NETWORK_CALLS_DURING_THIS_CAPABILITY")
    if network_calls is None or int(network_calls) != 0:
        blockers.append("NETWORK_CALLS_MUST_BE_ZERO_IN_THIS_CAPABILITY")
    if bool(manifest.get("network_session_started")):
        blockers.append("NETWORK_SESSION_STARTED_IN_PATH_MANIFEST")
    if bool(claims.get("STRUCTURAL_MAY_START_WITHOUT_NETWORK_SESSION_GO")):
        blockers.append("MAY_START_WITHOUT_GO_MUST_BE_FALSE")
    if not bool(claims.get("STRUCTURAL_MAY_START_UNDER_FULL_GO")):
        blockers.append("MAY_START_UNDER_FULL_GO_MUST_BE_TRUE")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "verified": not blockers,
        "claims": claims,
        "domain": "PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PROOF",
    }
