"""
Peak_Trade Backtest Invariants Tests
====================================
Comprehensive tests for the backtest invariant checking system.
"""

import pytest
import pandas as pd
import numpy as np
from dataclasses import dataclass

from src.backtest.invariants import (
    Invariant,
    BacktestInvariants,
    InvariantChecker,
    CheckMode,
    CORE_INVARIANTS,
)
from src.backtest.engine import BacktestEngine
from src.core.errors import BacktestInvariantError
from src.core.peak_config import load_config


@dataclass
class MockEngine:
    """Mock engine for testing invariants."""
    equity: float
    cash: float
    positions: any
    history: list = None
    
    def __post_init__(self):
        if self.history is None:
            self.history = []


def create_dummy_ohlcv(n_bars: int = 100) -> pd.DataFrame:
    """Create synthetic OHLCV data for tests."""
    np.random.seed(42)
    idx = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")
    
    returns = np.random.normal(0, 0.01, n_bars)
    close_prices = 50000 * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame(index=idx)
    df["close"] = close_prices
    df["open"] = df["close"].shift(1).fillna(50000)
    df["high"] = np.maximum(df["open"], df["close"]) * 1.002
    df["low"] = np.minimum(df["open"], df["close"]) * 0.998
    df["volume"] = np.random.uniform(100, 1000, n_bars)
    
    return df[["open", "high", "low", "close", "volume"]]


# ============================================================================
# INDIVIDUAL INVARIANT TESTS
# ============================================================================

def test_equity_non_negative_pass():
    """Test: equity_non_negative passes with positive equity."""
    engine = MockEngine(equity=10000.0, cash=10000.0, positions=[])
    assert BacktestInvariants.equity_non_negative(engine) is True


def test_equity_non_negative_fail():
    """Test: equity_non_negative fails with negative equity."""
    engine = MockEngine(equity=-100.0, cash=-100.0, positions=[])
    assert BacktestInvariants.equity_non_negative(engine) is False


def test_equity_non_negative_zero():
    """Test: equity_non_negative passes with zero equity."""
    engine = MockEngine(equity=0.0, cash=0.0, positions=[])
    assert BacktestInvariants.equity_non_negative(engine) is True


def test_positions_valid_empty_list():
    """Test: positions_valid passes with empty list."""
    engine = MockEngine(equity=10000.0, cash=10000.0, positions=[])
    assert BacktestInvariants.positions_valid(engine) is True


def test_positions_valid_none():
    """Test: positions_valid fails with None positions."""
    engine = MockEngine(equity=10000.0, cash=10000.0, positions=None)
    assert BacktestInvariants.positions_valid(engine) is False


def test_positions_valid_dict():
    """Test: positions_valid passes with valid dict (ExecutionPipeline mode)."""
    engine = MockEngine(equity=10000.0, cash=10000.0, positions={"BTC/EUR": 0.5, "ETH/EUR": 1.0})
    assert BacktestInvariants.positions_valid(engine) is True


def test_positions_valid_dict_with_none():
    """Test: positions_valid fails with None value in dict."""
    engine = MockEngine(equity=10000.0, cash=10000.0, positions={"BTC/EUR": None})
    assert BacktestInvariants.positions_valid(engine) is False


def test_timestamps_monotonic_empty():
    """Test: timestamps_monotonic passes with empty history."""
    engine = MockEngine(equity=10000.0, cash=10000.0, positions=[], history=[])
    assert BacktestInvariants.timestamps_monotonic(engine) is True


def test_timestamps_monotonic_single():
    """Test: timestamps_monotonic passes with single timestamp."""
    @dataclass
    class HistoryEntry:
        timestamp: pd.Timestamp
    
    engine = MockEngine(
        equity=10000.0,
        cash=10000.0,
        positions=[],
        history=[HistoryEntry(timestamp=pd.Timestamp("2024-01-01", tz="UTC"))]
    )
    assert BacktestInvariants.timestamps_monotonic(engine) is True


def test_timestamps_monotonic_increasing():
    """Test: timestamps_monotonic passes with strictly increasing timestamps."""
    @dataclass
    class HistoryEntry:
        timestamp: pd.Timestamp
    
    engine = MockEngine(
        equity=10000.0,
        cash=10000.0,
        positions=[],
        history=[
            HistoryEntry(timestamp=pd.Timestamp("2024-01-01 00:00", tz="UTC")),
            HistoryEntry(timestamp=pd.Timestamp("2024-01-01 01:00", tz="UTC")),
            HistoryEntry(timestamp=pd.Timestamp("2024-01-01 02:00", tz="UTC")),
        ]
    )
    assert BacktestInvariants.timestamps_monotonic(engine) is True


