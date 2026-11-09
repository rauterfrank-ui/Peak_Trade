"""Duplicate, out-of-order, and gap detection for public events."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from collections.abc import Mapping
from typing import Iterable, Optional


@dataclass
class EventSequenceStateV1:
    last_event_ts_ms: Optional[int] = None
    seen_ids: set[str] = field(default_factory=set)
    last_event_ts_ms_by_stream: dict[str, int] = field(default_factory=dict)
    last_event_id_by_stream: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedEventEnvelopeV1:
    event_id: str
    event_ts_ms: int
    duplicate: bool
    out_of_order: bool
    payload: dict
    corrected: bool = False


def process_public_events_v1(
    *,
    events: Iterable[dict],
    state: EventSequenceStateV1,
) -> tuple[list[NormalizedEventEnvelopeV1], EventSequenceStateV1, list[int]]:
    """Return envelopes, updated state, and detected gap start timestamps (missing steps)."""
    envelopes: list[NormalizedEventEnvelopeV1] = []
    gap_starts: list[int] = []
    for raw in events:
        # OKX timestamps live inside data rows. Channel/instrument clocks are
        # independent; a newer trade must not make a valid mark out-of-order.
        if isinstance(raw.get("arg"), Mapping) and isinstance(raw.get("data"), list):
            arg = raw["arg"]
            channel = str(arg.get("channel") or "")
            for row in raw["data"]:
                if not isinstance(row, Mapping):
                    raise ValueError("PUBLIC_WS_DATA_ROW_INVALID")
                ts = row.get("ts")
                if isinstance(ts, bool) or not str(ts).isdigit() or int(ts) <= 0:
                    raise ValueError("PUBLIC_WS_DATA_ROW_EVENT_TIME_INVALID")
                native = str(row.get("instId") or arg.get("instId") or "")
                if not channel or not native:
                    raise ValueError("PUBLIC_WS_STREAM_IDENTITY_REQUIRED")
                if arg.get("instId") not in (None, native):
                    raise ValueError("PUBLIC_WS_STREAM_INSTRUMENT_MISMATCH")
                stream = json.dumps([channel, native], separators=(",", ":"))
                material = json.dumps(dict(row), sort_keys=True, separators=(",", ":"))
                event_id = stream + ":" + hashlib.sha256(material.encode()).hexdigest()
                ts_ms = int(ts)
                previous = state.last_event_ts_ms_by_stream.get(stream)
                duplicate = (
                    previous == ts_ms and state.last_event_id_by_stream.get(stream) == event_id
                    if channel == "mark-price"
                    else event_id in state.seen_ids or raw.get("_duplicate") is True
                )
                out_of_order = previous is not None and ts_ms < previous
                # Marks are snapshots: only the latest value per stream is
                # needed, including same-ts corrections A -> B -> A. Keeping
                # every historical mark ID would grow every persisted cursor.
                if not duplicate and channel != "mark-price":
                    state.seen_ids.add(event_id)
                if not duplicate and not out_of_order:
                    state.last_event_ts_ms_by_stream[stream] = ts_ms
                    state.last_event_id_by_stream[stream] = event_id
                # Same timestamp with changed data is retained as a correction,
                # as specified by the mark-price source, not a second timestamp.
                envelopes.append(
                    NormalizedEventEnvelopeV1(
                        event_id=event_id,
                        event_ts_ms=ts_ms,
                        duplicate=duplicate,
                        out_of_order=out_of_order,
                        payload={**raw, "data": [dict(row)]},
                        corrected=channel == "mark-price" and previous == ts_ms and not duplicate,
                    )
                )
            continue
        event_id = str(raw.get("msg_id") or raw.get("tradeId") or raw.get("ts") or "")
        ts_raw = raw.get("ts") or raw.get("interval_start_ms")
        if ts_raw is None:
            continue
        ts_ms = int(str(ts_raw))
        duplicate = event_id in state.seen_ids or raw.get("_duplicate") is True
        out_of_order = state.last_event_ts_ms is not None and ts_ms < state.last_event_ts_ms
        if not duplicate:
            state.seen_ids.add(event_id)
        if state.last_event_ts_ms is not None and ts_ms > state.last_event_ts_ms + 60_000:
            # PT1M gap marker for REST recovery (single step simplified)
            gap_starts.append(state.last_event_ts_ms + 60_000)
        if not duplicate and not out_of_order:
            state.last_event_ts_ms = ts_ms
        envelopes.append(
            NormalizedEventEnvelopeV1(
                event_id=event_id,
                event_ts_ms=ts_ms,
                duplicate=duplicate,
                out_of_order=out_of_order,
                payload=dict(raw),
            )
        )
    return envelopes, state, gap_starts
