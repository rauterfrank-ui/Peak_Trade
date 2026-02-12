"""P26 adapter types — minimal order representation for execution integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

Side = str  # "BUY"|"SELL"
OrderType = str  # "MARKET"|"LIMIT"|"STOP_MARKET"


@dataclass(frozen=True)
class AdapterOrder:
    id: str
    symbol: str
    side: Side
    order_type: OrderType
    qty: float
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