def test_timestamps_monotonic_not_increasing():
    """Test: timestamps_monotonic fails with non-increasing timestamps."""
    @dataclass
    class HistoryEntry:
        timestamp: pd.Timestamp
    
    engine = MockEngine(
        equity=10000.0,
        cash=10000.0,
        positions=[],
        history=[
            HistoryEntry(timestamp=pd.Timestamp("2024-01-01 00:00", tz="UTC")),
            HistoryEntry(timestamp=pd.Timestamp("2024-01-01 02:00", tz="UTC")),
            HistoryEntry(timestamp=pd.Timestamp("2024-01-01 01:00", tz="UTC")),  # Out of order
        ]
    )
    assert BacktestInvariants.timestamps_monotonic(engine) is False


def test_cash_balance_valid_positive():
    """Test: cash_balance_valid passes with positive cash."""
    engine = MockEngine(equity=10000.0, cash=5000.0, positions=[])
    assert BacktestInvariants.cash_balance_valid(engine) is True


def test_cash_balance_valid_zero():
    """Test: cash_balance_valid passes with zero cash."""
    engine = MockEngine(equity=10000.0, cash=0.0, positions=[])
    assert BacktestInvariants.cash_balance_valid(engine) is True


def test_cash_balance_valid_negative():
    """Test: cash_balance_valid fails with negative cash."""
    engine = MockEngine(equity=10000.0, cash=-100.0, positions=[])
    assert BacktestInvariants.cash_balance_valid(engine) is False


def test_position_sizes_realistic_empty():
    """Test: position_sizes_realistic passes with no positions."""
    engine = MockEngine(equity=10000.0, cash=10000.0, positions=[])
    assert BacktestInvariants.position_sizes_realistic(engine) is True


def test_position_sizes_realistic_within_limits():
    """Test: position_sizes_realistic passes with positions within 10x leverage."""
    @dataclass
    class Position:
        value: float
    
    engine = MockEngine(
        equity=10000.0,
        cash=0.0,
        positions=[Position(value=50000.0)]  # 5x leverage
    )
    assert BacktestInvariants.position_sizes_realistic(engine) is True


def test_position_sizes_realistic_exceeds_limits():
    """Test: position_sizes_realistic fails with positions exceeding 10x leverage."""
    @dataclass
    class Position:
        value: float
    
    engine = MockEngine(
        equity=10000.0,
        cash=0.0,
        positions=[Position(value=150000.0)]  # 15x leverage
    )
    assert BacktestInvariants.position_sizes_realistic(engine) is False


# ============================================================================
# INVARIANT CHECKER TESTS
# ============================================================================

def test_invariant_checker_init_default():
    """Test: InvariantChecker initializes with default mode."""
    checker = InvariantChecker()
    assert checker.mode == CheckMode.START_END
    assert len(checker.invariants) == len(CORE_INVARIANTS)


def test_invariant_checker_init_always():
    """Test: InvariantChecker initializes with ALWAYS mode."""
    checker = InvariantChecker(mode=CheckMode.ALWAYS)
    assert checker.mode == CheckMode.ALWAYS


def test_invariant_checker_init_never():
    """Test: InvariantChecker initializes with NEVER mode."""
    checker = InvariantChecker(mode=CheckMode.NEVER)
    assert checker.mode == CheckMode.NEVER


def test_invariant_checker_passes_all():
    """Test: check_all passes with valid engine state."""
    checker = InvariantChecker(mode=CheckMode.ALWAYS)
    engine = MockEngine(equity=10000.0, cash=10000.0, positions=[])
    
    # Should not raise
    checker.check_all(engine)


def test_invariant_checker_fails_negative_equity():
    """Test: check_all raises on negative equity."""
    checker = InvariantChecker(mode=CheckMode.ALWAYS)
    engine = MockEngine(equity=-100.0, cash=-100.0, positions=[])
    
    with pytest.raises(BacktestInvariantError) as exc_info:
        checker.check_all(engine)
    
    assert "equity_non_negative" in str(exc_info.value)
    assert "Equity cannot be negative" in str(exc_info.value)


def test_invariant_checker_fails_negative_cash():
    """Test: check_all raises on negative cash."""
    checker = InvariantChecker(mode=CheckMode.ALWAYS)
    engine = MockEngine(equity=10000.0, cash=-100.0, positions=[])
    
    with pytest.raises(BacktestInvariantError) as exc_info:
        checker.check_all(engine)
    
    assert "cash_balance_valid" in str(exc_info.value)
    assert "Negative cash balance" in str(exc_info.value)


