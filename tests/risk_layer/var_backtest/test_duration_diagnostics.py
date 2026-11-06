"""
Tests für Duration-Based Independence Diagnostic
=================================================

Tests für Phase 9A: Duration extraction und diagnostische Metriken.
"""

import math

import pandas as pd
import pytest

from src.risk_layer.var_backtest.duration_diagnostics import (
    DurationDiagnosticResult,
    ExponentialTestResult,
    duration_independence_diagnostic,
    extract_exceedance_durations,
    format_duration_diagnostic,
)


# ============================================================================
# Test Duration Extraction
# ============================================================================


class TestExtractExceedanceDurations:
    """Test duration extraction from exceedance series."""

    def test_basic_extraction(self):
        """Test basic duration extraction with integer indices."""
        # Exceedances at positions: 2, 5, 7
        # Durations: 5-2=3, 7-5=2
        exceedances = [False, False, True, False, False, True, False, True]
        durations = extract_exceedance_durations(exceedances)

        assert len(durations) == 2
        assert durations[0] == 3.0
        assert durations[1] == 2.0

    def test_empty_exceedances(self):
        """Test with no exceedances."""
        exceedances = [False, False, False, False]
        durations = extract_exceedance_durations(exceedances)

        assert len(durations) == 0

    def test_single_exceedance(self):
        """Test with single exceedance (no durations)."""
        exceedances = [False, False, True, False]
        durations = extract_exceedance_durations(exceedances)

        assert len(durations) == 0

    def test_consecutive_exceedances(self):
        """Test with consecutive exceedances (duration = 1)."""
        # Exceedances at positions: 2, 3, 4
        # Durations: 3-2=1, 4-3=1
        exceedances = [False, False, True, True, True, False]
        durations = extract_exceedance_durations(exceedances)

        assert len(durations) == 2
        assert durations[0] == 1.0
        assert durations[1] == 1.0

    def test_with_datetime_index(self):
        """Test duration extraction with DatetimeIndex (in days)."""
        dates = pd.date_range("2024-01-01", periods=8, freq="D")
        # Exceedances on: 2024-01-03, 2024-01-06, 2024-01-08
        # Durations: 3 days, 2 days
        exceedances = [False, False, True, False, False, True, False, True]

        durations = extract_exceedance_durations(exceedances, timestamps=dates)

        assert len(durations) == 2
        assert durations[0] == 3.0  # days
        assert durations[1] == 2.0  # days

    def test_with_numeric_timestamps(self):
        """Test duration extraction with numeric timestamps."""
        timestamps = [1.0, 2.0, 3.5, 4.0, 5.0, 6.5, 7.0, 8.0]
        # Exceedances at indices: 2, 5, 7 → timestamps: 3.5, 6.5, 8.0
        # Durations: 6.5-3.5=3.0, 8.0-6.5=1.5
        exceedances = [False, False, True, False, False, True, False, True]

        durations = extract_exceedance_durations(exceedances, timestamps=timestamps)

        assert len(durations) == 2
        assert durations[0] == 3.0
        assert durations[1] == 1.5

    def test_with_pandas_series(self):
        """Test with pandas Series input."""
        exceedances = pd.Series([False, False, True, False, True])
        durations = extract_exceedance_durations(exceedances)

        assert len(durations) == 1
        assert durations[0] == 2.0


# ============================================================================
# Test Duration Ordering and Sanity
# ============================================================================


class TestDurationOrdering:
    """Test that durations maintain correct ordering and properties."""

    def test_durations_are_positive(self):
        """Test that all durations are positive."""
        exceedances = [False] * 50 + [True] + [False] * 10 + [True] + [False] * 5 + [True]
        durations = extract_exceedance_durations(exceedances)

        assert all(d > 0 for d in durations)

    def test_durations_respect_temporal_order(self):
        """Test that durations maintain temporal ordering."""
        # Exceedances at positions: 10, 15, 25, 30
        # Expected durations: 5, 10, 5 (in order)
        exceedances = (
            [False] * 10
            + [True]
            + [False] * 4
            + [True]
            + [False] * 9
            + [True]
            + [False] * 4
            + [True]
        )
        durations = extract_exceedance_durations(exceedances)

        assert len(durations) == 3
        assert durations[0] == 5.0
        assert durations[1] == 10.0
        assert durations[2] == 5.0

    def test_sum_of_durations_equals_range(self):
        """Test that sum of durations equals time range (minus first exceedance)."""
        # Exceedances at positions: 5, 10, 20
        # Durations: 5, 10 → sum = 15 = (20 - 5)
        exceedances = [False] * 5 + [True] + [False] * 4 + [True] + [False] * 9 + [True]
        durations = extract_exceedance_durations(exceedances)

        first_exceedance_idx = 5
        last_exceedance_idx = 20
        expected_sum = last_exceedance_idx - first_exceedance_idx

        assert sum(durations) == expected_sum


