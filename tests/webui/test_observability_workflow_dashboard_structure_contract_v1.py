"""Structure contract: Workflow Dashboard V1 on GET /observability (read-only)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

from src.webui.app import create_app

FIXTURE_ARCHIVE = (
    project_root
    / "tests"
    / "fixtures"
    / "workflow_dashboard_readmodel_v1"
    / "pipeline_minimal"
    / "archive_root"
).resolve()
LPR_FIXTURE = (
    project_root
    / "tests"
    / "fixtures"
    / "last_paper_run_panel_readmodel_v0"
    / "p1_complete_minimal"
).resolve()


@pytest.fixture()
def client_off() -> TestClient:
    return TestClient(create_app())


@pytest.fixture()
def client_on(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT", str(FIXTURE_ARCHIVE))
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-06-08T12:00:00+00:00")
    return TestClient(create_app())


def test_workflow_dashboard_absent_when_gate_disabled(client_off: TestClient) -> None:
    html = client_off.get("/observability").text
    assert 'data-workflow-dashboard-v1="true"' not in html


def test_workflow_dashboard_present_when_gate_enabled(client_on: TestClient) -> None:
    html = client_on.get("/observability").text
    assert 'data-workflow-dashboard-v1="true"' in html
    assert 'data-workflow-dashboard-readonly="true"' in html
    assert 'data-workflow-dashboard-authority="false"' in html
    assert 'data-workflow-dashboard-no-controls-v1="true"' in html


def test_all_panel_markers_present(client_on: TestClient) -> None:
    html = client_on.get("/observability").text
    for marker in (
        'data-workflow-panel-safety-v1="true"',
        'data-workflow-panel-universe-v1="true"',
        'data-workflow-panel-top20-v1="true"',
        'data-workflow-panel-selected-future-v1="true"',
        'data-workflow-panel-future-detail-v1="true"',
        'data-workflow-panel-pipeline-v1="true"',
        'data-workflow-panel-orders-fills-v1="true"',
        'data-workflow-panel-evidence-v1="true"',
        'data-workflow-panel-killswitch-v1="true"',
        'data-workflow-panel-next-go-v1="true"',
    ):
        assert marker in html


def test_pipeline_stages_visible(client_on: TestClient) -> None:
    html = client_on.get("/observability").text
    for key in ("P1", "P2", "S1", "T1_ORIGINAL", "T1_REPAIR", "T2", "T3"):
        assert f'data-workflow-stage-v1="{key}"' in html
    assert "PLANNED_PARKED" in html


def test_t1_reclassified_badge(client_on: TestClient) -> None:
    html = client_on.get("/observability").text
    assert 'data-workflow-stage-reclassified-v1="RECLASSIFIED_STAGING_ONLY"' in html


def test_missing_truth_visible(client_on: TestClient) -> None:
    html = client_on.get("/observability").text
    assert "UNIVERSE_SOURCE_NOT_PERSISTED" in html
    assert "TOP20_RANKING_NOT_PERSISTED" in html
    assert "SELECTED_FUTURE_NOT_PERSISTED" in html
    assert "FUTURE_DETAIL_NOT_AVAILABLE" in html
    assert 'data-workflow-pnl-status="NOT_PERSISTED"' in html


def test_no_controls_in_workflow_section(client_on: TestClient) -> None:
    html = client_on.get("/observability").text
    start = html.index('data-workflow-dashboard-v1="true"')
    end = html.index('data-observability-status-summary="true"')
    section = html[start:end]
    assert "<form" not in section.lower()
    assert 'method="POST"' not in section
    assert "<button" not in section.lower()
    assert "fetch(" not in section


def test_btc_not_workflow_truth(client_on: TestClient) -> None:
    html = client_on.get("/observability").text
    start = html.index('data-workflow-dashboard-v1="true"')
    end = html.index('data-observability-status-summary="true"')
    section = html[start:end]
    assert (
        "GET /market BTC/USD dummy is <strong>not</strong> Future or Paper runtime truth."
        in section
    )
    assert "instrument_truth_status" not in section
    assert "selected_symbol" not in section


def test_market_separation(client_off: TestClient) -> None:
    html = client_off.get("/market").text
    assert 'data-workflow-dashboard-v1="true"' not in html
    assert 'data-market-v0-paper-run-truth-separation-v0="true"' in html


def test_last_paper_run_still_works_with_both_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT", str(FIXTURE_ARCHIVE))
    monkeypatch.setenv("PEAK_TRADE_LAST_PAPER_RUN_PANEL_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_LAST_PAPER_RUN_BUNDLE_ROOT", str(LPR_FIXTURE))
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-06-08T12:00:00+00:00")
    client = TestClient(create_app())
    html = client.get("/observability").text
    assert 'data-workflow-dashboard-v1="true"' in html
    assert 'data-observability-last-paper-run-panel-v0="true"' in html
