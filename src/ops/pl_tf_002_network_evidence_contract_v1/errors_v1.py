"""PL-TF-002 network evidence contract errors."""

from __future__ import annotations


class PlTf002NetworkEvidenceError(RuntimeError):
    """Fail-closed PL-TF-002 evidence contract violation."""
