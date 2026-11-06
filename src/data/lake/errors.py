from __future__ import annotations


class LakeError(Exception):
    """Base error for LakeClient operations."""


class LakeQueryError(LakeError):
    """Raised when a query() operation fails."""


class LakeExecuteError(LakeError):
    """Raised when an execute() operation fails."""
