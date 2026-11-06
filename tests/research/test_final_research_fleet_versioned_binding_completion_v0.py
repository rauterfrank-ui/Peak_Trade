"""Contract tests for final_research_fleet_versioned_binding_completion_v0."""

from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    AUTHORITY_EFFECT,
    BINDING_STATUS_INCOMPLETE,
    BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
    CANONICAL_SERIALIZATION_VERSION,
    COMPLETION_ID,
    ECONOMIC_EVALUATION_AUTHORIZED,
    FAILED_HISTORICAL_CANDIDATES,
    FLEET_ID,
    FUTURES_ONLY,
    ORDER_EFFECT,
    REASON_BINDING_INCOMPLETE,
    REASON_BINDING_NOT_READY_FOR_EVAL,
    REASON_BINDING_REPAIR_REJECTED,
    REASON_BITCOIN_DIRECTION_BINDING,
    REASON_DUPLICATE_CANDIDATE,
    REASON_ECONOMIC_EVALUATION_AUTHORIZED,
    REASON_ECONOMIC_POLICY_MISMATCH,
    REASON_EFFECT_NOT_NONE,
    REASON_EXTRA_CANDIDATE,
    REASON_FAILED_HISTORICAL_CANDIDATE,
    REASON_FUTURES_ONLY_VIOLATION,
    REASON_MISSING_CANDIDATE,
    REASON_MISSING_REQUIRED_FIELD,
    REASON_SHARED_BINDING_MISMATCH,
    REASON_SPOT_BINDING,
    REASON_SYNTHETIC_SPOT_BINDING,
    REASON_UNKNOWN_SCHEMA_VERSION,
    REASON_UNKNOWN_STRATEGY,
    REASON_WRONG_BINDING_SEMANTIC_DIGEST,
    REASON_WRONG_COMPLETION_DIGEST,
    REASON_WRONG_CONFIG_DIGEST,
    REASON_WRONG_DATA_DIGEST,
    REASON_WRONG_IMPLEMENTATION_DIGEST,
    REASON_WRONG_STRATEGY_VERSION,
    REASON_ZERO_FEE,
    REASON_ZERO_SLIPPAGE,
    RUNTIME_EFFECT,
    SCHEMA_VERSION,
    ValidationVerdict,
    canonical_candidate_identifier,
    clone_completion,
    compute_binding_semantic_digest_v0,
    compute_completion_digest_v0,
    materialize_final_research_fleet_versioned_binding_completion_v0,
    serialize_completion_canonical_v0,
    validate_final_research_fleet_versioned_binding_completion_v0,
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


@pytest.fixture(scope="module")
def canonical_completion(production_bundle):
    production, panel_series = production_bundle
    return materialize_final_research_fleet_versioned_binding_completion_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
        panel_series=panel_series,
        source_registration_ref=_SOURCE_REF,
        source_registration_digest=_SOURCE_DIGEST,
    )


def _candidate(completion: dict, strategy_id: str) -> dict:
    for candidate in completion["candidates"]:
        if candidate["strategy_id"] == strategy_id:
            return candidate
    raise KeyError(strategy_id)


def _validate(completion: dict, *, require_ready: bool = True):
    return validate_final_research_fleet_versioned_binding_completion_v0(
        completion,
        repo_root=REPO_ROOT,
        require_ready_for_eval=require_ready,
    )


def test_materialize_exactly_three_fleet_candidates(canonical_completion: dict) -> None:
    assert len(canonical_completion["candidates"]) == 3
    ids = {candidate["strategy_id"] for candidate in canonical_completion["candidates"]}
    assert ids == {sid for sid, _ in FLEET_CANDIDATES}


def test_candidate_ids_and_versions(canonical_completion: dict) -> None:
    for strategy_id, strategy_version in FLEET_CANDIDATES:
        candidate = _candidate(canonical_completion, strategy_id)
        assert candidate["strategy_version"] == strategy_version
        assert candidate["canonical_candidate_identifier"] == canonical_candidate_identifier(
            strategy_id, strategy_version
        )


def test_deterministic_completion_generation(canonical_completion: dict, production_bundle) -> None:
    production, panel_series = production_bundle
    second = materialize_final_research_fleet_versioned_binding_completion_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
        panel_series=panel_series,
        source_registration_ref=_SOURCE_REF,
        source_registration_digest=_SOURCE_DIGEST,
    )
    assert serialize_completion_canonical_v0(
        canonical_completion
    ) == serialize_completion_canonical_v0(second)
    assert canonical_completion["completion_digest"] == second["completion_digest"]


