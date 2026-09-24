"""Explicit orchestration execution modes (no semantic conflation)."""

from __future__ import annotations

from enum import Enum


class F1M9OrchestrationExecutionModeV1(str, Enum):
    BUILD_BIND_ONLY = "BUILD_BIND_ONLY"
    HERMETIC_TERMINAL_TEST = "HERMETIC_TERMINAL_TEST"
    REAL_AUTHORIZED_CAMPAIGN_EXECUTION = "REAL_AUTHORIZED_CAMPAIGN_EXECUTION"


STATUS_REAL_EXECUTION_DISABLED_IN_ENABLEMENT_SLICE: str = (
    "F1_M9_REAL_CAMPAIGN_EXECUTION_DISABLED_IN_ENABLEMENT_SLICE"
)

__all__ = [
    "F1M9OrchestrationExecutionModeV1",
    "STATUS_REAL_EXECUTION_DISABLED_IN_ENABLEMENT_SLICE",
]
