"""
Christoffersen Independence & Conditional Coverage Tests
=========================================================

Statistical tests for VaR model validation, focusing on independence
of violations and conditional coverage.

Agent A3 Implementation: Full Christoffersen tests with optional scipy.

References:
-----------
- Christoffersen, P. F. (1998). Evaluating Interval Forecasts.
  International Economic Review, 39(4), 841-862.
- Christoffersen, P. F. (2012). Elements of Financial Risk Management (2nd ed.).

Tests:
------
1. Independence Test (LR_ind):
   - H0: Violations are independent (no clustering)
   - Tests for serial independence of violations
   - LR_ind ~ χ²(1)

2. Conditional Coverage Test (LR_cc):
   - H0: Model has correct unconditional coverage AND violations are independent
   - Combines Kupiec POF + Independence Test
   - LR_cc ~ χ²(2)
"""

import logging
import math
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Optional scipy import
try:
    from scipy.stats import chi2 as scipy_chi2

    SCIPY_AVAILABLE = True
except ImportError:
    scipy_chi2 = None
    SCIPY_AVAILABLE = False
    logger.debug("scipy not available. Using math-based chi2 fallbacks.")

# Epsilon for numerical stability
EPS = 1e-12


@dataclass
class ChristoffersenResult:
    """
    Result of a Christoffersen test.

    Attributes:
        test_name: Name of the test (Independence or Conditional Coverage)
        lr_statistic: Likelihood Ratio test statistic
        p_value: p-value of the test
        passed: Whether the test passed (p_value > significance level)
        critical_value: Critical value (chi-squared)
        degrees_of_freedom: Degrees of freedom for chi-squared distribution
        n_violations: Number of violations
        n_observations: Total number of observations
        transition_matrix: 2x2 transition matrix (for Independence Test)
    """

    test_name: str
    lr_statistic: float
    p_value: float
    passed: bool
    critical_value: float
    degrees_of_freedom: int
    n_violations: int
    n_observations: int
    transition_matrix: Optional[np.ndarray] = None

    def __repr__(self) -> str:
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return (
            f"<{self.test_name}: LR={self.lr_statistic:.4f}, "
            f"p={self.p_value:.4f}, {status}>"
        )


def christoffersen_independence_test(
    violations: List[bool], alpha: float = 0.05
) -> ChristoffersenResult:
    """
    Christoffersen Independence Test (LR_ind).

    Tests the null hypothesis that VaR violations are independent over time.
    Rejection indicates violations are clustered (model is mis-specified).

    Args:
        violations: Boolean list of violations (True = violation, False = no violation)
        alpha: Significance level for the test (default: 0.05)

    Returns:
        ChristoffersenResult with test statistics

    Theory:
    -------
    The test computes a 2x2 transition matrix:
        T = [[n00, n01],
             [n10, n11]]
    where:
        n00 = # of (no violation → no violation)
        n01 = # of (no violation → violation)
        n10 = # of (violation → no violation)
        n11 = # of (violation → violation)

    Likelihood Ratio statistic:
        LR_ind = -2 * ln(L_restricted / L_unrestricted)
        ~ χ²(1) under H0

    H0: Violations are independent (π₀₁ = π₁₁ = π)
    H1: Violations are NOT independent (π₀₁ ≠ π₁₁)

    Example:
        >>> violations = [False, False, True, False, True, True, False]
        >>> result = christoffersen_independence_test(violations)
        >>> print(result.passed)
    """
    if len(violations) < 2:
        raise ValueError("Need at least 2 observations for independence test")

    # Compute transition matrix
    transition_matrix = _compute_transition_matrix(violations)
    n00, n01 = transition_matrix[0]
    n10, n11 = transition_matrix[1]

    T = len(violations)
    N = sum(violations)

    # Calculate transition probabilities
    # π₀₁ = P(violation_t | no_violation_{t-1})
    # π₁₁ = P(violation_t | violation_{t-1})
    n0 = n00 + n01  # Total transitions from no-violation
    n1 = n10 + n11  # Total transitions from violation

    # Handle edge cases
    if n0 == 0 or n1 == 0:
        # Not enough data for independence test
        lr_statistic = 0.0
        p_value = 1.0
    else:
        pi_01 = n01 / n0 if n0 > 0 else 0.0
        pi_11 = n11 / n1 if n1 > 0 else 0.0

        # Unconditional probability (under H0)
        pi = N / T if T > 0 else 0.0

        # Compute LR statistic
        lr_statistic = _compute_independence_lr(n00, n01, n10, n11, pi_01, pi_11, pi)
        p_value = chi2_sf(lr_statistic, df=1)

    # Critical value for chi2(1)
    critical_value = chi2_ppf(1 - alpha, df=1)

    # Test decision
    passed = p_value > alpha

    return ChristoffersenResult(
        test_name="Christoffersen Independence Test",
        lr_statistic=lr_statistic,
        p_value=p_value,
        passed=passed,
        critical_value=critical_value,
        degrees_of_freedom=1,
        n_violations=N,
        n_observations=T,
        transition_matrix=transition_matrix,
    )


