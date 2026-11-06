"""Contract tests for P32 backtest report v1."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.backtest.p29.accounting_v2 import PositionCashStateV2
from src.backtest.p32.report_v1 import run_backtest_report_v1
from src.execution.p24.config import ExecutionModelV2Config
from src.execution.p24.execution_model_v2 import ExecutionModelV2
from src.execution.p26.adapter import ExecutionAdapterV1
from src.execution.p26.types import AdapterOrder


@dataclass(frozen=True)
class Bar:
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


def _adapter() -> ExecutionAdapterV1:
    cfg = ExecutionModelV2Config(fee_rate=0.0, slippage_bps=0.0)
    model = ExecutionModelV2(cfg)
    return ExecutionAdapterV1(model=model, cfg=cfg)


def test_determinism_same_inputs():
    bars = [Bar(1, 2, 1, 2), Bar(2, 3, 2, 3)]
    orders_by_bar: list[list[AdapterOrder]] = [[], []]
    a = _adapter()
    init = PositionCashStateV2.empty(100.0)
    r1 = run_backtest_report_v1(
        bars=bars,
        orders_by_bar=orders_by_bar,
        adapter=a,
        initial_state=init,
        initial_equity=100.0,
        symbol="MOCK",
    )
    r2 = run_backtest_report_v1(
        bars=bars,
        orders_by_bar=orders_by_bar,
        adapter=a,
        initial_state=init,
        initial_equity=100.0,
        symbol="MOCK",
    )
    assert r1.fills == r2.fills
    assert r1.state.cash == r2.state.cash
    assert r1.equity == r2.equity
    assert r1.metrics == r2.metrics


def test_equity_length_nbars_plus_1():
    bars = [Bar(1, 1, 1, 1), Bar(1, 1, 1, 1), Bar(1, 1, 1, 1)]
    orders_by_bar: list[list[AdapterOrder]] = [[], [], []]
    a = _adapter()
    init = PositionCashStateV2.empty(100.0)
    r = run_backtest_report_v1(
        bars=bars,
        orders_by_bar=orders_by_bar,
        adapter=a,
        initial_state=init,
        initial_equity=100.0,
        symbol="MOCK",
    )
    assert len(r.equity) == len(bars) + 1


def test_metrics_keys_present():
    bars = [Bar(1, 1, 1, 1)]
    orders_by_bar: list[list[AdapterOrder]] = [[]]
    a = _adapter()
    init = PositionCashStateV2.empty(100.0)
    r = run_backtest_report_v1(
        bars=bars,
        orders_by_bar=orders_by_bar,
        adapter=a,
        initial_state=init,
        initial_equity=100.0,
        symbol="MOCK",
    )
    for k in ("total_return", "max_drawdown", "sharpe", "n_steps"):
        assert k in r.metrics


def test_invalid_lengths_raises():
    bars = [Bar(1, 1, 1, 1)]
    orders_by_bar: list[list[AdapterOrder]] = [[], []]
    a = _adapter()
    init = PositionCashStateV2.empty(100.0)
    with pytest.raises(ValueError):
        run_backtest_report_v1(
            bars=bars,
            orders_by_bar=orders_by_bar,
            adapter=a,
            initial_state=init,
            initial_equity=100.0,
            symbol="MOCK",
        )
