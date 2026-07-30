"""Ticker endpoint semantics: last/bid/ask only — never markPx."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional

from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.constants_v1 import (
    TICKER_ENDPOINT,
    TICKER_FIELD_ASK,
    TICKER_FIELD_BID,
    TICKER_FIELD_LAST,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.error_classes_v1 import (
    MarketDataBindingErrorV1,
)


@dataclass(frozen=True)
class PublicTickerSemanticsV1:
    venue_instrument_id: str
    last: Optional[float]
    bid_px: Optional[float]
    ask_px: Optional[float]
    endpoint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _optional_positive(row: Mapping[str, Any], field: str) -> Optional[float]:
    raw = row.get(field)
    if raw is None or raw == "":
        return None
    value = float(raw)
    if value != value or value <= 0:  # noqa: PLR0124 — NaN check
        raise MarketDataBindingErrorV1("INVALID_PRICE_VALUE", f"{field}={value}")
    return value


def parse_public_ticker_semantics_v1(
    payload: Mapping[str, Any],
    *,
    expected_venue_instrument_id: str,
) -> PublicTickerSemanticsV1:
    """Parse declared ticker fields. Does not require or read markPx."""
    if str(payload.get("code", "0")) not in {"0", ""}:
        raise MarketDataBindingErrorV1(
            "TRANSPORT_FAILURE",
            f"PROVIDER_CODE_{payload.get('code')}",
        )
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise MarketDataBindingErrorV1(
            "TRANSPORT_FAILURE",
            "TICKER_DATA_MISSING",
        )
    row = data[0]
    if not isinstance(row, Mapping):
        raise MarketDataBindingErrorV1("TRANSPORT_FAILURE", "TICKER_ROW_INVALID")
    returned_inst = str(row.get("instId") or "").strip()
    if returned_inst != str(expected_venue_instrument_id).strip():
        raise MarketDataBindingErrorV1(
            "VENUE_INSTRUMENT_RESPONSE_MISMATCH",
            f"ticker_instId={returned_inst}",
        )
    # Explicit non-use of markPx from ticker.
    if "markPx" in row:
        # Presence is ignored for mark semantics; never treated as mark source.
        pass
    return PublicTickerSemanticsV1(
        venue_instrument_id=returned_inst,
        last=_optional_positive(row, TICKER_FIELD_LAST),
        bid_px=_optional_positive(row, TICKER_FIELD_BID),
        ask_px=_optional_positive(row, TICKER_FIELD_ASK),
        endpoint=TICKER_ENDPOINT,
    )
