"""Contract tests for pit_futures_universe_manifest_generator_registry_consumer_binding_v1 — Slice D."""

from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path

import pytest

from src.execution.replay_pack.canonical import dumps_canonical
from src.research.pit_futures_instrument_lifecycle_registry_persistence_v1 import (
    OverwritePolicy,
    read_registry_snapshot_v1,
    write_registry_snapshot_v1,
)
from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
    INPUT_CONTRACT_VERSION,
    REGISTRY_VERSION,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    InstrumentLifecycleIntervalV1,
    RegistrySnapshotV1,
    ObservationKind,
    QueryState,
    SourceObservationRecordV1,
    SourceTrustLevel,
    assemble_registry_snapshot_v1,
    attach_snapshot_digest,
    build_interval_from_observation_v1,
    compute_observation_digest,
    query_lifecycle_at_snapshot_v1,
)
from src.research.pit_futures_instrument_lifecycle_registry_validator_v1 import (
    ValidationVerdict,
    validate_pit_futures_instrument_lifecycle_registry_snapshot_v1,
)
from src.research.pit_futures_universe_manifest_generator_registry_consumer_binding_v1 import (
    BINDING_INPUT_CONTRACT_VERSION,
    BINDING_VERSION,
    RegistryBindingErrorCode,
    RegistryBoundEpochInputV1,
    PitFuturesUniverseManifestGeneratorRegistryBindingInputV1,
    SupplementaryInstrumentMarketDataV1,
    compute_binding_implementation_digest,
    generate_pit_futures_universe_manifest_from_registry_binding_v1,
)
from src.research.pit_futures_universe_manifest_generator_v1 import (
    GENERATOR_VERSION,
    INPUT_CONTRACT_VERSION as GENERATOR_INPUT_CONTRACT_VERSION,
    compute_generator_config_digest,
    compute_generator_implementation_digest,
)
from src.research.pit_futures_universe_manifest_v1 import (
    compute_manifest_digest,
    compute_sha256_digest,
)
from src.research.pit_futures_universe_manifest_validator_v1 import (
    ValidationVerdict as ManifestValidationVerdict,
    validate_pit_futures_universe_manifest_v1,
)

_SOURCE_ID = "synthetic:test:record:v0"
_SNAPSHOT_REF = "synthetic:test:snapshot:v0"
_DATASET_REF = "synthetic:generator:dataset:v0"
_PERIOD_REF = "synthetic:generator:period:v0"
_GENERATED_AT = "2026-07-03T03:00:00Z"
_LISTING = "2024-01-01T00:00:00Z"
_ELIGIBLE = "2024-01-02T00:00:00Z"
_BAR_CLOSE = "2024-06-01T01:00:00Z"
_MIN_HISTORY = 21
_CONFIG_DIGEST = "b" * 64
_IMPL_DIGEST = "c" * 64
_REGISTRY_ARTIFACT_ID = "synthetic_pit_lifecycle_registry_v0"


