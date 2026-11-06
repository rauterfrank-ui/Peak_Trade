"""
Simulated Venue Adapter (WP0C - Phase 0 Foundation)

Provides deterministic paper/shadow execution simulation.

Design Goals:
- Deterministic: Same inputs → same outputs (no random())
- Realistic: Simulates fills, slippage, fees
- Fast: No network I/O, instant execution
- Idempotent: Same idempotency_key → same result

IMPORTANT: NO live execution. This adapter is for paper/shadow/testnet only.
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional

from src.execution.contracts import Order, OrderSide, OrderType, Fill
from src.execution.orchestrator import ExecutionEvent
from src.execution.venue_adapters.base import VenueAdapterError
from src.execution.venue_adapters.fill_models import (
    FillModel,
    ImmediateFillModel,
    FeeModel,
    FixedFeeModel,
    SlippageModel,
    FixedSlippageModel,
)

logger = logging.getLogger(__name__)


class SimulatedVenueAdapter:
    """
    Simulated venue adapter for deterministic paper/shadow execution.

    Features:
    - Immediate fills (no order book simulation)
    - Deterministic slippage/fees
    - Idempotency tracking (prevents duplicates)
    - No network I/O (instant execution)

    Limitations:
    - No partial fills (always full fill or reject)
    - No order book depth simulation
    - No market impact simulation
    - Simplified limit order logic (immediate fill if price allows)

    Phase 0 Scope:
    - PAPER mode: Simulated fills with realistic slippage/fees
    - SHADOW mode: Same as PAPER (logging only, no state changes)
    - TESTNET mode: Same as PAPER (dry-run)
    """

    def __init__(
        self,
        market_prices: Optional[Dict[str, Decimal]] = None,
        fill_model: Optional[FillModel] = None,
        fee_model: Optional[FeeModel] = None,
        slippage_model: Optional[SlippageModel] = None,
        enable_fills: bool = True,
    ):
        """
        Initialize simulated venue adapter.

        Args:
            market_prices: Market prices per symbol (e.g., {"BTC/EUR": Decimal("50000")})
                          If None, defaults are used.
            fill_model: Fill price calculation model (default: ImmediateFillModel)
            fee_model: Fee calculation model (default: FixedFeeModel(0.1%))
            slippage_model: Slippage calculation model (default: FixedSlippageModel(5bps))
            enable_fills: If False, orders are ACKed but not filled (for testing)
        """
        self.market_prices = market_prices or self._default_market_prices()
        self.fill_model = fill_model or ImmediateFillModel()
        self.fee_model = fee_model or FixedFeeModel(fee_rate=Decimal("0.001"))  # 0.1%
        self.slippage_model = slippage_model or FixedSlippageModel(slippage_bps=5)
        self.enable_fills = enable_fills

        # Idempotency tracking (in-memory cache)
        self._idempotency_cache: Dict[str, ExecutionEvent] = {}

        logger.info(
            f"SimulatedVenueAdapter initialized: "
            f"enable_fills={enable_fills}, "
            f"market_prices={len(self.market_prices)} symbols"
        )

    def execute_order(self, order: Order, idempotency_key: str) -> ExecutionEvent:
        """
        Execute order with deterministic fill simulation.

        Process:
        1. Check idempotency (duplicate → return cached result)
        2. Validate order (symbol, quantity, price)
        3. Calculate fill price (market price + slippage)
        4. Calculate fee
        5. Generate FILL event
        6. Cache result (idempotency)

        Args:
            order: Order to execute
            idempotency_key: Idempotency key (prevents duplicates)

        Returns:
            ExecutionEvent (FILL or REJECT)

        Raises:
            VenueAdapterError: If execution fails
        """
        logger.info(
            f"[SIMULATED ADAPTER] Executing order: "
            f"id={order.client_order_id}, symbol={order.symbol}, "
            f"side={order.side.value}, qty={order.quantity}, "
            f"type={order.order_type.value}"
        )

        # 1. Check idempotency (prevent duplicates)
        if idempotency_key in self._idempotency_cache:
            cached_event = self._idempotency_cache[idempotency_key]
            logger.info(
                f"[SIMULATED ADAPTER] Duplicate idempotency_key={idempotency_key}, "
                f"returning cached result"
            )
            return cached_event

        # 2. Validate order
        validation_error = self._validate_order(order)
        if validation_error:
            event = ExecutionEvent(
                event_type="REJECT",
                order_id=order.client_order_id,
                reject_reason=validation_error,
                timestamp=datetime.utcnow(),
            )
            self._idempotency_cache[idempotency_key] = event
            return event

        # 3. Generate fill (if enabled)
        if not self.enable_fills:
            # ACK only (no fill)
            event = ExecutionEvent(
                event_type="ACK",
                order_id=order.client_order_id,
                exchange_order_id=f"sim_ack_{order.client_order_id}",
                timestamp=datetime.utcnow(),
            )
            self._idempotency_cache[idempotency_key] = event
            return event

        # 4. Calculate fill price
        try:
            market_price = self._get_market_price(order.symbol)
            slippage_bps = self.slippage_model.calculate_slippage_bps(order)
            fill_price = self.fill_model.calculate_fill_price(order, market_price, slippage_bps)
        except Exception as e:
            logger.error(f"[SIMULATED ADAPTER] Fill price calculation failed: {e}")
            event = ExecutionEvent(
                event_type="REJECT",
                order_id=order.client_order_id,
                reject_reason=f"Fill calculation error: {e}",
                timestamp=datetime.utcnow(),
            )
            self._idempotency_cache[idempotency_key] = event
            return event

        # 5. Calculate fee
        fee = self.fee_model.calculate_fee(order.quantity, fill_price)

        # 6. Generate Fill object
        fill = Fill(
            fill_id=f"sim_fill_{order.client_order_id}",
            client_order_id=order.client_order_id,
            exchange_order_id=f"sim_exch_{order.client_order_id}",
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,  # Full fill (no partial fills in Phase 0)
            price=fill_price,
            fee=fee,
            fee_currency=order.symbol.split("/")[1] if "/" in order.symbol else "EUR",
        )

        # 7. Generate FILL event
        event = ExecutionEvent(
            event_type="FILL",
            order_id=order.client_order_id,
            exchange_order_id=f"sim_exch_{order.client_order_id}",
            fill=fill,
            timestamp=datetime.utcnow(),
        )

        # 8. Cache result (idempotency)
        self._idempotency_cache[idempotency_key] = event

        logger.info(
            f"[SIMULATED ADAPTER] Fill generated: "
            f"id={order.client_order_id}, qty={fill.quantity}, "
            f"price={fill.price}, fee={fill.fee}"
        )

        return event

    def _validate_order(self, order: Order) -> Optional[str]:
        """
        Validate order before execution.

        Returns:
            Error message if invalid, None if valid
        """
        # Check symbol exists in market prices
        if order.symbol not in self.market_prices:
            return f"Unknown symbol: {order.symbol}"

        # Check quantity > 0
        if order.quantity <= Decimal(0):
            return f"Invalid quantity: {order.quantity}"

        # Check limit price for LIMIT orders
        if order.order_type == OrderType.LIMIT and order.price is None:
            return "LIMIT order requires price"

        # All checks passed
        return None

    def _get_market_price(self, symbol: str) -> Decimal:
        """
        Get market price for symbol.

        Args:
            symbol: Symbol (e.g., "BTC/EUR")

        Returns:
            Market price (Decimal)

        Raises:
            VenueAdapterError: If symbol not found
        """
        if symbol not in self.market_prices:
            raise VenueAdapterError(f"Unknown symbol: {symbol}")

        return self.market_prices[symbol]

    def set_market_price(self, symbol: str, price: Decimal) -> None:
        """
        Set market price for symbol (for testing).

        Args:
            symbol: Symbol (e.g., "BTC/EUR")
            price: Market price (Decimal)
        """
        self.market_prices[symbol] = price
        logger.debug(f"[SIMULATED ADAPTER] Market price updated: {symbol}={price}")

    @staticmethod
    def _default_market_prices() -> Dict[str, Decimal]:
        """
        Get default market prices for common symbols.

        Returns:
            Dict of symbol → price
        """
        return {
            "BTC/EUR": Decimal("50000.00"),
            "ETH/EUR": Decimal("3000.00"),
            "BTC/USD": Decimal("55000.00"),
            "ETH/USD": Decimal("3300.00"),
            # Add more as needed
        }

    def clear_idempotency_cache(self) -> None:
        """Clear idempotency cache (for testing)."""
        self._idempotency_cache.clear()
        logger.debug("[SIMULATED ADAPTER] Idempotency cache cleared")
