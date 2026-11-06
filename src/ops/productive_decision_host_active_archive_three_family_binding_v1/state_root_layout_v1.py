"""Versioned runtime state-root layout and single-writer fencing."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from src.ops.productive_decision_host_active_archive_three_family_binding_v1.authorization_v1 import (
    ProductiveHostAuthorizationError,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.constants_v1 import (
    ACCOUNTING_STATE_DIRNAME,
    ACTIVATION_STATE_DIRNAME,
    CANONICAL_DECISION_SOURCE_DIRNAME,
    CONFIRMATION_STATE_DIRNAME,
    DYNAMIC_SCOPE_STATE_DIRNAME,
    EVIDENCE_SESSION_DIRNAME,
    EXPORT_CURSOR_FILENAME,
    RUNTIME_STATE_DIRNAME,
    SESSION_STATE_FILENAME,
    SINGLE_WRITER_IDENTITY,
    STATE_LAYOUT_VERSION,
    WRITER_LOCK_FILENAME,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.models_v1 import (
    StateRootBindingV1,
)


def materialize_state_root_layout_v1(
    *,
    runtime_root: str | Path,
) -> StateRootBindingV1:
    """Create versioned durable state roots under an explicit runtime root.

    Runtime roots are decision-authority storage. They must not equal the
    dashboard archive root.
    """
    root = Path(runtime_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    runtime_state = root / RUNTIME_STATE_DIRNAME / STATE_LAYOUT_VERSION
    dynamic_scope = runtime_state / DYNAMIC_SCOPE_STATE_DIRNAME
    confirmation = runtime_state / CONFIRMATION_STATE_DIRNAME
    activation = runtime_state / ACTIVATION_STATE_DIRNAME
    accounting = runtime_state / ACCOUNTING_STATE_DIRNAME
    decision_source = runtime_state / CANONICAL_DECISION_SOURCE_DIRNAME
    evidence = root / EVIDENCE_SESSION_DIRNAME
    for path in (
        dynamic_scope,
        confirmation,
        activation,
        accounting,
        decision_source,
        evidence,
    ):
        path.mkdir(parents=True, exist_ok=True)
    lock_path = root / WRITER_LOCK_FILENAME
    return StateRootBindingV1(
        layout_version=STATE_LAYOUT_VERSION,
        runtime_root=str(root),
        dynamic_scope_state_root=str(dynamic_scope),
        confirmation_state_root=str(confirmation),
        activation_state_root=str(activation),
        accounting_state_root=str(accounting),
        canonical_decision_source_dir=str(decision_source),
        evidence_session_root=str(evidence),
        writer_lock_path=str(lock_path),
    )


@dataclass
class ProductiveHostSingleWriterV1:
    """Process-local exclusive lock for the productive decision host session."""

    lock_path: Path
    session_id: str
    identity: str = SINGLE_WRITER_IDENTITY
    _fd: Optional[int] = None
    _held: bool = False

    def acquire(self, *, timeout_seconds: float = 0.0) -> None:
        path = Path(self.lock_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.time() + max(0.0, float(timeout_seconds))
        while True:
            try:
                fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            except FileExistsError:
                # Stale or live foreign lock.
                try:
                    existing = json.loads(path.read_text(encoding="utf-8"))
                except Exception:  # noqa: BLE001
                    existing = {}
                foreign = str(existing.get("session_id") or "")
                if foreign and foreign != self.session_id:
                    raise ProductiveHostAuthorizationError(
                        "SECOND_WRITER_REJECTED",
                        f"existing_session={foreign}:requested={self.session_id}",
                    )
                # Same session recovery: remove stale lock if PID dead.
                pid = int(existing.get("pid") or 0)
                if pid and _pid_alive(pid) and foreign == self.session_id:
                    raise ProductiveHostAuthorizationError(
                        "WRITER_ALREADY_HELD",
                        f"session={self.session_id}:pid={pid}",
                    )
                try:
                    path.unlink(missing_ok=True)  # type: ignore[call-arg]
                except TypeError:
                    if path.exists():
                        path.unlink()
                if time.time() > deadline:
                    raise ProductiveHostAuthorizationError(
                        "WRITER_LOCK_TIMEOUT",
                        str(path),
                    )
                time.sleep(0.05)
                continue
            payload = {
                "identity": self.identity,
                "session_id": self.session_id,
                "pid": os.getpid(),
                "acquired_at_unix": time.time(),
            }
            os.write(fd, (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8"))
            os.fsync(fd)
            self._fd = fd
            self._held = True
            return

    def release(self) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None
        self._held = False
        path = Path(self.lock_path)
        try:
            if path.is_file():
                raw = json.loads(path.read_text(encoding="utf-8"))
                if str(raw.get("session_id") or "") == self.session_id:
                    path.unlink()
        except Exception:  # noqa: BLE001
            pass

    def __enter__(self) -> "ProductiveHostSingleWriterV1":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self.release()


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def write_session_contract_v1(*, evidence_root: Path, payload: dict[str, Any]) -> Path:
    path = Path(evidence_root) / SESSION_STATE_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(body, encoding="utf-8")
    os.replace(tmp, path)
    return path


def load_export_cursor_v1(evidence_root: Path) -> dict[str, Any]:
    path = Path(evidence_root) / EXPORT_CURSOR_FILENAME
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return raw if isinstance(raw, dict) else {}


def persist_export_cursor_v1(evidence_root: Path, cursor: dict[str, Any]) -> Path:
    path = Path(evidence_root) / EXPORT_CURSOR_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(cursor, sort_keys=True, indent=2) + "\n"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(body, encoding="utf-8")
    os.replace(tmp, path)
    return path
