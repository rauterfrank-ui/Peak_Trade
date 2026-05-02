"""Read-only Market Depth / Orderbook readmodel v0.

This package is intentionally pure/offline for v0:
- no provider calls
- no network
- no trading-side handles
- no dashboard polling
"""

from .builder import (
    MarketDepthReadmodelError,
    build_market_depth_readmodel_v0,
    to_json_dict,
)

__all__ = [
    "MarketDepthReadmodelError",
    "build_market_depth_readmodel_v0",
    "to_json_dict",
]
