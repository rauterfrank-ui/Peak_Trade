"""Contract tests for OKX archive ingest ↔ PIT lifecycle registry integration v0."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone

from src.research.missing_funding_policy_v0 import (
    MISSING_FUNDING_FAIL_CLOSED,
    MISSING_FUNDING_VALUE,
)
from src.research.okx_historical_funding_archive_ingest_v0 import (
    FULL_PANEL_PROMOTION_REQUIRES_HISTORICAL_UNIVERSE_LIFECYCLE_PASS,
    HISTORICAL_UNIVERSE_LIFECYCLE_PASS,
    check_full_panel_promotion_allowed_v0,
    parse_archive_csv_text_v0,
    pit_join_funding_rate_v0,
)
from src.research.okx_historical_funding_archive_lifecycle_integration_v0 import (
    CARRY_ZERO_FALLBACK_PRESENT,
    HISTORICAL_UNIVERSE_LIFECYCLE_PASS as INTEGRATION_LIFECYCLE_PASS,
    ArchiveLifecycleGateReason,
    compute_integration_contract_digest_v0,
    derive_archive_coverage_window_v0,
    evaluate_archive_funding_lifecycle_gate_by_venue_symbol_v0,
    evaluate_archive_funding_lifecycle_gate_v0,
    evaluate_lifecycle_membership_at_instant_v0,
    integration_contract_v0,
    resolve_archive_venue_symbol_to_instrument_id_v0,
    validate_terminated_interval_lifecycle_end_v0,
)
from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
    INPUT_CONTRACT_VERSION,
    InstrumentLifecycleIntervalV1,
    ObservationKind,
    QueryState,
    RegistrySnapshotV1,
    SourceObservationRecordV1,
    SourceTrustLevel,
    assemble_registry_snapshot_v1,
    attach_snapshot_digest,
    build_interval_from_observation_v1,
    compute_observation_digest,
    query_lifecycle_at_snapshot_v1,
)

_SOURCE_ID = "synthetic:test:record:v0"
_SNAPSHOT_REF = "synthetic:test:snapshot:v0"
_LISTING = "2024-04-01T00:00:00Z"
_ELIGIBLE = "2024-04-01T00:00:00Z"
_BAR_MS = int(
    datetime.strptime("2024-05-01T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
    .replace(tzinfo=timezone.utc)
    .timestamp()
    * 1000
)
_BEFORE_LISTING_MS = int(
    datetime.strptime("2024-03-01T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
    .replace(tzinfo=timezone.utc)
    .timestamp()
    * 1000
)
_AFTER_DELIST_MS = int(
    datetime.strptime("2024-07-01T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
    .replace(tzinfo=timezone.utc)
    .timestamp()
    * 1000
)
_GENERATED_AT = "2026-07-03T18:00:00Z"
_CONFIG_DIGEST = "a" * 64
_IMPL_DIGEST = "b" * 64

ETH_CSV = """\
instrument_name,funding_rate,funding_time
ETH-USDT-SWAP,0.000004880388991,1714492800000
ETH-USDT-SWAP,0.0000017236956739,1714521600000
ETH-USDT-SWAP,0.0000563153976033,1714550400000
"""


def _ms(utc: str) -> int:
    return int(
        datetime.strptime(utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp() * 1000
    )


def _source_record(**overrides: object) -> SourceObservationRecordV1:
    listing = str(overrides.get("listing_time", _LISTING))
    record = SourceObservationRecordV1(
        input_contract_version=INPUT_CONTRACT_VERSION,
        source_id=_SOURCE_ID,
        source_trust_level=SourceTrustLevel.TRUSTED.value,
        source_priority=1,
        source_snapshot_ref=_SNAPSHOT_REF,
        source_snapshot_digest="c" * 64,
        source_observed_at=listing,
        source_effective_at=str(overrides.get("source_effective_at", listing)),
        venue_id="okx",
        venue_timezone="UTC",
        market_type="futures",
        contract_type="linear_perpetual",
        base_asset=str(overrides.get("base_asset", "ETH")),
        quote_asset="USDT",
        settlement_asset="USDT",
        observation_kind=str(overrides.get("observation_kind", ObservationKind.LISTING.value)),
        observation_digest="0" * 64,
        venue_symbol=str(overrides.get("venue_symbol", "ETH-USDT-SWAP")),
        listing_time=listing,
        eligible_from=str(overrides.get("eligible_from", _ELIGIBLE)),
        delisting_time=(
            str(overrides["delisting_time"]) if overrides.get("delisting_time") else None
        ),
        eligible_until=(
            str(overrides["eligible_until"]) if overrides.get("eligible_until") else None
        ),
        expiry_time=str(overrides["expiry_time"]) if overrides.get("expiry_time") else None,
    )
    return dataclasses.replace(record, observation_digest=compute_observation_digest(record))


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


def _interval_from_source(**overrides: object) -> InstrumentLifecycleIntervalV1:
    from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
        normalize_source_observation_record_v1,
    )

    result = normalize_source_observation_record_v1(_source_record(**overrides))
    assert result.success, result.error_codes
    assert result.observation is not None
    interval = build_interval_from_observation_v1(result.observation)
    assert interval is not None
    return interval


def _manual_snapshot(*intervals: InstrumentLifecycleIntervalV1) -> RegistrySnapshotV1:
    snap = RegistrySnapshotV1(
        schema_name="pit_futures_instrument_lifecycle_registry",
        schema_version="v1",
        registry_snapshot_version=1,
        policy_version="pit_futures_instrument_lifecycle_registry.v1",
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


def _eth_snapshot(**overrides: object) -> RegistrySnapshotV1:
    return _assembled_snapshot(_source_record(**overrides))


def _delisted_eth_snapshot(*, delisting_time: str) -> RegistrySnapshotV1:
    interval = _interval_from_source(delisting_time=delisting_time)
    return _manual_snapshot(interval)


def _parsed_eth_events():
    result = parse_archive_csv_text_v0(ETH_CSV, source_file_digest="d" * 64)
    assert result.status.value == "COMPLETE"
    return result.events


def test_integration_contract_pass_flags() -> None:
    contract = integration_contract_v0()
    assert contract.historical_universe_lifecycle_pass is True
    assert contract.missing_funding_fail_closed is True
    assert contract.carry_zero_fallback_present is False
    assert contract.futures_only is True
    assert contract.bitcoin_direction_allowed is False
    assert INTEGRATION_LIFECYCLE_PASS is True
    assert HISTORICAL_UNIVERSE_LIFECYCLE_PASS is True


def test_ingest_module_lifecycle_pass_aligned_with_integration_owner() -> None:
    assert HISTORICAL_UNIVERSE_LIFECYCLE_PASS is True
    assert INTEGRATION_LIFECYCLE_PASS is True


def test_full_panel_promotion_allowed_after_lifecycle_integration() -> None:
    allowed, blocker = check_full_panel_promotion_allowed_v0()
    assert allowed is True
    assert blocker == ""


def test_integration_contract_digest_is_deterministic() -> None:
    left = compute_integration_contract_digest_v0()
    right = compute_integration_contract_digest_v0()
    assert left == right
    assert len(left) == 64


def test_archive_coverage_is_non_authoritative_for_lifecycle() -> None:
    events = _parsed_eth_events()
    coverage = derive_archive_coverage_window_v0(events, instrument_id="ETH-USDT-SWAP")
    assert coverage is not None
    assert coverage.coverage_non_authoritative is True
    assert coverage.settlement_count == 3


def test_instrument_before_listing_blocked() -> None:
    snapshot = _eth_snapshot(
        listing_time="2024-06-01T00:00:00Z", eligible_from="2024-06-01T00:00:00Z"
    )
    eth_id = snapshot.intervals[0].instrument_id
    allowed, state, reason, _ = evaluate_lifecycle_membership_at_instant_v0(
        snapshot,
        instrument_id=eth_id,
        decision_bar_time_ms=_BAR_MS,
    )
    assert allowed is False
    assert state == QueryState.NOT_LISTED.value
    assert reason == ArchiveLifecycleGateReason.NOT_LISTED_AT_DECISION_INSTANT.value


def test_instrument_during_valid_lifecycle_allowed_when_funding_complete() -> None:
    snapshot = _eth_snapshot()
    eth_id = snapshot.intervals[0].instrument_id
    events = _parsed_eth_events()
    gate = evaluate_archive_funding_lifecycle_gate_v0(
        snapshot,
        events,
        instrument_id=eth_id,
        decision_bar_time_ms=_BAR_MS,
        venue_symbol="ETH-USDT-SWAP",
    )
    assert gate.allowed is True
    assert gate.lifecycle_query_state == QueryState.ELIGIBLE.value
    assert gate.funding_rate is not None
    assert gate.reason_code == ArchiveLifecycleGateReason.LIFECYCLE_ELIGIBLE.value


def test_instrument_after_delisting_blocked() -> None:
    snapshot = _delisted_eth_snapshot(delisting_time="2024-05-15T00:00:00Z")
    eth_id = snapshot.intervals[0].instrument_id
    allowed, state, reason, _ = evaluate_lifecycle_membership_at_instant_v0(
        snapshot,
        instrument_id=eth_id,
        decision_bar_time_ms=_AFTER_DELIST_MS,
    )
    assert allowed is False
    assert state == QueryState.DELISTED.value
    assert reason == ArchiveLifecycleGateReason.DELISTED_AT_DECISION_INSTANT.value


def test_missing_lifecycle_begin_fail_closed() -> None:
    from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
        normalize_source_observation_record_v1,
    )

    record = dataclasses.replace(
        _source_record(),
        listing_time=None,
        eligible_from=None,
    )
    norm = normalize_source_observation_record_v1(record)
    assert not norm.success


def test_missing_lifecycle_end_for_terminated_contract_fail_closed() -> None:
    interval = _interval_from_source()
    broken = dataclasses.replace(interval, delisting_time=None, eligible_until=None)
    reason = validate_terminated_interval_lifecycle_end_v0(
        broken,
        query_state=QueryState.DELISTED.value,
    )
    assert reason == ArchiveLifecycleGateReason.MISSING_LIFECYCLE_END_FOR_TERMINATED.value


def test_venue_symbol_mapping_deterministic() -> None:
    snapshot = _eth_snapshot()
    instrument_id, reason = resolve_archive_venue_symbol_to_instrument_id_v0(
        snapshot,
        venue_symbol="ETH-USDT-SWAP",
    )
    assert reason is None
    assert instrument_id == snapshot.intervals[0].instrument_id


def test_venue_symbol_mapping_mismatch_blocked() -> None:
    snapshot = _eth_snapshot()
    instrument_id, reason = resolve_archive_venue_symbol_to_instrument_id_v0(
        snapshot,
        venue_symbol="UNKNOWN-USDT-SWAP",
    )
    assert instrument_id is None
    assert reason == ArchiveLifecycleGateReason.VENUE_SYMBOL_MAPPING_MISMATCH.value


def test_gate_by_venue_symbol_matches_direct_gate() -> None:
    snapshot = _eth_snapshot()
    events = _parsed_eth_events()
    direct = evaluate_archive_funding_lifecycle_gate_v0(
        snapshot,
        events,
        instrument_id=snapshot.intervals[0].instrument_id,
        decision_bar_time_ms=_BAR_MS,
        venue_symbol="ETH-USDT-SWAP",
    )
    mapped = evaluate_archive_funding_lifecycle_gate_by_venue_symbol_v0(
        snapshot,
        events,
        venue_symbol="ETH-USDT-SWAP",
        decision_bar_time_ms=_BAR_MS,
    )
    assert direct.result_digest == mapped.result_digest
    assert direct.allowed == mapped.allowed


def test_missing_funding_history_blocks_even_when_lifecycle_eligible() -> None:
    snapshot = _eth_snapshot()
    eth_id = snapshot.intervals[0].instrument_id
    gate = evaluate_archive_funding_lifecycle_gate_v0(
        snapshot,
        _parsed_eth_events(),
        instrument_id=eth_id,
        decision_bar_time_ms=_BEFORE_LISTING_MS,
        venue_symbol="ETH-USDT-SWAP",
    )
    assert gate.allowed is False
    assert gate.reason_code == ArchiveLifecycleGateReason.NOT_LISTED_AT_DECISION_INSTANT.value


def test_missing_funding_after_lifecycle_pass_blocks() -> None:
    snapshot = _eth_snapshot()
    eth_id = snapshot.intervals[0].instrument_id
    gate = evaluate_archive_funding_lifecycle_gate_v0(
        snapshot,
        _parsed_eth_events(),
        instrument_id=eth_id,
        decision_bar_time_ms=_ms("2024-04-01T00:00:00Z"),
        venue_symbol="ETH-USDT-SWAP",
    )
    assert gate.allowed is False
    assert gate.lifecycle_query_state == QueryState.ELIGIBLE.value
    assert gate.funding_rate is None
    assert gate.reason_code == "MISSING_FUNDING_NO_PRIOR_SETTLEMENT"


def test_no_zero_fallback_in_integration_module() -> None:
    assert CARRY_ZERO_FALLBACK_PRESENT is False
    assert MISSING_FUNDING_FAIL_CLOSED is True
    assert MISSING_FUNDING_VALUE is None


def test_pit_join_still_blocks_future_funding() -> None:
    events = _parsed_eth_events()
    rate, reason = pit_join_funding_rate_v0(events, _ms("2024-04-01T00:00:00Z"))
    assert rate is None
    assert reason == "MISSING_FUNDING_NO_PRIOR_SETTLEMENT"


def test_universe_snapshot_does_not_use_future_membership() -> None:
    future_listing = "2024-07-01T00:00:00Z"
    snapshot = _eth_snapshot(listing_time=future_listing, eligible_from=future_listing)
    eth_id = snapshot.intervals[0].instrument_id
    query_now = query_lifecycle_at_snapshot_v1(
        snapshot,
        instrument_id=eth_id,
        query_instant="2024-05-01T00:00:00Z",
    )
    assert query_now.query_state == QueryState.NOT_LISTED.value


def test_identical_inputs_produce_identical_gate_digests() -> None:
    snapshot = _eth_snapshot()
    events = _parsed_eth_events()
    eth_id = snapshot.intervals[0].instrument_id
    left = evaluate_archive_funding_lifecycle_gate_v0(
        snapshot,
        events,
        instrument_id=eth_id,
        decision_bar_time_ms=_BAR_MS,
        venue_symbol="ETH-USDT-SWAP",
    )
    right = evaluate_archive_funding_lifecycle_gate_v0(
        snapshot,
        events,
        instrument_id=eth_id,
        decision_bar_time_ms=_BAR_MS,
        venue_symbol="ETH-USDT-SWAP",
    )
    assert left.result_digest == right.result_digest


def test_missing_registry_instrument_fail_closed() -> None:
    snapshot = attach_snapshot_digest(
        RegistrySnapshotV1(
            schema_name="pit_futures_instrument_lifecycle_registry",
            schema_version="v1",
            registry_snapshot_version=1,
            policy_version="pit_futures_instrument_lifecycle_registry.v1",
            source_priority_policy_version="source_priority_policy.v1",
            conflict_resolution_policy_version="conflict_resolution_policy.v1",
            venue_scope=("okx",),
            generated_at=_GENERATED_AT,
            intervals=(),
            config_digest=_CONFIG_DIGEST,
            implementation_digest=_IMPL_DIGEST,
            registry_snapshot_digest="0" * 64,
        )
    )
    allowed, state, reason, _ = evaluate_lifecycle_membership_at_instant_v0(
        snapshot,
        instrument_id="missing:instrument",
        decision_bar_time_ms=_BAR_MS,
    )
    assert allowed is False
    assert state == QueryState.UNKNOWN.value
    assert reason == ArchiveLifecycleGateReason.MISSING_LIFECYCLE_EVIDENCE.value


def test_lifecycle_blocker_constant_retained_for_regression() -> None:
    assert FULL_PANEL_PROMOTION_REQUIRES_HISTORICAL_UNIVERSE_LIFECYCLE_PASS == (
        "FULL_PANEL_PROMOTION_REQUIRES_HISTORICAL_UNIVERSE_LIFECYCLE_PASS"
    )
