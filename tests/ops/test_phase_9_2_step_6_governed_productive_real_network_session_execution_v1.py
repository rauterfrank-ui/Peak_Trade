"""Tests for PHASE_9_2_STEP_6_GOVERNED_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTION_IMPLEMENTATION_V1."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.constants_v1 import (
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED as BINDING_PRODUCTIVE_AUTHORIZED,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.governed_session_execution_v1 import (
    execute_governed_step6_productive_session_offline_fail_closed_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.constants_v1 import (
    CORE_LOGIC_CHANGE,
    NETWORK_SESSION_ALLOWED,
    PHASE_9_2_STEP_6_STATUS,
    PHASE_9_2_STEP_7_STATUS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    SESSION_EXECUTION_ALLOWED,
    STEP6_BINDING_ONLY_EXECUTOR_PRESERVED,
    STEP6_GOVERNED_PRODUCTIVE_SESSION_EXECUTION_CAPABILITY_PRESENT,
    STEP6_PRODUCTIVE_PATH_IMPLEMENTATION_PRESERVED,
    STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT,
    STEP6_SESSION_OWNER_PRESENT,
    STEP7_STARTED,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.failure_injection_v1 import (
    run_step6_session_execution_failure_injection_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.governed_session_execution_v1 import (
    execute_governed_step6_session_offline_fail_closed_v1,
    prove_step6_session_execution_implementation_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.productive_path_consumer_v1 import (
    prove_path_alone_cannot_start_session_v1,
)
from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.productive_executor_v1 import (
    invoke_productive_executor_offline_fail_closed_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / PRODUCTIVE_ENTRYPOINT_PATH


def _sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), text=True
    ).strip()


def _cfg() -> str:
    return str(
        load_activation_config_v1(
            config_path=REPO_ROOT
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )


def test_implementation_present_without_starting_network() -> None:
    result = prove_step6_session_execution_implementation_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert result.ok is True
    assert result.network_session_started is False
    assert result.network_calls == 0
    assert result.confirm_token_minted is False
    assert result.confirm_token_consumed is False
    assert NETWORK_SESSION_ALLOWED is False
    assert SESSION_EXECUTION_ALLOWED is False
    assert STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT is True
    assert STEP6_GOVERNED_PRODUCTIVE_SESSION_EXECUTION_CAPABILITY_PRESENT is True
    assert STEP6_SESSION_OWNER_PRESENT is True
    assert STEP6_BINDING_ONLY_EXECUTOR_PRESERVED is True
    assert STEP6_PRODUCTIVE_PATH_IMPLEMENTATION_PRESERVED is True
    assert PHASE_9_2_STEP_6_STATUS == "OPEN"
    assert PHASE_9_2_STEP_7_STATUS == "OPEN"
    assert STEP7_STARTED is False
    assert CORE_LOGIC_CHANGE is False
    assert result.claims["PRODUCTIVE_PATH_CONSUMED"] is True
    assert result.claims["STEP6_REAL_TTY_EXECUTION_REACHABLE"] is True
    assert result.claims["STEP6_HIDDEN_CONFIRM_HANDOFF_REACHABLE"] is True
    assert result.claims["STEP6_STALE_CONTROL_PRODUCTIVELY_REACHABLE"] is True
    assert result.claims["STEP6_FAILURE_INJECTION_REACHABLE"] is True
    assert result.claims["STEP6_VERIFIER_REACHABLE"] is True


def test_no_owner_go_fail_closed() -> None:
    result = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=False,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        repo_root=REPO_ROOT,
    )
    assert result.network_session_started is False
    assert result.session_execution_may_start is False
    assert "OWNER_GO_REQUIRED" in result.blockers


def test_no_network_session_go_fail_closed() -> None:
    result = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=False,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        repo_root=REPO_ROOT,
    )
    assert result.session_execution_may_start is False
    assert "NETWORK_SESSION_GO_REQUIRED" in result.blockers


def test_no_real_tty_fail_closed() -> None:
    result = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=False,
        getpass_fn=lambda _p: "x" * 32,
        repo_root=REPO_ROOT,
    )
    assert result.session_execution_may_start is False
    assert "REAL_TTY_REQUIRED" in result.blockers


def test_no_hidden_confirm_channel_fail_closed() -> None:
    result = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
        getpass_fn=None,
        repo_root=REPO_ROOT,
    )
    assert result.session_execution_may_start is False
    assert (
        "HIDDEN_CONFIRM_CHANNEL_MISSING" in result.blockers
        or "HIDDEN_CONFIRM_HANDOFF_UNREACHABLE" in result.blockers
    )


def test_wrong_repository_sha_fail_closed() -> None:
    result = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        actual_repository_sha="deadbeef" * 5,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        repo_root=REPO_ROOT,
    )
    assert result.session_execution_may_start is False
    assert "REPOSITORY_SHA_MISMATCH" in result.blockers


def test_config_mismatch_fail_closed() -> None:
    result = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        actual_config_digest="0" * 64,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        repo_root=REPO_ROOT,
    )
    assert result.session_execution_may_start is False
    assert "CONFIG_DIGEST_MISMATCH" in result.blockers


def test_private_endpoint_and_auth_and_orders_fail_closed() -> None:
    private = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        private_endpoint_reachable=True,
        repo_root=REPO_ROOT,
    )
    assert private.session_execution_may_start is False
    assert "PRIVATE_ENDPOINT_REACHABLE_FORBIDDEN" in private.blockers

    auth = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        auth_header_present=True,
        credential_path_reachable=True,
        repo_root=REPO_ROOT,
    )
    assert auth.session_execution_may_start is False
    assert "AUTH_HEADER_PRESENT_FORBIDDEN" in auth.blockers
    assert "CREDENTIAL_PATH_REACHABLE_FORBIDDEN" in auth.blockers

    orders = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        order_side_effect_reachable=True,
        repo_root=REPO_ROOT,
    )
    assert orders.session_execution_may_start is False
    assert "ORDER_SIDE_EFFECT_REACHABLE_FORBIDDEN" in orders.blockers


def test_binding_only_cannot_be_used_as_productive_session() -> None:
    result = execute_governed_step6_productive_session_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
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
    assert result.ok is False
    assert result.network_session_started is False
    assert BINDING_PRODUCTIVE_AUTHORIZED is False
    assert "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY" in result.blockers


def test_productive_path_alone_cannot_start_session() -> None:
    path_alone = prove_path_alone_cannot_start_session_v1()
    assert path_alone["ok"] is True
    assert path_alone["path_side_effects_forbidden"] is True
    assert path_alone["path_may_start_with_request_real_network"] is False

    path_invoke = invoke_productive_executor_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        allow_real_network_side_effects=True,
        stdin_isatty=True,
        repo_root=REPO_ROOT,
    )
    assert path_invoke.network_session_started is False
    assert "REAL_NETWORK_SIDE_EFFECTS_FORBIDDEN_IN_THIS_IMPLEMENTATION_CAPABILITY" in (
        path_invoke.blockers
    )


def test_session_consumes_path_and_may_start_under_full_go_without_network() -> None:
    result = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
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
        repo_root=REPO_ROOT,
    )
    assert result.session_execution_may_start is True
    assert result.network_session_started is False
    assert result.confirm_token_minted is False
    assert result.claims["PRODUCTIVE_PATH_CONSUMED"] is True
    assert result.claims["STALE_CONTROL_PRESENT"] is True
    assert "NETWORK_SESSION_START_DEFERRED_IN_IMPLEMENTATION_CAPABILITY" in result.blockers


def test_failure_injection_matrix() -> None:
    fi = run_step6_session_execution_failure_injection_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
    )
    assert fi["ok"] is True
    assert fi["FAILURE_INJECTION_TESTS_PASS"] is True
    assert fi["network_session_started"] is False
    assert fi["confirm_token_minted"] is False
    names = {c["case"] for c in fi["cases"]}
    assert "no_owner_go_fail_closed" in names
    assert "productive_path_alone_cannot_start_session" in names
    assert "binding_only_cannot_be_productive_session" in names
    assert "stale_control_and_failure_injection_reachable" in names


def test_cli_prove_and_execute_never_starts_network() -> None:
    proc = subprocess.run(
        [sys.executable, str(CLI), "prove-implementation", "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["network_session_started"] is False
    assert (
        payload["claims"]["STEP6_GOVERNED_PRODUCTIVE_SESSION_EXECUTION_CAPABILITY_PRESENT"] is True
    )

    exec_proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "execute-governed-session",
            "--owner-go",
            "--operator-authorization-explicit",
            "--network-session-go",
            "--request-real-network",
            "--json",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert exec_proc.returncode == 2
    epayload = json.loads(exec_proc.stdout)
    assert epayload["network_session_started"] is False
    assert epayload["confirm_token_minted"] is False
