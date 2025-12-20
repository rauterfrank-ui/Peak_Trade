"""
Peak_Trade Resilience Module Tests
==================================
Comprehensive unit tests for circuit breaker, retry logic, and health checks.
"""

import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime

from src.core.resilience import (
    CircuitBreaker,
    CircuitState,
    circuit_breaker,
    retry_with_backoff,
    HealthCheck,
    HealthCheckResult,
    health_check as global_health_check
)


# ==============================================================================
# Circuit Breaker Tests
# ==============================================================================

class TestCircuitBreaker:
    """Tests for CircuitBreaker class."""
    
    @pytest.mark.smoke
    def test_circuit_breaker_init(self):
        """Test circuit breaker initialization."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_threshold == 3
        assert breaker.recovery_timeout == 30
        assert breaker.stats.failure_count == 0
        assert breaker.stats.success_count == 0
    
    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit opens after threshold failures."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30, name="test_breaker")
        
        @breaker.call
        def failing_func():
            raise ValueError("Test failure")
        
        # Should allow first 3 failures
        for i in range(3):
            with pytest.raises(ValueError):
                failing_func()
        
        # Circuit should now be OPEN
        assert breaker.state == CircuitState.OPEN
        assert breaker.stats.failure_count == 3
        
        # Next call should fail fast without calling function
        with pytest.raises(Exception, match="CircuitBreaker.*is OPEN"):
            failing_func()
    
    def test_circuit_breaker_success_resets_counter(self):
        """Test successful call in CLOSED state."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
        
        @breaker.call
        def working_func():
            return "success"
        
        result = working_func()
        
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.success_count == 1
        assert breaker.stats.last_success_time is not None
    
    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit transitions to HALF_OPEN and recovers."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1, name="recovery_test")
        
        call_count = [0]
        
        @breaker.call
        def sometimes_failing():
            call_count[0] += 1
            # Fail first 2 times, then succeed
            if call_count[0] <= 2:
                raise ValueError("Failing")
            return "success"
        
        # Cause 2 failures to open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                sometimes_failing()
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        time.sleep(0.15)
        
        # Next call should transition to HALF_OPEN and succeed
        result = sometimes_failing()
        
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.success_count == 1
    
    def test_circuit_breaker_half_open_failure(self):
        """Test circuit reopens if recovery attempt fails."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1, name="reopen_test")
        
        @breaker.call
        def always_fails():
            raise ValueError("Always fails")
        
        # Cause 2 failures to open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                always_fails()
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        time.sleep(0.15)
        
        # Recovery attempt should fail and reopen circuit
        with pytest.raises(ValueError):
            always_fails()
        
        assert breaker.state == CircuitState.OPEN
    
    def test_circuit_breaker_manual_reset(self):
        """Test manual reset of circuit breaker."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)
        
        @breaker.call
        def failing_func():
            raise ValueError("Test failure")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                failing_func()
        
        assert breaker.state == CircuitState.OPEN
        
        # Manually reset
        breaker.reset()
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.stats.failure_count == 0


class TestCircuitBreakerDecorator:
    """Tests for @circuit_breaker decorator."""
    
    def test_decorator_basic_usage(self):
        """Test basic decorator usage."""
        call_count = [0]
        
        @circuit_breaker(failure_threshold=2, recovery_timeout=30)
        def test_func():
            call_count[0] += 1
            return "success"
        
        result = test_func()
        
        assert result == "success"
        assert call_count[0] == 1
    
    def test_decorator_opens_on_failures(self):
        """Test decorator opens circuit on failures."""
        @circuit_breaker(failure_threshold=2, recovery_timeout=30, name="decorator_test")
        def failing_func():
            raise RuntimeError("Test error")
        
        # Fail twice to open circuit
        for _ in range(2):
            with pytest.raises(RuntimeError):
                failing_func()
        
        # Should now fail fast
        with pytest.raises(Exception, match="is OPEN"):
            failing_func()


# ==============================================================================
# Retry with Backoff Tests
# ==============================================================================

