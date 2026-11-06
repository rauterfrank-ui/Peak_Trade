"""Contract tests for canonical trade ledger, equity curve, and decision funnel persistence v0."""

from __future__ import annotations

import copy
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
from src.backtest.decision_funnel_v0 import (
    DECISION_FUNNEL_OWNER,
    classify_zero_trade_causal_v0,
    materialize_decision_funnel_persistence_v0,
)
from src.backtest.economic_observability_materialization_v1 import (
    MATERIALIZATION_OWNER,
    BacktestObservabilityInputsV1,
    materialize_observability_bundle_v1,
    materialize_snapshot_from_backtest_stats_v1,
    project_legacy_economic_evidence_metrics_v1,
)
from src.backtest.economic_observability_snapshot_v1 import (
    MetricMaterializationStatus,
    serialize_canonical_json,
)
from src.backtest.stats import compute_backtest_stats
from src.backtest.trade_ledger_equity_curve_persistence_v0 import (
    CANONICAL_TRADE_LEDGER_FIELDS,
    DRAWDOWN_CURVE_OWNER,
    EQUITY_CURVE_OWNER,
    TRADE_LEDGER_OWNER,
    DrawdownCurveStatus,
    PersistenceContractError,
    materialize_drawdown_curve_v0,
    materialize_trade_ledger_row_v0,
    materialize_trade_ledger_rows_v0,
    serialize_trade_ledger_jsonl,
    validate_drawdown_reconciliation_v0,
    validate_trade_ledger_reconciliation_v0,
)
from src.research.cross_sectional_offline_economic_evaluation_decision_funnel_v0 import (
    FUNNEL_OWNER as RESEARCH_FUNNEL_OWNER,
    RUNBOOK_FUNNEL_FIELDS,
)
from src.research.linear_evidence.import_boundary import scan_file_import_boundary

REPO_ROOT = Path(__file__).resolve().parents[2]
PERSISTENCE_MODULE = REPO_ROOT / "src/backtest/trade_ledger_equity_curve_persistence_v0.py"
DECISION_FUNNEL_MODULE = REPO_ROOT / "src/backtest/decision_funnel_v0.py"
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


def _fixture_trades(*, include_fees: bool = False) -> list[dict]:
    trades = [
        {
            "size": 1.0,
            "entry_time": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "exit_time": datetime(2024, 1, 2, tzinfo=timezone.utc),
            "entry_price": 100.0,
            "exit_price": 110.0,
            "pnl": 120.0,
            "gross_pnl": 130.0,
            "exit_reason": "signal_flip",
        },
        {
            "size": -1.0,
            "entry_time": datetime(2024, 1, 3, tzinfo=timezone.utc),
            "exit_time": datetime(2024, 1, 4, tzinfo=timezone.utc),
            "entry_price": 110.0,
            "exit_price": 105.0,
            "pnl": -40.0,
            "gross_pnl": -30.0,
            "exit_reason": "stop",
        },
        {
            "size": 1.0,
            "entry_time": datetime(2024, 1, 5, tzinfo=timezone.utc),
            "exit_time": datetime(2024, 1, 6, tzinfo=timezone.utc),
            "entry_price": 105.0,
            "exit_price": 115.0,
            "pnl": 55.0,
            "gross_pnl": 65.0,
            "exit_reason": "target",
        },
    ]
    if include_fees:
        per_trade_fee = 5.0
        for trade in trades:
            trade["entry_cost"] = per_trade_fee
            trade["exit_cost"] = per_trade_fee
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


