"""Kupiec Proportion of Failures (POF) Test.

**DEPRECATED IMPORT PATH**
This module is now a thin compatibility wrapper.
Prefer importing from: src.risk_layer.var_backtest.kupiec_pof

The canonical implementation lives in src/risk_layer/var_backtest/kupiec_pof.py
with Phase 7 enhancements. This module maintains the legacy API for backward
compatibility with zero breaking changes.

Pure Python implementation without SciPy dependency.
Uses math.erfc for chi-square p-value computation.

Reference:
---------
Kupiec, P. (1995): "Techniques for Verifying the Accuracy of
Risk Measurement Models", Journal of Derivatives.
"""

import warnings
from dataclasses import dataclass
from typing import Optional

# Import from canonical engine
from src.risk_layer.var_backtest.kupiec_pof import (
    kupiec_lr_uc as _canonical_kupiec_lr_uc,
    _compute_lr_statistic as _canonical_compute_lr_statistic,
    chi2_df1_sf as _canonical_chi2_sf,
)


# ============================================================================
# Deprecation Warning (Guarded for CI/Test Friendliness)
# ============================================================================


def _maybe_warn_deprecated() -> None:
    """Emit deprecation warning if not in test/CI context."""
    import os
    import sys

    # Don't warn in test contexts
    if "PYTEST_CURRENT_TEST" in os.environ:
        return
    if "PEAK_TRADE_SILENCE_DEPRECATIONS" in os.environ:
        return
    if "pytest" in sys.modules:
        return

    warnings.warn(
        "src.risk.validation.kupiec_pof is deprecated; "
        "prefer src.risk_layer.var_backtest.kupiec_pof",
        DeprecationWarning,
        stacklevel=3,
    )


# Emit warning on module import (guarded)
_maybe_warn_deprecated()


# ============================================================================
# Legacy API: Dataclass & Functions
# ============================================================================


@dataclass(frozen=True)
class KupiecResult:
    """Result of Kupiec POF test.

    This is the legacy dataclass API maintained for backward compatibility.
    The canonical engine uses KupiecLRResult for its Phase 7 API.

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

    **WRAPPER**: This function now delegates to the canonical engine
    (src.risk_layer.var_backtest.kupiec_pof.kupiec_lr_uc) for all computation.

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
    # Validation (reuse canonical validation by catching ValueError)
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

    # Handle edge case: no observations
    if observations == 0:
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

    # Delegate to canonical engine
    # kupiec_lr_uc(n, x, alpha_exceedance, p_threshold)
    # where: n=observations, x=breaches, alpha_exceedance=p, p_threshold=alpha
    try:
        canonical_result = _canonical_kupiec_lr_uc(
            n=observations,
            x=breaches,
            alpha=p,  # Expected exceedance rate
            p_threshold=alpha,  # Significance level
        )
    except ValueError as e:
        # Should not happen if we validated correctly, but safety first
        raise ValueError(f"Canonical engine rejected inputs: {e}")

    # Map canonical result to legacy KupiecResult
    is_valid = canonical_result.verdict == "PASS"

    return KupiecResult(
        p_value=canonical_result.p_value,
        test_statistic=canonical_result.lr_uc,
        breaches=breaches,
        observations=observations,
        expected_breaches=expected_breaches,
        is_valid=is_valid,
        confidence_level=confidence_level,
        alpha=alpha,
    )


def kupiec_lr_statistic(x: int, n: int, p: float) -> float:
    """Compute Kupiec likelihood ratio statistic.

    **WRAPPER**: This function now delegates to the canonical engine
    (src.risk_layer.var_backtest.kupiec_pof._compute_lr_statistic).

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
    # Delegate to canonical engine
    # _compute_lr_statistic(T, N, p_star) where T=n, N=x, p_star=p
    return _canonical_compute_lr_statistic(n, x, p)


def chi2_p_value(lr_statistic: float) -> float:
    """Compute p-value for chi-square test with df=1.

    **WRAPPER**: This function now delegates to the canonical engine
    (src.risk_layer.var_backtest.kupiec_pof.chi2_df1_sf).

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
    # Delegate to canonical engine
    # chi2_df1_sf(x) is the survival function (1 - CDF)
    return _canonical_chi2_sf(lr_statistic)
