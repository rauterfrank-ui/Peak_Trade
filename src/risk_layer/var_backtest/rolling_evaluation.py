"""
Rolling-Window Evaluation für VaR Backtests
============================================

Führt Kupiec POF (UC), Christoffersen Independence (IND) und Conditional Coverage (CC)
Tests über mehrere Rolling Windows aus, um Verdict-Stabilität zu prüfen.

Theory:
-------
Anstatt einen einzelnen Test über die gesamte Sample-Periode zu führen,
werden mehrere overlapping/non-overlapping Windows evaluiert:

- **Pass-Rate**: Wie viele Windows bestehen den Test?
- **Worst p-value**: Niedrigster p-Wert über alle Windows
- **Verdict Stability**: Wie konsistent sind die Ergebnisse?

Use Cases:
----------
1. **Time-Varying Model Quality**: Zeigt ob VaR-Modell über Zeit stabil ist
2. **Regime-Dependent Performance**: Identifiziert Perioden mit schlechter Performance
3. **Early Warning**: Erkennt degradierende Modellqualität früher

References:
-----------
- Christoffersen, P. F. (1998). Evaluating Interval Forecasts.
- Basel Committee (2006). International Convergence of Capital Measurement.

Agent Phase 9B Implementation: Rolling-window UC/IND/CC evaluation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional, Sequence, Union

import pandas as pd

from src.risk_layer.var_backtest.christoffersen_tests import (
    ChristoffersenResult,
    christoffersen_conditional_coverage_test,
    christoffersen_independence_test,
)
from src.risk_layer.var_backtest.kupiec_pof import KupiecPOFOutput, kupiec_pof_test

logger = logging.getLogger(__name__)

# Minimum observations per window
DEFAULT_MIN_WINDOW_SIZE = 100


@dataclass
class RollingWindowResult:
    """
    Result for a single rolling window.

    Attributes:
        window_id: Window identifier (0, 1, 2, ...)
        start_idx: Start index of window
        end_idx: End index of window (exclusive)
        n_observations: Number of observations in window
        n_violations: Number of violations in window
        kupiec: Kupiec POF test result
        independence: Christoffersen Independence test result
        conditional_coverage: Christoffersen CC test result
    """

    window_id: int
    start_idx: int
    end_idx: int
    n_observations: int
    n_violations: int
    kupiec: KupiecPOFOutput
    independence: ChristoffersenResult
    conditional_coverage: ChristoffersenResult

    @property
    def all_passed(self) -> bool:
        """Check if all tests passed for this window."""
        return (
            self.kupiec.is_valid and self.independence.passed and self.conditional_coverage.passed
        )

    def to_dict(self) -> dict:
        """Export to dictionary."""
        return {
            "window_id": self.window_id,
            "start_idx": self.start_idx,
            "end_idx": self.end_idx,
            "n_observations": self.n_observations,
            "n_violations": self.n_violations,
            "kupiec_passed": self.kupiec.is_valid,
            "kupiec_p_value": self.kupiec.p_value,
            "kupiec_lr_stat": self.kupiec.lr_statistic,
            "independence_passed": self.independence.passed,
            "independence_p_value": self.independence.p_value,
            "independence_lr_stat": self.independence.lr_statistic,
            "cc_passed": self.conditional_coverage.passed,
            "cc_p_value": self.conditional_coverage.p_value,
            "cc_lr_stat": self.conditional_coverage.lr_statistic,
            "all_passed": self.all_passed,
        }


@dataclass
class RollingSummary:
    """
    Summary statistics over all rolling windows.

    Attributes:
        n_windows: Total number of windows evaluated
        kupiec_pass_rate: Fraction of windows where Kupiec POF passed
        independence_pass_rate: Fraction where Independence test passed
        cc_pass_rate: Fraction where CC test passed
        all_pass_rate: Fraction where ALL tests passed
        worst_kupiec_p_value: Lowest Kupiec p-value across windows
        worst_independence_p_value: Lowest Independence p-value across windows
        worst_cc_p_value: Lowest CC p-value across windows
        verdict_stability: Score measuring consistency (0=unstable, 1=stable)
        notes: Interpretation guidance
    """

    n_windows: int
    kupiec_pass_rate: float
    independence_pass_rate: float
    cc_pass_rate: float
    all_pass_rate: float
    worst_kupiec_p_value: float
    worst_independence_p_value: float
    worst_cc_p_value: float
    verdict_stability: float
    notes: str

    def to_dict(self) -> dict:
        """Export to dictionary."""
        return {
            "n_windows": self.n_windows,
            "kupiec_pass_rate": self.kupiec_pass_rate,
            "independence_pass_rate": self.independence_pass_rate,
            "cc_pass_rate": self.cc_pass_rate,
            "all_pass_rate": self.all_pass_rate,
            "worst_kupiec_p_value": self.worst_kupiec_p_value,
            "worst_independence_p_value": self.worst_independence_p_value,
            "worst_cc_p_value": self.worst_cc_p_value,
            "verdict_stability": self.verdict_stability,
            "notes": self.notes,
        }


@dataclass
class RollingEvaluationResult:
    """
    Complete rolling evaluation result.

    Attributes:
        windows: List of individual window results
        summary: Summary statistics over all windows
        violations: Original violations series
        timestamps: Optional timestamps for each observation
        window_size: Size of each window
        step_size: Step size between windows
    """

    windows: List[RollingWindowResult]
    summary: RollingSummary
    violations: Sequence[bool]
    timestamps: Optional[pd.DatetimeIndex]
    window_size: int
    step_size: int

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert window results to pandas DataFrame.

        Returns:
            DataFrame with one row per window

        Example:
            >>> result = rolling_evaluation(violations, window_size=250, step_size=50)
            >>> df = result.to_dataframe()
            >>> print(df[['window_id', 'all_passed', 'kupiec_p_value']])
        """
        rows = [w.to_dict() for w in self.windows]
        return pd.DataFrame(rows)

    def to_dict(self) -> dict:
        """Export to dictionary."""
        return {
            "summary": self.summary.to_dict(),
            "windows": [w.to_dict() for w in self.windows],
            "window_size": self.window_size,
            "step_size": self.step_size,
            "n_total_observations": len(self.violations),
        }


