from __future__ import annotations

import random
import pytest

from src.execution.networked.limits.clock_v1 import FakeClockV1
from src.execution.networked.limits.rate_limiter_v1 import RateLimiterV1, RateLimitBucketV1
from src.execution.networked.limits.backoff_v1 import BackoffPolicyV1


def test_rate_limiter_token_bucket_refill_and_wait():
    c = FakeClockV1(t=0.0)
    rl = RateLimiterV1(clock=c)
    rl.add_bucket(RateLimitBucketV1(name="global", capacity=2.0, refill_per_sec=1.0))

    r1 = rl.try_acquire("global", tokens=1.0)
    assert r1["ok"] == 1.0 and r1["wait_sec"] == 0.0

    r2 = rl.try_acquire("global", tokens=1.0)
    assert r2["ok"] == 1.0

    r3 = rl.try_acquire("global", tokens=1.0)
    assert r3["ok"] == 0.0
    assert r3["wait_sec"] == pytest.approx(1.0)

    c.advance(1.0)
    r4 = rl.try_acquire("global", tokens=1.0)
    assert r4["ok"] == 1.0
    assert r4["wait_sec"] == 0.0


def test_rate_limiter_requires_explicit_bucket_init():
    c = FakeClockV1()
    rl = RateLimiterV1(clock=c)
    with pytest.raises(KeyError):
        rl.try_acquire("missing", tokens=1.0)


def test_backoff_no_jitter_is_deterministic():
    p = BackoffPolicyV1(base_sec=0.5, max_sec=10.0, factor=2.0, jitter=0.0)
    assert p.delay_for_attempt(0) == pytest.approx(0.5)
    assert p.delay_for_attempt(1) == pytest.approx(1.0)
    assert p.delay_for_attempt(2) == pytest.approx(2.0)
    assert p.delay_for_attempt(10) == pytest.approx(10.0)


def test_backoff_jitter_deterministic_with_seeded_rng():
    p = BackoffPolicyV1(base_sec=1.0, max_sec=10.0, factor=2.0, jitter=0.1)
    rng = random.Random(123)
    d0 = p.delay_for_attempt(0, rng=rng)
    rng2 = random.Random(123)
    d0b = p.delay_for_attempt(0, rng=rng2)
    assert d0 == d0b
    assert 0.9 <= d0 <= 1.1