def _source_record(**overrides: object) -> SourceObservationRecordV1:
    payload = {
        "base_asset": overrides.get("base_asset", "ETH"),
        "contract_type": overrides.get("contract_type", "linear_perpetual"),
        "correction_provenance_ref": None,
        "delisting_time": overrides.get("delisting_time"),
        "eligible_from": overrides.get("eligible_from", _ELIGIBLE),
        "eligible_until": overrides.get("eligible_until"),
        "expiry_time": overrides.get("expiry_time"),
        "listing_time": overrides.get("listing_time", _LISTING),
        "market_type": "futures",
        "native_instrument_id": None,
        "observation_kind": overrides.get("observation_kind", ObservationKind.LISTING.value),
        "quote_asset": "USDT",
        "settlement_asset": "USDT",
        "source_effective_at": overrides.get(
            "source_effective_at", overrides.get("listing_time", _LISTING)
        ),
        "source_id": _SOURCE_ID,
        "source_observed_at": _LISTING,
        "source_priority": 1,
        "source_snapshot_digest": "a" * 64,
        "source_snapshot_ref": _SNAPSHOT_REF,
        "venue_id": overrides.get("venue_id", "okx"),
        "venue_symbol": overrides.get("venue_symbol", "ETH-USDT-SWAP"),
        "venue_timezone": "UTC",
    }
    record = SourceObservationRecordV1(
        input_contract_version=INPUT_CONTRACT_VERSION,
        source_id=str(payload["source_id"]),
        source_trust_level=SourceTrustLevel.TRUSTED.value,
        source_priority=1,
        source_snapshot_ref=_SNAPSHOT_REF,
        source_snapshot_digest="a" * 64,
        source_observed_at=_LISTING,
        source_effective_at=str(payload["source_effective_at"]),
        venue_id=str(payload["venue_id"]),
        venue_timezone="UTC",
        market_type="futures",
        contract_type=str(payload["contract_type"]),
        base_asset=str(payload["base_asset"]),
        quote_asset="USDT",
        settlement_asset="USDT",
        observation_kind=str(payload["observation_kind"]),
        observation_digest="0" * 64,
        venue_symbol=str(payload["venue_symbol"]),
        listing_time=str(payload["listing_time"]) if payload.get("listing_time") else None,
        eligible_from=str(payload["eligible_from"]) if payload.get("eligible_from") else None,
        delisting_time=str(payload["delisting_time"]) if payload.get("delisting_time") else None,
        eligible_until=str(payload["eligible_until"]) if payload.get("eligible_until") else None,
        expiry_time=str(payload["expiry_time"]) if payload.get("expiry_time") else None,
    )
    return dataclasses.replace(record, observation_digest=compute_observation_digest(record))


def _assembled_snapshot(*records: SourceObservationRecordV1):
    result = assemble_registry_snapshot_v1(
        records,
        generated_at=_GENERATED_AT,
        venue_scope=("okx", "binance_usdm"),
        config_digest=_CONFIG_DIGEST,
        implementation_digest=_IMPL_DIGEST,
    )
    assert result.success, result.error_codes
    assert result.snapshot is not None
    return result.snapshot


def _supplementary(
    instrument_id: str, *, suffix: str = "eth", history: int = 30
) -> SupplementaryInstrumentMarketDataV1:
    payload = {"instrument_id": instrument_id, "suffix": suffix}
    return SupplementaryInstrumentMarketDataV1(
        instrument_id=instrument_id,
        source_ref=f"synthetic:binding:market:{suffix}",
        record_digest=compute_sha256_digest(payload),
        market_type="futures",
        history_bars_available=history,
        required_history_bars=_MIN_HISTORY,
        data_availability_status="AVAILABLE",
    )


def _panel_registry():
    specs = [
        ("ETH", "ETH-USDT-SWAP", "eth"),
        ("SOL", "SOL-USDT-SWAP", "sol"),
        ("AVAX", "AVAX-USDT-SWAP", "avax"),
        ("LINK", "LINK-USDT-SWAP", "link"),
        ("DOT", "DOT-USDT-SWAP", "dot"),
        ("ADA", "ADAUSDT", "ada", "binance_usdm"),
    ]
    records = []
    supplementary = []
    for item in specs:
        base = item[0]
        symbol = item[1]
        suffix = item[2]
        venue = item[3] if len(item) > 3 else "okx"
        records.append(_source_record(base_asset=base, venue_symbol=symbol, venue_id=venue))
    snapshot = _assembled_snapshot(*records)
    for interval in snapshot.intervals:
        suffix = interval.base_asset.lower()
        supplementary.append(_supplementary(interval.instrument_id, suffix=suffix))
    return snapshot, tuple(supplementary)


def _manual_snapshot(*intervals: InstrumentLifecycleIntervalV1) -> RegistrySnapshotV1:
    snap = RegistrySnapshotV1(
        schema_name=SCHEMA_NAME,
        schema_version=SCHEMA_VERSION,
        registry_snapshot_version=1,
        policy_version=REGISTRY_VERSION,
        source_priority_policy_version="source_priority_policy.v1",
        conflict_resolution_policy_version="conflict_resolution_policy.v1",
        venue_scope=("okx", "binance_usdm"),
        generated_at=_GENERATED_AT,
        intervals=intervals,
        config_digest=_CONFIG_DIGEST,
        implementation_digest=_IMPL_DIGEST,
        registry_snapshot_digest="0" * 64,
    )
    return attach_snapshot_digest(snap)


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


