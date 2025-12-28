"""Kupiec Proportion of Failures (POF) Test.

Pure Python implementation without SciPy dependency.
Uses math.erfc for chi-square p-value computation.

Reference:
---------
Kupiec, P. (1995): "Techniques for Verifying the Accuracy of
Risk Measurement Models", Journal of Derivatives.
"""

import math
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class KupiecResult:
    """Result of Kupiec POF test.

    Attributes:
        p_value: p-value from chi-square test (0 to 1)
        test_statistic: Likelihood ratio statistic (LR_uc)
        breaches: Number of VaR breaches observed
        observations: Total number of observations
        expected_breaches: Expected number of breaches (n * (1 - confidence_level))
        is_valid: True if model is valid (p_value >= alpha)
        confidence_level: VaR confidence level used
        alpha: Significance level used (default 0.05)
    """

    p_value: float
    test_statistic: float
    breaches: int
    observations: int
    expected_breaches: float
    is_valid: bool
    confidence_level: float
    alpha: float = 0.05

    def to_json_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "p_value": self.p_value,
            "test_statistic": self.test_statistic,
            "breaches": self.breaches,
            "observations": self.observations,
            "expected_breaches": self.expected_breaches,
            "breach_rate": self.breaches / self.observations if self.observations > 0 else 0.0,
            "expected_rate": 1.0 - self.confidence_level,
            "is_valid": self.is_valid,
            "confidence_level": self.confidence_level,
            "alpha": self.alpha,
        }

    def to_markdown(self) -> str:
        """Generate markdown report."""
        status = "✅ VALID" if self.is_valid else "❌ INVALID"
        breach_rate = self.breaches / self.observations if self.observations > 0 else 0.0
        expected_rate = 1.0 - self.confidence_level

        return f"""## Kupiec POF Test Result

**Status:** {status}

| Metric | Value |
|--------|-------|
| Observations | {self.observations} |
| Breaches | {self.breaches} |
| Expected Breaches | {self.expected_breaches:.2f} |
| Breach Rate | {breach_rate:.2%} |
| Expected Rate | {expected_rate:.2%} |
| LR Statistic | {self.test_statistic:.4f} |
| p-value | {self.p_value:.4f} |
| Confidence Level | {self.confidence_level:.1%} |
| Significance Level | {self.alpha:.1%} |

**Interpretation:** {"The VaR model is calibrated correctly." if self.is_valid else "The VaR model is mis-calibrated."}
"""


def kupiec_pof_test(
    breaches: int,
    observations: int,
    confidence_level: float = 0.99,
    alpha: float = 0.05,
) -> KupiecResult:
    """Perform Kupiec Proportion of Failures test.

    Tests if the observed breach rate matches the expected rate
    under the null hypothesis that the VaR model is correctly calibrated.

    Args:
        breaches: Number of VaR breaches (x)
        observations: Total number of observations (n)
        confidence_level: VaR confidence level (e.g., 0.99 for 99% VaR)
        alpha: Significance level for hypothesis test (default 0.05)

    Returns:
        KupiecResult with test statistics and validation result

    Raises:
        ValueError: If inputs are invalid

    Example:
        >>> result = kupiec_pof_test(breaches=5, observations=250, confidence_level=0.99)
        >>> print(result.is_valid)  # True or False
        >>> print(result.p_value)   # p-value from chi-square test
    """
    # Validation
    if observations < 0:
        raise ValueError(f"observations must be non-negative, got {observations}")
    if breaches < 0:
        raise ValueError(f"breaches must be non-negative, got {breaches}")
    if breaches > observations:
        raise ValueError(f"breaches ({breaches}) cannot exceed observations ({observations})")
    if not 0 < confidence_level < 1:
        raise ValueError(f"confidence_level must be in (0, 1), got {confidence_level}")
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")

    # Expected breach rate
    p = 1.0 - confidence_level
    expected_breaches = observations * p

    # Handle edge cases
    if observations == 0:
        # No observations -> cannot test
        return KupiecResult(
            p_value=float("nan"),
            test_statistic=float("nan"),
            breaches=0,
            observations=0,
            expected_breaches=0.0,
            is_valid=False,
            confidence_level=confidence_level,
            alpha=alpha,
        )

    # Compute LR statistic
    lr_uc = kupiec_lr_statistic(breaches, observations, p)

    # Compute p-value using chi-square(df=1) approximation
    p_value = chi2_p_value(lr_uc)

    # Decision: reject if p_value < alpha
    is_valid = p_value >= alpha

    return KupiecResult(
        p_value=p_value,
        test_statistic=lr_uc,
        breaches=breaches,
        observations=observations,
        expected_breaches=expected_breaches,
        is_valid=is_valid,
        confidence_level=confidence_level,
        alpha=alpha,
    )


def kupiec_lr_statistic(x: int, n: int, p: float) -> float:
    """Compute Kupiec likelihood ratio statistic.

    LR_uc = -2 * (log L_0 - log L_1)

    where:
    - L_0: likelihood under H_0 (p = expected rate)
    - L_1: likelihood under H_1 (p = observed rate = x/n)

    Args:
        x: Number of breaches
        n: Total observations
        p: Expected breach rate (1 - confidence_level)

    Returns:
        Likelihood ratio statistic

    Notes:
        Handles edge cases x=0 and x=n without log(0) errors.
    """
    if n == 0:
        return 0.0

    phat = x / n  # Observed breach rate

    # Edge case: x = 0 (no breaches)
    if x == 0:
        # L_1 = 1 (perfect fit), log L_1 = 0
        # L_0 = (1-p)^n
        # log L_0 = n * log(1-p)
        # LR = -2 * (n * log(1-p) - 0) = -2 * n * log(1-p)
        if p >= 1.0:
            return 0.0
        return -2.0 * n * math.log1p(-p)

    # Edge case: x = n (all breaches)
    if x == n:
        # L_1 = 1 (perfect fit), log L_1 = 0
        # L_0 = p^n
        # log L_0 = n * log(p)
        # LR = -2 * (n * log(p) - 0) = -2 * n * log(p)
        if p <= 0.0:
            return 0.0
        return -2.0 * n * math.log(p)

    # General case: 0 < x < n
    # log L_0 = x * log(p) + (n-x) * log(1-p)
    # log L_1 = x * log(phat) + (n-x) * log(1-phat)

    # Avoid log(0) by checking bounds
    if p <= 0.0 or p >= 1.0:
        return 0.0
    if phat <= 0.0 or phat >= 1.0:
        return 0.0

    log_L0 = x * math.log(p) + (n - x) * math.log1p(-p)
    log_L1 = x * math.log(phat) + (n - x) * math.log1p(-phat)

    lr_uc = -2.0 * (log_L0 - log_L1)

    return max(0.0, lr_uc)  # LR cannot be negative


def chi2_p_value(lr_statistic: float) -> float:
    """Compute p-value for chi-square test with df=1.

    Uses pure Python math.erfc (no scipy dependency).

    For chi-square distribution with df=1:
    p_value = P(X > lr_statistic) = erfc(sqrt(lr_statistic / 2))

    Args:
        lr_statistic: Likelihood ratio statistic

    Returns:
        p-value in [0, 1]

    Notes:
        This is exact for df=1 and does not require scipy.
    """
    if lr_statistic < 0:
        return 1.0

    if lr_statistic == 0:
        return 1.0

    # p_value = erfc(sqrt(lr_statistic / 2))
    # This is the survival function for chi-square(df=1)
    p_value = math.erfc(math.sqrt(lr_statistic / 2.0))

    # Clamp to [0, 1] for numerical stability
    return max(0.0, min(1.0, p_value))