def rolling_evaluation(
    violations: Union[Sequence[bool], pd.Series],
    window_size: int,
    step_size: Optional[int] = None,
    var_alpha: float = 0.05,
    test_alpha: float = 0.05,
    min_window_size: int = DEFAULT_MIN_WINDOW_SIZE,
    timestamps: Optional[Union[Sequence, pd.DatetimeIndex]] = None,
) -> RollingEvaluationResult:
    """
    Perform rolling-window evaluation of VaR backtest (UC/IND/CC).

    Args:
        violations: Boolean sequence (True = VaR violation)
        window_size: Size of each rolling window (number of observations)
        step_size: Step size between windows (default: window_size for non-overlapping)
        var_alpha: VaR significance level (e.g., 0.05 for 95% VaR, 0.01 for 99% VaR)
        test_alpha: Significance level for hypothesis tests (default: 0.05)
        min_window_size: Minimum observations per window (default: 100)
        timestamps: Optional timestamps for each observation

    Returns:
        RollingEvaluationResult with window results and summary

    Raises:
        ValueError: If window_size < min_window_size or insufficient data

    Theory:
        For each window W_i:
        - Kupiec POF Test (LR-UC): Tests unconditional coverage
        - Christoffersen IND Test (LR-IND): Tests independence
        - Christoffersen CC Test (LR-CC): Joint test of coverage + independence

        Summary metrics:
        - Pass-Rate: Fraction of windows passing each test
        - Worst p-value: Minimum p-value across windows (most critical)
        - Verdict Stability: Consistency of verdicts across windows

    Example:
        >>> # 500 observations, 5 windows of 250 with 50-step overlap
        >>> result = rolling_evaluation(
        ...     violations,
        ...     window_size=250,
        ...     step_size=50,
        ...     var_alpha=0.01,  # 99% VaR
        ... )
        >>> print(f"Pass Rate: {result.summary.all_pass_rate:.1%}")
        >>> print(f"Worst p-value: {result.summary.worst_kupiec_p_value:.4f}")
        >>> df = result.to_dataframe()
        >>> print(df[['window_id', 'all_passed']])

    Notes:
        - Overlapping windows (step_size < window_size) increase smoothness but reduce independence
        - Non-overlapping windows (step_size = window_size) are statistically more independent
        - Minimum window_size depends on var_alpha (lower alpha → need more observations)
    """
    # Convert to list
    if isinstance(violations, pd.Series):
        violations_list = violations.tolist()
    else:
        violations_list = list(violations)

    n_total = len(violations_list)

    # Validate inputs
    if window_size < min_window_size:
        raise ValueError(
            f"window_size ({window_size}) must be >= min_window_size ({min_window_size})"
        )

    if window_size > n_total:
        raise ValueError(f"window_size ({window_size}) exceeds total observations ({n_total})")

    # Default step_size = window_size (non-overlapping)
    if step_size is None:
        step_size = window_size

    if step_size <= 0:
        raise ValueError(f"step_size must be positive, got {step_size}")

    # Compute window starts
    window_starts = list(range(0, n_total - window_size + 1, step_size))

    if len(window_starts) == 0:
        raise ValueError(
            f"Insufficient data for even one window. Total: {n_total}, window_size: {window_size}"
        )

    logger.info(
        f"Rolling evaluation: {len(window_starts)} windows, size={window_size}, step={step_size}"
    )

    # Evaluate each window
    window_results: List[RollingWindowResult] = []

    for window_id, start_idx in enumerate(window_starts):
        end_idx = start_idx + window_size
        window_violations = violations_list[start_idx:end_idx]

        # Run tests
        try:
            # Kupiec POF (UC)
            confidence_level = 1 - var_alpha
            kupiec_result = kupiec_pof_test(
                window_violations,
                confidence_level=confidence_level,
                significance_level=test_alpha,
                min_observations=min_window_size,
            )

            # Christoffersen Independence (IND)
            independence_result = christoffersen_independence_test(
                window_violations, alpha=test_alpha
            )

            # Christoffersen Conditional Coverage (CC)
            cc_result = christoffersen_conditional_coverage_test(
                window_violations, alpha=test_alpha, var_alpha=var_alpha
            )

            # Create window result
            window_result = RollingWindowResult(
                window_id=window_id,
                start_idx=start_idx,
                end_idx=end_idx,
                n_observations=len(window_violations),
                n_violations=sum(window_violations),
                kupiec=kupiec_result,
                independence=independence_result,
                conditional_coverage=cc_result,
            )

            window_results.append(window_result)

        except Exception as e:
            logger.warning(f"Window {window_id} evaluation failed: {e}. Skipping window.")
            continue

    if len(window_results) == 0:
        raise ValueError("No windows successfully evaluated")

    # Compute summary statistics
    summary = _compute_summary(window_results)

    # Create result
    result = RollingEvaluationResult(
        windows=window_results,
        summary=summary,
        violations=violations_list,
        timestamps=timestamps,
        window_size=window_size,
        step_size=step_size,
    )

    return result


