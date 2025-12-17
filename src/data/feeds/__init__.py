from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any, List

if TYPE_CHECKING:
    from .offline_realtime_feed import (
        OfflineRealtimeFeed,
        OfflineRealtimeFeedConfig,
        RegimeConfig,
        SyntheticTick,
    )

__all__ = [
    "OfflineRealtimeFeed",
    "OfflineRealtimeFeedConfig",
    "RegimeConfig",
    "SyntheticTick",
]


def __getattr__(name: str) -> Any:
    if name in __all__:
        module = importlib.import_module(".offline_realtime_feed", __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)
