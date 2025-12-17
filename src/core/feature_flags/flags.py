"""
Feature Flags Manager

Central manager for feature flags with support for:
- Simple boolean flags
- Percentage-based rollouts
- User-based rollouts
- Environment-based flags
"""

import hashlib
from typing import Optional

from .config import FeatureFlagConfig


class FeatureFlags:
    """
    Singleton-like feature flag manager.

    Usage:
        # Simple flag check
        if FeatureFlags.is_enabled("new_risk_model"):
            use_new_risk_calculation()

        # User-based rollout
        if FeatureFlags.is_enabled_for_user("ai_signals", user_id):
            show_ai_signals()

        # Percentage-based check
        if FeatureFlags.is_enabled_for_percentage("new_feature", 0.1):
            # 10% rollout
            use_new_feature()
    """

    _config: Optional[FeatureFlagConfig] = None

    @classmethod
    def _get_config(cls) -> FeatureFlagConfig:
        """Get or create feature flag configuration."""
        if cls._config is None:
            cls._config = FeatureFlagConfig()
        return cls._config

    @classmethod
    def is_enabled(cls, flag_name: str, default: bool = False) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            flag_name: Name of the feature flag
            default: Default value if flag not found

        Returns:
            True if feature is enabled, False otherwise
        """
        config = cls._get_config()
        return config.get_flag(flag_name, default)

    @classmethod
    def is_enabled_for_user(
        cls, flag_name: str, user_id: str, default: bool = False
    ) -> bool:
        """
        Check if feature is enabled for specific user (A/B testing).

        Uses consistent hashing to ensure same user always gets same result.

        Args:
            flag_name: Name of the feature flag
            user_id: User identifier
            default: Default value if flag not found

        Returns:
            True if feature is enabled for this user, False otherwise
        """
        config = cls._get_config()

        # First check if feature is globally enabled
        if config.get_flag(flag_name, default):
            return True

        # Check rollout percentage
        rollout_percentage = config.get_rollout_percentage(flag_name, 0.0)
        if rollout_percentage <= 0.0:
            return False
        if rollout_percentage >= 1.0:
            return True

        # Use consistent hashing for percentage-based rollout
        return cls._hash_for_percentage(flag_name, user_id) < rollout_percentage

    @classmethod
    def is_enabled_for_percentage(
        cls, flag_name: str, percentage: float, seed: str = ""
    ) -> bool:
        """
        Check if feature should be enabled based on percentage rollout.

        Args:
            flag_name: Name of the feature flag
            percentage: Target percentage (0.0 to 1.0)
            seed: Optional seed for consistent hashing

        Returns:
            True if feature should be enabled for this instance
        """
        if percentage <= 0.0:
            return False
        if percentage >= 1.0:
            return True

        return cls._hash_for_percentage(flag_name, seed) < percentage

    @classmethod
    def get_rollout_percentage(cls, flag_name: str, default: float = 0.0) -> float:
        """
        Get configured rollout percentage for a feature.

        Args:
            flag_name: Name of the feature flag
            default: Default percentage

        Returns:
            Rollout percentage (0.0 to 1.0)
        """
        config = cls._get_config()
        return config.get_rollout_percentage(flag_name, default)

    @classmethod
    def is_enabled_for_environment(cls, flag_name: str, default: bool = False) -> bool:
        """
        Check if feature is enabled for current environment.

        Args:
            flag_name: Name of the feature flag
            default: Default value if flag not found

        Returns:
            True if feature is enabled for current environment
        """
        config = cls._get_config()
        return config.get_env_specific_flag(flag_name, default)

    @staticmethod
    def _hash_for_percentage(flag_name: str, identifier: str) -> float:
        """
        Generate consistent hash for percentage-based rollouts.

        Args:
            flag_name: Feature flag name
            identifier: User ID or other identifier

        Returns:
            Float between 0.0 and 1.0
        """
        hash_input = f"{flag_name}:{identifier}".encode("utf-8")
        hash_value = hashlib.md5(hash_input).hexdigest()
        # Convert first 8 hex digits to int, then to 0.0-1.0 range
        return int(hash_value[:8], 16) / 0xFFFFFFFF

    @classmethod
    def reset_config(cls) -> None:
        """Reset configuration (mainly for testing)."""
        cls._config = None
