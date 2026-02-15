from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Regime(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    NEUTRAL = "NEUTRAL"


@dataclass(frozen=True)
class RegimeDecision:
    regime: Regime
    confidence: float
    reason: str


def regime_switch_v1(*, score: float, neutral_band: float = 0.1) -> RegimeDecision:
    """
    Deterministic stub:
    - score > +neutral_band => UP
    - score < -neutral_band => DOWN
    - else => NEUTRAL
    """
    if neutral_band < 0:
        raise ValueError("neutral_band must be >= 0")
    if score > neutral_band:
        return RegimeDecision(Regime.UP, 0.6, "score>band")
    if score < -neutral_band:
        return RegimeDecision(Regime.DOWN, 0.6, "score<-band")
    return RegimeDecision(Regime.NEUTRAL, 0.5, "within_band")