def _compute_summary(window_results: List[RollingWindowResult]) -> RollingSummary:
    """
    Compute summary statistics over all windows.

    Args:
        window_results: List of window results

    Returns:
        RollingSummary with aggregate metrics
    """
    n_windows = len(window_results)

    # Pass rates
    kupiec_passes = sum(1 for w in window_results if w.kupiec.is_valid)
    independence_passes = sum(1 for w in window_results if w.independence.passed)
    cc_passes = sum(1 for w in window_results if w.conditional_coverage.passed)
    all_passes = sum(1 for w in window_results if w.all_passed)

    kupiec_pass_rate = kupiec_passes / n_windows
    independence_pass_rate = independence_passes / n_windows
    cc_pass_rate = cc_passes / n_windows
    all_pass_rate = all_passes / n_windows

    # Worst p-values
    worst_kupiec_p = min(w.kupiec.p_value for w in window_results)
    worst_ind_p = min(w.independence.p_value for w in window_results)
    worst_cc_p = min(w.conditional_coverage.p_value for w in window_results)

    # Verdict stability: measure of consistency
    # Simple metric: fraction of windows with all tests passed
    # More sophisticated: variance of p-values, but all_pass_rate is interpretable
    verdict_stability = all_pass_rate

    # Interpret results
    if all_pass_rate >= 0.9:
        notes = (
            "✅ STABLE: ≥90% of windows passed all tests. "
            "Model shows consistent performance over time."
        )
    elif all_pass_rate >= 0.75:
        notes = (
            "⚠️  MODERATE: 75-90% of windows passed. "
            "Some instability detected. Investigate failing windows."
        )
    elif all_pass_rate >= 0.5:
        notes = (
            "⚠️  UNSTABLE: 50-75% of windows passed. "
            "Significant time-varying performance. Model may be degrading."
        )
    else:
        notes = (
            "❌ CRITICAL: <50% of windows passed. "
            "Model shows poor performance across multiple periods."
        )

    return RollingSummary(
        n_windows=n_windows,
        kupiec_pass_rate=kupiec_pass_rate,
        independence_pass_rate=independence_pass_rate,
        cc_pass_rate=cc_pass_rate,
        all_pass_rate=all_pass_rate,
        worst_kupiec_p_value=worst_kupiec_p,
        worst_independence_p_value=worst_ind_p,
        worst_cc_p_value=worst_cc_p,
        verdict_stability=verdict_stability,
        notes=notes,
    )


