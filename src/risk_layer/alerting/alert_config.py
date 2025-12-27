"""
Alert Configuration Loader
===========================

Loads alerting configuration from TOML with environment variable substitution.
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[assignment]

from src.risk_layer.alerting.alert_types import AlertSeverity


@dataclass
class AlertConfig:
    """
    Configuration for the alerting system.

    Attributes:
        enabled: Whether alerting is active (default: False for safety)
        min_severity: Minimum severity to process (default: WARNING)
        buffer_size: Max events to buffer in memory (default: 1000)
        channels: Dict of channel configurations (default: empty)
        raw: Raw TOML dict for custom settings
    """

    enabled: bool = False
    min_severity: AlertSeverity = AlertSeverity.WARNING
    buffer_size: int = 1000
    channels: Dict[str, Dict[str, Any]] = None
    raw: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.channels is None:
            self.channels = {}
        if self.raw is None:
            self.raw = {}

    def get_channel_config(self, channel_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific channel.

        Args:
            channel_name: Name of the channel (e.g., "slack", "email")

        Returns:
            Channel config dict or None if not configured
        """
        return self.channels.get(channel_name)

    def is_channel_enabled(self, channel_name: str) -> bool:
        """
        Check if a specific channel is enabled.

        Args:
            channel_name: Name of the channel

        Returns:
            True if channel exists and is enabled
        """
        channel_cfg = self.get_channel_config(channel_name)
        if channel_cfg is None:
            return False
        return channel_cfg.get("enabled", False)


def _substitute_env_vars(value: Any) -> Any:
    """
    Recursively substitute ${ENV_VAR} placeholders in config values.

    Args:
        value: Config value (str, dict, list, or primitive)

    Returns:
        Value with environment variables substituted

    Raises:
        ValueError: If required env var is not set
    """
    if isinstance(value, str):
        # Find all ${VAR_NAME} patterns
        pattern = re.compile(r'\$\{([A-Z_][A-Z0-9_]*)\}')

        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            env_value = os.environ.get(var_name)
            if env_value is None:
                raise ValueError(
                    f"Environment variable ${{{var_name}}} not set. "
                    f"Required for alert configuration."
                )
            return env_value

        return pattern.sub(replacer, value)

    elif isinstance(value, dict):
        return {k: _substitute_env_vars(v) for k, v in value.items()}

    elif isinstance(value, list):
        return [_substitute_env_vars(item) for item in value]

    else:
        # Primitive types (int, float, bool, None) pass through
        return value


def load_alert_config(
    config_path: Optional[Path] = None,
    section: str = "alerting",
) -> AlertConfig:
    """
    Load alert configuration from TOML file.

    Args:
        config_path: Path to config TOML file (default: config/config.toml)
        section: TOML section to read (default: "alerting")

    Returns:
        AlertConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If TOML is invalid or required env vars missing

    Example TOML:
        [alerting]
        enabled = true
        min_severity = "warning"
        buffer_size = 2000

        [alerting.channels.slack]
        enabled = false
        webhook_url = "${SLACK_WEBHOOK_URL}"
    """
    # Resolve config path
    if config_path is None:
        # Use Peak_Trade convention: config/config.toml
        project_root = Path(__file__).resolve().parents[3]
        config_path = project_root / "config" / "config.toml"

    if not config_path.exists():
        # Return safe defaults if no config file
        return AlertConfig()

    # Load TOML
    with open(config_path, "rb") as f:
        raw_config = tomllib.load(f)

    # Extract alerting section
    alerting_config = raw_config.get(section, {})

    # Apply environment variable substitution
    try:
        alerting_config = _substitute_env_vars(alerting_config)
    except ValueError as e:
        # Re-raise with more context
        raise ValueError(f"Failed to load alert config: {e}") from e

    # Parse configuration
    enabled = alerting_config.get("enabled", False)

    severity_str = alerting_config.get("min_severity", "warning")
    try:
        min_severity = AlertSeverity(severity_str.lower())
    except ValueError:
        raise ValueError(
            f"Invalid min_severity '{severity_str}'. "
            f"Must be one of: {[s.value for s in AlertSeverity]}"
        )

    buffer_size = alerting_config.get("buffer_size", 1000)
    if not isinstance(buffer_size, int) or buffer_size < 1:
        raise ValueError(f"buffer_size must be positive integer, got {buffer_size}")

    channels = alerting_config.get("channels", {})
    if not isinstance(channels, dict):
        raise ValueError(f"channels must be a dict, got {type(channels)}")

    return AlertConfig(
        enabled=enabled,
        min_severity=min_severity,
        buffer_size=buffer_size,
        channels=channels,
        raw=alerting_config,
    )