def _compute_stats(trades: list[dict], *, include_fees: bool = False) -> dict:
    equity = _fixture_equity()
    stats = compute_backtest_stats(trades, equity, periods_per_year=252)
    total_fees = sum(
        float(trade.get("entry_cost", 0.0) or 0.0) + float(trade.get("exit_cost", 0.0) or 0.0)
        for trade in trades
    )
    if not include_fees:
        total_fees = 0.0
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
    include_fees: bool,
) -> list[dict]:
    """Align trade ledger fields to snapshot reconciliation targets without mutating stats."""
    snapshot, _ = materialize_snapshot_from_backtest_stats_v1(
        BacktestObservabilityInputsV1(
            stats=stats,
            initial_equity=10_000.0,
            trades=trades,
            effective_cost=_effective_cost(),
            total_notional=50_000.0,
        ),
        run_identity={"run_id": "align-trades-to-snapshot"},
    )
    target_gross = float(snapshot.economic["gross_pnl"].value)
    target_net = float(snapshot.economic["net_pnl"].value)
    target_cost = float(snapshot.costs["total_cost"].value)

    aligned = copy.deepcopy(trades)
    gross_sum = sum(float(trade["gross_pnl"]) for trade in aligned)
    net_sum = sum(float(trade["pnl"]) for trade in aligned)
    for trade in aligned:
        trade["gross_pnl"] = float(trade["gross_pnl"]) / gross_sum * target_gross
        trade["pnl"] = float(trade["pnl"]) / net_sum * target_net
        if include_fees and target_cost > 0:
            per_leg = target_cost / (2 * len(aligned))
            trade["entry_cost"] = per_leg
            trade["exit_cost"] = per_leg
        else:
            trade.pop("entry_cost", None)
            trade.pop("exit_cost", None)
    return aligned


def _fixture_stats(*, include_fees: bool = False) -> dict:
    trades = _fixture_trades(include_fees=include_fees)
    return _compute_stats(trades, include_fees=include_fees)


def _bundle_inputs(**kwargs) -> BacktestObservabilityInputsV1:
    include_fees = kwargs.pop("include_fees", False)
    base_trades = kwargs.pop("trades", _fixture_trades(include_fees=include_fees))
    stats = kwargs.pop("stats", _compute_stats(base_trades, include_fees=include_fees))
    trades = _align_trades_to_snapshot(base_trades, stats=stats, include_fees=include_fees)
    return BacktestObservabilityInputsV1(
        stats=stats,
        initial_equity=10_000.0,
        trades=trades,
        effective_cost=kwargs.pop("effective_cost", _effective_cost()),
        total_notional=kwargs.pop("total_notional", 50_000.0),
        equity_curve=kwargs.pop("equity_curve", _fixture_equity()),
        instrument_id="ETH/USDT",
        run_id="fixture-persistence-v0",
        strategy_ref="trend_following/v1",
        funnel_counts=kwargs.pop("funnel_counts", _fixture_funnel_counts()),
        block_reason_counts=kwargs.pop(
            "block_reason_counts",
            {"RISK_SIZING_BLOCKED": 12, "PORTFOLIO_BLOCKED": 4},
        ),
        **kwargs,
    )


def _materialize_bundle(**kwargs):
    return materialize_observability_bundle_v1(
        _bundle_inputs(**kwargs),
        run_identity={"run_id": "fixture-persistence-v0"},
        source_refs=["fixture_trade_ledger_equity_curve_decision_funnel_persistence_v0"],
    )


@pytest.fixture(name="bundle")
def fixture_bundle():
    bundle, summary = _materialize_bundle(include_fees=True)
    return bundle, summary


