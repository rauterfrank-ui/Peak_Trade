"""Single-writer fencing for Cap 6.5 exit-policy state."""

from __future__ import annotations

import os
import time
from pathlib import Path

from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
    SINGLE_WRITER_IDENTITY,
    WRITER_LOCK_FILENAME,
)
from src.ops.exit_policy_producer_binding_v1.reason_codes_v1 import (
    ExitPolicyBindingFailureCodeV1,
)


class ConflictingWriterError(RuntimeError):
    def __init__(self, detail: str = "") -> None:
        super().__init__(
            f"{ExitPolicyBindingFailureCodeV1.WRITER_CONFLICT.value}:{detail}"
            if detail
            else ExitPolicyBindingFailureCodeV1.WRITER_CONFLICT.value
        )
        self.code = ExitPolicyBindingFailureCodeV1.WRITER_CONFLICT


class ExitPolicySingleWriterV1:
    def __init__(
        self,
        state_root: Path,
        *,
        writer_session_id: str,
        identity: str = SINGLE_WRITER_IDENTITY,
    ) -> None:
        self.state_root = Path(state_root)
        self.writer_session_id = writer_session_id
        self.identity = identity
        self._lock_path = self.state_root / WRITER_LOCK_FILENAME
        self._fd: int | None = None

    def __enter__(self) -> "ExitPolicySingleWriterV1":
        self.state_root.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(self._lock_path), os.O_CREAT | os.O_RDWR, 0o644)
        try:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(fd)
            raise ConflictingWriterError(str(exc)) from exc
        payload = f"{self.identity}:{self.writer_session_id}:{time.time()}\n".encode()
        os.ftruncate(fd, 0)
        os.write(fd, payload)
        self._fd = fd
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        if self._fd is not None:
            try:
                import fcntl

                fcntl.flock(self._fd, fcntl.LOCK_UN)
            finally:
                os.close(self._fd)
                self._fd = None
