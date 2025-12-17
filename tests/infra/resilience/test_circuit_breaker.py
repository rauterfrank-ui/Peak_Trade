"""
Tests for Circuit Breaker
===========================

Tests for the circuit breaker pattern implementation.
"""

import pytest
import time
from threading import Thread

from src.infra.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerError,
    circuit_breaker,
    get_circuit_breaker,
)


class TestCircuitBreaker:
    """Test CircuitBreaker class."""
    
    def test_initialization(self):
        """Test circuit breaker initializes correctly."""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=5,
            timeout_seconds=60,
        )
        
        assert cb.name == "test"
        assert cb.failure_threshold == 5
        assert cb.timeout_seconds == 60
        assert cb.state == CircuitState.CLOSED
    
    def test_closed_state_allows_calls(self):
        """Test CLOSED state allows calls."""
        cb = CircuitBreaker(name="test", failure_threshold=3)
        
        def successful_operation():
            return "success"
        
        result = cb.call(successful_operation)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
    
    def test_failures_open_circuit(self):
        """Test failures open the circuit."""
        cb = CircuitBreaker(name="test", failure_threshold=3)
        
        def failing_operation():
            raise ValueError("Operation failed")
        
        # Fail threshold number of times
        for _ in range(3):
            with pytest.raises(ValueError):
                cb.call(failing_operation)
        
        # Circuit should be open now
        assert cb.state == CircuitState.OPEN
        
        # Next call should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            cb.call(failing_operation)
    
    def test_timeout_transitions_to_half_open(self):
        """Test timeout transitions circuit to HALF_OPEN."""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            timeout_seconds=1,  # Short timeout for testing
        )
        
        def failing_operation():
            raise ValueError("Failed")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(failing_operation)
        
        assert cb.state == CircuitState.OPEN
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Check state (should transition to HALF_OPEN)
        assert cb.state == CircuitState.HALF_OPEN
    
    def test_half_open_success_closes_circuit(self):
        """Test successful call in HALF_OPEN closes circuit."""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            timeout_seconds=1,
        )
        
        # Open the circuit
        def fail():
            raise ValueError("Failed")
        
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(fail)
        
        assert cb.state == CircuitState.OPEN
        
        # Wait for timeout
        time.sleep(1.1)
        assert cb.state == CircuitState.HALF_OPEN
        
        # Successful call should close circuit
        def success():
            return "OK"
        
        result = cb.call(success)
        assert result == "OK"
        assert cb.state == CircuitState.CLOSED
    
    def test_half_open_failure_reopens_circuit(self):
        """Test failure in HALF_OPEN reopens circuit."""
        cb = CircuitBreaker(
            name="test",
            failure_threshold=2,
            timeout_seconds=1,
        )
        
        # Open the circuit
        def fail():
            raise ValueError("Failed")
        
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(fail)
        
        assert cb.state == CircuitState.OPEN
        
        # Wait for timeout
        time.sleep(1.1)
        assert cb.state == CircuitState.HALF_OPEN
        
        # Failed call should reopen circuit
        with pytest.raises(ValueError):
            cb.call(fail)
        
        assert cb.state == CircuitState.OPEN
    
    def test_reset(self):
        """Test manual reset of circuit breaker."""
        cb = CircuitBreaker(name="test", failure_threshold=2)
        
        # Open the circuit
        def fail():
            raise ValueError("Failed")
        
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(fail)
        
        assert cb.state == CircuitState.OPEN
        
        # Reset
        cb.reset()
        assert cb.state == CircuitState.CLOSED
    
    def test_get_metrics(self):
        """Test getting metrics from circuit breaker."""
        cb = CircuitBreaker(name="test", failure_threshold=3)
        
        def success():
            return "OK"
        
        def fail():
            raise ValueError("Failed")
        
        # Some successful calls
        cb.call(success)
        cb.call(success)
        
        # Some failures
        with pytest.raises(ValueError):
            cb.call(fail)
        
        metrics = cb.get_metrics()
        assert metrics.name == "test"
        assert metrics.success_count == 2
        assert metrics.failure_count == 1
        assert metrics.total_calls == 3
        assert metrics.state == CircuitState.CLOSED
    
    def test_context_manager(self):
        """Test using circuit breaker as context manager."""
        cb = CircuitBreaker(name="test", failure_threshold=3)
        
        # Successful use
        with cb:
            result = "success"
        
        assert cb.state == CircuitState.CLOSED
        
        # Failed use
        with pytest.raises(ValueError):
            with cb:
                raise ValueError("Failed")
        
        # Circuit should still be closed (only 1 failure)
        assert cb.state == CircuitState.CLOSED


class TestCircuitBreakerDecorator:
    """Test circuit_breaker decorator."""
    
    def test_decorator_basic(self):
        """Test basic decorator usage."""
        
        @circuit_breaker(name="test_decorator", failure_threshold=3)
        def my_function():
            return "success"
        
        result = my_function()
        assert result == "success"
    
    def test_decorator_with_failures(self):
        """Test decorator with failures."""
        
        @circuit_breaker(name="test_fail_decorator", failure_threshold=2)
        def failing_function():
            raise ValueError("Failed")
        
        # Fail twice to open circuit
        with pytest.raises(ValueError):
            failing_function()
        
        with pytest.raises(ValueError):
            failing_function()
        
        # Third call should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            failing_function()


class TestGetCircuitBreaker:
    """Test get_circuit_breaker function."""
    
    def test_get_or_create(self):
        """Test get_circuit_breaker creates or retrieves breaker."""
        cb1 = get_circuit_breaker("shared", failure_threshold=5)
        cb2 = get_circuit_breaker("shared", failure_threshold=5)
        
        # Should be the same instance
        assert cb1 is cb2
    
    def test_different_names_different_instances(self):
        """Test different names create different instances."""
        cb1 = get_circuit_breaker("cb1")
        cb2 = get_circuit_breaker("cb2")
        
        assert cb1 is not cb2
        assert cb1.name == "cb1"
        assert cb2.name == "cb2"
