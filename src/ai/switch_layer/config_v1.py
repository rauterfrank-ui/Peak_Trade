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

    # ---- Routing allowlist (deny-by-default) ----
    # Consumed by routing layer (P56) for deterministic strategy selection by regime.
    # Does NOT enable AI model calls; AI remains gated by P49/P50.
    allow_bull_strategies: tuple[str, ...] = ()
    allow_bear_strategies: tuple[str, ...] = ()