def _ltc_with_delisting_snapshot(*, delisting_time: str) -> RegistrySnapshotV1:
    interval = _interval_from_source(
        base_asset="LTC",
        venue_symbol="LTC-USDT-SWAP",
        delisting_time=delisting_time,
    )
    return _manual_snapshot(interval)


def _build_binding_input(
    *,
    snapshot=None,
    supplementary=None,
    bound_digest: str | None = None,
    bound_version: int | None = None,
    epochs=None,
):
    if snapshot is None or supplementary is None:
        snapshot, supplementary = _panel_registry()
    partial = PitFuturesUniverseManifestGeneratorRegistryBindingInputV1(
        binding_input_contract_version=BINDING_INPUT_CONTRACT_VERSION,
        binding_version=BINDING_VERSION,
        registry_artifact_id=_REGISTRY_ARTIFACT_ID,
        bound_registry_schema_version=SCHEMA_VERSION,
        bound_registry_snapshot_version=bound_version or snapshot.registry_snapshot_version,
        bound_registry_snapshot_digest=bound_digest or snapshot.registry_snapshot_digest,
        registry_snapshot=snapshot,
        input_contract_version=GENERATOR_INPUT_CONTRACT_VERSION,
        artifact_id="synthetic_pit_generator_registry_binding_manifest_v0",
        venue_id="okx",
        universe_id="synthetic_universe_v0",
        hypothesis_id="CROSS_SECTIONAL_RELATIVE_STRENGTH_NON_BITCOIN_PERPETUALS_V0",
        universe_policy_id="synthetic_cross_sectional_okx_non_btc_perp_v0",
        universe_policy_version="v0",
        inclusion_policy_version="v0",
        exclusion_policy_version="v0",
        generator_version=GENERATOR_VERSION,
        generated_at=_GENERATED_AT,
        bar_interval="PT1H",
        minimum_history_bars=_MIN_HISTORY,
        minimum_required_member_count=5,
        venue_scope=("binance_usdm", "okx"),
        source_snapshot_refs=(_DATASET_REF,),
        source_digests=(compute_sha256_digest({"source_dataset_refs": [_DATASET_REF]}),),
        period_binding_ref=_PERIOD_REF,
        config_digest="0" * 64,
        implementation_digest="0" * 64,
        supplementary_market_data=supplementary,
        epochs=epochs
        or (
            RegistryBoundEpochInputV1(
                score_epoch=0,
                finalized_bar_close=_BAR_CLOSE,
                historical_as_of_time=_BAR_CLOSE,
            ),
        ),
    )
    from src.research.pit_futures_universe_manifest_generator_v1 import (
        PitFuturesUniverseManifestGeneratorInputV1,
        GeneratorEpochInputV1,
    )

    gen_partial = PitFuturesUniverseManifestGeneratorInputV1(
        input_contract_version=partial.input_contract_version,
        artifact_id=partial.artifact_id,
        venue_id=partial.venue_id,
        universe_id=partial.universe_id,
        hypothesis_id=partial.hypothesis_id,
        universe_policy_id=partial.universe_policy_id,
        universe_policy_version=partial.universe_policy_version,
        inclusion_policy_version=partial.inclusion_policy_version,
        exclusion_policy_version=partial.exclusion_policy_version,
        generator_version=partial.generator_version,
        generated_at=partial.generated_at,
        bar_interval=partial.bar_interval,
        minimum_history_bars=partial.minimum_history_bars,
        minimum_required_member_count=partial.minimum_required_member_count,
        venue_scope=partial.venue_scope,
        source_snapshot_refs=partial.source_snapshot_refs,
        source_digests=partial.source_digests,
        period_binding_ref=partial.period_binding_ref,
        config_digest="0" * 64,
        implementation_digest="0" * 64,
        epochs=(GeneratorEpochInputV1(0, _BAR_CLOSE, ()),),
    )
    return dataclasses.replace(
        partial,
        config_digest=compute_generator_config_digest(gen_partial),
        implementation_digest=compute_generator_implementation_digest(),
    )


