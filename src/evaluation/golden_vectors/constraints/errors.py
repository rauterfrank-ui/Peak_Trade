"""GVEF constraint matrix errors (fail-closed)."""

from __future__ import annotations


class GvefConstraintMatrixError(Exception):
    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.field = field
