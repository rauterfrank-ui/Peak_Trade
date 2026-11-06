"""Tests for PHASE_9_2_STEP_6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_IMPLEMENTATION_V1."""

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
from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.constants_v1 import (
    NETWORK_SESSION_ALLOWED,
    PHASE_9_2_STEP_6_STATUS,
    PHASE_9_2_STEP_7_STATUS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    STEP6_BINDING_ONLY_EXECUTOR_PRESERVED,
    STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_ABSENT,
    STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT,
    STEP7_STARTED,
)
from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.executor_contrast_v1 import (
    prove_binding_vs_productive_executor_contrast_v1,
)
from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.failure_injection_v1 import (
    run_step6_productive_execution_path_failure_injection_v1,
)
from src.ops.phase_9_2_step_6_productive_real_network_execution_path_v1.productive_executor_v1 import (
    invoke_productive_executor_offline_fail_closed_v1,
    prove_productive_real_network_execution_path_v1,
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


def test_path_present_without_starting_network() -> None:
    result = prove_productive_real_network_execution_path_v1(
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
    assert STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT is True
    assert STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_ABSENT is False
    assert STEP6_BINDING_ONLY_EXECUTOR_PRESERVED is True
    assert PHASE_9_2_STEP_6_STATUS == "OPEN"
    assert PHASE_9_2_STEP_7_STATUS == "OPEN"
    assert STEP7_STARTED is False
    assert result.claims["PRODUCTIVE_REAL_NETWORK_EXECUTOR_IMPLEMENTED"] is True
    assert result.claims["PRODUCTIVE_EXECUTOR_REQUIRES_SEPARATE_OWNER_GO_SESSION"] is True


def test_binding_only_executor_remains_real_network_forbidden() -> None:
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


def test_productive_executor_fails_without_network_session_go() -> None:
    result = invoke_productive_executor_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=False,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
    )
    assert result.ok is False
    assert result.network_session_started is False
    assert result.network_session_may_start is False
    assert "NETWORK_SESSION_GO_REQUIRED" in result.blockers


def test_orders_and_credentials_unreachable() -> None:
    result = prove_productive_real_network_execution_path_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert result.ok is True
    assert result.claims["ORDERS_DISABLED"] is True
    assert result.claims["PUBLIC_MD_ONLY_ENFORCED"] is True
    assert result.claims["ORDER_SIDE_EFFECT_REACHABLE"] is False
    assert result.claims["CREDENTIAL_PATH_REACHABLE"] is False
    assert result.claims["EXCHANGE_CREDENTIAL_PATH_CHANGED"] is False


def test_no_confirm_token_in_this_capability() -> None:
    result = prove_productive_real_network_execution_path_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert result.confirm_token_minted is False
    assert result.confirm_token_consumed is False
    assert result.claims["CONFIRM_TOKEN_MINTED"] is False
    assert result.claims["CONFIRM_TOKEN_CONSUMED"] is False
    assert result.claims["HIDDEN_CONFIRM_HANDOFF_USED"] is False
    assert result.claims["HIDDEN_CONFIRM_HANDOFF_BOUND_FOR_LATER_SESSION"] is True


def test_binding_vs_productive_contrast() -> None:
    contrast = prove_binding_vs_productive_executor_contrast_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
    )
    assert contrast["ok"] is True
    assert contrast["binding_executor"]["network_session_may_start"] is False
    assert contrast["binding_executor"]["real_network_forbidden"] is True
    assert (
        contrast["productive_real_network_executor"]["network_session_may_start_under_full_go"]
        is True
    )
    assert (
        contrast["productive_real_network_executor"][
            "network_session_may_start_without_network_session_go"
        ]
        is False
    )
    assert contrast["claims"]["ONLY_PRODUCTIVE_EXECUTOR_CAN_AUTHORIZE_MAY_START"] is True


def test_failure_injection_and_verifier_binding() -> None:
    fi = run_step6_productive_execution_path_failure_injection_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
    )
    assert fi["ok"] is True
    assert fi["FAILURE_INJECTION_TESTS_PASS"] is True
    assert fi["network_session_started"] is False
    assert fi["confirm_token_minted"] is False
    assert fi["PHASE_9_2_STEP_6_STATUS"] == "OPEN"
    names = {c["case"] for c in fi["cases"]}
    assert "failure_injection_binding_preserved" in names
    assert "step6_verifier_bound_and_step6_remains_open" in names
    assert "binding_executor_remains_real_network_forbidden" in names


def test_cli_prove_path_and_contrast() -> None:
    proc = subprocess.run(
        [sys.executable, str(CLI), "prove-path", "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["network_session_started"] is False
    assert payload["claims"]["STEP6_PRODUCTIVE_REAL_NETWORK_EXECUTION_PATH_PRESENT"] is True

    contrast = subprocess.run(
        [sys.executable, str(CLI), "prove-contrast", "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert contrast.returncode == 0, contrast.stderr
    cpayload = json.loads(contrast.stdout)
    assert cpayload["ok"] is True


def test_cli_execute_governed_session_never_starts_network() -> None:
    proc = subprocess.run(
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
    assert proc.returncode != 0
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert payload["network_session_started"] is False
    assert payload["confirm_token_minted"] is False
    assert payload["confirm_token_consumed"] is False
