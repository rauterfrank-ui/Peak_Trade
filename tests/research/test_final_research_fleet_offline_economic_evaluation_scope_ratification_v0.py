"""Contract tests for final_research_fleet_offline_economic_evaluation_scope_ratification_v0."""

from __future__ import annotations

import ast
import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
)
from src.research.final_research_fleet_offline_economic_evaluation_scope_ratification_v0 import (
    ALLOWED_EVALUATION_STAGES,
    AUTHORITY_EFFECT,
    ECONOMIC_EVALUATION_AUTHORIZED,
    ECONOMIC_EVALUATION_EXECUTED,
    ECONOMIC_EVALUATION_SCOPE_RATIFIED,
    ECONOMIC_VALIDITY_OFFLINE_GATE_PASS,
    FINAL_RESEARCH_FLEET_BINDING_READY,
    NEW_CANDIDATES_RATIFIED,
    OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED,
    ALLOWED_AFTER_THIS_RATIFICATION,
    ORDER_EFFECT,
    PROHIBITED_ACTIONS,
    RATIFICATION_ID,
    REASON_BINDING_COMPLETION_INVALID,
    REASON_BINDING_REPAIR_REJECTED,
    REASON_BITCOIN_DIRECTION_BINDING,
    REASON_DUPLICATE_CANDIDATE,
    REASON_ECONOMIC_POLICY_MISMATCH,
    REASON_EFFECT_NOT_NONE,
    REASON_EVALUATION_ALREADY_EXECUTED,
    REASON_FORBIDDEN_STAGE_IN_RATIFICATION,
    REASON_FAILED_HISTORICAL_CANDIDATE,
    REASON_FLEET_BINDING_DIGEST_MISMATCH,
    REASON_FUTURES_ONLY_VIOLATION,
    REASON_INCOMPLETE_PERIOD_SPLIT,
    REASON_MISSING_CANDIDATE,
    REASON_POLICY_DRIFT,
    REASON_SHARED_BINDING_MISMATCH,
    REASON_SPOT_BINDING,
    REASON_SYNTHETIC_SPOT_BINDING,
    REASON_UNKNOWN_SCHEMA_VERSION,
    REASON_WRONG_RATIFICATION_DIGEST,
    REASON_WRONG_SEMANTIC_DIGEST,
    REASON_ZERO_FEE,
    REASON_ZERO_SLIPPAGE,
    RUNTIME_EFFECT,
    RUNTIME_REWIRE_ADMISSIBLE,
    SCHEMA_VERSION,
    ValidationVerdict,
    clone_ratification,
    compute_ratification_digest_v0,
    materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0,
    serialize_ratification_canonical_v0,
    validate_final_research_fleet_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    BINDING_STATUS_INCOMPLETE,
    BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
    canonical_candidate_identifier,
    compute_completion_digest_v0,
    materialize_final_research_fleet_versioned_binding_completion_v0,
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
RATIFICATION_MODULE = (
    REPO_ROOT
    / "src"
    / "research"
    / "final_research_fleet_offline_economic_evaluation_scope_ratification_v0.py"
)

_GENERATED_AT = "2026-07-03T04:00:00Z"
_BAR_CLOSE = "2024-06-01T01:00:00Z"
_PERIOD_START = "2024-05-25T00:00:00Z"
_PERIOD_END = _BAR_CLOSE
_PANEL_DIGEST = "b" * 64
_SOURCE_REF = "okx_public_instruments_swap:test"
_SOURCE_DIGEST = "c" * 64
_REGISTRY_CONFIG = "d" * 64
_REGISTRY_IMPL = "e" * 64

_FORBIDDEN_EVAL_IMPORTS = frozenset(
    {
        "src.backtest.engine",
        "src.backtest.walkforward",
        "src.experiments.monte_carlo",
        "src.experiments.stress_tests",
        "src.experiments.portfolio_robustness",
        "src.backtest.economic_viability_evidence_v1",
    }
)


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


@pytest.fixture(scope="module")
def canonical_ratification(canonical_completion):
    return materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
        repo_root=REPO_ROOT,
        fleet_binding_completion=canonical_completion,
    )


def _validate(ratification: dict, *, completion: dict | None = None):
    return validate_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
        ratification,
        repo_root=REPO_ROOT,
        expected_fleet_binding_completion=completion,
    )


