"""Contract tests for rsi_reversion warmup in strategy signal binding v1."""

from __future__ import annotations

import pytest

from src.backtest.strategy_signal_binding_v1 import (
    StrategySignalBindingError,
    compute_required_warmup_rows_v1,
    project_strategy_params_for_binding_v1,
    resolve_effective_strategy_params_v1,
)


def test_rsi_reversion_warmup_equals_rsi_window() -> None:
    configured = {"rsi_window": 14, "lower": 30.0, "upper": 70.0, "price_col": "close"}
    projected = project_strategy_params_for_binding_v1("rsi_reversion", configured)
    effective, _ = resolve_effective_strategy_params_v1("rsi_reversion", projected)
    assert compute_required_warmup_rows_v1("rsi_reversion", effective) == 14


def test_rsi_reversion_price_col_is_evaluation_only() -> None:
    configured = {"rsi_window": 14, "lower": 30.0, "upper": 70.0, "price_col": "close"}
    projected = project_strategy_params_for_binding_v1("rsi_reversion", configured)
    assert "price_col" not in projected


def test_rsi_reversion_unknown_param_fail_closed() -> None:
    with pytest.raises(StrategySignalBindingError, match="unknown_strategy_param"):
        project_strategy_params_for_binding_v1(
            "rsi_reversion",
            {"rsi_window": 14, "lower": 30.0, "upper": 70.0, "foo": "bar"},
        )
