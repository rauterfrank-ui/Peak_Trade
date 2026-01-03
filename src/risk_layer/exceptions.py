"""
Risk Layer Exceptions
=====================

Custom exceptions for risk management operations.
These provide clear error semantics for different failure modes.
"""


class RiskLayerError(Exception):
    """Base exception for all risk layer errors."""

    pass


class InsufficientDataError(RiskLayerError, ValueError):
    """
    Raised when insufficient data is available for risk calculation.

    Examples:
    - Not enough historical data for VaR estimation
    - Missing price data for portfolio valuation
    - Incomplete position information
    """

    pass


class RiskConfigError(RiskLayerError, ValueError):
    """
    Raised when risk configuration is invalid or incomplete.

    Examples:
    - Missing required configuration parameters
    - Invalid confidence level (e.g., outside 0-1 range)
    - Conflicting risk limit settings
    """

    pass


class RiskCalculationError(RiskLayerError):
    """
    Raised when a risk calculation fails unexpectedly.

    Examples:
    - Numerical instability in VaR calculation
    - Matrix inversion failure in covariance estimation
    - Convergence failure in optimization
    """

    pass


class RiskViolationError(RiskLayerError):
    """
    Raised when a risk limit is violated and operation cannot proceed.

    Examples:
    - Position size exceeds limit
    - Portfolio VaR exceeds threshold
    - Stress test failure
    """

    pass
