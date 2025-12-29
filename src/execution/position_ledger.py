"""
Position Ledger (WP0A - Phase 0 Execution Core)

Tracks positions derived from fills.
Single source of truth for position state.

Design Goals:
- Position = cumulative fills per symbol
- Realized/Unrealized PnL tracking
- Cash balance tracking
- Invariant checks (position + cash = fills)
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from src.execution.contracts import Fill, OrderSide


# ============================================================================
# Position
# ============================================================================


@dataclass
class Position:
    """
    Position for a symbol.

    Design:
    - quantity: Net position (positive = long, negative = short)
    - avg_entry_price: Volume-weighted average entry price
    - realized_pnl: Realized PnL from closed positions
    - unrealized_pnl: Mark-to-market unrealized PnL
    """

    symbol: str
    quantity: Decimal = Decimal("0")
    avg_entry_price: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    cost_basis: Decimal = Decimal("0")  # Total cost of position

    # Stats
    total_buys: Decimal = Decimal("0")
    total_sells: Decimal = Decimal("0")
    total_fees: Decimal = Decimal("0")

    # Timestamps
    opened_at: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def is_flat(self) -> bool:
        """Check if position is flat (no exposure)"""
        return self.quantity == 0

    def is_long(self) -> bool:
        """Check if position is long"""
        return self.quantity > 0

    def is_short(self) -> bool:
        """Check if position is short"""
        return self.quantity < 0

    def unrealized_pnl(self, mark_price: Decimal) -> Decimal:
        """
        Calculate unrealized PnL at mark price.

        Args:
            mark_price: Current market price

        Returns:
            Unrealized PnL
        """
        if self.is_flat() or self.avg_entry_price == 0:
            return Decimal("0")

        return (mark_price - self.avg_entry_price) * self.quantity

    def to_dict(self) -> Dict:
        """Convert to dict"""
        return {
            "symbol": self.symbol,
            "quantity": str(self.quantity),
            "avg_entry_price": str(self.avg_entry_price),
            "realized_pnl": str(self.realized_pnl),
            "cost_basis": str(self.cost_basis),
            "total_buys": str(self.total_buys),
            "total_sells": str(self.total_sells),
            "total_fees": str(self.total_fees),
            "is_flat": self.is_flat(),
            "is_long": self.is_long(),
            "is_short": self.is_short(),
        }


# ============================================================================
# Position Ledger
# ============================================================================


class PositionLedger:
    """
    Position ledger (single source of truth for positions).

    Features:
    - Track positions per symbol
    - Apply fills to update positions
    - Calculate realized/unrealized PnL
    - Track cash balance
    """

    def __init__(self, initial_cash: Decimal = Decimal("0")):
        """
        Initialize position ledger.

        Args:
            initial_cash: Initial cash balance
        """
        # Positions by symbol
        self._positions: Dict[str, Position] = {}

        # Cash balance
        self._cash = initial_cash
        self._initial_cash = initial_cash

        # Fill history (for reconciliation)
        self._fills: List[Fill] = []

    def apply_fill(self, fill: Fill) -> Position:
        """
        Apply fill to update position.

        Logic:
        - BUY: increase position, decrease cash
        - SELL: decrease position, increase cash
        - Update avg_entry_price using FIFO/weighted average
        - Track realized PnL on position reductions

        Args:
            fill: Fill to apply

        Returns:
            Updated position
        """
        # Get or create position
        if fill.symbol not in self._positions:
            self._positions[fill.symbol] = Position(
                symbol=fill.symbol,
                opened_at=fill.filled_at,
            )

        position = self._positions[fill.symbol]

        # Calculate fill notional (price * quantity)
        fill_notional = fill.price * fill.quantity

        # Apply fill based on side
        if fill.side == OrderSide.BUY:
            # BUY: increase position
            new_quantity = position.quantity + fill.quantity

            if position.quantity == 0:
                # Opening new position
                position.avg_entry_price = fill.price
                position.cost_basis = fill_notional
            elif position.quantity > 0:
                # Adding to long position
                position.cost_basis += fill_notional
                position.avg_entry_price = position.cost_basis / new_quantity
            else:
                # Reducing short position (partial/full cover)
                if new_quantity >= 0:
                    # Full cover or flip to long
                    # Realize PnL from short cover
                    covered_quantity = min(fill.quantity, abs(position.quantity))
                    position.realized_pnl += (
                        position.avg_entry_price - fill.price
                    ) * covered_quantity

                    if new_quantity > 0:
                        # Flip to long
                        position.avg_entry_price = fill.price
                        position.cost_basis = fill.price * new_quantity
                    else:
                        # Flat position
                        position.avg_entry_price = Decimal("0")
                        position.cost_basis = Decimal("0")
                else:
                    # Partial short cover (still short)
                    # Realize PnL proportionally
                    position.realized_pnl += (position.avg_entry_price - fill.price) * fill.quantity
                    position.cost_basis = position.avg_entry_price * new_quantity

            position.quantity = new_quantity
            position.total_buys += fill.quantity

            # Update cash (spend)
            self._cash -= fill_notional + fill.fee

        else:  # OrderSide.SELL
            # SELL: decrease position
            new_quantity = position.quantity - fill.quantity

            if position.quantity == 0:
                # Opening new short position
                position.avg_entry_price = fill.price
                position.cost_basis = fill_notional
            elif position.quantity < 0:
                # Adding to short position
                position.cost_basis += fill_notional
                position.avg_entry_price = position.cost_basis / abs(new_quantity)
            else:
                # Reducing long position (partial/full close)
                if new_quantity <= 0:
                    # Full close or flip to short
                    # Realize PnL from long close
                    closed_quantity = min(fill.quantity, position.quantity)
                    position.realized_pnl += (
                        fill.price - position.avg_entry_price
                    ) * closed_quantity

                    if new_quantity < 0:
                        # Flip to short
                        position.avg_entry_price = fill.price
                        position.cost_basis = fill.price * abs(new_quantity)
                    else:
                        # Flat position
                        position.avg_entry_price = Decimal("0")
                        position.cost_basis = Decimal("0")
                else:
                    # Partial long close (still long)
                    # Realize PnL proportionally
                    position.realized_pnl += (fill.price - position.avg_entry_price) * fill.quantity
                    position.cost_basis = position.avg_entry_price * new_quantity

            position.quantity = new_quantity
            position.total_sells += fill.quantity

            # Update cash (receive)
            self._cash += fill_notional - fill.fee

        # Update fees
        position.total_fees += fill.fee
        position.last_updated = fill.filled_at

        # Store fill
        self._fills.append(fill)

        return position

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Position if exists, None otherwise
        """
        return self._positions.get(symbol)

    def get_all_positions(self) -> List[Position]:
        """Get all positions"""
        return list(self._positions.values())

    def get_active_positions(self) -> List[Position]:
        """Get all non-flat positions"""
        return [pos for pos in self._positions.values() if not pos.is_flat()]

    def get_cash_balance(self) -> Decimal:
        """Get current cash balance"""
        return self._cash

    def get_total_realized_pnl(self) -> Decimal:
        """Get total realized PnL across all positions"""
        return sum(pos.realized_pnl for pos in self._positions.values())

    def get_total_unrealized_pnl(self, mark_prices: Dict[str, Decimal]) -> Decimal:
        """
        Get total unrealized PnL across all positions.

        Args:
            mark_prices: Dict mapping symbol to mark price

        Returns:
            Total unrealized PnL
        """
        total = Decimal("0")
        for symbol, position in self._positions.items():
            if symbol in mark_prices:
                total += position.unrealized_pnl(mark_prices[symbol])
        return total

    def get_total_pnl(self, mark_prices: Dict[str, Decimal]) -> Decimal:
        """
        Get total PnL (realized + unrealized).

        Args:
            mark_prices: Dict mapping symbol to mark price

        Returns:
            Total PnL
        """
        return self.get_total_realized_pnl() + self.get_total_unrealized_pnl(mark_prices)

    def get_equity(self, mark_prices: Dict[str, Decimal]) -> Decimal:
        """
        Get total equity (cash + unrealized PnL).

        Args:
            mark_prices: Dict mapping symbol to mark price

        Returns:
            Total equity
        """
        return self._cash + self.get_total_unrealized_pnl(mark_prices)

    def get_fills(self) -> List[Fill]:
        """Get all fills"""
        return self._fills

    def to_dict(self, mark_prices: Optional[Dict[str, Decimal]] = None) -> Dict:
        """
        Export ledger summary as dict.

        Args:
            mark_prices: Optional mark prices for unrealized PnL

        Returns:
            Dict with ledger summary
        """
        mark_prices = mark_prices or {}

        return {
            "cash": str(self._cash),
            "initial_cash": str(self._initial_cash),
            "total_positions": len(self._positions),
            "active_positions": len(self.get_active_positions()),
            "total_fills": len(self._fills),
            "total_realized_pnl": str(self.get_total_realized_pnl()),
            "total_unrealized_pnl": str(self.get_total_unrealized_pnl(mark_prices)),
            "total_pnl": str(self.get_total_pnl(mark_prices)),
            "equity": str(self.get_equity(mark_prices)),
        }
