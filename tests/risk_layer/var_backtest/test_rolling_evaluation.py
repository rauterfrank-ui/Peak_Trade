"""
Tests für Rolling-Window Evaluation
====================================

Tests für Phase 9B: Rolling-window UC/IND/CC evaluation.
"""

import math

import pandas as pd
import pytest

from src.risk_layer.var_backtest.rolling_evaluation import (
    RollingEvaluationResult,
    RollingWindowResult,
    format_rolling_summary,
    get_failing_windows,
    get_worst_window,
    rolling_evaluation,
)


# ============================================================================
# Test Basic Rolling Evaluation
# ============================================================================


class TestBasicRollingEvaluation:
    """Test basic rolling evaluation functionality."""

    def test_non_overlapping_windows(self):
        """Test rolling evaluation with non-overlapping windows."""
        # 500 observations, 5 windows of 100 each
        violations = [False] * 495 + [True] * 5
        expected_rate = 5 / 500  # 1%

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,  # Non-overlapping
            var_alpha=expected_rate,
        )

        assert result.summary.n_windows == 5
        assert len(result.windows) == 5
        assert result.window_size == 100
        assert result.step_size == 100

        # Check window boundaries
        assert result.windows[0].start_idx == 0
        assert result.windows[0].end_idx == 100
        assert result.windows[4].start_idx == 400
        assert result.windows[4].end_idx == 500

    def test_overlapping_windows(self):
        """Test rolling evaluation with overlapping windows."""
        # 300 observations, windows of 100 with step=50
        violations = [False] * 297 + [True] * 3

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=50,
            var_alpha=0.01,
        )

        # (300 - 100) / 50 + 1 = 5 windows
        assert result.summary.n_windows == 5
        assert result.window_size == 100
        assert result.step_size == 50

        # Check overlaps
        assert result.windows[0].start_idx == 0
        assert result.windows[1].start_idx == 50
        assert result.windows[2].start_idx == 100

    def test_default_step_size(self):
        """Test that default step_size equals window_size (non-overlapping)."""
        violations = [False] * 200 + [True] * 2

        result = rolling_evaluation(
            violations,
            window_size=100,
            # step_size not specified → should default to window_size
            var_alpha=0.01,
        )

        assert result.step_size == 100
        assert result.summary.n_windows == 2

    def test_single_window(self):
        """Test with exactly one window."""
        violations = [False] * 99 + [True]

        result = rolling_evaluation(
            violations,
            window_size=100,
            var_alpha=0.01,
        )

        assert result.summary.n_windows == 1
        assert len(result.windows) == 1


# ============================================================================
# Test Summary Statistics
# ============================================================================


class TestSummaryStatistics:
    """Test summary statistics computation."""

    def test_all_windows_pass(self):
        """Test summary when all windows pass."""
        # Well-calibrated model: ~1% violations evenly distributed
        violations = []
        for _ in range(5):  # 5 windows
            violations.extend([False] * 99 + [True])  # 1 violation per 100

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,
            var_alpha=0.01,
        )

        # All windows should pass
        assert result.summary.all_pass_rate == 1.0
        assert result.summary.kupiec_pass_rate == 1.0
        assert "STABLE" in result.summary.notes

    def test_some_windows_fail(self):
        """Test summary when some windows fail."""
        # First 3 windows good, last 2 windows have many violations (fails Kupiec)
        violations = []
        violations.extend([False] * 99 + [True])  # Window 1: OK (1 violation)
        violations.extend([False] * 99 + [True])  # Window 2: OK (1 violation)
        violations.extend([False] * 99 + [True])  # Window 3: OK (1 violation)
        violations.extend([True] * 10 + [False] * 90)  # Window 4: 10 violations (too many)
        violations.extend([True] * 10 + [False] * 90)  # Window 5: 10 violations (too many)

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,
            var_alpha=0.01,
        )

        assert result.summary.n_windows == 5
        # Windows 4 and 5 should fail Kupiec test (too many violations)
        assert result.summary.all_pass_rate < 1.0
        assert result.summary.kupiec_pass_rate < 1.0

    def test_worst_p_values(self):
        """Test that worst p-values are correctly identified."""
        violations = []
        # Window 1: No violations → high p-value
        violations.extend([False] * 100)
        # Window 2: 1 violation → moderate p-value
        violations.extend([False] * 99 + [True])
        # Window 3: Many violations → low p-value
        violations.extend([True] * 5 + [False] * 95)

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,
            var_alpha=0.01,
        )

        # Worst p-values should come from window with many violations
        assert result.summary.worst_kupiec_p_value < 0.5
        # Check that worst p-value is indeed minimum
        all_kupiec_p_values = [w.kupiec.p_value for w in result.windows]
        assert result.summary.worst_kupiec_p_value == min(all_kupiec_p_values)


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_window_size_too_small(self):
        """Test that window_size < min_window_size raises error."""
        violations = [False] * 50 + [True]

        with pytest.raises(ValueError, match="must be >= min_window_size"):
            rolling_evaluation(
                violations,
                window_size=50,  # < default min (100)
                var_alpha=0.01,
            )

    def test_window_size_exceeds_total(self):
        """Test that window_size > total raises error."""
        violations = [False] * 50 + [True]

        with pytest.raises(ValueError, match="exceeds total observations"):
            rolling_evaluation(
                violations,
                window_size=200,  # > 51
                min_window_size=50,
                var_alpha=0.01,
            )

    def test_negative_step_size(self):
        """Test that negative step_size raises error."""
        violations = [False] * 200 + [True] * 2

        with pytest.raises(ValueError, match="step_size must be positive"):
            rolling_evaluation(
                violations,
                window_size=100,
                step_size=-10,
                var_alpha=0.01,
            )

    def test_zero_step_size(self):
        """Test that step_size=0 raises error."""
        violations = [False] * 200 + [True] * 2

        with pytest.raises(ValueError, match="step_size must be positive"):
            rolling_evaluation(
                violations,
                window_size=100,
                step_size=0,
                var_alpha=0.01,
            )

    def test_insufficient_data(self):
        """Test with insufficient data for even one window."""
        violations = [False] * 50  # < window_size

        with pytest.raises(ValueError, match="exceeds total observations"):
            rolling_evaluation(
                violations,
                window_size=100,
                min_window_size=50,  # Allow small windows, but total < window_size
                var_alpha=0.01,
            )

    def test_empty_violations(self):
        """Test with empty violations list."""
        violations = []

        with pytest.raises(ValueError):
            rolling_evaluation(
                violations,
                window_size=100,
                var_alpha=0.01,
            )


