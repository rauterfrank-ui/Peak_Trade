"""
Deterministic fake broker (Finish C1).

NO-LIVE: in-memory only. Designed for unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, Iterable, List, Sequence, Tuple

from src.execution.broker.base import BrokerOrderSnapshot, FillCursor
from src.execution.broker.errors import InvalidOrderError, OrderRejectedError
from src.execution.contracts import Fill, Order, OrderState, OrderType, validate_order


@dataclass
class _StoredOrder:
    order: Order
    broker_order_id: str
    state: OrderState
    created_at: datetime
    updated_at: datetime


class FakeBroker:
    """
    A broker-like fake with:
    - idempotent place_order via (idempotency_key -> broker_order_id)
    - deterministic ordering for list_open_orders
    - deterministic fill stream via monotonically increasing cursor
    """

    def __init__(self) -> None:
        self._seq = 0
        self._orders_by_broker_id: Dict[str, _StoredOrder] = {}
        self._idempotency_to_broker_id: Dict[str, str] = {}
        self._fills: List[Fill] = []

    @property
    def placed_orders_count(self) -> int:
        return len(self._orders_by_broker_id)

    def place_order(self, order: Order, idempotency_key: str) -> str:
        if idempotency_key in self._idempotency_to_broker_id:
            return self._idempotency_to_broker_id[idempotency_key]

        if not validate_order(order):
            raise InvalidOrderError("Invalid order")

        # Minimal rejection behavior for tests: reject STOP/STOP_LIMIT in C1.
        if order.order_type in {OrderType.STOP, OrderType.STOP_LIMIT}:
            raise OrderRejectedError(f"Unsupported order_type in C1: {order.order_type.value}")

        self._seq += 1
        broker_order_id = f"fake_{self._seq:08d}"
        now = datetime.utcnow()

        stored = _StoredOrder(
            order=order,
            broker_order_id=broker_order_id,
            state=OrderState.ACKNOWLEDGED,
            created_at=now,
            updated_at=now,
        )
        self._orders_by_broker_id[broker_order_id] = stored
        self._idempotency_to_broker_id[idempotency_key] = broker_order_id

        # For C1, we can optionally emit an immediate fill for MARKET orders to exercise fill stream.
        if order.order_type == OrderType.MARKET:
            self._emit_full_fill(stored)

        return broker_order_id

    def cancel_order(self, broker_order_id: str) -> OrderState:
        stored = self._orders_by_broker_id.get(broker_order_id)
        if stored is None:
            raise InvalidOrderError(f"Unknown broker_order_id: {broker_order_id}")

        if stored.state.is_terminal():
            return stored.state

        stored.state = OrderState.CANCELLED
        stored.updated_at = datetime.utcnow()
        return stored.state

    def query_order(self, broker_order_id: str) -> BrokerOrderSnapshot:
        stored = self._orders_by_broker_id.get(broker_order_id)
        if stored is None:
            raise InvalidOrderError(f"Unknown broker_order_id: {broker_order_id}")
        return BrokerOrderSnapshot(
            client_order_id=stored.order.client_order_id,
            broker_order_id=stored.broker_order_id,
            state=stored.state,
            created_at=stored.created_at,
            updated_at=stored.updated_at,
        )

    def list_open_orders(self) -> Sequence[BrokerOrderSnapshot]:
        open_states = {OrderState.SUBMITTED, OrderState.ACKNOWLEDGED, OrderState.PARTIALLY_FILLED}
        items = [
            self.query_order(bid)
            for bid, stored in sorted(self._orders_by_broker_id.items(), key=lambda kv: kv[0])
            if stored.state in open_states
        ]
        return items

    def iter_fills(self, since: FillCursor) -> Tuple[FillCursor, Iterable[Fill]]:
        start = max(0, since.position)
        new_position = len(self._fills)
        return (FillCursor(new_position), list(self._fills[start:new_position]))

    # -----------------
    # Internals
    # -----------------

    def _emit_full_fill(self, stored: _StoredOrder) -> None:
        order = stored.order
        # Deterministic fill id derived from broker_order_id.
        fill_id = f"fill_{stored.broker_order_id}"
        now = datetime.utcnow()

        # Deterministic fee: 0 for C1 (fee model comes later).
        fee = Decimal("0")
        fee_ccy = "USD"

        fill = Fill(
            fill_id=fill_id,
            client_order_id=order.client_order_id,
            exchange_order_id=stored.broker_order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=order.price if order.price is not None else Decimal("0"),
            fee=fee,
            fee_currency=fee_ccy,
            filled_at=now,
            metadata={"broker": "fake", "c1": True},
        )
        self._fills.append(fill)

        stored.state = OrderState.FILLED
        stored.updated_at = now
