"""
Peak_Trade Resilience & Stability Module
========================================
Provides circuit breaker, retry logic, and health check patterns for robust
handling of external dependencies (Exchange APIs, Databases).

Module Components:
- CircuitBreaker: Prevents cascading failures by opening circuit after threshold
- retry_with_backoff: Retries failed operations with exponential backoff
- HealthCheck: System health monitoring and reporting

Usage:
    from src.core.resilience import circuit_breaker, retry_with_backoff, health_check

    @circuit_breaker(failure_threshold=3, recovery_timeout=60)
    @retry_with_backoff(max_attempts=3, base_delay=1.0)
    def call_external_api():
        # Your API call here
        pass

    # Register health check
    health_check.register("my_service", lambda: check_my_service())
    
    # Run all checks
    results = health_check.run_all()
    is_healthy = health_check.is_system_healthy()
"""

import logging
import time
import functools
from enum import Enum
from typing import Callable, Dict, Any, Optional, Type, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    """
    Get current UTC time in a timezone-aware manner.
    
    Returns:
        Timezone-aware datetime in UTC
    """
    # Python 3.11+ has datetime.UTC, fall back to utcnow() for older versions
    if hasattr(datetime, 'UTC'):
        return datetime.now(datetime.UTC)
    else:
        return datetime.utcnow()


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker monitoring."""
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changes: int = 0


class CircuitBreaker:
    """
    Circuit Breaker Pattern implementation.
    
    Prevents cascading failures by opening the circuit after a threshold of failures.
    After a recovery timeout, the circuit transitions to HALF_OPEN state to test recovery.
    
    Args:
        failure_threshold: Number of consecutive failures before opening circuit (default: 5)
        recovery_timeout: Time in seconds before attempting recovery (default: 60)
        expected_exception: Exception type to catch (default: Exception)
        name: Optional name for this circuit breaker
        
    States:
        CLOSED: Normal operation, calls pass through
        OPEN: Circuit is open, calls fail immediately
        HALF_OPEN: Testing recovery, one call allowed through
        
    Example:
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
        
        @breaker.call
        def risky_operation():
            # Your operation here
            pass
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception,
        name: str = "circuit_breaker"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self._state = CircuitState.CLOSED
        self._stats = CircuitBreakerStats()
        
        logger.info(
            f"CircuitBreaker '{name}' initialized: "
            f"threshold={failure_threshold}, timeout={recovery_timeout}s"
        )
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state
    
    @property
    def stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics."""
        return self._stats
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._state != CircuitState.OPEN:
            return False
        
        if self._stats.last_failure_time is None:
            return False
        
        time_since_failure = time.time() - self._stats.last_failure_time
        return time_since_failure >= self.recovery_timeout
    
    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        old_state = self._state
        self._state = new_state
        self._stats.state_changes += 1
        
        logger.warning(
            f"CircuitBreaker '{self.name}' state change: "
            f"{old_state.value} -> {new_state.value}"
        )
    
    def _on_success(self) -> None:
        """Handle successful call."""
        self._stats.success_count += 1
        self._stats.last_success_time = time.time()
        
        if self._state == CircuitState.HALF_OPEN:
            # Recovery successful, close circuit
            self._stats.failure_count = 0
            self._transition_to(CircuitState.CLOSED)
            logger.info(f"CircuitBreaker '{self.name}' recovered and closed")
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        self._stats.failure_count += 1
        self._stats.last_failure_time = time.time()
        
        if self._state == CircuitState.HALF_OPEN:
            # Recovery failed, reopen circuit
            self._transition_to(CircuitState.OPEN)
            logger.warning(f"CircuitBreaker '{self.name}' recovery failed, reopening")
        elif self._state == CircuitState.CLOSED:
            # Check if we should open circuit
            if self._stats.failure_count >= self.failure_threshold:
                self._transition_to(CircuitState.OPEN)
                logger.error(
                    f"CircuitBreaker '{self.name}' opened after "
                    f"{self._stats.failure_count} failures"
                )
    
    def call(self, func: Callable) -> Callable:
        """
        Decorator to wrap a function with circuit breaker protection.
        
        Args:
            func: Function to protect
            
        Returns:
            Wrapped function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if we should attempt reset
            if self._should_attempt_reset():
                self._transition_to(CircuitState.HALF_OPEN)
                logger.info(f"CircuitBreaker '{self.name}' attempting recovery")
            
            # Fail fast if circuit is open
            if self._state == CircuitState.OPEN:
                raise Exception(
                    f"CircuitBreaker '{self.name}' is OPEN, call rejected"
                )
            
            # Attempt the call
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                logger.error(
                    f"CircuitBreaker '{self.name}' caught exception: {e}",
                    exc_info=True
                )
                raise
        
        return wrapper
    
    def reset(self) -> None:
        """Manually reset the circuit breaker to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._stats.failure_count = 0
        logger.info(f"CircuitBreaker '{self.name}' manually reset to CLOSED")


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Type[Exception] = Exception,
    name: Optional[str] = None
) -> Callable:
    """
    Decorator factory for circuit breaker pattern.
    
    Args:
        failure_threshold: Number of failures before opening circuit (default: 5)
        recovery_timeout: Time in seconds before recovery attempt (default: 60)
        expected_exception: Exception type to catch (default: Exception)
        name: Optional name for the circuit breaker
        
    Returns:
        Decorator function
        
    Example:
        @circuit_breaker(failure_threshold=3, recovery_timeout=30)
        def fetch_data():
            # Your code here
            pass
    """
    def decorator(func: Callable) -> Callable:
        breaker_name = name or f"cb_{func.__name__}"
        breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=breaker_name
        )
        return breaker.call(func)
    
    return decorator


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential: bool = True,
    expected_exception: Type[Exception] = Exception
) -> Callable:
    """
    Decorator for retry logic with exponential backoff.
    
    Retries a failed operation with increasing delays between attempts.
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        exponential: Use exponential backoff if True, else constant (default: True)
        expected_exception: Exception type to retry on (default: Exception)
        
    Returns:
        Decorator function
        
    Example:
        @retry_with_backoff(max_attempts=3, base_delay=1.0)
        def unstable_api_call():
            # Your code here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 1:
                        logger.info(
                            f"Retry successful for {func.__name__} on attempt {attempt}"
                        )
                    return result
                    
                except expected_exception as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"All {max_attempts} retry attempts exhausted for {func.__name__}",
                            exc_info=True
                        )
                        raise
                    
                    # Calculate delay
                    if exponential:
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    else:
                        delay = base_delay
                    
                    logger.warning(
                        f"Retry attempt {attempt}/{max_attempts} for {func.__name__} "
                        f"failed: {e}. Retrying in {delay:.2f}s..."
                    )
                    
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    
    return decorator


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    healthy: bool
    message: str = ""
    timestamp: datetime = field(default_factory=get_utc_now)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "healthy": self.healthy,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details
        }


