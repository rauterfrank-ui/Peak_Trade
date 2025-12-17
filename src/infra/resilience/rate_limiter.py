"""
Rate Limiter
=============

Implements token bucket rate limiting to protect against API overload
and ensure compliance with API rate limits.

Usage:
    from src.infra.resilience import RateLimiter, rate_limit
    
    # As a decorator
    @rate_limit(name="exchange_api", requests_per_second=10)
    def api_call():
        pass
    
    # Direct usage
    limiter = RateLimiter(requests_per_second=10)
    with limiter:
        # Rate-limited operation
        pass
"""

from __future__ import annotations

import functools
import logging
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RateLimiterMetrics:
    """Metrics for rate limiter."""
    
    name: str
    requests_per_second: float
    total_requests: int = 0
    total_throttled: int = 0
    total_wait_time_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "requests_per_second": self.requests_per_second,
            "total_requests": self.total_requests,
            "total_throttled": self.total_throttled,
            "total_wait_time_seconds": self.total_wait_time_seconds,
            "throttle_rate": (
                self.total_throttled / self.total_requests
                if self.total_requests > 0
                else 0.0
            ),
        }


class RateLimiter:
    """
    Token bucket rate limiter.
    
    Limits the rate of operations using the token bucket algorithm.
    Tokens are added at a constant rate, and each operation consumes
    one token. If no tokens available, the operation blocks.
    """
    
    def __init__(
        self,
        requests_per_second: float = 10.0,
        burst_size: Optional[int] = None,
        name: str = "default",
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_second: Maximum requests per second
            burst_size: Maximum burst size (default: 2 * requests_per_second)
            name: Identifier for this limiter
        """
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be > 0")
        
        self.name = name
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size or int(2 * requests_per_second)
        
        # Token bucket state
        self._tokens = float(self.burst_size)
        self._last_update = time.time()
        self._lock = Lock()
        
        # Metrics
        self.metrics = RateLimiterMetrics(
            name=name,
            requests_per_second=requests_per_second,
        )
        
        logger.debug(
            f"RateLimiter '{name}' initialized: "
            f"{requests_per_second} req/s, burst={self.burst_size}"
        )
    
    def _add_tokens(self) -> None:
        """Add tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self._last_update
        
        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.requests_per_second
        self._tokens = min(self._tokens + tokens_to_add, float(self.burst_size))
        self._last_update = now
    
    def acquire(self, tokens: int = 1, block: bool = True) -> bool:
        """
        Acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
            block: Whether to block if tokens not available
            
        Returns:
            True if tokens acquired, False if not available and not blocking
        """
        with self._lock:
            self._add_tokens()
            
            self.metrics.total_requests += 1
            
            if self._tokens >= tokens:
                # Tokens available
                self._tokens -= tokens
                return True
            
            if not block:
                # Not blocking, return False
                return False
            
            # Need to wait for tokens
            wait_time = (tokens - self._tokens) / self.requests_per_second
            self.metrics.total_throttled += 1
            self.metrics.total_wait_time_seconds += wait_time
        
        # Release lock during sleep
        logger.debug(
            f"RateLimiter '{self.name}' throttling for {wait_time:.3f}s"
        )
        time.sleep(wait_time)
        
        # Re-acquire lock and tokens
        with self._lock:
            self._add_tokens()
            self._tokens -= tokens
            return True
    
    def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without blocking.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens acquired, False otherwise
        """
        return self.acquire(tokens=tokens, block=False)
    
    def get_metrics(self) -> RateLimiterMetrics:
        """Get current metrics."""
        with self._lock:
            return self.metrics
    
    def __enter__(self) -> RateLimiter:
        """Context manager entry."""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False  # Don't suppress exceptions


# Global registry of rate limiters
_rate_limiters: Dict[str, RateLimiter] = {}
_registry_lock = Lock()


def get_rate_limiter(
    name: str,
    requests_per_second: float = 10.0,
    burst_size: Optional[int] = None,
) -> RateLimiter:
    """
    Get or create a rate limiter.
    
    Args:
        name: Rate limiter name
        requests_per_second: Maximum requests per second
        burst_size: Maximum burst size
        
    Returns:
        RateLimiter instance
    """
    with _registry_lock:
        if name not in _rate_limiters:
            _rate_limiters[name] = RateLimiter(
                name=name,
                requests_per_second=requests_per_second,
                burst_size=burst_size,
            )
        return _rate_limiters[name]


def rate_limit(
    name: str = "default",
    requests_per_second: float = 10.0,
    burst_size: Optional[int] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to rate-limit a function.
    
    Args:
        name: Rate limiter name (shared across decorated functions)
        requests_per_second: Maximum requests per second
        burst_size: Maximum burst size
        
    Returns:
        Decorated function
        
    Example:
        @rate_limit(name="exchange_api", requests_per_second=10)
        def call_exchange():
            # Rate-limited API call
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        limiter = get_rate_limiter(
            name=name,
            requests_per_second=requests_per_second,
            burst_size=burst_size,
        )
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with limiter:
                return func(*args, **kwargs)
        
        return wrapper
    
    return decorator
