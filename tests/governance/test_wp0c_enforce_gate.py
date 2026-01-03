"""
Tests for WP0C - enforce_live_mode_gate function

Tests specific requirements from WP0C prompt:
- live blocked by default
- live enabled without ack token => fails
- live enabled with ack but env != prod => fails
- live enabled + ack + env==prod => passes
"""

import pytest

from src.governance.live_mode_gate import (
    enforce_live_mode_gate,
    LiveModeViolationError,
)


class TestLiveBlockedByDefault:
    """Test that live is blocked by default."""

    def test_live_disabled_by_default(self):
        """Live mode disabled by default => should pass."""
        config = {
            "env": "dev",
            "session_id": "test",
            "strategy_id": "ma_crossover",
            "risk_limits": {},
        }
        # No "live" key => defaults to disabled
        enforce_live_mode_gate(config, env="dev")  # Should not raise

    def test_live_explicitly_disabled(self):
        """Live mode explicitly disabled => should pass."""
        config = {
            "live": {"enabled": False},
            "env": "dev",
            "session_id": "test",
            "strategy_id": "ma_crossover",
            "risk_limits": {},
        }
        enforce_live_mode_gate(config, env="dev")  # Should not raise

    def test_live_disabled_any_env(self):
        """Live disabled works in any env."""
        config = {
            "live": {"enabled": False},
            "session_id": "test",
            "strategy_id": "ma_crossover",
            "risk_limits": {},
        }
        # Should work in all envs when disabled
        for env in ["dev", "shadow", "testnet", "prod"]:
            enforce_live_mode_gate(config, env=env)  # Should not raise


class TestLiveEnabledWithoutAckToken:
    """Test that live enabled without ack token fails."""

    def test_live_enabled_no_ack_token(self):
        """Live enabled without operator_ack => should fail."""
        config = {
            "live": {"enabled": True},  # No operator_ack!
            "session_id": "test",
            "strategy_id": "ma_crossover",
            "risk_limits": {},
        }
        with pytest.raises(LiveModeViolationError) as exc_info:
            enforce_live_mode_gate(config, env="prod")

        error_msg = str(exc_info.value)
        assert "operator_ack" in error_msg.lower()
        assert "I_UNDERSTAND_LIVE_TRADING" in error_msg

    def test_live_enabled_wrong_ack_token(self):
        """Live enabled with wrong ack token => should fail."""
        config = {
            "live": {
                "enabled": True,
                "operator_ack": "WRONG_TOKEN",
            },
            "session_id": "test",
            "strategy_id": "ma_crossover",
            "risk_limits": {},
        }
        with pytest.raises(LiveModeViolationError) as exc_info:
            enforce_live_mode_gate(config, env="prod")

        error_msg = str(exc_info.value)
        assert "operator_ack" in error_msg.lower()

    def test_live_enabled_empty_ack_token(self):
        """Live enabled with empty ack token => should fail."""
        config = {
            "live": {
                "enabled": True,
                "operator_ack": "",
            },
            "session_id": "test",
            "strategy_id": "ma_crossover",
            "risk_limits": {},
        }
        with pytest.raises(LiveModeViolationError):
            enforce_live_mode_gate(config, env="prod")


class TestLiveEnabledWithAckButWrongEnv:
    """Test that live enabled with ack but wrong env fails."""

    def test_live_enabled_ack_but_dev_env(self):
        """Live enabled + ack but env=dev => should fail."""
        config = {
            "live": {
                "enabled": True,
                "operator_ack": "I_UNDERSTAND_LIVE_TRADING",
            },
            "session_id": "test",
            "strategy_id": "ma_crossover",
            "risk_limits": {},
        }
        with pytest.raises(LiveModeViolationError) as exc_info:
            enforce_live_mode_gate(config, env="dev")

        error_msg = str(exc_info.value)
        assert "env is 'dev'" in error_msg
        assert "prod" in error_msg or "live" in error_msg

    def test_live_enabled_ack_but_shadow_env(self):
        """Live enabled + ack but env=shadow => should fail."""
        config = {
            "live": {
                "enabled": True,
                "operator_ack": "I_UNDERSTAND_LIVE_TRADING",
            },
            "session_id": "test",
            "strategy_id": "ma_crossover",
            "risk_limits": {},
        }
        with pytest.raises(LiveModeViolationError) as exc_info:
            enforce_live_mode_gate(config, env="shadow")

        error_msg = str(exc_info.value)
        assert "env is 'shadow'" in error_msg

    def test_live_enabled_ack_but_testnet_env(self):
        """Live enabled + ack but env=testnet => should fail."""
        config = {
            "live": {
                "enabled": True,
                "operator_ack": "I_UNDERSTAND_LIVE_TRADING",
            },
            "session_id": "test",
            "strategy_id": "ma_crossover",
            "risk_limits": {},
        }
        with pytest.raises(LiveModeViolationError) as exc_info:
            enforce_live_mode_gate(config, env="testnet")

        error_msg = str(exc_info.value)
        assert "env is 'testnet'" in error_msg


class TestLiveEnabledWithAckAndProdEnv:
    """Test that live enabled + ack + prod env passes."""

    def test_live_enabled_ack_prod_env_passes(self):
        """Live enabled + correct ack + env=prod => should pass."""
        config = {
            "live": {
                "enabled": True,
                "operator_ack": "I_UNDERSTAND_LIVE_TRADING",
            },
            "session_id": "test",
            "strategy_id": "ma_crossover",
            "risk_limits": {"max_position_size": 1000},
        }
        # Should not raise
        enforce_live_mode_gate(config, env="prod")

    def test_live_enabled_ack_live_env_passes(self):
        """Live enabled + correct ack + env=live => should pass."""
        config = {
            "live": {
                "enabled": True,
                "operator_ack": "I_UNDERSTAND_LIVE_TRADING",
            },
            "session_id": "test",
            "strategy_id": "ma_crossover",
            "risk_limits": {"max_position_size": 1000},
        }
        # Should not raise (env="live" is also valid)
        enforce_live_mode_gate(config, env="live")


class TestMultipleViolations:
    """Test that multiple violations are reported together."""

    def test_multiple_violations_reported(self):
        """Multiple violations should be reported in single error."""
        config = {
            "live": {
                "enabled": True,
                # Missing operator_ack
            },
            "session_id": "test",
            "strategy_id": "ma_crossover",
            "risk_limits": {},
        }
        with pytest.raises(LiveModeViolationError) as exc_info:
            enforce_live_mode_gate(config, env="dev")

        error_msg = str(exc_info.value)
        # Should contain both violations:
        # 1. Wrong env (dev instead of prod/live)
        # 2. Missing operator_ack
        assert "env is 'dev'" in error_msg
        assert "operator_ack" in error_msg.lower()


class TestRiskRuntimeImportCheck:
    """Test that risk_runtime import is checked."""

    def test_risk_runtime_importable(self):
        """Risk runtime should be importable (basic sanity)."""
        config = {
            "live": {
                "enabled": True,
                "operator_ack": "I_UNDERSTAND_LIVE_TRADING",
            },
            "session_id": "test",
            "strategy_id": "ma_crossover",
            "risk_limits": {"max_position_size": 1000},
        }
        # Should not raise (risk_runtime exists from WP0B)
        enforce_live_mode_gate(config, env="prod")
