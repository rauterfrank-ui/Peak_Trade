"""Runtime mark-price history host for canonical volatility typed producer scaffold.

Capability-owned history under the existing Market-Sample acceptance authority.
Stores only distinct, finalized PT1M mark_price samples. Does not estimate
volatility, invent sample identity, synthesize bars, or wire Double Play.

Authority reuse:
- Sample acceptance / distinctness: ``accept_distinct_market_sample_v1``
- Event time: ``EventTimeInstantV1`` / ``MarketSampleIdentityV1``
- No second sample, event-time, or market-state authority

Persistence boundary: venue/instrument-isolated JSON with schema version;
atomic replace; fail-closed on corrupt / incompatible payloads. Process restart
reconstructs identical ordered history and digests.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import pandas as pd

from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceStateV1,
    ObservationClassification,
    ObservationTransportMetadataV1,
)
from trading.market_state.observation_identity_v1 import InstrumentObservationKeyV1
from trading.market_state.time_sample_epoch_semantics_v1 import (
    EventTimeInstantV1,
    MarketSampleIdentityV1,
    accept_distinct_market_sample_v1,
    deterministic_time_object_fingerprint_v1,
    initial_market_sample_acceptance_state_v1,
)
from trading.master_v2 import canonical_volatility_estimate_feature_contract_v1 as contract
from trading.master_v2 import canonical_volatility_estimate_materializer_v1 as materializer

HISTORY_OWNER = "trading.master_v2.canonical_volatility_runtime_mark_history_v1"
HISTORY_SCHEMA_VERSION = "canonical_volatility_runtime_mark_history/v1"
CAPABILITY_ID = "MASTER_V2_CANONICAL_VOLATILITY_TYPED_RUNTIME_PRODUCER_SCAFFOLD_V1"
BAR_INTERVAL_SECONDS = materializer.BAR_INTERVAL_SECONDS
REQUIRED_PRICE_OBSERVATIONS = contract.WARMUP_REQUIRED_PRICE_COUNT

# Soft retention: keep enough contiguous PT1M bars for the estimator window.
MAX_RETAINED_RECORDS = REQUIRED_PRICE_OBSERVATIONS * 2


class RuntimeMarkHistoryError(ValueError):
    """Fail-closed runtime mark-history host / persistence error."""


@dataclass(frozen=True)
class RuntimeMarkHistoryRecordV1:
    """One accepted distinct finalized PT1M mark_price observation."""

    venue: str
    canonical_instrument_id: str
    venue_instrument_id: str
    event_time: EventTimeInstantV1
    mark_price: float
    is_final: bool
    sample_digest: str
    receive_time: Optional[float] = None
    market_sample_identity: Optional[MarketSampleIdentityV1] = None

    def __post_init__(self) -> None:
        if not self.is_final:
            raise RuntimeMarkHistoryError("UNFINALIZED_MARK_HISTORY_RECORD")
        if not math.isfinite(self.mark_price) or self.mark_price <= 0.0:
            raise RuntimeMarkHistoryError("INVALID_MARK_PRICE_IN_HISTORY_RECORD")
        if self.market_sample_identity is None:
            object.__setattr__(
                self,
                "market_sample_identity",
                MarketSampleIdentityV1(
                    venue=self.venue,
                    canonical_instrument_id=self.canonical_instrument_id,
                    venue_instrument_id=self.venue_instrument_id,
                    event_time=self.event_time,
                    mark_price=self.mark_price,
                ),
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "venue": self.venue,
            "canonical_instrument_id": self.canonical_instrument_id,
            "venue_instrument_id": self.venue_instrument_id,
            "event_time": self.event_time.to_dict(),
            "mark_price": self.mark_price,
            "is_final": self.is_final,
            "sample_digest": self.sample_digest,
            "receive_time": self.receive_time,
            "market_sample_identity": (
                None
                if self.market_sample_identity is None
                else self.market_sample_identity.to_dict()
            ),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "RuntimeMarkHistoryRecordV1":
        identity_payload = payload.get("market_sample_identity")
        return cls(
            venue=str(payload["venue"]),
            canonical_instrument_id=str(payload["canonical_instrument_id"]),
            venue_instrument_id=str(payload["venue_instrument_id"]),
            event_time=EventTimeInstantV1.from_dict(payload["event_time"]),
            mark_price=float(payload["mark_price"]),
            is_final=bool(payload["is_final"]),
            sample_digest=str(payload["sample_digest"]),
            receive_time=(
                None if payload.get("receive_time") is None else float(payload["receive_time"])
            ),
            market_sample_identity=(
                None
                if identity_payload is None
                else MarketSampleIdentityV1.from_dict(identity_payload)
            ),
        )


def compute_sample_digest_v1(sample: MarketSampleIdentityV1) -> str:
    """Deterministic digest over canonical market-sample identity fields."""
    return deterministic_time_object_fingerprint_v1(sample.to_dict())


def compute_history_digest_v1(records: Sequence[RuntimeMarkHistoryRecordV1]) -> str:
    payload = {
        "owner": HISTORY_OWNER,
        "schema_version": HISTORY_SCHEMA_VERSION,
        "records": [record.to_dict() for record in records],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _assert_record_instrument_coherence(
    *,
    bound: InstrumentObservationKeyV1,
    record: RuntimeMarkHistoryRecordV1,
) -> None:
    key = InstrumentObservationKeyV1(
        venue=record.venue,
        canonical_instrument_id=record.canonical_instrument_id,
        venue_instrument_id=record.venue_instrument_id,
    )
    if key != bound:
        raise RuntimeMarkHistoryError(
            "HISTORY_INSTRUMENT_IDENTITY_MISMATCH:"
            f"bound={bound.to_dict()!r}:record={key.to_dict()!r}"
        )


def assert_pt1m_trailing_window_contiguous_v1(
    records: Sequence[RuntimeMarkHistoryRecordV1],
) -> None:
    """Fail-closed PT1M contiguity guard (reuse materializer interval semantics)."""
    if len(records) <= 1:
        return
    times = [r.event_time.unix_seconds for r in records]
    for prev, cur in zip(times, times[1:]):
        delta = cur - prev
        if not math.isfinite(delta) or delta <= 0.0:
            raise RuntimeMarkHistoryError("HISTORY_EVENT_TIME_NOT_STRICTLY_INCREASING")
        if delta > float(BAR_INTERVAL_SECONDS):
            raise RuntimeMarkHistoryError("HISTORY_GAP_EXCEEDS_PT1M")


@dataclass
class CanonicalVolatilityRuntimeMarkHistoryHostV1:
    """Ordered PT1M mark history for one venue/instrument binding.

    Polling / runtime cycles do not synthesize samples. Only distinct accepted
    samples from the existing sample authority advance history.
    """

    venue: str
    canonical_instrument_id: str
    venue_instrument_id: str
    _records: list[RuntimeMarkHistoryRecordV1]
    _acceptance_state: ObservationAcceptanceStateV1
    _history_digest: str

    @classmethod
    def create(
        cls,
        *,
        venue: str,
        canonical_instrument_id: str,
        venue_instrument_id: str,
    ) -> "CanonicalVolatilityRuntimeMarkHistoryHostV1":
        bound = InstrumentObservationKeyV1(
            venue=venue.strip(),
            canonical_instrument_id=canonical_instrument_id.strip(),
            venue_instrument_id=venue_instrument_id.strip(),
        )
        return cls(
            venue=bound.venue,
            canonical_instrument_id=bound.canonical_instrument_id,
            venue_instrument_id=bound.venue_instrument_id,
            _records=[],
            _acceptance_state=initial_market_sample_acceptance_state_v1(bound_instrument_key=bound),
            _history_digest=compute_history_digest_v1(()),
        )

    @property
    def bound_instrument_key(self) -> InstrumentObservationKeyV1:
        return InstrumentObservationKeyV1(
            venue=self.venue,
            canonical_instrument_id=self.canonical_instrument_id,
            venue_instrument_id=self.venue_instrument_id,
        )

    @property
    def records(self) -> tuple[RuntimeMarkHistoryRecordV1, ...]:
        return tuple(self._records)

    @property
    def observation_count_prices(self) -> int:
        return len(self._records)

    @property
    def history_digest(self) -> str:
        return self._history_digest

    @property
    def acceptance_state(self) -> ObservationAcceptanceStateV1:
        return self._acceptance_state

    @property
    def last_accepted_event_time(self) -> Optional[EventTimeInstantV1]:
        if not self._records:
            return None
        return self._records[-1].event_time

    def mark_price_series_v1(self) -> pd.Series:
        if not self._records:
            return pd.Series(dtype=float)
        index = pd.to_datetime(
            [r.event_time.unix_seconds for r in self._records],
            unit="s",
            utc=True,
        )
        values = [r.mark_price for r in self._records]
        return pd.Series(values, index=index, name=contract.PRICE_FIELD, dtype=float)

    def trailing_window_records_v1(
        self, *, count: int = REQUIRED_PRICE_OBSERVATIONS
    ) -> tuple[RuntimeMarkHistoryRecordV1, ...]:
        if count <= 0:
            raise RuntimeMarkHistoryError("INVALID_TRAILING_WINDOW_COUNT")
        if len(self._records) < count:
            return tuple(self._records)
        return tuple(self._records[-count:])

    def try_advance_with_sample_v1(
        self,
        sample: MarketSampleIdentityV1,
        *,
        is_final: bool = True,
        transport: Optional[ObservationTransportMetadataV1] = None,
    ) -> tuple[ObservationClassification, Optional[RuntimeMarkHistoryRecordV1]]:
        """Run existing sample authority; advance history only on DISTINCT + final."""
        bound = self.bound_instrument_key
        sample_key = sample.instrument_key()
        if sample_key != bound:
            raise RuntimeMarkHistoryError(
                "SAMPLE_INSTRUMENT_IDENTITY_MISMATCH:"
                f"bound={bound.to_dict()!r}:sample={sample_key.to_dict()!r}"
            )
        if not is_final:
            raise RuntimeMarkHistoryError("UNFINALIZED_SAMPLE_REJECTED")

        result, next_state = accept_distinct_market_sample_v1(
            current_state=self._acceptance_state,
            sample=sample,
            transport=transport,
        )
        classification = result.classification
        if classification is not ObservationClassification.DISTINCT:
            # Duplicate / out-of-order / invalid: sample authority already fail-closed;
            # history and observation_count must not change.
            return classification, None

        receive_time = None if transport is None else transport.receive_time
        record = RuntimeMarkHistoryRecordV1(
            venue=sample.venue,
            canonical_instrument_id=sample.canonical_instrument_id,
            venue_instrument_id=sample.venue_instrument_id,
            event_time=sample.event_time,
            mark_price=float(sample.mark_price),
            is_final=True,
            sample_digest=compute_sample_digest_v1(sample),
            receive_time=receive_time,
            market_sample_identity=sample,
        )
        _assert_record_instrument_coherence(bound=bound, record=record)

        if self._records:
            prev = self._records[-1].event_time.unix_seconds
            delta = sample.event_time.unix_seconds - prev
            if not math.isfinite(delta) or delta <= 0.0:
                # Should already be OUT_OF_ORDER via sample authority for <=0;
                # defend history integrity fail-closed.
                raise RuntimeMarkHistoryError("HISTORY_EVENT_TIME_NOT_STRICTLY_INCREASING")

        self._acceptance_state = next_state
        self._records.append(record)
        if len(self._records) > MAX_RETAINED_RECORDS:
            self._records = self._records[-MAX_RETAINED_RECORDS:]
        self._history_digest = compute_history_digest_v1(self._records)
        return classification, record

    def to_persistence_dict_v1(self) -> dict[str, Any]:
        return {
            "schema_version": HISTORY_SCHEMA_VERSION,
            "capability_id": CAPABILITY_ID,
            "owner": HISTORY_OWNER,
            "venue": self.venue,
            "canonical_instrument_id": self.canonical_instrument_id,
            "venue_instrument_id": self.venue_instrument_id,
            "records": [r.to_dict() for r in self._records],
            "acceptance_state": self._acceptance_state.to_dict(),
            "history_digest": self._history_digest,
            "last_accepted_event_time": (
                None
                if self.last_accepted_event_time is None
                else self.last_accepted_event_time.to_dict()
            ),
            "bar_interval_seconds": BAR_INTERVAL_SECONDS,
        }

    @classmethod
    def from_persistence_dict_v1(
        cls, payload: Mapping[str, Any]
    ) -> "CanonicalVolatilityRuntimeMarkHistoryHostV1":
        schema = str(payload.get("schema_version", ""))
        if schema != HISTORY_SCHEMA_VERSION:
            raise RuntimeMarkHistoryError(f"INCOMPATIBLE_HISTORY_SCHEMA_VERSION:{schema}")
        capability = str(payload.get("capability_id", ""))
        if capability != CAPABILITY_ID:
            raise RuntimeMarkHistoryError(f"INCOMPATIBLE_HISTORY_CAPABILITY_ID:{capability}")
        owner = str(payload.get("owner", ""))
        if owner != HISTORY_OWNER:
            raise RuntimeMarkHistoryError(f"INCOMPATIBLE_HISTORY_OWNER:{owner}")

        required = (
            "venue",
            "canonical_instrument_id",
            "venue_instrument_id",
            "records",
            "acceptance_state",
            "history_digest",
        )
        for key in required:
            if key not in payload:
                raise RuntimeMarkHistoryError(f"INCOMPLETE_HISTORY_PERSISTENCE:{key}")

        venue = str(payload["venue"])
        canonical = str(payload["canonical_instrument_id"])
        venue_inst = str(payload["venue_instrument_id"])
        records_raw = payload["records"]
        if not isinstance(records_raw, list):
            raise RuntimeMarkHistoryError("CORRUPT_HISTORY_RECORDS_TYPE")

        host = cls.create(
            venue=venue,
            canonical_instrument_id=canonical,
            venue_instrument_id=venue_inst,
        )
        records: list[RuntimeMarkHistoryRecordV1] = []
        for item in records_raw:
            if not isinstance(item, Mapping):
                raise RuntimeMarkHistoryError("CORRUPT_HISTORY_RECORD_TYPE")
            record = RuntimeMarkHistoryRecordV1.from_dict(item)
            _assert_record_instrument_coherence(bound=host.bound_instrument_key, record=record)
            records.append(record)

        # Event-time order + no invented fill.
        for prev, cur in zip(records, records[1:]):
            if cur.event_time.unix_seconds <= prev.event_time.unix_seconds:
                raise RuntimeMarkHistoryError("CORRUPT_HISTORY_EVENT_TIME_ORDER")

        digest = compute_history_digest_v1(records)
        stored_digest = str(payload["history_digest"])
        if digest != stored_digest:
            raise RuntimeMarkHistoryError("CORRUPT_HISTORY_DIGEST_MISMATCH")

        host._records = records
        host._acceptance_state = ObservationAcceptanceStateV1.from_dict(payload["acceptance_state"])
        host._history_digest = digest
        return host


def atomic_write_history_persistence_v1(
    *,
    path: Path,
    host: CanonicalVolatilityRuntimeMarkHistoryHostV1,
) -> None:
    """Atomic fail-closed persistence (temp + fsync + replace)."""
    payload = host.to_persistence_dict_v1()
    text = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(str(tmp), flags, 0o644)
    try:
        os.write(fd, text.encode("utf-8"))
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)


def load_history_persistence_v1(path: Path) -> CanonicalVolatilityRuntimeMarkHistoryHostV1:
    if not path.exists():
        raise RuntimeMarkHistoryError(f"HISTORY_PERSISTENCE_MISSING:{path}")
    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeError) as exc:
        raise RuntimeMarkHistoryError(f"CORRUPT_HISTORY_PERSISTENCE:{exc}") from exc
    if not isinstance(payload, Mapping):
        raise RuntimeMarkHistoryError("CORRUPT_HISTORY_PERSISTENCE_ROOT_TYPE")
    return CanonicalVolatilityRuntimeMarkHistoryHostV1.from_persistence_dict_v1(payload)


__all__ = [
    "BAR_INTERVAL_SECONDS",
    "CAPABILITY_ID",
    "CanonicalVolatilityRuntimeMarkHistoryHostV1",
    "HISTORY_OWNER",
    "HISTORY_SCHEMA_VERSION",
    "MAX_RETAINED_RECORDS",
    "REQUIRED_PRICE_OBSERVATIONS",
    "RuntimeMarkHistoryError",
    "RuntimeMarkHistoryRecordV1",
    "assert_pt1m_trailing_window_contiguous_v1",
    "atomic_write_history_persistence_v1",
    "compute_history_digest_v1",
    "compute_sample_digest_v1",
    "load_history_persistence_v1",
]
