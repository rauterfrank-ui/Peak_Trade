"""
Risk Context Snapshot (WP0B)

Snapshot of system state for risk evaluation.
Built from WP0A ledgers without cyclic imports.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any

from src.execution.contracts import Order, Fill


# ============================================================================
# Risk Context Snapshot
# ============================================================================


@dataclass
class RiskContextSnapshot:
    """
    Snapshot of system state for risk evaluation.

    Design:
    - Built from WP0A ledgers (OrderLedger, PositionLedger, AuditLog)
    - No direct imports of ledgers (avoid cycles)
    - Minimal, focused data (only what policies need)
    - Deterministic (same inputs → same snapshot)
    """

    # Timestamp
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Current operation context
    order: Optional[Order] = None
    fill: Optional[Fill] = None

    # Portfolio state summary
    positions_summary: Dict[str, Decimal] = field(default_factory=dict)  # symbol → quantity
    cash_balance: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")

    # Order state summary
    open_orders_count: int = 0
    active_orders_count: int = 0
    total_orders_count: int = 0

    # Metadata (extensible)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for logging/debugging"""
        d = {
            "timestamp": self.timestamp.isoformat(),
            "cash_balance": str(self.cash_balance),
            "realized_pnl": str(self.realized_pnl),
            "unrealized_pnl": str(self.unrealized_pnl),
            "open_orders_count": self.open_orders_count,
            "active_orders_count": self.active_orders_count,
            "total_orders_count": self.total_orders_count,
            "positions_count": len(self.positions_summary),
        }

        if self.order:
            d["order_id"] = self.order.client_order_id
            d["order_symbol"] = self.order.symbol

        if self.fill:
            d["fill_id"] = self.fill.fill_id

        return d

    def __repr__(self) -> str:
        """Deterministic repr"""
        return (
            f"RiskContextSnapshot("
            f"open_orders={self.open_orders_count}, "
            f"positions={len(self.positions_summary)}, "
            f"cash={self.cash_balance})"
        )


# ============================================================================
# Builder Functions
# ============================================================================


def build_context_snapshot(
    order: Optional[Order] = None,
    fill: Optional[Fill] = None,
    order_ledger=None,  # Type: OrderLedger (avoid import)
    position_ledger=None,  # Type: PositionLedger (avoid import)
    **metadata,
) -> RiskContextSnapshot:
    """
    Build risk context snapshot from ledgers.

    Design:
    - Takes ledger objects as arguments (no imports)
    - Extracts minimal state via public APIs
    - Deterministic (same ledgers → same snapshot)

    Args:
        order: Optional order being evaluated
        fill: Optional fill being evaluated
        order_ledger: Optional OrderLedger instance
        position_ledger: Optional PositionLedger instance
        **metadata: Additional metadata

    Returns:
        RiskContextSnapshot
    """
    snapshot = RiskContextSnapshot(
        order=order,
        fill=fill,
        metadata=metadata,
    )

    # Extract order state from order_ledger (if provided)
    if order_ledger:
        snapshot.total_orders_count = order_ledger.get_order_count()

        # Count active orders (not terminal)
        active_orders = order_ledger.get_active_orders()
        snapshot.active_orders_count = len(active_orders)

        # Count open orders (CREATED/SUBMITTED/ACKNOWLEDGED)
        from src.execution.contracts import OrderState

        open_states = {OrderState.CREATED, OrderState.SUBMITTED, OrderState.ACKNOWLEDGED}
        open_orders = [o for o in order_ledger.get_all_orders() if o.state in open_states]
        snapshot.open_orders_count = len(open_orders)

    # Extract position state from position_ledger (if provided)
    if position_ledger:
        snapshot.cash_balance = position_ledger.get_cash_balance()
        snapshot.realized_pnl = position_ledger.get_total_realized_pnl()

        # Build positions summary
        for position in position_ledger.get_all_positions():
            snapshot.positions_summary[position.symbol] = position.quantity

        # Calculate unrealized PnL (would need mark prices, skip for now)
        # In production: pass mark_prices to build_context_snapshot
        snapshot.unrealized_pnl = Decimal("0")

    return snapshot


def build_empty_snapshot() -> RiskContextSnapshot:
    """Create empty snapshot (for testing/defaults)"""
    return RiskContextSnapshot()
