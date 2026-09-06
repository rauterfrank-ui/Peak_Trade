"""Fail-closed errors for mutation-critical control-state storage."""

from __future__ import annotations


class MutationCriticalControlStateStorageError(RuntimeError):
    """Base fail-closed error. Never a success classification."""


class ControlStateConcurrentWriterError(MutationCriticalControlStateStorageError):
    pass


class ControlStateCorruptionError(MutationCriticalControlStateStorageError):
    pass


class ControlStateSchemaMismatchError(MutationCriticalControlStateStorageError):
    pass


class ControlStateVersionMismatchError(MutationCriticalControlStateStorageError):
    pass


class ControlStateDuplicateConflictError(MutationCriticalControlStateStorageError):
    pass


class ControlStateIncompleteTransactionError(MutationCriticalControlStateStorageError):
    pass


class ControlStateTornWriteError(MutationCriticalControlStateStorageError):
    pass


class ControlStatePermissionError(MutationCriticalControlStateStorageError):
    pass


class ControlStateStorageFullError(MutationCriticalControlStateStorageError):
    pass


class ControlStateFutureOnlyError(MutationCriticalControlStateStorageError):
    pass


class ControlStateWrongOwnerError(MutationCriticalControlStateStorageError):
    pass


class ControlStateMissingDependencyError(MutationCriticalControlStateStorageError):
    pass


class ControlStateAmbiguousRetryError(MutationCriticalControlStateStorageError):
    pass


class ControlStateUnknownError(MutationCriticalControlStateStorageError):
    pass


class ControlStateValidationError(MutationCriticalControlStateStorageError):
    pass


def classify_oserror_v1(
    exc: OSError, *, operation: str
) -> MutationCriticalControlStateStorageError:
    errno_code = getattr(exc, "errno", None)
    if errno_code in {13, 1}:  # EACCES, EPERM
        return ControlStatePermissionError(f"STORAGE_PERMISSION_FAILURE:{operation}:{errno_code}")
    if errno_code == 28:  # ENOSPC
        return ControlStateStorageFullError(f"STORAGE_FULL:{operation}:{errno_code}")
    return MutationCriticalControlStateStorageError(f"STORAGE_OS_FAILURE:{operation}:{errno_code}")
