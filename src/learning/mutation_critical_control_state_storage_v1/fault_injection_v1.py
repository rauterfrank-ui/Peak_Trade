"""Test-only write-boundary fault injection. Productive code must not call this."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Final, Iterator

from src.learning.mutation_critical_control_state_storage_v1.errors_v1 import (
    ControlStateValidationError,
)

BOUNDARY_BEFORE_PREPARE: Final[str] = "before_prepare"
BOUNDARY_DURING_PREPARE_WRITE: Final[str] = "during_prepare_write"
BOUNDARY_PREPARE_FILE_FSYNC: Final[str] = "prepare_file_fsync"
BOUNDARY_PREPARE_DIRECTORY_FSYNC: Final[str] = "prepare_directory_fsync"
BOUNDARY_DURING_PAYLOAD_WRITE: Final[str] = "during_payload_write"
BOUNDARY_DURING_COMMIT_WRITE: Final[str] = "during_commit_write"
BOUNDARY_COMMIT_FILE_FSYNC: Final[str] = "commit_file_fsync"
BOUNDARY_COMMIT_DIRECTORY_FSYNC: Final[str] = "commit_directory_fsync"
BOUNDARY_AFTER_COMMIT_BEFORE_RETURN: Final[str] = "after_commit_before_return"
BOUNDARY_LOCK_OPEN: Final[str] = "lock_open"
BOUNDARY_MKDIR: Final[str] = "mkdir"

FAULT_ACTION_RAISE: Final[str] = "raise"
FAULT_ACTION_PARTIAL_WRITE_THEN_RAISE: Final[str] = "partial_write_then_raise"

_BOUNDARIES: Final[frozenset[str]] = frozenset(
    {
        BOUNDARY_BEFORE_PREPARE,
        BOUNDARY_DURING_PREPARE_WRITE,
        BOUNDARY_PREPARE_FILE_FSYNC,
        BOUNDARY_PREPARE_DIRECTORY_FSYNC,
        BOUNDARY_DURING_PAYLOAD_WRITE,
        BOUNDARY_DURING_COMMIT_WRITE,
        BOUNDARY_COMMIT_FILE_FSYNC,
        BOUNDARY_COMMIT_DIRECTORY_FSYNC,
        BOUNDARY_AFTER_COMMIT_BEFORE_RETURN,
        BOUNDARY_LOCK_OPEN,
        BOUNDARY_MKDIR,
    }
)
_ACTIONS: Final[frozenset[str]] = frozenset(
    {FAULT_ACTION_RAISE, FAULT_ACTION_PARTIAL_WRITE_THEN_RAISE}
)


class ControlStateWalFaultInjectorV1:
    def __init__(
        self,
        *,
        boundary: str,
        action: str = FAULT_ACTION_RAISE,
        errno_code: int = 5,
    ) -> None:
        if boundary not in _BOUNDARIES:
            raise ControlStateValidationError(f"UNKNOWN_WAL_FAULT_BOUNDARY:{boundary}")
        if action not in _ACTIONS:
            raise ControlStateValidationError(f"UNKNOWN_WAL_FAULT_ACTION:{action}")
        if action == FAULT_ACTION_PARTIAL_WRITE_THEN_RAISE and boundary not in {
            BOUNDARY_DURING_PREPARE_WRITE,
            BOUNDARY_DURING_PAYLOAD_WRITE,
            BOUNDARY_DURING_COMMIT_WRITE,
        }:
            raise ControlStateValidationError("PARTIAL_WRITE_REQUIRES_WRITE_BOUNDARY")
        self.boundary = boundary
        self.action = action
        self.errno_code = errno_code
        self.fired = False

    def consume(self, boundary: str) -> bool:
        if boundary != self.boundary or self.fired:
            return False
        self.fired = True
        return True


_INJECTOR: ContextVar[ControlStateWalFaultInjectorV1 | None] = ContextVar(
    "control_state_wal_fault_injector_v1", default=None
)


def apply_wal_fault_v1(boundary: str) -> ControlStateWalFaultInjectorV1 | None:
    injector = _INJECTOR.get()
    if injector is None:
        return None
    if not injector.consume(boundary):
        return None
    if injector.action == FAULT_ACTION_RAISE:
        raise OSError(injector.errno_code, f"injected_wal_fault:{boundary}")
    return injector


@contextmanager
def control_state_wal_fault_injection_v1(
    injector: ControlStateWalFaultInjectorV1,
) -> Iterator[ControlStateWalFaultInjectorV1]:
    token: Token[ControlStateWalFaultInjectorV1 | None] = _INJECTOR.set(injector)
    try:
        yield injector
    finally:
        _INJECTOR.reset(token)
