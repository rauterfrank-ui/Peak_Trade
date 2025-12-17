"""
Retry Logic with Exponential Backoff
======================================

Provides configurable retry logic with exponential backoff
for transient failures.

Usage:
    from src.infra.resilience import retry_with_backoff
    
    @retry_with_backoff(max_attempts=3, base_delay=1.0)
    def unstable_function():
        # Function that might fail transiently
        pass
"""

from __future__ import annotations

import functools
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, Set, Tuple, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryPolicy:
    """Configuration for retry behavior."""
    
    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_exceptions: Optional[Tuple[Type[Exception], ...]] = None
    
    def __post_init__(self):
        """Validate configuration."""
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.base_delay < 0:
            raise ValueError("base_delay must be >= 0")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if self.exponential_base < 1:
            raise ValueError("exponential_base must be >= 1")


class MaxRetriesExceeded(Exception):
    """Raised when max retries exceeded."""
    
    def __init__(self, attempts: int, last_exception: Exception):
        self.attempts = attempts
        self.last_exception = last_exception
        super().__init__(
            f"Max retries ({attempts}) exceeded. "
            f"Last error: {type(last_exception).__name__}: {last_exception}"
        )


def calculate_backoff_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
    exponential_base: float,
    jitter: bool = True,
) -> float:
    """
    Calculate delay for exponential backoff.
    
    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        jitter: Whether to add random jitter
        
    Returns:
        Delay in seconds
    """
    import random
    
    # Calculate exponential delay
    delay = base_delay * (exponential_base ** attempt)
    
    # Cap at max_delay
    delay = min(delay, max_delay)
    
    # Add jitter (±25%)
    if jitter:
        jitter_range = delay * 0.25
        delay += random.uniform(-jitter_range, jitter_range)
        delay = max(0, delay)  # Ensure non-negative
    
    return delay


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: Optional[Tuple[Type[Exception], ...]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        base_delay: Base delay in seconds (default: 1s)
        max_delay: Maximum delay in seconds (default: 60s)
        exponential_base: Base for exponential calculation (default: 2)
        jitter: Whether to add random jitter (default: True)
        retry_on: Tuple of exception types to retry on (None = retry all)
        
    Returns:
        Decorated function
        
    Example:
        @retry_with_backoff(max_attempts=3, base_delay=1.0)
        def fetch_data():
            # Network call that might fail
            pass
    """
    policy = RetryPolicy(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
        retry_on_exceptions=retry_on,
    )
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None
            
            for attempt in range(policy.max_attempts):
                try:
                    result = func(*args, **kwargs)
                    
                    # Log success if this was a retry
                    if attempt > 0:
                        logger.info(
                            f"Function '{func.__name__}' succeeded on attempt {attempt + 1}"
                        )
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if we should retry this exception
                    if policy.retry_on_exceptions is not None:
                        if not isinstance(e, policy.retry_on_exceptions):
                            logger.debug(
                                f"Exception {type(e).__name__} not in retry list, "
                                f"not retrying"
                            )
                            raise
                    
                    # If this was the last attempt, raise
                    if attempt == policy.max_attempts - 1:
                        logger.error(
                            f"Function '{func.__name__}' failed after "
                            f"{policy.max_attempts} attempts: {e}"
                        )
                        raise MaxRetriesExceeded(
                            attempts=policy.max_attempts,
                            last_exception=e,
                        )
                    
                    # Calculate delay for next attempt
                    delay = calculate_backoff_delay(
                        attempt=attempt,
                        base_delay=policy.base_delay,
                        max_delay=policy.max_delay,
                        exponential_base=policy.exponential_base,
                        jitter=policy.jitter,
                    )
                    
                    logger.warning(
                        f"Function '{func.__name__}' failed on attempt {attempt + 1}, "
                        f"retrying in {delay:.2f}s... Error: {e}"
                    )
                    
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            else:
                raise RuntimeError("Unexpected retry state")
        
        return wrapper
    
    return decorator


class RetryWithBackoff:
    """
    Class-based retry context manager.
    
    Usage:
        retry = RetryWithBackoff(max_attempts=3)
        for attempt in retry:
            with attempt:
                # Try operation
                pass
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """Initialize retry context."""
        self.policy = RetryPolicy(
            max_attempts=max_attempts,
            base_delay=base_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
        )
        self.attempt_number = 0
        self.last_exception: Optional[Exception] = None
    
    def __iter__(self):
        """Iterate over attempts."""
        return self
    
    def __next__(self):
        """Get next attempt."""
        if self.attempt_number >= self.policy.max_attempts:
            if self.last_exception:
                raise MaxRetriesExceeded(
                    attempts=self.policy.max_attempts,
                    last_exception=self.last_exception,
                )
            else:
                raise StopIteration
        
        self.attempt_number += 1
        return RetryAttempt(self)


class RetryAttempt:
    """Single retry attempt context manager."""
    
    def __init__(self, retry: RetryWithBackoff):
        """Initialize attempt."""
        self.retry = retry
        self.success = False
    
    def __enter__(self):
        """Enter attempt context."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit attempt context."""
        if exc_type is None:
            # Success
            self.success = True
            return True  # Stop iteration
        
        # Failure
        self.retry.last_exception = exc_val
        
        # If this is not the last attempt, sleep and continue
        if self.retry.attempt_number < self.retry.policy.max_attempts:
            delay = calculate_backoff_delay(
                attempt=self.retry.attempt_number - 1,
                base_delay=self.retry.policy.base_delay,
                max_delay=self.retry.policy.max_delay,
                exponential_base=self.retry.policy.exponential_base,
                jitter=self.retry.policy.jitter,
            )
            
            logger.warning(
                f"Attempt {self.retry.attempt_number} failed, "
                f"retrying in {delay:.2f}s... Error: {exc_val}"
            )
            
            time.sleep(delay)
            return True  # Suppress exception, continue iteration
        
        # Last attempt, let exception propagate
        return False
