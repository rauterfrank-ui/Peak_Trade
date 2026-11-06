"""Contract tests for pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0."""

from __future__ import annotations

import copy
import dataclasses
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
)
from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (
    DATASET_ID,
    DATASET_SCHEMA_VERSION,
    MaterializationStatus,
    REASON_INSUFFICIENT_SPLIT_HISTORY,
    REASON_MISSING_PANEL_BARS,
    REASON_MISSING_SOURCE_REGISTRATION,
    REASON_PANEL_VALIDATION_FAILED,
    REASON_PERIOD_OVERLAP,
    REASON_UNIVERSE_MANIFEST_DIGEST_MISMATCH,
    compute_period_digest_v0,
    compute_semantic_data_digest_v0,
    load_split_policy_v0,
    materialize_cross_sectional_research_data_digest_and_period_split_v0,
)
from src.research.pit_futures_universe_manifest_dataset_period_binding_v0 import (
    BINDING_STATUS_BLOCKED,
    BINDING_STATUS_READY,
    ValidationVerdict,
    materialize_pit_futures_universe_manifest_dataset_period_binding_with_research_materialization_v0,
    validate_pit_futures_universe_manifest_dataset_period_binding_v0,
)
from src.research.pit_futures_universe_manifest_production_materialization_v1 import (
    DEFAULT_MINIMUM_HISTORY_BARS,
    DEFAULT_MINIMUM_REQUIRED_MEMBER_COUNT,
    EVALUATION_PERIOD_BINDING,
    EXCLUSION_POLICY_VERSION,
    INCLUSION_POLICY_VERSION,
    INPUT_CONTRACT_VERSION,
    MATERIALIZATION_VERSION,
    ProductionMaterializationEpochV1,
    PitFuturesUniverseManifestProductionMaterializationInputV1,
    assemble_production_registry_from_observations_v1,
    materialize_production_pit_futures_universe_manifest_v1,
)
from src.research.pit_futures_universe_manifest_v1 import manifest_to_dict
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    InstrumentPanelSeriesV1,
    PanelBarV1,
    PanelValidationErrorCode,
    build_panel_dataset_manifest_v1,
    compute_series_digest,
    panel_manifest_to_dict,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

_GENERATED_AT = "2026-07-03T04:00:00Z"
_BAR_CLOSE = "2024-06-01T01:00:00Z"
_PERIOD_START = "2024-05-25T00:00:00Z"
_PERIOD_END = _BAR_CLOSE
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


