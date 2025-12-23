"""
Peak_Trade Risk Module
=======================
Position Sizing, Stop-Loss-Management, Risk-Limits.

v1 Risk Layer:
- Portfolio-Level Risk (Exposures, Weights, Correlations)
- VaR / CVaR (Historical + Parametric)
- Stress-Testing (Szenarien-Engine)
- Risk-Limit Enforcement (Hard limits + Circuit Breaker)
"""

# Legacy Position Sizing & Limits
from .position_sizer import (
    PositionSizer,
    PositionSizerConfig,
    PositionRequest,
    PositionResult,
    calc_position_size,
)
from .limits import RiskLimits, RiskLimitsConfig

# v1 Risk Layer
from .types import (
    PositionSnapshot,
    PortfolioSnapshot,
    RiskBreach,
    RiskDecision,
    BreachSeverity,
)
from .portfolio import (
    compute_position_notional,
    compute_gross_exposure,
    compute_net_exposure,
    compute_weights,
    correlation_matrix,
    portfolio_returns,
)
from .var import (
    historical_var,
    historical_cvar,
    parametric_var,
    parametric_cvar,
)
from .stress import (
    StressScenario,
    apply_scenario_to_returns,
    run_stress_suite,
)
from .enforcement import (
    RiskLimitsV2,
    RiskEnforcer,
)

__all__ = [
    # Legacy Position Sizing
    "PositionSizer",
    "PositionSizerConfig",
    "PositionRequest",
    "PositionResult",
    "calc_position_size",
    # Legacy Risk Limits
    "RiskLimits",
    "RiskLimitsConfig",
    # v1 Types
    "PositionSnapshot",
    "PortfolioSnapshot",
    "RiskBreach",
    "RiskDecision",
    "BreachSeverity",
    # v1 Portfolio Analytics
    "compute_position_notional",
    "compute_gross_exposure",
    "compute_net_exposure",
    "compute_weights",
    "correlation_matrix",
    "portfolio_returns",
    # v1 VaR/CVaR
    "historical_var",
    "historical_cvar",
    "parametric_var",
    "parametric_cvar",
    # v1 Stress Testing
    "StressScenario",
    "apply_scenario_to_returns",
    "run_stress_suite",
    # v1 Enforcement
    "RiskLimitsV2",
    "RiskEnforcer",
]