def christoffersen_conditional_coverage_test(
    violations: List[bool], alpha: float = 0.05, var_alpha: float = 0.05
) -> ChristoffersenResult:
    """
    Christoffersen Conditional Coverage Test (LR_cc).

    Tests the joint hypothesis of:
    1. Correct unconditional coverage (Kupiec POF)
    2. Independence of violations (Christoffersen Independence)

    Args:
        violations: Boolean list of violations (True = violation, False = no violation)
        alpha: Significance level for the test (default: 0.05)
        var_alpha: VaR significance level (e.g., 0.05 for 95% VaR)

    Returns:
        ChristoffersenResult with test statistics

    Theory:
    -------
    LR_cc = LR_uc + LR_ind
    where:
        LR_uc = Kupiec POF test statistic (unconditional coverage)
        LR_ind = Independence test statistic

    LR_cc ~ χ²(2) under H0

    H0: Model has correct coverage AND violations are independent
    H1: Model fails on coverage OR independence (or both)

    Example:
        >>> violations = [False] * 95 + [True] * 5
        >>> result = christoffersen_conditional_coverage_test(violations, var_alpha=0.05)
        >>> print(result.passed)
    """
    if len(violations) < 2:
        raise ValueError("Need at least 2 observations for conditional coverage test")

    T = len(violations)
    N = sum(violations)

    # 1. Compute Kupiec POF LR statistic (LR_uc)
    from src.risk_layer.var_backtest.kupiec_pof import _compute_lr_statistic

    p_star = var_alpha  # Expected violation rate
    lr_uc = _compute_lr_statistic(T, N, p_star)

    # 2. Compute Independence LR statistic (LR_ind)
    independence_result = christoffersen_independence_test(violations, alpha=alpha)
    lr_ind = independence_result.lr_statistic

    # 3. Conditional Coverage LR statistic
    lr_cc = lr_uc + lr_ind

    # p-value from χ²(2)
    p_value = chi2_sf(lr_cc, df=2)

    # Critical value for chi2(2)
    critical_value = chi2_ppf(1 - alpha, df=2)

    # Test decision
    passed = p_value > alpha

    return ChristoffersenResult(
        test_name="Christoffersen Conditional Coverage Test",
        lr_statistic=lr_cc,
        p_value=p_value,
        passed=passed,
        critical_value=critical_value,
        degrees_of_freedom=2,
        n_violations=N,
        n_observations=T,
        transition_matrix=independence_result.transition_matrix,
    )


def _compute_transition_matrix(violations: List[bool]) -> np.ndarray:
    """
    Compute 2x2 transition matrix for violations.

    Args:
        violations: Boolean list of violations

    Returns:
        2x2 numpy array: [[n00, n01], [n10, n11]]

    where:
        n00 = # of (no violation → no violation)
        n01 = # of (no violation → violation)
        n10 = # of (violation → no violation)
        n11 = # of (violation → violation)
    """
    n00 = n01 = n10 = n11 = 0

    for i in range(len(violations) - 1):
        curr = violations[i]
        next_val = violations[i + 1]

        if not curr and not next_val:
            n00 += 1
        elif not curr and next_val:
            n01 += 1
        elif curr and not next_val:
            n10 += 1
        elif curr and next_val:
            n11 += 1

    return np.array([[n00, n01], [n10, n11]], dtype=int)


def _compute_independence_lr(
    n00: int, n01: int, n10: int, n11: int, pi_01: float, pi_11: float, pi: float
) -> float:
    """
    Compute Likelihood Ratio statistic for Independence Test.

    Args:
        n00, n01, n10, n11: Transition matrix counts
        pi_01: P(violation | no violation)
        pi_11: P(violation | violation)
        pi: Unconditional violation probability

    Returns:
        LR_ind statistic
    """
    # Avoid log(0)
    if pi <= EPS or pi >= 1 - EPS:
        return 0.0

    if pi_01 < EPS:
        pi_01 = EPS
    if pi_11 < EPS:
        pi_11 = EPS
    if pi_01 > 1 - EPS:
        pi_01 = 1 - EPS
    if pi_11 > 1 - EPS:
        pi_11 = 1 - EPS

    # Restricted likelihood (H0: π₀₁ = π₁₁ = π)
    log_L_restricted = (
        (n00 + n10) * math.log(1 - pi) + (n01 + n11) * math.log(pi)
    )

    # Unrestricted likelihood (H1: π₀₁ ≠ π₁₁)
    log_L_unrestricted = 0.0
    if n00 + n01 > 0:
        log_L_unrestricted += n00 * math.log(1 - pi_01) + n01 * math.log(pi_01)
    if n10 + n11 > 0:
        log_L_unrestricted += n10 * math.log(1 - pi_11) + n11 * math.log(pi_11)

    # LR statistic
    lr = -2 * (log_L_restricted - log_L_unrestricted)

    return max(0.0, lr)  # Can't be negative