class TestRetryWithBackoff:
    """Tests for retry_with_backoff decorator."""
    
    @pytest.mark.smoke
    def test_retry_success_first_attempt(self):
        """Test successful call on first attempt."""
        call_count = [0]
        
        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        def working_func():
            call_count[0] += 1
            return "success"
        
        result = working_func()
        
        assert result == "success"
        assert call_count[0] == 1
    
    def test_retry_with_backoff_success(self):
        """Test successful retry after failures."""
        call_count = [0]
        
        @retry_with_backoff(max_attempts=3, base_delay=0.05)
        def eventually_works():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        start = time.time()
        result = eventually_works()
        duration = time.time() - start
        
        assert result == "success"
        assert call_count[0] == 3
        # Should have delayed at least base_delay * 2 (for 2 retries)
        assert duration >= 0.05
    
    def test_retry_with_backoff_exhaustion(self):
        """Test all retries exhausted."""
        call_count = [0]
        
        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def always_fails():
            call_count[0] += 1
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            always_fails()
        
        assert call_count[0] == 3
    
    def test_retry_exponential_backoff(self):
        """Test exponential backoff calculation."""
        call_count = [0]
        delays = []
        
        @retry_with_backoff(max_attempts=4, base_delay=0.1, exponential=True)
        def track_delays():
            call_count[0] += 1
            if call_count[0] < 4:
                raise ValueError("Not yet")
            return "success"
        
        # Patch time.sleep to track delays
        original_sleep = time.sleep
        
        def mock_sleep(duration):
            delays.append(duration)
            original_sleep(0.01)  # Small actual sleep
        
        with patch('time.sleep', side_effect=mock_sleep):
            result = track_delays()
        
        assert result == "success"
        assert call_count[0] == 4
        assert len(delays) == 3  # 3 retries
        # Check exponential growth: 0.1, 0.2, 0.4
        assert delays[0] == pytest.approx(0.1, rel=0.01)
        assert delays[1] == pytest.approx(0.2, rel=0.01)
        assert delays[2] == pytest.approx(0.4, rel=0.01)
    
    def test_retry_constant_backoff(self):
        """Test constant (non-exponential) backoff."""
        call_count = [0]
        delays = []
        
        @retry_with_backoff(max_attempts=3, base_delay=0.1, exponential=False)
        def constant_delay():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Not yet")
            return "success"
        
        original_sleep = time.sleep
        
        def mock_sleep(duration):
            delays.append(duration)
            original_sleep(0.01)
        
        with patch('time.sleep', side_effect=mock_sleep):
            result = constant_delay()
        
        assert result == "success"
        assert all(d == 0.1 for d in delays)
    
    def test_retry_max_delay_cap(self):
        """Test max_delay caps exponential growth."""
        @retry_with_backoff(max_attempts=5, base_delay=1.0, max_delay=2.0, exponential=True)
        def check_max_delay():
            raise ValueError("Test")
        
        delays = []
        
        def mock_sleep(duration):
            delays.append(duration)
        
        with patch('time.sleep', side_effect=mock_sleep):
            with pytest.raises(ValueError):
                check_max_delay()
        
        # Delays should be: 1.0, 2.0, 2.0, 2.0 (capped at max_delay)
        assert delays[0] == 1.0
        assert all(d <= 2.0 for d in delays)


# ==============================================================================
# Health Check Tests
# ==============================================================================