def test_double_execution_produces_identical_bytes(
    canonical_completion: dict, production_bundle
) -> None:
    production, panel_series = production_bundle
    first_bytes = serialize_completion_canonical_v0(canonical_completion).encode("utf-8")
    second_bytes = serialize_completion_canonical_v0(
        materialize_final_research_fleet_versioned_binding_completion_v0(
            repo_root=REPO_ROOT,
            production_manifest=production.manifest,
            production_envelope=production.envelope,
            panel_series=panel_series,
            source_registration_ref=_SOURCE_REF,
            source_registration_digest=_SOURCE_DIGEST,
        )
    ).encode("utf-8")
    assert first_bytes == second_bytes


def test_binding_status_ready_for_eval_ratification(canonical_completion: dict) -> None:
    assert (
        canonical_completion["binding_materialization_status"]
        == BINDING_STATUS_READY_FOR_EVAL_RATIFICATION
    )
    for candidate in canonical_completion["candidates"]:
        assert candidate["binding_status"] == BINDING_STATUS_READY_FOR_EVAL_RATIFICATION


def test_economic_evaluation_not_authorized(canonical_completion: dict) -> None:
    assert canonical_completion["economic_evaluation_authorized"] is False
    assert ECONOMIC_EVALUATION_AUTHORIZED is False
    for candidate in canonical_completion["candidates"]:
        assert candidate["economic_evaluation_authorized"] is False


def test_futures_only_enforcement(canonical_completion: dict) -> None:
    assert canonical_completion["futures_only"] is True
    assert canonical_completion["bitcoin_direction_allowed"] is False
    assert canonical_completion["spot_allowed"] is False
    assert canonical_completion["synthetic_spot_allowed"] is False
    for candidate in canonical_completion["candidates"]:
        instrument = candidate["instrument_binding"]
        assert instrument["futures_only"] is True
        assert instrument["bitcoin_direction_allowed"] is False
        assert instrument["spot_allowed"] is False
        assert instrument["synthetic_spot_allowed"] is False


def test_shared_economic_policy_binding(canonical_completion: dict) -> None:
    policies = [
        candidate["economic_policy_binding"] for candidate in canonical_completion["candidates"]
    ]
    assert len({str(policy) for policy in policies}) == 1


def test_shared_cost_and_execution_bindings(canonical_completion: dict) -> None:
    reference = canonical_completion["candidates"][0]
    for candidate in canonical_completion["candidates"][1:]:
        assert candidate["fee_model_binding"] == reference["fee_model_binding"]
        assert candidate["slippage_model_binding"] == reference["slippage_model_binding"]
        assert candidate["funding_model_binding"] == reference["funding_model_binding"]
        assert candidate["execution_model_binding"] == reference["execution_model_binding"]


def test_dataset_period_split_binding_present(canonical_completion: dict) -> None:
    shared = canonical_completion["shared_bindings"]
    assert "dataset_envelope" in shared
    assert "period_split" in shared
    for candidate in canonical_completion["candidates"]:
        assert candidate["training_period"]["status"] == "MATERIALIZED"
        assert candidate["validation_period"]["status"] == "MATERIALIZED"
        assert candidate["out_of_sample_period"]["status"] == "MATERIALIZED"
        assert len(candidate["data_digest"]) == 64


def test_required_candidate_fields_present(canonical_completion: dict) -> None:
    required = {
        "parameter_schema_version",
        "dataset_provenance",
        "canonical_trading_logic_version",
        "binding_semantic_digest",
        "reproducibility_metadata",
        "strategy_params_digest",
    }
    for candidate in canonical_completion["candidates"]:
        for field in required:
            assert field in candidate, f"{candidate['strategy_id']} missing {field}"


def test_failed_historical_candidates_excluded(canonical_completion: dict) -> None:
    excluded = {
        (item["strategy_id"], item["strategy_version"])
        for item in canonical_completion["excluded_failed_historical_candidates"]
    }
    for pair in FAILED_HISTORICAL_CANDIDATES:
        assert pair in excluded
    fleet_ids = {candidate["strategy_id"] for candidate in canonical_completion["candidates"]}
    for strategy_id, _ in FAILED_HISTORICAL_CANDIDATES:
        assert strategy_id not in fleet_ids or strategy_id in {sid for sid, _ in FLEET_CANDIDATES}


def test_effects_remain_none(canonical_completion: dict) -> None:
    assert canonical_completion["authority_effect"] == AUTHORITY_EFFECT == "NONE"
    assert canonical_completion["runtime_effect"] == RUNTIME_EFFECT == "NONE"
    assert canonical_completion["order_effect"] == ORDER_EFFECT == "NONE"


def test_validator_accepts_canonical_completion(canonical_completion: dict) -> None:
    result = _validate(canonical_completion)
    assert result.valid is True
    assert result.verdict == ValidationVerdict.ACCEPTED
    assert result.fail_reasons == ()


