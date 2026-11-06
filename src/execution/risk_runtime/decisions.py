"""
Risk Decisions & Directives (WP0B)

Extended decision types for runtime risk evaluation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime

from src.execution.contracts import Order


# ============================================================================
# Risk Decision (Extended)
# ============================================================================


class RiskDecision(str, Enum):
    """
    Extended risk decision types.

    Design:
    - ALLOW: Proceed with order as-is
    - REJECT: Block order (e.g., limit exceeded)
    - MODIFY: Allow order with modifications (e.g., reduce quantity)
    - HALT: Emergency halt all trading (e.g., kill switch)
    """

    ALLOW = "ALLOW"
    REJECT = "REJECT"
    MODIFY = "MODIFY"
    HALT = "HALT"

    def is_allowed(self) -> bool:
        """Check if decision allows trading"""
        return self in {RiskDecision.ALLOW, RiskDecision.MODIFY}

    def is_blocked(self) -> bool:
        """Check if decision blocks trading"""
        return self in {RiskDecision.REJECT, RiskDecision.HALT}


# ============================================================================
# Risk Directive
# ============================================================================


@dataclass
class RiskDirective:
    """
    Risk evaluation directive (result of policy evaluation).

    Design:
    - decision: ALLOW/REJECT/MODIFY/HALT
    - reason: Human-readable explanation
    - modified_order: Optional modified order (only for MODIFY)
    - tags: Optional metadata (policy name, limits, etc.)
    - timestamp: When directive was created
    """

    decision: RiskDecision
    reason: str
    modified_order: Optional[Order] = None
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for logging/debugging"""
        d = {
            "decision": self.decision.value,
            "reason": self.reason,
            "tags": self.tags,
            "timestamp": self.timestamp.isoformat(),
        }

        if self.modified_order:
            d["modified_order_id"] = self.modified_order.client_order_id
            d["modified_quantity"] = str(self.modified_order.quantity)

        return d

    def __repr__(self) -> str:
        """Deterministic repr"""
        return f"RiskDirective(decision={self.decision.value}, reason={self.reason!r})"


# ============================================================================
# Helper Functions
# ============================================================================


def allow_directive(reason: str = "All checks passed", **tags) -> RiskDirective:
    """Create ALLOW directive"""
    return RiskDirective(
        decision=RiskDecision.ALLOW,
        reason=reason,
        tags=tags,
    )


def reject_directive(reason: str, **tags) -> RiskDirective:
    """Create REJECT directive"""
    return RiskDirective(
        decision=RiskDecision.REJECT,
        reason=reason,
        tags=tags,
    )


def modify_directive(modified_order: Order, reason: str, **tags) -> RiskDirective:
    """Create MODIFY directive"""
    return RiskDirective(
        decision=RiskDecision.MODIFY,
        reason=reason,
        modified_order=modified_order,
        tags=tags,
    )


def halt_directive(reason: str = "Emergency halt", **tags) -> RiskDirective:
    """Create HALT directive"""
    return RiskDirective(
        decision=RiskDecision.HALT,
        reason=reason,
        tags=tags,
    )
