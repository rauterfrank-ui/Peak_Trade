"""Hardening tests for Phase 2 VaR Validation.

Tests cover:
- Property-based invariants (p_value in [0,1], lr_uc >= 0)
- Edge cases (empty series, single obs, all NaNs)
- Numerical stability (x=0, x=n)
- Deterministic behavior
- Report output validation (JSON serializable, markdown formatting)
"""

import json
import math
from typing import Any

import numpy as np
import pandas as pd
import pytest

from src.risk.validation import (
    kupiec_pof_test,
    basel_traffic_light,
    run_var_backtest,
    detect_breaches,
    analyze_breaches,
    chi2_p_value,
    kupiec_lr_statistic,
    KupiecResult,
    TrafficLightResult,
    BacktestResult,
)


class TestKupiecPropertyInvariants:
    """Property-based invariants for Kupiec test."""

    def test_p_value_always_in_unit_interval(self):
        """p_value must always be in [0, 1]."""
        test_cases = [
            (0, 100, 0.99),
            (1, 100, 0.99),
            (50, 100, 0.99),
            (100, 100, 0.99),
            (0, 250, 0.95),
            (125, 250, 0.95),
            (250, 250, 0.95),
        ]

        for breaches, obs, conf in test_cases:
            result = kupiec_pof_test(breaches, obs, conf)
            if not math.isnan(result.p_value):
                assert 0.0 <= result.p_value <= 1.0, (
                    f"p_value={result.p_value} out of [0,1] for breaches={breaches}, obs={obs}"
                )

    def test_lr_statistic_always_non_negative(self):
        """LR statistic must always be >= 0."""
        test_cases = [
            (0, 100, 0.99),
            (1, 100, 0.99),
            (50, 100, 0.99),
            (100, 100, 0.99),
            (0, 250, 0.95),
            (125, 250, 0.95),
            (250, 250, 0.95),
        ]

        for breaches, obs, conf in test_cases:
            result = kupiec_pof_test(breaches, obs, conf)
            if not math.isnan(result.test_statistic):
                assert result.test_statistic >= 0.0, (
                    f"lr_statistic={result.test_statistic} < 0 for breaches={breaches}, obs={obs}"
                )

    def test_breaches_never_exceed_observations(self):
        """Breaches cannot exceed observations (enforced by validation)."""
        with pytest.raises(ValueError, match="cannot exceed observations"):
            kupiec_pof_test(breaches=101, observations=100, confidence_level=0.99)

    def test_breach_rate_invariant(self):
        """Breach rate must equal breaches / observations."""
        result = kupiec_pof_test(breaches=5, observations=250, confidence_level=0.99)

        json_dict = result.to_json_dict()
        expected_rate = 5 / 250
        actual_rate = json_dict["breach_rate"]

        assert actual_rate == pytest.approx(expected_rate)

    def test_expected_rate_invariant(self):
        """Expected rate must equal 1 - confidence_level."""
        result = kupiec_pof_test(breaches=5, observations=250, confidence_level=0.99)

        json_dict = result.to_json_dict()
        expected_rate = 1.0 - 0.99
        actual_rate = json_dict["expected_rate"]

        assert actual_rate == pytest.approx(expected_rate)


class TestKupiecEdgeCases:
    """Edge cases for Kupiec test."""

    def test_single_observation_no_breach(self):
        """Single observation, no breach."""
        result = kupiec_pof_test(breaches=0, observations=1, confidence_level=0.99)

        assert result.breaches == 0
        assert result.observations == 1
        assert 0 <= result.p_value <= 1
        assert result.test_statistic >= 0

    def test_single_observation_with_breach(self):
        """Single observation, one breach."""
        result = kupiec_pof_test(breaches=1, observations=1, confidence_level=0.99)

        assert result.breaches == 1
        assert result.observations == 1
        assert not result.is_valid  # 100% breach rate is invalid for 99% VaR

    def test_very_small_observations(self):
        """Very small observation count."""
        for n in [1, 2, 3, 5, 10]:
            result = kupiec_pof_test(breaches=0, observations=n, confidence_level=0.99)
            assert 0 <= result.p_value <= 1
            assert result.test_statistic >= 0