def test_happy_path_active_instrument_included() -> None:
    result = generate_pit_futures_universe_manifest_from_registry_binding_v1(_build_binding_input())
    assert result.success is True
    assert result.manifest is not None
    assert result.provenance is not None
    assert result.provenance.registry_content_digest == result.provenance.registry_content_digest
    assert len(result.manifest.epochs[0].members) >= 5
    validation = validate_pit_futures_universe_manifest_v1(result.manifest)
    assert validation.verdict == ManifestValidationVerdict.ACCEPTED


def test_not_yet_listed_instrument_excluded_by_generator() -> None:
    future_listing = "2024-07-01T00:00:00Z"
    record = _source_record(
        base_asset="LTC",
        venue_symbol="LTC-USDT-SWAP",
        listing_time=future_listing,
        eligible_from=future_listing,
    )
    snapshot = _assembled_snapshot(*[_source_record(), record])
    ltc = next(i for i in snapshot.intervals if i.base_asset == "LTC")
    supplementary = (
        _supplementary(snapshot.intervals[0].instrument_id, suffix="eth"),
        _supplementary(ltc.instrument_id, suffix="ltc"),
    )
    result = generate_pit_futures_universe_manifest_from_registry_binding_v1(
        _build_binding_input(snapshot=snapshot, supplementary=supplementary)
    )
    assert result.success
    assert result.manifest is not None
    excluded_ids = {item.instrument_id for item in result.manifest.epochs[0].excluded_members}
    assert ltc.instrument_id in excluded_ids


def test_delisted_instrument_excluded() -> None:
    snapshot = _ltc_with_delisting_snapshot(delisting_time=_BAR_CLOSE)
    ltc = snapshot.intervals[0]
    supplementary = (_supplementary(ltc.instrument_id, suffix="ltc"),)
    result = generate_pit_futures_universe_manifest_from_registry_binding_v1(
        _build_binding_input(snapshot=snapshot, supplementary=supplementary)
    )
    assert result.success
    assert result.manifest is not None
    excluded_ids = {item.instrument_id for item in result.manifest.epochs[0].excluded_members}
    assert ltc.instrument_id in excluded_ids


def test_listing_boundary_inclusive() -> None:
    listing = _BAR_CLOSE
    record = _source_record(
        base_asset="LTC", venue_symbol="LTC-USDT-SWAP", listing_time=listing, eligible_from=listing
    )
    snapshot = _assembled_snapshot(record)
    supplementary = (_supplementary(snapshot.intervals[0].instrument_id, suffix="ltc"),)
    result = generate_pit_futures_universe_manifest_from_registry_binding_v1(
        _build_binding_input(snapshot=snapshot, supplementary=supplementary)
    )
    assert result.success
    assert result.manifest is not None
    member_ids = {item.instrument_id for item in result.manifest.epochs[0].members}
    assert snapshot.intervals[0].instrument_id in member_ids


def test_delisting_boundary_exclusive() -> None:
    snapshot = _ltc_with_delisting_snapshot(delisting_time=_BAR_CLOSE)
    supplementary = (_supplementary(snapshot.intervals[0].instrument_id, suffix="ltc"),)
    result = generate_pit_futures_universe_manifest_from_registry_binding_v1(
        _build_binding_input(snapshot=snapshot, supplementary=supplementary)
    )
    assert result.success
    assert result.manifest is not None
    excluded_ids = {item.instrument_id for item in result.manifest.epochs[0].excluded_members}
    assert snapshot.intervals[0].instrument_id in excluded_ids


def test_unknown_supplementary_membership_fail_closed() -> None:
    snapshot, supplementary = _panel_registry()
    ghost = _supplementary("okx:linear_perpetual:GHOST:USDT:USDT:perp", suffix="ghost")
    result = generate_pit_futures_universe_manifest_from_registry_binding_v1(
        _build_binding_input(snapshot=snapshot, supplementary=supplementary + (ghost,))
    )
    assert not result.success
    assert RegistryBindingErrorCode.UNKNOWN_HISTORICAL_MEMBERSHIP.value in result.error_codes


