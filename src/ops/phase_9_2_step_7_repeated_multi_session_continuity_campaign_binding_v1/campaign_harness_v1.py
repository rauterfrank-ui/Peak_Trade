"""Campaign harness owner — binds Step-7 package without starting sessions."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_state_contract_v1 import (
    load_and_validate_campaign_state_contract_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.constants_v1 import (
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    CAMPAIGN_HARNESS_OWNER,
    CAMPAIGN_ID,
    CANONICAL_WALLCLOCK_RUNNER,
    CAPABILITY_ID,
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    CONFIRM_TOKEN_ISSUANCE_ALLOWED,
    NETWORK_SESSION_ALLOWED,
    PHASE_9_2_SESSION_LADDER_COMPLETE,
    PHASE_9_2_STEP_7_STATUS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    SESSION_LADDER_STEP,
    STEP3_RESTART_OWNER,
    STEP4_RECONNECT_OWNER,
    STEP6_STALE_ADVERSE_OWNER,
    STEP7_CAMPAIGN_BUNDLE_OWNER_PRESENT,
    STEP7_CAMPAIGN_HARNESS_BOUND,
    STEP7_CAMPAIGN_OWNER_PRESENT,
    STEP7_CAMPAIGN_VERIFIER_PRESENT,
    STEP7_PER_SESSION_EVIDENCE_CONTRACT_PRESENT,
    STEP7_PRODUCTIVE_ENTRYPOINT_PRESENT,
    TARGET_CAMPAIGN_CAPABILITY_ID,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.parity_v1 import (
    assert_no_parallel_campaign_authority_v1,
    prove_step7_reuse_bindings_v1,
    prove_phase92_step7_campaign_binding_parity_v1,
)


def evaluate_step7_binding_gate_v1(*, owner_go: bool, request_real_network: bool) -> dict[str, Any]:
    blockers: list[str] = []
    if not owner_go:
        blockers.append("OWNER_GO_REQUIRED")
    if request_real_network:
        blockers.append("REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY")
    if NETWORK_SESSION_ALLOWED:
        blockers.append("NETWORK_SESSION_ALLOWED_MUST_BE_FALSE")
    if PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED:
        blockers.append("PRODUCTIVE_NETWORK_EXECUTION_MUST_REMAIN_UNAUTHORIZED")
    if AUTHORIZATION_CONSUMPTION_ALLOWED or CONFIRM_TOKEN_CONSUMPTION_ALLOWED:
        blockers.append("AUTH_OR_CONFIRM_CONSUMPTION_MUST_REMAIN_FORBIDDEN")
    if CONFIRM_TOKEN_ISSUANCE_ALLOWED:
        blockers.append("CONFIRM_TOKEN_ISSUANCE_MUST_REMAIN_FORBIDDEN")
    if PHASE_9_2_STEP_7_STATUS != "OPEN":
        blockers.append("STEP7_STATUS_MUST_REMAIN_OPEN")
    if PHASE_9_2_SESSION_LADDER_COMPLETE:
        blockers.append("SESSION_LADDER_MUST_REMAIN_INCOMPLETE")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "NETWORK_SESSION_STARTED": False,
        "owner": CAMPAIGN_HARNESS_OWNER,
    }


def run_step7_campaign_harness_binding_v1(
    *,
    repository_sha: str,
    config_digest: str,
    owner_go: bool = True,
    request_real_network: bool = False,
    repo_root: Any = None,
) -> dict[str, Any]:
    """Bind campaign harness surfaces offline. Never starts a network session."""
    gate = evaluate_step7_binding_gate_v1(
        owner_go=owner_go, request_real_network=request_real_network
    )
    if not gate["ok"]:
        return {
            "ok": False,
            "blockers": list(gate["blockers"]),
            "NETWORK_SESSION_STARTED": False,
            "CAMPAIGN_EXECUTED": False,
            "PHASE_9_2_STEP_7_STATUS": PHASE_9_2_STEP_7_STATUS,
            "PHASE_9_2_SESSION_LADDER_COMPLETE": False,
            "owner": CAMPAIGN_HARNESS_OWNER,
        }

    contract = load_and_validate_campaign_state_contract_v1(repo_root=repo_root)
    parity = prove_phase92_step7_campaign_binding_parity_v1()
    reuse = prove_step7_reuse_bindings_v1()
    authority = assert_no_parallel_campaign_authority_v1()
    blockers: list[str] = []
    if not parity["ok"]:
        blockers.extend(parity["blockers"])
    if not reuse["ok"]:
        blockers.extend(reuse["blockers"])
    if not authority["ok"]:
        blockers.extend(authority["blockers"])

    return {
        "ok": not blockers,
        "blockers": blockers,
        "capability_id": CAPABILITY_ID,
        "target_campaign_capability_id": TARGET_CAMPAIGN_CAPABILITY_ID,
        "campaign_id": CAMPAIGN_ID,
        "session_ladder_step": SESSION_LADDER_STEP,
        "repository_sha": repository_sha,
        "config_digest": config_digest,
        "campaign_contract": contract,
        "parity": parity,
        "reuse": reuse,
        "authority": authority,
        "bindings": {
            "STEP7_CAMPAIGN_OWNER_PRESENT": STEP7_CAMPAIGN_OWNER_PRESENT,
            "STEP7_PRODUCTIVE_ENTRYPOINT_PRESENT": STEP7_PRODUCTIVE_ENTRYPOINT_PRESENT,
            "STEP7_CAMPAIGN_HARNESS_BOUND": STEP7_CAMPAIGN_HARNESS_BOUND,
            "STEP7_PER_SESSION_EVIDENCE_CONTRACT_PRESENT": (
                STEP7_PER_SESSION_EVIDENCE_CONTRACT_PRESENT
            ),
            "STEP7_CAMPAIGN_BUNDLE_OWNER_PRESENT": STEP7_CAMPAIGN_BUNDLE_OWNER_PRESENT,
            "STEP7_CAMPAIGN_VERIFIER_PRESENT": STEP7_CAMPAIGN_VERIFIER_PRESENT,
            "productive_entrypoint_path": PRODUCTIVE_ENTRYPOINT_PATH,
            "canonical_wallclock_runner_symbol": CANONICAL_WALLCLOCK_RUNNER,
            "step3_restart_owner": STEP3_RESTART_OWNER,
            "step4_reconnect_owner": STEP4_RECONNECT_OWNER,
            "step6_stale_adverse_owner": STEP6_STALE_ADVERSE_OWNER,
        },
        "NETWORK_SESSION_STARTED": False,
        "AUTHORIZATION_CONSUMED": False,
        "CONFIRM_TOKEN_MINTED": False,
        "CONFIRM_TOKEN_CONSUMED": False,
        "CAMPAIGN_EXECUTED": False,
        "PHASE_9_2_STEP_7_STATUS": "OPEN",
        "PHASE_9_2_SESSION_LADDER_COMPLETE": False,
        "owner": CAMPAIGN_HARNESS_OWNER,
    }


def exact_campaign_owner_path_v1() -> list[str]:
    return [
        "src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1."
        "campaign_harness_v1.run_step7_campaign_harness_binding_v1",
        "src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1."
        "campaign_bundle_v1.aggregate_completed_sessions_read_only_v1",
        "src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1."
        "campaign_verifier_v1.verify_campaign_bundle_v1",
    ]
