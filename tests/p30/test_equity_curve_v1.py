"""Tests for P30 equity curve v1."""

from __future__ import annotations

import math

from src.backtest.p30.equity_curve_v1 import equity_curve_v1
from src.execution.p26.adapter import FillRecord


def _fill(
    qty: float,
    price: float,
    fee: float = 0.0,
    side: str = "BUY",
    symbol: str = "MOCK",
) -> FillRecord:
    return FillRecord(
        order_id="o1",
        symbol=symbol,
        side=side,
        qty=float(qty),
        price=float(price),
        fee=float(fee),
    )


def test_empty_no_fills_equity_is_cash():
    prices = [100.0, 101.0]
    fills = [[], []]
    rows = equity_curve_v1(prices, fills, initial_cash=1000.0)
    assert len(rows) == 2
    assert rows[0].equity == 1000.0
    assert rows[1].equity == 1000.0


def test_single_buy_mark_to_market():
    prices = [100.0, 110.0]
    fills = [[_fill(1.0, 100.0, fee=1.0)], []]
    rows = equity_curve_v1(prices, fills, initial_cash=1000.0)
    assert rows[0].cash == 899.0  # 1000 - 100 - 1
    assert rows[0].qty == 1.0
    assert rows[0].equity == 999.0  # cash + pos_value(100)
    assert rows[1].equity == 1009.0  # cash + pos_value(110)


def test_determinism_same_inputs_same_outputs():
    prices = [100.0, 105.0, 103.0]
    fills = [
        [_fill(2.0, 100.0, fee=0.5)],
        [],
        [_fill(1.0, 103.0, fee=0.2)],
    ]
    a = equity_curve_v1(prices, fills, initial_cash=1000.0)
    b = equity_curve_v1(prices, fills, initial_cash=1000.0)
    assert a == b


def test_invariant_equity_equals_cash_plus_position_value():
    prices = [100.0, 90.0]
    fills = [[_fill(1.0, 100.0, fee=0.0)], []]
    rows = equity_curve_v1(prices, fills, initial_cash=1000.0)
    for r in rows:
        assert math.isclose(r.equity, r.cash + r.position_value, rel_tol=0, abs_tol=1e-9)
