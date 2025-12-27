"""
Tests for Error Taxonomy (Wave A - Stability Plan)
"""

import pytest
import pandas as pd

from src.core.errors import (
    BacktestError,
    BacktestInvariantError,
    CacheCorruptionError,
    CacheError,
    ConfigError,
    DataContractError,
    PeakTradeError,
    ProviderError,
    RiskError,
    StrategyError,
    add_backtest_context,
    chain_error,
)


@pytest.mark.smoke
def test_peak_trade_error_base():
    """PeakTradeError base class works correctly."""
    error = PeakTradeError("Test error")
    assert "PeakTradeError: Test error" in str(error)
    assert error.message == "Test error"
    assert error.hint is None
    assert error.context == {}


@pytest.mark.smoke
def test_peak_trade_error_with_hint():
    """PeakTradeError includes hint in message."""
    error = PeakTradeError("Test error", hint="Try fixing it this way")
    msg = str(error)
    assert "Test error" in msg
    assert "Hint: Try fixing it this way" in msg


def test_peak_trade_error_with_context():
    """PeakTradeError includes context in message."""
    error = PeakTradeError("Test error", context={"key": "value", "count": 42})
    msg = str(error)
    assert "Test error" in msg
    assert "Context:" in msg
    assert "'key': 'value'" in msg
    assert "'count': 42" in msg


def test_peak_trade_error_with_hint_and_context():
    """PeakTradeError includes both hint and context."""
    error = PeakTradeError(
        "Test error",
        hint="Fix it",
        context={"key": "value"},
    )
    msg = str(error)
    assert "Test error" in msg
    assert "Hint: Fix it" in msg
    assert "Context:" in msg


def test_data_contract_error_inheritance():
    """DataContractError inherits from PeakTradeError."""
    error = DataContractError("Missing columns", hint="Add them", context={"cols": ["open"]})
    assert isinstance(error, PeakTradeError)
    assert "DataContractError: Missing columns" in str(error)
    assert error.message == "Missing columns"
    assert error.hint == "Add them"
    assert error.context == {"cols": ["open"]}


def test_config_error_inheritance():
    """ConfigError inherits from PeakTradeError."""
    error = ConfigError("Invalid config", hint="Check schema")
    assert isinstance(error, PeakTradeError)
    assert "ConfigError: Invalid config" in str(error)


def test_provider_error_inheritance():
    """ProviderError inherits from PeakTradeError."""
    error = ProviderError("API timeout", hint="Retry with backoff")
    assert isinstance(error, PeakTradeError)
    assert "ProviderError: API timeout" in str(error)


def test_cache_corruption_error_inheritance():
    """CacheCorruptionError inherits from PeakTradeError."""
    error = CacheCorruptionError("Checksum mismatch", hint="Delete cache")
    assert isinstance(error, PeakTradeError)
    assert "CacheCorruptionError: Checksum mismatch" in str(error)


def test_backtest_invariant_error_inheritance():
    """BacktestInvariantError inherits from PeakTradeError."""
    error = BacktestInvariantError("Equity is NaN", hint="Check data")
    assert isinstance(error, PeakTradeError)
    assert "BacktestInvariantError: Equity is NaN" in str(error)


def test_error_can_be_caught_as_base():
    """All Peak_Trade errors can be caught by PeakTradeError."""
    errors = [
        DataContractError("test"),
        ConfigError("test"),
        ProviderError("test"),
        CacheCorruptionError("test"),
        BacktestInvariantError("test"),
    ]

    for error in errors:
        with pytest.raises(PeakTradeError):
            raise error


def test_error_can_be_caught_specifically():
    """Specific error types can be caught individually."""
    with pytest.raises(ConfigError):
        raise ConfigError("test")

    with pytest.raises(DataContractError):
        raise DataContractError("test")


def test_error_message_is_exception_message():
    """Error message is accessible via str(exception)."""
    error = ConfigError("Unknown key: foo", hint="Use bar instead")
    exception_msg = str(error)

    assert "Unknown key: foo" in exception_msg
    assert "Use bar instead" in exception_msg


