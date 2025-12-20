"""
Peak_Trade Rate Limiter Module
==============================
Thread-safe rate limiting using Token Bucket algorithm.

Supports:
- Multiple rate limits per endpoint/service
- Thread-safe for concurrent requests
- Automatic token replenishment
- Rate limit event logging

Usage:
    from src.core.rate_limiter import RateLimiter
    
    limiter = RateLimiter(max_requests=100, window_seconds=60)
    
    if limiter.acquire("api_call"):
        # Proceed with request
        make_api_call()
    else:
        # Rate limit exceeded
        raise RateLimitError("Too many requests")
"""

import logging
import threading
import time
from typing import Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    """Get current UTC time in a timezone-aware manner."""
    if hasattr(datetime, 'UTC'):
        return datetime.now(datetime.UTC)
    else:
        return datetime.utcnow()


@dataclass
class RateLimitConfig:
    """Configuration for a rate limiter."""
    max_requests: int  # Maximum requests allowed
    window_seconds: float  # Time window in seconds
    name: str = "default"  # Name/identifier for this limiter


@dataclass
class TokenBucket:
    """
    Token Bucket implementation for rate limiting.
    
    The token bucket algorithm maintains a bucket of tokens that are
    consumed with each request. Tokens are replenished at a fixed rate.
    
    Args:
        capacity: Maximum number of tokens (max burst size)
        refill_rate: Tokens added per second
        name: Optional name for logging
    """
    capacity: int
    refill_rate: float
    name: str = "bucket"
    
    # Mutable state
    tokens: float = field(init=False)
    last_refill: float = field(init=False)
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    
    def __post_init__(self):
        """Initialize bucket with full tokens."""
        self.tokens = float(self.capacity)
        self.last_refill = time.time()
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on elapsed time
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now
    
    def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire (default: 1)
            
        Returns:
            True if tokens were acquired, False if not enough tokens available
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            else:
                return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """
        Calculate time to wait until tokens are available.
        
        Args:
            tokens: Number of tokens needed
            
        Returns:
            Seconds to wait (0 if tokens available now)
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                return 0.0
            
            tokens_needed = tokens - self.tokens
            return tokens_needed / self.refill_rate
    
    def get_stats(self) -> Dict[str, float]:
        """
        Get current bucket statistics.
        
        Returns:
            Dictionary with current tokens and capacity
        """
        with self.lock:
            self._refill()
            return {
                "tokens": self.tokens,
                "capacity": self.capacity,
                "utilization": 1.0 - (self.tokens / self.capacity)
            }


class RateLimiter:
    """
    Rate limiter with support for multiple endpoints/services.
    
    Uses Token Bucket algorithm for smooth rate limiting with burst support.
    Thread-safe for concurrent access.
    
    Args:
        max_requests: Maximum requests per window (default: 100)
        window_seconds: Time window in seconds (default: 60)
        name: Optional name for this limiter
        
    Example:
        limiter = RateLimiter(max_requests=100, window_seconds=60)
        
        if limiter.acquire("fetch_data"):
            # Make request
            fetch_data()
        else:
            # Rate limited
            logger.warning("Rate limit exceeded")
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: float = 60.0,
        name: str = "global"
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.name = name
        
        # Calculate refill rate (requests per second)
        self.refill_rate = max_requests / window_seconds
        
        # Create main token bucket
        self.bucket = TokenBucket(
            capacity=max_requests,
            refill_rate=self.refill_rate,
            name=name
        )
        
        # Per-endpoint buckets
        self.endpoints: Dict[str, TokenBucket] = {}
        self.endpoints_lock = threading.Lock()
        
        # Statistics
        self.stats_lock = threading.Lock()
        self.total_requests = 0
        self.rejected_requests = 0
        self.last_rejection_time: Optional[float] = None
        
        logger.info(
            f"RateLimiter '{name}' initialized: "
            f"{max_requests} requests per {window_seconds}s "
            f"({self.refill_rate:.2f} req/s)"
        )
    
    def add_endpoint(
        self,
        endpoint: str,
        max_requests: Optional[int] = None,
        window_seconds: Optional[float] = None
    ) -> None:
        """
        Add a specific rate limit for an endpoint.
        
        Args:
            endpoint: Endpoint identifier
            max_requests: Max requests for this endpoint (default: global limit)
            window_seconds: Time window (default: global window)
        """
        max_req = max_requests or self.max_requests
        window = window_seconds or self.window_seconds
        refill = max_req / window
        
        with self.endpoints_lock:
            self.endpoints[endpoint] = TokenBucket(
                capacity=max_req,
                refill_rate=refill,
                name=f"{self.name}:{endpoint}"
            )
        
        logger.info(
            f"RateLimiter '{self.name}' added endpoint '{endpoint}': "
            f"{max_req} requests per {window}s"
        )
    
    def acquire(self, endpoint: Optional[str] = None, tokens: int = 1) -> bool:
        """
        Try to acquire permission for a request.
        
        Args:
            endpoint: Optional endpoint identifier
            tokens: Number of tokens to acquire (default: 1)
            
        Returns:
            True if request allowed, False if rate limited
        """
        with self.stats_lock:
            self.total_requests += 1
        
        # Check global limit
        if not self.bucket.acquire(tokens):
            self._record_rejection(endpoint)
            logger.warning(
                f"RateLimiter '{self.name}' global limit exceeded"
                f"{f' for endpoint {endpoint}' if endpoint else ''}"
            )
            return False
        
        # Check endpoint-specific limit if applicable
        if endpoint:
            with self.endpoints_lock:
                endpoint_bucket = self.endpoints.get(endpoint)
            
            if endpoint_bucket:
                if not endpoint_bucket.acquire(tokens):
                    # Return the global token since endpoint limit exceeded
                    self.bucket.tokens += tokens
                    self._record_rejection(endpoint)
                    logger.warning(
                        f"RateLimiter '{self.name}' endpoint '{endpoint}' limit exceeded"
                    )
                    return False
        
        return True
    
    def _record_rejection(self, endpoint: Optional[str]) -> None:
        """Record a rejected request."""
        with self.stats_lock:
            self.rejected_requests += 1
            self.last_rejection_time = time.time()
    
    def get_wait_time(self, endpoint: Optional[str] = None, tokens: int = 1) -> float:
        """
        Get wait time until tokens are available.
        
        Args:
            endpoint: Optional endpoint identifier
            tokens: Number of tokens needed
            
        Returns:
            Seconds to wait (0 if available now)
        """
        wait_time = self.bucket.get_wait_time(tokens)
        
        if endpoint:
            with self.endpoints_lock:
                endpoint_bucket = self.endpoints.get(endpoint)
            
            if endpoint_bucket:
                endpoint_wait = endpoint_bucket.get_wait_time(tokens)
                wait_time = max(wait_time, endpoint_wait)
        
        return wait_time
    
    def get_stats(self, endpoint: Optional[str] = None) -> Dict[str, any]:
        """
        Get rate limiter statistics.
        
        Args:
            endpoint: Optional endpoint to get stats for
            
        Returns:
            Dictionary with statistics
        """
        with self.stats_lock:
            stats = {
                "name": self.name,
                "total_requests": self.total_requests,
                "rejected_requests": self.rejected_requests,
                "rejection_rate": (
                    self.rejected_requests / self.total_requests
                    if self.total_requests > 0
                    else 0.0
                ),
                "last_rejection_time": (
                    datetime.fromtimestamp(self.last_rejection_time).isoformat()
                    if self.last_rejection_time
                    else None
                ),
                "global_bucket": self.bucket.get_stats()
            }
        
        if endpoint:
            with self.endpoints_lock:
                endpoint_bucket = self.endpoints.get(endpoint)
            
            if endpoint_bucket:
                stats["endpoint_bucket"] = endpoint_bucket.get_stats()
        
        return stats
    
    def reset(self) -> None:
        """Reset the rate limiter to initial state."""
        self.bucket = TokenBucket(
            capacity=self.max_requests,
            refill_rate=self.refill_rate,
            name=self.name
        )
        
        with self.endpoints_lock:
            for endpoint, bucket in self.endpoints.items():
                bucket.tokens = float(bucket.capacity)
                bucket.last_refill = time.time()
        
        with self.stats_lock:
            self.total_requests = 0
            self.rejected_requests = 0
            self.last_rejection_time = None
        
        logger.info(f"RateLimiter '{self.name}' reset")


class RateLimitError(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


__all__ = [
    "RateLimiter",
    "RateLimitConfig",
    "TokenBucket",
    "RateLimitError",
]
