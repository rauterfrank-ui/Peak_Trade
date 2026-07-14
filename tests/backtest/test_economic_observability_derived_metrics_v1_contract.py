"""Contract tests for canonical derived economic/trade observability metrics v1."""

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
    resolve_effective_backtest_cost_config,
)
from src.backtest.decision_funnel_v0 import materialize_decision_funnel_persistence_v0
from src.backtest.economic_observability_derived_metrics_v1 import (
    CANONICAL_DERIVED_METRICS_OWNER,
    DERIVED_METRICS_OWNER,
    SCOPE_METRIC_ALIASES,
    derive_all_metrics_v1,
    derive_drawdown_episode_metrics_v1,
    derive_stage_conversion_rates_v1,
    derive_trade_aggregates_v1,
    validate_exit_reason_counts_v1,
    validate_pnl_breakdown_reconciliation_v1,
)
from src.backtest.economic_observability_materialization_v1 import (
    BacktestObservabilityInputsV1,
    MATERIALIZATION_OWNER,
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
    materialize_empty_snapshot_v1,
    serialize_canonical_json,
)
from src.backtest.stats import compute_backtest_stats
from src.research.linear_evidence.import_boundary import scan_file_import_boundary

REPO_ROOT = Path(__file__).resolve().parents[2]
DERIVED_MODULE = REPO_ROOT / "src/backtest/economic_observability_derived_metrics_v1.py"


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


def _fixture_trades(*, with_regime: bool = False) -> list[dict]:
    trades = [
        {
            "size": 1.0,
            "instrument_id": "BTC-USDT",
            "entry_time": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "exit_time": datetime(2024, 1, 2, tzinfo=timezone.utc),
            "entry_price": 100.0,
            "exit_price": 110.0,
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
            "pnl": 55.0,
            "gross_pnl": 65.0,
            "entry_cost": 5.0,
            "exit_cost": 5.0,
            "exit_reason": "target",
        },
    ]
    if with_regime:
        for index, trade in enumerate(trades):
            trade["regime"] = "trend" if index % 2 == 0 else "range"
    return trades


def _fixture_equity() -> pd.Series:
    index = pd.date_range("2024-01-01", periods=8, freq="D", tz="UTC")
    return pd.Series(
        [10_000.0, 10_120.0, 10_080.0, 10_135.0, 10_095.0, 10_150.0, 10_110.0, 10_165.0],
        index=index,
    )


def _fixture_funnel_counts(*, trade_count: int = 3) -> dict[str, int]:
    return {
        "market_epochs_total": 100,
        "directional_candidate_count": 80,
        "directional_confirmed_count": 60,
        "survival_pass_count": 50,
        "suitability_pass_count": 40,
        "double_play_entry_eligible_count": 30,
        "entry_preconditions_pass_count": 20,
        "risk_sizing_admissible_count": 10,
        "portfolio_admissible_count": 8,
        "trades_opened_count": trade_count,
    }


def _compute_stats(trades: list[dict], *, zero_cost: bool = False) -> dict:
    equity = _fixture_equity() if trades else pd.Series([10_000.0, 10_000.0])
    stats = compute_backtest_stats(trades, equity, periods_per_year=252)
    total_fees = 0.0 if zero_cost else 30.0
    return append_cost_accounting_fields(
        stats,
        initial_equity=10_000.0,
        effective_cost=_effective_cost(),
        total_fees=total_fees,
        total_notional=50_000.0,
    )


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


def _materialize(**kwargs):
    trades = kwargs.pop("trades", _fixture_trades())
    stats = kwargs.pop("stats", _compute_stats(trades))
    return materialize_snapshot_from_backtest_stats_v1(
        BacktestObservabilityInputsV1(
            stats=stats,
            initial_equity=10_000.0,
            trades=trades,
            effective_cost=kwargs.pop("effective_cost", _effective_cost()),
            total_notional=kwargs.pop("total_notional", 50_000.0),
            equity_curve=kwargs.pop("equity_curve", _fixture_equity()),
            funnel_counts=kwargs.pop("funnel_counts", None),
            **kwargs,
        ),
        run_identity={"run_id": "fixture-derived-metrics-v0"},
        source_refs=["fixture_derived_metrics_v0"],
        **kwargs,
    )


@pytest.fixture(name="registry")
def fixture_registry():
    return get_canonical_metric_registry_v1()


@pytest.fixture(name="materialized")
def fixture_materialized():
    snapshot, summary = _materialize()
    return snapshot, summary


