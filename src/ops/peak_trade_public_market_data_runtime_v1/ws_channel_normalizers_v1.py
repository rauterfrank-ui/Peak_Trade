"""Canonical WS channel → MarkPrice / Trade / BestBidAsk fact normalizers (EEA public runtime)."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Optional

from src.ops.peak_trade_public_market_data_runtime_v1.constants_v1 import (
    EEA_REST_HOST,
    PT1M_STEP_MS,
)
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import (
    BestBidAskFactV1,
    DataQualityStateV1,
    InstrumentRefV1,
    MarkPriceFactV1,
    TradeFactV1,
    MarketFactProvenanceV1,
    MarketTimestampV1,
)


class PublicWsNormalizeError(ValueError):
    pass


def _digest(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _instrument_ref(instrument_ref: Mapping[str, Any]) -> InstrumentRefV1:
    return InstrumentRefV1(
        canonical_instrument_id=str(instrument_ref.get("canonical_instrument_id") or ""),
        venue_native_id=str(instrument_ref.get("venue_native_id") or ""),
        venue=str(instrument_ref.get("venue") or "okx_eea"),
        instrument_type=str(instrument_ref.get("instrument_type") or "SWAP"),
        settlement_asset=str(instrument_ref.get("settlement_asset") or "USDT"),
        mapping_provenance_digest=str(instrument_ref.get("mapping_provenance_digest") or ""),
    )


def _quality(*, duplicate: bool = False, out_of_order: bool = False) -> DataQualityStateV1:
    return DataQualityStateV1(
        finalized=True,
        in_progress=False,
        missing=False,
        stale=False,
        corrected=False,
        duplicate=duplicate,
        out_of_order=out_of_order,
        gap_detected=False,
    )


def normalize_ticker_row_to_mark_price_fact_v1(
    row: Mapping[str, Any],
    *,
    instrument_ref: Mapping[str, Any],
    captured_at: str,
    session_id: str,
    channel: str = "tickers",
    duplicate: bool = False,
    out_of_order: bool = False,
) -> MarkPriceFactV1:
    mark_px = str(row.get("markPx") or row.get("last") or "").strip()
    if not mark_px:
        raise PublicWsNormalizeError("TICKER_MARK_PX_MISSING")
    ts_raw = row.get("ts")
    venue_event_ms = int(str(ts_raw)) if ts_raw not in (None, "") else None
    inst = _instrument_ref(instrument_ref)
    prov = MarketFactProvenanceV1(
        transport="ws",
        endpoint_or_channel=channel,
        raw_payload_digest=_digest(dict(row)),
        session_id=session_id,
        eea_endpoint_family=EEA_REST_HOST,
    )
    return MarkPriceFactV1(
        instrument=inst,
        mark_px=mark_px,
        timestamps=MarketTimestampV1(
            venue_event_time_ms=venue_event_ms,
            captured_at=captured_at,
            effective_at=None,
            source_clock_class="venue_event_ms",
        ),
        provenance=prov,
        quality=_quality(duplicate=duplicate, out_of_order=out_of_order),
    )


def normalize_trade_row_to_trade_fact_v1(
    row: Mapping[str, Any],
    *,
    instrument_ref: Mapping[str, Any],
    captured_at: str,
    session_id: str,
    channel: str = "trades",
    duplicate: bool = False,
    out_of_order: bool = False,
) -> TradeFactV1:
    trade_id = str(row.get("tradeId") or row.get("trade_id") or "").strip()
    price = str(row.get("px") or row.get("price") or "").strip()
    size = str(row.get("sz") or row.get("size") or "").strip()
    side = str(row.get("side") or "").strip()
    if not trade_id or not price:
        raise PublicWsNormalizeError("TRADE_ROW_INCOMPLETE")
    ts_raw = row.get("ts")
    venue_event_ms = int(str(ts_raw)) if ts_raw not in (None, "") else None
    inst = _instrument_ref(instrument_ref)
    prov = MarketFactProvenanceV1(
        transport="ws",
        endpoint_or_channel=channel,
        raw_payload_digest=_digest(dict(row)),
        session_id=session_id,
        eea_endpoint_family=EEA_REST_HOST,
    )
    return TradeFactV1(
        instrument=inst,
        trade_id=trade_id,
        price=price,
        size=size or "0",
        side=side or "unknown",
        timestamps=MarketTimestampV1(
            venue_event_time_ms=venue_event_ms,
            captured_at=captured_at,
            effective_at=None,
            source_clock_class="venue_event_ms",
        ),
        provenance=prov,
        quality=_quality(duplicate=duplicate, out_of_order=out_of_order),
    )


def normalize_books5_row_to_best_bid_ask_fact_v1(
    row: Mapping[str, Any],
    *,
    instrument_ref: Mapping[str, Any],
    captured_at: str,
    session_id: str,
    channel: str = "books5",
    duplicate: bool = False,
    out_of_order: bool = False,
) -> BestBidAskFactV1:
    bids = row.get("bids")
    asks = row.get("asks")
    bid_px = ""
    ask_px = ""
    if isinstance(bids, list) and bids and isinstance(bids[0], list):
        bid_px = str(bids[0][0] or "").strip()
    if isinstance(asks, list) and asks and isinstance(asks[0], list):
        ask_px = str(asks[0][0] or "").strip()
    if not bid_px or not ask_px:
        raise PublicWsNormalizeError("BOOKS5_TOP_OF_BOOK_MISSING")
    ts_raw = row.get("ts")
    venue_event_ms = int(str(ts_raw)) if ts_raw not in (None, "") else None
    inst = _instrument_ref(instrument_ref)
    prov = MarketFactProvenanceV1(
        transport="ws",
        endpoint_or_channel=channel,
        raw_payload_digest=_digest(dict(row)),
        session_id=session_id,
        eea_endpoint_family=EEA_REST_HOST,
    )
    return BestBidAskFactV1(
        instrument=inst,
        bid_px=bid_px,
        ask_px=ask_px,
        timestamps=MarketTimestampV1(
            venue_event_time_ms=venue_event_ms,
            captured_at=captured_at,
            effective_at=None,
            source_clock_class="venue_event_ms",
        ),
        provenance=prov,
        quality=_quality(duplicate=duplicate, out_of_order=out_of_order),
    )


def normalize_ws_payload_to_canonical_facts_v1(
    message: Mapping[str, Any],
    *,
    instrument_ref: Mapping[str, Any],
    captured_at: str,
    session_id: str,
    duplicate: bool = False,
    out_of_order: bool = False,
) -> list[Mapping[str, Any]]:
    """Map one OKX public WS push (tickers / trades / books5) to canonical fact dicts."""

    arg = message.get("arg")
    channel: Optional[str] = None
    if isinstance(arg, Mapping):
        channel = str(arg.get("channel") or "").strip() or None
    data = message.get("data")
    if not isinstance(data, list):
        if channel is None and message.get("tradeId"):
            channel = "trades"
            data = [message]
        else:
            return []
    channel = channel or "unknown"
    out: list[Mapping[str, Any]] = []
    for row in data:
        if not isinstance(row, Mapping):
            continue
        if channel == "tickers":
            fact = normalize_ticker_row_to_mark_price_fact_v1(
                row,
                instrument_ref=instrument_ref,
                captured_at=captured_at,
                session_id=session_id,
                duplicate=duplicate,
                out_of_order=out_of_order,
            )
            out.append(fact.to_dict())
        elif channel == "trades":
            fact = normalize_trade_row_to_trade_fact_v1(
                row,
                instrument_ref=instrument_ref,
                captured_at=captured_at,
                session_id=session_id,
                duplicate=duplicate,
                out_of_order=out_of_order,
            )
            out.append(fact.to_dict())
        elif channel == "books5":
            fact = normalize_books5_row_to_best_bid_ask_fact_v1(
                row,
                instrument_ref=instrument_ref,
                captured_at=captured_at,
                session_id=session_id,
                duplicate=duplicate,
                out_of_order=out_of_order,
            )
            out.append(fact.to_dict())
    return out


def pt1m_interval_start_from_mark_ts_ms(ts_ms: int) -> int:
    return (int(ts_ms) // PT1M_STEP_MS) * PT1M_STEP_MS
