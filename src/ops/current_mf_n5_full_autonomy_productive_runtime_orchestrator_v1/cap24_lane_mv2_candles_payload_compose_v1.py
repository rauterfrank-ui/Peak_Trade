"""Derive per-lane MV2-aligned C1 candle payloads from Cap24 bind + cycle timing.

Composition-only. Does not alter C1 authority or Full-Core ingest semantics.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


class Cap24LaneMv2CandlesPayloadComposeError(ValueError):
    """Fail-closed Cap24 lane C1 payload compose violation."""


def _parse_positive_mark_v1(raw: Any, *, venue_native_id: str) -> float:
    text = str(raw or "").strip()
    if not text:
        raise Cap24LaneMv2CandlesPayloadComposeError(f"CAP24_MARK_PRICE_MISSING:{venue_native_id}")
    try:
        value = float(Decimal(text))
    except (InvalidOperation, ValueError) as exc:
        raise Cap24LaneMv2CandlesPayloadComposeError(
            f"CAP24_MARK_PRICE_MALFORMED:{venue_native_id}"
        ) from exc
    if value <= 0:
        raise Cap24LaneMv2CandlesPayloadComposeError(
            f"CAP24_MARK_PRICE_NONPOSITIVE:{venue_native_id}"
        )
    return value


def build_mv2_aligned_candles_payload_v1(
    *,
    venue_native_id: str,
    last_ts_ms: int,
    mark_px: float,
) -> dict[str, object]:
    """C1 payload whose last close matches mark_px; prior bars differ for P5 init."""

    rows: list[list[str]] = []
    base = float(mark_px)
    for index in range(8):
        ts = str(last_ts_ms - (7 - index) * 60_000)
        close = base - (7 - index) * 0.5
        px = f"{close:.4f}"
        rows.append([ts, px, px, px, px, "10", "100", "USDT", "1"])
    return {"code": "0", "instId": str(venue_native_id), "data": rows}


def build_n5_lane_candles_payload_from_cap24_v1(
    selected_pairs: Mapping[str, tuple[Any, BoundInstrumentV1]],
    mark_price_by_native_id: Mapping[str, Any],
    *,
    last_finalized_event_ts_unix: float,
) -> dict[str, dict[str, object]]:
    """One MV2-aligned candles payload per occupied lane, keyed by lane_id."""

    if float(last_finalized_event_ts_unix) <= 0:
        raise Cap24LaneMv2CandlesPayloadComposeError("LAST_FINALIZED_EVENT_TS_INVALID")
    last_ts_ms = int(float(last_finalized_event_ts_unix) * 1000)
    marks = dict(mark_price_by_native_id or {})
    out: dict[str, dict[str, object]] = {}
    for lane_id, pair in selected_pairs.items():
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise Cap24LaneMv2CandlesPayloadComposeError(f"LANE_PAIR_MALFORMED:{lane_id}")
        _slot, bound = pair
        if not isinstance(bound, BoundInstrumentV1):
            raise Cap24LaneMv2CandlesPayloadComposeError(f"BOUND_TYPE:{lane_id}")
        native = str(bound.venue_native_id or "").strip()
        if not native:
            raise Cap24LaneMv2CandlesPayloadComposeError(f"VENUE_NATIVE_ID_MISSING:{lane_id}")
        if native not in marks:
            raise Cap24LaneMv2CandlesPayloadComposeError(
                f"CAP24_MARK_PRICE_SIDECAR_MISSING:{native}"
            )
        mark_px = _parse_positive_mark_v1(marks[native], venue_native_id=native)
        out[str(lane_id)] = build_mv2_aligned_candles_payload_v1(
            venue_native_id=native,
            last_ts_ms=last_ts_ms,
            mark_px=mark_px,
        )
    if not out:
        raise Cap24LaneMv2CandlesPayloadComposeError("NO_OCCUPIED_LANES")
    return out


__all__ = [
    "Cap24LaneMv2CandlesPayloadComposeError",
    "build_mv2_aligned_candles_payload_v1",
    "build_n5_lane_candles_payload_from_cap24_v1",
]
