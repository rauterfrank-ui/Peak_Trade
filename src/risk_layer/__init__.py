"""
Risk Layer Core Module
=======================

Provides the foundational infrastructure for risk management:
- Models for risk decisions and violations
- Audit logging for all risk events
- Risk gate orchestrator for order validation
- Kill switch for emergency safety stops
- Type definitions and protocols for future implementation
- Custom exceptions for clear error semantics

**Phase 0 (Architecture Alignment):**
- Package structure established
- Common types and exceptions defined
- Config anchors set
- Ready for VaR/CVaR implementation (Phase R1)

**Future Phases:**
- R1: Portfolio VaR/CVaR implementation
- R2: VaR Backtesting & Validation
- R3: Stress Testing & Monte Carlo
- R4: 4-Layer Validation Architecture
- R5: Monitoring & Alerting
- R6: Integration & Final Validation

This is the plumbing layer - VaR, stress testing, and advanced
risk models are implemented in separate modules.
"""

from src.risk_layer.audit_log import AuditLogWriter
from src.risk_layer.exceptions import (
    InsufficientDataError,
    RiskCalculationError,
    RiskConfigError,
    RiskLayerError,
    RiskViolationError,
)

# Phase-0 Scaffold: These modules will be implemented in future phases
# from src.risk_layer.kill_switch import KillSwitchLayer, KillSwitchStatus
# from src.risk_layer.models import RiskDecision, RiskResult, Violation
# from src.risk_layer.risk_gate import RiskGate

from src.risk_layer.types import (
    ComponentVaRResult,
    Order,
    Portfolio,
    PortfolioVaRResult,
    RiskConfig,
    RiskMetrics,
    RiskValidationResult,
    StressTestResult,
)

__all__ = [
    # Infrastructure (Phase 0)
    "AuditLogWriter",
    # Type Definitions (Phase 0 Stubs)
    "PortfolioVaRResult",
    "ComponentVaRResult",
    "RiskValidationResult",
    "StressTestResult",
    "RiskMetrics",
    "RiskConfig",
    "Order",
    "Portfolio",
    # Exceptions
    "RiskLayerError",
    "InsufficientDataError",
    "RiskConfigError",
    "RiskCalculationError",
    "RiskViolationError",
    # Future phases (commented out imports above):
    # "Violation", "RiskDecision", "RiskResult",
    # "RiskGate", "KillSwitchLayer", "KillSwitchStatus",
]
