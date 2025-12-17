"""
Fallback Strategies
====================

Provides fallback mechanisms for handling failures gracefully.

Usage:
    from src.infra.resilience.fallback import with_fallback
    
    @with_fallback(fallback_value=None)
    def risky_operation():
        # Operation that might fail
        pass
"""

from __future__ import annotations

import functools
import logging
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def with_fallback(
    fallback_value: Optional[T] = None,
    fallback_func: Optional[Callable[..., T]] = None,
    log_errors: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to provide fallback value or function on failure.
    
    Args:
        fallback_value: Value to return on failure
        fallback_func: Function to call on failure (takes same args)
        log_errors: Whether to log errors
        
    Returns:
        Decorated function
        
    Example:
        @with_fallback(fallback_value=[])
        def get_data():
            # Might fail, returns [] on error
            pass
        
        @with_fallback(fallback_func=lambda: get_cached_data())
        def get_live_data():
            # Falls back to cached data on error
            pass
    """
    if fallback_value is not None and fallback_func is not None:
        raise ValueError("Cannot specify both fallback_value and fallback_func")
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(
                        f"Function '{func.__name__}' failed, using fallback: {e}"
                    )
                
                if fallback_func is not None:
                    return fallback_func(*args, **kwargs)
                else:
                    return fallback_value  # type: ignore
        
        return wrapper
    
    return decorator
