"""Tests für Risk Layer Exceptions."""

import pytest

from src.risk_layer.exceptions import (
    InsufficientDataError,
    InvalidStateTransitionError,
    RiskLayerError,
    TradingBlockedError,
    ValidationError,
)


def test_risk_layer_error_hierarchy():
    """Test Exception-Hierarchie."""
    assert issubclass(ValidationError, RiskLayerError)
    assert issubclass(InsufficientDataError, RiskLayerError)
    assert issubclass(TradingBlockedError, RiskLayerError)


def test_insufficient_data_error():
    """Test InsufficientDataError."""
    error = InsufficientDataError(required=250, actual=100)

    assert error.required == 250
    assert error.actual == 100
    assert "250" in str(error)
    assert "100" in str(error)


def test_insufficient_data_error_with_message():
    """Test InsufficientDataError mit zusätzlicher Message."""
    error = InsufficientDataError(required=250, actual=100, message="VaR calculation requires 250 days")

    assert "VaR calculation" in str(error)


def test_trading_blocked_error():
    """Test TradingBlockedError."""
    error = TradingBlockedError("Kill Switch active")

    assert error.reason == "Kill Switch active"
    assert "Kill Switch active" in str(error)


def test_invalid_state_transition_error():
    """Test InvalidStateTransitionError."""
    error = InvalidStateTransitionError("ACTIVE", "RECOVERING")

    assert error.from_state == "ACTIVE"
    assert error.to_state == "RECOVERING"
    assert "ACTIVE" in str(error)
    assert "RECOVERING" in str(error)


def test_exception_can_be_caught_as_risk_layer_error():
    """Test dass alle Exceptions als RiskLayerError gefangen werden können."""
    with pytest.raises(RiskLayerError):
        raise ValidationError("Test")

    with pytest.raises(RiskLayerError):
        raise InsufficientDataError(250, 100)

    with pytest.raises(RiskLayerError):
        raise TradingBlockedError("Test")
