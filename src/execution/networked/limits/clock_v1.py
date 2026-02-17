from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
import time


class ClockV1(Protocol):
    def now_monotonic(self) -> float: ...


class MonotonicClockV1:
    def now_monotonic(self) -> float:
        return time.monotonic()


@dataclass
class FakeClockV1:
    t: float = 0.0

    def now_monotonic(self) -> float:
        return float(self.t)

    def advance(self, dt: float) -> None:
        if dt < 0:
            raise ValueError("dt must be >= 0")
        self.t += float(dt)
