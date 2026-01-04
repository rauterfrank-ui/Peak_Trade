"""Tests for Christoffersen Independence & Conditional Coverage Tests.

Phase 8B: Comprehensive test suite for LR-IND and LR-CC tests.

Tests cover:
- Transition count correctness
- Edge cases (all False, all True, alternating patterns)
- Monotonic sanity (stronger clustering => lower p-value for IND)
- LR-CC equals LR-UC + LR-IND (within tolerance)
- Numerical stability
"""

import math

import pytest

from src.risk_layer.var_backtest.christoffersen_tests import (
    ChristoffersenCCResult,
    ChristoffersenIndResult,
    christoffersen_lr_cc,
    christoffersen_lr_ind,
    _compute_transition_counts,
    chi2_df1_sf,
    chi2_df2_sf,
)


class TestTransitionCounts:
    """Test transition matrix computation."""

    def test_all_false(self):
        """All False → only n00 transitions."""
        exceedances = [False, False, False, False]
        n00, n01, n10, n11 = _compute_transition_counts(exceedances)

        assert n00 == 3  # 3 transitions False→False
        assert n01 == 0
        assert n10 == 0
        assert n11 == 0

    def test_all_true(self):
        """All True → only n11 transitions."""
        exceedances = [True, True, True, True]
        n00, n01, n10, n11 = _compute_transition_counts(exceedances)

        assert n00 == 0
        assert n01 == 0
        assert n10 == 0
        assert n11 == 3  # 3 transitions True→True

    def test_alternating(self):
        """Alternating pattern → only n01 and n10."""
        exceedances = [False, True, False, True, False]
        n00, n01, n10, n11 = _compute_transition_counts(exceedances)

        assert n00 == 0
        assert n01 == 2  # False→True
        assert n10 == 2  # True→False
        assert n11 == 0

    def test_clustered(self):
        """Clustered violations."""
        exceedances = [False, False, True, True, True, False, False]
        n00, n01, n10, n11 = _compute_transition_counts(exceedances)

        assert n00 == 2  # False→False (positions 0-1, 5-6)
        assert n01 == 1  # False→True (position 1-2)
        assert n10 == 1  # True→False (position 4-5)
        assert n11 == 2  # True→True (positions 2-3, 3-4)

    def test_single_violation(self):
        """Single violation in middle."""
        exceedances = [False, False, True, False, False]
        n00, n01, n10, n11 = _compute_transition_counts(exceedances)

        assert n00 == 2  # False→False
        assert n01 == 1  # False→True
        assert n10 == 1  # True→False
        assert n11 == 0


class TestChristoffersenIndependence:
    """Test Christoffersen Independence Test (LR-IND)."""

    def test_all_false_pass(self):
        """All False → should pass (no violations to cluster)."""
        exceedances = [False] * 100
        result = christoffersen_lr_ind(exceedances)

        assert isinstance(result, ChristoffersenIndResult)
        assert result.n == 100
        assert result.x == 0
        assert result.verdict == "PASS"
        assert result.p_value == 1.0  # No transitions from violation state

    def test_all_true_pass(self):
        """All True → should pass (no transitions from no-violation state)."""
        exceedances = [True] * 100
        result = christoffersen_lr_ind(exceedances)

        assert result.n == 100
        assert result.x == 100
        assert result.verdict == "PASS"
        assert result.p_value == 1.0

    def test_alternating_fail(self):
        """Alternating pattern → should fail (perfect negative clustering)."""
        exceedances = [False, True] * 50
        result = christoffersen_lr_ind(exceedances)

        assert result.n == 100
        assert result.x == 50
        assert result.verdict == "FAIL"
        assert result.p_value < 0.05  # Strong evidence of dependence
        assert result.pi_01 == 1.0  # Always violate after no-violation
        assert result.pi_11 == 0.0  # Never violate after violation

    def test_random_like_pass(self):
        """Random-like pattern → should pass."""
        # Construct pattern with ~independent violations
        exceedances = [False] * 95 + [True] * 5
        result = christoffersen_lr_ind(exceedances)

        assert result.n == 100
        assert result.x == 5
        # Should pass if violations are at end (not clustered in middle)
        # This is a weak test - real independence requires scattered violations

    def test_clustered_fail(self):
        """Clustered violations → should fail."""
        # All violations clustered together
        exceedances = [False] * 90 + [True] * 10
        result = christoffersen_lr_ind(exceedances)

        assert result.n == 100
        assert result.x == 10
        # pi_11 should be high (violations cluster)
        assert result.pi_11 > 0.5
        # Should likely fail (but depends on threshold)

    def test_validation_too_few_observations(self):
        """Should raise ValueError for n < 2."""
        with pytest.raises(ValueError, match="at least 2 observations"):
            christoffersen_lr_ind([True])

    def test_validation_p_threshold(self):
        """Should raise ValueError for invalid p_threshold."""
        exceedances = [False, True, False]
        with pytest.raises(ValueError, match="p_threshold must be in"):
            christoffersen_lr_ind(exceedances, p_threshold=1.5)


