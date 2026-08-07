"""CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_EVIDENCE_V1 package."""

from __future__ import annotations

from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.constants_v1 import (
    CAPABILITY_ID,
    PACKAGE_MARKER,
)
from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.verifier_v1 import (
    verify_capability_11_6_v1,
)

__all__ = [
    "CAPABILITY_ID",
    "PACKAGE_MARKER",
    "verify_capability_11_6_v1",
]
