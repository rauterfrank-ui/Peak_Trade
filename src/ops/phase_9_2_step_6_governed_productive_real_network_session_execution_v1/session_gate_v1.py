"""Session-owned may-start gates for Step-6 productive Real-Network session execution."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.hidden_pty_handoff_v1 import (
    assert_real_tty_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.constants_v1 import (
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    CONFIRM_TOKEN_ISSUANCE_ALLOWED,
    CONFIRM_TOKEN_MINTING_ALLOWED,
    MODE_GOVERNED_REAL_NETWORK_SESSION,
    MODE_PROVE_IMPLEMENTATION_ONLY,
    NETWORK_SESSION_ALLOWED,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    REAL_NETWORK_REQUESTS_ALLOWED,
    SESSION_EXECUTION_ALLOWED,
    SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.constants_v1 import (
    NETWORK_SESSION_ALLOWED as PREDECESSOR_NETWORK_SESSION_ALLOWED,
)


def evaluate_session_execution_gate_v1(
    *,
    mode: str,
    owner_go: bool,
    operator_authorization_explicit: bool,
    network_session_go: bool,
    public_md_only: bool,
    authorization_valid: bool,
    confirm_token_valid: bool,
    stale_control_present: bool,
    productive_path_present: bool,
    productive_path_consumed: bool,
    repository_sha_match: bool,
    config_digest_match: bool,
    stdin_isatty: bool | None = None,
    hidden_confirm_handoff_reachable: bool = True,
    private_endpoint_reachable: bool = False,
    auth_header_present: bool = False,
    credential_path_reachable: bool = False,
    order_side_effect_reachable: bool = False,
    allow_real_network_side_effects: bool = False,
) -> dict[str, Any]:
    """Session-layer gate. Owns may_start; does not weaken Binding/Path forbid constants."""
    blockers: list[str] = []
    if NETWORK_SESSION_ALLOWED or REAL_NETWORK_REQUESTS_ALLOWED:
        blockers.append("PERMANENT_NETWORK_ENABLE_MUST_REMAIN_FALSE")
    if PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED:
        blockers.append("PERMANENT_PRODUCTIVE_EXECUTION_ENABLE_MUST_REMAIN_FALSE")
    if SESSION_EXECUTION_ALLOWED or SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED:
        blockers.append("PERMANENT_SESSION_EXECUTION_ENABLE_MUST_REMAIN_FALSE")
    if PREDECESSOR_NETWORK_SESSION_ALLOWED:
        blockers.append("PREDECESSOR_NETWORK_SESSION_ALLOWED_MUST_REMAIN_FALSE")
    if (
        CONFIRM_TOKEN_ISSUANCE_ALLOWED
        or CONFIRM_TOKEN_MINTING_ALLOWED
        or CONFIRM_TOKEN_CONSUMPTION_ALLOWED
        or AUTHORIZATION_CONSUMPTION_ALLOWED
    ):
        blockers.append("PERMANENT_TOKEN_OR_AUTH_CONSUMPTION_MUST_REMAIN_FALSE")

    if mode == MODE_PROVE_IMPLEMENTATION_ONLY:
        return {
            "ok": not blockers,
            "blockers": blockers,
            "mode": MODE_PROVE_IMPLEMENTATION_ONLY,
            "session_execution_may_start": False,
            "notes": ["IMPLEMENTATION_PROOF_MODE_NEVER_STARTS_NETWORK=true"],
        }

    if mode != MODE_GOVERNED_REAL_NETWORK_SESSION:
        blockers.append("UNKNOWN_EXECUTION_MODE")
        return {
            "ok": False,
            "blockers": blockers,
            "mode": mode,
            "session_execution_may_start": False,
        }

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
    if not stale_control_present:
        blockers.append("STALE_CONTROL_ABSENT")
    if not productive_path_present:
        blockers.append("PRODUCTIVE_PATH_ABSENT")
    if not productive_path_consumed:
        blockers.append("PRODUCTIVE_PATH_NOT_CONSUMED")
    if not repository_sha_match:
        blockers.append("REPOSITORY_SHA_MISMATCH")
    if not config_digest_match:
        blockers.append("CONFIG_DIGEST_MISMATCH")
    if not hidden_confirm_handoff_reachable:
        blockers.append("HIDDEN_CONFIRM_HANDOFF_UNREACHABLE")
    blockers.extend(assert_real_tty_v1(stdin_isatty=stdin_isatty))

    if private_endpoint_reachable:
        blockers.append("PRIVATE_ENDPOINT_REACHABLE_FORBIDDEN")
    if auth_header_present:
        blockers.append("AUTH_HEADER_PRESENT_FORBIDDEN")
    if credential_path_reachable:
        blockers.append("CREDENTIAL_PATH_REACHABLE_FORBIDDEN")
    if order_side_effect_reachable:
        blockers.append("ORDER_SIDE_EFFECT_REACHABLE_FORBIDDEN")

    structural_ok = not blockers
    # Session layer may authorize start under ephemeral GO. Actual invoke is separate.
    may_start = structural_ok
    notes = [
        "SESSION_OWNED_MAY_START_GATE=true",
        "BINDING_AND_PATH_FORBID_CONSTANTS_UNCHANGED=true",
        "EPHEMERAL_GO_REQUIRED=true",
    ]
    if allow_real_network_side_effects and not structural_ok:
        notes.append("REQUEST_REAL_NETWORK_IGNORED_WHILE_GATES_FAIL=true")

    return {
        "ok": structural_ok,
        "blockers": sorted(set(blockers)),
        "mode": MODE_GOVERNED_REAL_NETWORK_SESSION,
        "session_execution_may_start": bool(may_start),
        "structural_gates_pass": structural_ok,
        "allow_real_network_side_effects_requested": bool(allow_real_network_side_effects),
        "notes": notes,
    }
