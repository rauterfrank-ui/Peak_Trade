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
from src.risk_layer.kill_switch import KillSwitchLayer, to_violations
from src.risk_layer.metrics import extract_risk_metrics, metrics_to_dict
from src.risk_layer.models import RiskDecision, RiskResult, Violation
from src.risk_layer.var_gate import VaRGate, status_to_dict


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

        # Initialize kill switch
        self._kill_switch = KillSwitchLayer(cfg)

        # Initialize VaR gate
        self._var_gate = VaRGate(cfg)

    def evaluate(self, order: dict, context: dict | None = None) -> RiskResult:
        """
        Evaluate an order against risk rules.

        Args:
            order: Order dict (must contain "symbol" and "qty")
            context: Optional context dict with additional data
                     Can include metrics for kill switch evaluation

        Returns:
            RiskResult with decision and audit event
        """
        violations: list[Violation] = []

        # Normalize context
        if context is None:
            context = {}

        # Evaluate kill switch first
        # Extract metrics using canonical extractor (tolerant: nested/direct)
        risk_metrics = extract_risk_metrics(context)
        kill_switch_status = self._kill_switch.evaluate(risk_metrics)

        # If kill switch is armed, block immediately
        if kill_switch_status.armed:
            kill_switch_violations = to_violations(kill_switch_status)
            decision = RiskDecision(
                allowed=False,
                severity="BLOCK",
                reason=f"Kill switch armed: {kill_switch_status.reason}",
                violations=kill_switch_violations,
            )
            # Evaluate VaR gate for audit (even if blocked)
            var_gate_status = self._var_gate.evaluate(context)
        else:
            # Evaluate VaR gate (after kill switch, before order validation)
            var_gate_status = self._var_gate.evaluate(context)

            # If VaR gate blocks, stop here
            if var_gate_status.severity == "BLOCK":
                violations.append(
                    Violation(
                        code="VAR_LIMIT_EXCEEDED",
                        message=var_gate_status.reason,
                        severity="CRITICAL",
                        details={
                            "var_pct": var_gate_status.var_pct,
                            "threshold": var_gate_status.threshold_block,
                            "method": var_gate_status.method,
                            "confidence": var_gate_status.confidence,
                        },
                    )
                )
                decision = RiskDecision(
                    allowed=False,
                    severity="BLOCK",
                    reason=f"VaR limit exceeded: {var_gate_status.reason}",
                    violations=violations,
                )
            elif var_gate_status.severity == "WARN":
                # Add warning violation but continue
                violations.append(
                    Violation(
                        code="VAR_NEAR_LIMIT",
                        message=var_gate_status.reason,
                        severity="WARNING",
                        details={
                            "var_pct": var_gate_status.var_pct,
                            "threshold_warn": var_gate_status.threshold_warn,
                            "threshold_block": var_gate_status.threshold_block,
                        },
                    )
                )

            # Continue with normal order validation (if not blocked by VaR)
            # Only do order validation if not already blocked by VaR
            if var_gate_status.severity != "BLOCK":
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
                    # All checks passed
                    severity = "WARN" if var_gate_status.severity == "WARN" else "OK"
                    decision = RiskDecision(
                        allowed=True,
                        severity=severity,
                        reason="Order passed all risk checks",
                        violations=violations,  # May include WARN violations
                    )

        # Build audit event
        audit_event = self._build_audit_event(
            order, decision, context, kill_switch_status, var_gate_status
        )

        # Write to audit log
        self.audit_log.write(audit_event)

        return RiskResult(decision=decision, audit_event=audit_event)

    def _build_audit_event(
        self,
        order: dict,
        decision: RiskDecision,
        context: dict | None,
        kill_switch_status,
        var_gate_status,
    ) -> dict:
        """
        Build audit event dict.

        Args:
            order: The order being evaluated
            decision: The risk decision
            context: Optional context
            kill_switch_status: KillSwitchStatus from evaluation
            var_gate_status: VaRGateStatus from evaluation

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
            "kill_switch": {
                "enabled": self._kill_switch.enabled,
                "status": {
                    "armed": kill_switch_status.armed,
                    "severity": kill_switch_status.severity,
                    "reason": kill_switch_status.reason,
                    "triggered_by": kill_switch_status.triggered_by,
                    "timestamp_utc": kill_switch_status.timestamp_utc,
                },
                "metrics_snapshot": kill_switch_status.metrics_snapshot,
            },
            "var_gate": {
                "enabled": self._var_gate.enabled,
                "result": status_to_dict(var_gate_status),
            },
            "order": sanitized_order,
            "context": self._sanitize_context(context or {}),
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

    def _sanitize_context(self, context: dict) -> dict:
        """
        Sanitize context for audit log.

        Removes non-JSON-serializable objects like DataFrames.

        Args:
            context: Context dict to sanitize

        Returns:
            Sanitized context dict
        """
        import pandas as pd

        sanitized = {}
        for key, value in context.items():
            # Skip DataFrames and other non-serializable objects
            if isinstance(value, pd.DataFrame):
                sanitized[key] = {
                    "_type": "DataFrame",
                    "shape": value.shape,
                    "columns": list(value.columns),
                }
            elif isinstance(value, (list, tuple)) and len(value) > 0:
                # Check if it's a list of non-serializable objects
                if isinstance(value[0], pd.DataFrame):
                    sanitized[key] = {"_type": "list[DataFrame]", "length": len(value)}
                else:
                    sanitized[key] = value
            elif isinstance(value, dict):
                # Recursively sanitize nested dicts
                sanitized[key] = self._sanitize_context(value)
            else:
                # Keep primitive types
                sanitized[key] = value

        return sanitized

    def reset_kill_switch(self, reason: str = "manual_reset"):
        """
        Reset the kill switch (disarm).

        This delegates to the underlying KillSwitchLayer.reset() method.
        Only use after proper incident review (see KILL_SWITCH_RUNBOOK.md).

        Args:
            reason: Reason for reset (for audit trail)

        Returns:
            KillSwitchStatus after reset (armed=False)
        """
        from src.risk_layer.kill_switch import KillSwitchStatus

        if not self._kill_switch.enabled:
            # Kill switch is disabled, return unarmed status
            return KillSwitchStatus(
                armed=False,
                severity="OK",
                reason="Kill switch disabled",
                triggered_by=[],
                metrics_snapshot={},
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
            )

        return self._kill_switch.reset(reason)

    def get_kill_switch_status(self, context: dict | None = None):
        """
        Get current kill switch status.

        Args:
            context: Optional context dict with metrics
                     If provided, evaluates kill switch with fresh metrics
                     If None, returns last known status

        Returns:
            KillSwitchStatus object with current status
        """
        from src.risk_layer.kill_switch import KillSwitchStatus

        if not self._kill_switch.enabled:
            return KillSwitchStatus(
                armed=False,
                severity="OK",
                reason="Kill switch disabled",
                triggered_by=[],
                metrics_snapshot={},
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
            )

        if context is not None:
            # Evaluate with fresh metrics using canonical extractor
            risk_metrics = extract_risk_metrics(context)
            return self._kill_switch.evaluate(risk_metrics)

        # Return last known status
        if self._kill_switch._last_status is not None:
            return self._kill_switch._last_status

        # No status available, return default unarmed
        return KillSwitchStatus(
            armed=False,
            severity="OK",
            reason="No status available (not yet evaluated)",
            triggered_by=[],
            metrics_snapshot={},
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )
