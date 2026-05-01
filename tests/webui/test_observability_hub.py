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
    assert 'data-observability-safety-banner="true"' in body
    assert "Keine Orders" in body
    assert "Testnet" in body or "Live" in body
    assert "Capital" in body or "Scope" in body
    assert "KillSwitch" in body or "Risk" in body
    assert 'href="/market' in body
    assert "/api/market/ohlcv" in body
    assert "/health/detailed" in body
    assert "/api/master-v2/double-play/dashboard-display.json" in body
    assert "/r_and_d/experiments" in body
    assert "/ops/ci-health/status" in body
    assert 'method="POST"' not in body


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
