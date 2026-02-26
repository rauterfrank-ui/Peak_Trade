"""
Deterministic policy rules for the Policy Critic.

Each rule inspects diffs and changed files to detect policy violations.
All rules are evidence-based and must provide concrete references.
"""

import re
from typing import List, Optional

from .models import Evidence, Severity, Violation


class PolicyRule:
    """Base class for policy rules."""

    rule_id: str = "UNKNOWN"
    severity: Severity = Severity.INFO
    description: str = ""

    def check(
        self, diff: str, changed_files: List[str], context: Optional[dict] = None
    ) -> List[Violation]:
        """Check for violations. Returns list of violations (empty if none)."""
        raise NotImplementedError


class NoSecretsRule(PolicyRule):
    """Block commits containing secrets or sensitive tokens."""

    rule_id = "NO_SECRETS"
    severity = Severity.BLOCK
    description = "Detects secrets, API keys, and private keys in diffs"

    SECRET_PATTERNS = [
        (r"BEGIN.*PRIVATE KEY", "Private key detected"),
        (
            r"[Aa][Pp][Ii][_-]?[Kk][Ee][Yy]\s*[=:]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]",
            "API key pattern detected",
        ),
        (r"secret[_-]?key[\s:=]+['\"]?[a-zA-Z0-9]{16,}", "Secret key pattern detected"),
        (r"password[\s:=]+['\"]?[^\s'\"]{8,}", "Password pattern detected"),
        (r"token[\s:=]+['\"]?[a-zA-Z0-9_\-]{20,}", "Token pattern detected"),
        (r"aws_access_key_id", "AWS access key ID detected"),
        (r"aws_secret_access_key", "AWS secret access key detected"),
    ]

    def check(
        self, diff: str, changed_files: List[str], context: Optional[dict] = None
    ) -> List[Violation]:
        violations = []

        for pattern, message in self.SECRET_PATTERNS:
            for match in re.finditer(pattern, diff, re.IGNORECASE):
                # Skip false positives: env var references (e.g. ${VAR}, $VAR, ${VAR:?msg})
                matched_text = match.group(0)
                if re.search(r"[\$]\{?[A-Za-z_][A-Za-z0-9_]*", matched_text):
                    continue

                # Skip docs: runbooks/specs often show env var examples or detection patterns
                file_path = self._extract_file_from_diff_position(diff, match.start())
                if file_path and file_path.startswith("docs/"):
                    continue

                # Extract context around match
                start = max(0, match.start() - 50)
                end = min(len(diff), match.end() + 50)
                snippet = diff[start:end].replace("\n", " ")

                # Try to extract file from diff context
                file_path = self._extract_file_from_diff_position(diff, match.start())

                evidence = Evidence(
                    file_path=file_path or "unknown",
                    snippet=snippet[:100] + "..." if len(snippet) > 100 else snippet,
                    pattern=pattern,
                )

                violations.append(
                    Violation(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"{message}. Secrets must never be committed.",
                        evidence=[evidence],
                        suggested_fix="Remove the secret and use environment variables or secret management.",
                    )
                )

        return violations

    @staticmethod
    def _extract_file_from_diff_position(diff: str, position: int) -> Optional[str]:
        """Extract filename from diff for a given position."""
        # Look backwards for the most recent +++ line
        before = diff[:position]
        match = re.findall(r"\+\+\+ b/(.+?)$", before, re.MULTILINE)
        if match:
            return match[-1]
        return None


