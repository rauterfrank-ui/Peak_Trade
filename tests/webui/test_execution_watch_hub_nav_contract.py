"""
Hub navigation parity for GET /execution_watch (same crosslinks as other Ops standalones).

Execution Watch uses ``templates/peak_trade_dashboard/base.html`` (extends); nav must stay
aligned with standalone ops pages — mirror assertions from
``test_ci_health_dashboard_standalone_hub_nav``.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


@pytest.fixture
def app_client() -> TestClient:
    from src.webui.app import app

    return TestClient(app)


def test_execution_watch_dashboard_hub_nav_parity(app_client: TestClient) -> None:
    """Execution Watch page includes same hub crosslinks as other Operator WebUI standalones."""
    response = app_client.get("/execution_watch")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    html = response.text
    assert "Execution Watch Dashboard" in html
    assert 'href="/ops"' in html
    assert "Ops Cockpit" in html
    assert 'href="/ops/stage1"' in html
    assert 'href="/ops/workflows"' in html
    assert 'href="/ops/ci-health"' in html
    assert "http://127.0.0.1:8010/" in html
    assert "Run UI (companion)" in html
