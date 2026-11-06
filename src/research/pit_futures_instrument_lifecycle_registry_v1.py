"""Historical PIT futures instrument lifecycle registry v1 — Slice A contracts and pure core.

Research-only, non-authorizing. No I/O, no network, no clock, no runtime authority.
Provides immutable contracts, deterministic normalization, PIT query resolution,
digest computation, and LifecycleRegistryErrorCode taxonomy (28 codes).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from src.research.instrument_id_canonicalization_v1 import (
    InstrumentIdCanonicalizationInputV1,
    canonicalize_instrument_id_v1,
)
from src.research.pit_futures_universe_manifest_v1 import (
    ContractType,
    compute_sha256_digest,
    is_valid_digest,
    is_valid_rfc3339_utc,
)

PACKAGE_MARKER = "PIT_FUTURES_INSTRUMENT_LIFECYCLE_REGISTRY_V1=true"
INPUT_CONTRACT_VERSION = "pit_futures_instrument_lifecycle_registry_input.v1"
SCHEMA_NAME = "pit_futures_instrument_lifecycle_registry"
SCHEMA_VERSION = "v1"
REGISTRY_VERSION = "pit_futures_instrument_lifecycle_registry.v1"
SOURCE_PRIORITY_POLICY_VERSION = "source_priority_policy.v1"
CONFLICT_RESOLUTION_POLICY_VERSION = "conflict_resolution_policy.v1"
REFERENCE_PREFIX = "pit_futures_lifecycle_registry_v1"

_OPEN_INTERVAL_END = (99991231, 235959)

_PERPETUAL_TYPES = frozenset(
    {ContractType.LINEAR_PERPETUAL.value, ContractType.INVERSE_PERPETUAL.value}
)
_DATED_TYPES = frozenset(
    {ContractType.LINEAR_DATED_FUTURE.value, ContractType.INVERSE_DATED_FUTURE.value}
)
_FUTURES_MARKET_TYPES = frozenset({"futures", "futures_panel", "future", "perpetual"})
_VENUE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_ABSOLUTE_PATH_PATTERN = re.compile(r"(^/|^\\\\|^[A-Za-z]:[/\\\\])")
OKX_PRODUCTION_INSTRUMENT_LIFECYCLE_HISTORICAL_AS_OF_FAIL_CLOSED_V1 = (
    "okx_production_instrument_lifecycle_historical_as_of_fail_closed.v1"
)
_REGISTERED_SOURCES_V0 = frozenset(
    {
        "synthetic:test:fixture:v0",
        "synthetic:test:record:v0",
        OKX_PRODUCTION_INSTRUMENT_LIFECYCLE_HISTORICAL_AS_OF_FAIL_CLOSED_V1,
    }
)


class ObservationKind(str, Enum):
    LISTING = "LISTING"
    ELIGIBILITY = "ELIGIBILITY"
    DELISTING = "DELISTING"
    EXPIRY = "EXPIRY"
    SUSPENSION_START = "SUSPENSION_START"
    SUSPENSION_END = "SUSPENSION_END"
    CORRECTION = "CORRECTION"
    RELISTING = "RELISTING"


class QueryState(str, Enum):
    NOT_LISTED = "NOT_LISTED"
    LISTED_INELIGIBLE = "LISTED_INELIGIBLE"
    ELIGIBLE = "ELIGIBLE"
    SUSPENDED = "SUSPENDED"
    DELISTED = "DELISTED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


class SourceTrustLevel(str, Enum):
    TRUSTED = "TRUSTED"
    UNTRUSTED = "UNTRUSTED"


class LifecycleRegistryErrorCode(str, Enum):
    INVALID_INPUT_CONTRACT = "INVALID_INPUT_CONTRACT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_VENUE_ID = "INVALID_VENUE_ID"
    INVALID_INSTRUMENT_TYPE = "INVALID_INSTRUMENT_TYPE"
    NON_FUTURES_INSTRUMENT = "NON_FUTURES_INSTRUMENT"
    BITCOIN_DIRECTION_PROHIBITED = "BITCOIN_DIRECTION_PROHIBITED"
    SPOT_INSTRUMENT_BLOCKED = "SPOT_INSTRUMENT_BLOCKED"
    SYNTHETIC_SPOT_BLOCKED = "SYNTHETIC_SPOT_BLOCKED"
    INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
    AMBIGUOUS_EFFECTIVE_TIME = "AMBIGUOUS_EFFECTIVE_TIME"
    CONFLICTING_SOURCE_RECORDS = "CONFLICTING_SOURCE_RECORDS"
    UNKNOWN_SOURCE = "UNKNOWN_SOURCE"
    UNTRUSTED_SOURCE = "UNTRUSTED_SOURCE"
    DUPLICATE_EVENT = "DUPLICATE_EVENT"
    DUPLICATE_CANONICAL_INSTRUMENT_ID = "DUPLICATE_CANONICAL_INSTRUMENT_ID"
    OVERLAPPING_LIFECYCLE_INTERVALS = "OVERLAPPING_LIFECYCLE_INTERVALS"
    INVALID_TRANSITION = "INVALID_TRANSITION"
    OUT_OF_ORDER_EVENT = "OUT_OF_ORDER_EVENT"
    UNKNOWN_LIFECYCLE_STATE = "UNKNOWN_LIFECYCLE_STATE"
    STALE_SOURCE_SNAPSHOT = "STALE_SOURCE_SNAPSHOT"
    DIGEST_MISMATCH = "DIGEST_MISMATCH"
    POLICY_MISMATCH = "POLICY_MISMATCH"
    VALIDATOR_REJECTION = "VALIDATOR_REJECTION"
    PERSISTENCE_BEFORE_VALIDATION = "PERSISTENCE_BEFORE_VALIDATION"
    RETROACTIVE_CORRECTION_WITHOUT_PROVENANCE = "RETROACTIVE_CORRECTION_WITHOUT_PROVENANCE"
    INVALID_CONTRACT_TYPE = "INVALID_CONTRACT_TYPE"
    MISSING_EXPIRY_FOR_DATED_FUTURE = "MISSING_EXPIRY_FOR_DATED_FUTURE"
    INVALID_SOURCE_REFERENCE = "INVALID_SOURCE_REFERENCE"


@dataclass(frozen=True)
class SuspensionSubIntervalV1:
    suspension_start: str
    suspension_end: str


@dataclass(frozen=True)
class SourceObservationRecordV1:
    input_contract_version: str
    source_id: str
    source_trust_level: str
    source_priority: int
    source_snapshot_ref: str
    source_snapshot_digest: str
    source_observed_at: str
    source_effective_at: str
    venue_id: str
    venue_timezone: str
    market_type: str
    contract_type: str
    base_asset: str
    quote_asset: str
    settlement_asset: str
    observation_kind: str
    observation_digest: str
    venue_symbol: str | None = None
    native_instrument_id: str | None = None
    contract_expiry: str | None = None
    listing_time: str | None = None
    eligible_from: str | None = None
    delisting_time: str | None = None
    eligible_until: str | None = None
    expiry_time: str | None = None
    correction_provenance_ref: str | None = None


@dataclass(frozen=True)
class NormalizedLifecycleObservationV1:
    input_contract_version: str
    source_id: str
    source_trust_level: str
    source_priority: int
    source_snapshot_ref: str
    source_snapshot_digest: str
    source_observed_at: str
    source_effective_at: str
    venue_id: str
    venue_timezone: str
    market_type: str
    contract_type: str
    base_asset: str
    quote_asset: str
    settlement_asset: str
    observation_kind: str
    observation_digest: str
    instrument_id: str
    venue_symbol: str | None = None
    native_instrument_id: str | None = None
    contract_expiry: str | None = None
    listing_time: str | None = None
    eligible_from: str | None = None
    delisting_time: str | None = None
    eligible_until: str | None = None
    expiry_time: str | None = None
    correction_provenance_ref: str | None = None


@dataclass(frozen=True)
class InstrumentLifecycleIntervalV1:
    instrument_id: str
    venue_id: str
    contract_type: str
    base_asset: str
    quote_asset: str
    settlement_asset: str
    listing_time: str
    eligible_from: str
    interval_sequence: int
    registry_record_version: int
    record_digest: str
    venue_symbol: str | None = None
    native_instrument_id: str | None = None
    contract_expiry: str | None = None
    delisting_time: str | None = None
    eligible_until: str | None = None
    expiry_time: str | None = None
    suspension_sub_intervals: tuple[SuspensionSubIntervalV1, ...] = ()
    source_snapshot_refs: tuple[str, ...] = ()
    source_digests: tuple[str, ...] = ()
    superseded_by_version: int | None = None
    correction_provenance_ref: str | None = None


@dataclass(frozen=True)
class RegistrySnapshotV1:
    schema_name: str
    schema_version: str
    registry_snapshot_version: int
    policy_version: str
    source_priority_policy_version: str
    conflict_resolution_policy_version: str
    venue_scope: tuple[str, ...]
    generated_at: str
    intervals: tuple[InstrumentLifecycleIntervalV1, ...]
    config_digest: str
    implementation_digest: str
    registry_snapshot_digest: str


@dataclass(frozen=True)
class RegistryReferenceV1:
    schema_prefix: str
    artifact_id: str
    digest_algorithm: str
    registry_snapshot_digest: str


@dataclass(frozen=True)
class LifecycleQueryResultV1:
    query_state: str
    instrument_id: str
    query_instant: str
    registry_snapshot_version: int
    registry_snapshot_digest: str
    interval: InstrumentLifecycleIntervalV1 | None = None
    error_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class NormalizationResultV1:
    success: bool
    observation: NormalizedLifecycleObservationV1 | None
    error_codes: tuple[str, ...]


@dataclass(frozen=True)
class ObservationConflictResultV1:
    has_conflict: bool
    error_codes: tuple[str, ...]
    deduplicated: tuple[NormalizedLifecycleObservationV1, ...]


@dataclass(frozen=True)
class TransitionValidationResultV1:
    valid: bool
    error_codes: tuple[str, ...]


@dataclass(frozen=True)
class CorrectionVersionResultV1:
    success: bool
    snapshot: RegistrySnapshotV1 | None
    error_codes: tuple[str, ...]


@dataclass(frozen=True)
class AssemblyIssueV1:
    error_code: str
    instrument_id: str | None = None
    record_ref: str | None = None
    field_path: str | None = None


@dataclass(frozen=True)
class RegistryAssemblyResultV1:
    success: bool
    snapshot: RegistrySnapshotV1 | None
    error_codes: tuple[str, ...]
    issues: tuple[AssemblyIssueV1, ...] = ()


def _add(errors: list[str], code: LifecycleRegistryErrorCode) -> None:
    value = code.value
    if value not in errors:
        errors.append(value)


def parse_utc_instant(value: str) -> tuple[int, int] | None:
    if not is_valid_rfc3339_utc(value):
        return None
    date_part, time_part = value.split("T", 1)
    year, month, day = (int(part) for part in date_part.split("-"))
    hour = int(time_part[0:2])
    minute = int(time_part[3:5])
    second = int(time_part[6:8])
    return (year * 10_000 + month * 100 + day, hour * 10_000 + minute * 100 + second)


def _validate_source_ref(value: str, errors: list[str]) -> bool:
    if not value.strip():
        _add(errors, LifecycleRegistryErrorCode.INVALID_SOURCE_REFERENCE)
        return False
    if _ABSOLUTE_PATH_PATTERN.search(value):
        _add(errors, LifecycleRegistryErrorCode.INVALID_SOURCE_REFERENCE)
        return False
    return True


def _validate_timestamp(value: str | None, errors: list[str], *, required: bool) -> bool:
    if value is None:
        if required:
            _add(errors, LifecycleRegistryErrorCode.MISSING_REQUIRED_FIELD)
        return not required
    if not is_valid_rfc3339_utc(value):
        _add(errors, LifecycleRegistryErrorCode.INVALID_TIMESTAMP)
        return False
    return True


def _classify_market_errors(market_type: str, contract_type: str, errors: list[str]) -> bool:
    mt = market_type.strip().lower()
    if mt == "spot":
        _add(errors, LifecycleRegistryErrorCode.SPOT_INSTRUMENT_BLOCKED)
        return True
    if mt in {"synthetic_spot", "synthetic-spot"}:
        _add(errors, LifecycleRegistryErrorCode.SYNTHETIC_SPOT_BLOCKED)
        return True
    if mt not in _FUTURES_MARKET_TYPES:
        _add(errors, LifecycleRegistryErrorCode.NON_FUTURES_INSTRUMENT)
        return True
    ct = contract_type.strip().lower()
    if ct not in {item.value for item in ContractType}:
        _add(errors, LifecycleRegistryErrorCode.INVALID_CONTRACT_TYPE)
        return True
    return False


def observation_semantic_payload(
    obs: SourceObservationRecordV1 | NormalizedLifecycleObservationV1,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "base_asset": obs.base_asset.strip().upper(),
        "contract_expiry": obs.contract_expiry,
        "contract_type": obs.contract_type.strip().lower(),
        "correction_provenance_ref": obs.correction_provenance_ref,
        "delisting_time": obs.delisting_time,
        "eligible_from": obs.eligible_from,
        "eligible_until": obs.eligible_until,
        "expiry_time": obs.expiry_time,
        "listing_time": obs.listing_time,
        "market_type": obs.market_type.strip().lower(),
        "native_instrument_id": obs.native_instrument_id,
        "observation_kind": obs.observation_kind.strip().upper(),
        "quote_asset": obs.quote_asset.strip().upper(),
        "settlement_asset": obs.settlement_asset.strip().upper(),
        "source_effective_at": obs.source_effective_at,
        "source_id": obs.source_id.strip(),
        "source_observed_at": obs.source_observed_at,
        "source_priority": obs.source_priority,
        "source_snapshot_digest": obs.source_snapshot_digest.strip().lower(),
        "source_snapshot_ref": obs.source_snapshot_ref.strip(),
        "venue_id": obs.venue_id.strip().lower(),
        "venue_symbol": obs.venue_symbol,
        "venue_timezone": obs.venue_timezone.strip(),
    }
    if isinstance(obs, NormalizedLifecycleObservationV1):
        payload["instrument_id"] = obs.instrument_id
    return payload


def compute_observation_digest(
    obs: SourceObservationRecordV1 | NormalizedLifecycleObservationV1,
) -> str:
    return compute_sha256_digest(observation_semantic_payload(obs))


def _interval_to_dict(
    interval: InstrumentLifecycleIntervalV1, *, include_digest: bool
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "base_asset": interval.base_asset,
        "contract_expiry": interval.contract_expiry,
        "contract_type": interval.contract_type,
        "correction_provenance_ref": interval.correction_provenance_ref,
        "delisting_time": interval.delisting_time,
        "eligible_from": interval.eligible_from,
        "eligible_until": interval.eligible_until,
        "expiry_time": interval.expiry_time,
        "instrument_id": interval.instrument_id,
        "interval_sequence": interval.interval_sequence,
        "listing_time": interval.listing_time,
        "native_instrument_id": interval.native_instrument_id,
        "quote_asset": interval.quote_asset,
        "registry_record_version": interval.registry_record_version,
        "settlement_asset": interval.settlement_asset,
        "source_digests": list(interval.source_digests),
        "source_snapshot_refs": list(interval.source_snapshot_refs),
        "suspension_sub_intervals": [
            {"suspension_end": item.suspension_end, "suspension_start": item.suspension_start}
            for item in interval.suspension_sub_intervals
        ],
        "superseded_by_version": interval.superseded_by_version,
        "venue_id": interval.venue_id,
        "venue_symbol": interval.venue_symbol,
    }
    if include_digest:
        payload["record_digest"] = interval.record_digest
    return {k: v for k, v in payload.items() if v is not None}


def compute_interval_digest(interval: InstrumentLifecycleIntervalV1) -> str:
    return compute_sha256_digest(_interval_to_dict(interval, include_digest=False))


def compute_registry_snapshot_digest(snapshot: RegistrySnapshotV1) -> str:
    payload: dict[str, Any] = {
        "config_digest": snapshot.config_digest.strip().lower(),
        "conflict_resolution_policy_version": snapshot.conflict_resolution_policy_version,
        "generated_at": snapshot.generated_at,
        "implementation_digest": snapshot.implementation_digest.strip().lower(),
        "intervals": [
            interval.record_digest.strip().lower()
            for interval in sorted(
                snapshot.intervals,
                key=lambda item: (item.instrument_id, item.interval_sequence),
            )
        ],
        "policy_version": snapshot.policy_version,
        "registry_snapshot_version": snapshot.registry_snapshot_version,
        "schema_name": snapshot.schema_name,
        "schema_version": snapshot.schema_version,
        "source_priority_policy_version": snapshot.source_priority_policy_version,
        "venue_scope": list(snapshot.venue_scope),
    }
    return compute_sha256_digest(payload)


def attach_snapshot_digest(snapshot: RegistrySnapshotV1) -> RegistrySnapshotV1:
    intervals = tuple(
        _attach_interval_digest(interval)
        for interval in sorted(
            snapshot.intervals, key=lambda i: (i.instrument_id, i.interval_sequence)
        )
    )
    interim = RegistrySnapshotV1(
        schema_name=snapshot.schema_name,
        schema_version=snapshot.schema_version,
        registry_snapshot_version=snapshot.registry_snapshot_version,
        policy_version=snapshot.policy_version,
        source_priority_policy_version=snapshot.source_priority_policy_version,
        conflict_resolution_policy_version=snapshot.conflict_resolution_policy_version,
        venue_scope=tuple(sorted(snapshot.venue_scope)),
        generated_at=snapshot.generated_at,
        intervals=intervals,
        config_digest=snapshot.config_digest.strip().lower(),
        implementation_digest=snapshot.implementation_digest.strip().lower(),
        registry_snapshot_digest="0" * 64,
    )
    digest = compute_registry_snapshot_digest(interim)
    return RegistrySnapshotV1(
        schema_name=interim.schema_name,
        schema_version=interim.schema_version,
        registry_snapshot_version=interim.registry_snapshot_version,
        policy_version=interim.policy_version,
        source_priority_policy_version=interim.source_priority_policy_version,
        conflict_resolution_policy_version=interim.conflict_resolution_policy_version,
        venue_scope=interim.venue_scope,
        generated_at=interim.generated_at,
        intervals=interim.intervals,
        config_digest=interim.config_digest,
        implementation_digest=interim.implementation_digest,
        registry_snapshot_digest=digest,
    )


def _attach_interval_digest(
    interval: InstrumentLifecycleIntervalV1,
) -> InstrumentLifecycleIntervalV1:
    digest = compute_interval_digest(interval)
    return InstrumentLifecycleIntervalV1(
        instrument_id=interval.instrument_id,
        venue_id=interval.venue_id,
        contract_type=interval.contract_type,
        base_asset=interval.base_asset,
        quote_asset=interval.quote_asset,
        settlement_asset=interval.settlement_asset,
        listing_time=interval.listing_time,
        eligible_from=interval.eligible_from,
        interval_sequence=interval.interval_sequence,
        registry_record_version=interval.registry_record_version,
        record_digest=digest,
        venue_symbol=interval.venue_symbol,
        native_instrument_id=interval.native_instrument_id,
        contract_expiry=interval.contract_expiry,
        delisting_time=interval.delisting_time,
        eligible_until=interval.eligible_until,
        expiry_time=interval.expiry_time,
        suspension_sub_intervals=interval.suspension_sub_intervals,
        source_snapshot_refs=tuple(sorted(set(interval.source_snapshot_refs))),
        source_digests=tuple(sorted(d.strip().lower() for d in interval.source_digests)),
        superseded_by_version=interval.superseded_by_version,
        correction_provenance_ref=interval.correction_provenance_ref,
    )


def observation_sort_key(obs: NormalizedLifecycleObservationV1) -> tuple[Any, ...]:
    return (
        obs.source_effective_at,
        obs.source_priority,
        obs.source_observed_at,
        obs.source_id,
        obs.observation_digest,
    )


def sort_normalized_observations(
    observations: Sequence[NormalizedLifecycleObservationV1],
) -> tuple[NormalizedLifecycleObservationV1, ...]:
    return tuple(sorted(observations, key=observation_sort_key))


def observation_identity_key(obs: NormalizedLifecycleObservationV1) -> tuple[Any, ...]:
    return (
        obs.instrument_id,
        obs.observation_kind.strip().upper(),
        obs.source_effective_at,
        compute_observation_digest(obs),
    )


def observation_conflict_key(obs: NormalizedLifecycleObservationV1) -> tuple[Any, ...]:
    return (
        obs.instrument_id,
        obs.observation_kind.strip().upper(),
        obs.source_effective_at,
    )


def normalize_source_observation_record_v1(
    record: SourceObservationRecordV1,
    *,
    registered_sources: frozenset[str] | None = None,
    approved_snapshot_digests: frozenset[str] | None = None,
) -> NormalizationResultV1:
    errors: list[str] = []
    sources = registered_sources if registered_sources is not None else _REGISTERED_SOURCES_V0

    if record.input_contract_version != INPUT_CONTRACT_VERSION:
        _add(errors, LifecycleRegistryErrorCode.INVALID_INPUT_CONTRACT)

    if not record.source_id.strip():
        _add(errors, LifecycleRegistryErrorCode.MISSING_REQUIRED_FIELD)
    elif record.source_id.strip() not in sources:
        _add(errors, LifecycleRegistryErrorCode.UNKNOWN_SOURCE)

    trust = record.source_trust_level.strip().upper()
    if trust != SourceTrustLevel.TRUSTED.value:
        _add(errors, LifecycleRegistryErrorCode.UNTRUSTED_SOURCE)

    venue_id = record.venue_id.strip().lower()
    if not venue_id or not _VENUE_ID_PATTERN.fullmatch(venue_id):
        _add(errors, LifecycleRegistryErrorCode.INVALID_VENUE_ID)

    if not record.venue_timezone.strip():
        _add(errors, LifecycleRegistryErrorCode.MISSING_REQUIRED_FIELD)

    if not _validate_source_ref(record.source_snapshot_ref, errors):
        pass
    if not is_valid_digest(record.source_snapshot_digest.strip().lower()):
        _add(errors, LifecycleRegistryErrorCode.DIGEST_MISMATCH)

    if approved_snapshot_digests is not None:
        if record.source_snapshot_digest.strip().lower() not in approved_snapshot_digests:
            _add(errors, LifecycleRegistryErrorCode.STALE_SOURCE_SNAPSHOT)

    _validate_timestamp(record.source_observed_at, errors, required=True)
    if not _validate_timestamp(record.source_effective_at, errors, required=True):
        pass
    elif parse_utc_instant(record.source_effective_at) is None:
        _add(errors, LifecycleRegistryErrorCode.AMBIGUOUS_EFFECTIVE_TIME)

    try:
        ObservationKind(record.observation_kind.strip().upper())
    except ValueError:
        _add(errors, LifecycleRegistryErrorCode.INVALID_INSTRUMENT_TYPE)

    if _classify_market_errors(record.market_type, record.contract_type, errors):
        return NormalizationResultV1(False, None, tuple(sorted(errors)))

    contract_type = record.contract_type.strip().lower()
    if contract_type in _PERPETUAL_TYPES:
        if record.expiry_time is not None or record.contract_expiry is not None:
            _add(errors, LifecycleRegistryErrorCode.INVALID_INSTRUMENT_TYPE)
    elif contract_type in _DATED_TYPES:
        if record.expiry_time is None or record.contract_expiry is None:
            _add(errors, LifecycleRegistryErrorCode.MISSING_EXPIRY_FOR_DATED_FUTURE)

    kind = record.observation_kind.strip().upper()
    if kind in {
        ObservationKind.LISTING.value,
        ObservationKind.RELISTING.value,
        ObservationKind.ELIGIBILITY.value,
    }:
        if record.listing_time is None:
            _add(errors, LifecycleRegistryErrorCode.MISSING_REQUIRED_FIELD)
        else:
            _validate_timestamp(record.listing_time, errors, required=True)
        if record.eligible_from is None:
            _add(errors, LifecycleRegistryErrorCode.MISSING_REQUIRED_FIELD)
        else:
            _validate_timestamp(record.eligible_from, errors, required=True)

    if record.delisting_time is not None:
        _validate_timestamp(record.delisting_time, errors, required=True)
    if record.eligible_until is not None:
        _validate_timestamp(record.eligible_until, errors, required=True)
    if record.expiry_time is not None:
        _validate_timestamp(record.expiry_time, errors, required=True)

    if kind == ObservationKind.CORRECTION.value and not record.correction_provenance_ref:
        _add(errors, LifecycleRegistryErrorCode.RETROACTIVE_CORRECTION_WITHOUT_PROVENANCE)
    elif record.correction_provenance_ref is not None:
        _validate_source_ref(record.correction_provenance_ref, errors)

    if errors:
        return NormalizationResultV1(False, None, tuple(sorted(errors)))

    canon = canonicalize_instrument_id_v1(
        InstrumentIdCanonicalizationInputV1(
            venue_id=venue_id,
            market_type=record.market_type.strip().lower(),
            contract_type=contract_type,
            base_asset=record.base_asset.strip(),
            quote_asset=record.quote_asset.strip(),
            settlement_asset=record.settlement_asset.strip(),
            venue_symbol=record.venue_symbol,
            native_instrument_id=record.native_instrument_id,
            contract_expiry=record.contract_expiry,
        )
    )
    if not canon.success or canon.instrument_id is None:
        for code in canon.error_codes:
            if code == "BITCOIN_DIRECTION_DISALLOWED":
                _add(errors, LifecycleRegistryErrorCode.BITCOIN_DIRECTION_PROHIBITED)
            elif code == "SPOT_MARKET":
                _add(errors, LifecycleRegistryErrorCode.SPOT_INSTRUMENT_BLOCKED)
            elif code == "SYNTHETIC_SPOT_MARKET":
                _add(errors, LifecycleRegistryErrorCode.SYNTHETIC_SPOT_BLOCKED)
            elif code == "NON_FUTURES_MARKET":
                _add(errors, LifecycleRegistryErrorCode.NON_FUTURES_INSTRUMENT)
            else:
                _add(errors, LifecycleRegistryErrorCode.INVALID_INSTRUMENT_TYPE)
        return NormalizationResultV1(False, None, tuple(sorted(errors)))

    expected_digest = compute_observation_digest(record)
    if expected_digest != record.observation_digest.strip().lower():
        _add(errors, LifecycleRegistryErrorCode.DIGEST_MISMATCH)
        return NormalizationResultV1(False, None, tuple(sorted(errors)))

    normalized = NormalizedLifecycleObservationV1(
        input_contract_version=record.input_contract_version,
        source_id=record.source_id.strip(),
        source_trust_level=trust,
        source_priority=record.source_priority,
        source_snapshot_ref=record.source_snapshot_ref.strip(),
        source_snapshot_digest=record.source_snapshot_digest.strip().lower(),
        source_observed_at=record.source_observed_at,
        source_effective_at=record.source_effective_at,
        venue_id=venue_id,
        venue_timezone=record.venue_timezone.strip(),
        market_type=record.market_type.strip().lower(),
        contract_type=contract_type,
        base_asset=record.base_asset.strip().upper(),
        quote_asset=record.quote_asset.strip().upper(),
        settlement_asset=record.settlement_asset.strip().upper(),
        observation_kind=kind,
        observation_digest=expected_digest,
        instrument_id=canon.instrument_id,
        venue_symbol=record.venue_symbol.strip() if record.venue_symbol else None,
        native_instrument_id=record.native_instrument_id,
        contract_expiry=record.contract_expiry,
        listing_time=record.listing_time,
        eligible_from=record.eligible_from,
        delisting_time=record.delisting_time,
        eligible_until=record.eligible_until,
        expiry_time=record.expiry_time,
        correction_provenance_ref=record.correction_provenance_ref,
    )
    return NormalizationResultV1(True, normalized, ())


def resolve_observation_conflicts_v1(
    observations: Sequence[NormalizedLifecycleObservationV1],
) -> ObservationConflictResultV1:
    errors: list[str] = []
    sorted_obs = sort_normalized_observations(observations)
    seen_identity: set[tuple[Any, ...]] = set()
    conflict_groups: dict[tuple[Any, ...], list[NormalizedLifecycleObservationV1]] = {}
    deduplicated: list[NormalizedLifecycleObservationV1] = []

    for obs in sorted_obs:
        identity = observation_identity_key(obs)
        if identity in seen_identity:
            continue
        conflict_key = observation_conflict_key(obs)
        conflict_groups.setdefault(conflict_key, []).append(obs)

    for key, group in conflict_groups.items():
        digests = {item.observation_digest for item in group}
        semantic = {compute_observation_digest(item) for item in group}
        if len(group) > 1 and len(digests) > 1 and len(semantic) > 1:
            priorities = {item.source_priority for item in group}
            if len(priorities) == 1:
                _add(errors, LifecycleRegistryErrorCode.CONFLICTING_SOURCE_RECORDS)
            else:
                winner = min(group, key=observation_sort_key)
                deduplicated.append(winner)
                seen_identity.add(observation_identity_key(winner))
            continue
        item = group[0]
        deduplicated.append(item)
        seen_identity.add(observation_identity_key(item))

    if errors:
        return ObservationConflictResultV1(True, tuple(sorted(errors)), ())
    return ObservationConflictResultV1(False, (), tuple(sort_normalized_observations(deduplicated)))


def _is_in_suspension(interval: InstrumentLifecycleIntervalV1, instant: tuple[int, int]) -> bool:
    for sub in interval.suspension_sub_intervals:
        start = parse_utc_instant(sub.suspension_start)
        end = parse_utc_instant(sub.suspension_end)
        if start is None or end is None:
            continue
        if start <= instant < end:
            return True
    return False


def _exclusive_end_instant(interval: InstrumentLifecycleIntervalV1) -> tuple[int, int] | None:
    candidates: list[tuple[int, int]] = []
    for ts in (interval.delisting_time, interval.eligible_until, interval.expiry_time):
        if ts is None:
            continue
        parsed = parse_utc_instant(ts)
        if parsed is not None:
            candidates.append(parsed)
    if not candidates:
        return None
    return min(candidates)


def query_lifecycle_state_at_instant_v1(
    interval: InstrumentLifecycleIntervalV1,
    query_instant: str,
) -> QueryState:
    instant = parse_utc_instant(query_instant)
    if instant is None:
        return QueryState.UNKNOWN

    listing = parse_utc_instant(interval.listing_time)
    eligible_from = parse_utc_instant(interval.eligible_from)
    if listing is None or eligible_from is None:
        return QueryState.UNKNOWN

    if instant < listing:
        return QueryState.NOT_LISTED
    if instant < eligible_from:
        return QueryState.LISTED_INELIGIBLE

    if interval.delisting_time is not None:
        delist = parse_utc_instant(interval.delisting_time)
        if delist is not None and delist <= instant:
            return QueryState.DELISTED

    if interval.expiry_time is not None:
        expiry = parse_utc_instant(interval.expiry_time)
        if expiry is not None and expiry <= instant:
            return QueryState.EXPIRED

    if interval.eligible_until is not None:
        eligible_until = parse_utc_instant(interval.eligible_until)
        if eligible_until is not None and eligible_until <= instant:
            return QueryState.DELISTED

    end = _exclusive_end_instant(interval)
    if end is not None and instant >= end:
        if interval.expiry_time is not None:
            return QueryState.EXPIRED
        return QueryState.DELISTED

    if _is_in_suspension(interval, instant):
        return QueryState.SUSPENDED

    return QueryState.ELIGIBLE


def query_lifecycle_at_snapshot_v1(
    snapshot: RegistrySnapshotV1,
    *,
    instrument_id: str,
    query_instant: str,
) -> LifecycleQueryResultV1:
    if parse_utc_instant(query_instant) is None:
        return LifecycleQueryResultV1(
            query_state=QueryState.UNKNOWN.value,
            instrument_id=instrument_id,
            query_instant=query_instant,
            registry_snapshot_version=snapshot.registry_snapshot_version,
            registry_snapshot_digest=snapshot.registry_snapshot_digest,
            error_codes=(LifecycleRegistryErrorCode.INVALID_TIMESTAMP.value,),
        )

    active_intervals = [
        item
        for item in snapshot.intervals
        if item.instrument_id == instrument_id and item.superseded_by_version is None
    ]
    if not active_intervals:
        return LifecycleQueryResultV1(
            query_state=QueryState.UNKNOWN.value,
            instrument_id=instrument_id,
            query_instant=query_instant,
            registry_snapshot_version=snapshot.registry_snapshot_version,
            registry_snapshot_digest=snapshot.registry_snapshot_digest,
            error_codes=(LifecycleRegistryErrorCode.UNKNOWN_LIFECYCLE_STATE.value,),
        )

    chosen = max(active_intervals, key=lambda i: i.interval_sequence)
    state = query_lifecycle_state_at_instant_v1(chosen, query_instant)
    return LifecycleQueryResultV1(
        query_state=state.value,
        instrument_id=instrument_id,
        query_instant=query_instant,
        registry_snapshot_version=snapshot.registry_snapshot_version,
        registry_snapshot_digest=snapshot.registry_snapshot_digest,
        interval=chosen,
    )


_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    ObservationKind.LISTING.value: frozenset({ObservationKind.ELIGIBILITY.value}),
    ObservationKind.ELIGIBILITY.value: frozenset(
        {
            ObservationKind.SUSPENSION_START.value,
            ObservationKind.DELISTING.value,
            ObservationKind.EXPIRY.value,
            ObservationKind.CORRECTION.value,
        }
    ),
    ObservationKind.SUSPENSION_START.value: frozenset({ObservationKind.SUSPENSION_END.value}),
    ObservationKind.SUSPENSION_END.value: frozenset(
        {
            ObservationKind.SUSPENSION_START.value,
            ObservationKind.DELISTING.value,
            ObservationKind.EXPIRY.value,
        }
    ),
    ObservationKind.DELISTING.value: frozenset(
        {ObservationKind.RELISTING.value, ObservationKind.CORRECTION.value}
    ),
    ObservationKind.EXPIRY.value: frozenset(
        {ObservationKind.RELISTING.value, ObservationKind.CORRECTION.value}
    ),
    ObservationKind.RELISTING.value: frozenset({ObservationKind.ELIGIBILITY.value}),
    ObservationKind.CORRECTION.value: frozenset({kind.value for kind in ObservationKind}),
}


def validate_observation_transition_v1(
    prior_kind: str | None,
    next_kind: str,
) -> TransitionValidationResultV1:
    errors: list[str] = []
    try:
        next_enum = ObservationKind(next_kind.strip().upper())
    except ValueError:
        _add(errors, LifecycleRegistryErrorCode.INVALID_TRANSITION)
        return TransitionValidationResultV1(False, tuple(errors))

    if (
        next_enum == ObservationKind.SUSPENSION_END
        and prior_kind != ObservationKind.SUSPENSION_START.value
    ):
        _add(errors, LifecycleRegistryErrorCode.INVALID_TRANSITION)
        return TransitionValidationResultV1(False, tuple(errors))

    if prior_kind is None:
        if next_enum not in {
            ObservationKind.LISTING,
            ObservationKind.RELISTING,
            ObservationKind.CORRECTION,
        }:
            _add(errors, LifecycleRegistryErrorCode.INVALID_TRANSITION)
        return TransitionValidationResultV1(not errors, tuple(errors))

    prior = prior_kind.strip().upper()
    allowed = _ALLOWED_TRANSITIONS.get(prior, frozenset())
    if next_enum.value not in allowed and next_enum != ObservationKind.CORRECTION:
        if next_enum == ObservationKind.RELISTING:
            if prior not in {ObservationKind.DELISTING.value, ObservationKind.EXPIRY.value}:
                _add(errors, LifecycleRegistryErrorCode.INVALID_TRANSITION)
        elif next_enum in {ObservationKind.LISTING, ObservationKind.ELIGIBILITY}:
            if prior in {ObservationKind.DELISTING.value, ObservationKind.EXPIRY.value}:
                _add(errors, LifecycleRegistryErrorCode.INVALID_TRANSITION)
        else:
            _add(errors, LifecycleRegistryErrorCode.INVALID_TRANSITION)

    return TransitionValidationResultV1(not errors, tuple(sorted(errors)))


def build_interval_from_observation_v1(
    obs: NormalizedLifecycleObservationV1,
    *,
    interval_sequence: int = 0,
    registry_record_version: int = 1,
    suspension_sub_intervals: tuple[SuspensionSubIntervalV1, ...] = (),
) -> InstrumentLifecycleIntervalV1 | None:
    if obs.listing_time is None or obs.eligible_from is None:
        return None
    interval = InstrumentLifecycleIntervalV1(
        instrument_id=obs.instrument_id,
        venue_id=obs.venue_id,
        contract_type=obs.contract_type,
        base_asset=obs.base_asset,
        quote_asset=obs.quote_asset,
        settlement_asset=obs.settlement_asset,
        listing_time=obs.listing_time,
        eligible_from=obs.eligible_from,
        interval_sequence=interval_sequence,
        registry_record_version=registry_record_version,
        record_digest="0" * 64,
        venue_symbol=obs.venue_symbol,
        native_instrument_id=obs.native_instrument_id,
        contract_expiry=obs.contract_expiry,
        delisting_time=obs.delisting_time,
        eligible_until=obs.eligible_until,
        expiry_time=obs.expiry_time,
        suspension_sub_intervals=suspension_sub_intervals,
        source_snapshot_refs=(obs.source_snapshot_ref,),
        source_digests=(obs.source_snapshot_digest,),
        correction_provenance_ref=obs.correction_provenance_ref,
    )
    return _attach_interval_digest(interval)


def create_correction_snapshot_version_v1(
    prior: RegistrySnapshotV1,
    *,
    corrected_interval: InstrumentLifecycleIntervalV1,
    correction_provenance_ref: str,
    generated_at: str,
) -> CorrectionVersionResultV1:
    errors: list[str] = []
    if not correction_provenance_ref.strip():
        _add(errors, LifecycleRegistryErrorCode.RETROACTIVE_CORRECTION_WITHOUT_PROVENANCE)
        return CorrectionVersionResultV1(False, None, tuple(errors))

    if not is_valid_rfc3339_utc(generated_at):
        _add(errors, LifecycleRegistryErrorCode.INVALID_TIMESTAMP)
        return CorrectionVersionResultV1(False, None, tuple(errors))

    new_version = prior.registry_snapshot_version + 1
    new_record_version = corrected_interval.registry_record_version + 1
    updated_intervals: list[InstrumentLifecycleIntervalV1] = []
    replaced = False

    for interval in prior.intervals:
        if (
            interval.instrument_id == corrected_interval.instrument_id
            and interval.interval_sequence == corrected_interval.interval_sequence
            and interval.superseded_by_version is None
        ):
            superseded = InstrumentLifecycleIntervalV1(
                instrument_id=interval.instrument_id,
                venue_id=interval.venue_id,
                contract_type=interval.contract_type,
                base_asset=interval.base_asset,
                quote_asset=interval.quote_asset,
                settlement_asset=interval.settlement_asset,
                listing_time=interval.listing_time,
                eligible_from=interval.eligible_from,
                interval_sequence=interval.interval_sequence,
                registry_record_version=interval.registry_record_version,
                record_digest=interval.record_digest,
                venue_symbol=interval.venue_symbol,
                native_instrument_id=interval.native_instrument_id,
                contract_expiry=interval.contract_expiry,
                delisting_time=interval.delisting_time,
                eligible_until=interval.eligible_until,
                expiry_time=interval.expiry_time,
                suspension_sub_intervals=interval.suspension_sub_intervals,
                source_snapshot_refs=interval.source_snapshot_refs,
                source_digests=interval.source_digests,
                superseded_by_version=new_version,
                correction_provenance_ref=interval.correction_provenance_ref,
            )
            updated_intervals.append(_attach_interval_digest(superseded))
            corrected = InstrumentLifecycleIntervalV1(
                instrument_id=corrected_interval.instrument_id,
                venue_id=corrected_interval.venue_id,
                contract_type=corrected_interval.contract_type,
                base_asset=corrected_interval.base_asset,
                quote_asset=corrected_interval.quote_asset,
                settlement_asset=corrected_interval.settlement_asset,
                listing_time=corrected_interval.listing_time,
                eligible_from=corrected_interval.eligible_from,
                interval_sequence=corrected_interval.interval_sequence,
                registry_record_version=new_record_version,
                record_digest="0" * 64,
                venue_symbol=corrected_interval.venue_symbol,
                native_instrument_id=corrected_interval.native_instrument_id,
                contract_expiry=corrected_interval.contract_expiry,
                delisting_time=corrected_interval.delisting_time,
                eligible_until=corrected_interval.eligible_until,
                expiry_time=corrected_interval.expiry_time,
                suspension_sub_intervals=corrected_interval.suspension_sub_intervals,
                source_snapshot_refs=corrected_interval.source_snapshot_refs,
                source_digests=corrected_interval.source_digests,
                correction_provenance_ref=correction_provenance_ref.strip(),
            )
            updated_intervals.append(_attach_interval_digest(corrected))
            replaced = True
        else:
            updated_intervals.append(interval)

    if not replaced:
        _add(errors, LifecycleRegistryErrorCode.UNKNOWN_LIFECYCLE_STATE)
        return CorrectionVersionResultV1(False, None, tuple(errors))

    snapshot = RegistrySnapshotV1(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        registry_snapshot_version=new_version,
        policy_version=prior.policy_version,
        source_priority_policy_version=prior.source_priority_policy_version,
        conflict_resolution_policy_version=prior.conflict_resolution_policy_version,
        venue_scope=prior.venue_scope,
        generated_at=generated_at,
        intervals=tuple(updated_intervals),
        config_digest=prior.config_digest,
        implementation_digest=prior.implementation_digest,
        registry_snapshot_digest="0" * 64,
    )
    return CorrectionVersionResultV1(True, attach_snapshot_digest(snapshot), ())


def format_registry_reference_v1(*, artifact_id: str, registry_snapshot_digest: str) -> str:
    return f"{REFERENCE_PREFIX}:{artifact_id.strip()}:sha256:{registry_snapshot_digest.strip().lower()}"


def intervals_overlap_v1(
    a: InstrumentLifecycleIntervalV1, b: InstrumentLifecycleIntervalV1
) -> bool:
    if a.instrument_id != b.instrument_id or a.interval_sequence != b.interval_sequence:
        return False
    a_start = parse_utc_instant(a.eligible_from)
    a_end = _exclusive_end_instant(a) or _OPEN_INTERVAL_END
    b_start = parse_utc_instant(b.eligible_from)
    b_end = _exclusive_end_instant(b) or _OPEN_INTERVAL_END
    if a_start is None or b_start is None:
        return False
    return a_start < b_end and b_start < a_end


def _cross_sequence_intervals_overlap_v1(
    a: InstrumentLifecycleIntervalV1, b: InstrumentLifecycleIntervalV1
) -> bool:
    if a.instrument_id != b.instrument_id:
        return False
    if a.interval_sequence == b.interval_sequence:
        return False
    a_start = parse_utc_instant(a.eligible_from)
    a_end = _exclusive_end_instant(a) or _OPEN_INTERVAL_END
    b_start = parse_utc_instant(b.eligible_from)
    b_end = _exclusive_end_instant(b) or _OPEN_INTERVAL_END
    if a_start is None or b_start is None:
        return False
    return a_start < b_end and b_start < a_end


def _issue_sort_key(issue: AssemblyIssueV1) -> tuple[str, str, str, str]:
    return (
        issue.error_code,
        issue.instrument_id or "",
        issue.field_path or "",
        issue.record_ref or "",
    )


def _make_issue(
    code: LifecycleRegistryErrorCode,
    *,
    instrument_id: str | None = None,
    record_ref: str | None = None,
    field_path: str | None = None,
) -> AssemblyIssueV1:
    return AssemblyIssueV1(
        error_code=code.value,
        instrument_id=instrument_id,
        record_ref=record_ref,
        field_path=field_path,
    )


@dataclass
class _IntervalBuilderState:
    instrument_id: str
    venue_id: str
    contract_type: str
    base_asset: str
    quote_asset: str
    settlement_asset: str
    venue_symbol: str | None
    native_instrument_id: str | None
    contract_expiry: str | None
    listing_time: str | None = None
    eligible_from: str | None = None
    delisting_time: str | None = None
    eligible_until: str | None = None
    expiry_time: str | None = None
    interval_sequence: int = 0
    registry_record_version: int = 1
    suspension_sub_intervals: list[SuspensionSubIntervalV1] = field(default_factory=list)
    source_snapshot_refs: set[str] = field(default_factory=set)
    source_digests: set[str] = field(default_factory=set)
    correction_provenance_ref: str | None = None
    pending_suspension_start: str | None = None
    prior_kind: str | None = None
    finalized_intervals: list[InstrumentLifecycleIntervalV1] = field(default_factory=list)

    def absorb_source(self, obs: NormalizedLifecycleObservationV1) -> None:
        self.source_snapshot_refs.add(obs.source_snapshot_ref)
        self.source_digests.add(obs.source_snapshot_digest)

    def to_interval(self) -> InstrumentLifecycleIntervalV1 | None:
        if self.listing_time is None or self.eligible_from is None:
            return None
        interval = InstrumentLifecycleIntervalV1(
            instrument_id=self.instrument_id,
            venue_id=self.venue_id,
            contract_type=self.contract_type,
            base_asset=self.base_asset,
            quote_asset=self.quote_asset,
            settlement_asset=self.settlement_asset,
            listing_time=self.listing_time,
            eligible_from=self.eligible_from,
            interval_sequence=self.interval_sequence,
            registry_record_version=self.registry_record_version,
            record_digest="0" * 64,
            venue_symbol=self.venue_symbol,
            native_instrument_id=self.native_instrument_id,
            contract_expiry=self.contract_expiry,
            delisting_time=self.delisting_time,
            eligible_until=self.eligible_until,
            expiry_time=self.expiry_time,
            suspension_sub_intervals=tuple(self.suspension_sub_intervals),
            source_snapshot_refs=tuple(sorted(self.source_snapshot_refs)),
            source_digests=tuple(sorted(self.source_digests)),
            correction_provenance_ref=self.correction_provenance_ref,
        )
        return _attach_interval_digest(interval)

    def reset_for_relisting(self) -> None:
        interval = self.to_interval()
        if interval is not None:
            self.finalized_intervals.append(interval)
        self.interval_sequence += 1
        self.registry_record_version = 1
        self.listing_time = None
        self.eligible_from = None
        self.delisting_time = None
        self.eligible_until = None
        self.expiry_time = None
        self.suspension_sub_intervals = []
        self.pending_suspension_start = None
        self.correction_provenance_ref = None
        self.prior_kind = None


def _state_from_observation(obs: NormalizedLifecycleObservationV1) -> _IntervalBuilderState:
    return _IntervalBuilderState(
        instrument_id=obs.instrument_id,
        venue_id=obs.venue_id,
        contract_type=obs.contract_type,
        base_asset=obs.base_asset,
        quote_asset=obs.quote_asset,
        settlement_asset=obs.settlement_asset,
        venue_symbol=obs.venue_symbol,
        native_instrument_id=obs.native_instrument_id,
        contract_expiry=obs.contract_expiry,
    )


def _apply_observation_to_builder(
    state: _IntervalBuilderState,
    obs: NormalizedLifecycleObservationV1,
    issues: list[AssemblyIssueV1],
) -> bool:
    kind = obs.observation_kind.strip().upper()
    transition = validate_observation_transition_v1(state.prior_kind, kind)
    if not transition.valid:
        for code in transition.error_codes:
            issues.append(
                _make_issue(
                    LifecycleRegistryErrorCode(code),
                    instrument_id=obs.instrument_id,
                    record_ref=obs.observation_digest,
                    field_path="observation_kind",
                )
            )
        return False

    state.absorb_source(obs)

    if kind in {ObservationKind.LISTING.value, ObservationKind.RELISTING.value}:
        if kind == ObservationKind.RELISTING.value:
            state.reset_for_relisting()
        state.listing_time = obs.listing_time or obs.source_effective_at
        state.eligible_from = obs.eligible_from or state.listing_time
        state.venue_id = obs.venue_id
        state.contract_type = obs.contract_type
        state.base_asset = obs.base_asset
        state.quote_asset = obs.quote_asset
        state.settlement_asset = obs.settlement_asset
        state.venue_symbol = obs.venue_symbol
        state.native_instrument_id = obs.native_instrument_id
        state.contract_expiry = obs.contract_expiry
    elif kind == ObservationKind.ELIGIBILITY.value:
        if obs.eligible_from is not None:
            state.eligible_from = obs.eligible_from
        if obs.eligible_until is not None:
            state.eligible_until = obs.eligible_until
    elif kind == ObservationKind.DELISTING.value:
        state.delisting_time = obs.delisting_time or obs.source_effective_at
    elif kind == ObservationKind.EXPIRY.value:
        state.expiry_time = obs.expiry_time or obs.source_effective_at
    elif kind == ObservationKind.SUSPENSION_START.value:
        state.pending_suspension_start = obs.source_effective_at
    elif kind == ObservationKind.SUSPENSION_END.value:
        if state.pending_suspension_start is None:
            issues.append(
                _make_issue(
                    LifecycleRegistryErrorCode.INVALID_TRANSITION,
                    instrument_id=obs.instrument_id,
                    record_ref=obs.observation_digest,
                    field_path="observation_kind",
                )
            )
            return False
        state.suspension_sub_intervals.append(
            SuspensionSubIntervalV1(
                suspension_start=state.pending_suspension_start,
                suspension_end=obs.source_effective_at,
            )
        )
        state.pending_suspension_start = None
    elif kind == ObservationKind.CORRECTION.value:
        if obs.listing_time is not None:
            state.listing_time = obs.listing_time
        if obs.eligible_from is not None:
            state.eligible_from = obs.eligible_from
        if obs.delisting_time is not None:
            state.delisting_time = obs.delisting_time
        if obs.eligible_until is not None:
            state.eligible_until = obs.eligible_until
        if obs.expiry_time is not None:
            state.expiry_time = obs.expiry_time
        state.correction_provenance_ref = obs.correction_provenance_ref
        state.registry_record_version += 1

    state.prior_kind = kind
    return True


def _detect_correction_cycle(
    observations: Sequence[NormalizedLifecycleObservationV1],
) -> bool:
    provenance_to_digest: dict[str, str] = {}
    digest_to_provenance: dict[str, str | None] = {}
    for obs in observations:
        digest_to_provenance[obs.observation_digest] = obs.correction_provenance_ref
        if obs.correction_provenance_ref:
            provenance_to_digest[obs.correction_provenance_ref.strip()] = obs.observation_digest

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(ref: str) -> bool:
        if ref in visiting:
            return True
        if ref in visited:
            return False
        visiting.add(ref)
        next_digest = provenance_to_digest.get(ref)
        if next_digest is not None:
            next_ref = digest_to_provenance.get(next_digest)
            if next_ref and visit(next_ref.strip()):
                return True
        visiting.remove(ref)
        visited.add(ref)
        return False

    for obs in observations:
        if obs.correction_provenance_ref and visit(obs.correction_provenance_ref.strip()):
            return True
    return False


def _validate_correction_references(
    observations: Sequence[NormalizedLifecycleObservationV1],
    known_refs: frozenset[str],
    issues: list[AssemblyIssueV1],
) -> bool:
    ok = True
    for obs in observations:
        if not obs.correction_provenance_ref:
            continue
        ref = obs.correction_provenance_ref.strip()
        if ref not in known_refs and ref not in {item.source_snapshot_ref for item in observations}:
            issues.append(
                _make_issue(
                    LifecycleRegistryErrorCode.INVALID_SOURCE_REFERENCE,
                    instrument_id=obs.instrument_id,
                    record_ref=obs.observation_digest,
                    field_path="correction_provenance_ref",
                )
            )
            ok = False
    if _detect_correction_cycle(observations):
        for obs in observations:
            if obs.correction_provenance_ref:
                issues.append(
                    _make_issue(
                        LifecycleRegistryErrorCode.OUT_OF_ORDER_EVENT,
                        instrument_id=obs.instrument_id,
                        record_ref=obs.observation_digest,
                        field_path="correction_provenance_ref",
                    )
                )
        ok = False
    return ok


def _assemble_instrument_intervals(
    observations: Sequence[NormalizedLifecycleObservationV1],
    issues: list[AssemblyIssueV1],
) -> tuple[InstrumentLifecycleIntervalV1, ...]:
    if not observations:
        return ()

    conflict = resolve_observation_conflicts_v1(observations)
    if conflict.has_conflict:
        for code in conflict.error_codes:
            issues.append(
                _make_issue(
                    LifecycleRegistryErrorCode(code),
                    instrument_id=observations[0].instrument_id,
                )
            )
        return ()

    sorted_obs = sort_normalized_observations(conflict.deduplicated)
    known_refs = frozenset(item.observation_digest for item in sorted_obs) | frozenset(
        item.source_snapshot_ref for item in sorted_obs
    )
    if not _validate_correction_references(sorted_obs, known_refs, issues):
        return ()

    state: _IntervalBuilderState | None = None
    for obs in sorted_obs:
        if state is None or obs.instrument_id != state.instrument_id:
            state = _state_from_observation(obs)
        if not _apply_observation_to_builder(state, obs, issues):
            return ()

    if state is None:
        return ()

    if state.pending_suspension_start is not None:
        issues.append(
            _make_issue(
                LifecycleRegistryErrorCode.INVALID_TRANSITION,
                instrument_id=state.instrument_id,
                field_path="suspension_sub_intervals",
            )
        )
        return ()

    final_interval = state.to_interval()
    if final_interval is None and state.finalized_intervals:
        return tuple(state.finalized_intervals)
    if final_interval is None:
        issues.append(
            _make_issue(
                LifecycleRegistryErrorCode.MISSING_REQUIRED_FIELD,
                instrument_id=state.instrument_id,
                field_path="listing_time",
            )
        )
        return ()

    all_intervals = list(state.finalized_intervals)
    all_intervals.append(final_interval)

    seen_sequences: set[int] = set()
    for interval in all_intervals:
        if interval.interval_sequence in seen_sequences:
            issues.append(
                _make_issue(
                    LifecycleRegistryErrorCode.DUPLICATE_CANONICAL_INSTRUMENT_ID,
                    instrument_id=interval.instrument_id,
                    field_path="interval_sequence",
                )
            )
            return ()
        seen_sequences.add(interval.interval_sequence)

    for i, left in enumerate(all_intervals):
        for right in all_intervals[i + 1 :]:
            if _cross_sequence_intervals_overlap_v1(left, right):
                issues.append(
                    _make_issue(
                        LifecycleRegistryErrorCode.OVERLAPPING_LIFECYCLE_INTERVALS,
                        instrument_id=left.instrument_id,
                        field_path="eligible_from",
                    )
                )
                return ()

    return tuple(all_intervals)


def assemble_registry_snapshot_v1(
    records: Sequence[SourceObservationRecordV1],
    *,
    generated_at: str,
    venue_scope: Sequence[str],
    config_digest: str,
    implementation_digest: str,
    policy_version: str = REGISTRY_VERSION,
    registry_snapshot_version: int = 1,
    registered_sources: frozenset[str] | None = None,
    approved_snapshot_digests: frozenset[str] | None = None,
) -> RegistryAssemblyResultV1:
    """Deterministic multi-source assembler — pure, no I/O."""
    issues: list[AssemblyIssueV1] = []

    if not is_valid_rfc3339_utc(generated_at):
        issues.append(
            _make_issue(LifecycleRegistryErrorCode.INVALID_TIMESTAMP, field_path="generated_at")
        )
    if not is_valid_digest(config_digest.strip().lower()):
        issues.append(
            _make_issue(LifecycleRegistryErrorCode.DIGEST_MISMATCH, field_path="config_digest")
        )
    if not is_valid_digest(implementation_digest.strip().lower()):
        issues.append(
            _make_issue(
                LifecycleRegistryErrorCode.DIGEST_MISMATCH, field_path="implementation_digest"
            )
        )
    if policy_version != REGISTRY_VERSION:
        issues.append(
            _make_issue(LifecycleRegistryErrorCode.POLICY_MISMATCH, field_path="policy_version")
        )
    if registry_snapshot_version < 1:
        issues.append(
            _make_issue(
                LifecycleRegistryErrorCode.POLICY_MISMATCH, field_path="registry_snapshot_version"
            )
        )

    if issues:
        error_codes = tuple(sorted({item.error_code for item in issues}))
        sorted_issues = tuple(sorted(issues, key=_issue_sort_key))
        return RegistryAssemblyResultV1(False, None, error_codes, sorted_issues)

    normalized: list[NormalizedLifecycleObservationV1] = []
    for record in records:
        result = normalize_source_observation_record_v1(
            record,
            registered_sources=registered_sources,
            approved_snapshot_digests=approved_snapshot_digests,
        )
        if not result.success or result.observation is None:
            for code in result.error_codes:
                issues.append(
                    _make_issue(
                        LifecycleRegistryErrorCode(code),
                        record_ref=record.observation_digest,
                        field_path="source_observation_record",
                    )
                )
            error_codes = tuple(sorted({item.error_code for item in issues}))
            sorted_issues = tuple(sorted(issues, key=_issue_sort_key))
            return RegistryAssemblyResultV1(False, None, error_codes, sorted_issues)
        normalized.append(result.observation)

    by_instrument: dict[str, list[NormalizedLifecycleObservationV1]] = {}
    for obs in normalized:
        by_instrument.setdefault(obs.instrument_id, []).append(obs)

    all_intervals: list[InstrumentLifecycleIntervalV1] = []
    for instrument_id in sorted(by_instrument.keys()):
        instrument_intervals = _assemble_instrument_intervals(by_instrument[instrument_id], issues)
        if issues:
            error_codes = tuple(sorted({item.error_code for item in issues}))
            sorted_issues = tuple(sorted(issues, key=_issue_sort_key))
            return RegistryAssemblyResultV1(False, None, error_codes, sorted_issues)
        all_intervals.extend(instrument_intervals)

    snapshot = RegistrySnapshotV1(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        registry_snapshot_version=registry_snapshot_version,
        policy_version=policy_version,
        source_priority_policy_version=SOURCE_PRIORITY_POLICY_VERSION,
        conflict_resolution_policy_version=CONFLICT_RESOLUTION_POLICY_VERSION,
        venue_scope=tuple(sorted({v.strip().lower() for v in venue_scope})),
        generated_at=generated_at,
        intervals=tuple(
            sorted(all_intervals, key=lambda item: (item.instrument_id, item.interval_sequence))
        ),
        config_digest=config_digest.strip().lower(),
        implementation_digest=implementation_digest.strip().lower(),
        registry_snapshot_digest="0" * 64,
    )
    final_snapshot = attach_snapshot_digest(snapshot)
    return RegistryAssemblyResultV1(True, final_snapshot, (), ())


def registry_snapshot_to_dict(
    snapshot: RegistrySnapshotV1,
    *,
    include_digest: bool = True,
) -> dict[str, Any]:
    """Deterministic snapshot dict for canonical persistence (Slice C)."""
    return {
        "config_digest": snapshot.config_digest,
        "conflict_resolution_policy_version": snapshot.conflict_resolution_policy_version,
        "generated_at": snapshot.generated_at,
        "implementation_digest": snapshot.implementation_digest,
        "intervals": [
            _interval_to_dict(interval, include_digest=include_digest)
            for interval in snapshot.intervals
        ],
        "policy_version": snapshot.policy_version,
        "registry_snapshot_digest": snapshot.registry_snapshot_digest,
        "registry_snapshot_version": snapshot.registry_snapshot_version,
        "schema_name": snapshot.schema_name,
        "schema_version": snapshot.schema_version,
        "source_priority_policy_version": snapshot.source_priority_policy_version,
        "venue_scope": list(snapshot.venue_scope),
    }
