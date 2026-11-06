"""Exclusive single-writer authority for governed universe snapshots."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from src.ops.governed_futures_universe_producer_v1.constants_v1 import (
    SINGLE_WRITER_IDENTITY,
    WRITER_LOCK_FILENAME,
)
from src.ops.governed_futures_universe_producer_v1.reason_codes_v1 import UniverseFailureCodeV1


class DuplicateUniverseWriterError(RuntimeError):
    """Raised when another universe producer writer holds or claims the lock."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.failure_code = UniverseFailureCodeV1.DUPLICATE_PRODUCER_WRITER.value


@dataclass
class GovernedUniverseSingleWriterV1:
    state_root: Path
    writer_identity: str = SINGLE_WRITER_IDENTITY
    session_id: str = "default"
    _held: bool = False

    @property
    def lock_path(self) -> Path:
        return Path(self.state_root) / WRITER_LOCK_FILENAME

    def acquire(self, *, now_unix: Optional[float] = None) -> None:
        root = Path(self.state_root)
        root.mkdir(parents=True, exist_ok=True)
        lock = self.lock_path
        payload = {
            "writer_identity": self.writer_identity,
            "session_id": self.session_id,
            "pid": os.getpid(),
            "acquired_at_unix": float(now_unix if now_unix is not None else time.time()),
        }
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(str(lock), flags, 0o644)
        except FileExistsError as exc:
            existing: dict[str, Any] = {}
            try:
                existing = json.loads(lock.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                existing = {"raw": "UNREADABLE"}
            raise DuplicateUniverseWriterError(
                f"DUPLICATE_PRODUCER_WRITER:existing={existing}"
            ) from exc
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, sort_keys=True, indent=2) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        self._held = True

    def release(self) -> None:
        if not self._held:
            return
        lock = self.lock_path
        if lock.is_file():
            try:
                existing = json.loads(lock.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                existing = {}
            if (
                existing.get("writer_identity") == self.writer_identity
                and existing.get("session_id") == self.session_id
            ):
                lock.unlink(missing_ok=True)
        self._held = False

    def assert_held(self) -> None:
        if not self._held:
            raise DuplicateUniverseWriterError("WRITER_LOCK_NOT_HELD")
        if not self.lock_path.is_file():
            raise DuplicateUniverseWriterError("WRITER_LOCK_MISSING")
        existing = json.loads(self.lock_path.read_text(encoding="utf-8"))
        if existing.get("writer_identity") != self.writer_identity:
            raise DuplicateUniverseWriterError("CONFLICTING_WRITER_IDENTITY")
        if existing.get("session_id") != self.session_id:
            raise DuplicateUniverseWriterError("CONFLICTING_WRITER_SESSION")
