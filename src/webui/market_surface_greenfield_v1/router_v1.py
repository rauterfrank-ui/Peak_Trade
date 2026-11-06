"""Read-only routes for greenfield operator trading surface v1."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .canonical_state_v1 import build_canonical_surface_state_v1
from .contracts_v1 import STATE_API_PATH, SURFACE_HTML_ROUTE

router = APIRouter(tags=["market-surface-greenfield-v1", "read-only"])

_TEMPLATES: Jinja2Templates | None = None


def set_market_surface_greenfield_templates(templates: Jinja2Templates) -> None:
    global _TEMPLATES
    _TEMPLATES = templates


def _templates() -> Jinja2Templates:
    if _TEMPLATES is None:
        raise RuntimeError("market_surface_greenfield_v1 templates not configured")
    return _TEMPLATES


@router.get(SURFACE_HTML_ROUTE, response_class=HTMLResponse, name="operator_trading_surface_v1")
async def operator_trading_surface_page(request: Request) -> Any:
    return _templates().TemplateResponse(
        request,
        "market_surface_greenfield_v1.html",
        {
            "request": request,
            "state_api_path": STATE_API_PATH,
            "read_only": True,
        },
    )


@router.get(STATE_API_PATH, name="operator_trading_surface_state_v1")
async def operator_trading_surface_state(
    force_refresh: bool = Query(default=False, alias="force_refresh"),
) -> JSONResponse:
    body = await build_canonical_surface_state_v1(force_refresh=force_refresh)
    headers = {
        "Cache-Control": "no-store",
        "X-Peak-Trade-Surface": "market_surface_greenfield_v1",
        "X-Peak-Trade-Read-Only": "1",
    }
    return JSONResponse(content=body, headers=headers)