# ============================================================================
# Test Duration Independence Diagnostic
# ============================================================================


class TestDurationIndependenceDiagnostic:
    """Test duration independence diagnostic computation."""

    def test_basic_diagnostic(self):
        """Test basic diagnostic with known expected rate."""
        # 100 observations, 10 exceedances (~10% rate)
        # Exceedances roughly evenly spaced (every 10 observations)
        exceedances = [False] * 9 + [True] + [False] * 9 + [True] + [False] * 9 + [True]
        expected_rate = 0.1

        result = duration_independence_diagnostic(exceedances, expected_rate=expected_rate)

        assert result.n_exceedances == 3
        assert result.n_durations == 2
        assert result.mean_duration == 10.0
        assert result.expected_duration == 10.0  # 1 / 0.1
        assert result.duration_ratio == pytest.approx(1.0, abs=0.01)
        assert not result.is_suspicious()

    def test_clustered_exceedances(self):
        """Test diagnostic with clustered exceedances (short durations)."""
        # Exceedances clustered together → short durations
        exceedances = [False] * 50 + [True, False, True, False, True] + [False] * 50
        expected_rate = 3 / len(exceedances)  # ~2.8%

        result = duration_independence_diagnostic(exceedances, expected_rate=expected_rate)

        assert result.n_exceedances == 3
        assert result.n_durations == 2
        assert result.mean_duration == 2.0
        # Expected duration ≈ 1/0.028 ≈ 35.7
        assert result.duration_ratio < 0.5  # Strong clustering
        assert result.is_suspicious()

    def test_sparse_exceedances(self):
        """Test diagnostic with sparse exceedances (long durations)."""
        # Exceedances widely spaced
        # Positions: 100, 201, 302 → durations: 101, 101
        exceedances = [False] * 100 + [True] + [False] * 100 + [True] + [False] * 100 + [True]
        expected_rate = 3 / len(exceedances)  # ~1%

        result = duration_independence_diagnostic(exceedances, expected_rate=expected_rate)

        assert result.n_exceedances == 3
        assert result.n_durations == 2
        assert result.mean_duration == 101.0  # Corrected: 201-100=101
        # Expected duration ≈ 1/0.01 = 101
        assert result.duration_ratio == pytest.approx(1.0, rel=0.05)

    def test_insufficient_data(self):
        """Test diagnostic with insufficient data (< 2 exceedances)."""
        exceedances = [False] * 50 + [True] + [False] * 50

        result = duration_independence_diagnostic(exceedances, expected_rate=0.01)

        assert result.n_exceedances == 1
        assert result.n_durations == 0
        assert math.isnan(result.mean_duration)
        assert math.isnan(result.duration_ratio)
        assert "Insufficient data" in result.notes

    def test_auto_estimate_rate(self):
        """Test diagnostic with auto-estimated expected rate."""
        # Total: 95 observations, 5 exceedances → rate = 5/95 ≈ 0.0526
        # Positions: 18, 37, 56, 75, 94 → durations: 19, 19, 19, 19
        exceedances = (
            [False] * 18
            + [True]
            + [False] * 18
            + [True]
            + [False] * 18
            + [True]
            + [False] * 18
            + [True]
            + [False] * 18
            + [True]
        )

        # Don't provide expected_rate → should estimate from data
        result = duration_independence_diagnostic(exceedances, expected_rate=None)

        assert result.n_exceedances == 5
        assert result.n_durations == 4
        # Expected rate = 5 / 95 ≈ 0.0526 → expected_duration ≈ 19.0
        assert result.expected_duration == pytest.approx(19.0, abs=0.5)

    def test_with_datetime_index(self):
        """Test diagnostic with DatetimeIndex."""
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        # Exceedances on days: 5, 15, 25
        exceedances = (
            [False] * 5 + [True] + [False] * 9 + [True] + [False] * 9 + [True] + [False] * 5
        )

        result = duration_independence_diagnostic(exceedances, expected_rate=0.1, timestamps=dates)

        assert result.n_exceedances == 3
        assert result.n_durations == 2
        assert result.mean_duration == 10.0  # days

    def test_is_suspicious_threshold(self):
        """Test is_suspicious() with custom threshold."""
        exceedances = [False] * 50 + [True, False, True] + [False] * 50

        result = duration_independence_diagnostic(exceedances, expected_rate=0.02)

        # duration_ratio = 2 / 50 = 0.04 → very small
        assert result.is_suspicious(threshold=0.5)
        assert result.is_suspicious(threshold=0.1)
        assert result.is_suspicious(threshold=0.05)