def _build_registry_and_panel(
    instruments: list[dict[str, str]],
) -> tuple[object, tuple[InstrumentPanelSeriesV1, ...], str]:
    from src.research.instrument_id_canonicalization_v1 import (
        InstrumentIdCanonicalizationInputV1,
        canonicalize_instrument_id_v1,
    )
    from src.research.okx_production_instrument_lifecycle_source_v1 import (
        build_lifecycle_source_observations_v1,
        build_okx_lifecycle_source_snapshot_v1,
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
        panel_series.append(
            InstrumentPanelSeriesV1(
                instrument_id=canon.instrument_id,
                native_instrument_id=metadata.inst_id,
                bars=_hourly_bars(canon.instrument_id, count=30, end=_BAR_CLOSE),
                series_digest="0" * 64,
            )
        )
    for index, series in enumerate(panel_series):
        panel_series[index] = InstrumentPanelSeriesV1(
            instrument_id=series.instrument_id,
            native_instrument_id=series.native_instrument_id,
            bars=series.bars,
            series_digest=compute_series_digest(series),
        )
    return registry, tuple(panel_series), snapshot.raw_snapshot_digest


def _default_instruments() -> list[dict[str, str]]:
    return [
        _live_inst("BTC"),
        *[_live_inst(base) for base in ("ETH", "SOL", "ADA", "DOT", "LINK", "AVAX")],
    ]


def _build_production_result():
    registry, panel_series, source_digest = _build_registry_and_panel(_default_instruments())
    inp = PitFuturesUniverseManifestProductionMaterializationInputV1(
        input_contract_version=INPUT_CONTRACT_VERSION,
        materialization_version=MATERIALIZATION_VERSION,
        generated_at=_GENERATED_AT,
        universe_policy_id="pit_okx_linear_usdt_non_bitcoin_perpetual_cross_sectional_universe",
        universe_policy_version="v1",
        inclusion_policy_version=INCLUSION_POLICY_VERSION,
        exclusion_policy_version=EXCLUSION_POLICY_VERSION,
        lifecycle_source_id="okx_production_instrument_lifecycle_historical_as_of_fail_closed.v1",
        lifecycle_source_snapshot_ref=_SOURCE_REF,
        lifecycle_source_snapshot_digest=source_digest,
        registry_artifact_id="okx_production_lifecycle_v1",
        registry_snapshot=registry,
        panel_series=panel_series,
        panel_dataset_ref="pit_okx_pt1h_panel_ohlcv_dataset_v1:test_panel:sha256:" + "a" * 64,
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
    result = materialize_production_pit_futures_universe_manifest_v1(inp)
    assert result.success is True
    assert result.manifest is not None and result.envelope is not None
    return result, panel_series


@pytest.fixture(scope="module")
def production_bundle():
    return _build_production_result()


def test_materialize_success_with_real_panel(production_bundle) -> None:
    production, panel_series = production_bundle
    policy = load_split_policy_v0(REPO_ROOT)
    result = materialize_cross_sectional_research_data_digest_and_period_split_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
        panel_series=panel_series,
        source_registration_ref=_SOURCE_REF,
        source_registration_digest=_SOURCE_DIGEST,
        split_policy=policy,
    )
    assert result.success is True
    assert result.dataset_envelope is not None
    assert result.period_split is not None
    assert (
        result.dataset_envelope.materialization_status == MaterializationStatus.MATERIALIZED.value
    )
    assert result.dataset_envelope.data_quality_status == "PASS"
    assert result.dataset_envelope.instrument_count >= 5
    assert all("btc" not in i.lower() for i in result.dataset_envelope.instrument_ids)
    assert result.dataset_envelope.data_digest == compute_semantic_data_digest_v0(
        series_list=panel_series,
        universe_manifest_digest=production.manifest.manifest_digest,
        source_registration_digest=_SOURCE_DIGEST,
        dataset_id=DATASET_ID,
        dataset_version="v1",
        dataset_schema_version=DATASET_SCHEMA_VERSION,
    )


def test_deterministic_data_digest(production_bundle) -> None:
    production, panel_series = production_bundle
    policy = load_split_policy_v0(REPO_ROOT)
    first = materialize_cross_sectional_research_data_digest_and_period_split_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
        panel_series=panel_series,
        source_registration_ref=_SOURCE_REF,
        source_registration_digest=_SOURCE_DIGEST,
        split_policy=policy,
    )
    second = materialize_cross_sectional_research_data_digest_and_period_split_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
        panel_series=panel_series,
        source_registration_ref=_SOURCE_REF,
        source_registration_digest=_SOURCE_DIGEST,
        split_policy=policy,
    )
    assert first.dataset_envelope is not None and second.dataset_envelope is not None
    assert first.dataset_envelope.data_digest == second.dataset_envelope.data_digest
    assert first.period_split is not None and second.period_split is not None
    assert first.period_split.period_digest == second.period_split.period_digest


def test_blocked_missing_panel(production_bundle) -> None:
    production, _ = production_bundle
    result = materialize_cross_sectional_research_data_digest_and_period_split_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
        panel_series=None,
        source_registration_ref=_SOURCE_REF,
        source_registration_digest=_SOURCE_DIGEST,
    )
    assert result.success is False
    assert result.dataset_envelope is not None
    assert result.dataset_envelope.materialization_status == MaterializationStatus.BLOCKED.value
    assert REASON_MISSING_PANEL_BARS in result.error_codes


def test_blocked_invalid_source_digest(production_bundle) -> None:
    production, panel_series = production_bundle
    result = materialize_cross_sectional_research_data_digest_and_period_split_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
        panel_series=panel_series,
        source_registration_ref=_SOURCE_REF,
        source_registration_digest="not-a-digest",
    )
    assert result.success is False
    assert REASON_MISSING_SOURCE_REGISTRATION in result.error_codes


def test_blocked_universe_digest_mismatch(production_bundle) -> None:
    production, panel_series = production_bundle
    tampered_envelope = dataclasses.replace(
        production.envelope,
        manifest_digest="f" * 64,
    )
    result = materialize_cross_sectional_research_data_digest_and_period_split_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=tampered_envelope,
        panel_series=panel_series,
        source_registration_ref=_SOURCE_REF,
        source_registration_digest=_SOURCE_DIGEST,
    )
    assert result.success is False
    assert REASON_UNIVERSE_MANIFEST_DIGEST_MISMATCH in result.error_codes


