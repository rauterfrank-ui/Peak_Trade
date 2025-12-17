"""
Tests for Policy Critic orchestration.

Tests the main critic logic and integration of rules.
"""


from src.governance.policy_critic.critic import PolicyCritic
from src.governance.policy_critic.models import (
    PolicyCriticInput,
    RecommendedAction,
    ReviewContext,
    Severity,
)


class TestPolicyCriticOrchestration:
    """Tests for main critic orchestration."""

    def test_clean_diff_passes(self):
        """Clean diff with no violations should pass."""
        critic = PolicyCritic()
        input_data = PolicyCriticInput(
            diff="""
+++ b/src/strategies/test.py
+def new_feature():
+    return "safe"
            """,
            changed_files=["src/strategies/test.py"],
        )

        result = critic.review(input_data)

        assert result.max_severity == Severity.INFO
        assert result.recommended_action == RecommendedAction.ALLOW
        assert len(result.violations) == 0
        assert result.exit_code == 0

    def test_secret_detection_blocks(self):
        """Secrets in diff should block."""
        critic = PolicyCritic()
        input_data = PolicyCriticInput(
            diff="""
+++ b/config.py
+api_key = "sk_live_1234567890abcdef"
            """,
            changed_files=["config.py"],
        )

        result = critic.review(input_data)

        assert result.max_severity == Severity.BLOCK
        assert result.recommended_action == RecommendedAction.AUTO_APPLY_DENY
        assert len(result.violations) >= 1
        assert result.violations[0].rule_id == "NO_SECRETS"
        assert result.exit_code == 2

    def test_live_unlock_blocks(self):
        """Live unlock attempts should block."""
        critic = PolicyCritic()
        input_data = PolicyCriticInput(
            diff="""
+++ b/config.toml
+enable_live_trading = true
            """,
            changed_files=["config.toml"],
        )

        result = critic.review(input_data)

        assert result.max_severity == Severity.BLOCK
        assert result.recommended_action == RecommendedAction.AUTO_APPLY_DENY
        assert any(v.rule_id == "NO_LIVE_UNLOCK" for v in result.violations)
        assert result.exit_code == 2

    def test_execution_changes_require_review(self):
        """Execution path changes should require review."""
        critic = PolicyCritic()
        input_data = PolicyCriticInput(
            diff="""
+++ b/src/execution/utils.py
+def helper():
+    pass
            """,
            changed_files=["src/execution/utils.py"],
        )

        result = critic.review(input_data)

        assert result.max_severity == Severity.WARN
        assert result.recommended_action == RecommendedAction.REVIEW_REQUIRED
        assert any(v.rule_id == "EXECUTION_ENDPOINT_TOUCH" for v in result.violations)

    def test_order_execution_blocks(self):
        """Order execution code changes should block."""
        critic = PolicyCritic()
        input_data = PolicyCriticInput(
            diff="""
+++ b/src/execution/executor.py
+def place_order(symbol, qty):
+    exchange.submit_order(symbol, qty)
            """,
            changed_files=["src/execution/executor.py"],
        )

        result = critic.review(input_data)

        assert result.max_severity == Severity.BLOCK
        assert result.recommended_action == RecommendedAction.AUTO_APPLY_DENY

    def test_risk_limit_without_justification_blocks(self):
        """Risk limit changes without justification should block."""
        critic = PolicyCritic()
        input_data = PolicyCriticInput(
            diff="""
+++ b/config.toml
+max_daily_loss = 10000
            """,
            changed_files=["config.toml"],
        )

        result = critic.review(input_data)

        assert result.max_severity == Severity.BLOCK
        assert result.recommended_action == RecommendedAction.AUTO_APPLY_DENY
        assert any(v.rule_id == "RISK_LIMIT_RAISE_WITHOUT_JUSTIFICATION" for v in result.violations)

    def test_risk_limit_with_justification_warns(self):
        """Risk limit changes with justification should only warn."""
        critic = PolicyCritic()
        input_data = PolicyCriticInput(
            diff="""
+++ b/config.toml
+max_daily_loss = 10000
            """,
            changed_files=["config.toml"],
            context=ReviewContext(justification="Based on 6 months backtest data"),
        )

        result = critic.review(input_data)

        assert result.max_severity == Severity.WARN
        assert result.recommended_action == RecommendedAction.REVIEW_REQUIRED

    def test_large_critical_changes_without_test_plan_warns(self):
        """Large critical changes without test plan should warn."""
        critic = PolicyCritic()
        diff = "+++ b/src/execution/core.py\n"
        diff += "\n".join([f"+# Line {i}" for i in range(60)])

        input_data = PolicyCriticInput(
            diff=diff,
            changed_files=["src/execution/core.py"],
        )

        result = critic.review(input_data)

        assert result.max_severity == Severity.WARN
        assert result.recommended_action == RecommendedAction.REVIEW_REQUIRED
        assert any(v.rule_id == "MISSING_TEST_PLAN" for v in result.violations)

    def test_test_plan_provided_reduces_violations(self):
        """Providing test plan should reduce violations."""
        critic = PolicyCritic()
        diff = "+++ b/src/execution/core.py\n"
        diff += "\n".join([f"+# Line {i}" for i in range(60)])

        input_data = PolicyCriticInput(
            diff=diff,
            changed_files=["src/execution/core.py"],
            context=ReviewContext(test_plan="Integration tests + shadow mode"),
        )

        result = critic.review(input_data)

        # Should still warn due to execution path, but no TEST_PLAN violation
        assert not any(v.rule_id == "MISSING_TEST_PLAN" for v in result.violations)

    def test_multiple_violations_aggregated(self):
        """Multiple violations should be properly aggregated."""
        critic = PolicyCritic()
        input_data = PolicyCriticInput(
            diff="""
+++ b/config.toml
+enable_live_trading = true
+max_daily_loss = 99999
+++ b/secrets.py
+api_key = "sk_live_secret123456789"
            """,
            changed_files=["config.toml", "secrets.py"],
        )

        result = critic.review(input_data)

        assert result.max_severity == Severity.BLOCK
        assert len(result.violations) >= 2  # At least NO_LIVE_UNLOCK + one more
        assert result.recommended_action == RecommendedAction.AUTO_APPLY_DENY

    def test_generates_test_plan_suggestions(self):
        """Should generate test plan suggestions for execution changes."""
        critic = PolicyCritic()
        input_data = PolicyCriticInput(
            diff="""
+++ b/src/execution/executor.py
+def update_logic():
+    pass
            """,
            changed_files=["src/execution/executor.py"],
        )

        result = critic.review(input_data)

        assert len(result.minimum_test_plan) > 0
        assert any("execution" in item.lower() for item in result.minimum_test_plan)

    def test_generates_operator_questions(self):
        """Should generate operator questions for risky changes."""
        critic = PolicyCritic()
        input_data = PolicyCriticInput(
            diff="""
+++ b/src/execution/executor.py
+def place_order():
+    pass
            """,
            changed_files=["src/execution/executor.py"],
        )

        result = critic.review(input_data)

        assert len(result.operator_questions) > 0
        assert any("shadow" in q.lower() or "rollback" in q.lower() for q in result.operator_questions)

    def test_summary_reflects_severity(self):
        """Summary should reflect the severity level."""
        critic = PolicyCritic()

        # Clean case
        clean_input = PolicyCriticInput(
            diff="+++ b/README.md\n+# Update",
            changed_files=["README.md"],
        )
        clean_result = critic.review(clean_input)
        assert "safe" in clean_result.summary.lower()

        # Block case
        block_input = PolicyCriticInput(
            diff="+++ b/config.py\n+api_key = 'sk_live_secret1234567890'",
            changed_files=["config.py"],
        )
        block_result = critic.review(block_input)
        assert "denied" in block_result.summary.lower() or "block" in block_result.summary.lower()


class TestPolicyCriticContext:
    """Tests for context handling."""

    def test_context_with_all_fields(self):
        """Should properly handle full context."""
        critic = PolicyCritic()
        context = ReviewContext(
            justification="Performance optimization",
            test_plan="Run benchmarks + integration tests",
            author="test_user",
            related_issue="ISSUE-123",
        )

        input_data = PolicyCriticInput(
            diff="+++ b/src/execution/utils.py\n+# optimization",
            changed_files=["src/execution/utils.py"],
            context=context,
        )

        result = critic.review(input_data)
        # Should still warn about execution path, but context is considered
        assert result.max_severity == Severity.WARN

    def test_empty_context_handled(self):
        """Empty context should not cause errors."""
        critic = PolicyCritic()
        input_data = PolicyCriticInput(
            diff="+++ b/test.py\n+# test",
            changed_files=["test.py"],
            context=None,
        )

        result = critic.review(input_data)
        assert result is not None
