"""
P23 ExecutionModelV1 — Deterministic Fill Model for Backtests.

Provides deterministic order → fill transformation with:
- market, limit, stop (stop-market) order types
- configurable fees and slippage
- reproducible results under fixed config

IMPORTANT: No randomness. All calculations are deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from src.execution.contracts import Fill, Order, OrderSide, OrderType
from src.execution.p23.config import ExecutionModelP23Config


@dataclass
class MarketSnapshot:
    """
    OHLCV bar or mid-price snapshot for fill evaluation.

    Attributes:
        open: Bar open price.
        high: Bar high price.
        low: Bar low price.
        close: Bar close price (used as mid if no separate mid).
        ts: Timestamp of snapshot.
    """

    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def mid(self) -> Decimal:
        """Mid price (close for bar-based evaluation)."""
        return self.close


class ExecutionModelV1:
    """
    Deterministic execution model v1.

    Fill rules:
    - MARKET: fill at mid ± slippage (BUY pays more, SELL receives less)
    - LIMIT: fill if price crosses limit within bar; fill at limit (or better)
    - STOP (stop-market): trigger if price crosses stop; then market fill

    All fills have fees applied (taker for market/stop, maker for limit when applicable).
    """

    def __init__(self, config: Optional[ExecutionModelP23Config] = None) -> None:
        self.config = config or ExecutionModelP23Config()

    def apply(
        self,
        order: Order,
        snapshot: MarketSnapshot,
        fill_id_prefix: str = "fill",
    ) -> List[Fill]:
        """
        Apply order against market snapshot → list of fills.

        Deterministic: same (order, snapshot, config) → same fills.

        Args:
            order: Order to evaluate.
            snapshot: Market snapshot (OHLCV bar).
            fill_id_prefix: Prefix for generated fill IDs.

        Returns:
            List of fills (0 or 1 for v1; no partial fills).
        """
        if not self.config.enabled:
            return []

        fills: List[Fill] = []

        if order.order_type == OrderType.MARKET:
            fills = self._fill_market(order, snapshot, fill_id_prefix)
        elif order.order_type == OrderType.LIMIT:
            fills = self._fill_limit(order, snapshot, fill_id_prefix)
        elif order.order_type == OrderType.STOP and self.config.stop_market_enabled:
            fills = self._fill_stop_market(order, snapshot, fill_id_prefix)
        # STOP_LIMIT not in v1 scope

        return fills

    def _fill_market(
        self,
        order: Order,
        snapshot: MarketSnapshot,
        fill_id_prefix: str,
    ) -> List[Fill]:
        """Market order: fill at mid ± slippage."""
        fill_price = self._apply_slippage(order.side, snapshot.mid)
        return self._make_fill(
            order=order,
            fill_price=fill_price,
            snapshot=snapshot,
            fill_id_prefix=fill_id_prefix,
            is_taker=True,
        )

    def _fill_limit(
        self,
        order: Order,
        snapshot: MarketSnapshot,
        fill_id_prefix: str,
    ) -> List[Fill]:
        """Limit order: fill if price crosses limit within bar."""
        if order.price is None:
            return []

        crosses = self._limit_crosses(order, snapshot)
        if not crosses:
            return []

        # Fill at limit (or better) deterministically
        fill_price = order.price
        return self._make_fill(
            order=order,
            fill_price=fill_price,
            snapshot=snapshot,
            fill_id_prefix=fill_id_prefix,
            is_taker=False,
        )

    def _limit_crosses(self, order: Order, snapshot: MarketSnapshot) -> bool:
        """Check if bar crosses limit (BUY: low <= limit; SELL: high >= limit)."""
        limit = order.price
        if limit is None:
            return False
        if order.side == OrderSide.BUY:
            return snapshot.low <= limit
        else:
            return snapshot.high >= limit

    def _fill_stop_market(
        self,
        order: Order,
        snapshot: MarketSnapshot,
        fill_id_prefix: str,
    ) -> List[Fill]:
        """Stop-market: trigger if price crosses stop; then market fill."""
        if order.price is None:
            return []

        triggered = self._stop_triggered(order, snapshot)
        if not triggered:
            return []

        # After trigger: market fill
        fill_price = self._apply_slippage(order.side, snapshot.mid)
        return self._make_fill(
            order=order,
            fill_price=fill_price,
            snapshot=snapshot,
            fill_id_prefix=fill_id_prefix,
            is_taker=True,
        )

    def _stop_triggered(self, order: Order, snapshot: MarketSnapshot) -> bool:
        """Check if stop is triggered (BUY: high >= stop; SELL: low <= stop)."""
        stop = order.price
        if stop is None:
            return False
        if order.side == OrderSide.BUY:
            return snapshot.high >= stop
        else:
            return snapshot.low <= stop

    def _apply_slippage(self, side: OrderSide, mid: Decimal) -> Decimal:
        """Apply slippage in unfavorable direction."""
        bps = Decimal(self.config.slippage_bps) / Decimal(10000)
        if side == OrderSide.BUY:
            return (mid * (Decimal(1) + bps)).quantize(Decimal("0.00000001"))
        else:
            return (mid * (Decimal(1) - bps)).quantize(Decimal("0.00000001"))

    def _compute_fee(
        self,
        fill_qty: Decimal,
        fill_price: Decimal,
        is_taker: bool,
    ) -> Decimal:
        """Compute fee from notional."""
        bps = self.config.taker_bps if is_taker else self.config.maker_bps
        notional = fill_qty * fill_price
        fee = notional * (Decimal(bps) / Decimal(10000))
        return fee.quantize(Decimal("0.00000001"))

    def _make_fill(
        self,
        order: Order,
        fill_price: Decimal,
        snapshot: MarketSnapshot,
        fill_id_prefix: str,
        is_taker: bool,
    ) -> List[Fill]:
        """Create single fill with fee."""
        fee = self._compute_fee(order.quantity, fill_price, is_taker)
        fill_id = f"{fill_id_prefix}_{order.client_order_id}_{snapshot.ts.timestamp():.0f}"

        return [
            Fill(
                fill_id=fill_id,
                client_order_id=order.client_order_id,
                exchange_order_id=order.exchange_order_id or order.client_order_id,
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                price=fill_price,
                fee=fee,
                fee_currency="USD",
                filled_at=snapshot.ts,
                metadata={
                    "slippage_bps": self.config.slippage_bps,
                    "reason": "p23_execution_model_v1",
                },
            )
        ]
