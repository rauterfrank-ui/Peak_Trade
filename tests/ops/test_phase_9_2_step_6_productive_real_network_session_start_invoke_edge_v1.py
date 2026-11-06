"""Tests for Step-6 productive Real-Network start-invoke edge."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.constants_v1 import (
    CAPABILITY_ID,
    PRODUCTIVE_SESSION_INVOKE_SYMBOL,
    STEP6_PRODUCTIVE_REAL_NETWORK_START_INVOKE_EDGE_PRESENT,
    STEP6_PRODUCTIVE_REAL_NETWORK_START_INVOKE_EDGE_RUNTIME_REACHABLE,
    TARGET_SESSION_CAPABILITY_ID,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_execution_v1.governed_session_execution_v1 import (
    execute_governed_step6_session_offline_fail_closed_v1,
    execute_governed_step6_session_v1,
)
from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.governed_session_execution_v1 import (
    execute_governed_step6_productive_session_offline_fail_closed_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG = REPO_ROOT / "src/ops/phase_9_2_step_6_governed_productive_real_network_session_execution_v1"


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
    assert CAPABILITY_ID.endswith("START_INVOKE_EDGE_IMPLEMENTATION_V1")
    assert (
        TARGET_SESSION_CAPABILITY_ID
        == "PHASE_9_2_STEP_6_GOVERNED_PRODUCTIVE_REAL_NETWORK_SESSION_EXECUTION_V1"
    )
    assert PRODUCTIVE_SESSION_INVOKE_SYMBOL == "execute_governed_step6_session_v1"
    assert STEP6_PRODUCTIVE_REAL_NETWORK_START_INVOKE_EDGE_PRESENT is True
    assert STEP6_PRODUCTIVE_REAL_NETWORK_START_INVOKE_EDGE_RUNTIME_REACHABLE is True


def test_ast_exactly_one_productive_wallclock_callsite() -> None:
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
    assert hits[0][0].endswith("session_start_invoke_v1.py")


def test_no_owner_go_zero_wallclock_calls() -> None:
    calls: list = []
    result = execute_governed_step6_session_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=False,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        wallclock_runner=_fake_runner_factory(calls),
        session_start_state={},
        repo_root=REPO_ROOT,
    )
    assert len(calls) == 0
    assert result.network_session_started is False
    assert "OWNER_GO_REQUIRED" in result.blockers


def test_no_network_session_go_zero_wallclock_calls() -> None:
    calls: list = []
    result = execute_governed_step6_session_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=False,
        authorization_valid=True,
        confirm_token_valid=True,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        wallclock_runner=_fake_runner_factory(calls),
        session_start_state={},
        repo_root=REPO_ROOT,
    )
    assert len(calls) == 0
    assert "NETWORK_SESSION_GO_REQUIRED" in result.blockers


def test_non_tty_zero_wallclock_calls() -> None:
    calls: list = []
    result = execute_governed_step6_session_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=False,
        getpass_fn=lambda _p: "x" * 32,
        wallclock_runner=_fake_runner_factory(calls),
        session_start_state={},
        repo_root=REPO_ROOT,
    )
    assert len(calls) == 0
    assert "REAL_TTY_REQUIRED" in result.blockers


def test_hidden_confirm_failure_zero_wallclock_calls() -> None:
    calls: list = []
    result = execute_governed_step6_session_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=True,
        getpass_fn=None,
        wallclock_runner=_fake_runner_factory(calls),
        session_start_state={},
        repo_root=REPO_ROOT,
    )
    assert len(calls) == 0
    assert "HIDDEN_CONFIRM_CHANNEL_MISSING" in result.blockers


def test_wrong_capability_zero_wallclock_calls() -> None:
    calls: list = []
    result = execute_governed_step6_session_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        expected_capability_id="WRONG_CAPABILITY",
        wallclock_runner=_fake_runner_factory(calls),
        session_start_state={},
        repo_root=REPO_ROOT,
    )
    assert len(calls) == 0
    assert "WRONG_CAPABILITY_ID" in result.blockers


def test_sha_mismatch_zero_wallclock_calls() -> None:
    calls: list = []
    result = execute_governed_step6_session_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        actual_repository_sha="deadbeef" * 5,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        wallclock_runner=_fake_runner_factory(calls),
        session_start_state={},
        repo_root=REPO_ROOT,
    )
    assert len(calls) == 0
    assert "REPOSITORY_SHA_MISMATCH" in result.blockers


def test_authorized_synthetic_path_exactly_one_wallclock_invoke() -> None:
    calls: list = []
    state: dict = {}
    result = execute_governed_step6_session_v1(
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
        wallclock_runner=_fake_runner_factory(calls),
        session_start_state=state,
        repo_root=REPO_ROOT,
    )
    assert result.ok is True
    assert len(calls) == 1
    assert int((result.claims or {}).get("WALLCLOCK_INVOKED_COUNT") or 0) == 1
    overrides = dict(calls[0].get("runtime_overrides") or {})
    assert "governed_stale_data_control" in overrides
    assert result.network_session_started is False
    assert result.confirm_token_consumed is True
    assert result.confirm_token_minted is False


def test_duplicate_invocation_still_exactly_one() -> None:
    calls: list = []
    state: dict = {}
    common = dict(
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
        wallclock_runner=_fake_runner_factory(calls),
        session_start_state=state,
        repo_root=REPO_ROOT,
    )
    first = execute_governed_step6_session_v1(**common)
    second = execute_governed_step6_session_v1(**common)
    assert first.ok is True
    assert len(calls) == 1
    assert second.ok is False
    assert "DUPLICATE_SESSION_START_FORBIDDEN" in second.blockers
    assert len(calls) == 1


def test_private_auth_credential_order_surfaces_unreachable() -> None:
    calls: list = []
    for kwargs in (
        {"private_endpoint_reachable": True},
        {"auth_header_present": True},
        {"credential_path_reachable": True},
        {"order_side_effect_reachable": True},
    ):
        calls.clear()
        result = execute_governed_step6_session_v1(
            expected_repository_sha=_sha(),
            expected_config_digest=_cfg(),
            owner_go=True,
            operator_authorization_explicit=True,
            network_session_go=True,
            authorization_valid=True,
            confirm_token_valid=True,
            allow_real_network_side_effects=True,
            invoke_executor=True,
            stdin_isatty=True,
            getpass_fn=lambda _p: "x" * 32,
            wallclock_runner=_fake_runner_factory(calls),
            session_start_state={},
            repo_root=REPO_ROOT,
            **kwargs,
        )
        assert len(calls) == 0
        assert result.network_session_started is False


def test_binding_only_and_offline_paths_remain_non_starting() -> None:
    offline = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_go=True,
        authorization_valid=True,
        confirm_token_valid=True,
        allow_real_network_side_effects=True,
        invoke_executor=True,
        stdin_isatty=True,
        getpass_fn=lambda _p: "x" * 32,
        repo_root=REPO_ROOT,
    )
    assert offline.network_session_started is False
    assert "NETWORK_SESSION_START_DEFERRED_IN_IMPLEMENTATION_CAPABILITY" in offline.blockers

    binding = execute_governed_step6_productive_session_offline_fail_closed_v1(
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
    assert binding.network_session_started is False
    assert "REAL_NETWORK_SESSION_FORBIDDEN_IN_THIS_BINDING_CAPABILITY" in binding.blockers