def test_bitcoin_instrument_rejected(production_bundle) -> None:
    production, panel_series = production_bundle
    btc_series = InstrumentPanelSeriesV1(
        instrument_id="okx:linear_perpetual:BTC:USDT:USDT:perp",
        native_instrument_id="BTC-USDT-SWAP",
        bars=panel_series[0].bars,
        series_digest=compute_series_digest(panel_series[0]),
    )
    result = materialize_cross_sectional_research_data_digest_and_period_split_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
        panel_series=(btc_series, *panel_series[1:6]),
        source_registration_ref=_SOURCE_REF,
        source_registration_digest=_SOURCE_DIGEST,
    )
    assert result.success is False
    assert PanelValidationErrorCode.BITCOIN_INSTRUMENT_PRESENT.value in result.error_codes


def test_duplicate_bars_blocked(production_bundle) -> None:
    production, panel_series = production_bundle
    series = panel_series[0]
    dup_bar = series.bars[0]
    dup_series = InstrumentPanelSeriesV1(
        instrument_id=series.instrument_id,
        native_instrument_id=series.native_instrument_id,
        bars=(dup_bar, dup_bar, *series.bars[2:]),
        series_digest="0" * 64,
    )
    dup_series = InstrumentPanelSeriesV1(
        instrument_id=dup_series.instrument_id,
        native_instrument_id=dup_series.native_instrument_id,
        bars=dup_series.bars,
        series_digest=compute_series_digest(dup_series),
    )
    result = materialize_cross_sectional_research_data_digest_and_period_split_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
        panel_series=(dup_series, *panel_series[1:6]),
        source_registration_ref=_SOURCE_REF,
        source_registration_digest=_SOURCE_DIGEST,
    )
    assert result.success is False
    assert REASON_PANEL_VALIDATION_FAILED in result.error_codes


def test_overlapping_splits_blocked(production_bundle) -> None:
    production, panel_series = production_bundle
    policy = dict(load_split_policy_v0(REPO_ROOT))
    policy["validation_start"] = policy["training_start"]
    result = materialize_cross_sectional_research_data_digest_and_period_split_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
        panel_series=panel_series,
        source_registration_ref=_SOURCE_REF,
        source_registration_digest=_SOURCE_DIGEST,
        split_policy=policy,
    )
    assert result.success is False
    assert REASON_PERIOD_OVERLAP in result.error_codes


def test_insufficient_split_history_blocked(production_bundle) -> None:
    production, panel_series = production_bundle
    policy = dict(load_split_policy_v0(REPO_ROOT))
    policy["minimum_required_rows"] = 999
    result = materialize_cross_sectional_research_data_digest_and_period_split_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
        panel_series=panel_series,
        source_registration_ref=_SOURCE_REF,
        source_registration_digest=_SOURCE_DIGEST,
        split_policy=policy,
    )
    assert result.success is False
    assert any(REASON_INSUFFICIENT_SPLIT_HISTORY in code for code in result.error_codes)


def test_period_split_shared_across_fleet(production_bundle) -> None:
    production, panel_series = production_bundle
    policy = load_split_policy_v0(REPO_ROOT)
    result = materialize_cross_sectional_research_data_digest_and_period_split_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
        panel_series=panel_series,
        source_registration_ref=_SOURCE_REF,
        source_registration_digest=_SOURCE_DIGEST,
        split_policy=policy,
    )
    assert result.period_split is not None
    assert result.period_split.candidate_applicability == tuple(sid for sid, _ in FLEET_CANDIDATES)


def test_binding_upgrade_ready(production_bundle) -> None:
    production, panel_series = production_bundle
    research = materialize_cross_sectional_research_data_digest_and_period_split_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
        panel_series=panel_series,
        source_registration_ref=_SOURCE_REF,
        source_registration_digest=_SOURCE_DIGEST,
    )
    contract = materialize_pit_futures_universe_manifest_dataset_period_binding_with_research_materialization_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
        research_materialization_result=research,
    )
    assert contract["binding_materialization_status"] == BINDING_STATUS_READY
    assert len(contract["candidates"]) == 3
    for candidate in contract["candidates"]:
        assert candidate["binding_status"] == BINDING_STATUS_READY
        assert candidate["data_digest"]["status"] == "MATERIALIZED"
        assert candidate["training_period"]["status"] == "MATERIALIZED"
        assert candidate["validation_period"]["status"] == "MATERIALIZED"
        assert candidate["out_of_sample_period"]["status"] == "MATERIALIZED"
    validation = validate_pit_futures_universe_manifest_dataset_period_binding_v0(
        contract,
        repo_root=REPO_ROOT,
        expected_manifest=production.manifest,
        expected_envelope=production.envelope,
    )
    assert validation.valid is True
    assert validation.verdict == ValidationVerdict.ACCEPTED


