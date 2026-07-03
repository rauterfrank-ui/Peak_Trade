"""Contract tests for pit_futures_instrument_lifecycle_registry_v1 — Slice A."""

from __future__ import annotations

import dataclasses

import pytest

from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
    INPUT_CONTRACT_VERSION,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    InstrumentLifecycleIntervalV1,
    LifecycleQueryResultV1,
    LifecycleRegistryErrorCode,
    NormalizedLifecycleObservationV1,
    ObservationKind,
    QueryState,
    RegistrySnapshotV1,
    SourceObservationRecordV1,
    SourceTrustLevel,
    SuspensionSubIntervalV1,
    attach_snapshot_digest,
    assemble_registry_snapshot_v1,
    build_interval_from_observation_v1,
    compute_interval_digest,
    compute_observation_digest,
    compute_registry_snapshot_digest,
    create_correction_snapshot_version_v1,
    intervals_overlap_v1,
    normalize_source_observation_record_v1,
    query_lifecycle_at_snapshot_v1,
    query_lifecycle_state_at_instant_v1,
    resolve_observation_conflicts_v1,
    sort_normalized_observations,
    validate_observation_transition_v1,
)

_SOURCE_ID = "synthetic:test:record:v0"
_SNAPSHOT_REF = "synthetic:test:snapshot:v0"
_LISTING = "2024-01-01T00:00:00Z"
_ELIGIBLE = "2024-01-02T00:00:00Z"
_QUERY = "2024-06-01T01:00:00Z"
_GENERATED_AT = "2026-07-03T02:00:00Z"
_APPROVED_DIGESTS = frozenset()


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
    digest = compute_observation_digest(
        SourceObservationRecordV1(
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
                str(payload["native_instrument_id"])
                if payload.get("native_instrument_id")
                else None
            ),
            contract_expiry=str(payload["contract_expiry"])
            if payload.get("contract_expiry")
            else None,
            listing_time=str(payload["listing_time"]) if payload.get("listing_time") else None,
            eligible_from=str(payload["eligible_from"]) if payload.get("eligible_from") else None,
            delisting_time=str(payload["delisting_time"])
            if payload.get("delisting_time")
            else None,
            eligible_until=str(payload["eligible_until"])
            if payload.get("eligible_until")
            else None,
            expiry_time=str(payload["expiry_time"]) if payload.get("expiry_time") else None,
            correction_provenance_ref=(
                str(payload["correction_provenance_ref"])
                if payload.get("correction_provenance_ref")
                else None
            ),
        )
    )
    return SourceObservationRecordV1(
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
        observation_digest=digest,
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


def _normalize(**overrides: object) -> NormalizedLifecycleObservationV1:
    result = normalize_source_observation_record_v1(_source_record(**overrides))
    assert result.success, result.error_codes
    assert result.observation is not None
    return result.observation


def _interval(**overrides: object) -> InstrumentLifecycleIntervalV1:
    interval = build_interval_from_observation_v1(_normalize(**overrides))
    assert interval is not None
    return interval


def _snapshot(*intervals: InstrumentLifecycleIntervalV1) -> RegistrySnapshotV1:
    snap = RegistrySnapshotV1(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        registry_snapshot_version=1,
        policy_version="policy.v0",
        source_priority_policy_version="source_priority_policy.v1",
        conflict_resolution_policy_version="conflict_resolution_policy.v1",
        venue_scope=("okx",),
        generated_at=_GENERATED_AT,
        intervals=intervals,
        config_digest="b" * 64,
        implementation_digest="c" * 64,
        registry_snapshot_digest="0" * 64,
    )
    return attach_snapshot_digest(snap)


def test_observation_kind_count_exactly_eight() -> None:
    assert len(ObservationKind) == 8


def test_query_state_count_exactly_seven() -> None:
    assert len(QueryState) == 7


def test_error_code_count_exactly_twenty_eight() -> None:
    assert len(LifecycleRegistryErrorCode) == 28


def test_source_record_is_immutable() -> None:
    record = _source_record()
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.source_id = "mutated"  # type: ignore[misc]


def test_normalize_happy_path_futures_perpetual() -> None:
    result = normalize_source_observation_record_v1(_source_record())
    assert result.success
    assert result.observation is not None
    assert result.observation.instrument_id.startswith("okx:linear_perpetual:")


def test_spot_rejected() -> None:
    result = normalize_source_observation_record_v1(_source_record(market_type="spot"))
    assert not result.success
    assert LifecycleRegistryErrorCode.SPOT_INSTRUMENT_BLOCKED.value in result.error_codes


def test_synthetic_spot_rejected() -> None:
    result = normalize_source_observation_record_v1(_source_record(market_type="synthetic_spot"))
    assert not result.success
    assert LifecycleRegistryErrorCode.SYNTHETIC_SPOT_BLOCKED.value in result.error_codes


def test_non_futures_rejected() -> None:
    result = normalize_source_observation_record_v1(_source_record(market_type="option"))
    assert not result.success
    assert LifecycleRegistryErrorCode.NON_FUTURES_INSTRUMENT.value in result.error_codes


def test_bitcoin_base_rejected() -> None:
    result = normalize_source_observation_record_v1(_source_record(base_asset="BTC"))
    assert not result.success
    assert LifecycleRegistryErrorCode.BITCOIN_DIRECTION_PROHIBITED.value in result.error_codes


def test_xbt_base_rejected() -> None:
    result = normalize_source_observation_record_v1(_source_record(base_asset="XBT"))
    assert not result.success
    assert LifecycleRegistryErrorCode.BITCOIN_DIRECTION_PROHIBITED.value in result.error_codes


def test_invalid_timestamp_rejected() -> None:
    result = normalize_source_observation_record_v1(
        _source_record(source_effective_at="not-a-time")
    )
    assert not result.success
    assert LifecycleRegistryErrorCode.INVALID_TIMESTAMP.value in result.error_codes


def test_missing_listing_time_rejected() -> None:
    result = normalize_source_observation_record_v1(_source_record(listing_time=None))
    assert not result.success
    assert LifecycleRegistryErrorCode.MISSING_REQUIRED_FIELD.value in result.error_codes


def test_dated_future_requires_expiry() -> None:
    result = normalize_source_observation_record_v1(
        _source_record(contract_type="linear_dated_future", contract_expiry=None, expiry_time=None)
    )
    assert not result.success
    assert LifecycleRegistryErrorCode.MISSING_EXPIRY_FOR_DATED_FUTURE.value in result.error_codes


def test_correction_requires_provenance() -> None:
    result = normalize_source_observation_record_v1(
        _source_record(
            observation_kind=ObservationKind.CORRECTION.value, correction_provenance_ref=None
        )
    )
    assert not result.success
    assert (
        LifecycleRegistryErrorCode.RETROACTIVE_CORRECTION_WITHOUT_PROVENANCE.value
        in result.error_codes
    )


def test_unknown_source_rejected() -> None:
    result = normalize_source_observation_record_v1(_source_record(source_id="unknown:source:v0"))
    assert not result.success
    assert LifecycleRegistryErrorCode.UNKNOWN_SOURCE.value in result.error_codes


def test_untrusted_source_rejected() -> None:
    record = _source_record()
    untrusted = dataclasses.replace(record, source_trust_level=SourceTrustLevel.UNTRUSTED.value)
    result = normalize_source_observation_record_v1(untrusted)
    assert not result.success
    assert LifecycleRegistryErrorCode.UNTRUSTED_SOURCE.value in result.error_codes


def test_digest_mismatch_rejected() -> None:
    record = _source_record()
    bad = dataclasses.replace(record, observation_digest="f" * 64)
    result = normalize_source_observation_record_v1(bad)
    assert not result.success
    assert LifecycleRegistryErrorCode.DIGEST_MISMATCH.value in result.error_codes


def test_same_semantic_observation_same_digest() -> None:
    first = _source_record()
    second = _source_record()
    assert first.observation_digest == second.observation_digest


def test_different_semantic_observation_different_digest() -> None:
    first = _source_record()
    second = _source_record(base_asset="SOL", venue_symbol="SOL-USDT-SWAP")
    assert first.observation_digest != second.observation_digest


def test_sort_observations_permutation_invariant_digest_set() -> None:
    a = _normalize(source_priority=1, source_id="synthetic:test:record:v0")
    b = _normalize(source_priority=2, source_effective_at="2024-01-03T00:00:00Z")
    ordered = sort_normalized_observations((a, b))
    reversed_order = sort_normalized_observations((b, a))
    assert ordered == reversed_order


def test_conflicting_equal_priority_observations_fail_closed() -> None:
    first = _normalize(source_priority=1)
    second = _normalize(source_priority=1, eligible_from="2024-01-05T00:00:00Z")
    result = resolve_observation_conflicts_v1((first, second))
    assert result.has_conflict
    assert LifecycleRegistryErrorCode.CONFLICTING_SOURCE_RECORDS.value in result.error_codes


def test_duplicate_identical_observations_deduplicated() -> None:
    obs = _normalize()
    result = resolve_observation_conflicts_v1((obs, obs))
    assert not result.has_conflict
    assert len(result.deduplicated) == 1


def test_listing_boundary_inclusive() -> None:
    interval = _interval(listing_time=_QUERY, eligible_from=_QUERY)
    assert query_lifecycle_state_at_instant_v1(interval, _QUERY) == QueryState.ELIGIBLE


def test_eligible_from_inclusive() -> None:
    interval = _interval(listing_time=_LISTING, eligible_from=_QUERY)
    assert query_lifecycle_state_at_instant_v1(interval, _QUERY) == QueryState.ELIGIBLE


def test_listed_ineligible_before_eligible_from() -> None:
    interval = _interval(listing_time=_LISTING, eligible_from="2024-06-02T00:00:00Z")
    assert query_lifecycle_state_at_instant_v1(interval, _QUERY) == QueryState.LISTED_INELIGIBLE


def test_not_listed_before_listing() -> None:
    interval = _interval(listing_time="2024-06-02T00:00:00Z", eligible_from="2024-06-02T00:00:00Z")
    assert query_lifecycle_state_at_instant_v1(interval, _QUERY) == QueryState.NOT_LISTED


def test_delisting_boundary_exclusive() -> None:
    interval = _interval(delisting_time=_QUERY)
    assert query_lifecycle_state_at_instant_v1(interval, _QUERY) == QueryState.DELISTED


def test_expiry_boundary_exclusive() -> None:
    interval = _interval(
        contract_type="linear_dated_future",
        contract_expiry="20240601",
        expiry_time=_QUERY,
    )
    assert query_lifecycle_state_at_instant_v1(interval, _QUERY) == QueryState.EXPIRED


def test_eligible_until_boundary_exclusive() -> None:
    interval = _interval(eligible_until=_QUERY)
    assert query_lifecycle_state_at_instant_v1(interval, _QUERY) == QueryState.DELISTED


def test_suspension_sub_interval() -> None:
    interval = build_interval_from_observation_v1(
        _normalize(),
        suspension_sub_intervals=(
            SuspensionSubIntervalV1("2024-05-01T00:00:00Z", "2024-07-01T00:00:00Z"),
        ),
    )
    assert interval is not None
    assert query_lifecycle_state_at_instant_v1(interval, _QUERY) == QueryState.SUSPENDED


def test_unknown_historical_membership_fail_closed() -> None:
    snap = _snapshot()
    result = query_lifecycle_at_snapshot_v1(
        snap,
        instrument_id="okx:linear_perpetual:MISSING:USDT:USDT:perp",
        query_instant=_QUERY,
    )
    assert result.query_state == QueryState.UNKNOWN.value
    assert LifecycleRegistryErrorCode.UNKNOWN_LIFECYCLE_STATE.value in result.error_codes


def test_query_bound_to_snapshot_version_and_digest() -> None:
    interval = _interval()
    snap = _snapshot(interval)
    result = query_lifecycle_at_snapshot_v1(
        snap,
        instrument_id=interval.instrument_id,
        query_instant=_QUERY,
    )
    assert isinstance(result, LifecycleQueryResultV1)
    assert result.registry_snapshot_version == 1
    assert result.registry_snapshot_digest == snap.registry_snapshot_digest


def test_stable_interval_and_snapshot_digests() -> None:
    interval = _interval()
    snap = _snapshot(interval)
    assert interval.record_digest == compute_interval_digest(interval)
    assert snap.registry_snapshot_digest == compute_registry_snapshot_digest(snap)


def test_snapshot_digest_permutation_invariant() -> None:
    first = _interval(base_asset="ETH", venue_symbol="ETH-USDT-SWAP")
    second = _interval(base_asset="SOL", venue_symbol="SOL-USDT-SWAP")
    snap_a = _snapshot(first, second)
    snap_b = _snapshot(second, first)
    assert snap_a.registry_snapshot_digest == snap_b.registry_snapshot_digest


def test_correction_creates_new_snapshot_version_no_inplace_rewrite() -> None:
    interval = _interval()
    prior = _snapshot(interval)
    corrected = dataclasses.replace(
        interval, eligible_from="2024-01-03T00:00:00Z", record_digest="0" * 64
    )
    corrected = build_interval_from_observation_v1(
        _normalize(eligible_from="2024-01-03T00:00:00Z"),
        interval_sequence=interval.interval_sequence,
        registry_record_version=interval.registry_record_version,
    )
    assert corrected is not None
    result = create_correction_snapshot_version_v1(
        prior,
        corrected_interval=corrected,
        correction_provenance_ref="synthetic:correction:prov:v0",
        generated_at="2026-07-03T03:00:00Z",
    )
    assert result.success
    assert result.snapshot is not None
    assert result.snapshot.registry_snapshot_version == 2
    assert result.snapshot.registry_snapshot_digest != prior.registry_snapshot_digest
    superseded = [i for i in result.snapshot.intervals if i.superseded_by_version == 2]
    assert superseded


def test_invalid_transition_suspension_end_without_start() -> None:
    result = validate_observation_transition_v1(
        ObservationKind.LISTING.value, ObservationKind.SUSPENSION_END.value
    )
    assert not result.valid
    assert LifecycleRegistryErrorCode.INVALID_TRANSITION.value in result.error_codes


def test_valid_transition_listing_to_eligibility() -> None:
    result = validate_observation_transition_v1(
        ObservationKind.LISTING.value, ObservationKind.ELIGIBILITY.value
    )
    assert result.valid


def test_relisting_after_delisting_allowed() -> None:
    result = validate_observation_transition_v1(
        ObservationKind.DELISTING.value,
        ObservationKind.RELISTING.value,
    )
    assert result.valid


def test_delisted_to_eligible_without_relisting_forbidden() -> None:
    result = validate_observation_transition_v1(
        ObservationKind.DELISTING.value,
        ObservationKind.ELIGIBILITY.value,
    )
    assert not result.valid


def test_overlapping_intervals_detected() -> None:
    a = _interval(eligible_from=_LISTING, eligible_until="2024-12-01T00:00:00Z")
    b = _interval(
        eligible_from="2024-06-01T00:00:00Z",
        eligible_until="2025-01-01T00:00:00Z",
    )
    assert intervals_overlap_v1(a, b)


def test_all_error_codes_are_unique_strings() -> None:
    values = [item.value for item in LifecycleRegistryErrorCode]
    assert len(values) == len(set(values))


_CONFIG_DIGEST = "b" * 64
_IMPL_DIGEST = "c" * 64


def _event_record(**overrides: object) -> SourceObservationRecordV1:
    """Build a source record with a correctly computed observation digest."""
    base = _source_record(**overrides)
    digest = compute_observation_digest(base)
    return dataclasses.replace(base, observation_digest=digest)


def _assemble(*records: SourceObservationRecordV1) -> RegistrySnapshotV1:
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


def test_assembler_empty_input_produces_valid_empty_snapshot() -> None:
    result = assemble_registry_snapshot_v1(
        (),
        generated_at=_GENERATED_AT,
        venue_scope=("okx",),
        config_digest=_CONFIG_DIGEST,
        implementation_digest=_IMPL_DIGEST,
    )
    assert result.success
    assert result.snapshot is not None
    assert result.snapshot.intervals == ()


def test_assembler_single_instrument_listing() -> None:
    snap = _assemble(_source_record())
    assert len(snap.intervals) == 1
    assert snap.intervals[0].instrument_id.startswith("okx:")


def test_assembler_multiple_instruments() -> None:
    eth = _source_record()
    sol = _source_record(base_asset="SOL", venue_symbol="SOL-USDT-SWAP")
    snap = _assemble(eth, sol)
    assert len(snap.intervals) == 2
    ids = {item.instrument_id for item in snap.intervals}
    assert len(ids) == 2


def test_assembler_identical_duplicates_deduplicated() -> None:
    record = _source_record()
    snap = _assemble(record, record)
    assert len(snap.intervals) == 1


def test_assembler_conflicting_equal_priority_fail_closed() -> None:
    first = _source_record(source_priority=1)
    second = _source_record(source_priority=1, eligible_from="2024-01-05T00:00:00Z")
    result = assemble_registry_snapshot_v1(
        (first, second),
        generated_at=_GENERATED_AT,
        venue_scope=("okx",),
        config_digest=_CONFIG_DIGEST,
        implementation_digest=_IMPL_DIGEST,
    )
    assert not result.success
    assert LifecycleRegistryErrorCode.CONFLICTING_SOURCE_RECORDS.value in result.error_codes


def test_assembler_different_source_priority_lower_wins() -> None:
    low = _source_record(source_priority=1, eligible_from="2024-01-02T00:00:00Z")
    high = _source_record(source_priority=2, eligible_from="2024-01-05T00:00:00Z")
    snap = _assemble(high, low)
    assert snap.intervals[0].eligible_from == "2024-01-02T00:00:00Z"


def test_assembler_permutation_invariant_snapshot_digest() -> None:
    eth = _source_record()
    sol = _source_record(base_asset="SOL", venue_symbol="SOL-USDT-SWAP")
    snap_a = _assemble(eth, sol)
    snap_b = _assemble(sol, eth)
    assert snap_a.registry_snapshot_digest == snap_b.registry_snapshot_digest


def test_assembler_listing_to_delisting_lifecycle() -> None:
    listing = _event_record(observation_kind=ObservationKind.LISTING.value)
    eligibility = _event_record(
        observation_kind=ObservationKind.ELIGIBILITY.value,
        source_effective_at="2024-01-02T00:00:00Z",
    )
    delist = _event_record(
        observation_kind=ObservationKind.DELISTING.value,
        source_effective_at="2024-12-01T00:00:00Z",
        delisting_time="2024-12-01T00:00:00Z",
    )
    snap = _assemble(listing, eligibility, delist)
    assert snap.intervals[0].delisting_time == "2024-12-01T00:00:00Z"


def test_assembler_suspension_start_end_pair() -> None:
    listing = _event_record()
    eligibility = _event_record(
        observation_kind=ObservationKind.ELIGIBILITY.value,
        source_effective_at="2024-01-02T00:00:00Z",
    )
    suspend_start = _event_record(
        observation_kind=ObservationKind.SUSPENSION_START.value,
        source_effective_at="2024-05-01T00:00:00Z",
    )
    suspend_end = _event_record(
        observation_kind=ObservationKind.SUSPENSION_END.value,
        source_effective_at="2024-07-01T00:00:00Z",
    )
    snap = _assemble(listing, eligibility, suspend_start, suspend_end)
    assert len(snap.intervals[0].suspension_sub_intervals) == 1


def test_assembler_invalid_transition_fail_closed() -> None:
    listing = _event_record()
    bad_end = _event_record(
        observation_kind=ObservationKind.SUSPENSION_END.value,
        source_effective_at="2024-05-01T00:00:00Z",
    )
    result = assemble_registry_snapshot_v1(
        (listing, bad_end),
        generated_at=_GENERATED_AT,
        venue_scope=("okx",),
        config_digest=_CONFIG_DIGEST,
        implementation_digest=_IMPL_DIGEST,
    )
    assert not result.success
    assert LifecycleRegistryErrorCode.INVALID_TRANSITION.value in result.error_codes


def test_assembler_unknown_normalization_fail_closed() -> None:
    result = assemble_registry_snapshot_v1(
        (_source_record(source_id="unknown:source:v0"),),
        generated_at=_GENERATED_AT,
        venue_scope=("okx",),
        config_digest=_CONFIG_DIGEST,
        implementation_digest=_IMPL_DIGEST,
    )
    assert not result.success
    assert LifecycleRegistryErrorCode.UNKNOWN_SOURCE.value in result.error_codes
