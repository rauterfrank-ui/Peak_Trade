from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import random


@dataclass(frozen=True)
class BackoffPolicyV1:
    base_sec: float = 0.5
    max_sec: float = 10.0
    factor: float = 2.0
    jitter: float = 0.1  # fraction of delay

    def __post_init__(self) -> None:
        if self.base_sec <= 0:
            raise ValueError("base_sec must be > 0")
        if self.max_sec <= 0:
            raise ValueError("max_sec must be > 0")
        if self.factor <= 1.0:
            raise ValueError("factor must be > 1.0")
        if not (0.0 <= self.jitter <= 1.0):
            raise ValueError("jitter must be in [0,1]")

    def delay_for_attempt(self, attempt: int, *, rng: Optional[random.Random] = None) -> float:
        """
        attempt: 0,1,2,...
        deterministic if rng is provided with fixed seed.
        """
        if attempt < 0:
            raise ValueError("attempt must be >= 0")
        raw = self.base_sec * (self.factor**attempt)
        raw = min(raw, self.max_sec)

        if self.jitter == 0.0:
            return float(raw)

        r = rng or random.Random()
        # jitter in [ (1-j), (1+j) ]
        lo = 1.0 - self.jitter
        hi = 1.0 + self.jitter
        return float(raw * (lo + (hi - lo) * r.random()))
