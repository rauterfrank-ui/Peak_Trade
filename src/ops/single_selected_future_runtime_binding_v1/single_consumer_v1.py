"""Exactly-one selection consumer lock for Cap 2.4 runtime binding."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    CONSUMER_LOCK_FILENAME,
    SELECTION_CONSUMER_IDENTITY,
)
from src.ops.single_selected_future_runtime_binding_v1.reason_codes_v1 import BindingFailureCodeV1


class DuplicateSelectionConsumerError(RuntimeError):
    def __init__(self, detail: str = "") -> None:
        code = BindingFailureCodeV1.DUPLICATE_SELECTION_CONSUMER.value
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


class SelectionRuntimeBindingConsumerV1:
    """Single productive consumer of Cap 2.3 persisted selection in the runtime host."""

    def __init__(
        self,
        *,
        state_root: Path,
        consumer_identity: str = SELECTION_CONSUMER_IDENTITY,
        session_id: str,
    ) -> None:
        self.state_root = Path(state_root)
        self.consumer_identity = consumer_identity
        self.session_id = session_id
        self._held = False
        self.lock_path = self.state_root / CONSUMER_LOCK_FILENAME

    def acquire(self, *, now_unix: float | None = None) -> None:
        self.state_root.mkdir(parents=True, exist_ok=True)
        wall = float(now_unix if now_unix is not None else time.time())
        payload = {
            "consumer_identity": self.consumer_identity,
            "session_id": self.session_id,
            "acquired_at_unix": wall,
            "pid": os.getpid(),
        }
        if self.lock_path.is_file():
            try:
                existing = json.loads(self.lock_path.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                raise DuplicateSelectionConsumerError(f"UNREADABLE_LOCK:{exc}") from exc
            existing_id = str(existing.get("consumer_identity") or "")
            existing_session = str(existing.get("session_id") or "")
            if existing_id and existing_id != self.consumer_identity:
                raise DuplicateSelectionConsumerError(f"CONFLICTING_IDENTITY:{existing_id}")
            if existing_session and existing_session != self.session_id:
                raise DuplicateSelectionConsumerError(f"CONFLICTING_SESSION:{existing_session}")
        tmp = self.lock_path.with_suffix(".lock.tmp")
        tmp.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, self.lock_path)
        self._held = True

    def assert_held(self) -> None:
        if not self._held:
            raise DuplicateSelectionConsumerError("CONSUMER_LOCK_NOT_HELD")
        if not self.lock_path.is_file():
            raise DuplicateSelectionConsumerError("CONSUMER_LOCK_MISSING")
        existing = json.loads(self.lock_path.read_text(encoding="utf-8"))
        if str(existing.get("consumer_identity") or "") != self.consumer_identity:
            raise DuplicateSelectionConsumerError("CONSUMER_IDENTITY_DRIFT")

    def release(self) -> None:
        if self.lock_path.is_file():
            try:
                self.lock_path.unlink()
            except FileNotFoundError:
                pass
        self._held = False
