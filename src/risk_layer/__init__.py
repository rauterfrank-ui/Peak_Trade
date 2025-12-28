"""
Risk Layer Core Module
=======================

Provides the foundational infrastructure for risk management:
- Models for risk decisions and violations
- Audit logging for all risk events
- Risk gate orchestrator for order validation
- Kill switch for emergency safety stops
- Production alerting system (Phase 1)

This is the plumbing layer - VaR, stress testing, and advanced
risk models are implemented in separate modules.
"""

from src.risk_layer.audit_log import AuditLogWriter
from src.risk_layer.kill_switch import KillSwitch, KillSwitchState, ExecutionGate
from src.risk_layer.models import RiskDecision, RiskResult, Violation
from src.risk_layer.risk_gate import RiskGate

# Alerting system (Phase 1)
# Import available but not exported in __all__ to keep core API minimal
# Use: from src.risk_layer.alerting import AlertManager, AlertSeverity, etc.

# Legacy aliases for backwards compatibility
KillSwitchLayer = KillSwitch
KillSwitchStatus = KillSwitchState

__all__ = [
    "Violation",
    "RiskDecision",
    "RiskResult",
    "AuditLogWriter",
    "RiskGate",
    "KillSwitch",
    "KillSwitchState",
    "ExecutionGate",
    # Legacy aliases
    "KillSwitchLayer",
    "KillSwitchStatus",
]