class TestKupiecNumericalStability:
    """Numerical stability tests for Kupiec."""

    def test_x_equals_zero_no_log_zero(self):
        """x=0 should not cause log(0) errors."""
        result = kupiec_pof_test(breaches=0, observations=250, confidence_level=0.99)

        assert not math.isnan(result.test_statistic)
        assert not math.isinf(result.test_statistic)
        assert result.test_statistic >= 0

    def test_x_equals_n_no_log_zero(self):
        """x=n should not cause log(0) errors."""
        result = kupiec_pof_test(breaches=250, observations=250, confidence_level=0.99)

        assert not math.isnan(result.test_statistic)
        assert not math.isinf(result.test_statistic)
        assert result.test_statistic >= 0

    def test_very_high_confidence_level(self):
        """Very high confidence level (99.9%)."""
        result = kupiec_pof_test(breaches=1, observations=1000, confidence_level=0.999)

        assert not math.isnan(result.p_value)
        assert 0 <= result.p_value <= 1

    def test_chi2_p_value_stability(self):
        """Chi-square p-value computation stability."""
        # Test edge cases
        assert chi2_p_value(-1.0) == 1.0  # Negative lr
        assert chi2_p_value(0.0) == 1.0  # Zero lr
        assert 0 <= chi2_p_value(0.1) <= 1.0
        assert 0 <= chi2_p_value(100.0) <= 1.0
        assert 0 <= chi2_p_value(1000.0) <= 1.0


class TestKupiecDeterministicBehavior:
    """Test deterministic behavior of Kupiec test."""

    def test_same_input_same_output(self):
        """Same input should always give same output."""
        result1 = kupiec_pof_test(breaches=5, observations=250, confidence_level=0.99)
        result2 = kupiec_pof_test(breaches=5, observations=250, confidence_level=0.99)

        assert result1.p_value == result2.p_value
        assert result1.test_statistic == result2.test_statistic
        assert result1.is_valid == result2.is_valid

    def test_lr_statistic_deterministic(self):
        """LR statistic computation is deterministic."""
        lr1 = kupiec_lr_statistic(5, 250, 0.01)
        lr2 = kupiec_lr_statistic(5, 250, 0.01)

        assert lr1 == lr2


class TestBacktestRunnerEdgeCases:
    """Edge cases for backtest runner."""

    def test_empty_series(self):
        """Empty returns and VaR series."""
        returns = pd.Series(dtype=float)
        var_series = pd.Series(dtype=float)

        result = run_var_backtest(returns, var_series, confidence_level=0.99)

        assert result.breaches == 0
        assert result.observations == 0
        assert math.isnan(result.kupiec.p_value)
        assert not result.kupiec.is_valid

    def test_single_observation(self):
        """Single observation."""
        returns = pd.Series([0.01])
        var_series = pd.Series([0.03])

        result = run_var_backtest(returns, var_series, confidence_level=0.99)

        assert result.observations == 1
        assert result.breaches == 0  # 1% return doesn't breach 3% VaR

    def test_all_nans(self):
        """All NaN values."""
        returns = pd.Series([np.nan] * 100)
        var_series = pd.Series([np.nan] * 100)

        result = run_var_backtest(returns, var_series, confidence_level=0.99)

        assert result.observations == 0
        assert result.breaches == 0

    def test_partial_nans(self):
        """Partial NaN values should be dropped."""
        returns = pd.Series([0.01, np.nan, -0.05, 0.02, np.nan])
        var_series = pd.Series([0.03, 0.03, 0.03, np.nan, 0.03])

        result = run_var_backtest(returns, var_series, confidence_level=0.99)

        # After alignment and dropna, should have 2 valid observations
        assert result.observations == 2
        assert result.breaches == 1  # -5% breaches 3% VaR

    def test_completely_misaligned_indices(self):
        """Completely misaligned indices."""
        returns = pd.Series([0.01, 0.02], index=[0, 1])
        var_series = pd.Series([0.03, 0.03], index=[2, 3])

        result = run_var_backtest(returns, var_series, confidence_level=0.99)

        assert result.observations == 0  # No overlapping indices
        assert result.breaches == 0


