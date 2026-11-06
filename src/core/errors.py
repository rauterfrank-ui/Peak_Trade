"""
Peak_Trade Error Taxonomy (Wave A - Stability Plan)
====================================================
Structured error hierarchy with hints and context for better debugging.

Design Principles:
- Fail-fast with clear messages
- Always provide actionable hints
- Include context dict for programmatic access
- Inherit from common base for uniform handling
- Support error chaining to preserve stack traces

Usage:
    from src.core.errors import ConfigError, DataContractError, chain_error

    # Basic usage
    raise ConfigError(
        "Unknown strategy key: 'foo'",
        hint="Available strategies: ['momentum', 'mean_reversion']",
        context={"key": "foo", "available": ["momentum", "mean_reversion"]}
    )

    # Error chaining
    try:
        risky_operation()
    except Exception as e:
        raise chain_error(e, "Failed to load strategy", hint="Check configuration")
"""

from typing import Any, Dict, Optional
import pandas as pd


class PeakTradeError(Exception):
    """
    Base exception for all Peak_Trade errors.

    Attributes:
        message: Human-readable error message
        hint: Suggested fix or next steps (optional)
        context: Dict with additional context for debugging (optional)
        cause: Original exception that caused this error (optional)
    """

    def __init__(
        self,
        message: str,
        *,
        hint: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        self.message = message
        self.hint = hint
        self.context = context or {}
        self.cause = cause

        # Preserve exception chaining for proper stack traces
        if cause is not None:
            self.__cause__ = cause

        # Call parent __init__ with formatted message
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format error message with hint and context."""
        parts = [f"{self.__class__.__name__}: {self.message}"]
        if self.hint:
            parts.append(f"Hint: {self.hint}")
        if self.context:
            parts.append(f"Context: {self.context}")
        if self.cause:
            parts.append(f"Caused by: {type(self.cause).__name__}: {str(self.cause)}")
        return "\n".join(parts)

    def __str__(self) -> str:
        """Return formatted error message, regenerated on each call."""
        return self._format_message()


class DataContractError(PeakTradeError):
    """
    Raised when data fails contract validation.

    Examples:
        - Missing OHLCV columns
        - Timezone-naive index
        - NaN values in strict mode
        - Unsorted or duplicate timestamps
        - Invalid price/volume values (negative, high < low, etc.)
    """

    pass


class ConfigError(PeakTradeError):
    """
    Raised when configuration is invalid or incomplete.

    Examples:
        - Unknown config keys
        - Missing required fields
        - Invalid value types or ranges
        - Schema validation failures
    """

    pass


class ProviderError(PeakTradeError):
    """
    Raised when external data providers fail.

    Examples:
        - API timeout or network error
        - Rate limit exceeded
        - Invalid API credentials
        - Unexpected response format
    """

    pass


class CacheCorruptionError(PeakTradeError):
    """
    Raised when cached data fails integrity checks.

    Examples:
        - Checksum mismatch
        - Incomplete/partial write detected
        - Corrupted file format
    """

    pass


class CacheError(PeakTradeError):
    """
    Raised when cache operations fail.

    Examples:
        - Cache write failures
        - Cache read failures
        - Cache access permission issues
        - Cache directory creation failures

    Note:
        Use CacheCorruptionError for data integrity issues.
    """

    pass


class BacktestInvariantError(PeakTradeError):
    """
    Raised when backtest engine detects invariant violations.

    Examples:
        - NaN in equity curve
        - Negative positions without shorting enabled
        - Timestamp misalignment
        - Negative equity (should be caught earlier)
    """

    pass


class StrategyError(PeakTradeError):
    """
    Raised when strategy logic or initialization fails.

    Examples:
        - Invalid strategy parameters
        - Strategy initialization failures
        - Signal generation errors
        - Missing required indicators or data
        - Invalid strategy configuration
    """

    pass


class BacktestError(PeakTradeError):
    """
    Raised when backtest engine operations fail.

    Examples:
        - Invalid backtest configuration
        - Data loading failures during backtest
        - Engine state corruption
        - Result calculation errors
        - Trade execution simulation errors
    """

    pass


class RiskError(PeakTradeError):
    """
    Raised when risk limits are violated or risk management fails.

    Examples:
        - Position size exceeds risk limits
        - Drawdown threshold breached
        - Daily loss limit exceeded
        - Portfolio leverage constraints violated
        - Risk calculation errors
    """

    pass


# Error Context Helpers
# =====================


def add_backtest_context(
    error: PeakTradeError, *, run_id: str, timestamp: pd.Timestamp
) -> PeakTradeError:
    """
    Enrich error with backtest context.

    Args:
        error: Error to enrich
        run_id: Backtest run identifier
        timestamp: Current backtest timestamp

    Returns:
        The same error instance with updated context

    Example:
        >>> error = BacktestError("Equity became negative")
        >>> add_backtest_context(error, run_id="bt_001", timestamp=pd.Timestamp("2024-01-01"))
        >>> # error.context now includes run_id and timestamp
    """
    error.context.update({"run_id": run_id, "timestamp": str(timestamp)})
    return error


def chain_error(original: Exception, new_message: str, **kwargs) -> PeakTradeError:
    """
    Chain exceptions with context preservation.

    Args:
        original: Original exception that was caught
        new_message: New error message providing higher-level context
        **kwargs: Additional arguments (hint, context) for PeakTradeError

    Returns:
        New PeakTradeError with original exception as cause

    Example:
        >>> try:
        ...     load_data()
        ... except IOError as e:
        ...     raise chain_error(
        ...         e,
        ...         "Failed to load market data",
        ...         hint="Check data source credentials in .env",
        ...         context={"symbol": "BTC/USD"}
        ...     )
    """
    return PeakTradeError(new_message, cause=original, **kwargs)
