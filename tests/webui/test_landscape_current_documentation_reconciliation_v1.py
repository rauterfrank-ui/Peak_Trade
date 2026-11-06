"""Docs-only reconciliation contracts for LANDSCAPE_CURRENT_DOCUMENTATION_RECONCILIATION_V1."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RECONCILIATION = (
    REPO
    / "docs"
    / "ops"
    / "market_dashboard"
    / "LANDSCAPE_CURRENT_DOCUMENTATION_RECONCILIATION_V1.md"
)
RUNBOOK = (
    REPO
    / "docs"
    / "ops"
    / "market_dashboard"
    / "PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md"
)
CENSUS = (
    REPO
    / "docs"
    / "ops"
    / "market_dashboard"
    / "MARKET_DASHBOARD_LANDSCAPE_V2_CURRENT_COMPLETION_CENSUS_V1.md"
)
PRESENTATION_RUNBOOK = (
    REPO
    / "docs"
    / "runbooks"
    / "canonical"
    / "PEAK_TRADE_CANONICAL_PRESENTATION_IMPLEMENTATION_RUNBOOK.md"
)

WP_ID = "LANDSCAPE_CURRENT_DOCUMENTATION_RECONCILIATION_V1"
CONSUMER_CLOSEOUT_SHA = "b81d03a4e7169b20f212e8cf80bd581e96e19fc4"
DOC_POINTER_SHA = "f3ced3c5ba146b6f7f26f7c6587fa44947270ee1"


def test_reconciliation_artifact_present_and_separates_closeout_from_ops() -> None:
    text = RECONCILIATION.read_text(encoding="utf-8")
    assert f"WP_ID={WP_ID}" in text
    assert "LAST_MERGED_LANDSCAPE_CONSUMER_CLOSEOUT_PR=6690" not in text
    assert "#6690" in text
    assert CONSUMER_CLOSEOUT_SHA in text
    assert DOC_POINTER_SHA in text
    assert "POST_LANDSCAPE_PRESENTATION_OPS_MERGE_RANGE=#6697-#6705" in text
    assert "NEXT_ACTION=STOP_IDLE" in text
    assert "CONNECTABLE_CURRENT_CONSUMER_GAP_COUNT=0" in text
    assert "No PR numbered **6711**" in text


def test_landscape_runbook_header_points_at_reconciliation() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert f"CURRENT_ORIGIN_MAIN_DOC_POINTER_SHA={DOC_POINTER_SHA}" in runbook
    assert f"LANDSCAPE_CONSUMER_CLOSEOUT_MERGE_SHA={CONSUMER_CLOSEOUT_SHA}" in runbook
    assert (
        "LANDSCAPE_CURRENT_DOC_RECONCILIATION=docs/ops/market_dashboard/LANDSCAPE_CURRENT_DOCUMENTATION_RECONCILIATION_V1.md"
        in runbook
    )
    assert "POST_LANDSCAPE_PRESENTATION_OPS_LAST_MERGED_PR=6705" in runbook
    assert "NEXT_ACTION=STOP_IDLE" in runbook
    assert "CURRENT_MAIN_SHA=b81d03a4" not in runbook.split("```text", 2)[1]


def test_census_preserves_historical_base_sha() -> None:
    census = CENSUS.read_text(encoding="utf-8")
    assert CONSUMER_CLOSEOUT_SHA in census
    assert "Historical evidence base (frozen)" in census
    assert "LANDSCAPE_CURRENT_DOCUMENTATION_RECONCILIATION_V1.md" in census


def test_presentation_runbook_has_supersession_block() -> None:
    pres = PRESENTATION_RUNBOOK.read_text(encoding="utf-8")
    assert "LANDSCAPE_CURRENT_DOCUMENTATION_RECONCILIATION_V1" in pres
    assert "run_operational_presentation_materializer_invocation_v1.py" in pres
    assert "#6697" in pres
