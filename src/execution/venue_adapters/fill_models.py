"""
Fill Models for Simulated Execution (WP0C - Phase 0 Foundation)

Provides deterministic fill/slippage/fee calculation models for paper/shadow execution.

Design Goals:
- Deterministic: Same inputs → same outputs (no random() calls)
- Configurable: Fee rates, slippage, fill logic
- Realistic: Simulates real market conditions (within reason)

IMPORTANT: NO randomness. All calculations must be deterministic.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from src.execution.contracts import Order, OrderType, OrderSide


class FillModel(Protocol):
    """
    Protocol for fill price calculation.

    Implementations must be deterministic (no random()).
    """

    def calculate_fill_price(
        self, order: Order, market_price: Decimal, slippage_bps: int = 0
    ) -> Decimal:
        """
        Calculate fill price for order.

        Args:
            order: Order to fill
            market_price: Current market price (reference price)
            slippage_bps: Slippage in basis points (0 = no slippage)

        Returns:
            Fill price (Decimal)
        """
        ...


class ImmediateFillModel:
    """
    Immediate fill model (deterministic).

    Rules:
    - Market orders: Fill at market_price ± slippage
    - Limit BUY: Fill at min(limit_price, market_price - slippage)
    - Limit SELL: Fill at max(limit_price, market_price + slippage)
    - Slippage: Always applied in unfavorable direction (BUY = higher, SELL = lower)

    Determinism:
    - No randomness, same inputs → same output
    - Slippage is fixed (not random)
    """

    def calculate_fill_price(
        self, order: Order, market_price: Decimal, slippage_bps: int = 0
    ) -> Decimal:
        """Calculate fill price with deterministic slippage."""
        # Calculate slippage (basis points)
        slippage_factor = Decimal(slippage_bps) / Decimal(10000)  # bps to decimal

        if order.order_type == OrderType.MARKET:
            # Market order: apply slippage in unfavorable direction
            if order.side == OrderSide.BUY:
                # BUY: pay more (higher price)
                fill_price = market_price * (Decimal(1) + slippage_factor)
            else:
                # SELL: receive less (lower price)
                fill_price = market_price * (Decimal(1) - slippage_factor)

        elif order.order_type == OrderType.LIMIT:
            # Limit order: fill at best available price (within limit)
            if order.price is None:
                raise ValueError("LIMIT order must have price")

            # Apply slippage to market price
            if order.side == OrderSide.BUY:
                slipped_market_price = market_price * (Decimal(1) + slippage_factor)
                # BUY: fill at min(limit, slipped_market)
                fill_price = min(order.price, slipped_market_price)
            else:
                slipped_market_price = market_price * (Decimal(1) - slippage_factor)
                # SELL: fill at max(limit, slipped_market)
                fill_price = max(order.price, slipped_market_price)

        else:
            # Default: market price with slippage
            if order.side == OrderSide.BUY:
                fill_price = market_price * (Decimal(1) + slippage_factor)
            else:
                fill_price = market_price * (Decimal(1) - slippage_factor)

        # Round to 8 decimals (crypto standard)
        return fill_price.quantize(Decimal("0.00000001"))


class FeeModel(Protocol):
    """
    Protocol for fee calculation.

    Implementations must be deterministic.
    """

    def calculate_fee(self, fill_qty: Decimal, fill_price: Decimal) -> Decimal:
        """
        Calculate fee for fill.

        Args:
            fill_qty: Filled quantity
            fill_price: Fill price

        Returns:
            Fee amount (in quote currency)
        """
        ...


class FixedFeeModel:
    """
    Fixed percentage fee model (deterministic).

    Typical exchange fees:
    - Maker: 0.00% - 0.10%
    - Taker: 0.05% - 0.25%

    Phase 0 default: 0.10% taker fee (conservative)
    """

    def __init__(self, fee_rate: Decimal = Decimal("0.001")):
        """
        Initialize fixed fee model.

        Args:
            fee_rate: Fee rate (decimal, e.g., 0.001 = 0.1%)
        """
        self.fee_rate = fee_rate

    def calculate_fee(self, fill_qty: Decimal, fill_price: Decimal) -> Decimal:
        """Calculate fee (fill_qty * fill_price * fee_rate)."""
        notional = fill_qty * fill_price
        fee = notional * self.fee_rate

        # Round to 8 decimals
        return fee.quantize(Decimal("0.00000001"))


class SlippageModel(Protocol):
    """
    Protocol for slippage calculation.

    Implementations must be deterministic.
    """

    def calculate_slippage_bps(self, order: Order) -> int:
        """
        Calculate slippage in basis points.

        Args:
            order: Order to calculate slippage for

        Returns:
            Slippage in basis points (e.g., 5 = 0.05%)
        """
        ...


class FixedSlippageModel:
    """
    Fixed slippage model (deterministic).

    Typical slippage for liquid crypto pairs:
    - BTC/EUR, ETH/EUR: 1-5 bps (0.01%-0.05%)
    - Mid-cap alts: 5-20 bps
    - Low liquidity: 20-100 bps

    Phase 0 default: 5 bps (conservative for liquid pairs)
    """

    def __init__(self, slippage_bps: int = 5):
        """
        Initialize fixed slippage model.

        Args:
            slippage_bps: Slippage in basis points (e.g., 5 = 0.05%)
        """
        self.slippage_bps = slippage_bps

    def calculate_slippage_bps(self, order: Order) -> int:
        """Return fixed slippage (deterministic)."""
        return self.slippage_bps
