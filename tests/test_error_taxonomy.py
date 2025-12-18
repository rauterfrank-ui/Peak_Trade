"""
Tests for Error Taxonomy (Wave A - Stability Plan)
"""
import pytest

from src.core.errors import (
    BacktestInvariantError,
    CacheCorruptionError,
    ConfigError,
    DataContractError,
    PeakTradeError,
    ProviderError,
)


def test_peak_trade_error_base():
    """PeakTradeError base class works correctly."""
    error = PeakTradeError("Test error")
    assert "PeakTradeError: Test error" in str(error)
    assert error.message == "Test error"
    assert error.hint is None
    assert error.context == {}


def test_peak_trade_error_with_hint():
    """PeakTradeError includes hint in message."""
    error = PeakTradeError("Test error", hint="Try fixing it this way")
    msg = str(error)
    assert "Test error" in msg
    assert "Hint: Try fixing it this way" in msg


def test_peak_trade_error_with_context():
    """PeakTradeError includes context in message."""
    error = PeakTradeError(
        "Test error", context={"key": "value", "count": 42}
    )
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
