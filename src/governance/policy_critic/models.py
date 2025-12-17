"""
Data models for the Policy Critic.

These models define the input and output contracts for policy review.
"""

from dataclasses import dataclass, field
from enum import Enum


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
    line_range: str | None = None  # e.g., "42-45" or "123"
    snippet: str | None = None
    pattern: str | None = None  # The pattern that matched


@dataclass
class Violation:
    """A single policy violation."""
    rule_id: str
    severity: Severity
    message: str
    evidence: list[Evidence] = field(default_factory=list)
    suggested_fix: str | None = None


@dataclass
class ReviewContext:
    """Optional context for the review."""
    justification: str | None = None
    test_plan: str | None = None
    author: str | None = None
    related_issue: str | None = None


@dataclass
class PolicyCriticInput:
    """Input for the policy critic."""
    diff: str
    changed_files: list[str]
    context: ReviewContext | None = None


@dataclass
class PolicyCriticResult:
    """Result of a policy review."""
    max_severity: Severity
    recommended_action: RecommendedAction
    violations: list[Violation] = field(default_factory=list)
    minimum_test_plan: list[str] = field(default_factory=list)
    operator_questions: list[str] = field(default_factory=list)
    summary: str = ""
    # G3: Policy Pack metadata
    policy_pack_id: str | None = None
    policy_pack_version: str | None = None
    effective_ruleset_hash: str | None = None

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

    @property
    def exit_code(self) -> int:
        """Exit code for CLI (0=ok, 2=block)."""
        if self.max_severity == Severity.BLOCK:
            return 2
        return 0
