"""
P23 ExecutionModelV1 unit tests.

Covers:
- determinism (same inputs => same outputs)
- fee applied
- slippage applied
- stop trigger behavior
- limit fill/no-fill behavior
"""

from __future__ import annotations

from decimal import Decimal
from datetime import datetime, timezone

import pytest

from src.execution.contracts import Order, OrderSide, OrderType
from src.execution.p23 import ExecutionModelV1, ExecutionModelP23Config
from src.execution.p23.execution_model import MarketSnapshot


def _snap(open_: float, high: float, low: float, close: float) -> MarketSnapshot:
    return MarketSnapshot(
        open=Decimal(str(open_)),
        high=Decimal(str(high)),
        low=Decimal(str(low)),
        close=Decimal(str(close)),
        ts=datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
    )


def _order(
    side: str = "BUY",
    order_type: str = "MARKET",
    qty: str = "1.0",
    price: str | None = None,
) -> Order:
    return Order(
        client_order_id="ord_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY if side == "BUY" else OrderSide.SELL,
        order_type=OrderType[order_type],
        quantity=Decimal(qty),
        price=Decimal(price) if price else None,
    )


# -----------------------------------------------------------------------------
# Determinism
# -----------------------------------------------------------------------------


def test_determinism_same_inputs_same_outputs() -> None:
    """Same (order, snapshot, config) must produce identical fills."""
    model = ExecutionModelV1(ExecutionModelP23Config(slippage_bps=5, taker_bps=10))
    order = _order(side="BUY", order_type="MARKET", qty="1.0")
    snapshot = _snap(100.0, 101.0, 99.0, 100.0)

    fills1 = model.apply(order, snapshot, fill_id_prefix="f1")
    fills2 = model.apply(order, snapshot, fill_id_prefix="f1")

    assert len(fills1) == len(fills2) == 1
    assert fills1[0].price == fills2[0].price
    assert fills1[0].fee == fills2[0].fee
    assert fills1[0].quantity == fills2[0].quantity


# -----------------------------------------------------------------------------
# Fee applied
# -----------------------------------------------------------------------------


def test_fee_applied_market_order() -> None:
    """Fee must be applied to fill notional."""
    model = ExecutionModelV1(ExecutionModelP23Config(taker_bps=10, slippage_bps=0))
    order = _order(side="BUY", order_type="MARKET", qty="1.0")
    snapshot = _snap(100.0, 100.0, 100.0, 100.0)  # no slippage

    fills = model.apply(order, snapshot)
    assert len(fills) == 1
    # 100 * 1.0 * 0.001 = 0.1
    assert fills[0].fee == Decimal("0.1")


def test_fee_zero_when_bps_zero() -> None:
    """When fee_bps=0, fee is zero."""
    model = ExecutionModelV1(ExecutionModelP23Config(taker_bps=0, slippage_bps=0))
    order = _order(side="BUY", order_type="MARKET", qty="1.0")
    snapshot = _snap(100.0, 100.0, 100.0, 100.0)

    fills = model.apply(order, snapshot)
    assert len(fills) == 1
    assert fills[0].fee == Decimal("0")


# -----------------------------------------------------------------------------
# Slippage applied
# -----------------------------------------------------------------------------


def test_slippage_buy_pays_more() -> None:
    """BUY: fill price > mid."""
    model = ExecutionModelV1(ExecutionModelP23Config(slippage_bps=50, taker_bps=0))
    order = _order(side="BUY", order_type="MARKET", qty="1.0")
    snapshot = _snap(100.0, 100.0, 100.0, 100.0)

    fills = model.apply(order, snapshot)
    assert len(fills) == 1
    assert fills[0].price > Decimal("100")


def test_slippage_sell_receives_less() -> None:
    """SELL: fill price < mid."""
    model = ExecutionModelV1(ExecutionModelP23Config(slippage_bps=50, taker_bps=0))
    order = _order(side="SELL", order_type="MARKET", qty="1.0")
    snapshot = _snap(100.0, 100.0, 100.0, 100.0)

    fills = model.apply(order, snapshot)
    assert len(fills) == 1
    assert fills[0].price < Decimal("100")


# -----------------------------------------------------------------------------
# Limit fill / no-fill
# -----------------------------------------------------------------------------


def test_limit_buy_fills_when_low_crosses_limit() -> None:
    """LIMIT BUY: fill when bar low <= limit."""
    model = ExecutionModelV1(ExecutionModelP23Config(slippage_bps=0, maker_bps=5))
    order = _order(side="BUY", order_type="LIMIT", qty="1.0", price="99.0")
    snapshot = _snap(100.0, 101.0, 98.0, 100.0)  # low=98 <= 99

    fills = model.apply(order, snapshot)
    assert len(fills) == 1
    assert fills[0].price == Decimal("99")


