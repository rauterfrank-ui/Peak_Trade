"""
Risk Gate Orchestrator
======================

Central orchestrator for risk evaluation and audit logging.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, Union

from src.core.peak_config import PeakConfig
from src.execution_simple.types import Order
from src.risk_layer.adapters import order_to_dict, to_order
from src.risk_layer.audit_log import AuditLogWriter
from src.risk_layer.models import RiskDecision, RiskResult, Violation


class RiskGate:
    """
    Orchestrates risk evaluation and audit logging.

    In this skeleton version, only basic validation is performed.
    Future versions will integrate VaR, stress testing, and other
    risk models.
    """

    def __init__(self, cfg: PeakConfig) -> None:
        """
        Initialize the risk gate.

        Args:
            cfg: PeakConfig instance
        """
        self.cfg = cfg

        # Get audit log path from config
        audit_path = cfg.get("risk.audit_log.path", "./logs/risk_audit.jsonl")
        self.audit_log = AuditLogWriter(audit_path)

    def evaluate(self, order: Union[Order, dict], context: Optional[dict] = None) -> RiskResult:
        """
        Evaluate an order against risk rules.

        Args:
            order: Order object or dict (dict must contain "symbol" and "qty"/"quantity")
            context: Optional context dict with additional data

        Returns:
            RiskResult with decision and audit event
        """
        violations: list[Violation] = []

        # Normalize order to Order object
        try:
            order_obj = to_order(order)
        except ValueError as e:
            # Conversion failed - treat as critical violation
            violations.append(
                Violation(
                    code="ORDER_CONVERSION_FAILED",
                    message=str(e),
                    severity="CRITICAL",
                    details={"order_input_type": type(order).__name__},
                )
            )

        # Determine decision
        if violations:
            decision = RiskDecision(
                allowed=False,
                severity="BLOCK",
                reason="Order validation failed",
                violations=violations,
            )
            # Use original order for audit if conversion failed
            order_for_audit = order if not isinstance(order, Order) else order_obj
        else:
            decision = RiskDecision(
                allowed=True,
                severity="OK",
                reason="Order passed basic validation",
                violations=[],
            )
            order_for_audit = order_obj

        # Build audit event
        audit_event = self._build_audit_event(order_for_audit, decision, context)

        # Write to audit log
        self.audit_log.write(audit_event)

        return RiskResult(decision=decision, audit_event=audit_event)

    def _build_audit_event(
        self, order: Union[Order, dict], decision: RiskDecision, context: Optional[dict]
    ) -> dict:
        """
        Build audit event dict.

        Args:
            order: The order being evaluated (Order or dict)
            decision: The risk decision
            context: Optional context

        Returns:
            Dict containing the audit event
        """
        # Convert to dict for serialization
        if isinstance(order, Order):
            sanitized_order = order_to_dict(order)
        else:
            sanitized_order = self._sanitize_order(order)

        return {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "decision": {
                "allowed": decision.allowed,
                "severity": decision.severity,
                "reason": decision.reason,
            },
            "violations": [
                {
                    "code": v.code,
                    "message": v.message,
                    "severity": v.severity,
                    "details": v.details,
                }
                for v in decision.violations
            ],
            "order": sanitized_order,
            "context": context or {},
        }

    def _sanitize_order(self, order: Any) -> dict:
        """
        Sanitize order for audit log.

        Args:
            order: The order to sanitize

        Returns:
            Sanitized order dict
        """
        if not isinstance(order, dict):
            return {"_type": type(order).__name__, "_repr": str(order)}

        # For now, just return a copy
        # Future: remove sensitive fields like API keys
        return dict(order)
