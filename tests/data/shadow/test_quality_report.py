"""
Tests for Shadow Pipeline Quality Report HTML Generator.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from src.data.shadow.quality_report import render_quality_html_report


def test_render_quality_html_report_basic():
    """Test basic HTML report generation with minimal data."""
    summary = {
        "run_timestamp": datetime(2025, 12, 27, 15, 30, 45),
        "symbol": "XBT/EUR",
        "timeframe": "1m",
        "tick_count": 100,
        "bar_count": 10,
        "quality_events": [],
    }

    html = render_quality_html_report(summary)

    # Verify HTML structure
    assert html.startswith("<!DOCTYPE html>")
    assert html.endswith("</html>\n")
    assert "<title>Shadow Pipeline Quality Report</title>" in html

    # Verify metadata is present
    assert "XBT/EUR" in html
    assert "1m" in html
    assert "100" in html  # tick count
    assert "10" in html  # bar count

    # Verify "no quality issues" message when events list is empty
    assert "No quality issues detected" in html


def test_render_quality_html_report_with_events():
    """Test HTML report generation with quality events."""
    summary = {
        "run_timestamp": datetime(2025, 12, 27, 15, 30, 45),
        "symbol": "BTC-USD",
        "timeframe": "5m",
        "tick_count": 500,
        "bar_count": 20,
        "quality_events": [
            {
                "kind": "GAP",
                "severity": "WARN",
                "ts_ms": 1735317045000,
                "details": {
                    "expected_next_start_ms": 1735317000000,
                    "actual_next_start_ms": 1735317300000,
                    "missing_bars": 1,
                },
            },
            {
                "kind": "SPIKE",
                "severity": "ERROR",
                "ts_ms": 1735317600000,
                "details": {
                    "abs_log_return": 0.15,
                    "threshold": 0.10,
                },
            },
        ],
    }

    html = render_quality_html_report(summary)

    # Verify HTML structure
    assert html.startswith("<!DOCTYPE html>")
    assert html.endswith("</html>\n")

    # Verify metadata
    assert "BTC-USD" in html
    assert "5m" in html
    assert "500" in html
    assert "20" in html

    # Verify events are rendered
    assert "GAP" in html
    assert "WARN" in html
    assert "SPIKE" in html
    assert "ERROR" in html

    # Verify event details are present
    assert "missing_bars=1" in html
    assert "abs_log_return=0.15" in html

    # Should NOT have "no quality issues" message
    assert "No quality issues detected" not in html


def test_render_quality_html_report_timestamp_string():
    """Test HTML report generation with timestamp as string."""
    summary = {
        "run_timestamp": "2025-12-27T15:30:45Z",
        "symbol": "ETH/EUR",
        "timeframe": "15m",
        "tick_count": 50,
        "bar_count": 5,
        "quality_events": [],
    }

    html = render_quality_html_report(summary)

    # Should handle string timestamp gracefully
    assert "2025-12-27T15:30:45Z" in html
    assert "ETH/EUR" in html


def test_render_quality_html_report_contains_css():
    """Test that HTML report includes CSS styling."""
    summary = {
        "run_timestamp": datetime.utcnow(),
        "symbol": "TEST/USD",
        "timeframe": "1m",
        "tick_count": 10,
        "bar_count": 2,
        "quality_events": [],
    }

    html = render_quality_html_report(summary)

    # Verify CSS is present
    assert "<style>" in html
    assert "font-family:" in html
    assert ".container" in html
    assert ".metadata" in html


def test_render_quality_html_report_standalone():
    """Test that HTML report is standalone (no external dependencies)."""
    summary = {
        "run_timestamp": datetime.utcnow(),
        "symbol": "BTC/USD",
        "timeframe": "1m",
        "tick_count": 1,
        "bar_count": 1,
        "quality_events": [],
    }

    html = render_quality_html_report(summary)

    # Should not reference external resources
    assert "http://" not in html
    assert "https://" not in html
    assert "<link" not in html  # No external stylesheets
    assert "<script" not in html  # No external scripts

    # All CSS should be inline
    assert "<style>" in html
