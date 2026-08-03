"""PT1M mark observation finalizer for productive typed-volatility wiring.

Converts high-frequency distinct mark observations into finalized PT1M mark
samples for ``CanonicalVolatilityTypedRuntimeProducerScaffoldV1``.

Wiring only:
- reuses ``BAR_INTERVAL_SECONDS`` from the canonical materializer
- never invents mark prices
- never promotes regime-proxy / legacy float authority
- emits at most one finalized sample per completed PT1M bucket
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Optional

from trading.master_v2.canonical_volatility_estimate_materializer_v1 import (
    BAR_INTERVAL_SECONDS,
)

PACKAGE_MARKER = "MASTER_V2_CANONICAL_VOLATILITY_PT1M_MARK_OBSERVATION_FINALIZER_V1=true"
CAPABILITY_ID = "MASTER_V2_CANONICAL_VOLATILITY_PT1M_MARK_OBSERVATION_FINALIZER_V1"
CAPABILITY_VERSION = "canonical_volatility_pt1m_mark_observation_finalizer/v1"
FINALIZER_OWNER = "trading.master_v2.canonical_volatility_pt1m_mark_observation_finalizer_v1"

NO_SYNTHETIC_MARK_PRICE = True
NO_PROXY_PROMOTION = True
NO_SILENT_DEFAULT = True
NO_IMPLICIT_GAP_FILL = True
ONE_FINALIZED_SAMPLE_PER_COMPLETED_PT1M_BUCKET = True


class Pt1mMarkObservationFinalizerError(ValueError):
    """Fail-closed PT1M mark observation finalizer error."""


@dataclass(frozen=True)
class FinalizedPt1mMarkObservationV1:
    """One finalized PT1M mark observation ready for producer ingest."""

    event_time_unix_seconds: float
    mark_price: float
    bucket_start_unix_seconds: float
    source_event_time_unix_seconds: float
    receive_time_unix_seconds: Optional[float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_time_unix_seconds": self.event_time_unix_seconds,
            "mark_price": self.mark_price,
            "bucket_start_unix_seconds": self.bucket_start_unix_seconds,
            "source_event_time_unix_seconds": self.source_event_time_unix_seconds,
            "receive_time_unix_seconds": self.receive_time_unix_seconds,
            "bar_interval_seconds": BAR_INTERVAL_SECONDS,
            "is_final": True,
        }


def pt1m_bucket_start_unix_seconds_v1(event_time_unix_seconds: float) -> float:
    if not isinstance(event_time_unix_seconds, (int, float)) or not math.isfinite(
        float(event_time_unix_seconds)
    ):
        raise Pt1mMarkObservationFinalizerError("INVALID_EVENT_TIME")
    et = float(event_time_unix_seconds)
    if et <= 0.0:
        raise Pt1mMarkObservationFinalizerError("NONPOSITIVE_EVENT_TIME")
    return math.floor(et / float(BAR_INTERVAL_SECONDS)) * float(BAR_INTERVAL_SECONDS)


def _validate_mark_price_v1(mark_price: Any) -> float:
    if mark_price is None:
        raise Pt1mMarkObservationFinalizerError("MARK_PRICE_NULL")
    try:
        price = float(mark_price)
    except (TypeError, ValueError) as exc:
        raise Pt1mMarkObservationFinalizerError("MARK_PRICE_NON_NUMERIC") from exc
    if not math.isfinite(price) or price <= 0.0:
        raise Pt1mMarkObservationFinalizerError("MARK_PRICE_NON_FINITE_OR_NONPOSITIVE")
    return price


@dataclass
class CanonicalVolatilityPt1mMarkObservationFinalizerV1:
    """Session-local finalizer: last mark per open PT1M bucket → finalize on rollover."""

    venue: str
    canonical_instrument_id: str
    venue_instrument_id: str
    _open_bucket_start: Optional[float] = None
    _open_mark_price: Optional[float] = None
    _open_source_event_time: Optional[float] = None
    _open_receive_time: Optional[float] = None
    _last_emitted_bucket_start: Optional[float] = None
    _finalized_count: int = 0

    @classmethod
    def create(
        cls,
        *,
        venue: str,
        canonical_instrument_id: str,
        venue_instrument_id: str,
    ) -> "CanonicalVolatilityPt1mMarkObservationFinalizerV1":
        return cls(
            venue=str(venue).strip(),
            canonical_instrument_id=str(canonical_instrument_id).strip(),
            venue_instrument_id=str(venue_instrument_id).strip(),
        )

    @property
    def finalized_count(self) -> int:
        return int(self._finalized_count)

    @property
    def open_bucket_start_unix_seconds(self) -> Optional[float]:
        return self._open_bucket_start

    def reset_for_instrument_v1(
        self,
        *,
        venue: str,
        canonical_instrument_id: str,
        venue_instrument_id: str,
    ) -> None:
        self.venue = str(venue).strip()
        self.canonical_instrument_id = str(canonical_instrument_id).strip()
        self.venue_instrument_id = str(venue_instrument_id).strip()
        self._open_bucket_start = None
        self._open_mark_price = None
        self._open_source_event_time = None
        self._open_receive_time = None
        self._last_emitted_bucket_start = None
        self._finalized_count = 0

    def observe_mark_v1(
        self,
        *,
        event_time_unix_seconds: float,
        mark_price: float,
        receive_time_unix_seconds: float | None = None,
    ) -> Optional[FinalizedPt1mMarkObservationV1]:
        """Observe one mark; emit prior bucket finalize when the PT1M bucket rolls."""
        price = _validate_mark_price_v1(mark_price)
        bucket_start = pt1m_bucket_start_unix_seconds_v1(event_time_unix_seconds)
        receive = None
        if receive_time_unix_seconds is not None:
            if not isinstance(receive_time_unix_seconds, (int, float)) or not math.isfinite(
                float(receive_time_unix_seconds)
            ):
                raise Pt1mMarkObservationFinalizerError("INVALID_RECEIVE_TIME")
            receive = float(receive_time_unix_seconds)

        if self._open_bucket_start is None:
            self._open_bucket_start = bucket_start
            self._open_mark_price = price
            self._open_source_event_time = float(event_time_unix_seconds)
            self._open_receive_time = receive
            return None

        if bucket_start < float(self._open_bucket_start):
            raise Pt1mMarkObservationFinalizerError("OUT_OF_ORDER_BUCKET")

        if bucket_start == float(self._open_bucket_start):
            # Same open PT1M bucket: update last mark only; do not emit / advance history.
            self._open_mark_price = price
            self._open_source_event_time = float(event_time_unix_seconds)
            self._open_receive_time = receive
            return None

        # Bucket rolled: finalize the previous open bucket exactly once.
        emitted = self._finalize_open_bucket_v1()
        self._open_bucket_start = bucket_start
        self._open_mark_price = price
        self._open_source_event_time = float(event_time_unix_seconds)
        self._open_receive_time = receive
        return emitted

    def _finalize_open_bucket_v1(self) -> FinalizedPt1mMarkObservationV1:
        if (
            self._open_bucket_start is None
            or self._open_mark_price is None
            or self._open_source_event_time is None
        ):
            raise Pt1mMarkObservationFinalizerError("NO_OPEN_BUCKET")
        bucket_start = float(self._open_bucket_start)
        if self._last_emitted_bucket_start is not None and bucket_start == float(
            self._last_emitted_bucket_start
        ):
            raise Pt1mMarkObservationFinalizerError("DUPLICATE_BUCKET_FINALIZE")
        close_event_time = bucket_start + float(BAR_INTERVAL_SECONDS)
        observation = FinalizedPt1mMarkObservationV1(
            event_time_unix_seconds=close_event_time,
            mark_price=float(self._open_mark_price),
            bucket_start_unix_seconds=bucket_start,
            source_event_time_unix_seconds=float(self._open_source_event_time),
            receive_time_unix_seconds=self._open_receive_time,
        )
        self._last_emitted_bucket_start = bucket_start
        self._finalized_count += 1
        return observation

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": CAPABILITY_ID,
            "capability_version": CAPABILITY_VERSION,
            "finalizer_owner": FINALIZER_OWNER,
            "venue": self.venue,
            "canonical_instrument_id": self.canonical_instrument_id,
            "venue_instrument_id": self.venue_instrument_id,
            "open_bucket_start_unix_seconds": self._open_bucket_start,
            "finalized_count": self._finalized_count,
            "last_emitted_bucket_start_unix_seconds": self._last_emitted_bucket_start,
            "bar_interval_seconds": BAR_INTERVAL_SECONDS,
            "no_synthetic_mark_price": NO_SYNTHETIC_MARK_PRICE,
            "no_proxy_promotion": NO_PROXY_PROMOTION,
            "no_silent_default": NO_SILENT_DEFAULT,
            "no_implicit_gap_fill": NO_IMPLICIT_GAP_FILL,
        }


__all__ = [
    "BAR_INTERVAL_SECONDS",
    "CAPABILITY_ID",
    "CAPABILITY_VERSION",
    "CanonicalVolatilityPt1mMarkObservationFinalizerV1",
    "FINALIZER_OWNER",
    "FinalizedPt1mMarkObservationV1",
    "NO_IMPLICIT_GAP_FILL",
    "NO_PROXY_PROMOTION",
    "NO_SILENT_DEFAULT",
    "NO_SYNTHETIC_MARK_PRICE",
    "ONE_FINALIZED_SAMPLE_PER_COMPLETED_PT1M_BUCKET",
    "PACKAGE_MARKER",
    "Pt1mMarkObservationFinalizerError",
    "pt1m_bucket_start_unix_seconds_v1",
]
