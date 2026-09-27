"""Landscape V3 read-only routes (GET + WebSocket observation only)."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from src.webui.market_dashboard_landscape_v3.constants_v1 import (
    AUTHORITY,
    READ_ONLY,
    V3_HTML_ROUTE,
    V3_SNAPSHOT_API_ROUTE,
    V3_STREAM_WS_ROUTE,
)
from src.webui.market_dashboard_landscape_v3.stream_hub_v1 import get_landscape_v3_stream_hub_v1
from src.webui.market_dashboard_landscape_v3.upstream_public_md_v1 import (
    LandscapeV3UpstreamPublicMdServiceV1,
)

router = APIRouter(tags=["market-dashboard-landscape-v3", "read-only"])

_TEMPLATES: Jinja2Templates | None = None


def set_market_landscape_v3_shell_config(templates: Jinja2Templates) -> None:
    global _TEMPLATES
    _TEMPLATES = templates


def _templates() -> Jinja2Templates:
    if _TEMPLATES is None:
        raise RuntimeError("Landscape V3 shell not configured")
    return _TEMPLATES


def _ensure_hub(request: Request) -> Any:
    hub = get_landscape_v3_stream_hub_v1()
    try:
        hub.bind_loop(asyncio.get_running_loop())
    except RuntimeError:
        pass
    svc = getattr(request.app.state, "landscape_v3_upstream", None)
    if svc is None:
        svc = LandscapeV3UpstreamPublicMdServiceV1.from_env(hub)
        request.app.state.landscape_v3_upstream = svc
        svc.start_if_enabled()
    return hub


@router.get(V3_HTML_ROUTE, response_class=HTMLResponse, name="market_landscape_v3")
async def market_landscape_v3_page(request: Request) -> HTMLResponse:
    _ensure_hub(request)
    return _templates().TemplateResponse(
        request,
        "market_landscape_v3.html",
        {
            "authority": AUTHORITY,
            "read_only": READ_ONLY,
            "snapshot_path": V3_SNAPSHOT_API_ROUTE,
            "stream_path": V3_STREAM_WS_ROUTE,
        },
    )


@router.get(V3_SNAPSHOT_API_ROUTE, name="market_landscape_v3_snapshot")
async def market_landscape_v3_snapshot(request: Request) -> JSONResponse:
    hub = _ensure_hub(request)
    return JSONResponse(hub.get_snapshot())


@router.websocket(V3_STREAM_WS_ROUTE)
async def market_landscape_v3_stream(websocket: WebSocket) -> None:
    hub = get_landscape_v3_stream_hub_v1()
    try:
        hub.bind_loop(asyncio.get_running_loop())
    except RuntimeError:
        pass
    await hub.handle_client(websocket)


async def landscape_v3_app_startup(app: Any) -> None:
    hub = get_landscape_v3_stream_hub_v1()
    hub.bind_loop(asyncio.get_running_loop())
    svc = LandscapeV3UpstreamPublicMdServiceV1.from_env(hub)
    app.state.landscape_v3_upstream = svc
    svc.start_if_enabled()
