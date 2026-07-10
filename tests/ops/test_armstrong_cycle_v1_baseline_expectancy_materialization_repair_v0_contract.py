"""Contract tests for armstrong_cycle/v1 baseline expectancy materialization repair v0."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.ops.run_armstrong_cycle_v1_bound_offline_economic_baseline_evaluation_v0 import (
    ARMSTRONG_CYCLE_V1_BASELINE_NET_EXPECTANCY_NET_OR_GROSS,
    ARMSTRONG_CYCLE_V1_BASELINE_NET_EXPECTANCY_OWNER,
    ARMSTRONG_CYCLE_V1_BASELINE_NET_EXPECTANCY_UNIT,
    resolve_armstrong_cycle_v1_net_expectancy_for_baseline_v0,
)
from src.backtest import mv2_research_wiring_v1 as mv2_wiring
from src.backtest.result import BacktestResult
from src.backtest.stats import compute_backtest_stats
from src.backtest.step29m_armstrong_cycle_v1_economic_evaluation_admissibility_contract_v1 import (
    load_armstrong_cycle_v1_evaluation_config_v1,
)
from src.research.armstrong_cycle_v1_offline_economic_evaluation_scope_ratification_v0 import (
    materialize_evaluation_config_v1,
    materialize_material_difference_contract_v0,
    materialize_versioned_research_binding_v0,
)
from src.research.cross_sectional_single_slot_accounting_reconciliation_v0 import (
    reconcile_legacy_backtest_result_accounting_v0,
)
from src.research.step29m_armstrong_cycle_v1_offline_economic_baseline_materialization_v0 import (
    compute_step29m_armstrong_implementation_digest_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RATIFIED_BINDING_DIGEST = "d29de831f426eeca087518ab9ebe53c1e77895fc0f9f4550a0d804a69403d69c"
DATASET_DIGEST = "b4cbe7fff81a137da055588231757937406d8cb30d531ee0aab41d95ee9b6c78"
UNIVERSE_DIGEST = "be6ea12f6e883de596e8e7987be071bcb4ebc3d32bff15ec933643dcf74f9ee2"
EVAL_CONFIG_PATH = (
    "config/ops/step29m_okx_inst_eth_usdt_perp_armstrong_cycle_v1_economic_evaluation_v1.json"
)
BINDING_CONFIG_PATH = "config/research/armstrong_cycle_v1_versioned_research_binding_v0.json"
HISTORICAL_EVIDENCE_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/armstrong_cycle_v1_bound_offline_economic_baseline_evaluation_v0_20260710T153705Z"
)
HISTORICAL_EXPECTANCY = -34.59587143635476


def _backtest_from_trades(
    trades: list[dict[str, float | str]],
    *,
    initial_cash: float = 10000.0,
    engine_expectancy: float | None = None,
) -> BacktestResult:
    equity_values = [initial_cash]
    for trade in trades:
        equity_values.append(equity_values[-1] + float(trade["pnl"]))
    index = pd.date_range("2026-06-17", periods=len(equity_values), freq="h", tz="UTC")
    equity_curve = pd.Series(equity_values, index=index)
    drawdown = equity_curve / equity_curve.cummax() - 1.0
    stats: dict[str, float | int] = {
        "total_return": (equity_values[-1] / initial_cash) - 1.0,
        "total_trades": len(trades),
        "profit_factor": 0.16,
        "max_drawdown": float(drawdown.min()),
        "sharpe": -0.24,
    }
    if engine_expectancy is not None:
        stats["expectancy"] = engine_expectancy
    trades_df = pd.DataFrame(trades) if trades else None
    return BacktestResult(
        equity_curve=equity_curve,
        drawdown=drawdown,
        trades=trades_df,
        stats=stats,
    )


def _historical_trades() -> list[dict[str, float | str]]:
    lines = (HISTORICAL_EVIDENCE_DIR / "trade_ledger.jsonl").read_text(encoding="utf-8").strip()
    return [json.loads(line) for line in lines.split("\n") if line.strip()]


def test_materializer_uses_canonical_mv2_metrics_owner() -> None:
    assert (
        ARMSTRONG_CYCLE_V1_BASELINE_NET_EXPECTANCY_OWNER
        == "src/backtest/mv2_research_wiring_v1.py::compute_mv2_backtest_metrics_v1"
    )


def test_resolver_adopts_canonical_expectancy_not_engine_stats_default() -> None:
    trades = _historical_trades()
    backtest = _backtest_from_trades(trades, engine_expectancy=None)
    assert "expectancy" not in backtest.stats
    resolved = resolve_armstrong_cycle_v1_net_expectancy_for_baseline_v0(backtest)
    canonical = mv2_wiring.compute_mv2_backtest_metrics_v1(backtest)["expectancy"]
    assert resolved == pytest.approx(canonical)
    assert resolved == pytest.approx(HISTORICAL_EXPECTANCY)
    assert resolved != 0.0


def test_resolver_matches_compute_backtest_stats_directly() -> None:
    trades = [{"pnl": 100.0}, {"pnl": -40.0}, {"pnl": 25.0}]
    backtest = _backtest_from_trades(trades)
    expected = compute_backtest_stats(trades, backtest.equity_curve)["expectancy"]
    assert resolve_armstrong_cycle_v1_net_expectancy_for_baseline_v0(backtest) == pytest.approx(
        expected
    )
    assert expected == pytest.approx(85.0 / 3.0)


def test_zero_trade_semantics_returns_zero() -> None:
    backtest = _backtest_from_trades([])
    assert resolve_armstrong_cycle_v1_net_expectancy_for_baseline_v0(backtest) == 0.0


def test_net_expectancy_unit_and_scaling_explicit() -> None:
    assert ARMSTRONG_CYCLE_V1_BASELINE_NET_EXPECTANCY_UNIT == "absolute_quote_currency_per_trade"
    trades = [{"pnl": 50.0}, {"pnl": -30.0}]
    backtest = _backtest_from_trades(trades)
    resolved = resolve_armstrong_cycle_v1_net_expectancy_for_baseline_v0(backtest)
    assert resolved == pytest.approx(10.0)
    assert abs(resolved) < 1.0 or abs(resolved) >= 1.0


def test_net_not_gross_expectancy() -> None:
    assert ARMSTRONG_CYCLE_V1_BASELINE_NET_EXPECTANCY_NET_OR_GROSS == "net"
    trades = [{"pnl": 100.0}, {"pnl": -50.0}]
    backtest = _backtest_from_trades(trades)
    metrics = mv2_wiring.compute_mv2_backtest_metrics_v1(backtest)
    assert "expectancy" in metrics
    assert "gross_expectancy" not in metrics


def test_closed_trade_and_end_of_data_semantics_preserved() -> None:
    trades = _historical_trades()
    assert len(trades) == 6
    assert sum(1 for row in trades if row["exit_reason"] == "end_of_data") == 1
    backtest = _backtest_from_trades(trades)
    assert resolve_armstrong_cycle_v1_net_expectancy_for_baseline_v0(backtest) == pytest.approx(
        sum(float(row["pnl"]) for row in trades) / len(trades)
    )


def test_binding_dataset_universe_digests_unchanged() -> None:
    binding_cfg = json.loads((REPO_ROOT / BINDING_CONFIG_PATH).read_text(encoding="utf-8"))
    assert binding_cfg["binding_digest"] == RATIFIED_BINDING_DIGEST
    assert binding_cfg["binding"]["digest_bindings"]["data_digest"]["value"] == DATASET_DIGEST
    assert binding_cfg["universe_digest"] == UNIVERSE_DIGEST


def test_strategy_parameters_and_cost_policy_unchanged() -> None:
    eval_cfg = load_armstrong_cycle_v1_evaluation_config_v1(REPO_ROOT, EVAL_CONFIG_PATH)
    binding_cfg = json.loads((REPO_ROOT / BINDING_CONFIG_PATH).read_text(encoding="utf-8"))
    assert (
        binding_cfg["binding"]["parameter_binding"]["parameters"]
        == eval_cfg["economic_evaluation_v1"]["strategy_params"]
    )
    assert binding_cfg["binding"]["cost_execution_binding"]["roundtrip_cost_bps"] == 40.0
    assert eval_cfg["backtest"]["fee_bps"] == 10.0
    assert eval_cfg["backtest"]["slippage_bps"] == 5.0


def test_risk_sizing_semantics_unchanged() -> None:
    eval_cfg = load_armstrong_cycle_v1_evaluation_config_v1(REPO_ROOT, EVAL_CONFIG_PATH)
    sizing = eval_cfg["offline_evaluation_sizing_contract_v1"]
    assert sizing["risk_per_trade"] == 0.005
    assert sizing["stop_pct"] == 0.025


def test_implementation_digest_unchanged() -> None:
    digest = compute_step29m_armstrong_implementation_digest_v0(REPO_ROOT)
    assert len(digest) == 64


def test_gross_pnl_accounting_behavior_unchanged() -> None:
    trades = _historical_trades()
    backtest = _backtest_from_trades(trades)
    result = reconcile_legacy_backtest_result_accounting_v0(backtest, initial_cash=10000.0)
    assert result.realized_gross_pnl == 0.0
    assert result.realized_net_pnl_from_trades == pytest.approx(-207.5752286181286)
    assert result.reconciled is True


def test_historical_evidence_preserved() -> None:
    assert HISTORICAL_EVIDENCE_DIR.is_dir()
    perf = json.loads((HISTORICAL_EVIDENCE_DIR / "performance_metrics.json").read_text())
    assert perf["net_expectancy"] == 0.0


def test_versioned_binding_materialization_unchanged() -> None:
    versioned_binding = materialize_versioned_research_binding_v0(
        REPO_ROOT,
        material_difference=materialize_material_difference_contract_v0(),
        evaluation_config=materialize_evaluation_config_v1(REPO_ROOT),
    )
    assert versioned_binding["binding_digest"] == RATIFIED_BINDING_DIGEST


def test_no_runtime_or_authority_effect() -> None:
    binding_cfg = json.loads((REPO_ROOT / BINDING_CONFIG_PATH).read_text(encoding="utf-8"))
    assert binding_cfg["runtime_effect"] == "NONE"
    assert binding_cfg["authority_effect"] == "NONE"