class NoLiveUnlockRule(PolicyRule):
    """Block attempts to enable live trading or remove safety locks."""

    rule_id = "NO_LIVE_UNLOCK"
    severity = Severity.BLOCK
    description = "Detects attempts to enable live trading or remove safety gates"

    UNLOCK_PATTERNS = [
        (r"enable_live_trading\s*[=:]\s*[Tt]rue", "Attempt to enable live trading"),
        (r"live_mode_armed\s*[=:]\s*[Tt]rue", "Attempt to arm live mode"),
        (r"confirm_token\s*[=:]\s*['\"]bypass", "Attempt to bypass confirm token"),
        (r"LIVE_MODE\s*=\s*[Tt]rue", "Attempt to set LIVE_MODE to true"),
        (r"\.unlock\(\)", "Attempt to unlock a safety gate"),
        (r"Lock\.remove", "Attempt to remove a lock"),
        (r"disable.*safety.*check", "Attempt to disable safety checks"),
    ]

    def check(
        self, diff: str, changed_files: List[str], context: Optional[dict] = None
    ) -> List[Violation]:
        violations = []

        for pattern, message in self.UNLOCK_PATTERNS:
            for match in re.finditer(pattern, diff, re.IGNORECASE):
                file_path = NoSecretsRule._extract_file_from_diff_position(diff, match.start())

                evidence = Evidence(
                    file_path=file_path or "unknown",
                    snippet=match.group(0),
                    pattern=pattern,
                )

                violations.append(
                    Violation(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"{message}. Live unlocks require explicit governance approval.",
                        evidence=[evidence],
                        suggested_fix="Remove this change. Live mode changes require manual review and owner approval.",
                    )
                )

        return violations


class ExecutionEndpointTouchRule(PolicyRule):
    """Warn or block changes to execution-critical paths."""

    rule_id = "EXECUTION_ENDPOINT_TOUCH"
    description = "Detects changes to execution-critical code paths"

    CRITICAL_PATHS = [
        "src/execution/",
        "src/exchange/",
        "src/live/",
    ]

    ORDER_PATTERNS = [
        r"def\s+place_order",
        r"def\s+submit_order",
        r"\.place_order\(",
        r"\.submit_order\(",
        r"class\s+\w*Order\w*Executor",
    ]

    def check(
        self, diff: str, changed_files: List[str], context: Optional[dict] = None
    ) -> List[Violation]:
        violations = []

        # Check if any changed files are in critical paths
        critical_files = [
            f for f in changed_files if any(f.startswith(path) for path in self.CRITICAL_PATHS)
        ]

        if not critical_files:
            return violations

        # Check for order-related changes (BLOCK)
        for pattern in self.ORDER_PATTERNS:
            if re.search(pattern, diff, re.IGNORECASE):
                for cfile in critical_files:
                    violations.append(
                        Violation(
                            rule_id=self.rule_id,
                            severity=Severity.BLOCK,
                            message=f"Order execution code modified in {cfile}. This requires manual review.",
                            evidence=[Evidence(file_path=cfile, pattern=pattern)],
                            suggested_fix="Order execution changes require peer review and extensive testing.",
                        )
                    )
                break  # Only report once

        # If no order patterns but still critical path: WARN
        if not violations:
            for cfile in critical_files:
                violations.append(
                    Violation(
                        rule_id=self.rule_id,
                        severity=Severity.WARN,
                        message=f"Execution-critical file modified: {cfile}. Review carefully.",
                        evidence=[Evidence(file_path=cfile)],
                        suggested_fix="Ensure changes are well-tested and reviewed.",
                    )
                )

        return violations


