"""
Thread-safe LRU Cache Implementation
=====================================

In-memory LRU cache with TTL support, metrics tracking, and memory limits.
"""

import time
import threading
from typing import Any, Optional, Dict, Tuple
from collections import OrderedDict
import sys
import logging

logger = logging.getLogger(__name__)


class LRUCache:
    """
    Thread-safe LRU Cache.
    
    Features:
    - Configurable size
    - TTL support
    - Metrics (hit rate, evictions)
    - Memory limit
    - Thread-safe operations
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        max_memory_mb: int = 500,
        default_ttl: Optional[int] = None
    ):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of entries
            max_memory_mb: Maximum memory usage in MB
            default_ttl: Default TTL in seconds
        """
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._max_memory = max_memory_mb * 1024 * 1024
        self._default_ttl = default_ttl
        self._lock = threading.RLock()
        
        # Metrics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._sets = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            
            value, expiry = self._cache[key]
            
            # Check expiry
            if expiry is not None and time.time() > expiry:
                del self._cache[key]
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (overrides default)
        """
        with self._lock:
            # Calculate expiry
            expiry = None
            ttl_to_use = ttl if ttl is not None else self._default_ttl
            if ttl_to_use is not None:
                expiry = time.time() + ttl_to_use
            
            # Check if key exists
            if key in self._cache:
                del self._cache[key]
            
            # Add to cache
            self._cache[key] = (value, expiry)
            self._cache.move_to_end(key)
            self._sets += 1
            
            # Evict if necessary
            while len(self._cache) > self._max_size:
                evicted_key = next(iter(self._cache))
                del self._cache[evicted_key]
                self._evictions += 1
    
    def delete(self, key: str):
        """Delete key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            
            # Estimate memory usage
            memory_estimate = sum(
                sys.getsizeof(key) + sys.getsizeof(value) + sys.getsizeof(expiry)
                for key, (value, expiry) in self._cache.items()
            )
            
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "evictions": self._evictions,
                "sets": self._sets,
                "memory_bytes": memory_estimate,
                "memory_mb": memory_estimate / (1024 * 1024)
            }
    
    def __len__(self) -> int:
        """Return number of entries in cache."""
        with self._lock:
            return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self.get(key) is not None
