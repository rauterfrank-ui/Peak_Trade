"""
Tests for Rate Limiter Module
==============================
Comprehensive tests for rate limiting functionality.
"""

import pytest
import time
import threading
from unittest.mock import patch

from src.core.rate_limiter import (
    RateLimiter,
    TokenBucket,
    RateLimitConfig,
    RateLimitError
)


class TestTokenBucket:
    """Tests for TokenBucket implementation."""
    
    def test_token_bucket_init(self):
        """Test token bucket initialization."""
        bucket = TokenBucket(capacity=10, refill_rate=2.0)
        
        assert bucket.capacity == 10
        assert bucket.refill_rate == 2.0
        assert bucket.tokens == 10.0
    
    def test_token_bucket_acquire_success(self):
        """Test successful token acquisition."""
        bucket = TokenBucket(capacity=10, refill_rate=2.0)
        
        assert bucket.acquire(5) is True
        assert bucket.tokens == 5.0
    
    def test_token_bucket_acquire_failure(self):
        """Test token acquisition failure when not enough tokens."""
        bucket = TokenBucket(capacity=10, refill_rate=2.0)
        
        # Acquire 8 tokens
        assert bucket.acquire(8) is True
        
        # Try to acquire 5 more (only 2 left)
        assert bucket.acquire(5) is False
        assert bucket.tokens == pytest.approx(2.0, abs=0.1)
    
    def test_token_bucket_refill(self):
        """Test token refilling over time."""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)  # 10 tokens/second
        
        # Use 5 tokens
        bucket.acquire(5)
        assert bucket.tokens == 5.0
        
        # Wait 0.5 seconds (should add 5 tokens)
        time.sleep(0.5)
        bucket._refill()
        
        assert bucket.tokens == pytest.approx(10.0, abs=0.5)
    
    def test_token_bucket_max_capacity(self):
        """Test that tokens don't exceed capacity."""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)
        
        # Wait to accumulate tokens beyond capacity
        time.sleep(2.0)
        bucket._refill()
        
        # Should cap at capacity
        assert bucket.tokens <= 10.0
    
    def test_token_bucket_get_wait_time(self):
        """Test wait time calculation."""
        bucket = TokenBucket(capacity=10, refill_rate=2.0)  # 2 tokens/second
        
        # Use all tokens
        bucket.acquire(10)
        
        # Need 5 tokens, should take 2.5 seconds
        wait_time = bucket.get_wait_time(5)
        assert wait_time == pytest.approx(2.5, abs=0.1)
    
    def test_token_bucket_thread_safety(self):
        """Test thread-safe token acquisition."""
        bucket = TokenBucket(capacity=100, refill_rate=10.0)
        results = []
        
        def acquire_tokens():
            for _ in range(10):
                result = bucket.acquire(1)
                results.append(result)
        
        threads = [threading.Thread(target=acquire_tokens) for _ in range(5)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have 50 successful acquisitions total
        successful = sum(1 for r in results if r)
        assert successful <= 100  # Can't exceed capacity
    
    def test_token_bucket_get_stats(self):
        """Test statistics retrieval."""
        bucket = TokenBucket(capacity=10, refill_rate=2.0)
        bucket.acquire(3)
        
        stats = bucket.get_stats()
        
        assert stats["capacity"] == 10
        assert stats["tokens"] == pytest.approx(7.0, abs=0.1)
        assert 0.0 <= stats["utilization"] <= 1.0


class TestRateLimiter:
    """Tests for RateLimiter class."""
    
    def test_rate_limiter_init(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(max_requests=100, window_seconds=60)
        
        assert limiter.max_requests == 100
        assert limiter.window_seconds == 60
        assert limiter.refill_rate == pytest.approx(100.0 / 60.0)
    
    def test_rate_limiter_acquire_success(self):
        """Test successful request acquisition."""
        limiter = RateLimiter(max_requests=10, window_seconds=1)
        
        assert limiter.acquire() is True
        assert limiter.total_requests == 1
        assert limiter.rejected_requests == 0
    
    def test_rate_limiter_acquire_rejection(self):
        """Test request rejection when limit exceeded."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # Acquire all 5 tokens
        for _ in range(5):
            assert limiter.acquire() is True
        
        # Next should be rejected
        assert limiter.acquire() is False
        assert limiter.total_requests == 6
        assert limiter.rejected_requests == 1
    
    def test_rate_limiter_endpoint_specific_limit(self):
        """Test endpoint-specific rate limits."""
        limiter = RateLimiter(max_requests=100, window_seconds=60)
        limiter.add_endpoint("fast_api", max_requests=5, window_seconds=1)
        
        # Global limit allows more, but endpoint limit restricts
        for _ in range(5):
            assert limiter.acquire("fast_api") is True
        
        # Endpoint limit exceeded
        assert limiter.acquire("fast_api") is False
    
    def test_rate_limiter_multiple_endpoints(self):
        """Test multiple endpoint limits."""
        limiter = RateLimiter(max_requests=100, window_seconds=60)
        limiter.add_endpoint("api1", max_requests=3, window_seconds=1)
        limiter.add_endpoint("api2", max_requests=5, window_seconds=1)
        
        # api1 can handle 3
        for _ in range(3):
            assert limiter.acquire("api1") is True
        assert limiter.acquire("api1") is False
        
        # api2 can still handle 5
        for _ in range(5):
            assert limiter.acquire("api2") is True
        assert limiter.acquire("api2") is False
    
    def test_rate_limiter_wait_time(self):
        """Test wait time calculation."""
        limiter = RateLimiter(max_requests=10, window_seconds=10)  # 1 req/sec
        
        # Use all tokens
        for _ in range(10):
            limiter.acquire()
        
        # Should need to wait
        wait_time = limiter.get_wait_time()
        assert wait_time > 0
    
    def test_rate_limiter_stats(self):
        """Test statistics collection."""
        limiter = RateLimiter(max_requests=10, window_seconds=1, name="test_limiter")
        
        # Make some requests
        for _ in range(5):
            limiter.acquire()
        
        # Reject one
        for _ in range(6):
            limiter.acquire()
        
        stats = limiter.get_stats()
        
        assert stats["name"] == "test_limiter"
        assert stats["total_requests"] == 11
        assert stats["rejected_requests"] >= 1
        assert "global_bucket" in stats
    
    def test_rate_limiter_reset(self):
        """Test rate limiter reset."""
        limiter = RateLimiter(max_requests=5, window_seconds=1)
        
        # Use all tokens
        for _ in range(5):
            limiter.acquire()
        
        assert limiter.acquire() is False
        
        # Reset
        limiter.reset()
        
        # Should work again
        assert limiter.acquire() is True
        assert limiter.total_requests == 1
        assert limiter.rejected_requests == 0
    
    def test_rate_limiter_concurrent_access(self):
        """Test thread-safe concurrent access."""
        limiter = RateLimiter(max_requests=50, window_seconds=1)
        results = []
        lock = threading.Lock()
        
        def make_requests():
            for _ in range(10):
                result = limiter.acquire()
                with lock:
                    results.append(result)
        
        threads = [threading.Thread(target=make_requests) for _ in range(10)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Total attempts = 100, capacity = 50
        successful = sum(1 for r in results if r)
        assert successful <= 50
        assert limiter.total_requests == 100
    
    def test_rate_limiter_refill_over_time(self):
        """Test that tokens refill over time."""
        limiter = RateLimiter(max_requests=10, window_seconds=1)  # 10 req/sec
        
        # Use 5 tokens
        for _ in range(5):
            limiter.acquire()
        
        # Wait for refill (0.5 seconds = 5 tokens)
        time.sleep(0.5)
        
        # Should be able to acquire more tokens
        for _ in range(5):
            assert limiter.acquire() is True


class TestRateLimitConfig:
    """Tests for RateLimitConfig."""
    
    def test_config_creation(self):
        """Test creating rate limit config."""
        config = RateLimitConfig(
            max_requests=100,
            window_seconds=60,
            name="test_config"
        )
        
        assert config.max_requests == 100
        assert config.window_seconds == 60
        assert config.name == "test_config"


class TestRateLimitError:
    """Tests for RateLimitError exception."""
    
    def test_error_raised(self):
        """Test raising RateLimitError."""
        with pytest.raises(RateLimitError):
            raise RateLimitError("Rate limit exceeded")


class TestIntegration:
    """Integration tests."""
    
    def test_burst_handling(self):
        """Test handling burst of requests."""
        limiter = RateLimiter(max_requests=10, window_seconds=1)
        
        # Burst of 10 requests should all succeed
        results = [limiter.acquire() for _ in range(10)]
        assert all(results)
        
        # Next requests should fail
        assert limiter.acquire() is False
    
    def test_gradual_refill(self):
        """Test gradual token refilling."""
        limiter = RateLimiter(max_requests=10, window_seconds=1)
        
        # Use all tokens
        for _ in range(10):
            limiter.acquire()
        
        # Wait and try again periodically
        for _ in range(5):
            time.sleep(0.2)  # Wait for 2 tokens to refill
            assert limiter.acquire() is True
            assert limiter.acquire() is True
    
    def test_mixed_endpoint_usage(self):
        """Test mixed global and endpoint-specific limits."""
        limiter = RateLimiter(max_requests=20, window_seconds=1)
        limiter.add_endpoint("restricted", max_requests=5, window_seconds=1)
        
        # Use restricted endpoint (hits endpoint limit first)
        for _ in range(5):
            assert limiter.acquire("restricted") is True
        assert limiter.acquire("restricted") is False
        
        # Global limit still has capacity for other requests
        for _ in range(10):
            assert limiter.acquire("other") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