class RiskLimitRaiseRule(PolicyRule):
    """Warn when risk limits are raised without justification."""

    rule_id = "RISK_LIMIT_RAISE_WITHOUT_JUSTIFICATION"
    severity = Severity.WARN
    description = "Detects risk limit increases without documented justification"

    LIMIT_PATTERNS = [
        r"max_.*_limit\s*[=:]\s*(\d+\.?\d*)",
        r"max_daily_loss\s*[=:]\s*(\d+\.?\d*)",
        r"max_position_size\s*[=:]\s*(\d+\.?\d*)",
        r"max_leverage\s*[=:]\s*(\d+\.?\d*)",
        r"max_drawdown\s*[=:]\s*(\d+\.?\d*)",
    ]

    def check(
        self, diff: str, changed_files: List[str], context: Optional[dict] = None
    ) -> List[Violation]:
        violations = []
        context_dict = context or {}

        # Check if justification is provided
        has_justification = bool(context_dict.get("justification"))

        # Look for limit increases in diff
        for pattern in self.LIMIT_PATTERNS:
            matches = list(re.finditer(pattern, diff, re.IGNORECASE))
            if matches:
                for match in matches:
                    file_path = NoSecretsRule._extract_file_from_diff_position(diff, match.start())

                    # Skip excluded paths: docs/, tmp/, tests/ (tests instantiate configs, not production limits)
                    if file_path and any(
                        file_path.startswith(excluded)
                        for excluded in ["docs/", "tmp/", "tests/fixtures/", "tests/"]
                    ):
                        continue

                    severity = Severity.WARN if has_justification else Severity.BLOCK
                    message = f"Risk limit change detected in {file_path or 'config'}."

                    if not has_justification:
                        message += " No justification provided."

                    violations.append(
                        Violation(
                            rule_id=self.rule_id,
                            severity=severity,
                            message=message,
                            evidence=[
                                Evidence(
                                    file_path=file_path or "unknown",
                                    snippet=match.group(0),
                                    pattern=pattern,
                                )
                            ],
                            suggested_fix="Provide justification via --context-json with 'justification' field explaining why limits are changed.",
                        )
                    )

        return violations


class MissingTestPlanRule(PolicyRule):
    """Warn when significant changes lack a test plan."""

    rule_id = "MISSING_TEST_PLAN"
    severity = Severity.WARN
    description = "Detects significant changes without documented test plans"

    CRITICAL_PATHS = [
        "src/execution/",
        "src/exchange/",
        "src/live/",
        "src/risk/",
        "src/strategies/",
    ]

    # G3.6: Stricter thresholds for highly critical paths
    HIGH_CRITICAL_PATHS = [
        "src/execution/",
        "src/exchange/",
        "src/live/",
        "config/live",
        "config/production",
    ]

    MIN_LINES_CHANGED = 50  # Threshold for "significant change"
    MIN_LINES_HIGH_CRITICAL = 10  # G3.6: Lower threshold for highly critical paths

    def check(
        self, diff: str, changed_files: List[str], context: Optional[dict] = None
    ) -> List[Violation]:
        violations = []
        context_dict = context or {}

        # Check if test plan is provided
        has_test_plan = bool(context_dict.get("test_plan"))

        if has_test_plan:
            return violations  # No violation if test plan exists

        # Check if changes are in critical paths
        critical_files = [
            f for f in changed_files if any(f.startswith(path) for path in self.CRITICAL_PATHS)
        ]

        if not critical_files:
            return violations

        # G3.6: Check for highly critical paths (lower threshold)
        high_critical_files = [
            f
            for f in critical_files
            if any(f.startswith(path) for path in self.HIGH_CRITICAL_PATHS)
        ]

        # Count changed lines (rough heuristic)
        added_lines = len(re.findall(r"^\+[^+]", diff, re.MULTILINE))
        removed_lines = len(re.findall(r"^-[^-]", diff, re.MULTILINE))
        total_changed = added_lines + removed_lines

        # G3.6: Use lower threshold for highly critical paths
        threshold = self.MIN_LINES_HIGH_CRITICAL if high_critical_files else self.MIN_LINES_CHANGED

        if total_changed >= threshold:
            path_type = "highly critical" if high_critical_files else "critical"
            violations.append(
                Violation(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=f"Changes ({total_changed} lines) in {path_type} paths without test plan.",
                    evidence=[
                        Evidence(file_path=f) for f in critical_files[:3]
                    ],  # Limit to first 3
                    suggested_fix="Provide test plan via --context-json with 'test_plan' field describing testing approach.",
                )
            )

        return violations


# Registry of all rules
ALL_RULES: List[PolicyRule] = [
    NoSecretsRule(),
    NoLiveUnlockRule(),
    ExecutionEndpointTouchRule(),
    RiskLimitRaiseRule(),
    MissingTestPlanRule(),
]
