"""Contract tests for pit_futures_instrument_lifecycle_registry_validator_v1 — Slice B."""

from __future__ import annotations

import dataclasses
import itertools

from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
    INPUT_CONTRACT_VERSION,
    REGISTRY_VERSION,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    InstrumentLifecycleIntervalV1,
    LifecycleRegistryErrorCode,
    ObservationKind,
    QueryState,
    RegistrySnapshotV1,
    SourceObservationRecordV1,
    SourceTrustLevel,
    SuspensionSubIntervalV1,
    assemble_registry_snapshot_v1,
    attach_snapshot_digest,
    build_interval_from_observation_v1,
    compute_interval_digest,
    compute_observation_digest,
    normalize_source_observation_record_v1,
    query_lifecycle_at_snapshot_v1,
)
from src.research.pit_futures_instrument_lifecycle_registry_validator_v1 import (
    ValidationVerdict,
    validate_pit_futures_instrument_lifecycle_registry_snapshot_v1,
    validate_registry_snapshot_is_immutable_v1,
)

_SOURCE_ID = "synthetic:test:record:v0"
_SNAPSHOT_REF = "synthetic:test:snapshot:v0"
_LISTING = "2024-01-01T00:00:00Z"
_ELIGIBLE = "2024-01-02T00:00:00Z"
_GENERATED_AT = "2026-07-03T02:00:00Z"
_CONFIG_DIGEST = "b" * 64
_IMPL_DIGEST = "c" * 64


def _observation_payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "base_asset": "ETH",
        "contract_type": "linear_perpetual",
        "correction_provenance_ref": None,
        "delisting_time": None,
        "eligible_from": _ELIGIBLE,
        "eligible_until": None,
        "expiry_time": None,
        "listing_time": _LISTING,
        "market_type": "futures",
        "native_instrument_id": None,
        "observation_kind": ObservationKind.LISTING.value,
        "quote_asset": "USDT",
        "settlement_asset": "USDT",
        "source_effective_at": _LISTING,
        "source_id": _SOURCE_ID,
        "source_observed_at": _LISTING,
        "source_priority": 1,
        "source_snapshot_digest": "a" * 64,
        "source_snapshot_ref": _SNAPSHOT_REF,
        "venue_id": "okx",
        "venue_symbol": "ETH-USDT-SWAP",
        "venue_timezone": "UTC",
    }
    base.update(overrides)
    return base


def _source_record(**overrides: object) -> SourceObservationRecordV1:
    payload = _observation_payload(**overrides)
    record = SourceObservationRecordV1(
        input_contract_version=INPUT_CONTRACT_VERSION,
        source_id=str(payload["source_id"]),
        source_trust_level=SourceTrustLevel.TRUSTED.value,
        source_priority=int(payload["source_priority"]),  # type: ignore[arg-type]
        source_snapshot_ref=str(payload["source_snapshot_ref"]),
        source_snapshot_digest=str(payload["source_snapshot_digest"]),
        source_observed_at=str(payload["source_observed_at"]),
        source_effective_at=str(payload["source_effective_at"]),
        venue_id=str(payload["venue_id"]),
        venue_timezone=str(payload["venue_timezone"]),
        market_type=str(payload["market_type"]),
        contract_type=str(payload["contract_type"]),
        base_asset=str(payload["base_asset"]),
        quote_asset=str(payload["quote_asset"]),
        settlement_asset=str(payload["settlement_asset"]),
        observation_kind=str(payload["observation_kind"]),
        observation_digest="0" * 64,
        venue_symbol=str(payload["venue_symbol"]) if payload.get("venue_symbol") else None,
        native_instrument_id=(
            str(payload["native_instrument_id"]) if payload.get("native_instrument_id") else None
        ),
        contract_expiry=str(payload["contract_expiry"]) if payload.get("contract_expiry") else None,
        listing_time=str(payload["listing_time"]) if payload.get("listing_time") else None,
        eligible_from=str(payload["eligible_from"]) if payload.get("eligible_from") else None,
        delisting_time=str(payload["delisting_time"]) if payload.get("delisting_time") else None,
        eligible_until=str(payload["eligible_until"]) if payload.get("eligible_until") else None,
        expiry_time=str(payload["expiry_time"]) if payload.get("expiry_time") else None,
        correction_provenance_ref=(
            str(payload["correction_provenance_ref"])
            if payload.get("correction_provenance_ref")
            else None
        ),
    )
    return dataclasses.replace(record, observation_digest=compute_observation_digest(record))


def _normalize(**overrides: object):
    result = normalize_source_observation_record_v1(_source_record(**overrides))
    assert result.success, result.error_codes
    assert result.observation is not None
    return result.observation


def _interval(**overrides: object) -> InstrumentLifecycleIntervalV1:
    interval = build_interval_from_observation_v1(_normalize(**overrides))
    assert interval is not None
    return interval


