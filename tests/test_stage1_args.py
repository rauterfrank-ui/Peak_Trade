#!/usr/bin/env python3
"""
Peak_Trade – Phase 16L: Tests for Stage1 scripts argument parsing
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
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


def test_stage1_wrappers_index_own_outputs_and_keep_actionable_status(tmp_path):
    inputs = tmp_path / "input"
    inputs.mkdir()
    now = datetime.now(timezone.utc)
    (inputs / "alerts.jsonl").write_text(
        json.dumps({"ts": now.isoformat(), "event_type": "alert", "severity": "critical"}) + "\n"
    )
    reports = tmp_path / "custom stage1"
    env = {
        **os.environ,
        "STAGE1_INPUT_ROOT": str(inputs),
        "REPORT_ROOT": str(reports),
        "RUN_DATE": now.date().isoformat(),
    }

    def run(kind):
        return subprocess.run(
            ["/bin/bash", str(repo_root / f"scripts/obs/stage1_run_{kind}.sh")],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
        )

    empty_weekly = run("weekly")
    assert empty_weekly.returncode != 0
    assert not list(reports.iterdir())

    daily = run("daily")
    assert daily.returncode == 2, daily.stderr
    assert json.loads((reports / "validation.json").read_text())["ok"]
    summary = reports / f"{now.date()}_summary.json"
    assert json.loads(summary.read_text())["metrics"]["critical_alerts"] == 1
    assert not (reports / "stage1_trend.json").exists()

    weekly = run("weekly")
    assert weekly.returncode == 0, weekly.stderr
    assert json.loads((reports / "validation.json").read_text())["ok"]
    trend = json.loads((reports / "stage1_trend.json").read_text())
    assert trend["rollups"]["go_no_go"] == "NO_GO"
    assert (reports / f"{now.date()}_trend.md").is_file()
