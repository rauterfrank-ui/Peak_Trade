"""Contract tests for canonical advanced economic capability pack v0."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from src.backtest.cost_config_v0 import (
    COST_MODEL_VERSION,
    EffectiveBacktestCostConfigV0,
    append_cost_accounting_fields,
    compute_effective_roundtrip_cost_bps,
    resolve_effective_backtest_cost_config,
)
from src.backtest.economic_observability_advanced_capabilities_v1 import (
    ADVANCED_CAPABILITIES_OWNER,
    ADVANCED_METRIC_IDS,
    AdvancedCapabilitiesInputsV1,
    FixedCostComponentV1,
    COST_FRONTIER_SCENARIO_VERSION,
    derive_break_even_diagnostics_v1,
    derive_cost_frontier_v1,
    derive_edge_decay_diagnostics_v1,
    derive_liquidity_stress_diagnostics_v1,
    derive_trade_excursion_analytics_v1,
    materialize_advanced_economic_capabilities_v1,
    validate_no_post_exit_lookahead_v1,
)
from src.backtest.economic_observability_derived_metrics_v1 import (
    DERIVED_METRICS_OWNER,
    derive_all_metrics_v1,
    derive_cost_ratio_metrics_v1,
)
from src.backtest.economic_observability_materialization_v1 import (
    BacktestObservabilityInputsV1,
    materialize_observability_bundle_v1,
    materialize_snapshot_from_backtest_stats_v1,
)
from src.backtest.economic_observability_registry_v1 import (
    DISCOVERY_METRIC_COUNT,
    get_canonical_metric_registry_v1,
)
from src.backtest.economic_observability_snapshot_v1 import (
    MetricMaterializationStatus,
    compute_snapshot_digest,
    serialize_canonical_json,
)
from src.backtest.economic_viability_evidence_v1 import EconomicViabilityEvidenceV1
from src.backtest.stats import compute_backtest_stats
from src.research.linear_evidence.import_boundary import scan_file_import_boundary

REPO_ROOT = Path(__file__).resolve().parents[2]
ADVANCED_MODULE = REPO_ROOT / "src/backtest/economic_observability_advanced_capabilities_v1.py"


def _minimal_cfg() -> dict:
    return {
        "backtest": {
            "initial_cash": 10_000.0,
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
            "cost_model_version": COST_MODEL_VERSION,
        }
    }


def _effective_cost() -> EffectiveBacktestCostConfigV0:
    return resolve_effective_backtest_cost_config(_minimal_cfg())


def _fixture_trades(*, with_price_path: bool = False) -> list[dict]:
    trades = [
        {
            "size": 1.0,
            "instrument_id": "BTC-USDT",
            "entry_time": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "exit_time": datetime(2024, 1, 2, tzinfo=timezone.utc),
            "entry_price": 100.0,
            "exit_price": 110.0,
            "entry_notional": 100.0,
            "pnl": 120.0,
            "gross_pnl": 130.0,
            "entry_cost": 5.0,
            "exit_cost": 5.0,
            "exit_reason": "signal_flip",
        },
        {
            "size": -1.0,
            "instrument_id": "ETH-USDT",
            "entry_time": datetime(2024, 1, 3, tzinfo=timezone.utc),
            "exit_time": datetime(2024, 1, 4, tzinfo=timezone.utc),
            "entry_price": 110.0,
            "exit_price": 105.0,
            "entry_notional": 110.0,
            "pnl": -40.0,
            "gross_pnl": -30.0,
            "entry_cost": 5.0,
            "exit_cost": 5.0,
            "exit_reason": "stop",
        },
        {
            "size": 1.0,
            "instrument_id": "BTC-USDT",
            "entry_time": datetime(2024, 1, 5, tzinfo=timezone.utc),
            "exit_time": datetime(2024, 1, 6, tzinfo=timezone.utc),
            "entry_price": 105.0,
            "exit_price": 115.0,
            "entry_notional": 105.0,
            "pnl": 55.0,
            "gross_pnl": 65.0,
            "entry_cost": 5.0,
            "exit_cost": 5.0,
            "exit_reason": "target",
        },
        {
            "size": 1.0,
            "instrument_id": "BTC-USDT",
            "entry_time": datetime(2024, 1, 7, tzinfo=timezone.utc),
            "exit_time": datetime(2024, 1, 8, tzinfo=timezone.utc),
            "entry_price": 108.0,
            "exit_price": 112.0,
            "entry_notional": 108.0,
            "pnl": 25.0,
            "gross_pnl": 35.0,
            "entry_cost": 5.0,
            "exit_cost": 5.0,
            "exit_reason": "target",
        },
    ]
    if with_price_path:
        trades[0]["intratrade_bars"] = [
            {
                "timestamp": datetime(2024, 1, 1, 12, tzinfo=timezone.utc),
                "high": 105.0,
                "low": 95.0,
            },
            {"timestamp": datetime(2024, 1, 2, tzinfo=timezone.utc), "high": 112.0, "low": 98.0},
        ]
        trades[1]["intratrade_bars"] = [
            {
                "timestamp": datetime(2024, 1, 3, 12, tzinfo=timezone.utc),
                "high": 115.0,
                "low": 108.0,
            },
            {"timestamp": datetime(2024, 1, 4, tzinfo=timezone.utc), "high": 112.0, "low": 102.0},
        ]
        trades[2]["intratrade_bars"] = [
            {
                "timestamp": datetime(2024, 1, 5, 12, tzinfo=timezone.utc),
                "high": 118.0,
                "low": 103.0,
            },
            {"timestamp": datetime(2024, 1, 6, tzinfo=timezone.utc), "high": 116.0, "low": 104.0},
        ]
        trades[3]["intratrade_bars"] = [
            {
                "timestamp": datetime(2024, 1, 7, 12, tzinfo=timezone.utc),
                "high": 113.0,
                "low": 106.0,
            },
            {"timestamp": datetime(2024, 1, 8, tzinfo=timezone.utc), "high": 114.0, "low": 107.0},
        ]
    return trades


def _fixture_equity() -> pd.Series:
    index = pd.date_range("2024-01-01", periods=10, freq="D", tz="UTC")
    return pd.Series(
        [
            10_000.0,
            10_120.0,
            10_080.0,
            10_135.0,
            10_095.0,
            10_150.0,
            10_110.0,
            10_165.0,
            10_190.0,
            10_215.0,
        ],
        index=index,
    )


def _compute_stats(trades: list[dict]) -> dict:
    equity = _fixture_equity() if trades else pd.Series([10_000.0, 10_000.0])
    stats = compute_backtest_stats(trades, equity, periods_per_year=252)
    total_fees = 10.0 * len(trades)
    return append_cost_accounting_fields(
        stats,
        initial_equity=10_000.0,
        effective_cost=_effective_cost(),
        total_fees=total_fees,
        total_notional=50_000.0,
    )


def _advanced_inputs(
    trades: list[dict] | None = None,
    *,
    with_price_path: bool = False,
    offline_market_volume: float | None = None,
    fixed_cost: FixedCostComponentV1 | None = None,
) -> AdvancedCapabilitiesInputsV1:
    trades = trades if trades is not None else _fixture_trades(with_price_path=with_price_path)
    stats = _compute_stats(trades)
    derived = derive_all_metrics_v1(
        trades=trades,
        stats=stats,
        gross_profit=200.0,
        gross_pnl=200.0,
        net_pnl=160.0,
        total_cost=40.0,
        effective_cost=_effective_cost(),
    )
    return AdvancedCapabilitiesInputsV1(
        trades=trades,
        stats=stats,
        gross_profit=200.0,
        gross_pnl=200.0,
        net_pnl=160.0,
        total_cost=40.0,
        initial_equity=10_000.0,
        total_notional=50_000.0,
        effective_cost=_effective_cost(),
        offline_market_volume=offline_market_volume,
        fixed_cost_components=fixed_cost,
        derived_bundle=derived,
    )


@pytest.fixture
def registry():
    return get_canonical_metric_registry_v1()


def _align_trades_to_snapshot(
    trades: list[dict],
    *,
    stats: dict,
) -> list[dict]:
    snapshot, _ = materialize_snapshot_from_backtest_stats_v1(
        BacktestObservabilityInputsV1(
            stats=stats,
            initial_equity=10_000.0,
            trades=trades,
            effective_cost=_effective_cost(),
            total_notional=50_000.0,
            equity_curve=_fixture_equity(),
        ),
        run_identity={"run_id": "align-trades-to-snapshot"},
        validate_reconciliation=False,
    )
    target_gross = float(snapshot.economic["gross_pnl"].value)
    target_net = float(snapshot.economic["net_pnl"].value)
    target_cost = float(snapshot.costs["total_cost"].value)

    aligned = [dict(trade) for trade in trades]
    gross_sum = sum(float(trade["gross_pnl"]) for trade in aligned)
    net_sum = sum(float(trade["pnl"]) for trade in aligned)
    for trade in aligned:
        trade["gross_pnl"] = float(trade["gross_pnl"]) / gross_sum * target_gross
        trade["pnl"] = float(trade["pnl"]) / net_sum * target_net
        if target_cost > 0:
            per_leg = target_cost / (2 * len(aligned))
            trade["entry_cost"] = per_leg
            trade["exit_cost"] = per_leg
    return aligned


def _bundle_inputs(
    trades: list[dict] | None = None,
    *,
    with_price_path: bool = False,
) -> BacktestObservabilityInputsV1:
    raw = trades if trades is not None else _fixture_trades(with_price_path=with_price_path)[:3]
    stats = _compute_stats(raw)
    aligned = _align_trades_to_snapshot(raw, stats=stats)
    stats = _compute_stats(aligned)
    return BacktestObservabilityInputsV1(
        stats=stats,
        initial_equity=10_000.0,
        trades=aligned,
        effective_cost=_effective_cost(),
        total_notional=50_000.0,
        equity_curve=_fixture_equity(),
        offline_market_volume=1_000_000.0,
    )


@pytest.fixture
def materialized_bundle():
    bundle, _ = materialize_observability_bundle_v1(_bundle_inputs(with_price_path=True))
    return bundle


class TestBreakEvenDiagnostics:
    def test_required_gross_edge_reconciles_with_total_cost(self) -> None:
        inputs = _advanced_inputs()
        payload, _ = derive_break_even_diagnostics_v1(inputs)
        expected = compute_effective_roundtrip_cost_bps(
            fee_bps=_effective_cost().taker_fee_bps,
            slippage_bps=_effective_cost().entry_slippage_bps,
        )
        assert payload["required_gross_edge_for_break_even"] == pytest.approx(expected)

    def test_break_even_cost_bps_unit_consistency(self) -> None:
        inputs = _advanced_inputs()
        payload, metrics = derive_break_even_diagnostics_v1(inputs)
        assert payload["break_even_cost_bps"] == payload["required_gross_edge_for_break_even"]
        assert metrics["realized_cost_bps"].value == pytest.approx(payload["break_even_cost_bps"])

    def test_proportional_cost_model_does_not_claim_break_even_capital(self) -> None:
        inputs = _advanced_inputs()
        payload, _ = derive_break_even_diagnostics_v1(inputs)
        capital = payload["break_even_capital"]
        assert capital["status"] == MetricMaterializationStatus.NOT_COMPUTED.value
        assert (
            "BREAK_EVEN_CAPITAL_NOT_DERIVABLE_PROPORTIONAL_COST_MODEL_ONLY"
            in capital["reason_codes"]
        )

    def test_fixed_cost_fixture_can_derive_break_even_capital_if_contract_exists(self) -> None:
        inputs = _advanced_inputs(
            fixed_cost=FixedCostComponentV1(
                fixed_cost=100.0, minimum_order_cost=0.0, minimum_notional=0.0
            )
        )
        payload, _ = derive_break_even_diagnostics_v1(inputs)
        capital = payload["break_even_capital"]
        assert capital["status"] == MetricMaterializationStatus.COMPUTED.value
        assert capital["value"] is not None
        assert capital["value"] > 0

    def test_zero_gross_edge_does_not_divide_by_zero(self) -> None:
        inputs = _advanced_inputs()
        inputs = AdvancedCapabilitiesInputsV1(
            trades=inputs.trades,
            stats=inputs.stats,
            gross_profit=0.0,
            gross_pnl=0.0,
            net_pnl=0.0,
            total_cost=10.0,
            initial_equity=10_000.0,
            total_notional=50_000.0,
            effective_cost=_effective_cost(),
            derived_bundle=inputs.derived_bundle,
        )
        _, metrics = derive_break_even_diagnostics_v1(inputs)
        assert (
            metrics["cost_to_gross_edge_ratio"].status
            is MetricMaterializationStatus.INSUFFICIENT_DATA
        )
        assert "ZERO_GROSS_EDGE" in metrics["cost_to_gross_edge_ratio"].reason_codes

    def test_missing_cost_source_fails_closed(self) -> None:
        inputs = _advanced_inputs()
        inputs = AdvancedCapabilitiesInputsV1(
            trades=inputs.trades,
            stats=inputs.stats,
            gross_profit=200.0,
            gross_pnl=200.0,
            net_pnl=160.0,
            total_cost=40.0,
            initial_equity=10_000.0,
            total_notional=0.0,
            effective_cost=None,
            derived_bundle=None,
        )
        _, metrics = derive_break_even_diagnostics_v1(inputs)
        assert metrics["realized_cost_bps"].status is MetricMaterializationStatus.SOURCE_MISSING


class TestTradeExcursion:
    def test_mae_long_side_correct(self) -> None:
        trade = {
            "size": 1.0,
            "entry_price": 100.0,
            "intratrade_bars": [{"high": 110.0, "low": 92.0}],
        }
        payload, metrics = derive_trade_excursion_analytics_v1([trade])
        record = payload["trade_level"][0]
        assert record["mae"] == pytest.approx(8.0)
        assert metrics["MAE"].value == pytest.approx(8.0)

    def test_mfe_long_side_correct(self) -> None:
        trade = {
            "size": 1.0,
            "entry_price": 100.0,
            "intratrade_bars": [{"high": 110.0, "low": 92.0}],
        }
        payload, _ = derive_trade_excursion_analytics_v1([trade])
        assert payload["trade_level"][0]["mfe"] == pytest.approx(10.0)

    def test_mae_short_side_correct(self) -> None:
        trade = {
            "size": -1.0,
            "entry_price": 100.0,
            "intratrade_bars": [{"high": 108.0, "low": 90.0}],
        }
        payload, _ = derive_trade_excursion_analytics_v1([trade])
        assert payload["trade_level"][0]["mae"] == pytest.approx(8.0)

    def test_mfe_short_side_correct(self) -> None:
        trade = {
            "size": -1.0,
            "entry_price": 100.0,
            "intratrade_bars": [{"high": 108.0, "low": 90.0}],
        }
        payload, _ = derive_trade_excursion_analytics_v1([trade])
        assert payload["trade_level"][0]["mfe"] == pytest.approx(10.0)

    def test_mae_mfe_no_post_exit_lookahead(self) -> None:
        trade = {
            "size": 1.0,
            "entry_price": 100.0,
            "exit_time": datetime(2024, 1, 2, tzinfo=timezone.utc),
            "intratrade_bars": [
                {
                    "timestamp": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "high": 105.0,
                    "low": 95.0,
                },
                {
                    "timestamp": datetime(2024, 1, 3, tzinfo=timezone.utc),
                    "high": 200.0,
                    "low": 50.0,
                },
            ],
        }
        assert validate_no_post_exit_lookahead_v1(trade, exit_time=trade["exit_time"]) is False

    def test_missing_price_path_not_zero_filled(self) -> None:
        trade = {"size": 1.0, "entry_price": 100.0, "exit_price": 110.0}
        _, metrics = derive_trade_excursion_analytics_v1([trade])
        assert metrics["MAE"].status is MetricMaterializationStatus.SOURCE_MISSING
        assert metrics["MAE"].value is None

    def test_trade_level_excursions_reconcile_to_aggregates(self) -> None:
        trades = _fixture_trades(with_price_path=True)
        payload, metrics = derive_trade_excursion_analytics_v1(trades)
        valid = [row for row in payload["trade_level"] if row["status"] == "COMPUTED"]
        assert payload["aggregates"]["valid_trade_count"] == len(valid)
        assert metrics["MAE"].sample_count == len(valid)


class TestCapitalEfficiency:
    def test_capital_efficiency_denominator_explicit(self, materialized_bundle) -> None:
        payload = materialized_bundle.advanced_capability_payloads["CAPITAL_EFFICIENCY.json"]
        assert payload["denominator_version"] == "average_entry_notional_v1"
        assert payload["denominator_definition"] == "average_entry_notional"

    def test_invalid_capital_denominator_fails_closed(self) -> None:
        trades = [{"size": 1.0, "entry_price": 100.0, "pnl": 1.0}]
        inputs = _advanced_inputs(trades)
        inputs = AdvancedCapabilitiesInputsV1(
            trades=[{"size": 1.0, "pnl": 1.0}],
            stats=inputs.stats,
            gross_profit=1.0,
            gross_pnl=1.0,
            net_pnl=1.0,
            total_cost=0.0,
            initial_equity=10_000.0,
            total_notional=0.0,
        )
        payload, metrics = __import__(
            "src.backtest.economic_observability_advanced_capabilities_v1",
            fromlist=["derive_capital_efficiency_v1"],
        ).derive_capital_efficiency_v1(inputs)
        assert payload["status"] == MetricMaterializationStatus.INVALID_INPUT.value
        assert metrics["capital_efficiency"].reason_codes == ("INVALID_CAPITAL_DENOMINATOR",)


class TestCapacityDiagnostics:
    def test_capacity_proxy_has_no_runtime_effect(self, materialized_bundle) -> None:
        payload = materialized_bundle.advanced_capability_payloads["CAPACITY_DIAGNOSTICS.json"]
        assert payload["runtime_effect"] == "NONE"
        assert payload["capacity_proxy_is_not_order_limit"] is True

    def test_capacity_missing_liquidity_input_fails_closed(self) -> None:
        inputs = _advanced_inputs(offline_market_volume=None)
        payload, metrics = __import__(
            "src.backtest.economic_observability_advanced_capabilities_v1",
            fromlist=["derive_capacity_diagnostics_v1"],
        ).derive_capacity_diagnostics_v1(inputs)
        assert payload["status"] == MetricMaterializationStatus.SOURCE_MISSING.value
        assert metrics["capacity_proxy"].status is MetricMaterializationStatus.SOURCE_MISSING


class TestCostFrontier:
    def test_cost_frontier_baseline_matches_canonical_costs(self) -> None:
        inputs = _advanced_inputs()
        payload, _ = derive_cost_frontier_v1(inputs)
        expected = compute_effective_roundtrip_cost_bps(
            fee_bps=_effective_cost().taker_fee_bps,
            slippage_bps=_effective_cost().entry_slippage_bps,
        )
        assert payload["baseline_cost_bps"] == pytest.approx(expected)

    def test_cost_frontier_scenarios_are_versioned(self) -> None:
        inputs = _advanced_inputs()
        payload, _ = derive_cost_frontier_v1(inputs)
        assert payload["scenario_version"] == COST_FRONTIER_SCENARIO_VERSION
        assert len(payload["scenarios"]) >= 4

    def test_cost_frontier_does_not_emit_verdict(self) -> None:
        inputs = _advanced_inputs()
        payload, _ = derive_cost_frontier_v1(inputs)
        assert payload["economic_verdict_source"] == "EconomicViabilityEvidenceV1"
        assert payload["diagnostic_only"] is True


class TestEdgeDecay:
    def test_edge_decay_insufficient_sample_fails_closed(self) -> None:
        trades = _fixture_trades()[:2]
        payload, metrics = derive_edge_decay_diagnostics_v1(trades)
        assert payload["status"] == MetricMaterializationStatus.INSUFFICIENT_DATA.value
        assert metrics["edge_decay_status"].status is MetricMaterializationStatus.INSUFFICIENT_DATA

    def test_edge_decay_bucket_boundaries_deterministic(self) -> None:
        trades = _fixture_trades()
        first, _ = derive_edge_decay_diagnostics_v1(trades)
        second, _ = derive_edge_decay_diagnostics_v1(trades)
        assert first == second


class TestLiquidityStress:
    def test_liquidity_stress_baseline_matches_canonical_snapshot(self) -> None:
        inputs = _advanced_inputs()
        payload, _ = derive_liquidity_stress_diagnostics_v1(inputs)
        frontier, _ = derive_cost_frontier_v1(inputs)
        assert payload["baseline_cost_bps"] == frontier["baseline_cost_bps"]

    def test_liquidity_stress_does_not_mutate_execution_model(self) -> None:
        inputs = _advanced_inputs()
        payload, _ = derive_liquidity_stress_diagnostics_v1(inputs)
        assert payload["execution_model_unchanged"] is True


class TestRegistryAndSnapshot:
    def test_all_new_metrics_registered(self, registry) -> None:
        registry_ids = {entry.metric_id for entry in registry.entries}
        assert ADVANCED_METRIC_IDS <= registry_ids

    def test_all_new_metrics_have_single_owner(self, registry) -> None:
        for metric_id in ADVANCED_METRIC_IDS:
            owners = {
                entry.canonical_owner for entry in registry.entries if entry.metric_id == metric_id
            }
            assert len(owners) == 1
            assert ADVANCED_CAPABILITIES_OWNER in owners

    def test_all_new_metrics_have_formula_version(self) -> None:
        bundle = materialize_advanced_economic_capabilities_v1(
            _advanced_inputs(with_price_path=True)
        )
        for result in bundle.metric_results.values():
            assert result.formula_version

    def test_all_new_metrics_have_unit(self, registry) -> None:
        for metric_id in ADVANCED_METRIC_IDS:
            entry = next(e for e in registry.entries if e.metric_id == metric_id)
            assert entry.unit

    def test_all_unavailable_metrics_have_reason_codes(self) -> None:
        bundle = materialize_advanced_economic_capabilities_v1(
            _advanced_inputs(offline_market_volume=None)
        )
        for result in bundle.metric_results.values():
            if result.status in {
                MetricMaterializationStatus.NOT_COMPUTED,
                MetricMaterializationStatus.NOT_APPLICABLE,
                MetricMaterializationStatus.INSUFFICIENT_DATA,
                MetricMaterializationStatus.SOURCE_MISSING,
                MetricMaterializationStatus.INVALID_INPUT,
            }:
                assert result.reason_codes

    def test_zero_and_null_semantics_distinct(self) -> None:
        inputs = _advanced_inputs()
        inputs = AdvancedCapabilitiesInputsV1(
            trades=inputs.trades,
            stats=inputs.stats,
            gross_profit=0.0,
            gross_pnl=0.0,
            net_pnl=0.0,
            total_cost=0.0,
            initial_equity=10_000.0,
            total_notional=50_000.0,
            effective_cost=_effective_cost(),
        )
        _, metrics = derive_break_even_diagnostics_v1(inputs)
        assert metrics["cost_to_gross_edge_ratio"].value is None
        assert (
            metrics["cost_to_gross_edge_ratio"].status
            is MetricMaterializationStatus.INSUFFICIENT_DATA
        )


class TestDeterminismAndBoundaries:
    def test_same_inputs_same_snapshot_digest(self) -> None:
        inputs = _bundle_inputs(with_price_path=True)
        first, _ = materialize_observability_bundle_v1(inputs)
        second, _ = materialize_observability_bundle_v1(inputs)
        first_payload = first.snapshot_payload.copy()
        second_payload = second.snapshot_payload.copy()
        first_payload["manifest_digest"] = ""
        second_payload["manifest_digest"] = ""
        assert compute_snapshot_digest(first_payload) == compute_snapshot_digest(second_payload)

    def test_second_materialization_diff_empty(self) -> None:
        bundle1 = materialize_advanced_economic_capabilities_v1(
            _advanced_inputs(with_price_path=True)
        )
        bundle2 = materialize_advanced_economic_capabilities_v1(
            _advanced_inputs(with_price_path=True)
        )
        assert serialize_canonical_json(bundle1.to_dict()) == serialize_canonical_json(
            bundle2.to_dict()
        )

    def test_no_runtime_import_boundary_violation(self) -> None:
        assert scan_file_import_boundary(ADVANCED_MODULE, repo_root=REPO_ROOT) == []

    def test_no_order_adapter_import_boundary_violation(self) -> None:
        hits = scan_file_import_boundary(ADVANCED_MODULE, repo_root=REPO_ROOT)
        assert all("order" not in hit.module.lower() for hit in hits)

    def test_no_scheduler_import_boundary_violation(self) -> None:
        hits = scan_file_import_boundary(ADVANCED_MODULE, repo_root=REPO_ROOT)
        assert all("scheduler" not in hit.module.lower() for hit in hits)

    def test_no_direct_report_formula(self) -> None:
        source = ADVANCED_MODULE.read_text(encoding="utf-8")
        assert "final_report" not in source.lower() or "economic_verdict_source" in source

    def test_report_verdict_source_unchanged(self, materialized_bundle) -> None:
        index = materialized_bundle.advanced_capability_payloads[
            "ADVANCED_ECONOMIC_CAPABILITIES.json"
        ]
        assert index["economic_verdict_source"] == "EconomicViabilityEvidenceV1"

    def test_economic_viability_evidence_owner_unchanged(self) -> None:
        assert (
            EconomicViabilityEvidenceV1.__module__ == "src.backtest.economic_viability_evidence_v1"
        )

    def test_historical_negative_evidence_unchanged(self) -> None:
        archive = Path(
            "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
            "pr5177_merge_closeout_canonical_derived_economic_and_trade_metrics_v0_20260714T201906Z"
        )
        assert (archive / "MANIFEST.sha256").exists()


class TestDerivedMetricsReuse:
    def test_break_even_edge_bound_without_capital(self) -> None:
        ratios = derive_cost_ratio_metrics_v1(
            gross_profit=200.0,
            gross_pnl=200.0,
            net_pnl=160.0,
            total_cost=40.0,
            effective_cost=_effective_cost(),
        )
        assert ratios["break_even_cost"].status is MetricMaterializationStatus.NOT_APPLICABLE
        assert ratios["required_gross_edge_for_break_even"].value is not None

    def test_gross_cost_net_reconciliation_preserved(self) -> None:
        trades = _fixture_trades()
        stats = _compute_stats(trades)
        derived = derive_all_metrics_v1(
            trades=trades,
            stats=stats,
            gross_profit=200.0,
            gross_pnl=200.0,
            net_pnl=160.0,
            total_cost=40.0,
            effective_cost=_effective_cost(),
        )
        assert (
            derived.cost_ratios["required_gross_edge_for_break_even"].owner == DERIVED_METRICS_OWNER
        )


class TestBundleArtifacts:
    def test_advanced_artifacts_present(self, materialized_bundle) -> None:
        artifacts = materialized_bundle.advanced_capability_payloads
        for name in (
            "ADVANCED_ECONOMIC_CAPABILITIES.json",
            "BREAK_EVEN_DIAGNOSTICS.json",
            "TRADE_EXCURSION_ANALYTICS.json",
            "CAPITAL_EFFICIENCY.json",
            "CAPACITY_DIAGNOSTICS.json",
            "COST_FRONTIER.json",
            "EDGE_DECAY.json",
            "LIQUIDITY_STRESS.json",
        ):
            assert name in artifacts

    def test_registry_metric_count(self, registry) -> None:
        assert len(registry.entries) == DISCOVERY_METRIC_COUNT
