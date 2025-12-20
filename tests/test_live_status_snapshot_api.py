# tests/test_live_status_snapshot_api.py
"""
Tests for Live Status Snapshot API Endpoints (Phase 57 Extension).

Tests:
- JSON endpoint 200 + parseable JSON
- JSON has version + panels list
- HTML endpoint 200 + content-type correct
- HTML contains expected panel titles
- XSS safety check (details with <script> are escaped)
- Cache-Control header == no-store (both endpoints)
- Graceful degradation (provider crashes, endpoint still 200)

Run:
    pytest tests/test_live_status_snapshot_api.py -v
"""
from __future__ import annotations

import json
import pytest

# Skip if FastAPI not installed
pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

# Mark all tests in this module as web tests
pytestmark = pytest.mark.web


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def test_client():
    """Create FastAPI test client with live status endpoints."""
    from src.webui.app import create_app

    app = create_app()
    return TestClient(app)


# =============================================================================
# Tests: JSON Endpoint
# =============================================================================


def test_json_endpoint_returns_200(test_client):
    """Test JSON endpoint returns 200 OK."""
    response = test_client.get("/api/live/status/snapshot.json")
    assert response.status_code == 200


def test_json_endpoint_content_type(test_client):
    """Test JSON endpoint has correct content-type."""
    response = test_client.get("/api/live/status/snapshot.json")
    assert "application/json" in response.headers["content-type"]


def test_json_endpoint_parseable(test_client):
    """Test JSON endpoint returns parseable JSON."""
    response = test_client.get("/api/live/status/snapshot.json")
    data = response.json()

    assert isinstance(data, dict)


def test_json_endpoint_has_version(test_client):
    """Test JSON response has version field."""
    response = test_client.get("/api/live/status/snapshot.json")
    data = response.json()

    assert "version" in data
    assert data["version"] == "0.1"


def test_json_endpoint_has_generated_at(test_client):
    """Test JSON response has generated_at field."""
    response = test_client.get("/api/live/status/snapshot.json")
    data = response.json()

    assert "generated_at" in data
    assert isinstance(data["generated_at"], str)


def test_json_endpoint_has_panels_list(test_client):
    """Test JSON response has panels list."""
    response = test_client.get("/api/live/status/snapshot.json")
    data = response.json()

    assert "panels" in data
    assert isinstance(data["panels"], list)
    assert len(data["panels"]) >= 1  # At least default system panel


def test_json_endpoint_panel_structure(test_client):
    """Test JSON panels have correct structure."""
    response = test_client.get("/api/live/status/snapshot.json")
    data = response.json()

    panel = data["panels"][0]
    assert "id" in panel
    assert "title" in panel
    assert "status" in panel
    assert "details" in panel


def test_json_endpoint_cache_control(test_client):
    """Test JSON endpoint has Cache-Control: no-store header."""
    response = test_client.get("/api/live/status/snapshot.json")

    assert "cache-control" in response.headers
    assert response.headers["cache-control"] == "no-store"


# =============================================================================
# Tests: HTML Endpoint
# =============================================================================


def test_html_endpoint_returns_200(test_client):
    """Test HTML endpoint returns 200 OK."""
    response = test_client.get("/api/live/status/snapshot.html")
    assert response.status_code == 200


def test_html_endpoint_content_type(test_client):
    """Test HTML endpoint has correct content-type."""
    response = test_client.get("/api/live/status/snapshot.html")

    assert "text/html" in response.headers["content-type"]


def test_html_endpoint_contains_title(test_client):
    """Test HTML contains expected page title."""
    response = test_client.get("/api/live/status/snapshot.html")
    html = response.text

    assert "Peak_Trade Live Status Snapshot" in html
    assert "<title>" in html


def test_html_endpoint_contains_panel_titles(test_client):
    """Test HTML contains panel information."""
    response = test_client.get("/api/live/status/snapshot.html")
    html = response.text

    # Should have at least the default system panel
    assert "System Status" in html or "system" in html.lower()


def test_html_endpoint_has_css(test_client):
    """Test HTML includes CSS styling."""
    response = test_client.get("/api/live/status/snapshot.html")
    html = response.text

    assert "<style>" in html
    assert "status-ok" in html
    assert "status-error" in html


def test_html_endpoint_cache_control(test_client):
    """Test HTML endpoint has Cache-Control: no-store header."""
    response = test_client.get("/api/live/status/snapshot.html")

    assert "cache-control" in response.headers
    assert response.headers["cache-control"] == "no-store"


# =============================================================================
# Tests: XSS Safety
# =============================================================================


def test_html_xss_safety_script_tag():
    """Test that <script> tags in panel details are escaped (not executed)."""
    # Create custom app with malicious provider
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    from fastapi.testclient import TestClient
    from src.reporting.live_status_snapshot_builder import build_live_status_snapshot
    from src.reporting.html_reports import _html_escape

    # Build snapshot with XSS payload
    def xss_provider():
        return {
            "id": "xss_test",
            "title": "<script>alert('XSS')</script>",
            "status": "ok",
            "details": {
                "payload": "<script>alert('XSS in details')</script>",
                "onclick": "onclick='alert(1)'",
            }
        }

    snapshot = build_live_status_snapshot(panel_providers={"xss": xss_provider})

    # Render HTML (same logic as endpoint)
    html_lines = []
    html_lines.append("<html><body>")

    for panel in snapshot.panels:
        html_lines.append(f"<h2>{_html_escape(panel.title)}</h2>")
        if panel.details:
            details_json = json.dumps(panel.details, indent=2, sort_keys=True)
            html_lines.append(f"<pre>{_html_escape(details_json)}</pre>")

    html_lines.append("</body></html>")
    html_content = "\n".join(html_lines)

    # Check that script tags are escaped
    assert "<script>" not in html_content
    assert "&lt;script&gt;" in html_content
    assert "alert(" in html_content  # Text is still there, but escaped


