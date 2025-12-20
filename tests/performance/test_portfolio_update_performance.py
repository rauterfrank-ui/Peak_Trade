"""
Portfolio Update Performance Benchmarks
========================================

Benchmark portfolio calculation and update operations.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from tests.performance.benchmark import PerformanceBenchmark


@pytest.fixture
def benchmark():
    """Create benchmark instance."""
    return PerformanceBenchmark()


@pytest.fixture
def test_portfolio():
    """Create test portfolio with positions."""
    return {
        'BTC/USD': {'size': 0.5, 'entry_price': 45000, 'current_price': 48000},
        'ETH/USD': {'size': 10.0, 'entry_price': 2500, 'current_price': 2700},
        'SOL/USD': {'size': 100.0, 'entry_price': 100, 'current_price': 110},
    }


@pytest.fixture
def large_portfolio():
    """Create large portfolio with 100 positions."""
    symbols = [f"SYMBOL{i}/USD" for i in range(100)]
    return {
        symbol: {
            'size': np.random.uniform(0.1, 10),
            'entry_price': np.random.uniform(100, 50000),
            'current_price': np.random.uniform(100, 50000)
        }
        for symbol in symbols
    }


def test_portfolio_value_calculation(benchmark, test_portfolio):
    """
    Benchmark portfolio value calculation.
    
    Should be < 1ms for small portfolio.
    """
    def calculate_portfolio_value():
        total_value = sum(
            pos['size'] * pos['current_price']
            for pos in test_portfolio.values()
        )
        return total_value
    
    result = benchmark.run(
        calculate_portfolio_value,
        name="portfolio_value_calc",
        iterations=1000,
        warmup=10
    )
    
    assert result.mean_time < 0.001, f"Portfolio calc too slow: {result.mean_time:.6f}s"


def test_portfolio_pnl_calculation(benchmark, test_portfolio):
    """Benchmark portfolio PnL calculation."""
    def calculate_pnl():
        total_pnl = sum(
            pos['size'] * (pos['current_price'] - pos['entry_price'])
            for pos in test_portfolio.values()
        )
        return total_pnl
    
    result = benchmark.run(
        calculate_pnl,
        name="portfolio_pnl_calc",
        iterations=1000,
        warmup=10
    )
    
    assert result.mean_time < 0.001, f"PnL calc too slow: {result.mean_time:.6f}s"


def test_large_portfolio_update(benchmark, large_portfolio):
    """
    Benchmark large portfolio update (100 positions).
    
    Should be < 10ms for 100 positions.
    """
    def update_portfolio():
        # Update all prices
        for symbol in large_portfolio:
            large_portfolio[symbol]['current_price'] *= (1 + np.random.uniform(-0.01, 0.01))
        
        # Calculate total value
        total_value = sum(
            pos['size'] * pos['current_price']
            for pos in large_portfolio.values()
        )
        
        # Calculate total PnL
        total_pnl = sum(
            pos['size'] * (pos['current_price'] - pos['entry_price'])
            for pos in large_portfolio.values()
        )
        
        return total_value, total_pnl
    
    result = benchmark.run(
        update_portfolio,
        name="large_portfolio_update",
        iterations=1000,
        warmup=10
    )
    
    assert result.mean_time < 0.01, f"Large portfolio update too slow: {result.mean_time:.6f}s"


def test_portfolio_statistics_calculation(benchmark, large_portfolio):
    """Benchmark portfolio statistics calculation."""
    def calculate_stats():
        values = [
            pos['size'] * pos['current_price']
            for pos in large_portfolio.values()
        ]
        pnls = [
            pos['size'] * (pos['current_price'] - pos['entry_price'])
            for pos in large_portfolio.values()
        ]
        
        stats = {
            'total_value': sum(values),
            'mean_position_value': np.mean(values),
            'max_position_value': max(values),
            'min_position_value': min(values),
            'total_pnl': sum(pnls),
            'winning_positions': sum(1 for pnl in pnls if pnl > 0),
            'losing_positions': sum(1 for pnl in pnls if pnl < 0),
        }
        return stats
    
    result = benchmark.run(
        calculate_stats,
        name="portfolio_stats_calc",
        iterations=1000,
        warmup=10
    )
    
    assert result.mean_time < 0.005, f"Stats calc too slow: {result.mean_time:.6f}s"


def test_portfolio_rebalance_calculation(benchmark, large_portfolio):
    """Benchmark portfolio rebalance calculation."""
    target_weights = {symbol: 1.0 / len(large_portfolio) for symbol in large_portfolio}
    
    def calculate_rebalance():
        # Calculate current weights
        total_value = sum(
            pos['size'] * pos['current_price']
            for pos in large_portfolio.values()
        )
        
        current_weights = {
            symbol: (pos['size'] * pos['current_price']) / total_value
            for symbol, pos in large_portfolio.items()
        }
        
        # Calculate trades needed
        trades = {
            symbol: (target_weights[symbol] - current_weights[symbol]) * total_value
            for symbol in large_portfolio
        }
        
        return trades
    
    result = benchmark.run(
        calculate_rebalance,
        name="portfolio_rebalance_calc",
        iterations=500,
        warmup=5
    )
    
    assert result.mean_time < 0.01, f"Rebalance calc too slow: {result.mean_time:.6f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
