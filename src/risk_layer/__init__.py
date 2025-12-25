"""
Risk Layer Core Module
=======================

Provides the foundational infrastructure for risk management:
- Models for risk decisions and violations
- Audit logging for all risk events
- Risk gate orchestrator for order validation
- Adapters for order normalization

This is the plumbing layer - VaR, stress testing, and advanced
risk models are implemented in separate modules.
"""

from src.risk_layer.adapters import order_to_dict, to_order
from src.risk_layer.audit_log import AuditLogWriter
from src.risk_layer.models import RiskDecision, RiskResult, Violation
from src.risk_layer.risk_gate import RiskGate

__all__ = [
    "Violation",
    "RiskDecision",
    "RiskResult",
    "AuditLogWriter",
    "RiskGate",
    "to_order",
    "order_to_dict",
]
