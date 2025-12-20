"""
Data Loading Performance Benchmarks
====================================

Benchmark data loading from various sources and cache layers.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import shutil
from pathlib import Path

from ..performance.benchmark import PerformanceBenchmark
from ...core.cache import MultiLevelCache
from ...core.serialization import save_optimized_parquet, load_optimized_parquet


@pytest.fixture
def benchmark():
    """Create benchmark instance."""
    return PerformanceBenchmark()


@pytest.fixture
def test_data():
    """Create test data."""
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=10000),
        periods=10000,
        freq='1h'
    )
    
    return pd.DataFrame({
        'timestamp': dates,
        'open': np.random.uniform(40000, 50000, 10000),
        'high': np.random.uniform(40000, 50000, 10000),
        'low': np.random.uniform(40000, 50000, 10000),
        'close': np.random.uniform(40000, 50000, 10000),
        'volume': np.random.uniform(100, 1000, 10000)
    })


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_cache_l1_performance(benchmark, test_data):
    """
    Benchmark L1 (in-memory) cache performance.
    
    Should be < 1ms for cache hits.
    """
    cache = MultiLevelCache(
        l1_size=1000,
        l2_enabled=False,
        l3_enabled=False
    )
    
    # Warm cache
    cache.set("test_key", test_data)
    
    # Benchmark cache hit
    result = benchmark.run(
        lambda: cache.get("test_key"),
        name="cache_l1_hit",
        iterations=1000,
        warmup=10
    )
    
    assert result.mean_time < 0.001, f"L1 cache too slow: {result.mean_time:.6f}s"


def test_parquet_load_performance(benchmark, test_data, temp_cache_dir):
    """
    Benchmark Parquet loading performance.
    
    Should be < 100ms for 10k rows.
    """
    parquet_path = Path(temp_cache_dir) / "test_data.parquet"
    
    # Save test data
    save_optimized_parquet(test_data, str(parquet_path))
    
    # Benchmark loading
    result = benchmark.run(
        lambda: load_optimized_parquet(str(parquet_path)),
        name="parquet_load",
        iterations=50,
        warmup=5
    )
    
    assert result.mean_time < 0.1, f"Parquet loading too slow: {result.mean_time:.3f}s"


def test_parquet_save_performance(benchmark, test_data, temp_cache_dir):
    """Benchmark Parquet saving performance."""
    parquet_path = Path(temp_cache_dir) / "test_save.parquet"
    
    result = benchmark.run(
        lambda: save_optimized_parquet(test_data, str(parquet_path)),
        name="parquet_save",
        iterations=20,
        warmup=2
    )
    
    assert result.mean_time < 0.2, f"Parquet saving too slow: {result.mean_time:.3f}s"


def test_dataframe_copy_performance(benchmark, test_data):
    """Benchmark DataFrame copy operations."""
    result = benchmark.run(
        lambda: test_data.copy(),
        name="dataframe_copy",
        iterations=100,
        warmup=10
    )
    
    assert result.mean_time < 0.05, f"DataFrame copy too slow: {result.mean_time:.3f}s"


def test_cache_multilevel_performance(benchmark, test_data, temp_cache_dir):
    """
    Benchmark multi-level cache performance.
    
    Tests L1 miss → L3 hit → L1 promotion.
    """
    cache = MultiLevelCache(
        l1_size=100,  # Small L1 to force evictions
        l2_enabled=False,
        l3_enabled=True,
        l3_path=temp_cache_dir
    )
    
    # Set in cache (goes to all levels)
    cache.set("test_key", test_data)
    
    # Clear L1 to test L3 → L1 promotion
    cache.l1.clear()
    
    # Benchmark L3 hit and promotion
    result = benchmark.run(
        lambda: cache.get("test_key"),
        name="cache_l3_promotion",
        iterations=10,
        warmup=2
    )
    
    # Should be slower than L1 but still fast
    assert result.mean_time < 0.5, f"L3 cache too slow: {result.mean_time:.3f}s"


def test_data_preprocessing_performance(benchmark, test_data):
    """Benchmark common data preprocessing operations."""
    def preprocess():
        df = test_data.copy()
        # Common preprocessing
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        df.dropna(inplace=True)
        return df
    
    result = benchmark.run(
        preprocess,
        name="data_preprocessing",
        iterations=100,
        warmup=10
    )
    
    assert result.mean_time < 0.05, f"Preprocessing too slow: {result.mean_time:.3f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
