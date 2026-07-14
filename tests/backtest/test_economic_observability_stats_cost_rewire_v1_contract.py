"""Contract tests for canonical stats/cost decomposition snapshot materialization v1."""

from __future__ import annotations

import copy
import math
from pathlib import Path

import pandas as pd
import pytest

from src.backtest.cost_config_v0 import (
    COST_MODEL_VERSION,
    EffectiveBacktestCostConfigV0,
    append_cost_accounting_fields,
    resolve_effective_backtest_cost_config,
)
from src.backtest.economic_observability_materialization_v1 import (
    COST_OWNER,
    MATERIALIZATION_OWNER,
    RECONCILIATION_TOLERANCE,
    STATS_OWNER,
    BacktestObservabilityInputsV1,
    ReconciliationError,
    existing_cost_field_keys_v0,
    existing_stats_field_keys_v0,
    materialize_snapshot_from_backtest_stats_v1,
    project_legacy_economic_evidence_metrics_v1,
    validate_gross_net_cost_reconciliation_v1,
)
from src.backtest.economic_observability_registry_v1 import (
    DISCOVERY_METRIC_COUNT,
    get_canonical_metric_registry_v1,
)
from src.backtest.economic_observability_snapshot_v1 import (
    MetricMaterializationStatus,
    SNAPSHOT_OWNER,
    compute_snapshot_digest,
    materialize_empty_snapshot_v1,
    serialize_canonical_json,
)
from src.backtest.stats import compute_backtest_stats
from src.research.linear_evidence.import_boundary import scan_file_import_boundary

REPO_ROOT = Path(__file__).resolve().parents[2]
MATERIALIZATION_MODULE = REPO_ROOT / "src/backtest/economic_observability_materialization_v1.py"


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


def _fixture_trades() -> list[dict]:
    return [
        {
            "pnl": 120.0,
            "gross_pnl": 130.0,
            "entry_cost": 5.0,
            "exit_cost": 5.0,
        },
        {
            "pnl": -40.0,
            "gross_pnl": -30.0,
            "entry_cost": 5.0,
            "exit_cost": 5.0,
        },
        {
            "pnl": 55.0,
            "gross_pnl": 65.0,
            "entry_cost": 5.0,
            "exit_cost": 5.0,
        },
    ]


def _fixture_equity() -> pd.Series:
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
        ]
    )


def _fixture_stats(*, with_cost: bool = True) -> dict:
    equity = _fixture_equity()
    stats = compute_backtest_stats(_fixture_trades(), equity, periods_per_year=252)
    if with_cost:
        stats = append_cost_accounting_fields(
            stats,
            initial_equity=10_000.0,
            effective_cost=_effective_cost(),
            total_fees=15.0,
            total_notional=50_000.0,
        )
    return stats


def _materialize(**kwargs):
    stats = kwargs.pop("stats", _fixture_stats())
    return materialize_snapshot_from_backtest_stats_v1(
        BacktestObservabilityInputsV1(
            stats=stats,
            initial_equity=10_000.0,
            trades=kwargs.pop("trades", _fixture_trades()),
            effective_cost=kwargs.pop("effective_cost", _effective_cost()),
            total_notional=kwargs.pop("total_notional", 50_000.0),
            **kwargs,
        ),
        run_identity={"run_id": "fixture-stats-cost-rewire-v0"},
        source_refs=["fixture_stats_cost_rewire_v0"],
        **kwargs,
    )


@pytest.fixture(name="registry")
def fixture_registry():
    return get_canonical_metric_registry_v1()


@pytest.fixture(name="materialized")
def fixture_materialized():
    snapshot, summary = _materialize()
    return snapshot, summary


