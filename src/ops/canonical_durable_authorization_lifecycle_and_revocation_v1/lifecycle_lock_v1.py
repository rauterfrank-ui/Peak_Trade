"""Exclusive lifecycle lock covering revocation check + consumption (TOCTOU-safe)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Mapping, Callable
from uuid import uuid4

from src.ops.local_single_writer_lock_recovery_v1 import acquire_exclusive_local_writer_lock_v1

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
    # Technical exclusion only; generic consumption/revocation locks stay strict.
    recover_dead_local_owner: bool = False
    recovery_context: Mapping[str, Any] | None = None
    dead_owner_validator: Callable[[Mapping[str, Any]], bool] | None = None
    _claim_id: Optional[str] = field(default=None, init=False, repr=False)

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
        if self.recover_dead_local_owner:
            if self.acquired:
                raise LifecycleLockError("AUTHORIZATION_LIFECYCLE_LOCK_HELD")
            self._claim_id = uuid4().hex
            payload = {
                "authorization_id": self.authorization_id,
                "owner": self.owner,
                "writer_identity": f"{self.owner}:{self.authorization_id}",
                "pid": os.getpid(),
                "claim_id": self._claim_id,
                "recovery_context": dict(self.recovery_context or {}),
            }
            try:
                acquire_exclusive_local_writer_lock_v1(
                    self.lock_path,
                    writer_identity=payload["writer_identity"],
                    payload=payload,
                    dead_owner_validator=self.dead_owner_validator,
                )
            except FileExistsError as exc:
                raise LifecycleLockError("AUTHORIZATION_LIFECYCLE_LOCK_HELD") from exc
            self.fd = os.open(self.lock_path, os.O_RDONLY)
            self.acquired = True
            return
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
        if self.recover_dead_local_owner:
            try:
                payload = json.loads(self.lock_path.read_text())
            except (OSError, ValueError) as exc:
                raise LifecycleLockError("AUTHORIZATION_LIFECYCLE_LOCK_LOSS") from exc
            if (
                not isinstance(payload, dict)
                or payload.get("claim_id") != self._claim_id
                or payload.get("pid") != os.getpid()
                or payload.get("authorization_id") != self.authorization_id
                or payload.get("owner") != self.owner
                or payload.get("writer_identity") != f"{self.owner}:{self.authorization_id}"
            ):
                raise LifecycleLockError("AUTHORIZATION_LIFECYCLE_LOCK_LOSS")

    def release(self) -> None:
        if self.recover_dead_local_owner:
            if not self.acquired:
                return
            # An unsuccessful/obsolete owner must never remove a newer claim.
            try:
                self.assert_held()
            except LifecycleLockError:
                if self.fd is not None:
                    os.close(self.fd)
                    self.fd = None
                self.acquired = False
                return
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