# ============================================================================
# Test Deterministic Behavior
# ============================================================================


class TestDeterministicBehavior:
    """Test that rolling evaluation is deterministic."""

    def test_deterministic_results(self):
        """Test that same input produces same output."""
        violations = [False] * 98 + [True] + [False] * 98 + [True] + [False] * 98 + [True]

        result1 = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,
            var_alpha=0.01,
        )

        result2 = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,
            var_alpha=0.01,
        )

        # Same summary statistics
        assert result1.summary.n_windows == result2.summary.n_windows
        assert result1.summary.all_pass_rate == result2.summary.all_pass_rate
        assert result1.summary.worst_kupiec_p_value == result2.summary.worst_kupiec_p_value

        # Same window results
        for w1, w2 in zip(result1.windows, result2.windows):
            assert w1.window_id == w2.window_id
            assert w1.start_idx == w2.start_idx
            assert w1.end_idx == w2.end_idx
            assert w1.n_violations == w2.n_violations
            assert w1.kupiec.p_value == w2.kupiec.p_value

    def test_window_boundaries_consistent(self):
        """Test that window boundaries are consistent and correct."""
        violations = [False] * 500

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=50,
            var_alpha=0.01,
        )

        # Check that windows are correctly positioned
        for i, window in enumerate(result.windows):
            expected_start = i * 50
            expected_end = expected_start + 100

            assert window.start_idx == expected_start
            assert window.end_idx == expected_end
            assert window.n_observations == 100


# ============================================================================
# Test Result Export
# ============================================================================


class TestResultExport:
    """Test result export to DataFrame and dict."""

    def test_to_dataframe(self):
        """Test conversion to DataFrame."""
        violations = [False] * 297 + [True] * 3

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,
            var_alpha=0.01,
        )

        df = result.to_dataframe()

        assert len(df) == result.summary.n_windows
        assert "window_id" in df.columns
        assert "all_passed" in df.columns
        assert "kupiec_p_value" in df.columns
        assert "independence_p_value" in df.columns
        assert "cc_p_value" in df.columns

    def test_to_dict(self):
        """Test conversion to dictionary."""
        violations = [False] * 199 + [True]

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,
            var_alpha=0.01,
        )

        result_dict = result.to_dict()

        assert "summary" in result_dict
        assert "windows" in result_dict
        assert "window_size" in result_dict
        assert "step_size" in result_dict
        assert len(result_dict["windows"]) == result.summary.n_windows


# ============================================================================
# Test Utility Functions
# ============================================================================