class TestBacktestBreachDetectionPrecision:
    """Test exact breach detection with known timestamps."""

    def test_exact_breach_timestamps(self):
        """Breach detection should return exact timestamps."""
        dates = pd.date_range("2020-01-01", periods=10)

        # Create returns with specific breaches
        returns = pd.Series([0.01] * 10, index=dates)
        returns.iloc[2] = -0.05  # Breach at 2020-01-03
        returns.iloc[7] = -0.04  # Breach at 2020-01-08

        var_series = pd.Series([0.03] * 10, index=dates)

        result = run_var_backtest(returns, var_series, confidence_level=0.99)

        assert result.breaches == 2
        assert len(result.breach_dates) == 2
        assert result.breach_dates[0] == dates[2]
        assert result.breach_dates[1] == dates[7]

    def test_breach_boundary_precision(self):
        """Test breach detection at exact VaR boundary."""
        returns = pd.Series([-0.03, -0.0299, -0.0301])
        var_series = pd.Series([0.03, 0.03, 0.03])

        breach_mask, _, _ = detect_breaches(returns, var_series)

        # realized_loss = [0.03, 0.0299, 0.0301]
        # breach = realized_loss > var_series
        assert not breach_mask.iloc[0]  # 0.03 == 0.03 (not >)
        assert not breach_mask.iloc[1]  # 0.0299 < 0.03
        assert breach_mask.iloc[2]  # 0.0301 > 0.03


class TestReportOutputValidation:
    """Test report output formats."""

    def test_kupiec_json_serializable(self):
        """Kupiec result JSON dict must be serializable."""
        result = kupiec_pof_test(breaches=5, observations=250, confidence_level=0.99)
        json_dict = result.to_json_dict()

        # Should not raise exception
        json_str = json.dumps(json_dict)
        assert isinstance(json_str, str)

        # Verify all expected keys
        expected_keys = {
            "p_value",
            "test_statistic",
            "breaches",
            "observations",
            "expected_breaches",
            "breach_rate",
            "expected_rate",
            "is_valid",
            "confidence_level",
            "alpha",
        }
        assert set(json_dict.keys()) == expected_keys

    def test_kupiec_markdown_contains_key_numbers(self):
        """Kupiec markdown report must contain key numbers."""
        result = kupiec_pof_test(breaches=5, observations=250, confidence_level=0.99)
        markdown = result.to_markdown()

        assert str(result.observations) in markdown
        assert str(result.breaches) in markdown
        assert f"{result.p_value:.4f}" in markdown
        assert "Kupiec POF Test" in markdown

    def test_traffic_light_json_serializable(self):
        """Traffic light result JSON dict must be serializable."""
        result = basel_traffic_light(breaches=5, observations=250, confidence_level=0.99)
        json_dict = result.to_json_dict()

        json_str = json.dumps(json_dict)
        assert isinstance(json_str, str)

        expected_keys = {
            "color",
            "breaches",
            "observations",
            "green_threshold",
            "yellow_threshold",
            "breach_rate",
        }
        assert set(json_dict.keys()) == expected_keys

    def test_traffic_light_markdown_contains_key_numbers(self):
        """Traffic light markdown report must contain key numbers."""
        result = basel_traffic_light(breaches=5, observations=250, confidence_level=0.99)
        markdown = result.to_markdown()

        assert str(result.breaches) in markdown
        assert str(result.observations) in markdown
        assert result.color.upper() in markdown
        assert "Basel Traffic Light" in markdown

    def test_backtest_json_serializable(self):
        """Backtest result JSON dict must be serializable."""
        returns = pd.Series([0.01] * 250)
        var_series = pd.Series([0.03] * 250)

        result = run_var_backtest(returns, var_series, confidence_level=0.99)
        json_dict = result.to_json_dict()

        json_str = json.dumps(json_dict)
        assert isinstance(json_str, str)

        # Verify nested structures are also serializable
        assert isinstance(json_dict["kupiec"], dict)
        assert isinstance(json_dict["traffic_light"], dict)
        assert isinstance(json_dict["breach_dates"], list)

    def test_backtest_markdown_contains_key_sections(self):
        """Backtest markdown report must contain key sections."""
        returns = pd.Series([0.01] * 250)
        var_series = pd.Series([0.03] * 250)

        result = run_var_backtest(returns, var_series, confidence_level=0.99)
        markdown = result.to_markdown()

        assert "VaR Backtest Report" in markdown
        assert "Summary" in markdown
        assert "Kupiec" in markdown
        assert "Traffic Light" in markdown
        assert str(result.breaches) in markdown