class TestEconomicAndCostDerived:
    def test_gross_profit_plus_gross_loss_reconciles(self) -> None:
        trades = _fixture_trades()
        aggregates = derive_trade_aggregates_v1(trades)
        gross_profit = aggregates["gross_profit"].value
        gross_loss = aggregates["gross_loss"].value
        trade_gross_pnl = sum(float(t["gross_pnl"]) for t in trades)
        assert gross_profit + gross_loss == pytest.approx(trade_gross_pnl)

    def test_gross_minus_costs_reconciles_to_net(self, materialized) -> None:
        snapshot, _ = materialized
        gross_pnl = snapshot.economic["gross_pnl"].value
        net_pnl = snapshot.economic["net_pnl"].value
        total_cost = snapshot.costs["total_cost"].value
        assert gross_pnl - total_cost == pytest.approx(net_pnl, abs=1e-6)

    def test_trade_ledger_sums_reconcile_to_snapshot(self) -> None:
        trades = _align_trades_to_snapshot(
            _fixture_trades(), stats=_compute_stats(_fixture_trades())
        )
        stats = _compute_stats(trades)
        bundle, _ = materialize_observability_bundle_v1(
            BacktestObservabilityInputsV1(
                stats=stats,
                initial_equity=10_000.0,
                trades=trades,
                effective_cost=_effective_cost(),
                total_notional=50_000.0,
                equity_curve=_fixture_equity(),
                funnel_counts=_fixture_funnel_counts(),
                instrument_id="BTC-USDT",
                run_id="ledger-reconcile-v0",
            ),
            run_identity={"run_id": "ledger-reconcile-v0"},
            source_refs=["fixture_derived_metrics_v0"],
        )
        reconciliation = bundle.reconciliation_payload
        assert reconciliation["trade_count_reconciliation_pass"] is True
        assert reconciliation["net_pnl_reconciliation_pass"] is True

    def test_zero_denominator_fails_closed_or_uses_explicit_semantics(self) -> None:
        trades = [{"size": 1.0, "pnl": 10.0, "gross_pnl": 10.0}]
        bundle = derive_all_metrics_v1(
            trades=trades,
            stats=_compute_stats(trades, zero_cost=True),
            gross_profit=10.0,
            gross_pnl=10.0,
            net_pnl=10.0,
            total_cost=0.0,
            effective_cost=_effective_cost(),
        )
        assert bundle.cost_ratios["cost_share_of_gross_profit"].status is (
            MetricMaterializationStatus.RECONSTRUCTED
        )
        assert bundle.trade_aggregates["profit_factor_gross"].value == 0.0


class TestStrategyQualityFormulas:
    def test_profit_factor_gross_formula_contract(self) -> None:
        trades = _fixture_trades()
        aggregates = derive_trade_aggregates_v1(trades)
        gross_wins = sum(p for p in (float(t["gross_pnl"]) for t in trades) if p > 0)
        gross_losses = abs(sum(p for p in (float(t["gross_pnl"]) for t in trades) if p < 0))
        assert aggregates["profit_factor_gross"].value == pytest.approx(gross_wins / gross_losses)

    def test_profit_factor_net_formula_contract(self, materialized) -> None:
        snapshot, _ = materialized
        pf = snapshot.economic["profit_factor_net"]
        assert pf.status is MetricMaterializationStatus.COMPUTED
        assert pf.value > 0.0

    def test_expectancy_gross_formula_contract(self) -> None:
        trades = _fixture_trades()
        aggregates = derive_trade_aggregates_v1(trades)
        expected = sum(float(t["gross_pnl"]) for t in trades) / len(trades)
        assert aggregates["expectancy_gross"].value == pytest.approx(expected)

    def test_expectancy_net_formula_contract(self, materialized) -> None:
        snapshot, _ = materialized
        metric = snapshot.economic["expectancy_net"]
        assert metric.status is MetricMaterializationStatus.COMPUTED

    def test_payoff_ratio_formula_contract(self) -> None:
        trades = _fixture_trades()
        aggregates = derive_trade_aggregates_v1(trades)
        winners = [float(t["pnl"]) for t in trades if float(t["pnl"]) > 0]
        losers = [float(t["pnl"]) for t in trades if float(t["pnl"]) < 0]
        expected = abs(sum(winners) / len(winners)) / abs(sum(losers) / len(losers))
        assert aggregates["payoff_ratio"].value == pytest.approx(expected)