def test_invariant_checker_never_mode_no_check():
    """Test: check_all does not check in NEVER mode."""
    checker = InvariantChecker(mode=CheckMode.NEVER)
    engine = MockEngine(equity=-100.0, cash=-100.0, positions=None)  # Invalid state
    
    # Should not raise even with invalid state
    checker.check_all(engine)


def test_add_custom_invariant():
    """Test: add_custom_invariant adds user-defined invariant."""
    checker = InvariantChecker()
    initial_count = len(checker.invariants)
    
    def custom_check(engine) -> bool:
        return engine.equity < 1000000
    
    custom_invariant = Invariant(
        name="equity_cap",
        check=custom_check,
        error_message="Equity exceeded 1M cap",
        hint="Check strategy parameters"
    )
    
    checker.add_custom_invariant(custom_invariant)
    
    assert len(checker.invariants) == initial_count + 1
    assert custom_invariant in checker.invariants


def test_custom_invariant_violation():
    """Test: Custom invariant violation raises error."""
    checker = InvariantChecker()
    
    def custom_check(engine) -> bool:
        return engine.equity < 1000000
    
    custom_invariant = Invariant(
        name="equity_cap",
        check=custom_check,
        error_message="Equity exceeded 1M cap",
        hint="Check strategy parameters"
    )
    
    checker.add_custom_invariant(custom_invariant)
    
    # Valid state
    engine = MockEngine(equity=500000.0, cash=500000.0, positions=[])
    checker.check_all(engine)  # Should pass
    
    # Invalid state
    engine_invalid = MockEngine(equity=2000000.0, cash=2000000.0, positions=[])
    with pytest.raises(BacktestInvariantError) as exc_info:
        checker.check_all(engine_invalid)
    
    assert "equity_cap" in str(exc_info.value)
    assert "Equity exceeded 1M cap" in str(exc_info.value)


def test_remove_invariant():
    """Test: remove_invariant removes invariant by name."""
    checker = InvariantChecker()
    initial_count = len(checker.invariants)
    
    result = checker.remove_invariant("equity_non_negative")
    
    assert result is True
    assert len(checker.invariants) == initial_count - 1
    assert "equity_non_negative" not in checker.get_invariant_names()


def test_remove_invariant_not_found():
    """Test: remove_invariant returns False for non-existent invariant."""
    checker = InvariantChecker()
    initial_count = len(checker.invariants)
    
    result = checker.remove_invariant("nonexistent_invariant")
    
    assert result is False
    assert len(checker.invariants) == initial_count


def test_get_invariant_names():
    """Test: get_invariant_names returns all invariant names."""
    checker = InvariantChecker()
    names = checker.get_invariant_names()
    
    assert len(names) == len(CORE_INVARIANTS)
    assert "equity_non_negative" in names
    assert "positions_valid" in names
    assert "timestamps_monotonic" in names
    assert "cash_balance_valid" in names
    assert "position_sizes_realistic" in names


# ============================================================================
# INTEGRATION TESTS WITH BACKTEST ENGINE
# ============================================================================

def test_backtest_engine_init_with_invariant_checker():
    """Test: BacktestEngine initializes with invariant checker."""
    cfg = load_config()
    engine = BacktestEngine()
    
    assert hasattr(engine, 'invariant_checker')
    assert isinstance(engine.invariant_checker, InvariantChecker)


def test_backtest_engine_check_mode_from_config():
    """Test: BacktestEngine reads check_mode from config."""
    cfg = load_config()
    engine = BacktestEngine()
    
    # Should default to START_END from config
    expected_mode = cfg.get("backtest", {}).get("invariant_check_mode", "start_end")
    assert engine.invariant_checker.mode == CheckMode(expected_mode)


def test_backtest_engine_check_mode_override():
    """Test: BacktestEngine check_mode can be overridden."""
    engine = BacktestEngine(check_mode="always")
    assert engine.invariant_checker.mode == CheckMode.ALWAYS


def test_backtest_engine_invalid_check_mode_fallback():
    """Test: BacktestEngine falls back to START_END with invalid mode."""
    engine = BacktestEngine(check_mode="invalid_mode")
    assert engine.invariant_checker.mode == CheckMode.START_END