def test_ratification_module_does_not_import_evaluation_executors() -> None:
    tree = ast.parse(RATIFICATION_MODULE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert imported.isdisjoint(_FORBIDDEN_EVAL_IMPORTS)


def test_materialize_exactly_three_candidates(canonical_ratification: dict) -> None:
    assert len(canonical_ratification["candidate_refs"]) == 3
    assert set(canonical_ratification["candidate_refs"]) == {
        canonical_candidate_identifier(sid, ver) for sid, ver in FLEET_CANDIDATES
    }


def test_ratification_status_fields(canonical_ratification: dict) -> None:
    assert (
        canonical_ratification["final_research_fleet_binding_ready"]
        is FINAL_RESEARCH_FLEET_BINDING_READY
    )
    assert canonical_ratification["new_candidates_ratified"] is NEW_CANDIDATES_RATIFIED
    assert (
        canonical_ratification["offline_economic_evaluation_scope_ratified"]
        is OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED
    )
    assert (
        canonical_ratification["economic_evaluation_scope_ratified"]
        is ECONOMIC_EVALUATION_SCOPE_RATIFIED
    )
    assert (
        canonical_ratification["economic_evaluation_authorized"] is ECONOMIC_EVALUATION_AUTHORIZED
    )
    assert ECONOMIC_EVALUATION_AUTHORIZED is False
    assert (
        canonical_ratification["allowed_after_this_ratification"] is ALLOWED_AFTER_THIS_RATIFICATION
    )
    assert ALLOWED_AFTER_THIS_RATIFICATION is False
    assert canonical_ratification["economic_evaluation_executed"] is ECONOMIC_EVALUATION_EXECUTED
    assert (
        canonical_ratification["economic_validity_offline_gate_pass"]
        is ECONOMIC_VALIDITY_OFFLINE_GATE_PASS
    )
    assert canonical_ratification["runtime_rewire_admissible"] is RUNTIME_REWIRE_ADMISSIBLE
    assert canonical_ratification["authority_effect"] == AUTHORITY_EFFECT
    assert canonical_ratification["runtime_effect"] == RUNTIME_EFFECT
    assert canonical_ratification["order_effect"] == ORDER_EFFECT
    assert canonical_ratification["evaluation_execution_performed"] is False
    assert canonical_ratification["evaluation_modules_invoked"] == []


def test_allowed_stages_and_prohibited_actions(canonical_ratification: dict) -> None:
    assert canonical_ratification["allowed_evaluation_stages"] == list(ALLOWED_EVALUATION_STAGES)
    assert canonical_ratification["prohibited_actions"] == list(PROHIBITED_ACTIONS)


def test_deterministic_ratification_generation(
    canonical_ratification: dict, canonical_completion: dict
) -> None:
    second = materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
        repo_root=REPO_ROOT,
        fleet_binding_completion=canonical_completion,
    )
    assert serialize_ratification_canonical_v0(
        canonical_ratification
    ) == serialize_ratification_canonical_v0(second)
    assert canonical_ratification["ratification_digest"] == second["ratification_digest"]


def test_validate_accepts_canonical_ratification(
    canonical_ratification: dict, canonical_completion: dict
) -> None:
    result = _validate(canonical_ratification, completion=canonical_completion)
    assert result.valid is True
    assert result.verdict == ValidationVerdict.ACCEPTED


def test_all_candidates_ready_for_eval_ratification(canonical_completion: dict) -> None:
    for candidate in canonical_completion["candidates"]:
        assert candidate["binding_status"] == BINDING_STATUS_READY_FOR_EVAL_RATIFICATION


def test_materialize_rejects_incomplete_binding(production_bundle) -> None:
    production, panel_series = production_bundle
    incomplete = materialize_final_research_fleet_versioned_binding_completion_v0(
        repo_root=REPO_ROOT,
        production_manifest=production.manifest,
        production_envelope=production.envelope,
    )
    assert incomplete["binding_materialization_status"] == BINDING_STATUS_INCOMPLETE
    with pytest.raises(ValueError, match=REASON_BINDING_COMPLETION_INVALID):
        materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
            repo_root=REPO_ROOT,
            fleet_binding_completion=incomplete,
        )