# Tests for new error types
# ==========================


def test_cache_error_inheritance():
    """CacheError inherits from PeakTradeError."""
    error = CacheError("Failed to write cache", hint="Check disk space")
    assert isinstance(error, PeakTradeError)
    assert "CacheError: Failed to write cache" in str(error)


def test_strategy_error_inheritance():
    """StrategyError inherits from PeakTradeError."""
    error = StrategyError("Invalid parameter", hint="Check strategy config")
    assert isinstance(error, PeakTradeError)
    assert "StrategyError: Invalid parameter" in str(error)


def test_backtest_error_inheritance():
    """BacktestError inherits from PeakTradeError."""
    error = BacktestError("Failed to load data", hint="Verify data files exist")
    assert isinstance(error, PeakTradeError)
    assert "BacktestError: Failed to load data" in str(error)


def test_risk_error_inheritance():
    """RiskError inherits from PeakTradeError."""
    error = RiskError("Position size exceeds limit", hint="Reduce position size")
    assert isinstance(error, PeakTradeError)
    assert "RiskError: Position size exceeds limit" in str(error)


def test_all_error_types_can_be_caught_as_base():
    """All Peak_Trade errors including new types can be caught by PeakTradeError."""
    errors = [
        DataContractError("test"),
        ConfigError("test"),
        ProviderError("test"),
        CacheCorruptionError("test"),
        CacheError("test"),
        BacktestInvariantError("test"),
        BacktestError("test"),
        StrategyError("test"),
        RiskError("test"),
    ]

    for error in errors:
        with pytest.raises(PeakTradeError):
            raise error


# Tests for error chaining
# =========================


def test_error_with_cause():
    """PeakTradeError can include a cause exception."""
    original = ValueError("Original error")
    error = PeakTradeError("Wrapped error", cause=original)

    assert error.cause is original
    assert "Caused by: ValueError: Original error" in str(error)
    assert error.__cause__ is original


def test_chain_error_function():
    """chain_error creates a PeakTradeError with cause."""
    original = IOError("File not found")
    error = chain_error(
        original,
        "Failed to load configuration",
        hint="Check file path",
        context={"file": "config.toml"},
    )

    assert isinstance(error, PeakTradeError)
    assert error.message == "Failed to load configuration"
    assert error.hint == "Check file path"
    assert error.context == {"file": "config.toml"}
    assert error.cause is original
    assert error.__cause__ is original


def test_chain_error_preserves_stack_trace():
    """chain_error preserves exception chaining for stack traces."""
    try:
        try:
            raise ValueError("Original problem")
        except ValueError as e:
            raise chain_error(e, "Wrapped error")
    except PeakTradeError as e:
        assert e.__cause__.__class__.__name__ == "ValueError"
        assert str(e.__cause__) == "Original problem"


def test_error_chaining_with_specific_error_types():
    """Error chaining works with specific error types."""
    original = KeyError("missing_key")
    error = ConfigError("Invalid configuration", cause=original)

    assert isinstance(error, ConfigError)
    assert isinstance(error, PeakTradeError)
    assert error.cause is original
    assert "Caused by: KeyError" in str(error)


# Tests for context helpers
# ==========================


def test_add_backtest_context():
    """add_backtest_context enriches error with backtest metadata."""
    error = BacktestError("Something went wrong")
    timestamp = pd.Timestamp("2024-01-15 10:30:00", tz="UTC")

    result = add_backtest_context(error, run_id="bt_12345", timestamp=timestamp)

    assert result is error  # Returns same instance
    assert "run_id" in error.context
    assert error.context["run_id"] == "bt_12345"
    assert "timestamp" in error.context
    assert "2024-01-15" in error.context["timestamp"]


