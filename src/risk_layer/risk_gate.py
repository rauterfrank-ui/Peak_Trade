"""
Risk Gate Orchestrator
======================

Central orchestrator for risk evaluation and audit logging.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.core.peak_config import PeakConfig
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

    def evaluate(self, order: dict, context: dict | None = None) -> RiskResult:
        """
        Evaluate an order against risk rules.

        Args:
            order: Order dict (must contain "symbol" and "qty")
            context: Optional context dict with additional data

        Returns:
            RiskResult with decision and audit event
        """
        violations: list[Violation] = []

        # Basic validation: order must be a dict
        if not isinstance(order, dict):
            violations.append(
                Violation(
                    code="INVALID_ORDER_TYPE",
                    message="Order must be a dict",
                    severity="CRITICAL",
                    details={"order_type": type(order).__name__},
                )
            )

        # Check required fields
        if "symbol" not in order:
            violations.append(
                Violation(
                    code="MISSING_SYMBOL",
                    message="Order missing required field: symbol",
                    severity="CRITICAL",
                    details={},
                )
            )

        if "qty" not in order:
            violations.append(
                Violation(
                    code="MISSING_QTY",
                    message="Order missing required field: qty",
                    severity="CRITICAL",
                    details={},
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
        else:
            decision = RiskDecision(
                allowed=True,
                severity="OK",
                reason="Order passed basic validation",
                violations=[],
            )

        # Build audit event
        audit_event = self._build_audit_event(order, decision, context)

        # Write to audit log
        self.audit_log.write(audit_event)

        return RiskResult(decision=decision, audit_event=audit_event)

    def _build_audit_event(
        self, order: dict, decision: RiskDecision, context: dict | None
    ) -> dict:
        """
        Build audit event dict.

        Args:
            order: The order being evaluated
            decision: The risk decision
            context: Optional context

        Returns:
            Dict containing the audit event
        """
        # Sanitize order (remove sensitive data if needed)
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

