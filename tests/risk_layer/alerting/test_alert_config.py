"""
Tests for AlertConfig and configuration loading.
"""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from src.risk_layer.alerting.alert_config import (
    AlertConfig,
    _substitute_env_vars,
    load_alert_config,
)
from src.risk_layer.alerting.alert_types import AlertSeverity


class TestAlertConfig:
    """Test AlertConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AlertConfig()

        assert config.enabled is False
        assert config.min_severity == AlertSeverity.WARNING
        assert config.buffer_size == 1000
        assert config.channels == {}
        assert config.raw == {}

    def test_custom_config(self):
        """Test creating config with custom values."""
        channels = {"slack": {"enabled": True, "webhook": "https://..."}}
        config = AlertConfig(
            enabled=True,
            min_severity=AlertSeverity.ERROR,
            buffer_size=500,
            channels=channels,
        )

        assert config.enabled is True
        assert config.min_severity == AlertSeverity.ERROR
        assert config.buffer_size == 500
        assert config.channels == channels

    def test_get_channel_config(self):
        """Test retrieving channel configuration."""
        config = AlertConfig(
            channels={
                "slack": {"enabled": True, "webhook": "https://..."},
                "email": {"enabled": False},
            }
        )

        slack_cfg = config.get_channel_config("slack")
        assert slack_cfg == {"enabled": True, "webhook": "https://..."}

        email_cfg = config.get_channel_config("email")
        assert email_cfg == {"enabled": False}

        missing_cfg = config.get_channel_config("pagerduty")
        assert missing_cfg is None

    def test_is_channel_enabled(self):
        """Test checking if channel is enabled."""
        config = AlertConfig(
            channels={
                "slack": {"enabled": True},
                "email": {"enabled": False},
                "sms": {},  # No 'enabled' key
            }
        )

        assert config.is_channel_enabled("slack") is True
        assert config.is_channel_enabled("email") is False
        assert config.is_channel_enabled("sms") is False
        assert config.is_channel_enabled("nonexistent") is False


class TestEnvVarSubstitution:
    """Test environment variable substitution."""

    def test_substitute_simple_string(self):
        """Test substituting a single env var in string."""
        os.environ["TEST_VAR"] = "test_value"
        try:
            result = _substitute_env_vars("prefix_${TEST_VAR}_suffix")
            assert result == "prefix_test_value_suffix"
        finally:
            del os.environ["TEST_VAR"]

    def test_substitute_multiple_vars(self):
        """Test substituting multiple env vars."""
        os.environ["VAR1"] = "value1"
        os.environ["VAR2"] = "value2"
        try:
            result = _substitute_env_vars("${VAR1}_middle_${VAR2}")
            assert result == "value1_middle_value2"
        finally:
            del os.environ["VAR1"]
            del os.environ["VAR2"]

    def test_substitute_in_dict(self):
        """Test substitution in nested dict."""
        os.environ["SECRET_KEY"] = "secret123"
        try:
            input_dict = {
                "api_key": "${SECRET_KEY}",
                "nested": {"token": "Bearer ${SECRET_KEY}"},
            }
            result = _substitute_env_vars(input_dict)
            assert result["api_key"] == "secret123"
            assert result["nested"]["token"] == "Bearer secret123"
        finally:
            del os.environ["SECRET_KEY"]

    def test_substitute_in_list(self):
        """Test substitution in list."""
        os.environ["HOST"] = "localhost"
        try:
            input_list = ["${HOST}:8080", "other_value"]
            result = _substitute_env_vars(input_list)
            assert result == ["localhost:8080", "other_value"]
        finally:
            del os.environ["HOST"]

    def test_substitute_primitives_unchanged(self):
        """Test that non-string primitives pass through unchanged."""
        assert _substitute_env_vars(42) == 42
        assert _substitute_env_vars(3.14) == 3.14
        assert _substitute_env_vars(True) is True
        assert _substitute_env_vars(None) is None

    def test_substitute_missing_var_raises(self):
        """Test that missing env var raises ValueError."""
        # Ensure var doesn't exist
        if "NONEXISTENT_VAR_XYZ" in os.environ:
            del os.environ["NONEXISTENT_VAR_XYZ"]

        with pytest.raises(ValueError, match="NONEXISTENT_VAR_XYZ.*not set"):
            _substitute_env_vars("${NONEXISTENT_VAR_XYZ}")

    def test_substitute_no_vars(self):
        """Test string without env vars passes through."""
        result = _substitute_env_vars("plain string")
        assert result == "plain string"


class TestLoadAlertConfig:
    """Test loading configuration from TOML."""

    def test_load_nonexistent_file_returns_defaults(self):
        """Test that missing config file returns safe defaults."""
        nonexistent = Path("/tmp/nonexistent_config_xyz.toml")
        config = load_alert_config(config_path=nonexistent)

        assert config.enabled is False
        assert config.min_severity == AlertSeverity.WARNING
        assert config.buffer_size == 1000

    def test_load_minimal_config(self):
        """Test loading minimal TOML config."""
        toml_content = """
[alerting]
enabled = true
"""
        with NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            f.flush()
            temp_path = Path(f.name)

        try:
            config = load_alert_config(config_path=temp_path)
            assert config.enabled is True
            assert config.min_severity == AlertSeverity.WARNING  # default
        finally:
            temp_path.unlink()

    def test_load_full_config(self):
        """Test loading complete TOML config."""
        toml_content = """
[alerting]
enabled = true
min_severity = "error"
buffer_size = 2000

[alerting.channels.slack]
enabled = true
webhook_url = "https://hooks.slack.com/test"

[alerting.channels.email]
enabled = false
"""
        with NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            f.flush()
            temp_path = Path(f.name)

        try:
            config = load_alert_config(config_path=temp_path)
            assert config.enabled is True
            assert config.min_severity == AlertSeverity.ERROR
            assert config.buffer_size == 2000
            assert config.is_channel_enabled("slack") is True
            assert config.is_channel_enabled("email") is False
        finally:
            temp_path.unlink()

    def test_load_config_with_env_vars(self):
        """Test loading config with environment variable substitution."""
        os.environ["SLACK_WEBHOOK"] = "https://hooks.slack.com/secret"

        toml_content = """
[alerting]
enabled = true

[alerting.channels.slack]
enabled = true
webhook_url = "${SLACK_WEBHOOK}"
"""
        with NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            f.flush()
            temp_path = Path(f.name)

        try:
            config = load_alert_config(config_path=temp_path)
            slack_cfg = config.get_channel_config("slack")
            assert slack_cfg["webhook_url"] == "https://hooks.slack.com/secret"
        finally:
            temp_path.unlink()
            del os.environ["SLACK_WEBHOOK"]

    def test_load_config_missing_env_var_raises(self):
        """Test that missing required env var raises error."""
        if "MISSING_SECRET" in os.environ:
            del os.environ["MISSING_SECRET"]

        toml_content = """
[alerting]
enabled = true

[alerting.channels.slack]
webhook_url = "${MISSING_SECRET}"
"""
        with NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            f.flush()
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="MISSING_SECRET.*not set"):
                load_alert_config(config_path=temp_path)
        finally:
            temp_path.unlink()

    def test_load_config_invalid_severity(self):
        """Test that invalid severity raises error."""
        toml_content = """
[alerting]
min_severity = "super_critical"
"""
        with NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            f.flush()
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Invalid min_severity"):
                load_alert_config(config_path=temp_path)
        finally:
            temp_path.unlink()

    def test_load_config_invalid_buffer_size(self):
        """Test that invalid buffer_size raises error."""
        toml_content = """
[alerting]
buffer_size = -100
"""
        with NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            f.flush()
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="buffer_size must be positive"):
                load_alert_config(config_path=temp_path)
        finally:
            temp_path.unlink()

    def test_load_config_custom_section(self):
        """Test loading from custom TOML section."""
        toml_content = """
[custom_alerts]
enabled = true
min_severity = "critical"
"""
        with NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(toml_content)
            f.flush()
            temp_path = Path(f.name)

        try:
            config = load_alert_config(config_path=temp_path, section="custom_alerts")
            assert config.enabled is True
            assert config.min_severity == AlertSeverity.CRITICAL
        finally:
            temp_path.unlink()
