"""Tests for PHASE_9_2_STEP_6_GOVERNED_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_BINDING_V1."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.constants_v1 import (
    NETWORK_SESSION_ALLOWED as PREDECESSOR_NETWORK_SESSION_ALLOWED,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.adverse_stale_executor_v1 import (
    prepare_adverse_stale_runtime_overrides_v1,
    prove_adverse_stale_executor_binding_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.constants_v1 import (
    MAX_NETWORK_SESSION_COUNT,
    MODE_GOVERNED_REAL_NETWORK_SESSION,
    NETWORK_SESSION_ALLOWED,
    PHASE_9_2_STEP_6_STATUS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    SESSION_EXECUTED,
    STEP6_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_BOUND,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.failure_injection_v1 import (
    run_step6_productive_executor_failure_injection_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.governed_session_execution_v1 import (
    evaluate_productive_session_gate_v1,
    execute_governed_step6_productive_session_offline_fail_closed_v1,
    prove_step6_productive_executor_binding_v1,
    request_real_network_offline_fail_closed_v1,
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


def test_default_cannot_start_network() -> None:
    result = prove_step6_productive_executor_binding_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert result.ok is True
    assert result.network_session_started is False
    assert result.network_calls == 0
    assert result.authorization_consumed is False
    assert result.confirm_token_consumed is False
    assert NETWORK_SESSION_ALLOWED is False
    assert PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED is False
    assert SESSION_EXECUTED is False
    assert PHASE_9_2_STEP_6_STATUS == "OPEN"
    assert STEP6_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTOR_BOUND is True
    assert result.claims["PRODUCTIVE_EXECUTOR_BOUND"] is True


def test_non_tty_cannot_start_network() -> None:
    result = execute_governed_step6_productive_session_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        authorization_id="auth_1",
        authorization_digest="b" * 64,
        confirm_token_binding_sha256="c" * 64,
        getpass_fn=lambda _p: "must-not-consume",
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        stdin_isatty=False,
    )
    assert result.ok is False
    assert result.network_session_started is False
    assert result.confirm_token_consumed is False
    assert any("TTY" in b for b in result.blockers)


def test_missing_owner_go_cannot_start_network() -> None:
    token = "tok-fixture"
    result = execute_governed_step6_productive_session_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        authorization_id="auth_1",
        authorization_digest="d" * 64,
        confirm_token_binding_sha256=hashlib.sha256(token.encode()).hexdigest(),
        getpass_fn=lambda _p: token,
        owner_go=False,
        operator_authorization_explicit=True,
        network_session_go=True,
        stdin_isatty=True,
    )
    assert result.ok is False
    assert result.network_session_started is False
    assert "OWNER_GO_REQUIRED" in result.blockers


def test_invalid_confirm_token_cannot_start_network() -> None:
    result = execute_governed_step6_productive_session_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        authorization_id="auth_1",
        authorization_digest="e" * 64,
        confirm_token_binding_sha256=hashlib.sha256(b"expected").hexdigest(),
        getpass_fn=lambda _p: "wrong",
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        stdin_isatty=True,
    )
    assert result.ok is False
    assert result.confirm_token_consumed is False
    assert any("CONFIRM_TOKEN" in b for b in result.blockers)


def test_stale_control_absent_cannot_start() -> None:
    gate = evaluate_productive_session_gate_v1(
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stale_control_present=False,
        stdin_isatty=True,
    )
    assert gate["ok"] is False
    assert "STALE_CONTROL_ABSENT" in gate["blockers"]


def test_permanent_network_flip_not_required() -> None:
    assert NETWORK_SESSION_ALLOWED is False
    assert PREDECESSOR_NETWORK_SESSION_ALLOWED is False
    assert PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED is False


def test_public_md_only_and_orders_disabled() -> None:
    result = prove_step6_productive_executor_binding_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert result.claims["PUBLIC_MD_ONLY_ENFORCED"] is True
    assert result.claims["ORDERS_DISABLED"] is True
    assert result.claims["PRIVATE_ENDPOINT_REACHABLE"] is False
    assert result.claims["ORDER_SIDE_EFFECT_REACHABLE"] is False
    assert result.claims["CREDENTIAL_PATH_REACHABLE"] is False


def test_fault_schedule_reaches_stale_receive_lag_control() -> None:
    stale = prove_adverse_stale_executor_binding_v1()
    assert stale["ok"] is True
    assert stale["classification"]["ok"] is True
    assert stale["receive_lag_enabled_binding"]["receive_lag_schedule"] is True
    assert stale["network_calls"] == 0
    prepared = prepare_adverse_stale_runtime_overrides_v1(enable_receive_lag=True)
    assert prepared["ok"] is True
    assert "governed_stale_data_control" in prepared["runtime_overrides"]


def test_max_session_count_one() -> None:
    assert MAX_NETWORK_SESSION_COUNT == 1
    result = prove_step6_productive_executor_binding_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert result.claims["MAX_NETWORK_SESSION_COUNT"] == 1


def test_binding_zero_network_calls() -> None:
    req = request_real_network_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        stdin_isatty=True,
    )
    assert req.ok is False
    assert req.network_session_started is False
    assert req.network_calls == 0
    assert "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY" in req.blockers


def test_failure_injection_matrix_pass() -> None:
    fi = run_step6_productive_executor_failure_injection_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
    )
    assert fi["ok"] is True
    assert fi["FAILURE_INJECTION_TESTS_PASS"] is True
    assert fi["network_session_started"] is False
    assert fi["network_calls"] == 0


def test_cli_prove_binding() -> None:
    proc = subprocess.run(
        [sys.executable, str(CLI), "prove-binding", "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "PRODUCTIVE_EXECUTOR_BOUND" in proc.stdout
    assert "PHASE_9_2_STEP_6_STATUS" in proc.stdout
