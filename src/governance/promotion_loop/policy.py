"""
Auto-apply policies for the Promotion Loop v0.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class AutoApplyBounds:
    """
    Bounds for automatic application of configuration changes.
    """

    min_value: float
    max_value: float
    max_step: float  # max absolute change per update


@dataclass
class AutoApplyPolicy:
    """
    Configuration for live auto-apply behaviour.

    mode:
      - "disabled": no auto-apply at all
      - "manual_only": proposals only, no auto-apply
      - "bounded_auto": proposals + bounded auto-apply
    """

    mode: str = "manual_only"
    leverage_bounds: Optional[AutoApplyBounds] = None
    trigger_delay_bounds: Optional[AutoApplyBounds] = None
    macro_weight_bounds: Optional[AutoApplyBounds] = None

    def is_bounded_auto(self) -> bool:
        """Check if bounded auto-apply is enabled."""
        return self.mode == "bounded_auto"