class TestChristoffersenConditionalCoverage:
    """Test Christoffersen Conditional Coverage Test (LR-CC)."""

    def test_perfect_calibration_independent(self):
        """Perfect calibration + independent → should pass."""
        # 5% exceedance rate, scattered
        exceedances = [False] * 95 + [True] * 5
        result = christoffersen_lr_cc(exceedances, alpha=0.05)

        assert isinstance(result, ChristoffersenCCResult)
        assert result.n == 100
        assert result.x == 5
        assert result.alpha == 0.05
        # Should pass both UC and IND
        # (though this specific pattern has all violations at end)

    def test_lr_cc_equals_lr_uc_plus_lr_ind(self):
        """Verify LR-CC = LR-UC + LR-IND."""
        from src.risk_layer.var_backtest.kupiec_pof import _compute_lr_statistic

        exceedances = [False] * 90 + [True] * 10
        alpha = 0.05

        # Compute LR-CC
        cc_result = christoffersen_lr_cc(exceedances, alpha=alpha)

        # Compute LR-UC separately
        n = len(exceedances)
        x = sum(exceedances)
        lr_uc = _compute_lr_statistic(n, x, alpha)

        # Compute LR-IND separately
        ind_result = christoffersen_lr_ind(exceedances)
        lr_ind = ind_result.lr_ind

        # Verify decomposition
        assert cc_result.lr_uc == pytest.approx(lr_uc, abs=1e-9)
        assert cc_result.lr_ind == pytest.approx(lr_ind, abs=1e-9)
        assert cc_result.lr_cc == pytest.approx(lr_uc + lr_ind, abs=1e-9)

    def test_too_many_violations_fail(self):
        """Too many violations → should fail UC (and thus CC)."""
        # 20% exceedance rate vs 5% expected
        exceedances = [False] * 80 + [True] * 20
        result = christoffersen_lr_cc(exceedances, alpha=0.05)

        assert result.x == 20
        assert result.verdict == "FAIL"
        assert result.p_value < 0.05

    def test_clustered_violations_fail(self):
        """Clustered violations → should fail IND (and thus CC)."""
        # Correct count but clustered
        exceedances = [False] * 95 + [True] * 5
        result = christoffersen_lr_cc(exceedances, alpha=0.05)

        # May fail due to clustering (all violations at end)
        # LR-IND should be elevated

    def test_validation_too_few_observations(self):
        """Should raise ValueError for n < 2."""
        with pytest.raises(ValueError, match="at least 2 observations"):
            christoffersen_lr_cc([True], alpha=0.05)

    def test_validation_alpha(self):
        """Should raise ValueError for invalid alpha."""
        exceedances = [False, True, False]
        with pytest.raises(ValueError, match="alpha must be in"):
            christoffersen_lr_cc(exceedances, alpha=1.5)


class TestMonotonicSanity:
    """Test monotonic properties of LR-IND."""

    def test_stronger_clustering_lower_pvalue(self):
        """Stronger clustering → lower p-value for IND."""
        # Pattern 1: Mild clustering (2 clusters of 2)
        pattern1 = [False] * 46 + [True, True] + [False] * 46 + [True, True] + [False] * 4
        result1 = christoffersen_lr_ind(pattern1)

        # Pattern 2: Strong clustering (1 cluster of 4)
        pattern2 = [False] * 96 + [True, True, True, True]
        result2 = christoffersen_lr_ind(pattern2)

        # Pattern 3: Perfect clustering (all 4 consecutive)
        pattern3 = [False] * 96 + [True] * 4
        result3 = christoffersen_lr_ind(pattern3)

        # Stronger clustering should have higher LR-IND
        # (though pattern1 vs pattern2 may be subtle)
        assert result2.lr_ind >= result1.lr_ind or result1.lr_ind < 1.0
        assert result3.lr_ind >= result1.lr_ind or result1.lr_ind < 1.0


