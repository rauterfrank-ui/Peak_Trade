"""GVEF contract validation errors (fail-closed)."""

from __future__ import annotations


class GvefSchemaError(ValueError):
    """Schema validation failure; maps to SCHEMA_FAILURE in BWP-1."""

    failure_classification: str = "SCHEMA_FAILURE"

    def __init__(self, message: str, *, field: str | None = None) -> None:
        self.field = field
        super().__init__(message)


SCHEMA_FAILURE = "SCHEMA_FAILURE"
