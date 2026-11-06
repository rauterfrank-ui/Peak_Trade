from __future__ import annotations

from typing import Any, Mapping, Sequence

from .normalized_event import NormalizedEvent


_ALLOWED_SENS = {"public", "internal", "restricted"}


def validate_normalized_event(ev: NormalizedEvent) -> None:
    if not isinstance(ev.event_id, str) or not ev.event_id:
        raise ValueError("event_id must be non-empty str")
    if not isinstance(ev.ts_ms, int) or ev.ts_ms < 0:
        raise ValueError("ts_ms must be non-negative int")
    for name in ("source", "kind", "scope"):
        v = getattr(ev, name)
        if not isinstance(v, str) or not v:
            raise ValueError(f"{name} must be non-empty str")
    if not isinstance(ev.tags, Sequence):
        raise ValueError("tags must be a sequence of str")
    if any((not isinstance(t, str) or not t) for t in ev.tags):
        raise ValueError("tags entries must be non-empty str")
    if ev.sensitivity not in _ALLOWED_SENS:
        raise ValueError(f"sensitivity must be one of {_ALLOWED_SENS}")
    if not isinstance(ev.payload, Mapping):
        raise ValueError("payload must be a mapping (JSON object)")
