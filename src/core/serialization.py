"""
Fast Serialization and Compression
===================================

Fast serialization with msgpack and zstd compression.
"""

import pickle
import logging
from typing import Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class FastSerializer:
    """
    Fast serialization with compression.
    
    - msgpack: 3x faster than pickle
    - zstd: Better compression than gzip
    """
    
    def __init__(
        self,
        use_msgpack: bool = False,
        use_compression: bool = True,
        compression_level: int = 3
    ):
        """
        Initialize serializer.
        
        Args:
            use_msgpack: Use msgpack (requires msgpack package)
            use_compression: Use zstd compression
            compression_level: Compression level (1-22, default 3)
        """
        self.use_msgpack = use_msgpack
        self.use_compression = use_compression
        self.compression_level = compression_level
        
        # Check msgpack availability
        if use_msgpack:
            try:
                import msgpack
                self.msgpack = msgpack
            except ImportError:
                logger.warning("msgpack not available, falling back to pickle")
                self.use_msgpack = False
        
        # Check zstd availability
        if use_compression:
            try:
                import zstandard as zstd
                self.zstd = zstd
            except ImportError:
                logger.warning("zstandard not available, compression disabled")
                self.use_compression = False
    
    def serialize(self, obj: Any) -> bytes:
        """
        Serialize with msgpack/pickle + zstd.
        
        Args:
            obj: Object to serialize
            
        Returns:
            Serialized bytes
        """
        # Serialize
        if self.use_msgpack:
            try:
                packed = self.msgpack.packb(obj, use_bin_type=True)
            except Exception as e:
                logger.debug(f"msgpack serialization failed, using pickle: {e}")
                packed = pickle.dumps(obj)
        else:
            packed = pickle.dumps(obj)
        
        # Compress
        if self.use_compression:
            try:
                compressor = self.zstd.ZstdCompressor(level=self.compression_level)
                compressed = compressor.compress(packed)
                return compressed
            except Exception as e:
                logger.warning(f"Compression failed: {e}")
                return packed
        
        return packed
    
    def deserialize(self, data: bytes) -> Any:
        """
        Deserialize from msgpack/pickle + zstd.
        
        Args:
            data: Serialized bytes
            
        Returns:
            Deserialized object
        """
        # Decompress
        if self.use_compression:
            try:
                decompressor = self.zstd.ZstdDecompressor()
                decompressed = decompressor.decompress(data)
            except Exception as e:
                logger.debug(f"Decompression failed, assuming uncompressed: {e}")
                decompressed = data
        else:
            decompressed = data
        
        # Deserialize
        if self.use_msgpack:
            try:
                return self.msgpack.unpackb(decompressed, raw=False)
            except Exception as e:
                logger.debug(f"msgpack deserialization failed, using pickle: {e}")
                return pickle.loads(decompressed)
        else:
            return pickle.loads(decompressed)


def save_optimized_parquet(
    df: pd.DataFrame,
    path: str,
    compression: str = "snappy",
    row_group_size: int = 100000
):
    """
    Save Parquet with optimal settings.
    
    - snappy compression (fast)
    - row_group_size optimized
    - use_dictionary for string columns
    
    Args:
        df: DataFrame to save
        path: Output path
        compression: Compression codec (snappy, gzip, zstd)
        row_group_size: Row group size for Parquet
    """
    try:
        df.to_parquet(
            path,
            compression=compression,
            engine="pyarrow",
            index=False,
            use_dictionary=True,
            row_group_size=row_group_size
        )
        logger.info(f"Saved optimized Parquet: {path}")
    except Exception as e:
        logger.error(f"Failed to save Parquet: {e}")
        raise


def load_optimized_parquet(path: str) -> pd.DataFrame:
    """
    Load Parquet with optimal settings.
    
    Args:
        path: Input path
        
    Returns:
        DataFrame
    """
    try:
        df = pd.read_parquet(path, engine="pyarrow")
        logger.info(f"Loaded optimized Parquet: {path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load Parquet: {e}")
        raise


# Global serializer instance
_global_serializer = FastSerializer()


def serialize(obj: Any) -> bytes:
    """Convenience function for serialization."""
    return _global_serializer.serialize(obj)


def deserialize(data: bytes) -> Any:
    """Convenience function for deserialization."""
    return _global_serializer.deserialize(data)
