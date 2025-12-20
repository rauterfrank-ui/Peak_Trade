"""
Integration tests for reproducibility features.

Tests the full workflow: BacktestEngine -> ReproContext -> reproduce run.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import shutil

from src.backtest.engine import BacktestEngine
from src.core.repro import ReproContext, set_global_seed


@pytest.fixture
def sample_data():
    """Generate sample OHLCV data for testing."""
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')
    np.random.seed(42)  # Fixed seed for test data
    
    df = pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    return df


@pytest.fixture
def simple_strategy():
    """Simple strategy function for testing."""
    def strategy(df, params):
        # Simple MA crossover
        fast_period = params.get('fast_period', 10)
        slow_period = params.get('slow_period', 30)
        
        fast_ma = df['close'].rolling(fast_period).mean()
        slow_ma = df['close'].rolling(slow_period).mean()
        
        signals = pd.Series(0, index=df.index)
        signals[fast_ma > slow_ma] = 1
        signals[fast_ma < slow_ma] = -1
        
        return signals
    
    return strategy


@pytest.fixture
def cleanup_results():
    """Clean up results directory after tests."""
    yield
    # Cleanup after test
    results_dir = Path("results")
    if results_dir.exists():
        shutil.rmtree(results_dir)


def test_backtest_engine_saves_repro_context(sample_data, simple_strategy, cleanup_results):
    """BacktestEngine saves reproducibility context."""
    engine = BacktestEngine(use_execution_pipeline=False)
    
    result = engine.run_realistic(
        df=sample_data,
        strategy_signal_fn=simple_strategy,
        strategy_params={'fast_period': 10, 'slow_period': 30},
        seed=42,
        save_repro=True
    )
    
    # Check repro context in metadata
    assert 'repro_context' in result.metadata
    repro = result.metadata['repro_context']
    
    assert repro['seed'] == 42
    assert 'run_id' in repro
    assert len(repro['run_id']) == 8
    assert 'timestamp' in repro
    assert 'config_hash' in repro
    
    # Check file was saved
    run_id = repro['run_id']
    repro_file = Path("results") / run_id / "repro.json"
    assert repro_file.exists()


def test_backtest_determinism_same_seed(sample_data, simple_strategy, cleanup_results):
    """Backtest with same seed produces identical results."""
    engine = BacktestEngine(use_execution_pipeline=False)
    
    params = {'fast_period': 10, 'slow_period': 30}
    
    # Run 1
    result1 = engine.run_realistic(
        df=sample_data,
        strategy_signal_fn=simple_strategy,
        strategy_params=params,
        seed=42,
        save_repro=False
    )
    
    # Run 2 with same seed
    result2 = engine.run_realistic(
        df=sample_data,
        strategy_signal_fn=simple_strategy,
        strategy_params=params,
        seed=42,
        save_repro=False
    )
    
    # Compare equity curves
    equity_diff = np.abs(result1.equity_curve.values - result2.equity_curve.values)
    max_diff = equity_diff.max()
    
    assert max_diff < 1e-8, f"Equity curves differ by {max_diff}"
    
    # Compare stats
    assert result1.stats['total_trades'] == result2.stats['total_trades']
    assert abs(result1.stats['total_return'] - result2.stats['total_return']) < 1e-10


def test_backtest_different_seeds_different_results(sample_data, simple_strategy, cleanup_results):
    """Backtest with different seeds may produce different results (if randomness is used)."""
    engine = BacktestEngine(use_execution_pipeline=False)
    
    params = {'fast_period': 10, 'slow_period': 30}
    
    # Run with seed 42
    result1 = engine.run_realistic(
        df=sample_data,
        strategy_signal_fn=simple_strategy,
        strategy_params=params,
        seed=42,
        save_repro=False
    )
    
    # Run with seed 123
    result2 = engine.run_realistic(
        df=sample_data,
        strategy_signal_fn=simple_strategy,
        strategy_params=params,
        seed=123,
        save_repro=False
    )
    
    # For this deterministic strategy, results should actually be the same
    # (no randomness in the strategy itself)
    # But the repro contexts should differ
    ctx1 = result1.metadata['repro_context']
    ctx2 = result2.metadata['repro_context']
    
    assert ctx1['seed'] != ctx2['seed']
    assert ctx1['run_id'] != ctx2['run_id']


def test_repro_context_roundtrip(sample_data, simple_strategy, cleanup_results):
    """ReproContext can be saved and loaded correctly."""
    engine = BacktestEngine(use_execution_pipeline=False)
    
    result = engine.run_realistic(
        df=sample_data,
        strategy_signal_fn=simple_strategy,
        strategy_params={'fast_period': 10, 'slow_period': 30},
        seed=42,
        save_repro=True
    )
    
    # Load saved context
    run_id = result.metadata['repro_context']['run_id']
    repro_file = Path("results") / run_id / "repro.json"
    
    loaded_ctx = ReproContext.load(repro_file)
    
    # Compare with original
    original_ctx = result.metadata['repro_context']
    
    assert loaded_ctx.run_id == original_ctx['run_id']
    assert loaded_ctx.seed == original_ctx['seed']
    assert loaded_ctx.config_hash == original_ctx['config_hash']
    assert loaded_ctx.timestamp == original_ctx['timestamp']
    assert loaded_ctx.git_sha == original_ctx['git_sha']


def test_config_hash_stable_across_runs(sample_data, simple_strategy, cleanup_results):
    """Same config produces same hash across runs."""
    engine = BacktestEngine(use_execution_pipeline=False)
    
    params = {'fast_period': 10, 'slow_period': 30}
    
    # Run 1
    result1 = engine.run_realistic(
        df=sample_data,
        strategy_signal_fn=simple_strategy,
        strategy_params=params,
        seed=42,
        save_repro=False
    )
    
    # Run 2 with same params
    result2 = engine.run_realistic(
        df=sample_data,
        strategy_signal_fn=simple_strategy,
        strategy_params=params,
        seed=42,
        save_repro=False
    )
    
    # Config hashes should be identical
    hash1 = result1.metadata['repro_context']['config_hash']
    hash2 = result2.metadata['repro_context']['config_hash']
    
    assert hash1 == hash2


def test_config_hash_changes_with_params(sample_data, simple_strategy, cleanup_results):
    """Different config produces different hash."""
    engine = BacktestEngine(use_execution_pipeline=False)
    
    # Run 1 with params A
    result1 = engine.run_realistic(
        df=sample_data,
        strategy_signal_fn=simple_strategy,
        strategy_params={'fast_period': 10, 'slow_period': 30},
        seed=42,
        save_repro=False
    )
    
    # Run 2 with params B
    result2 = engine.run_realistic(
        df=sample_data,
        strategy_signal_fn=simple_strategy,
        strategy_params={'fast_period': 20, 'slow_period': 50},
        seed=42,
        save_repro=False
    )
    
    # Config hashes should differ
    hash1 = result1.metadata['repro_context']['config_hash']
    hash2 = result2.metadata['repro_context']['config_hash']
    
    assert hash1 != hash2


def test_set_global_seed_affects_numpy(cleanup_results):
    """set_global_seed() properly sets NumPy seed."""
    # Run 1
    set_global_seed(42)
    values1 = np.random.rand(10)
    
    # Run 2 with same seed
    set_global_seed(42)
    values2 = np.random.rand(10)
    
    # Should be identical
    assert np.allclose(values1, values2)


def test_multiple_runs_create_separate_directories(sample_data, simple_strategy, cleanup_results):
    """Each run creates its own directory."""
    engine = BacktestEngine(use_execution_pipeline=False)
    
    params = {'fast_period': 10, 'slow_period': 30}
    
    # Run multiple times
    run_ids = []
    for _ in range(3):
        result = engine.run_realistic(
            df=sample_data,
            strategy_signal_fn=simple_strategy,
            strategy_params=params,
            seed=42,
            save_repro=True
        )
        run_ids.append(result.metadata['repro_context']['run_id'])
    
    # All run IDs should be unique
    assert len(set(run_ids)) == 3
    
    # All directories should exist
    for run_id in run_ids:
        repro_file = Path("results") / run_id / "repro.json"
        assert repro_file.exists()
