#!/usr/bin/env python3
"""
Risk-Layer Alerting Integration Example
========================================

Shows how to integrate the multi-channel alerting system with existing
risk_layer components (risk_gate, var_gate, kill_switch, etc.).
"""

from datetime import datetime, timezone
from typing import Optional

from src.risk_layer.alerting import (
    AlertDispatcher,
    AlertEvent,
    AlertSeverity,
    ConsoleChannel,
    FileChannel,
)
from src.risk_layer.models import RiskDecision, Violation


class RiskAlertingIntegration:
    """
    Integration layer between risk_layer and alerting system.
    
    Converts risk decisions and violations into structured alerts.
    """
    
    def __init__(self, dispatcher: AlertDispatcher):
        """Initialize with alert dispatcher."""
        self.dispatcher = dispatcher
    
    def alert_from_risk_decision(
        self,
        decision: RiskDecision,
        source: str,
        order_id: Optional[str] = None,
    ) -> Optional[AlertEvent]:
        """
        Create alert from risk decision.
        
        Args:
            decision: Risk decision from risk gate
            source: Source component (e.g., "risk_gate", "var_gate")
            order_id: Optional order ID for context
            
        Returns:
            AlertEvent if decision severity warrants an alert, None otherwise
        """
        # Map risk decision severity to alert severity
        severity_map = {
            "OK": None,  # No alert needed
            "WARN": AlertSeverity.WARN,
            "BLOCK": AlertSeverity.CRITICAL,
        }
        
        alert_severity = severity_map.get(decision.severity)
        if alert_severity is None:
            return None  # No alert for OK status
        
        # Build title and labels
        if decision.allowed:
            title = f"Risk Warning: {source}"
        else:
            title = f"Risk Block: {source}"
        
        labels = {
            "source": source,
            "allowed": str(decision.allowed),
            "severity": decision.severity,
        }
        
        if order_id:
            labels["order_id"] = order_id
        
        # Include violation details
        metadata = {
            "violations": [
                {
                    "code": v.code,
                    "message": v.message,
                    "severity": v.severity,
                    "details": v.details,
                }
                for v in decision.violations
            ]
        }
        
        alert = AlertEvent(
            source=source,
            severity=alert_severity,
            title=title,
            body=decision.reason,
            labels=labels,
            metadata=metadata,
        )
        
        return alert
    
    def alert_from_violation(
        self,
        violation: Violation,
        source: str,
        context: Optional[dict] = None,
    ) -> AlertEvent:
        """
        Create alert from individual violation.
        
        Args:
            violation: Violation instance
            source: Source component
            context: Optional context dict
            
        Returns:
            AlertEvent
        """
        # Map violation severity to alert severity
        severity_map = {
            "INFO": AlertSeverity.INFO,
            "WARN": AlertSeverity.WARN,
            "CRITICAL": AlertSeverity.CRITICAL,
        }
        
        alert = AlertEvent(
            source=source,
            severity=severity_map[violation.severity],
            title=f"Risk Violation: {violation.code}",
            body=violation.message,
            labels={"code": violation.code, "severity": violation.severity},
            metadata={"details": violation.details, "context": context or {}},
        )
        
        return alert
    
    def dispatch_decision(
        self,
        decision: RiskDecision,
        source: str,
        order_id: Optional[str] = None,
    ) -> dict:
        """
        Convert risk decision to alert and dispatch.
        
        Returns:
            Dispatch results dict
        """
        alert = self.alert_from_risk_decision(decision, source, order_id)
        
        if alert is None:
            return {}
        
        return self.dispatcher.dispatch(alert)


def example_risk_gate_integration():
    """Example: Integrate alerting with risk gate."""
    print("\n" + "=" * 80)
    print("Example: Risk Gate Integration")
    print("=" * 80 + "\n")
    
    # Setup dispatcher
    console = ConsoleChannel()
    dispatcher = AlertDispatcher(channels=[console])
    integration = RiskAlertingIntegration(dispatcher)
    
    # Simulate risk gate decision (BLOCK)
    decision = RiskDecision(
        allowed=False,
        severity="BLOCK",
        reason="Position size exceeds configured limit",
        violations=[
            Violation(
                code="POSITION_SIZE_EXCEEDED",
                message="Position size of 1000 exceeds limit of 800",
                severity="CRITICAL",
                details={"position_size": 1000, "limit": 800, "pct": 125.0},
            ),
            Violation(
                code="PORTFOLIO_EXPOSURE_HIGH",
                message="Portfolio exposure at 95% of max",
                severity="WARN",
                details={"exposure_pct": 95.0, "max_pct": 100.0},
            ),
        ],
    )
    
    # Dispatch alert
    print("Risk Gate Decision:")
    print(f"  Allowed: {decision.allowed}")
    print(f"  Severity: {decision.severity}")
    print(f"  Reason: {decision.reason}")
    print(f"  Violations: {len(decision.violations)}")
    print()
    
    results = integration.dispatch_decision(
        decision=decision,
        source="risk_gate",
        order_id="order-12345",
    )
    
    print(f"\nDispatch Results: {results}")


