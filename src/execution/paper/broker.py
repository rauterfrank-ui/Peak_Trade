"""
Paper Broker - WP1B (Phase 1 Shadow Trading)

Simulates order execution with deterministic fills, slippage, and fees.
"""

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import uuid4

from src.execution.contracts import Fill, Order, OrderSide, OrderState, OrderType

logger = logging.getLogger(__name__)


@dataclass
class FillSimulationConfig:
    """
    Configuration for fill simulation.

    Attributes:
        slippage_bps: Slippage in basis points (100 bps = 1%)
        fee_bps: Fee in basis points (maker/taker average)
        fill_delay_ms: Simulated fill delay in milliseconds
        partial_fill_prob: Probability of partial fills (0.0 = always full)
        random_seed: Random seed for deterministic simulation
    """

    slippage_bps: Decimal = Decimal("5")  # 0.05% slippage
    fee_bps: Decimal = Decimal("10")  # 0.10% fee
    fill_delay_ms: int = 100  # 100ms simulated latency
    partial_fill_prob: float = 0.0  # No partial fills by default
    random_seed: Optional[int] = 42  # Deterministic by default

    def __post_init__(self):
        """Validate config."""
        if self.slippage_bps < 0:
            raise ValueError(f"slippage_bps must be >= 0, got {self.slippage_bps}")
        if self.fee_bps < 0:
            raise ValueError(f"fee_bps must be >= 0, got {self.fee_bps}")


