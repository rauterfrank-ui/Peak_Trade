"""
Risk Layer Data Models
=======================

Core data structures for risk decisions and violations.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class Violation:
    """
    Represents a single risk violation.

    Attributes:
        code: Unique violation code (e.g., "MISSING_SYMBOL", "POSITION_SIZE_EXCEEDED")
        message: Human-readable description
        severity: Severity level (INFO, WARN, CRITICAL)
        details: Additional context as key-value pairs
    """

    code: str
    message: str
    severity: Literal["INFO", "WARN", "CRITICAL"]
    details: dict = field(default_factory=dict)


@dataclass(frozen=True)
class RiskDecision:
    """
    Result of a risk evaluation.

    Attributes:
        allowed: Whether the order is allowed to proceed
        severity: Overall severity (OK, WARN, BLOCK)
        reason: Primary reason for the decision
        violations: List of violations found during evaluation
    """

    allowed: bool
    severity: Literal["OK", "WARN", "BLOCK"]
    reason: str
    violations: list[Violation] = field(default_factory=list)


@dataclass(frozen=True)
class RiskResult:
    """
    Complete result of risk gate evaluation including audit trail.

    Attributes:
        decision: The risk decision
        audit_event: Dict containing the full audit event to be logged
    """

    decision: RiskDecision
    audit_event: dict