# ============================================================================
# Test Exponential Goodness-of-Fit
# ============================================================================


class TestExponentialGoodnessOfFit:
    """Test exponential distribution goodness-of-fit test."""

    def test_exponential_test_enabled(self):
        """Test that exponential test runs when enabled."""
        # Generate durations roughly exponentially distributed
        exceedances = (
            [False] * 10
            + [True]
            + [False] * 5
            + [True]
            + [False] * 20
            + [True]
            + [False] * 3
            + [True]
        )
        expected_rate = 0.1

        result = duration_independence_diagnostic(
            exceedances,
            expected_rate=expected_rate,
            enable_exponential_test=True,
        )

        assert result.exponential_test is not None
        assert isinstance(result.exponential_test, ExponentialTestResult)
        assert "Anderson-Darling" in result.exponential_test.test_name

    def test_exponential_test_disabled(self):
        """Test that exponential test is None when disabled."""
        exceedances = [False] * 10 + [True] + [False] * 10 + [True] + [False] * 10 + [True]

        result = duration_independence_diagnostic(
            exceedances,
            expected_rate=0.1,
            enable_exponential_test=False,
        )

        assert result.exponential_test is None

    def test_exponential_test_insufficient_data(self):
        """Test exponential test with insufficient data (< 3 durations)."""
        exceedances = [False] * 10 + [True] + [False] * 10 + [True]

        result = duration_independence_diagnostic(
            exceedances,
            expected_rate=0.1,
            enable_exponential_test=True,
        )

        # Should have only 1 duration → exponential test can't run properly
        # But should not crash
        assert result.n_durations == 1


# ============================================================================
# Test Result Formatting
# ============================================================================


