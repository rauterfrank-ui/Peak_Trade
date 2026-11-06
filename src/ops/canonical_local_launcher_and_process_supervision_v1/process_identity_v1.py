"""PID-reuse-safe process identity helpers (macOS-portable, no setsid CLI)."""

from __future__ import annotations

import hashlib
import os
import subprocess
from typing import Optional

from src.ops.canonical_local_launcher_and_process_supervision_v1.errors_v1 import (
    ProcessIdentityMismatchError,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.models_v1 import (
    ProcessIdentityV1,
)


def _run_ps(pid: int, fmt: str) -> str:
    try:
        completed = subprocess.run(
            ["ps", "-p", str(pid), "-o", fmt],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return ""
    if completed.returncode != 0:
        return ""
    lines = [ln.strip() for ln in completed.stdout.splitlines() if ln.strip()]
    if len(lines) < 2:
        # Some platforms omit header when using trailing '=' formats.
        return lines[0] if lines else ""
    return " ".join(lines[1:]).strip()


def process_state(pid: int) -> str:
    """Return ps state code (e.g. S/R/Z) or empty if absent."""
    return _run_ps(pid, "state=") or _run_ps(pid, "stat=")


def process_alive(pid: int) -> bool:
    """True only for a live, non-zombie process.

    Zombies still answer ``os.kill(pid, 0)`` on POSIX; treating them as alive
    breaks stop escalation (SIGKILL on a zombie pgid can raise EPERM on macOS).
    """
    if pid <= 0:
        return False
    state = process_state(pid)
    if not state:
        return False
    # First character is the primary state code on macOS/Linux.
    if state[0].upper() == "Z":
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but is not signalable by us — still "present".
        return state[0].upper() != "Z"
    except OSError:
        return False
    return True


def read_pgid(pid: int) -> Optional[int]:
    raw = _run_ps(pid, "pgid=")
    if not raw:
        try:
            return os.getpgid(pid)
        except OSError:
            return None
    try:
        return int(raw.split()[0])
    except (TypeError, ValueError, IndexError):
        return None


def read_process_start_identity(pid: int) -> str:
    """Stable start-time identity for PID-reuse detection.

    Prefers ``lstart`` (macOS/BSD). Falls back to ``etime`` then empty.
    """
    for fmt in ("lstart=", "lstart", "etime=", "etime"):
        value = _run_ps(pid, fmt)
        if value:
            return value
    return ""


def read_cmdline_fingerprint(pid: int) -> str:
    raw = _run_ps(pid, "args=") or _run_ps(pid, "command=")
    if not raw:
        return ""
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()


def capture_process_identity(pid: int) -> ProcessIdentityV1:
    if not process_alive(pid):
        raise ProcessIdentityMismatchError(f"pid_not_alive:{pid}")
    pgid = read_pgid(pid)
    if pgid is None:
        raise ProcessIdentityMismatchError(f"pgid_unreadable:{pid}")
    start_identity = read_process_start_identity(pid)
    if not start_identity:
        raise ProcessIdentityMismatchError(f"start_identity_unreadable:{pid}")
    return ProcessIdentityV1(
        pid=int(pid),
        pgid=int(pgid),
        process_start_identity=start_identity,
        cmdline_fingerprint=read_cmdline_fingerprint(pid),
    )


def verify_process_identity(expected: ProcessIdentityV1) -> ProcessIdentityV1:
    if not process_alive(expected.pid):
        raise ProcessIdentityMismatchError(
            f"pid_dead:{expected.pid}",
            payload=expected.to_dict(),
        )
    observed = capture_process_identity(expected.pid)
    if observed.pgid != expected.pgid:
        raise ProcessIdentityMismatchError(
            f"pgid_mismatch:expected={expected.pgid}:observed={observed.pgid}",
            payload={"expected": expected.to_dict(), "observed": observed.to_dict()},
        )
    if observed.process_start_identity != expected.process_start_identity:
        raise ProcessIdentityMismatchError(
            "process_start_identity_mismatch",
            payload={"expected": expected.to_dict(), "observed": observed.to_dict()},
        )
    if (
        expected.cmdline_fingerprint
        and observed.cmdline_fingerprint
        and expected.cmdline_fingerprint != observed.cmdline_fingerprint
    ):
        raise ProcessIdentityMismatchError(
            "cmdline_fingerprint_mismatch",
            payload={"expected": expected.to_dict(), "observed": observed.to_dict()},
        )
    return observed
