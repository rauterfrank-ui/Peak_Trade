"""
Basel Traffic Light System for VaR Model Validation
====================================================

Implements the Basel Committee's traffic light approach for monitoring
VaR model performance.

PLACEHOLDER: Agent A3 implements full Basel Traffic Light logic.

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
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
from scipy.stats import binom

logger = logging.getLogger(__name__)


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
        confidence_level: Confidence level for zone boundaries
    """

    zone: BaselZone
    n_violations: int
    expected_violations: float
    n_observations: int
    alpha: float
    violation_rate: float
    green_threshold: int
    yellow_threshold: int
    confidence_level: float = 0.95

    def __repr__(self) -> str:
        emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}[self.zone.value]
        return (
            f"<BaselTrafficLight: {emoji} {self.zone.value.upper()} | "
            f"Violations={self.n_violations} (expected={self.expected_violations:.1f}, "
            f"rate={self.violation_rate:.2%})>"
        )


def basel_traffic_light(
    n_violations: int,
    n_observations: int,
    alpha: float = 0.01,
    confidence_level: float = 0.95,
) -> TrafficLightResult:
    """
    Basel Traffic Light Assessment for VaR model.

    PLACEHOLDER: Agent A3 implements full logic.

    Args:
        n_violations: Number of observed VaR violations
        n_observations: Total number of observations (e.g., 250 trading days)
        alpha: VaR significance level (default: 0.01 = 99% VaR)
        confidence_level: Confidence level for zone thresholds (default: 0.95)

    Returns:
        TrafficLightResult with zone classification and statistics

    Raises:
        NotImplementedError: Agent A3 must implement this

    Theory:
    -------
    Under the null hypothesis that the VaR model is correct, violations
    follow a Binomial(n, α) distribution.

    Zone boundaries are defined using binomial quantiles:
    - GREEN: violations ≤ F⁻¹(confidence_level/2)
    - YELLOW: F⁻¹(confidence_level/2) < violations ≤ F⁻¹(1 - confidence_level/2)
    - RED: violations > F⁻¹(1 - confidence_level/2)

    where F⁻¹ is the inverse CDF of Binomial(n, α).

    Example (99% VaR, 250 days, 95% confidence):
    ---------------------------------------------
    Expected violations: 250 * 0.01 = 2.5
    GREEN: 0-4 exceptions
    YELLOW: 5-9 exceptions
    RED: ≥10 exceptions

    Note:
    -----
    The Basel framework typically uses 99% VaR (alpha=0.01) and 250 trading days.
    For 95% VaR (alpha=0.05), the thresholds would be different.
    """
    raise NotImplementedError(
        "Agent A3: Implement Basel Traffic Light System.\n"
        "Steps:\n"
        "1. Calculate expected violations: E[V] = n * alpha\n"
        "2. Compute zone thresholds using Binomial(n, alpha) quantiles:\n"
        "   - green_threshold = quantile(0.95) or similar\n"
        "   - yellow_threshold = quantile(0.995) or similar\n"
        "3. Classify based on n_violations:\n"
        "   - GREEN if n_violations <= green_threshold\n"
        "   - YELLOW if green_threshold < n_violations <= yellow_threshold\n"
        "   - RED if n_violations > yellow_threshold\n"
        "4. Return TrafficLightResult"
    )


def compute_zone_thresholds(
    n_observations: int, alpha: float = 0.01, confidence_level: float = 0.95
) -> tuple[int, int]:
    """
    Compute zone thresholds for Basel Traffic Light.

    PLACEHOLDER: Agent A3 implements.

    Args:
        n_observations: Number of observations
        alpha: VaR significance level
        confidence_level: Confidence level for thresholds

    Returns:
        Tuple of (green_threshold, yellow_threshold)

    Raises:
        NotImplementedError: Agent A3 must implement this

    Example:
    --------
    >>> green, yellow = compute_zone_thresholds(n=250, alpha=0.01)
    >>> print(f"GREEN: 0-{green}, YELLOW: {green+1}-{yellow}, RED: >{yellow}")
    """
    raise NotImplementedError(
        "Agent A3: Implement zone threshold calculation using Binomial quantiles"
    )


def traffic_light_recommendation(result: TrafficLightResult) -> str:
    """
    Provide regulatory recommendation based on Basel zone.

    PLACEHOLDER: Agent A3 can implement this as a helper.

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
            "✅ GREEN ZONE: Model performance is acceptable.\n"
            "   No action required. Continue periodic monitoring."
        )
    elif result.zone == BaselZone.YELLOW:
        return (
            "⚠️  YELLOW ZONE: Model requires increased monitoring.\n"
            "   Actions:\n"
            "   1. Analyze violation patterns (clustered? market stress?)\n"
            "   2. Review model assumptions and calibration\n"
            "   3. Consider model adjustments if trend persists\n"
            "   4. Increase monitoring frequency"
        )
    else:  # RED
        return (
            "🔴 RED ZONE: Model is inadequate. IMMEDIATE ACTION REQUIRED.\n"
            "   Regulatory Actions:\n"
            "   1. INCREASE capital multiplier (Basel: +0.2 to +1.0)\n"
            "   2. REVISE model methodology immediately\n"
            "   3. REPORT to risk committee and regulators\n"
            "   4. SUSPEND model for trading until fixed\n"
            "   5. CONDUCT root cause analysis"
        )


# ============================================================
# Integration: Continuous Monitoring
# ============================================================


@dataclass
class TrafficLightMonitor:
    """
    Continuous monitoring of VaR model using Traffic Light.

    PLACEHOLDER: Agent A3 can implement this for live monitoring.

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
    confidence_level: float = 0.95

    def __post_init__(self):
        """Initialize monitoring state."""
        self.violations: list[bool] = []
        self.current_zone: Optional[BaselZone] = None

    def update(self, realized_loss: float, var_estimate: float) -> TrafficLightResult:
        """
        Update monitor with new observation.

        PLACEHOLDER: Agent A3 implements.

        Args:
            realized_loss: Actual loss (positive = loss, negative = gain)
            var_estimate: VaR estimate (positive value)

        Returns:
            Updated TrafficLightResult

        Raises:
            NotImplementedError: Agent A3 must implement this
        """
        raise NotImplementedError(
            "Agent A3: Implement continuous Traffic Light monitoring"
        )

    def reset(self):
        """Reset monitoring state."""
        self.violations.clear()
        self.current_zone = None
