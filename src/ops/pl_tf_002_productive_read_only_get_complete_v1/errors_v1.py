"""Fail-closed errors for PL-TF-002 productive read-only GET completion."""

from __future__ import annotations


class PlTf002ProductiveReadOnlyGetCompleteError(RuntimeError):
    """Bounded PL-TF-002 capture / closure violation."""
