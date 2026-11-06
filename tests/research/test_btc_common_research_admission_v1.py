"""Common generic admission and explicit historical cohort identity are distinct."""

from dataclasses import fields, replace

import pytest

from src.research.pit_futures_instrument_lifecycle_registry_v1 import (
    assemble_registry_snapshot_v1,
    attach_snapshot_digest,
    compute_interval_digest,
    compute_observation_digest,
)
from src.research.pit_futures_instrument_lifecycle_registry_validator_v1 import (
    validate_pit_futures_instrument_lifecycle_registry_snapshot_v1,
)
from src.research.pit_futures_universe_manifest_generator_v1 import (
    PitFuturesUniverseManifestGeneratorInputV1,
    compute_generator_config_digest,
)
from src.research.pit_futures_universe_manifest_generator_registry_consumer_binding_v1 import (
    generate_pit_futures_universe_manifest_from_registry_binding_v1,
)
from src.research.pit_futures_universe_manifest_production_materialization_v1 import (
    ProductionMaterializationErrorCode,
    assemble_production_registry_from_observations_v1,
    materialize_production_pit_futures_universe_manifest_v1,
)
from tests.research.test_pit_futures_universe_manifest_generator_registry_consumer_binding_v1 import (
    _assembled_snapshot,
    _build_binding_input,
    _source_record,
    _supplementary,
)
from tests.research.test_pit_futures_universe_manifest_production_materialization_v1 import (
    SOURCE_ID,
    _build_input,
)


def _common_research_request(asset, *, history=30, listing_time=None):
    records = [
        _source_record(base_asset=base, venue_symbol=f"{base}-USDT-SWAP")
        for base in ("SOL", "ADA", "DOT", "LINK", "AVAX")
    ]
    overrides = {"base_asset": asset, "venue_symbol": f"{asset}-USDT-SWAP"}
    if listing_time is not None:
        overrides.update(listing_time=listing_time, eligible_from=listing_time)
    records.append(_source_record(**overrides))
    snapshot = _assembled_snapshot(*records)
    assert validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snapshot).valid
    supplementary = tuple(
        _supplementary(
            item.instrument_id,
            suffix=item.base_asset.lower(),
            history=history if item.base_asset == asset else 30,
        )
        for item in snapshot.intervals
    )
    request = replace(
        _build_binding_input(snapshot=snapshot, supplementary=supplementary),
        universe_id="synthetic_common_futures_research_v1",
        hypothesis_id="SYNTHETIC_COMMON_FUTURES_ADMISSION_V1",
        universe_policy_id="synthetic_common_futures_research_v1",
    )
    generator = PitFuturesUniverseManifestGeneratorInputV1(
        **{f.name: getattr(request, f.name) for f in fields(PitFuturesUniverseManifestGeneratorInputV1)}
    )
    return replace(request, config_digest=compute_generator_config_digest(generator))


@pytest.mark.parametrize("asset", ["ETH", "BTC", "SUI", "XBT", "WBTC"])
def test_actual_registry_to_manifest_chain_uses_common_asset_admission(asset):
    request = _common_research_request(asset)
    result = generate_pit_futures_universe_manifest_from_registry_binding_v1(request)
    assert result.success, (result.error_codes, result.validator_reason_codes)
    assert any(member.base_asset == asset for member in result.manifest.epochs[0].members)
    assert result.manifest.non_authorizing is True
    assert result.manifest.research_binding_only is True
    assert result.manifest.bitcoin_direction_allowed is False
    assert result.manifest.universe_policy_id == "synthetic_common_futures_research_v1"


@pytest.mark.parametrize("asset", ["ETH", "BTC", "SUI"])
@pytest.mark.parametrize("condition", ["short_history", "not_yet_listed"])
def test_common_assets_still_require_history_and_point_in_time_eligibility(asset, condition):
    request = _common_research_request(
        asset,
        history=0 if condition == "short_history" else 30,
        listing_time="2024-07-01T00:00:00Z" if condition == "not_yet_listed" else None,
    )
    result = generate_pit_futures_universe_manifest_from_registry_binding_v1(request)
    assert result.success, result.error_codes
    epoch = result.manifest.epochs[0]
    assert not any(member.base_asset == asset for member in epoch.members)
    assert any(f":{asset}:" in member.instrument_id and member.reason_codes for member in epoch.excluded_members)


def test_legacy_named_non_bitcoin_materializer_rejects_injected_btc_cohort_member():
    original = _build_input()
    interval = replace(
        original.registry_snapshot.intervals[0],
        base_asset="BTC",
        venue_symbol="BTC-USDT-SWAP",
        instrument_id="okx:linear_perpetual:BTC:USDT:USDT:perp",
    )
    interval = replace(interval, record_digest=compute_interval_digest(interval))
    snapshot = attach_snapshot_digest(
        replace(
            original.registry_snapshot,
            intervals=tuple(sorted((*original.registry_snapshot.intervals, interval), key=lambda x: x.instrument_id)),
        )
    )
    assert validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(snapshot).valid
    result = materialize_production_pit_futures_universe_manifest_v1(
        replace(original, registry_snapshot=snapshot)
    )
    assert not result.success
    assert result.error_codes == (ProductionMaterializationErrorCode.REGISTRY_VALIDATION_FAILED.value,)


def test_legacy_named_cohort_assembly_rejects_btc_after_generic_assembly_accepts_it():
    record = replace(
        _source_record(base_asset="BTC", venue_symbol="BTC-USDT-SWAP"),
        source_id=SOURCE_ID,
    )
    record = replace(record, observation_digest=compute_observation_digest(record))
    kwargs = dict(
        generated_at="2026-07-03T03:00:00Z",
        config_digest="b" * 64,
        implementation_digest="c" * 64,
    )
    generic = assemble_registry_snapshot_v1(
        (record,),
        venue_scope=("okx",),
        registered_sources=frozenset({SOURCE_ID}),
        approved_snapshot_digests=frozenset({record.source_snapshot_digest}),
        **kwargs,
    )
    assert generic.success, generic.error_codes
    assert validate_pit_futures_instrument_lifecycle_registry_snapshot_v1(generic.snapshot).valid
    snapshot, errors = assemble_production_registry_from_observations_v1(
        (record,), lifecycle_source_snapshot_digest=record.source_snapshot_digest, **kwargs
    )
    assert snapshot is None
    assert errors == (ProductionMaterializationErrorCode.REGISTRY_VALIDATION_FAILED.value,)
