"""
Tests for VaR Backtest Suite Report Formatter.

Phase 8C: Suite Report & Regression Guard
"""

import json

import pytest

from src.risk.validation.suite_runner import VaRBacktestSuiteResult
from src.risk.validation.report_formatter import (
    format_suite_result_json,
    format_suite_result_markdown,
)


class TestFormatSuiteResultJson:
    """Tests for format_suite_result_json."""

    def test_json_structure_all_pass(self):
        """Test JSON structure when all tests pass."""
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

        json_str = format_suite_result_json(result)
        data = json.loads(json_str)

        # Check top-level keys
        assert "suite_metadata" in data
        assert "test_results" in data
        assert "overall_result" in data

        # Check metadata
        assert data["suite_metadata"]["observations"] == 100
        assert data["suite_metadata"]["breaches"] == 5
        assert data["suite_metadata"]["confidence_level"] == 0.95

        # Check test results
        assert data["test_results"]["kupiec_pof"]["result"] == "PASS"
        assert data["test_results"]["kupiec_pof"]["p_value"] == 0.123456
        assert data["test_results"]["basel_traffic_light"]["result"] == "GREEN"
        assert data["test_results"]["christoffersen_ind"]["result"] == "PASS"
        assert data["test_results"]["christoffersen_ind"]["p_value"] == 0.234567
        assert data["test_results"]["christoffersen_cc"]["result"] == "PASS"
        assert data["test_results"]["christoffersen_cc"]["p_value"] == 0.345678

        # Check overall
        assert data["overall_result"] == "PASS"

    def test_json_deterministic(self):
        """Test that JSON output is deterministic (same input = same output)."""
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

        json_str1 = format_suite_result_json(result)
        json_str2 = format_suite_result_json(result)

        assert json_str1 == json_str2

    def test_json_valid_parseable(self):
        """Test that JSON output is valid and parseable."""
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

        json_str = format_suite_result_json(result)

        # Should not raise
        data = json.loads(json_str)
        assert isinstance(data, dict)

    def test_json_with_fail_results(self):
        """Test JSON output when tests fail."""
        result = VaRBacktestSuiteResult(
            observations=100,
            breaches=50,
            confidence_level=0.95,
            kupiec_pof_result="FAIL",
            kupiec_pof_pvalue=0.000001,
            basel_traffic_light="RED",
            christoffersen_ind_result="FAIL",
            christoffersen_ind_pvalue=0.000002,
            christoffersen_cc_result="FAIL",
            christoffersen_cc_pvalue=0.000003,
        )

        json_str = format_suite_result_json(result)
        data = json.loads(json_str)

        assert data["overall_result"] == "FAIL"
        assert data["test_results"]["kupiec_pof"]["result"] == "FAIL"
        assert data["test_results"]["basel_traffic_light"]["result"] == "RED"
        assert data["test_results"]["christoffersen_ind"]["result"] == "FAIL"
        assert data["test_results"]["christoffersen_cc"]["result"] == "FAIL"


class TestFormatSuiteResultMarkdown:
    """Tests for format_suite_result_markdown."""

    def test_markdown_structure_all_pass(self):
        """Test Markdown structure when all tests pass."""
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

        md_str = format_suite_result_markdown(result)

        # Check key sections
        assert "# VaR Backtest Suite Report" in md_str
        assert "Overall Result" in md_str
        assert "✅ PASS" in md_str
        assert "Suite Metadata" in md_str
        assert "Test Results" in md_str
        assert "Interpretation" in md_str

        # Check metadata
        assert "Observations:** 100" in md_str
        assert "Breaches:** 5" in md_str
        assert "Confidence Level:** 95.00%" in md_str

        # Check test results
        assert "Kupiec POF" in md_str
        assert "Basel Traffic Light" in md_str
        assert "Christoffersen IND" in md_str
        assert "Christoffersen CC" in md_str

    def test_markdown_deterministic(self):
        """Test that Markdown output is deterministic."""
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

        md_str1 = format_suite_result_markdown(result)
        md_str2 = format_suite_result_markdown(result)

        assert md_str1 == md_str2

    def test_markdown_with_fail_results(self):
        """Test Markdown output when tests fail."""
        result = VaRBacktestSuiteResult(
            observations=100,
            breaches=50,
            confidence_level=0.95,
            kupiec_pof_result="FAIL",
            kupiec_pof_pvalue=0.000001,
            basel_traffic_light="RED",
            christoffersen_ind_result="FAIL",
            christoffersen_ind_pvalue=0.000002,
            christoffersen_cc_result="FAIL",
            christoffersen_cc_pvalue=0.000003,
        )

        md_str = format_suite_result_markdown(result)

        assert "❌ FAIL" in md_str
        assert "🔴 RED" in md_str
        assert "One or more tests failed" in md_str

    def test_markdown_yellow_traffic_light(self):
        """Test Markdown output with YELLOW traffic light."""
        result = VaRBacktestSuiteResult(
            observations=250,
            breaches=7,
            confidence_level=0.99,
            kupiec_pof_result="PASS",
            kupiec_pof_pvalue=0.123456,
            basel_traffic_light="YELLOW",
            christoffersen_ind_result="PASS",
            christoffersen_ind_pvalue=0.234567,
            christoffersen_cc_result="PASS",
            christoffersen_cc_pvalue=0.345678,
        )

        md_str = format_suite_result_markdown(result)

        assert "🟡 YELLOW" in md_str
        assert "❌ FAIL" in md_str  # Overall result should be FAIL

    def test_markdown_table_format(self):
        """Test that Markdown table is properly formatted."""
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

        md_str = format_suite_result_markdown(result)

        # Check table structure
        assert "| Test | Result | Details |" in md_str
        assert "|------|--------|---------|" in md_str
        assert "| Kupiec POF |" in md_str
        assert "| Basel Traffic Light |" in md_str
        assert "| Christoffersen IND |" in md_str
        assert "| Christoffersen CC |" in md_str

    def test_markdown_pvalue_precision(self):
        """Test that p-values are formatted with 6 decimals."""
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

        md_str = format_suite_result_markdown(result)

        assert "0.123456" in md_str
        assert "0.234567" in md_str
        assert "0.345678" in md_str
