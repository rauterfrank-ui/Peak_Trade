"""
Tests for Stage1 IO Module (Phase 16K)
"""

import json
from pathlib import Path

import pytest

from src.obs.stage1.io import (
    discover_stage1_days,
    load_stage1_summary,
    load_latest_summary,
    load_all_summaries,
)
from src.obs.stage1.models import Stage1Summary


def test_discover_stage1_days_empty(tmp_path):
    """Test discovery with no reports."""
    result = discover_stage1_days(tmp_path)
    assert result == []


def test_discover_stage1_days_with_summaries(tmp_path):
    """Test discovery with summary files."""
    # Create some summary files
    (tmp_path / "2025-12-20_summary.json").write_text("{}")
    (tmp_path / "2025-12-19_summary.json").write_text("{}")
    
    result = discover_stage1_days(tmp_path)
    assert len(result) > 0


def test_load_stage1_summary_missing(tmp_path):
    """Test loading non-existent summary."""
    result = load_stage1_summary(tmp_path, date="2025-12-20")
    assert result is None


def test_load_stage1_summary_valid(tmp_path):
    """Test loading valid summary."""
    summary_data = {
        "schema_version": 1,
        "date": "2025-12-20",
        "created_at_utc": "2025-12-20T10:00:00+00:00",
        "report_dir": str(tmp_path),
        "metrics": {
            "new_alerts": 5,
            "critical_alerts": 1,
            "parse_errors": 0,
            "operator_actions": 2,
            "legacy_alerts": 10,
        },
        "notes": ["test note"],
    }
    
    summary_path = tmp_path / "2025-12-20_summary.json"
    summary_path.write_text(json.dumps(summary_data))
    
    result = load_stage1_summary(tmp_path, date="2025-12-20")
    
    assert result is not None
    assert isinstance(result, Stage1Summary)
    assert result.date == "2025-12-20"
    assert result.metrics.new_alerts == 5
    assert result.metrics.critical_alerts == 1
    assert "test note" in result.notes


def test_load_stage1_summary_invalid_json(tmp_path):
    """Test loading invalid JSON."""
    summary_path = tmp_path / "2025-12-20_summary.json"
    summary_path.write_text("not valid json")
    
    result = load_stage1_summary(tmp_path, date="2025-12-20")
    assert result is None


def test_load_latest_summary_empty(tmp_path):
    """Test loading latest from empty directory."""
    result = load_latest_summary(tmp_path)
    assert result is None


def test_load_latest_summary_picks_newest(tmp_path):
    """Test that latest summary picks the newest file."""
    # Create multiple summaries
    for date in ["2025-12-18", "2025-12-19", "2025-12-20"]:
        summary_data = {
            "schema_version": 1,
            "date": date,
            "created_at_utc": f"{date}T10:00:00+00:00",
            "report_dir": str(tmp_path),
            "metrics": {
                "new_alerts": int(date.split("-")[-1]),  # Use day as identifier
                "critical_alerts": 0,
                "parse_errors": 0,
                "operator_actions": 0,
                "legacy_alerts": 0,
            },
            "notes": [],
        }
        summary_path = tmp_path / f"{date}_summary.json"
        summary_path.write_text(json.dumps(summary_data))
    
    result = load_latest_summary(tmp_path)
    
    assert result is not None
    assert result.date == "2025-12-20"  # Newest
    assert result.metrics.new_alerts == 20  # Day number


def test_load_all_summaries_with_limit(tmp_path):
    """Test loading all summaries with limit."""
    # Create multiple summaries
    dates = ["2025-12-18", "2025-12-19", "2025-12-20", "2025-12-21"]
    for date in dates:
        summary_data = {
            "schema_version": 1,
            "date": date,
            "created_at_utc": f"{date}T10:00:00+00:00",
            "report_dir": str(tmp_path),
            "metrics": {
                "new_alerts": 0,
                "critical_alerts": 0,
                "parse_errors": 0,
                "operator_actions": 0,
                "legacy_alerts": 0,
            },
            "notes": [],
        }
        summary_path = tmp_path / f"{date}_summary.json"
        summary_path.write_text(json.dumps(summary_data))
    
    result = load_all_summaries(tmp_path, limit=2)
    
    assert len(result) == 2
    # Should be newest first
    assert result[0].date == "2025-12-21"
    assert result[1].date == "2025-12-20"

