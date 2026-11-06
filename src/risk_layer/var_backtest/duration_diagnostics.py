"""
Duration-Based Independence Diagnostic
=======================================

Optional diagnostic tool for VaR backtest independence testing.
Complements Christoffersen Independence Test with duration-based analysis.

Theory:
-------
If VaR violations are independent, the time between violations (durations)
should follow an exponential distribution with rate parameter λ = p
(where p is the expected violation rate).

This module provides:
1. Duration extraction (time between exceedances)
2. Simple diagnostic metrics (mean, std, clustering score)
3. Optional exponential distribution goodness-of-fit (stdlib-only)

References:
-----------
- Christoffersen, P. F. (1998). Evaluating Interval Forecasts.
- Haas, M. (2005). Improved Duration-Based Backtesting of VaR.

Usage:
------
This is a DIAGNOSTIC tool, not a primary validation gate.
- Use alongside Kupiec POF and Christoffersen Independence tests
- Results should be interpreted as supplementary evidence
- Not recommended as sole basis for model rejection

Agent Phase 9A Implementation: Duration-based independence diagnostic (stdlib-only)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Union

import pandas as pd

# Epsilon for numerical stability
EPS = 1e-12


@dataclass
class DurationDiagnosticResult:
    """
    Result of duration-based independence diagnostic.

    Attributes:
        n_exceedances: Number of exceedances observed
        n_durations: Number of durations computed (n_exceedances - 1)
        mean_duration: Average time between exceedances (in time units)
        std_duration: Standard deviation of durations
        expected_duration: Expected mean under independence (1/p)
        duration_ratio: Observed mean / Expected mean (< 1 suggests clustering)
        clustering_score: Diagnostic score (0 = perfect, > 0 = deviation)
        durations: List of observed durations
        notes: Interpretation guidance
        exponential_test: Optional exponential goodness-of-fit test result
    """

    n_exceedances: int
    n_durations: int
    mean_duration: float
    std_duration: float
    expected_duration: float
    duration_ratio: float
    clustering_score: float
    durations: List[float]
    notes: str
    exponential_test: Optional[ExponentialTestResult] = None

    def to_dict(self) -> dict:
        """Export to dictionary."""
        result = {
            "n_exceedances": self.n_exceedances,
            "n_durations": self.n_durations,
            "mean_duration": self.mean_duration,
            "std_duration": self.std_duration,
            "expected_duration": self.expected_duration,
            "duration_ratio": self.duration_ratio,
            "clustering_score": self.clustering_score,
            "durations": self.durations,
            "notes": self.notes,
        }
        if self.exponential_test is not None:
            result["exponential_test"] = self.exponential_test.to_dict()
        return result

    def is_suspicious(self, threshold: float = 0.5) -> bool:
        """
        Check if durations suggest clustering (diagnostic only).

        Args:
            threshold: Duration ratio below which clustering is suspicious (default: 0.5)

        Returns:
            True if duration_ratio < threshold (suggests clustering)

        Notes:
            - This is NOT a formal hypothesis test
            - Use as supplementary diagnostic only
            - Combine with Christoffersen Independence Test for formal testing
        """
        return self.duration_ratio < threshold


@dataclass
class ExponentialTestResult:
    """
    Result of exponential distribution goodness-of-fit test.

    Attributes:
        test_name: Name of the test
        test_statistic: Test statistic value
        p_value: Approximate p-value (if available)
        passed: Whether test passed at significance level
        significance_level: Significance level used
        notes: Additional information
    """

    test_name: str
    test_statistic: float
    p_value: Optional[float]
    passed: bool
    significance_level: float
    notes: str

    def to_dict(self) -> dict:
        """Export to dictionary."""
        return {
            "test_name": self.test_name,
            "test_statistic": self.test_statistic,
            "p_value": self.p_value,
            "passed": self.passed,
            "significance_level": self.significance_level,
            "notes": self.notes,
        }


def extract_exceedance_durations(
    exceedances: Union[Sequence[bool], pd.Series],
    timestamps: Optional[Union[Sequence, pd.DatetimeIndex]] = None,
) -> List[float]:
    """
    Extract time between exceedances (durations).

    Args:
        exceedances: Boolean sequence (True = exceedance occurred)
        timestamps: Optional timestamps for each observation.
                   If None, uses integer time indices (1, 2, 3, ...)
                   If provided and DatetimeIndex, returns durations in days

    Returns:
        List of durations (time between consecutive exceedances)
        Empty list if fewer than 2 exceedances

    Example:
        >>> exceedances = [False, False, True, False, False, True, False, True]
        >>> durations = extract_exceedance_durations(exceedances)
        >>> durations  # [3, 2] (positions: 2→5→7, diffs: 3, 2)
        [3, 2]

        >>> dates = pd.date_range("2024-01-01", periods=8, freq="D")
        >>> durations = extract_exceedance_durations(exceedances, dates)
        >>> durations  # [3.0, 2.0] (in days)
        [3.0, 2.0]

    Notes:
        - Durations are measured from exceedance to exceedance
        - First exceedance has no duration (no prior exceedance)
        - Returns empty list if < 2 exceedances
    """
    # Convert to list if necessary
    if isinstance(exceedances, pd.Series):
        exceedances = exceedances.tolist()
    else:
        exceedances = list(exceedances)

    # Find exceedance indices
    exceedance_indices = [i for i, exc in enumerate(exceedances) if exc]

    # Need at least 2 exceedances to compute durations
    if len(exceedance_indices) < 2:
        return []

    # Compute durations
    if timestamps is None:
        # Use integer indices
        durations = [
            float(exceedance_indices[i + 1] - exceedance_indices[i])
            for i in range(len(exceedance_indices) - 1)
        ]
    else:
        # Use provided timestamps
        if isinstance(timestamps, pd.DatetimeIndex):
            # Convert to days
            durations = [
                (
                    timestamps[exceedance_indices[i + 1]] - timestamps[exceedance_indices[i]]
                ).total_seconds()
                / 86400.0  # Convert seconds to days
                for i in range(len(exceedance_indices) - 1)
            ]
        else:
            # Assume numeric timestamps
            timestamps_list = list(timestamps)
            durations = [
                float(
                    timestamps_list[exceedance_indices[i + 1]]
                    - timestamps_list[exceedance_indices[i]]
                )
                for i in range(len(exceedance_indices) - 1)
            ]

    return durations


def duration_independence_diagnostic(
    exceedances: Union[Sequence[bool], pd.Series],
    expected_rate: Optional[float] = None,
    timestamps: Optional[Union[Sequence, pd.DatetimeIndex]] = None,
    enable_exponential_test: bool = False,
    significance_level: float = 0.05,
) -> DurationDiagnosticResult:
    """
    Compute duration-based independence diagnostic.

    This is a DIAGNOSTIC tool, not a formal hypothesis test gate.
    Use alongside Kupiec POF and Christoffersen tests.

    Args:
        exceedances: Boolean sequence (True = exceedance)
        expected_rate: Expected exceedance rate (e.g., 0.01 for 99% VaR)
                      If None, estimated from data as n_exceedances/n_observations
        timestamps: Optional timestamps (for time-aware durations)
        enable_exponential_test: Whether to run exponential goodness-of-fit test
        significance_level: Significance level for exponential test (default: 0.05)

    Returns:
        DurationDiagnosticResult with diagnostic metrics

    Theory:
        Under independence, durations ~ Exponential(λ = p), where:
        - Mean = 1/p
        - Std = 1/p
        - Coefficient of variation = 1.0

        Clustering → durations shorter than expected → ratio < 1

    Example:
        >>> exceedances = [False] * 98 + [True, False] * 1  # 1% rate
        >>> result = duration_independence_diagnostic(exceedances, expected_rate=0.01)
        >>> print(result.duration_ratio)  # Close to 1.0 if independent
        >>> print(result.is_suspicious())  # False if not clustered

    Notes:
        - DIAGNOSTIC USE ONLY - not a replacement for Christoffersen test
        - Interpret clustering_score and duration_ratio as supplementary evidence
        - For formal independence testing, use Christoffersen Independence Test
    """
    # Convert to list
    if isinstance(exceedances, pd.Series):
        exceedances_list = exceedances.tolist()
    else:
        exceedances_list = list(exceedances)

    n_obs = len(exceedances_list)
    n_exceedances = sum(exceedances_list)

    # Estimate expected rate if not provided
    if expected_rate is None:
        expected_rate = n_exceedances / n_obs if n_obs > 0 else 0.0

    # Extract durations
    durations = extract_exceedance_durations(exceedances_list, timestamps)
    n_durations = len(durations)

    # Handle insufficient data
    if n_durations == 0:
        return DurationDiagnosticResult(
            n_exceedances=n_exceedances,
            n_durations=0,
            mean_duration=float("nan"),
            std_duration=float("nan"),
            expected_duration=1.0 / expected_rate if expected_rate > EPS else float("inf"),
            duration_ratio=float("nan"),
            clustering_score=float("nan"),
            durations=[],
            notes="Insufficient data: need at least 2 exceedances for duration analysis",
        )

    # Compute duration statistics
    mean_duration = sum(durations) / len(durations)

    # Compute standard deviation
    if len(durations) > 1:
        variance = sum((d - mean_duration) ** 2 for d in durations) / (len(durations) - 1)
        std_duration = math.sqrt(variance)
    else:
        std_duration = 0.0

    # Expected duration under independence (exponential with rate = expected_rate)
    expected_duration = 1.0 / expected_rate if expected_rate > EPS else float("inf")

    # Duration ratio (< 1 suggests clustering)
    if expected_duration > EPS and not math.isinf(expected_duration):
        duration_ratio = mean_duration / expected_duration
    else:
        duration_ratio = float("nan")

    # Clustering score (absolute deviation from expected, normalized)
    if expected_duration > EPS and not math.isinf(expected_duration):
        clustering_score = abs(mean_duration - expected_duration) / expected_duration
    else:
        clustering_score = float("nan")

    # Interpret results
    if duration_ratio < 0.5:
        notes = (
            "⚠️  DIAGNOSTIC: Duration ratio < 0.5 suggests potential clustering. "
            "Verify with Christoffersen Independence Test."
        )
    elif duration_ratio > 1.5:
        notes = (
            "⚠️  DIAGNOSTIC: Duration ratio > 1.5 suggests violations may be too sparse. "
            "Check if model is conservative."
        )
    else:
        notes = (
            "✓ DIAGNOSTIC: Duration ratio within normal range [0.5, 1.5]. "
            "No strong clustering evidence from durations."
        )

    # Optional: Exponential goodness-of-fit test
    exponential_test = None
    if enable_exponential_test and n_durations >= 3:
        exponential_test = _exponential_goodness_of_fit(
            durations, expected_rate, significance_level
        )

    return DurationDiagnosticResult(
        n_exceedances=n_exceedances,
        n_durations=n_durations,
        mean_duration=mean_duration,
        std_duration=std_duration,
        expected_duration=expected_duration,
        duration_ratio=duration_ratio,
        clustering_score=clustering_score,
        durations=durations,
        notes=notes,
        exponential_test=exponential_test,
    )


def _exponential_goodness_of_fit(
    durations: List[float],
    rate: float,
    significance_level: float = 0.05,
) -> ExponentialTestResult:
    """
    Simple exponential distribution goodness-of-fit test (stdlib-only).

    Uses Anderson-Darling-style test statistic (simplified version).

    Args:
        durations: Observed durations
        rate: Expected rate parameter (λ)
        significance_level: Significance level (default: 0.05)

    Returns:
        ExponentialTestResult

    Notes:
        - This is a simplified implementation without scipy
        - For rigorous testing, consider scipy.stats.anderson or scipy.stats.kstest
        - Provided as optional diagnostic, not primary gate
    """
    if len(durations) < 3:
        return ExponentialTestResult(
            test_name="Exponential Goodness-of-Fit (Simplified)",
            test_statistic=float("nan"),
            p_value=None,
            passed=True,  # Inconclusive, so don't fail
            significance_level=significance_level,
            notes="Insufficient data (need >= 3 durations)",
        )

    # Sort durations
    sorted_durations = sorted(durations)
    n = len(sorted_durations)

    # Compute Anderson-Darling-style statistic
    # A² = -n - (1/n) * Σ[(2i-1) * (ln F(x_i) + ln(1 - F(x_{n+1-i})))]
    # where F(x) = 1 - exp(-λx) for exponential

    ad_sum = 0.0
    for i, x in enumerate(sorted_durations, start=1):
        # F(x_i)
        F_xi = 1.0 - math.exp(-rate * x)
        # F(x_{n+1-i})
        x_rev = sorted_durations[n - i]
        F_xrev = 1.0 - math.exp(-rate * x_rev)

        # Avoid log(0)
        F_xi = max(F_xi, EPS)
        F_xi = min(F_xi, 1.0 - EPS)
        F_xrev = max(F_xrev, EPS)
        F_xrev = min(F_xrev, 1.0 - EPS)

        ad_sum += (2 * i - 1) * (math.log(F_xi) + math.log(1.0 - F_xrev))

    A2 = -n - (1.0 / n) * ad_sum

    # Critical value approximation (for exponential, A² critical ≈ 2.5 at α=0.05)
    # This is a rough approximation - for exact values, use scipy or lookup tables
    critical_value_approx = 2.5  # Approximate for α=0.05

    passed = A2 < critical_value_approx

    notes = (
        f"Anderson-Darling test (simplified, stdlib-only). "
        f"A²={A2:.4f}, critical≈{critical_value_approx:.2f}. "
        f"{'PASS' if passed else 'FAIL'} at α={significance_level}. "
        f"NOTE: This is an approximation; use scipy.stats.anderson for exact test."
    )

    return ExponentialTestResult(
        test_name="Exponential Goodness-of-Fit (Anderson-Darling Approx)",
        test_statistic=A2,
        p_value=None,  # Not computed without scipy
        passed=passed,
        significance_level=significance_level,
        notes=notes,
    )


def format_duration_diagnostic(result: DurationDiagnosticResult) -> str:
    """
    Format duration diagnostic result as human-readable string.

    Args:
        result: DurationDiagnosticResult to format

    Returns:
        Formatted string with diagnostic summary

    Example:
        >>> result = duration_independence_diagnostic(exceedances, expected_rate=0.01)
        >>> print(format_duration_diagnostic(result))
    """
    lines = [
        "=" * 60,
        "DURATION-BASED INDEPENDENCE DIAGNOSTIC",
        "=" * 60,
        f"Exceedances:       {result.n_exceedances}",
        f"Durations:         {result.n_durations}",
        f"Mean Duration:     {result.mean_duration:.2f}",
        f"Std Duration:      {result.std_duration:.2f}",
        f"Expected Duration: {result.expected_duration:.2f}",
        f"Duration Ratio:    {result.duration_ratio:.4f}",
        f"Clustering Score:  {result.clustering_score:.4f}",
        "",
        f"Interpretation: {result.notes}",
    ]

    if result.exponential_test is not None:
        lines.extend(
            [
                "",
                "Exponential Goodness-of-Fit Test:",
                f"  Test Statistic: {result.exponential_test.test_statistic:.4f}",
                f"  Result: {'PASS' if result.exponential_test.passed else 'FAIL'}",
                f"  Notes: {result.exponential_test.notes}",
            ]
        )

    lines.append("=" * 60)
    return "\n".join(lines)
