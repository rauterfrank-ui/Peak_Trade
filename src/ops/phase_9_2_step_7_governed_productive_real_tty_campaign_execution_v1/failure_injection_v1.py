"""Failure-injection matrix for Step-7 Real-TTY campaign owner implementation."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.constants_v1 import (
    PHASE_9_2_STEP_6_STATUS,
    PHASE_9_2_STEP_7_STATUS,
    TARGET_CAMPAIGN_CAPABILITY_ID,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.governed_campaign_execution_v1 import (
    execute_governed_step7_campaign_offline_fail_closed_v1,
    execute_governed_step7_campaign_v1,
    prove_step7_campaign_execution_owner_implementation_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.productive_path_consumer_v1 import (
    prove_path_alone_cannot_start_campaign_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_harness_v1 import (
    evaluate_step7_binding_gate_v1,
)


def run_step7_campaign_execution_owner_failure_injection_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
    repo_root: Any = None,
) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []

    def _case(name: str, ok: bool, **extra: Any) -> None:
        cases.append({"case": name, "ok": ok, **extra})

    proof = prove_step7_campaign_execution_owner_implementation_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        repo_root=repo_root,
    )
    _case(
        "implementation_proof_no_network",
        proof.ok and not proof.network_session_started and not proof.confirm_token_minted,
        network_session_started=proof.network_session_started,
    )

    no_owner = execute_governed_step7_campaign_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=False,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        repo_root=repo_root,
    )
    _case(
        "no_owner_go_fail_closed",
        (not no_owner.campaign_may_start)
        and "OWNER_GO_REQUIRED" in no_owner.blockers
        and not no_owner.network_session_started,
        blockers=no_owner.blockers,
    )

    no_tty = execute_governed_step7_campaign_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=False,
        getpass_fn=lambda _p: "x" * 32,
        wallclock_runner=lambda **_k: {"ok": True},
        campaign_start_state={},
        repo_root=repo_root,
    )
    _case(
        "non_tty_fail_closed_no_invoke",
        (not no_tty.ok)
        and no_tty.network_session_started is False
        and int(no_tty.claims.get("WALLCLOCK_INVOKED_COUNT") or 0) == 0
        and (
            "REAL_TTY_REQUIRED" in no_tty.blockers or "HIDDEN_PTY_STDIN_NOT_TTY" in no_tty.blockers
        ),
        blockers=no_tty.blockers,
    )

    wrong_cap = execute_governed_step7_campaign_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        expected_capability_id="WRONG_CAPABILITY",
        wallclock_runner=lambda **_k: {"ok": True},
        campaign_start_state={},
        repo_root=repo_root,
    )
    _case(
        "wrong_capability_id_fail_closed",
        (not wrong_cap.ok)
        and "WRONG_CAPABILITY_ID" in wrong_cap.blockers
        and int(wrong_cap.claims.get("WALLCLOCK_INVOKED_COUNT") or 0) == 0,
        blockers=wrong_cap.blockers,
    )

    invalid_confirm = execute_governed_step7_campaign_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "",
        wallclock_runner=lambda **_k: {"ok": True},
        campaign_start_state={},
        repo_root=repo_root,
    )
    _case(
        "hidden_confirm_invalid_fail_closed",
        (not invalid_confirm.ok)
        and int(invalid_confirm.claims.get("WALLCLOCK_INVOKED_COUNT") or 0) == 0
        and (
            "CONFIRM_TOKEN_MISSING" in invalid_confirm.blockers
            or "CONFIRM_TOKEN_FAILURE" in invalid_confirm.blockers
        ),
        blockers=invalid_confirm.blockers,
    )

    before_gate = execute_governed_step7_campaign_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=False,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        wallclock_runner=lambda **_k: {"ok": True},
        campaign_start_state={},
        repo_root=repo_root,
    )
    _case(
        "invoke_before_gate_excluded",
        int(before_gate.claims.get("WALLCLOCK_INVOKED_COUNT") or 0) == 0
        and before_gate.network_session_started is False,
        blockers=before_gate.blockers,
    )

    path_alone = prove_path_alone_cannot_start_campaign_v1()
    _case(
        "path_alone_cannot_start",
        bool(path_alone.get("ok")),
        blockers=path_alone.get("blockers"),
    )

    binding = evaluate_step7_binding_gate_v1(owner_go=True, request_real_network=True)
    _case(
        "binding_remains_forbidden",
        (not binding.get("ok"))
        and "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY"
        in (binding.get("blockers") or []),
        blockers=binding.get("blockers"),
    )

    ok = all(bool(c.get("ok")) for c in cases)
    return {
        "ok": ok,
        "cases": cases,
        "case_count": len(cases),
        "NETWORK_SESSION_STARTED": False,
        "CONFIRM_TOKEN_MINTED": False,
        "PHASE_9_2_STEP_6_STATUS": PHASE_9_2_STEP_6_STATUS,
        "PHASE_9_2_STEP_7_STATUS": PHASE_9_2_STEP_7_STATUS,
        "TARGET_CAMPAIGN_CAPABILITY_ID": TARGET_CAMPAIGN_CAPABILITY_ID,
    }
