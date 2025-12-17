"""
Tests for Rate Limiter
========================

Tests for the rate limiter implementation.
"""

import pytest
import time

from src.infra.resilience.rate_limiter import (
    RateLimiter,
    rate_limit,
    get_rate_limiter,
)


class TestRateLimiter:
    """Test RateLimiter class."""
    
    def test_initialization(self):
        """Test rate limiter initializes correctly."""
        limiter = RateLimiter(
            requests_per_second=10.0,
            burst_size=20,
            name="test",
        )
        
        assert limiter.requests_per_second == 10.0
        assert limiter.burst_size == 20
        assert limiter.name == "test"
    
    def test_invalid_rate(self):
        """Test initialization with invalid rate raises error."""
        with pytest.raises(ValueError):
            RateLimiter(requests_per_second=0)
        
        with pytest.raises(ValueError):
            RateLimiter(requests_per_second=-1)
    
    def test_acquire_allows_requests(self):
        """Test acquire allows requests within limit."""
        limiter = RateLimiter(requests_per_second=10.0)
        
        # Should succeed immediately (tokens available)
        result = limiter.acquire()
        assert result is True
    
    def test_try_acquire_non_blocking(self):
        """Test try_acquire doesn't block."""
        limiter = RateLimiter(requests_per_second=1.0, burst_size=1)
        
        # First request should succeed
        assert limiter.try_acquire() is True
        
        # Second request should fail immediately (no tokens)
        assert limiter.try_acquire() is False
    
    def test_rate_limiting_throttles(self):
        """Test rate limiter actually throttles requests."""
        limiter = RateLimiter(requests_per_second=10.0, burst_size=2)
        
        start = time.time()
        
        # Use up burst
        limiter.acquire()
        limiter.acquire()
        
        # Next request should be throttled
        limiter.acquire()
        
        elapsed = time.time() - start
        
        # Should have been delayed (at least 0.1s for 1 token at 10/s)
        assert elapsed >= 0.08  # Allow some tolerance
    
    def test_context_manager(self):
        """Test using rate limiter as context manager."""
        limiter = RateLimiter(requests_per_second=10.0)
        
        with limiter:
            # Should acquire token successfully
            pass
    
    def test_metrics(self):
        """Test metrics collection."""
        limiter = RateLimiter(requests_per_second=100.0, burst_size=5)
        
        # Make some requests
        for _ in range(3):
            limiter.acquire()
        
        metrics = limiter.get_metrics()
        assert metrics.name == limiter.name
        assert metrics.requests_per_second == 100.0
        assert metrics.total_requests == 3


class TestRateLimitDecorator:
    """Test rate_limit decorator."""
    
    def test_decorator_basic(self):
        """Test basic decorator usage."""
        
        @rate_limit(name="test_decorator", requests_per_second=10.0)
        def my_function():
            return "success"
        
        result = my_function()
        assert result == "success"
    
    def test_decorator_throttles(self):
        """Test decorator throttles calls."""
        
        @rate_limit(name="test_throttle", requests_per_second=5.0, burst_size=1)
        def my_function():
            return "success"
        
        start = time.time()
        
        # First call uses burst
        my_function()
        
        # Second call should be throttled
        my_function()
        
        elapsed = time.time() - start
        
        # Should have been delayed (at least 0.2s for 1 token at 5/s)
        assert elapsed >= 0.15


class TestGetRateLimiter:
    """Test get_rate_limiter function."""
    
    def test_get_or_create(self):
        """Test get_rate_limiter creates or retrieves limiter."""
        limiter1 = get_rate_limiter("shared", requests_per_second=10.0)
        limiter2 = get_rate_limiter("shared", requests_per_second=10.0)
        
        # Should be the same instance
        assert limiter1 is limiter2
    
    def test_different_names(self):
        """Test different names create different limiters."""
        limiter1 = get_rate_limiter("limiter1", requests_per_second=10.0)
        limiter2 = get_rate_limiter("limiter2", requests_per_second=20.0)
        
        assert limiter1 is not limiter2
        assert limiter1.name == "limiter1"
        assert limiter2.name == "limiter2"