def _assembled_snapshot(*records: SourceObservationRecordV1) -> RegistrySnapshotV1:
    result = assemble_registry_snapshot_v1(
        records,
        generated_at=_GENERATED_AT,
        venue_scope=("okx",),
        config_digest=_CONFIG_DIGEST,
        implementation_digest=_IMPL_DIGEST,
    )
    assert result.success, result.error_codes
    assert result.snapshot is not None
    return result.snapshot


def _manual_snapshot(*intervals: InstrumentLifecycleIntervalV1) -> RegistrySnapshotV1:
    snap = RegistrySnapshotV1(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        registry_snapshot_version=1,
        policy_version=REGISTRY_VERSION,
        source_priority_policy_version="source_priority_policy.v1",
        conflict_resolution_policy_version="conflict_resolution_policy.v1",
        venue_scope=("okx",),
        generated_at=_GENERATED_AT,
        intervals=intervals,
        config_digest=_CONFIG_DIGEST,
        implementation_digest=_IMPL_DIGEST,
        registry_snapshot_digest="0" * 64,
    )
    return attach_snapshot_digest(snap)


def test_validator_accepts_minimal_assembled_snapshot() -> None:
    snap = _assembled_snapshot(_source_record())
    result = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snap)
    assert result.verdict == ValidationVerdict.ACCEPTED
    assert result.valid is True
    assert result.issues == ()


def test_validator_accepts_multi_instrument_assembled_snapshot() -> None:
    snap = _assembled_snapshot(
        _source_record(),
        _source_record(base_asset="SOL", venue_symbol="SOL-USDT-SWAP"),
    )
    result = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snap)
    assert result.valid is True


def test_validator_rejects_digest_mismatch() -> None:
    interval = _interval()
    snap = _manual_snapshot(interval)
    bad = dataclasses.replace(snap, registry_snapshot_digest="f" * 64)
    result = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(bad)
    assert LifecycleRegistryErrorCode.DIGEST_MISMATCH.value in result.error_codes


def test_validator_rejects_record_digest_mismatch() -> None:
    interval = _interval()
    snap = _manual_snapshot(interval)
    bad_interval = dataclasses.replace(snap.intervals[0], eligible_from="2024-01-09T00:00:00Z")
    bad_snap = dataclasses.replace(snap, intervals=(bad_interval,))
    result = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(bad_snap)
    assert LifecycleRegistryErrorCode.DIGEST_MISMATCH.value in result.error_codes


def test_validator_rejects_invalid_registry_version() -> None:
    interval = _interval()
    snap = _manual_snapshot(interval)
    bad = dataclasses.replace(snap, policy_version="wrong.version")
    result = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(bad)
    assert LifecycleRegistryErrorCode.POLICY_MISMATCH.value in result.error_codes


def test_validator_rejects_spot_at_normalization() -> None:
    result = normalize_source_observation_record_v1(_source_record(market_type="spot"))
    assert not result.success
    assert LifecycleRegistryErrorCode.SPOT_INSTRUMENT_BLOCKED.value in result.error_codes


def test_validator_rejects_bitcoin_on_manual_snapshot() -> None:
    interval = _interval()
    bad = dataclasses.replace(interval, base_asset="BTC")
    bad = dataclasses.replace(bad, record_digest=compute_interval_digest(bad))
    snap = _manual_snapshot(bad)
    result = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snap)
    assert LifecycleRegistryErrorCode.BITCOIN_DIRECTION_PROHIBITED.value in result.error_codes


def test_validator_rejects_naive_datetime() -> None:
    interval = _interval()
    bad = dataclasses.replace(interval, listing_time="2024-01-01T00:00:00")
    bad = dataclasses.replace(bad, record_digest=compute_interval_digest(bad))
    snap = _manual_snapshot(bad)
    result = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snap)
    assert LifecycleRegistryErrorCode.INVALID_TIMESTAMP.value in result.error_codes


def test_validator_rejects_unsorted_intervals() -> None:
    first = _interval(base_asset="ETH", venue_symbol="ETH-USDT-SWAP")
    second = _interval(base_asset="SOL", venue_symbol="SOL-USDT-SWAP")
    ordered = _manual_snapshot(first, second)
    bad = dataclasses.replace(ordered, intervals=(ordered.intervals[1], ordered.intervals[0]))
    result = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(bad)
    assert LifecycleRegistryErrorCode.OUT_OF_ORDER_EVENT.value in result.error_codes


def test_validator_rejects_overlapping_cross_sequence_intervals() -> None:
    first = _interval(eligible_from=_LISTING, eligible_until="2025-01-01T00:00:00Z")
    second = build_interval_from_observation_v1(
        _normalize(
            observation_kind=ObservationKind.RELISTING.value,
            source_effective_at="2024-06-01T00:00:00Z",
            listing_time="2024-06-01T00:00:00Z",
            eligible_from="2024-06-01T00:00:00Z",
        ),
        interval_sequence=1,
    )
    assert second is not None
    snap = _manual_snapshot(first, second)
    result = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snap)
    assert LifecycleRegistryErrorCode.OVERLAPPING_LIFECYCLE_INTERVALS.value in result.error_codes


