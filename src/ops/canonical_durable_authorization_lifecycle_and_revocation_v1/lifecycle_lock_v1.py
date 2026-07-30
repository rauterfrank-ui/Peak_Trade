"""Exclusive lifecycle lock covering revocation check + consumption (TOCTOU-safe)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.constants_v1 import (
    LIFECYCLE_LOCK_NAME,
)


class LifecycleLockError(RuntimeError):
    """Fail-closed lifecycle lock error."""


@dataclass
class AuthorizationLifecycleLockV1:
    lock_path: Path
    authorization_id: str
    owner: str
    acquired: bool = False
    fd: Optional[int] = None

    @classmethod
    def for_evidence_root(
        cls,
        *,
        evidence_root: Path,
        authorization_id: str,
        owner: str,
    ) -> "AuthorizationLifecycleLockV1":
        return cls(
            lock_path=Path(evidence_root) / LIFECYCLE_LOCK_NAME,
            authorization_id=authorization_id,
            owner=owner,
        )

    def acquire(self) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(str(self.lock_path), flags, 0o644)
        except FileExistsError as exc:
            raise LifecycleLockError("AUTHORIZATION_LIFECYCLE_LOCK_HELD") from exc
        payload = {
            "authorization_id": self.authorization_id,
            "owner": self.owner,
            "pid": os.getpid(),
        }
        os.write(fd, (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8"))
        os.fsync(fd)
        self.fd = fd
        self.acquired = True

    def assert_held(self) -> None:
        if not self.acquired or self.fd is None or not self.lock_path.is_file():
            raise LifecycleLockError("AUTHORIZATION_LIFECYCLE_LOCK_LOSS")

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
        return {
            "lock_path": str(self.lock_path),
            "authorization_id": self.authorization_id,
            "owner": self.owner,
            "acquired": self.acquired,
        }
