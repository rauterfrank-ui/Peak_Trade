"""Exclusive single-writer lock for the O2 launcher registry root."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from src.ops.local_single_writer_lock_recovery_v1 import acquire_exclusive_local_writer_lock_v1

from src.ops.canonical_local_launcher_and_process_supervision_v1.constants_v1 import (
    SINGLE_WRITER_IDENTITY,
    WRITER_LOCK_FILENAME,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.errors_v1 import (
    ConflictingWriterError,
)


@dataclass
class LauncherSingleWriterV1:
    registry_root: Path
    writer_identity: str = SINGLE_WRITER_IDENTITY
    session_id: str = "default"
    _held: bool = False

    @property
    def lock_path(self) -> Path:
        return Path(self.registry_root) / WRITER_LOCK_FILENAME

    def acquire(self, *, now_unix: Optional[float] = None) -> None:
        root = Path(self.registry_root)
        root.mkdir(parents=True, exist_ok=True)
        lock = self.lock_path
        payload = {
            "writer_identity": self.writer_identity,
            "session_id": self.session_id,
            "pid": os.getpid(),
            "acquired_at_unix": float(now_unix if now_unix is not None else time.time()),
        }
        try:
            acquire_exclusive_local_writer_lock_v1(
                lock, writer_identity=self.writer_identity, payload=payload
            )
        except FileExistsError as exc:
            existing: dict[str, Any] = {}
            try:
                existing = json.loads(lock.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                existing = {"raw": "UNREADABLE"}
            raise ConflictingWriterError(f"existing={existing}", payload=existing) from exc
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

    def __enter__(self) -> "LauncherSingleWriterV1":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        self.release()
