"""
Feature Flag Management System for Peak Trade.

Provides environment-based, user-based, and percentage-based feature rollouts
with runtime toggle support.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class FeatureFlag(Enum):
    """Available feature flags."""

    ENABLE_REDIS_CACHE = "enable_redis_cache"
    ENABLE_AI_WORKFLOW = "enable_ai_workflow"
    ENABLE_ADVANCED_METRICS = "enable_advanced_metrics"
    ENABLE_EXPERIMENTAL_STRATEGIES = "enable_experimental_strategies"
    ENABLE_BACKUP_RECOVERY = "enable_backup_recovery"


class FeatureFlagManager:
    """
    Feature flag management system.

    Features:
    - Environment-based flags
    - User-based rollouts
    - Percentage-based rollouts
    - A/B testing support
    - Runtime toggle

    Example:
        flags = FeatureFlagManager()

        if flags.is_enabled(FeatureFlag.ENABLE_REDIS_CACHE):
            use_redis_cache()
        else:
            use_memory_cache()
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config/feature_flags.json")
        self.flags = self._load_flags()
        self.overrides: dict[str, bool] = {}

    def _load_flags(self) -> dict[str, Any]:
        """Load flags from config file."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return json.load(f)
        return {}

    def is_enabled(
        self,
        flag: FeatureFlag,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Check if feature flag is enabled.

        Args:
            flag: Feature flag to check
            user_id: Optional user ID for user-based rollout

        Returns:
            True if flag is enabled, False otherwise
        """
        flag_name = flag.value

        # Check override first
        if flag_name in self.overrides:
            return self.overrides[flag_name]

        # Check config
        flag_config = self.flags.get(flag_name, {"enabled": False})

        # Simple enabled/disabled
        if isinstance(flag_config, bool):
            return flag_config

        enabled = flag_config.get("enabled", False)

        # Percentage-based rollout
        if "percentage" in flag_config:
            import hashlib

            if user_id:
                hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
                return (hash_value % 100) < flag_config["percentage"]

        # Environment-based
        if "environments" in flag_config:
            import os

            env = os.getenv("ENVIRONMENT", "development")
            return env in flag_config["environments"]

        return enabled

    def enable(self, flag: FeatureFlag):
        """Temporarily enable a flag (runtime only)."""
        self.overrides[flag.value] = True

    def disable(self, flag: FeatureFlag):
        """Temporarily disable a flag (runtime only)."""
        self.overrides[flag.value] = False

    def reset_overrides(self):
        """Clear all runtime overrides."""
        self.overrides.clear()


# Global instance
feature_flags = FeatureFlagManager()


def requires_feature(flag: FeatureFlag):
    """
    Decorator to gate function execution behind feature flag.

    Example:
        @requires_feature(FeatureFlag.ENABLE_AI_WORKFLOW)
        def run_ai_analysis():
            pass
    """
    from functools import wraps

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not feature_flags.is_enabled(flag):
                raise RuntimeError(
                    f"Feature {flag.value} is not enabled. "
                    f"Enable it in config/feature_flags.json"
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator
