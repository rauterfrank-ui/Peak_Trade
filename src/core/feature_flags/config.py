"""
Feature Flag Configuration Loader

Loads feature flag configurations from config.toml and environment variables.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional


class FeatureFlagConfig:
    """Load and manage feature flag configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize feature flag configuration.

        Args:
            config_path: Path to config.toml. If None, searches for config.toml
                        in current directory and parent directories.
        """
        self.config_path = config_path or self._find_config()
        self.config = self._load_config()

    def _find_config(self) -> Path:
        """Find config.toml by searching current and parent directories."""
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            config_file = parent / "config.toml"
            if config_file.exists():
                return config_file
        # Default to current directory
        return Path("config.toml")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from TOML file."""
        if not self.config_path.exists():
            return {}

        try:
            # Try tomllib first (Python 3.11+ built-in, requires binary)
            import tomllib
            with open(self.config_path, "rb") as f:
                return tomllib.load(f)
        except (ImportError, AttributeError):
            # Fall back to toml library (requires text mode)
            import toml
            with open(self.config_path, "r", encoding="utf-8") as f:
                return toml.load(f)

    def get_flag(self, flag_name: str, default: bool = False) -> bool:
        """
        Get feature flag value.

        Checks in order:
        1. Environment variable FEATURE_{FLAG_NAME}
        2. config.toml [feature_flags] section
        3. Default value

        Args:
            flag_name: Name of the feature flag
            default: Default value if flag not found

        Returns:
            Boolean flag value
        """
        # Check environment variable first
        env_var = f"FEATURE_{flag_name.upper()}"
        env_value = os.getenv(env_var)
        if env_value is not None:
            return env_value.lower() in ("true", "1", "yes", "on")

        # Check config file
        feature_flags = self.config.get("feature_flags", {})
        return feature_flags.get(flag_name, default)

    def get_rollout_percentage(self, flag_name: str, default: float = 0.0) -> float:
        """
        Get rollout percentage for gradual feature rollout.

        Args:
            flag_name: Name of the feature flag
            default: Default percentage (0.0 = 0%, 1.0 = 100%)

        Returns:
            Percentage as float between 0.0 and 1.0
        """
        # Check environment variable first
        env_var = f"FEATURE_ROLLOUT_{flag_name.upper()}"
        env_value = os.getenv(env_var)
        if env_value is not None:
            try:
                return max(0.0, min(1.0, float(env_value)))
            except ValueError:
                pass

        # Check config file
        rollout = self.config.get("feature_flags", {}).get("rollout", {})
        percentage = rollout.get(flag_name, default)
        return max(0.0, min(1.0, float(percentage)))

    def get_env_specific_flag(self, flag_name: str, default: bool = False) -> bool:
        """
        Get environment-specific feature flag.

        Checks [feature_flags.by_env.{environment}] section based on
        ENVIRONMENT variable (default: "development").

        Args:
            flag_name: Name of the feature flag
            default: Default value if flag not found

        Returns:
            Boolean flag value
        """
        environment = os.getenv("ENVIRONMENT", "development")
        env_flags = (
            self.config.get("feature_flags", {})
            .get("by_env", {})
            .get(environment, {})
        )
        return env_flags.get(flag_name, default)
