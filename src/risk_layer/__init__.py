"""
Risk Layer Core Module
=======================

Provides the foundational infrastructure for risk management:
- Models for risk decisions and violations
- Audit logging for all risk events
- Risk gate orchestrator for order validation
- Adapters for order normalization
- Type definitions and protocols for future implementation
- Custom exceptions for clear error semantics

**Current Implementation:**
- Core risk gate with order validation
- JSONL audit logging
- Canonical order contract and adapters

**Phase 0 Type Definitions (for future VaR/CVaR):**
- PortfolioVaRResult, ComponentVaRResult
- RiskValidationResult, StressTestResult
- Ready for VaR/CVaR implementation

This is the plumbing layer - VaR, stress testing, and advanced
risk models are implemented in separate modules.
"""

# Core Implementation (PR #334)
from src.risk_layer.adapters import order_to_dict, to_order
from src.risk_layer.audit_log import AuditLogWriter
from src.risk_layer.models import RiskDecision, RiskResult, Violation
from src.risk_layer.risk_gate import RiskGate

# Type Definitions & Exceptions (Phase 0 Scaffold)
from src.risk_layer.exceptions import (
    InsufficientDataError,
    RiskCalculationError,
    RiskConfigError,
    RiskLayerError,
    RiskViolationError,
)
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
    # Core Implementation
    "Violation",
    "RiskDecision",
    "RiskResult",
    "AuditLogWriter",
    "RiskGate",
    "to_order",
    "order_to_dict",
    # Type Definitions (Phase 0)
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
]
