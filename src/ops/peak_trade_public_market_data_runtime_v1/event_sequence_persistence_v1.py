"""Durable persistence for public WS event sequence state (RW-PUB-G9)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
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

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "last_event_ts_ms": self.last_event_ts_ms,
            "seen_ids": list(self.seen_ids),
        }


def persist_event_sequence_state_v1(
    store_root: Path,
    state: EventSequenceStateV1,
) -> Path:
    store_root.mkdir(parents=True, exist_ok=True)
    payload = PersistedEventSequenceStateV1(
        schema_version=SCHEMA_VERSION,
        last_event_ts_ms=state.last_event_ts_ms,
        seen_ids=tuple(sorted(state.seen_ids)),
    )
    path = store_root / SEQUENCE_STATE_FILENAME
    path.write_text(json.dumps(payload.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path


def load_event_sequence_state_v1(store_root: Path) -> EventSequenceStateV1:
    path = store_root / SEQUENCE_STATE_FILENAME
    if not path.is_file():
        return EventSequenceStateV1()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return EventSequenceStateV1()
    seen = raw.get("seen_ids")
    if not isinstance(seen, list):
        seen = []
    last = raw.get("last_event_ts_ms")
    return EventSequenceStateV1(
        last_event_ts_ms=int(last) if last is not None else None,
        seen_ids={str(x) for x in seen},
    )


def event_sequence_state_snapshot_v1(state: EventSequenceStateV1) -> dict:
    return {
        "last_event_ts_ms": state.last_event_ts_ms,
        "seen_id_count": len(state.seen_ids),
        "seen_ids_sorted": sorted(state.seen_ids),
    }
