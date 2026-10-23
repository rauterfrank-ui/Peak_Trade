"""Fail-closed errors for the read-only observation GET path."""

from __future__ import annotations


class ReadOnlyObservationGetError(RuntimeError):
    """Fail-closed violation of the isolated GET-only observation path."""


__all__ = ["ReadOnlyObservationGetError"]
