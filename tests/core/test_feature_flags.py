"""
Tests for Feature Flags System

Tests the feature flag manager and configuration loader.
"""

import os
import tempfile
from pathlib import Path

import pytest

from src.core.feature_flags import FeatureFlags, FeatureFlagConfig


class TestFeatureFlagConfig:
    """Test feature flag configuration loading."""

    def test_load_nonexistent_config(self):
        """Test loading when config file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = FeatureFlagConfig(Path(tmpdir) / "nonexistent.toml")
            assert config.get_flag("any_flag") is False

    def test_get_flag_default(self):
        """Test getting flag with default value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = FeatureFlagConfig(Path(tmpdir) / "test.toml")
            assert config.get_flag("missing_flag", default=True) is True
            assert config.get_flag("missing_flag", default=False) is False

    def test_get_flag_from_env(self):
        """Test flag override from environment variable."""
        os.environ["FEATURE_TEST_FLAG"] = "true"
        try:
            config = FeatureFlagConfig()
            assert config.get_flag("test_flag") is True
        finally:
            del os.environ["FEATURE_TEST_FLAG"]

    def test_get_flag_env_variations(self):
        """Test various environment variable value formats."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("1", True),
            ("yes", True),
            ("on", True),
            ("false", False),
            ("False", False),
            ("0", False),
            ("no", False),
            ("off", False),
        ]

        for env_value, expected in test_cases:
            os.environ["FEATURE_TEST"] = env_value
            try:
                config = FeatureFlagConfig()
                assert config.get_flag("test") == expected, f"Failed for {env_value}"
            finally:
                del os.environ["FEATURE_TEST"]

    def test_get_rollout_percentage_default(self):
        """Test getting rollout percentage with default."""
        config = FeatureFlagConfig()
        assert config.get_rollout_percentage("missing", default=0.5) == 0.5

    def test_get_rollout_percentage_from_env(self):
        """Test rollout percentage from environment."""
        os.environ["FEATURE_ROLLOUT_TEST"] = "0.75"
        try:
            config = FeatureFlagConfig()
            assert config.get_rollout_percentage("test") == 0.75
        finally:
            del os.environ["FEATURE_ROLLOUT_TEST"]

    def test_rollout_percentage_bounds(self):
        """Test that rollout percentage is clamped to [0, 1]."""
        config = FeatureFlagConfig()

        # Test with env vars
        os.environ["FEATURE_ROLLOUT_OVER"] = "1.5"
        os.environ["FEATURE_ROLLOUT_UNDER"] = "-0.5"
        try:
            assert config.get_rollout_percentage("over") == 1.0
            assert config.get_rollout_percentage("under") == 0.0
        finally:
            del os.environ["FEATURE_ROLLOUT_OVER"]
            del os.environ["FEATURE_ROLLOUT_UNDER"]


class TestFeatureFlags:
    """Test feature flags manager."""

    def setup_method(self):
        """Reset config before each test."""
        FeatureFlags.reset_config()

    def teardown_method(self):
        """Clean up after each test."""
        FeatureFlags.reset_config()

    def test_is_enabled_default(self):
        """Test flag check with default value."""
        assert FeatureFlags.is_enabled("missing_flag", default=True) is True
        assert FeatureFlags.is_enabled("missing_flag", default=False) is False

    def test_is_enabled_from_env(self):
        """Test flag from environment variable."""
        os.environ["FEATURE_NEW_FEATURE"] = "true"
        try:
            FeatureFlags.reset_config()  # Reload config
            assert FeatureFlags.is_enabled("new_feature") is True
        finally:
            del os.environ["FEATURE_NEW_FEATURE"]
            FeatureFlags.reset_config()

    def test_is_enabled_for_user_globally_enabled(self):
        """Test user-based flag when globally enabled."""
        os.environ["FEATURE_TEST"] = "true"
        try:
            FeatureFlags.reset_config()
            assert FeatureFlags.is_enabled_for_user("test", "user123") is True
            assert FeatureFlags.is_enabled_for_user("test", "user456") is True
        finally:
            del os.environ["FEATURE_TEST"]
            FeatureFlags.reset_config()

    def test_is_enabled_for_user_percentage_rollout(self):
        """Test user-based percentage rollout."""
        os.environ["FEATURE_ROLLOUT_GRADUAL"] = "0.5"
        try:
            FeatureFlags.reset_config()
            # Test with multiple users - some should be enabled, some not
            results = [
                FeatureFlags.is_enabled_for_user("gradual", f"user{i}")
                for i in range(100)
            ]
            enabled_count = sum(results)
            # With 50% rollout, expect roughly 50 enabled (allow some variance)
            assert 30 < enabled_count < 70, f"Got {enabled_count} enabled users"
        finally:
            del os.environ["FEATURE_ROLLOUT_GRADUAL"]
            FeatureFlags.reset_config()

    def test_is_enabled_for_user_consistent_hashing(self):
        """Test that same user always gets same result."""
        os.environ["FEATURE_ROLLOUT_CONSISTENT"] = "0.5"
        try:
            FeatureFlags.reset_config()
            user_id = "user123"

            # Check multiple times - should always be the same
            result1 = FeatureFlags.is_enabled_for_user("consistent", user_id)
            result2 = FeatureFlags.is_enabled_for_user("consistent", user_id)
            result3 = FeatureFlags.is_enabled_for_user("consistent", user_id)

            assert result1 == result2 == result3
        finally:
            del os.environ["FEATURE_ROLLOUT_CONSISTENT"]
            FeatureFlags.reset_config()

    def test_is_enabled_for_percentage(self):
        """Test percentage-based flag."""
        # 0% should never be enabled
        assert FeatureFlags.is_enabled_for_percentage("test", 0.0) is False

        # 100% should always be enabled
        assert FeatureFlags.is_enabled_for_percentage("test", 1.0) is True

        # Test distribution with 50%
        results = [
            FeatureFlags.is_enabled_for_percentage("test", 0.5, seed=str(i))
            for i in range(100)
        ]
        enabled_count = sum(results)
        # Expect roughly 50% (allow variance)
        assert 30 < enabled_count < 70

    def test_get_rollout_percentage(self):
        """Test getting configured rollout percentage."""
        os.environ["FEATURE_ROLLOUT_TEST"] = "0.3"
        try:
            FeatureFlags.reset_config()
            assert FeatureFlags.get_rollout_percentage("test") == 0.3
        finally:
            del os.environ["FEATURE_ROLLOUT_TEST"]
            FeatureFlags.reset_config()

    def test_hash_consistency(self):
        """Test that hash function is consistent."""
        hash1 = FeatureFlags._hash_for_percentage("flag1", "user1")
        hash2 = FeatureFlags._hash_for_percentage("flag1", "user1")
        assert hash1 == hash2

        # Different inputs should give different hashes (usually)
        hash3 = FeatureFlags._hash_for_percentage("flag2", "user1")
        hash4 = FeatureFlags._hash_for_percentage("flag1", "user2")
        # While technically possible for these to be equal, it's extremely unlikely
        assert hash1 != hash3 or hash1 != hash4

    def test_hash_range(self):
        """Test that hash values are in valid range [0, 1]."""
        for i in range(100):
            hash_val = FeatureFlags._hash_for_percentage(f"flag{i}", f"user{i}")
            assert 0.0 <= hash_val <= 1.0
