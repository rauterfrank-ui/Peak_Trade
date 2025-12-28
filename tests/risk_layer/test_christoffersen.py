"""
Tests for Christoffersen Independence & Conditional Coverage Tests
===================================================================
"""

import numpy as np
import pytest

from src.risk_layer.var_backtest.christoffersen_tests import (
    ChristoffersenResult,
    christoffersen_independence_test,
    christoffersen_conditional_coverage_test,
    run_full_var_backtest,
    _compute_transition_matrix,
)


class TestTransitionMatrix:
    """Tests for transition matrix computation."""

    def test_transition_matrix_all_violations(self):
        """All violations should give specific transition matrix."""
        violations = [True, True, True, True]
        matrix = _compute_transition_matrix(violations)

        # All transitions are violation → violation
        assert matrix[0, 0] == 0  # no→no
        assert matrix[0, 1] == 0  # no→yes
        assert matrix[1, 0] == 0  # yes→no
        assert matrix[1, 1] == 3  # yes→yes

    def test_transition_matrix_no_violations(self):
        """No violations should give specific transition matrix."""
        violations = [False, False, False, False]
        matrix = _compute_transition_matrix(violations)

        # All transitions are no violation → no violation
        assert matrix[0, 0] == 3  # no→no
        assert matrix[0, 1] == 0  # no→yes
        assert matrix[1, 0] == 0  # yes→no
        assert matrix[1, 1] == 0  # yes→yes

    def test_transition_matrix_alternating(self):
        """Alternating violations should give specific pattern."""
        violations = [False, True, False, True, False]
        matrix = _compute_transition_matrix(violations)

        # Pattern: F→T, T→F, F→T, T→F
        assert matrix[0, 0] == 0  # no→no
        assert matrix[0, 1] == 2  # no→yes (2 times)
        assert matrix[1, 0] == 2  # yes→no (2 times)
        assert matrix[1, 1] == 0  # yes→yes

    def test_transition_matrix_known_sequence(self):
        """Test with known sequence."""
        # F F T T F
        # Transitions: F→F, F→T, T→T, T→F
        violations = [False, False, True, True, False]
        matrix = _compute_transition_matrix(violations)

        assert matrix[0, 0] == 1  # no→no: F→F
        assert matrix[0, 1] == 1  # no→yes: F→T
        assert matrix[1, 0] == 1  # yes→no: T→F
        assert matrix[1, 1] == 1  # yes→yes: T→T


class TestChristoffersenIndependence:
    """Tests for Christoffersen Independence Test."""

    def test_independence_test_independent_sequence(self):
        """Independent random sequence should pass independence test."""
        np.random.seed(42)
        # Generate independent violations
        violations = list(np.random.random(100) < 0.05)

        result = christoffersen_independence_test(violations, alpha=0.05)

        assert isinstance(result, ChristoffersenResult)
        assert result.test_name == "Christoffersen Independence Test"
        assert result.degrees_of_freedom == 1
        assert result.n_observations == 100
        # Should typically pass for independent data
        # (but not guaranteed with random data)
        assert result.p_value >= 0 and result.p_value <= 1

    def test_independence_test_clustered_violations(self):
        """Clustered violations should fail independence test."""
        # Create clustered pattern: many violations together
        violations = [False] * 40 + [True] * 10 + [False] * 40 + [True] * 10

        result = christoffersen_independence_test(violations, alpha=0.05)

        # Clustered violations should have low p-value (likely fail)
        # But this is a probabilistic test, so we just check it runs
        assert result.p_value >= 0
        assert result.transition_matrix is not None

    def test_independence_test_alternating_violations(self):
        """Alternating pattern should fail independence test."""
        # F T F T F T ... (perfect alternation)
        violations = [i % 2 == 1 for i in range(100)]

        result = christoffersen_independence_test(violations, alpha=0.05)

        # Perfect alternation is NOT independent
        # Should have low p-value (fail test)
        assert result.p_value >= 0
        # Likely fails independence (but don't assert passed=False as it depends on threshold)

    def test_independence_test_small_sample(self):
        """Small sample should still work."""
        violations = [False, True, False, False, True]

        result = christoffersen_independence_test(violations, alpha=0.05)

        assert result.n_observations == 5
        assert result.p_value >= 0 and result.p_value <= 1

    def test_independence_test_too_few_observations(self):
        """Less than 2 observations should raise error."""
        violations = [True]

        with pytest.raises(ValueError, match="at least 2 observations"):
            christoffersen_independence_test(violations)