def format_rolling_summary(result: RollingEvaluationResult) -> str:
    """
    Format rolling evaluation result as human-readable string.

    Args:
        result: RollingEvaluationResult to format

    Returns:
        Formatted string with summary and window details

    Example:
        >>> result = rolling_evaluation(violations, window_size=250, step_size=50)
        >>> print(format_rolling_summary(result))
    """
    summary = result.summary

    lines = [
        "=" * 70,
        "ROLLING-WINDOW VAR BACKTEST EVALUATION",
        "=" * 70,
        f"Configuration:",
        f"  Window Size:       {result.window_size}",
        f"  Step Size:         {result.step_size}",
        f"  Total Observations: {len(result.violations)}",
        f"  Windows Evaluated:  {summary.n_windows}",
        "",
        "Summary Statistics:",
        f"  Kupiec POF Pass Rate:       {summary.kupiec_pass_rate:6.1%}",
        f"  Independence Pass Rate:     {summary.independence_pass_rate:6.1%}",
        f"  Cond. Coverage Pass Rate:   {summary.cc_pass_rate:6.1%}",
        f"  ALL Tests Pass Rate:        {summary.all_pass_rate:6.1%}",
        "",
        "Worst p-values (across all windows):",
        f"  Kupiec POF:        {summary.worst_kupiec_p_value:.4f}",
        f"  Independence:      {summary.worst_independence_p_value:.4f}",
        f"  Cond. Coverage:    {summary.worst_cc_p_value:.4f}",
        "",
        f"Verdict Stability:  {summary.verdict_stability:.1%}",
        "",
        f"Interpretation: {summary.notes}",
        "=" * 70,
        "",
        "Window Details:",
    ]

    # Add table header
    lines.extend(
        [
            "",
            f"{'Win':>3} | {'Start':>6} | {'End':>6} | {'N':>4} | {'Viol':>4} | "
            f"{'UC':>4} | {'IND':>4} | {'CC':>4} | {'All':>4}",
            "-" * 70,
        ]
    )

    # Add window rows
    for w in result.windows:
        uc_status = "✓" if w.kupiec.is_valid else "✗"
        ind_status = "✓" if w.independence.passed else "✗"
        cc_status = "✓" if w.conditional_coverage.passed else "✗"
        all_status = "✓" if w.all_passed else "✗"

        lines.append(
            f"{w.window_id:3d} | {w.start_idx:6d} | {w.end_idx:6d} | "
            f"{w.n_observations:4d} | {w.n_violations:4d} | "
            f"{uc_status:>4} | {ind_status:>4} | {cc_status:>4} | {all_status:>4}"
        )

    lines.append("=" * 70)

    return "\n".join(lines)


def get_failing_windows(
    result: RollingEvaluationResult,
) -> List[RollingWindowResult]:
    """
    Extract windows that failed at least one test.

    Args:
        result: RollingEvaluationResult

    Returns:
        List of windows where at least one test failed

    Example:
        >>> result = rolling_evaluation(violations, window_size=250)
        >>> failing = get_failing_windows(result)
        >>> for w in failing:
        ...     print(f"Window {w.window_id}: Failed at idx {w.start_idx}-{w.end_idx}")
    """
    return [w for w in result.windows if not w.all_passed]


def get_worst_window(
    result: RollingEvaluationResult,
    criterion: str = "kupiec_p_value",
) -> RollingWindowResult:
    """
    Get window with worst performance according to criterion.

    Args:
        result: RollingEvaluationResult
        criterion: Criterion to use:
            - "kupiec_p_value": Lowest Kupiec p-value
            - "independence_p_value": Lowest Independence p-value
            - "cc_p_value": Lowest CC p-value
            - "n_violations": Highest number of violations

    Returns:
        Window with worst performance

    Raises:
        ValueError: If criterion is unknown or no windows

    Example:
        >>> result = rolling_evaluation(violations, window_size=250)
        >>> worst = get_worst_window(result, criterion="kupiec_p_value")
        >>> print(f"Worst window: {worst.window_id}, p-value: {worst.kupiec.p_value:.4f}")
    """
    if len(result.windows) == 0:
        raise ValueError("No windows to evaluate")

    if criterion == "kupiec_p_value":
        return min(result.windows, key=lambda w: w.kupiec.p_value)
    elif criterion == "independence_p_value":
        return min(result.windows, key=lambda w: w.independence.p_value)
    elif criterion == "cc_p_value":
        return min(result.windows, key=lambda w: w.conditional_coverage.p_value)
    elif criterion == "n_violations":
        return max(result.windows, key=lambda w: w.n_violations)
    else:
        raise ValueError(
            f"Unknown criterion: {criterion}. "
            f"Choose from: kupiec_p_value, independence_p_value, cc_p_value, n_violations"
        )
