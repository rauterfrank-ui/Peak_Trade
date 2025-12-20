"""
Multi-Level Cache System
=========================

Multi-level caching with L1 (in-memory), L2 (Redis), and L3 (disk) support.
"""

import pickle
import logging
from typing import Any, Optional
from pathlib import Path

from .lru_cache import LRUCache

logger = logging.getLogger(__name__)


class MultiLevelCache:
    """
    Multi-Level Caching System.
    
    Levels:
    - L1: In-Memory LRU Cache (fastest)
    - L2: Redis Cache (shared, fast) - optional
    - L3: Disk Cache (Parquet/pickle files)
    
    Features:
    - Automatic cache invalidation
    - TTL support
    - Cache warming
    - Hit/Miss metrics
    """
    
    def __init__(
        self,
        l1_size: int = 1000,
        l1_ttl: int = 300,
        l2_enabled: bool = False,
        l2_host: str = "localhost",
        l2_port: int = 6379,
        l3_enabled: bool = True,
        l3_path: Optional[str] = None
    ):
        """
        Initialize multi-level cache.
        
        Args:
            l1_size: L1 cache size (number of entries)
            l1_ttl: L1 cache TTL in seconds
            l2_enabled: Enable Redis L2 cache
            l2_host: Redis host
            l2_port: Redis port
            l3_enabled: Enable disk L3 cache
            l3_path: Disk cache path
        """
        # L1: In-memory LRU cache
        self.l1 = LRUCache(max_size=l1_size, default_ttl=l1_ttl)
        
        # L2: Redis cache (optional)
        self.l2_enabled = l2_enabled
        self.l2 = None
        if l2_enabled:
            try:
                from .redis_cache import RedisCache
                self.l2 = RedisCache(host=l2_host, port=l2_port)
                logger.info(f"Redis L2 cache enabled: {l2_host}:{l2_port}")
            except ImportError:
                logger.warning("Redis not available, L2 cache disabled")
                self.l2_enabled = False
            except Exception as e:
                logger.warning(f"Failed to initialize Redis L2 cache: {e}")
                self.l2_enabled = False
        
        # L3: Disk cache
        self.l3_enabled = l3_enabled
        self.l3_path = Path(l3_path) if l3_path else Path("data/cache")
        if l3_enabled:
            self.l3_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Disk L3 cache enabled: {self.l3_path}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get from cache (L1 → L2 → L3).
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        # Try L1 (in-memory)
        value = self.l1.get(key)
        if value is not None:
            logger.debug(f"Cache hit L1: {key}")
            return value
        
        # Try L2 (Redis)
        if self.l2_enabled and self.l2:
            value = self.l2.get(key)
            if value is not None:
                logger.debug(f"Cache hit L2: {key}")
                # Promote to L1
                self.l1.set(key, value)
                return value
        
        # Try L3 (Disk)
        if self.l3_enabled:
            value = self._l3_get(key)
            if value is not None:
                logger.debug(f"Cache hit L3: {key}")
                # Promote to L1 and L2
                self.l1.set(key, value)
                if self.l2_enabled and self.l2:
                    self.l2.set(key, value)
                return value
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """
        Set in all cache levels.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds
        """
        # Set in L1
        self.l1.set(key, value, ttl=ttl)
        
        # Set in L2
        if self.l2_enabled and self.l2:
            self.l2.set(key, value, ttl=ttl)
        
        # Set in L3
        if self.l3_enabled:
            self._l3_set(key, value)
    
    def delete(self, key: str):
        """Delete from all cache levels."""
        self.l1.delete(key)
        
        if self.l2_enabled and self.l2:
            self.l2.delete(key)
        
        if self.l3_enabled:
            self._l3_delete(key)
    
    def clear(self):
        """Clear all cache levels."""
        self.l1.clear()
        
        if self.l2_enabled and self.l2:
            self.l2.clear()
        
        if self.l3_enabled:
            import shutil
            if self.l3_path.exists():
                shutil.rmtree(self.l3_path)
                self.l3_path.mkdir(parents=True, exist_ok=True)
    
    def get_stats(self) -> dict:
        """Get cache statistics for all levels."""
        stats = {
            "l1": self.l1.get_stats(),
            "l2": None,
            "l3": None
        }
        
        if self.l2_enabled and self.l2:
            stats["l2"] = self.l2.get_stats()
        
        if self.l3_enabled:
            stats["l3"] = self._l3_stats()
        
        return stats
    
    def _l3_get(self, key: str) -> Optional[Any]:
        """Get value from L3 disk cache."""
        try:
            cache_file = self.l3_path / f"{key}.pkl"
            if cache_file.exists():
                with open(cache_file, "rb") as f:
                    return pickle.load(f)
        except Exception as e:
            logger.warning(f"L3 cache read error for {key}: {e}")
        return None
    
    def _l3_set(self, key: str, value: Any):
        """Set value in L3 disk cache."""
        try:
            cache_file = self.l3_path / f"{key}.pkl"
            with open(cache_file, "wb") as f:
                pickle.dump(value, f)
        except Exception as e:
            logger.warning(f"L3 cache write error for {key}: {e}")
    
    def _l3_delete(self, key: str):
        """Delete value from L3 disk cache."""
        try:
            cache_file = self.l3_path / f"{key}.pkl"
            if cache_file.exists():
                cache_file.unlink()
        except Exception as e:
            logger.warning(f"L3 cache delete error for {key}: {e}")
    
    def _l3_stats(self) -> dict:
        """Get L3 cache statistics."""
        try:
            files = list(self.l3_path.glob("*.pkl"))
            total_size = sum(f.stat().st_size for f in files)
            return {
                "files": len(files),
                "size_bytes": total_size,
                "size_mb": total_size / (1024 * 1024)
            }
        except Exception as e:
            logger.warning(f"L3 cache stats error: {e}")
            return {"files": 0, "size_bytes": 0, "size_mb": 0}
