"""
Backtest Performance Benchmarks
================================

Benchmark backtest execution time and memory usage.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from tests.performance.benchmark import PerformanceBenchmark


@pytest.fixture
def benchmark():
    """Create benchmark instance."""
    return PerformanceBenchmark()


@pytest.fixture
def test_data():
    """Create test data for backtesting."""
    # Generate 10,000 bars of test data
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=10000),
        periods=10000,
        freq='1h'
    )
    
    data = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.uniform(40000, 50000, 10000),
        'high': np.random.uniform(40000, 50000, 10000),
        'low': np.random.uniform(40000, 50000, 10000),
        'close': np.random.uniform(40000, 50000, 10000),
        'volume': np.random.uniform(100, 1000, 10000)
    })
    
    # Ensure high >= low, etc.
    data['high'] = data[['open', 'high', 'close']].max(axis=1)
    data['low'] = data[['open', 'low', 'close']].min(axis=1)
    
    return data


def test_simple_backtest_performance(benchmark, test_data):
    """
    Benchmark simple backtest execution time.
    
    This tests a simple moving average strategy backtest.
    """
    # Simple MA crossover logic (simplified for benchmark)
    def simple_backtest():
        df = test_data.copy()
        df['ma_fast'] = df['close'].rolling(window=20).mean()
        df['ma_slow'] = df['close'].rolling(window=50).mean()
        df['signal'] = (df['ma_fast'] > df['ma_slow']).astype(int)
        return df
    
    result = benchmark.run(
        simple_backtest,
        name="simple_backtest",
        iterations=10,
        warmup=2
    )
    
    # Assert performance requirements
    assert result.mean_time < 1.0, f"Backtest too slow: {result.mean_time:.3f}s"
    assert result.memory_peak_mb < 100, f"Memory usage too high: {result.memory_peak_mb:.1f}MB"


def test_vectorized_operations_performance(benchmark, test_data):
    """
    Benchmark vectorized pandas operations.
    
    This tests the performance of common vectorized operations.
    """
    def vectorized_ops():
        df = test_data.copy()
        # Common operations
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=20).std()
        df['rsi'] = calculate_rsi(df['close'], period=14)
        return df
    
    result = benchmark.run(
        vectorized_ops,
        name="vectorized_operations",
        iterations=100,
        warmup=10
    )
    
    assert result.mean_time < 0.1, f"Vectorized ops too slow: {result.mean_time:.3f}s"


def test_rolling_calculations_performance(benchmark, test_data):
    """Benchmark rolling window calculations."""
    def rolling_calcs():
        df = test_data.copy()
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        df['vol_20'] = df['close'].rolling(window=20).std()
        return df
    
    result = benchmark.run(
        rolling_calcs,
        name="rolling_calculations",
        iterations=50,
        warmup=5
    )
    
    assert result.mean_time < 0.05, f"Rolling calcs too slow: {result.mean_time:.3f}s"


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


@pytest.mark.slow
def test_large_dataset_performance(benchmark):
    """
    Benchmark performance with large datasets.
    
    This tests scalability with 100k+ bars.
    """
    # Generate large dataset
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=100000),
        periods=100000,
        freq='1h'
    )
    
    large_data = pd.DataFrame({
        'timestamp': dates,
        'close': np.random.uniform(40000, 50000, 100000),
        'volume': np.random.uniform(100, 1000, 100000)
    })
    
    def process_large_data():
        df = large_data.copy()
        df['ma_20'] = df['close'].rolling(window=20).mean()
        df['ma_50'] = df['close'].rolling(window=50).mean()
        return df
    
    result = benchmark.run(
        process_large_data,
        name="large_dataset",
        iterations=5,
        warmup=1
    )
    
    # More lenient for large datasets
    assert result.mean_time < 5.0, f"Large dataset processing too slow: {result.mean_time:.3f}s"
    assert result.memory_peak_mb < 500, f"Memory usage too high: {result.memory_peak_mb:.1f}MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
