"""Contract tests for ehlers_cycle_filter/v1 bound offline evaluation runner invocation v0."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from scripts.ops.offline_evaluation_runner_invocation_contract_v0 import (
    CONFIRM_GO_TOKEN_EMPTY,
    CONFIRM_GO_TOKEN_MISSING,
    EXIT_CONFIRM_GO_TOKEN_EMPTY,
    EXIT_CONFIRM_GO_TOKEN_MISSING,
    EXIT_REPO_VENV_PYTHON_MISSING,
    INTERPRETER_RESOLUTION_PASS,
    REPO_VENV_PYTHON_MISSING,
    REPO_VENV_PYTHON_NOT_EXECUTABLE,
    RUNNER_INVOCATION_CONTRACT_PASS,
    build_runner_invocation_argv_v0,
    invoke_bound_offline_evaluation_runner_v0,
    prepare_bound_offline_evaluation_runner_invocation_v0,
    read_confirm_go_token_from_env_v0,
    resolve_repo_local_python_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_REL_PATH = (
    "scripts/ops/run_ehlers_cycle_filter_v1_bound_offline_economic_baseline_evaluation_v0.py"
)
INVOKE_SCRIPT = (
    REPO_ROOT
    / "scripts/ops/invoke_ehlers_cycle_filter_v1_bound_offline_economic_baseline_evaluation_v0.py"
)
SHELL_WRAPPER = (
    REPO_ROOT
    / "scripts/ops/invoke_ehlers_cycle_filter_v1_bound_offline_economic_baseline_evaluation_v0.sh"
)
CONFIRM_GO_VALUE = "GO_EHLERS_CYCLE_FILTER_V1_BOUND_OFFLINE_ECONOMIC_BASELINE_EVALUATION_V0"


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_local_venv_python() -> Iterator[None]:
    """Provide repo-local interpreter for CI runners without a committed .venv."""
    venv_python = REPO_ROOT / ".venv/bin/python"
    created_symlink = False
    if not venv_python.is_file():
        venv_python.parent.mkdir(parents=True, exist_ok=True)
        venv_python.symlink_to(sys.executable)
        created_symlink = True
    yield
    if created_symlink and venv_python.is_symlink():
        venv_python.unlink()
        for parent in (venv_python.parent, venv_python.parent.parent):
            if parent.exists() and not any(parent.iterdir()):
                parent.rmdir()


def test_resolve_repo_local_python_uses_repo_venv() -> None:
    interpreter, reason = resolve_repo_local_python_v0(REPO_ROOT)
    assert reason == INTERPRETER_RESOLUTION_PASS
    assert interpreter is not None
    assert interpreter == REPO_ROOT / ".venv/bin/python"
    assert interpreter.is_file()
    assert os.access(interpreter, os.X_OK)


def test_prepare_invocation_forwards_confirm_go_token_once() -> None:
    prepared = prepare_bound_offline_evaluation_runner_invocation_v0(
        repo_root=REPO_ROOT,
        runner_rel_path=RUNNER_REL_PATH,
        confirm_go_token=CONFIRM_GO_VALUE,
    )
    assert prepared.reason_code == RUNNER_INVOCATION_CONTRACT_PASS
    assert prepared.interpreter is not None
    assert prepared.argv[0] == str(prepared.interpreter)
    assert prepared.argv[1] == str((REPO_ROOT / RUNNER_REL_PATH).resolve())
    assert prepared.argv[2:4] == ("--confirm-go-token", CONFIRM_GO_VALUE)
    assert prepared.argv.count("--confirm-go-token") == 1


def test_build_runner_invocation_argv_preserves_shell_metacharacters() -> None:
    token = "GO_TOKEN; rm -rf /"
    argv = build_runner_invocation_argv_v0(
        interpreter=Path("/tmp/repo/.venv/bin/python"),
        runner_script=Path("/tmp/repo/scripts/ops/runner.py"),
        confirm_go_token=token,
    )
    assert argv[-1] == token
    assert argv.count("--confirm-go-token") == 1


def test_read_confirm_go_token_missing_fail_closed() -> None:
    token, reason, exit_code = read_confirm_go_token_from_env_v0({}, env_var_name="GO_TOKEN")
    assert token is None
    assert reason == CONFIRM_GO_TOKEN_MISSING
    assert exit_code == EXIT_CONFIRM_GO_TOKEN_MISSING


def test_read_confirm_go_token_empty_fail_closed() -> None:
    token, reason, exit_code = read_confirm_go_token_from_env_v0(
        {"GO_TOKEN": ""},
        env_var_name="GO_TOKEN",
    )
    assert token is None
    assert reason == CONFIRM_GO_TOKEN_EMPTY
    assert exit_code == EXIT_CONFIRM_GO_TOKEN_EMPTY


def test_prepare_invocation_missing_token_does_not_start_runner() -> None:
    prepared = prepare_bound_offline_evaluation_runner_invocation_v0(
        repo_root=REPO_ROOT,
        runner_rel_path=RUNNER_REL_PATH,
        confirm_go_token=None,
    )
    assert prepared.reason_code == CONFIRM_GO_TOKEN_MISSING
    assert prepared.argv == ()
    assert prepared.runner_started is False


def test_prepare_invocation_empty_token_does_not_start_runner() -> None:
    prepared = prepare_bound_offline_evaluation_runner_invocation_v0(
        repo_root=REPO_ROOT,
        runner_rel_path=RUNNER_REL_PATH,
        confirm_go_token="",
    )
    assert prepared.reason_code == CONFIRM_GO_TOKEN_EMPTY
    assert prepared.argv == ()
    assert prepared.runner_started is False


def test_prepare_invocation_missing_venv_fail_closed(tmp_path: Path) -> None:
    prepared = prepare_bound_offline_evaluation_runner_invocation_v0(
        repo_root=tmp_path,
        runner_rel_path=RUNNER_REL_PATH,
        confirm_go_token=CONFIRM_GO_VALUE,
    )
    assert prepared.reason_code == REPO_VENV_PYTHON_MISSING
    assert prepared.exit_code == EXIT_REPO_VENV_PYTHON_MISSING
    assert prepared.argv == ()


def test_prepare_invocation_non_executable_venv_fail_closed(tmp_path: Path) -> None:
    interpreter = tmp_path / ".venv/bin/python"
    interpreter.parent.mkdir(parents=True)
    interpreter.write_text("#!/bin/sh\n", encoding="utf-8")
    interpreter.chmod(0o644)
    prepared = prepare_bound_offline_evaluation_runner_invocation_v0(
        repo_root=tmp_path,
        runner_rel_path=RUNNER_REL_PATH,
        confirm_go_token=CONFIRM_GO_VALUE,
    )
    assert prepared.reason_code == REPO_VENV_PYTHON_NOT_EXECUTABLE
    assert prepared.argv == ()


def test_invoke_does_not_start_runner_when_token_missing() -> None:
    calls: list[list[str]] = []

    def _forbidden_runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(list(args[0]))
        return subprocess.CompletedProcess(args=args, returncode=0)

    exit_code, reason = invoke_bound_offline_evaluation_runner_v0(
        repo_root=REPO_ROOT,
        runner_rel_path=RUNNER_REL_PATH,
        confirm_go_token=None,
        subprocess_runner=_forbidden_runner,
    )
    assert exit_code == EXIT_CONFIRM_GO_TOKEN_MISSING
    assert reason == CONFIRM_GO_TOKEN_MISSING
    assert calls == []


def test_invoke_forwards_exact_argv_without_economic_execution() -> None:
    captured: list[list[str]] = []

    def _capture_runner(
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        captured.append(list(argv))
        return subprocess.CompletedProcess(args=argv, returncode=0)

    exit_code, reason = invoke_bound_offline_evaluation_runner_v0(
        repo_root=REPO_ROOT,
        runner_rel_path=RUNNER_REL_PATH,
        confirm_go_token=CONFIRM_GO_VALUE,
        subprocess_runner=_capture_runner,
    )
    assert exit_code == 0
    assert reason == RUNNER_INVOCATION_CONTRACT_PASS
    assert len(captured) == 1
    assert captured[0][0].endswith("/.venv/bin/python")
    assert captured[0][1].endswith(RUNNER_REL_PATH)
    assert captured[0][2:4] == ["--confirm-go-token", CONFIRM_GO_VALUE]


def test_invoke_script_fail_closed_without_go_token() -> None:
    env = os.environ.copy()
    env.pop("GO_TOKEN", None)
    result = subprocess.run(
        [str(REPO_ROOT / ".venv/bin/python"), str(INVOKE_SCRIPT)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == EXIT_CONFIRM_GO_TOKEN_MISSING
    assert "REASON_CODE=CONFIRM_GO_TOKEN_MISSING" in result.stderr
    assert "RUNNER_NOT_STARTED=RUNNER_NOT_STARTED" in result.stderr


def test_shell_wrapper_fail_closed_without_go_token() -> None:
    env = os.environ.copy()
    env.pop("GO_TOKEN", None)
    env["PATH"] = "/usr/bin:/bin"
    result = subprocess.run(
        ["bash", str(SHELL_WRAPPER)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == EXIT_CONFIRM_GO_TOKEN_MISSING
    assert "REASON_CODE=CONFIRM_GO_TOKEN_MISSING" in result.stderr


def test_shell_wrapper_works_without_global_python_on_path() -> None:
    captured: list[list[str]] = []

    def _capture_runner(
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        captured.append(list(argv))
        return subprocess.CompletedProcess(args=argv, returncode=0)

    exit_code, reason = invoke_bound_offline_evaluation_runner_v0(
        repo_root=REPO_ROOT,
        runner_rel_path=RUNNER_REL_PATH,
        confirm_go_token=CONFIRM_GO_VALUE,
        subprocess_runner=_capture_runner,
    )
    assert exit_code == 0
    assert reason == RUNNER_INVOCATION_CONTRACT_PASS
    assert captured[0][0].endswith("/.venv/bin/python")


def test_invalid_token_still_reaches_runner_for_existing_validation() -> None:
    captured: list[list[str]] = []

    def _capture_runner(
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        captured.append(list(argv))
        return subprocess.CompletedProcess(args=argv, returncode=2, stderr="ERR: invalid_go_token")

    exit_code, reason = invoke_bound_offline_evaluation_runner_v0(
        repo_root=REPO_ROOT,
        runner_rel_path=RUNNER_REL_PATH,
        confirm_go_token="GO_INVALID_TOKEN",
        subprocess_runner=_capture_runner,
    )
    assert reason == RUNNER_INVOCATION_CONTRACT_PASS
    assert exit_code == 2
    assert captured[0][2:4] == ["--confirm-go-token", "GO_INVALID_TOKEN"]


def test_regression_exit_127_when_repo_venv_missing(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            "bash",
            "-lc",
            (
                f"export PATH=/usr/bin:/bin; "
                f"REPO={tmp_path}; "
                f"INTERPRETER=$REPO/.venv/bin/python; "
                f"if [[ ! -f $INTERPRETER ]]; then "
                f"printf 'REASON_CODE=REPO_VENV_PYTHON_MISSING\\n'; exit 127; fi"
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 127
    assert "REASON_CODE=REPO_VENV_PYTHON_MISSING" in result.stdout
