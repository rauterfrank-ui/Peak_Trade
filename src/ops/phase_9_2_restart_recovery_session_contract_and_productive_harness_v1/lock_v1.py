"""Segment lock lifecycle: owner release only; orphan lock fail-closed."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from src.ops.phase_9_2_restart_recovery_session_contract_and_productive_harness_v1.constants_v1 import (
    LOCK_FILENAME,
    ORPHAN_LOCK_TAKEOVER_ALLOWED,
)


class RestartLockError(RuntimeError):
    """Fail-closed restart lock error."""


@dataclass
class RestartSegmentLockV1:
    lock_path: Path
    runtime_session_id: str
    owner: str
    acquired: bool = False
    fd: Optional[int] = None

    def acquire(self) -> None:
        if ORPHAN_LOCK_TAKEOVER_ALLOWED:
            raise RestartLockError("orphan_lock_takeover_misconfigured")
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(str(self.lock_path), flags, 0o644)
        except FileExistsError as exc:
            raise RestartLockError("ORPHAN_OR_DUPLICATE_LOCK_FAIL_CLOSED") from exc
        payload = {
            "runtime_session_id": self.runtime_session_id,
            "owner": self.owner,
            "pid": os.getpid(),
        }
        os.write(fd, (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8"))
        os.fsync(fd)
        self.fd = fd
        self.acquired = True

    def assert_owner(self) -> None:
        if not self.acquired or self.fd is None:
            raise RestartLockError("LOCK_NOT_HELD")
        if not self.lock_path.is_file():
            raise RestartLockError("LOCK_LOSS")
        current = json.loads(self.lock_path.read_text(encoding="utf-8"))
        if str(current.get("owner")) != self.owner:
            raise RestartLockError("LOCK_OWNER_MISMATCH")
        if str(current.get("runtime_session_id")) != self.runtime_session_id:
            raise RestartLockError("LOCK_SESSION_MISMATCH")

    def release_by_owner(self) -> None:
        self.assert_owner()
        if self.fd is not None:
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = None
        self.acquired = False
        if self.lock_path.exists():
            self.lock_path.unlink()

    def to_dict(self) -> dict[str, Any]:
        return {
            "lock_path": str(self.lock_path),
            "runtime_session_id": self.runtime_session_id,
            "owner": self.owner,
            "acquired": self.acquired,
            "orphan_lock_takeover_allowed": ORPHAN_LOCK_TAKEOVER_ALLOWED,
        }


def lock_path_for_root_v1(persistence_root: Path) -> Path:
    return Path(persistence_root) / LOCK_FILENAME
