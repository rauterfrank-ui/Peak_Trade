"""
Contract tests for static registration metadata of the Health APIRouter (v0).

No TestClient, no route execution, no response/timestamp assertions.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from src.webui.health_endpoint import router


def test_health_router_registration_contract_v0() -> None:
    assert router.prefix == "/health"
    assert router.tags == ["health"]
