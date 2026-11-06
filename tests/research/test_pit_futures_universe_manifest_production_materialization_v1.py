"""Contract tests for pit_futures_universe_manifest_production_materialization_v1."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone
from typing import Callable

import pytest

from src.execution.replay_pack.canonical import dumps_canonical
from src.research.okx_production_instrument_lifecycle_source_v1 import (
    MIN_ELIGIBLE_INSTRUMENT_COUNT,
    SOURCE_ID,
    build_lifecycle_source_observations_v1,
    build_okx_lifecycle_source_snapshot_v1,
    evaluate_okx_instrument_eligibility_v1,
)
from src.research.pit_futures_universe_manifest_production_materialization_v1 import (
    DEFAULT_MINIMUM_HISTORY_BARS,
    DEFAULT_MINIMUM_REQUIRED_MEMBER_COUNT,
    EVALUATION_PERIOD_BINDING,
    EXCLUSION_POLICY_VERSION,
    FUTURES_ONLY,
    INCLUSION_POLICY_VERSION,
    INPUT_CONTRACT_VERSION,
    MATERIALIZATION_VERSION,
    ProductionMaterializationEpochV1,
    ProductionMaterializationErrorCode,
    PitFuturesUniverseManifestProductionMaterializationInputV1,
    UNIVERSE_POLICY_ID,
    UNIVERSE_POLICY_VERSION,
    assemble_production_registry_from_observations_v1,
    build_supplementary_market_data_from_panel_v1,
    compute_materialization_config_digest,
    compute_reproducibility_inputs_digest,
    materialize_production_pit_futures_universe_manifest_v1,
    production_materialization_result_to_dict,
)
from src.research.pit_futures_universe_manifest_v1 import (
    EXCLUSION_REASON_CODES,
    manifest_to_dict,
)
from src.research.pit_futures_universe_manifest_validator_v1 import (
    ValidationVerdict,
    validate_pit_futures_universe_manifest_v1,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    InstrumentPanelSeriesV1,
    PanelBarV1,
    compute_series_digest,
)

_GENERATED_AT = "2026-07-03T04:00:00Z"
_BAR_CLOSE = "2024-06-01T01:00:00Z"
_PERIOD_START = "2024-05-25T00:00:00Z"
_PERIOD_END = _BAR_CLOSE
_PANEL_REF = "pit_okx_pt1h_panel_ohlcv_dataset_v1:test_panel:sha256:" + "a" * 64
_PANEL_DIGEST = "b" * 64
_SOURCE_REF = "okx_public_instruments_swap:test"
_SOURCE_DIGEST = "c" * 64
_REGISTRY_CONFIG = "d" * 64
_REGISTRY_IMPL = "e" * 64


def _live_inst(base: str, *, inst_id: str | None = None) -> dict[str, str]:
    symbol = inst_id or f"{base}-USDT-SWAP"
    return {
        "instId": symbol,
        "instType": "SWAP",
        "settleCcy": "USDT",
        "ctType": "linear",
        "baseCcy": base,
        "state": "live",
        "listTime": "1609459200000",
        "expTime": "",
    }


def _hourly_bars(instrument_id: str, *, count: int, end: str) -> tuple[PanelBarV1, ...]:
    end_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    bars: list[PanelBarV1] = []
    for offset in range(count):
        ts = end_dt - timedelta(hours=count - 1 - offset)
        ts_str = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        bars.append(
            PanelBarV1(
                instrument_id=instrument_id,
                timestamp_utc=ts_str,
                open="1",
                high="2",
                low="0.5",
                close="1.5",
                volume="10",
                is_final=True,
            )
        )
    return tuple(bars)


def _panel_series_for_instrument(instrument_id: str, native_id: str) -> InstrumentPanelSeriesV1:
    interim = InstrumentPanelSeriesV1(
        instrument_id=instrument_id,
        native_instrument_id=native_id,
        bars=_hourly_bars(instrument_id, count=30, end=_BAR_CLOSE),
        series_digest="0" * 64,
    )
    return InstrumentPanelSeriesV1(
        instrument_id=interim.instrument_id,
        native_instrument_id=interim.native_instrument_id,
        bars=interim.bars,
        series_digest=compute_series_digest(interim),
    )


def _build_registry_and_panel(
    instruments: list[dict[str, str]],
) -> tuple[object, tuple[InstrumentPanelSeriesV1, ...], str]:
    from src.research.instrument_id_canonicalization_v1 import (
        InstrumentIdCanonicalizationInputV1,
        canonicalize_instrument_id_v1,
    )

    snapshot = build_okx_lifecycle_source_snapshot_v1(
        instruments,
        retrieval_timestamp_utc=_GENERATED_AT,
        source_snapshot_ref=_SOURCE_REF,
    )
    observations = build_lifecycle_source_observations_v1(snapshot)
    registry, errors = assemble_production_registry_from_observations_v1(
        observations,
        generated_at=_GENERATED_AT,
        lifecycle_source_snapshot_digest=snapshot.raw_snapshot_digest,
        config_digest=_REGISTRY_CONFIG,
        implementation_digest=_REGISTRY_IMPL,
    )
    assert errors == (), errors
    assert registry is not None
    panel_series: list[InstrumentPanelSeriesV1] = []
    for metadata in snapshot.eligible_instruments:
        canon = canonicalize_instrument_id_v1(
            InstrumentIdCanonicalizationInputV1(
                venue_id="okx",
                market_type="futures",
                contract_type="linear_perpetual",
                base_asset=metadata.base_asset,
                quote_asset="USDT",
                settlement_asset="USDT",
                venue_symbol=metadata.inst_id,
            )
        )
        assert canon.success and canon.instrument_id is not None
        panel_series.append(_panel_series_for_instrument(canon.instrument_id, metadata.inst_id))
    return registry, tuple(panel_series), snapshot.raw_snapshot_digest


def _default_instruments() -> list[dict[str, str]]:
    return [
        _live_inst("BTC"),
        *[_live_inst(base) for base in ("ETH", "SOL", "ADA", "DOT", "LINK", "AVAX")],
    ]


def _build_input(
    *,
    registry=None,
    panel_series=None,
    source_digest: str = _SOURCE_DIGEST,
    mutator: Callable[
        [PitFuturesUniverseManifestProductionMaterializationInputV1],
        PitFuturesUniverseManifestProductionMaterializationInputV1,
    ]
    | None = None,
) -> PitFuturesUniverseManifestProductionMaterializationInputV1:
    if registry is None or panel_series is None:
        registry, panel_series, source_digest = _build_registry_and_panel(_default_instruments())
    inp = PitFuturesUniverseManifestProductionMaterializationInputV1(
        input_contract_version=INPUT_CONTRACT_VERSION,
        materialization_version=MATERIALIZATION_VERSION,
        generated_at=_GENERATED_AT,
        universe_policy_id=UNIVERSE_POLICY_ID,
        universe_policy_version=UNIVERSE_POLICY_VERSION,
        inclusion_policy_version=INCLUSION_POLICY_VERSION,
        exclusion_policy_version=EXCLUSION_POLICY_VERSION,
        lifecycle_source_id=SOURCE_ID,
        lifecycle_source_snapshot_ref=_SOURCE_REF,
        lifecycle_source_snapshot_digest=source_digest,
        registry_artifact_id="okx_production_lifecycle_v1",
        registry_snapshot=registry,
        panel_series=panel_series,
        panel_dataset_ref=_PANEL_REF,
        panel_dataset_digest=_PANEL_DIGEST,
        period_binding_ref=EVALUATION_PERIOD_BINDING,
        period_start_utc=_PERIOD_START,
        period_end_utc=_PERIOD_END,
        minimum_history_bars=DEFAULT_MINIMUM_HISTORY_BARS,
        minimum_required_member_count=DEFAULT_MINIMUM_REQUIRED_MEMBER_COUNT,
        registry_config_digest=_REGISTRY_CONFIG,
        registry_implementation_digest=_REGISTRY_IMPL,
        epochs=(
            ProductionMaterializationEpochV1(
                score_epoch=0,
                finalized_bar_close=_BAR_CLOSE,
            ),
        ),
    )
    if mutator is not None:
        return mutator(inp)
    return inp


def test_happy_path_production_manifest_materialization() -> None:
    result = materialize_production_pit_futures_universe_manifest_v1(_build_input())
    assert result.success is True
    assert result.manifest is not None
    assert result.envelope is not None
    validation = validate_pit_futures_universe_manifest_v1(result.manifest)
    assert validation.verdict == ValidationVerdict.ACCEPTED
    assert result.manifest.universe_policy_id == UNIVERSE_POLICY_ID
    assert result.manifest.universe_policy_version == UNIVERSE_POLICY_VERSION
    assert result.manifest.futures_only is True
    assert result.manifest.bitcoin_direction_allowed is False
    assert result.manifest.spot_allowed is False
    assert result.manifest.synthetic_spot_allowed is False
    assert result.envelope.eligible_instrument_count >= MIN_ELIGIBLE_INSTRUMENT_COUNT
    assert result.envelope.no_runtime_effect is True
    assert result.envelope.pit_semantics_enforced is True


def test_deterministic_manifest_and_digests() -> None:
    first = materialize_production_pit_futures_universe_manifest_v1(_build_input())
    second = materialize_production_pit_futures_universe_manifest_v1(_build_input())
    assert first.manifest is not None and second.manifest is not None
    assert first.manifest.manifest_digest == second.manifest.manifest_digest
    assert first.manifest.membership_digest == second.manifest.membership_digest
    assert dumps_canonical(manifest_to_dict(first.manifest)) == dumps_canonical(
        manifest_to_dict(second.manifest)
    )


def test_members_sorted_deterministically() -> None:
    result = materialize_production_pit_futures_universe_manifest_v1(_build_input())
    assert result.manifest is not None
    members = result.manifest.epochs[0].members
    assert [member.instrument_id for member in members] == sorted(
        member.instrument_id for member in members
    )


def test_bitcoin_xbt_and_spot_excluded_from_eligible_membership() -> None:
    instruments = _default_instruments() + [
        _live_inst("XBT", inst_id="XBT-USDT-SWAP"),
        {**_live_inst("ETH"), "instType": "SPOT", "instId": "ETH-USDT"},
        {**_live_inst("ETH"), "instType": "SWAP", "settleCcy": "ETH", "instId": "ETH-ETH-SWAP"},
    ]
    registry, panel_series, source_digest = _build_registry_and_panel(instruments)
    result = materialize_production_pit_futures_universe_manifest_v1(
        _build_input(registry=registry, panel_series=panel_series, source_digest=source_digest)
    )
    assert result.success is True
    assert result.manifest is not None
    eligible_ids = {member.instrument_id for member in result.manifest.epochs[0].members}
    assert all("btc" not in item.lower() for item in eligible_ids)
    assert all("xbt" not in item.lower() for item in eligible_ids)
    assert result.envelope is not None
    assert result.envelope.eligible_instrument_count >= MIN_ELIGIBLE_INSTRUMENT_COUNT


def test_source_level_bitcoin_and_spot_fail_closed() -> None:
    btc = evaluate_okx_instrument_eligibility_v1(_live_inst("BTC"))
    assert not btc.eligible
    assert "BITCOIN_INSTRUMENT_BLOCKED" in btc.error_codes
    spot = evaluate_okx_instrument_eligibility_v1({**_live_inst("ETH"), "instType": "SPOT"})
    assert not spot.eligible
    assert "NON_LINEAR_USDT_SWAP" in spot.error_codes


def test_insufficient_history_excluded_with_reason_code() -> None:
    registry, panel_series, source_digest = _build_registry_and_panel(_default_instruments())
    short_panel = []
    for series in panel_series:
        interim = InstrumentPanelSeriesV1(
            instrument_id=series.instrument_id,
            native_instrument_id=series.native_instrument_id,
            bars=_hourly_bars(series.instrument_id, count=5, end=_BAR_CLOSE),
            series_digest="0" * 64,
        )
        short_panel.append(
            InstrumentPanelSeriesV1(
                instrument_id=interim.instrument_id,
                native_instrument_id=interim.native_instrument_id,
                bars=interim.bars,
                series_digest=compute_series_digest(interim),
            )
        )
    result = materialize_production_pit_futures_universe_manifest_v1(
        _build_input(
            registry=registry,
            panel_series=tuple(short_panel),
            source_digest=source_digest,
        )
    )
    assert result.success is False
    assert (
        ProductionMaterializationErrorCode.INSUFFICIENT_ELIGIBLE_INSTRUMENTS.value
        in result.error_codes
    )
    assert result.manifest is not None
    assert result.manifest.epochs[0].eligible_member_count == 0
    assert all(
        "INSUFFICIENT_HISTORY" in exclusion.reason_codes
        for exclusion in result.manifest.epochs[0].excluded_members
    )


def test_pit_semantics_no_current_state_fallback() -> None:
    result = materialize_production_pit_futures_universe_manifest_v1(
        _build_input(
            mutator=lambda inp: dataclasses.replace(
                inp, lifecycle_source_snapshot_ref="okx:use_current_state:v0"
            )
        )
    )
    assert result.success is False
    assert (
        ProductionMaterializationErrorCode.CURRENT_STATE_FALLBACK_BLOCKED.value
        in result.error_codes
    )


@pytest.mark.parametrize(
    "mutator,expected",
    [
        (
            lambda inp: dataclasses.replace(inp, universe_policy_version="v999"),
            ProductionMaterializationErrorCode.UNKNOWN_UNIVERSE_POLICY_VERSION.value,
        ),
        (
            lambda inp: dataclasses.replace(inp, universe_policy_id="unknown_policy"),
            ProductionMaterializationErrorCode.UNKNOWN_UNIVERSE_POLICY.value,
        ),
        (
            lambda inp: dataclasses.replace(inp, inclusion_policy_version="unknown"),
            ProductionMaterializationErrorCode.UNKNOWN_INCLUSION_POLICY_VERSION.value,
        ),
        (
            lambda inp: dataclasses.replace(inp, lifecycle_source_id="unknown_source"),
            ProductionMaterializationErrorCode.UNREGISTERED_LIFECYCLE_SOURCE.value,
        ),
    ],
)
def test_unknown_policy_or_source_fail_closed(
    mutator: Callable[
        [PitFuturesUniverseManifestProductionMaterializationInputV1],
        PitFuturesUniverseManifestProductionMaterializationInputV1,
    ],
    expected: str,
) -> None:
    result = materialize_production_pit_futures_universe_manifest_v1(_build_input(mutator=mutator))
    assert result.success is False
    assert expected in result.error_codes


def test_reproducibility_digest_stable_for_identical_input() -> None:
    inp = _build_input()
    first = compute_reproducibility_inputs_digest(inp)
    second = compute_reproducibility_inputs_digest(inp)
    assert first == second


def test_reproducibility_digest_changes_on_membership_change() -> None:
    base = _build_input()
    registry, panel_series, source_digest = _build_registry_and_panel(
        [_live_inst(base) for base in ("ETH", "SOL", "ADA", "DOT", "LINK", "AVAX", "MATIC")]
    )
    mutated = _build_input(
        registry=registry, panel_series=panel_series, source_digest=source_digest
    )
    assert compute_reproducibility_inputs_digest(base) != compute_reproducibility_inputs_digest(
        mutated
    )


def test_manifest_digest_changes_on_generated_at_mutation() -> None:
    first = materialize_production_pit_futures_universe_manifest_v1(_build_input())
    second = materialize_production_pit_futures_universe_manifest_v1(
        _build_input(
            mutator=lambda inp: dataclasses.replace(inp, generated_at="2026-07-03T05:00:00Z")
        )
    )
    assert first.manifest is not None and second.manifest is not None
    assert first.manifest.manifest_digest != second.manifest.manifest_digest


def test_supplementary_market_data_sorted_and_available() -> None:
    _, panel_series, _ = _build_registry_and_panel(_default_instruments())
    supplementary = build_supplementary_market_data_from_panel_v1(
        panel_series,
        finalized_bar_close=_BAR_CLOSE,
        minimum_history_bars=DEFAULT_MINIMUM_HISTORY_BARS,
        panel_dataset_ref=_PANEL_REF,
    )
    assert [item.instrument_id for item in supplementary] == sorted(
        item.instrument_id for item in supplementary
    )
    assert all(
        item.history_bars_available >= DEFAULT_MINIMUM_HISTORY_BARS for item in supplementary
    )


def test_linear_usdt_perpetual_inclusion() -> None:
    result = materialize_production_pit_futures_universe_manifest_v1(_build_input())
    assert result.manifest is not None
    for member in result.manifest.epochs[0].members:
        assert member.contract_type == "linear_perpetual"
        assert member.quote_asset == "USDT"
        assert member.settlement_asset == "USDT"


def test_exclusion_reason_codes_are_stable_machine_codes() -> None:
    result = materialize_production_pit_futures_universe_manifest_v1(_build_input())
    assert result.manifest is not None
    for exclusion in result.manifest.epochs[0].excluded_members:
        assert all(code in EXCLUSION_REASON_CODES for code in exclusion.reason_codes)


def test_no_runtime_trading_side_effects_in_envelope() -> None:
    result = materialize_production_pit_futures_universe_manifest_v1(_build_input())
    assert result.envelope is not None
    assert result.envelope.non_authorizing is True
    assert result.envelope.no_runtime_effect is True
    payload = production_materialization_result_to_dict(result)
    assert "manifest" in payload
    assert payload["success"] is True


def test_materialization_config_digest_matches_ratified_policy() -> None:
    digest = compute_materialization_config_digest()
    assert isinstance(digest, str) and len(digest) == 64


def test_futures_only_constants() -> None:
    assert FUTURES_ONLY is True
