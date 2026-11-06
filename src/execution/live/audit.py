"""
Deterministic audit trail for C2 live-session dryrun.

Governance-safe design:
- append-only audit events
- deterministic ordering via seq counter
- timestamps only from injected clock (no datetime.now())
- IO only via injected sinks
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Optional, Protocol, Sequence


class Clock(Protocol):
    def now(self) -> datetime: ...


class LineSink(Protocol):
    def write(self, line: str) -> None: ...


class AuditLevel(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


@dataclass(frozen=True)
class AuditEvent:
    ts: str
    seq: int
    level: AuditLevel
    code: str
    message: str
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        # Stable key ordering via json.dumps(sort_keys=True) at serialization boundary.
        return {
            "ts": self.ts,
            "seq": self.seq,
            "level": self.level.value,
            "code": self.code,
            "message": self.message,
            "meta": dict(self.meta),
        }


def _canonical_json(obj: Mapping[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _write_line(sink: Any, line: str) -> None:
    # Accept list sinks (tests), file-like sinks, or custom sink objects.
    if sink is None:
        return
    append = getattr(sink, "append", None)
    if callable(append):
        append(line)
        return
    write = getattr(sink, "write", None)
    if callable(write):
        write(line)
        return
    raise TypeError("Unsupported sink type: expected .append(str) or .write(str)")


class AuditTrail:
    """
    Deterministic audit collector with optional JSONL sink.

    Notes:
    - seq is strictly increasing per instance
    - ts comes from injected clock
    - sink writes JSONL lines (one AuditEvent per line)
    """

    def __init__(self, *, clock: Clock, sink: Any = None, seq_start: int = 0) -> None:
        self._clock = clock
        self._sink = sink
        self._seq = seq_start
        self._events: list[AuditEvent] = []

    @property
    def events(self) -> Sequence[AuditEvent]:
        return tuple(self._events)

    @property
    def next_seq(self) -> int:
        return self._seq

    def emit(
        self,
        *,
        level: AuditLevel,
        code: str,
        message: str,
        meta: Optional[Mapping[str, Any]] = None,
    ) -> AuditEvent:
        ev = AuditEvent(
            ts=self._clock.now().isoformat(),
            seq=self._seq,
            level=level,
            code=code,
            message=message,
            meta=dict(meta or {}),
        )
        self._seq += 1
        self._events.append(ev)
        _write_line(self._sink, _canonical_json(ev.to_dict()) + "\n")
        return ev

    def extend(self, events: Sequence[AuditEvent]) -> None:
        # Only used for tests/helpers; does not renumber seq.
        for ev in events:
            self._events.append(ev)
            _write_line(self._sink, _canonical_json(ev.to_dict()) + "\n")