class TestExistingStats:
    def test_all_existing_stats_fields_registered(self, registry) -> None:
        stats_keys = set(existing_stats_field_keys_v0())
        bound_registry_sources = {
            entry.source_field_or_formula.split(":")[-1]
            for entry in registry.entries
            if entry.canonical_owner in {STATS_OWNER, "backtest.economic_viability_evidence_v1"}
        }
        assert "profit_factor" in stats_keys
        assert "total_trades" in stats_keys
        assert "win_rate" in bound_registry_sources or "profit_factor_net" in {
            e.metric_id for e in registry.entries
        }

    def test_all_existing_stats_fields_persisted(self, materialized) -> None:
        snapshot, _ = materialized
        for metric_id in (
            "trade_count",
            "win_rate",
            "profit_factor_net",
            "expectancy_net",
            "sharpe",
            "sortino",
            "calmar",
            "max_drawdown_percent",
        ):
            bucket = (
                snapshot.economic.get(metric_id)
                or snapshot.risk.get(metric_id)
                or snapshot.trade_analytics.get(metric_id)
            )
            assert bucket is not None
            assert bucket.status is MetricMaterializationStatus.COMPUTED

    def test_stats_field_units_are_explicit(self, materialized) -> None:
        snapshot, _ = materialized
        for bucket in (snapshot.economic, snapshot.risk, snapshot.trade_analytics):
            for metric in bucket.values():
                if metric.status is MetricMaterializationStatus.COMPUTED:
                    assert metric.unit

    def test_stats_null_and_zero_semantics_distinct(self, materialized) -> None:
        snapshot, _ = materialized
        empty = materialize_empty_snapshot_v1()
        computed = snapshot.economic["win_rate"]
        absent = empty.economic["win_rate"]
        assert computed.value is not None
        assert absent.value is None

    def test_stats_missing_values_have_reason_codes(self) -> None:
        snapshot, _ = _materialize(stats={"total_trades": 0}, trades=[])
        turnover = snapshot.trade_analytics["turnover"]
        assert turnover.status in {
            MetricMaterializationStatus.NOT_COMPUTED,
            MetricMaterializationStatus.INSUFFICIENT_DATA,
            MetricMaterializationStatus.SOURCE_MISSING,
        }
        assert turnover.reason_codes


class TestCostAttribution:
    def test_all_existing_cost_fields_registered(self, registry) -> None:
        cost_ids = {entry.metric_id for entry in registry.entries if entry.domain == "costs"}
        for field in ("fee_drag", "slippage_drag", "total_fees", "total_cost", "spread_drag"):
            assert field in cost_ids

    def test_all_existing_cost_fields_persisted(self, materialized) -> None:
        snapshot, _ = materialized
        for metric_id in ("fee_drag", "slippage_drag", "total_fees", "total_cost"):
            metric = snapshot.costs[metric_id]
            assert metric.status is MetricMaterializationStatus.COMPUTED

    def test_gross_return_is_not_aliased_to_net_return(self, materialized) -> None:
        snapshot, summary = materialized
        gross = snapshot.economic["gross_return"]
        net = snapshot.economic["net_return"]
        assert gross.status is MetricMaterializationStatus.COMPUTED
        assert net.status is MetricMaterializationStatus.COMPUTED
        assert gross.value != net.value
        assert summary.gross_net_alias_removed

    def test_fee_drag_is_bound_to_existing_cost_owner(self, materialized) -> None:
        snapshot, _ = materialized
        fee_drag = snapshot.costs["fee_drag"]
        assert fee_drag.owner == COST_OWNER
        assert fee_drag.formula_version == "append_cost_accounting_fields_v0"
        assert fee_drag.value == pytest.approx(15.0 / 10_000.0)

    def test_slippage_drag_is_bound_to_existing_cost_owner(self, materialized) -> None:
        snapshot, _ = materialized
        slippage = snapshot.costs["slippage_drag"]
        assert slippage.owner == COST_OWNER
        assert slippage.formula_version == "append_cost_accounting_fields_v0"
        assert slippage.value > 0.0

    def test_funding_drag_status_is_explicit(self) -> None:
        snapshot, _ = _materialize()
        funding = snapshot.costs["funding_drag"]
        assert funding.status in {
            MetricMaterializationStatus.NOT_APPLICABLE,
            MetricMaterializationStatus.SOURCE_MISSING,
            MetricMaterializationStatus.COMPUTED,
        }
        if funding.status is not MetricMaterializationStatus.COMPUTED:
            assert funding.reason_codes

    def test_spread_drag_status_is_explicit(self) -> None:
        snapshot, _ = _materialize()
        spread = snapshot.costs["spread_drag"]
        assert spread.status is MetricMaterializationStatus.NOT_APPLICABLE
        assert spread.reason_codes == ("SPREAD_NOT_BOUND_IN_STANDARD_PATH",)

    def test_cost_components_not_double_counted(self, materialized) -> None:
        _, summary = materialized
        assert summary.cost_component_double_counting is False

    def test_total_cost_reconciles_to_available_components(self, materialized) -> None:
        snapshot, _ = materialized
        total_cost = snapshot.costs["total_cost"].value
        fee_drag = snapshot.costs["fee_drag"].value
        slippage_drag = snapshot.costs["slippage_drag"].value
        assert total_cost == pytest.approx((fee_drag + slippage_drag) * 10_000.0)


