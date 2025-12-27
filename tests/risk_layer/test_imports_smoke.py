"""
Risk Layer Smoke Tests - Phase 0
=================================

Validates that the risk layer architecture is properly set up:
- All imports work
- Types can be instantiated
- Exceptions can be raised
- No implementation logic tested (Phase 0 = structure only)
"""

from datetime import datetime

import pytest

# Test all imports from risk_layer
from src.risk_layer import (
    AuditLogWriter,
    ComponentVaRResult,
    InsufficientDataError,
    KillSwitchLayer,
    KillSwitchStatus,
    Order,
    Portfolio,
    PortfolioVaRResult,
    RiskCalculationError,
    RiskConfig,
    RiskConfigError,
    RiskDecision,
    RiskGate,
    RiskLayerError,
    RiskMetrics,
    RiskResult,
    RiskValidationResult,
    RiskViolationError,
    StressTestResult,
    Violation,
)


class TestPhase0Imports:
    """Test that all Phase 0 components can be imported."""

    def test_core_models_import(self):
        """Core models (Violation, RiskDecision, RiskResult) are importable."""
        assert Violation is not None
        assert RiskDecision is not None
        assert RiskResult is not None

    def test_infrastructure_import(self):
        """Infrastructure components (RiskGate, KillSwitch, AuditLog) are importable."""
        assert RiskGate is not None
        assert KillSwitchLayer is not None
        assert KillSwitchStatus is not None
        assert AuditLogWriter is not None

    def test_phase0_types_import(self):
        """Phase 0 type stubs are importable."""
        assert PortfolioVaRResult is not None
        assert ComponentVaRResult is not None
        assert RiskValidationResult is not None
        assert StressTestResult is not None
        assert RiskMetrics is not None
        assert RiskConfig is not None

    def test_protocols_import(self):
        """Protocols for external dependencies are importable."""
        assert Order is not None
        assert Portfolio is not None

    def test_exceptions_import(self):
        """All custom exceptions are importable."""
        assert RiskLayerError is not None
        assert InsufficientDataError is not None
        assert RiskConfigError is not None
        assert RiskCalculationError is not None
        assert RiskViolationError is not None


class TestPhase0TypeInstantiation:
    """Test that Phase 0 type stubs can be instantiated."""

    def test_portfolio_var_result_minimal(self):
        """PortfolioVaRResult can be instantiated with defaults."""
        result = PortfolioVaRResult()
        assert result.var_amount == 0.0
        assert result.cvar_amount == 0.0
        assert result.confidence_level == 0.95
        assert result.method == "not_implemented"

    def test_portfolio_var_result_with_values(self):
        """PortfolioVaRResult can be instantiated with custom values."""
        timestamp = datetime(2025, 12, 27, 10, 0, 0)
        result = PortfolioVaRResult(
            var_amount=1000.0,
            cvar_amount=1500.0,
            confidence_level=0.99,
            horizon_days=10,
            method="historical",
            timestamp=timestamp,
            metadata={"source": "test"},
        )
        assert result.var_amount == 1000.0
        assert result.cvar_amount == 1500.0
        assert result.confidence_level == 0.99
        assert result.horizon_days == 10
        assert result.method == "historical"
        assert result.timestamp == timestamp
        assert result.metadata == {"source": "test"}

    def test_component_var_result_minimal(self):
        """ComponentVaRResult can be instantiated with defaults."""
        result = ComponentVaRResult()
        assert result.component_id == ""
        assert result.component_var == 0.0
        assert result.percentage == 0.0

    def test_risk_validation_result_minimal(self):
        """RiskValidationResult can be instantiated with defaults."""
        result = RiskValidationResult()
        assert result.validation_type == "not_implemented"
        assert result.passed is False
        assert result.p_value == 1.0

    def test_stress_test_result_minimal(self):
        """StressTestResult can be instantiated with defaults."""
        result = StressTestResult()
        assert result.scenario_name == "not_implemented"
        assert result.portfolio_pnl == 0.0
        assert result.breach_severity == 0.0

    def test_risk_metrics_minimal(self):
        """RiskMetrics can be instantiated with defaults."""
        result = RiskMetrics()
        assert result.portfolio_var == 0.0
        assert result.alert_level == "OK"
        assert result.validation_status == "unknown"

    def test_risk_config_minimal(self):
        """RiskConfig can be instantiated with defaults."""
        config = RiskConfig()
        assert config.enabled is False
        assert config.var_confidence == 0.95
        assert config.var_horizon_days == 1
        assert config.cvar_enabled is False

    def test_risk_config_custom(self):
        """RiskConfig can be instantiated with custom values."""
        config = RiskConfig(
            enabled=True,
            var_confidence=0.99,
            var_horizon_days=5,
            cvar_enabled=True,
            stress_testing_enabled=True,
        )
        assert config.enabled is True
        assert config.var_confidence == 0.99
        assert config.var_horizon_days == 5
        assert config.cvar_enabled is True
        assert config.stress_testing_enabled is True