def test_binding_semantic_digest_deterministic(canonical_completion: dict) -> None:
    for candidate in canonical_completion["candidates"]:
        expected = compute_binding_semantic_digest_v0(candidate)
        assert candidate["binding_semantic_digest"] == expected


def test_incomplete_without_panel(production_bundle) -> None:
    production, _ = production_bundle
    completion = materialize_final_research_fleet_versioned_binding_completion_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
    )
    assert completion["binding_materialization_status"] == BINDING_STATUS_INCOMPLETE
    result = _validate(completion, require_ready=True)
    assert result.valid is False
    assert any(
        reason.startswith(REASON_BINDING_NOT_READY_FOR_EVAL) for reason in result.fail_reasons
    )


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
                    **copy.deepcopy(c["candidates"][0]),
                    "strategy_id": "macd",
                    "strategy_version": "v1",
                    "canonical_candidate_identifier": "macd/v1",
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
            lambda c: _candidate(c, "trend_following").update(
                {"economic_evaluation_authorized": True}
            ),
            REASON_ECONOMIC_EVALUATION_AUTHORIZED,
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
                {"bitcoin_direction_allowed": True}
            ),
            REASON_BITCOIN_DIRECTION_BINDING,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following")["instrument_binding"].update(
                {"futures_only": False}
            ),
            REASON_FUTURES_ONLY_VIOLATION,
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
            lambda c: _candidate(c, "bollinger_bands")["economic_policy_binding"].update(
                {"policy_version": "other_policy_v9"}
            ),
            REASON_ECONOMIC_POLICY_MISMATCH,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following").update({"data_digest": "0" * 64}),
            REASON_WRONG_DATA_DIGEST,
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
                {"binding_semantic_digest": "0" * 64}
            ),
            REASON_WRONG_BINDING_SEMANTIC_DIGEST,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following")["period_binding"].update(
                {"period_binding_ref": "other_ref"}
            ),
            REASON_SHARED_BINDING_MISMATCH,
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
            lambda c: c.update({"completion_digest": "0" * 64}),
            REASON_WRONG_COMPLETION_DIGEST,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following").update({"fallback": True}),
            REASON_BINDING_REPAIR_REJECTED,
        ),
        (
            "trend_following",
            lambda c: _candidate(c, "trend_following").update(
                {"binding_status": BINDING_STATUS_INCOMPLETE}
            ),
            REASON_BINDING_NOT_READY_FOR_EVAL,
        ),
    ],
)
def test_negative_validation_cases(
    canonical_completion: dict,
    strategy_id: str,
    mutator,
    reason_prefix: str,
) -> None:
    mutated = clone_completion(canonical_completion)
    mutator(mutated)
    if mutated.get("completion_digest") == canonical_completion["completion_digest"]:
        mutated["completion_digest"] = compute_completion_digest_v0(mutated)
    result = _validate(mutated)
    assert result.valid is False
    assert result.verdict == ValidationVerdict.REJECTED
    assert any(reason.startswith(reason_prefix) for reason in result.fail_reasons)


def test_extra_candidate_rejected(canonical_completion: dict) -> None:
    mutated = clone_completion(canonical_completion)
    extra = copy.deepcopy(mutated["candidates"][0])
    extra["strategy_id"] = "rsi_reversion"
    extra["strategy_version"] = "step30a"
    extra["canonical_candidate_identifier"] = "rsi_reversion/step30a"
    mutated["candidates"].append(extra)
    mutated["completion_digest"] = compute_completion_digest_v0(mutated)
    result = _validate(mutated)
    assert any(reason.startswith(REASON_EXTRA_CANDIDATE) for reason in result.fail_reasons)


def test_failed_historical_candidate_in_fleet_rejected(canonical_completion: dict) -> None:
    mutated = clone_completion(canonical_completion)
    extra = copy.deepcopy(mutated["candidates"][0])
    extra["strategy_id"] = "macd"
    extra["strategy_version"] = "v1"
    extra["canonical_candidate_identifier"] = "macd/v1"
    mutated["candidates"].append(extra)
    mutated["completion_digest"] = compute_completion_digest_v0(mutated)
    result = _validate(mutated)
    assert any(
        reason.startswith(REASON_FAILED_HISTORICAL_CANDIDATE) for reason in result.fail_reasons
    )


def test_completion_metadata_fields(canonical_completion: dict) -> None:
    assert canonical_completion["schema_version"] == SCHEMA_VERSION
    assert canonical_completion["completion_id"] == COMPLETION_ID
    assert canonical_completion["fleet_id"] == FLEET_ID
    assert (
        canonical_completion["canonical_serialization_version"] == CANONICAL_SERIALIZATION_VERSION
    )
    assert canonical_completion["futures_only"] is FUTURES_ONLY
