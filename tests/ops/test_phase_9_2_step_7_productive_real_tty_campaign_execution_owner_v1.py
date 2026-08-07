"""Tests for PHASE_9_2_STEP_7_PRODUCTIVE_REAL_TTY_CAMPAIGN_EXECUTION_OWNER_IMPLEMENTATION_V1."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.constants_v1 import (
    CAPABILITY_ID,
    MULTI_SESSION_REQUIREMENT_EXPRESSION,
    NETWORK_SESSION_ALLOWED,
    PHASE_9_2_STEP_6_STATUS,
    PHASE_9_2_STEP_7_STATUS,
    PRODUCTIVE_CAMPAIGN_INVOKE_SYMBOL,
    PRODUCTIVE_ENTRYPOINT_PATH,
    REAL_TTY_OPERATOR_ENTRYPOINT_PATH,
    STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_PRESENT,
    STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_RUNTIME_REACHABLE,
    STEP7_REAL_TTY_CAMPAIGN_OWNER_PRESENT,
    TARGET_CAMPAIGN_CAPABILITY_ID,
    multi_session_requirement_satisfied_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.failure_injection_v1 import (
    run_step7_campaign_execution_owner_failure_injection_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.governed_campaign_execution_v1 import (
    execute_governed_step7_campaign_offline_fail_closed_v1,
    execute_governed_step7_campaign_v1,
    prove_step7_campaign_execution_owner_implementation_v1,
)
from src.ops.phase_9_2_step_7_repeated_multi_session_continuity_campaign_binding_v1.campaign_harness_v1 import (
    evaluate_step7_binding_gate_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG = REPO_ROOT / "src/ops/phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1"
CLI = REPO_ROOT / PRODUCTIVE_ENTRYPOINT_PATH
OPERATOR = REPO_ROOT / REAL_TTY_OPERATOR_ENTRYPOINT_PATH


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


def _fake_runner_factory(bucket: list):
    def _runner(**kwargs):
        bucket.append(dict(kwargs))
        return {"ok": True, "NETWORK_SESSION_STARTED": False, "synthetic": True}

    return _runner


def test_constants_and_capability_ids() -> None:
    assert CAPABILITY_ID.endswith("OWNER_IMPLEMENTATION_V1")
    assert TARGET_CAMPAIGN_CAPABILITY_ID.endswith("CAMPAIGN_EXECUTION_V1")
    assert PRODUCTIVE_CAMPAIGN_INVOKE_SYMBOL == "execute_governed_step7_campaign_v1"
    assert STEP7_REAL_TTY_CAMPAIGN_OWNER_PRESENT is True
    assert STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_PRESENT is True
    assert STEP7_PRODUCTIVE_CAMPAIGN_INVOKE_EDGE_RUNTIME_REACHABLE is True
    assert PHASE_9_2_STEP_6_STATUS == "CLOSED_PASS"
    assert PHASE_9_2_STEP_7_STATUS == "OPEN"
    assert MULTI_SESSION_REQUIREMENT_EXPRESSION == ">1"
    assert multi_session_requirement_satisfied_v1(1) is False
    assert multi_session_requirement_satisfied_v1(2) is True
    assert NETWORK_SESSION_ALLOWED is False
    assert CLI.is_file()
    assert OPERATOR.is_file()


def test_ast_productive_wallclock_callsite_in_campaign_invoke() -> None:
    hits: list[tuple[str, int]] = []
    for path in PKG.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = None
                func = node.func
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                if name == "run_productive_wallclock_session_v1":
                    hits.append((str(path.relative_to(REPO_ROOT)), node.lineno))
    assert len(hits) == 1
    assert hits[0][0].endswith("campaign_start_invoke_v1.py")


def test_implementation_proof_no_network() -> None:
    result = prove_step7_campaign_execution_owner_implementation_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert result.ok is True
    assert result.network_session_started is False
    assert result.confirm_token_minted is False
    assert result.confirm_token_consumed is False
    assert result.claims["STEP7_REAL_TTY_CAMPAIGN_OWNER_PRESENT"] is True
    assert result.claims["STEP7_CAMPAIGN_HARNESS_BOUND"] is True
    assert result.claims["STEP7_CAMPAIGN_VERIFIER_PRESENT"] is True
    assert result.claims["PRODUCTIVE_PATH_CONSUMED"] is True
    assert result.claims["PATH_ALONE_CANNOT_START_CAMPAIGN"] is True
    assert result.claims["READY_FOR_SEPARATE_OWNER_GO_REAL_TTY_CAMPAIGN"] is True
    assert result.claims["ORDERS_DISABLED"] is True
    assert result.claims["ORDER_SIDE_EFFECT_REACHABLE"] is False
    assert result.claims["CREDENTIAL_PATH_REACHABLE"] is False


def test_non_tty_fail_closed() -> None:
    calls: list = []
    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
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
        wallclock_runner=_fake_runner_factory(calls),
        campaign_start_state={},
        repo_root=REPO_ROOT,
    )
    assert result.ok is False
    assert calls == []
    assert result.network_session_started is False
    assert "REAL_TTY_REQUIRED" in result.blockers or "HIDDEN_PTY_STDIN_NOT_TTY" in result.blockers


def test_owner_go_missing_fail_closed() -> None:
    calls: list = []
    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
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
        wallclock_runner=_fake_runner_factory(calls),
        campaign_start_state={},
        repo_root=REPO_ROOT,
    )
    assert result.ok is False
    assert calls == []
    assert "OWNER_GO_REQUIRED" in result.blockers


def test_wrong_capability_id_fail_closed() -> None:
    calls: list = []
    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
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
        expected_capability_id="NOT_STEP7_CAMPAIGN",
        wallclock_runner=_fake_runner_factory(calls),
        campaign_start_state={},
        repo_root=REPO_ROOT,
    )
    assert result.ok is False
    assert calls == []
    assert "WRONG_CAPABILITY_ID" in result.blockers


def test_hidden_confirm_invalid_fail_closed() -> None:
    calls: list = []
    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
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
        wallclock_runner=_fake_runner_factory(calls),
        campaign_start_state={},
        repo_root=REPO_ROOT,
    )
    assert result.ok is False
    assert calls == []
    assert result.confirm_token_consumed is False
    assert "CONFIRM_TOKEN_MISSING" in result.blockers or "CONFIRM_TOKEN_FAILURE" in result.blockers


def test_hidden_confirm_plaintext_not_exposed_in_result() -> None:
    secret = "super-secret-confirm-token-value-xyz"
    calls: list = []
    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: secret,
        wallclock_runner=_fake_runner_factory(calls),
        campaign_start_state={},
        repo_root=REPO_ROOT,
    )
    blob = json.dumps(result.to_dict(), sort_keys=True)
    assert secret not in blob
    assert result.claims.get("CONFIRM_TOKEN_PLAINTEXT_EXPOSED") is False
    assert result.claims.get("CONFIRM_TOKEN_PERSISTED") is False


def test_invoke_before_successful_gate_excluded() -> None:
    calls: list = []
    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=False,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=2,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        wallclock_runner=_fake_runner_factory(calls),
        campaign_start_state={},
        repo_root=REPO_ROOT,
    )
    assert calls == []
    assert result.network_session_started is False
    assert "NETWORK_SESSION_GO_REQUIRED" in result.blockers


def test_productive_invoke_edge_multi_session_with_double() -> None:
    calls: list = []
    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
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
        wallclock_runner=_fake_runner_factory(calls),
        campaign_start_state={},
        repo_root=REPO_ROOT,
    )
    assert result.ok is True
    assert len(calls) == 2
    assert result.completed_session_count == 2
    assert result.network_session_started is False  # doubles never claim real network
    assert result.confirm_token_consumed is True
    assert result.confirm_token_minted is False


def test_single_session_rejected() -> None:
    calls: list = []
    result = execute_governed_step7_campaign_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        planned_session_count=1,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        wallclock_runner=_fake_runner_factory(calls),
        campaign_start_state={},
        repo_root=REPO_ROOT,
    )
    assert result.ok is False
    assert calls == []
    assert "MULTI_SESSION_REQUIREMENT_NOT_SATISFIED" in result.blockers


def test_binding_and_path_remain_non_starting() -> None:
    gate = evaluate_step7_binding_gate_v1(owner_go=True, request_real_network=True)
    assert gate["ok"] is False
    assert "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY" in gate["blockers"]
    offline = execute_governed_step7_campaign_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
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
        repo_root=REPO_ROOT,
    )
    assert offline.ok is False
    assert offline.network_session_started is False
    assert "NETWORK_SESSION_START_DEFERRED_IN_IMPLEMENTATION_CAPABILITY" in offline.blockers


def test_failure_injection_matrix() -> None:
    payload = run_step7_campaign_execution_owner_failure_injection_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert payload["ok"] is True
    assert payload["NETWORK_SESSION_STARTED"] is False


def test_cli_prove_implementation_no_network() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "prove-implementation",
            "--json",
            "--expected-repository-sha",
            _sha(),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["network_session_started"] is False
    assert payload["confirm_token_minted"] is False
