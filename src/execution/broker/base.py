"""
Broker base protocol + stable broker-layer types (Finish C1).

This layer is separate from `venue_adapters`:
- `venue_adapters` execute a single order and emit an ExecutionEvent.
- `broker` models broker-style commands (place/cancel/query/list) and a fill stream.

Scope: mock/fake only, NO-LIVE.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Protocol, Sequence

from src.execution.contracts import Fill, Order, OrderState


@dataclass(frozen=True)
class BrokerOrderSnapshot:
    """Minimal order snapshot returned by broker queries."""

    client_order_id: str
    broker_order_id: str
    state: OrderState
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class FillCursor:
    """
    Cursor for deterministic fill iteration.

    The fake broker uses a monotonically increasing integer cursor.
    """

    position: int = 0


class Broker(Protocol):
    """
    Minimal broker contract (Finish C1).

    Requirements:
    - Deterministic behavior in tests (no random, no real time dependency unless injected)
    - NO external I/O (no network)
    - Idempotency: same idempotency_key should not duplicate side effects
    """

    def place_order(self, order: Order, idempotency_key: str) -> str:
        """Place an order and return broker_order_id."""

    def cancel_order(self, broker_order_id: str) -> OrderState:
        """Cancel an order (best-effort) and return resulting state."""

    def query_order(self, broker_order_id: str) -> BrokerOrderSnapshot:
        """Return a snapshot for an order id."""

    def list_open_orders(self) -> Sequence[BrokerOrderSnapshot]:
        """Return open orders (deterministic ordering)."""

    def iter_fills(self, since: FillCursor) -> tuple[FillCursor, Iterable[Fill]]:
        """Return (new_cursor, fills) since cursor."""