def test_html_xss_safety_full_endpoint(test_client):
    """Test XSS safety in actual HTML endpoint."""
    # Make request (default providers shouldn't have XSS, but let's check escaping works)
    response = test_client.get("/api/live/status/snapshot.html")
    html = response.text

    # Raw script tags should never appear (even if somehow injected)
    # This is a safety check - if this fails, XSS escaping is broken
    assert "<script>alert" not in html
    assert "<img src=x onerror=" not in html
    assert "javascript:" not in html.lower()


# =============================================================================
# Tests: Graceful Degradation
# =============================================================================


def test_json_endpoint_with_failing_provider():
    """Test that JSON endpoint returns 200 even if a provider fails."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from src.reporting.live_status_snapshot_builder import build_live_status_snapshot

    # Create app with failing provider
    app = FastAPI()

    @app.get("/api/live/status/snapshot.json")
    def get_snapshot_json():
        def failing_provider():
            raise RuntimeError("Provider crashed!")

        snapshot = build_live_status_snapshot(panel_providers={"broken": failing_provider})

        from src.reporting.status_snapshot_schema import model_dump_helper
        from fastapi.responses import JSONResponse

        return JSONResponse(
            content=model_dump_helper(snapshot),
            headers={"Cache-Control": "no-store"},
        )

    client = TestClient(app)
    response = client.get("/api/live/status/snapshot.json")

    # Should still return 200
    assert response.status_code == 200

    data = response.json()
    assert len(data["panels"]) == 1

    # Panel should be error panel
    panel = data["panels"][0]
    assert panel["id"] == "broken"
    assert panel["status"] == "error"
    assert "RuntimeError" in panel["details"]["error"]


def test_html_endpoint_with_failing_provider():
    """Test that HTML endpoint returns 200 even if a provider fails."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from src.reporting.live_status_snapshot_builder import build_live_status_snapshot
    from src.reporting.html_reports import _html_escape
    from fastapi.responses import HTMLResponse

    # Create app with failing provider
    app = FastAPI()

    @app.get("/api/live/status/snapshot.html", response_class=HTMLResponse)
    def get_snapshot_html():
        def failing_provider():
            raise ValueError("Boom!")

        snapshot = build_live_status_snapshot(panel_providers={"crash": failing_provider})

        # Minimal HTML rendering
        html = f"<html><body><h1>Status</h1>"
        for panel in snapshot.panels:
            html += f"<div><h2>{_html_escape(panel.title)}</h2>"
            html += f"<p>Status: {_html_escape(panel.status)}</p>"
            html += f"</div>"
        html += "</body></html>"

        return HTMLResponse(content=html, headers={"Cache-Control": "no-store"})

    client = TestClient(app)
    response = client.get("/api/live/status/snapshot.html")

    # Should still return 200
    assert response.status_code == 200

    html = response.text
    assert "Status" in html
    # Error panel should be visible
    assert "error" in html.lower()


# =============================================================================
# Tests: Response Determinism
# =============================================================================


def test_json_endpoint_deterministic_panel_order(test_client):
    """Test that JSON panels are always in the same order (sorted by ID)."""
    # Make multiple requests
    response1 = test_client.get("/api/live/status/snapshot.json")
    response2 = test_client.get("/api/live/status/snapshot.json")

    data1 = response1.json()
    data2 = response2.json()

    # Panel order should be identical
    panel_ids_1 = [p["id"] for p in data1["panels"]]
    panel_ids_2 = [p["id"] for p in data2["panels"]]

    assert panel_ids_1 == panel_ids_2


def test_json_endpoint_details_keys_sorted(test_client):
    """Test that JSON panel details have sorted keys."""
    response = test_client.get("/api/live/status/snapshot.json")
    data = response.json()

    for panel in data["panels"]:
        if panel["details"]:
            keys = list(panel["details"].keys())
            assert keys == sorted(keys), f"Panel {panel['id']} details not sorted"


# =============================================================================
# Tests: Snapshot Structure Validation
# =============================================================================


def test_json_response_has_all_required_fields(test_client):
    """Test JSON response has all required top-level fields."""
    response = test_client.get("/api/live/status/snapshot.json")
    data = response.json()

    required_fields = ["version", "generated_at", "panels", "meta"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"


def test_json_panel_has_all_required_fields(test_client):
    """Test each panel has all required fields."""
    response = test_client.get("/api/live/status/snapshot.json")
    data = response.json()

    required_panel_fields = ["id", "title", "status", "details"]

    for panel in data["panels"]:
        for field in required_panel_fields:
            assert field in panel, f"Panel missing field: {field}"


def test_json_panel_status_values(test_client):
    """Test panel status values are valid."""
    response = test_client.get("/api/live/status/snapshot.json")
    data = response.json()

    valid_statuses = {"ok", "warn", "error", "unknown"}

    for panel in data["panels"]:
        assert panel["status"] in valid_statuses, f"Invalid status: {panel['status']}"
