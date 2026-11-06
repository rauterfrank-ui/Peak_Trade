"""
Contract test for GET /health (src.webui.health_endpoint): minimal stable JSON shape.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest

pytest.importorskip("fastapi")
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.webui.health_endpoint import router


@pytest.fixture
def health_client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_health_basic_json_contract_stable_keys(health_client: TestClient) -> None:
    """GET /health returns a JSON object with stable top-level keys when checks succeed."""
    with patch(
        "src.webui.health_endpoint.health_check.is_system_healthy",
        return_value=True,
    ):
        response = health_client.get("/health")

    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/json")
    data = response.json()
    assert isinstance(data, dict)
    assert set(data.keys()) >= {"status", "timestamp"}
    assert data["status"] == "healthy"
    assert isinstance(data["timestamp"], str)
    assert len(data["timestamp"]) >= 10
    assert datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))


def test_health_basic_json_contract_unhealthy_returns_503(health_client: TestClient) -> None:
    """Unhealthy system: still JSON with status + timestamp; HTTP 503."""
    with patch(
        "src.webui.health_endpoint.health_check.is_system_healthy",
        return_value=False,
    ):
        response = health_client.get("/health")

    assert response.status_code == 503
    data = response.json()
    assert isinstance(data, dict)
    assert data["status"] == "unhealthy"
    assert "timestamp" in data
    assert isinstance(data["timestamp"], str)
    assert datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
