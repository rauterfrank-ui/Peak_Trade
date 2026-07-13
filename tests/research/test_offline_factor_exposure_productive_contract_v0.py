"""Contract tests for operator-ratified productive factor exposure normative contract v0."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from src.backtest.economic_viability_evidence_v1 import (
    ECONOMIC_VIABILITY_EVIDENCE_LAYER_VERSION,
    ECONOMIC_VIABILITY_EVIDENCE_OWNER,
    EconomicViabilityEvidenceV1,
    EconomicViabilityStatus,
    MetricFieldV1,
    MetricSemantic,
)
from research.linear_evidence.factor_exposure import (
    FactorExposureEvidenceV1,
    FactorExposureInputV1,
    build_factor_matrix,
    compute_factor_exposure_precheck_v0,
    fit_factor_exposure,
)
from research.linear_evidence.factor_exposure_productive_contract_v0 import (
    EXPECTED_DATASET_DIGEST,
    EXPECTED_PRODUCTIVE_FACTOR_ORDER,
    PRODUCTIVE_EVIDENCE_TYPE,
    PRODUCTIVE_FACTOR_NAMES,
    PRODUCTIVE_MODEL_FAMILY,
    ProductiveJoinRejectionReason,
    TargetReturnContractV0,
    compute_instrument_universe_digest_v0,
    compute_target_return_decimal_v0,
    materialize_productive_input_row_v0,
    productive_factor_names_v0,
    resolve_productive_factor_values_v0,
    stable_digest_v0,
    validate_dataset_digest_v0,
    validate_productive_join_batch_v0,
    validate_time_order_v0,
)
from research.linear_evidence.import_boundary import scan_file_import_boundary
from research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    EXPECTED_DATASET_DIGEST as CANONICAL_EXPECTED_DATASET_DIGEST,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_MODULE = (
    REPO_ROOT / "src/research/linear_evidence/factor_exposure_productive_contract_v0.py"
)
FACTOR_EXPOSURE_MODULE = REPO_ROOT / "src/research/linear_evidence/factor_exposure.py"


def _trade(
    *,
    trade_id: str = "t-1",
    instrument_id: str = "inst-eth-usdt-perp",
    entry_time: str = "2026-01-01T00:00:00+00:00",
    exit_time: str = "2026-01-01T01:00:00+00:00",
    net_pnl: float = 10.0,
    notional: float = 1000.0,
) -> dict[str, object]:
    return {
        "trade_id": trade_id,
        "instrument_id": instrument_id,
        "entry_time": entry_time,
        "exit_time": exit_time,
        "net_pnl": net_pnl,
        "notional": notional,
    }


def _snapshot(
    *,
    trade_id: str = "t-1",
    instrument_id: str = "inst-eth-usdt-perp",
    entry_time: str = "2026-01-01T00:00:00+00:00",
    bar_timestamp: str = "2026-01-01T00:00:00+00:00",
    feature_timestamp: str = "2025-12-31T23:00:00+00:00",
    spread_bps: float = 10.0,
    volatility_estimate: float = 0.02,
    funding_rate: float = -0.0001,
    is_finalized: bool = True,
) -> dict[str, object]:
    return {
        "trade_id": trade_id,
        "instrument_id": instrument_id,
        "entry_time": entry_time,
        "bar_timestamp": bar_timestamp,
        "feature_timestamp": feature_timestamp,
        "spread_bps": spread_bps,
        "volatility_estimate": volatility_estimate,
        "funding_rate": funding_rate,
        "is_finalized": is_finalized,
    }


def _minimal_economic_viability_evidence(**overrides: object) -> EconomicViabilityEvidenceV1:
    base = EconomicViabilityEvidenceV1(
        contract_version=ECONOMIC_VIABILITY_EVIDENCE_LAYER_VERSION,
        owner=ECONOMIC_VIABILITY_EVIDENCE_OWNER,
        strategy_id="trend_following",
        strategy_version="v1",
        instrument_id_or_universe="inst-eth-usdt-perp",
        canonical_trading_logic_version="v1",
        data_period="p",
        training_period="p",
        validation_period="p",
        out_of_sample_period="p",
        fee_model_version="v1",
        slippage_model_version="v1",
        funding_model_version="v1",
        execution_model_version="v1",
        config_digest="c",
        implementation_digest="i",
        data_digest="d",
        gross_return=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        net_return=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        net_expectancy=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        profit_factor=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        sharpe=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        sortino=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        max_drawdown=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        calmar=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        trade_count=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        turnover=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        fee_drag=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        funding_drag=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        slippage_impact=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        tail_loss=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        time_in_market=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        long_contribution=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        short_contribution=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        regime_breakdown={},
        portfolio_contribution={},
        walk_forward_results={},
        monte_carlo_results={},
        stress_results={},
        parameter_sensitivity_results={},
        parameter_neighbor_degradation=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        single_trade_profit_contribution=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        single_regime_profit_contribution=MetricFieldV1(semantic=MetricSemantic.UNKNOWN),
        status=EconomicViabilityStatus.RESEARCH_ONLY,
        reason_codes=(),
        manifest_digest="m",
        wiring_chain_digest="w",
        randomness_seed=0,
        data_admissibility={},
        cost_binding={},
    )
    return replace(base, **overrides)  # type: ignore[arg-type]


def test_target_return_equals_net_pnl_over_entry_notional() -> None:
    value, reason = compute_target_return_decimal_v0(_trade(net_pnl=10.0, notional=1000.0))
    assert reason is None
    assert value == pytest.approx(0.01)


def test_target_return_stays_decimal_not_bps() -> None:
    value, _ = compute_target_return_decimal_v0(_trade(net_pnl=10.0, notional=1000.0))
    assert value == pytest.approx(0.01)
    assert value != pytest.approx(100.0)


def test_entry_notional_non_positive_blocks() -> None:
    _, reason = compute_target_return_decimal_v0(_trade(notional=0.0))
    assert reason == ProductiveJoinRejectionReason.TARGET_DENOMINATOR_NON_POSITIVE.value


def test_missing_net_pnl_blocks() -> None:
    trade = _trade()
    trade.pop("net_pnl")
    _, reason = compute_target_return_decimal_v0(trade)
    assert reason == ProductiveJoinRejectionReason.TARGET_NUMERATOR_MISSING.value


def test_non_finite_target_blocks() -> None:
    _, reason = compute_target_return_decimal_v0(_trade(net_pnl=float("nan")))
    assert reason == ProductiveJoinRejectionReason.TARGET_NON_FINITE.value


def test_target_time_is_exit_time() -> None:
    row, reason = materialize_productive_input_row_v0(
        trade=_trade(exit_time="2026-01-01T02:00:00+00:00"),
        snapshot=_snapshot(),
    )
    assert reason is None
    assert row is not None
    assert row.target_time == "2026-01-01T02:00:00+00:00"


def test_time_order_factor_before_decision_before_target() -> None:
    row, reason = materialize_productive_input_row_v0(trade=_trade(), snapshot=_snapshot())
    assert reason is None
    assert row is not None
    assert row.factor_time < row.decision_time < row.target_time


def test_equal_factor_and_decision_time_blocks() -> None:
    ts = "2026-01-01T00:00:00+00:00"
    reason = validate_time_order_v0(
        factor_time=ts,
        decision_time=ts,
        target_time="2026-01-01T01:00:00+00:00",
    )
    assert reason == ProductiveJoinRejectionReason.FEATURE_LEAKAGE_DETECTED.value


def test_decision_time_ge_target_time_blocks() -> None:
    reason = validate_time_order_v0(
        factor_time="2026-01-01T00:00:00+00:00",
        decision_time="2026-01-01T02:00:00+00:00",
        target_time="2026-01-01T01:00:00+00:00",
    )
    assert reason == ProductiveJoinRejectionReason.INVALID_TIME_ORDER.value


def test_unfinalized_trade_blocks() -> None:
    trade = _trade()
    trade.pop("exit_time")
    _, reason = materialize_productive_input_row_v0(trade=trade, snapshot=_snapshot())
    assert reason == ProductiveJoinRejectionReason.TARGET_TIME_MISSING


def test_unfinalized_factor_snapshot_blocks() -> None:
    _, reason = materialize_productive_input_row_v0(
        trade=_trade(),
        snapshot=_snapshot(is_finalized=False),
    )
    assert reason == ProductiveJoinRejectionReason.UNFINALIZED_FACTOR_INPUT


def test_exact_productive_factor_names() -> None:
    assert PRODUCTIVE_FACTOR_NAMES == (
        "funding_rate_abs",
        "spread_bps",
        "volatility_estimate",
    )


def test_exact_alphabetical_factor_order() -> None:
    assert productive_factor_names_v0() == EXPECTED_PRODUCTIVE_FACTOR_ORDER


def test_funding_rate_abs_uses_abs() -> None:
    values, reason = resolve_productive_factor_values_v0(_snapshot(funding_rate=-0.25))
    assert reason is None
    assert values is not None
    assert values["funding_rate_abs"] == pytest.approx(0.25)


def test_no_normalization_on_factor_values() -> None:
    values, _ = resolve_productive_factor_values_v0(_snapshot(spread_bps=10.0))
    assert values is not None
    assert values["spread_bps"] == pytest.approx(10.0)


def test_missing_factor_blocks() -> None:
    snap = _snapshot()
    snap.pop("spread_bps")
    _, reason = resolve_productive_factor_values_v0(snap)
    assert reason == ProductiveJoinRejectionReason.MISSING_FACTOR_VALUE.value


def test_non_finite_factor_blocks() -> None:
    _, reason = resolve_productive_factor_values_v0(_snapshot(volatility_estimate=float("inf")))
    assert reason == ProductiveJoinRejectionReason.NON_FINITE_FACTOR_VALUE.value


def test_zero_variance_blocked_by_existing_precheck() -> None:
    records = [
        FactorExposureInputV1(
            instrument_id="inst-eth-usdt-perp",
            timestamp=i,
            target_return=0.01,
            factor_values={
                "funding_rate_abs": 1.0,
                "spread_bps": float(i),
                "volatility_estimate": float(i % 3),
            },
            factor_time=f"2026-01-01T{i:02d}:00:00Z",
            decision_time=f"2026-01-01T{i + 1:02d}:00:00Z",
        )
        for i in range(1, 12)
    ]
    evidence = fit_factor_exposure(records)
    assert any("ZERO_VARIANCE_FACTOR" in str(code) for code in evidence.reason_codes)


def test_trade_id_is_primary_join_key() -> None:
    result = validate_productive_join_batch_v0(
        trade_ledger_rows=[_trade(trade_id="t-1")],
        factor_snapshots=[_snapshot(trade_id="t-1")],
    )
    assert len(result.admissible_rows) == 1


def test_missing_trade_id_blocks() -> None:
    trade = _trade()
    trade.pop("trade_id")
    result = validate_productive_join_batch_v0(
        trade_ledger_rows=[trade],
        factor_snapshots=[_snapshot()],
    )
    assert result.row_count_after_filter == 0
    assert ProductiveJoinRejectionReason.MISSING_TRADE_ID.value in result.dropped_rows_by_reason


def test_duplicate_trade_id_blocks() -> None:
    result = validate_productive_join_batch_v0(
        trade_ledger_rows=[_trade(trade_id="t-1"), _trade(trade_id="t-1")],
        factor_snapshots=[_snapshot(trade_id="t-1")],
    )
    assert ProductiveJoinRejectionReason.DUPLICATE_TRADE_ID.value in result.dropped_rows_by_reason


def test_instrument_id_conflict_blocks() -> None:
    result = validate_productive_join_batch_v0(
        trade_ledger_rows=[_trade(trade_id="t-1", instrument_id="inst-a")],
        factor_snapshots=[_snapshot(trade_id="t-1", instrument_id="inst-b")],
    )
    assert (
        ProductiveJoinRejectionReason.INSTRUMENT_ID_MISMATCH.value in result.dropped_rows_by_reason
    )


def test_entry_time_conflict_blocks() -> None:
    result = validate_productive_join_batch_v0(
        trade_ledger_rows=[_trade(trade_id="t-1", entry_time="2026-01-01T00:00:00+00:00")],
        factor_snapshots=[
            _snapshot(
                trade_id="t-1",
                entry_time="2026-01-01T01:00:00+00:00",
                bar_timestamp="2026-01-01T01:00:00+00:00",
            )
        ],
    )
    assert ProductiveJoinRejectionReason.ENTRY_TIME_MISMATCH.value in result.dropped_rows_by_reason


def test_orphan_factor_row_blocks() -> None:
    result = validate_productive_join_batch_v0(
        trade_ledger_rows=[_trade(trade_id="t-1")],
        factor_snapshots=[_snapshot(trade_id="t-1"), _snapshot(trade_id="orphan")],
    )
    assert ProductiveJoinRejectionReason.ORPHAN_FACTOR_ROW.value in result.dropped_rows_by_reason


def test_missing_factor_snapshot_blocks() -> None:
    result = validate_productive_join_batch_v0(
        trade_ledger_rows=[_trade(trade_id="t-1")],
        factor_snapshots=[],
    )
    assert (
        ProductiveJoinRejectionReason.MISSING_FACTOR_SNAPSHOT.value in result.dropped_rows_by_reason
    )


def test_dataset_digest_must_match_canonical_owner() -> None:
    validate_dataset_digest_v0(CANONICAL_EXPECTED_DATASET_DIGEST)
    with pytest.raises(ValueError, match="DATASET_DIGEST_CANONICAL_OWNER_MISMATCH"):
        validate_dataset_digest_v0("0" * 64)


def test_universe_digest_deterministic() -> None:
    first = compute_instrument_universe_digest_v0(["inst-b", "inst-a"])
    second = compute_instrument_universe_digest_v0(["inst-a", "inst-b"])
    assert first == second


def test_universe_digest_uses_sorted_instruments_only() -> None:
    digest_a = compute_instrument_universe_digest_v0(["inst-a"])
    digest_b = compute_instrument_universe_digest_v0(["inst-b"])
    assert digest_a != digest_b


def test_provenance_fields_serialize_fully() -> None:
    from research.linear_evidence.factor_exposure_productive_contract_v0 import (
        FactorExposureProductiveProvenanceV0,
    )

    provenance = FactorExposureProductiveProvenanceV0(
        dataset_digest=EXPECTED_DATASET_DIGEST,
        instrument_universe=("inst-eth-usdt-perp",),
        instrument_universe_digest=stable_digest_v0(["inst-eth-usdt-perp"]),
        implementation_digest="impl",
        source_trade_ledger_digest="ledger",
        source_factor_snapshot_digest="snapshots",
        time_range={"start": "a", "end": "b"},
        row_count_before_filter=10,
        row_count_after_filter=8,
        dropped_rows_by_reason={"MISSING_FACTOR_SNAPSHOT": 2},
    )
    evidence = FactorExposureEvidenceV1(
        evidence_type=PRODUCTIVE_EVIDENCE_TYPE,
        model_family=PRODUCTIVE_MODEL_FAMILY,
        target_name=TargetReturnContractV0().target_name,
        feature_names=PRODUCTIVE_FACTOR_NAMES,
        n_samples=8,
        n_features=3,
        solver="numpy.linalg.lstsq",
        fit_intercept=True,
        coefficients={},
        diagnostics={},
        feature_matrix_digest="x",
        target_digest="y",
        config_digest="c",
        validation_policy="time_ordered",
        status="DIAGNOSTIC_ONLY",
        reason_codes=(),
        authority_effect="NONE",
        runtime_effect="NONE",
        productive_provenance=provenance,
    )
    payload = evidence.to_dict()
    assert payload["dataset_digest"] == EXPECTED_DATASET_DIGEST
    assert payload["instrument_universe"] == ["inst-eth-usdt-perp"]
    assert payload["join_contract_version"] == "offline_factor_exposure_trade_join_v0"
    assert json.dumps(payload)


def test_factor_exposure_ref_optional_and_backward_compatible() -> None:
    without_ref = _minimal_economic_viability_evidence()
    assert "factor_exposure_ref" not in without_ref.to_semantic_dict()

    with_ref = _minimal_economic_viability_evidence(factor_exposure_ref="bundle/path")
    assert with_ref.to_semantic_dict()["factor_exposure_ref"] == "bundle/path"


def test_authority_and_runtime_effects_remain_none() -> None:
    contract_hits = scan_file_import_boundary(CONTRACT_MODULE, repo_root=REPO_ROOT)
    exposure_hits = scan_file_import_boundary(FACTOR_EXPOSURE_MODULE, repo_root=REPO_ROOT)
    assert contract_hits == []
    assert exposure_hits == []

    row, _ = materialize_productive_input_row_v0(trade=_trade(), snapshot=_snapshot())
    assert row is not None
    result = validate_productive_join_batch_v0(
        trade_ledger_rows=[_trade()],
        factor_snapshots=[_snapshot()],
    )
    assert result.authority_effect == "NONE"
    assert result.runtime_effect == "NONE"


def test_existing_factor_exposure_evidence_backward_compatible() -> None:
    records = [
        FactorExposureInputV1(
            instrument_id="inst-eth-usdt-perp",
            timestamp=i,
            target_return=0.01,
            factor_values={
                "funding_rate_abs": float(i) * 0.01,
                "spread_bps": float(i % 3) * 0.01,
                "volatility_estimate": float(i % 5) * 0.01,
            },
            factor_time=f"2026-01-01T{i:02d}:00:00Z",
            decision_time=f"2026-01-01T{i + 1:02d}:00:00Z",
        )
        for i in range(1, 12)
    ]
    evidence = fit_factor_exposure(records)
    payload = evidence.to_dict()
    assert "dataset_digest" not in payload
    assert evidence.productive_provenance is None


def test_build_factor_matrix_stable_order_for_productive_names() -> None:
    records = [
        FactorExposureInputV1(
            instrument_id="inst-eth-usdt-perp",
            timestamp=1,
            target_return=0.01,
            factor_values={
                "volatility_estimate": 0.02,
                "spread_bps": 10.0,
                "funding_rate_abs": 0.001,
            },
            factor_time="2026-01-01T01:00:00Z",
            decision_time="2026-01-01T02:00:00Z",
        )
    ]
    _, _, names, _, _ = build_factor_matrix(records)
    assert names == EXPECTED_PRODUCTIVE_FACTOR_ORDER
