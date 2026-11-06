"""
Tests for Shadow Pipeline Quality Report HTML Generator.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from src.data.shadow.quality_report import (
    build_reports_index_html,
    render_quality_html_report,
    update_latest_and_index,
)


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


def test_build_reports_index_html_basic():
    """Test index HTML generation with report list."""
    report_files = [
        "quality_report_20251227_120000.html",
        "quality_report_20251227_110000.html",
        "quality_report_20251227_100000.html",
    ]

    html = build_reports_index_html(report_files, max_entries=20)

    # Verify HTML structure
    assert html.startswith("<!DOCTYPE html>")
    assert html.endswith("</html>\n")
    assert "<title>Shadow Pipeline Quality Reports</title>" in html

    # Verify reports are listed (newest first ordering is preserved)
    assert "quality_report_20251227_120000.html" in html
    assert "quality_report_20251227_110000.html" in html
    assert "quality_report_20251227_100000.html" in html

    # Verify relative links
    assert "./quality_report_20251227_120000.html" in html

    # Verify latest.html link
    assert "./latest.html" in html

    # Should NOT have "no reports" message
    assert "No reports available" not in html


def test_build_reports_index_html_empty():
    """Test index HTML generation with no reports."""
    html = build_reports_index_html([], max_entries=20)

    # Verify HTML structure
    assert html.startswith("<!DOCTYPE html>")
    assert html.endswith("</html>\n")

    # Should have "no reports" message
    assert "No reports available" in html


def test_update_latest_and_index(tmp_path: Path):
    """Test update_latest_and_index creates/updates convenience files."""
    # Create output directory
    output_dir = tmp_path / "reports" / "shadow" / "quality"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create some mock timestamped reports
    report1_path = output_dir / "quality_report_20251227_100000.html"
    report2_path = output_dir / "quality_report_20251227_110000.html"
    report3_path = output_dir / "quality_report_20251227_120000.html"

    report1_path.write_text("<html><body>Report 1</body></html>", encoding="utf-8")
    report2_path.write_text("<html><body>Report 2</body></html>", encoding="utf-8")
    report3_path.write_text("<html><body>Report 3 (newest)</body></html>", encoding="utf-8")

    # Update latest and index with newest report
    result = update_latest_and_index(output_dir, report3_path, max_entries=10)

    # Verify return values
    assert "latest_path" in result
    assert "index_path" in result
    assert "report_count" in result
    assert result["report_count"] == 3

    # Verify latest.html exists and matches newest report
    latest_path = Path(result["latest_path"])
    assert latest_path.exists()
    latest_content = latest_path.read_text(encoding="utf-8")
    assert "Report 3 (newest)" in latest_content

    # Verify index.html exists and contains links
    index_path = Path(result["index_path"])
    assert index_path.exists()
    index_content = index_path.read_text(encoding="utf-8")

    # Verify all reports are listed (newest first)
    assert "quality_report_20251227_120000.html" in index_content
    assert "quality_report_20251227_110000.html" in index_content
    assert "quality_report_20251227_100000.html" in index_content

    # Verify newest is listed before older (check order by finding indices)
    idx_newest = index_content.find("quality_report_20251227_120000.html")
    idx_oldest = index_content.find("quality_report_20251227_100000.html")
    assert idx_newest < idx_oldest  # Newest appears before oldest in HTML
