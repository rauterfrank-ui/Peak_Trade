# src/execution_simple/adapters/simulated.py
"""
Simulated Broker Adapter for Paper/Backtest.

Provides instant fills with configurable slippage and fees.
"""

from __future__ import annotations

from ..types import ExecutionContext, Fill, Order, OrderSide
from .base import BaseBrokerAdapter


class SimulatedBrokerAdapter(BaseBrokerAdapter):
    """
    Simulated broker for paper trading and backtesting.

    Features:
    - Instant fills at mid price ± slippage
    - Configurable slippage (basis points)
    - Configurable fees (basis points)
    - No network latency or real broker integration
    """

    def __init__(self, slippage_bps: float = 2.0, fee_bps: float = 0.0):
        """
        Initialize simulated adapter.

        Args:
            slippage_bps: Slippage in basis points (100 bps = 1%)
                         BUY: price increased by slippage
                         SELL: price decreased by slippage
            fee_bps: Fee in basis points (10 bps = 0.1%)
        """
        self.slippage_bps = slippage_bps
        self.fee_bps = fee_bps

    def get_name(self) -> str:
        """Adapter name."""
        return "SimulatedBroker"

    def execute_order(self, order: Order, context: ExecutionContext) -> Fill:
        """
        Execute order with simulated fill.

        Args:
            order: Order to execute
            context: Execution context

        Returns:
            Fill with slippage and fees applied
        """
        # Calculate fill price with slippage
        mid_price = context.price
        slippage_multiplier = self.slippage_bps / 10000.0

        if order.side == OrderSide.BUY:
            # BUY: pay slippage (higher price)
            fill_price = mid_price * (1.0 + slippage_multiplier)
        else:
            # SELL: receive less (lower price)
            fill_price = mid_price * (1.0 - slippage_multiplier)

        # Calculate notional and fee
        notional = abs(order.quantity * fill_price)
        fee = notional * (self.fee_bps / 10000.0)

        # Create fill
        fill = Fill(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            notional=notional,
            fee=fee,
            ts=context.ts,
        )

        return fill