class TestTradeAnalyticsDerived:
    def test_holding_time_is_exit_minus_entry(self) -> None:
        trades = _fixture_trades()
        bundle = derive_all_metrics_v1(
            trades=trades,
            stats=_compute_stats(trades),
            gross_profit=165.0,
            gross_pnl=165.0,
            net_pnl=135.0,
            total_cost=30.0,
        )
        assert bundle.trade_aggregates["holding_time_mean"].status in {
            MetricMaterializationStatus.COMPUTED,
            MetricMaterializationStatus.RECONSTRUCTED,
        }
        assert bundle.trade_aggregates["holding_time_mean"].value == pytest.approx(86400.0)

    def test_exit_reason_counts_match_trade_count(self) -> None:
        trades = _fixture_trades()
        bundle = derive_all_metrics_v1(
            trades=trades,
            stats=_compute_stats(trades),
            gross_profit=165.0,
            gross_pnl=165.0,
            net_pnl=135.0,
            total_cost=30.0,
        )
        validate_exit_reason_counts_v1(
            exit_reason_counts=bundle.exit_reason_counts,
            trade_count=len(trades),
        )
        assert sum(bundle.exit_reason_counts.values()) == len(trades)

    def test_pnl_by_side_reconciles_to_total(self) -> None:
        trades = _fixture_trades()
        bundle = derive_all_metrics_v1(
            trades=trades,
            stats=_compute_stats(trades),
            gross_profit=165.0,
            gross_pnl=165.0,
            net_pnl=135.0,
            total_cost=30.0,
        )
        validate_pnl_breakdown_reconciliation_v1(
            pnl_by_side=bundle.pnl_by_side,
            pnl_by_instrument=bundle.pnl_by_instrument,
            total_net_pnl=sum(float(t["pnl"]) for t in trades),
        )

    def test_pnl_by_instrument_reconciles_to_total(self) -> None:
        trades = _fixture_trades()
        bundle = derive_all_metrics_v1(
            trades=trades,
            stats=_compute_stats(trades),
            gross_profit=165.0,
            gross_pnl=165.0,
            net_pnl=135.0,
            total_cost=30.0,
        )
        assert sum(bundle.pnl_by_instrument.values()) == pytest.approx(135.0)

    def test_pnl_by_regime_reconciles_when_regime_available(self) -> None:
        trades = _fixture_trades(with_regime=True)
        bundle = derive_all_metrics_v1(
            trades=trades,
            stats=_compute_stats(trades),
            gross_profit=165.0,
            gross_pnl=165.0,
            net_pnl=135.0,
            total_cost=30.0,
        )
        assert sum(bundle.pnl_by_regime.values()) == pytest.approx(135.0)
        assert bundle.breakdown_metrics["regime_breakdown"].status is (
            MetricMaterializationStatus.RECONSTRUCTED
        )


class TestDecisionFunnelDerived:
    def test_funnel_conversion_rates_are_stage_consistent(self) -> None:
        funnel = materialize_decision_funnel_persistence_v0(
            funnel_counts=_fixture_funnel_counts(),
        )
        rates = derive_stage_conversion_rates_v1(funnel.stage_counts)
        for rate in rates.values():
            assert 0.0 <= rate <= 1.0


class TestDrawdownDerived:
    def test_drawdown_duration_reconstructs_deterministically(self) -> None:
        equity = _fixture_equity()
        first = derive_drawdown_episode_metrics_v1(equity)
        second = derive_drawdown_episode_metrics_v1(equity)
        assert first["drawdown_duration"].value == second["drawdown_duration"].value
        assert first["recovery_duration"].value == second["recovery_duration"].value


class TestSnapshotSemantics:
    def test_zero_and_null_semantics_distinct(self) -> None:
        empty = materialize_empty_snapshot_v1()
        assert empty.economic["gross_profit"].value is None

    def test_not_applicable_has_reason(self, materialized) -> None:
        snapshot, _ = materialized
        break_even_cost = snapshot.economic.get("break_even_cost")
        if break_even_cost is not None:
            assert break_even_cost.status is MetricMaterializationStatus.NOT_APPLICABLE
            assert break_even_cost.reason_codes

    def test_insufficient_data_has_reason(self) -> None:
        bundle = derive_trade_aggregates_v1([])
        metric = bundle["gross_profit"]
        assert metric.status is MetricMaterializationStatus.INSUFFICIENT_DATA
        assert metric.reason_codes


class TestRegistryBinding:
    def test_registry_ids_remain_unique(self, registry) -> None:
        ids = [entry.metric_id for entry in registry.entries]
        assert len(ids) == len(set(ids))

    def test_all_materialized_metrics_exist_in_registry(self, registry, materialized) -> None:
        snapshot, _ = materialized
        registry_ids = {entry.metric_id for entry in registry.entries}
        for domain in (
            "economic",
            "costs",
            "strategy_quality",
            "risk",
            "trade_analytics",
            "decision_funnel",
            "portfolio",
        ):
            bucket = getattr(snapshot, domain)
            assert set(bucket) <= registry_ids

    def test_no_duplicate_formula_owner(self, registry) -> None:
        source_owner_map: dict[str, set[str]] = {}
        for entry in registry.entries:
            source_owner_map.setdefault(entry.source_field_or_formula, set()).add(
                entry.canonical_owner
            )
        conflicts = {
            source: owners for source, owners in source_owner_map.items() if len(owners) > 1
        }
        assert not conflicts


