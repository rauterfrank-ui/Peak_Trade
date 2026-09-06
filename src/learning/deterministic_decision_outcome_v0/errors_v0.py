"""Explicit failure modes for the offline DDO contract foundation v0."""

from __future__ import annotations

import errno
from typing import Final


class DdoError(Exception):
    """Base error for the offline DDO contract foundation."""

    error_code = "DDO_ERROR"


class DdoValidationError(DdoError):
    error_code = "DDO_VALIDATION_ERROR"


class DdoUnsupportedSchemaVersionError(DdoError):
    error_code = "DDO_UNSUPPORTED_SCHEMA_VERSION"


class DdoMalformedRecordError(DdoError):
    error_code = "DDO_MALFORMED_RECORD"


class DdoDuplicateConflictError(DdoError):
    error_code = "DDO_DUPLICATE_CONFLICT"


class DdoLineageError(DdoError):
    error_code = "DDO_INVALID_LINEAGE"


class DdoIntegrityError(DdoError):
    error_code = "DDO_INTEGRITY_ERROR"


class DdoLedgerCorruptionError(DdoError):
    error_code = "DDO_LEDGER_CORRUPTION"


class DdoUnsupportedLineageSlotError(DdoError):
    error_code = "DDO_UNSUPPORTED_LINEAGE_SLOT"


class DdoSilentOverwriteError(DdoError):
    error_code = "DDO_SILENT_OVERWRITE_FORBIDDEN"


FAILURE_CLASS_PERMISSION_ACCESS: Final[str] = "PERMISSION_ACCESS_FAILURE"
FAILURE_CLASS_FILESYSTEM_CAPACITY: Final[str] = "FILESYSTEM_CAPACITY_FAILURE"
FAILURE_CLASS_PATH_TYPE_INVALID: Final[str] = "PATH_TYPE_INVALIDITY"
FAILURE_CLASS_SERIALIZATION_VALIDATION: Final[str] = "SERIALIZATION_VALIDATION_FAILURE"
FAILURE_CLASS_CORRUPTION_UNREADABLE: Final[str] = "CORRUPTION_PREEXISTING_UNREADABLE_LEDGER"
FAILURE_CLASS_UNSUPPORTED_SCHEMA: Final[str] = "UNSUPPORTED_SCHEMA"
FAILURE_CLASS_DUPLICATE_CONFLICT: Final[str] = "DUPLICATE_CONFLICT"
FAILURE_CLASS_CONCURRENT_WRITER: Final[str] = "CONCURRENT_WRITER_VIOLATION"
FAILURE_CLASS_UNKNOWN_IO: Final[str] = "UNKNOWN_UNCLASSIFIED_IO_FAILURE"

DURABILITY_FAILURE_CLASSES: Final[frozenset[str]] = frozenset(
    {
        FAILURE_CLASS_PERMISSION_ACCESS,
        FAILURE_CLASS_FILESYSTEM_CAPACITY,
        FAILURE_CLASS_PATH_TYPE_INVALID,
        FAILURE_CLASS_SERIALIZATION_VALIDATION,
        FAILURE_CLASS_CORRUPTION_UNREADABLE,
        FAILURE_CLASS_UNSUPPORTED_SCHEMA,
        FAILURE_CLASS_DUPLICATE_CONFLICT,
        FAILURE_CLASS_CONCURRENT_WRITER,
        FAILURE_CLASS_UNKNOWN_IO,
    }
)


