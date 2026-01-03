"""Risk Layer Audit Log - Phase 0 Scaffold.

Minimal, deterministic, side-effect free implementtion.
Exists to satisfy imports/tests; no I/O, no global state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence


@dataclass(frozen=True)
class AuditRecord:
    """Phase-0 scaffold: minimal audit record."""

    event: str
    payload: Mapping[str, Any]


class AuditLogWriter:
    """Phase-0 scaffold: in-memory writer.

    Provides a small, compatibility-friendly surface.
    """

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []

    def write(self, event: str, payload: Optional[Mapping[str, Any]] = None) -> AuditRecord:
        """Write an audit record."""
        rec = AuditRecord(event=event, payload=dict(payload or {}))
        self._records.append(rec)
        return rec

    # Common aliases (defensive)
    append = write
    record = write

    def records(self) -> Sequence[AuditRecord]:
        """Return all recorded events."""
        return tuple(self._records)
