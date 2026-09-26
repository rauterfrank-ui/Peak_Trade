"""Shared O4 N_BARS snapshot materialization (chain selection only; no authority)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Final, Mapping, Sequence

from src.learning.deterministic_decision_outcome_v0.common_v0 import require_event_time_utc
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.o4_n_bars_bar_evidence_bridge_contracts_v1 import (
    O4_SNAPSHOT_SCHEMA_NAME,
    O4_SNAPSHOT_SCHEMA_VERSION,
    unix_seconds_to_event_time_utc,
    validate_o4_n_bars_bar_evidence_snapshot_v1,
)
from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import O4_AUTHORITATIVE_INTERVAL
from src.ops.peak_trade_public_market_data_runtime_v1.o4_pt1h_bar_fact_v1 import (
    canonical_bar_envelope_to_o4_bar_element_v1,
)

MATERIALIZATION_ID: Final[str] = (
    "peak_trade.ops.wallclock_bridge.ddo_o4_n_bars_snapshot_materialization_v1"
)


def _decision_event_unix_v1(decision_event: Mapping[str, Any]) -> float:
    text = require_event_time_utc(decision_event.get("event_time_utc"), "event_time_utc")
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def select_gapless_o4_bar_chain_v1(
    finalized_bars: Sequence[Mapping[str, Any]],
    *,
    n_bars: int,
    decision_event: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Select N gapless finalized PT1H bars for DDO horizon (fail-closed)."""
    if n_bars <= 0:
        raise DdoValidationError("N_BARS_MUST_BE_POSITIVE")
    normalized = [canonical_bar_envelope_to_o4_bar_element_v1(bar) for bar in finalized_bars]
    normalized.sort(key=lambda row: float(row["bar_open_time"]))
    if len(normalized) < n_bars:
        raise DdoValidationError("O4_FINALIZED_BAR_COUNT_INSUFFICIENT")
    decision_unix = None if decision_event is None else _decision_event_unix_v1(decision_event)
    if decision_unix is None:
        tail = normalized[-n_bars:]
    else:
        anchored = [
            row for row in normalized if float(row["bar_open_time"]) >= float(decision_unix)
        ]
        if len(anchored) < n_bars:
            raise DdoValidationError("O4_FINALIZED_BAR_COUNT_INSUFFICIENT_AFTER_DECISION")
        tail = anchored[:n_bars]
    if len(tail) < n_bars:
        raise DdoValidationError("O4_FINALIZED_BAR_COUNT_INSUFFICIENT")
    for index, bar in enumerate(tail):
        if index > 0:
            prev_close = float(tail[index - 1]["bar_close_time"])
            if float(bar["bar_open_time"]) != prev_close:
                raise DdoValidationError("O4_BAR_CHAIN_NOT_GAPLESS")
    return tail


def build_o4_n_bars_bar_evidence_snapshot_v1(
    *,
    decision_event_ref: str,
    o4_bars: Sequence[Mapping[str, Any]],
    n_bars: int,
    decision_event: Mapping[str, Any] | None = None,
    o4_interval_id: str = O4_AUTHORITATIVE_INTERVAL,
) -> dict[str, Any]:
    tail = select_gapless_o4_bar_chain_v1(o4_bars, n_bars=n_bars, decision_event=decision_event)
    horizon_start = unix_seconds_to_event_time_utc(float(tail[0]["bar_open_time"]), "horizon_start")
    payload = {
        "schema_name": O4_SNAPSHOT_SCHEMA_NAME,
        "schema_version": O4_SNAPSHOT_SCHEMA_VERSION,
        "decision_event_ref": decision_event_ref,
        "horizon_start_time_utc": horizon_start,
        "n_bars": n_bars,
        "o4_interval_id": o4_interval_id,
        "o4_bars": tail,
    }
    validate_o4_n_bars_bar_evidence_snapshot_v1(payload)
    return payload
