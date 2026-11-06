"""Contract tests for bouchaud OHLCV proxy v1 bound offline evaluation runner invocation v0."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from scripts.ops.offline_evaluation_runner_invocation_contract_v0 import (
    CONFIRM_GO_TOKEN_MISSING,
    EXIT_CONFIRM_GO_TOKEN_MISSING,
    INTERPRETER_RESOLUTION_PASS,
    RUNNER_INVOCATION_CONTRACT_PASS,
    invoke_bound_offline_evaluation_runner_v0,
    prepare_bound_offline_evaluation_runner_invocation_v0,
    read_confirm_go_token_from_env_v0,
    resolve_repo_local_python_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_REL_PATH = "scripts/ops/run_bouchaud_microstructure_ohlcv_proxy_v1_bound_offline_economic_baseline_evaluation_v0.py"
INVOKE_SCRIPT = (
    REPO_ROOT
    / "scripts/ops/invoke_bouchaud_microstructure_ohlcv_proxy_v1_bound_offline_economic_baseline_evaluation_v0.py"
)
CONFIRM_GO_VALUE = (
    "GO_BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_BOUND_OFFLINE_ECONOMIC_BASELINE_EVALUATION_V0"
)


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_local_venv_python() -> Iterator[None]:
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


def test_prepare_invocation_forwards_confirm_go_token_once_with_admissibility_flag() -> None:
    prepared = prepare_bound_offline_evaluation_runner_invocation_v0(
        repo_root=REPO_ROOT,
        runner_rel_path=RUNNER_REL_PATH,
        confirm_go_token=CONFIRM_GO_VALUE,
        extra_args=("--admissibility-validation-only",),
    )
    assert prepared.reason_code == RUNNER_INVOCATION_CONTRACT_PASS
    assert prepared.argv[2:4] == ("--confirm-go-token", CONFIRM_GO_VALUE)
    assert "--admissibility-validation-only" in prepared.argv


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
        extra_args=("--admissibility-validation-only",),
        subprocess_runner=_capture_runner,
    )
    assert exit_code == 0
    assert reason == RUNNER_INVOCATION_CONTRACT_PASS
    assert captured[0][2:4] == ["--confirm-go-token", CONFIRM_GO_VALUE]
    assert "--admissibility-validation-only" in captured[0]


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


def test_read_confirm_go_token_missing_fail_closed() -> None:
    token, reason, exit_code = read_confirm_go_token_from_env_v0({}, env_var_name="GO_TOKEN")
    assert token is None
    assert reason == CONFIRM_GO_TOKEN_MISSING
    assert exit_code == EXIT_CONFIRM_GO_TOKEN_MISSING
