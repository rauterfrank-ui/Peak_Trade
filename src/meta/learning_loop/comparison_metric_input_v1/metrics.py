"""Ratified metric semantics for comparison_metric_input.v1."""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from src.meta.learning_loop.comparison_metric_input_v1.constants import (
    METRIC_KEYS,
    METRIC_SEMANTICS_VERSION,
    MINIMUM_RETURN_OBSERVATIONS,
)
from src.meta.learning_loop.comparison_metric_input_v1.models import ComparisonMetricInputError


def _reject_non_finite(value: float, *, metric: str) -> None:
    if not math.isfinite(value):
        raise ComparisonMetricInputError(f"{metric} must be finite, got {value!r}")


def _returns_from_equity(equity: pd.Series) -> pd.Series:
    if len(equity) < 2:
        raise ComparisonMetricInputError("equity series too short for returns")
    returns = equity.astype(float).pct_change().dropna()
    if len(returns) < MINIMUM_RETURN_OBSERVATIONS:
        raise ComparisonMetricInputError(
            f"insufficient return observations: need >= {MINIMUM_RETURN_OBSERVATIONS}"
        )
    if returns.isna().any() or np.isinf(returns.to_numpy()).any():
        raise ComparisonMetricInputError("returns contain NaN or Infinity")
    return returns


def compute_sharpe(equity: pd.Series, *, periods_per_year: int) -> float:
    returns = _returns_from_equity(equity)
    std = float(returns.std(ddof=1))
    mean = float(returns.mean())
    if std == 0.0:
        if mean == 0.0:
            value = 0.0
        else:
            raise ComparisonMetricInputError("zero volatility with non-zero mean is fail-closed")
    else:
        mean_return = mean * periods_per_year
        std_return = std * math.sqrt(periods_per_year)
        value = (mean_return - 0.0) / std_return
    _reject_non_finite(value, metric="sharpe")
    return float(value)


def compute_volatility(equity: pd.Series, *, periods_per_year: int) -> float:
    returns = _returns_from_equity(equity)
    std = float(returns.std(ddof=1))
    if std == 0.0 and float(returns.mean()) == 0.0:
        value = 0.0
    elif std == 0.0:
        raise ComparisonMetricInputError("zero volatility with non-zero mean is fail-closed")
    else:
        value = std * math.sqrt(periods_per_year)
    _reject_non_finite(value, metric="volatility")
    if value < 0.0:
        raise ComparisonMetricInputError("volatility must be non-negative")
    return float(value)


def compute_total_return(equity: pd.Series) -> float:
    if len(equity) < 2:
        raise ComparisonMetricInputError("equity series too short for total_return")
    initial = float(equity.iloc[0])
    final = float(equity.iloc[-1])
    if initial <= 0.0:
        raise ComparisonMetricInputError("initial equity must be positive")
    value = (final - initial) / initial
    _reject_non_finite(value, metric="total_return")
    return float(value)


def compute_max_drawdown(equity: pd.Series) -> float:
    if len(equity) < 2:
        raise ComparisonMetricInputError("equity series too short for max_drawdown")
    equity_f = equity.astype(float)
    running_max = equity_f.cummax()
    dd = (equity_f - running_max) / running_max.replace(0.0, np.nan)
    dd = dd.fillna(0.0)
    value = abs(float(dd.min()))
    _reject_non_finite(value, metric="max_drawdown")
    if value < 0.0 or value > 1.0:
        raise ComparisonMetricInputError("max_drawdown must be in [0, 1]")
    return float(value)


def _trade_pnls(trades: Sequence[Mapping[str, Any]]) -> list[float]:
    if not trades:
        raise ComparisonMetricInputError("trade ledger is empty")
    pnls: list[float] = []
    for index, trade in enumerate(trades):
        if "pnl" not in trade:
            raise ComparisonMetricInputError(f"trade {index} missing pnl")
        pnl = float(trade["pnl"])
        if not math.isfinite(pnl):
            raise ComparisonMetricInputError(f"trade {index} pnl is not finite")
        pnls.append(pnl)
    return pnls


def compute_profit_factor(trades: Sequence[Mapping[str, Any]]) -> float:
    pnls = _trade_pnls(trades)
    gross_profit = sum(p for p in pnls if p > 0.0)
    gross_loss = abs(sum(p for p in pnls if p < 0.0))
    if gross_loss == 0.0:
        raise ComparisonMetricInputError("gross_loss=0 is fail-closed for profit_factor")
    value = gross_profit / gross_loss
    _reject_non_finite(value, metric="profit_factor")
    if value < 0.0:
        raise ComparisonMetricInputError("profit_factor must be non-negative")
    return float(value)


def compute_trade_count(trades: Sequence[Mapping[str, Any]]) -> int:
    pnls = _trade_pnls(trades)
    count = len(pnls)
    if count == 0:
        raise ComparisonMetricInputError("trade_count=0 is fail-closed")
    return int(count)


def compute_all_metrics(
    *,
    equity: pd.Series,
    trades: Sequence[Mapping[str, Any]],
    periods_per_year: int,
) -> dict[str, float | int]:
    metrics: dict[str, float | int] = {
        "sharpe": compute_sharpe(equity, periods_per_year=periods_per_year),
        "volatility": compute_volatility(equity, periods_per_year=periods_per_year),
        "total_return": compute_total_return(equity),
        "max_drawdown": compute_max_drawdown(equity),
        "profit_factor": compute_profit_factor(trades),
        "trade_count": compute_trade_count(trades),
    }
    for key in METRIC_KEYS:
        if key not in metrics:
            raise ComparisonMetricInputError(f"missing metric: {key}")
    return metrics


def metrics_within_tolerance(
    left: Mapping[str, float | int],
    right: Mapping[str, float | int],
) -> bool:
    from src.meta.learning_loop.comparison_metric_input_v1.constants import TIE_TOLERANCE_CATALOG

    for key in METRIC_KEYS:
        if key not in left or key not in right:
            return False
        if key == "trade_count":
            if int(left[key]) != int(right[key]):
                return False
            continue
        tolerance = TIE_TOLERANCE_CATALOG[key]
        assert tolerance is not None
        if abs(float(left[key]) - float(right[key])) > tolerance:
            return False
    return True
