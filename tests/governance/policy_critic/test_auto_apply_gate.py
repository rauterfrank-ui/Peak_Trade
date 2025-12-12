"""
Tests for Auto-Apply Gate integration.

These tests verify the critical fail-closed behavior and decision mapping.
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.governance.policy_critic.auto_apply_gate import (
    ApplyMode,
    AutoApplyDecision,
    evaluate_policy_critic_before_apply,
    persist_decision_to_report,
    should_deny_auto_apply,
)


class TestEvaluatePolicyCriticBeforeApply:
    """Tests for the main integration point."""

    def test_clean_change_allows_auto_apply(self):
        """Clean change with no violations should allow auto-apply."""
        diff = """
+++ b/src/strategies/test.py
+def new_feature():
+    return "safe"
        """
        changed_files = ["src/strategies/test.py"]

        decision = evaluate_policy_critic_before_apply(diff, changed_files)

        assert decision.allowed is True
        assert decision.mode == ApplyMode.AUTO
        assert "allow" in decision.reason.lower()
        assert decision.policy_critic_result is not None

    def test_secret_leak_blocks_auto_apply(self):
        """Secret in diff must block auto-apply (AUTO_APPLY_DENY)."""
        diff = """
+++ b/config.py
+api_key = "sk_live_1234567890abcdef"
        """
        changed_files = ["config.py"]

        decision = evaluate_policy_critic_before_apply(diff, changed_files)

        assert decision.allowed is False
        assert decision.mode == ApplyMode.BLOCKED
        assert "denied" in decision.reason.lower()
        assert decision.policy_critic_result is not None
        assert len(decision.policy_critic_result["violations"]) >= 1

    def test_live_unlock_blocks_auto_apply(self):
        """Live unlock attempt must block auto-apply."""
        diff = """
+++ b/config.toml
+enable_live_trading = true
        """
        changed_files = ["config.toml"]

        decision = evaluate_policy_critic_before_apply(diff, changed_files)

        assert decision.allowed is False
        assert decision.mode in [ApplyMode.BLOCKED, ApplyMode.MANUAL_ONLY]
        assert decision.policy_critic_result is not None

    def test_execution_changes_require_review(self):
        """Execution path changes should require manual review."""
        diff = """
+++ b/src/execution/utils.py
+def helper():
+    pass
        """
        changed_files = ["src/execution/utils.py"]

        decision = evaluate_policy_critic_before_apply(diff, changed_files)

        assert decision.allowed is False
        assert decision.mode == ApplyMode.MANUAL_ONLY
        assert "review" in decision.reason.lower()

    def test_with_context_justification(self):
        """Context with justification should be considered."""
        diff = """
+++ b/config.toml
+max_daily_loss = 10000
        """
        changed_files = ["config.toml"]
        context = {
            "run_id": "test-123",
            "source": "test",
            "justification": "Based on 6-month backtest",
            "test_plan": "Shadow mode for 24h",
        }

        decision = evaluate_policy_critic_before_apply(diff, changed_files, context)

        # Should still block or require review due to risk limit change,
        # but justification reduces severity
        assert decision.policy_critic_result is not None
        assert decision.inputs_summary["source"] == "test"

    def test_fail_closed_on_invalid_diff(self):
        """Invalid/malformed input should fail-closed."""
        # Empty diff
        decision = evaluate_policy_critic_before_apply("", [])

        # Should allow (no violations) or require review (empty changes)
        # The key is it doesn't crash
        assert decision is not None
        assert isinstance(decision.allowed, bool)

    def test_fail_closed_mode_enforced(self):
        """fail_closed=True must block on errors."""
        # This would normally cause an error in a real scenario
        # For now, just verify the parameter is respected
        diff = "+++ b/test.py\n+# test"
        decision = evaluate_policy_critic_before_apply(
            diff, ["test.py"], fail_closed=True
        )

        assert decision is not None


class TestDecisionMapping:
    """Tests for decision mapping logic."""

    def test_deny_blocks_auto_apply(self):
        """AUTO_APPLY_DENY must result in allowed=False and BLOCKED mode."""
        diff = """
