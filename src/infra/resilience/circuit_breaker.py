"""
Circuit Breaker Pattern
=========================

Implements the circuit breaker pattern to prevent cascading failures
and provide automatic recovery for failing services.

States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failure threshold exceeded, requests blocked
    - HALF_OPEN: Testing if service recovered

Usage:
    from src.infra.resilience import CircuitBreaker, circuit_breaker
    
    # As a decorator
    @circuit_breaker(name="exchange_api", threshold=5, timeout=60)
    def call_exchange_api():
        # API call here
        pass
    
    # As a context manager
    cb = CircuitBreaker(name="my_service", threshold=3)
    with cb:
        # Protected operation
        pass
"""

from __future__ import annotations

import functools
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, Optional, TypeVar, cast

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    """Circuit breaker states."""
    
    CLOSED = "CLOSED"        # Normal operation
    OPEN = "OPEN"            # Failure threshold exceeded
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


@dataclass
class CircuitBreakerMetrics:
    """Metrics for a circuit breaker."""
    
    name: str
    state: CircuitState
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    total_calls: int = 0
    state_changes: int = 0
    last_state_change: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "total_calls": self.total_calls,
            "state_changes": self.state_changes,
            "last_state_change": self.last_state_change.isoformat() if self.last_state_change else None,
            "failure_rate": self.failure_count / self.total_calls if self.total_calls > 0 else 0.0,
        }


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation.
    
    Monitors failures and automatically opens the circuit when
    failure threshold is exceeded. After timeout, transitions to
    HALF_OPEN to test recovery.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        half_open_max_calls: int = 3,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Identifier for this circuit
            failure_threshold: Number of failures before opening
            timeout_seconds: Seconds to wait before testing recovery
            half_open_max_calls: Max calls in HALF_OPEN before deciding
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.half_open_max_calls = half_open_max_calls
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = Lock()
        
        self.metrics = CircuitBreakerMetrics(name=name, state=self._state)
        
        logger.info(
            f"CircuitBreaker '{name}' initialized: "
            f"threshold={failure_threshold}, timeout={timeout_seconds}s"
        )
    
    @property
    def state(self) -> CircuitState:
        """Get current state."""
        with self._lock:
            self._check_timeout()
            return self._state
    
    def _check_timeout(self) -> None:
        """Check if timeout expired and transition to HALF_OPEN."""
        if self._state == CircuitState.OPEN and self._last_failure_time:
            elapsed = time.time() - self._last_failure_time
            if elapsed >= self.timeout_seconds:
                self._transition_to(CircuitState.HALF_OPEN)
                self._half_open_calls = 0
                logger.info(
                    f"CircuitBreaker '{self.name}' timeout expired, "
                    f"transitioning to HALF_OPEN"
                )
    
    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state."""
        old_state = self._state
        self._state = new_state
        self.metrics.state = new_state
        self.metrics.state_changes += 1
        self.metrics.last_state_change = datetime.now()
        
        if old_state != new_state:
            logger.info(
                f"CircuitBreaker '{self.name}' state change: "
                f"{old_state.value} -> {new_state.value}"
            )
    
    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
        """
        with self._lock:
            self._check_timeout()
            
            if self._state == CircuitState.OPEN:
                raise CircuitBreakerError(
                    f"CircuitBreaker '{self.name}' is OPEN "
                    f"(failures: {self._failure_count}/{self.failure_threshold})"
                )
            
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerError(
                        f"CircuitBreaker '{self.name}' HALF_OPEN max calls exceeded"
                    )
                self._half_open_calls += 1
        
        # Execute function outside lock
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self) -> None:
        """Handle successful call."""
        with self._lock:
            self._success_count += 1
            self.metrics.success_count += 1
            self.metrics.total_calls += 1
            self.metrics.last_success_time = datetime.now()
            
            if self._state == CircuitState.HALF_OPEN:
                # Successful recovery
                self._transition_to(CircuitState.CLOSED)
                self._failure_count = 0
                logger.info(
                    f"CircuitBreaker '{self.name}' recovered, "
                    f"transitioning to CLOSED"
                )
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        with self._lock:
            self._failure_count += 1
            self.metrics.failure_count += 1
            self.metrics.total_calls += 1
            self.metrics.last_failure_time = datetime.now()
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                # Recovery failed
                self._transition_to(CircuitState.OPEN)
                logger.warning(
                    f"CircuitBreaker '{self.name}' recovery failed, "
                    f"transitioning back to OPEN"
                )
            elif self._failure_count >= self.failure_threshold:
                # Threshold exceeded
                self._transition_to(CircuitState.OPEN)
                logger.error(
                    f"CircuitBreaker '{self.name}' threshold exceeded "
                    f"({self._failure_count}/{self.failure_threshold}), "
                    f"transitioning to OPEN"
                )
    
    def reset(self) -> None:
        """Reset circuit breaker to CLOSED state."""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            self._half_open_calls = 0
            logger.info(f"CircuitBreaker '{self.name}' manually reset")
    
    def get_metrics(self) -> CircuitBreakerMetrics:
        """Get current metrics."""
        with self._lock:
            return self.metrics
    
    def __enter__(self) -> CircuitBreaker:
        """Context manager entry."""
        with self._lock:
            self._check_timeout()
            
            if self._state == CircuitState.OPEN:
                raise CircuitBreakerError(
                    f"CircuitBreaker '{self.name}' is OPEN"
                )
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        if exc_type is None:
            self._on_success()
        else:
            self._on_failure()
        
        # Don't suppress exceptions
        return False


# Global registry of circuit breakers
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_registry_lock = Lock()


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout_seconds: int = 60,
) -> CircuitBreaker:
    """
    Get or create a circuit breaker.
    
    Args:
        name: Circuit breaker name
        failure_threshold: Failure threshold
        timeout_seconds: Timeout in seconds
        
    Returns:
        CircuitBreaker instance
    """
    with _registry_lock:
        if name not in _circuit_breakers:
            _circuit_breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                timeout_seconds=timeout_seconds,
            )
        return _circuit_breakers[name]


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    timeout_seconds: int = 60,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to protect a function with circuit breaker.
    
    Args:
        name: Circuit breaker name
        failure_threshold: Number of failures before opening
        timeout_seconds: Seconds to wait before recovery
        
    Returns:
        Decorated function
        
    Example:
        @circuit_breaker(name="exchange_api", threshold=5, timeout=60)
        def call_api():
            # API call here
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cb = get_circuit_breaker(
            name=name,
            failure_threshold=failure_threshold,
            timeout_seconds=timeout_seconds,
        )
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return cb.call(func, *args, **kwargs)
        
        return wrapper
    
    return decorator
