"""Typed observation identity and MarketObservationEpoch for C1.

PURE_DOMAIN_COMPONENT=true
NO_IO=true
NO_GLOBAL_STATE=true
NO_WALLCLOCK_READ=true
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional, Tuple

# Distinctness authority fields only. Transport/receive/runtime fields are excluded.
DISTINCTNESS_IDENTITY_FIELDS: Tuple[str, ...] = (
    "venue",
    "canonical_instrument_id",
    "venue_instrument_id",
    "venue_event_time",
    "mark_price",
)

NON_DISTINCTNESS_AUTHORITY_FIELDS: Tuple[str, ...] = (
    "receive_time",
    "runtime_cycle_index",
    "poll_attempt",
    "wallclock_now",
    "heartbeat_sequence",
    "transport_latency",
)


def _require_non_empty_str(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"INVALID_OBSERVATION_IDENTITY_FIELD:{name}")
    return value.strip()


def _require_epoch_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("INVALID_MARKET_OBSERVATION_EPOCH")
    if value < 0:
        raise ValueError("INVALID_MARKET_OBSERVATION_EPOCH_NEGATIVE")
    return value


@dataclass(frozen=True)
class MarketObservationEpoch:
    """Opaque non-negative epoch advanced only by accepted DISTINCT observations.

    Invariants:
    - value >= 0
    - no implicit RuntimeCycleIndex conversion
    - no implicit DecisionEpoch conversion
    """

    value: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _require_epoch_int(self.value))

    def advanced_by_one(self) -> "MarketObservationEpoch":
        return MarketObservationEpoch(value=self.value + 1)

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value}

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "MarketObservationEpoch":
        return cls(value=int(payload["value"]))


@dataclass(frozen=True)
class InstrumentObservationKeyV1:
    """Instrument-bound ownership key; prevents cross-instrument epoch crosstalk."""

    venue: str
    canonical_instrument_id: str
    venue_instrument_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "venue", _require_non_empty_str("venue", self.venue))
        object.__setattr__(
            self,
            "canonical_instrument_id",
            _require_non_empty_str("canonical_instrument_id", self.canonical_instrument_id),
        )
        object.__setattr__(
            self,
            "venue_instrument_id",
            _require_non_empty_str("venue_instrument_id", self.venue_instrument_id),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "InstrumentObservationKeyV1":
        return cls(
            venue=str(payload["venue"]),
            canonical_instrument_id=str(payload["canonical_instrument_id"]),
            venue_instrument_id=str(payload["venue_instrument_id"]),
        )


@dataclass(frozen=True)
class ObservationIdentityV1:
    """Normalized market-observation identity used as distinctness authority.

    Distinctness authority fields:
    venue, canonical_instrument_id, venue_instrument_id, venue_event_time, mark_price.

    Explicitly NOT distinctness authority:
    receive_time, runtime_cycle_index, poll_attempt, wallclock_now,
    heartbeat_sequence, transport_latency.
    """

    venue: str
    canonical_instrument_id: str
    venue_instrument_id: str
    venue_event_time: float
    mark_price: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "venue", _require_non_empty_str("venue", self.venue))
        object.__setattr__(
            self,
            "canonical_instrument_id",
            _require_non_empty_str("canonical_instrument_id", self.canonical_instrument_id),
        )
        object.__setattr__(
            self,
            "venue_instrument_id",
            _require_non_empty_str("venue_instrument_id", self.venue_instrument_id),
        )
        if isinstance(self.venue_event_time, bool) or not isinstance(
            self.venue_event_time, (int, float)
        ):
            raise ValueError("INVALID_OBSERVATION_IDENTITY_FIELD:venue_event_time")
        if isinstance(self.mark_price, bool) or not isinstance(self.mark_price, (int, float)):
            raise ValueError("INVALID_OBSERVATION_IDENTITY_FIELD:mark_price")
        object.__setattr__(self, "venue_event_time", float(self.venue_event_time))
        object.__setattr__(self, "mark_price", float(self.mark_price))

    def instrument_key(self) -> InstrumentObservationKeyV1:
        return InstrumentObservationKeyV1(
            venue=self.venue,
            canonical_instrument_id=self.canonical_instrument_id,
            venue_instrument_id=self.venue_instrument_id,
        )

    def event_identity_key(self) -> Tuple[str, str, str, float]:
        """Venue/instrument/event-time identity without mark (conflict detection)."""
        return (
            self.venue,
            self.canonical_instrument_id,
            self.venue_instrument_id,
            self.venue_event_time,
        )

    def distinctness_key(self) -> Tuple[str, str, str, float, float]:
        return (
            self.venue,
            self.canonical_instrument_id,
            self.venue_instrument_id,
            self.venue_event_time,
            self.mark_price,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "venue": self.venue,
            "canonical_instrument_id": self.canonical_instrument_id,
            "venue_instrument_id": self.venue_instrument_id,
            "venue_event_time": self.venue_event_time,
            "mark_price": self.mark_price,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ObservationIdentityV1":
        return cls(
            venue=str(payload["venue"]),
            canonical_instrument_id=str(payload["canonical_instrument_id"]),
            venue_instrument_id=str(payload["venue_instrument_id"]),
            venue_event_time=float(payload["venue_event_time"]),
            mark_price=float(payload["mark_price"]),
        )


def is_finite_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(float(value))


def observation_identity_from_normalized_public_market_data_v1(
    data: Any,
) -> ObservationIdentityV1:
    """Map existing NormalizedPublicMarketDataV1 fields onto ObservationIdentityV1.

    Mapping authority remains the normalized public market-data contract.
    receive_ts_unix is intentionally excluded from identity.
    """
    return ObservationIdentityV1(
        venue=str(data.venue),
        canonical_instrument_id=str(data.canonical_instrument_id),
        venue_instrument_id=str(data.venue_instrument_id),
        venue_event_time=float(data.event_ts_unix),
        mark_price=float(data.mark_px),
    )


def observation_candidate_from_normalized_public_market_data_v1(
    data: Any,
    *,
    poll_attempt: Optional[int] = None,
    runtime_cycle_index: Optional[int] = None,
    heartbeat_sequence: Optional[int] = None,
    transport_latency: Optional[float] = None,
) -> "ObservationCandidateRef":
    """Build evaluator candidate from normalized market data + optional transport meta."""
    from trading.market_state.distinct_market_observation_acceptor_v1 import (
        ObservationCandidateV1,
        ObservationTransportMetadataV1,
    )

    return ObservationCandidateV1(
        venue=str(data.venue),
        canonical_instrument_id=str(data.canonical_instrument_id),
        venue_instrument_id=str(data.venue_instrument_id),
        venue_event_time=float(data.event_ts_unix),
        mark_price=float(data.mark_px),
        transport=ObservationTransportMetadataV1(
            receive_time=float(data.receive_ts_unix),
            poll_attempt=poll_attempt,
            runtime_cycle_index=runtime_cycle_index,
            heartbeat_sequence=heartbeat_sequence,
            transport_latency=transport_latency,
        ),
    )


# Forward type alias for typing without circular import at runtime annotation site.
ObservationCandidateRef = Any
