"""
Peak_Trade Risk Module
=======================
Position Sizing, Stop-Loss-Management, Risk-Limits.

P0 Guardrails Drill Test: Risk module changes trigger required checks
This comment verifies that src/risk/ changes require proper review and testing.
"""

from .position_sizer import (
    PositionSizer,
    PositionSizerConfig,
    PositionRequest,
    PositionResult,
    calc_position_size,
)
from .limits import RiskLimits, RiskLimitsConfig

__all__ = [
    # Position Sizing
    "PositionSizer",
    "PositionSizerConfig",
    "PositionRequest",
    "PositionResult",
    "calc_position_size",
    # Risk Limits
    "RiskLimits",
    "RiskLimitsConfig",
]
