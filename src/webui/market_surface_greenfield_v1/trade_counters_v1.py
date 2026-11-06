"""Execution-watch trade counter classification (watch-only, PROVEN_CURRENT rules)."""

from __future__ import annotations

from typing import Any, Mapping

_EXECUTION_EVENT_V0_TYPES = frozenset(
    {"created", "validated", "submitted", "acked", "filled", "canceled", "failed"}
)
_LEGACY_REJECT_EVENT_TYPES = frozenset({"order_reject"})
_EFFECT_CLASS_TRADES_SET = frozenset(
    {"SIMULATED_EFFECT", "TESTNET_VENUE_EFFECT", "REAL_VENUE_EFFECT"}
)


def _payload_dict(raw: Mapping[str, Any]) -> dict[str, Any]:
    inner = raw.get("payload")
    return inner if isinstance(inner, dict) else {}


def _effect_class(raw: Mapping[str, Any]) -> str | None:
    pl = _payload_dict(raw)
    for key in ("semantic_class", "effect_class", "effect_type"):
        val = pl.get(key) or raw.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip().upper()
    return None


def _rejection_class(raw: Mapping[str, Any]) -> str | None:
    pl = _payload_dict(raw)
    for key in ("rejection_class", "reject_class", "reason_code", "error_code"):
        val = pl.get(key) or raw.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip().upper()
    return None


def classify_execution_event(raw: Mapping[str, Any]) -> dict[str, Any]:
    event_type = str(raw.get("event_type") or "").strip().lower()
    effect = _effect_class(raw)
    rejection = _rejection_class(raw)

    trades_set = False
    trades_rejected = False

    if event_type == "filled":
        if effect is None or effect in _EFFECT_CLASS_TRADES_SET:
            trades_set = True
    elif event_type == "failed":
        trades_rejected = True
    elif event_type in _LEGACY_REJECT_EVENT_TYPES:
        trades_rejected = True

    return {
        "event_type": event_type or None,
        "effect_class": effect,
        "rejection_class": rejection,
        "counts_as_trades_set": trades_set,
        "counts_as_trades_rejected": trades_rejected,
    }


def aggregate_trade_counters(events: list[Mapping[str, Any]]) -> dict[str, Any]:
    trades_set_total = 0
    trades_rejected_total = 0
    by_rejection: dict[str, int] = {}

    for raw in events:
        cls = classify_execution_event(raw)
        if cls["counts_as_trades_set"]:
            trades_set_total += 1
        if cls["counts_as_trades_rejected"]:
            trades_rejected_total += 1
            rej = cls.get("rejection_class")
            if rej:
                by_rejection[rej] = by_rejection.get(rej, 0) + 1

    return {
        "trades_set": trades_set_total,
        "trades_rejected": trades_rejected_total,
        "rejection_classes": by_rejection,
        "events_scanned": len(events),
    }
