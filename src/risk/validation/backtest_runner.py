"""VaR Backtest Runner.

Aligns returns and VaR series, detects breaches, and runs validation tests.
"""

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from src.risk.validation.kupiec_pof import KupiecResult, kupiec_pof_test
from src.risk.validation.traffic_light import TrafficLightResult, basel_traffic_light
from src.risk.validation.breach_analysis import BreachAnalysis, analyze_breaches


@dataclass(frozen=True)
class BacktestResult:
    """Complete backtest result.

    Attributes:
        breaches: Number of VaR breaches
        observations: Total number of observations
        breach_rate: Observed breach rate (breaches / observations)
        breach_dates: List of timestamps where breaches occurred
        kupiec: Kupiec POF test result
        traffic_light: Basel traffic light result
        breach_analysis: Detailed breach analysis (optional)
    """
    breaches: int
    observations: int
    breach_rate: float
    breach_dates: list
    kupiec: KupiecResult
    traffic_light: TrafficLightResult
    breach_analysis: Optional[BreachAnalysis] = None

    def to_json_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        result = {
            "breaches": self.breaches,
            "observations": self.observations,
            "breach_rate": self.breach_rate,
            "breach_dates": [str(d) for d in self.breach_dates],
            "kupiec": self.kupiec.to_json_dict(),
            "traffic_light": self.traffic_light.to_json_dict(),
        }

        if self.breach_analysis is not None:
            result["breach_analysis"] = self.breach_analysis.to_json_dict()

        return result

    def to_markdown(self) -> str:
        """Generate comprehensive markdown report."""
        report = f"""# VaR Backtest Report

## Summary

| Metric | Value |
|--------|-------|
| Observations | {self.observations} |
| Breaches | {self.breaches} |
| Breach Rate | {self.breach_rate:.2%} |

{self.kupiec.to_markdown()}

{self.traffic_light.to_markdown()}
"""

        if self.breach_analysis is not None:
            report += f"\n{self.breach_analysis.to_markdown()}"

        if self.breach_dates:
            report += f"\n\n## Breach Dates\n\n"
            for i, date in enumerate(self.breach_dates[:10], 1):
                report += f"{i}. {date}\n"
            if len(self.breach_dates) > 10:
                report += f"\n... and {len(self.breach_dates) - 10} more\n"

        return report


def run_var_backtest(
    returns: pd.Series,
    var_series: pd.Series,
    confidence_level: float = 0.99,
    alpha: float = 0.05,
    include_breach_analysis: bool = True,
) -> BacktestResult:
    """Run complete VaR backtest.

    Steps:
    1. Align returns and VaR series by index
    2. Drop NaNs
    3. Detect breaches (realized_loss > var_value)
    4. Run Kupiec POF test
    5. Run Basel traffic light test
    6. Analyze breach patterns (optional)

    Args:
        returns: Return series (negative = loss)
        var_series: VaR estimates (positive = loss magnitude)
        confidence_level: VaR confidence level (e.g., 0.99)
        alpha: Significance level for Kupiec test (default 0.05)
        include_breach_analysis: Whether to include detailed breach analysis

    Returns:
        BacktestResult with all validation metrics

    Raises:
        ValueError: If inputs are invalid

    Example:
        >>> result = run_var_backtest(returns, var_series, confidence_level=0.99)
        >>> print(result.kupiec.is_valid)
        >>> print(result.traffic_light.color)
    """
    # Validate inputs
    if not isinstance(returns, pd.Series):
        raise TypeError(f"returns must be pd.Series, got {type(returns)}")
    if not isinstance(var_series, pd.Series):
        raise TypeError(f"var_series must be pd.Series, got {type(var_series)}")

    # Detect breaches
    breach_mask, aligned_returns, aligned_var = detect_breaches(returns, var_series)

    # Count breaches
    breaches = int(breach_mask.sum())
    observations = len(breach_mask)
    breach_rate = breaches / observations if observations > 0 else 0.0

    # Get breach dates
    breach_dates = breach_mask[breach_mask].index.tolist()

    # Run Kupiec test
    kupiec = kupiec_pof_test(
        breaches=breaches,
        observations=observations,
        confidence_level=confidence_level,
        alpha=alpha,
    )

    # Run traffic light test
    traffic_light = basel_traffic_light(
        breaches=breaches,
        observations=observations,
        confidence_level=confidence_level,
    )

    # Breach analysis (optional)
    breach_analysis = None
    if include_breach_analysis and breaches > 0:
        breach_analysis = analyze_breaches(breach_mask)

    return BacktestResult(
        breaches=breaches,
        observations=observations,
        breach_rate=breach_rate,
        breach_dates=breach_dates,
        kupiec=kupiec,
        traffic_light=traffic_light,
        breach_analysis=breach_analysis,
    )


def detect_breaches(
    returns: pd.Series,
    var_series: pd.Series,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Detect VaR breaches.

    Breach Logic:
    - Align returns and VaR series by index
    - Drop NaNs
    - realized_loss = -returns (negative return = positive loss)
    - breach = realized_loss > var_value

    Args:
        returns: Return series (negative = loss)
        var_series: VaR estimates (positive = loss magnitude)

    Returns:
        (breach_mask, aligned_returns, aligned_var) tuple
        - breach_mask: Boolean series indicating breaches
        - aligned_returns: Aligned and cleaned returns
        - aligned_var: Aligned and cleaned VaR series

    Example:
        >>> breach_mask, ret, var = detect_breaches(returns, var_series)
        >>> breach_count = breach_mask.sum()
    """
    # Align by index (inner join)
    aligned = pd.DataFrame({
        'returns': returns,
        'var': var_series,
    }).dropna()

    if len(aligned) == 0:
        # No valid data points
        return (
            pd.Series(dtype=bool),
            pd.Series(dtype=float),
            pd.Series(dtype=float),
        )

    aligned_returns = aligned['returns']
    aligned_var = aligned['var']

    # Compute realized losses (negative return = positive loss)
    realized_loss = -aligned_returns

    # Detect breaches (realized loss exceeds VaR)
    breach_mask = realized_loss > aligned_var

    return breach_mask, aligned_returns, aligned_var
