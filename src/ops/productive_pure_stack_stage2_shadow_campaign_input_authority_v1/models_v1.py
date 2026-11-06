"""Immutable models for Stage-2 Shadow Campaign Input Authority v1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional, Sequence, Tuple


class InputAuthorityErrorV1(ValueError):
    """Fail-closed Surface-B input authority error."""


@dataclass(frozen=True)
class InstrumentBindingV1:
    venue: str
    canonical_instrument_id: str
    venue_instrument_id: str
    contract_type: str
    market_type: str
    quote_currency: str
    settlement_currency: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class VenueNativeCandleInputV1:
    """Raw venue-native finalized candle OHLCV (not mark, not trade equivalence)."""

    event_time_epoch_s: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    venue_finalized: bool
    open_tip: bool = False


@dataclass(frozen=True)
class MarkPriceInputV1:
    """Required separate mark-price observation for the same event-time bucket."""

    event_time_epoch_s: int
    mark_price: float


@dataclass(frozen=True)
class ProducedFinalizedBarV1:
    instrument_id: str
    event_time_epoch_s: int
    open: float
    high: float
    low: float
    close: float
    mark_price: float
    volume: float
    finalized: bool
    dataset_id: str
    source_id: str
    venue: str
    revision: int = 0
    correction_of_event_time_epoch_s: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EventTimeRangeV1:
    start_epoch_s: int
    end_epoch_s_exclusive: int

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class ObservationPackProvenanceV1:
    dataset_id: str
    source_id: str
    venue: str
    instrument_id: str
    timeframe: str
    event_time_range: EventTimeRangeV1
    ingestion_timestamp: str
    finalization_timestamp: str
    repository_sha: str
    config_digest: str
    producer_version: str
    raw_source_digest: str
    correction_revision_policy: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["event_time_range"] = self.event_time_range.to_dict()
        return payload


@dataclass(frozen=True)
class ObservationPackV1:
    provenance: ObservationPackProvenanceV1
    bars: Tuple[ProducedFinalizedBarV1, ...]
    observation_pack_digest: str
    instrument_binding: InstrumentBindingV1

    def to_dict(self) -> dict[str, Any]:
        return {
            "provenance": self.provenance.to_dict(),
            "bars": [b.to_dict() for b in self.bars],
            "observation_pack_digest": self.observation_pack_digest,
            "instrument_binding": self.instrument_binding.to_dict(),
        }


@dataclass(frozen=True)
class StructuralManifestSpecV1:
    """Structural-only partition/walk-forward/bootstrap/stress specs.

    Numeric Owner magnitudes remain unset (None) until a separate GO.
    """

    dataset_id: str
    instrument_id: str
    event_time_range: EventTimeRangeV1
    segment_boundaries_event_time_epoch_s: Mapping[str, int]
    fold_ids: Sequence[str]
    bootstrap_seeds: Sequence[int]
    regime_coverage: Mapping[str, int]
    stress_families: Sequence[str]
    purge_seconds: Optional[int] = None
    embargo_seconds: Optional[int] = None
    fold_sizes: Optional[Mapping[str, int]] = None
    bootstrap_block_length: Optional[int] = None
    bootstrap_path_count: Optional[int] = None
    resampling_unit: Optional[str] = None