class TestDeterminismAndBoundaries:
    def test_stable_serialization(self, materialized) -> None:
        snapshot, _ = materialized
        first = serialize_canonical_json(snapshot.to_dict())
        second = serialize_canonical_json(snapshot.to_dict())
        assert first == second

    def test_same_inputs_same_snapshot_digest(self) -> None:
        first, _ = _materialize()
        second, _ = _materialize()
        first_payload = first.to_dict()
        second_payload = second.to_dict()
        first_payload["manifest_digest"] = ""
        second_payload["manifest_digest"] = ""
        assert compute_snapshot_digest(first_payload) == compute_snapshot_digest(second_payload)

    def test_second_materialization_diff_empty(self) -> None:
        first, _ = _materialize()
        second, _ = _materialize()
        first_payload = first.to_dict()
        second_payload = second.to_dict()
        first_payload["manifest_digest"] = ""
        second_payload["manifest_digest"] = ""
        assert serialize_canonical_json(first_payload) == serialize_canonical_json(second_payload)

    def test_missing_source_fails_closed(self) -> None:
        empty = materialize_empty_snapshot_v1()
        assert empty.trade_analytics["holding_time_mean"].status in {
            MetricMaterializationStatus.NOT_COMPUTED,
            MetricMaterializationStatus.SOURCE_MISSING,
            MetricMaterializationStatus.INSUFFICIENT_DATA,
        }

    def test_no_runtime_import_boundary_violation(self) -> None:
        assert scan_file_import_boundary(DERIVED_MODULE, repo_root=REPO_ROOT) == []

    def test_no_order_adapter_import_boundary_violation(self) -> None:
        hits = scan_file_import_boundary(DERIVED_MODULE, repo_root=REPO_ROOT)
        assert all("order" not in hit.module.lower() for hit in hits)

    def test_no_scheduler_import_boundary_violation(self) -> None:
        hits = scan_file_import_boundary(DERIVED_MODULE, repo_root=REPO_ROOT)
        assert all("scheduler" not in hit.module.lower() for hit in hits)

    def test_no_direct_report_formula(self) -> None:
        assert DERIVED_METRICS_OWNER.startswith("backtest.")
        assert MATERIALIZATION_OWNER.startswith("backtest.")


def test_canonical_derived_metrics_owner_alias() -> None:
    assert CANONICAL_DERIVED_METRICS_OWNER == DERIVED_METRICS_OWNER


def test_scope_aliases_map_to_registry_ids(registry) -> None:
    registry_ids = {entry.metric_id for entry in registry.entries}
    for alias, metric_id in SCOPE_METRIC_ALIASES.items():
        assert metric_id in registry_ids, f"alias {alias} -> {metric_id}"


def test_registry_metric_count_unchanged(registry) -> None:
    assert len(registry.entries) == DISCOVERY_METRIC_COUNT


def test_derived_gross_profit_bound_in_snapshot(materialized) -> None:
    snapshot, _ = materialized
    metric = snapshot.economic["gross_profit"]
    assert metric.status in {
        MetricMaterializationStatus.COMPUTED,
        MetricMaterializationStatus.RECONSTRUCTED,
    }
    assert metric.value is not None


def test_break_even_edge_bound_without_capital(materialized) -> None:
    snapshot, _ = materialized
    edge = snapshot.trade_analytics["required_gross_edge_for_break_even"]
    assert edge.status in {
        MetricMaterializationStatus.COMPUTED,
        MetricMaterializationStatus.RECONSTRUCTED,
    }
    assert edge.value is not None


def test_break_even_capital_not_derivable(materialized) -> None:
    snapshot, _ = materialized
    capital = snapshot.economic.get("break_even_cost")
    if capital is not None:
        assert capital.status is MetricMaterializationStatus.NOT_APPLICABLE
        assert "PROPORTIONAL" in capital.reason_codes[0]


def test_funnel_conversion_bound_with_funnel_counts() -> None:
    trades = _align_trades_to_snapshot(_fixture_trades(), stats=_compute_stats(_fixture_trades()))
    stats = _compute_stats(trades)
    bundle, _ = materialize_observability_bundle_v1(
        BacktestObservabilityInputsV1(
            stats=stats,
            initial_equity=10_000.0,
            trades=trades,
            effective_cost=_effective_cost(),
            total_notional=50_000.0,
            equity_curve=_fixture_equity(),
            funnel_counts=_fixture_funnel_counts(),
        ),
        run_identity={"run_id": "funnel-conversion-v0"},
    )
    payload = json.loads(json.dumps(bundle.decision_funnel_payload))
    assert payload["stage_counts"]["trades_opened_count"] == 3