class TestTrafficLightPropertyInvariants:
    """Property invariants for traffic light."""

    def test_color_is_valid_zone(self):
        """Color must be one of: green, yellow, red."""
        test_cases = [
            (0, 250),
            (4, 250),
            (5, 250),
            (9, 250),
            (10, 250),
            (50, 250),
        ]

        for breaches, obs in test_cases:
            result = basel_traffic_light(breaches, obs, 0.99)
            assert result.color in {"green", "yellow", "red"}

    def test_thresholds_monotonic(self):
        """Yellow threshold must be > green threshold."""
        green, yellow = (
            basel_traffic_light(5, 250, 0.99).green_threshold,
            basel_traffic_light(5, 250, 0.99).yellow_threshold,
        )

        assert yellow > green


class TestBreachAnalysisEdgeCases:
    """Edge cases for breach analysis."""

    def test_no_breaches_analysis(self):
        """Analysis with no breaches."""
        breach_mask = pd.Series([False] * 100)
        analysis = analyze_breaches(breach_mask)

        assert analysis.total_breaches == 0
        assert analysis.max_consecutive == 0
        assert analysis.avg_gap is None
        assert len(analysis.gaps) == 0
        assert len(analysis.streaks) == 0

    def test_single_breach_analysis(self):
        """Analysis with single breach."""
        breach_mask = pd.Series([False] * 50 + [True] + [False] * 49)
        analysis = analyze_breaches(breach_mask)

        assert analysis.total_breaches == 1
        assert analysis.max_consecutive == 1
        assert len(analysis.streaks) == 1
        assert analysis.streaks[0] == 1

    def test_all_breaches_analysis(self):
        """Analysis with all breaches."""
        breach_mask = pd.Series([True] * 100)
        analysis = analyze_breaches(breach_mask)

        assert analysis.total_breaches == 100
        assert analysis.max_consecutive == 100
        assert len(analysis.streaks) == 1
        assert analysis.streaks[0] == 100
        assert len(analysis.gaps) == 0  # No gaps when all breaches


class TestInputValidation:
    """Test input validation and error messages."""

    def test_kupiec_negative_breaches(self):
        """Negative breaches should raise ValueError."""
        with pytest.raises(ValueError, match="breaches must be non-negative"):
            kupiec_pof_test(breaches=-1, observations=250, confidence_level=0.99)

    def test_kupiec_negative_observations(self):
        """Negative observations should raise ValueError."""
        with pytest.raises(ValueError, match="observations must be non-negative"):
            kupiec_pof_test(breaches=5, observations=-250, confidence_level=0.99)

    def test_kupiec_invalid_confidence_level(self):
        """Invalid confidence level should raise ValueError."""
        with pytest.raises(ValueError, match="confidence_level must be in"):
            kupiec_pof_test(breaches=5, observations=250, confidence_level=1.5)

        with pytest.raises(ValueError, match="confidence_level must be in"):
            kupiec_pof_test(breaches=5, observations=250, confidence_level=-0.1)

    def test_backtest_invalid_input_types(self):
        """Invalid input types should raise TypeError."""
        with pytest.raises(TypeError, match="returns must be pd.Series"):
            run_var_backtest([0.01, 0.02], pd.Series([0.03, 0.03]), 0.99)

        with pytest.raises(TypeError, match="var_series must be pd.Series"):
            run_var_backtest(pd.Series([0.01, 0.02]), [0.03, 0.03], 0.99)