def test_validator_rejects_invalid_suspension_bounds() -> None:
    interval = build_interval_from_observation_v1(
        _normalize(),
        suspension_sub_intervals=(
            SuspensionSubIntervalV1("2024-05-01T00:00:00Z", "2024-03-01T00:00:00Z"),
        ),
    )
    assert interval is not None
    snap = _manual_snapshot(interval)
    result = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snap)
    assert LifecycleRegistryErrorCode.INVALID_TRANSITION.value in result.error_codes


def test_validator_issue_order_deterministic() -> None:
    interval = _interval()
    bad = dataclasses.replace(
        interval,
        listing_time="bad-time",
        record_digest="f" * 64,
        base_asset="BTC",
    )
    snap = _manual_snapshot(bad)
    first = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snap)
    second = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snap)
    assert first.issues == second.issues


def test_validator_same_invalid_input_same_issues() -> None:
    interval = _interval()
    bad = dataclasses.replace(interval, registry_record_version=0, record_digest="f" * 64)
    snap = _manual_snapshot(bad)
    a = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snap)
    b = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snap)
    assert a.error_codes == b.error_codes
    assert a.issues == b.issues


def test_assembler_output_accepted_by_validator() -> None:
    snap = _assembled_snapshot(_source_record())
    result = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snap)
    assert result.valid is True


def test_manipulated_assembler_output_rejected() -> None:
    snap = _assembled_snapshot(_source_record())
    tampered = dataclasses.replace(
        snap.intervals[0],
        eligible_from="2024-01-09T00:00:00Z",
    )
    bad_snap = dataclasses.replace(snap, intervals=(tampered,))
    result = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(bad_snap)
    assert result.valid is False
    assert LifecycleRegistryErrorCode.DIGEST_MISMATCH.value in result.error_codes


def test_snapshot_immutability_check() -> None:
    snap = _assembled_snapshot(_source_record())
    assert validate_registry_snapshot_is_immutable_v1(snap) is True


def test_property_permutation_assembler_validator_digest_stable() -> None:
    listing = _source_record()
    sol = _source_record(base_asset="SOL", venue_symbol="SOL-USDT-SWAP")
    permutations = list(itertools.permutations((listing, sol)))
    digests: set[str] = set()
    for batch in permutations:
        snap = _assembled_snapshot(*batch)
        val = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snap)
        assert val.valid is True
        digests.add(snap.registry_snapshot_digest)
    assert len(digests) == 1


def test_validator_rejects_current_state_fallback_marker() -> None:
    interval = _interval()
    bad = dataclasses.replace(
        interval,
        instrument_id="okx:linear_perpetual:current_state:USDT:USDT:perp",
    )
    bad = dataclasses.replace(bad, record_digest=compute_interval_digest(bad))
    snap = _manual_snapshot(bad)
    result = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snap)
    assert LifecycleRegistryErrorCode.UNKNOWN_LIFECYCLE_STATE.value in result.error_codes


def test_validator_rejects_absolute_source_reference() -> None:
    interval = _interval()
    bad = dataclasses.replace(interval, source_snapshot_refs=("/etc/passwd",))
    bad = dataclasses.replace(bad, record_digest=compute_interval_digest(bad))
    snap = _manual_snapshot(bad)
    result = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snap)
    assert LifecycleRegistryErrorCode.INVALID_SOURCE_REFERENCE.value in result.error_codes


def test_validator_rejects_dated_future_missing_expiry() -> None:
    interval = _interval(
        contract_type="linear_dated_future",
        contract_expiry="20240601",
        expiry_time="2024-06-01T00:00:00Z",
    )
    bad = dataclasses.replace(interval, expiry_time=None, contract_expiry=None)
    bad = dataclasses.replace(bad, record_digest=compute_interval_digest(bad))
    snap = _manual_snapshot(bad)
    result = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snap)
    assert LifecycleRegistryErrorCode.MISSING_EXPIRY_FOR_DATED_FUTURE.value in result.error_codes


def test_validator_uses_lifecycle_registry_error_codes_only() -> None:
    snap = _assembled_snapshot(_source_record())
    result = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snap)
    for code in result.error_codes:
        assert code in {item.value for item in LifecycleRegistryErrorCode}


def test_unknown_query_state_fail_closed_still_applies() -> None:
    snap = _assembled_snapshot(_source_record())
    result = query_lifecycle_at_snapshot_v1(
        snap,
        instrument_id="okx:linear_perpetual:MISSING:USDT:USDT:perp",
        query_instant="2024-06-01T01:00:00Z",
    )
    assert result.query_state == QueryState.UNKNOWN.value
