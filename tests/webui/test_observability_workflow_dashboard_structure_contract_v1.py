"""Structure contract: Workflow Dashboard V1 on GET /observability (read-only)."""

from __future__ import annotations

import json
import shutil
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
UNIVERSE_FIXTURES = (
    project_root
    / "tests"
    / "fixtures"
    / "workflow_dashboard_readmodel_v1"
    / "universe_selection_readmodel_v1"
)


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


def test_persisted_readmodel_renders_futures_only_values(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import json

    from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

    archive = tmp_path / "archive_with_universe"
    shutil.copytree(FIXTURE_ARCHIVE, archive)
    readmodels_dir = archive / "readmodels"
    readmodels_dir.mkdir(parents=True, exist_ok=True)
    src = UNIVERSE_FIXTURES / "complete_minimal" / "universe_selection_readmodel.v1.json"
    payload = json.loads(src.read_text(encoding="utf-8"))
    payload["fixture_marked"] = False
    payload["source_run_id"] = "test_persisted_complete_minimal_non_fixture_marked"
    dest = readmodels_dir / "universe_selection_readmodel.v1.json"
    dest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_manifest_sha256(readmodels_dir)

    monkeypatch.setenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT", str(archive))
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-06-08T12:00:00+00:00")
    client = TestClient(create_app())
    html = client.get("/observability").text
    start = html.index('data-workflow-dashboard-v1="true"')
    end = html.index('data-observability-status-summary="true"')
    section = html[start:end]
    assert "SOLUSDT" in section
    assert "ETHUSDT" in section
    assert "PERSISTED" in section
    assert (
        "GET /market BTC/USD dummy is <strong>not</strong> Future or Paper runtime truth."
        in section
    )
    assert "selected_symbol" not in section
    for marker in (
        'data-workflow-panel-universe-v1="true"',
        'data-workflow-panel-top20-v1="true"',
        'data-workflow-panel-selected-future-v1="true"',
        'data-workflow-panel-future-detail-v1="true"',
    ):
        assert marker in section


def _copy_pipeline_archive_with_cvc_projection(tmp_path: Path) -> Path:
    from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

    archive = tmp_path / "archive_with_cvc_projection"
    shutil.copytree(FIXTURE_ARCHIVE, archive)
    readmodels_dir = archive / "readmodels"
    readmodels_dir.mkdir(parents=True, exist_ok=True)
    src = UNIVERSE_FIXTURES / "complete_minimal" / "universe_selection_readmodel.v1.json"
    dest = readmodels_dir / "universe_selection_readmodel.v1.json"
    payload = json.loads(src.read_text(encoding="utf-8"))
    payload["fixture_marked"] = False
    payload["real_metadata_source_marked"] = True
    payload["observability_truth_allowed"] = False
    payload["non_authorizing"] = True
    payload["selected_future"] = {"truth_status": "NOT_PERSISTED"}
    payload["missing_truth"]["selected_future"] = "SELECTED_FUTURE_NOT_PERSISTED"
    payload["missing_truth"]["future_detail"] = "FUTURE_DETAIL_NOT_AVAILABLE"
    payload["market_snapshot"] = {
        "truth_status": "NOT_PERSISTED",
        "source_kind": "NOT_PERSISTED",
        "snapshot_id": None,
        "exchange": None,
        "captured_at": None,
    }
    evidence = payload.get("evidence")
    if not isinstance(evidence, dict):
        evidence = {}
        payload["evidence"] = evidence
    evidence["candidate_validation_projection"] = True
    evidence["projection_source"] = "candidate_validation_bridge"
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_manifest_sha256(readmodels_dir)
    return archive


def _workflow_dashboard_section(html: str) -> str:
    start = html.index('data-workflow-dashboard-v1="true"')
    end = html.index('data-observability-status-summary="true"')
    return html[start:end]


def test_projection_coverage_section_absent_when_gate_disabled(client_off: TestClient) -> None:
    html = client_off.get("/observability").text
    assert 'data-workflow-panel-projection-coverage-v1="true"' not in html


def test_projection_coverage_section_absent_without_cvc_readmodel(client_on: TestClient) -> None:
    html = client_on.get("/observability").text
    assert 'data-workflow-panel-projection-coverage-v1="true"' not in html


def test_projection_coverage_section_present_with_cvc_archive(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    archive = _copy_pipeline_archive_with_cvc_projection(tmp_path)
    monkeypatch.setenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT", str(archive))
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-06-08T12:00:00+00:00")
    client = TestClient(create_app())
    html = client.get("/observability").text
    section = _workflow_dashboard_section(html)
    assert 'data-workflow-panel-projection-coverage-v1="true"' in section
    assert 'data-projection-coverage-not-truth="true"' in section
    assert 'data-projection-coverage-non-authorizing="true"' in section
    assert 'data-projection-coverage-not-selected-future="true"' in section
    assert 'data-projection-coverage-strict-upstream-blocked="true"' in section
    assert "Projection Coverage" in section
    assert "Candidate Validation" in section
    assert "Non-authorizing" in section
    assert "Not Truth" in section
    assert "Not Selected Future" in section
    assert "Strict Upstream Blocked" in section
    assert "ETHUSDT" in section
    assert "SOLUSDT" in section
    assert "projection_universe_rows=3" in section
    assert "projection_ranking_rows=2" in section


def test_projection_coverage_truth_panels_unchanged_with_cvc_archive(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    archive = _copy_pipeline_archive_with_cvc_projection(tmp_path)
    monkeypatch.setenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT", str(archive))
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-06-08T12:00:00+00:00")
    client = TestClient(create_app())
    html = client.get("/observability").text
    section = _workflow_dashboard_section(html)
    assert "UNIVERSE_SOURCE_NOT_PERSISTED" in section
    assert "TOP20_RANKING_NOT_PERSISTED" in section
    assert "SELECTED_FUTURE_NOT_PERSISTED" in section
    assert "FUTURE_DETAIL_NOT_AVAILABLE" in section
    assert 'data-workflow-panel-projection-coverage-v1="true"' in section
    universe_start = section.index('data-workflow-panel-universe-v1="true"')
    universe_end = section.index('data-workflow-panel-top20-v1="true"')
    universe_panel = section[universe_start:universe_end]
    assert 'data-workflow-universe-truth-status="UNIVERSE_SOURCE_NOT_PERSISTED"' in universe_panel
    assert "No persisted universe rows" in universe_panel
    top20_start = section.index('data-workflow-panel-top20-v1="true"')
    top20_end = section.index('data-workflow-panel-selected-future-v1="true"')
    top20_panel = section[top20_start:top20_end]
    assert 'data-workflow-top20-truth-status="TOP20_RANKING_NOT_PERSISTED"' in top20_panel
    assert "not persisted" in top20_panel.lower()


def test_projection_coverage_section_forbidden_wording_absent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    archive = _copy_pipeline_archive_with_cvc_projection(tmp_path)
    monkeypatch.setenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT", str(archive))
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-06-08T12:00:00+00:00")
    client = TestClient(create_app())
    html = client.get("/observability").text
    section = _workflow_dashboard_section(html)
    proj_start = section.index('data-workflow-panel-projection-coverage-v1="true"')
    proj_end = section.index('data-workflow-panel-pipeline-v1="true"')
    proj_section = section[proj_start:proj_end].lower()
    for forbidden in ("ready", "tradeable", " live ", "preflight", "persisted truth"):
        assert forbidden not in proj_section


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
