"""
Contract tests for static registration metadata of the R&D APIRouter (v0).

No TestClient, no route execution, no batch/comparison/response assertions.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from src.webui.r_and_d_api import router


def test_r_and_d_api_router_registration_contract_v0() -> None:
    assert router.prefix == "/api/r_and_d"
    assert router.tags == ["r_and_d"]