def test_add_backtest_context_preserves_existing_context():
    """add_backtest_context preserves existing context entries."""
    error = BacktestError("Error", context={"symbol": "BTC/USD"})
    timestamp = pd.Timestamp("2024-01-15", tz="UTC")

    add_backtest_context(error, run_id="bt_001", timestamp=timestamp)

    assert error.context["symbol"] == "BTC/USD"
    assert error.context["run_id"] == "bt_001"
    assert "timestamp" in error.context


def test_error_context_in_formatted_message():
    """Error context appears in formatted error message."""
    error = BacktestError(
        "Backtest failed", hint="Check your data", context={"symbol": "BTC/USD", "timeframe": "1h"}
    )
    timestamp = pd.Timestamp("2024-01-15", tz="UTC")
    add_backtest_context(error, run_id="bt_001", timestamp=timestamp)

    msg = str(error)
    assert "BacktestError: Backtest failed" in msg
    assert "Hint: Check your data" in msg
    assert "Context:" in msg
    assert "symbol" in msg
    assert "BTC/USD" in msg
    assert "run_id" in msg
    assert "bt_001" in msg


# Tests for error formatting
# ===========================


def test_error_with_all_fields():
    """Error with message, hint, context, and cause formats correctly."""
    original = RuntimeError("Low-level error")
    error = PeakTradeError(
        "High-level error", hint="Try this fix", context={"key": "value"}, cause=original
    )

    msg = str(error)
    assert "PeakTradeError: High-level error" in msg
    assert "Hint: Try this fix" in msg
    assert "Context:" in msg
    assert "'key': 'value'" in msg
    assert "Caused by: RuntimeError: Low-level error" in msg


def test_error_without_optional_fields():
    """Error without optional fields formats correctly."""
    error = PeakTradeError("Simple error")
    msg = str(error)

    assert "PeakTradeError: Simple error" in msg
    assert "Hint:" not in msg
    assert "Context:" not in msg
    assert "Caused by:" not in msg


# Integration tests
# =================


def test_realistic_config_error_scenario():
    """Realistic ConfigError with hint and context."""
    error = ConfigError(
        "Unknown config key: 'invalid_strategy'",
        hint="Available strategies: ['momentum', 'mean_reversion', 'breakout']",
        context={
            "key": "invalid_strategy",
            "config_file": "/path/to/config.toml",
            "available_keys": ["momentum", "mean_reversion", "breakout"],
        },
    )

    msg = str(error)
    assert "ConfigError:" in msg
    assert "Unknown config key" in msg
    assert "Available strategies" in msg
    assert "invalid_strategy" in msg


def test_realistic_provider_error_scenario():
    """Realistic ProviderError with API failure context."""
    error = ProviderError(
        "API request failed: Rate limit exceeded",
        hint="Wait 60 seconds before retrying or check API credentials in .env",
        context={"endpoint": "/api/v3/ohlcv", "status_code": 429, "retry_after": 60},
    )

    msg = str(error)
    assert "ProviderError:" in msg
    assert "Rate limit exceeded" in msg
    assert "Wait 60 seconds" in msg


def test_realistic_strategy_error_with_chaining():
    """Realistic StrategyError using error chaining."""
    try:
        # Simulate parameter validation failure
        raise ValueError("lookback_period must be positive")
    except ValueError as e:
        error = chain_error(
            e,
            "Failed to initialize MA Crossover strategy",
            hint="Check strategy parameters in config",
            context={"lookback_period": -10, "valid_range": ">0"},
        )

        assert isinstance(error, PeakTradeError)
        assert "Failed to initialize" in str(error)
        assert "Caused by: ValueError" in str(error)


def test_realistic_risk_error_scenario():
    """Realistic RiskError for position size limit."""
    error = RiskError(
        "Position size $15000 exceeds daily risk limit",
        hint="Reduce position size or increase risk_pct in config",
        context={
            "requested_size": 15000,
            "daily_limit": 10000,
            "risk_pct": 1.0,
            "account_balance": 100000,
        },
    )

    msg = str(error)
    assert "RiskError:" in msg
    assert "exceeds daily risk limit" in msg
    assert "requested_size" in msg
