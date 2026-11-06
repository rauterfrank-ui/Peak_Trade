"""Explicit OKX public mark-price contract (markPx from /api/v5/public/mark-price)."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional

from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.constants_v1 import (
    DEFAULT_MAX_MARK_PRICE_STALE_SECONDS,
    MARK_PRICE_ENDPOINT,
    MARK_PRICE_FIELD,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.error_classes_v1 import (
    MarketDataBindingErrorV1,
)


@dataclass(frozen=True)
class PublicMarkPriceV1:
    venue_instrument_id: str
    mark_px: float
    event_ts_unix: float
    receive_ts_unix: float
    endpoint: str
    field: str
    provider_ts_ms: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parse_provider_ts_ms(raw: Any) -> int:
    if raw is None or raw == "":
        raise MarketDataBindingErrorV1("MARKET_DATA_TIMESTAMP_MISSING", "ts")
    try:
        ts_ms = int(float(raw))
    except (TypeError, ValueError) as exc:
        raise MarketDataBindingErrorV1(
            "MARKET_DATA_TIMESTAMP_MISSING", f"ts_unparseable:{raw}"
        ) from exc
    if ts_ms <= 0:
        raise MarketDataBindingErrorV1("MARKET_DATA_TIMESTAMP_MISSING", f"ts={ts_ms}")
    return ts_ms


def parse_public_mark_price_response_v1(
    payload: Mapping[str, Any],
    *,
    expected_venue_instrument_id: str,
    receive_ts_unix: float,
    max_stale_seconds: float = DEFAULT_MAX_MARK_PRICE_STALE_SECONDS,
    wall_now_unix: Optional[float] = None,
) -> PublicMarkPriceV1:
    """Validate mark-price payload; no last/bid/ask/index/mid/zero substitution."""
    if str(payload.get("code", "0")) not in {"0", ""}:
        raise MarketDataBindingErrorV1(
            "TRANSPORT_FAILURE",
            f"PROVIDER_CODE_{payload.get('code')}",
        )
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise MarketDataBindingErrorV1("PUBLIC_MARK_PRICE_RESPONSE_EMPTY", "data")
    row = data[0]
    if not isinstance(row, Mapping):
        raise MarketDataBindingErrorV1("PUBLIC_MARK_PRICE_RESPONSE_EMPTY", "row")

    returned_inst = str(row.get("instId") or "").strip()
    if returned_inst != str(expected_venue_instrument_id).strip():
        raise MarketDataBindingErrorV1(
            "VENUE_INSTRUMENT_RESPONSE_MISMATCH",
            f"instId={returned_inst}",
        )

    raw_mark = row.get(MARK_PRICE_FIELD)
    if raw_mark is None or raw_mark == "":
        raise MarketDataBindingErrorV1(
            "REQUIRED_PRICE_FIELD_MISSING",
            MARK_PRICE_FIELD,
        )
    try:
        mark_px = float(raw_mark)
    except (TypeError, ValueError) as exc:
        raise MarketDataBindingErrorV1(
            "INVALID_PRICE_VALUE", f"{MARK_PRICE_FIELD}:{raw_mark}"
        ) from exc
    if not math.isfinite(mark_px) or mark_px <= 0:
        raise MarketDataBindingErrorV1("INVALID_PRICE_VALUE", f"{MARK_PRICE_FIELD}={mark_px}")

    ts_ms = _parse_provider_ts_ms(row.get("ts"))
    event_ts_unix = ts_ms / 1000.0
    now = float(receive_ts_unix if wall_now_unix is None else wall_now_unix)
    age = now - event_ts_unix
    if age > float(max_stale_seconds):
        raise MarketDataBindingErrorV1(
            "MARKET_DATA_STALE",
            f"age={age:.3f}>max={max_stale_seconds}",
        )

    return PublicMarkPriceV1(
        venue_instrument_id=returned_inst,
        mark_px=mark_px,
        event_ts_unix=event_ts_unix,
        receive_ts_unix=float(receive_ts_unix),
        endpoint=MARK_PRICE_ENDPOINT,
        field=MARK_PRICE_FIELD,
        provider_ts_ms=ts_ms,
    )
