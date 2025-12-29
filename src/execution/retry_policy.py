"""
Retry Policy (WP0A - Phase 0 Execution Core)

Retry logic for transient failures.

Design Goals:
- Exponential backoff
- Max retries configuration
- Error taxonomy (retryable vs non-retryable)
- Jitter to avoid thundering herd
"""

import time
import random
from typing import Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# Error Classification
# ============================================================================


class ErrorClass(str, Enum):
    """Error classification for retry decisions"""

    RETRYABLE = "RETRYABLE"          # Transient error, safe to retry
    NON_RETRYABLE = "NON_RETRYABLE"  # Permanent error, do not retry
    FATAL = "FATAL"                   # Fatal error, abort immediately


# Common retryable errors
RETRYABLE_ERRORS = {
    "NetworkError",
    "TimeoutError",
    "ConnectionError",
    "ServiceUnavailable",
    "TooManyRequests",
    "RateLimitExceeded",
}


# Common non-retryable errors
NON_RETRYABLE_ERRORS = {
    "ValidationError",
    "ValueError",
    "InvalidOrder",
    "InsufficientBalance",
    "SymbolNotFound",
    "InvalidPrice",
    "OrderRejected",
}


def classify_error(error: Exception) -> ErrorClass:
    """
    Classify error for retry decision.

    Args:
        error: Exception

    Returns:
        ErrorClass
    """
    error_name = type(error).__name__

    if error_name in RETRYABLE_ERRORS:
        return ErrorClass.RETRYABLE

    if error_name in NON_RETRYABLE_ERRORS:
        return ErrorClass.NON_RETRYABLE

    # Default: assume retryable (conservative)
    return ErrorClass.RETRYABLE


# ============================================================================
# Retry Policy
# ============================================================================


@dataclass
class RetryConfig:
    """Retry configuration"""

    max_retries: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 30.0     # seconds
    exponential_base: float = 2.0
    jitter: bool = True         # Add random jitter
    jitter_factor: float = 0.1  # 10% jitter


class RetryPolicy:
    """
    Retry policy with exponential backoff.

    Features:
    - Exponential backoff (delay *= base^attempt)
    - Jitter (random variation to avoid thundering herd)
    - Max retries cap
    - Error classification (retryable vs non-retryable)
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        """
        Initialize retry policy.

        Args:
            config: Retry configuration (defaults to RetryConfig())
        """
        self.config = config or RetryConfig()

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate backoff delay for attempt.

        Args:
            attempt: Retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff
        delay = self.config.initial_delay * (self.config.exponential_base ** attempt)

        # Cap at max_delay
        delay = min(delay, self.config.max_delay)

        # Add jitter
        if self.config.jitter:
            jitter_range = delay * self.config.jitter_factor
            jitter = random.uniform(-jitter_range, jitter_range)
            delay += jitter

        return max(0, delay)

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if operation should be retried.

        Args:
            error: Exception that occurred
            attempt: Current retry attempt (0-indexed)

        Returns:
            True if should retry, False otherwise
        """
        # Check max retries
        if attempt >= self.config.max_retries:
            return False

        # Classify error
        error_class = classify_error(error)

        # Fatal or non-retryable errors should not be retried
        if error_class in (ErrorClass.FATAL, ErrorClass.NON_RETRYABLE):
            return False

        return True

    def retry(
        self,
        operation: Callable[[], Any],
        error_handler: Optional[Callable[[Exception, int], None]] = None,
    ) -> Any:
        """
        Execute operation with retry logic.

        Args:
            operation: Callable to execute
            error_handler: Optional callback for each error (error, attempt)

        Returns:
            Result of successful operation

        Raises:
            Exception if all retries exhausted or non-retryable error
        """
        attempt = 0
        last_error = None

        while True:
            try:
                return operation()
            except Exception as error:
                last_error = error

                # Call error handler if provided
                if error_handler:
                    error_handler(error, attempt)

                # Check if should retry
                if not self.should_retry(error, attempt):
                    raise error

                # Calculate delay
                delay = self.calculate_delay(attempt)

                # Sleep before retry
                time.sleep(delay)

                attempt += 1

        # Should never reach here, but for type safety
        if last_error:
            raise last_error

    async def retry_async(
        self,
        operation: Callable[[], Any],
        error_handler: Optional[Callable[[Exception, int], None]] = None,
    ) -> Any:
        """
        Execute async operation with retry logic.

        Args:
            operation: Async callable to execute
            error_handler: Optional callback for each error

        Returns:
            Result of successful operation

        Raises:
            Exception if all retries exhausted or non-retryable error
        """
        import asyncio

        attempt = 0
        last_error = None

        while True:
            try:
                return await operation()
            except Exception as error:
                last_error = error

                if error_handler:
                    error_handler(error, attempt)

                if not self.should_retry(error, attempt):
                    raise error

                delay = self.calculate_delay(attempt)
                await asyncio.sleep(delay)

                attempt += 1

        if last_error:
            raise last_error


# ============================================================================
# Helper Functions
# ============================================================================


def create_default_retry_policy() -> RetryPolicy:
    """Create default retry policy"""
    return RetryPolicy(RetryConfig(
        max_retries=3,
        initial_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=True,
    ))


def create_aggressive_retry_policy() -> RetryPolicy:
    """Create aggressive retry policy (more retries, longer delays)"""
    return RetryPolicy(RetryConfig(
        max_retries=5,
        initial_delay=2.0,
        max_delay=60.0,
        exponential_base=2.0,
        jitter=True,
    ))


def create_fast_retry_policy() -> RetryPolicy:
    """Create fast retry policy (fewer retries, shorter delays)"""
    return RetryPolicy(RetryConfig(
        max_retries=2,
        initial_delay=0.5,
        max_delay=5.0,
        exponential_base=1.5,
        jitter=True,
    ))
