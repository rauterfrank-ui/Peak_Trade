"""
Order Ledger (WP0A - Phase 0 Execution Core)

Tracks all orders with their full history.
Single source of truth for order state.

Design Goals:
- In-memory storage (future: persistent backend)
- Fast lookups by client_order_id and exchange_order_id
- Append-only history (immutable past)
- Thread-safe (future: locking/transactions)
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from src.execution.contracts import Order, OrderState


# ============================================================================
# Order History Entry
# ============================================================================


@dataclass
class OrderHistoryEntry:
    """Snapshot of order at a point in time"""

    timestamp: datetime
    state: OrderState
    snapshot: Dict
    event: str = ""
    metadata: Dict = field(default_factory=dict)


# ============================================================================
# Order Ledger
# ============================================================================


class OrderLedger:
    """
    In-memory order ledger (single source of truth).

    Features:
    - Track all orders by client_order_id
    - Track by exchange_order_id (after ACK)
    - Order history (append-only)
    - Query by state, symbol, session
    """

    def __init__(self):
        """Initialize empty ledger"""
        # Primary index: client_order_id → Order
        self._orders: Dict[str, Order] = {}

        # Secondary index: exchange_order_id → client_order_id
        self._exchange_to_client: Dict[str, str] = {}

        # Order history: client_order_id → List[OrderHistoryEntry]
        self._history: Dict[str, List[OrderHistoryEntry]] = {}

        # Counters
        self._total_orders = 0

    def add_order(self, order: Order) -> bool:
        """
        Add new order to ledger.

        Args:
            order: Order to add

        Returns:
            True if added, False if already exists
        """
        if order.client_order_id in self._orders:
            return False  # Already exists (idempotent)

        self._orders[order.client_order_id] = order
        self._history[order.client_order_id] = []
        self._total_orders += 1

        # Add initial history entry
        self._add_history_entry(
            order=order,
            event="ORDER_CREATED",
        )

        return True

    def update_order(self, order: Order, event: str = "ORDER_UPDATED") -> bool:
        """
        Update existing order.

        Args:
            order: Updated order
            event: Event type for history

        Returns:
            True if updated, False if not found
        """
        if order.client_order_id not in self._orders:
            return False

        self._orders[order.client_order_id] = order

        # Update exchange_order_id index if set
        if order.exchange_order_id:
            self._exchange_to_client[order.exchange_order_id] = order.client_order_id

        # Add history entry
        self._add_history_entry(order=order, event=event)

        return True

    def get_order(self, client_order_id: str) -> Optional[Order]:
        """
        Get order by client_order_id.

        Args:
            client_order_id: Client order ID

        Returns:
            Order if found, None otherwise
        """
        return self._orders.get(client_order_id)

    def get_order_by_exchange_id(self, exchange_order_id: str) -> Optional[Order]:
        """
        Get order by exchange_order_id.

        Args:
            exchange_order_id: Exchange order ID

        Returns:
            Order if found, None otherwise
        """
        client_id = self._exchange_to_client.get(exchange_order_id)
        if client_id:
            return self._orders.get(client_id)
        return None

    def get_order_history(self, client_order_id: str) -> List[OrderHistoryEntry]:
        """
        Get full history of an order.

        Args:
            client_order_id: Client order ID

        Returns:
            List of history entries (chronological)
        """
        return self._history.get(client_order_id, [])

    def get_orders_by_state(self, state: OrderState) -> List[Order]:
        """
        Get all orders in a specific state.

        Args:
            state: Order state

        Returns:
            List of orders
        """
        return [order for order in self._orders.values() if order.state == state]

    def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """
        Get all orders for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            List of orders
        """
        return [order for order in self._orders.values() if order.symbol == symbol]

    def get_active_orders(self) -> List[Order]:
        """
        Get all active orders (not terminal).

        Returns:
            List of active orders
        """
        return [order for order in self._orders.values() if order.state.is_active()]

    def get_all_orders(self) -> List[Order]:
        """
        Get all orders.

        Returns:
            List of all orders
        """
        return list(self._orders.values())

    def get_order_count(self) -> int:
        """Get total number of orders"""
        return self._total_orders

    def get_state_counts(self) -> Dict[OrderState, int]:
        """
        Get count of orders by state.

        Returns:
            Dict mapping state to count
        """
        counts: Dict[OrderState, int] = {}
        for order in self._orders.values():
            counts[order.state] = counts.get(order.state, 0) + 1
        return counts

    def _add_history_entry(self, order: Order, event: str) -> None:
        """
        Internal: Add history entry for order.

        Args:
            order: Order
            event: Event type
        """
        if order.client_order_id not in self._history:
            self._history[order.client_order_id] = []

        entry = OrderHistoryEntry(
            timestamp=datetime.utcnow(),
            state=order.state,
            snapshot=order.to_dict(),
            event=event,
        )

        self._history[order.client_order_id].append(entry)

    def to_dict(self) -> Dict:
        """
        Export ledger summary as dict.

        Returns:
            Dict with ledger statistics
        """
        return {
            "total_orders": self._total_orders,
            "active_orders": len(self.get_active_orders()),
            "state_counts": {state.value: count for state, count in self.get_state_counts().items()},
        }
