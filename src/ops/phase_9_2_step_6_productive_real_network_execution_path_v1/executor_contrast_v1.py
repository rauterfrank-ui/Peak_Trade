"""Explicit contrast: BINDING_EXECUTOR vs PRODUCTIVE_REAL_NETWORK_EXECUTOR."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.constants_v1 import (
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED as BINDING_PRODUCTIVE_AUTHORIZED,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.governed_session_execution_v1 import (
    evaluate_productive_session_gate_v1 as evaluate_binding_gate_v1,
    execute_governed_step6_productive_session_offline_fail_closed_v1,
    request_real_network_offline_fail_closed_v1,
)
from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.constants_v1 import (
    BINDING_EXECUTOR_CAPABILITY_ID,
    BINDING_EXECUTOR_ROLE,
    CAPABILITY_ID,
    MODE_GOVERNED_REAL_NETWORK_SESSION,
    PRODUCTIVE_REAL_NETWORK_EXECUTOR_ROLE,
)
from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.productive_executor_v1 import (
    evaluate_productive_real_network_execution_gate_v1,
)


def prove_binding_vs_productive_executor_contrast_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
) -> dict[str, Any]:
    """Prove only the productive executor can authorize may_start under ephemeral GO."""
    blockers: list[str] = []

    binding_gate = evaluate_binding_gate_v1(
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stale_control_present=True,
        stdin_isatty=True,
    )
    if binding_gate.get("network_session_may_start"):
        blockers.append("BINDING_EXECUTOR_MUST_NEVER_AUTHORIZE_MAY_START")

    binding_exec = execute_governed_step6_productive_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        authorization_id="auth_contrast",
        authorization_digest="a" * 64,
        confirm_token_binding_sha256="b" * 64,
        getpass_fn=lambda _p: "contrast-token",
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        allow_real_network_side_effects=True,
        enable_receive_lag=True,
        stdin_isatty=True,
    )
    if binding_exec.network_session_started:
        blockers.append("BINDING_EXECUTOR_STARTED_NETWORK")
    if "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY" not in binding_exec.blockers:
        blockers.append("BINDING_EXECUTOR_MUST_REMAIN_REAL_NETWORK_FORBIDDEN")
    if BINDING_PRODUCTIVE_AUTHORIZED:
        blockers.append("BINDING_PRODUCTIVE_AUTHORIZED_MUST_REMAIN_FALSE")

    binding_req = request_real_network_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        stdin_isatty=True,
    )
    if binding_req.ok or binding_req.network_session_started:
        blockers.append("BINDING_REQUEST_REAL_NETWORK_MUST_FAIL_CLOSED")

    productive_full = evaluate_productive_real_network_execution_gate_v1(
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stale_control_present=True,
        stdin_isatty=True,
    )
    if not productive_full.get("network_session_may_start"):
        blockers.append("PRODUCTIVE_EXECUTOR_MUST_AUTHORIZE_MAY_START_UNDER_FULL_GO")

    productive_no_go = evaluate_productive_real_network_execution_gate_v1(
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=False,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stale_control_present=True,
        stdin_isatty=True,
    )
    if productive_no_go.get("network_session_may_start"):
        blockers.append("PRODUCTIVE_EXECUTOR_MUST_NOT_AUTHORIZE_WITHOUT_NETWORK_SESSION_GO")

    ok = not blockers
    return {
        "ok": ok,
        "blockers": sorted(set(blockers)),
        "capability_id": CAPABILITY_ID,
        "binding_executor": {
            "role": BINDING_EXECUTOR_ROLE,
            "capability_id": BINDING_EXECUTOR_CAPABILITY_ID,
            "network_session_may_start": bool(binding_gate.get("network_session_may_start")),
            "real_network_forbidden": (
                "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY" in binding_exec.blockers
            ),
            "network_session_started": bool(binding_exec.network_session_started),
            "productive_network_session_execution_authorized": BINDING_PRODUCTIVE_AUTHORIZED,
            "request_real_network_ok": bool(binding_req.ok),
        },
        "productive_real_network_executor": {
            "role": PRODUCTIVE_REAL_NETWORK_EXECUTOR_ROLE,
            "capability_id": CAPABILITY_ID,
            "network_session_may_start_under_full_go": bool(
                productive_full.get("network_session_may_start")
            ),
            "network_session_may_start_without_network_session_go": bool(
                productive_no_go.get("network_session_may_start")
            ),
            "network_session_started_in_this_capability": False,
            "requires_separate_owner_go_session": True,
        },
        "claims": {
            "BINDING_EXECUTOR_PRESERVED_FAIL_CLOSED": ok
            and not bool(binding_gate.get("network_session_may_start")),
            "ONLY_PRODUCTIVE_EXECUTOR_CAN_AUTHORIZE_MAY_START": ok
            and bool(productive_full.get("network_session_may_start")),
            "PRODUCTIVE_EXECUTOR_REQUIRES_NETWORK_SESSION_GO": ok
            and not bool(productive_no_go.get("network_session_may_start")),
            "NETWORK_SESSION_STARTED": False,
            "CONFIRM_TOKEN_MINTED": False,
            "CONFIRM_TOKEN_CONSUMED": False,
        },
        "notes": [
            "BINDING_EXECUTOR=always forbids Real-Network side effects",
            "PRODUCTIVE_REAL_NETWORK_EXECUTOR=may authorize may_start under ephemeral GO",
            "ONLY_LATER_SEPARATE_OWNER_GO_SESSION_MAY_START_NETWORK=true",
        ],
    }
