"""Process-group launch and deterministic termination (no setsid CLI)."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Mapping, Optional, Sequence

from src.ops.canonical_local_launcher_and_process_supervision_v1.constants_v1 import (
    DEFAULT_ESCALATION_KILL_TIMEOUT_SECONDS,
    DEFAULT_GRACEFUL_STOP_TIMEOUT_SECONDS,
    SETSID_CLI_REQUIRED,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.errors_v1 import (
    CanonicalLauncherError,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.models_v1 import (
    ProcessIdentityV1,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.process_identity_v1 import (
    capture_process_identity,
    process_alive,
)


def assert_no_setsid_cli_dependency() -> None:
    if SETSID_CLI_REQUIRED:
        raise CanonicalLauncherError(
            "PLATFORM_PORTABILITY_FAILURE",
            "SETSID_CLI_REQUIRED_TRUE",
        )


def spawn_detached_process_group(
    argv: Sequence[str],
    *,
    env: Mapping[str, str],
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
) -> ProcessIdentityV1:
    """Spawn a child in a new session/process group without the setsid CLI.

    Uses ``subprocess.Popen(..., start_new_session=True)`` (``os.setsid`` in the
    child on POSIX / macOS). An intermediate reaper process exits immediately so
    the supervised worker is adopted by init/launchd and is caller-independent.
    """
    assert_no_setsid_cli_dependency()
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    pid_file = stdout_path.parent / "worker.pid"
    if pid_file.exists():
        pid_file.unlink()

    # Intermediate process: start_new_session + spawn worker + write pid + exit.
    # The worker outlives both the caller and this intermediate process.
    bootstrap = f"""
import os, sys, subprocess, time
from pathlib import Path
argv = {list(argv)!r}
env = {dict(env)!r}
cwd = {str(cwd)!r}
stdout_path = Path({str(stdout_path)!r})
stderr_path = Path({str(stderr_path)!r})
pid_file = Path({str(pid_file)!r})
stdout_fh = open(stdout_path, "a", encoding="utf-8")
stderr_fh = open(stderr_path, "a", encoding="utf-8")
try:
    worker = subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=stdout_fh,
        stderr=stderr_fh,
        start_new_session=True,
        close_fds=True,
    )
finally:
    stdout_fh.close()
    stderr_fh.close()
pid_file.write_text(str(worker.pid) + "\\n", encoding="utf-8")
# Keep intermediate alive briefly so worker can setsid before we exit.
time.sleep(0.05)
sys.exit(0)
"""
    intermediate = subprocess.Popen(
        [python_executable(), "-c", bootstrap],
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    intermediate.wait(timeout=5.0)
    if intermediate.returncode not in (0, None):
        raise CanonicalLauncherError(
            "PROCESS_START_FAILURE",
            f"bootstrap_failed:rc={intermediate.returncode}",
        )

    deadline = time.time() + 3.0
    last_err: Optional[Exception] = None
    worker_pid: Optional[int] = None
    while time.time() < deadline:
        if pid_file.is_file():
            raw = pid_file.read_text(encoding="utf-8").strip()
            if raw.isdigit():
                worker_pid = int(raw)
        if worker_pid is not None and process_alive(worker_pid):
            try:
                return capture_process_identity(worker_pid)
            except Exception as exc:  # noqa: BLE001
                last_err = exc
        time.sleep(0.05)
    raise CanonicalLauncherError(
        "PROCESS_START_FAILURE",
        f"identity_capture_failed:pid={worker_pid}:err={last_err}",
    )


def _reap_if_child(pid: int) -> None:
    try:
        os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        return
    except OSError:
        return


def _signal_process_group(pgid: int, sig: signal.Signals, *, fallback_pid: int) -> None:
    """Signal the process group; fall back to the main PID on EPERM."""
    try:
        os.killpg(pgid, sig)
        return
    except ProcessLookupError:
        return
    except PermissionError:
        pass
    try:
        os.kill(-pgid, sig)
        return
    except ProcessLookupError:
        return
    except PermissionError:
        pass
    try:
        os.kill(fallback_pid, sig)
    except ProcessLookupError:
        return
    except PermissionError as exc:
        raise CanonicalLauncherError(
            "PROCESS_SUPERVISION_FAILURE",
            f"signal_permission:pgid={pgid}:pid={fallback_pid}:sig={sig.name}",
        ) from exc


def terminate_process_group(
    identity: ProcessIdentityV1,
    *,
    graceful_timeout_seconds: float = DEFAULT_GRACEFUL_STOP_TIMEOUT_SECONDS,
    kill_timeout_seconds: float = DEFAULT_ESCALATION_KILL_TIMEOUT_SECONDS,
) -> dict[str, object]:
    """Deterministic process-group stop with graceful → SIGKILL escalation."""
    pgid = int(identity.pgid)
    pid = int(identity.pid)
    escalated = False
    if process_alive(pid):
        _signal_process_group(pgid, signal.SIGTERM, fallback_pid=pid)
    deadline = time.time() + max(0.0, float(graceful_timeout_seconds))
    while time.time() < deadline:
        _reap_if_child(pid)
        if not process_alive(pid):
            return {
                "stopped": True,
                "escalated": False,
                "pgid": pgid,
                "pid": pid,
                "signal_path": "SIGTERM",
            }
        time.sleep(0.05)
    if process_alive(pid):
        escalated = True
        _signal_process_group(pgid, signal.SIGKILL, fallback_pid=pid)
        kill_deadline = time.time() + max(0.0, float(kill_timeout_seconds))
        while time.time() < kill_deadline:
            _reap_if_child(pid)
            if not process_alive(pid):
                break
            time.sleep(0.05)
    _reap_if_child(pid)
    still_alive = process_alive(pid)
    if still_alive:
        raise CanonicalLauncherError(
            "PROCESS_SUPERVISION_FAILURE",
            f"process_group_still_alive:pid={pid}:pgid={pgid}",
        )
    return {
        "stopped": True,
        "escalated": escalated,
        "pgid": pgid,
        "pid": pid,
        "signal_path": "SIGKILL" if escalated else "SIGTERM",
    }


def python_executable() -> str:
    return sys.executable
