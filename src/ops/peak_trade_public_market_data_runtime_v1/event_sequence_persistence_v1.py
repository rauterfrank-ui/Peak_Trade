"""Durable persistence for public WS event sequence state (RW-PUB-G9)."""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.ops.peak_trade_public_market_data_runtime_v1.event_pipeline_v1 import (
    EventSequenceStateV1,
)

SEQUENCE_STATE_FILENAME = "public_ws_event_sequence_state_v1.json"
SCHEMA_VERSION = "public_ws_event_sequence_state.v1"


@dataclass(frozen=True)
class PersistedEventSequenceStateV1:
    schema_version: str
    last_event_ts_ms: Optional[int]
    seen_ids: tuple[str, ...]
    last_event_ts_ms_by_stream: dict[str, int] = field(default_factory=dict)
    last_event_id_by_stream: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        result = {
            "schema_version": self.schema_version,
            "last_event_ts_ms": self.last_event_ts_ms,
            "seen_ids": list(self.seen_ids),
        }
        if self.last_event_ts_ms_by_stream:
            result["schema_version"] = "public_ws_event_sequence_state.v2"
            result["last_event_ts_ms_by_stream"] = self.last_event_ts_ms_by_stream
            result["last_event_id_by_stream"] = self.last_event_id_by_stream
        return result


def persist_event_sequence_state_v1(
    store_root: Path,
    state: EventSequenceStateV1,
) -> Path:
    store_root.mkdir(parents=True, exist_ok=True)
    payload = PersistedEventSequenceStateV1(
        schema_version=SCHEMA_VERSION,
        last_event_ts_ms=state.last_event_ts_ms,
        seen_ids=tuple(sorted(state.seen_ids)),
        last_event_ts_ms_by_stream=dict(state.last_event_ts_ms_by_stream),
        last_event_id_by_stream=dict(state.last_event_id_by_stream),
    )
    path = store_root / SEQUENCE_STATE_FILENAME
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=store_root, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(json.dumps(payload.to_dict(), indent=2, sort_keys=True))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        descriptor = os.open(store_root, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return path


def load_event_sequence_state_v1(store_root: Path) -> EventSequenceStateV1:
    path = store_root / SEQUENCE_STATE_FILENAME
    if not path.is_file():
        return EventSequenceStateV1()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") not in {
        SCHEMA_VERSION,
        "public_ws_event_sequence_state.v2",
    }:
        raise ValueError("PUBLIC_WS_SEQUENCE_STATE_SCHEMA_INVALID")
    seen = raw.get("seen_ids")
    if not isinstance(seen, list) or any(type(item) is not str for item in seen):
        raise ValueError("PUBLIC_WS_SEQUENCE_SEEN_IDS_INVALID")
    last = raw.get("last_event_ts_ms")
    if last is not None and (type(last) is not int or last < 0):
        raise ValueError("PUBLIC_WS_SEQUENCE_EVENT_TIME_INVALID")
    streams = raw.get("last_event_ts_ms_by_stream", {})
    if (
        raw["schema_version"] == "public_ws_event_sequence_state.v2"
        and "last_event_ts_ms_by_stream" not in raw
    ):
        raise ValueError("PUBLIC_WS_SEQUENCE_STREAM_CLOCKS_REQUIRED")
    if not isinstance(streams, dict) or any(
        type(key) is not str or not key or type(value) is not int or value <= 0
        for key, value in streams.items()
    ):
        raise ValueError("PUBLIC_WS_SEQUENCE_STREAM_CLOCKS_INVALID")
    identifiers = raw.get("last_event_id_by_stream", {})

    def valid_identity(key, value):
        if type(value) is not str or not value.startswith(key + ":"):
            return False
        try:
            stream = json.loads(key)
        except (ValueError, TypeError):
            return False
        if (
            type(stream) is not list
            or len(stream) != 2
            or any(type(part) is not str or not part for part in stream)
        ):
            return False
        return re.fullmatch(r"[0-9a-f]{64}", value[len(key) + 1 :]) is not None and (
            stream[0] == "mark-price" or value in seen
        )

    if (
        not isinstance(identifiers, dict)
        or set(identifiers) != set(streams)
        or any(not valid_identity(key, value) for key, value in identifiers.items())
    ):
        raise ValueError("PUBLIC_WS_SEQUENCE_STREAM_IDENTITIES_INVALID")
    return EventSequenceStateV1(
        last_event_ts_ms=int(last) if last is not None else None,
        seen_ids={str(x) for x in seen},
        last_event_ts_ms_by_stream=streams,
        last_event_id_by_stream=identifiers,
    )


def event_sequence_state_snapshot_v1(state: EventSequenceStateV1) -> dict:
    return {
        "last_event_ts_ms": state.last_event_ts_ms,
        "seen_id_count": len(state.seen_ids),
        "seen_ids_sorted": sorted(state.seen_ids),
        "last_event_ts_ms_by_stream": dict(state.last_event_ts_ms_by_stream),
    }
