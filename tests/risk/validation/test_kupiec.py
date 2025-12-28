"""Tests for Kupiec POF test.

Tests cover:
- Edge cases (x=0, x=n, n=0)
- Typical cases
- Monotonicity
- p-value bounds
- Pure Python chi-square implementation
"""

import math

import pytest

from src.risk.validation.kupiec_pof import (
    KupiecResult,
    kupiec_pof_test,
    kupiec_lr_statistic,
    chi2_p_value,
)


class TestKupiecPOFEdgeCases:
    """Test edge cases for Kupiec POF test."""

    def test_no_breaches(self):
        """Test with x=0 (no breaches)."""
        result = kupiec_pof_test(breaches=0, observations=250, confidence_level=0.99)

        assert result.breaches == 0
        assert result.observations == 250
        assert result.expected_breaches == pytest.approx(2.5, abs=0.01)
        assert 0 <= result.p_value <= 1
        assert result.test_statistic >= 0

    def test_all_breaches(self):
        """Test with x=n (all breaches)."""
        result = kupiec_pof_test(breaches=250, observations=250, confidence_level=0.99)

        assert result.breaches == 250
        assert result.observations == 250
        assert result.p_value < 0.05  # Should reject
        assert not result.is_valid

    def test_zero_observations(self):
        """Test with n=0 (no observations)."""
        result = kupiec_pof_test(breaches=0, observations=0, confidence_level=0.99)

        assert result.breaches == 0
        assert result.observations == 0
        assert math.isnan(result.p_value)
        assert not result.is_valid


class TestKupiecPOFTypicalCases:
    """Test typical cases."""

    def test_perfect_calibration_99_var(self):
        """Test 99% VaR with perfect calibration (1% breach rate)."""
        # 2.5 expected breaches for 250 observations, 99% VaR
        # 2-3 breaches should be acceptable
        result = kupiec_pof_test(breaches=3, observations=250, confidence_level=0.99)

        assert result.is_valid  # Should accept
        assert result.p_value > 0.05

    def test_perfect_calibration_95_var(self):
        """Test 95% VaR with perfect calibration (5% breach rate)."""
        # 12.5 expected breaches for 250 observations, 95% VaR
        # 12-13 breaches should be acceptable
        result = kupiec_pof_test(breaches=13, observations=250, confidence_level=0.95)

        assert result.is_valid  # Should accept
        assert result.p_value > 0.05

    def test_too_many_breaches(self):
        """Test with too many breaches (model under-estimates risk)."""
        # 2.5 expected for 99% VaR, but 20 observed
        result = kupiec_pof_test(breaches=20, observations=250, confidence_level=0.99)

        assert not result.is_valid  # Should reject
        assert result.p_value < 0.05


class TestKupiecPOFMonotonicity:
    """Test monotonicity properties."""

    def test_lr_statistic_increases_with_deviation(self):
        """LR statistic should increase as breach count deviates from expected."""
        # Expected: 2.5 breaches
        lr_2 = kupiec_pof_test(2, 250, 0.99).test_statistic
        lr_5 = kupiec_pof_test(5, 250, 0.99).test_statistic
        lr_10 = kupiec_pof_test(10, 250, 0.99).test_statistic

        assert lr_5 > lr_2
        assert lr_10 > lr_5

    def test_p_value_decreases_with_deviation(self):
        """p-value should decrease as breach count deviates from expected."""
        # Expected: 2.5 breaches
        p_2 = kupiec_pof_test(2, 250, 0.99).p_value
        p_5 = kupiec_pof_test(5, 250, 0.99).p_value
        p_10 = kupiec_pof_test(10, 250, 0.99).p_value

        assert p_5 < p_2
        assert p_10 < p_5


class TestKupiecPOFBounds:
    """Test bounds and invariants."""

    def test_p_value_bounds(self):
        """p-value should always be in [0, 1]."""
        for breaches in [0, 1, 5, 10, 50, 100, 250]:
            result = kupiec_pof_test(breaches, 250, 0.99)
            if not math.isnan(result.p_value):
                assert 0 <= result.p_value <= 1

    def test_lr_statistic_non_negative(self):
        """LR statistic should always be non-negative."""
        for breaches in [0, 1, 5, 10, 50, 100, 250]:
            result = kupiec_pof_test(breaches, 250, 0.99)
            if not math.isnan(result.test_statistic):
                assert result.test_statistic >= 0


class TestChi2PValue:
    """Test pure Python chi-square p-value computation."""

    def test_chi2_p_value_zero(self):
        """p-value for lr=0 should be 1.0."""
        assert chi2_p_value(0.0) == pytest.approx(1.0)

    def test_chi2_p_value_negative(self):
        """p-value for negative lr should be 1.0."""
        assert chi2_p_value(-1.0) == pytest.approx(1.0)

    def test_chi2_p_value_known_values(self):
        """Test known chi-square(df=1) values."""
        # Critical value for alpha=0.05: ~3.841
        p_value = chi2_p_value(3.841)
        assert 0.04 < p_value < 0.06  # Should be ~0.05

        # Large LR should give small p-value
        p_value = chi2_p_value(100.0)
        assert p_value < 0.001

    def test_chi2_p_value_bounds(self):
        """p-value should be in [0, 1]."""
        for lr in [0.0, 0.1, 1.0, 3.841, 10.0, 100.0]:
            p_value = chi2_p_value(lr)
            assert 0 <= p_value <= 1


class TestKupiecLRStatistic:
    """Test LR statistic computation."""

    def test_lr_zero_breaches(self):
        """LR for x=0 should be positive."""
        lr = kupiec_lr_statistic(0, 250, 0.01)
        assert lr > 0

    def test_lr_all_breaches(self):
        """LR for x=n should be positive."""
        lr = kupiec_lr_statistic(250, 250, 0.01)
        assert lr > 0

    def test_lr_perfect_match(self):
        """LR should be small when phat = p."""
        # If 2.5 expected and 2.5 observed (can't have 0.5, use 2 or 3)
        lr_2 = kupiec_lr_statistic(2, 250, 0.01)
        lr_3 = kupiec_lr_statistic(3, 250, 0.01)

        # Both should be small (close to perfect calibration)
        assert lr_2 < 1.0
        assert lr_3 < 1.0


class TestKupiecResultSerialization:
    """Test result serialization."""

    def test_to_json_dict(self):
        """Test JSON serialization."""
        result = kupiec_pof_test(5, 250, 0.99)
        json_dict = result.to_json_dict()

        assert isinstance(json_dict, dict)
        assert "p_value" in json_dict
        assert "test_statistic" in json_dict
        assert "breaches" in json_dict
        assert "observations" in json_dict
        assert "is_valid" in json_dict
        assert "breach_rate" in json_dict

    def test_to_markdown(self):
        """Test markdown report generation."""
        result = kupiec_pof_test(5, 250, 0.99)
        markdown = result.to_markdown()

        assert isinstance(markdown, str)
        assert "Kupiec POF Test" in markdown
        assert str(result.breaches) in markdown
        assert str(result.observations) in markdown
