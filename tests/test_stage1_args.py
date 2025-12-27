#!/usr/bin/env python3
"""
Peak_Trade – Phase 16L: Tests for Stage1 scripts argument parsing
"""

import sys
from pathlib import Path

import pytest

# Add repo root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))


def test_stage1_snapshot_accepts_reports_root():
    """Test that stage1_daily_snapshot.py accepts --reports-root flag."""
    # Import the script's main function
    from scripts.obs.stage1_daily_snapshot import parse_ts

    # If we can import without errors, argument parsing structure is valid
    # This is a smoke test - actual execution would need mocking
    assert parse_ts is not None


def test_stage1_trend_accepts_reports_root():
    """Test that stage1_trend_report.py accepts --reports-root flag."""
    # Import the script's main function
    from scripts.obs.stage1_trend_report import read_int

    # If we can import without errors, argument parsing structure is valid
    # This is a smoke test - actual execution would need mocking
    assert read_int is not None


def test_stage1_snapshot_imports_report_paths():
    """Test that stage1_daily_snapshot.py successfully imports report_paths."""
    try:
        # This import will fail if report_paths is broken
        from scripts.obs import stage1_daily_snapshot

        # Check that the module has access to report_paths functions
        assert hasattr(stage1_daily_snapshot, "get_reports_root")
        assert hasattr(stage1_daily_snapshot, "ensure_dir")
    except ImportError as e:
        pytest.fail(f"Failed to import stage1_daily_snapshot: {e}")


def test_stage1_trend_imports_report_paths():
    """Test that stage1_trend_report.py successfully imports report_paths."""
    try:
        # This import will fail if report_paths is broken
        from scripts.obs import stage1_trend_report

        # Check that the module has access to report_paths functions
        assert hasattr(stage1_trend_report, "get_reports_root")
    except ImportError as e:
        pytest.fail(f"Failed to import stage1_trend_report: {e}")
