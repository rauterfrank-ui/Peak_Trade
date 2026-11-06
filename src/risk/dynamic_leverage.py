from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class DynamicLeverageConfig:
    min_leverage: float = 1.0
    max_leverage: float = 50.0
    gamma: float = 2.0  # >= 1.0


def _is_finite(x: float) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(float(x))


def compute_dynamic_leverage(*, strength: float, cfg: DynamicLeverageConfig) -> float:
    """
    Deterministic leverage sizing contract.
    strength: normalized in [0, 1]
    leverage = min + (max - min) * strength**gamma
    Hard-capped to [min, max].

    Raises ValueError on invalid inputs to fail-closed.
    """
    if not _is_finite(strength):
        raise ValueError("strength must be finite")
    if (
        not _is_finite(cfg.min_leverage)
        or not _is_finite(cfg.max_leverage)
        or not _is_finite(cfg.gamma)
    ):
        raise ValueError("config values must be finite")

    min_lv = float(cfg.min_leverage)
    max_lv = float(cfg.max_leverage)
    gamma = float(cfg.gamma)

    if min_lv < 0.0:
        raise ValueError("min_leverage must be >= 0")
    if max_lv < min_lv:
        raise ValueError("max_leverage must be >= min_leverage")
    if gamma < 1.0:
        raise ValueError("gamma must be >= 1")

    s = float(strength)
    # clamp to [0,1] conservatively (do not allow >1 to imply >cap)
    if s < 0.0:
        s = 0.0
    if s > 1.0:
        s = 1.0

    lv = min_lv + (max_lv - min_lv) * (s**gamma)

    # hard clamp (defense in depth)
    if lv < min_lv:
        lv = min_lv
    if lv > max_lv:
        lv = max_lv

    return float(lv)
