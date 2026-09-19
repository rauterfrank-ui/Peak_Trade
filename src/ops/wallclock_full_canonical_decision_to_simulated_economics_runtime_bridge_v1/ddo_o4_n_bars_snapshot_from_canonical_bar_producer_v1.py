"""Materialize DDO O4 N_BARS bar-evidence snapshot from CanonicalPublicMdBarProducerV1.

Uses authoritative O4 envelopes only. Explicit snapshot injection wins.
"""

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
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.canonical_bar_producer_v1 import (
    CanonicalPublicMdBarProducerV1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    BAR_STATE_CORRECTED,
    BAR_STATE_FINALIZED,
)

BINDING_ID: Final[str] = (
    "peak_trade.ops.wallclock_bridge.ddo_o4_n_bars_snapshot_from_canonical_bar_producer_v1"
)
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
_FINALIZED_STATES: Final[frozenset[str]] = frozenset({BAR_STATE_FINALIZED, BAR_STATE_CORRECTED})


def _envelope_to_o4_bar_element_v1(envelope: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "canonical_instrument_id": envelope["canonical_instrument_id"],
        "venue_instrument_id": envelope["venue_instrument_id"],
        "venue": envelope["venue"],
        "interval": envelope["interval"],
        "bar_open_time": float(envelope["bar_open_time"]),
        "bar_close_time": float(envelope["bar_close_time"]),
        "finalization_state": str(envelope["finalization_state"]),
        "quality_state": str(envelope["quality_state"]),
        "last_observation_identity": dict(envelope["last_observation_identity"]),
        "session_id": envelope["session_id"],
        "repository_sha": envelope["repository_sha"],
        "config_digest": envelope["config_digest"],
        "close": float(envelope["close"]),
        "revision": int(envelope["revision"]),
    }


def _decision_event_unix_v1(decision_event: Mapping[str, Any]) -> float:
    text = require_event_time_utc(decision_event.get("event_time_utc"), "event_time_utc")
    dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _select_gapless_chain_v1(
    finalized: list[dict[str, Any]], *, n_bars: int, decision_unix: float | None
) -> list[dict[str, Any]]:
    if decision_unix is None:
        return finalized[-n_bars:]
    anchored = [row for row in finalized if float(row["bar_open_time"]) >= float(decision_unix)]
    if len(anchored) >= n_bars:
        return anchored[:n_bars]
    raise DdoValidationError("O4_FINALIZED_BAR_COUNT_INSUFFICIENT_AFTER_DECISION")


def materialize_o4_n_bars_bar_evidence_snapshot_v1(
    *,
    decision_event_ref: str,
    producer: CanonicalPublicMdBarProducerV1,
    n_bars: int,
    decision_event: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a validated O4 snapshot from the producer's finalized bar chain tail."""
    if n_bars <= 0:
        raise DdoValidationError("N_BARS_MUST_BE_POSITIVE")
    finalized = [
        item
        for item in producer.list_envelopes()
        if str(item.get("finalization_state")) in _FINALIZED_STATES
    ]
    finalized.sort(key=lambda row: float(row["bar_open_time"]))
    if len(finalized) < n_bars:
        raise DdoValidationError("O4_FINALIZED_BAR_COUNT_INSUFFICIENT")
    decision_unix = None if decision_event is None else _decision_event_unix_v1(decision_event)
    tail = _select_gapless_chain_v1(finalized, n_bars=n_bars, decision_unix=decision_unix)
    if len(tail) < n_bars:
        raise DdoValidationError("O4_FINALIZED_BAR_COUNT_INSUFFICIENT")
    for index, bar in enumerate(tail):
        open_t = float(bar["bar_open_time"])
        if index > 0:
            prev_close = float(tail[index - 1]["bar_close_time"])
            if open_t != prev_close:
                raise DdoValidationError("O4_BAR_CHAIN_NOT_GAPLESS")
    horizon_start = unix_seconds_to_event_time_utc(float(tail[0]["bar_open_time"]), "horizon_start")
    payload = {
        "schema_name": O4_SNAPSHOT_SCHEMA_NAME,
        "schema_version": O4_SNAPSHOT_SCHEMA_VERSION,
        "decision_event_ref": decision_event_ref,
        "horizon_start_time_utc": horizon_start,
        "n_bars": n_bars,
        "o4_interval_id": producer.interval,
        "o4_bars": [_envelope_to_o4_bar_element_v1(bar) for bar in tail],
    }
    validate_o4_n_bars_bar_evidence_snapshot_v1(payload)
    return payload


def maybe_materialize_ddo_o4_n_bars_snapshot_from_canonical_producer_v1(
    state: Any,
    *,
    decision_event_ref: str | None,
    n_bars: int | None = None,
) -> dict[str, Any] | None:
    """Fill or refresh ``ddo_o4_n_bars_bar_evidence_snapshot`` from session producer."""
    if getattr(state, "ddo_o4_n_bars_bar_evidence_snapshot_locked", False):
        return None
    if not decision_event_ref:
        return None
    producer = getattr(state, "ddo_canonical_public_md_bar_producer", None)
    if not isinstance(producer, CanonicalPublicMdBarProducerV1):
        return None
    count = n_bars if n_bars is not None else int(getattr(state, "ddo_n_bars_horizon_n_bars", 2))
    decision_event = getattr(state, "ddo_n_bars_horizon_decision_event", None)
    try:
        snapshot = materialize_o4_n_bars_bar_evidence_snapshot_v1(
            decision_event_ref=decision_event_ref,
            producer=producer,
            n_bars=count,
            decision_event=decision_event if isinstance(decision_event, Mapping) else None,
        )
    except DdoValidationError as exc:
        return {
            "ok": False,
            "binding_id": BINDING_ID,
            "reason": str(exc),
            "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        }
    state.ddo_o4_n_bars_bar_evidence_snapshot = snapshot
    return {
        "ok": True,
        "binding_id": BINDING_ID,
        "n_bars": count,
        "decision_event_ref": decision_event_ref,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
    }
