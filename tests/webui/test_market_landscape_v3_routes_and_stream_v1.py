"""Landscape V3 routes, snapshot, and WebSocket stream tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_v3.constants_v1 import (
    AUTHORITY,
    V3_HTML_ROUTE,
    V3_SNAPSHOT_API_ROUTE,
    V3_STREAM_WS_ROUTE,
)


def test_v3_html_route_without_upstream_live() -> None:
    client = TestClient(create_app())
    resp = client.get(V3_HTML_ROUTE)
    assert resp.status_code == 200
    assert "data-market-landscape-v3" in resp.text
    assert "market_dashboard_landscape_v3.js" in resp.text
    assert "market_dashboard_landscape_v2" not in resp.text


def test_v2_market_route_unchanged() -> None:
    client = TestClient(create_app())
    resp = client.get("/market")
    assert resp.status_code == 200
    assert 'data-market-landscape-v2="true"' in resp.text


def test_snapshot_schema_authority_none() -> None:
    client = TestClient(create_app())
    snap = client.get(V3_SNAPSHOT_API_ROUTE).json()
    assert snap["authority"] == AUTHORITY
    assert snap["read_only"] is True
    assert snap["type"] == "snapshot" or snap.get("presentation_schema")


def test_websocket_snapshot_bootstrap_and_resync() -> None:
    client = TestClient(create_app())
    with client.websocket_connect(V3_STREAM_WS_ROUTE) as ws:
        first = ws.receive_json()
        assert first["type"] == "snapshot"
        ws.send_text("resync")
        second = ws.receive_json()
        assert second["type"] == "snapshot"


def test_shell_available_when_transport_disconnected() -> None:
    client = TestClient(create_app())
    snap = client.get(V3_SNAPSHOT_API_ROUTE).json()
    assert snap["transport"]["state"] in {"DISCONNECTED", "CONNECTED", "STALE", "BOOTSTRAP_ONLY"}
    html = client.get(V3_HTML_ROUTE).text
    assert "v3-chart-canvas" in html