class PaperBroker:
    """
    Paper broker with deterministic fill simulation.

    Simulates:
    - Immediate fills for market orders
    - Slippage (configurable)
    - Fees (configurable)
    - Partial fills (optional)

    Usage:
        >>> config = FillSimulationConfig(slippage_bps=Decimal("5"))
        >>> broker = PaperBroker(config)
        >>> order = Order(...)
        >>> fills = broker.submit_order(order, current_price=Decimal("50000"))
    """

    def __init__(self, config: FillSimulationConfig):
        """
        Initialize paper broker.

        Args:
            config: Fill simulation configuration
        """
        self.config = config

        # Initialize RNG for deterministic simulation
        if config.random_seed is not None:
            self._rng = random.Random(config.random_seed)
        else:
            self._rng = random.Random()

        # Stats
        self._orders_submitted = 0
        self._fills_generated = 0
        self._total_fees = Decimal("0")

    def submit_order(
        self,
        order: Order,
        current_price: Decimal,
    ) -> tuple[OrderState, List[Fill]]:
        """
        Submit order and simulate fills.

        Args:
            order: Order to submit
            current_price: Current market price for the symbol

        Returns:
            Tuple of (new_order_state, fills_generated)
        """
        self._orders_submitted += 1

        # Validate order
        if order.quantity <= 0:
            logger.warning(f"Invalid order quantity: {order.quantity}")
            return (OrderState.REJECTED, [])

        # Simulate ACK
        logger.debug(
            f"Paper order submitted: {order.client_order_id} "
            f"{order.side.value} {order.quantity} {order.symbol}"
        )

        # Generate fills based on order type
        if order.order_type == OrderType.MARKET:
            fills = self._simulate_market_order_fill(order, current_price)
        elif order.order_type == OrderType.LIMIT:
            # For Phase 1: Immediate fill at limit price if price is favorable
            fills = self._simulate_limit_order_fill(order, current_price)
        else:
            logger.warning(f"Unsupported order type: {order.order_type}")
            return (OrderState.REJECTED, [])

        # Determine final state
        if not fills:
            return (OrderState.ACKNOWLEDGED, [])

        total_filled = sum(fill.quantity for fill in fills)

        if total_filled >= order.quantity:
            return (OrderState.FILLED, fills)
        elif total_filled > 0:
            return (OrderState.PARTIALLY_FILLED, fills)
        else:
            return (OrderState.ACKNOWLEDGED, [])

    def _simulate_market_order_fill(
        self,
        order: Order,
        current_price: Decimal,
    ) -> List[Fill]:
        """
        Simulate market order fill.

        Args:
            order: Market order
            current_price: Current market price

        Returns:
            List of fills
        """
        # Apply slippage
        fill_price = self._apply_slippage(current_price, order.side)

        # Calculate fee
        notional = fill_price * order.quantity
        fee = self._calculate_fee(notional)

        # Check for partial fill
        if self._should_partial_fill():
            # Partial fill: 50-90% of quantity
            fill_ratio = Decimal(str(self._rng.uniform(0.5, 0.9)))
            fill_qty = order.quantity * fill_ratio
        else:
            # Full fill
            fill_qty = order.quantity

        # Generate fill
        fill = Fill(
            fill_id=str(uuid4()),
            client_order_id=order.client_order_id,
            exchange_order_id=order.exchange_order_id or str(uuid4()),
            symbol=order.symbol,
            side=order.side,
            quantity=fill_qty,
            price=fill_price,
            fee=fee,
            fee_currency="USD",  # Simplified
            filled_at=datetime.utcnow(),
            metadata={
                "simulation": "paper_market",
                "slippage_bps": str(self.config.slippage_bps),
            },
        )

        self._fills_generated += 1
        self._total_fees += fee

        logger.debug(
            f"Paper fill: {fill.fill_id} @ {fill.price} (qty: {fill.quantity}, fee: {fill.fee})"
        )

        return [fill]

    def _simulate_limit_order_fill(
        self,
        order: Order,
        current_price: Decimal,
    ) -> List[Fill]:
        """
        Simulate limit order fill.

        For Phase 1: Simplified logic (immediate fill if price is favorable).

        Args:
            order: Limit order
            current_price: Current market price

        Returns:
            List of fills
        """
        if order.price is None:
            logger.warning("Limit order without price")
            return []

        # Check if limit price is favorable
        should_fill = False
        if order.side == OrderSide.BUY and current_price <= order.price:
            # Buy limit: fill if market price <= limit price
            should_fill = True
        elif order.side == OrderSide.SELL and current_price >= order.price:
            # Sell limit: fill if market price >= limit price
            should_fill = True

        if not should_fill:
            logger.debug(f"Limit order not filled: market={current_price} limit={order.price}")
            return []

        # Fill at limit price (no slippage for limit orders)
        fill_price = order.price

        # Calculate fee
        notional = fill_price * order.quantity
        fee = self._calculate_fee(notional)

        # Generate fill
        fill = Fill(
            fill_id=str(uuid4()),
            client_order_id=order.client_order_id,
            exchange_order_id=order.exchange_order_id or str(uuid4()),
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,  # Full fill for limit
            price=fill_price,
            fee=fee,
            fee_currency="USD",
            filled_at=datetime.utcnow(),
            metadata={
                "simulation": "paper_limit",
                "slippage_bps": "0",  # No slippage for limit
            },
        )

        self._fills_generated += 1
        self._total_fees += fee

        return [fill]

    def _apply_slippage(
        self,
        price: Decimal,
        side: OrderSide,
    ) -> Decimal:
        """
        Apply slippage to price.

        Args:
            price: Base price
            side: Order side

        Returns:
            Price with slippage
        """
        slippage_factor = self.config.slippage_bps / Decimal("10000")

        if side == OrderSide.BUY:
            # Buy: slippage increases price
            return price * (Decimal("1") + slippage_factor)
        else:
            # Sell: slippage decreases price
            return price * (Decimal("1") - slippage_factor)

    def _calculate_fee(self, notional: Decimal) -> Decimal:
        """
        Calculate fee for a trade.

        Args:
            notional: Notional value (price * quantity)

        Returns:
            Fee amount
        """
        fee_factor = self.config.fee_bps / Decimal("10000")
        return notional * fee_factor

    def _should_partial_fill(self) -> bool:
        """
        Determine if order should be partially filled.

        Returns:
            True if partial fill, False for full fill
        """
        return self._rng.random() < self.config.partial_fill_prob

    def get_stats(self) -> dict:
        """Get broker statistics."""
        return {
            "orders_submitted": self._orders_submitted,
            "fills_generated": self._fills_generated,
            "total_fees": str(self._total_fees),
        }
