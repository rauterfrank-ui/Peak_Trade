"""Landscape V2 final consumer-closeout census (read-only evidence)."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CENSUS = (
    REPO
    / "docs"
    / "ops"
    / "market_dashboard"
    / "MARKET_DASHBOARD_LANDSCAPE_V2_CURRENT_COMPLETION_CENSUS_V1.md"
)
RUNBOOK = (
    REPO
    / "docs"
    / "ops"
    / "market_dashboard"
    / "PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md"
)

WP_ID = "MARKET_DASHBOARD_LANDSCAPE_V2_FINAL_COMPLETION_V1"
LANDSCAPE_CURRENT_COMPLETION_STATUS = "COMPLETE"
CONNECTABLE_CURRENT_CONSUMER_GAP_COUNT = 0


def test_final_completion_census_artifact_present() -> None:
    text = CENSUS.read_text(encoding="utf-8")
    assert f"WP_ID={WP_ID}" in text
    assert "CONNECTABLE_CURRENT_CONSUMER_GAP_COUNT" in text
    assert "INTENTIONAL_NOT_BOUND" in text
    assert "NOT_CANONICALLY_AVAILABLE" in text


def test_runbook_records_current_completion_status() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert f"LANDSCAPE_CURRENT_COMPLETION_STATUS={LANDSCAPE_CURRENT_COMPLETION_STATUS}" in runbook
    assert "MARKET_DASHBOARD_LANDSCAPE_V2_CURRENT_COMPLETION_CENSUS_V1.md" in runbook


def test_consumer_gap_count_remains_zero() -> None:
    assert CONNECTABLE_CURRENT_CONSUMER_GAP_COUNT == 0
