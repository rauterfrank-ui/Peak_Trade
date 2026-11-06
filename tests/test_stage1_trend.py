"""
Tests for Stage1 Trend Module (Phase 16K)
"""

import json
from pathlib import Path

import pytest

from src.obs.stage1.models import Stage1Summary, Stage1Metrics
from src.obs.stage1.trend import compute_trend_from_summaries, load_trend


def test_compute_trend_from_summaries_empty():
    """Test trend computation with no summaries."""
    trend = compute_trend_from_summaries([], days=7)

    assert trend is not None
    assert len(trend.series) == 0
    assert trend.rollups.new_alerts_total == 0
    assert trend.rollups.go_no_go == "GO"


def test_compute_trend_from_summaries_go_status():
    """Test GO status when all checks pass."""
    summaries = [
        Stage1Summary(
            schema_version=1,
            date=f"2025-12-{20 - i:02d}",
            created_at_utc=f"2025-12-{20 - i:02d}T10:00:00+00:00",
            report_dir="/tmp",
            metrics=Stage1Metrics(
                new_alerts=0,
                critical_alerts=0,
                parse_errors=0,
                operator_actions=0,
                legacy_alerts=0,
            ),
            notes=[],
        )
        for i in range(7)
    ]

    trend = compute_trend_from_summaries(summaries, days=7)

    assert len(trend.series) == 7
    assert trend.rollups.new_alerts_total == 0
    assert trend.rollups.critical_days == 0
    assert trend.rollups.go_no_go == "GO"
    assert "all checks passed" in trend.rollups.reasons


def test_compute_trend_from_summaries_no_go_critical():
    """Test NO_GO status when critical alerts present."""
    summaries = [
        Stage1Summary(
            schema_version=1,
            date=f"2025-12-{20 - i:02d}",
            created_at_utc=f"2025-12-{20 - i:02d}T10:00:00+00:00",
            report_dir="/tmp",
            metrics=Stage1Metrics(
                new_alerts=0,
                critical_alerts=1 if i == 0 else 0,  # One critical day
                parse_errors=0,
                operator_actions=0,
                legacy_alerts=0,
            ),
            notes=[],
        )
        for i in range(7)
    ]

    trend = compute_trend_from_summaries(summaries, days=7)

    assert trend.rollups.critical_days == 1
    assert trend.rollups.go_no_go == "NO_GO"
    assert any("critical alerts" in r for r in trend.rollups.reasons)


def test_compute_trend_from_summaries_hold_high_alerts():
    """Test HOLD status when new alerts exceed threshold."""
    summaries = [
        Stage1Summary(
            schema_version=1,
            date=f"2025-12-{20 - i:02d}",
            created_at_utc=f"2025-12-{20 - i:02d}T10:00:00+00:00",
            report_dir="/tmp",
            metrics=Stage1Metrics(
                new_alerts=2,  # Total will be 14 over 7 days
                critical_alerts=0,
                parse_errors=0,
                operator_actions=0,
                legacy_alerts=0,
            ),
            notes=[],
        )
        for i in range(7)
    ]

    trend = compute_trend_from_summaries(summaries, days=7)

    assert trend.rollups.new_alerts_total == 14
    assert trend.rollups.go_no_go == "HOLD"
    assert any("new_alerts_total" in r for r in trend.rollups.reasons)


def test_compute_trend_from_summaries_averages():
    """Test that averages are computed correctly."""
    summaries = [
        Stage1Summary(
            schema_version=1,
            date=f"2025-12-{20 - i:02d}",
            created_at_utc=f"2025-12-{20 - i:02d}T10:00:00+00:00",
            report_dir="/tmp",
            metrics=Stage1Metrics(
                new_alerts=i,  # 0,1,2,3,4,5,6 = 21 total
                critical_alerts=0,
                parse_errors=0,
                operator_actions=1 if i % 2 == 0 else 0,  # 4 days
                legacy_alerts=0,
            ),
            notes=[],
        )
        for i in range(7)
    ]

    trend = compute_trend_from_summaries(summaries, days=7)

    assert trend.rollups.new_alerts_total == 21
    assert trend.rollups.new_alerts_avg == 3.0  # 21/7
    assert trend.rollups.operator_action_days == 4


def test_load_trend_from_json_file(tmp_path):
    """Test loading pre-computed trend from JSON."""
    trend_data = {
        "schema_version": 1,
        "generated_at_utc": "2025-12-20T10:00:00+00:00",
        "range": {
            "days": 7,
            "start": "2025-12-14",
            "end": "2025-12-20",
        },
        "series": [
            {
                "date": f"2025-12-{14 + i}",
                "new_alerts": 0,
                "critical_alerts": 0,
                "parse_errors": 0,
                "operator_actions": 0,
            }
            for i in range(7)
        ],
        "rollups": {
            "new_alerts_total": 0,
            "new_alerts_avg": 0.0,
            "critical_days": 0,
            "parse_error_days": 0,
            "operator_action_days": 0,
            "go_no_go": "GO",
            "reasons": ["all checks passed"],
        },
    }

    trend_path = tmp_path / "stage1_trend.json"
    trend_path.write_text(json.dumps(trend_data))

    result = load_trend(tmp_path, days=14)

    assert result is not None
    assert result.range.days == 7
    assert len(result.series) == 7
    assert result.rollups.go_no_go == "GO"


def test_load_trend_computes_when_no_json(tmp_path):
    """Test that trend is computed from summaries when no JSON exists."""
    # Create some summary files
    for i in range(3):
        summary_data = {
            "schema_version": 1,
            "date": f"2025-12-{20 - i:02d}",
            "created_at_utc": f"2025-12-{20 - i:02d}T10:00:00+00:00",
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
        summary_path = tmp_path / f"2025-12-{20 - i:02d}_summary.json"
        summary_path.write_text(json.dumps(summary_data))

    result = load_trend(tmp_path, days=7)

    assert result is not None
    assert len(result.series) == 3  # Only 3 summaries available
    assert result.rollups.go_no_go == "GO"


def test_load_trend_nonexistent_dir():
    """Test loading trend from non-existent directory."""
    result = load_trend(Path("/nonexistent/path"), days=7)
    assert result is None