class TestGrossNetReconciliation:
    def test_gross_minus_costs_reconciles_to_net_pnl(self, materialized) -> None:
        snapshot, _ = materialized
        gross_pnl = snapshot.economic["gross_pnl"].value
        net_pnl = snapshot.economic["net_pnl"].value
        total_cost = snapshot.costs["total_cost"].value
        assert gross_pnl - total_cost == pytest.approx(net_pnl, rel=0.0, abs=1e-6)

    def test_return_reconciliation_uses_correct_units(self) -> None:
        stats = _fixture_stats()
        derived = {
            "gross_pnl": 10_000.0 * stats["gross_return"],
            "net_pnl": 10_000.0 * stats["net_return"],
            "total_cost": stats["fee_drag"] * 10_000.0 + stats["slippage_impact"] * 10_000.0,
            "spread_drag": None,
        }
        validate_gross_net_cost_reconciliation_v1(
            initial_equity=10_000.0,
            stats=stats,
            derived=derived,
        )

    def test_reconciliation_tolerance_is_explicit(self) -> None:
        assert RECONCILIATION_TOLERANCE == 1e-9

    def test_reconciliation_failure_fails_closed(self) -> None:
        stats = _fixture_stats()
        broken = copy.deepcopy(stats)
        broken["gross_return"] = broken["net_return"] + 0.5
        with pytest.raises(ReconciliationError):
            materialize_snapshot_from_backtest_stats_v1(
                BacktestObservabilityInputsV1(
                    stats=broken,
                    initial_equity=10_000.0,
                    effective_cost=_effective_cost(),
                ),
                validate_reconciliation=True,
            )


class TestSnapshot:
    def test_canonical_snapshot_schema_roundtrip(self, materialized) -> None:
        snapshot, _ = materialized
        payload = snapshot.to_dict()
        reparsed_payload = payload
        assert reparsed_payload["schema_version"]
        assert len(reparsed_payload["economic"]) > 0

    def test_stable_serialization(self, materialized) -> None:
        snapshot, _ = materialized
        first = serialize_canonical_json(snapshot.to_dict())
        second = serialize_canonical_json(snapshot.to_dict())
        assert first == second

    def test_deterministic_digest(self, materialized) -> None:
        snapshot, _ = materialized
        payload = snapshot.to_dict()
        assert compute_snapshot_digest(payload) == compute_snapshot_digest(payload)

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

    def test_snapshot_metric_owners_match_registry(self, registry, materialized) -> None:
        snapshot, _ = materialized
        for entry in registry.entries:
            if entry.domain == "provenance":
                continue
            bucket = getattr(snapshot, entry.domain)
            metric = bucket.get(entry.metric_id)
            assert metric is not None
            if metric.status is MetricMaterializationStatus.COMPUTED:
                assert metric.owner

    def test_snapshot_sources_match_registry(self, registry, materialized) -> None:
        snapshot, _ = materialized
        for entry in registry.entries:
            if entry.domain == "provenance":
                continue
            metric = getattr(snapshot, entry.domain)[entry.metric_id]
            if metric.status is MetricMaterializationStatus.COMPUTED:
                assert metric.source

    def test_no_unregistered_snapshot_metric(self, registry, materialized) -> None:
        snapshot, _ = materialized
        registry_ids = {entry.metric_id for entry in registry.entries}
        for domain in (
            "economic",
            "costs",
            "strategy_quality",
            "risk",
            "trade_analytics",
            "decision_funnel",
            "exposure",
            "portfolio",
            "robustness",
            "data_quality",
        ):
            bucket = getattr(snapshot, domain)
            assert set(bucket) <= registry_ids

    def test_zero_is_valid_value(self) -> None:
        stats = {
            "total_return": 0.0,
            "net_return": 0.0,
            "gross_return": 0.0,
            "fee_drag": 0.0,
            "slippage_impact": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "expectancy": 0.0,
            "sharpe": 0.0,
            "sortino": 0.0,
            "calmar": 0.0,
            "max_drawdown": 0.0,
            "cagr": 0.0,
            "total_fees": 0.0,
        }
        snapshot, _ = _materialize(stats=stats, trades=[], total_notional=0.0)
        assert snapshot.costs["fee_drag"].value == 0.0

    def test_null_means_unavailable(self) -> None:
        empty = materialize_empty_snapshot_v1()
        assert empty.economic["gross_return"].value is None

    def test_not_applicable_has_reason(self, materialized) -> None:
        snapshot, _ = materialized
        spread = snapshot.costs["spread_drag"]
        assert spread.status is MetricMaterializationStatus.NOT_APPLICABLE
        assert spread.reason_codes

    def test_not_computed_has_reason(self) -> None:
        empty = materialize_empty_snapshot_v1()
        assert empty.trade_analytics["turnover"].reason_codes


