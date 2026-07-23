"""GET /market Landscape Shell router (Phase 4.1 market/universe binding).

Read-only SSR surface. No POST/PUT/PATCH/DELETE. No command endpoints.
No execution / order / runtime-activation imports.
Phase 4.1 binds market_instrument / universe_ranking fail-closed.
Dynamic scope and later Phase 4 slots remain unbound.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .market_dashboard_landscape_producer_binding_v2 import bind_market_universe_slots
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
    """Read-only Landscape surface with Phase 4.1 market/universe binding."""
    # Lazy import avoids circular import during create_app().
    from .app import get_project_status

    generated_at = datetime.now(timezone.utc)
    phase41_slots = bind_market_universe_slots(generated_at=generated_at, git_sha=None)
    page = _READ_SERVICE.load_page_snapshot(
        generated_at=generated_at,
        git_sha=None,
        slot_overrides=phase41_slots,
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