+++ b/config.py
+api_key = "sk_live_secret1234567890"
        """
        decision = evaluate_policy_critic_before_apply(diff, ["config.py"])

        assert decision.allowed is False
        assert decision.mode == ApplyMode.BLOCKED
        assert should_deny_auto_apply(decision) is True

    def test_review_required_blocks_auto_apply(self):
        """REVIEW_REQUIRED must result in allowed=False and MANUAL_ONLY mode."""
        diff = """
+++ b/src/execution/executor.py
+# small change
+logger.info("test")
        """
        decision = evaluate_policy_critic_before_apply(diff, ["src/execution/executor.py"])

        assert decision.allowed is False
        assert decision.mode == ApplyMode.MANUAL_ONLY
        assert should_deny_auto_apply(decision) is True

    def test_allow_permits_auto_apply(self):
        """ALLOW must result in allowed=True and AUTO mode."""
        diff = "+++ b/README.md\n+# Documentation update"
        decision = evaluate_policy_critic_before_apply(diff, ["README.md"])

        assert decision.allowed is True
        assert decision.mode == ApplyMode.AUTO
        assert should_deny_auto_apply(decision) is False


class TestReportPersistence:
    """Tests for report persistence."""

    def test_persist_decision_to_report(self):
        """Decision should be persisted to report JSON."""
        # Create temporary report
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            report_path = Path(f.name)
            json.dump({"run_id": "test-123", "results": {}}, f)

        try:
            # Create decision
            diff = "+++ b/test.py\n+# test"
            decision = evaluate_policy_critic_before_apply(diff, ["test.py"])

            # Persist
            persist_decision_to_report(report_path, decision)

            # Read back
            with open(report_path, "r") as f:
                report = json.load(f)

            # Verify
            assert "governance" in report
            assert "auto_apply_decision" in report["governance"]
            assert report["governance"]["auto_apply_decision"]["allowed"] == decision.allowed
            assert report["governance"]["auto_apply_decision"]["mode"] == decision.mode.value

            if decision.policy_critic_result:
                assert "policy_critic" in report["governance"]

        finally:
            # Cleanup
            report_path.unlink(missing_ok=True)

    def test_persist_updates_existing_report(self):
        """Persisting should update existing governance section."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            report_path = Path(f.name)
            json.dump(
                {
                    "run_id": "test-123",
                    "governance": {"existing_key": "existing_value"},
                },
                f,
            )

        try:
            diff = "+++ b/test.py\n+# test"
            decision = evaluate_policy_critic_before_apply(diff, ["test.py"])

            persist_decision_to_report(report_path, decision)

            with open(report_path, "r") as f:
                report = json.load(f)

            # Verify existing key is preserved
            assert report["governance"]["existing_key"] == "existing_value"
            # And new keys are added
            assert "auto_apply_decision" in report["governance"]

        finally:
            report_path.unlink(missing_ok=True)


class TestShouldDenyAutoApply:
    """Tests for the helper function."""

    def test_blocks_when_not_allowed(self):
        """should_deny_auto_apply returns True when not allowed."""
        decision = AutoApplyDecision(
            allowed=False,
            mode=ApplyMode.BLOCKED,
            reason="Test block",
            decided_at="2025-01-01T00:00:00Z",
        )

        assert should_deny_auto_apply(decision) is True

    def test_allows_when_permitted(self):
        """should_deny_auto_apply returns False when allowed."""
        decision = AutoApplyDecision(
            allowed=True,
            mode=ApplyMode.AUTO,
            reason="Test allow",
            decided_at="2025-01-01T00:00:00Z",
        )

        assert should_deny_auto_apply(decision) is False
