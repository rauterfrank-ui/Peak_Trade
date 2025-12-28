"""
Basel Traffic Light System for VaR Model Validation
====================================================

Implements the Basel Committee's traffic light approach for monitoring
VaR model performance.

Agent A3 Implementation: Full Basel Traffic Light with binomial thresholds.

References:
-----------
- Basel Committee on Banking Supervision (1996).
  Supervisory Framework for the Use of "Backtesting" in Conjunction
  with the Internal Models Approach to Market Risk Capital Requirements.
- Basel Committee (2011). Messages from the Academic Literature on Risk
  Measurement for the Trading Book.

Overview:
---------
The Basel Traffic Light System classifies VaR models into three zones
based on the number of exceptions (violations):

- GREEN ZONE: Model is acceptable (0-4 exceptions in ~250 days at 99% VaR)
- YELLOW ZONE: Model requires attention (5-9 exceptions)
- RED ZONE: Model is inadequate and must be revised (≥10 exceptions)

The zones are defined based on binomial test confidence intervals.
"""

import logging
import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Optional scipy import for binomial
try:
    from scipy.stats import binom as scipy_binom

    SCIPY_AVAILABLE = True
except ImportError:
    scipy_binom = None
    SCIPY_AVAILABLE = False


class BaselZone(str, Enum):
    """
    Basel Traffic Light Zones.

    Attributes:
        GREEN: Model is acceptable (no action required)
        YELLOW: Model requires increased monitoring/analysis
        RED: Model is inadequate (regulatory action required)
    """

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


@dataclass
class TrafficLightResult:
    """
    Result of Basel Traffic Light Assessment.

    Attributes:
        zone: Basel zone (GREEN, YELLOW, RED)
        n_violations: Actual number of violations observed
        expected_violations: Expected number of violations (n * alpha)
        n_observations: Total number of observations
        alpha: VaR significance level (e.g., 0.01 for 99% VaR)
        violation_rate: Observed violation rate (n_violations / n_observations)
        green_threshold: Maximum violations for GREEN zone
        yellow_threshold: Maximum violations for YELLOW zone (above = RED)
        capital_multiplier: Basel capital multiplier (3.0 + zone penalty)
    """

    zone: BaselZone
    n_violations: int
    expected_violations: float
    n_observations: int
    alpha: float
    violation_rate: float
    green_threshold: int
    yellow_threshold: int
    capital_multiplier: float

    def __repr__(self) -> str:
        emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}[self.zone.value]
        return (
            f"<BaselTrafficLight: {emoji} {self.zone.value.upper()} | "
            f"Violations={self.n_violations} (expected={self.expected_violations:.1f}, "
            f"rate={self.violation_rate:.2%}), "
            f"Multiplier={self.capital_multiplier:.2f}>"
        )


def basel_traffic_light(
    n_violations: int,
    n_observations: int,
    alpha: float = 0.01,
) -> TrafficLightResult:
    """
    Basel Traffic Light Assessment for VaR model.

    Args:
        n_violations: Number of observed VaR violations
        n_observations: Total number of observations (e.g., 250 trading days)
        alpha: VaR significance level (default: 0.01 = 99% VaR)

    Returns:
        TrafficLightResult with zone classification and statistics

    Theory:
    -------
    Under the null hypothesis that the VaR model is correct, violations
    follow a Binomial(n, α) distribution.

    Zone boundaries (Basel standard for 99% VaR, 250 days):
    - GREEN: 0-4 exceptions (no action)
    - YELLOW: 5-9 exceptions (increased monitoring)
    - RED: ≥10 exceptions (model revision required)

    Capital multipliers:
    - GREEN: 3.0 (base)
    - YELLOW: 3.0 + penalty (increases with violations)
    - RED: 4.0 (maximum penalty)

    Example:
        >>> result = basel_traffic_light(n_violations=3, n_observations=250, alpha=0.01)
        >>> print(result.zone)  # BaselZone.GREEN
        >>> print(result.capital_multiplier)  # 3.0
    """
    if n_violations < 0:
        raise ValueError(f"n_violations must be >= 0, got {n_violations}")
    if n_observations <= 0:
        raise ValueError(f"n_observations must be > 0, got {n_observations}")
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")

    # Expected violations
    expected_violations = n_observations * alpha
    violation_rate = n_violations / n_observations

    # Compute zone thresholds
    green_threshold, yellow_threshold = compute_zone_thresholds(n_observations, alpha)

    # Classify into zone
    if n_violations <= green_threshold:
        zone = BaselZone.GREEN
        # Base capital multiplier
        capital_multiplier = 3.0
    elif n_violations <= yellow_threshold:
        zone = BaselZone.YELLOW
        # Yellow zone penalty increases with violations
        # Basel: 3.0 + 0.2 per exception above green threshold
        excess_violations = n_violations - green_threshold
        capital_multiplier = 3.0 + 0.2 * excess_violations
    else:
        zone = BaselZone.RED
        # Maximum penalty
        capital_multiplier = 4.0

    return TrafficLightResult(
        zone=zone,
        n_violations=n_violations,
        expected_violations=expected_violations,
        n_observations=n_observations,
        alpha=alpha,
        violation_rate=violation_rate,
        green_threshold=green_threshold,
        yellow_threshold=yellow_threshold,
        capital_multiplier=capital_multiplier,
    )


