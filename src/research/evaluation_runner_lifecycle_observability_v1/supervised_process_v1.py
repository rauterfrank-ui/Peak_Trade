"""Supervised child-process execution with drain, reap, and exit classification."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.evaluation_runner_lifecycle_observability_v1.classification_v1 import (
    DEATH_CLASS_NO_RESULT_EOF,
    DEATH_CLASS_TIMEOUT_OR_MISSING_HEARTBEAT,
    DEATH_CLASS_WORKER_EXCEPTION,
    normalize_process_exit_v1,
)
from src.research.evaluation_runner_lifecycle_observability_v1.constants_v1 import (
    MAX_TRACEBACK_CHARS,
)


@dataclass(frozen=True)
class SupervisedProcessResultV1:
    returncode: int | None
    exit_code: int | None
    signal_name: str | None
    death_class: str
    process_completed: bool
    stdout: str
    stderr: str
    timed_out: bool
    abrupt_eof: bool
    worker_exception_observed: bool
    pid: int | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "returncode": self.returncode,
            "exit_code": self.exit_code,
            "signal_name": self.signal_name,
            "death_class": self.death_class,
            "process_completed": self.process_completed,
            "stdout_chars": len(self.stdout),
            "stderr_chars": len(self.stderr),
            "timed_out": self.timed_out,
            "abrupt_eof": self.abrupt_eof,
            "worker_exception_observed": self.worker_exception_observed,
            "pid": self.pid,
        }


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)] + "..."


def run_supervised_python_worker_v1(
    *,
    code: str,
    timeout_seconds: float | None = None,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
    python_executable: str | None = None,
    send_signal: int | None = None,
    signal_after_seconds: float = 0.05,
) -> SupervisedProcessResultV1:
    """Run a synthetic Python worker under Popen with stdout/stderr drain + reap.

    Parent always consumes pipes and waits (or times out and terminates).
    Does not auto-rerun. Intended for lifecycle observability / tests.
    """
    exe = python_executable or sys.executable
    merged_env = dict(os.environ if env is None else env)
    # Avoid leaking sensitive host env into worker logs; keep PATH/PYTHONPATH minimal.
    proc = subprocess.Popen(
        [exe, "-c", code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(cwd) if cwd is not None else None,
        env=merged_env,
        text=True,
    )
    pid = proc.pid
    timed_out = False
    abrupt_eof = False
    stdout = ""
    stderr = ""
    returncode: int | None = None

    try:
        if send_signal is not None:
            time.sleep(max(0.0, float(signal_after_seconds)))
            if proc.poll() is None:
                proc.send_signal(send_signal)
        try:
            stdout, stderr = proc.communicate(timeout=timeout_seconds)
            returncode = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            stdout, stderr = proc.communicate()
            returncode = proc.returncode
    finally:
        # Hard reap: ensure no zombie even if communicate failed oddly.
        if proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass
            try:
                out2, err2 = proc.communicate(timeout=2)
                stdout = stdout or out2
                stderr = stderr or err2
            except Exception:
                pass
        if returncode is None:
            returncode = proc.poll()

    stdout = stdout or ""
    stderr = stderr or ""
    # Abrupt EOF: process ended with empty stdout and no structured result marker.
    if (not timed_out) and ("WORKER_RESULT=" not in stdout) and returncode != 0:
        abrupt_eof = True

    normalized = normalize_process_exit_v1(returncode=returncode)
    death_class = normalized["death_class"]
    worker_exception_observed = "Traceback (most recent call last)" in stderr or (
        "WORKER_EXCEPTION=" in stdout or "WORKER_EXCEPTION=" in stderr
    )
    if timed_out:
        death_class = DEATH_CLASS_TIMEOUT_OR_MISSING_HEARTBEAT
    elif worker_exception_observed and death_class != "SIGNAL_TERMINATION":
        death_class = DEATH_CLASS_WORKER_EXCEPTION
    elif abrupt_eof and death_class not in {"SIGNAL_TERMINATION", "CLEAN_EXIT"}:
        death_class = DEATH_CLASS_NO_RESULT_EOF

    return SupervisedProcessResultV1(
        returncode=returncode,
        exit_code=normalized["exit_code"],
        signal_name=normalized["signal_name"],
        death_class=death_class,
        process_completed=bool(normalized["process_completed"]),
        stdout=_truncate(stdout, MAX_TRACEBACK_CHARS),
        stderr=_truncate(stderr, MAX_TRACEBACK_CHARS),
        timed_out=timed_out,
        abrupt_eof=abrupt_eof,
        worker_exception_observed=worker_exception_observed,
        pid=pid,
    )


def portable_terminating_signal_v1() -> int:
    """Prefer SIGTERM for portable synthetic signal-death tests."""
    return int(signal.SIGTERM)


def run_supervised_argv_v1(
    argv: Sequence[str],
    *,
    timeout_seconds: float | None = None,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> SupervisedProcessResultV1:
    """Supervise an arbitrary argv child (tests / harness only)."""
    proc = subprocess.Popen(
        list(argv),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(cwd) if cwd is not None else None,
        env=dict(os.environ if env is None else env),
        text=True,
    )
    pid = proc.pid
    timed_out = False
    stdout = ""
    stderr = ""
    returncode: int | None = None
    try:
        try:
            stdout, stderr = proc.communicate(timeout=timeout_seconds)
            returncode = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            stdout, stderr = proc.communicate()
            returncode = proc.returncode
    finally:
        if proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass
            try:
                proc.communicate(timeout=2)
            except Exception:
                pass
        if returncode is None:
            returncode = proc.poll()

    stdout = stdout or ""
    stderr = stderr or ""
    abrupt_eof = (not timed_out) and ("WORKER_RESULT=" not in stdout) and returncode != 0
    normalized = normalize_process_exit_v1(returncode=returncode)
    death_class = normalized["death_class"]
    worker_exception_observed = "Traceback (most recent call last)" in stderr
    if timed_out:
        death_class = DEATH_CLASS_TIMEOUT_OR_MISSING_HEARTBEAT
    elif worker_exception_observed:
        death_class = DEATH_CLASS_WORKER_EXCEPTION
    elif abrupt_eof and death_class not in {"SIGNAL_TERMINATION", "CLEAN_EXIT"}:
        death_class = DEATH_CLASS_NO_RESULT_EOF

    return SupervisedProcessResultV1(
        returncode=returncode,
        exit_code=normalized["exit_code"],
        signal_name=normalized["signal_name"],
        death_class=death_class,
        process_completed=bool(normalized["process_completed"]),
        stdout=_truncate(stdout, MAX_TRACEBACK_CHARS),
        stderr=_truncate(stderr, MAX_TRACEBACK_CHARS),
        timed_out=timed_out,
        abrupt_eof=abrupt_eof,
        worker_exception_observed=worker_exception_observed,
        pid=pid,
    )
