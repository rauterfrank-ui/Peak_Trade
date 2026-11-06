from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any, List

if TYPE_CHECKING:
    from .data_safety_gate import (
        DataSafetyContext,
        DataSafetyGate,
        DataSafetyResult,
        DataSafetyViolationError,
        DataSourceKind,
        DataUsageContextKind,
    )

__all__ = [
    "DataSafetyContext",
    "DataSafetyGate",
    "DataSafetyResult",
    "DataSafetyViolationError",
    "DataSourceKind",
    "DataUsageContextKind",
]


def __getattr__(name: str) -> Any:
    if name in __all__:
        module = importlib.import_module(".data_safety_gate", __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> List[str]:
    return sorted(list(globals().keys()) + __all__)
