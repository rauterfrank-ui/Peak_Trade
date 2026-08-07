"""Campaign-owned may-start gates for Step-7 multi-session campaign.

Supports two confirm/authorization channels:
  REAL_TTY_HUMAN_CONFIRM — Hidden-PTY + Real-TTY required
  DELEGATED_CURSOR_SECURE_CONFIRM — EPHEMERAL_EXECUTION_LATCH; Real-TTY not required
"""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.hidden_pty_handoff_v1 import (
    assert_real_tty_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.constants_v1 import (
    ALLOWED_AUTHORIZATION_CHANNELS,
    AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
    AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM,
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    CAMPAIGN_EXECUTION_ALLOWED,
    CAMPAIGN_EXECUTION_SIDE_EFFECTS_AUTHORIZED,
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    CONFIRM_TOKEN_ISSUANCE_ALLOWED,
    CONFIRM_TOKEN_MINTING_ALLOWED,
    CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
    DEFAULT_AUTHORIZATION_CHANNEL,
    MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
    MODE_PROVE_IMPLEMENTATION_ONLY,
    MULTI_SESSION_REQUIREMENT_EXPRESSION,
    NETWORK_SESSION_ALLOWED,
    PHASE_9_2_STEP_6_STATUS,
    PHASE_9_2_STEP_7_STATUS,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    REAL_NETWORK_REQUESTS_ALLOWED,
    multi_session_requirement_satisfied_v1,
)
from src.ops.phase_9_2_step_7_productive_campaign_execution_path_v1.constants_v1 import (
    NETWORK_SESSION_ALLOWED as PATH_NETWORK_SESSION_ALLOWED,
)
from src.ops.phase_9_2_step_7_productive_campaign_execution_path_v1.constants_v1 import (
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED as PATH_PRODUCTIVE_AUTHORIZED,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.constants_v1 import (
    NETWORK_SESSION_ALLOWED as BINDING_NETWORK_SESSION_ALLOWED,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.constants_v1 import (
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED as BINDING_PRODUCTIVE_AUTHORIZED,
)


def evaluate_campaign_execution_gate_v1(
    *,
    mode: str,
    owner_go: bool,
    operator_authorization_explicit: bool,
    network_session_go: bool,
    public_md_only: bool,
    authorization_valid: bool,
    confirm_token_valid: bool,
    planned_session_count: int,
    productive_path_present: bool,
    productive_path_consumed: bool,
    harness_bound: bool,
    verifier_bound: bool,
    repository_sha_match: bool,
    config_digest_match: bool,
    stdin_isatty: bool | None = None,
    hidden_confirm_handoff_reachable: bool = True,
    private_endpoint_reachable: bool = False,
    auth_header_present: bool = False,
    credential_path_reachable: bool = False,
    order_side_effect_reachable: bool = False,
    allow_real_network_side_effects: bool = False,
    authorization_channel: str | None = None,
    delegated_secure_confirm_verified: bool = False,
    head_equals_origin_main: bool = False,
    tracked_worktree_clean: bool = False,
) -> dict[str, Any]:
    """Campaign-layer gate. Owns may_start; does not weaken Binding/Path forbid constants."""
    blockers: list[str] = []
    channel = str(authorization_channel or DEFAULT_AUTHORIZATION_CHANNEL)
    if NETWORK_SESSION_ALLOWED or REAL_NETWORK_REQUESTS_ALLOWED:
        blockers.append("PERMANENT_NETWORK_ENABLE_MUST_REMAIN_FALSE")
    if PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED:
        blockers.append("PERMANENT_PRODUCTIVE_EXECUTION_ENABLE_MUST_REMAIN_FALSE")
    if CAMPAIGN_EXECUTION_ALLOWED or CAMPAIGN_EXECUTION_SIDE_EFFECTS_AUTHORIZED:
        blockers.append("PERMANENT_CAMPAIGN_EXECUTION_ENABLE_MUST_REMAIN_FALSE")
    if BINDING_NETWORK_SESSION_ALLOWED or BINDING_PRODUCTIVE_AUTHORIZED:
        blockers.append("BINDING_NETWORK_FLAGS_MUST_REMAIN_FALSE")
    if PATH_NETWORK_SESSION_ALLOWED or PATH_PRODUCTIVE_AUTHORIZED:
        blockers.append("PATH_NETWORK_FLAGS_MUST_REMAIN_FALSE")
    if (
        CONFIRM_TOKEN_ISSUANCE_ALLOWED
        or CONFIRM_TOKEN_MINTING_ALLOWED
        or CONFIRM_TOKEN_CONSUMPTION_ALLOWED
        or AUTHORIZATION_CONSUMPTION_ALLOWED
    ):
        blockers.append("PERMANENT_TOKEN_OR_AUTH_CONSUMPTION_MUST_REMAIN_FALSE")
    if PHASE_9_2_STEP_6_STATUS != "CLOSED_PASS":
        blockers.append("STEP6_STATUS_MUST_BE_CLOSED_PASS")
    if PHASE_9_2_STEP_7_STATUS != "OPEN":
        blockers.append("STEP7_STATUS_MUST_REMAIN_OPEN")

    if mode == MODE_PROVE_IMPLEMENTATION_ONLY:
        return {
            "ok": not blockers,
            "blockers": blockers,
            "mode": MODE_PROVE_IMPLEMENTATION_ONLY,
            "campaign_may_start": False,
            "network_session_may_start": False,
            "AUTHORIZATION_CHANNEL": channel,
            "TOKEN_ROLE": CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
            "notes": ["IMPLEMENTATION_PROOF_MODE_NEVER_STARTS_NETWORK=true"],
        }

    if mode != MODE_GOVERNED_MULTI_SESSION_CAMPAIGN:
        blockers.append("UNKNOWN_EXECUTION_MODE")
        return {
            "ok": False,
            "blockers": blockers,
            "mode": mode,
            "campaign_may_start": False,
            "network_session_may_start": False,
            "AUTHORIZATION_CHANNEL": channel,
            "TOKEN_ROLE": CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
        }

    if channel not in ALLOWED_AUTHORIZATION_CHANNELS:
        blockers.append("UNKNOWN_AUTHORIZATION_CHANNEL")

    if not owner_go:
        blockers.append("OWNER_GO_REQUIRED")
    if not operator_authorization_explicit:
        blockers.append("OPERATOR_AUTHORIZATION_EXPLICIT_REQUIRED")
    if not network_session_go:
        blockers.append("NETWORK_SESSION_GO_REQUIRED")
    if not public_md_only:
        blockers.append("PUBLIC_MD_ONLY_REQUIRED")
    if not authorization_valid:
        blockers.append("AUTHORIZATION_INVALID")
    if not confirm_token_valid:
        blockers.append("CONFIRM_TOKEN_INVALID")
    if not multi_session_requirement_satisfied_v1(planned_session_count):
        blockers.append("MULTI_SESSION_REQUIREMENT_NOT_SATISFIED")
    if not productive_path_present:
        blockers.append("PRODUCTIVE_PATH_ABSENT")
    if not productive_path_consumed:
        blockers.append("PRODUCTIVE_PATH_NOT_CONSUMED")
    if not harness_bound:
        blockers.append("STEP7_CAMPAIGN_HARNESS_NOT_BOUND")
    if not verifier_bound:
        blockers.append("STEP7_CAMPAIGN_VERIFIER_NOT_BOUND")
    if not repository_sha_match:
        blockers.append("REPOSITORY_SHA_MISMATCH")
    if not config_digest_match:
        blockers.append("CONFIG_DIGEST_MISMATCH")

    real_tty_verified = False
    delegated_verified = False
    if channel == AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM:
        if not hidden_confirm_handoff_reachable:
            blockers.append("HIDDEN_CONFIRM_HANDOFF_UNREACHABLE")
        tty_blockers = assert_real_tty_v1(stdin_isatty=stdin_isatty)
        blockers.extend(tty_blockers)
        real_tty_verified = not tty_blockers and bool(stdin_isatty)
    elif channel == AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM:
        # Real-TTY explicitly NOT required; latch is EPHEMERAL_EXECUTION_LATCH.
        if not delegated_secure_confirm_verified:
            blockers.append("DELEGATED_SECURE_CONFIRM_REQUIRED")
        if not head_equals_origin_main:
            blockers.append("HEAD_NOT_EQUAL_ORIGIN_MAIN")
        if not tracked_worktree_clean:
            blockers.append("TRACKED_WORKTREE_DIRTY")
        if not allow_real_network_side_effects:
            blockers.append("REQUEST_REAL_NETWORK_REQUIRED_FOR_DELEGATED_CURSOR")
        delegated_verified = bool(
            delegated_secure_confirm_verified
            and head_equals_origin_main
            and tracked_worktree_clean
            and allow_real_network_side_effects
        )

    if private_endpoint_reachable:
        blockers.append("PRIVATE_ENDPOINT_REACHABLE_FORBIDDEN")
    if auth_header_present:
        blockers.append("AUTH_HEADER_PRESENT_FORBIDDEN")
    if credential_path_reachable:
        blockers.append("CREDENTIAL_PATH_REACHABLE_FORBIDDEN")
    if order_side_effect_reachable:
        blockers.append("ORDER_SIDE_EFFECT_REACHABLE_FORBIDDEN")

    structural_ok = not blockers
    may_start = structural_ok
    notes = [
        "CAMPAIGN_OWNED_MAY_START_GATE=true",
        "BINDING_AND_PATH_FORBID_CONSTANTS_UNCHANGED=true",
        "EPHEMERAL_GO_REQUIRED=true",
        f"AUTHORIZATION_CHANNEL={channel}",
        f"TOKEN_ROLE={CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH}",
        "TOKEN_IS_NOT_HUMAN_TTY_PRESENCE_PROOF=true",
        f"MULTI_SESSION_REQUIREMENT_EXPRESSION={MULTI_SESSION_REQUIREMENT_EXPRESSION}",
        f"PLANNED_SESSION_COUNT={int(planned_session_count)}",
        f"REAL_TTY_VERIFIED={real_tty_verified}",
        f"DELEGATED_SECURE_CONFIRM_VERIFIED={delegated_verified}",
    ]
    if allow_real_network_side_effects and not structural_ok:
        notes.append("REQUEST_REAL_NETWORK_IGNORED_WHILE_GATES_FAIL=true")

    return {
        "ok": structural_ok,
        "blockers": sorted(set(blockers)),
        "mode": MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        "campaign_may_start": bool(may_start),
        "network_session_may_start": bool(may_start),
        "structural_gates_pass": structural_ok,
        "planned_session_count": int(planned_session_count),
        "multi_session_requirement_expression": MULTI_SESSION_REQUIREMENT_EXPRESSION,
        "allow_real_network_side_effects_requested": bool(allow_real_network_side_effects),
        "AUTHORIZATION_CHANNEL": channel,
        "TOKEN_ROLE": CONFIRM_TOKEN_ROLE_EPHEMERAL_EXECUTION_LATCH,
        "REAL_TTY_VERIFIED": bool(real_tty_verified),
        "DELEGATED_SECURE_CONFIRM_VERIFIED": bool(delegated_verified),
        "notes": notes,
    }
