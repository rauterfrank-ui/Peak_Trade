from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .base_v1 import AdapterCapabilitiesV1, ExecutionAdapterV1, OrderIntentV1, OrderResultV1


@dataclass
class MockExecutionAdapterV1(ExecutionAdapterV1):
    _caps: AdapterCapabilitiesV1
    _orders: Dict[str, OrderIntentV1] = field(default_factory=dict)
    _seq: int = 0

    def capabilities(self) -> AdapterCapabilitiesV1:
        return self._caps

    def place_order(self, intent: OrderIntentV1) -> OrderResultV1:
        self._seq += 1
        oid = f"mock_{self._caps.name}_{self._seq}"
        self._orders[oid] = intent
        return OrderResultV1(
            ok=True,
            adapter=self._caps.name,
            order_id=oid,
            client_id=intent.client_id,
            message="mock_order_accepted",
        )

    def cancel_all(self, symbol: Optional[str] = None) -> int:
        if symbol is None:
            n = len(self._orders)
            self._orders.clear()
            return n
        to_del = [oid for oid, it in self._orders.items() if it.symbol == symbol]
        for oid in to_del:
            del self._orders[oid]
        return len(to_del)

    def batch_cancel(self, order_ids: List[str]) -> int:
        n = 0
        for oid in order_ids:
            if oid in self._orders:
                del self._orders[oid]
                n += 1
        return n
