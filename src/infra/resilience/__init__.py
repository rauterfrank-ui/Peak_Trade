"""
Resilience Module for Peak Trade
==================================

Provides circuit breaker, retry logic, rate limiting, and fallback strategies
to improve system stability and handle failures gracefully.

Components:
    - CircuitBreaker: Prevents cascading failures
    - Retry: Exponential backoff retry logic
    - RateLimiter: Token bucket rate limiting
    - Fallback: Fallback strategies for failures
"""

from src.infra.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    circuit_breaker,
)
from src.infra.resilience.retry import (
    RetryPolicy,
    retry_with_backoff,
)
from src.infra.resilience.rate_limiter import (
    RateLimiter,
    rate_limit,
)

__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "circuit_breaker",
    "RetryPolicy",
    "retry_with_backoff",
    "RateLimiter",
    "rate_limit",
]