class TestHealthCheck:
    """Tests for HealthCheck system."""
    
    def test_health_check_init(self):
        """Test HealthCheck initialization."""
        hc = HealthCheck()
        assert len(hc._checks) == 0
    
    def test_health_check_registration(self):
        """Test registering health checks."""
        hc = HealthCheck()
        
        def check_func():
            return True, "All good"
        
        hc.register("test_check", check_func)
        
        assert "test_check" in hc._checks
        assert hc._checks["test_check"] == check_func
    
    def test_health_check_run_all_success(self):
        """Test running all health checks successfully."""
        hc = HealthCheck()
        
        hc.register("check1", lambda: (True, "OK"))
        hc.register("check2", lambda: (True, "All good"))
        
        results = hc.run_all()
        
        assert len(results) == 2
        assert results["check1"].healthy is True
        assert results["check2"].healthy is True
        assert results["check1"].message == "OK"
    
    def test_health_check_failure_detection(self):
        """Test detecting failed health checks."""
        hc = HealthCheck()
        
        hc.register("good_check", lambda: (True, "OK"))
        hc.register("bad_check", lambda: (False, "Failed"))
        
        results = hc.run_all()
        
        assert results["good_check"].healthy is True
        assert results["bad_check"].healthy is False
        assert results["bad_check"].message == "Failed"
    
    def test_health_check_exception_handling(self):
        """Test handling exceptions in health checks."""
        hc = HealthCheck()
        
        def failing_check():
            raise RuntimeError("Check exploded")
        
        hc.register("exploding_check", failing_check)
        
        results = hc.run_all()
        
        assert results["exploding_check"].healthy is False
        assert "exception" in results["exploding_check"].message.lower()
    
    def test_is_system_healthy(self):
        """Test is_system_healthy method."""
        hc = HealthCheck()
        
        hc.register("check1", lambda: True)
        hc.register("check2", lambda: True)
        
        assert hc.is_system_healthy() is True
        
        # Add a failing check
        hc.register("check3", lambda: False)
        
        assert hc.is_system_healthy() is False
    
    def test_health_check_result_to_dict(self):
        """Test HealthCheckResult serialization."""
        result = HealthCheckResult(
            name="test",
            healthy=True,
            message="All good",
            details={"version": "1.0"}
        )
        
        data = result.to_dict()
        
        assert data["name"] == "test"
        assert data["healthy"] is True
        assert data["message"] == "All good"
        assert data["details"]["version"] == "1.0"
        assert "timestamp" in data
    
    def test_get_status(self):
        """Test get_status method."""
        hc = HealthCheck()
        
        hc.register("check1", lambda: (True, "OK"))
        hc.register("check2", lambda: (False, "Failed"))
        
        status = hc.get_status()
        
        assert status["healthy"] is False
        assert status["summary"]["total"] == 2
        assert status["summary"]["passed"] == 1
        assert status["summary"]["failed"] == 1
        assert "timestamp" in status
        assert "checks" in status
    
    def test_health_check_bool_return(self):
        """Test health check with just boolean return."""
        hc = HealthCheck()
        
        hc.register("simple_check", lambda: True)
        
        results = hc.run_all()
        
        assert results["simple_check"].healthy is True
        assert results["simple_check"].message == ""
    
    def test_health_check_overwrite_warning(self):
        """Test overwriting existing check logs warning."""
        hc = HealthCheck()
        
        hc.register("check", lambda: True)
        
        # Registering again should log warning (but still work)
        hc.register("check", lambda: False)
        
        results = hc.run_all()
        assert results["check"].healthy is False


class TestGlobalHealthCheck:
    """Tests for global health_check instance."""
    
    def test_global_instance_exists(self):
        """Test that global health_check instance exists."""
        assert global_health_check is not None
        assert isinstance(global_health_check, HealthCheck)
    
    def test_global_instance_can_register(self):
        """Test registering checks on global instance."""
        # Note: This modifies global state, but tests should be isolated
        # In practice, each test should use a fresh HealthCheck instance
        
        check_name = f"test_global_{time.time()}"
        global_health_check.register(check_name, lambda: True)
        
        assert check_name in global_health_check._checks


# ==============================================================================
# Integration Tests
# ==============================================================================

class TestIntegration:
    """Integration tests combining multiple patterns."""
    
    def test_circuit_breaker_with_retry(self):
        """Test circuit breaker combined with retry logic."""
        call_count = [0]
        
        @circuit_breaker(failure_threshold=5, recovery_timeout=30)
        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def combined_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        result = combined_func()
        
        assert result == "success"
        # Retry should handle first 2 failures, succeed on attempt 3
        assert call_count[0] == 3
    
    def test_health_check_with_circuit_breaker(self):
        """Test health check monitoring circuit breaker status."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=30, name="monitored")
        
        @breaker.call
        def protected_func():
            raise ValueError("Fails")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                protected_func()
        
        # Create health check that monitors breaker state
        hc = HealthCheck()
        hc.register("breaker_status", lambda: (breaker.state == CircuitState.CLOSED, f"State: {breaker.state.value}"))
        
        results = hc.run_all()
        
        assert results["breaker_status"].healthy is False
        assert "OPEN" in results["breaker_status"].message.upper()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
