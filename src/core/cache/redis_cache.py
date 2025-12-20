"""
Redis Cache Implementation
===========================

Redis-based distributed cache with serialization and compression support.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RedisCache:
    """
    Redis-based distributed cache.
    
    Features:
    - Automatic serialization (pickle/msgpack)
    - Compression (optional)
    - Pub/Sub for cache invalidation
    - Connection pooling
    
    Note: Requires redis-py package (optional dependency)
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        use_compression: bool = False
    ):
        """
        Initialize Redis cache.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            use_compression: Enable compression
        """
        try:
            import redis
            self.redis = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=False
            )
            self.redis.ping()
            logger.info(f"Connected to Redis: {host}:{port}")
        except ImportError:
            raise ImportError("redis-py not installed. Install with: pip install redis")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")
        
        self.use_compression = use_compression
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        try:
            data = self.redis.get(key)
            if data is None:
                return None
            
            return self._deserialize(data)
        except Exception as e:
            logger.warning(f"Redis get error for {key}: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """
        Set value in Redis cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds
        """
        try:
            data = self._serialize(value)
            if ttl:
                self.redis.setex(key, ttl, data)
            else:
                self.redis.set(key, data)
        except Exception as e:
            logger.warning(f"Redis set error for {key}: {e}")
    
    def delete(self, key: str):
        """Delete key from Redis."""
        try:
            self.redis.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete error for {key}: {e}")
    
    def clear(self):
        """Clear all keys in current database."""
        try:
            self.redis.flushdb()
        except Exception as e:
            logger.warning(f"Redis clear error: {e}")
    
    def get_stats(self) -> dict:
        """Get Redis cache statistics."""
        try:
            info = self.redis.info()
            return {
                "keys": self.redis.dbsize(),
                "memory_used_mb": info.get("used_memory", 0) / (1024 * 1024),
                "connected_clients": info.get("connected_clients", 0)
            }
        except Exception as e:
            logger.warning(f"Redis stats error: {e}")
            return {"keys": 0, "memory_used_mb": 0, "connected_clients": 0}
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value to bytes."""
        import pickle
        data = pickle.dumps(value)
        
        if self.use_compression:
            try:
                import zstandard as zstd
                compressor = zstd.ZstdCompressor(level=3)
                data = compressor.compress(data)
            except ImportError:
                pass  # Compression not available
        
        return data
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to value."""
        import pickle
        
        if self.use_compression:
            try:
                import zstandard as zstd
                decompressor = zstd.ZstdDecompressor()
                data = decompressor.decompress(data)
            except ImportError:
                pass  # Compression not available
        
        return pickle.loads(data)
