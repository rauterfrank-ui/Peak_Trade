"""Observation-only transport of the market input and its exact DP producer result."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.learning.deterministic_decision_outcome_v0.double_play_observation_projection_v1 import (
    producer_canonical_payload_from_decision_v1,
)


def canonical_payload_json_v1(payload: Any) -> str:
    return json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True)
class PendingDecisionContextV1:
    cycle_id: str
    instrument_id: str
    native_id: str
    decision_timestamp_unix: float
    reference_price: float
    market_context_ref: str
    producer_payload_json: str


def pending_decision_context_from_invocation_v1(invocation: Any) -> PendingDecisionContextV1 | None:
    """Copy consumed replay objects; never reconstruct prices from forensic traces."""
    if invocation is None:
        return None
    cycle = invocation.cycle_result
    replay = cycle.replay
    if replay is None or not replay.replay_pass or replay.intermediate is None:
        return None
    intermediate = replay.intermediate
    market = intermediate.market_context
    decision = intermediate.entry_exit_decision
    cursor = cycle.outgoing_cursor
    if cursor is None:
        return None
    producer = producer_canonical_payload_from_decision_v1(decision)
    instrument = str(invocation.bound_instrument.instrument_id or "")
    native = str(invocation.bound_instrument.venue_native_id or "")
    if not instrument or not native or market.instrument_id != instrument:
        return None
    if producer["instrument_id"] != instrument or producer["trading_epoch"] != market.trading_epoch:
        return None
    try:
        timestamp = datetime.fromisoformat(market.decision_time.replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            return None
        ts = timestamp.timestamp()
        price = market.mark_price
        if any(
            isinstance(v, bool) or not math.isfinite(float(v)) or float(v) <= 0 for v in (ts, price)
        ):
            return None
    except (ValueError, TypeError, OverflowError):
        return None
    return PendingDecisionContextV1(
        cycle_id=f"{cycle.cycle_id}:cycle:{cursor.now_tick}",
        instrument_id=instrument,
        native_id=native,
        decision_timestamp_unix=ts,
        reference_price=float(price),
        market_context_ref=market.context_id,
        producer_payload_json=canonical_payload_json_v1(producer),
    )