def compute_zone_thresholds(n_observations: int, alpha: float = 0.01) -> tuple[int, int]:
    """
    Compute zone thresholds for Basel Traffic Light.

    Uses binomial distribution quantiles to determine thresholds.

    Args:
        n_observations: Number of observations
        alpha: VaR significance level

    Returns:
        Tuple of (green_threshold, yellow_threshold)

    Theory:
    -------
    For 99% VaR (alpha=0.01) and 250 days, Basel uses:
    - GREEN: 0-4 exceptions
    - YELLOW: 5-9 exceptions

    These thresholds are based on binomial confidence intervals.

    Example:
        >>> green, yellow = compute_zone_thresholds(n=250, alpha=0.01)
        >>> print(f"GREEN: 0-{green}, YELLOW: {green+1}-{yellow}, RED: >{yellow}")
        GREEN: 0-4, YELLOW: 5-9, RED: >9
    """
    # Basel standard thresholds for 99% VaR, ~250 days
    # These are well-established in the literature
    if 240 <= n_observations <= 260 and 0.009 <= alpha <= 0.011:
        # Standard Basel case: 250 days, 99% VaR
        return (4, 9)

    # For other cases, use binomial quantiles
    # Green threshold: ~95% confidence (conservative)
    # Yellow threshold: ~99.9% confidence (very conservative)
    if SCIPY_AVAILABLE:
        green_threshold = int(scipy_binom.ppf(0.95, n_observations, alpha))
        yellow_threshold = int(scipy_binom.ppf(0.999, n_observations, alpha))
    else:
        # Fallback: use approximation based on expected violations
        expected = n_observations * alpha
        std = math.sqrt(n_observations * alpha * (1 - alpha))

        # Green: E[V] + 1.645 * σ (95% one-sided)
        green_threshold = int(expected + 1.645 * std)

        # Yellow: E[V] + 3.09 * σ (99.9% one-sided)
        yellow_threshold = int(expected + 3.09 * std)

    # Ensure sensible bounds
    green_threshold = max(0, green_threshold)
    yellow_threshold = max(green_threshold + 1, yellow_threshold)

    return (green_threshold, yellow_threshold)


def traffic_light_recommendation(result: TrafficLightResult) -> str:
    """
    Provide regulatory recommendation based on Basel zone.

    Args:
        result: TrafficLightResult from basel_traffic_light()

    Returns:
        Human-readable recommendation string

    Example Output:
    ---------------
    GREEN: "✅ Model performance is acceptable. Continue monitoring."
    YELLOW: "⚠️  Model requires increased monitoring and analysis.
             Consider model recalibration if trend continues."
    RED: "🔴 Model is inadequate. IMMEDIATE ACTION REQUIRED:
         - Increase capital multiplier
         - Revise model methodology
         - Report to risk committee"
    """
    if result.zone == BaselZone.GREEN:
        return (
            f"✅ GREEN ZONE: Model performance is acceptable.\n"
            f"   Violations: {result.n_violations} (expected: {result.expected_violations:.1f})\n"
            f"   Capital Multiplier: {result.capital_multiplier:.2f}\n"
            f"   No action required. Continue periodic monitoring."
        )
    elif result.zone == BaselZone.YELLOW:
        return (
            f"⚠️  YELLOW ZONE: Model requires increased monitoring.\n"
            f"   Violations: {result.n_violations} (expected: {result.expected_violations:.1f})\n"
            f"   Capital Multiplier: {result.capital_multiplier:.2f} "
            f"(+{result.capital_multiplier - 3.0:.2f} penalty)\n"
            f"   Actions:\n"
            f"   1. Analyze violation patterns (clustered? market stress?)\n"
            f"   2. Review model assumptions and calibration\n"
            f"   3. Consider model adjustments if trend persists\n"
            f"   4. Increase monitoring frequency"
        )
    else:  # RED
        return (
            f"🔴 RED ZONE: Model is inadequate. IMMEDIATE ACTION REQUIRED.\n"
            f"   Violations: {result.n_violations} (expected: {result.expected_violations:.1f})\n"
            f"   Capital Multiplier: {result.capital_multiplier:.2f} (MAXIMUM PENALTY)\n"
            f"   Regulatory Actions:\n"
            f"   1. INCREASE capital multiplier to {result.capital_multiplier:.2f}\n"
            f"   2. REVISE model methodology immediately\n"
            f"   3. REPORT to risk committee and regulators\n"
            f"   4. SUSPEND model for trading until fixed\n"
            f"   5. CONDUCT root cause analysis"
        )


# ============================================================================
# Integration: Continuous Monitoring
# ============================================================================


@dataclass
class TrafficLightMonitor:
    """
    Continuous monitoring of VaR model using Traffic Light.

    Usage:
    ------
    >>> monitor = TrafficLightMonitor(alpha=0.01, window=250)
    >>> for date, (var, realized_loss) in daily_data.items():
    ...     result = monitor.update(realized_loss, var)
    ...     if result.zone != BaselZone.GREEN:
    ...         send_alert(result)
    """

    alpha: float = 0.01
    window: int = 250

    def __post_init__(self):
        """Initialize monitoring state."""
        self.violations: list[bool] = []
        self.current_zone: Optional[BaselZone] = None

    def update(self, realized_loss: float, var_estimate: float) -> TrafficLightResult:
        """
        Update monitor with new observation.

        Args:
            realized_loss: Actual loss (positive = loss, negative = gain)
            var_estimate: VaR estimate (positive value)

        Returns:
            Updated TrafficLightResult
        """
        # Check for violation
        is_violation = realized_loss > var_estimate

        # Add to history
        self.violations.append(is_violation)

        # Keep only last window observations
        if len(self.violations) > self.window:
            self.violations = self.violations[-self.window :]

        # Assess current state
        n_violations = sum(self.violations)
        n_observations = len(self.violations)

        result = basel_traffic_light(n_violations, n_observations, self.alpha)

        self.current_zone = result.zone

        return result

    def reset(self):
        """Reset monitoring state."""
        self.violations.clear()
        self.current_zone = None
