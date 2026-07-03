"""Contract tests for pit_futures_universe_manifest_dataset_period_binding_v0."""

from __future__ import annotations

import copy
import dataclasses
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
)
from src.research.okx_production_instrument_lifecycle_source_v1 import (
    MIN_ELIGIBLE_INSTRUMENT_COUNT,
    build_lifecycle_source_observations_v1,
    build_okx_lifecycle_source_snapshot_v1,
)
from src.research.pit_futures_universe_manifest_dataset_period_binding_v0 import (
    AUTHORITY_EFFECT,
    BINDING_STATUS_NOT_READY,
    CANDIDATE_BINDING_VERSION,
    DATASET_BINDING_VERSION,
    FLEET_ID,
    INSTRUMENT_BINDING_VERSION,
    NOT_YET_MATERIALIZED,
    ORDER_EFFECT,
    PERIOD_BINDING_VERSION,
    REASON_BITCOIN_INSTRUMENT_PRESENT,
    REASON_BINDING_REPAIR_REJECTED,
    REASON_DATA_DIGEST_NOT_MATERIALIZED,
    REASON_DUPLICATE_CANDIDATE,
    REASON_EFFECT_NOT_NONE,
    REASON_ENVELOPE_MANIFEST_DIGEST_MISMATCH,
    REASON_EXTRA_CANDIDATE,
    REASON_MANIFEST_TAMPERED,
    REASON_MISSING_CANDIDATE,
    REASON_MISSING_PANEL_DATASET_DIGEST,
    REASON_MISSING_PERIOD_COVERAGE,
    REASON_MISSING_REQUIRED_FIELD,
    REASON_PERIOD_SPLIT_NOT_MATERIALIZED,
    REASON_PRODUCTION_MANIFEST_DIGEST_MISMATCH,
    REASON_SHARED_BINDING_MISMATCH,
    REASON_SPOT_BINDING,
    REASON_SYNTHETIC_SPOT_BINDING,
    REASON_UNKNOWN_SCHEMA_VERSION,
    REASON_UNKNOWN_STRATEGY,
    REASON_WRONG_CONFIG_DIGEST,
    REASON_WRONG_CONTRACT_DIGEST,
    REASON_WRONG_IMPLEMENTATION_DIGEST,
    REASON_WRONG_PARAMETER_BINDING,
    REASON_WRONG_STRATEGY_VERSION,
    REASON_ZERO_FEE,
    REASON_ZERO_SLIPPAGE,
    RUNTIME_EFFECT,
    SCHEMA_VERSION,
    UNIVERSE_POLICY_ID,
    UNIVERSE_POLICY_VERSION,
    ValidationVerdict,
    clone_contract,
    compute_contract_digest_v0,
    materialize_pit_futures_universe_manifest_dataset_period_binding_v0,
    serialize_contract_canonical_v0,
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
from src.research.pit_futures_universe_manifest_validator_v1 import (
    ValidationVerdict as ManifestValidationVerdict,
    validate_pit_futures_universe_manifest_v1,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import (
    InstrumentPanelSeriesV1,
    PanelBarV1,
    compute_series_digest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

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


def _build_production_result():
    registry, panel_series, source_digest = _build_registry_and_panel(_default_instruments())
    inp = PitFuturesUniverseManifestProductionMaterializationInputV1(
        input_contract_version=INPUT_CONTRACT_VERSION,
        materialization_version=MATERIALIZATION_VERSION,
        generated_at=_GENERATED_AT,
        universe_policy_id=UNIVERSE_POLICY_ID,
        universe_policy_version=UNIVERSE_POLICY_VERSION,
        inclusion_policy_version=INCLUSION_POLICY_VERSION,
        exclusion_policy_version=EXCLUSION_POLICY_VERSION,
        lifecycle_source_id="okx_production_instrument_lifecycle_historical_as_of_fail_closed.v1",
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
    result = materialize_production_pit_futures_universe_manifest_v1(inp)
    assert result.success is True
    assert result.manifest is not None and result.envelope is not None
    return result


@pytest.fixture(scope="module")
def canonical_contract() -> dict:
    production = _build_production_result()
    return materialize_pit_futures_universe_manifest_dataset_period_binding_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
    )


def _candidate(contract: dict, strategy_id: str) -> dict:
    for candidate in contract["candidates"]:
        if candidate["strategy_id"] == strategy_id:
            return candidate
    raise KeyError(strategy_id)


def _validate(contract: dict, *, production=None):
    kwargs = {"repo_root": REPO_ROOT, "allow_recompute_digests": True}
    if production is not None:
        kwargs["expected_manifest"] = production.manifest
        kwargs["expected_envelope"] = production.envelope
    return validate_pit_futures_universe_manifest_dataset_period_binding_v0(contract, **kwargs)


def test_materialize_exactly_three_fleet_candidates(canonical_contract: dict) -> None:
    assert len(canonical_contract["candidates"]) == 3
    ids = {candidate["strategy_id"] for candidate in canonical_contract["candidates"]}
    assert ids == {sid for sid, _ in FLEET_CANDIDATES}


def test_deterministic_contract_generation(canonical_contract: dict) -> None:
    production = _build_production_result()
    second = materialize_pit_futures_universe_manifest_dataset_period_binding_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
    )
    assert serialize_contract_canonical_v0(canonical_contract) == serialize_contract_canonical_v0(
        second
    )
    assert canonical_contract["contract_digest"] == second["contract_digest"]


def test_candidate_order_is_canonical_sorted(canonical_contract: dict) -> None:
    strategy_ids = [candidate["strategy_id"] for candidate in canonical_contract["candidates"]]
    assert strategy_ids == sorted(strategy_ids)


def test_production_universe_manifest_digest_bound(canonical_contract: dict) -> None:
    production = _build_production_result()
    assert (
        canonical_contract["production_universe_manifest_digest"]
        == production.manifest.manifest_digest
    )
    for strategy_id, _ in FLEET_CANDIDATES:
        candidate = _candidate(canonical_contract, strategy_id)
        assert (
            candidate["production_universe_manifest_digest"] == production.manifest.manifest_digest
        )
        assert (
            candidate["production_universe_manifest_ref"] == production.envelope.manifest_reference
        )


def test_futures_only_and_bitcoin_exclusion(canonical_contract: dict) -> None:
    assert canonical_contract["futures_only"] is True
    assert canonical_contract["bitcoin_direction_allowed"] is False
    instrument_binding = canonical_contract["shared_bindings"]["instrument_binding"]
    assert instrument_binding["futures_only"] is True
    assert instrument_binding["bitcoin_direction_allowed"] is False
    for instrument_id in instrument_binding["eligible_instrument_ids"]:
        assert "btc" not in instrument_id.lower()
        assert "xbt" not in instrument_id.lower()
        assert "bitcoin" not in instrument_id.lower()


def test_deferred_periods_and_data_digest_fail_closed(canonical_contract: dict) -> None:
    for strategy_id, _ in FLEET_CANDIDATES:
        candidate = _candidate(canonical_contract, strategy_id)
        assert candidate["training_period"] == NOT_YET_MATERIALIZED
        assert candidate["validation_period"] == NOT_YET_MATERIALIZED
        assert candidate["out_of_sample_period"] == NOT_YET_MATERIALIZED
        assert candidate["data_digest"]["status"] == "NOT_YET_MATERIALIZED"
        assert candidate["binding_status"] == BINDING_STATUS_NOT_READY
        assert REASON_DATA_DIGEST_NOT_MATERIALIZED in candidate["reason_codes"]
        assert REASON_PERIOD_SPLIT_NOT_MATERIALIZED in candidate["reason_codes"]


def test_shared_bindings_identical_across_candidates(canonical_contract: dict) -> None:
    first = canonical_contract["candidates"][0]
    for candidate in canonical_contract["candidates"][1:]:
        assert candidate["dataset_binding"] == first["dataset_binding"]
        assert candidate["period_binding"] == first["period_binding"]
        assert candidate["instrument_binding"] == first["instrument_binding"]
        assert candidate["data_digest"] == first["data_digest"]


def test_effects_remain_none(canonical_contract: dict) -> None:
    assert canonical_contract["authority_effect"] == AUTHORITY_EFFECT == "NONE"
    assert canonical_contract["runtime_effect"] == RUNTIME_EFFECT == "NONE"
    assert canonical_contract["order_effect"] == ORDER_EFFECT == "NONE"
    assert canonical_contract["no_runtime_effect"] is True
    assert canonical_contract["no_economic_evaluation_execution"] is True


def test_validator_accepts_canonical_contract(canonical_contract: dict) -> None:
    production = _build_production_result()
    result = _validate(canonical_contract, production=production)
    assert result.valid is True
    assert result.verdict == ValidationVerdict.ACCEPTED
    assert result.fail_reasons == ()


def test_version_fields_present(canonical_contract: dict) -> None:
    assert canonical_contract["schema_version"] == SCHEMA_VERSION
    assert canonical_contract["fleet_id"] == FLEET_ID
    assert canonical_contract["candidate_binding_version"] == CANDIDATE_BINDING_VERSION
    assert canonical_contract["dataset_binding_version"] == DATASET_BINDING_VERSION
    assert canonical_contract["period_binding_version"] == PERIOD_BINDING_VERSION
    assert canonical_contract["instrument_binding_version"] == INSTRUMENT_BINDING_VERSION


def test_tampered_production_manifest_digest_rejected(canonical_contract: dict) -> None:
    mutated = clone_contract(canonical_contract)
    mutated["production_universe_manifest_digest"] = "f" * 64
    mutated["contract_digest"] = compute_contract_digest_v0(mutated)
    production = _build_production_result()
    result = _validate(mutated, production=production)
    assert result.valid is False
    assert REASON_PRODUCTION_MANIFEST_DIGEST_MISMATCH in result.fail_reasons


def test_materialize_rejects_tampered_manifest() -> None:
    production = _build_production_result()
    tampered = dataclasses.replace(
        production.manifest,
        manifest_digest="f" * 64,
    )
    with pytest.raises(ValueError, match="PRODUCTION_MANIFEST_VALIDATION_FAILED|PRODUCTION_MANIFEST_TAMPERED"):
        materialize_pit_futures_universe_manifest_dataset_period_binding_v0(
            repo_root=REPO_ROOT,
            production_manifest=tampered,
            production_envelope=production.envelope,
        )


def test_materialize_rejects_envelope_manifest_digest_mismatch() -> None:
    production = _build_production_result()
    tampered_envelope = dataclasses.replace(
        production.envelope,
        manifest_digest="f" * 64,
    )
    with pytest.raises(ValueError, match=REASON_ENVELOPE_MANIFEST_DIGEST_MISMATCH):
        materialize_pit_futures_universe_manifest_dataset_period_binding_v0(
            repo_root=REPO_ROOT,
            production_manifest=production.manifest,
            production_envelope=tampered_envelope,
        )


def test_production_manifest_validation_required() -> None:
    production = _build_production_result()
    manifest_dict = manifest_to_dict(production.manifest)
    manifest_dict["futures_only"] = False
    broken = validate_pit_futures_universe_manifest_v1(
        __import__(
            "src.research.pit_futures_universe_manifest_v1",
            fromlist=["manifest_from_dict"],
        ).manifest_from_dict(manifest_dict)
    )
    assert broken.verdict != ManifestValidationVerdict.ACCEPTED


def test_eligible_instrument_count_meets_minimum(canonical_contract: dict) -> None:
    count = canonical_contract["shared_bindings"]["instrument_binding"]["eligible_instrument_count"]
    assert count >= MIN_ELIGIBLE_INSTRUMENT_COUNT


@pytest.mark.parametrize(
    ("strategy_id", "mutator", "reason_prefix"),
    [
        ("trend_following", lambda c: c["candidates"].pop(0), REASON_MISSING_CANDIDATE),
        (
            "trend_following",
            lambda c: c["candidates"].append(copy.deepcopy(c["candidates"][0])),
            REASON_DUPLICATE_CANDIDATE,
        ),
        (
            "trend_following",
            lambda c: c["candidates"].append(
                {
                    **_candidate(c, "bollinger_bands"),
                    "strategy_id": "macd",
                    "strategy_version": "v1",
                }
            ),
            REASON_UNKNOWN_STRATEGY,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following").update({"strategy_version": "v2"}),
            REASON_WRONG_STRATEGY_VERSION,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following").pop("parameter_binding", None),
            REASON_MISSING_REQUIRED_FIELD,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following").update(
                {"parameter_binding": {"adx_period": 99}}
            ),
            REASON_WRONG_PARAMETER_BINDING,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following")["period_binding"].update(
                {"coverage_period_start_utc": ""}
            ),
            REASON_MISSING_PERIOD_COVERAGE,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following")["dataset_binding"].update(
                {"panel_dataset_digest": "not-a-digest"}
            ),
            REASON_MISSING_PANEL_DATASET_DIGEST,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following")["instrument_binding"].update(
                {"spot_allowed": True}
            ),
            REASON_SPOT_BINDING,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following")["instrument_binding"].update(
                {"synthetic_spot_allowed": True}
            ),
            REASON_SYNTHETIC_SPOT_BINDING,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following")["instrument_binding"].update(
                {"eligible_instrument_ids": ["inst-btc-usdt-perp"]}
            ),
            REASON_BITCOIN_INSTRUMENT_PRESENT,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following")["fee_model_binding"].update({"fee_bps": 0}),
            REASON_ZERO_FEE,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following")["slippage_model_binding"].update(
                {"slippage_bps": 0}
            ),
            REASON_ZERO_SLIPPAGE,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "bollinger_bands")["period_binding"].update(
                {"coverage_period_end_utc": "1970-01-01T00:00:00Z"}
            ),
            REASON_SHARED_BINDING_MISMATCH,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following").update({"implementation_digest": "0" * 64}),
            REASON_WRONG_IMPLEMENTATION_DIGEST,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following").update({"config_digest": "0" * 64}),
            REASON_WRONG_CONFIG_DIGEST,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following").update(
                {"training_period": {"status": "BOUND", "value": "2020..2021"}}
            ),
            REASON_PERIOD_SPLIT_NOT_MATERIALIZED,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following").update(
                {"data_digest": {"status": "BOUND", "value": "0" * 64}}
            ),
            REASON_DATA_DIGEST_NOT_MATERIALIZED,
        ),
        (
            "trend_following",
            lambda c: c.update({"schema_version": "unknown.v9"}),
            REASON_UNKNOWN_SCHEMA_VERSION,
        ),
        (
            "trend_following",
            lambda c: c.update({"authority_effect": "LIVE"}),
            REASON_EFFECT_NOT_NONE,
        ),
        (
            "trend_following",
            lambda c: c.update({"contract_digest": "0" * 64}),
            REASON_WRONG_CONTRACT_DIGEST,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following").update({"fallback": True}),
            REASON_BINDING_REPAIR_REJECTED,
        ),
    ],
)
def test_negative_validation_cases(
    canonical_contract: dict,
    strategy_id: str,
    mutator,
    reason_prefix: str,
) -> None:
    mutated = clone_contract(canonical_contract)
    mutator(mutated)
    if mutated.get("contract_digest") == canonical_contract["contract_digest"]:
        mutated["contract_digest"] = compute_contract_digest_v0(mutated)
    production = _build_production_result()
    result = _validate(mutated, production=production)
    assert result.valid is False
    assert result.verdict == ValidationVerdict.REJECTED
    assert any(reason.startswith(reason_prefix) for reason in result.fail_reasons)


def test_extra_candidate_rejected(canonical_contract: dict) -> None:
    mutated = clone_contract(canonical_contract)
    extra = copy.deepcopy(mutated["candidates"][0])
    extra["strategy_id"] = "rsi_reversion"
    extra["strategy_version"] = "v1"
    mutated["candidates"].append(extra)
    mutated["contract_digest"] = compute_contract_digest_v0(mutated)
    production = _build_production_result()
    result = _validate(mutated, production=production)
    assert any(reason.startswith(REASON_EXTRA_CANDIDATE) for reason in result.fail_reasons)
