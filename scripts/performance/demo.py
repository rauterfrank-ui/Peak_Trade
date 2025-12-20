#!/usr/bin/env python3
"""
Performance Optimization Demo
==============================

Demonstrates usage of Peak Trade performance features.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import performance components
from src.core.cache import MultiLevelCache, LRUCache
from src.core.cache.decorators import cached
from src.core.parallel import parallel_map, get_cpu_info
from src.core.numpy_accel import optimize_dataframe_memory, estimate_dataframe_memory
from src.core.serialization import save_optimized_parquet, load_optimized_parquet
from tests.performance.benchmark import PerformanceBenchmark


def demo_caching():
    """Demonstrate caching features."""
    print("\n" + "="*70)
    print("CACHING DEMO")
    print("="*70)
    
    # Create multi-level cache
    cache = MultiLevelCache(
        l1_size=1000,
        l1_ttl=300,
        l3_enabled=False  # Disable disk cache for demo
    )
    
    # Store and retrieve values
    cache.set("key1", "value1")
    cache.set("key2", {"data": [1, 2, 3]})
    
    print(f"✓ Get key1: {cache.get('key1')}")
    print(f"✓ Get key2: {cache.get('key2')}")
    
    # Cache statistics
    stats = cache.get_stats()
    print(f"\n✓ Cache Stats:")
    print(f"  - L1 size: {stats['l1']['size']}/{stats['l1']['max_size']}")
    print(f"  - L1 hit rate: {stats['l1']['hit_rate']:.1%}")
    print(f"  - L1 memory: {stats['l1']['memory_mb']:.2f} MB")
    
    # Decorator example
    @cached(ttl=60, cache_level="memory")
    def expensive_calculation(x):
        return x ** 2
    
    print(f"\n✓ Cached function: {expensive_calculation(10)}")


def demo_benchmarking():
    """Demonstrate benchmarking."""
    print("\n" + "="*70)
    print("BENCHMARKING DEMO")
    print("="*70)
    
    benchmark = PerformanceBenchmark()
    
    # Simple benchmark
    result = benchmark.run(
        lambda: sum(range(10000)),
        name="sum_10k",
        iterations=100,
        warmup=10
    )
    
    print(f"\n✓ Benchmark: {result.name}")
    print(f"  - Mean time: {result.mean_time*1000:.3f} ms")
    print(f"  - Median time: {result.median_time*1000:.3f} ms")
    print(f"  - Std dev: {result.std_time*1000:.3f} ms")
    print(f"  - Memory peak: {result.memory_peak_mb:.2f} MB")


def demo_parallel_processing():
    """Demonstrate parallel processing."""
    print("\n" + "="*70)
    print("PARALLEL PROCESSING DEMO")
    print("="*70)
    
    # CPU info
    cpu_info = get_cpu_info()
    print(f"\n✓ CPU Info:")
    print(f"  - Total cores: {cpu_info['total_cores']}")
    print(f"  - Performance cores: {cpu_info['performance_cores']}")
    print(f"  - Efficiency cores: {cpu_info['efficiency_cores']}")
    
    # Parallel map
    def square(x):
        return x ** 2
    
    numbers = list(range(10))
    results = parallel_map(
        square,
        numbers,
        max_workers=4,
        use_processes=False  # Use threads for demo
    )
    
    print(f"\n✓ Parallel map: {numbers[:5]}... -> {results[:5]}...")


def demo_memory_optimization():
    """Demonstrate memory optimization."""
    print("\n" + "="*70)
    print("MEMORY OPTIMIZATION DEMO")
    print("="*70)
    
    # Create test DataFrame
    df = pd.DataFrame({
        'int_col': np.random.randint(0, 100, 1000),
        'float_col': np.random.uniform(0, 1, 1000),
        'category_col': np.random.choice(['A', 'B', 'C'], 1000)
    })
    
    # Before optimization
    before = estimate_dataframe_memory(df)
    print(f"\n✓ Before optimization:")
    print(f"  - Total memory: {before['total_mb']:.2f} MB")
    
    # Optimize
    df_optimized = optimize_dataframe_memory(df)
    
    # After optimization
    after = estimate_dataframe_memory(df_optimized)
    print(f"\n✓ After optimization:")
    print(f"  - Total memory: {after['total_mb']:.2f} MB")
    print(f"  - Reduction: {(1 - after['total_mb']/before['total_mb'])*100:.1f}%")


def demo_dataframe_performance():
    """Demonstrate DataFrame performance."""
    print("\n" + "="*70)
    print("DATAFRAME PERFORMANCE DEMO")
    print("="*70)
    
    # Create test data
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=1000),
        periods=1000,
        freq='1h'
    )
    
    df = pd.DataFrame({
        'timestamp': dates,
        'close': np.random.uniform(40000, 50000, 1000),
        'volume': np.random.uniform(100, 1000, 1000)
    })
    
    benchmark = PerformanceBenchmark()
    
    # Benchmark vectorized operations
    def vectorized_ops():
        result = df.copy()
        result['ma_20'] = result['close'].rolling(window=20).mean()
        result['ma_50'] = result['close'].rolling(window=50).mean()
        result['returns'] = result['close'].pct_change()
        return result
    
    result = benchmark.run(
        vectorized_ops,
        name="vectorized_ops",
        iterations=50,
        warmup=5
    )
    
    print(f"\n✓ Vectorized operations benchmark:")
    print(f"  - Mean time: {result.mean_time*1000:.3f} ms")
    print(f"  - Memory peak: {result.memory_peak_mb:.2f} MB")


def demo_serialization():
    """Demonstrate serialization."""
    print("\n" + "="*70)
    print("SERIALIZATION DEMO")
    print("="*70)
    
    # Create test DataFrame
    df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=1000, freq='1h'),
        'close': np.random.uniform(40000, 50000, 1000),
        'volume': np.random.uniform(100, 1000, 1000)
    })
    
    # Save to Parquet
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
        path = f.name
    
    try:
        # Benchmark save
        benchmark = PerformanceBenchmark()
        save_result = benchmark.run(
            lambda: save_optimized_parquet(df, path),
            name="parquet_save",
            iterations=10,
            warmup=2
        )
        
        # Benchmark load
        load_result = benchmark.run(
            lambda: load_optimized_parquet(path),
            name="parquet_load",
            iterations=10,
            warmup=2
        )
        
        print(f"\n✓ Parquet I/O performance:")
        print(f"  - Save time: {save_result.mean_time*1000:.3f} ms")
        print(f"  - Load time: {load_result.mean_time*1000:.3f} ms")
        
    finally:
        import os
        if os.path.exists(path):
            os.unlink(path)


def main():
    """Run all demos."""
    print("\n" + "="*70)
    print("PEAK TRADE PERFORMANCE OPTIMIZATION DEMO")
    print("="*70)
    
    demo_caching()
    demo_benchmarking()
    demo_parallel_processing()
    demo_memory_optimization()
    demo_dataframe_performance()
    demo_serialization()
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\nFor more information:")
    print("  - Performance Guide: docs/performance_guide.md")
    print("  - Benchmarks: docs/performance_benchmarks.md")
    print("  - Run tests: python3 scripts/performance/run_benchmarks.py")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
