"""
Risk Layer Core Module
=======================

Provides the foundational infrastructure for risk management:
- Models for risk decisions and violations
- Audit logging for all risk events
- Risk gate orchestrator for order validation
- Kill switch for emergency safety stops
- Production alerting system (Phase 1)
- Attribution analytics (Phase 3 - NEW)
- Stress testing (Phase 4 - NEW)

This is the plumbing layer - VaR, stress testing, and advanced
risk models are implemented in separate modules.

Usage:
    from src.risk_layer import (
        # Core Types
        RiskDecision, RiskResult, Violation,

        # VaR Backtest
        kupiec_pof_test, KupiecPOFOutput,

        # Attribution (NEW)
        VaRDecomposition, ComponentVaR, PnLAttribution,

        # Stress Testing (NEW)
        StressScenario, ReverseStressResult, ForwardStressResult,

        # Kill Switch
        KillSwitch, KillSwitchState, ExecutionGate,

        # Exceptions
        RiskLayerError, TradingBlockedError,
    )
"""

# ============================================================================
# Core Models
# ============================================================================
from src.risk_layer.audit_log import AuditLogWriter
from src.risk_layer.kill_switch import ExecutionGate, KillSwitch, KillSwitchState
from src.risk_layer.models import RiskDecision, RiskResult, Violation
from src.risk_layer.risk_gate import RiskGate

# ============================================================================
# VaR Backtest
# ============================================================================
from src.risk_layer.var_backtest import (
    KupiecPOFOutput,
    KupiecResult,
    kupiec_pof_test,
)

# Christoffersen & Traffic Light (optional, wenn benötigt)
try:
    from src.risk_layer.var_backtest import (
        TrafficLightZone,
        christoffersen_independence_test,
        traffic_light_test,
    )
except ImportError:
    pass  # Optional features

# ============================================================================
# NEW: Attribution Types (Phase 3)
# ============================================================================
from src.risk_layer.types import (
    ComponentVaR,
    PnLAttribution,
    VaRDecomposition,
)

# ============================================================================
# NEW: Stress Testing Types (Phase 4)
# ============================================================================
from src.risk_layer.types import (
    ForwardStressResult,
    ReverseStressResult,
    StressScenario,
)

# ============================================================================
# NEW: Unified Results
# ============================================================================
from src.risk_layer.types import RiskLayerResult

# ============================================================================
# NEW: Exceptions
# ============================================================================
from src.risk_layer.exceptions import (
    CalculationError,
    ConfigurationError,
    ConvergenceError,
    InsufficientDataError,
    InvalidStateTransitionError,
    KillSwitchError,
    RiskLayerError,
    TradingBlockedError,
    ValidationError,
)

# ============================================================================
# Alerting (Phase 1)
# ============================================================================
# Import available but not exported in __all__ to keep core API minimal
# Use: from src.risk_layer.alerting import AlertManager, AlertSeverity, etc.

# ============================================================================
# Legacy Aliases (Backward Compatibility)
# ============================================================================
KillSwitchLayer = KillSwitch
KillSwitchStatus = KillSwitchState

# ============================================================================
# Public API
# ============================================================================
__all__ = [
    # Core
    "Violation",
    "RiskDecision",
    "RiskResult",
    "RiskLayerResult",
    "AuditLogWriter",
    "RiskGate",
    # Kill Switch
    "KillSwitch",
    "KillSwitchState",
    "ExecutionGate",
    "KillSwitchLayer",  # Legacy
    "KillSwitchStatus",  # Legacy
    # VaR Backtest
    "kupiec_pof_test",
    "KupiecPOFOutput",
    "KupiecResult",
    # Attribution (NEW)
    "ComponentVaR",
    "VaRDecomposition",
    "PnLAttribution",
    # Stress Testing (NEW)
    "StressScenario",
    "ReverseStressResult",
    "ForwardStressResult",
    # Exceptions
    "RiskLayerError",
    "ValidationError",
    "InsufficientDataError",
    "ConfigurationError",
    "CalculationError",
    "ConvergenceError",
    "TradingBlockedError",
    "KillSwitchError",
    "InvalidStateTransitionError",
]
