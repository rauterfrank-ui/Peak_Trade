"""Offline TestClient contract for Chart.js vendor static route (no browser, no network)."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

from src.webui.app import create_app

VENDOR_FALLBACK_PATH = "/static/vendor/chartjs/4.4.1/chart.umd.min.js"
PINNED_SHA256 = "d2af8974e95271638772e9e9524db5b9a6f58d6ec2d5d781400447b4a31c681e"
PINNED_SIZE_BYTES = 205399


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def test_chartjs_vendor_static_route_returns_200_v0(client: TestClient) -> None:
    response = client.get(VENDOR_FALLBACK_PATH)
    assert response.status_code == 200


def test_chartjs_vendor_static_route_content_type_v0(client: TestClient) -> None:
    response = client.get(VENDOR_FALLBACK_PATH)
    content_type = response.headers.get("content-type", "")
    assert "javascript" in content_type


def test_chartjs_vendor_static_route_body_non_empty_and_chart_marker_v0(
    client: TestClient,
) -> None:
    response = client.get(VENDOR_FALLBACK_PATH)
    body = response.content
    assert len(body) > 0
    text = body.decode("utf-8", errors="replace")
    assert "Chart" in text


def test_chartjs_vendor_static_route_sha256_matches_pinned_v0(client: TestClient) -> None:
    response = client.get(VENDOR_FALLBACK_PATH)
    digest = hashlib.sha256(response.content).hexdigest()
    assert digest == PINNED_SHA256


def test_chartjs_vendor_static_route_size_matches_pinned_v0(client: TestClient) -> None:
    response = client.get(VENDOR_FALLBACK_PATH)
    assert len(response.content) == PINNED_SIZE_BYTES


def test_static_route_missing_asset_returns_404_v0(client: TestClient) -> None:
    response = client.get("/static/does-not-exist.js")
    assert response.status_code == 404