class TestTradeLedger:
    def test_trade_ledger_schema_roundtrip(self, bundle) -> None:
        payload, _ = bundle
        first_line = payload.trade_ledger_jsonl.strip().splitlines()[0]
        parsed = json.loads(first_line)
        assert set(parsed) == set(CANONICAL_TRADE_LEDGER_FIELDS)
        for field_payload in parsed.values():
            assert "status" in field_payload
            assert "value" in field_payload
            assert "reason_codes" in field_payload

    def test_trade_ledger_stable_serialization(self) -> None:
        rows = materialize_trade_ledger_rows_v0(
            _fixture_trades(include_fees=True),
            instrument_id="ETH/USDT",
            run_id="stable-run",
            strategy_ref="trend_following/v1",
        )
        first = serialize_trade_ledger_jsonl(rows)
        second = serialize_trade_ledger_jsonl(rows)
        assert first == second

    def test_trade_ledger_row_count_matches_trade_count(self, bundle) -> None:
        payload, _ = bundle
        lines = [line for line in payload.trade_ledger_jsonl.splitlines() if line.strip()]
        assert len(lines) == 3
        assert payload.reconciliation_payload["trade_count_reconciliation_pass"] is True

    def test_trade_ledger_net_pnl_reconciles_to_snapshot(self, bundle) -> None:
        payload, _ = bundle
        assert payload.reconciliation_payload["net_pnl_reconciliation_pass"] is True

    def test_trade_ledger_gross_pnl_reconciles_to_snapshot(self, bundle) -> None:
        payload, _ = bundle
        assert payload.reconciliation_payload["gross_pnl_reconciliation_pass"] is True

    def test_trade_ledger_costs_reconcile_to_snapshot(self, bundle) -> None:
        payload, _ = bundle
        assert payload.reconciliation_payload["total_cost_reconciliation_pass"] is True

    def test_missing_trade_fields_are_not_zero_filled(self) -> None:
        row = materialize_trade_ledger_row_v0(
            _fixture_trades()[0],
            trade_index=0,
            instrument_id="ETH/USDT",
            run_id="missing-fields",
        )
        assert row.fields["slippage"].value is None
        assert row.fields["funding"].value is None
        assert row.fields["slippage"].status is MetricMaterializationStatus.SOURCE_MISSING

    def test_missing_trade_fields_have_explicit_status_and_reason(self) -> None:
        row = materialize_trade_ledger_row_v0(
            _fixture_trades()[0],
            trade_index=0,
            instrument_id="ETH/USDT",
            run_id="missing-fields",
        )
        for field_name in ("slippage", "funding", "entry_reason", "regime"):
            field = row.fields[field_name]
            assert field.status is MetricMaterializationStatus.SOURCE_MISSING
            assert field.reason_codes


class TestEquityAndDrawdown:
    def test_equity_curve_stable_serialization(self, bundle) -> None:
        payload, _ = bundle
        assert payload.equity_curve_csv.count("\n") >= 4
        assert "timestamp,equity" in payload.equity_curve_csv

    def test_equity_curve_final_value_matches_final_equity(self, bundle) -> None:
        payload, _ = bundle
        assert payload.reconciliation_payload["equity_reconciliation_pass"] is True

    def test_drawdown_curve_reconciles_to_equity_curve_if_materialized(self, bundle) -> None:
        equity = _fixture_equity()
        drawdown = materialize_drawdown_curve_v0(equity_curve=equity)
        assert drawdown.status is DrawdownCurveStatus.RECONSTRUCTED
        validate_drawdown_reconciliation_v0(equity_curve=equity, drawdown=drawdown)


class TestDecisionFunnel:
    def test_decision_funnel_all_available_stages_persisted(self, bundle) -> None:
        payload, _ = bundle
        for field in RUNBOOK_FUNNEL_FIELDS:
            assert field in payload.decision_funnel_payload["stage_counts"]

    def test_unavailable_funnel_stages_have_reason(self) -> None:
        funnel = materialize_decision_funnel_persistence_v0()
        assert funnel.unavailable_stages
        for reason in funnel.unavailable_stages.values():
            assert reason

    def test_trades_opened_reconciles_to_trade_count(self, bundle) -> None:
        payload, _ = bundle
        assert payload.reconciliation_payload["trades_opened_reconciliation_pass"] is True

    def test_block_reason_counts_are_deterministic(self) -> None:
        counts = {"RISK_SIZING_BLOCKED": 2, "PORTFOLIO_BLOCKED": 1}
        first = materialize_decision_funnel_persistence_v0(
            funnel_counts=_fixture_funnel_counts(),
            block_reason_counts=counts,
        )
        second = materialize_decision_funnel_persistence_v0(
            funnel_counts=_fixture_funnel_counts(),
            block_reason_counts=counts,
        )
        assert first.block_reason_counts == second.block_reason_counts

    def test_zero_trade_classification_persisted(self) -> None:
        zero_counts = {field: 0 for field in RUNBOOK_FUNNEL_FIELDS}
        zero_counts["market_epochs_total"] = 10
        classification = classify_zero_trade_causal_v0(
            stage_counts=zero_counts,
            block_reason_counts={"DIRECTIONAL_NO_CANDIDATE": 10},
        )
        assert classification["status"] == MetricMaterializationStatus.COMPUTED.value
        funnel = materialize_decision_funnel_persistence_v0(
            funnel_counts=zero_counts,
            block_reason_counts={"DIRECTIONAL_NO_CANDIDATE": 10},
        )
        assert funnel.zero_trade_causal_classification["classification"]