@pytest.mark.parametrize(
    ("mutator", "reason_prefix"),
    [
        (lambda r: r.update({"schema_version": "unknown.v9"}), REASON_UNKNOWN_SCHEMA_VERSION),
        (lambda r: r.update({"authority_effect": "LIVE"}), REASON_EFFECT_NOT_NONE),
        (
            lambda r: r.update({"economic_evaluation_executed": True}),
            REASON_EVALUATION_ALREADY_EXECUTED,
        ),
        (
            lambda r: r.update({"evaluation_execution_performed": True}),
            REASON_EVALUATION_ALREADY_EXECUTED,
        ),
        (
            lambda r: r.update({"evaluation_modules_invoked": ["backtest"]}),
            REASON_FORBIDDEN_STAGE_IN_RATIFICATION,
        ),
        (lambda r: r["candidate_refs"].pop(0), REASON_MISSING_CANDIDATE),
        (
            lambda r: r["candidate_refs"].append(r["candidate_refs"][0]),
            REASON_DUPLICATE_CANDIDATE,
        ),
        (
            lambda r: r["candidate_refs"].append("rsi_reversion/step30a"),
            REASON_FAILED_HISTORICAL_CANDIDATE,
        ),
        (
            lambda r: r["fee_model_binding"].update({"fee_bps": 0}),
            REASON_ZERO_FEE,
        ),
        (
            lambda r: r["slippage_model_binding"].update({"slippage_bps": 0}),
            REASON_ZERO_SLIPPAGE,
        ),
        (
            lambda r: r["common_instrument_policy_ref"].update({"spot_allowed": True}),
            REASON_SPOT_BINDING,
        ),
        (
            lambda r: r["common_instrument_policy_ref"].update({"synthetic_spot_allowed": True}),
            REASON_SYNTHETIC_SPOT_BINDING,
        ),
        (
            lambda r: r["common_instrument_policy_ref"].update({"bitcoin_direction_allowed": True}),
            REASON_BITCOIN_DIRECTION_BINDING,
        ),
        (
            lambda r: r["common_instrument_policy_ref"].update({"futures_only": False}),
            REASON_FUTURES_ONLY_VIOLATION,
        ),
        (
            lambda r: r["allowed_evaluation_stages"].append("LIVE_TRADING"),
            REASON_POLICY_DRIFT,
        ),
        (
            lambda r: r.update({"fleet_binding_digest": "0" * 64}),
            REASON_FLEET_BINDING_DIGEST_MISMATCH,
        ),
        (
            lambda r: r.update({"semantic_digest": "0" * 64}),
            REASON_WRONG_SEMANTIC_DIGEST,
        ),
        (
            lambda r: r.update({"ratification_digest": "0" * 64}),
            REASON_WRONG_RATIFICATION_DIGEST,
        ),
        (
            lambda r: r.update({"fallback": True}),
            REASON_BINDING_REPAIR_REJECTED,
        ),
    ],
)
def test_negative_validation_cases(
    canonical_ratification: dict,
    canonical_completion: dict,
    mutator,
    reason_prefix: str,
) -> None:
    mutated = clone_ratification(canonical_ratification)
    mutator(mutated)
    if mutated.get("ratification_digest") == canonical_ratification["ratification_digest"]:
        mutated["ratification_digest"] = compute_ratification_digest_v0(mutated)
    result = _validate(mutated, completion=canonical_completion)
    assert result.valid is False
    assert result.verdict == ValidationVerdict.REJECTED
    assert any(reason.startswith(reason_prefix) for reason in result.fail_reasons)


def test_failed_historical_candidate_rejected(
    canonical_ratification: dict, canonical_completion: dict
) -> None:
    mutated = clone_ratification(canonical_ratification)
    mutated["candidate_refs"] = list(mutated["candidate_refs"]) + ["macd/v1"]
    mutated["ratification_digest"] = compute_ratification_digest_v0(mutated)
    result = _validate(mutated, completion=canonical_completion)
    assert any(
        reason.startswith(REASON_FAILED_HISTORICAL_CANDIDATE) for reason in result.fail_reasons
    )


def test_policy_drift_rejected(canonical_completion: dict) -> None:
    mutated_completion = copy.deepcopy(canonical_completion)
    for candidate in mutated_completion["candidates"]:
        if candidate["strategy_id"] == "bollinger_bands":
            candidate["economic_policy_binding"] = {
                **candidate["economic_policy_binding"],
                "policy_version": "other_policy_v9",
            }
    mutated_completion["completion_digest"] = compute_completion_digest_v0(mutated_completion)
    with pytest.raises(ValueError, match=REASON_ECONOMIC_POLICY_MISMATCH):
        materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
            repo_root=REPO_ROOT,
            fleet_binding_completion=mutated_completion,
        )


def test_incomplete_period_split_rejected(
    canonical_ratification: dict, canonical_completion: dict
) -> None:
    mutated_completion = copy.deepcopy(canonical_completion)
    for candidate in mutated_completion["candidates"]:
        candidate["training_period"] = {"status": "INCOMPLETE"}
    mutated_completion["completion_digest"] = compute_completion_digest_v0(mutated_completion)
    with pytest.raises(ValueError, match=REASON_BINDING_COMPLETION_INVALID):
        materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
            repo_root=REPO_ROOT,
            fleet_binding_completion=mutated_completion,
        )


def test_shared_binding_mismatch_rejected(
    canonical_ratification: dict, canonical_completion: dict, production_bundle
) -> None:
    production, panel_series = production_bundle
    mutated_completion = copy.deepcopy(canonical_completion)
    for candidate in mutated_completion["candidates"]:
        if candidate["strategy_id"] == "bollinger_bands":
            candidate["period_binding"] = {
                **candidate["period_binding"],
                "period_binding_ref": "other_period_ref",
            }
    mutated_completion["completion_digest"] = compute_completion_digest_v0(mutated_completion)
    with pytest.raises(ValueError, match=REASON_BINDING_COMPLETION_INVALID):
        materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
            repo_root=REPO_ROOT,
            fleet_binding_completion=mutated_completion,
        )


def test_ratification_metadata(canonical_ratification: dict) -> None:
    assert canonical_ratification["schema_version"] == SCHEMA_VERSION
    assert canonical_ratification["ratification_id"] == RATIFICATION_ID
    assert canonical_ratification["fee_model_binding"]["fee_bps"] > 0
    assert canonical_ratification["slippage_model_binding"]["slippage_bps"] > 0
    assert canonical_ratification["walk_forward_policy_binding"]["bind"] is True
    assert canonical_ratification["monte_carlo_policy_binding"]["bind"] is True
    assert canonical_ratification["stress_policy_binding"]["bind"] is True
    assert canonical_ratification["parameter_sensitivity_policy_binding"]["bind"] is True