class TestPhase0Exceptions:
    """Test that Phase 0 exceptions can be raised and caught."""

    def test_risk_layer_error_base(self):
        """RiskLayerError is the base exception."""
        with pytest.raises(RiskLayerError):
            raise RiskLayerError("Base error")

    def test_insufficient_data_error(self):
        """InsufficientDataError can be raised and caught."""
        with pytest.raises(InsufficientDataError):
            raise InsufficientDataError("Not enough data")

        # Should also be catchable as ValueError (subclass)
        with pytest.raises(ValueError):
            raise InsufficientDataError("Not enough data")

        # Should also be catchable as RiskLayerError (subclass)
        with pytest.raises(RiskLayerError):
            raise InsufficientDataError("Not enough data")

    def test_risk_config_error(self):
        """RiskConfigError can be raised and caught."""
        with pytest.raises(RiskConfigError):
            raise RiskConfigError("Invalid config")

        # Should also be catchable as ValueError
        with pytest.raises(ValueError):
            raise RiskConfigError("Invalid config")

    def test_risk_calculation_error(self):
        """RiskCalculationError can be raised and caught."""
        with pytest.raises(RiskCalculationError):
            raise RiskCalculationError("Calculation failed")

        # Should also be catchable as RiskLayerError
        with pytest.raises(RiskLayerError):
            raise RiskCalculationError("Calculation failed")

    def test_risk_violation_error(self):
        """RiskViolationError can be raised and caught."""
        with pytest.raises(RiskViolationError):
            raise RiskViolationError("Limit exceeded")

        # Should also be catchable as RiskLayerError
        with pytest.raises(RiskLayerError):
            raise RiskViolationError("Limit exceeded")

    def test_exception_hierarchy(self):
        """Verify exception hierarchy is correct."""
        # All custom exceptions inherit from RiskLayerError
        assert issubclass(InsufficientDataError, RiskLayerError)
        assert issubclass(RiskConfigError, RiskLayerError)
        assert issubclass(RiskCalculationError, RiskLayerError)
        assert issubclass(RiskViolationError, RiskLayerError)

        # Some also inherit from ValueError for semantic reasons
        assert issubclass(InsufficientDataError, ValueError)
        assert issubclass(RiskConfigError, ValueError)


class TestPhase0CoreModels:
    """Test that existing core models still work (regression check)."""

    def test_violation_instantiation(self):
        """Violation can be instantiated."""
        v = Violation(
            code="TEST_VIOLATION", message="Test message", severity="WARN", details={"key": "value"}
        )
        assert v.code == "TEST_VIOLATION"
        assert v.message == "Test message"
        assert v.severity == "WARN"
        assert v.details == {"key": "value"}

    def test_risk_decision_instantiation(self):
        """RiskDecision can be instantiated."""
        v1 = Violation(code="V1", message="Violation 1", severity="WARN")
        v2 = Violation(code="V2", message="Violation 2", severity="CRITICAL")

        decision = RiskDecision(
            allowed=False, severity="BLOCK", reason="Multiple violations", violations=[v1, v2]
        )

        assert decision.allowed is False
        assert decision.severity == "BLOCK"
        assert decision.reason == "Multiple violations"
        assert len(decision.violations) == 2


# ============================================================================
# Smoke Test Summary
# ============================================================================
# These tests verify Phase 0 architecture alignment:
# ✅ Package structure is correct (all imports work)
# ✅ Type stubs are properly defined (can be instantiated)
# ✅ Exceptions follow correct hierarchy (can be raised/caught)
# ✅ Existing models still work (no regressions)
#
# What these tests DO NOT verify (future phases):
# ❌ VaR/CVaR calculation logic (Phase R1)
# ❌ Validation algorithms (Phase R2)
# ❌ Stress testing scenarios (Phase R3)
# ❌ Integration with execution pipeline (Phase R4)
# ============================================================================
