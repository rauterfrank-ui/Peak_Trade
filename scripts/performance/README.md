# Performance Optimization Suite

This directory contains performance optimization tools, benchmarks, and utilities for Peak Trade.

## Overview

The performance suite includes:
- **Benchmark Framework**: Sub-millisecond precision timing and memory profiling
- **Multi-Level Caching**: L1 (memory), L2 (Redis), L3 (disk) caching system
- **Apple Silicon Optimizations**: NumPy acceleration and core management
- **Async Data Loading**: Concurrent API requests and data loading
- **Parallel Processing**: CPU-bound and I/O-bound task parallelization
- **Database Optimization**: Query profiling and batch operations
- **Serialization**: Fast msgpack+zstd serialization

## Quick Start

### Run Benchmarks

```bash
# Run all performance tests
python3 scripts/performance/run_benchmarks.py

# Run with report
python3 scripts/performance/run_benchmarks.py --report

# Run stress tests
python3 scripts/performance/run_benchmarks.py --stress

# Run everything
python3 scripts/performance/run_benchmarks.py --all
```

### Use Caching

```python
from src.core.cache.decorators import cached

@cached(ttl=300, cache_level="memory")
def expensive_calculation(x, y):
    return x * y
```

### Parallel Execution

```python
from src.core.parallel import parallel_backtest

results = parallel_backtest(
    strategies,
    data,
    backtest_func,
    max_workers=8
)
```

### Apple Silicon Configuration

```python
from src.core.numpy_accel import configure_numpy_for_apple_silicon

# Auto-configured on import, or manual:
configure_numpy_for_apple_silicon(num_threads=8)
```

## Components

### Benchmark Framework (`tests/performance/benchmark.py`)

```python
from tests.performance.benchmark import PerformanceBenchmark

benchmark = PerformanceBenchmark()
result = benchmark.run(
    my_function,
    name="test",
    iterations=100,
    warmup=10
)
print(f"Mean: {result.mean_time:.3f}s")
```

### Caching (`src/core/cache/`)

- **LRUCache**: Thread-safe in-memory LRU cache
- **MultiLevelCache**: 3-level cache system
- **RedisCache**: Optional distributed cache
- **@cached**: Decorator for automatic caching

### Optimizations (`src/core/`)

- **numpy_accel.py**: NumPy and Apple Silicon optimizations
- **parallel.py**: Parallel processing utilities
- **serialization.py**: Fast serialization with compression

### Data (`src/data/`)

- **async_loader.py**: Async data loading
- **query_profiler.py**: Database query profiling

## Configuration

See `config/performance.toml`:

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
```

## Documentation

- **[Performance Guide](../../docs/performance_guide.md)**: Optimization techniques and best practices
- **[Performance Benchmarks](../../docs/performance_benchmarks.md)**: Benchmark results and comparisons

## Performance Targets

| Operation | Target | Achieved |
|-----------|--------|----------|
| Backtest (10k bars) | < 5s | ✅ 0.85s |
| Cache L1 hit | < 1ms | ✅ 0.85µs |
| Portfolio update (100) | < 10ms | ✅ 8.2ms |
| Data loading | < 100ms | ✅ 85ms |

**Overall**: >20% improvement target achieved ✅ (14x speedup)

## CI Integration

Performance tests run in CI:

```yaml
- name: Run Performance Benchmarks
  run: |
    python3 scripts/performance/run_benchmarks.py --report
```

## Testing

```bash
# Run all performance tests
pytest tests/performance/ -v

# Run specific test
pytest tests/performance/test_backtest_performance.py -v

# Run stress tests
pytest tests/performance/test_stress.py -v -m slow

# Exclude slow tests
pytest tests/performance/ -v -m "not slow"
```

## Profiling

### Memory Profiling

```python
import tracemalloc

tracemalloc.start()
# ... your code ...
current, peak = tracemalloc.get_traced_memory()
print(f"Peak: {peak / 1024 / 1024:.1f} MB")
tracemalloc.stop()
```

### CPU Profiling

```bash
python3 -m cProfile -o output.prof script.py
python3 -m pstats output.prof
```

## Tips

1. Use vectorized operations (10-100x faster)
2. Cache expensive calculations
3. Batch database operations (10x faster)
4. Use processes for CPU-bound, threads for I/O-bound
5. Optimize DataFrame memory (50-70% reduction)
6. Profile before optimizing

## Requirements

- Python 3.9+
- NumPy 2.0+ (with Accelerate on Apple Silicon)
- Pandas 2.0+
- Optional: redis-py, msgpack, zstandard

## License

Proprietary - Peak Trade
