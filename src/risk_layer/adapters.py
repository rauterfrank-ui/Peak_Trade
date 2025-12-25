"""
Risk Layer Adapters
====================

Adapters for converting external types to Risk Layer internal types.
"""

from __future__ import annotations

from typing import Any, Union

from src.execution_simple.types import Order, OrderSide, OrderType


def to_order(order_input: Union[Order, dict]) -> Order:
    """
    Convert order input to canonical Order model.

    Accepts either:
    - Order object (returned as-is)
    - dict with order data (converted to Order)

    Args:
        order_input: Order object or dict

    Returns:
        Order instance

    Raises:
        ValueError: If order_input is invalid or missing required fields

    Examples:
        >>> order = to_order({"symbol": "BTCUSDT", "qty": 1.0})
        >>> order = to_order(Order(symbol="BTCUSDT", side=OrderSide.BUY, quantity=1.0, price=50000.0))
    """
    # Already an Order? Return as-is
    if isinstance(order_input, Order):
        return order_input

    # Must be a dict
    if not isinstance(order_input, dict):
        raise ValueError(f"order_input must be Order or dict, got {type(order_input).__name__}")

    # Extract required fields
    symbol = order_input.get("symbol")
    if not symbol or not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("Order missing required field: symbol (non-empty string)")

    # Support both "qty" and "quantity" keys
    quantity = order_input.get("qty") if "qty" in order_input else order_input.get("quantity")
    if quantity is None:
        raise ValueError("Order missing required field: qty or quantity")

    try:
        quantity = float(quantity)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Order quantity must be numeric, got {quantity}") from e

    if quantity <= 0:
        raise ValueError(f"Order quantity must be > 0, got {quantity}")

    # Extract optional fields with defaults
    price_raw = order_input.get("price", 0.0)
    try:
        price = float(price_raw) if price_raw is not None else 0.0
    except (TypeError, ValueError) as e:
        raise ValueError(f"Order price must be numeric, got {price_raw}") from e

    # Parse side (default: BUY)
    side_raw = order_input.get("side", "BUY")
    if isinstance(side_raw, OrderSide):
        side = side_raw
    elif isinstance(side_raw, str):
        side_upper = side_raw.upper()
        if side_upper in ("BUY", "LONG"):
            side = OrderSide.BUY
        elif side_upper in ("SELL", "SHORT"):
            side = OrderSide.SELL
        else:
            raise ValueError(f"Invalid order side: {side_raw} (expected BUY/SELL/LONG/SHORT)")
    else:
        raise ValueError(f"Order side must be str or OrderSide, got {type(side_raw)}")

    # Parse order_type (default: MARKET)
    order_type_raw = order_input.get("order_type", "MARKET")
    if isinstance(order_type_raw, OrderType):
        order_type = order_type_raw
    elif isinstance(order_type_raw, str):
        order_type_upper = order_type_raw.upper()
        if order_type_upper == "MARKET":
            order_type = OrderType.MARKET
        elif order_type_upper == "LIMIT":
            order_type = OrderType.LIMIT
        else:
            raise ValueError(f"Invalid order_type: {order_type_raw} (expected MARKET/LIMIT)")
    else:
        raise ValueError(f"Order order_type must be str or OrderType, got {type(order_type_raw)}")

    # Create Order
    return Order(
        symbol=symbol.strip(),
        side=side,
        quantity=quantity,
        price=price,
        order_type=order_type,
    )


def order_to_dict(order: Order) -> dict[str, Any]:
    """
    Convert Order to deterministic dict for serialization.

    Args:
        order: Order instance

    Returns:
        Dict with order data (stable field order)
    """
    return {
        "symbol": order.symbol,
        "side": order.side.value,
        "quantity": order.quantity,
        "price": order.price,
        "order_type": order.order_type.value,
        "notional": order.notional,
    }