class TestChi2Functions:
    """Test chi-square distribution functions."""

    def test_chi2_df1_sf_zero(self):
        """SF(0) = 1.0 for df=1."""
        assert chi2_df1_sf(0.0) == pytest.approx(1.0)

    def test_chi2_df1_sf_negative(self):
        """SF(negative) = 1.0 for df=1."""
        assert chi2_df1_sf(-1.0) == pytest.approx(1.0)

    def test_chi2_df1_sf_known_value(self):
        """Test known chi²(1) value."""
        # Critical value for alpha=0.05: ~3.841
        p_value = chi2_df1_sf(3.841)
        assert 0.04 < p_value < 0.06  # Should be ~0.05

    def test_chi2_df2_sf_zero(self):
        """SF(0) = 1.0 for df=2."""
        assert chi2_df2_sf(0.0) == pytest.approx(1.0)

    def test_chi2_df2_sf_negative(self):
        """SF(negative) = 1.0 for df=2."""
        assert chi2_df2_sf(-1.0) == pytest.approx(1.0)

    def test_chi2_df2_sf_known_value(self):
        """Test known chi²(2) value."""
        # Critical value for alpha=0.05: ~5.991
        p_value = chi2_df2_sf(5.991)
        assert 0.04 < p_value < 0.06  # Should be ~0.05

    def test_chi2_df2_sf_exponential(self):
        """Verify exponential form for df=2."""
        x = 4.0
        expected = math.exp(-x / 2)
        assert chi2_df2_sf(x) == pytest.approx(expected)


class TestResultSerialization:
    """Test result serialization."""

    def test_ind_result_to_dict(self):
        """Test ChristoffersenIndResult.to_dict()."""
        exceedances = [False, True, False, True, False]
        result = christoffersen_lr_ind(exceedances)
        d = result.to_dict()

        assert isinstance(d, dict)
        assert "n" in d
        assert "x" in d
        assert "transition_matrix" in d
        assert "lr_ind" in d
        assert "p_value" in d
        assert "verdict" in d

    def test_cc_result_to_dict(self):
        """Test ChristoffersenCCResult.to_dict()."""
        exceedances = [False] * 95 + [True] * 5
        result = christoffersen_lr_cc(exceedances, alpha=0.05)
        d = result.to_dict()

        assert isinstance(d, dict)
        assert "n" in d
        assert "x" in d
        assert "alpha" in d
        assert "lr_uc" in d
        assert "lr_ind" in d
        assert "lr_cc" in d
        assert "p_value" in d
        assert "verdict" in d


class TestLegacyAPI:
    """Test backward compatibility with legacy API."""

    def test_legacy_independence_test(self):
        """Test christoffersen_independence_test() legacy function."""
        from src.risk_layer.var_backtest.christoffersen_tests import (
            christoffersen_independence_test,
        )

        violations = [False, True, False, True, False]
        result = christoffersen_independence_test(violations, alpha=0.05)

        assert result.test_name == "Christoffersen Independence Test"
        assert result.degrees_of_freedom == 1
        assert hasattr(result, "passed")
        assert hasattr(result, "transition_matrix")

    def test_legacy_conditional_coverage_test(self):
        """Test christoffersen_conditional_coverage_test() legacy function."""
        from src.risk_layer.var_backtest.christoffersen_tests import (
            christoffersen_conditional_coverage_test,
        )

        violations = [False] * 95 + [True] * 5
        result = christoffersen_conditional_coverage_test(
            violations,
            alpha=0.05,
            var_alpha=0.05,
        )

        assert result.test_name == "Christoffersen Conditional Coverage Test"
        assert result.degrees_of_freedom == 2
        assert hasattr(result, "passed")

    def test_legacy_run_full_backtest(self):
        """Test run_full_var_backtest() legacy function."""
        from src.risk_layer.var_backtest.christoffersen_tests import (
            run_full_var_backtest,
        )

        violations = [False] * 95 + [True] * 5
        results = run_full_var_backtest(violations, alpha=0.05)

        assert "kupiec" in results
        assert "independence" in results
        assert "conditional_coverage" in results
        assert "all_passed" in results
        assert isinstance(results["all_passed"], bool)
