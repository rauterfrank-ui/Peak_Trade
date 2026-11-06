"""
Tests for VaR Backtest Suite Runner.

Phase 8C: Suite Report & Regression Guard
"""

import pandas as pd
import pytest

from src.risk.validation.suite_runner import (
    VaRBacktestSuiteResult,
    run_var_backtest_suite,
)


class TestVaRBacktestSuiteResult:
    """Tests for VaRBacktestSuiteResult dataclass."""

    def test_overall_result_all_pass(self):
        """Test overall_result is PASS when all tests pass."""
        result = VaRBacktestSuiteResult(
            observations=100,
            breaches=5,
            confidence_level=0.95,
            kupiec_pof_result="PASS",
            kupiec_pof_pvalue=0.123456,
            basel_traffic_light="GREEN",
            christoffersen_ind_result="PASS",
            christoffersen_ind_pvalue=0.234567,
            christoffersen_cc_result="PASS",
            christoffersen_cc_pvalue=0.345678,
        )
        assert result.overall_result == "PASS"

    def test_overall_result_kupiec_fail(self):
        """Test overall_result is FAIL when Kupiec fails."""
        result = VaRBacktestSuiteResult(
            observations=100,
            breaches=5,
            confidence_level=0.95,
            kupiec_pof_result="FAIL",
            kupiec_pof_pvalue=0.001,
            basel_traffic_light="GREEN",
            christoffersen_ind_result="PASS",
            christoffersen_ind_pvalue=0.234567,
            christoffersen_cc_result="PASS",
            christoffersen_cc_pvalue=0.345678,
        )
        assert result.overall_result == "FAIL"

    def test_overall_result_traffic_light_yellow(self):
        """Test overall_result is FAIL when traffic light is YELLOW."""
        result = VaRBacktestSuiteResult(
            observations=100,
            breaches=5,
            confidence_level=0.95,
            kupiec_pof_result="PASS",
            kupiec_pof_pvalue=0.123456,
            basel_traffic_light="YELLOW",
            christoffersen_ind_result="PASS",
            christoffersen_ind_pvalue=0.234567,
            christoffersen_cc_result="PASS",
            christoffersen_cc_pvalue=0.345678,
        )
        assert result.overall_result == "FAIL"

    def test_overall_result_christoffersen_fail(self):
        """Test overall_result is FAIL when Christoffersen tests fail."""
        result = VaRBacktestSuiteResult(
            observations=100,
            breaches=5,
            confidence_level=0.95,
            kupiec_pof_result="PASS",
            kupiec_pof_pvalue=0.123456,
            basel_traffic_light="GREEN",
            christoffersen_ind_result="FAIL",
            christoffersen_ind_pvalue=0.001,
            christoffersen_cc_result="FAIL",
            christoffersen_cc_pvalue=0.001,
        )
        assert result.overall_result == "FAIL"