def test_backtest_run_realistic_passes_invariants():
    """Test: run_realistic passes invariants with valid strategy."""
    cfg = load_config()
    df = create_dummy_ohlcv(50)
    
    engine = BacktestEngine(check_mode="start_end", use_execution_pipeline=False)
    
    def simple_signal_fn(data, params):
        """Simple strategy that returns all zeros (no trades)."""
        return pd.Series(0, index=data.index)
    
    # Should complete without raising
    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=simple_signal_fn,
        strategy_params={"stop_pct": 0.02},
    )
    
    assert result is not None
    assert result.stats["total_trades"] == 0  # No trades with zero signals


def test_backtest_run_with_execution_pipeline_passes_invariants():
    """Test: _run_with_execution_pipeline passes invariants."""
    cfg = load_config()
    df = create_dummy_ohlcv(50)
    
    engine = BacktestEngine(check_mode="start_end", use_execution_pipeline=True)
    
    def simple_signal_fn(data, params):
        """Simple strategy that returns all zeros (no trades)."""
        return pd.Series(0, index=data.index)
    
    # Should complete without raising
    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=simple_signal_fn,
        strategy_params={},
        symbol="BTC/EUR",
        fee_bps=0.0,
        slippage_bps=0.0,
    )
    
    assert result is not None


def test_backtest_never_mode_allows_invalid_state():
    """Test: NEVER mode does not check invariants."""
    df = create_dummy_ohlcv(50)
    
    engine = BacktestEngine(check_mode="never", use_execution_pipeline=False)
    
    # Manually corrupt state (this wouldn't normally happen, but demonstrates NEVER mode)
    # The invariants won't be checked, so this should still run
    
    def simple_signal_fn(data, params):
        return pd.Series(0, index=data.index)
    
    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=simple_signal_fn,
        strategy_params={"stop_pct": 0.02},
    )
    
    assert result is not None


# ============================================================================
# CORE INVARIANTS VERIFICATION
# ============================================================================

def test_core_invariants_count():
    """Test: Verify all 5 core invariants are defined."""
    assert len(CORE_INVARIANTS) >= 5
    
    names = [inv.name for inv in CORE_INVARIANTS]
    assert "equity_non_negative" in names
    assert "positions_valid" in names
    assert "timestamps_monotonic" in names
    assert "cash_balance_valid" in names
    assert "position_sizes_realistic" in names


def test_core_invariants_structure():
    """Test: All core invariants have required attributes."""
    for invariant in CORE_INVARIANTS:
        assert hasattr(invariant, 'name')
        assert hasattr(invariant, 'check')
        assert hasattr(invariant, 'error_message')
        assert hasattr(invariant, 'hint')
        
        assert isinstance(invariant.name, str)
        assert callable(invariant.check)
        assert isinstance(invariant.error_message, str)
        assert isinstance(invariant.hint, str)
        
        # Check that messages are not empty
        assert len(invariant.name) > 0
        assert len(invariant.error_message) > 0
        assert len(invariant.hint) > 0


# ============================================================================
# ERROR MESSAGE TESTS
# ============================================================================

def test_invariant_error_includes_context():
    """Test: InvariantViolationError includes context information."""
    checker = InvariantChecker()
    engine = MockEngine(equity=-100.0, cash=5000.0, positions=[])
    
    with pytest.raises(BacktestInvariantError) as exc_info:
        checker.check_all(engine)
    
    error = exc_info.value
    assert hasattr(error, 'context')
    assert "equity" in error.context
    assert error.context["equity"] == -100.0


def test_invariant_error_includes_hint():
    """Test: InvariantViolationError includes actionable hint."""
    checker = InvariantChecker()
    engine = MockEngine(equity=-100.0, cash=5000.0, positions=[])
    
    with pytest.raises(BacktestInvariantError) as exc_info:
        checker.check_all(engine)
    
    error = exc_info.value
    assert hasattr(error, 'hint')
    assert error.hint is not None
    assert len(error.hint) > 0


# ============================================================================
# PERFORMANCE / CHECK MODE TESTS
# ============================================================================

def test_check_mode_enum_values():
    """Test: CheckMode enum has expected values."""
    assert CheckMode.ALWAYS.value == "always"
    assert CheckMode.START_END.value == "start_end"
    assert CheckMode.NEVER.value == "never"


def test_check_mode_from_string():
    """Test: CheckMode can be created from string."""
    assert CheckMode("always") == CheckMode.ALWAYS
    assert CheckMode("start_end") == CheckMode.START_END
    assert CheckMode("never") == CheckMode.NEVER


def test_check_mode_invalid_string():
    """Test: Invalid CheckMode string raises ValueError."""
    with pytest.raises(ValueError):
        CheckMode("invalid")
