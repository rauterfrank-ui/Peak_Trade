"""Verifier for Step-7 Real-TTY campaign owner implementation manifests."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.constants_v1 import (
    PRODUCTIVE_CAMPAIGN_INVOKE_SYMBOL,
)


FORBIDDEN_TRUE_OWNER_IMPL_CLAIMS = {
    "NETWORK_SESSION_STARTED",
    "CAMPAIGN_EXECUTED",
    "AUTHORIZATION_CONSUMED",
    "CONFIRM_TOKEN_CONSUMED",
    "CONFIRM_TOKEN_MINTED",
    "HIDDEN_CONFIRM_HANDOFF_USED",
    "MULTI_SESSION_CONTINUITY_LADDER_STEP_CLOSED",
    "PHASE_9_2_SESSION_LADDER_COMPLETE",
    "CAPABILITY_CLOSED",
    "CORE_LOGIC_CHANGED",
    "TRADING_LOGIC_CHANGED",
    "STEP7_STARTED",
}

REQUIRED_TRUE_OWNER_IMPL_CLAIMS = {
    "STEP7_REAL_TTY_CAMPAIGN_OWNER_PRESENT",
    "STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_PRESENT",
    "STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_RUNTIME_REACHABLE",
    "STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PRESENT",
    "STEP7_BINDING_ONLY_PRESERVED",
    "BINDING_ONLY_NOT_USED_AS_CAMPAIGN_OWNER",
    "PATH_ALONE_CANNOT_START_CAMPAIGN",
    "PRODUCTIVE_PATH_CONSUMED",
    "STEP7_CAMPAIGN_HARNESS_BOUND",
    "STEP7_CAMPAIGN_VERIFIER_PRESENT",
    "REPEATED_MULTI_SESSION_SUPPORTED",
    "PUBLIC_MD_FETCHER_BOUND",
    "REAL_TTY_REQUIRED",
    "REAL_TTY_CHANNEL_SUPPORTED",
    "DELEGATED_CURSOR_SECURE_CONFIRM_SUPPORTED",
    "AUTH_CHANNEL_REAL_TTY_SUPPORTED",
    "AUTH_CHANNEL_DELEGATED_CURSOR_SUPPORTED",
    "HIDDEN_CONFIRM_HANDOFF_BOUND",
    "DELEGATED_CURSOR_SECURE_CONFIRM_BROKER_BOUND",
    "PUBLIC_MD_ONLY_ENFORCED",
    "ORDERS_DISABLED",
    "READY_FOR_SEPARATE_OWNER_GO_REAL_TTY_CAMPAIGN",
    "READY_FOR_SEPARATE_OWNER_GO_DELEGATED_CURSOR_CAMPAIGN",
    "CAMPAIGN_OWNED_MAY_START_UNDER_FULL_GO",
    "CAMPAIGN_OWNED_MAY_START_UNDER_DELEGATED_CURSOR",
}


def verify_campaign_execution_owner_implementation_manifest_v1(
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    blockers: list[str] = []
    claims = dict(manifest.get("claims") or {})
    for key in FORBIDDEN_TRUE_OWNER_IMPL_CLAIMS:
        if bool(claims.get(key)):
            blockers.append(f"FORBIDDEN_CLAIM_TRUE:{key}")
    for key in REQUIRED_TRUE_OWNER_IMPL_CLAIMS:
        if not bool(claims.get(key)):
            blockers.append(f"REQUIRED_TRUE_MISSING:{key}")
    if str(claims.get("PHASE_9_2_STEP_6_STATUS") or "") != "CLOSED_PASS":
        blockers.append("STEP6_STATUS_MUST_BE_CLOSED_PASS")
    if str(claims.get("PHASE_9_2_STEP_7_STATUS") or "") != "OPEN":
        blockers.append("STEP7_STATUS_MUST_REMAIN_OPEN")
    network_calls = claims.get("NETWORK_CALLS_DURING_THIS_CAPABILITY")
    if network_calls is None or int(network_calls) != 0:
        blockers.append("NETWORK_CALLS_MUST_BE_ZERO_IN_THIS_CAPABILITY")
    if bool(manifest.get("network_session_started")):
        blockers.append("NETWORK_SESSION_STARTED_IN_IMPLEMENTATION_MANIFEST")
    if bool(claims.get("CAMPAIGN_OWNED_MAY_START_WITHOUT_NETWORK_SESSION_GO")):
        blockers.append("MAY_START_WITHOUT_GO_MUST_BE_FALSE")
    if bool(claims.get("CAMPAIGN_OWNED_MAY_START_WITH_SINGLE_SESSION")):
        blockers.append("MAY_START_WITH_SINGLE_SESSION_MUST_BE_FALSE")
    if not bool(claims.get("CAMPAIGN_OWNED_MAY_START_UNDER_FULL_GO")):
        blockers.append("MAY_START_UNDER_FULL_GO_MUST_BE_TRUE")
    if bool(claims.get("STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_ABSENT")):
        blockers.append("PATH_ABSENT_CLAIM_MUST_BE_FALSE")
    if str(claims.get("PRODUCTIVE_CAMPAIGN_INVOKE_SYMBOL") or "") != (
        PRODUCTIVE_CAMPAIGN_INVOKE_SYMBOL
    ):
        blockers.append("PRODUCTIVE_CAMPAIGN_INVOKE_SYMBOL_MISMATCH")
    if str(claims.get("TOKEN_ROLE") or "") != "EPHEMERAL_EXECUTION_LATCH":
        blockers.append("TOKEN_ROLE_MUST_BE_EPHEMERAL_EXECUTION_LATCH")
    if str(claims.get("MULTI_SESSION_REQUIREMENT_EXPRESSION") or "") != ">1":
        blockers.append("MULTI_SESSION_REQUIREMENT_EXPRESSION_DRIFT")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "verified": not blockers,
        "claims": claims,
        "domain": "STEP7_REAL_TTY_CAMPAIGN_OWNER_IMPLEMENTATION_PROOF",
    }
