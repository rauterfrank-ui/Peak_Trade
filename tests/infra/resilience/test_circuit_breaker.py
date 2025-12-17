"""
Tests for Circuit Breaker
"""

import pytest
from src.infra.resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    CircuitBreakerOpenError,
)


@pytest.mark.asyncio
async def test_circuit_breaker_initialization():
    """Test CircuitBreaker initialization"""
    config = CircuitBreakerConfig(name="test", failure_threshold=3)
    cb = CircuitBreaker(config)
    
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.metrics.total_calls == 0


@pytest.mark.asyncio
async def test_circuit_breaker_success():
    """Test successful calls through circuit breaker"""
    config = CircuitBreakerConfig(name="test", failure_threshold=3)
    cb = CircuitBreaker(config)
    
    async def success_func():
        return "success"
    
    result = await cb.call(success_func)
    assert result == "success"
    assert cb.state == CircuitBreakerState.CLOSED
    assert cb.metrics.success_calls == 1
    assert cb.metrics.failure_calls == 0


@pytest.mark.asyncio
async def test_circuit_breaker_opens_on_failures():
    """Test circuit breaker opens after threshold failures"""
    config = CircuitBreakerConfig(name="test", failure_threshold=3)
    cb = CircuitBreaker(config)
    
    async def failing_func():
        raise Exception("Test error")
    
    # First 3 failures should go through
    for i in range(3):
        with pytest.raises(Exception, match="Test error"):
            await cb.call(failing_func)
    
    # Circuit should be OPEN now
    assert cb.state == CircuitBreakerState.OPEN
    assert cb.metrics.failure_calls == 3
    
    # Next call should be rejected
    with pytest.raises(CircuitBreakerOpenError):
        await cb.call(failing_func)
    
    assert cb.metrics.rejected_calls == 1


@pytest.mark.asyncio
async def test_circuit_breaker_half_open():
    """Test circuit breaker transitions to half-open"""
    config = CircuitBreakerConfig(
        name="test",
        failure_threshold=2,
        timeout_seconds=0.1,  # Short timeout for testing
    )
    cb = CircuitBreaker(config)
    
    async def failing_func():
        raise Exception("Test error")
    
    # Cause failures to open circuit
    for _ in range(2):
        with pytest.raises(Exception):
            await cb.call(failing_func)
    
    assert cb.state == CircuitBreakerState.OPEN
    
    # Wait for timeout
    import asyncio
    await asyncio.sleep(0.15)
    
    # After timeout, next call should transition to HALF_OPEN and then fail
    # This will cause it to go back to OPEN
    with pytest.raises(Exception):
        await cb.call(failing_func)
    
    # State should be OPEN again after failure in HALF_OPEN
    assert cb.state == CircuitBreakerState.OPEN


@pytest.mark.asyncio
async def test_circuit_breaker_get_state():
    """Test getting circuit breaker state"""
    config = CircuitBreakerConfig(name="test")
    cb = CircuitBreaker(config)
    
    state = cb.get_state()
    assert state["name"] == "test"
    assert state["state"] == CircuitBreakerState.CLOSED.value
    assert "metrics" in state
    assert state["metrics"]["total_calls"] == 0


@pytest.mark.asyncio
async def test_circuit_breaker_reset():
    """Test manual circuit breaker reset"""
    config = CircuitBreakerConfig(name="test", failure_threshold=2)
    cb = CircuitBreaker(config)
    
    async def failing_func():
        raise Exception("Test error")
    
    # Open circuit
    for _ in range(2):
        with pytest.raises(Exception):
            await cb.call(failing_func)
    
    assert cb.state == CircuitBreakerState.OPEN
    
    # Reset
    cb.reset()
    assert cb.state == CircuitBreakerState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_metrics():
    """Test circuit breaker metrics collection"""
    config = CircuitBreakerConfig(name="test", failure_threshold=5)
    cb = CircuitBreaker(config)
    
    async def success_func():
        return "ok"
    
    async def fail_func():
        raise Exception("error")
    
    # Mix of successes and failures
    await cb.call(success_func)
    await cb.call(success_func)
    
    with pytest.raises(Exception):
        await cb.call(fail_func)
    
    await cb.call(success_func)
    
    state = cb.get_state()
    assert state["metrics"]["total_calls"] == 4
    assert state["metrics"]["success_calls"] == 3
    assert state["metrics"]["failure_calls"] == 1
    assert state["metrics"]["success_rate"] == 0.75
