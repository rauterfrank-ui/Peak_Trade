# src/execution_simple/types.py
"""
Execution Pipeline Types & Data Structures.

Defines core types for order execution, gates, and results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Set


class ExecutionMode(str, Enum):
    """Execution environment mode."""

    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"


class OrderSide(str, Enum):
    """Order side (buy or sell)."""

    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type."""

    MARKET = "market"
    LIMIT = "limit"


@dataclass
class ExecutionContext:
    """
    Context for execution decisions.

    Attributes:
        mode: Execution mode (backtest/paper/live)
        ts: Timestamp
        symbol: Trading symbol (e.g., "BTC-USD")
        price: Current market price
        tags: Optional tags for policy decisions (e.g., {"research_only"})
    """

    mode: ExecutionMode
    ts: datetime
    symbol: str
    price: float
    tags: Set[str] = field(default_factory=set)


@dataclass
class OrderIntent:
    """
    Trading intent before gate validation.

    Represents desired position change.
    """

    symbol: str
    side: OrderSide
    quantity: float
    price: float
    order_type: OrderType = OrderType.MARKET


@dataclass
class Order:
    """
    Validated order ready for submission.

    Passed all gates and ready to send to broker.
    """

    symbol: str
    side: OrderSide
    quantity: float
    price: float
    order_type: OrderType = OrderType.MARKET
    notional: float = 0.0

    def __post_init__(self):
        """Calculate notional value."""
        if self.notional == 0.0:
            self.notional = abs(self.quantity * self.price)


@dataclass
class Fill:
    """
    Execution fill result.

    Attributes:
        symbol: Trading symbol
        side: Order side
        quantity: Filled quantity
        price: Fill price (including slippage)
        notional: Fill notional value
        fee: Execution fee
        ts: Fill timestamp
    """

    symbol: str
    side: OrderSide
    quantity: float
    price: float
    notional: float
    fee: float
    ts: datetime


@dataclass
class GateDecision:
    """
    Result from a gate check.

    Attributes:
        gate_name: Name of the gate
        passed: Whether order passed gate
        reason: Explanation (especially for blocks)
        modified_qty: If gate modified quantity (e.g., rounding)
    """

    gate_name: str
    passed: bool
    reason: str = ""
    modified_qty: Optional[float] = None


@dataclass
class ExecutionResult:
    """
    Result of execution pipeline run.

    Attributes:
        context: Execution context
        desired_delta: Target position change
        gate_decisions: All gate decisions
        orders: Validated orders (if any gates passed)
        fills: Execution fills (if simulated/executed)
        blocked: Whether execution was blocked
        block_reason: Reason for block (if any)
    """

    context: ExecutionContext
    desired_delta: float
    gate_decisions: list[GateDecision] = field(default_factory=list)
    orders: list[Order] = field(default_factory=list)
    fills: list[Fill] = field(default_factory=list)
    blocked: bool = False
    block_reason: str = ""

    @property
    def success(self) -> bool:
        """Whether execution was successful (not blocked)."""
        return not self.blocked

    @property
    def total_filled_qty(self) -> float:
        """Total filled quantity."""
        return sum(f.quantity for f in self.fills)

    @property
    def total_notional(self) -> float:
        """Total notional value."""
        return sum(f.notional for f in self.fills)

    @property
    def total_fees(self) -> float:
        """Total fees paid."""
        return sum(f.fee for f in self.fills)
