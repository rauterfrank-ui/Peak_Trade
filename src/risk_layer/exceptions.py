"""
Risk Layer Exceptions
======================

Unified exception hierarchy for Risk Layer.
"""


class RiskLayerError(Exception):
    """Base exception for all Risk Layer errors."""

    pass


# ============================================================================
# Validation Errors
# ============================================================================


class ValidationError(RiskLayerError):
    """Input validation failed."""

    pass


class InsufficientDataError(RiskLayerError):
    """Not enough data for calculation."""

    def __init__(self, required: int, actual: int, message: str = ""):
        self.required = required
        self.actual = actual
        msg = f"Insufficient data: required {required}, got {actual}"
        if message:
            msg = f"{msg}. {message}"
        super().__init__(msg)


class ConfigurationError(RiskLayerError):
    """Configuration is invalid or missing."""

    pass


# ============================================================================
# Calculation Errors
# ============================================================================


class CalculationError(RiskLayerError):
    """Calculation failed."""

    pass


class ConvergenceError(CalculationError):
    """Optimization did not converge."""

    def __init__(self, message: str = "Optimization failed to converge"):
        super().__init__(message)


class NumericalError(CalculationError):
    """Numerical instability detected."""

    pass


# ============================================================================
# Integration Errors
# ============================================================================


class IntegrationError(RiskLayerError):
    """Integration with other systems failed."""

    pass


class TradingBlockedError(RiskLayerError):
    """Trading is blocked by Risk Layer."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Trading blocked: {reason}")


# ============================================================================
# Kill Switch Errors
# ============================================================================


class KillSwitchError(RiskLayerError):
    """Kill Switch specific error."""

    pass


class InvalidStateTransitionError(KillSwitchError):
    """Invalid Kill Switch state transition."""

    def __init__(self, from_state: str, to_state: str):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Invalid state transition: {from_state} → {to_state}")
