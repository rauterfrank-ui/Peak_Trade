from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class MarketRegimeV1(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class SwitchDecisionV1:
    regime: MarketRegimeV1
    confidence: float  # 0..1
    evidence: Dict[str, Any]
