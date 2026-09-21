"""Regression: canonical Landscape HTML host vs O2 supervised host poll contracts."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from fastapi.testclient import TestClient

from src.ops.canonical_local_launcher_and_process_supervision_v1.dashboard_http_host_v1 import (
    create_o2_dashboard_http_app_v1,
)
from src.webui.app import create_app
from src.webui.market_dashboard_landscape_host_contract_v1 import (
    DASHBOARD_HOST_MODE_CANONICAL_LANDSCAPE_HTML,
    DASHBOARD_HOST_MODE_O2_SUPERVISED,
    HEADER_DASHBOARD_HOST_MODE,
    HEADER_OHLCV_SOURCE_CLASS,
    OHLCV_SOURCE_CLASS_ARCHIVE_OKX_READMODEL,
    OHLCV_SOURCE_CLASS_O5_DURABLE,
)
from src.webui.market_dashboard_landscape_shell_router_v2 import build_ohlcv_poll_response_v1


async def _asgi_get(app: Any, path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 50000))
    async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1") as client:
        return await client.get(path)


def _get(app: Any, path: str) -> httpx.Response:
    return asyncio.run(_asgi_get(app, path))


def test_canonical_webui_poll_declares_archive_host_contract() -> None:
    client = TestClient(create_app())
    response = client.get("/api/market/landscape/ohlcv")
    assert response.status_code == 200
    body = response.json()
    assert body["dashboard_host_mode"] == DASHBOARD_HOST_MODE_CANONICAL_LANDSCAPE_HTML
    assert body["ohlcv_source_class"] == OHLCV_SOURCE_CLASS_ARCHIVE_OKX_READMODEL
    assert body["is_canonical_landscape_html_host_poll"] is True
    assert body["is_o2_supervised_host_poll"] is False
    assert (
        response.headers.get(HEADER_DASHBOARD_HOST_MODE)
        == DASHBOARD_HOST_MODE_CANONICAL_LANDSCAPE_HTML
    )
    assert (
        response.headers.get(HEADER_OHLCV_SOURCE_CLASS) == OHLCV_SOURCE_CLASS_ARCHIVE_OKX_READMODEL
    )


def test_canonical_webui_market_html_carries_host_contract_attributes() -> None:
    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    html = response.text
    assert f'data-dashboard-host-mode="{DASHBOARD_HOST_MODE_CANONICAL_LANDSCAPE_HTML}"' in html
    assert f'data-ohlcv-source-class="{OHLCV_SOURCE_CLASS_ARCHIVE_OKX_READMODEL}"' in html
    assert (
        response.headers.get(HEADER_DASHBOARD_HOST_MODE)
        == DASHBOARD_HOST_MODE_CANONICAL_LANDSCAPE_HTML
    )


def test_build_ohlcv_poll_response_v1_includes_canonical_contract() -> None:
    payload = build_ohlcv_poll_response_v1(force_refresh=False)
    assert payload["dashboard_host_mode"] == DASHBOARD_HOST_MODE_CANONICAL_LANDSCAPE_HTML
    assert payload["ohlcv_source_class"] == OHLCV_SOURCE_CLASS_ARCHIVE_OKX_READMODEL


def test_o2_poll_declares_o5_supervised_contract(tmp_path: Any) -> None:
    app = create_o2_dashboard_http_app_v1(
        state_root=tmp_path / "o2_state",
        session_id="contract-isolation",
    )
    response = _get(app, "/api/market/landscape/ohlcv")
    assert response.status_code == 200
    body = response.json()
    assert body["dashboard_host_mode"] == DASHBOARD_HOST_MODE_O2_SUPERVISED
    assert body["ohlcv_source_class"] == OHLCV_SOURCE_CLASS_O5_DURABLE
    assert body["is_o2_supervised_host_poll"] is True
    assert body["is_canonical_landscape_html_host_poll"] is False
    assert response.headers.get(HEADER_DASHBOARD_HOST_MODE) == DASHBOARD_HOST_MODE_O2_SUPERVISED


def test_o2_landscape_html_declares_supervised_contract(tmp_path: Any) -> None:
    app = create_o2_dashboard_http_app_v1(
        state_root=tmp_path / "o2_state_html",
        session_id="contract-html",
    )
    response = _get(app, "/landscape")
    assert response.status_code == 200
    html = response.text
    assert f'data-dashboard-host-mode="{DASHBOARD_HOST_MODE_O2_SUPERVISED}"' in html
    assert f'data-ohlcv-source-class="{OHLCV_SOURCE_CLASS_O5_DURABLE}"' in html
    assert 'data-supervised-presentation-only="true"' in html


def test_host_contract_modes_are_distinct() -> None:
    assert DASHBOARD_HOST_MODE_CANONICAL_LANDSCAPE_HTML != DASHBOARD_HOST_MODE_O2_SUPERVISED
    assert OHLCV_SOURCE_CLASS_ARCHIVE_OKX_READMODEL != OHLCV_SOURCE_CLASS_O5_DURABLE
