"""Single-writer lock for Cap 7.2 activation state."""

from __future__ import annotations

import os
from pathlib import Path

from src.ops.single_future_stateful_no_order_runtime_activation_v1.constants_v1 import (
    SINGLE_WRITER_IDENTITY,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.reason_codes_v1 import (
    ActivationFailureCodeV1,
)


class ConflictingWriterError(RuntimeError):
    def __init__(self, detail: str = "") -> None:
        super().__init__(
            f"{ActivationFailureCodeV1.WRITER_CONFLICT.value}:{detail}"
            if detail
            else ActivationFailureCodeV1.WRITER_CONFLICT.value
        )


class ActivationSingleWriterV1:
    def __init__(self, state_root: Path, *, writer_session_id: str) -> None:
        self.state_root = Path(state_root)
        self.writer_session_id = str(writer_session_id)
        self._lock_path = self.state_root / ".activation_writer.lock"
        self._held = False

    def acquire(self) -> None:
        self.state_root.mkdir(parents=True, exist_ok=True)
        if self._lock_path.exists():
            existing = self._lock_path.read_text(encoding="utf-8").strip()
            if existing and existing != self.writer_session_id:
                raise ConflictingWriterError(existing)
        self._lock_path.write_text(self.writer_session_id, encoding="utf-8")
        self._held = True

    def release(self) -> None:
        if not self._held:
            return
        try:
            if self._lock_path.exists():
                current = self._lock_path.read_text(encoding="utf-8").strip()
                if current == self.writer_session_id:
                    os.unlink(self._lock_path)
        except OSError:
            pass
        self._held = False

    def __enter__(self) -> ActivationSingleWriterV1:
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        self.release()

    @property
    def identity(self) -> str:
        return SINGLE_WRITER_IDENTITY
