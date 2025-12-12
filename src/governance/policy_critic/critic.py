"""
Policy Critic - Main orchestration logic.

The Policy Critic is a read-only governance layer that reviews changes
against security, risk, and operational policies.
"""

from typing import List, Optional

from .models import (
    PolicyCriticInput,
    PolicyCriticResult,
    RecommendedAction,
    ReviewContext,
    Severity,
    Violation,
)
from .rules import ALL_RULES


class PolicyCritic:
    """Main Policy Critic orchestrator."""

    def __init__(self, rules: Optional[List] = None):
        """Initialize with rules (defaults to ALL_RULES)."""
        self.rules = rules if rules is not None else ALL_RULES

    def review(self, input_data: PolicyCriticInput) -> PolicyCriticResult:
        """
        Review changes against policy rules.

        Args:
            input_data: Input containing diff, changed files, and optional context

        Returns:
            PolicyCriticResult with violations, recommendations, and summary
        """
        all_violations: List[Violation] = []

        # Convert context to dict for rules
        context_dict = None
        if input_data.context:
            context_dict = {
                "justification": input_data.context.justification,
                "test_plan": input_data.context.test_plan,
                "author": input_data.context.author,
                "related_issue": input_data.context.related_issue,
            }

        # Run all rules
        for rule in self.rules:
            violations = rule.check(
                diff=input_data.diff,
                changed_files=input_data.changed_files,
                context=context_dict,
            )
            all_violations.extend(violations)

        # Determine max severity
        max_severity = Severity.INFO
        if all_violations:
            severity_order = {Severity.INFO: 0, Severity.WARN: 1, Severity.BLOCK: 2}
            max_severity = max(
                (v.severity for v in all_violations),
                key=lambda s: severity_order[s]
            )

        # Determine recommended action
        recommended_action = self._determine_action(max_severity, all_violations)

        # Generate test plan suggestions
        minimum_test_plan = self._generate_test_plan(input_data.changed_files, all_violations)

        # Generate operator questions
        operator_questions = self._generate_operator_questions(all_violations, input_data.context)

        # Generate summary
        summary = self._generate_summary(max_severity, all_violations, recommended_action)

        # Build result
        result = PolicyCriticResult(
            max_severity=max_severity,
            recommended_action=recommended_action,
            violations=all_violations,
            minimum_test_plan=minimum_test_plan,
            operator_questions=operator_questions,
            summary=summary,
        )

        # G3: Attach policy pack metadata if present
        if hasattr(self, '_policy_pack'):
            pack = self._policy_pack
            result.policy_pack_id = pack.pack_id
            result.policy_pack_version = pack.version
            result.effective_ruleset_hash = pack.compute_hash()

        return result

    def _determine_action(self, max_severity: Severity, violations: List[Violation]) -> RecommendedAction:
        """Determine recommended action based on severity and violations."""
        if max_severity == Severity.BLOCK:
            return RecommendedAction.AUTO_APPLY_DENY

        if max_severity == Severity.WARN:
            # Check if multiple warnings or critical path warnings
            if len(violations) >= 3:
                return RecommendedAction.REVIEW_REQUIRED

            # Check for execution-critical warnings
            execution_warnings = [v for v in violations if v.rule_id == "EXECUTION_ENDPOINT_TOUCH"]
            if execution_warnings:
                return RecommendedAction.REVIEW_REQUIRED

            return RecommendedAction.REVIEW_REQUIRED  # Conservative: all warnings need review

        return RecommendedAction.ALLOW

    def _generate_test_plan(self, changed_files: List[str], violations: List[Violation]) -> List[str]:
        """Generate minimum test plan suggestions."""
        test_plan = []

        # Check for execution path changes
        execution_files = [f for f in changed_files if "execution" in f or "exchange" in f]
        if execution_files:
            test_plan.append("Run integration tests for execution pipeline")
            test_plan.append("Verify order routing in paper/shadow mode")

        # Check for strategy changes
        strategy_files = [f for f in changed_files if "strategies" in f]
        if strategy_files:
            test_plan.append("Run backtest smoke tests for affected strategies")

        # Check for risk-related changes
        risk_violations = [v for v in violations if "RISK" in v.rule_id]
        if risk_violations:
            test_plan.append("Verify risk limit enforcement with edge cases")
            test_plan.append("Document risk limit changes in changelog")

        return test_plan

    def _generate_operator_questions(
        self, violations: List[Violation], context: Optional[ReviewContext]
    ) -> List[str]:
        """Generate questions for the operator/reviewer."""
        questions = []

        # Check for missing justification
        if context is None or not context.justification:
            risk_violations = [v for v in violations if "RISK_LIMIT" in v.rule_id]
            if risk_violations:
                questions.append("Why are risk limits being changed? What data/metrics support this?")

        # Check for execution changes
        execution_violations = [v for v in violations if "EXECUTION" in v.rule_id]
        if execution_violations:
            questions.append("Have these execution changes been tested in shadow mode?")
            questions.append("Is there a rollback plan if issues arise?")

        # Check for missing test plan
        test_plan_violations = [v for v in violations if "TEST_PLAN" in v.rule_id]
        if test_plan_violations:
            questions.append("What testing approach will be used to verify these changes?")
            questions.append("Are there any edge cases that need special attention?")

        return questions

    def _generate_summary(
        self, max_severity: Severity, violations: List[Violation], action: RecommendedAction
    ) -> str:
        """Generate human-readable summary."""
        if not violations:
            return "No policy violations detected. Changes appear safe."

        violation_summary = []
        by_severity = {
            Severity.BLOCK: [v for v in violations if v.severity == Severity.BLOCK],
            Severity.WARN: [v for v in violations if v.severity == Severity.WARN],
            Severity.INFO: [v for v in violations if v.severity == Severity.INFO],
        }

        if by_severity[Severity.BLOCK]:
            violation_summary.append(f"{len(by_severity[Severity.BLOCK])} blocking violation(s)")
        if by_severity[Severity.WARN]:
            violation_summary.append(f"{len(by_severity[Severity.WARN])} warning(s)")
        if by_severity[Severity.INFO]:
            violation_summary.append(f"{len(by_severity[Severity.INFO])} info item(s)")

        summary = f"Policy review: {', '.join(violation_summary)}. "

        if action == RecommendedAction.AUTO_APPLY_DENY:
            summary += "Auto-apply DENIED. Manual review required."
        elif action == RecommendedAction.REVIEW_REQUIRED:
            summary += "Review required before applying."
        else:
            summary += "Changes may proceed with caution."

        return summary