def test_limit_buy_no_fill_when_above_limit() -> None:
    """LIMIT BUY: no fill when bar stays above limit."""
    model = ExecutionModelV1(ExecutionModelP23Config())
    order = _order(side="BUY", order_type="LIMIT", qty="1.0", price="98.0")
    snapshot = _snap(100.0, 101.0, 99.0, 100.0)  # low=99 > 98

    fills = model.apply(order, snapshot)
    assert len(fills) == 0


def test_limit_sell_fills_when_high_crosses_limit() -> None:
    """LIMIT SELL: fill when bar high >= limit."""
    model = ExecutionModelV1(ExecutionModelP23Config(slippage_bps=0))
    order = Order(
        client_order_id="ord_001",
        symbol="BTC-EUR",
        side=OrderSide.SELL,
        order_type=OrderType.LIMIT,
        quantity=Decimal("1.0"),
        price=Decimal("101.0"),
    )
    snapshot = _snap(100.0, 102.0, 99.0, 100.0)  # high=102 >= 101

    fills = model.apply(order, snapshot)
    assert len(fills) == 1
    assert fills[0].price == Decimal("101")


# -----------------------------------------------------------------------------
# Stop trigger
# -----------------------------------------------------------------------------


def test_stop_market_buy_triggers_when_high_crosses_stop() -> None:
    """STOP BUY: triggers when high >= stop, then market fill."""
    model = ExecutionModelV1(
        ExecutionModelP23Config(slippage_bps=5, taker_bps=10, stop_market_enabled=True)
    )
    order = _order(side="BUY", order_type="STOP", qty="1.0", price="101.0")
    order = Order(
        client_order_id="ord_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        order_type=OrderType.STOP,
        quantity=Decimal("1.0"),
        price=Decimal("101.0"),
    )
    snapshot = _snap(100.0, 102.0, 99.0, 101.0)  # high=102 >= 101

    fills = model.apply(order, snapshot)
    assert len(fills) == 1
    assert fills[0].price >= Decimal("101")  # market fill with slippage


def test_stop_market_buy_no_fill_when_below_stop() -> None:
    """STOP BUY: no fill when high < stop."""
    model = ExecutionModelV1(ExecutionModelP23Config(stop_market_enabled=True))
    order = Order(
        client_order_id="ord_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        order_type=OrderType.STOP,
        quantity=Decimal("1.0"),
        price=Decimal("102.0"),
    )
    snapshot = _snap(100.0, 101.0, 99.0, 100.0)  # high=101 < 102

    fills = model.apply(order, snapshot)
    assert len(fills) == 0


def test_stop_market_sell_triggers_when_low_crosses_stop() -> None:
    """STOP SELL: triggers when low <= stop, then market fill."""
    model = ExecutionModelV1(ExecutionModelP23Config(slippage_bps=5, stop_market_enabled=True))
    order = Order(
        client_order_id="ord_001",
        symbol="BTC-EUR",
        side=OrderSide.SELL,
        order_type=OrderType.STOP,
        quantity=Decimal("1.0"),
        price=Decimal("99.0"),
    )
    snapshot = _snap(100.0, 101.0, 98.0, 99.0)  # low=98 <= 99

    fills = model.apply(order, snapshot)
    assert len(fills) == 1
    assert fills[0].price <= Decimal("99")  # market fill with slippage (SELL receives less)


def test_stop_disabled_returns_no_fill() -> None:
    """When stop_market_enabled=False, STOP orders yield no fill."""
    model = ExecutionModelV1(ExecutionModelP23Config(stop_market_enabled=False))
    order = Order(
        client_order_id="ord_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        order_type=OrderType.STOP,
        quantity=Decimal("1.0"),
        price=Decimal("101.0"),
    )
    snapshot = _snap(100.0, 102.0, 99.0, 101.0)

    fills = model.apply(order, snapshot)
    assert len(fills) == 0


# -----------------------------------------------------------------------------
# Smoke
# -----------------------------------------------------------------------------


def test_p23_smoke() -> None:
    """Basic smoke test."""
    assert True


def test_config_from_dict() -> None:
    """Config.from_dict handles flat and nested structures."""
    from src.execution.p23.config import ExecutionModelP23Config

    flat = ExecutionModelP23Config.from_dict({"maker_bps": 3, "taker_bps": 8, "slippage_bps": 10})
    assert flat.maker_bps == 3
    assert flat.taker_bps == 8
    assert flat.slippage_bps == 10

    nested = ExecutionModelP23Config.from_dict(
        {"fees": {"maker_bps": 2, "taker_bps": 6}, "slippage": {"bps": 4}}
    )
    assert nested.maker_bps == 2
    assert nested.taker_bps == 6
    assert nested.slippage_bps == 4
