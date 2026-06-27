"""
Offline adapter for VaR backtest suite integration.

Deterministic, look-ahead-free bridge between portfolio return series and the
existing Christoffersen/Kupiec suite runner.  No trading, runtime, or data
loading authority.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.risk.portfolio_var import historical_var
from src.risk.validation.suite_runner import (
    VaRBacktestSuiteResult,
    run_var_backtest_suite,
)

_SINGLE_ASSET_COL = "RET"
_SINGLE_ASSET_WEIGHT = {_SINGLE_ASSET_COL: 1.0}


@dataclass(frozen=True)
class AlignedVaRBacktestInputs:
    """Strictly aligned returns and VaR forecasts ready for suite evaluation."""

    returns: pd.Series
    var_series: pd.Series


def _validate_returns_series(returns: pd.Series) -> None:
    if not isinstance(returns, pd.Series):
        raise ValueError(f"returns must be a pd.Series, got {type(returns).__name__}")
    if returns.index.duplicated().any():
        raise ValueError("returns index must be unique")
    if len(returns) == 0:
        raise ValueError("returns must not be empty")
    values = returns.to_numpy(dtype=float, copy=False)
    if not np.isfinite(values).all():
        raise ValueError("returns must not contain NaN or Inf values")


def _validate_var_series_strict(var_series: pd.Series) -> None:
    if not isinstance(var_series, pd.Series):
        raise ValueError(f"var_series must be a pd.Series, got {type(var_series).__name__}")
    if var_series.index.duplicated().any():
        raise ValueError("var_series index must be unique")
    if len(var_series) == 0:
        raise ValueError("var_series must not be empty")
    values = var_series.to_numpy(dtype=float, copy=False)
    if not np.isfinite(values).all():
        raise ValueError("var_series must not contain NaN or Inf values")


def _validate_var_series_for_alignment(var_series: pd.Series) -> None:
    if not isinstance(var_series, pd.Series):
        raise ValueError(f"var_series must be a pd.Series, got {type(var_series).__name__}")
    if var_series.index.duplicated().any():
        raise ValueError("var_series index must be unique")
    if len(var_series) == 0:
        raise ValueError("var_series must not be empty")
    finite_mask = np.isfinite(var_series.to_numpy(dtype=float, copy=False))
    if not finite_mask.any():
        raise ValueError("var_series has no finite values")


def _validate_confidence_level(confidence_level: float) -> None:
    if not 0.0 < confidence_level < 1.0:
        raise ValueError(
            f"confidence_level must be strictly between 0 and 1, got {confidence_level}"
        )


def _validate_window(window: int) -> None:
    if not isinstance(window, int) or isinstance(window, bool):
        raise ValueError(f"window must be an integer, got {window!r}")
    if window <= 1:
        raise ValueError(f"window must be > 1, got {window}")


def build_rolling_historical_var_forecast(
    returns: pd.Series,
    window: int,
    confidence_level: float = 0.95,
) -> pd.Series:
    """
    Build look-ahead-free rolling historical VaR forecasts.

    Forecast at integer position ``t`` uses only ``returns.iloc[t - window : t]``.
    The first ``window`` positions receive no forecast (NaN).

    Reuses ``historical_var`` from ``src.risk.portfolio_var``; no alternative
    quantile implementation.
    """
    _validate_returns_series(returns)
    _validate_window(window)
    _validate_confidence_level(confidence_level)

    if len(returns) <= window:
        raise ValueError(f"returns length ({len(returns)}) must exceed window ({window})")

    forecasts = pd.Series(np.nan, index=returns.index, dtype=float)

    for pos in range(window, len(returns)):
        training = returns.iloc[pos - window : pos]
        training_df = training.to_frame(name=_SINGLE_ASSET_COL)
        var_val = historical_var(
            training_df,
            weights=_SINGLE_ASSET_WEIGHT,
            confidence=confidence_level,
            horizon_days=1,
        )
        forecasts.iloc[pos] = var_val

    return forecasts


def normalize_var_sign_to_positive_loss(var_series: pd.Series) -> pd.Series:
    """
    Normalize VaR sign convention to positive loss magnitude.

    Negative values are converted via absolute value; positive values are
    unchanged.  This function adjusts sign only — not unit, horizon, or
    confidence level.
    """
    _validate_var_series_strict(var_series)
    return var_series.abs()


def align_var_backtest_inputs(
    returns: pd.Series,
    var_series: pd.Series,
    *,
    min_observations: int = 2,
) -> AlignedVaRBacktestInputs:
    """
    Strict label-based alignment of returns and VaR forecasts.

    Only common index labels are retained.  No forward-fill, backfill, or
    interpolation.  Pairs with NaN or Inf in either series are dropped.
    """
    _validate_returns_series(returns)
    _validate_var_series_for_alignment(var_series)

    common_labels = returns.index.intersection(var_series.index)
    if len(common_labels) == 0:
        raise ValueError("no overlapping index labels between returns and var_series")

    common_labels = common_labels.sort_values()

    aligned_returns = returns.loc[common_labels]
    aligned_var = var_series.loc[common_labels].abs()

    valid_mask = (
        aligned_returns.notna()
        & aligned_var.notna()
        & np.isfinite(aligned_returns.to_numpy(dtype=float, copy=False))
        & np.isfinite(aligned_var.to_numpy(dtype=float, copy=False))
    )
    aligned_returns = aligned_returns[valid_mask]
    aligned_var = aligned_var[valid_mask]

    if len(aligned_returns) == 0:
        raise ValueError("alignment produced empty series")

    if len(aligned_returns) < min_observations:
        raise ValueError(
            f"aligned series length ({len(aligned_returns)}) is below minimum ({min_observations})"
        )

    if not aligned_returns.index.equals(aligned_var.index):
        raise ValueError("aligned returns and var_series indices must be identical")

    return AlignedVaRBacktestInputs(
        returns=aligned_returns,
        var_series=aligned_var,
    )


def run_rolling_historical_var_backtest_suite(
    returns: pd.Series,
    window: int,
    confidence_level: float = 0.95,
    significance: float = 0.05,
) -> VaRBacktestSuiteResult:
    """
    Convenience entry: rolling forecast, sign normalize, align, delegate to suite.

    Pure delegation — no new statistics, no file I/O, no network.
    """
    var_forecast = build_rolling_historical_var_forecast(
        returns,
        window=window,
        confidence_level=confidence_level,
    )
    var_normalized = var_forecast.abs()
    aligned = align_var_backtest_inputs(returns, var_normalized)
    return run_var_backtest_suite(
        aligned.returns,
        aligned.var_series,
        confidence_level=confidence_level,
        significance=significance,
    )
