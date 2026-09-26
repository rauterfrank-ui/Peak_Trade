"""Duplicate, out-of-order, and gap handling for private WS events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from src.ops.okx_eea_private_account_state_runtime_v1.quality_v1 import transition_on_ambiguity_v1


@dataclass
class PrivateEventSequenceStateV1:
    last_event_ts_ms: Optional[int] = None
    seen_ids: set[str] = field(default_factory=set)
    fill_trade_ids: set[str] = field(default_factory=set)
    order_ids: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class PrivateNormalizedEventV1:
    event_id: str
    event_ts_ms: int
    channel: str
    duplicate: bool
    out_of_order: bool
    gap_detected: bool
    quality_after: str
    payload: dict


def process_private_ws_events_v1(
    *,
    events: Iterable[dict],
    state: PrivateEventSequenceStateV1,
) -> tuple[list[PrivateNormalizedEventV1], PrivateEventSequenceStateV1, bool]:
    envelopes: list[PrivateNormalizedEventV1] = []
    reconciliation_required = False
    for raw in events:
        channel = str(raw.get("channel") or raw.get("arg", {}).get("channel") or "")
        event_id = str(
            raw.get("event_id")
            or raw.get("ordId")
            or raw.get("tradeId")
            or raw.get("uTime")
            or raw.get("ts")
            or ""
        )
        ts_raw = raw.get("uTime") or raw.get("ts")
        if ts_raw is None:
            reconciliation_required = True
            continue
        ts_ms = int(str(ts_raw))
        duplicate = event_id in state.seen_ids or raw.get("_duplicate") is True
        out_of_order = state.last_event_ts_ms is not None and ts_ms < state.last_event_ts_ms
        gap_detected = (
            state.last_event_ts_ms is not None and ts_ms > state.last_event_ts_ms + 120_000
        )
        quality_after = "CURRENT"
        if duplicate or out_of_order or gap_detected:
            quality_after = transition_on_ambiguity_v1("CURRENT")
            reconciliation_required = True
        if channel == "fills" or raw.get("tradeId"):
            tid = str(raw.get("tradeId") or "")
            if tid and tid in state.fill_trade_ids:
                duplicate = True
                reconciliation_required = True
            if tid:
                state.fill_trade_ids.add(tid)
        if not duplicate and not out_of_order:
            state.seen_ids.add(event_id)
            state.last_event_ts_ms = ts_ms
        envelopes.append(
            PrivateNormalizedEventV1(
                event_id=event_id,
                event_ts_ms=ts_ms,
                channel=channel,
                duplicate=duplicate,
                out_of_order=out_of_order,
                gap_detected=gap_detected,
                quality_after=quality_after,
                payload=dict(raw),
            )
        )
    return envelopes, state, reconciliation_required
