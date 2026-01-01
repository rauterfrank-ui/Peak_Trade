"""
Auto-Pause Policy - WP1C (Phase 1 Shadow Trading)

Recommends PAUSE based on drift thresholds.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from src.observability.drift.comparator import DriftMetrics

logger = logging.getLogger(__name__)


@dataclass
class PauseRecommendation:
    """
    Pause recommendation.

    Attributes:
        should_pause: Whether to pause
        severity: Severity level ("LOW" | "MEDIUM" | "HIGH" | "CRITICAL")
        reason_codes: List of reason codes
        details: Additional details
    """

    should_pause: bool
    severity: str
    reason_codes: List[str]
    details: dict

    def to_dict(self) -> dict:
        """Convert to dict."""
        return {
            "should_pause": self.should_pause,
            "severity": self.severity,
            "reason_codes": self.reason_codes,
            "details": self.details,
        }


class AutoPausePolicy:
    """
    Auto-pause policy based on drift thresholds.

    Recommends PAUSE when drift exceeds configured thresholds.

    This is a **callable policy** - returns recommendation but does not
    execute pause itself. Integration layer handles actual pause.

    Usage:
        >>> policy = AutoPausePolicy(
        ...     match_rate_threshold=0.85,
        ...     price_divergence_threshold=3.0,
        ... )
        >>> recommendation = policy.evaluate(metrics)
        >>> if recommendation.should_pause:
        ...     pause_trading()
    """

    def __init__(
        self,
        match_rate_threshold: float = 0.85,  # Pause if < 85%
        price_divergence_threshold: float = 3.0,  # Pause if > 3%
        quantity_divergence_threshold: float = 10.0,  # Pause if > 10%
        min_signals_for_evaluation: int = 10,  # Need >= 10 signals
    ):
        """
        Initialize auto-pause policy.

        Args:
            match_rate_threshold: Match rate threshold (pause if below)
            price_divergence_threshold: Price divergence threshold (pause if above)
            quantity_divergence_threshold: Quantity divergence threshold (pause if above)
            min_signals_for_evaluation: Minimum signals required for evaluation
        """
        self.match_rate_threshold = match_rate_threshold
        self.price_divergence_threshold = price_divergence_threshold
        self.quantity_divergence_threshold = quantity_divergence_threshold
        self.min_signals_for_evaluation = min_signals_for_evaluation

    def evaluate(self, metrics: DriftMetrics) -> PauseRecommendation:
        """
        Evaluate drift metrics and recommend pause if needed.

        Args:
            metrics: Drift metrics

        Returns:
            PauseRecommendation
        """
        reason_codes = []
        details = {}

        # Check minimum signals
        if metrics.total_signals_shadow < self.min_signals_for_evaluation:
            return PauseRecommendation(
                should_pause=False,
                severity="INSUFFICIENT_DATA",
                reason_codes=["INSUFFICIENT_SIGNALS"],
                details={
                    "signals_required": self.min_signals_for_evaluation,
                    "signals_observed": metrics.total_signals_shadow,
                },
            )

        # Check match rate
        if metrics.match_rate < self.match_rate_threshold:
            reason_codes.append("LOW_MATCH_RATE")
            details["match_rate"] = metrics.match_rate
            details["match_rate_threshold"] = self.match_rate_threshold

        # Check price divergence
        if abs(metrics.avg_price_divergence) > self.price_divergence_threshold:
            reason_codes.append("HIGH_PRICE_DIVERGENCE")
            details["price_divergence"] = metrics.avg_price_divergence
            details["price_threshold"] = self.price_divergence_threshold

        # Check quantity divergence
        if abs(metrics.avg_quantity_divergence) > self.quantity_divergence_threshold:
            reason_codes.append("HIGH_QUANTITY_DIVERGENCE")
            details["quantity_divergence"] = metrics.avg_quantity_divergence
            details["quantity_threshold"] = self.quantity_divergence_threshold

        # Determine severity
        severity = self._determine_severity(metrics)

        # Should pause?
        should_pause = len(reason_codes) > 0

        if should_pause:
            logger.warning(f"Auto-pause recommended: severity={severity} reasons={reason_codes}")

        return PauseRecommendation(
            should_pause=should_pause,
            severity=severity,
            reason_codes=reason_codes,
            details=details,
        )

    def _determine_severity(self, metrics: DriftMetrics) -> str:
        """
        Determine drift severity.

        Args:
            metrics: Drift metrics

        Returns:
            Severity level
        """
        if metrics.match_rate < 0.70:
            return "CRITICAL"
        elif metrics.match_rate < 0.80:
            return "HIGH"
        elif metrics.match_rate < 0.90:
            return "MEDIUM"
        else:
            return "LOW"
