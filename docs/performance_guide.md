# Performance Optimization Guide

## Overview

This guide covers performance optimization techniques for Peak Trade, with a focus on Apple Silicon (M1/M2/M3) hardware.

## Table of Contents

1. [Apple Silicon Optimizations](#apple-silicon-optimizations)
2. [Caching Best Practices](#caching-best-practices)
3. [Parallel Processing](#parallel-processing)
4. [Database Optimization](#database-optimization)
5. [Memory Optimization](#memory-optimization)
6. [Profiling Tools](#profiling-tools)

## Apple Silicon Optimizations

### NumPy Acceleration

Peak Trade automatically configures NumPy for Apple Silicon on startup:

```python
from src.core.numpy_accel import configure_numpy_for_apple_silicon

# Manual configuration (optional)
configure_numpy_for_apple_silicon(num_threads=8)
```

This configures:
- Accelerate Framework usage
- OpenBLAS thread count
- Optimal thread configuration for M-series chips

### CPU Core Selection

Apple Silicon has performance and efficiency cores:
- **M2 Pro**: 8 performance + 4 efficiency = 12 total
- **M3 Pro**: 6 performance + 6 efficiency = 12 total

For CPU-bound tasks (backtests, calculations), use performance cores:

```python
from src.core.parallel import get_cpu_info, parallel_backtest

cpu_info = get_cpu_info()
print(f"Performance cores: {cpu_info['performance_cores']}")

# Run parallel backtests on performance cores
results = parallel_backtest(
    strategies,
    data,
    backtest_func,
    max_workers=cpu_info['performance_cores']
)
```

### Memory Optimization

Optimize DataFrame memory usage:

```python
from src.core.numpy_accel import optimize_dataframe_memory

# Reduce memory footprint by 50-70%
df = optimize_dataframe_memory(df)
```

This applies:
- Integer/float downcasting
- Category dtype for low-cardinality strings
- Sparse arrays for sparse data

## Caching Best Practices

### Multi-Level Cache

Peak Trade uses a 3-level cache system:

1. **L1**: In-memory LRU cache (fastest, ~1μs)
2. **L2**: Redis cache (fast, shared, ~1ms) - optional
3. **L3**: Disk cache (slower, persistent, ~10ms)

```python
from src.core.cache import MultiLevelCache

cache = MultiLevelCache(
    l1_size=1000,      # 1000 entries in memory
    l1_ttl=300,        # 5 minute TTL
    l2_enabled=False,  # Redis optional
    l3_enabled=True,   # Disk cache enabled
    l3_path="data/cache"
)

# Set value (goes to all levels)
cache.set("key", value)

# Get value (L1 → L2 → L3)
value = cache.get("key")
```

### Cache Decorators

Use decorators for automatic caching:

```python
from src.core.cache.decorators import cached

@cached(ttl=300, cache_level="memory")
def expensive_calculation(symbol: str) -> float:
    # Heavy calculation
    return result

@cached(ttl=3600, cache_level="full")
def load_historical_data(symbol: str) -> pd.DataFrame:
    # Data loading
    return data
```

### Cache Hit Rate

Monitor cache effectiveness:

```python
cache = get_global_cache()
stats = cache.get_stats()

print(f"L1 hit rate: {stats['l1']['hit_rate']:.1%}")
print(f"L1 size: {stats['l1']['size']}/{stats['l1']['max_size']}")
```

Target: >80% hit rate for optimal performance.

## Parallel Processing

### CPU-Bound Tasks

Use processes for CPU-bound tasks (backtests, calculations):

```python
from src.core.parallel import parallel_map

def calculate_indicators(data):
    # CPU-intensive calculation
    return result

# Parallel execution on performance cores
results = parallel_map(
    calculate_indicators,
    datasets,
    use_processes=True,
    max_workers=8
)
```

### I/O-Bound Tasks

Use threads for I/O-bound tasks (API calls, file I/O):

```python
# Async data loading
from src.data.async_loader import load_multiple_symbols_async

data = await load_multiple_symbols_async(
    symbols=["BTC/USD", "ETH/USD", "SOL/USD"],
    timeframe="1h",
    loader_func=load_data,
    max_concurrent=10
)
```

### Task Manager

Use the task manager for mixed workloads:

```python
from src.core.parallel import get_task_manager

task_mgr = get_task_manager()

# CPU-bound tasks
cpu_results = task_mgr.execute_cpu_tasks(heavy_calc, items)

# I/O-bound tasks
io_results = task_mgr.execute_io_tasks(fetch_data, urls)
```

## Database Optimization

### Indexes

Apply recommended indexes:

```python
from src.data.query_profiler import optimize_database

optimize_database("data/trades.db")
```

This creates indexes on:
- `trades.timestamp`
- `trades.symbol`
- `portfolio_history.date`
- Composite indexes for common queries

### Batch Operations

Use batch operations for better performance:

```python
from src.data.query_profiler import batch_insert_trades

# 10x faster than individual inserts
batch_insert_trades(db_conn, trades)
```

### Query Profiling

Profile slow queries:

```python
from src.data.query_profiler import QueryProfiler

profiler = QueryProfiler(slow_query_threshold=0.1)
profile = profiler.profile_query(db_conn, "SELECT * FROM trades")

if profile.is_slow:
    print(f"Slow query: {profile.execution_time:.3f}s")
```

## Memory Optimization

### DataFrame Memory

Estimate and optimize memory:

```python
from src.core.numpy_accel import (
    estimate_dataframe_memory,
    optimize_dataframe_memory
)

# Check memory usage
stats = estimate_dataframe_memory(df)
print(f"Memory: {stats['total_mb']:.1f} MB")

# Optimize
df = optimize_dataframe_memory(df)
```

### Parquet Optimization

Use optimized Parquet I/O:

```python
from src.core.serialization import (
    save_optimized_parquet,
    load_optimized_parquet
)

# Save with optimal settings
save_optimized_parquet(df, "data/ohlcv.parquet")

# Load
df = load_optimized_parquet("data/ohlcv.parquet")
```

Settings:
- Snappy compression (fast)
- Dictionary encoding for strings
- Optimized row group size

## Profiling Tools

### Benchmark Framework

Use the benchmark framework to measure performance:

```python
from tests.performance.benchmark import PerformanceBenchmark

benchmark = PerformanceBenchmark()

result = benchmark.run(
    lambda: my_function(),
    name="my_benchmark",
    iterations=100,
    warmup=10
)

print(result)  # Mean, median, std, min, max, memory
```

### Performance Tests

Run performance tests:

```bash
# Run all performance tests
pytest tests/performance/ -v

# Run specific test
pytest tests/performance/test_backtest_performance.py -v

# Run with profiling
pytest tests/performance/ --profile
```

### Memory Profiling

Profile memory usage:

```python
import tracemalloc

tracemalloc.start()

# Your code here

current, peak = tracemalloc.get_traced_memory()
print(f"Peak memory: {peak / 1024 / 1024:.1f} MB")

tracemalloc.stop()
```

## Performance Targets

### Benchmarks

Target performance for key operations:

| Operation | Target Time | Max Memory |
|-----------|-------------|------------|
| Backtest (10k bars) | < 5s | < 500 MB |
| Data loading (cache) | < 100ms | - |
| Portfolio update (100 positions) | < 10ms | - |
| Simple calculation | < 50ms | - |

### Cache Hit Rates

| Cache Level | Target Hit Rate |
|-------------|-----------------|
| L1 (memory) | > 80% |
| L2 (Redis) | > 50% |
| L3 (disk) | > 30% |

## Configuration

Performance settings in `config/performance.toml`:

```toml
[performance]
enable_caching = true

[performance.cache]
l1_size = 1000
l1_ttl = 300
l3_enabled = true

[performance.parallel]
max_workers = 8
use_processes = true

[performance.numpy]
num_threads = 8
auto_configure = true
```

## Tips and Best Practices

1. **Use vectorized operations**: Pandas/NumPy vectorization is 10-100x faster than loops
2. **Cache expensive operations**: Use `@cached` decorator for repeated calculations
3. **Batch database operations**: 10x faster than individual operations
4. **Profile before optimizing**: Use benchmarks to identify bottlenecks
5. **Use appropriate parallelization**: Processes for CPU, threads for I/O
6. **Monitor memory usage**: Optimize DataFrames to reduce memory footprint
7. **Use Parquet for data storage**: 5-10x faster than CSV

## Troubleshooting

### Slow Backtests

1. Check if NumPy is using Accelerate Framework
2. Use parallel execution for multiple strategies
3. Enable caching for repeated data access
4. Optimize DataFrame memory usage

### High Memory Usage

1. Use `optimize_dataframe_memory()`
2. Enable disk cache to offload memory
3. Process data in chunks
4. Use Parquet instead of CSV

### Cache Misses

1. Increase L1 cache size
2. Adjust TTL settings
3. Enable L3 disk cache
4. Pre-warm cache for common queries

## See Also

- [Performance Benchmarks](performance_benchmarks.md)
- [Configuration Guide](../README.md)
