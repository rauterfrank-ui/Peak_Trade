"""Golden and fail-closed tests for comparison_metric_input.v1 metrics."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from src.meta.learning_loop.comparison_metric_input_v1.constants import (
    METRIC_KEYS,
    TIE_TOLERANCE_CATALOG,
)
from src.meta.learning_loop.comparison_metric_input_v1.metrics import (
    compute_all_metrics,
    compute_max_drawdown,
    compute_profit_factor,
    compute_sharpe,
    compute_total_return,
    compute_trade_count,
    compute_volatility,
    metrics_within_tolerance,
)
from src.meta.learning_loop.comparison_metric_input_v1.models import ComparisonMetricInputError
from tests.meta.comparison_metric_input_v1_fixtures import (
    GOLDEN_METRICS,
    write_equity_csv,
    write_trades_parquet,
)


def _equity_series(values: list[float]) -> pd.Series:
    index = pd.date_range("2025-01-01", periods=len(values), freq="D")
    return pd.Series(values, index=index)


def _trades(pnls: list[float]) -> list[dict[str, float]]:
    return [{"pnl": pnl} for pnl in pnls]


def test_golden_compute_all_metrics_matches_fixture_catalog() -> None:
    equity = _equity_series([10000.0, 10100.0, 10050.0, 10200.0, 10300.0, 10150.0, 10400.0])
    metrics = compute_all_metrics(
        equity=equity, trades=_trades([100.0, -50.0, 75.0, 25.0]), periods_per_year=252
    )
    assert metrics == GOLDEN_METRICS


@pytest.mark.parametrize("metric", METRIC_KEYS)
def test_golden_metric_keys_present(metric: str) -> None:
    equity = _equity_series([10000.0, 10100.0, 10050.0, 10200.0, 10300.0, 10150.0, 10400.0])
    metrics = compute_all_metrics(
        equity=equity, trades=_trades([100.0, -50.0, 75.0, 25.0]), periods_per_year=252
    )
    assert metric in metrics


def test_compute_sharpe_zero_volatility_zero_mean_returns_zero() -> None:
    equity = _equity_series([100.0, 100.0, 100.0])
    assert compute_sharpe(equity, periods_per_year=252) == 0.0


def test_compute_sharpe_zero_volatility_non_zero_mean_fail_closed() -> None:
    equity = _equity_series([100.0, 110.0, 121.0])
    with pytest.raises(ComparisonMetricInputError, match="zero volatility with non-zero mean"):
        compute_sharpe(equity, periods_per_year=252)


def test_compute_total_return_requires_positive_initial_equity() -> None:
    equity = _equity_series([0.0, 1.0, 2.0])
    with pytest.raises(ComparisonMetricInputError, match="initial equity must be positive"):
        compute_total_return(equity)


def test_compute_max_drawdown_out_of_range_fail_closed() -> None:
    equity = pd.Series([1.0, -1.0], index=pd.date_range("2025-01-01", periods=2, freq="D"))
    with pytest.raises(ComparisonMetricInputError, match="max_drawdown must be in"):
        compute_max_drawdown(equity)


def test_compute_profit_factor_zero_gross_loss_fail_closed() -> None:
    with pytest.raises(ComparisonMetricInputError, match="gross_loss=0"):
        compute_profit_factor(_trades([10.0, 5.0]))


def test_compute_trade_count_empty_ledger_fail_closed() -> None:
    with pytest.raises(ComparisonMetricInputError, match="trade ledger is empty"):
        compute_trade_count([])


def test_returns_with_nan_fail_closed() -> None:
    equity = _equity_series([100.0, 0.0, 100.0])
    with pytest.raises(ComparisonMetricInputError, match="returns contain NaN or Infinity"):
        compute_volatility(equity, periods_per_year=252)


def test_metrics_within_tolerance_exact_match() -> None:
    assert metrics_within_tolerance(GOLDEN_METRICS, dict(GOLDEN_METRICS)) is True


def test_metrics_within_tolerance_respects_trade_count_exactness() -> None:
    left = dict(GOLDEN_METRICS)
    right = dict(GOLDEN_METRICS)
    right["trade_count"] = int(right["trade_count"]) + 1
    assert metrics_within_tolerance(left, right) is False


def test_metrics_within_tolerance_respects_numeric_tolerance() -> None:
    left = dict(GOLDEN_METRICS)
    right = dict(GOLDEN_METRICS)
    tol = TIE_TOLERANCE_CATALOG["sharpe"]
    assert tol is not None
    right["sharpe"] = float(left["sharpe"]) + tol * 2
    assert metrics_within_tolerance(left, right) is False


def test_fixture_artifacts_support_metric_recompute(tmp_path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    write_equity_csv(run_dir)
    write_trades_parquet(run_dir)
    frame = pd.read_csv(run_dir / "equity.csv")
    equity = pd.Series(frame["equity"].values, index=pd.to_datetime(frame["timestamp"]))
    trades = pd.read_parquet(run_dir / "trades.parquet")
    recomputed = compute_all_metrics(
        equity=equity,
        trades=[{"pnl": float(v)} for v in trades["pnl"].tolist()],
        periods_per_year=252,
    )
    assert math.isfinite(float(recomputed["sharpe"]))
