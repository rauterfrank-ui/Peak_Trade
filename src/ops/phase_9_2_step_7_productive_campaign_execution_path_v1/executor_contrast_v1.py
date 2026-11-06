"""Explicit contrast: BINDING_CAMPAIGN_EXECUTOR vs PRODUCTIVE_CAMPAIGN_EXECUTOR."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_step_7_productive_campaign_execution_path_v1.constants_v1 import (
    BINDING_CAMPAIGN_CAPABILITY_ID,
    BINDING_CAMPAIGN_ROLE,
    CAPABILITY_ID,
    MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
    PRODUCTIVE_CAMPAIGN_EXECUTOR_ROLE,
)
from src.ops.phase_9_2_step_7_productive_campaign_execution_path_v1.productive_campaign_executor_v1 import (
    evaluate_productive_campaign_execution_gate_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_harness_v1 import (
    evaluate_step7_binding_gate_v1,
    run_step7_campaign_harness_binding_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.constants_v1 import (
    NETWORK_SESSION_ALLOWED as BINDING_NETWORK_SESSION_ALLOWED,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.constants_v1 import (
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED as BINDING_PRODUCTIVE_AUTHORIZED,
)


def prove_binding_vs_productive_campaign_executor_contrast_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Any = None,
) -> dict[str, Any]:
    """Prove only the productive campaign executor can authorize may_start under ephemeral GO."""
    blockers: list[str] = []

    binding_gate = evaluate_step7_binding_gate_v1(owner_go=True, request_real_network=True)
    if binding_gate.get("ok"):
        blockers.append("BINDING_CAMPAIGN_MUST_FORBID_REAL_NETWORK")
    if "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY" not in (
        binding_gate.get("blockers") or []
    ):
        blockers.append("BINDING_CAMPAIGN_MUST_EMIT_REAL_NETWORK_FORBIDDEN")
    if BINDING_NETWORK_SESSION_ALLOWED or BINDING_PRODUCTIVE_AUTHORIZED:
        blockers.append("BINDING_PRODUCTIVE_AUTHORIZED_MUST_REMAIN_FALSE")

    binding_harness = run_step7_campaign_harness_binding_v1(
        repository_sha=expected_repository_sha,
        config_digest=expected_config_digest,
        owner_go=True,
        request_real_network=False,
        repo_root=repo_root,
    )
    if binding_harness.get("NETWORK_SESSION_STARTED"):
        blockers.append("BINDING_CAMPAIGN_STARTED_NETWORK")
    if binding_harness.get("CAMPAIGN_EXECUTED"):
        blockers.append("BINDING_CAMPAIGN_EXECUTED_MUST_BE_FALSE")

    productive_full = evaluate_productive_campaign_execution_gate_v1(
        mode=MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        stdin_isatty=True,
    )
    if not productive_full.get("campaign_may_start"):
        blockers.append("PRODUCTIVE_CAMPAIGN_MUST_AUTHORIZE_MAY_START_UNDER_FULL_GO")

    productive_no_go = evaluate_productive_campaign_execution_gate_v1(
        mode=MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=False,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        stdin_isatty=True,
    )
    if productive_no_go.get("campaign_may_start"):
        blockers.append("PRODUCTIVE_CAMPAIGN_MUST_NOT_AUTHORIZE_WITHOUT_NETWORK_SESSION_GO")

    productive_one = evaluate_productive_campaign_execution_gate_v1(
        mode=MODE_GOVERNED_MULTI_SESSION_CAMPAIGN,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=1,
        stdin_isatty=True,
    )
    if productive_one.get("campaign_may_start"):
        blockers.append("PRODUCTIVE_CAMPAIGN_MUST_REJECT_SINGLE_SESSION")

    ok = not blockers
    return {
        "ok": ok,
        "blockers": sorted(set(blockers)),
        "capability_id": CAPABILITY_ID,
        "binding_campaign_executor": {
            "role": BINDING_CAMPAIGN_ROLE,
            "capability_id": BINDING_CAMPAIGN_CAPABILITY_ID,
            "network_session_may_start": False,
            "real_network_forbidden": (
                "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY"
                in (binding_gate.get("blockers") or [])
            ),
            "network_session_started": bool(binding_harness.get("NETWORK_SESSION_STARTED")),
            "productive_network_session_execution_authorized": BINDING_PRODUCTIVE_AUTHORIZED,
            "harness_ok_without_real_network": bool(binding_harness.get("ok")),
        },
        "productive_campaign_executor": {
            "role": PRODUCTIVE_CAMPAIGN_EXECUTOR_ROLE,
            "capability_id": CAPABILITY_ID,
            "campaign_may_start_under_full_go": bool(productive_full.get("campaign_may_start")),
            "campaign_may_start_without_network_session_go": bool(
                productive_no_go.get("campaign_may_start")
            ),
            "campaign_may_start_with_single_session": bool(
                productive_one.get("campaign_may_start")
            ),
            "network_session_started_in_this_capability": False,
            "requires_separate_owner_go_campaign": True,
        },
        "claims": {
            "BINDING_CAMPAIGN_PRESERVED_FAIL_CLOSED": ok and not bool(binding_gate.get("ok")),
            "ONLY_PRODUCTIVE_CAMPAIGN_EXECUTOR_CAN_AUTHORIZE_MAY_START": ok
            and bool(productive_full.get("campaign_may_start")),
            "PRODUCTIVE_CAMPAIGN_REQUIRES_NETWORK_SESSION_GO": ok
            and not bool(productive_no_go.get("campaign_may_start")),
            "PRODUCTIVE_CAMPAIGN_REQUIRES_MULTI_SESSION": ok
            and not bool(productive_one.get("campaign_may_start")),
            "NETWORK_SESSION_STARTED": False,
            "CONFIRM_TOKEN_MINTED": False,
            "CONFIRM_TOKEN_CONSUMED": False,
        },
        "notes": [
            "BINDING_CAMPAIGN_EXECUTOR=always forbids Real-Network side effects",
            "PRODUCTIVE_CAMPAIGN_EXECUTOR=may authorize may_start under ephemeral GO and >1 sessions",
            "ONLY_LATER_SEPARATE_OWNER_GO_CAMPAIGN_MAY_START_NETWORK=true",
        ],
    }
