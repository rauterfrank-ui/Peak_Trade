"""Basel Traffic Light System for VaR Model Validation.

Reference:
---------
Basel Committee on Banking Supervision (1996):
"Supervisory Framework for the Use of Backtesting"
"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class TrafficLightResult:
    """Result of Basel Traffic Light assessment.

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
    # Validation
    if observations < 0:
        raise ValueError(f"observations must be non-negative, got {observations}")
    if breaches < 0:
        raise ValueError(f"breaches must be non-negative, got {breaches}")
    if breaches > observations:
        raise ValueError(f"breaches ({breaches}) cannot exceed observations ({observations})")
    if not 0 < confidence_level < 1:
        raise ValueError(f"confidence_level must be in (0, 1), got {confidence_level}")

    # Get thresholds
    green_threshold, yellow_threshold = get_traffic_light_thresholds(observations, confidence_level)

    # Classify
    if breaches <= green_threshold:
        color = "green"
    elif breaches <= yellow_threshold:
        color = "yellow"
    else:
        color = "red"

    return TrafficLightResult(
        color=color,
        breaches=breaches,
        observations=observations,
        green_threshold=green_threshold,
        yellow_threshold=yellow_threshold,
    )


def get_traffic_light_thresholds(
    observations: int,
    confidence_level: float = 0.99,
) -> tuple[int, int]:
    """Get Basel traffic light thresholds.

    For 99% VaR and ~250 observations:
    - Green: 0-4 breaches
    - Yellow: 5-9 breaches
    - Red: ≥10 breaches

    For other observation counts, scale proportionally.

    Args:
        observations: Total number of observations
        confidence_level: VaR confidence level

    Returns:
        (green_threshold, yellow_threshold) tuple

    Notes:
        Basel standard thresholds are defined for 250 observations
        and 99% VaR. We scale these proportionally for other counts.
    """
    # Basel standard thresholds (250 obs, 99% VaR)
    basel_observations = 250
    basel_green = 4
    basel_yellow = 9

    if observations == 0:
        return (0, 0)

    # Scale thresholds proportionally
    scale_factor = observations / basel_observations

    green_threshold = int(basel_green * scale_factor)
    yellow_threshold = int(basel_yellow * scale_factor)

    # Ensure yellow > green
    if yellow_threshold <= green_threshold:
        yellow_threshold = green_threshold + 1

    return (green_threshold, yellow_threshold)