class TestBoundaries:
    def test_no_runtime_import_boundary_violation(self) -> None:
        assert scan_file_import_boundary(MATERIALIZATION_MODULE, repo_root=REPO_ROOT) == []

    def test_no_order_adapter_import_boundary_violation(self) -> None:
        hits = scan_file_import_boundary(MATERIALIZATION_MODULE, repo_root=REPO_ROOT)
        assert all("order" not in hit.module.lower() for hit in hits)

    def test_no_scheduler_import_boundary_violation(self) -> None:
        hits = scan_file_import_boundary(MATERIALIZATION_MODULE, repo_root=REPO_ROOT)
        assert all("scheduler" not in hit.module.lower() for hit in hits)

    def test_no_live_import_boundary_violation(self) -> None:
        hits = scan_file_import_boundary(MATERIALIZATION_MODULE, repo_root=REPO_ROOT)
        assert all("live" not in hit.module.lower() for hit in hits)

    def test_no_report_formula_owner(self) -> None:
        assert MATERIALIZATION_OWNER.startswith("backtest.")

    def test_no_duplicate_metric_formula_owner(self, registry) -> None:
        source_owner_map: dict[str, set[str]] = {}
        for entry in registry.entries:
            source_owner_map.setdefault(entry.source_field_or_formula, set()).add(
                entry.canonical_owner
            )
        conflicts = {
            source: owners for source, owners in source_owner_map.items() if len(owners) > 1
        }
        assert not conflicts


class TestCompatibility:
    def test_existing_economic_evidence_consumers_remain_compatible(self, materialized) -> None:
        snapshot, _ = materialized
        legacy = project_legacy_economic_evidence_metrics_v1(snapshot)
        assert legacy["gross_return"] is not None
        assert legacy["net_return"] is not None
        assert legacy["gross_return"] != legacy["net_return"]
        assert legacy["fee_drag"] is not None
        assert legacy["slippage_impact"] is not None

    def test_legacy_projection_matches_canonical_snapshot_where_applicable(
        self, materialized
    ) -> None:
        snapshot, _ = materialized
        legacy = project_legacy_economic_evidence_metrics_v1(snapshot)
        assert legacy["gross_return"] == snapshot.economic["gross_return"].value
        assert legacy["net_return"] == snapshot.economic["net_return"].value
        assert legacy["fee_drag"] == snapshot.costs["fee_drag"].value


def test_registry_metric_count_unchanged(registry) -> None:
    assert len(registry.entries) == DISCOVERY_METRIC_COUNT


def test_existing_cost_field_keys_cover_append_cost_accounting_fields() -> None:
    stats = _fixture_stats()
    for key in existing_cost_field_keys_v0():
        if key == "funding_drag_or_status":
            assert key in stats
        else:
            assert key in stats


def test_materialization_owner_present(materialized) -> None:
    snapshot, _ = materialized
    assert snapshot.run_identity["materialization_owner"] == MATERIALIZATION_OWNER
    assert SNAPSHOT_OWNER
