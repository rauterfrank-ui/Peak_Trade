from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .clock_v1 import ClockV1


@dataclass(frozen=True)
class RateLimitBucketV1:
    # token-bucket: capacity tokens, refills at refill_per_sec
    name: str
    capacity: float
    refill_per_sec: float

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("capacity must be > 0")
        if self.refill_per_sec <= 0:
            raise ValueError("refill_per_sec must be > 0")


@dataclass
class _BucketState:
    tokens: float
    last_t: float


class RateLimiterV1:
    """
    Deterministic token-bucket rate limiter (no sleeps).
    Caller decides whether to wait/skip based on returned wait_sec.
    """

    def __init__(self, clock: ClockV1):
        self._clock = clock
        self._buckets: Dict[str, RateLimitBucketV1] = {}
        self._state: Dict[str, _BucketState] = {}

    def add_bucket(self, bucket: RateLimitBucketV1) -> None:
        self._buckets[bucket.name] = bucket
        if bucket.name not in self._state:
            now = self._clock.now_monotonic()
            self._state[bucket.name] = _BucketState(tokens=bucket.capacity, last_t=now)

    def get_bucket(self, name: str) -> RateLimitBucketV1:
        if name not in self._buckets:
            raise KeyError(f"unknown bucket: {name}")
        return self._buckets[name]

    def _refill(self, name: str, now: float) -> None:
        b = self.get_bucket(name)
        st = self._state[name]
        dt = max(0.0, now - st.last_t)
        st.tokens = min(b.capacity, st.tokens + dt * b.refill_per_sec)
        st.last_t = now

    def try_acquire(self, name: str, tokens: float = 1.0) -> Dict[str, float]:
        """
        Returns dict: {"ok":0/1, "wait_sec": float, "tokens_after": float}
        """
        if tokens <= 0:
            raise ValueError("tokens must be > 0")
        if name not in self._state:
            # require explicit add_bucket to avoid implicit config
            raise KeyError(f"bucket not initialized: {name}")

        now = self._clock.now_monotonic()
        self._refill(name, now)
        b = self.get_bucket(name)
        st = self._state[name]

        if st.tokens >= tokens:
            st.tokens -= tokens
            return {"ok": 1.0, "wait_sec": 0.0, "tokens_after": float(st.tokens)}

        deficit = tokens - st.tokens
        wait = deficit / b.refill_per_sec
        return {"ok": 0.0, "wait_sec": float(wait), "tokens_after": float(st.tokens)}

    def peek(self, name: str) -> Dict[str, float]:
        if name not in self._state:
            raise KeyError(f"bucket not initialized: {name}")
        now = self._clock.now_monotonic()
        self._refill(name, now)
        st = self._state[name]
        return {"tokens": float(st.tokens), "t": float(st.last_t)}
