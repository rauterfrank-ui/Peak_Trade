# P133 — Execution Networked Rate Limits & Backoff v1 (networkless)

Scope:
- Pure-python, deterministic primitives for rate limiting + exponential backoff.
- NO networking, NO sleep; caller decides how/when to wait.

Artifacts:
- src/execution/networked/limits/rate_limiter_v1.py
- src/execution/networked/limits/backoff_v1.py
- src/execution/networked/limits/clock_v1.py

Notes:
- RateLimiterV1 is token-bucket per named bucket. `try_acquire()` returns ok/wait_sec.
- BackoffPolicyV1 supports deterministic jitter via injected RNG.
