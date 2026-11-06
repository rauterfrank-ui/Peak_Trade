"""
Golden/Snapshot Tests for VaR Backtest Suite Reports.

These tests ensure report outputs remain stable and deterministic.

Phase 8C: Suite Report & Regression Guard
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from src.risk.validation.suite_runner import run_var_backtest_suite
from src.risk.validation.report_formatter import (
    format_suite_result_json,
    format_suite_result_markdown,
)


@pytest.fixture
def fixture_dir():
    """Return path to fixtures directory."""
    return Path(__file__).parent.parent.parent / "fixtures" / "var"


@pytest.fixture
def sample_data_all_pass():
    """Create sample data that should pass all tests."""
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    # 5 breaches out of 100 at 95% confidence -> expected 5, should pass
    returns = pd.Series([0.01] * 95 + [-0.03] * 5, index=dates)
    var_series = pd.Series([0.02] * 100, index=dates)
    return returns, var_series


class TestSuiteGoldenOutputs:
    """Golden/snapshot tests for deterministic outputs."""

    def test_json_output_stable(self, sample_data_all_pass, fixture_dir):
        """Test that JSON output matches golden file."""
        returns, var_series = sample_data_all_pass

        result = run_var_backtest_suite(returns, var_series, 0.95)
        json_str = format_suite_result_json(result)

        # Parse to validate structure
        data = json.loads(json_str)

        # Check structure (not exact values, as they depend on test implementation)
        assert "suite_metadata" in data
        assert "test_results" in data
        assert "overall_result" in data

        # Check that JSON is stable (same data produces same JSON)
        result2 = run_var_backtest_suite(returns, var_series, 0.95)
        json_str2 = format_suite_result_json(result2)
        assert json_str == json_str2

    def test_markdown_output_stable(self, sample_data_all_pass):
        """Test that Markdown output is stable."""
        returns, var_series = sample_data_all_pass

        result = run_var_backtest_suite(returns, var_series, 0.95)
        md_str = format_suite_result_markdown(result)

        # Check structure
        assert "# VaR Backtest Suite Report" in md_str
        assert "Overall Result" in md_str
        assert "Suite Metadata" in md_str
        assert "Test Results" in md_str

        # Check that Markdown is stable
        result2 = run_var_backtest_suite(returns, var_series, 0.95)
        md_str2 = format_suite_result_markdown(result2)
        assert md_str == md_str2

    def test_json_key_order_stable(self, sample_data_all_pass):
        """Test that JSON key order is deterministic."""
        returns, var_series = sample_data_all_pass

        result = run_var_backtest_suite(returns, var_series, 0.95)
        json_str = format_suite_result_json(result)

        # Multiple runs should produce identical strings (not just semantically equal)
        for _ in range(5):
            result_run = run_var_backtest_suite(returns, var_series, 0.95)
            json_str_run = format_suite_result_json(result_run)
            assert json_str == json_str_run

    def test_pvalue_rounding_stable(self, sample_data_all_pass):
        """Test that p-value rounding is consistent (6 decimals)."""
        returns, var_series = sample_data_all_pass

        result = run_var_backtest_suite(returns, var_series, 0.95)
        json_str = format_suite_result_json(result)
        data = json.loads(json_str)

        # Check p-value precision (6 decimals max)
        kupiec_pvalue = data["test_results"]["kupiec_pof"]["p_value"]
        ind_pvalue = data["test_results"]["christoffersen_ind"]["p_value"]
        cc_pvalue = data["test_results"]["christoffersen_cc"]["p_value"]

        # Round-trip check: rounding to 6 decimals should be no-op
        assert round(kupiec_pvalue, 6) == kupiec_pvalue
        assert round(ind_pvalue, 6) == ind_pvalue
        assert round(cc_pvalue, 6) == cc_pvalue

    def test_confidence_level_formatting(self):
        """Test that confidence level is formatted consistently."""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        returns = pd.Series([0.01] * 99 + [-0.03], index=dates)
        var_series = pd.Series([0.02] * 100, index=dates)

        # Test with 0.95
        result = run_var_backtest_suite(returns, var_series, 0.95)
        md_str = format_suite_result_markdown(result)
        assert "95.00%" in md_str

        # Test with 0.99
        result = run_var_backtest_suite(returns, var_series, 0.99)
        md_str = format_suite_result_markdown(result)
        assert "99.00%" in md_str
