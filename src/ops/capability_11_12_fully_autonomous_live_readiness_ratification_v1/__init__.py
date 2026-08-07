"""CAPABILITY_11_12_FULLY_AUTONOMOUS_LIVE_READINESS_RATIFICATION_V1 package."""

from __future__ import annotations

from src.ops.capability_11_12_fully_autonomous_live_readiness_ratification_v1.constants_v1 import (
    CAPABILITY_ID,
    PACKAGE_MARKER,
)
from src.ops.capability_11_12_fully_autonomous_live_readiness_ratification_v1.verifier_v1 import (
    verify_capability_11_12_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "PACKAGE_MARKER",
    "verify_capability_11_12_v1",
]
