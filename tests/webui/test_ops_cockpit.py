"""Tests for Ops Cockpit read-only UI."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.webui.app import app
from src.webui.ops_cockpit import load_ops_cockpit_data


def test_ops_cockpit_data_loads_without_crashing() -> None:
    data = load_ops_cockpit_data()
    assert "system_state" in data
    assert "guard_state" in data
    assert "latest_evidence" in data
    assert "latest_testnet_pilot_status" in data
    assert "incidents_abort" in data
    assert "readiness_routing_health" in data


def test_ops_route_responds() -> None:
    client = TestClient(app)
    response = client.get("/ops")
    assert response.status_code == 200
    assert "Peak_Trade Ops Cockpit" in response.text


def test_ops_api_route_responds() -> None:
    client = TestClient(app)
    response = client.get("/api/ops-cockpit")
    assert response.status_code == 200
    payload = response.json()
    assert "system_state" in payload
    assert "latest_evidence" in payload


def test_missing_artifacts_do_not_break_response() -> None:
    client = TestClient(app)
    response = client.get("/api/ops-cockpit")
    assert response.status_code == 200