def test_data_digest_tampering_detected(production_bundle) -> None:
    production, panel_series = production_bundle
    research = materialize_cross_sectional_research_data_digest_and_period_split_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
        panel_series=panel_series,
        source_registration_ref=_SOURCE_REF,
        source_registration_digest=_SOURCE_DIGEST,
    )
    assert research.dataset_envelope is not None
    tampered = copy.deepcopy(research)
    tampered_env = dataclasses.replace(
        research.dataset_envelope,
        data_digest="f" * 64,
    )
    tampered = dataclasses.replace(tampered, dataset_envelope=tampered_env)
    recomputed = compute_semantic_data_digest_v0(
        series_list=panel_series,
        universe_manifest_digest=production.manifest.manifest_digest,
        source_registration_digest=_SOURCE_DIGEST,
        dataset_id=DATASET_ID,
        dataset_version="v1",
        dataset_schema_version=DATASET_SCHEMA_VERSION,
    )
    assert tampered_env.data_digest != recomputed


def test_period_digest_tampering_detected(production_bundle) -> None:
    production, panel_series = production_bundle
    policy = load_split_policy_v0(REPO_ROOT)
    research = materialize_cross_sectional_research_data_digest_and_period_split_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
        panel_series=panel_series,
        source_registration_ref=_SOURCE_REF,
        source_registration_digest=_SOURCE_DIGEST,
        split_policy=policy,
    )
    assert research.dataset_envelope is not None and research.period_split is not None
    expected = compute_period_digest_v0(
        policy=policy,
        data_digest=research.dataset_envelope.data_digest,
        dataset_id=research.dataset_envelope.dataset_id,
        dataset_version=research.dataset_envelope.dataset_version,
    )
    assert research.period_split.period_digest == expected
    assert research.period_split.period_digest != ("f" * 64)


def test_write_panel_manifest_roundtrip(production_bundle, tmp_path: Path) -> None:
    production, panel_series = production_bundle
    manifest = build_panel_dataset_manifest_v1(
        series_list=panel_series,
        lifecycle_registry_ref="registry:test",
        lifecycle_registry_digest=_REGISTRY_CONFIG,
        period_start_utc=_PERIOD_START,
        period_end_utc=_PERIOD_END,
        config_digest=_REGISTRY_CONFIG,
        source_provenance_digest=_SOURCE_DIGEST,
    )
    panel_dir = tmp_path / "panel"
    panel_dir.mkdir()
    (panel_dir / "panel_dataset_manifest.json").write_text(
        json.dumps(panel_manifest_to_dict(manifest), indent=2) + "\n",
        encoding="utf-8",
    )
    rows = []
    for series in panel_series:
        for bar in series.bars:
            rows.append(
                {
                    "instrument_id": bar.instrument_id,
                    "timestamp_utc": bar.timestamp_utc,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                    "is_final": bar.is_final,
                }
            )
    (panel_dir / "normalized_panel_bars.json").write_text(json.dumps(rows) + "\n", encoding="utf-8")
    universe_dir = tmp_path / "universe"
    universe_dir.mkdir()
    (universe_dir / "pit_futures_universe_manifest_v1.json").write_text(
        json.dumps(manifest_to_dict(production.manifest), indent=2) + "\n",
        encoding="utf-8",
    )
    from src.research.pit_futures_universe_manifest_production_materialization_v1 import (
        production_materialization_envelope_to_dict,
    )

    (universe_dir / "production_materialization_envelope_v1.json").write_text(
        json.dumps(production_materialization_envelope_to_dict(production.envelope), indent=2)
        + "\n",
        encoding="utf-8",
    )
    lifecycle_dir = tmp_path / "lifecycle"
    lifecycle_dir.mkdir()
    (lifecycle_dir / "SOURCE_REGISTRATION.json").write_text(
        json.dumps(
            {
                "source_snapshot_ref": _SOURCE_REF,
                "source_snapshot_digest": _SOURCE_DIGEST,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    from scripts.ops.materialize_pit_futures_cross_sectional_research_data_digest_period_split_v0 import (
        CONFIRM_GO,
        run_materialization,
    )

    payload = run_materialization(
        confirm=CONFIRM_GO,
        staging_root=tmp_path,
        durable_evidence_root=tmp_path / "evidence",
    )
    assert payload["materialization_status"] == MaterializationStatus.MATERIALIZED.value
    assert payload["binding_materialization_status"] == BINDING_STATUS_READY
