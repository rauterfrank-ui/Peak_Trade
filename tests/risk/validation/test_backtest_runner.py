"""Tests for VaR backtest runner."""

import numpy as np
import pandas as pd
import pytest

from src.risk.validation.backtest_runner import (
    BacktestResult,
    run_var_backtest,
    detect_breaches,
)
from src.risk.validation.breach_analysis import (
    BreachAnalysis,
    analyze_breaches,
    compute_breach_statistics,
)


class TestDetectBreaches:
    """Test breach detection."""

    def test_detect_breaches_simple(self):
        """Test simple breach detection."""
        # Returns: [-1%, -2%, -3%, 1%] (negative = loss)
        # VaR: [2.5%, 2.5%, 2.5%, 2.5%] (positive = loss magnitude)
        # Realized loss: [1%, 2%, 3%, -1%]
        # Breaches: [False, False, True, False]

        returns = pd.Series([-0.01, -0.02, -0.03, 0.01])
        var_series = pd.Series([0.025, 0.025, 0.025, 0.025])

        breach_mask, aligned_returns, aligned_var = detect_breaches(returns, var_series)

        assert len(breach_mask) == 4
        assert breach_mask.sum() == 1  # Only -3% breaches 2.5% VaR
        assert breach_mask.iloc[2]  # -3% breaches 2.5% VaR

    def test_detect_breaches_alignment(self):
        """Test index alignment."""
        dates = pd.date_range("2020-01-01", periods=5)

        # Returns missing index 2
        returns = pd.Series(
            [-0.01, -0.02, -0.04, -0.05], index=[dates[0], dates[1], dates[3], dates[4]]
        )

        # VaR has all dates
        var_series = pd.Series([0.03] * 5, index=dates)

        breach_mask, aligned_returns, aligned_var = detect_breaches(returns, var_series)

        # Should only include aligned indices (4 total)
        assert len(breach_mask) == 4

    def test_detect_breaches_with_nans(self):
        """Test breach detection with NaNs."""
        returns = pd.Series([-0.01, np.nan, -0.03, -0.04])
        var_series = pd.Series([0.025, 0.025, np.nan, 0.025])

        breach_mask, aligned_returns, aligned_var = detect_breaches(returns, var_series)

        # Should drop rows with NaN (only indices 0 and 3 remain)
        assert len(breach_mask) == 2

    def test_detect_breaches_empty(self):
        """Test with empty series."""
        returns = pd.Series(dtype=float)
        var_series = pd.Series(dtype=float)

        breach_mask, aligned_returns, aligned_var = detect_breaches(returns, var_series)

        assert len(breach_mask) == 0


class TestRunVaRBacktest:
    """Test full backtest runner."""

    def test_run_backtest_known_breaches(self):
        """Test backtest with known breach pattern."""
        # Create synthetic data with exactly 5 breaches out of 250 observations
        # Use small returns that won't breach VaR
        returns = pd.Series([0.001] * 250)  # Small positive returns (no breaches)

        # Set exactly 5 returns to be breaches
        returns.iloc[[10, 50, 100, 150, 200]] = -0.05  # -5% loss

        # VaR = 3% (should catch only the -5% losses)
        var_series = pd.Series([0.03] * 250)

        result = run_var_backtest(returns, var_series, confidence_level=0.99)

        assert result.breaches == 5
        assert result.observations == 250
        assert result.breach_rate == pytest.approx(0.02)  # 5/250 = 2%
        assert len(result.breach_dates) == 5
        assert result.kupiec.breaches == 5
        assert result.traffic_light.breaches == 5

    def test_backtest_result_invariants(self):
        """Test backtest result invariants."""
        np.random.seed(123)
        returns = pd.Series(np.random.normal(0, 0.02, 250))
        var_series = pd.Series([0.03] * 250)

        result = run_var_backtest(returns, var_series, confidence_level=0.99)

        # Invariant: breach_rate = breaches / observations
        assert result.breach_rate == pytest.approx(result.breaches / result.observations)

        # Invariant: len(breach_dates) == breaches
        assert len(result.breach_dates) == result.breaches

        # Invariant: kupiec and traffic_light use same breach count
        assert result.kupiec.breaches == result.breaches
        assert result.traffic_light.breaches == result.breaches

    def test_backtest_with_breach_analysis(self):
        """Test backtest with breach analysis."""
        np.random.seed(456)
        returns = pd.Series(np.random.normal(0, 0.02, 250))
        var_series = pd.Series([0.03] * 250)

        # Add consecutive breaches
        returns.iloc[10:13] = -0.05  # 3 consecutive breaches

        result = run_var_backtest(returns, var_series, include_breach_analysis=True)

        assert result.breach_analysis is not None
        assert isinstance(result.breach_analysis, BreachAnalysis)
        assert result.breach_analysis.max_consecutive >= 3

    def test_backtest_without_breach_analysis(self):
        """Test backtest without breach analysis."""
        np.random.seed(789)
        returns = pd.Series(np.random.normal(0, 0.02, 250))
        var_series = pd.Series([0.03] * 250)

        result = run_var_backtest(returns, var_series, include_breach_analysis=False)

        assert result.breach_analysis is None


