"""Panel economic evaluation wiring for cross-sectional relative-strength v0.

Orchestrates backtest, walk-forward period splits, Monte Carlo, and stress via
existing canonical owners. No parallel engines or evidence SSOT.
Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

import pandas as pd

from src.experiments.monte_carlo import MonteCarloConfig, run_monte_carlo_from_equity
from src.experiments.stress_tests import StressScenarioConfig, run_stress_test_suite
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (
    MONTE_CARLO_RUNS,
    MONTE_CARLO_SEED,
    STRATEGY_ID,
    STRATEGY_VERSION,
)
from src.research.cross_sectional_single_slot_backtest_wiring_v0 import (
    SingleSlotBacktestResultV0,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_PANEL_ECONOMIC_EVALUATION_WIRING_V0=true"
WIRING_VERSION = "cross_sectional_panel_economic_evaluation_wiring.v0"


@dataclass(frozen=True)
class WalkForwardPeriodMetricsV0:
    period_name: str
    start_utc: str
    end_utc: str
    net_return: float
    trade_count: int
    bar_count: int


@dataclass(frozen=True)
class RobustnessStageResultsV0:
    wiring_version: str
    walk_forward_results: tuple[WalkForwardPeriodMetricsV0, ...]
    monte_carlo_summary: dict[str, Any]
    stress_results: dict[str, Any]
    parameter_sensitivity_status: str
    authority_effect: str


def _slice_equity_by_period(
    equity_curve: pd.Series,
    *,
    start_utc: str,
    end_utc: str,
) -> pd.Series:
    start = pd.Timestamp(start_utc)
    end = pd.Timestamp(end_utc)
    if equity_curve.index.tz is None:
        idx = equity_curve.index.tz_localize("UTC")
    else:
        idx = equity_curve.index
    sliced = equity_curve.copy()
    sliced.index = idx
    mask = (sliced.index >= start) & (sliced.index <= end)
    return sliced.loc[mask]


def compute_walk_forward_period_metrics_v0(
    backtest: SingleSlotBacktestResultV0,
    *,
    period_binding: Mapping[str, Any],
) -> tuple[WalkForwardPeriodMetricsV0, ...]:
    periods = (
        ("training", period_binding["training_start"], period_binding["training_end"]),
        ("validation", period_binding["validation_start"], period_binding["validation_end"]),
        (
            "out_of_sample",
            period_binding["out_of_sample_start"],
            period_binding["out_of_sample_end"],
        ),
    )
    results: list[WalkForwardPeriodMetricsV0] = []
    for name, start, end in periods:
        sliced = _slice_equity_by_period(backtest.equity_curve, start_utc=start, end_utc=end)
        if len(sliced) < 2:
            net_return = 0.0
        else:
            net_return = float(sliced.iloc[-1] / sliced.iloc[0] - 1.0)
        trade_count = len(
            [
                row
                for row in backtest.trades.to_dict(orient="records")
                if row.get("exit_time") and start <= str(row["exit_time"]) <= end
            ]
        )
        results.append(
            WalkForwardPeriodMetricsV0(
                period_name=name,
                start_utc=str(start),
                end_utc=str(end),
                net_return=net_return,
                trade_count=trade_count,
                bar_count=len(sliced),
            )
        )
    return tuple(results)


def invoke_monte_carlo_v0(
    backtest: SingleSlotBacktestResultV0,
    *,
    runs: int = MONTE_CARLO_RUNS,
    seed: int = MONTE_CARLO_SEED,
) -> dict[str, Any]:
    config = MonteCarloConfig(num_runs=runs, seed=seed, method="simple")
    summary = run_monte_carlo_from_equity(backtest.equity_curve, config)
    return {
        "runs": runs,
        "seed": seed,
        "method": config.method,
        "metric_quantiles": {
            key: dict(value) if hasattr(value, "items") else value
            for key, value in getattr(summary, "metric_quantiles", {}).items()
        },
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
    }


def invoke_stress_v0(backtest: SingleSlotBacktestResultV0) -> dict[str, Any]:
    returns = backtest.equity_curve.pct_change().dropna()
    scenarios = [
        StressScenarioConfig(scenario_type="single_crash_bar", severity=0.2, position="middle"),
        StressScenarioConfig(scenario_type="vol_spike", severity=0.15, window=3, position="middle"),
    ]

    def _stats_fn(rets: pd.Series) -> dict[str, float]:
        if rets.empty:
            return {"total_return": 0.0, "max_drawdown": 0.0}
        equity = (1.0 + rets).cumprod()
        total_return = float(equity.iloc[-1] - 1.0) if len(equity) else 0.0
        dd = float((equity / equity.cummax() - 1.0).min()) if len(equity) else 0.0
        return {"total_return": total_return, "max_drawdown": dd}

    suite = run_stress_test_suite(returns, scenarios, _stats_fn)
    return {
        "baseline_metrics": dict(suite.baseline_metrics or {}),
        "scenarios": [
            {
                "scenario_type": r.scenario.scenario_type,
                "severity": r.scenario.severity,
                "stressed_metrics": dict(r.stressed_metrics or {}),
                "diff_metrics": dict(r.diff_metrics or {}),
            }
            for r in suite.scenario_results
        ],
    }


def wire_robustness_stages_v0(
    backtest: SingleSlotBacktestResultV0,
    *,
    period_binding: Mapping[str, Any],
    economic_policy_binding: Mapping[str, Any],
) -> RobustnessStageResultsV0:
    wf = compute_walk_forward_period_metrics_v0(backtest, period_binding=period_binding)
    mc_binding = economic_policy_binding.get("monte_carlo_policy_binding", {})
    runs = int(mc_binding.get("runs", MONTE_CARLO_RUNS))
    seed = int(mc_binding.get("seed", MONTE_CARLO_SEED))
    mc = invoke_monte_carlo_v0(backtest, runs=runs, seed=seed)
    stress = invoke_stress_v0(backtest)
    return RobustnessStageResultsV0(
        wiring_version=WIRING_VERSION,
        walk_forward_results=wf,
        monte_carlo_summary=mc,
        stress_results=stress,
        parameter_sensitivity_status="BOUND_PRIMARY_ONLY_NO_SEARCH",
        authority_effect="NONE",
    )


def robustness_results_to_dict(results: RobustnessStageResultsV0) -> dict[str, Any]:
    return {
        "wiring_version": results.wiring_version,
        "walk_forward_results": [
            {
                "period_name": item.period_name,
                "start_utc": item.start_utc,
                "end_utc": item.end_utc,
                "net_return": item.net_return,
                "trade_count": item.trade_count,
                "bar_count": item.bar_count,
            }
            for item in results.walk_forward_results
        ],
        "monte_carlo_results": results.monte_carlo_summary,
        "stress_results": results.stress_results,
        "parameter_sensitivity_results": {
            "status": results.parameter_sensitivity_status,
            "parameter_search_forbidden": True,
            "primary_binding_only": True,
        },
        "authority_effect": results.authority_effect,
    }


def serialize_robustness_json_v0(results: RobustnessStageResultsV0) -> str:
    return json.dumps(robustness_results_to_dict(results), indent=2, sort_keys=True) + "\n"
