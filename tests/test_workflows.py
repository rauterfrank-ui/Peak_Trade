"""
Tests for workflow automation components.
"""

import subprocess
from pathlib import Path

import pytest

from src.core.feature_flags import FeatureFlag, FeatureFlagManager, requires_feature


class TestFeatureFlags:
    """Test feature flag system."""

    def test_feature_flag_simple(self, tmp_path):
        """Test simple flag enabled/disabled."""
        config_file = tmp_path / "flags.json"
        config_file.write_text('{"enable_redis_cache": {"enabled": true}}')

        flags = FeatureFlagManager(config_path=config_file)
        assert flags.is_enabled(FeatureFlag.ENABLE_REDIS_CACHE) is True

    def test_feature_flag_disabled(self, tmp_path):
        """Test disabled flag."""
        config_file = tmp_path / "flags.json"
        config_file.write_text('{"enable_redis_cache": {"enabled": false}}')

        flags = FeatureFlagManager(config_path=config_file)
        assert flags.is_enabled(FeatureFlag.ENABLE_REDIS_CACHE) is False

    def test_feature_flag_override(self, tmp_path):
        """Test runtime override."""
        config_file = tmp_path / "flags.json"
        config_file.write_text('{"enable_ai_workflow": {"enabled": false}}')

        flags = FeatureFlagManager(config_path=config_file)
        assert flags.is_enabled(FeatureFlag.ENABLE_AI_WORKFLOW) is False

        # Override to enable
        flags.enable(FeatureFlag.ENABLE_AI_WORKFLOW)
        assert flags.is_enabled(FeatureFlag.ENABLE_AI_WORKFLOW) is True

        # Reset overrides
        flags.reset_overrides()
        assert flags.is_enabled(FeatureFlag.ENABLE_AI_WORKFLOW) is False

    def test_feature_flag_percentage(self, tmp_path):
        """Test percentage-based rollout."""
        config_file = tmp_path / "flags.json"
        config_file.write_text('{"enable_ai_workflow": {"enabled": true, "percentage": 50}}')

        flags = FeatureFlagManager(config_path=config_file)

        # With user_id, percentage logic applies
        result = flags.is_enabled(FeatureFlag.ENABLE_AI_WORKFLOW, user_id="test_user_123")
        assert isinstance(result, bool)

    def test_feature_flag_environment(self, tmp_path, monkeypatch):
        """Test environment-based rollout."""
        config_file = tmp_path / "flags.json"
        config_file.write_text(
            '{"enable_redis_cache": {"enabled": true, "environments": ["production", "staging"]}}'
        )

        flags = FeatureFlagManager(config_path=config_file)

        # Test with development environment (default)
        monkeypatch.setenv("ENVIRONMENT", "development")
        flags = FeatureFlagManager(config_path=config_file)
        assert flags.is_enabled(FeatureFlag.ENABLE_REDIS_CACHE) is False

        # Test with production environment
        monkeypatch.setenv("ENVIRONMENT", "production")
        flags = FeatureFlagManager(config_path=config_file)
        assert flags.is_enabled(FeatureFlag.ENABLE_REDIS_CACHE) is True

    def test_feature_flag_decorator(self, tmp_path):
        """Test requires_feature decorator."""
        config_file = tmp_path / "flags.json"
        config_file.write_text('{"enable_ai_workflow": {"enabled": true}}')

        # Temporarily set the global feature_flags config path
        from src.core import feature_flags as ff_module

        original_flags = ff_module.feature_flags
        ff_module.feature_flags = FeatureFlagManager(config_path=config_file)

        try:

            @requires_feature(FeatureFlag.ENABLE_AI_WORKFLOW)
            def test_function():
                return "success"

            assert test_function() == "success"

            # Disable the flag
            ff_module.feature_flags.disable(FeatureFlag.ENABLE_AI_WORKFLOW)

            with pytest.raises(RuntimeError, match="not enabled"):
                test_function()

        finally:
            # Restore original
            ff_module.feature_flags = original_flags

    def test_missing_config_file(self, tmp_path):
        """Test behavior with missing config file."""
        non_existent = tmp_path / "nonexistent.json"
        flags = FeatureFlagManager(config_path=non_existent)

        # Should default to disabled
        assert flags.is_enabled(FeatureFlag.ENABLE_REDIS_CACHE) is False


class TestCIPipeline:
    """Test CI pipeline components."""

    def test_ci_workflow_exists(self):
        """Verify CI workflow file exists."""
        assert Path(".github/workflows/ci.yml").exists()

    def test_pre_commit_config_exists(self):
        """Verify pre-commit config exists."""
        assert Path(".pre-commit-config.yaml").exists()

    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml exists."""
        assert Path("pyproject.toml").exists()


class TestDocumentation:
    """Test documentation generation components."""

    def test_docs_directory_exists(self):
        """Verify docs directory exists."""
        assert Path("docs").exists()
