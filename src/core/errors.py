"""
Peak_Trade Error Taxonomy (Wave A - Stability Plan)
====================================================
Structured error hierarchy with hints and context for better debugging.

Design Principles:
- Fail-fast with clear messages
- Always provide actionable hints
- Include context dict for programmatic access
- Inherit from common base for uniform handling

Usage:
    from src.core.errors import ConfigError, DataContractError

    raise ConfigError(
        "Unknown strategy key: 'foo'",
        hint="Available strategies: ['momentum', 'mean_reversion']",
        context={"key": "foo", "available": ["momentum", "mean_reversion"]}
    )
"""
from typing import Any, Dict, Optional


class PeakTradeError(Exception):
    """
    Base exception for all Peak_Trade errors.

    Attributes:
        message: Human-readable error message
        hint: Suggested fix or next steps (optional)
        context: Dict with additional context for debugging (optional)
    """

    def __init__(
        self,
        message: str,
        hint: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.hint = hint
        self.context = context or {}
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format error message with hint and context."""
        parts = [f"{self.__class__.__name__}: {self.message}"]
        if self.hint:
            parts.append(f"Hint: {self.hint}")
        if self.context:
            parts.append(f"Context: {self.context}")
        return "\n".join(parts)


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
