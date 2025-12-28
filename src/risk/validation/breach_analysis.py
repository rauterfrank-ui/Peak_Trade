"""Breach Analysis for VaR Backtesting.

Analyzes patterns in VaR breaches including streaks, gaps, and timing.
"""

from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class BreachAnalysis:
    """Detailed analysis of VaR breaches.

    Attributes:
        max_consecutive: Maximum consecutive breaches (longest streak)
        avg_gap: Average gap between breaches (in observations)
        gaps: List of gaps between consecutive breaches
        streaks: List of consecutive breach counts
        first_breach: Timestamp of first breach
        last_breach: Timestamp of last breach
        total_breaches: Total number of breaches
        total_observations: Total number of observations
    """
    max_consecutive: int
    avg_gap: Optional[float]
    gaps: list[int]
    streaks: list[int]
    first_breach: Optional[pd.Timestamp]
    last_breach: Optional[pd.Timestamp]
    total_breaches: int
    total_observations: int

    def to_json_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "max_consecutive": self.max_consecutive,
            "avg_gap": self.avg_gap,
            "gaps": self.gaps,
            "streaks": self.streaks,
            "first_breach": str(self.first_breach) if self.first_breach is not None else None,
            "last_breach": str(self.last_breach) if self.last_breach is not None else None,
            "total_breaches": self.total_breaches,
            "total_observations": self.total_observations,
        }

    def to_markdown(self) -> str:
        """Generate markdown report."""
        return f"""## Breach Pattern Analysis

| Metric | Value |
|--------|-------|
| Total Breaches | {self.total_breaches} |
| Max Consecutive | {self.max_consecutive} |
| Average Gap | {self.avg_gap:.1f} obs if self.avg_gap is not None else 'N/A' |
| Number of Streaks | {len(self.streaks)} |
| First Breach | {self.first_breach if self.first_breach is not None else 'N/A'} |
| Last Breach | {self.last_breach if self.last_breach is not None else 'N/A'} |

**Interpretation:**
- Max consecutive breaches: {self.max_consecutive} (clustering indicator)
- Average gap: {self.avg_gap:.1f} obs if self.avg_gap is not None else 'N/A' (breach frequency)
"""


def analyze_breaches(breach_mask: pd.Series) -> BreachAnalysis:
    """Analyze breach patterns.

    Computes:
    - Maximum consecutive breaches (clustering)
    - Average gap between breaches
    - List of all gaps and streaks
    - First and last breach timestamps

    Args:
        breach_mask: Boolean series indicating breaches

    Returns:
        BreachAnalysis with pattern statistics

    Example:
        >>> analysis = analyze_breaches(breach_mask)
        >>> print(analysis.max_consecutive)  # Longest streak
        >>> print(analysis.avg_gap)  # Average gap between breaches
    """
    total_observations = len(breach_mask)
    breach_indices = breach_mask[breach_mask].index
    total_breaches = len(breach_indices)

    if total_breaches == 0:
        # No breaches
        return BreachAnalysis(
            max_consecutive=0,
            avg_gap=None,
            gaps=[],
            streaks=[],
            first_breach=None,
            last_breach=None,
            total_breaches=0,
            total_observations=total_observations,
        )

    # First and last breach
    first_breach = breach_indices[0]
    last_breach = breach_indices[-1]

    # Compute streaks and gaps
    streaks = []
    gaps = []

    current_streak = 0
    last_breach_idx = None

    for idx in range(len(breach_mask)):
        is_breach = breach_mask.iloc[idx]

        if is_breach:
            current_streak += 1

            if last_breach_idx is not None:
                gap = idx - last_breach_idx - 1
                if gap > 0:
                    gaps.append(gap)

            last_breach_idx = idx
        else:
            if current_streak > 0:
                streaks.append(current_streak)
                current_streak = 0

    # Add final streak if any
    if current_streak > 0:
        streaks.append(current_streak)

    # Compute statistics
    max_consecutive = max(streaks) if streaks else 0
    avg_gap = sum(gaps) / len(gaps) if gaps else None

    return BreachAnalysis(
        max_consecutive=max_consecutive,
        avg_gap=avg_gap,
        gaps=gaps,
        streaks=streaks,
        first_breach=first_breach,
        last_breach=last_breach,
        total_breaches=total_breaches,
        total_observations=total_observations,
    )


def compute_breach_statistics(breach_mask: pd.Series) -> dict:
    """Compute basic breach statistics.

    Args:
        breach_mask: Boolean series indicating breaches

    Returns:
        Dictionary with breach statistics

    Example:
        >>> stats = compute_breach_statistics(breach_mask)
        >>> print(stats['breach_rate'])
        >>> print(stats['breach_count'])
    """
    total = len(breach_mask)
    breaches = int(breach_mask.sum())
    breach_rate = breaches / total if total > 0 else 0.0

    return {
        "breach_count": breaches,
        "observations": total,
        "breach_rate": breach_rate,
        "non_breach_count": total - breaches,
    }
