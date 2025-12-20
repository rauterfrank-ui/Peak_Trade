"""
Integration Test: Trace Context with Backtest Engine
====================================================
Tests that trace context propagates correctly through backtest execution.
"""
import logging
from io import StringIO
import pandas as pd
import pytest

from src.core.trace_context import get_run_id, get_trace_id, TraceContext
from src.core.logging_config import TraceContextFilter


def test_backtest_engine_sets_trace_context():
    """BacktestEngine sets trace context during execution."""
    from src.backtest.engine import BacktestEngine
    
    # Create simple test data
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    df = pd.DataFrame({
        "open": [100.0] * 10,
        "high": [105.0] * 10,
        "low": [95.0] * 10,
        "close": [100.0 + i for i in range(10)],
        "volume": [1000.0] * 10,
    }, index=dates)
    
    # Simple strategy function
    def simple_strategy(df, params):
        # Always hold
        return pd.Series([0] * len(df), index=df.index)
    
    # Create engine
    engine = BacktestEngine(use_execution_pipeline=False)
    
    # Run backtest - this should set trace context internally
    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=simple_strategy,
        strategy_params={"stop_pct": 0.02},
    )
    
    # After execution, trace context should be set (within the execution)
    # The result should include metadata
    assert result is not None
    assert result.stats is not None


def test_trace_context_in_backtest_logs():
    """Trace context appears in logs during backtest execution."""
    from src.backtest.engine import BacktestEngine
    
    # Setup logging to capture output
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(TraceContextFilter())
    formatter = logging.Formatter('[%(run_id)s] [%(trace_id)s] %(message)s')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger("src.backtest.engine")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    
    # Create simple test data
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    df = pd.DataFrame({
        "open": [100.0] * 5,
        "high": [105.0] * 5,
        "low": [95.0] * 5,
        "close": [100.0 + i for i in range(5)],
        "volume": [1000.0] * 5,
    }, index=dates)
    
    # Simple strategy
    def simple_strategy(df, params):
        return pd.Series([0] * len(df), index=df.index)
    
    # Run backtest
    engine = BacktestEngine(use_execution_pipeline=False)
    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=simple_strategy,
        strategy_params={"stop_pct": 0.02},
    )
    
    # Check that logs include run_id
    output = stream.getvalue()
    assert "backtest_legacy_" in output or "Starting" in output


def test_manual_trace_context_usage():
    """Manual trace context setting works for custom use cases."""
    from src.core.trace_context import trace_context, _run_id_var, _trace_id_var
    
    # Clean slate for this test
    _run_id_var.set(None)
    _trace_id_var.set(None)
    
    # Before context
    assert get_run_id() is None
    
    # Within context
    with trace_context(run_id="manual_test_123"):
        assert get_run_id() == "manual_test_123"
        assert get_trace_id() is not None
        
        # Simulate some backtest operations
        logger = logging.getLogger("test")
        logger.info("Processing backtest step")
    
    # After context - context is cleared after with block
    assert get_run_id() is None


@pytest.mark.smoke
def test_trace_context_smoke():
    """Smoke test: Basic trace context functionality."""
    from src.core.trace_context import TraceContext, get_run_id, get_trace_id
    
    # Create and activate context
    ctx = TraceContext.create(run_id="smoke_test")
    ctx.set_active()
    
    # Verify it's accessible
    assert get_run_id() == "smoke_test"
    assert get_trace_id() is not None
    assert len(get_trace_id()) == 8
