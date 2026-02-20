"""
Tests for Policy Critic rules.

All tests are deterministic and verify rule behavior.
"""

import pytest

from src.governance.policy_critic.models import Severity
from src.governance.policy_critic.rules import (
    ExecutionEndpointTouchRule,
    MissingTestPlanRule,
    NoLiveUnlockRule,
    NoSecretsRule,
    RiskLimitRaiseRule,
)


class TestNoSecretsRule:
    """Tests for secret detection rule."""

    def test_detects_private_key(self):
        rule = NoSecretsRule()
        diff = """
+++ b/config/secrets.py
+BEGIN RSA PRIVATE KEY
+MIIEpAIBAAKCAQEA...
        """
        violations = rule.check(diff, ["config/secrets.py"])

        assert len(violations) == 1
        assert violations[0].rule_id == "NO_SECRETS"
        assert violations[0].severity == Severity.BLOCK
        assert "Private key" in violations[0].message

    def test_detects_api_key(self):
        rule = NoSecretsRule()
        diff = """
+++ b/config.py
+API_KEY = "sk_live_abcd1234567890efgh"
        """
        violations = rule.check(diff, ["config.py"])

        assert len(violations) == 1
        assert violations[0].rule_id == "NO_SECRETS"
        assert violations[0].severity == Severity.BLOCK

    def test_detects_aws_credentials(self):
        rule = NoSecretsRule()
        diff = """
+aws_access_key_id = AKIAIOSFODNN7EXAMPLE
+aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
        """
        violations = rule.check(diff, ["config.yml"])

        assert len(violations) >= 2
        assert all(v.severity == Severity.BLOCK for v in violations)

    def test_no_false_positive_on_safe_content(self):
        rule = NoSecretsRule()
        diff = """
+++ b/README.md
+# Authentication
+Use environment variables for API keys, never commit them.
        """
        violations = rule.check(diff, ["README.md"])

        assert len(violations) == 0


class TestNoLiveUnlockRule:
    """Tests for live unlock detection rule."""

    def test_detects_enable_live_trading(self):
        rule = NoLiveUnlockRule()
        diff = """
+++ b/config.toml
-enable_live_trading = false
+enable_live_trading = true
        """
        violations = rule.check(diff, ["config.toml"])

        assert len(violations) == 1
        assert violations[0].rule_id == "NO_LIVE_UNLOCK"
        assert violations[0].severity == Severity.BLOCK
        assert "enable live trading" in violations[0].message.lower()

    def test_detects_live_mode_armed(self):
        rule = NoLiveUnlockRule()
        diff = """
+++ b/src/live/config.py
+LIVE_MODE_ARMED = True
        """
        violations = rule.check(diff, ["src/live/config.py"])

        assert len(violations) == 1
        assert violations[0].severity == Severity.BLOCK

    def test_detects_lock_removal(self):
        rule = NoLiveUnlockRule()
        diff = """
+++ b/src/execution/executor.py
+safety_lock.unlock()
        """
        violations = rule.check(diff, ["src/execution/executor.py"])

        assert len(violations) == 1
        assert violations[0].severity == Severity.BLOCK

    def test_no_false_positive_on_disable(self):
        rule = NoLiveUnlockRule()
        diff = """
+++ b/config.toml
+enable_live_trading = false
        """
        violations = rule.check(diff, ["config.toml"])

        assert len(violations) == 0


class TestExecutionEndpointTouchRule:
    """Tests for execution path changes rule."""

    def test_blocks_order_execution_changes(self):
        rule = ExecutionEndpointTouchRule()
        diff = """
+++ b/src/execution/executor.py
+def place_order(self, symbol, qty):
+    return self.exchange.submit_order(symbol, qty)
        """
        violations = rule.check(diff, ["src/execution/executor.py"])

        assert len(violations) >= 1
        assert violations[0].rule_id == "EXECUTION_ENDPOINT_TOUCH"
        assert violations[0].severity == Severity.BLOCK
        assert "Order execution" in violations[0].message

    def test_warns_on_non_order_execution_changes(self):
        rule = ExecutionEndpointTouchRule()
        diff = """
+++ b/src/execution/utils.py
+def format_price(price):
+    return round(price, 2)
        """
        violations = rule.check(diff, ["src/execution/utils.py"])

        assert len(violations) == 1
        assert violations[0].severity == Severity.WARN
        assert "Execution-critical" in violations[0].message

    def test_no_violation_for_non_critical_paths(self):
        rule = ExecutionEndpointTouchRule()
        diff = """
+++ b/src/strategies/ma_crossover.py
+def generate_signal(self):
+    return "BUY"
        """
        violations = rule.check(diff, ["src/strategies/ma_crossover.py"])

        assert len(violations) == 0


