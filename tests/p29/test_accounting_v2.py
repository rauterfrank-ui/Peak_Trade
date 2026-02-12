"""P29 accounting v2 contract tests."""

import math

import pytest

from src.backtest.p29.accounting_v2 import AccountingErrorV2, PositionCashStateV2, apply_fills_v2
from src.execution.p26.adapter import FillRecord


def _fill(
    symbol: str,
    side: str,
    qty: float,
    price: float,
    fee: float = 0.0,
    order_id: str = "o1",
) -> FillRecord:
    return FillRecord(
        order_id=order_id,
        symbol=symbol,
        side=side,
        qty=float(qty),
        price=float(price),
        fee=float(fee),
    )


def test_buy_updates_qty_avg_cost_cash() -> None:
    s0 = PositionCashStateV2.empty(initial_cash=1000.0)
    s1 = apply_fills_v2(s0, [_fill("BTC", "BUY", 2.0, 100.0, fee=1.0)])
    assert s1.positions_qty["BTC"] == 2.0
    assert s1.avg_cost["BTC"] == 100.0
    assert math.isclose(s1.cash, 1000.0 - (200.0 + 1.0))
    assert math.isclose(s1.realized_pnl, 0.0)


def test_buy_weighted_avg_cost() -> None:
    s0 = PositionCashStateV2.empty(initial_cash=1000.0)
    s1 = apply_fills_v2(s0, [_fill("BTC", "BUY", 2.0, 100.0, fee=0.0)])
    s2 = apply_fills_v2(s1, [_fill("BTC", "BUY", 1.0, 130.0, fee=0.0)])
    assert s2.positions_qty["BTC"] == 3.0
    assert math.isclose(s2.avg_cost["BTC"], (2.0 * 100.0 + 1.0 * 130.0) / 3.0)
    assert math.isclose(s2.realized_pnl, 0.0)


def test_sell_realized_pnl_and_cash() -> None:
    s0 = PositionCashStateV2.empty(initial_cash=1000.0)
    s1 = apply_fills_v2(s0, [_fill("BTC", "BUY", 2.0, 100.0, fee=0.0)])
    s2 = apply_fills_v2(s1, [_fill("BTC", "SELL", 1.5, 110.0, fee=2.0)])
    assert math.isclose(s2.positions_qty["BTC"], 0.5)
    assert math.isclose(s2.avg_cost["BTC"], 100.0)
    assert math.isclose(s2.cash, 1000.0 - 200.0 + (1.5 * 110.0 - 2.0))
    assert math.isclose(s2.realized_pnl, (110.0 - 100.0) * 1.5 - 2.0)


def test_full_close_resets_avg_cost_to_zero() -> None:
    s0 = PositionCashStateV2.empty(initial_cash=0.0)
    s1 = apply_fills_v2(s0, [_fill("ETH", "BUY", 1.0, 50.0, fee=0.0)])
    s2 = apply_fills_v2(s1, [_fill("ETH", "SELL", 1.0, 55.0, fee=0.0)])
    assert "ETH" not in s2.positions_qty
    assert "ETH" not in s2.avg_cost
    assert math.isclose(s2.realized_pnl, (55.0 - 50.0) * 1.0)


def test_sell_more_than_position_errors() -> None:
    s0 = PositionCashStateV2.empty(initial_cash=0.0)
    s1 = apply_fills_v2(s0, [_fill("BTC", "BUY", 1.0, 100.0, fee=0.0)])
    with pytest.raises(AccountingErrorV2):
        apply_fills_v2(s1, [_fill("BTC", "SELL", 1.0001, 100.0, fee=0.0)])


def test_determinism_same_inputs_same_outputs() -> None:
    fills = [
        _fill("BTC", "BUY", 1.0, 100.0, fee=1.0, order_id="a"),
        _fill("BTC", "BUY", 1.0, 120.0, fee=1.0, order_id="b"),
        _fill("BTC", "SELL", 0.5, 130.0, fee=0.5, order_id="c"),
    ]
    s0 = PositionCashStateV2.empty(initial_cash=1000.0)
    s1 = apply_fills_v2(s0, fills)
    s2 = apply_fills_v2(s0, fills)
    assert s1 == s2
