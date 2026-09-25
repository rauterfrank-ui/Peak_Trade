"""Basel Traffic Light System for VaR Model Validation.

**DEPRECATED IMPORT PATH**
This module is now a thin compatibility wrapper.
Prefer importing from: src.risk_layer.var_backtest.traffic_light

The canonical implementation lives in src/risk_layer/var_backtest/traffic_light.py
with full Basel features (capital multipliers, monitoring, recommendations).
This module maintains the legacy API for backward compatibility with zero breaking changes.

Reference:
---------
Basel Committee on Banking Supervision (1996):
"Supervisory Framework for the Use of Backtesting"
"""

import warnings
from dataclasses import dataclass
from typing import Literal

# Import from canonical engine
from src.risk_layer.var_backtest.traffic_light import (
    basel_traffic_light as _canonical_basel_traffic_light,
    compute_zone_thresholds as _canonical_compute_zone_thresholds,
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
        "src.risk.validation.traffic_light is deprecated; "
        "prefer src.risk_layer.var_backtest.traffic_light",
        DeprecationWarning,
        stacklevel=3,
    )


# Emit warning on module import (guarded)
_maybe_warn_deprecated()


# ============================================================================
# Legacy API: Dataclass & Functions
# ============================================================================


@dataclass(frozen=True)
class TrafficLightResult:
    """Result of Basel Traffic Light assessment.

    This is the legacy dataclass API maintained for backward compatibility.
    The canonical engine uses a richer dataclass with BaselZone enum and capital_multiplier.

    Attributes:
        color: Traffic light color ('green', 'yellow', 'red')
        breaches: Number of VaR breaches observed
        observations: Total number of observations
        green_threshold: Maximum breaches for green zone
        yellow_threshold: Maximum breaches for yellow zone
    """

    color: Literal["green", "yellow", "red"]
    breaches: int
    observations: int
    green_threshold: int
    yellow_threshold: int

    def to_json_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "color": self.color,
            "breaches": self.breaches,
            "observations": self.observations,
            "green_threshold": self.green_threshold,
            "yellow_threshold": self.yellow_threshold,
            "breach_rate": self.breaches / self.observations if self.observations > 0 else 0.0,
        }

    def to_markdown(self) -> str:
        """Generate markdown report."""
        emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}[self.color]

        return f"""## Basel Traffic Light Result

**Status:** {emoji} **{self.color.upper()} ZONE**

| Metric | Value |
|--------|-------|
| Observations | {self.observations} |
| Breaches | {self.breaches} |
| Breach Rate | {self.breaches / self.observations if self.observations > 0 else 0:.2%} |
| Green Threshold | ≤ {self.green_threshold} |
| Yellow Threshold | {self.green_threshold + 1}-{self.yellow_threshold} |
| Red Threshold | ≥ {self.yellow_threshold + 1} |

**Interpretation:**
- **Green Zone:** Model is acceptable, no action required
- **Yellow Zone:** Model requires increased monitoring
- **Red Zone:** Model is inadequate, must be revised
"""


def basel_traffic_light(
    breaches: int,
    observations: int,
    confidence_level: float = 0.99,
) -> TrafficLightResult:
    """Classify VaR model using Basel Traffic Light System.

    **WRAPPER**: This function now delegates to the canonical engine
    (src.risk_layer.var_backtest.traffic_light.basel_traffic_light) for all computation.

    Zones (for 99% VaR, 250 observations):
    - Green: 0-4 breaches (model acceptable)
    - Yellow: 5-9 breaches (increased monitoring)
    - Red: ≥10 breaches (model inadequate)

    Args:
        breaches: Number of VaR breaches
        observations: Total number of observations
        confidence_level: VaR confidence level (default 0.99)

    Returns:
        TrafficLightResult with color classification

    Raises:
        ValueError: If inputs are invalid

    Example:
        >>> result = basel_traffic_light(breaches=5, observations=250)
        >>> print(result.color)  # 'yellow'
    """
    # Validation (canonical engine also validates, but check early for better error messages)
    if observations < 0:
        raise ValueError(f"observations must be non-negative, got {observations}")
    if breaches < 0:
        raise ValueError(f"breaches must be non-negative, got {breaches}")
    if breaches > observations:
        raise ValueError(f"breaches ({breaches}) cannot exceed observations ({observations})")
    if not 0 < confidence_level < 1:
        raise ValueError(f"confidence_level must be in (0, 1), got {confidence_level}")

    # Handle edge case: zero observations (legacy behavior)
    # Canonical engine doesn't allow this, but legacy code does
    if observations == 0:
        return TrafficLightResult(
            color="green",  # Default to green for empty data
            breaches=0,
            observations=0,
            green_threshold=0,
            yellow_threshold=0,
        )

    # Convert confidence_level to alpha (e.g., 0.99 → 0.01)
    alpha = 1.0 - confidence_level

    # Delegate to canonical engine
    # Canonical API: basel_traffic_light(n_violations, n_observations, alpha)
    try:
        canonical_result = _canonical_basel_traffic_light(
            n_violations=breaches,
            n_observations=observations,
            alpha=alpha,
        )
    except ValueError as e:
        # Should not happen if we validated correctly, but safety first
        raise ValueError(f"Canonical engine rejected inputs: {e}")

    # Map canonical result to legacy TrafficLightResult
    # Canonical has BaselZone enum, we need color string
    color = canonical_result.zone.value  # BaselZone.GREEN → "green"

    return TrafficLightResult(
        color=color,
        breaches=breaches,
        observations=observations,
        green_threshold=canonical_result.green_threshold,
        yellow_threshold=canonical_result.yellow_threshold,
    )


def get_traffic_light_thresholds(
    observations: int,
    confidence_level: float = 0.99,
) -> tuple[int, int]:
    """Get Basel traffic light thresholds.

    **WRAPPER**: This function now delegates to the canonical engine
    (src.risk_layer.var_backtest.traffic_light.compute_zone_thresholds).

    For 99% VaR and ~250 observations:
    - Green: 0-4 breaches
    - Yellow: 5-9 breaches
    - Red: ≥10 breaches

    Args:
        observations: Total number of observations
        confidence_level: VaR confidence level (default 0.99)

    Returns:
        (green_threshold, yellow_threshold) tuple

    Notes:
        Basel standard thresholds are defined for 250 observations
        and 99% VaR. The canonical engine uses binomial distribution
        for accurate threshold computation.
    """
    # Convert confidence_level to alpha
    alpha = 1.0 - confidence_level

    # Delegate to canonical engine
    # Canonical API: compute_zone_thresholds(n_observations, alpha)
    green_threshold, yellow_threshold = _canonical_compute_zone_thresholds(observations, alpha)

    return (green_threshold, yellow_threshold)