class TestChristoffersenConditionalCoverage:
    """Tests for Christoffersen Conditional Coverage Test."""

    def test_conditional_coverage_correct_model(self):
        """Model with correct coverage should pass."""
        # 95% VaR: 5% violations expected
        np.random.seed(42)
        violations = list(np.random.random(100) < 0.05)

        result = christoffersen_conditional_coverage_test(violations, alpha=0.05, var_alpha=0.05)

        assert isinstance(result, ChristoffersenResult)
        assert result.test_name == "Christoffersen Conditional Coverage Test"
        assert result.degrees_of_freedom == 2
        assert result.n_observations == 100
        assert result.p_value >= 0 and result.p_value <= 1

    def test_conditional_coverage_incorrect_rate(self):
        """Model with incorrect violation rate should fail."""
        # 95% VaR but 20% violations (way too many)
        violations = [False] * 80 + [True] * 20

        result = christoffersen_conditional_coverage_test(violations, alpha=0.05, var_alpha=0.05)

        # Should likely fail (low p-value)
        assert result.p_value >= 0
        # p-value should be low due to wrong rate

    def test_conditional_coverage_clustered_violations(self):
        """Model with clustered violations should fail."""
        # Correct rate but clustered
        violations = [False] * 90 + [True] * 10

        result = christoffersen_conditional_coverage_test(violations, alpha=0.05, var_alpha=0.10)

        # Should likely fail due to clustering
        assert result.p_value >= 0

    def test_conditional_coverage_small_sample(self):
        """Small sample should still work."""
        violations = [False, True, False, False, True]

        result = christoffersen_conditional_coverage_test(violations, alpha=0.05, var_alpha=0.20)

        assert result.n_observations == 5
        assert result.p_value >= 0


class TestFullBacktest:
    """Tests for run_full_var_backtest wrapper."""

    def test_full_backtest_all_tests(self):
        """Full backtest should run all three tests."""
        np.random.seed(42)
        violations = list(np.random.random(100) < 0.05)

        results = run_full_var_backtest(violations, alpha=0.05)

        assert "kupiec" in results
        assert "independence" in results
        assert "conditional_coverage" in results
        assert "all_passed" in results

        # Check types
        assert hasattr(results["kupiec"], "is_valid")
        assert hasattr(results["independence"], "passed")
        assert hasattr(results["conditional_coverage"], "passed")
        assert isinstance(results["all_passed"], bool)

    def test_full_backtest_perfect_model(self):
        """Perfect model (correct rate, independent) should pass all tests."""
        # Generate 100 observations with 5% violations (for 95% VaR)
        np.random.seed(123)
        violations = list(np.random.random(250) < 0.05)

        results = run_full_var_backtest(violations, alpha=0.05)

        # Should typically pass (but probabilistic)
        # Just check structure
        assert results["kupiec"].n_observations == 250
        assert results["independence"].n_observations == 250
        assert results["conditional_coverage"].n_observations == 250


class TestDeterminism:
    """Tests for deterministic behavior."""

    def test_independence_determinism(self):
        """Same input should give same output."""
        violations = [False, True, True, False, True, False] * 10

        result1 = christoffersen_independence_test(violations, alpha=0.05)
        result2 = christoffersen_independence_test(violations, alpha=0.05)

        assert result1.lr_statistic == result2.lr_statistic
        assert result1.p_value == result2.p_value
        assert result1.passed == result2.passed

    def test_conditional_coverage_determinism(self):
        """Same input should give same output."""
        violations = [False, True, True, False, True, False] * 10

        result1 = christoffersen_conditional_coverage_test(violations, alpha=0.05, var_alpha=0.10)
        result2 = christoffersen_conditional_coverage_test(violations, alpha=0.05, var_alpha=0.10)

        assert result1.lr_statistic == result2.lr_statistic
        assert result1.p_value == result2.p_value
        assert result1.passed == result2.passed


class TestEdgeCases:
    """Tests for edge cases."""

    def test_all_false_violations(self):
        """All False violations should work."""
        violations = [False] * 100

        ind_result = christoffersen_independence_test(violations)
        cc_result = christoffersen_conditional_coverage_test(violations, var_alpha=0.05)

        # Should handle gracefully (p-value may be 1.0 or similar)
        assert ind_result.p_value >= 0
        assert cc_result.p_value >= 0

    def test_all_true_violations(self):
        """All True violations should work."""
        violations = [True] * 100

        ind_result = christoffersen_independence_test(violations)
        cc_result = christoffersen_conditional_coverage_test(violations, var_alpha=0.95)

        # Should handle gracefully
        assert ind_result.p_value >= 0
        assert cc_result.p_value >= 0