def example_var_gate_integration():
    """Example: Integrate alerting with VaR gate."""
    print("\n" + "=" * 80)
    print("Example: VaR Gate Integration")
    print("=" * 80 + "\n")
    
    # Setup dispatcher
    console = ConsoleChannel()
    dispatcher = AlertDispatcher(channels=[console])
    integration = RiskAlertingIntegration(dispatcher)
    
    # Simulate VaR gate warning
    decision = RiskDecision(
        allowed=True,
        severity="WARN",
        reason="Portfolio VaR approaching threshold (90%)",
        violations=[
            Violation(
                code="VAR_THRESHOLD_WARNING",
                message="VaR at 0.045 approaching threshold 0.05",
                severity="WARN",
                details={
                    "current_var": 0.045,
                    "threshold": 0.05,
                    "pct_of_threshold": 90.0,
                },
            ),
        ],
    )
    
    print("VaR Gate Decision:")
    print(f"  Allowed: {decision.allowed}")
    print(f"  Severity: {decision.severity}")
    print(f"  Reason: {decision.reason}")
    print()
    
    results = integration.dispatch_decision(
        decision=decision,
        source="var_gate",
    )
    
    print(f"\nDispatch Results: {results}")


def example_kill_switch_integration():
    """Example: Integrate alerting with kill switch."""
    print("\n" + "=" * 80)
    print("Example: Kill Switch Integration")
    print("=" * 80 + "\n")
    
    # Setup dispatcher
    console = ConsoleChannel()
    dispatcher = AlertDispatcher(channels=[console])
    integration = RiskAlertingIntegration(dispatcher)
    
    # Simulate kill switch activation
    decision = RiskDecision(
        allowed=False,
        severity="BLOCK",
        reason="Kill switch activated due to excessive drawdown",
        violations=[
            Violation(
                code="KILL_SWITCH_ACTIVE",
                message="Drawdown of 15% exceeds limit of 10%",
                severity="CRITICAL",
                details={
                    "drawdown": 0.15,
                    "limit": 0.10,
                    "trigger_time": datetime.now(timezone.utc).isoformat(),
                },
            ),
        ],
    )
    
    print("Kill Switch Decision:")
    print(f"  Allowed: {decision.allowed}")
    print(f"  Severity: {decision.severity}")
    print(f"  Reason: {decision.reason}")
    print()
    
    results = integration.dispatch_decision(
        decision=decision,
        source="kill_switch",
    )
    
    print(f"\nDispatch Results: {results}")


def example_custom_violation_alert():
    """Example: Create alert from custom violation."""
    print("\n" + "=" * 80)
    print("Example: Custom Violation Alert")
    print("=" * 80 + "\n")
    
    # Setup dispatcher
    console = ConsoleChannel()
    dispatcher = AlertDispatcher(channels=[console])
    integration = RiskAlertingIntegration(dispatcher)
    
    # Create custom violation
    violation = Violation(
        code="LIQUIDITY_WARNING",
        message="Insufficient liquidity for large position",
        severity="WARN",
        details={
            "required_liquidity": 100000,
            "available_liquidity": 75000,
            "shortfall": 25000,
        },
    )
    
    print("Custom Violation:")
    print(f"  Code: {violation.code}")
    print(f"  Message: {violation.message}")
    print(f"  Severity: {violation.severity}")
    print()
    
    # Create and dispatch alert
    alert = integration.alert_from_violation(
        violation=violation,
        source="liquidity_gate",
        context={"symbol": "BTC-USD", "side": "BUY"},
    )
    
    results = dispatcher.dispatch(alert)
    print(f"\nDispatch Results: {results}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Risk-Layer Alerting Integration Examples")
    print("=" * 80)
    
    example_risk_gate_integration()
    example_var_gate_integration()
    example_kill_switch_integration()
    example_custom_violation_alert()
    
    print("\n" + "=" * 80)
    print("Integration Examples Complete!")
    print("=" * 80)
    print("\nKey Integration Points:")
    print("  ✓ Risk gate decisions → Alerts")
    print("  ✓ VaR gate warnings → Alerts")
    print("  ✓ Kill switch triggers → Alerts")
    print("  ✓ Custom violations → Alerts")
    print()
