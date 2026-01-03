"""
Tests for Risk Layer Adapters
"""

import pytest

from src.execution_simple.types import Order, OrderSide, OrderType
from src.risk_layer.adapters import order_to_dict, to_order


def test_to_order_with_order_object_returns_as_is() -> None:
    """Test that Order objects are returned as-is."""
    order = Order(symbol="BTCUSDT", side=OrderSide.BUY, quantity=1.0, price=50000.0)
    result = to_order(order)
    assert result is order


def test_to_order_with_minimal_dict() -> None:
    """Test converting minimal dict to Order."""
    order_dict = {"symbol": "BTCUSDT", "qty": 1.0}
    result = to_order(order_dict)

    assert isinstance(result, Order)
    assert result.symbol == "BTCUSDT"
    assert result.quantity == 1.0
    assert result.side == OrderSide.BUY  # default
    assert result.order_type == OrderType.MARKET  # default
    assert result.price == 0.0  # default


def test_to_order_with_quantity_key() -> None:
    """Test that 'quantity' key also works."""
    order_dict = {"symbol": "ETHUSDT", "quantity": 2.5}
    result = to_order(order_dict)

    assert result.symbol == "ETHUSDT"
    assert result.quantity == 2.5


def test_to_order_with_full_dict() -> None:
    """Test converting full dict with all fields."""
    order_dict = {
        "symbol": "BTCUSDT",
        "qty": 1.5,
        "side": "SELL",
        "price": 48000.0,
        "order_type": "LIMIT",
    }
    result = to_order(order_dict)

    assert result.symbol == "BTCUSDT"
    assert result.quantity == 1.5
    assert result.side == OrderSide.SELL
    assert result.price == 48000.0
    assert result.order_type == OrderType.LIMIT


def test_to_order_with_long_short_side() -> None:
    """Test that LONG/SHORT are mapped to BUY/SELL."""
    order_long = to_order({"symbol": "BTCUSDT", "qty": 1.0, "side": "LONG"})
    assert order_long.side == OrderSide.BUY

    order_short = to_order({"symbol": "BTCUSDT", "qty": 1.0, "side": "SHORT"})
    assert order_short.side == OrderSide.SELL


def test_to_order_with_lowercase_side() -> None:
    """Test that lowercase side is handled."""
    order_buy = to_order({"symbol": "BTCUSDT", "qty": 1.0, "side": "buy"})
    assert order_buy.side == OrderSide.BUY

    order_sell = to_order({"symbol": "BTCUSDT", "qty": 1.0, "side": "sell"})
    assert order_sell.side == OrderSide.SELL


def test_to_order_missing_symbol_raises() -> None:
    """Test that missing symbol raises ValueError."""
    with pytest.raises(ValueError, match="missing required field: symbol"):
        to_order({"qty": 1.0})


def test_to_order_empty_symbol_raises() -> None:
    """Test that empty symbol raises ValueError."""
    with pytest.raises(ValueError, match="missing required field: symbol"):
        to_order({"symbol": "", "qty": 1.0})

    with pytest.raises(ValueError, match="missing required field: symbol"):
        to_order({"symbol": "   ", "qty": 1.0})


def test_to_order_missing_qty_raises() -> None:
    """Test that missing qty/quantity raises ValueError."""
    with pytest.raises(ValueError, match="missing required field: qty or quantity"):
        to_order({"symbol": "BTCUSDT"})


def test_to_order_invalid_qty_raises() -> None:
    """Test that invalid qty types raise ValueError."""
    with pytest.raises(ValueError, match="quantity must be numeric"):
        to_order({"symbol": "BTCUSDT", "qty": "invalid"})


def test_to_order_zero_qty_raises() -> None:
    """Test that zero or negative qty raises ValueError."""
    with pytest.raises(ValueError, match="quantity must be > 0"):
        to_order({"symbol": "BTCUSDT", "qty": 0})

    with pytest.raises(ValueError, match="quantity must be > 0"):
        to_order({"symbol": "BTCUSDT", "qty": -1.0})


def test_to_order_invalid_side_raises() -> None:
    """Test that invalid side raises ValueError."""
    with pytest.raises(ValueError, match="Invalid order side"):
        to_order({"symbol": "BTCUSDT", "qty": 1.0, "side": "INVALID"})


def test_to_order_invalid_order_type_raises() -> None:
    """Test that invalid order_type raises ValueError."""
    with pytest.raises(ValueError, match="Invalid order_type"):
        to_order({"symbol": "BTCUSDT", "qty": 1.0, "order_type": "INVALID"})


def test_to_order_non_dict_non_order_raises() -> None:
    """Test that non-dict, non-Order input raises ValueError."""
    with pytest.raises(ValueError, match="must be Order or dict"):
        to_order("not a dict")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="must be Order or dict"):
        to_order([{"symbol": "BTC", "qty": 1}])  # type: ignore[arg-type]


def test_order_to_dict() -> None:
    """Test converting Order to dict."""
    order = Order(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        quantity=1.5,
        price=50000.0,
        order_type=OrderType.LIMIT,
    )
    result = order_to_dict(order)

    assert result == {
        "symbol": "BTCUSDT",
        "side": "buy",
        "quantity": 1.5,
        "price": 50000.0,
        "order_type": "limit",
        "notional": 75000.0,  # 1.5 * 50000
    }


def test_order_to_dict_is_deterministic() -> None:
    """Test that order_to_dict produces consistent output."""
    order = Order(symbol="ETHUSDT", side=OrderSide.SELL, quantity=2.0, price=3000.0)

    result1 = order_to_dict(order)
    result2 = order_to_dict(order)

    assert result1 == result2
    # Check field order is stable (dict order is preserved in Python 3.7+)
    assert list(result1.keys()) == [
        "symbol",
        "side",
        "quantity",
        "price",
        "order_type",
        "notional",
    ]
