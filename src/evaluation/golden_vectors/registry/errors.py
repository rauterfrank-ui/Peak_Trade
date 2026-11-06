"""GVEF evidence registry errors (BWP-9)."""

from __future__ import annotations


class GvefRegistryError(ValueError):
    """Fail-closed registry boundary violation."""