class TestResultFormatting:
    """Test diagnostic result formatting."""

    def test_to_dict(self):
        """Test DurationDiagnosticResult.to_dict()."""
        exceedances = [False] * 10 + [True] + [False] * 10 + [True] + [False] * 10 + [True]

        result = duration_independence_diagnostic(exceedances, expected_rate=0.1)
        result_dict = result.to_dict()

        assert "n_exceedances" in result_dict
        assert "n_durations" in result_dict
        assert "mean_duration" in result_dict
        assert "duration_ratio" in result_dict
        assert "clustering_score" in result_dict
        assert "notes" in result_dict

    def test_to_dict_with_exponential_test(self):
        """Test to_dict() with exponential test."""
        exceedances = (
            [False] * 10
            + [True]
            + [False] * 5
            + [True]
            + [False] * 20
            + [True]
            + [False] * 3
            + [True]
        )

        result = duration_independence_diagnostic(
            exceedances, expected_rate=0.1, enable_exponential_test=True
        )
        result_dict = result.to_dict()

        assert "exponential_test" in result_dict
        assert isinstance(result_dict["exponential_test"], dict)

    def test_format_duration_diagnostic(self):
        """Test format_duration_diagnostic() output."""
        exceedances = [False] * 10 + [True] + [False] * 10 + [True] + [False] * 10 + [True]

        result = duration_independence_diagnostic(exceedances, expected_rate=0.1)
        formatted = format_duration_diagnostic(result)

        assert "DURATION-BASED INDEPENDENCE DIAGNOSTIC" in formatted
        assert "Exceedances:" in formatted
        assert "Mean Duration:" in formatted
        assert "Duration Ratio:" in formatted
        assert "Interpretation:" in formatted


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_exceedances(self):
        """Test with empty exceedances list."""
        exceedances = []

        result = duration_independence_diagnostic(exceedances, expected_rate=0.01)

        assert result.n_exceedances == 0
        assert result.n_durations == 0
        assert math.isnan(result.mean_duration)

    def test_all_false(self):
        """Test with no exceedances."""
        exceedances = [False] * 100

        result = duration_independence_diagnostic(exceedances, expected_rate=0.01)

        assert result.n_exceedances == 0
        assert result.n_durations == 0

    def test_all_true(self):
        """Test with all exceedances."""
        exceedances = [True] * 10

        result = duration_independence_diagnostic(exceedances, expected_rate=0.5)

        # All True → durations all = 1
        assert result.n_exceedances == 10
        assert result.n_durations == 9
        assert result.mean_duration == 1.0

    def test_expected_rate_zero(self):
        """Test with expected_rate = 0 (edge case)."""
        exceedances = [False] * 10 + [True] + [False] * 10 + [True]

        # expected_rate=0 → expected_duration = inf
        result = duration_independence_diagnostic(exceedances, expected_rate=0.0)

        assert math.isinf(result.expected_duration)
        assert math.isnan(result.duration_ratio)

    def test_two_exceedances_exactly(self):
        """Test with exactly 2 exceedances (minimum for 1 duration)."""
        # Positions: 10, 31 → duration: 21
        exceedances = [False] * 10 + [True] + [False] * 20 + [True]

        result = duration_independence_diagnostic(exceedances, expected_rate=0.05)

        assert result.n_exceedances == 2
        assert result.n_durations == 1
        assert result.mean_duration == 21.0  # Corrected: 31-10=21
        assert result.std_duration == 0.0  # Only 1 duration → std = 0


# ============================================================================
# Test Integration with Real-World Scenarios
# ============================================================================


class TestRealWorldScenarios:
    """Test with realistic VaR violation scenarios."""

    def test_99_var_normal_case(self):
        """Test 99% VaR with normal violation pattern."""
        # 250 observations, expect ~2-3 violations (1%)
        # Positions: 80, 161, 242 → durations: 81, 81
        exceedances = [False] * 80 + [True] + [False] * 80 + [True] + [False] * 80 + [True]
        expected_rate = 0.01

        result = duration_independence_diagnostic(exceedances, expected_rate=expected_rate)

        # Expected duration = 1/0.01 = 100
        # Observed mean = 81
        assert result.expected_duration == 100.0
        assert result.mean_duration == 81.0  # Corrected
        assert 0.5 < result.duration_ratio < 1.5  # Within acceptable range
        assert not result.is_suspicious()

    def test_99_var_clustered_crisis(self):
        """Test 99% VaR with clustered violations (crisis period)."""
        # 250 observations with crisis cluster
        exceedances = [False] * 100 + [True, False, False, True, False, True] + [False] * 144

        result = duration_independence_diagnostic(exceedances, expected_rate=0.01)

        # Clustered violations → short durations → ratio << 1
        assert result.duration_ratio < 0.5
        assert result.is_suspicious()
        assert "clustering" in result.notes.lower()

    def test_95_var_normal_case(self):
        """Test 95% VaR with normal violation pattern."""
        # 100 observations, expect ~5 violations (5%)
        exceedances = (
            [False] * 18
            + [True]
            + [False] * 18
            + [True]
            + [False] * 18
            + [True]
            + [False] * 18
            + [True]
            + [False] * 18
            + [True]
        )
        expected_rate = 0.05

        result = duration_independence_diagnostic(exceedances, expected_rate=expected_rate)

        # Expected duration = 1/0.05 = 20
        assert result.expected_duration == 20.0
        assert 0.5 < result.duration_ratio < 1.5
