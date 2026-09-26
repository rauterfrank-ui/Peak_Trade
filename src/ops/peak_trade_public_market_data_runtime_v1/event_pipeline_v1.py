"""Duplicate, out-of-order, and gap detection for public events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional


@dataclass
class EventSequenceStateV1:
    last_event_ts_ms: Optional[int] = None
    seen_ids: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class NormalizedEventEnvelopeV1:
    event_id: str
    event_ts_ms: int
    duplicate: bool
    out_of_order: bool
    payload: dict


def process_public_events_v1(
    *,
    events: Iterable[dict],
    state: EventSequenceStateV1,
) -> tuple[list[NormalizedEventEnvelopeV1], EventSequenceStateV1, list[int]]:
    """Return envelopes, updated state, and detected gap start timestamps (missing steps)."""
    envelopes: list[NormalizedEventEnvelopeV1] = []
    gap_starts: list[int] = []
    for raw in events:
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
