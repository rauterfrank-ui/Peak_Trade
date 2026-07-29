"""Exclusive filesystem session lock."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional


class SessionLockError(RuntimeError):
    """Fail-closed session lock error."""


@dataclass
class SessionLockV1:
    lock_path: Path
    session_id: str
    owner: str
    acquired: bool = False
    fd: Optional[int] = None

    def acquire(self) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(str(self.lock_path), flags, 0o644)
        except FileExistsError as exc:
            raise SessionLockError("ABORT_DUPLICATE_SESSION") from exc
        payload = {
            "session_id": self.session_id,
            "owner": self.owner,
            "pid": os.getpid(),
        }
        os.write(fd, (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8"))
        os.fsync(fd)
        self.fd = fd
        self.acquired = True

    def assert_held(self) -> None:
        if not self.acquired or self.fd is None:
            raise SessionLockError("LOCK_LOSS")
        if not self.lock_path.is_file():
            raise SessionLockError("LOCK_LOSS")

    def release(self) -> None:
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
        return asdict(self) | {"lock_path": str(self.lock_path), "fd": None}
