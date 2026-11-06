from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Protocol

MarketType = Literal["spot", "margin", "perp"]
OrderType = Literal["market", "limit", "stop", "stop_limit", "take_profit"]
TimeInForce = Literal["gtc", "ioc", "fok"]


@dataclass(frozen=True)
class AdapterCapabilitiesV1:
    name: str
    markets: List[MarketType]
    order_types: List[OrderType]
    supports_post_only: bool
    supports_reduce_only: bool
    supports_batch_cancel: bool
    supports_cancel_all: bool
    supports_ws_orders: bool
    supports_ws_fills: bool


@dataclass(frozen=True)
class OrderIntentV1:
    symbol: str
    side: Literal["buy", "sell"]
    qty: float
    order_type: OrderType
    price: Optional[float] = None
    tif: TimeInForce = "gtc"
    post_only: bool = False
    reduce_only: bool = False
    client_id: Optional[str] = None
    meta: Optional[Dict[str, str]] = None


@dataclass(frozen=True)
class OrderResultV1:
    ok: bool
    adapter: str
    order_id: Optional[str]
    client_id: Optional[str]
    message: str


class ExecutionAdapterV1(Protocol):
    def capabilities(self) -> AdapterCapabilitiesV1: ...

    def place_order(self, intent: OrderIntentV1) -> OrderResultV1: ...

    def cancel_all(self, symbol: Optional[str] = None) -> int: ...

    def batch_cancel(self, order_ids: List[str]) -> int: ...
