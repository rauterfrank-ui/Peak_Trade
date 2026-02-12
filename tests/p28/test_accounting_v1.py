"""P28 accounting v1 contract tests."""

from decimal import Decimal

import pytest

from src.backtest.p28 import AccountingError, apply_fills_v1
from src.execution.p26.adapter import FillRecord


def _fill(
    *,
    order_id: str = "f1",
    symbol: str = "BTC/USDT",
    side: str = "BUY",
    qty: float = 1.0,
    price: float = 100.0,
    fee: float = 0.0,
) -> FillRecord:
    return FillRecord(
        order_id=order_id,
        symbol=symbol,
        side=side,
        qty=qty,
        price=price,
        fee=fee,
    )


def test_buy_decreases_cash_increases_pos() -> None:
    fills = [_fill(side="BUY", qty=2.0, price=10.0, fee=1.0)]
    st = apply_fills_v1(
        symbol="BTC/USDT",
        starting_cash=Decimal("100"),
        starting_position_qty=Decimal("0"),
        fills=fills,
    )
    assert st.position_qty == Decimal("2")
    assert st.cash == Decimal("100") - Decimal("20") - Decimal("1")


def test_sell_increases_cash_decreases_pos() -> None:
    fills = [_fill(side="SELL", qty=1.5, price=20.0, fee=0.5)]
    st = apply_fills_v1(
        symbol="BTC/USDT",
        starting_cash=Decimal("10"),
        starting_position_qty=Decimal("2"),
        fills=fills,
    )
    assert st.position_qty == Decimal("0.5")
    assert st.cash == Decimal("10") + Decimal("30") - Decimal("0.5")


def test_no_shorting_raises() -> None:
    fills = [_fill(side="SELL", qty=1.0, price=10.0, fee=0.0)]
    with pytest.raises(AccountingError):
        apply_fills_v1(
            symbol="BTC/USDT",
            starting_cash=Decimal("0"),
            starting_position_qty=Decimal("0.5"),
            fills=fills,
        )


def test_allow_short() -> None:
    fills = [_fill(side="SELL", qty=1.0, price=10.0, fee=0.0)]
    st = apply_fills_v1(
        symbol="BTC/USDT",
        starting_cash=Decimal("0"),
        starting_position_qty=Decimal("0.5"),
        fills=fills,
        allow_short=True,
    )
    assert st.position_qty == Decimal("-0.5")
    assert st.cash == Decimal("10")


def test_determinism_same_inputs_same_outputs() -> None:
    fills = [
        _fill(side="BUY", qty=1.0, price=10.0, fee=0.1),
        _fill(side="BUY", qty=2.0, price=11.0, fee=0.2),
        _fill(side="SELL", qty=1.0, price=12.0, fee=0.3),
    ]
    a = apply_fills_v1(
        symbol="BTC/USDT",
        starting_cash=Decimal("1000"),
        starting_position_qty=Decimal("0"),
        fills=fills,
    )
    b = apply_fills_v1(
        symbol="BTC/USDT",
        starting_cash=Decimal("1000"),
        starting_position_qty=Decimal("0"),
        fills=fills,
    )
    assert a == b


def test_symbol_mismatch_raises() -> None:
    fills = [_fill(symbol="ETH/USDT", side="BUY", qty=1.0, price=10.0, fee=0.0)]
    with pytest.raises(AccountingError):
        apply_fills_v1(
            symbol="BTC/USDT",
            starting_cash=Decimal("100"),
            starting_position_qty=Decimal("0"),
            fills=fills,
        )
