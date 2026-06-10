"""Read-only Market Trades / Tape readmodel v0.

This package is intentionally pure/offline for v0:
- no provider calls
- no network
- no trading-side handles
- no dashboard polling
"""

from .builder import (
    AUTHORITY_BOUNDARY,
    MarketTapeReadmodelError,
    build_market_tape_readmodel_v0,
    to_json_dict,
)
from .gate import (
    ENV_BUNDLE_ROOT,
    ENV_ENABLED,
    enabled_explicitly_on,
    resolve_market_tape_readmodel_payload_v0,
    resolved_bundle_root_or_none,
)

__all__ = [
    "AUTHORITY_BOUNDARY",
    "ENV_BUNDLE_ROOT",
    "ENV_ENABLED",
    "MarketTapeReadmodelError",
    "build_market_tape_readmodel_v0",
    "enabled_explicitly_on",
    "resolve_market_tape_readmodel_payload_v0",
    "resolved_bundle_root_or_none",
    "to_json_dict",
]
