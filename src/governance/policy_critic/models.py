"""
Data models for the Policy Critic.

These models define the input and output contracts for policy review.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Severity(str, Enum):
    """Severity levels for policy violations."""

    INFO = "INFO"
    WARN = "WARN"
    BLOCK = "BLOCK"


class RecommendedAction(str, Enum):
    """Recommended actions for the change under review."""

    ALLOW = "ALLOW"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    AUTO_APPLY_DENY = "AUTO_APPLY_DENY"


@dataclass
class Evidence:
    """Evidence for a policy violation."""

    file_path: str
    line_range: Optional[str] = None  # e.g., "42-45" or "123"
    snippet: Optional[str] = None
    pattern: Optional[str] = None  # The pattern that matched


@dataclass
class Violation:
    """A single policy violation."""

    rule_id: str
    severity: Severity
    message: str
    evidence: List[Evidence] = field(default_factory=list)
    suggested_fix: Optional[str] = None


@dataclass
class ReviewContext:
    """Optional context for the review."""

    justification: Optional[str] = None
    test_plan: Optional[str] = None
    author: Optional[str] = None
    related_issue: Optional[str] = None


@dataclass
class PolicyCriticInput:
    """Input for the policy critic."""

    diff: str
    changed_files: List[str]
    context: Optional[ReviewContext] = None


@dataclass
class PolicyCriticResult:
    """Result of a policy review."""

    max_severity: Severity
    recommended_action: RecommendedAction
    violations: List[Violation] = field(default_factory=list)
    minimum_test_plan: List[str] = field(default_factory=list)
    operator_questions: List[str] = field(default_factory=list)
    summary: str = ""
    # G3: Policy Pack metadata
    policy_pack_id: Optional[str] = None
    policy_pack_version: Optional[str] = None
    effective_ruleset_hash: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "max_severity": self.max_severity.value,
            "recommended_action": self.recommended_action.value,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "severity": v.severity.value,
                    "message": v.message,
                    "evidence": [
                        {
                            "file_path": e.file_path,
                            "line_range": e.line_range,
                            "snippet": e.snippet,
                            "pattern": e.pattern,
                        }
                        for e in v.evidence
                    ],
                    "suggested_fix": v.suggested_fix,
                }
                for v in self.violations
            ],
            "minimum_test_plan": self.minimum_test_plan,
            "operator_questions": self.operator_questions,
            "summary": self.summary,
        }

        # Include pack metadata if present
        if self.policy_pack_id:
            result["policy_pack_id"] = self.policy_pack_id
        if self.policy_pack_version:
            result["policy_pack_version"] = self.policy_pack_version
        if self.effective_ruleset_hash:
            result["effective_ruleset_hash"] = self.effective_ruleset_hash

        return result

    def to_canonical_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary with stable ordering for deterministic hashing.

        Violations are sorted by rule_id then message; evidence by file_path then line_range.
        Use with json.dumps(..., sort_keys=True) for identical output for same logical result.
        """
        result = self.to_dict()
        # Sort violations by rule_id, then message (stable order)
        violations = result.get("violations", [])
        result["violations"] = sorted(
            violations,
            key=lambda v: (v.get("rule_id", ""), v.get("message", "")),
        )
        # Sort evidence within each violation by file_path, then line_range
        for v in result["violations"]:
            ev_list = v.get("evidence", [])
            v["evidence"] = sorted(
                ev_list,
                key=lambda e: (e.get("file_path", ""), str(e.get("line_range") or "")),
            )
        # minimum_test_plan and operator_questions already lists; sort for determinism
        result["minimum_test_plan"] = sorted(result.get("minimum_test_plan", []))
        result["operator_questions"] = sorted(result.get("operator_questions", []))
        return result

    @property
    def exit_code(self) -> int:
        """Exit code for CLI (0=ok, 2=block)."""
        if self.max_severity == Severity.BLOCK:
            return 2
        return 0
