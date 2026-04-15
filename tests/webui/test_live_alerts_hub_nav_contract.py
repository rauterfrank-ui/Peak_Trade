"""
Hub navigation parity for GET /live/alerts (same crosslinks as other Operator WebUI pages).

Alerts dashboard extends ``templates/peak_trade_dashboard/base.html``; nav alignment mirrors
``test_execution_watch_dashboard_hub_nav_parity``.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


@pytest.fixture
def app_client() -> TestClient:
    from src.webui.app import app

    return TestClient(app)


def test_live_alerts_dashboard_hub_nav_parity(app_client: TestClient) -> None:
    """Live Alerts page includes same hub crosslinks as other Operator WebUI standalones."""
    response = app_client.get("/live/alerts")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    html = response.text
    assert "Alert-Historie" in html
    assert 'href="/ops"' in html
    assert "Ops Cockpit" in html
    assert 'href="/ops/stage1"' in html
    assert 'href="/ops/workflows"' in html
    assert 'href="/ops/ci-health"' in html
    assert "http://127.0.0.1:8010/" in html
    assert "Run UI (companion)" in html
