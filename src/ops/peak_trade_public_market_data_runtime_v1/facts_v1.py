"""Canonical public market fact contracts (V1)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Optional


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def fact_digest(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class InstrumentRefV1:
    canonical_instrument_id: str
    venue_native_id: str
    venue: str
    instrument_type: str
    settlement_asset: str
    mapping_provenance_digest: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MarketTimestampV1:
    venue_event_time_ms: Optional[int]
    captured_at: str
    effective_at: Optional[str]
    source_clock_class: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MarketFactProvenanceV1:
    transport: str
    endpoint_or_channel: str
    raw_payload_digest: str
    session_id: str
    eea_endpoint_family: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DataQualityStateV1:
    finalized: bool
    in_progress: bool
    missing: bool
    stale: bool
    corrected: bool
    duplicate: bool
    out_of_order: bool
    gap_detected: bool
    stale_reason: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MarkPriceFactV1:
    instrument: InstrumentRefV1
    mark_px: str
    timestamps: MarketTimestampV1
    provenance: MarketFactProvenanceV1
    quality: DataQualityStateV1
    fact_kind: str = "MarkPriceFactV1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_kind": self.fact_kind,
            "instrument": self.instrument.to_dict(),
            "mark_px": self.mark_px,
            "timestamps": self.timestamps.to_dict(),
            "provenance": self.provenance.to_dict(),
            "quality": self.quality.to_dict(),
        }


@dataclass(frozen=True)
class TradeFactV1:
    instrument: InstrumentRefV1
    trade_id: str
    price: str
    size: str
    side: str
    timestamps: MarketTimestampV1
    provenance: MarketFactProvenanceV1
    quality: DataQualityStateV1
    immutable_after_ingestion: bool = True
    fact_kind: str = "TradeFactV1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_kind": self.fact_kind,
            "instrument": self.instrument.to_dict(),
            "trade_id": self.trade_id,
            "price": self.price,
            "size": self.size,
            "side": self.side,
            "timestamps": self.timestamps.to_dict(),
            "provenance": self.provenance.to_dict(),
            "quality": self.quality.to_dict(),
            "immutable_after_ingestion": self.immutable_after_ingestion,
        }


@dataclass(frozen=True)
class LastTradePriceFactV1:
    instrument: InstrumentRefV1
    last_px: str
    derived_from_trade_id: str
    timestamps: MarketTimestampV1
    provenance: MarketFactProvenanceV1
    quality: DataQualityStateV1
    consumer_freshness_policy: str = "CONSUMER_SPECIFIC"
    fact_kind: str = "LastTradePriceFactV1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_kind": self.fact_kind,
            "instrument": self.instrument.to_dict(),
            "last_px": self.last_px,
            "derived_from_trade_id": self.derived_from_trade_id,
            "timestamps": self.timestamps.to_dict(),
            "provenance": self.provenance.to_dict(),
            "quality": self.quality.to_dict(),
            "consumer_freshness_policy": self.consumer_freshness_policy,
        }


@dataclass(frozen=True)
class BestBidAskFactV1:
    instrument: InstrumentRefV1
    bid_px: str
    ask_px: str
    timestamps: MarketTimestampV1
    provenance: MarketFactProvenanceV1
    quality: DataQualityStateV1
    fact_kind: str = "BestBidAskFactV1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_kind": self.fact_kind,
            "instrument": self.instrument.to_dict(),
            "bid_px": self.bid_px,
            "ask_px": self.ask_px,
            "timestamps": self.timestamps.to_dict(),
            "provenance": self.provenance.to_dict(),
            "quality": self.quality.to_dict(),
        }


@dataclass(frozen=True)
class FinalizedPt1mMarkFactV1:
    instrument: InstrumentRefV1
    mark_px: str
    interval_start_ms: int
    confirm: str
    timestamps: MarketTimestampV1
    provenance: MarketFactProvenanceV1
    quality: DataQualityStateV1
    source_price_kind: str = "mark_price_candle"
    fact_kind: str = "FinalizedPt1mMarkFactV1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_kind": self.fact_kind,
            "instrument": self.instrument.to_dict(),
            "mark_px": self.mark_px,
            "interval_start_ms": self.interval_start_ms,
            "confirm": self.confirm,
            "source_price_kind": self.source_price_kind,
            "timestamps": self.timestamps.to_dict(),
            "provenance": self.provenance.to_dict(),
            "quality": self.quality.to_dict(),
        }


@dataclass(frozen=True)
class OhlcvIntervalFactV1:
    instrument: InstrumentRefV1
    interval_id: str
    open_px: str
    high_px: str
    low_px: str
    close_px: str
    volume: str
    volume_unit_semantics: str
    source_price_kind: str
    interval_start_ms: int
    confirm: str
    timestamps: MarketTimestampV1
    provenance: MarketFactProvenanceV1
    quality: DataQualityStateV1
    fact_kind: str = "OhlcvIntervalFactV1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_kind": self.fact_kind,
            "instrument": self.instrument.to_dict(),
            "interval_id": self.interval_id,
            "open_px": self.open_px,
            "high_px": self.high_px,
            "low_px": self.low_px,
            "close_px": self.close_px,
            "volume": self.volume,
            "volume_unit_semantics": self.volume_unit_semantics,
            "source_price_kind": self.source_price_kind,
            "interval_start_ms": self.interval_start_ms,
            "confirm": self.confirm,
            "timestamps": self.timestamps.to_dict(),
            "provenance": self.provenance.to_dict(),
            "quality": self.quality.to_dict(),
        }


@dataclass
class PublicMarketFactRecordV1:
    schema_version: str
    fact_digest: str
    payload: Mapping[str, Any]
    persisted_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "fact_digest": self.fact_digest,
            "payload": dict(self.payload),
            "persisted_at": self.persisted_at,
        }