class DdoDurabilityWriteError(DdoError):
    """Classified durability write failure. Not a trading authority."""

    error_code = "DDO_DURABILITY_WRITE_ERROR"

    def __init__(
        self,
        failure_class: str,
        message: str,
        *,
        retryable: bool | None = None,
        errno_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.failure_class = failure_class
        self.retryable = retryable
        self.errno_code = errno_code


class DdoConcurrentWriterError(DdoDurabilityWriteError):
    error_code = "DDO_CONCURRENT_WRITER"

    def __init__(self, message: str = "CONCURRENT_WRITER_VIOLATION") -> None:
        super().__init__(
            FAILURE_CLASS_CONCURRENT_WRITER,
            message,
            retryable=False,
        )


class DdoPathResolutionError(DdoValidationError):
    error_code = "DDO_PATH_RESOLUTION_ERROR"


def classify_oserror_v0(exc: OSError) -> DdoDurabilityWriteError:
    """Map OS errno to a proven DDO durability class. No path secrets in the message."""
    code = exc.errno
    if code in {errno.EACCES, errno.EPERM, errno.EROFS}:
        return DdoDurabilityWriteError(
            FAILURE_CLASS_PERMISSION_ACCESS,
            "PERMISSION_ACCESS_FAILURE",
            retryable=False,
            errno_code=code,
        )
    if code in {errno.ENOSPC, getattr(errno, "EDQUOT", None)}:
        return DdoDurabilityWriteError(
            FAILURE_CLASS_FILESYSTEM_CAPACITY,
            "FILESYSTEM_CAPACITY_FAILURE",
            retryable=False,
            errno_code=code,
        )
    if code in {
        errno.EISDIR,
        errno.ENOTDIR,
        errno.EINVAL,
        errno.ENAMETOOLONG,
        errno.ENOENT,
        errno.ELOOP,
    }:
        return DdoDurabilityWriteError(
            FAILURE_CLASS_PATH_TYPE_INVALID,
            "PATH_TYPE_INVALIDITY",
            retryable=False,
            errno_code=code,
        )
    if code in {errno.EAGAIN, errno.EWOULDBLOCK}:
        return DdoConcurrentWriterError("CONCURRENT_WRITER_VIOLATION")
    return DdoDurabilityWriteError(
        FAILURE_CLASS_UNKNOWN_IO,
        "UNKNOWN_UNCLASSIFIED_IO_FAILURE",
        retryable=None,
        errno_code=code,
    )


def classify_ddo_write_failure_v0(exc: BaseException) -> DdoDurabilityWriteError:
    """Classify a ledger write/open failure without inventing unprovable granularity."""
    if isinstance(exc, DdoDurabilityWriteError):
        return exc
    if isinstance(exc, DdoDuplicateConflictError):
        return DdoDurabilityWriteError(
            FAILURE_CLASS_DUPLICATE_CONFLICT,
            "DUPLICATE_CONFLICT",
            retryable=False,
        )
    if isinstance(exc, DdoUnsupportedSchemaVersionError):
        return DdoDurabilityWriteError(
            FAILURE_CLASS_UNSUPPORTED_SCHEMA,
            "UNSUPPORTED_SCHEMA",
            retryable=False,
        )
    if isinstance(exc, (DdoLedgerCorruptionError, DdoIntegrityError, DdoMalformedRecordError)):
        return DdoDurabilityWriteError(
            FAILURE_CLASS_CORRUPTION_UNREADABLE,
            "CORRUPTION_PREEXISTING_UNREADABLE_LEDGER",
            retryable=False,
        )
    if isinstance(exc, DdoSilentOverwriteError):
        return DdoDurabilityWriteError(
            FAILURE_CLASS_PATH_TYPE_INVALID,
            "PATH_TYPE_INVALIDITY",
            retryable=False,
        )
    if isinstance(exc, (DdoValidationError, DdoLineageError, DdoUnsupportedLineageSlotError)):
        return DdoDurabilityWriteError(
            FAILURE_CLASS_SERIALIZATION_VALIDATION,
            "SERIALIZATION_VALIDATION_FAILURE",
            retryable=False,
        )
    if isinstance(exc, OSError):
        return classify_oserror_v0(exc)
    return DdoDurabilityWriteError(
        FAILURE_CLASS_UNKNOWN_IO,
        "UNKNOWN_UNCLASSIFIED_IO_FAILURE",
        retryable=None,
    )
