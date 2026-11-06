"""
Tests for Separation of Duties (SoD) Checker

Tests SoD validation logic.
"""

import pytest

from src.ai_orchestration import SoDChecker, SoDViolationError
from src.ai_orchestration.models import SoDResult


def test_sod_pass_different_models():
    """Test SoD passes when proposer != critic."""
    checker = SoDChecker()
    result = checker.check(
        proposer_model_id="gpt-5.2-pro",
        critic_model_id="deepseek-r1",
    )

    assert result.result == SoDResult.PASS
    assert result.proposer_model_id == "gpt-5.2-pro"
    assert result.critic_model_id == "deepseek-r1"
    assert "PASS" in result.reason


def test_sod_fail_same_models():
    """Test SoD fails when proposer == critic."""
    checker = SoDChecker()
    result = checker.check(
        proposer_model_id="gpt-5.2-pro",
        critic_model_id="gpt-5.2-pro",
    )

    assert result.result == SoDResult.FAIL
    assert "FAIL" in result.reason
    assert "different" in result.reason.lower() or "same" in result.reason.lower()


def test_sod_validate_raises_on_fail():
    """Test validate() raises exception on SoD failure."""
    checker = SoDChecker()

    with pytest.raises(SoDViolationError, match="FAIL"):
        checker.validate(
            proposer_model_id="gpt-5.2-pro",
            critic_model_id="gpt-5.2-pro",
        )


def test_sod_validate_passes():
    """Test validate() does not raise on SoD success."""
    checker = SoDChecker()

    # Should not raise
    checker.validate(
        proposer_model_id="gpt-5.2-pro",
        critic_model_id="deepseek-r1",
    )


def test_sod_provider_diversity_pass():
    """Test SoD with provider diversity enabled (different providers)."""
    checker = SoDChecker(enforce_provider_diversity=True)
    result = checker.check(
        proposer_model_id="gpt-5.2-pro",
        critic_model_id="deepseek-r1",
        proposer_provider="openai",
        critic_provider="deepseek",
    )

    assert result.result == SoDResult.PASS


def test_sod_provider_diversity_fail():
    """Test SoD with provider diversity enabled (same provider)."""
    checker = SoDChecker(enforce_provider_diversity=True)
    result = checker.check(
        proposer_model_id="gpt-5.2-pro",
        critic_model_id="o3-pro",
        proposer_provider="openai",
        critic_provider="openai",
    )

    assert result.result == SoDResult.FAIL
    assert "provider" in result.reason.lower()


def test_sod_check_has_timestamp():
    """Test that SoD check includes timestamp."""
    checker = SoDChecker()
    result = checker.check(
        proposer_model_id="gpt-5.2-pro",
        critic_model_id="deepseek-r1",
    )

    assert result.timestamp
    # Should be ISO8601 format
    assert "T" in result.timestamp
    assert "Z" in result.timestamp or "+" in result.timestamp
