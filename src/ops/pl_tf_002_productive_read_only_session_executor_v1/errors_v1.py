"""PL-TF-002 productive read-only session executor errors."""

from __future__ import annotations


class PlTf002ProductiveReadOnlySessionError(RuntimeError):
    """Fail-closed PL-TF-002 read-only GET session violation."""
