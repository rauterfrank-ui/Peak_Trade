"""
HTTP contract for GET /api/ops-cockpit: minimal stable JSON top-level shape.

Aligns with ``EXPECTED_OPS_COCKPIT_PAYLOAD_TOP_LEVEL_KEYS`` from the payload
contract test (same invariant as ``build_ops_cockpit_payload``, via HTTP).
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from tests.ops.test_ops_cockpit_payload_top_level_contract import (
    EXPECTED_OPS_COCKPIT_PAYLOAD_TOP_LEVEL_KEYS,
)


@pytest.fixture
def ops_client() -> TestClient:
    from src.webui.app import app

    return TestClient(app)


def test_api_ops_cockpit_json_contract_top_level_keys(ops_client: TestClient) -> None:
    """GET /api/ops-cockpit: 200, JSON object, stable top-level key set (no value assertions)."""
    response = ops_client.get("/api/ops-cockpit")
    assert response.status_code == 200
    assert "application/json" in (response.headers.get("content-type") or "")
    data = response.json()
    assert isinstance(data, dict)
    assert set(data.keys()) == EXPECTED_OPS_COCKPIT_PAYLOAD_TOP_LEVEL_KEYS