class TestBreachAnalysis:
    """Test breach pattern analysis."""

    def test_analyze_no_breaches(self):
        """Test analysis with no breaches."""
        breach_mask = pd.Series([False] * 100)

        analysis = analyze_breaches(breach_mask)

        assert analysis.total_breaches == 0
        assert analysis.max_consecutive == 0
        assert analysis.avg_gap is None
        assert len(analysis.gaps) == 0
        assert len(analysis.streaks) == 0
        assert analysis.first_breach is None
        assert analysis.last_breach is None

    def test_analyze_consecutive_breaches(self):
        """Test analysis with consecutive breaches."""
        # Pattern: 3 consecutive breaches at positions 10-12
        breach_mask = pd.Series([False] * 100)
        breach_mask.iloc[10:13] = True

        analysis = analyze_breaches(breach_mask)

        assert analysis.total_breaches == 3
        assert analysis.max_consecutive == 3
        assert len(analysis.streaks) == 1
        assert analysis.streaks[0] == 3

    def test_analyze_multiple_streaks(self):
        """Test analysis with multiple breach streaks."""
        breach_mask = pd.Series([False] * 100)
        breach_mask.iloc[10:12] = True  # 2 consecutive
        breach_mask.iloc[50] = True  # 1 isolated
        breach_mask.iloc[80:84] = True  # 4 consecutive

        analysis = analyze_breaches(breach_mask)

        assert analysis.total_breaches == 7
        assert analysis.max_consecutive == 4
        assert len(analysis.streaks) == 3
        assert 4 in analysis.streaks
        assert 2 in analysis.streaks
        assert 1 in analysis.streaks

    def test_analyze_gaps(self):
        """Test gap computation."""
        breach_mask = pd.Series([False] * 100)
        breach_mask.iloc[10] = True
        breach_mask.iloc[20] = True  # Gap of 9
        breach_mask.iloc[25] = True  # Gap of 4

        analysis = analyze_breaches(breach_mask)

        assert len(analysis.gaps) == 2
        assert 9 in analysis.gaps
        assert 4 in analysis.gaps
        assert analysis.avg_gap == pytest.approx(6.5)  # (9 + 4) / 2


class TestComputeBreachStatistics:
    """Test breach statistics computation."""

    def test_compute_basic_stats(self):
        """Test basic breach statistics."""
        breach_mask = pd.Series([False] * 90 + [True] * 10)

        stats = compute_breach_statistics(breach_mask)

        assert stats["breach_count"] == 10
        assert stats["observations"] == 100
        assert stats["breach_rate"] == pytest.approx(0.1)
        assert stats["non_breach_count"] == 90


class TestBacktestResultSerialization:
    """Test backtest result serialization."""

    def test_to_json_dict(self):
        """Test JSON serialization."""
        np.random.seed(999)
        returns = pd.Series(np.random.normal(0, 0.02, 250))
        var_series = pd.Series([0.03] * 250)

        result = run_var_backtest(returns, var_series)
        json_dict = result.to_json_dict()

        assert isinstance(json_dict, dict)
        assert "breaches" in json_dict
        assert "observations" in json_dict
        assert "breach_rate" in json_dict
        assert "breach_dates" in json_dict
        assert "kupiec" in json_dict
        assert "traffic_light" in json_dict

    def test_to_markdown(self):
        """Test markdown report generation."""
        np.random.seed(111)
        returns = pd.Series(np.random.normal(0, 0.02, 250))
        var_series = pd.Series([0.03] * 250)

        result = run_var_backtest(returns, var_series)
        markdown = result.to_markdown()

        assert isinstance(markdown, str)
        assert "VaR Backtest Report" in markdown
        assert "Summary" in markdown
        assert "Kupiec" in markdown
        assert "Traffic Light" in markdown