class TestRiskLimitRaiseRule:
    """Tests for risk limit changes rule."""

    def test_blocks_limit_raise_without_justification(self):
        rule = RiskLimitRaiseRule()
        diff = """
+++ b/config.toml
-max_daily_loss = 1000
+max_daily_loss = 5000
        """
        violations = rule.check(diff, ["config.toml"], context=None)

        assert len(violations) >= 1  # May detect both old and new value
        assert violations[0].rule_id == "RISK_LIMIT_RAISE_WITHOUT_JUSTIFICATION"
        assert violations[0].severity == Severity.BLOCK
        assert "No justification" in violations[0].message

    def test_warns_with_justification(self):
        rule = RiskLimitRaiseRule()
        diff = """
+++ b/config.toml
+max_position_size = 10000
        """
        context = {"justification": "Increased based on backtesting results"}
        violations = rule.check(diff, ["config.toml"], context=context)

        assert len(violations) == 1
        assert violations[0].severity == Severity.WARN

    def test_detects_multiple_limit_changes(self):
        rule = RiskLimitRaiseRule()
        diff = """
+++ b/config.toml
+max_daily_loss = 2000
+max_leverage = 5
        """
        violations = rule.check(diff, ["config.toml"])

        assert len(violations) >= 2

    def test_skips_tests_path_max_leverage(self):
        """Tests instantiate configs with max_leverage; not production limit changes."""
        rule = RiskLimitRaiseRule()
        diff = """
+++ b/tests/risk/test_dynamic_leverage_contract.py
+cfg = DynamicLeverageConfig(min_leverage=1.0, max_leverage=50.0, gamma=2.0)
+    assert compute_dynamic_leverage(strength=1.0, cfg=cfg) == pytest.approx(50.0)
        """
        violations = rule.check(diff, ["tests/risk/test_dynamic_leverage_contract.py"])

        assert len(violations) == 0


class TestMissingTestPlanRule:
    """Tests for missing test plan rule."""

    def test_warns_on_large_critical_path_changes_without_plan(self):
        rule = MissingTestPlanRule()
        # Generate a diff with many lines
        diff = "+++ b/src/execution/executor.py\n"
        diff += "\n".join([f"+# Line {i}" for i in range(60)])

        violations = rule.check(diff, ["src/execution/executor.py"], context=None)

        assert len(violations) == 1
        assert violations[0].rule_id == "MISSING_TEST_PLAN"
        assert violations[0].severity == Severity.WARN

    def test_no_warning_with_test_plan(self):
        rule = MissingTestPlanRule()
        diff = "+++ b/src/execution/executor.py\n"
        diff += "\n".join([f"+# Line {i}" for i in range(60)])

        context = {"test_plan": "Run integration tests + shadow mode verification"}
        violations = rule.check(diff, ["src/execution/executor.py"], context=context)

        assert len(violations) == 0

    def test_no_warning_for_small_changes(self):
        rule = MissingTestPlanRule()
        diff = """
+++ b/src/execution/executor.py
+# Small change
+logger.info("order placed")
        """
        violations = rule.check(diff, ["src/execution/executor.py"])

        assert len(violations) == 0

    def test_no_warning_for_non_critical_paths(self):
        rule = MissingTestPlanRule()
        # Large change but not in critical path
        diff = "+++ b/docs/README.md\n"
        diff += "\n".join([f"+Line {i}" for i in range(100)])

        violations = rule.check(diff, ["docs/README.md"])

        assert len(violations) == 0
