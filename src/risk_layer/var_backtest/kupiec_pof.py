"""
Kupiec Proportion of Failures (POF) Test
=========================================

Statistischer Backtest für VaR-Modelle ohne scipy-Abhängigkeit.

Referenz:
- Kupiec, P. (1995): "Techniques for Verifying the Accuracy of
  Risk Measurement Models", Journal of Derivatives

Implementation Notes:
- Chi-square distribution (df=1) implemented using stdlib only
- No scipy dependency (uses math.erf and binary search)
- Numerically stable for edge cases (N=0, N=T)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

# Epsilon for numerical stability
EPS = 1e-12


class KupiecResult(Enum):
    """Ergebnis des Kupiec POF Tests."""

    ACCEPT = "accept"  # H₀ nicht abgelehnt → Modell OK
    REJECT = "reject"  # H₀ abgelehnt → Modell fehlkalibriert
    INCONCLUSIVE = "inconclusive"  # Zu wenig Daten


@dataclass(frozen=True)
class KupiecPOFOutput:
    """Strukturiertes Ergebnis des Kupiec POF Tests."""

    # Eingabedaten
    n_observations: int  # T: Anzahl Beobachtungen
    n_violations: int  # N: Anzahl Überschreitungen
    confidence_level: float  # z.B. 0.99 für 99% VaR
    significance_level: float  # z.B. 0.05 für 5% Signifikanz

    # Berechnete Werte
    expected_violation_rate: float  # p* = 1 - confidence_level
    observed_violation_rate: float  # N / T
    lr_statistic: float  # Likelihood Ratio Statistik
    p_value: float  # p-Wert aus χ²(1)
    critical_value: float  # χ²(1) kritischer Wert

    # Ergebnis
    result: KupiecResult

    @property
    def is_valid(self) -> bool:
        """Modell gilt als valide wenn H₀ nicht abgelehnt."""
        return self.result == KupiecResult.ACCEPT

    @property
    def violation_ratio(self) -> float:
        """Verhältnis beobachtete / erwartete Violations."""
        if self.expected_violation_rate < EPS:
            return float("inf")
        return self.observed_violation_rate / self.expected_violation_rate


def kupiec_pof_test(
    violations: Sequence[bool],
    confidence_level: float = 0.99,
    significance_level: float = 0.05,
    min_observations: int = 250,
) -> KupiecPOFOutput:
    """
    Führt den Kupiec POF Test durch.

    Args:
        violations: Sequenz von bool (True = VaR-Überschreitung)
        confidence_level: VaR-Konfidenzniveau (z.B. 0.99 für 99% VaR)
        significance_level: Signifikanzniveau für Hypothesentest
        min_observations: Minimum für validen Test (Basel: 250)

    Returns:
        KupiecPOFOutput mit allen Ergebnissen

    Raises:
        ValueError: Bei ungültigen Eingaben

    Example:
        >>> violations = [False] * 245 + [True] * 5  # 5 Violations in 250 Tagen
        >>> result = kupiec_pof_test(violations, confidence_level=0.99)
        >>> result.is_valid
        True
    """
    # Input Validation
    if not 0 < confidence_level < 1:
        raise ValueError(f"confidence_level muss in (0,1) liegen: {confidence_level}")
    if not 0 < significance_level < 1:
        raise ValueError(f"significance_level muss in (0,1) liegen: {significance_level}")

    T = len(violations)
    N = sum(violations)
    p_star = 1 - confidence_level  # Erwartete Violation Rate

    # Beobachtete Violation Rate
    p_obs = N / T if T > 0 else 0.0

    # Kritischer Wert berechnen (einmal, unabhängig von Datenanzahl)
    critical_value = chi2_df1_ppf(1 - significance_level)

    # Prüfe Mindestanzahl Beobachtungen
    if T < min_observations:
        return KupiecPOFOutput(
            n_observations=T,
            n_violations=N,
            confidence_level=confidence_level,
            significance_level=significance_level,
            expected_violation_rate=p_star,
            observed_violation_rate=p_obs,
            lr_statistic=float("nan"),
            p_value=float("nan"),
            critical_value=critical_value,
            result=KupiecResult.INCONCLUSIVE,
        )

    # Likelihood Ratio Statistik berechnen
    lr_stat = _compute_lr_statistic(T, N, p_star)

    # p-Wert aus χ²(1) Verteilung
    p_value = chi2_df1_sf(lr_stat)

    # Entscheidung
    if lr_stat > critical_value:
        result = KupiecResult.REJECT
    else:
        result = KupiecResult.ACCEPT

    return KupiecPOFOutput(
        n_observations=T,
        n_violations=N,
        confidence_level=confidence_level,
        significance_level=significance_level,
        expected_violation_rate=p_star,
        observed_violation_rate=p_obs,
        lr_statistic=lr_stat,
        p_value=p_value,
        critical_value=critical_value,
        result=result,
    )


def _compute_lr_statistic(T: int, N: int, p_star: float) -> float:
    """
    Berechnet die Likelihood Ratio Statistik mit numerischer Stabilität.

    LR = -2 * ln(L₀) + 2 * ln(L₁)

    Wobei:
    - L₀ = (1-p*)^(T-N) * p*^N  (unter H₀)
    - L₁ = (1-p̂)^(T-N) * p̂^N   (unter H₁, mit p̂ = N/T)
    """
    # Edge Case: keine Violations
    if N == 0:
        # LR = -2 * [T * log(1 - p*)]
        # Numerisch sicher: wenn p* sehr klein, log(1-p*) ≈ -p*
        if p_star < EPS:
            return 0.0
        return -2 * T * math.log(1 - p_star)

    # Edge Case: alle Violations
    if N == T:
        # LR = -2 * [T * log(p*)] (L₁ Term wird 0)
        if p_star < EPS:
            return float("inf")
        return -2 * T * math.log(p_star)

    p_obs = N / T

    # Schütze vor log(0) - sollte nicht passieren bei N in (0, T)
    # Aber sicher ist sicher
    if p_obs < EPS or (1 - p_obs) < EPS:
        return float("inf")
    if p_star < EPS or (1 - p_star) < EPS:
        return float("inf")

    # Log-Likelihood unter H₀
    log_L0 = (T - N) * math.log(1 - p_star) + N * math.log(p_star)

    # Log-Likelihood unter H₁ (mit beobachteter Rate)
    log_L1 = (T - N) * math.log(1 - p_obs) + N * math.log(p_obs)

    # LR Statistik
    lr = -2 * (log_L0 - log_L1)

    return lr


# ============================================================================
# Chi-Square Distribution (df=1) - Stdlib Only Implementation
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


def chi2_df1_ppf(p: float) -> float:
    """
    Chi-square percent point function (inverse CDF) for df=1.

    Finds x such that CDF(x) = p, using binary search.

    Args:
        p: Probability (must be in (0, 1))

    Returns:
        Critical value x where CDF(x) = p

    Raises:
        ValueError: If p not in (0, 1)
    """
    if not 0 < p < 1:
        raise ValueError(f"p must be in (0, 1), got {p}")

    # Special cases
    if p < 1e-10:
        return 0.0
    if p > 1 - 1e-10:
        return 1000.0  # Large value for practical purposes

    # Binary search for inverse
    # chi2(1) has support [0, inf), but we can bound search reasonably
    low, high = 0.0, 100.0

    # Ensure high is large enough
    while chi2_df1_cdf(high) < p:
        high *= 2

    # Binary search
    max_iterations = 100
    tolerance = 1e-9

    for _ in range(max_iterations):
        mid = (low + high) / 2
        cdf_mid = chi2_df1_cdf(mid)

        if abs(cdf_mid - p) < tolerance:
            return mid

        if cdf_mid < p:
            low = mid
        else:
            high = mid

    # Return best estimate
    return (low + high) / 2


def chi2_df1_cdf(x: float) -> float:
    """
    Chi-square CDF for df=1.

    CDF(x) = erf(sqrt(x/2))

    Args:
        x: Chi-square statistic (non-negative)

    Returns:
        CDF value
    """
    if x < 0:
        return 0.0
    if x == 0:
        return 0.0

    return math.erf(math.sqrt(x / 2))


# ============================================================================
# Convenience Functions
# ============================================================================


def quick_kupiec_check(
    n_violations: int,
    n_observations: int,
    confidence_level: float = 0.99,
) -> bool:
    """
    Schneller Check ohne Violations-Sequenz.

    Args:
        n_violations: Anzahl VaR-Überschreitungen
        n_observations: Anzahl Beobachtungen
        confidence_level: VaR-Konfidenzniveau

    Returns:
        True wenn Modell valide (H₀ nicht abgelehnt)
    """
    violations = [True] * n_violations + [False] * (n_observations - n_violations)
    result = kupiec_pof_test(violations, confidence_level=confidence_level)
    return result.is_valid


# ============================================================================
# Phase 7: Direct n/x/alpha Convenience API
# ============================================================================


@dataclass(frozen=True)
class KupiecLRResult:
    """
    Phase 7 convenience result for direct n/x/alpha interface.

    Attributes:
        n: Total observations
        x: Number of exceedances/violations
        alpha: Exceedance probability (e.g., 0.01 for 99% VaR)
        phat: Observed exceedance rate (x/n)
        lr_uc: Likelihood Ratio statistic (unconditional coverage)
        p_value: p-value from chi²(df=1)
        verdict: "PASS" if p_value >= p_threshold, else "FAIL"
        notes: Additional context or warnings
    """

    n: int
    x: int
    alpha: float
    phat: float
    lr_uc: float
    p_value: float
    verdict: str
    notes: str

    def to_dict(self) -> dict:
        """Export to dictionary."""
        return {
            "n": self.n,
            "x": self.x,
            "alpha": self.alpha,
            "phat": self.phat,
            "lr_uc": self.lr_uc,
            "p_value": self.p_value,
            "verdict": self.verdict,
            "notes": self.notes,
        }


def kupiec_lr_uc(
    n: int,
    x: int,
    alpha: float,
    *,
    p_threshold: float = 0.05,
) -> KupiecLRResult:
    """
    Phase 7: Direct Kupiec Unconditional Coverage (LR-UC) test.

    Compute Kupiec test using raw counts (n observations, x exceedances)
    without building a full violations series.

    Args:
        n: Total number of observations (must be > 0)
        x: Number of exceedances/violations (0 <= x <= n)
        alpha: Expected exceedance rate (e.g., 0.01 for 99% VaR)
        p_threshold: Significance level for verdict (default 0.05)

    Returns:
        KupiecLRResult with test statistics and verdict

    Raises:
        ValueError: If inputs are invalid (n<=0, x<0, x>n, alpha not in (0,1))

    Example:
        >>> result = kupiec_lr_uc(n=1000, x=10, alpha=0.01)
        >>> print(result.verdict)  # "PASS"
        >>> print(result.p_value)  # ~0.92

    Notes:
        - Uses existing internal engine (_compute_lr_statistic, chi2_df1_sf)
        - Numerically stable for edge cases (x=0, x=n)
        - Verdict: PASS if p_value >= p_threshold, else FAIL
    """
    # Validation
    if n <= 0:
        raise ValueError(f"n must be > 0, got {n}")
    if x < 0:
        raise ValueError(f"x must be >= 0, got {x}")
    if x > n:
        raise ValueError(f"x ({x}) cannot exceed n ({n})")
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    if not 0 < p_threshold < 1:
        raise ValueError(f"p_threshold must be in (0, 1), got {p_threshold}")

    # Observed exceedance rate with numerical safety
    phat = x / n if n > 0 else 0.0

    # Compute LR statistic using existing internal engine
    # _compute_lr_statistic(T, N, p_star) where T=n, N=x, p_star=alpha
    lr_uc = _compute_lr_statistic(n, x, alpha)

    # Compute p-value using existing chi² survival function
    p_value = chi2_df1_sf(lr_uc)

    # Verdict
    if p_value >= p_threshold:
        verdict = "PASS"
        notes = f"Model calibration acceptable (p={p_value:.4f} >= {p_threshold})"
    else:
        verdict = "FAIL"
        notes = f"Model calibration rejected (p={p_value:.4f} < {p_threshold})"

    return KupiecLRResult(
        n=n,
        x=x,
        alpha=alpha,
        phat=phat,
        lr_uc=lr_uc,
        p_value=p_value,
        verdict=verdict,
        notes=notes,
    )


def kupiec_from_exceedances(
    exceedances: Sequence[bool],
    alpha: float,
    *,
    p_threshold: float = 0.05,
) -> KupiecLRResult:
    """
    Phase 7: Kupiec test from exceedances boolean series.

    Convenience wrapper that extracts n/x from exceedances list
    and calls kupiec_lr_uc().

    Args:
        exceedances: Boolean sequence (True = exceedance occurred)
        alpha: Expected exceedance rate (e.g., 0.01 for 99% VaR)
        p_threshold: Significance level for verdict (default 0.05)

    Returns:
        KupiecLRResult with test statistics and verdict

    Raises:
        ValueError: If inputs are invalid

    Example:
        >>> exceedances = [False] * 990 + [True] * 10
        >>> result = kupiec_from_exceedances(exceedances, alpha=0.01)
        >>> print(result.verdict)  # "PASS"
        >>> assert result.n == 1000
        >>> assert result.x == 10

    Notes:
        - Efficiently counts True values without copying
        - Delegates to kupiec_lr_uc() for computation
    """
    if not isinstance(exceedances, (list, tuple)) and not hasattr(exceedances, "__len__"):
        raise ValueError("exceedances must be a sequence (list, tuple, or array-like)")

    n = len(exceedances)
    x = sum(exceedances)

    return kupiec_lr_uc(n=n, x=x, alpha=alpha, p_threshold=p_threshold)