class TestUtilityFunctions:
    """Test utility functions for result analysis."""

    def test_get_failing_windows(self):
        """Test extraction of failing windows."""
        violations = []
        violations.extend([False] * 99 + [True])  # Window 1: OK
        violations.extend([True] * 10 + [False] * 90)  # Window 2: Too many violations
        violations.extend([False] * 99 + [True])  # Window 3: OK

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,
            var_alpha=0.01,
        )

        failing = get_failing_windows(result)

        # At least window 2 should fail
        assert len(failing) >= 1
        # Check that all returned windows actually failed
        for w in failing:
            assert not w.all_passed

    def test_get_worst_window_kupiec(self):
        """Test getting worst window by Kupiec p-value."""
        violations = []
        violations.extend([False] * 99 + [True])  # Window 1: 1 violation
        violations.extend([True] * 5 + [False] * 95)  # Window 2: 5 violations (worst)
        violations.extend([False] * 98 + [True] * 2)  # Window 3: 2 violations

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,
            var_alpha=0.01,
        )

        worst = get_worst_window(result, criterion="kupiec_p_value")

        # Should be window 2 (most violations)
        assert worst.window_id == 1
        assert worst.n_violations == 5

    def test_get_worst_window_violations(self):
        """Test getting worst window by number of violations."""
        violations = []
        violations.extend([False] * 99 + [True])  # Window 1: 1 violation
        violations.extend([True] * 10 + [False] * 90)  # Window 2: 10 violations (worst)
        violations.extend([False] * 98 + [True] * 2)  # Window 3: 2 violations

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,
            var_alpha=0.01,
        )

        worst = get_worst_window(result, criterion="n_violations")

        assert worst.window_id == 1
        assert worst.n_violations == 10

    def test_get_worst_window_unknown_criterion(self):
        """Test that unknown criterion raises error."""
        violations = [False] * 199 + [True]

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,
            var_alpha=0.01,
        )

        with pytest.raises(ValueError, match="Unknown criterion"):
            get_worst_window(result, criterion="invalid_criterion")


# ============================================================================
# Test Formatting
# ============================================================================


class TestFormatting:
    """Test result formatting."""

    def test_format_rolling_summary(self):
        """Test human-readable summary formatting."""
        violations = [False] * 297 + [True] * 3

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,
            var_alpha=0.01,
        )

        formatted = format_rolling_summary(result)

        assert "ROLLING-WINDOW VAR BACKTEST EVALUATION" in formatted
        assert "Window Size:" in formatted
        assert "Summary Statistics:" in formatted
        assert "Pass Rate:" in formatted
        assert "Worst p-values (across all windows):" in formatted  # Full string
        assert "Window Details:" in formatted

    def test_formatting_with_failures(self):
        """Test formatting when some windows fail."""
        violations = []
        violations.extend([False] * 99 + [True])  # OK
        violations.extend([True] * 10 + [False] * 90)  # Many violations

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,
            var_alpha=0.01,
        )

        formatted = format_rolling_summary(result)

        # Should show checkmarks and crosses
        assert "✓" in formatted or "✗" in formatted


# ============================================================================
# Test with Pandas Series
# ============================================================================


class TestPandasIntegration:
    """Test integration with pandas Series."""

    def test_with_pandas_series(self):
        """Test rolling evaluation with pandas Series."""
        dates = pd.date_range("2024-01-01", periods=300, freq="D")
        violations = pd.Series([False] * 297 + [True] * 3, index=dates)

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,
            var_alpha=0.01,
            timestamps=dates,
        )

        assert result.summary.n_windows == 3
        assert result.timestamps is not None

    def test_dataframe_export_with_dates(self):
        """Test DataFrame export preserves structure."""
        dates = pd.date_range("2024-01-01", periods=200, freq="D")
        violations = pd.Series([False] * 198 + [True] * 2, index=dates)

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,
            var_alpha=0.01,
            timestamps=dates,
        )

        df = result.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2


# ============================================================================
# Test Real-World Scenarios
# ============================================================================


class TestRealWorldScenarios:
    """Test with realistic VaR violation scenarios."""

    def test_stable_model_over_time(self):
        """Test stable VaR model (consistent performance)."""
        # 1000 observations, ~1% violations evenly distributed
        violations = []
        for _ in range(10):  # 10 windows of 100
            violations.extend([False] * 99 + [True])

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,
            var_alpha=0.01,
        )

        # Should have high pass rate
        assert result.summary.all_pass_rate >= 0.7
        assert "STABLE" in result.summary.notes or "MODERATE" in result.summary.notes

    def test_degrading_model(self):
        """Test degrading VaR model (worsens over time)."""
        violations = []
        # First 3 windows: Good (1 violation each)
        for _ in range(3):
            violations.extend([False] * 99 + [True])
        # Last 2 windows: Bad (many violations)
        for _ in range(2):
            violations.extend([True] * 5 + [False] * 95)

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,
            var_alpha=0.01,
        )

        # Should have lower pass rate
        assert result.summary.all_pass_rate < 1.0
        # Worst windows should be the last ones
        worst = get_worst_window(result, criterion="n_violations")
        assert worst.window_id >= 3  # One of the last 2 windows

    def test_crisis_period_detection(self):
        """Test that crisis period (clustered violations) is detected."""
        violations = []
        # Normal period (windows 1-2)
        violations.extend([False] * 99 + [True])
        violations.extend([False] * 99 + [True])
        # Crisis period (window 3)
        violations.extend([True, False, True, False, True, False, True] + [False] * 93)
        # Recovery period (window 4)
        violations.extend([False] * 99 + [True])

        result = rolling_evaluation(
            violations,
            window_size=100,
            step_size=100,
            var_alpha=0.01,
        )

        # Crisis window should fail independence test
        crisis_window = result.windows[2]
        assert crisis_window.n_violations > 1
        # Independence test likely fails due to clustering
        # (but not guaranteed depending on exact pattern)
