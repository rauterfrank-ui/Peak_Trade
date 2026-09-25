"""
Christoffersen Independence & Conditional Coverage Tests
=========================================================

Statistical tests for VaR model validation, focusing on independence
of violations and conditional coverage.

**Phase 8B:** Stdlib-only implementation (no scipy, no numpy).

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

Implementation Notes:
---------------------
- Pure stdlib (math.erfc, math.exp)
- No scipy dependency (chi²(1) via erfc, chi²(2) via exp)
- No numpy dependency (transition matrix as tuple)
- Numerically stable for edge cases (zero counts, eps clamping)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

# Epsilon for numerical stability
EPS = 1e-12


@dataclass(frozen=True)
class ChristoffersenIndResult:
    """
    Result of Christoffersen Independence Test.

    Phase 8B: Lightweight dataclass following Phase 7 style.

    Attributes:
        n: Total observations
        x: Number of exceedances/violations
        n00: Transitions from no-violation to no-violation
        n01: Transitions from no-violation to violation
        n10: Transitions from violation to no-violation
        n11: Transitions from violation to violation
        pi_01: Transition probability P(violation | no-violation)
        pi_11: Transition probability P(violation | violation)
        lr_ind: Likelihood Ratio statistic (independence test)
        p_value: p-value from chi²(df=1)
        verdict: "PASS" if p_value >= p_threshold, else "FAIL"
        notes: Additional context or warnings
    """

    n: int
    x: int
    n00: int
    n01: int
    n10: int
    n11: int
    pi_01: float
    pi_11: float
    lr_ind: float
    p_value: float
    verdict: str
    notes: str

    def to_dict(self) -> dict:
        """Export to dictionary."""
        return {
            "n": self.n,
            "x": self.x,
            "transition_matrix": {
                "n00": self.n00,
                "n01": self.n01,
                "n10": self.n10,
                "n11": self.n11,
            },
            "transition_probabilities": {
                "pi_01": self.pi_01,
                "pi_11": self.pi_11,
            },
            "lr_ind": self.lr_ind,
            "p_value": self.p_value,
            "verdict": self.verdict,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class ChristoffersenCCResult:
    """
    Result of Christoffersen Conditional Coverage Test.

    Phase 8B: Combines Kupiec UC + Independence test.

    Attributes:
        n: Total observations
        x: Number of exceedances/violations
        alpha: Expected exceedance rate
        lr_uc: Kupiec unconditional coverage statistic
        lr_ind: Independence test statistic
        lr_cc: Conditional coverage statistic (lr_uc + lr_ind)
        p_value: p-value from chi²(df=2)
        verdict: "PASS" if p_value >= p_threshold, else "FAIL"
        notes: Additional context or warnings
    """

    n: int
    x: int
    alpha: float
    lr_uc: float
    lr_ind: float
    lr_cc: float
    p_value: float
    verdict: str
    notes: str

    def to_dict(self) -> dict:
        """Export to dictionary."""
        return {
            "n": self.n,
            "x": self.x,
            "alpha": self.alpha,
            "lr_uc": self.lr_uc,
            "lr_ind": self.lr_ind,
            "lr_cc": self.lr_cc,
            "p_value": self.p_value,
            "verdict": self.verdict,
            "notes": self.notes,
        }


# ============================================================================
# Christoffersen Independence Test (LR-IND)
# ============================================================================


def christoffersen_lr_ind(
    exceedances: Sequence[bool],
    *,
    p_threshold: float = 0.05,
) -> ChristoffersenIndResult:
    """
    Christoffersen Independence Test (LR-IND).

    Tests the null hypothesis that VaR violations are independent over time.
    Rejection indicates violations are clustered (model is mis-specified).

    Args:
        exceedances: Boolean sequence (True = exceedance occurred)
        p_threshold: Significance level for verdict (default 0.05)

    Returns:
        ChristoffersenIndResult with test statistics and verdict

    Raises:
        ValueError: If inputs are invalid (n < 2)

    Theory:
    -------
    Compute 2x2 transition matrix:
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
        >>> exceedances = [False, False, True, False, True, True, False]
        >>> result = christoffersen_lr_ind(exceedances)
        >>> print(result.verdict)  # "PASS" or "FAIL"
    """
    # Validation
    n = len(exceedances)
    if n < 2:
        raise ValueError(f"Need at least 2 observations for independence test, got {n}")

    if not 0 < p_threshold < 1:
        raise ValueError(f"p_threshold must be in (0, 1), got {p_threshold}")

    x = sum(exceedances)

    # Compute transition matrix
    n00, n01, n10, n11 = _compute_transition_counts(exceedances)

    # Calculate transition probabilities
    n0 = n00 + n01  # Total transitions from no-violation
    n1 = n10 + n11  # Total transitions from violation

    # Handle edge cases: not enough transitions from one state
    if n0 == 0 or n1 == 0:
        # Cannot test independence without transitions from both states
        pi_01 = 0.0 if n0 == 0 else n01 / n0
        pi_11 = 0.0 if n1 == 0 else n11 / n1

        return ChristoffersenIndResult(
            n=n,
            x=x,
            n00=n00,
            n01=n01,
            n10=n10,
            n11=n11,
            pi_01=pi_01,
            pi_11=pi_11,
            lr_ind=0.0,
            p_value=1.0,
            verdict="PASS",
            notes=f"Insufficient transitions (n0={n0}, n1={n1}). Test inconclusive.",
        )

    # Transition probabilities
    pi_01 = n01 / n0  # P(violation | no-violation)
    pi_11 = n11 / n1  # P(violation | violation)

    # Unconditional probability (under H0)
    pi = x / n if n > 0 else 0.0

    # Compute LR statistic
    lr_ind = _compute_independence_lr(n00, n01, n10, n11, pi_01, pi_11, pi)

    # p-value from χ²(1) using stdlib
    p_value = chi2_df1_sf(lr_ind)

    # Verdict
    if p_value >= p_threshold:
        verdict = "PASS"
        notes = f"Violations are independent (p={p_value:.4f} >= {p_threshold})"
    else:
        verdict = "FAIL"
        notes = f"Violations show clustering (p={p_value:.4f} < {p_threshold})"

    return ChristoffersenIndResult(
        n=n,
        x=x,
        n00=n00,
        n01=n01,
        n10=n10,
        n11=n11,
        pi_01=pi_01,
        pi_11=pi_11,
        lr_ind=lr_ind,
        p_value=p_value,
        verdict=verdict,
        notes=notes,
    )


# ============================================================================
# Christoffersen Conditional Coverage Test (LR-CC)
# ============================================================================


def christoffersen_lr_cc(
    exceedances: Sequence[bool],
    alpha: float,
    *,
    p_threshold: float = 0.05,
) -> ChristoffersenCCResult:
    """
    Christoffersen Conditional Coverage Test (LR-CC).

    Tests the joint hypothesis of:
    1. Correct unconditional coverage (Kupiec POF)
    2. Independence of violations (Christoffersen Independence)

    Args:
        exceedances: Boolean sequence (True = exceedance occurred)
        alpha: Expected exceedance rate (e.g., 0.01 for 99% VaR)
        p_threshold: Significance level for verdict (default 0.05)

    Returns:
        ChristoffersenCCResult with test statistics and verdict

    Raises:
        ValueError: If inputs are invalid

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
        >>> exceedances = [False] * 95 + [True] * 5
        >>> result = christoffersen_lr_cc(exceedances, alpha=0.05)
        >>> print(result.verdict)  # "PASS" or "FAIL"
    """
    # Validation
    n = len(exceedances)
    if n < 2:
        raise ValueError(f"Need at least 2 observations for conditional coverage test, got {n}")

    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")

    if not 0 < p_threshold < 1:
        raise ValueError(f"p_threshold must be in (0, 1), got {p_threshold}")

    x = sum(exceedances)

    # 1. Compute Kupiec POF LR statistic (LR_uc)
    from src.risk_layer.var_backtest.kupiec_pof import _compute_lr_statistic

    lr_uc = _compute_lr_statistic(n, x, alpha)

    # 2. Compute Independence LR statistic (LR_ind)
    independence_result = christoffersen_lr_ind(exceedances, p_threshold=p_threshold)
    lr_ind = independence_result.lr_ind

    # 3. Conditional Coverage LR statistic
    lr_cc = lr_uc + lr_ind

    # p-value from χ²(2) using stdlib
    p_value = chi2_df2_sf(lr_cc)

    # Verdict
    if p_value >= p_threshold:
        verdict = "PASS"
        notes = f"Model has correct coverage and independent violations (p={p_value:.4f} >= {p_threshold})"
    else:
        verdict = "FAIL"
        notes = f"Model fails conditional coverage (p={p_value:.4f} < {p_threshold})"

    return ChristoffersenCCResult(
        n=n,
        x=x,
        alpha=alpha,
        lr_uc=lr_uc,
        lr_ind=lr_ind,
        lr_cc=lr_cc,
        p_value=p_value,
        verdict=verdict,
        notes=notes,
    )


# ============================================================================
# Internal Helpers
# ============================================================================


def _compute_transition_counts(exceedances: Sequence[bool]) -> tuple[int, int, int, int]:
    """
    Compute 2x2 transition matrix counts for exceedances.

    Args:
        exceedances: Boolean sequence

    Returns:
        Tuple (n00, n01, n10, n11) where:
            n00 = # of (no violation → no violation)
            n01 = # of (no violation → violation)
            n10 = # of (violation → no violation)
            n11 = # of (violation → violation)
    """
    n00 = n01 = n10 = n11 = 0

    for i in range(len(exceedances) - 1):
        curr = exceedances[i]
        next_val = exceedances[i + 1]

        if not curr and not next_val:
            n00 += 1
        elif not curr and next_val:
            n01 += 1
        elif curr and not next_val:
            n10 += 1
        elif curr and next_val:
            n11 += 1

    return n00, n01, n10, n11


def _compute_independence_lr(
    n00: int,
    n01: int,
    n10: int,
    n11: int,
    pi_01: float,
    pi_11: float,
    pi: float,
) -> float:
    """
    Compute Likelihood Ratio statistic for Independence Test.

    Args:
        n00, n01, n10, n11: Transition matrix counts
        pi_01: P(violation | no violation)
        pi_11: P(violation | violation)
        pi: Unconditional violation probability

    Returns:
        LR_ind statistic (non-negative)

    Notes:
        Handles edge cases with eps clamping to avoid log(0).
    """
    # Avoid log(0) by clamping
    if pi <= EPS or pi >= 1 - EPS:
        return 0.0

    # Clamp transition probabilities
    pi_01 = max(EPS, min(1 - EPS, pi_01))
    pi_11 = max(EPS, min(1 - EPS, pi_11))

    # Restricted likelihood (H0: π₀₁ = π₁₁ = π)
    log_L_restricted = (n00 + n10) * math.log(1 - pi) + (n01 + n11) * math.log(pi)

    # Unrestricted likelihood (H1: π₀₁ ≠ π₁₁)
    log_L_unrestricted = 0.0
    if n00 + n01 > 0:
        log_L_unrestricted += n00 * math.log(1 - pi_01) + n01 * math.log(pi_01)
    if n10 + n11 > 0:
        log_L_unrestricted += n10 * math.log(1 - pi_11) + n11 * math.log(pi_11)

    # LR statistic
    lr = -2 * (log_L_restricted - log_L_unrestricted)

    return max(0.0, lr)  # Cannot be negative


# ============================================================================
# Chi-Square Distribution Functions (stdlib-only)
# ============================================================================


def chi2_df1_sf(x: float) -> float:
    """
    Chi-square survival function (1 - CDF) for df=1.

    Uses the relationship between chi-square(1) and standard normal:
    If Z ~ N(0,1), then Z² ~ χ²(1)

    CDF(x) = erf(sqrt(x/2))
    SF(x) = 1 - CDF(x) = erfc(sqrt(x/2))

    Args:
        x: Chi-square statistic (non-negative)

    Returns:
        Survival function value (p-value)
    """
    if x < 0:
        return 1.0
    if x == 0:
        return 1.0

    # Use erfc for better numerical stability at large x
    return math.erfc(math.sqrt(x / 2))


def chi2_df2_sf(x: float) -> float:
    """
    Chi-square survival function (1 - CDF) for df=2.

    For df=2, the chi-square distribution is exponential:
    CDF(x) = 1 - exp(-x/2)
    SF(x) = exp(-x/2)

    Args:
        x: Chi-square statistic (non-negative)

    Returns:
        Survival function value (p-value)
    """
    if x < 0:
        return 1.0
    if x == 0:
        return 1.0

    return math.exp(-x / 2)


# ============================================================================
# Legacy API Compatibility (for existing code)
# ============================================================================


@dataclass
class ChristoffersenResult:
    """
    Legacy result type for backward compatibility.

    Maintained for existing code that uses the old API.
    New code should use ChristoffersenIndResult or ChristoffersenCCResult.
    """

    test_name: str
    lr_statistic: float
    p_value: float
    passed: bool
    critical_value: float
    degrees_of_freedom: int
    n_violations: int
    n_observations: int
    transition_matrix: tuple[tuple[int, int], tuple[int, int]] | None = None

    def __repr__(self) -> str:
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"<{self.test_name}: LR={self.lr_statistic:.4f}, p={self.p_value:.4f}, {status}>"


def christoffersen_independence_test(
    violations: Sequence[bool],
    alpha: float = 0.05,
) -> ChristoffersenResult:
    """
    Legacy API: Christoffersen Independence Test.

    This function maintains backward compatibility with existing code.
    New code should use christoffersen_lr_ind() for Phase 8B API.

    Args:
        violations: Boolean list of violations (True = violation)
        alpha: Significance level for the test (default: 0.05)

    Returns:
        ChristoffersenResult with test statistics
    """
    result = christoffersen_lr_ind(violations, p_threshold=alpha)

    # Map to legacy result type
    transition_matrix = (
        (result.n00, result.n01),
        (result.n10, result.n11),
    )

    # Compute critical value for chi2(1)
    from src.risk_layer.var_backtest.kupiec_pof import chi2_df1_ppf

    critical_value = chi2_df1_ppf(1 - alpha)

    return ChristoffersenResult(
        test_name="Christoffersen Independence Test",
        lr_statistic=result.lr_ind,
        p_value=result.p_value,
        passed=(result.verdict == "PASS"),
        critical_value=critical_value,
        degrees_of_freedom=1,
        n_violations=result.x,
        n_observations=result.n,
        transition_matrix=transition_matrix,
    )


def christoffersen_conditional_coverage_test(
    violations: Sequence[bool],
    alpha: float = 0.05,
    var_alpha: float = 0.05,
) -> ChristoffersenResult:
    """
    Legacy API: Christoffersen Conditional Coverage Test.

    This function maintains backward compatibility with existing code.
    New code should use christoffersen_lr_cc() for Phase 8B API.

    Args:
        violations: Boolean list of violations (True = violation)
        alpha: Significance level for the test (default: 0.05)
        var_alpha: VaR significance level (e.g., 0.05 for 95% VaR)

    Returns:
        ChristoffersenResult with test statistics
    """
    result = christoffersen_lr_cc(violations, alpha=var_alpha, p_threshold=alpha)

    # Get transition matrix from independence test
    ind_result = christoffersen_lr_ind(violations, p_threshold=alpha)
    transition_matrix = (
        (ind_result.n00, ind_result.n01),
        (ind_result.n10, ind_result.n11),
    )

    # Compute critical value for chi2(2)
    critical_value = chi2_df2_ppf(1 - alpha)

    return ChristoffersenResult(
        test_name="Christoffersen Conditional Coverage Test",
        lr_statistic=result.lr_cc,
        p_value=result.p_value,
        passed=(result.verdict == "PASS"),
        critical_value=critical_value,
        degrees_of_freedom=2,
        n_violations=result.x,
        n_observations=result.n,
        transition_matrix=transition_matrix,
    )


def chi2_df2_ppf(p: float) -> float:
    """
    Chi-square percent point function (inverse CDF) for df=2.

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


def run_full_var_backtest(
    violations: Sequence[bool],
    alpha: float = 0.05,
) -> dict:
    """
    Legacy API: Run full VaR backtest suite (Kupiec + Christoffersen).

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
            "kupiec": KupiecPOFOutput,
            "independence": ChristoffersenResult,
            "conditional_coverage": ChristoffersenResult,
            "all_passed": bool
        }
    """
    from src.risk_layer.var_backtest.kupiec_pof import kupiec_pof_test

    # Kupiec POF Test (use 1-alpha for confidence level)
    confidence_level = 1 - alpha
    kupiec_result = kupiec_pof_test(
        violations,
        confidence_level=confidence_level,
        significance_level=0.05,
    )

    # Christoffersen Tests
    independence_result = christoffersen_independence_test(violations, alpha=0.05)
    conditional_coverage_result = christoffersen_conditional_coverage_test(
        violations,
        alpha=0.05,
        var_alpha=alpha,
    )

    # Check if all passed
    all_passed = (
        kupiec_result.is_valid and independence_result.passed and conditional_coverage_result.passed
    )

    return {
        "kupiec": kupiec_result,
        "independence": independence_result,
        "conditional_coverage": conditional_coverage_result,
        "all_passed": all_passed,
    }