# ============================================================================
# Chi-Square Distribution Functions (with optional scipy fallback)
# ============================================================================


def chi2_sf(x: float, df: int) -> float:
    """
    Chi-square survival function (1 - CDF).

    Args:
        x: Chi-square statistic (non-negative)
        df: Degrees of freedom (1 or 2)

    Returns:
        Survival function value (p-value)
    """
    if SCIPY_AVAILABLE:
        return float(scipy_chi2.sf(x, df))

    # Fallback implementation
    if df == 1:
        return chi2_df1_sf(x)
    elif df == 2:
        return chi2_df2_sf(x)
    else:
        raise ValueError(f"Fallback only supports df=1 or df=2, got df={df}")


def chi2_ppf(p: float, df: int) -> float:
    """
    Chi-square percent point function (inverse CDF).

    Args:
        p: Probability (must be in (0, 1))
        df: Degrees of freedom (1 or 2)

    Returns:
        Critical value x where CDF(x) = p
    """
    if SCIPY_AVAILABLE:
        return float(scipy_chi2.ppf(p, df))

    # Fallback implementation
    if df == 1:
        return chi2_df1_ppf(p)
    elif df == 2:
        return chi2_df2_ppf(p)
    else:
        raise ValueError(f"Fallback only supports df=1 or df=2, got df={df}")


# ============================================================================
# Chi-Square df=1 (from kupiec_pof.py)
# ============================================================================


def chi2_df1_sf(x: float) -> float:
    """Chi-square survival function for df=1."""
    if x < 0:
        return 1.0
    if x == 0:
        return 1.0
    return math.erfc(math.sqrt(x / 2))


def chi2_df1_ppf(p: float) -> float:
    """Chi-square percent point function for df=1."""
    from src.risk_layer.var_backtest.kupiec_pof import chi2_df1_ppf as kupiec_ppf

    return kupiec_ppf(p)


# ============================================================================
# Chi-Square df=2 (Agent A3 Implementation)
# ============================================================================


def chi2_df2_sf(x: float) -> float:
    """
    Chi-square survival function for df=2.

    For df=2, the chi-square distribution is exponential:
    CDF(x) = 1 - exp(-x/2)
    SF(x) = exp(-x/2)

    Args:
        x: Chi-square statistic (non-negative)

    Returns:
        Survival function value
    """
    if x < 0:
        return 1.0
    if x == 0:
        return 1.0
    return math.exp(-x / 2)


def chi2_df2_ppf(p: float) -> float:
    """
    Chi-square percent point function for df=2.

    For df=2:
    CDF(x) = 1 - exp(-x/2)
    Inverse: x = -2 * ln(1 - p)

    Args:
        p: Probability (must be in (0, 1))

    Returns:
        Critical value x where CDF(x) = p
    """
    if not 0 < p < 1:
        raise ValueError(f"p must be in (0, 1), got {p}")

    if p < 1e-10:
        return 0.0
    if p > 1 - 1e-10:
        return 100.0  # Large value

    return -2 * math.log(1 - p)


# ============================================================================
# Convenience Functions
# ============================================================================


def run_full_var_backtest(violations: List[bool], alpha: float = 0.05) -> dict:
    """
    Run full VaR backtest suite (Kupiec + Christoffersen).

    Convenience wrapper that runs all three tests:
    - Kupiec POF (unconditional coverage)
    - Christoffersen Independence
    - Christoffersen Conditional Coverage

    Args:
        violations: Boolean list of violations
        alpha: VaR significance level (default: 0.05 for 95% VaR)

    Returns:
        Dictionary with all test results:
        {
            "kupiec": KupiecResult,
            "independence": ChristoffersenResult,
            "conditional_coverage": ChristoffersenResult,
            "all_passed": bool
        }

    Example:
        >>> results = run_full_var_backtest(violations, alpha=0.05)
        >>> if results["all_passed"]:
        ...     print("✅ VaR model passed all tests")
        >>> else:
        ...     print(f"❌ Failed tests: {[k for k, v in results.items() if hasattr(v, 'passed') and not v.passed]}")
    """
    from src.risk_layer.var_backtest.kupiec_pof import kupiec_pof_test

    # Kupiec POF Test (use 1-alpha for confidence level)
    confidence_level = 1 - alpha
    kupiec_result = kupiec_pof_test(
        violations, confidence_level=confidence_level, significance_level=0.05
    )

    # Christoffersen Tests
    independence_result = christoffersen_independence_test(violations, alpha=0.05)
    conditional_coverage_result = christoffersen_conditional_coverage_test(
        violations, alpha=0.05, var_alpha=alpha
    )

    # Check if all passed
    all_passed = (
        kupiec_result.is_valid
        and independence_result.passed
        and conditional_coverage_result.passed
    )

    return {
        "kupiec": kupiec_result,
        "independence": independence_result,
        "conditional_coverage": conditional_coverage_result,
        "all_passed": all_passed,
    }
