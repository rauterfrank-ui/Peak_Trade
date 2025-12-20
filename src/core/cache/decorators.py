"""
Cache Decorators
================

Decorators for easy caching of function results.
"""

import functools
import hashlib
import json
import logging
from typing import Callable, Optional, Any

from .multi_level_cache import MultiLevelCache

logger = logging.getLogger(__name__)

# Global cache instance
_global_cache: Optional[MultiLevelCache] = None


def get_global_cache() -> MultiLevelCache:
    """Get or create global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = MultiLevelCache()
    return _global_cache


def cached(
    ttl: Optional[int] = 300,
    cache_level: str = "memory",
    key_prefix: Optional[str] = None
):
    """
    Cache decorator for function results.
    
    Args:
        ttl: TTL in seconds (None = no expiry)
        cache_level: "memory" (L1 only) or "full" (all levels)
        key_prefix: Optional key prefix
        
    Usage:
        @cached(ttl=300, cache_level="memory")
        def expensive_calculation(x, y):
            return x * y
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key
            cache_key = _generate_cache_key(func, args, kwargs, key_prefix)
            
            # Try to get from cache
            cache = get_global_cache()
            
            if cache_level == "memory":
                # Only use L1 cache
                result = cache.l1.get(cache_key)
                if result is not None:
                    logger.debug(f"Cache hit (L1): {func.__name__}")
                    return result
            else:
                # Use multi-level cache
                result = cache.get(cache_key)
                if result is not None:
                    logger.debug(f"Cache hit (multi-level): {func.__name__}")
                    return result
            
            # Cache miss - execute function
            logger.debug(f"Cache miss: {func.__name__}")
            result = func(*args, **kwargs)
            
            # Store in cache
            if cache_level == "memory":
                cache.l1.set(cache_key, result, ttl=ttl)
            else:
                cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


def _generate_cache_key(
    func: Callable,
    args: tuple,
    kwargs: dict,
    prefix: Optional[str] = None
) -> str:
    """
    Generate cache key from function and arguments.
    
    Args:
        func: Function
        args: Positional arguments
        kwargs: Keyword arguments
        prefix: Optional prefix
        
    Returns:
        Cache key string
    """
    # Build key components
    key_parts = [
        prefix or func.__module__,
        func.__name__
    ]
    
    # Add arguments to key
    try:
        # Try to serialize arguments
        args_str = json.dumps(args, sort_keys=True)
        kwargs_str = json.dumps(kwargs, sort_keys=True)
        key_parts.append(args_str)
        key_parts.append(kwargs_str)
    except (TypeError, ValueError):
        # Fallback to str representation
        key_parts.append(str(args))
        key_parts.append(str(sorted(kwargs.items())))
    
    # Create hash of key parts
    key_str = "|".join(key_parts)
    key_hash = hashlib.md5(key_str.encode()).hexdigest()
    
    return f"{func.__name__}_{key_hash}"
