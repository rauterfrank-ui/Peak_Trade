"""Exclusive grant-ledger lock (cross-process, blocking flock)."""

from __future__ import annotations

import fcntl
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.ops.owner_scoped_get_budget_enforcement_v1.errors_v1 import OwnerScopedGetBudgetError


@dataclass
class OwnerScopedGetBudgetGrantLockV1:
    lock_path: Path
    grant_id: str
    acquired: bool = False
    fd: Optional[int] = None

    def acquire(self) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(self.lock_path), os.O_CREAT | os.O_RDWR, 0o644)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
        except OSError as exc:
            os.close(fd)
            raise OwnerScopedGetBudgetError("GRANT_LEDGER_LOCK_ACQUIRE_FAILED") from exc
        self.fd = fd
        self.acquired = True

    def assert_held(self) -> None:
        if not self.acquired or self.fd is None:
            raise OwnerScopedGetBudgetError("GRANT_LEDGER_LOCK_LOSS")

    def release(self) -> None:
        if self.fd is not None:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
            except OSError:
                pass
            try:
                os.close(self.fd)
            except OSError:
                pass
            self.fd = None
        self.acquired = False
