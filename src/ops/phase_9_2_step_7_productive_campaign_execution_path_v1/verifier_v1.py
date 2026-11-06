"""Verifiers for Step-7 productive campaign execution path manifests."""

from __future__ import annotations

from typing import Any, Mapping


FORBIDDEN_TRUE_PATH_CLAIMS = {
    "NETWORK_SESSION_STARTED",
    "CAMPAIGN_EXECUTED",
    "AUTHORIZATION_CONSUMED",
    "CONFIRM_TOKEN_CONSUMED",
    "CONFIRM_TOKEN_MINTED",
    "HIDDEN_CONFIRM_HANDOFF_USED",
    "MULTI_SESSION_CONTINUITY_LADDER_STEP_CLOSED",
    "PHASE_9_2_SESSION_LADDER_COMPLETE",
    "CAPABILITY_CLOSED",
    "PHASE_9_2_COMPLETE",
    "CORE_LOGIC_CHANGED",
    "TRADING_LOGIC_CHANGED",
    "STEP7_STARTED",
    "STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_ABSENT",
    "MULTI_SESSION_REQUIREMENT_SATISFIED_FOR_ONE",
    "STRUCTURAL_MAY_START_WITH_SINGLE_SESSION",
}

REQUIRED_TRUE_PATH_CLAIMS = {
    "STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PRESENT",
    "STEP7_BINDING_ONLY_PRESERVED",
    "PRODUCTIVE_CAMPAIGN_EXECUTOR_IMPLEMENTED",
    "PRODUCTIVE_EXECUTOR_REQUIRES_SEPARATE_OWNER_GO_CAMPAIGN",
    "REAL_TTY_REQUIRED",
    "HIDDEN_CONFIRM_HANDOFF_BOUND_FOR_LATER_CAMPAIGN",
    "EXPLICIT_CAMPAIGN_OWNER_GO_REQUIRED",
    "PUBLIC_MD_ONLY_ENFORCED",
    "ORDERS_DISABLED",
    "WALLCLOCK_OWNER_REUSED",
    "PRODUCTIVE_ENTRYPOINT_BOUND_TO_WALLCLOCK_RUNNER",
    "STEP7_CAMPAIGN_HARNESS_BOUND",
    "STEP7_CAMPAIGN_VERIFIER_PRESENT",
    "REPEATED_MULTI_SESSION_SUPPORTED",
    "READY_FOR_SEPARATE_OWNER_GO_CAMPAIGN_EXECUTION",
    "REAL_NETWORK_SESSION_FORBIDDEN_IN_IMPLEMENTATION_CAPABILITY",
}


def verify_productive_campaign_execution_path_manifest_v1(
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
    if str(claims.get("PHASE_9_2_STEP_6_STATUS") or "") != "CLOSED_PASS":
        blockers.append("STEP6_STATUS_MUST_BE_CLOSED_PASS")
    if str(claims.get("PHASE_9_2_STEP_7_STATUS") or "") != "OPEN":
        blockers.append("STEP7_STATUS_MUST_REMAIN_OPEN")
    if str(claims.get("MULTI_SESSION_REQUIREMENT_EXPRESSION") or "") != ">1":
        blockers.append("MULTI_SESSION_REQUIREMENT_EXPRESSION_MUST_BE_GT_ONE")
    if not bool(claims.get("MULTI_SESSION_REQUIREMENT_SATISFIED_FOR_TWO")):
        blockers.append("MULTI_SESSION_REQUIREMENT_TWO_MUST_PASS")
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
        "domain": "PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PROOF",
    }