def test_missing_registry_fail_closed() -> None:
    inp = _build_binding_input()
    broken = dataclasses.replace(inp, registry_snapshot=None)
    result = generate_pit_futures_universe_manifest_from_registry_binding_v1(broken)
    assert not result.success
    assert RegistryBindingErrorCode.MISSING_REGISTRY.value in result.error_codes


def test_corrupt_registry_fail_closed() -> None:
    snapshot, supplementary = _panel_registry()
    bad = dataclasses.replace(snapshot, registry_snapshot_digest="f" * 64)
    result = generate_pit_futures_universe_manifest_from_registry_binding_v1(
        _build_binding_input(snapshot=bad, supplementary=supplementary)
    )
    assert not result.success
    assert RegistryBindingErrorCode.CORRUPT_REGISTRY.value in result.error_codes


def test_digest_mismatch_fail_closed() -> None:
    snapshot, supplementary = _panel_registry()
    result = generate_pit_futures_universe_manifest_from_registry_binding_v1(
        _build_binding_input(
            snapshot=snapshot,
            supplementary=supplementary,
            bound_digest="f" * 64,
        )
    )
    assert not result.success
    assert RegistryBindingErrorCode.REGISTRY_DIGEST_MISMATCH.value in result.error_codes


def test_unsupported_registry_version_fail_closed() -> None:
    snapshot, supplementary = _panel_registry()
    result = generate_pit_futures_universe_manifest_from_registry_binding_v1(
        _build_binding_input(
            snapshot=snapshot,
            supplementary=supplementary,
            bound_version=999,
        )
    )
    assert not result.success
    assert RegistryBindingErrorCode.REGISTRY_VERSION_MISMATCH.value in result.error_codes


def test_current_state_fallback_blocked() -> None:
    snapshot, supplementary = _panel_registry()
    inp = _build_binding_input(snapshot=snapshot, supplementary=supplementary)
    broken = dataclasses.replace(inp, period_binding_ref="synthetic:use_current_state:v0")
    result = generate_pit_futures_universe_manifest_from_registry_binding_v1(broken)
    assert not result.success
    assert RegistryBindingErrorCode.CURRENT_STATE_FALLBACK_BLOCKED.value in result.error_codes


def test_registry_validation_before_consumption() -> None:
    snapshot, supplementary = _panel_registry()
    corrupt = dataclasses.replace(snapshot.intervals[0], eligible_from="2024-01-09T00:00:00Z")
    bad_snap = dataclasses.replace(snapshot, intervals=(corrupt, *snapshot.intervals[1:]))
    result = generate_pit_futures_universe_manifest_from_registry_binding_v1(
        _build_binding_input(snapshot=bad_snap, supplementary=supplementary)
    )
    assert not result.success
    assert RegistryBindingErrorCode.CORRUPT_REGISTRY.value in result.error_codes


def test_generator_does_not_mutate_registry_snapshot() -> None:
    snapshot, supplementary = _panel_registry()
    before = dumps_canonical(
        {
            "digest": snapshot.registry_snapshot_digest,
            "version": snapshot.registry_snapshot_version,
            "intervals": [interval.record_digest for interval in snapshot.intervals],
        }
    )
    generate_pit_futures_universe_manifest_from_registry_binding_v1(
        _build_binding_input(snapshot=snapshot, supplementary=supplementary)
    )
    after = dumps_canonical(
        {
            "digest": snapshot.registry_snapshot_digest,
            "version": snapshot.registry_snapshot_version,
            "intervals": [interval.record_digest for interval in snapshot.intervals],
        }
    )
    assert before == after


def test_deterministic_output_and_provenance() -> None:
    first = generate_pit_futures_universe_manifest_from_registry_binding_v1(_build_binding_input())
    second = generate_pit_futures_universe_manifest_from_registry_binding_v1(_build_binding_input())
    assert first.success and second.success
    assert first.manifest is not None and second.manifest is not None
    assert first.manifest.manifest_digest == second.manifest.manifest_digest
    assert first.provenance is not None and second.provenance is not None
    assert first.provenance.output_manifest_digest == second.provenance.output_manifest_digest
    assert first.provenance.binding_implementation_digest == compute_binding_implementation_digest()