class TestRunVarBacktestSuite:
    """Tests for run_var_backtest_suite function."""

    def test_basic_execution_all_pass(self):
        """Test basic execution with data that passes all tests."""
        # Create returns with few breaches (should pass all tests)
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        returns = pd.Series([0.01] * 95 + [-0.03] * 5, index=dates)
        var_series = pd.Series([0.02] * 100, index=dates)

        result = run_var_backtest_suite(
            returns=returns,
            var_series=var_series,
            confidence_level=0.95,
        )

        assert result.observations == 100
        assert result.breaches == 5
        assert result.confidence_level == 0.95
        assert result.kupiec_pof_result in ["PASS", "FAIL"]
        assert 0 <= result.kupiec_pof_pvalue <= 1
        assert result.basel_traffic_light in ["GREEN", "YELLOW", "RED"]
        assert result.christoffersen_ind_result in ["PASS", "FAIL"]
        assert 0 <= result.christoffersen_ind_pvalue <= 1
        assert result.christoffersen_cc_result in ["PASS", "FAIL"]
        assert 0 <= result.christoffersen_cc_pvalue <= 1
        assert result.overall_result in ["PASS", "FAIL"]

    def test_deterministic_output(self):
        """Test that same input produces identical output (determinism)."""
        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        returns = pd.Series([0.01] * 48 + [-0.03] * 2, index=dates)
        var_series = pd.Series([0.02] * 50, index=dates)

        result1 = run_var_backtest_suite(returns, var_series, 0.95)
        result2 = run_var_backtest_suite(returns, var_series, 0.95)

        # All fields must be identical
        assert result1.observations == result2.observations
        assert result1.breaches == result2.breaches
        assert result1.confidence_level == result2.confidence_level
        assert result1.kupiec_pof_result == result2.kupiec_pof_result
        assert result1.kupiec_pof_pvalue == result2.kupiec_pof_pvalue
        assert result1.basel_traffic_light == result2.basel_traffic_light
        assert result1.christoffersen_ind_result == result2.christoffersen_ind_result
        assert result1.christoffersen_ind_pvalue == result2.christoffersen_ind_pvalue
        assert result1.christoffersen_cc_result == result2.christoffersen_cc_result
        assert result1.christoffersen_cc_pvalue == result2.christoffersen_cc_pvalue
        assert result1.overall_result == result2.overall_result

    def test_pvalue_precision_6_decimals(self):
        """Test that p-values are rounded to 6 decimals."""
        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        returns = pd.Series([0.01] * 48 + [-0.03] * 2, index=dates)
        var_series = pd.Series([0.02] * 50, index=dates)

        result = run_var_backtest_suite(returns, var_series, 0.95)

        # Check precision (6 decimals)
        assert len(str(result.kupiec_pof_pvalue).split(".")[-1]) <= 6
        assert len(str(result.christoffersen_ind_pvalue).split(".")[-1]) <= 6
        assert len(str(result.christoffersen_cc_pvalue).split(".")[-1]) <= 6

    def test_mismatched_length_raises(self):
        """Test that mismatched lengths raise ValueError."""
        dates1 = pd.date_range("2024-01-01", periods=50, freq="D")
        dates2 = pd.date_range("2024-01-01", periods=49, freq="D")
        returns = pd.Series([0.01] * 50, index=dates1)
        var_series = pd.Series([0.02] * 49, index=dates2)

        with pytest.raises(ValueError, match="must have same length"):
            run_var_backtest_suite(returns, var_series, 0.95)

    def test_mismatched_index_raises(self):
        """Test that mismatched indices raise ValueError."""
        dates1 = pd.date_range("2024-01-01", periods=50, freq="D")
        dates2 = pd.date_range("2024-02-01", periods=50, freq="D")
        returns = pd.Series([0.01] * 50, index=dates1)
        var_series = pd.Series([0.02] * 50, index=dates2)

        with pytest.raises(ValueError, match="must have identical indices"):
            run_var_backtest_suite(returns, var_series, 0.95)

    def test_zero_breaches(self):
        """Test execution with zero breaches."""
        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        returns = pd.Series([0.01] * 50, index=dates)
        var_series = pd.Series([0.02] * 50, index=dates)

        result = run_var_backtest_suite(returns, var_series, 0.95)

        assert result.breaches == 0
        assert result.observations == 50
        # Kupiec POF should likely fail (0 breaches is too few)
        # But we don't enforce expected outcome here (unit test scope)

    def test_all_breaches(self):
        """Test execution with all breaches."""
        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        returns = pd.Series([-0.03] * 50, index=dates)
        var_series = pd.Series([0.02] * 50, index=dates)

        result = run_var_backtest_suite(returns, var_series, 0.95)

        assert result.breaches == 50
        assert result.observations == 50
        # All tests should fail
        assert result.overall_result == "FAIL"
        assert result.basel_traffic_light == "RED"

    def test_confidence_level_parameter(self):
        """Test that confidence_level parameter is stored correctly."""
        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        returns = pd.Series([0.01] * 49 + [-0.03], index=dates)
        var_series = pd.Series([0.02] * 50, index=dates)

        result_95 = run_var_backtest_suite(returns, var_series, 0.95)
        result_99 = run_var_backtest_suite(returns, var_series, 0.99)

        assert result_95.confidence_level == 0.95
        assert result_99.confidence_level == 0.99
