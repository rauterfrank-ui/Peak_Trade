"""GET /market Landscape Shell router (Phase 3 / PR 2).

Read-only SSR surface. No POST/PUT/PATCH/DELETE. No command endpoints.
No execution / order / runtime-activation imports.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .market_dashboard_landscape_v2.page_aggregate import MarketDashboardReadServiceV1
from .market_dashboard_landscape_v2.presenter import present_market_landscape_v2

router = APIRouter(tags=["market-dashboard-landscape-v2", "read-only"])

_TEMPLATES: Jinja2Templates | None = None
_READ_SERVICE = MarketDashboardReadServiceV1()


def set_market_landscape_shell_config(templates: Jinja2Templates) -> None:
    global _TEMPLATES
    _TEMPLATES = templates


def get_templates() -> Jinja2Templates:
    if _TEMPLATES is None:
        raise RuntimeError(
            "Market landscape shell not configured. Call set_market_landscape_shell_config()."
        )
    return _TEMPLATES


@router.get("/market", response_class=HTMLResponse, name="market_landscape_v2")
async def market_landscape_dashboard(request: Request) -> Any:
    """Read-only Landscape product skeleton. Formatting only via presenter."""
    # Lazy import avoids circular import during create_app().
    from .app import get_project_status

    page = _READ_SERVICE.load_page_snapshot(
        generated_at=datetime.now(timezone.utc),
        git_sha=None,
    )
    context = present_market_landscape_v2(page)
    return get_templates().TemplateResponse(
        request,
        "market_landscape_v2.html",
        {
            "request": request,
            "status": get_project_status(),
            **context,
        },
    )
