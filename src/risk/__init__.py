"""
Peak_Trade Risk Module
=======================
Position Sizing, Stop-Loss-Management, Risk-Limits.

v1 Risk Layer:
- Portfolio-Level Risk (Exposures, Weights, Correlations)
- VaR / CVaR (Historical + Parametric)
- Stress-Testing (Szenarien-Engine)
- Risk-Limit Enforcement (Hard limits + Circuit Breaker)
- Component VaR (Parametric Attribution via Euler Allocation)
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
    cornish_fisher_var,
    cornish_fisher_cvar,
    ewma_var,
    ewma_cvar,
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

# Component VaR (Parametric Attribution)
from .covariance import (
    CovarianceEstimator,
    CovarianceEstimatorConfig,
    CovarianceMethod,
)
from .parametric_var import (
    ParametricVaR,
    ParametricVaRConfig,
    z_score,
    portfolio_sigma_from_cov,
)
from .component_var import (
    ComponentVaRCalculator,
    ComponentVaRResult,
    IncrementalVaRResult,
    DiversificationBenefitResult,
    calculate_incremental_var,
    calculate_diversification_benefit,
)

# Monte Carlo VaR (Risk Layer v1.0)
from .monte_carlo import (
    MonteCarloVaRCalculator,
    MonteCarloVaRConfig,
    MonteCarloVaRResult,
    EquityPathResult,
    MonteCarloMethod,
    CopulaType,
    build_monte_carlo_var_from_config,
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
    "cornish_fisher_var",
    "cornish_fisher_cvar",
    "ewma_var",
    "ewma_cvar",
    # v1 Stress Testing
    "StressScenario",
    "apply_scenario_to_returns",
    "run_stress_suite",
    # v1 Enforcement
    "RiskLimitsV2",
    "RiskEnforcer",
    # Component VaR
    "CovarianceEstimator",
    "CovarianceEstimatorConfig",
    "CovarianceMethod",
    "ParametricVaR",
    "ParametricVaRConfig",
    "z_score",
    "portfolio_sigma_from_cov",
    "ComponentVaRCalculator",
    "ComponentVaRResult",
    "IncrementalVaRResult",
    "DiversificationBenefitResult",
    "calculate_incremental_var",
    "calculate_diversification_benefit",
    # Monte Carlo VaR (Risk Layer v1.0)
    "MonteCarloVaRCalculator",
    "MonteCarloVaRConfig",
    "MonteCarloVaRResult",
    "EquityPathResult",
    "MonteCarloMethod",
    "CopulaType",
    "build_monte_carlo_var_from_config",
]