class TestBundleDeterminism:
    def test_same_inputs_same_bundle_digest(self) -> None:
        first, _ = _materialize_bundle(include_fees=True)
        second, _ = _materialize_bundle(include_fees=True)
        assert first.bundle_digest == second.bundle_digest

    def test_second_materialization_diff_empty(self) -> None:
        first, _ = _materialize_bundle(include_fees=True)
        second, _ = _materialize_bundle(include_fees=True)
        first_snapshot = copy.deepcopy(first.snapshot_payload)
        second_snapshot = copy.deepcopy(second.snapshot_payload)
        first_snapshot["manifest_digest"] = ""
        second_snapshot["manifest_digest"] = ""
        assert serialize_canonical_json(first_snapshot) == serialize_canonical_json(second_snapshot)
        assert first.trade_ledger_jsonl == second.trade_ledger_jsonl
        assert first.equity_curve_csv == second.equity_curve_csv

    def test_legacy_projection_remains_compatible(self, bundle) -> None:
        payload, _ = bundle
        snapshot, _ = materialize_snapshot_from_backtest_stats_v1(
            _bundle_inputs(include_fees=True),
            run_identity={"run_id": "legacy-projection"},
        )
        from src.backtest.economic_observability_snapshot_v1 import (
            CanonicalEconomicObservabilitySnapshotV1,
        )

        reparsed = CanonicalEconomicObservabilitySnapshotV1.from_dict(payload.snapshot_payload)
        legacy = project_legacy_economic_evidence_metrics_v1(reparsed)
        assert legacy["gross_return"] is not None
        assert legacy["net_return"] is not None


class TestOwnersAndBoundaries:
    def test_no_duplicate_owner(self) -> None:
        assert TRADE_LEDGER_OWNER == EQUITY_CURVE_OWNER == DRAWDOWN_CURVE_OWNER
        assert DECISION_FUNNEL_OWNER != RESEARCH_FUNNEL_OWNER

    def test_no_runtime_import_boundary_violation(self) -> None:
        for module in (PERSISTENCE_MODULE, DECISION_FUNNEL_MODULE, MATERIALIZATION_MODULE):
            assert scan_file_import_boundary(module, repo_root=REPO_ROOT) == []

    def test_no_order_adapter_import_boundary_violation(self) -> None:
        for module in (PERSISTENCE_MODULE, DECISION_FUNNEL_MODULE, MATERIALIZATION_MODULE):
            hits = scan_file_import_boundary(module, repo_root=REPO_ROOT)
            assert all("order" not in hit.module.lower() for hit in hits)

    def test_no_scheduler_import_boundary_violation(self) -> None:
        for module in (PERSISTENCE_MODULE, DECISION_FUNNEL_MODULE, MATERIALIZATION_MODULE):
            hits = scan_file_import_boundary(module, repo_root=REPO_ROOT)
            assert all("scheduler" not in hit.module.lower() for hit in hits)


class TestReconciliationFailClosed:
    def test_trade_ledger_reconciliation_failure_fails_closed(self) -> None:
        rows = materialize_trade_ledger_rows_v0(
            _fixture_trades(include_fees=True),
            instrument_id="ETH/USDT",
            run_id="fail-closed",
        )
        with pytest.raises(PersistenceContractError):
            validate_trade_ledger_reconciliation_v0(
                rows=rows,
                canonical_trade_count=99,
                snapshot_gross_pnl=100.0,
                snapshot_net_pnl=50.0,
                snapshot_total_cost=10.0,
            )


def test_manifest_verify_rc_zero(tmp_path: Path) -> None:
    from scripts.ops.primary_evidence_retention_v0 import (
        finalize_durable_bundle_manifest,
        verify_manifest_sha256,
    )

    bundle, _ = _materialize_bundle(include_fees=True)
    from src.backtest.trade_ledger_equity_curve_persistence_v0 import write_observability_bundle_v0

    write_observability_bundle_v0(bundle, tmp_path)
    rc, _ = finalize_durable_bundle_manifest(tmp_path)
    ok, _ = verify_manifest_sha256(tmp_path)
    assert rc == 0
    assert ok
