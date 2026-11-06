"""Versioned DTOs for persisted Economic-MD MVR raw-input snapshots."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from src.ops.economic_md_input_producer_v1.constants_v1 import (
    ALPHA_ALLOWED_DEFAULT,
    CANARY_AUTHORITY_TRANSFERRED,
    CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED,
    CAPABILITY_ID,
    CAP52_AUTHORITY_TRANSFERRED,
    CMC_AUTHORITY_TRANSFERRED,
    ECONOMIC_MD_PRODUCER_MAY_APPLY_POLICY_A,
    ECONOMIC_MD_PRODUCER_MAY_DEFINE_ACTIVE_SET,
    ECONOMIC_MD_PRODUCER_MAY_DEFINE_TOP20,
    ECONOMIC_MD_PRODUCER_MAY_RANK,
    ECONOMIC_MD_PRODUCER_MAY_SELECT,
    ECONOMIC_MD_PRODUCER_MAY_TRIGGER_EXECUTION,
    ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED,
    ECONOMIC_RANK_ACTIVATED,
    LIBRARY_REUSE_AUTHORITY_TRANSFER,
    LIVE_AUTHORIZED,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    OWNER,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    SELECTED_FUTURE_MD_AUTHORITY_TRANSFERRED,
    VENUE,
)


def canonical_json_dumps(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class FinalizedPt1mMarkObservationV1:
    mark_px: str
    event_timestamp: str
    receive_or_capture_timestamp: str
    finalization_status: str
    source_class: str
    source_endpoint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_timestamp": self.event_timestamp,
            "finalization_status": self.finalization_status,
            "mark_px": self.mark_px,
            "receive_or_capture_timestamp": self.receive_or_capture_timestamp,
            "source_class": self.source_class,
            "source_endpoint": self.source_endpoint,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "FinalizedPt1mMarkObservationV1":
        return FinalizedPt1mMarkObservationV1(
            mark_px=str(payload["mark_px"]),
            event_timestamp=str(payload["event_timestamp"]),
            receive_or_capture_timestamp=str(payload["receive_or_capture_timestamp"]),
            finalization_status=str(payload["finalization_status"]),
            source_class=str(payload["source_class"]),
            source_endpoint=str(payload["source_endpoint"]),
        )


@dataclass(frozen=True)
class SameCycleTickerObservationV1:
    bid_px: str
    ask_px: str
    ticker_event_timestamp: Optional[str]
    capture_or_receive_timestamp: str
    source_class: str
    source_endpoint: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ask_px": self.ask_px,
            "bid_px": self.bid_px,
            "capture_or_receive_timestamp": self.capture_or_receive_timestamp,
            "source_class": self.source_class,
            "source_endpoint": self.source_endpoint,
            "ticker_event_timestamp": self.ticker_event_timestamp,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "SameCycleTickerObservationV1":
        event_ts = payload.get("ticker_event_timestamp")
        return SameCycleTickerObservationV1(
            bid_px=str(payload["bid_px"]),
            ask_px=str(payload["ask_px"]),
            ticker_event_timestamp=None if event_ts in (None, "") else str(event_ts),
            capture_or_receive_timestamp=str(payload["capture_or_receive_timestamp"]),
            source_class=str(payload["source_class"]),
            source_endpoint=str(payload["source_endpoint"]),
        )


@dataclass(frozen=True)
class UnresolvedValidityDimensionsV1:
    locked_market: str
    near_zero_spread: str
    stale_seconds: str
    collection_skew: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "collection_skew": self.collection_skew,
            "locked_market": self.locked_market,
            "near_zero_spread": self.near_zero_spread,
            "stale_seconds": self.stale_seconds,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "UnresolvedValidityDimensionsV1":
        return UnresolvedValidityDimensionsV1(
            locked_market=str(payload.get("locked_market") or ""),
            near_zero_spread=str(payload.get("near_zero_spread") or ""),
            stale_seconds=str(payload.get("stale_seconds") or ""),
            collection_skew=str(payload.get("collection_skew") or ""),
        )


@dataclass(frozen=True)
class EconomicMdInstrumentRawInputV1:
    canonical_instrument_id: str
    venue_native_id: str
    raw_input_eligible: bool
    exclusion_reason_codes: tuple[str, ...]
    finalized_pt1m_marks: tuple[FinalizedPt1mMarkObservationV1, ...]
    ticker: Optional[SameCycleTickerObservationV1]
    unresolved_validity_dimensions: UnresolvedValidityDimensionsV1
    raw_input_digest: str
    provenance: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_instrument_id": self.canonical_instrument_id,
            "exclusion_reason_codes": list(self.exclusion_reason_codes),
            "finalized_pt1m_marks": [row.to_dict() for row in self.finalized_pt1m_marks],
            "provenance": dict(self.provenance),
            "raw_input_digest": self.raw_input_digest,
            "raw_input_eligible": self.raw_input_eligible,
            "ticker": None if self.ticker is None else self.ticker.to_dict(),
            "unresolved_validity_dimensions": self.unresolved_validity_dimensions.to_dict(),
            "venue_native_id": self.venue_native_id,
        }

    def deterministic_payload_for_digest(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("raw_input_digest", None)
        return payload

    def compute_raw_input_digest(self) -> str:
        return sha256_hex(canonical_json_dumps(self.deterministic_payload_for_digest()))

    def with_raw_input_digest(self) -> "EconomicMdInstrumentRawInputV1":
        return EconomicMdInstrumentRawInputV1(
            canonical_instrument_id=self.canonical_instrument_id,
            venue_native_id=self.venue_native_id,
            raw_input_eligible=self.raw_input_eligible,
            exclusion_reason_codes=self.exclusion_reason_codes,
            finalized_pt1m_marks=self.finalized_pt1m_marks,
            ticker=self.ticker,
            unresolved_validity_dimensions=self.unresolved_validity_dimensions,
            raw_input_digest=self.compute_raw_input_digest(),
            provenance=dict(self.provenance),
        )

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "EconomicMdInstrumentRawInputV1":
        marks = tuple(
            FinalizedPt1mMarkObservationV1.from_dict(row)
            for row in (payload.get("finalized_pt1m_marks") or [])
        )
        ticker_raw = payload.get("ticker")
        ticker = (
            None
            if ticker_raw in (None, "")
            else SameCycleTickerObservationV1.from_dict(dict(ticker_raw))
        )
        return EconomicMdInstrumentRawInputV1(
            canonical_instrument_id=str(payload["canonical_instrument_id"]),
            venue_native_id=str(payload["venue_native_id"]),
            raw_input_eligible=bool(payload.get("raw_input_eligible", False)),
            exclusion_reason_codes=tuple(
                str(x) for x in (payload.get("exclusion_reason_codes") or ())
            ),
            finalized_pt1m_marks=marks,
            ticker=ticker,
            unresolved_validity_dimensions=UnresolvedValidityDimensionsV1.from_dict(
                dict(payload.get("unresolved_validity_dimensions") or {})
            ),
            raw_input_digest=str(payload.get("raw_input_digest") or ""),
            provenance=dict(payload.get("provenance") or {}),
        )


@dataclass(frozen=True)
class EconomicMdInputSnapshotV1:
    schema_version: str
    producer_version: str
    capability_id: str
    economic_input_snapshot_id: str
    universe_snapshot_reference: Mapping[str, Any]
    collection_cycle_identity: str
    collection_started_at: str
    collection_completed_at: str
    instrument_count_requested: int
    instrument_count_rankable_raw_input: int
    payload_digest: str
    provenance: Mapping[str, Any]
    instruments: tuple[EconomicMdInstrumentRawInputV1, ...]
    authority: Mapping[str, Any] = field(default_factory=dict)
    call_graph: tuple[str, ...] = ()
    failure_codes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority": dict(self.authority),
            "call_graph": list(self.call_graph),
            "capability_id": self.capability_id,
            "collection_completed_at": self.collection_completed_at,
            "collection_cycle_identity": self.collection_cycle_identity,
            "collection_started_at": self.collection_started_at,
            "economic_input_snapshot_id": self.economic_input_snapshot_id,
            "failure_codes": list(self.failure_codes),
            "instrument_count_rankable_raw_input": self.instrument_count_rankable_raw_input,
            "instrument_count_requested": self.instrument_count_requested,
            "instruments": [row.to_dict() for row in self.instruments],
            "payload_digest": self.payload_digest,
            "producer_version": self.producer_version,
            "provenance": dict(self.provenance),
            "schema_version": self.schema_version,
            "universe_snapshot_reference": dict(self.universe_snapshot_reference),
        }

    def deterministic_payload_for_digest(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("payload_digest", None)
        return payload

    def compute_payload_digest(self) -> str:
        return sha256_hex(canonical_json_dumps(self.deterministic_payload_for_digest()))

    def with_payload_digest(self) -> "EconomicMdInputSnapshotV1":
        return EconomicMdInputSnapshotV1(
            schema_version=self.schema_version,
            producer_version=self.producer_version,
            capability_id=self.capability_id,
            economic_input_snapshot_id=self.economic_input_snapshot_id,
            universe_snapshot_reference=dict(self.universe_snapshot_reference),
            collection_cycle_identity=self.collection_cycle_identity,
            collection_started_at=self.collection_started_at,
            collection_completed_at=self.collection_completed_at,
            instrument_count_requested=self.instrument_count_requested,
            instrument_count_rankable_raw_input=self.instrument_count_rankable_raw_input,
            payload_digest=self.compute_payload_digest(),
            provenance=dict(self.provenance),
            instruments=self.instruments,
            authority=dict(self.authority),
            call_graph=self.call_graph,
            failure_codes=self.failure_codes,
        )

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "EconomicMdInputSnapshotV1":
        instruments = tuple(
            EconomicMdInstrumentRawInputV1.from_dict(row)
            for row in (payload.get("instruments") or [])
        )
        return EconomicMdInputSnapshotV1(
            schema_version=str(payload.get("schema_version") or ""),
            producer_version=str(payload.get("producer_version") or ""),
            capability_id=str(payload.get("capability_id") or ""),
            economic_input_snapshot_id=str(payload.get("economic_input_snapshot_id") or ""),
            universe_snapshot_reference=dict(payload.get("universe_snapshot_reference") or {}),
            collection_cycle_identity=str(payload.get("collection_cycle_identity") or ""),
            collection_started_at=str(payload.get("collection_started_at") or ""),
            collection_completed_at=str(payload.get("collection_completed_at") or ""),
            instrument_count_requested=int(payload.get("instrument_count_requested") or 0),
            instrument_count_rankable_raw_input=int(
                payload.get("instrument_count_rankable_raw_input") or 0
            ),
            payload_digest=str(payload.get("payload_digest") or ""),
            provenance=dict(payload.get("provenance") or {}),
            instruments=instruments,
            authority=dict(payload.get("authority") or {}),
            call_graph=tuple(str(x) for x in (payload.get("call_graph") or ())),
            failure_codes=tuple(str(x) for x in (payload.get("failure_codes") or ())),
        )


@dataclass(frozen=True)
class EconomicMdProduceResultV1:
    snapshot: EconomicMdInputSnapshotV1
    ok: bool
    hard_stop: bool
    failure_codes: tuple[str, ...]


def authority_block() -> dict[str, Any]:
    return {
        "ALPHA_ALLOWED": ALPHA_ALLOWED_DEFAULT,
        "AUTHORITY_OWNER": CAPABILITY_ID,
        "CANARY_AUTHORITY_TRANSFERRED": CANARY_AUTHORITY_TRANSFERRED,
        "CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED": CAP22_PRODUCTIVE_ECONOMIC_RUNTIME_WIRED,
        "CAP52_AUTHORITY_TRANSFERRED": CAP52_AUTHORITY_TRANSFERRED,
        "CMC_AUTHORITY_TRANSFERRED": CMC_AUTHORITY_TRANSFERRED,
        "ECONOMIC_MD_PRODUCER_MAY_APPLY_POLICY_A": ECONOMIC_MD_PRODUCER_MAY_APPLY_POLICY_A,
        "ECONOMIC_MD_PRODUCER_MAY_DEFINE_ACTIVE_SET": ECONOMIC_MD_PRODUCER_MAY_DEFINE_ACTIVE_SET,
        "ECONOMIC_MD_PRODUCER_MAY_DEFINE_TOP20": ECONOMIC_MD_PRODUCER_MAY_DEFINE_TOP20,
        "ECONOMIC_MD_PRODUCER_MAY_RANK": ECONOMIC_MD_PRODUCER_MAY_RANK,
        "ECONOMIC_MD_PRODUCER_MAY_SELECT": ECONOMIC_MD_PRODUCER_MAY_SELECT,
        "ECONOMIC_MD_PRODUCER_MAY_TRIGGER_EXECUTION": (ECONOMIC_MD_PRODUCER_MAY_TRIGGER_EXECUTION),
        "ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED": (
            ECONOMIC_MD_PRODUCER_PRODUCTIVELY_SCHEDULED
        ),
        "ECONOMIC_RANK_ACTIVATED": ECONOMIC_RANK_ACTIVATED,
        "LIBRARY_REUSE_AUTHORITY_TRANSFER": LIBRARY_REUSE_AUTHORITY_TRANSFER,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "MULTI_FUTURE_RUNTIME_AUTHORIZED": MULTI_FUTURE_RUNTIME_AUTHORIZED,
        "OWNER": OWNER,
        "PRODUCER_VERSION": PRODUCER_VERSION,
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "SELECTED_FUTURE_MD_AUTHORITY_TRANSFERRED": SELECTED_FUTURE_MD_AUTHORITY_TRANSFERRED,
        "VENUE": VENUE,
    }


def compute_collection_cycle_identity_v1(
    *,
    universe_snapshot_id: str,
    collection_started_at: str,
    collection_completed_at: str,
) -> str:
    material = canonical_json_dumps(
        {
            "capability_id": CAPABILITY_ID,
            "collection_completed_at": collection_completed_at,
            "collection_started_at": collection_started_at,
            "producer_version": PRODUCER_VERSION,
            "universe_snapshot_id": universe_snapshot_id,
        }
    )
    return f"emd_cycle_{sha256_hex(material)[:24]}"


def compute_economic_input_snapshot_id_v1(
    *,
    universe_snapshot_id: str,
    universe_payload_digest: str,
    collection_cycle_identity: str,
    instrument_raw_digests: Sequence[str],
) -> str:
    material = canonical_json_dumps(
        {
            "capability_id": CAPABILITY_ID,
            "collection_cycle_identity": collection_cycle_identity,
            "instrument_raw_digests": list(instrument_raw_digests),
            "producer_version": PRODUCER_VERSION,
            "schema_version": SCHEMA_VERSION,
            "universe_payload_digest": universe_payload_digest,
            "universe_snapshot_id": universe_snapshot_id,
        }
    )
    return f"emd_{sha256_hex(material)[:24]}"