class HealthCheck:
    """
    Health check system for monitoring service availability.
    
    Allows registration of health check functions and execution of all checks.
    
    Example:
        health_check = HealthCheck()
        
        def check_database():
            # Check database connection
            return True, "Database is healthy"
        
        health_check.register("database", check_database)
        results = health_check.run_all()
        is_healthy = health_check.is_system_healthy()
    """
    
    def __init__(self):
        self._checks: Dict[str, Callable] = {}
        logger.info("HealthCheck system initialized")
    
    def register(self, name: str, check_func: Callable) -> None:
        """
        Register a health check function.
        
        Args:
            name: Unique name for the health check
            check_func: Function that returns (bool, str) or just bool
                       True/False indicates health status
                       Optional string provides additional message
                       
        Example:
            def check_api():
                return True, "API is responding"
            
            health_check.register("api", check_api)
        """
        if name in self._checks:
            logger.warning(f"Overwriting existing health check: {name}")
        
        self._checks[name] = check_func
        logger.info(f"Health check '{name}' registered")
    
    def run_all(self) -> Dict[str, HealthCheckResult]:
        """
        Run all registered health checks.
        
        Returns:
            Dictionary mapping check names to HealthCheckResult objects
        """
        results = {}
        
        logger.info(f"Running {len(self._checks)} health checks...")
        
        # Make a copy of checks to avoid RuntimeError if checks are registered during iteration
        checks_snapshot = dict(self._checks)
        
        for name, check_func in checks_snapshot.items():
            try:
                result = check_func()
                
                # Handle different return types
                if isinstance(result, tuple):
                    healthy, message = result[0], result[1] if len(result) > 1 else ""
                    details = result[2] if len(result) > 2 else {}
                elif isinstance(result, bool):
                    healthy, message, details = result, "", {}
                else:
                    healthy = bool(result)
                    message = ""
                    details = {}
                
                results[name] = HealthCheckResult(
                    name=name,
                    healthy=healthy,
                    message=message,
                    details=details
                )
                
                status = "✅ PASS" if healthy else "❌ FAIL"
                logger.info(f"Health check '{name}': {status}")
                
            except Exception as e:
                logger.error(f"Health check '{name}' raised exception: {e}", exc_info=True)
                results[name] = HealthCheckResult(
                    name=name,
                    healthy=False,
                    message=f"Check failed with exception: {str(e)}"
                )
        
        return results
    
    def is_system_healthy(self) -> bool:
        """
        Check if all registered health checks pass.
        
        Returns:
            True if all checks pass, False otherwise
        """
        results = self.run_all()
        return all(result.healthy for result in results.values())
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system health status.
        
        Returns:
            Dictionary with overall status and individual check results
        """
        results = self.run_all()
        all_healthy = all(result.healthy for result in results.values())
        
        return {
            "healthy": all_healthy,
            "timestamp": get_utc_now().isoformat(),
            "checks": {name: result.to_dict() for name, result in results.items()},
            "summary": {
                "total": len(results),
                "passed": sum(1 for r in results.values() if r.healthy),
                "failed": sum(1 for r in results.values() if not r.healthy)
            }
        }


# Global health check instance for convenience
health_check = HealthCheck()


__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "circuit_breaker",
    "retry_with_backoff",
    "HealthCheck",
    "HealthCheckResult",
    "health_check",
]
