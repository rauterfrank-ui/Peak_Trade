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
    assert 'data-observability-market-panel="true"' in body
    assert 'data-observability-double-play-panel="true"' in body
    assert 'data-observability-rd-panel="true"' in body
    assert 'data-observability-ops-ci-panel="true"' in body
    assert 'data-observability-health-panel="true"' in body
    assert 'data-observability-health-readonly="true"' in body
    assert 'data-observability-health-no-actions="true"' in body

    assert "read-only / display-only" in body
    assert "Workflows" in body
    assert "Keine Orders" in body
    assert "Testnet" in body and "Live" in body
    assert "Capital" in body and "Scope" in body
    assert "Risk" in body and "KillSwitch" in body
    assert "Workflow-Trigger" in body
    assert "PaperExecutionEngine" in body

    assert 'href="/market' in body
    assert "/api/market/ohlcv" in body
    assert "/health/detailed" in body
    assert 'href="/health"' in body
    assert "/health/metrics" in body
    assert "/health/prometheus" in body
    assert "/api/health" in body
    assert "/api/master-v2/double-play/dashboard-display.json" in body
    assert "/r_and_d/experiments" in body
    assert "/ops/ci-health/status" in body

    assert 'method="POST"' not in body
    assert "<form" not in body.lower()
    assert 'type="submit"' not in body
    assert "fetch(" not in body

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
    assert 'data-observability-market-panel="true"' in txt
    assert 'data-observability-double-play-panel="true"' in txt
    assert 'data-observability-rd-panel="true"' in txt
    assert 'data-observability-ops-ci-panel="true"' in txt
    assert 'data-observability-display-only="true"' in txt
    assert "read-only / display-only" in txt
    assert "Workflows" in txt
    assert "PaperExecutionEngine" in txt
    assert "Workflow-Trigger" in txt
    assert 'method="POST"' not in txt
    assert "<form" not in txt.lower()
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
