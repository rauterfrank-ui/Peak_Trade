"""Tests for PHASE_9_2_STEP_7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_IMPLEMENTATION_V1."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.ops.phase_9_2_step_7_productive_campaign_execution_path_v1.constants_v1 import (
    MULTI_SESSION_REQUIREMENT_EXPRESSION,
    NETWORK_SESSION_ALLOWED,
    PHASE_9_2_STEP_6_STATUS,
    PHASE_9_2_STEP_7_STATUS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    STEP7_BINDING_ONLY_PRESERVED,
    STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_ABSENT,
    STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PRESENT,
    STEP7_STARTED,
    multi_session_requirement_satisfied_v1,
)
from src.ops.phase_9_2_step_7_productive_campaign_execution_path_v1.executor_contrast_v1 import (
    prove_binding_vs_productive_campaign_executor_contrast_v1,
)
from src.ops.phase_9_2_step_7_productive_campaign_execution_path_v1.failure_injection_v1 import (
    run_step7_productive_campaign_execution_path_failure_injection_v1,
)
from src.ops.phase_9_2_step_7_productive_campaign_execution_path_v1.productive_campaign_executor_v1 import (
    invoke_productive_campaign_executor_offline_fail_closed_v1,
    prove_productive_campaign_execution_path_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_harness_v1 import (
    evaluate_step7_binding_gate_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.constants_v1 import (
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED as BINDING_PRODUCTIVE_AUTHORIZED,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / PRODUCTIVE_ENTRYPOINT_PATH
BINDING_CLI = (
    REPO_ROOT
    / "scripts/ops/run_phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.py"
)


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
    result = prove_productive_campaign_execution_path_v1(
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
    assert PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED is False
    assert STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PRESENT is True
    assert STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_ABSENT is False
    assert STEP7_BINDING_ONLY_PRESERVED is True
    assert PHASE_9_2_STEP_6_STATUS == "CLOSED_PASS"
    assert PHASE_9_2_STEP_7_STATUS == "OPEN"
    assert STEP7_STARTED is False
    assert result.claims["PRODUCTIVE_CAMPAIGN_EXECUTOR_IMPLEMENTED"] is True
    assert result.claims["PRODUCTIVE_ENTRYPOINT_BOUND_TO_WALLCLOCK_RUNNER"] is True
    assert result.claims["REPEATED_MULTI_SESSION_SUPPORTED"] is True
    assert result.claims["STEP7_CAMPAIGN_HARNESS_BOUND"] is True
    assert result.claims["STEP7_CAMPAIGN_VERIFIER_PRESENT"] is True
    assert MULTI_SESSION_REQUIREMENT_EXPRESSION == ">1"
    assert multi_session_requirement_satisfied_v1(1) is False
    assert multi_session_requirement_satisfied_v1(2) is True


def test_binding_only_campaign_remains_real_network_forbidden() -> None:
    gate = evaluate_step7_binding_gate_v1(owner_go=True, request_real_network=True)
    assert gate["ok"] is False
    assert "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY" in gate["blockers"]
    assert BINDING_PRODUCTIVE_AUTHORIZED is False

    proc = subprocess.run(
        [
            sys.executable,
            str(BINDING_CLI),
            "wire-harness",
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
    assert "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_CAPABILITY_CLI" in payload["blockers"]


def test_productive_campaign_fails_without_network_session_go() -> None:
    result = invoke_productive_campaign_executor_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=False,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        stdin_isatty=True,
        repo_root=REPO_ROOT,
    )
    assert result.ok is False
    assert result.network_session_started is False
    assert result.campaign_may_start is False
    assert "NETWORK_SESSION_GO_REQUIRED" in result.blockers


def test_productive_campaign_rejects_single_session() -> None:
    result = invoke_productive_campaign_executor_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=1,
        stdin_isatty=True,
        repo_root=REPO_ROOT,
    )
    assert result.ok is False
    assert result.campaign_may_start is False
    assert "MULTI_SESSION_REQUIREMENT_NOT_SATISFIED" in result.blockers


def test_orders_and_credentials_unreachable() -> None:
    result = prove_productive_campaign_execution_path_v1(
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
    result = prove_productive_campaign_execution_path_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert result.confirm_token_minted is False
    assert result.confirm_token_consumed is False
    assert result.claims["CONFIRM_TOKEN_MINTED"] is False
    assert result.claims["CONFIRM_TOKEN_CONSUMED"] is False
    assert result.claims["HIDDEN_CONFIRM_HANDOFF_USED"] is False
    assert result.claims["HIDDEN_CONFIRM_HANDOFF_BOUND_FOR_LATER_CAMPAIGN"] is True


def test_binding_vs_productive_contrast() -> None:
    contrast = prove_binding_vs_productive_campaign_executor_contrast_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert contrast["ok"] is True
    assert contrast["binding_campaign_executor"]["network_session_may_start"] is False
    assert contrast["binding_campaign_executor"]["real_network_forbidden"] is True
    assert contrast["productive_campaign_executor"]["campaign_may_start_under_full_go"] is True
    assert (
        contrast["productive_campaign_executor"]["campaign_may_start_without_network_session_go"]
        is False
    )
    assert (
        contrast["productive_campaign_executor"]["campaign_may_start_with_single_session"] is False
    )
    assert contrast["claims"]["ONLY_PRODUCTIVE_CAMPAIGN_EXECUTOR_CAN_AUTHORIZE_MAY_START"] is True


def test_failure_injection_and_path_binding() -> None:
    fi = run_step7_productive_campaign_execution_path_failure_injection_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert fi["ok"] is True
    assert fi["FAILURE_INJECTION_TESTS_PASS"] is True
    assert fi["network_session_started"] is False
    assert fi["confirm_token_minted"] is False
    assert fi["PHASE_9_2_STEP_7_STATUS"] == "OPEN"
    names = {c["case"] for c in fi["cases"]}
    assert "binding_campaign_remains_real_network_forbidden" in names
    assert "productive_campaign_rejects_single_session" in names
    assert "implementation_capability_forbids_real_network_side_effects" in names


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
    assert payload["claims"]["STEP7_PRODUCTIVE_CAMPAIGN_EXECUTION_PATH_PRESENT"] is True
    assert payload["claims"]["PRODUCTIVE_ENTRYPOINT_BOUND_TO_WALLCLOCK_RUNNER"] is True

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


def test_cli_execute_governed_campaign_never_starts_network() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "execute-governed-campaign",
            "--owner-go",
            "--operator-authorization-explicit",
            "--network-session-go",
            "--request-real-network",
            "--planned-session-count",
            "2",
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
    assert CLI.is_file()
