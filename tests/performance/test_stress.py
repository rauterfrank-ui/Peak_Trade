"""
Stress Tests for Performance
=============================

Stress tests for parallel execution and high-load scenarios.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from concurrent.futures import as_completed

from tests.performance.benchmark import PerformanceBenchmark
from src.core.parallel import parallel_map, get_cpu_info


@pytest.fixture
def benchmark():
    """Create benchmark instance."""
    return PerformanceBenchmark()


def create_test_strategy(strategy_id: int):
    """Create a test strategy with unique ID."""
    return {
        'id': strategy_id,
        'name': f'Strategy_{strategy_id}',
        'params': {
            'fast_period': np.random.randint(10, 30),
            'slow_period': np.random.randint(40, 100)
        }
    }


def run_simple_backtest(strategy):
    """Run a simple backtest simulation."""
    # Generate synthetic data
    data = pd.DataFrame({
        'close': np.random.uniform(40000, 50000, 1000),
        'volume': np.random.uniform(100, 1000, 1000)
    })
    
    # Simple MA calculation
    data['ma_fast'] = data['close'].rolling(window=strategy['params']['fast_period']).mean()
    data['ma_slow'] = data['close'].rolling(window=strategy['params']['slow_period']).mean()
    data['signal'] = (data['ma_fast'] > data['ma_slow']).astype(int)
    
    # Calculate returns
    total_return = data['signal'].sum() / len(data)
    
    return {
        'strategy_id': strategy['id'],
        'total_return': total_return,
        'num_signals': data['signal'].sum()
    }


@pytest.mark.slow
def test_stress_parallel_backtests(benchmark):
    """
    Stress test: 100 backtests in parallel.
    
    Tests parallel execution under heavy load.
    """
    num_strategies = 100
    strategies = [create_test_strategy(i) for i in range(num_strategies)]
    
    cpu_info = get_cpu_info()
    max_workers = cpu_info['performance_cores']
    
    def run_all_backtests():
        results = parallel_map(
            run_simple_backtest,
            strategies,
            max_workers=max_workers,
            use_processes=True
        )
        return results
    
    result = benchmark.run(
        run_all_backtests,
        name="stress_parallel_backtests",
        iterations=1,
        warmup=0
    )
    
    # Should complete in reasonable time
    assert result.mean_time < 60, f"Parallel backtests too slow: {result.mean_time:.1f}s"
    
    # Memory should be reasonable
    assert result.memory_peak_mb < 1000, f"Memory usage too high: {result.memory_peak_mb:.1f}MB"


@pytest.mark.slow
def test_stress_cache_operations(benchmark):
    """
    Stress test: High volume cache operations.
    
    Tests cache performance under load.
    """
    from src.core.cache import LRUCache
    
    cache = LRUCache(max_size=10000, max_memory_mb=500)
    
    # Pre-populate cache
    for i in range(1000):
        cache.set(f"key_{i}", f"value_{i}" * 100)
    
    def cache_operations():
        # Mix of gets and sets
        for i in range(1000):
            if i % 2 == 0:
                cache.get(f"key_{i % 1000}")
            else:
                cache.set(f"key_{i}", f"value_{i}" * 100)
    
    result = benchmark.run(
        cache_operations,
        name="stress_cache_operations",
        iterations=10,
        warmup=2
    )
    
    # Should handle high volume
    assert result.mean_time < 0.5, f"Cache operations too slow: {result.mean_time:.3f}s"


@pytest.mark.slow
def test_stress_dataframe_operations(benchmark):
    """
    Stress test: Large DataFrame operations.
    
    Tests DataFrame performance with large datasets.
    """
    # Create large dataset
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=100000),
        periods=100000,
        freq='1h'
    )
    
    large_df = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.uniform(40000, 50000, 100000),
        'high': np.random.uniform(40000, 50000, 100000),
        'low': np.random.uniform(40000, 50000, 100000),
        'close': np.random.uniform(40000, 50000, 100000),
        'volume': np.random.uniform(100, 1000, 100000)
    })
    
    def process_dataframe():
        df = large_df.copy()
        
        # Multiple operations
        df['returns'] = df['close'].pct_change()
        df['ma_20'] = df['close'].rolling(window=20).mean()
        df['ma_50'] = df['close'].rolling(window=50).mean()
        df['ma_200'] = df['close'].rolling(window=200).mean()
        df['volatility'] = df['returns'].rolling(window=20).std()
        
        # Filter
        df = df[df['volume'] > 500]
        
        return df
    
    result = benchmark.run(
        process_dataframe,
        name="stress_dataframe_operations",
        iterations=5,
        warmup=1
    )
    
    # Should handle large data
    assert result.mean_time < 10, f"DataFrame ops too slow: {result.mean_time:.1f}s"
    assert result.memory_peak_mb < 1500, f"Memory usage too high: {result.memory_peak_mb:.1f}MB"


@pytest.mark.slow
def test_stress_concurrent_updates(benchmark):
    """
    Stress test: Concurrent portfolio updates.
    
    Tests thread safety and concurrent operations.
    """
    from threading import Thread
    import time
    
    # Shared portfolio state
    portfolio = {
        f"SYMBOL{i}/USD": {
            'size': np.random.uniform(0.1, 10),
            'entry_price': np.random.uniform(100, 50000),
            'current_price': np.random.uniform(100, 50000)
        }
        for i in range(100)
    }
    
    def update_prices():
        """Update prices concurrently."""
        for _ in range(100):
            for symbol in portfolio:
                portfolio[symbol]['current_price'] *= (1 + np.random.uniform(-0.001, 0.001))
            time.sleep(0.001)
    
    def calculate_values():
        """Calculate values concurrently."""
        results = []
        for _ in range(100):
            total = sum(
                pos['size'] * pos['current_price']
                for pos in portfolio.values()
            )
            results.append(total)
            time.sleep(0.001)
        return results
    
    def concurrent_operations():
        threads = []
        
        # Start update threads
        for _ in range(4):
            t = Thread(target=update_prices)
            t.start()
            threads.append(t)
        
        # Start calculation threads
        for _ in range(4):
            t = Thread(target=calculate_values)
            t.start()
            threads.append(t)
        
        # Wait for completion
        for t in threads:
            t.join()
    
    result = benchmark.run(
        concurrent_operations,
        name="stress_concurrent_updates",
        iterations=1,
        warmup=0
    )
    
    # Should complete without deadlock
    assert result.mean_time < 15, f"Concurrent ops too slow: {result.mean_time:.1f}s"


@pytest.mark.slow
def test_memory_stability():
    """
    Test memory stability over extended operations.
    
    Ensures no memory leaks during repeated operations.
    """
    from src.core.cache import LRUCache
    import gc
    
    cache = LRUCache(max_size=1000)
    
    # Baseline memory - populate cache first to get realistic baseline
    for i in range(500):
        cache.set(f"init_{i}", f"value_{i}" * 10)
    
    gc.collect()
    initial_size = cache.get_stats()['memory_mb']
    
    # Perform many operations (should not grow unbounded)
    for iteration in range(50):
        # Set many items (cache will evict old ones)
        for i in range(100):
            cache.set(f"key_{iteration}_{i}", f"value_{iteration}_{i}" * 10)
        
        # Get many items
        for i in range(100):
            cache.get(f"key_{iteration}_{i}")
    
    # Final memory
    gc.collect()
    final_size = cache.get_stats()['memory_mb']
    
    # Memory should be stable (within 3x of initial due to cache churn)
    # Using 3x to account for LRU cache dynamics
    max_allowed = max(initial_size * 3, 1.0)  # At least 1MB threshold
    assert final_size < max_allowed, (
        f"Memory leak detected: "
        f"initial={initial_size:.1f}MB, final={final_size:.1f}MB, "
        f"max_allowed={max_allowed:.1f}MB"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "slow"])
