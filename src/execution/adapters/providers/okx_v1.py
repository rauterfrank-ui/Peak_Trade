"""OKX adapter — v1 (MOCKS ONLY)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from src.execution.adapters.base_v1 import (
    AdapterCapabilitiesV1,
    ExecutionAdapterV1,
    OrderIntentV1,
    OrderResultV1,
)


@dataclass(frozen=True)
class OKXAdapterConfigV1:
    """Mocks-only: no keys, no network."""

    name: str = "okx_v1_mock"


class OKXExecutionAdapterV1(ExecutionAdapterV1):
    """OKX execution adapter — v1 (MOCKS ONLY). Deterministic, offline."""

    def __init__(self, cfg: Optional[OKXAdapterConfigV1] = None) -> None:
        self._cfg = cfg or OKXAdapterConfigV1()
        self._orders: Dict[str, OrderIntentV1] = {}
        self._seq: int = 0

    def capabilities(self) -> AdapterCapabilitiesV1:
        return AdapterCapabilitiesV1(
            name="okx",
            markets=["spot", "perp"],
            order_types=["market", "limit", "stop"],
            supports_post_only=True,
            supports_reduce_only=True,
            supports_batch_cancel=True,
            supports_cancel_all=True,
            supports_ws_orders=False,
            supports_ws_fills=False,
        )

    def place_order(self, intent: OrderIntentV1) -> OrderResultV1:
        self._seq += 1
        oid = f"okx_mock_{self._seq}"
        self._orders[oid] = intent
        return OrderResultV1(
            ok=True,
            adapter="okx",
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
