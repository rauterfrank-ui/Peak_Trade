"""Failure-injection matrix for Step-6 session-execution implementation."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.governed_session_execution_v1 import (
    execute_governed_step6_productive_session_offline_fail_closed_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.constants_v1 import (
    PHASE_9_2_STEP_6_STATUS,
    PHASE_9_2_STEP_7_STATUS,
    STEP6_GOVERNED_PRODUCTIVE_SESSION_EXECUTION_CAPABILITY_PRESENT,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.governed_session_execution_v1 import (
    execute_governed_step6_session_offline_fail_closed_v1,
    prove_step6_session_execution_implementation_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.productive_path_consumer_v1 import (
    prove_path_alone_cannot_start_session_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.session_executor_v1 import (
    prove_session_executor_wiring_v1,
)


def run_step6_session_execution_failure_injection_v1(
    *,
    expected_repository_sha: str,
    expected_config_digest: str,
) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []

    def _case(name: str, ok: bool, **extra: Any) -> None:
        cases.append({"case": name, "ok": ok, **extra})

    proof = prove_step6_session_execution_implementation_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
    )
    _case(
        "implementation_proof_no_network",
        proof.ok and not proof.network_session_started and not proof.confirm_token_minted,
        network_session_started=proof.network_session_started,
    )

    no_owner = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=False,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
    )
    _case(
        "no_owner_go_fail_closed",
        (not no_owner.session_execution_may_start)
        and "OWNER_GO_REQUIRED" in no_owner.blockers
        and not no_owner.network_session_started,
        blockers=no_owner.blockers,
    )

    no_go = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=False,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
    )
    _case(
        "no_network_session_go_fail_closed",
        (not no_go.session_execution_may_start)
        and "NETWORK_SESSION_GO_REQUIRED" in no_go.blockers
        and not no_go.network_session_started,
        blockers=no_go.blockers,
    )

    no_tty = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=False,
        getpass_fn=lambda _p: "x" * 32,
    )
    _case(
        "no_real_tty_fail_closed",
        (not no_tty.session_execution_may_start)
        and "REAL_TTY_REQUIRED" in no_tty.blockers
        and not no_tty.network_session_started,
        blockers=no_tty.blockers,
    )

    no_channel = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
        getpass_fn=None,
    )
    _case(
        "no_hidden_confirm_channel_fail_closed",
        (not no_channel.session_execution_may_start)
        and (
            "HIDDEN_CONFIRM_CHANNEL_MISSING" in no_channel.blockers
            or "HIDDEN_CONFIRM_HANDOFF_UNREACHABLE" in no_channel.blockers
        )
        and not no_channel.network_session_started,
        blockers=no_channel.blockers,
    )

    wrong_sha = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        actual_repository_sha="deadbeef" * 5,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
    )
    _case(
        "wrong_repository_sha_fail_closed",
        (not wrong_sha.session_execution_may_start)
        and "REPOSITORY_SHA_MISMATCH" in wrong_sha.blockers
        and not wrong_sha.network_session_started,
        blockers=wrong_sha.blockers,
    )

    wrong_cfg = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        actual_config_digest="0" * 64,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
    )
    _case(
        "config_mismatch_fail_closed",
        (not wrong_cfg.session_execution_may_start)
        and "CONFIG_DIGEST_MISMATCH" in wrong_cfg.blockers
        and not wrong_cfg.network_session_started,
        blockers=wrong_cfg.blockers,
    )

    private = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        private_endpoint_reachable=True,
    )
    _case(
        "private_endpoint_fail_closed",
        (not private.session_execution_may_start)
        and "PRIVATE_ENDPOINT_REACHABLE_FORBIDDEN" in private.blockers
        and not private.network_session_started,
        blockers=private.blockers,
    )

    auth_hdr = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        auth_header_present=True,
        credential_path_reachable=True,
    )
    _case(
        "auth_header_credential_fail_closed",
        (not auth_hdr.session_execution_may_start)
        and (
            "AUTH_HEADER_PRESENT_FORBIDDEN" in auth_hdr.blockers
            or "CREDENTIAL_PATH_REACHABLE_FORBIDDEN" in auth_hdr.blockers
        )
        and not auth_hdr.network_session_started,
        blockers=auth_hdr.blockers,
    )

    orders = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        order_side_effect_reachable=True,
    )
    _case(
        "order_reachability_fail_closed",
        (not orders.session_execution_may_start)
        and "ORDER_SIDE_EFFECT_REACHABLE_FORBIDDEN" in orders.blockers
        and not orders.network_session_started,
        blockers=orders.blockers,
    )

    binding = execute_governed_step6_productive_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        authorization_id="auth_1",
        authorization_digest="b" * 64,
        confirm_token_binding_sha256="c" * 64,
        getpass_fn=lambda _p: "must-not-start",
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        allow_real_network_side_effects=True,
        stdin_isatty=True,
    )
    _case(
        "binding_only_cannot_be_productive_session",
        (not binding.network_session_started)
        and "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY" in binding.blockers,
        blockers=binding.blockers,
    )

    path_alone = prove_path_alone_cannot_start_session_v1()
    _case(
        "productive_path_alone_cannot_start_session",
        bool(path_alone.get("ok")) and bool(path_alone.get("path_side_effects_forbidden")),
        path_alone=path_alone,
    )

    wiring = prove_session_executor_wiring_v1(enable_receive_lag=True)
    _case(
        "stale_control_and_failure_injection_reachable",
        bool(wiring.get("ok"))
        and bool((wiring.get("stale_prep") or {}).get("stale_control_present"))
        and bool((wiring.get("stale_prep") or {}).get("receive_lag_schedule")),
        wiring_ok=bool(wiring.get("ok")),
    )

    full = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=expected_repository_sha,
        expected_config_digest=expected_config_digest,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        enable_receive_lag=True,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
    )
    _case(
        "full_go_may_start_but_implementation_does_not_start_network",
        bool(full.session_execution_may_start)
        and not full.network_session_started
        and "NETWORK_SESSION_START_DEFERRED_IN_IMPLEMENTATION_CAPABILITY" in full.blockers
        and bool((full.claims or {}).get("PRODUCTIVE_PATH_CONSUMED")),
        may_start=full.session_execution_may_start,
        started=full.network_session_started,
    )

    _case(
        "verifier_and_step_status_open",
        PHASE_9_2_STEP_6_STATUS == "OPEN"
        and PHASE_9_2_STEP_7_STATUS == "OPEN"
        and STEP6_GOVERNED_PRODUCTIVE_SESSION_EXECUTION_CAPABILITY_PRESENT is True,
    )

    ok = all(bool(c.get("ok")) for c in cases)
    return {
        "ok": ok,
        "FAILURE_INJECTION_TESTS_PASS": ok,
        "cases": cases,
        "network_session_started": False,
        "confirm_token_minted": False,
        "PHASE_9_2_STEP_6_STATUS": PHASE_9_2_STEP_6_STATUS,
        "PHASE_9_2_STEP_7_STATUS": PHASE_9_2_STEP_7_STATUS,
    }