def test_changed_registry_binding_changes_output_digest() -> None:
    snapshot, supplementary = _panel_registry()
    first = generate_pit_futures_universe_manifest_from_registry_binding_v1(
        _build_binding_input(snapshot=snapshot, supplementary=supplementary)
    )
    second_record = _source_record(base_asset="NEAR", venue_symbol="NEAR-USDT-SWAP")
    second_snapshot = _assembled_snapshot(*[_source_record(), second_record])
    second_supplementary = (
        _supplementary(second_snapshot.intervals[0].instrument_id, suffix="eth"),
        _supplementary(second_snapshot.intervals[1].instrument_id, suffix="near"),
    )
    second = generate_pit_futures_universe_manifest_from_registry_binding_v1(
        _build_binding_input(snapshot=second_snapshot, supplementary=second_supplementary)
    )
    assert first.success and second.success
    assert first.manifest is not None and second.manifest is not None
    assert first.manifest.manifest_digest != second.manifest.manifest_digest
    assert first.provenance is not None and second.provenance is not None
    assert first.provenance.registry_content_digest != second.provenance.registry_content_digest


def test_provenance_binds_registry_fields() -> None:
    snapshot, supplementary = _panel_registry()
    result = generate_pit_futures_universe_manifest_from_registry_binding_v1(
        _build_binding_input(snapshot=snapshot, supplementary=supplementary)
    )
    assert result.provenance is not None
    prov = result.provenance
    assert prov.registry_schema_version == SCHEMA_VERSION
    assert prov.registry_artifact_id == _REGISTRY_ARTIFACT_ID
    assert prov.registry_snapshot_version == snapshot.registry_snapshot_version
    assert prov.registry_content_digest == snapshot.registry_snapshot_digest
    assert prov.historical_as_of_times == (_BAR_CLOSE,)
    assert prov.output_manifest_digest == result.manifest.manifest_digest


def test_registry_reference_in_manifest_source_refs() -> None:
    result = generate_pit_futures_universe_manifest_from_registry_binding_v1(_build_binding_input())
    assert result.success and result.manifest is not None and result.provenance is not None
    assert result.provenance.registry_reference in result.manifest.source_dataset_refs


def test_persistence_read_only_consumer_no_registry_write(tmp_path: Path) -> None:
    snapshot, supplementary = _panel_registry()
    rel = Path("registry_snapshot.json")
    write_result = write_registry_snapshot_v1(
        snapshot,
        root_dir=tmp_path,
        relative_path=rel,
        overwrite_policy=OverwritePolicy.FAIL_IF_EXISTS,
    )
    assert write_result.success
    path = tmp_path / rel
    before_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    read_result = read_registry_snapshot_v1(root_dir=tmp_path, relative_path=rel)
    assert read_result.success and read_result.snapshot is not None
    result = generate_pit_futures_universe_manifest_from_registry_binding_v1(
        _build_binding_input(snapshot=read_result.snapshot, supplementary=supplementary)
    )
    assert result.success
    after_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    assert before_hash == after_hash


def test_binding_error_code_taxonomy_has_exactly_eleven_codes() -> None:
    assert len(RegistryBindingErrorCode) == 11


def test_slice_abc_regression_registry_validator_still_accepts_assembled() -> None:
    snapshot = _assembled_snapshot(_source_record())
    result = validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snapshot)
    assert result.verdict == ValidationVerdict.ACCEPTED


def test_unknown_historical_membership_query_fail_closed() -> None:
    snapshot = _assembled_snapshot(_source_record())
    query = query_lifecycle_at_snapshot_v1(
        snapshot,
        instrument_id="okx:linear_perpetual:MISSING:USDT:USDT:perp",
        query_instant=_BAR_CLOSE,
    )
    assert query.query_state == QueryState.UNKNOWN.value
