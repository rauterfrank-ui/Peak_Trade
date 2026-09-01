"""Explicit failure modes for the offline DDO contract foundation v0."""

from __future__ import annotations


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
