from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SwitchLayerConfigV1:
    # Window lengths
    fast_window: int = 20
    slow_window: int = 50

    # Thresholds (returns-based)
    bull_threshold: float = 0.002  # e.g. +0.2% avg return
    bear_threshold: float = -0.002  # e.g. -0.2% avg return

    # Confidence shaping
    min_confidence: float = 0.55
    max_confidence: float = 0.95

    # Safety
    require_min_samples: int = 60
