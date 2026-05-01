"""Observability-Hub (GET /observability) — read-only Link-Schicht ohne POST."""

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


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def test_observability_hub_ok_markers(client: TestClient) -> None:
    r = client.get("/observability")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    body = r.text
    assert 'data-observability-hub="true"' in body
    assert 'data-observability-readonly="true"' in body
    assert 'data-observability-display-only="true"' in body
    assert 'data-observability-safety-banner="true"' in body
    assert 'data-observability-boundary-legend="true"' in body
    assert 'data-observability-status-summary="true"' in body
    assert 'data-observability-market-panel="true"' in body
    assert 'data-observability-market-provenance="true"' in body
    assert 'data-observability-market-no-fetch="true"' in body
    assert 'data-observability-market-no-readiness="true"' in body
    assert 'data-observability-double-play-panel="true"' in body
    assert 'data-observability-double-play-display-json="true"' in body
    assert 'data-observability-double-play-no-authority="true"' in body
    assert 'data-observability-rd-panel="true"' in body
    assert 'data-observability-rd-research-only="true"' in body
    assert 'data-observability-rd-no-deployment="true"' in body
    assert 'data-observability-rd-no-strategy-authority="true"' in body
    assert 'data-observability-ops-ci-panel="true"' in body
    assert 'data-observability-ops-ci-readonly-links="true"' in body
    assert 'data-observability-ops-ci-no-workflow-trigger="true"' in body
    assert 'data-observability-ops-ci-no-approval="true"' in body
    assert 'data-observability-health-panel="true"' in body
    assert 'data-observability-health-readonly="true"' in body
    assert 'data-observability-health-no-actions="true"' in body

    assert "read-only / display-only" in body
    assert "Display-only status snapshot" in body
    assert "No backend health certification" in body
    assert "No provider readiness" in body
    assert "No Paper/Testnet/Live/order readiness" in body
    assert "source=dummy" in body
    assert "source=kraken" in body
    assert "offline/synthetic" in body
    assert "does not fetch OHLCV" in body
    assert "does not call Kraken" in body
    assert "not provider readiness" in body
    assert "not Futures readiness" in body
    assert "not Paper/Testnet/Live/order readiness" in body
    assert "not trading authority" in body
    assert "Workflows" in body
    assert "Keine Orders" in body
    assert "Testnet" in body and "Live" in body
    assert "Capital" in body and "Scope" in body
    assert "Risk" in body and "KillSwitch" in body
    assert "Workflow-Trigger" in body
    assert "PaperExecutionEngine" in body
    assert "Display JSON only" in body
    assert "pure snapshot/display contract" in body
    assert "no execution authority" in body
    assert "no strategy authorization" in body
    assert "no Live/Testnet/order path" in body
    assert "no Capital/Scope approval" in body
    assert "no Risk/KillSwitch override" in body
    assert "R&amp;D experiments are research visibility only." in body
    assert "The hub does not fetch experiment data." in body
    assert "The hub does not promote experiments." in body
    assert "The hub does not deploy strategies." in body
    assert "The hub does not authorize strategy output." in body
    assert "R&amp;D display is not readiness approval." in body
    assert "R&amp;D display is not Paper/Testnet/Live/order readiness." in body
    assert "R&amp;D display is not trading authority." in body

    assert 'href="/market' in body
    assert "/api/market/ohlcv" in body
    assert "/health/detailed" in body
    assert 'href="/health"' in body
    assert "/health/metrics" in body
    assert "/health/prometheus" in body
    assert "/api/health" in body
    assert "/api/master-v2/double-play/dashboard-display.json" in body
    assert "/r_and_d/experiments" in body
    assert "/api/r_and_d/experiments?limit=20" in body
    assert 'href="/ops/ci-health"' in body
    assert "/ops/ci-health/status" in body

    assert "The Observability Hub only links to OPS CI GET surfaces." in body
    assert "is the preferred read-only status path." in body
    assert "may show the dedicated CI dashboard, but the Hub itself" in body
    assert "The Hub does not trigger workflows." in body
    assert "The Hub does not start GitHub Actions." in body
    assert "CI status display is not readiness approval." in body
    assert "CI status display is not deployment approval." in body
    assert "CI status display is not Live/Testnet/order readiness." in body
    assert "CI status display is not trading authority." in body

    assert 'method="POST"' not in body
    assert "<form" not in body.lower()
    assert 'type="submit"' not in body
    assert "fetch(" not in body
    assert "/api/knowledge" not in body

    assert "data-observability-health-project-snapshot=" in body


