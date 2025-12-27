"""
Risk Layer Type Definitions
============================

Type stubs and protocols for risk management components.
These define the interfaces that will be implemented in future phases.

Phase 0: Stub definitions for architecture alignment
Future Phases: Full implementations with business logic
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Protocol


# ============================================================================
# Phase 0: Stubs for Future VaR/CVaR Implementation
# ============================================================================


@dataclass
class PortfolioVaRResult:
    """
    Result of portfolio Value-at-Risk calculation.

    **Status:** STUB (Phase 0)
    **Implementation:** Phase R1 (Portfolio VaR/CVaR)

    Attributes:
        var_amount: VaR in monetary units
        cvar_amount: CVaR (Expected Shortfall) in monetary units
        confidence_level: Confidence level (e.g., 0.95, 0.99)
        horizon_days: Time horizon in days
        method: Calculation method (e.g., "historical", "parametric", "monte_carlo")
        timestamp: When the calculation was performed
        metadata: Additional calculation details
    """

    var_amount: float = 0.0
    cvar_amount: float = 0.0
    confidence_level: float = 0.95
    horizon_days: int = 1
    method: str = "not_implemented"
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentVaRResult:
    """
    Component VaR for risk attribution.

    **Status:** STUB (Phase 0)
    **Implementation:** Phase R1 (Component VaR)

    Attributes:
        component_id: Identifier for the component (e.g., asset symbol, strategy ID)
        component_var: VaR contribution of this component
        percentage: Percentage contribution to total portfolio VaR
        marginal_var: Marginal VaR (dVaR/dPosition)
        incremental_var: Incremental VaR (VaR with - VaR without component)
    """

    component_id: str = ""
    component_var: float = 0.0
    percentage: float = 0.0
    marginal_var: float = 0.0
    incremental_var: float = 0.0


@dataclass
class RiskValidationResult:
    """
    Result of risk model validation (backtesting).

    **Status:** STUB (Phase 0)
    **Implementation:** Phase R2 (VaR Backtesting & Validation)

    Attributes:
        validation_type: Type of validation (e.g., "kupiec_test", "christoffersen_test")
        passed: Whether validation passed
        p_value: Statistical significance
        violations_count: Number of VaR violations observed
        expected_violations: Expected number of violations
        confidence: Confidence level of the test
        details: Additional validation metrics
    """

    validation_type: str = "not_implemented"
    passed: bool = False
    p_value: float = 1.0
    violations_count: int = 0
    expected_violations: float = 0.0
    confidence: float = 0.95
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class StressTestResult:
    """
    Result of a stress test scenario.

    **Status:** STUB (Phase 0)
    **Implementation:** Phase R3 (Stress Testing)

    Attributes:
        scenario_name: Name of the stress scenario
        portfolio_pnl: Expected P&L under stress
        var_under_stress: VaR under stress scenario
        max_drawdown: Maximum drawdown in scenario
        breach_severity: Severity of limit breaches (0.0 = no breach, >1.0 = severe)
        component_impacts: Per-component stress impacts
    """

    scenario_name: str = "not_implemented"
    portfolio_pnl: float = 0.0
    var_under_stress: float = 0.0
    max_drawdown: float = 0.0
    breach_severity: float = 0.0
    component_impacts: dict[str, float] = field(default_factory=dict)


@dataclass
class RiskMetrics:
    """
    Comprehensive risk metrics for monitoring and reporting.

    **Status:** STUB (Phase 0)
    **Implementation:** Phase R5 (Monitoring & Alerting)

    Attributes:
        timestamp: When metrics were calculated
        portfolio_var: Current portfolio VaR
        portfolio_cvar: Current portfolio CVaR
        utilization: Risk limit utilization (0.0 to 1.0)
        stress_score: Aggregate stress test score
        validation_status: Latest validation result
        alert_level: Current alert level (OK, WARN, CRITICAL)
    """

    timestamp: datetime = field(default_factory=datetime.now)
    portfolio_var: float = 0.0
    portfolio_cvar: float = 0.0
    utilization: float = 0.0
    stress_score: float = 0.0
    validation_status: str = "unknown"
    alert_level: str = "OK"


@dataclass
class RiskConfig:
    """
    Configuration for risk layer operations.

    **Status:** STUB (Phase 0)
    **Implementation:** Phase R1+ (incremental)

    Attributes:
        enabled: Whether risk layer is enabled
        var_confidence: VaR confidence level
        var_horizon_days: VaR time horizon
        cvar_enabled: Whether to calculate CVaR
        stress_testing_enabled: Whether to run stress tests
        validation_frequency_days: How often to run validation
        alert_threshold_utilization: Utilization threshold for alerts
    """

    enabled: bool = False
    var_confidence: float = 0.95
    var_horizon_days: int = 1
    cvar_enabled: bool = False
    stress_testing_enabled: bool = False
    validation_frequency_days: int = 7
    alert_threshold_utilization: float = 0.8


# ============================================================================
# Protocols for External Dependencies
# ============================================================================


class Order(Protocol):
    """
    Minimal protocol for order objects.

    Risk layer needs to validate orders without depending on specific
    order implementations. This protocol defines the minimum interface.
    """

    symbol: str
    side: str  # "buy" or "sell"
    quantity: float
    price: Optional[float]


class Portfolio(Protocol):
    """
    Minimal protocol for portfolio objects.

    Risk layer needs to assess portfolio risk without depending on
    specific portfolio implementations.
    """

    def get_positions(self) -> dict[str, float]:
        """Return current positions as {symbol: quantity}."""
        ...

    def get_total_value(self) -> float:
        """Return total portfolio value in base currency."""
        ...
