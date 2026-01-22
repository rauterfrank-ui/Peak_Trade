from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, Iterable, Mapping, Optional


class BetaEventSchemaError(ValueError):
    pass


def _assert_no_floats(x: Any, *, path: str = "$") -> None:
    if isinstance(x, float):
        raise BetaEventSchemaError(f"float forbidden in deterministic artifacts at {path}")
    if isinstance(x, Mapping):
        for k, v in x.items():
            _assert_no_floats(v, path=f"{path}.{k}")
        return
    if isinstance(x, (list, tuple)):
        for i, v in enumerate(x):
            _assert_no_floats(v, path=f"{path}[{i}]")


def _as_str_or_none(v: Any) -> Optional[str]:
    if v is None:
        return None
    return str(v)


def normalize_beta_exec_v1_event(e: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Normalize a (possibly raw) BETA_EXEC_V1 event into a canonical dict.

    Determinism rules:
    - Drop wall-clock `ts_utc` if present.
    - Reject floats anywhere.
    - Ensure required keys exist with correct basic types.
    """
    d: Dict[str, Any] = dict(e)

    # Explicitly drop non-deterministic field from Slice 1 emitter.
    d.pop("ts_utc", None)

    _assert_no_floats(d)

    schema = d.get("schema_version")
    if schema != "BETA_EXEC_V1":
        raise BetaEventSchemaError(f"Unsupported schema_version: {schema!r}")

    event_id = _as_str_or_none(d.get("event_id"))
    if not event_id:
        raise BetaEventSchemaError("Missing event_id")
    d["event_id"] = event_id

    # Basic fields used for deterministic sorting/replay.
    for key in ("run_id", "session_id", "intent_id", "symbol", "event_type"):
        val = _as_str_or_none(d.get(key))
        if val is None:
            raise BetaEventSchemaError(f"Missing required field: {key}")
        d[key] = val

    ts_sim = d.get("ts_sim")
    if ts_sim is None:
        raise BetaEventSchemaError("Missing ts_sim")
    try:
        d["ts_sim"] = int(ts_sim)
    except Exception as ex:  # noqa: BLE001
        raise BetaEventSchemaError(f"Invalid ts_sim: {ts_sim!r}") from ex
    if d["ts_sim"] < 0:
        raise BetaEventSchemaError(f"Invalid ts_sim (must be >= 0): {d['ts_sim']}")

    # Optional identifiers.
    d["request_id"] = _as_str_or_none(d.get("request_id"))
    d["client_order_id"] = _as_str_or_none(d.get("client_order_id"))
    d["reason_code"] = _as_str_or_none(d.get("reason_code"))
    d["reason_detail"] = _as_str_or_none(d.get("reason_detail"))

    payload = d.get("payload", {})
    if payload is None:
        payload = {}
    if not isinstance(payload, Mapping):
        raise BetaEventSchemaError("payload must be a mapping")
    payload_d = dict(payload)
    _assert_no_floats(payload_d, path="$.payload")

    # For FILL events, enforce economic fields exist.
    if d["event_type"] == "FILL":
        # LedgerEngine requires 'side' for deterministic accounting.
        side = payload_d.get("side")
        if side is None:
            raise BetaEventSchemaError("FILL payload missing side")
        payload_d["side"] = str(side)

        # These are serialized as strings to avoid binary float persistence.
        for num_key in ("quantity", "price", "fee"):
            if num_key in payload_d and payload_d[num_key] is not None:
                if isinstance(payload_d[num_key], Decimal):
                    payload_d[num_key] = str(payload_d[num_key])
                else:
                    payload_d[num_key] = str(payload_d[num_key])
            elif num_key in ("quantity", "price"):
                raise BetaEventSchemaError(f"FILL payload missing {num_key}")

        fee_ccy = payload_d.get("fee_currency")
        if fee_ccy is not None:
            payload_d["fee_currency"] = str(fee_ccy)

        fill_id = payload_d.get("fill_id")
        if fill_id is not None:
            payload_d["fill_id"] = str(fill_id)

    d["payload"] = payload_d

    # Keep only JSON-safe types; schema intentionally preserves string numerics.
    return d


def dedupe_by_event_id(events: Iterable[Mapping[str, Any]]) -> list[Dict[str, Any]]:
    """
    Deduplicate deterministically.

    Rule:
    - identical duplicates by event_id are removed (first wins after sorting)
    - conflicting duplicates by event_id raise
    """
    seen: Dict[str, Dict[str, Any]] = {}
    out: list[Dict[str, Any]] = []
    for e in events:
        ev = normalize_beta_exec_v1_event(e)
        event_id = ev["event_id"]
        if event_id in seen:
            if seen[event_id] == ev:
                continue
            raise BetaEventSchemaError(f"Conflicting duplicate event_id: {event_id}")
        seen[event_id] = ev
        out.append(ev)
    return out


def sort_key_beta_exec_v1(ev: Mapping[str, Any]) -> tuple:
    """
    Stable ordering key with explicit tie-breakers.
    """
    return (
        str(ev.get("run_id") or ""),
        str(ev.get("session_id") or ""),
        int(ev.get("ts_sim", -1)),
        str(ev.get("event_type") or ""),
        str(ev.get("event_id") or ""),
    )
