"""Decode existing public-fact clocks without inventing observation time."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any, Mapping


def capture_order_key_v1(value: Any) -> tuple[datetime, int]:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("public fact capture timestamp missing")
    match = re.fullmatch(
        r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,9}))?(Z|[+-]\d{2}:\d{2})", value
    )
    if match is None:
        raise ValueError("public fact capture timestamp invalid or timezone missing")
    try:
        parsed = datetime.fromisoformat(match[1] + match[3].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("public fact capture timestamp invalid") from exc
    return parsed.astimezone(timezone.utc), int((match[2] or "").ljust(9, "0"))


def fact_capture_timestamp_v1(fact: Mapping[str, Any]) -> str:
    # The legacy top-level shape remains readable only with its own explicit
    # capture. A malformed canonical envelope must not fall back to that shape.
    timestamps = fact.get("timestamps")
    if "timestamps" in fact:
        if not isinstance(timestamps, Mapping):
            raise ValueError("public fact capture timestamps invalid")
        captured = timestamps.get("captured_at")
    else:
        captured = fact.get("captured_at")
    capture_order_key_v1(captured)
    return captured


def fact_event_time_ms_v1(fact: Mapping[str, Any]) -> int:
    if "timestamps" in fact:
        timestamps = fact.get("timestamps")
        if not isinstance(timestamps, Mapping):
            raise ValueError("public fact timestamps invalid")
        event = timestamps.get("venue_event_time_ms")
    else:
        event = fact.get("ts")
    if isinstance(event, bool) or not isinstance(event, (int, str)) or not str(event).isdigit():
        raise ValueError("public fact event timestamp invalid")
    parsed = int(event)
    if parsed <= 0:
        raise ValueError("public fact event timestamp nonpositive")
    return parsed


def canonical_fact_source_v1(fact: Mapping[str, Any]) -> dict[str, str]:
    """Keep the existing producer kind/channel; do not relabel books5 as REST ticker."""
    provenance = fact.get("provenance")
    if not isinstance(provenance, Mapping):
        raise ValueError("canonical public fact provenance missing")
    kind, endpoint = fact.get("fact_kind"), provenance.get("endpoint_or_channel")
    if not isinstance(kind, str) or not kind or not isinstance(endpoint, str) or not endpoint:
        raise ValueError("canonical public fact source binding missing")
    return {"source_class": kind, "source_endpoint": endpoint}
