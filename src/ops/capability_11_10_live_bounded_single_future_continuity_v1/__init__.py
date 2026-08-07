"""CAPABILITY_11_10_LIVE_BOUNDED_SINGLE_FUTURE_CONTINUITY_V1 package."""

from __future__ import annotations

from src.ops.capability_11_10_live_bounded_single_future_continuity_v1.constants_v1 import (
    CAPABILITY_ID,
    PACKAGE_MARKER,
)
from src.ops.capability_11_10_live_bounded_single_future_continuity_v1.verifier_v1 import (
    verify_capability_11_10_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "PACKAGE_MARKER",
    "verify_capability_11_10_v1",
]
