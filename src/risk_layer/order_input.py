"""
Risk-layer order input types (audit / gate evaluation).

These types normalize dict or object inputs for RiskGate. They are not live
execution contracts (see ``src.execution.contracts`` and ``src.orders.base``).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OrderSide(str, Enum):
    """Order side (buy or sell)."""

    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type."""

    MARKET = "market"
    LIMIT = "limit"


@dataclass
class Order:
    """Validated order snapshot for risk audit serialization."""

    symbol: str
    side: OrderSide
    quantity: float
    price: float
    order_type: OrderType = OrderType.MARKET
    notional: float = 0.0

    def __post_init__(self) -> None:
        if self.notional == 0.0:
            self.notional = abs(self.quantity * self.price)