def test_observability_hub_template_knowledge_exclusion_banner() -> None:
    tmpl = (
        Path(__file__).resolve().parents[2]
        / "templates"
        / "peak_trade_dashboard"
        / "observability_hub.html"
    )
    txt = tmpl.read_text(encoding="utf-8")
    assert "Knowledge API" in txt
    assert "/api/knowledge" not in txt


def test_observability_hub_template_health_panel_markers_and_no_post() -> None:
    tmpl = (
        Path(__file__).resolve().parents[2]
        / "templates"
        / "peak_trade_dashboard"
        / "observability_hub.html"
    )
    txt = tmpl.read_text(encoding="utf-8")
    assert 'data-observability-health-panel="true"' in txt
    assert 'data-observability-health-readonly="true"' in txt
    assert 'data-observability-health-no-actions="true"' in txt
    assert 'data-observability-boundary-legend="true"' in txt
    assert 'data-observability-status-summary="true"' in txt
    assert 'data-observability-market-panel="true"' in txt
    assert 'data-observability-market-provenance="true"' in txt
    assert 'data-observability-market-no-fetch="true"' in txt
    assert 'data-observability-market-no-readiness="true"' in txt
    assert 'data-observability-double-play-panel="true"' in txt
    assert 'data-observability-double-play-display-json="true"' in txt
    assert 'data-observability-double-play-no-authority="true"' in txt
    assert 'data-observability-rd-panel="true"' in txt
    assert 'data-observability-rd-research-only="true"' in txt
    assert 'data-observability-rd-no-deployment="true"' in txt
    assert 'data-observability-rd-no-strategy-authority="true"' in txt
    assert 'data-observability-ops-ci-panel="true"' in txt
    assert 'data-observability-ops-ci-readonly-links="true"' in txt
    assert 'data-observability-ops-ci-no-workflow-trigger="true"' in txt
    assert 'data-observability-ops-ci-no-approval="true"' in txt
    assert 'data-observability-display-only="true"' in txt
    assert "read-only / display-only" in txt
    assert "Display-only status snapshot" in txt
    assert "No backend health certification" in txt
    assert "No provider readiness" in txt
    assert "No Paper/Testnet/Live/order readiness" in txt
    assert "source=dummy" in txt
    assert "source=kraken" in txt
    assert "offline/synthetic" in txt
    assert "does not fetch OHLCV" in txt
    assert "does not call Kraken" in txt
    assert "not provider readiness" in txt
    assert "not Futures readiness" in txt
    assert "not Paper/Testnet/Live/order readiness" in txt
    assert "not trading authority" in txt
    assert "Workflows" in txt
    assert "PaperExecutionEngine" in txt
    assert "Workflow-Trigger" in txt
    assert "Display JSON only" in txt
    assert "pure snapshot/display contract" in txt
    assert "no execution authority" in txt
    assert "no strategy authorization" in txt
    assert "no Live/Testnet/order path" in txt
    assert "no Capital/Scope approval" in txt
    assert "no Risk/KillSwitch override" in txt
    assert "R&amp;D experiments are research visibility only." in txt
    assert "The hub does not fetch experiment data." in txt
    assert "The hub does not promote experiments." in txt
    assert "The hub does not deploy strategies." in txt
    assert "The hub does not authorize strategy output." in txt
    assert "R&amp;D display is not readiness approval." in txt
    assert "R&amp;D display is not Paper/Testnet/Live/order readiness." in txt
    assert "R&amp;D display is not trading authority." in txt
    assert "/api/r_and_d/experiments?limit=20" in txt
    assert "The Observability Hub only links to OPS CI GET surfaces." in txt
    assert "The Hub does not start GitHub Actions." in txt
    assert "CI status display is not deployment approval." in txt
    assert 'method="POST"' not in txt
    assert "<form" not in txt.lower()
    assert 'type="submit"' not in txt
    assert "fetch(" not in txt


def test_observability_hub_doc_exists_and_tokens() -> None:
    doc = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "webui"
        / "observability"
        / "OBSERVABILITY_HUB_V0.md"
    )
    assert doc.exists()
    t = doc.read_text(encoding="utf-8")
    assert "PaperExecutionEngine" in t
    assert "`/api/knowledge`" not in t
    assert "GET &#47;observability" in t
    assert "data-observability-" in t
    assert "Paper/Shadow" in t.lower() or "Paper" in t
