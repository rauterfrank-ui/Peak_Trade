"""
Contract tests for FastAPI/OpenAPI identity metadata returned by create_app() (v0).

Covers stable public strings only; no routes, authority flags, live wiring checks,
or full OpenAPI/schema dumps.
"""

from __future__ import annotations

from src.webui.app import create_app


def test_create_app_openapi_metadata_contract_v0() -> None:
    app = create_app()
    assert app.title == "Peak_Trade Dashboard v1.2"
    assert app.version == "1.2.0"
    desc = app.description or ""
    assert desc.startswith("Read-only Dashboard")
    assert "Phase 76" in desc
