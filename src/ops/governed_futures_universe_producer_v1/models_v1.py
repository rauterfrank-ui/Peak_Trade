"""Versioned DTOs for governed futures universe snapshots."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence

from src.ops.governed_futures_universe_producer_v1.constants_v1 import (
    ALPHA_ALLOWED_DEFAULT,
    CAPABILITY_ID,
    PRODUCER_VERSION,
    SCHEMA_VERSION,
    UNIVERSE_STATUS_EMPTY,
    UNIVERSE_STATUS_ELIGIBLE,
    VENUE,
)


def canonical_json_dumps(payload: Mapping[str, Any] | list[Any] | Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True)
class GovernedUniverseInstrumentV1:
    """Normalized eligible or classified instrument row."""

    canonical_instrument_id: str
    venue: str
    venue_native_inst_id: str
    instrument_type: str
    base_currency: str
    quote_currency: str
    settlement_currency: str
    contract_type: str
    perpetual_or_expiry_semantics: str
    expiry_time: Optional[str]
    tick_size: str
    lot_size: str
    minimum_order_size: str
    contract_value: str
    contract_value_currency: str
    trading_status: str
    mark_price_supported: bool
    market_data_supported: bool
    data_quality_status: str
    source_event_time: str
    producer_observed_at: str
    producer_version: str
    repository_sha: str
    config_digest: str
    source_digest: str
    eligibility: bool
    exclusion_reason_codes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_instrument_id": self.canonical_instrument_id,
            "venue": self.venue,
            "venue_native_inst_id": self.venue_native_inst_id,
            "instrument_type": self.instrument_type,
            "base_currency": self.base_currency,
            "quote_currency": self.quote_currency,
            "settlement_currency": self.settlement_currency,
            "contract_type": self.contract_type,
            "perpetual_or_expiry_semantics": self.perpetual_or_expiry_semantics,
            "expiry_time": self.expiry_time,
            "tick_size": self.tick_size,
            "lot_size": self.lot_size,
            "minimum_order_size": self.minimum_order_size,
            "contract_value": self.contract_value,
            "contract_value_currency": self.contract_value_currency,
            "trading_status": self.trading_status,
            "mark_price_supported": self.mark_price_supported,
            "market_data_supported": self.market_data_supported,
            "data_quality_status": self.data_quality_status,
            "source_event_time": self.source_event_time,
            "producer_observed_at": self.producer_observed_at,
            "producer_version": self.producer_version,
            "repository_sha": self.repository_sha,
            "config_digest": self.config_digest,
            "source_digest": self.source_digest,
            "eligibility": self.eligibility,
            "exclusion_reason_codes": list(self.exclusion_reason_codes),
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "GovernedUniverseInstrumentV1":
        return GovernedUniverseInstrumentV1(
            canonical_instrument_id=str(payload["canonical_instrument_id"]),
            venue=str(payload["venue"]),
            venue_native_inst_id=str(payload["venue_native_inst_id"]),
            instrument_type=str(payload["instrument_type"]),
            base_currency=str(payload["base_currency"]),
            quote_currency=str(payload["quote_currency"]),
            settlement_currency=str(payload["settlement_currency"]),
            contract_type=str(payload["contract_type"]),
            perpetual_or_expiry_semantics=str(payload["perpetual_or_expiry_semantics"]),
            expiry_time=None
            if payload.get("expiry_time") in (None, "")
            else str(payload.get("expiry_time")),
            tick_size=str(payload["tick_size"]),
            lot_size=str(payload["lot_size"]),
            minimum_order_size=str(payload["minimum_order_size"]),
            contract_value=str(payload["contract_value"]),
            contract_value_currency=str(payload["contract_value_currency"]),
            trading_status=str(payload["trading_status"]),
            mark_price_supported=bool(payload["mark_price_supported"]),
            market_data_supported=bool(payload["market_data_supported"]),
            data_quality_status=str(payload["data_quality_status"]),
            source_event_time=str(payload["source_event_time"]),
            producer_observed_at=str(payload["producer_observed_at"]),
            producer_version=str(payload["producer_version"]),
            repository_sha=str(payload["repository_sha"]),
            config_digest=str(payload["config_digest"]),
            source_digest=str(payload["source_digest"]),
            eligibility=bool(payload["eligibility"]),
            exclusion_reason_codes=tuple(
                str(x) for x in (payload.get("exclusion_reason_codes") or ())
            ),
        )


@dataclass(frozen=True)
class GovernedFuturesUniverseSnapshotV1:
    """Deterministic, versioned universe snapshot DTO."""

    schema_version: str
    capability_id: str
    producer_version: str
    snapshot_id: str
    repository_sha: str
    config_digest: str
    source_digest: str
    payload_digest: str
    generated_at_event_time: str
    generated_at_wall_time: str
    venue: str
    universe_status: str
    alpha_allowed: bool
    raw_instrument_count: int
    eligible_instrument_count: int
    excluded_instrument_count: int
    exclusion_counts_by_reason: Mapping[str, int]
    instruments: tuple[GovernedUniverseInstrumentV1, ...]
    authority: Mapping[str, Any] = field(default_factory=dict)
    call_graph: tuple[str, ...] = ()
    failure_codes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "capability_id": self.capability_id,
            "producer_version": self.producer_version,
            "snapshot_id": self.snapshot_id,
            "repository_sha": self.repository_sha,
            "config_digest": self.config_digest,
            "source_digest": self.source_digest,
            "payload_digest": self.payload_digest,
            "generated_at_event_time": self.generated_at_event_time,
            "generated_at_wall_time": self.generated_at_wall_time,
            "venue": self.venue,
            "universe_status": self.universe_status,
            "alpha_allowed": self.alpha_allowed,
            "raw_instrument_count": self.raw_instrument_count,
            "eligible_instrument_count": self.eligible_instrument_count,
            "excluded_instrument_count": self.excluded_instrument_count,
            "exclusion_counts_by_reason": dict(sorted(self.exclusion_counts_by_reason.items())),
            "instruments": [row.to_dict() for row in self.instruments],
            "authority": dict(self.authority),
            "call_graph": list(self.call_graph),
            "failure_codes": list(self.failure_codes),
        }

    def deterministic_payload_for_digest(self) -> dict[str, Any]:
        """Payload excluding payload_digest itself (digest over content)."""
        payload = self.to_dict()
        payload.pop("payload_digest", None)
        return payload

    def compute_payload_digest(self) -> str:
        return sha256_hex(canonical_json_dumps(self.deterministic_payload_for_digest()))

    def with_payload_digest(self) -> "GovernedFuturesUniverseSnapshotV1":
        digest = self.compute_payload_digest()
        return GovernedFuturesUniverseSnapshotV1(
            schema_version=self.schema_version,
            capability_id=self.capability_id,
            producer_version=self.producer_version,
            snapshot_id=self.snapshot_id,
            repository_sha=self.repository_sha,
            config_digest=self.config_digest,
            source_digest=self.source_digest,
            payload_digest=digest,
            generated_at_event_time=self.generated_at_event_time,
            generated_at_wall_time=self.generated_at_wall_time,
            venue=self.venue,
            universe_status=self.universe_status,
            alpha_allowed=self.alpha_allowed,
            raw_instrument_count=self.raw_instrument_count,
            eligible_instrument_count=self.eligible_instrument_count,
            excluded_instrument_count=self.excluded_instrument_count,
            exclusion_counts_by_reason=dict(sorted(self.exclusion_counts_by_reason.items())),
            instruments=self.instruments,
            authority=dict(self.authority),
            call_graph=self.call_graph,
            failure_codes=self.failure_codes,
        )

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "GovernedFuturesUniverseSnapshotV1":
        instruments = tuple(
            GovernedUniverseInstrumentV1.from_dict(row)
            for row in (payload.get("instruments") or [])
        )
        return GovernedFuturesUniverseSnapshotV1(
            schema_version=str(payload.get("schema_version") or ""),
            capability_id=str(payload.get("capability_id") or ""),
            producer_version=str(payload.get("producer_version") or ""),
            snapshot_id=str(payload.get("snapshot_id") or ""),
            repository_sha=str(payload.get("repository_sha") or ""),
            config_digest=str(payload.get("config_digest") or ""),
            source_digest=str(payload.get("source_digest") or ""),
            payload_digest=str(payload.get("payload_digest") or ""),
            generated_at_event_time=str(payload.get("generated_at_event_time") or ""),
            generated_at_wall_time=str(payload.get("generated_at_wall_time") or ""),
            venue=str(payload.get("venue") or ""),
            universe_status=str(payload.get("universe_status") or ""),
            alpha_allowed=bool(payload.get("alpha_allowed", False)),
            raw_instrument_count=int(payload.get("raw_instrument_count") or 0),
            eligible_instrument_count=int(payload.get("eligible_instrument_count") or 0),
            excluded_instrument_count=int(payload.get("excluded_instrument_count") or 0),
            exclusion_counts_by_reason={
                str(k): int(v)
                for k, v in dict(payload.get("exclusion_counts_by_reason") or {}).items()
            },
            instruments=instruments,
            authority=dict(payload.get("authority") or {}),
            call_graph=tuple(str(x) for x in (payload.get("call_graph") or ())),
            failure_codes=tuple(str(x) for x in (payload.get("failure_codes") or ())),
        )


@dataclass(frozen=True)
class UniverseProduceResultV1:
    snapshot: GovernedFuturesUniverseSnapshotV1
    excluded_instruments: tuple[GovernedUniverseInstrumentV1, ...]
    ok: bool
    hard_stop: bool
    failure_codes: tuple[str, ...]


def empty_universe_status(*, eligible_count: int) -> str:
    if eligible_count <= 0:
        return UNIVERSE_STATUS_EMPTY
    return UNIVERSE_STATUS_ELIGIBLE


def authority_block() -> dict[str, Any]:
    return {
        "UNIVERSE_AUTHORITY_OWNER_SINGLE": True,
        "AUTHORITY_OWNER": CAPABILITY_ID,
        "OWNER": "ops.governed_futures_universe_producer_v1",
        "DASHBOARD_AUTHORITY": False,
        "RANKING_AUTHORITY_ADDED": False,
        "SELECTION_AUTHORITY_ADDED": False,
        "ALPHA_AUTHORITY_ADDED": False,
        "EXECUTION_AUTHORITY_ADDED": False,
        "LEGACY_PARALLEL_AUTHORITY_ABSENT": True,
        "ALPHA_ALLOWED": ALPHA_ALLOWED_DEFAULT,
        "VENUE": VENUE,
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "PRODUCER_VERSION": PRODUCER_VERSION,
    }


def compute_config_digest_v1(
    *,
    repository_sha: str,
    max_source_age_seconds: float,
    venue: str = VENUE,
    futures_only: bool = True,
    btc_excluded: bool = True,
    spot_excluded: bool = True,
) -> str:
    payload = {
        "capability_id": CAPABILITY_ID,
        "schema_version": SCHEMA_VERSION,
        "producer_version": PRODUCER_VERSION,
        "venue": venue,
        "futures_only": futures_only,
        "btc_excluded": btc_excluded,
        "spot_excluded": spot_excluded,
        "max_source_age_seconds": max_source_age_seconds,
        "repository_sha": repository_sha,
        "alpha_allowed": ALPHA_ALLOWED_DEFAULT,
        "ranking_authority_added": False,
        "selection_authority_added": False,
        "multi_future_runtime_authorized": False,
        "max_positions_effective": 1,
    }
    return sha256_hex(canonical_json_dumps(payload))


def compute_source_digest_v1(
    *,
    instruments: Sequence[Mapping[str, Any]],
    mark_price_supported_ids: Sequence[str],
    source_event_time: str,
    venue: str,
) -> str:
    normalized = [
        {
            "instId": str(row.get("instId") or ""),
            "instType": str(row.get("instType") or ""),
            "state": str(row.get("state") or ""),
            "baseCcy": str(row.get("baseCcy") or ""),
            "quoteCcy": str(row.get("quoteCcy") or ""),
            "settleCcy": str(row.get("settleCcy") or ""),
            "ctType": str(row.get("ctType") or ""),
            "ctVal": str(row.get("ctVal") or ""),
            "ctValCcy": str(row.get("ctValCcy") or ""),
            "tickSz": str(row.get("tickSz") or ""),
            "lotSz": str(row.get("lotSz") or ""),
            "minSz": str(row.get("minSz") or ""),
            "expTime": str(row.get("expTime") or ""),
            "uly": str(row.get("uly") or ""),
        }
        for row in sorted(instruments, key=lambda r: str(r.get("instId") or ""))
    ]
    payload = {
        "venue": venue,
        "source_event_time": source_event_time,
        "instruments": normalized,
        "mark_price_supported_ids": sorted(str(x) for x in mark_price_supported_ids),
    }
    return sha256_hex(canonical_json_dumps(payload))
