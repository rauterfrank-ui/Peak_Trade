"""Structure contract: Market single-page consolidation on GET /market (view-only)."""

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

CONSOLIDATION_ENV = "PEAK_TRADE_MARKET_SINGLE_PAGE_CONSOLIDATION_V1_ENABLED"


@pytest.fixture()
def client_off(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.delenv(CONSOLIDATION_ENV, raising=False)
    monkeypatch.delenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT", raising=False)
    monkeypatch.delenv("PEAK_TRADE_LAST_PAPER_RUN_PANEL_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_LAST_PAPER_RUN_BUNDLE_ROOT", raising=False)
    return TestClient(create_app())


@pytest.fixture()
def client_on(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv(CONSOLIDATION_ENV, "1")
    monkeypatch.setenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT", str(FIXTURE_ARCHIVE))
    monkeypatch.setenv("PEAK_TRADE_LAST_PAPER_RUN_PANEL_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_LAST_PAPER_RUN_BUNDLE_ROOT", str(LPR_FIXTURE))
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-06-08T12:00:00+00:00")
    return TestClient(create_app())


def test_consolidation_absent_when_gate_disabled(client_off: TestClient) -> None:
    html = client_off.get("/market?source=dummy").text
    assert 'data-market-single-page-consolidation-v1="true"' not in html
    assert 'data-workflow-dashboard-v1="true"' not in html
    assert 'data-observability-last-paper-run-panel-v0="true"' not in html


def test_consolidation_present_when_gate_enabled(client_on: TestClient) -> None:
    html = client_on.get("/market?source=dummy").text
    assert 'data-market-single-page-consolidation-v1="true"' in html
    assert 'data-market-single-page-consolidation-readonly="true"' in html
    assert 'data-market-single-page-consolidation-authority="false"' in html
    assert 'data-market-single-page-consolidation-gated="true"' in html


def test_workflow_dashboard_markers_on_market(client_on: TestClient) -> None:
    html = client_on.get("/market?source=dummy").text
    assert 'data-workflow-dashboard-v1="true"' in html
    assert 'data-workflow-dashboard-readonly="true"' in html
    assert 'data-workflow-dashboard-authority="false"' in html
    for marker in (
        'data-workflow-panel-safety-v1="true"',
        'data-workflow-panel-universe-v1="true"',
        'data-workflow-panel-top20-v1="true"',
        'data-workflow-panel-selected-future-v1="true"',
        'data-workflow-panel-pipeline-v1="true"',
        'data-workflow-panel-killswitch-v1="true"',
        'data-workflow-panel-next-go-v1="true"',
    ):
        assert marker in html


def test_last_paper_run_marker_on_market(client_on: TestClient) -> None:
    html = client_on.get("/market?source=dummy").text
    assert 'data-observability-last-paper-run-panel-v0="true"' in html
    assert 'data-observability-last-paper-run-readonly="true"' in html
    assert 'data-observability-last-paper-run-authority="false"' in html


def test_missing_truth_markers_on_market(client_on: TestClient) -> None:
    html = client_on.get("/market?source=dummy").text
    assert "UNIVERSE_SOURCE_NOT_PERSISTED" in html
    assert "TOP20_RANKING_NOT_PERSISTED" in html
    assert "SELECTED_FUTURE_NOT_PERSISTED" in html
    assert "FUTURE_DETAIL_NOT_AVAILABLE" in html


def test_preflight_blocked_visible_on_market(client_on: TestClient) -> None:
    html = client_on.get("/market?source=dummy").text
    start = html.index('data-market-single-page-consolidation-v1="true"')
    section = html[start : start + 120_000]
    assert "PREFLIGHT_LIFT" in section


def test_negative_safety_markers_on_market(client_on: TestClient) -> None:
    html = client_on.get("/market?source=dummy").text
    assert 'data-dashboard-truth-granted="false"' in html
    assert 'data-selected-tradable-future-created="false"' in html
    assert 'data-readmodel-write-executed="false"' in html
    assert 'data-paper-shadow-testnet-runtime-run-executed="false"' in html


def test_observability_still_supports_workflow_after_partial_refactor(
    client_on: TestClient,
) -> None:
    html = client_on.get("/observability").text
    assert 'data-workflow-dashboard-v1="true"' in html
    assert 'data-observability-last-paper-run-panel-v0="true"' in html
    assert 'data-observability-status-summary="true"' in html
