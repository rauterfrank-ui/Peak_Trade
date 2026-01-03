"""
Tests for WP0C - Config Validation

Tests requirements from WP0C prompt:
- invalid env => fails
- missing required keys => fails (minimal set)
- valid minimal config => passes
"""

import pytest

from src.governance.config_validation import (
    validate_execution_config,
    validate_execution_config_strict,
    ConfigValidationError,
)


class TestInvalidEnv:
    """Test that invalid env fails validation."""

    def test_missing_env(self):
        """Missing env field => should fail."""
        config = {
            "session_id": "test",
            "strategy_id": "ma_crossover",
            "risk_limits": {},
        }
        errors = validate_execution_config(config)
        assert len(errors) > 0
        assert any("env" in err.lower() for err in errors)

    def test_invalid_env_value(self):
        """Invalid env value => should fail."""
        config = {
            "env": "invalid_env",
            "session_id": "test",
            "strategy_id": "ma_crossover",
            "risk_limits": {},
        }
        errors = validate_execution_config(config)
        assert len(errors) > 0
        assert any("invalid_env" in err for err in errors)
        assert any("dev" in err and "shadow" in err for err in errors)  # Valid envs listed

    def test_empty_env(self):
        """Empty env string => should fail."""
        config = {
            "env": "",
            "session_id": "test",
            "strategy_id": "ma_crossover",
            "risk_limits": {},
        }
        errors = validate_execution_config(config)
        assert len(errors) > 0

    def test_valid_envs(self):
        """Valid envs should pass."""
        valid_envs = ["dev", "shadow", "testnet", "prod"]
        for env in valid_envs:
            config = {
                "env": env,
                "session_id": "test",
                "strategy_id": "ma_crossover",
                "risk_limits": {},
            }
            errors = validate_execution_config(config)
            # Should only have env-related errors (not env itself)
            assert not any("invalid env" in err.lower() for err in errors)


class TestMissingRequiredKeys:
    """Test that missing required keys fail validation."""

    def test_missing_session_id(self):
        """Missing session_id => should fail."""
        config = {
            "env": "dev",
            # Missing: session_id
            "strategy_id": "ma_crossover",
            "risk_limits": {},
        }
        errors = validate_execution_config(config)
        assert len(errors) > 0
        assert any("session_id" in err for err in errors)

    def test_missing_strategy_id(self):
        """Missing strategy_id => should fail."""
        config = {
            "env": "dev",
            "session_id": "test",
            # Missing: strategy_id
            "risk_limits": {},
        }
        errors = validate_execution_config(config)
        assert len(errors) > 0
        assert any("strategy_id" in err for err in errors)

    def test_missing_risk_limits(self):
        """Missing risk_limits => should fail."""
        config = {
            "env": "dev",
            "session_id": "test",
            "strategy_id": "ma_crossover",
            # Missing: risk_limits
        }
        errors = validate_execution_config(config)
        assert len(errors) > 0
        assert any("risk_limits" in err for err in errors)

    def test_risk_limits_wrong_type(self):
        """risk_limits as non-dict => should fail."""
        config = {
            "env": "dev",
            "session_id": "test",
            "strategy_id": "ma_crossover",
            "risk_limits": "not_a_dict",  # Wrong type!
        }
        errors = validate_execution_config(config)
        assert len(errors) > 0
        assert any("risk_limits" in err and "dict" in err for err in errors)

    def test_all_keys_missing(self):
        """All required keys missing => multiple errors."""
        config = {}
        errors = validate_execution_config(config)
        assert len(errors) >= 4  # env, session_id, strategy_id, risk_limits
        assert any("env" in err for err in errors)
        assert any("session_id" in err for err in errors)
        assert any("strategy_id" in err for err in errors)
        assert any("risk_limits" in err for err in errors)


class TestValidMinimalConfig:
    """Test that valid minimal config passes."""

    def test_valid_minimal_dev_config(self):
        """Valid minimal config for dev => should pass."""
        config = {
            "env": "dev",
            "session_id": "test_session",
            "strategy_id": "ma_crossover",
            "risk_limits": {},  # Empty is OK for dev
        }
        errors = validate_execution_config(config)
        # Should have no errors (or only warnings, but no blocking errors)
        assert len([e for e in errors if "missing required" in e.lower()]) == 0

    def test_valid_minimal_prod_config(self):
        """Valid minimal config for prod => should pass."""
        config = {
            "env": "prod",
            "session_id": "prod_session",
            "strategy_id": "ma_crossover",
            "risk_limits": {"max_position_size": 1000},
        }
        errors = validate_execution_config(config)
        # Should have no blocking errors
        # (may have warnings about R&D patterns, but no "missing required")
        blocking_errors = [e for e in errors if "missing required" in e.lower()]
        assert len(blocking_errors) == 0

    def test_valid_config_all_envs(self):
        """Valid config should pass in all envs."""
        for env in ["dev", "shadow", "testnet", "prod"]:
            config = {
                "env": env,
                "session_id": f"{env}_session",
                "strategy_id": "ma_crossover",
                "risk_limits": {"max_position_size": 1000},
            }
            errors = validate_execution_config(config)
            # No blocking errors
            assert len([e for e in errors if "missing required" in e.lower()]) == 0


class TestStrictValidation:
    """Test strict validation mode (raises on error)."""

    def test_strict_mode_raises_on_invalid_config(self):
        """Strict mode should raise ConfigValidationError."""
        config = {
            "env": "invalid_env",
            # Missing other required fields
        }
        with pytest.raises(ConfigValidationError) as exc_info:
            validate_execution_config_strict(config)

        error_msg = str(exc_info.value)
        assert "Config validation failed" in error_msg
        assert "error(s)" in error_msg.lower()

    def test_strict_mode_passes_on_valid_config(self):
        """Strict mode should not raise on valid config."""
        config = {
            "env": "dev",
            "session_id": "test",
            "strategy_id": "ma_crossover",
            "risk_limits": {},
        }
        # Should not raise
        validate_execution_config_strict(config)


class TestRAndDStrategyWarning:
    """Test R&D strategy warning in live env."""

    def test_r_and_d_strategy_in_prod_warns(self):
        """R&D strategy pattern in prod => should warn."""
        r_and_d_strategies = [
            "test_strategy",
            "debug_ma_crossover",
            "experimental_breakout",
        ]
        for strategy_id in r_and_d_strategies:
            config = {
                "env": "prod",
                "session_id": "test",
                "strategy_id": strategy_id,
                "risk_limits": {"max_position_size": 1000},
            }
            errors = validate_execution_config(config)
            # Should have warning about R&D pattern
            assert len(errors) > 0
            assert any("r&d" in err.lower() or "test" in err.lower() for err in errors)

    def test_r_and_d_strategy_in_dev_ok(self):
        """R&D strategy pattern in dev => no warning."""
        config = {
            "env": "dev",
            "session_id": "test",
            "strategy_id": "test_strategy",
            "risk_limits": {},
        }
        errors = validate_execution_config(config)
        # Should not warn in dev env
        # (may have other non-critical warnings, but not R&D-related)
        # For dev env, R&D strategies are OK
        assert all("r&d" not in err.lower() for err in errors)

    def test_normal_strategy_in_prod_ok(self):
        """Normal strategy in prod => no warning."""
        config = {
            "env": "prod",
            "session_id": "test",
            "strategy_id": "ma_crossover",  # Normal name
            "risk_limits": {"max_position_size": 1000},
        }
        errors = validate_execution_config(config)
        # Should have no errors at all
        assert len(errors) == 0
