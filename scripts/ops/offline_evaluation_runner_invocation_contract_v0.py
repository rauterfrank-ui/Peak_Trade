#!/usr/bin/env python3
"""Shared offline evaluation runner invocation contract v0 (non-authorizing).

Resolves repo-local ``.venv/bin/python``, forwards ``--confirm-go-token`` argv-only,
and fail-closes before runner start when interpreter or token preconditions fail.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

REPO_VENV_PYTHON_REL: Final = Path(".venv/bin/python")

INTERPRETER_RESOLUTION_PASS: Final = "INTERPRETER_RESOLUTION_PASS"
REPO_VENV_PYTHON_MISSING: Final = "REPO_VENV_PYTHON_MISSING"
REPO_VENV_PYTHON_NOT_EXECUTABLE: Final = "REPO_VENV_PYTHON_NOT_EXECUTABLE"
CONFIRM_GO_TOKEN_MISSING: Final = "CONFIRM_GO_TOKEN_MISSING"
CONFIRM_GO_TOKEN_EMPTY: Final = "CONFIRM_GO_TOKEN_EMPTY"
RUNNER_INVOCATION_CONTRACT_PASS: Final = "RUNNER_INVOCATION_CONTRACT_PASS"
RUNNER_NOT_STARTED: Final = "RUNNER_NOT_STARTED"

EXIT_REPO_VENV_PYTHON_MISSING: Final = 127
EXIT_REPO_VENV_PYTHON_NOT_EXECUTABLE: Final = 127
EXIT_CONFIRM_GO_TOKEN_MISSING: Final = 125
EXIT_CONFIRM_GO_TOKEN_EMPTY: Final = 126


@dataclass(frozen=True)
class InvocationPreparation:
    reason_code: str
    exit_code: int
    interpreter: Path | None
    argv: tuple[str, ...]
    runner_started: bool


def resolve_repo_local_python_v0(repo_root: Path) -> tuple[Path | None, str]:
    interpreter = repo_root / REPO_VENV_PYTHON_REL
    if not interpreter.is_file():
        return None, REPO_VENV_PYTHON_MISSING
    if not os.access(interpreter, os.X_OK):
        return None, REPO_VENV_PYTHON_NOT_EXECUTABLE
    return interpreter, INTERPRETER_RESOLUTION_PASS


def read_confirm_go_token_from_env_v0(
    env: Mapping[str, str] | None = None,
    *,
    env_var_name: str = "GO_TOKEN",
) -> tuple[str | None, str, int]:
    mapping = os.environ if env is None else env
    if env_var_name not in mapping:
        return None, CONFIRM_GO_TOKEN_MISSING, EXIT_CONFIRM_GO_TOKEN_MISSING
    token = mapping[env_var_name]
    if token == "":
        return None, CONFIRM_GO_TOKEN_EMPTY, EXIT_CONFIRM_GO_TOKEN_EMPTY
    return token, RUNNER_INVOCATION_CONTRACT_PASS, 0


def build_runner_invocation_argv_v0(
    *,
    interpreter: Path,
    runner_script: Path,
    confirm_go_token: str,
    extra_args: Sequence[str] = (),
) -> list[str]:
    return [
        str(interpreter),
        str(runner_script),
        "--confirm-go-token",
        confirm_go_token,
        *extra_args,
    ]


def prepare_bound_offline_evaluation_runner_invocation_v0(
    *,
    repo_root: Path,
    runner_rel_path: str,
    confirm_go_token: str | None,
    extra_args: Sequence[str] = (),
) -> InvocationPreparation:
    interpreter, interpreter_reason = resolve_repo_local_python_v0(repo_root)
    if interpreter is None:
        return InvocationPreparation(
            reason_code=interpreter_reason,
            exit_code=EXIT_REPO_VENV_PYTHON_MISSING
            if interpreter_reason == REPO_VENV_PYTHON_MISSING
            else EXIT_REPO_VENV_PYTHON_NOT_EXECUTABLE,
            interpreter=None,
            argv=(),
            runner_started=False,
        )

    if confirm_go_token is None:
        return InvocationPreparation(
            reason_code=CONFIRM_GO_TOKEN_MISSING,
            exit_code=EXIT_CONFIRM_GO_TOKEN_MISSING,
            interpreter=interpreter,
            argv=(),
            runner_started=False,
        )
    if confirm_go_token == "":
        return InvocationPreparation(
            reason_code=CONFIRM_GO_TOKEN_EMPTY,
            exit_code=EXIT_CONFIRM_GO_TOKEN_EMPTY,
            interpreter=interpreter,
            argv=(),
            runner_started=False,
        )

    runner_script = (repo_root / runner_rel_path).resolve()
    argv = build_runner_invocation_argv_v0(
        interpreter=interpreter,
        runner_script=runner_script,
        confirm_go_token=confirm_go_token,
        extra_args=extra_args,
    )
    return InvocationPreparation(
        reason_code=RUNNER_INVOCATION_CONTRACT_PASS,
        exit_code=0,
        interpreter=interpreter,
        argv=tuple(argv),
        runner_started=False,
    )


def invoke_bound_offline_evaluation_runner_v0(
    *,
    repo_root: Path,
    runner_rel_path: str,
    confirm_go_token: str | None,
    extra_args: Sequence[str] = (),
    env: Mapping[str, str] | None = None,
    subprocess_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    cwd: Path | None = None,
) -> tuple[int, str]:
    preparation = prepare_bound_offline_evaluation_runner_invocation_v0(
        repo_root=repo_root,
        runner_rel_path=runner_rel_path,
        confirm_go_token=confirm_go_token,
        extra_args=extra_args,
    )
    if preparation.reason_code != RUNNER_INVOCATION_CONTRACT_PASS:
        return preparation.exit_code, preparation.reason_code

    completed = subprocess_runner(
        list(preparation.argv),
        cwd=repo_root if cwd is None else cwd,
        env=dict(os.environ if env is None else env),
        check=False,
    )
    return completed.returncode, RUNNER_INVOCATION_CONTRACT_PASS


def emit_invocation_contract_failure_v0(
    reason_code: str, *, stream: Callable[[str], None] | None = None
) -> None:
    writer = stream if stream is not None else sys.stderr.write
    writer(f"REASON_CODE={reason_code}\n")
    writer(f"RUNNER_NOT_STARTED={RUNNER_NOT_STARTED}\n")
