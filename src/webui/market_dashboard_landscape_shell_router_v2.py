"""GET /market Landscape Shell router (Phase 4.3B canonical Double Play binding).

Read-only SSR surface. No POST/PUT/PATCH/DELETE. No command endpoints.
No execution / order / runtime-activation imports.
Phase 4.1 binds market_instrument / universe_ranking fail-closed from the
canonical Workflow Dashboard archive root (explicit → Env → platform default)
via universe_selection_readmodel.v1 — no Env required when the default exists.
Phase 4.2 binds dynamic_scope lifecycle identity fail-closed (injection only).
Phase 4.3A binds canonical_decision fail-closed (injection only).
Phase 4.3B binds double_play display fail-closed (injection only).
OHLCV binds from materialized okx_selected_instrument_ohlcv_readmodel.v1 only.
Continuous refresh: GET /api/market/landscape/ohlcv rate-limits rematerialization
via the OKX OHLCV readmodel owner; browser polls read-only JSON only.
Regime / bull-bear / switch stay unbound.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .market_dashboard_landscape_producer_binding_v2 import (
    bind_market_universe_slots,
    load_bound_okx_ohlcv_readmodel_v1,
    resolve_landscape_archive_root,
)
from .market_dashboard_landscape_v2.availability import Availability
from .market_dashboard_landscape_v2.page_aggregate import MarketDashboardReadServiceV1
from .market_dashboard_landscape_v2.presenter import (
    OHLCV_POLL_PATH,
    _ohlcv_data_connection_state,
    present_market_landscape_v2,
    serialize_ohlcv_browser_payload_v1,
)

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


def _chart_availability_for_ohlcv(ohlcv: dict[str, Any] | None) -> Availability:
    if ohlcv is None:
        return Availability.MISSING_SOURCE
    freshness = str(ohlcv.get("freshness_state") or "").lower()
    if freshness == "stale" or bool(ohlcv.get("is_stale")):
        return Availability.STALE
    return Availability.AVAILABLE


def build_ohlcv_poll_response_v1(
    *,
    force_refresh: bool = False,
    client: Any | None = None,
) -> dict[str, Any]:
    """Compose read-only OHLCV poll JSON; optional rate-limited rematerialization."""
    from src.ops.okx_selected_instrument_ohlcv_readmodel_v1 import (
        DEFAULT_DASHBOARD_OHLCV_POLL_INTERVAL_SECONDS,
        OkxOhlcvReadmodelError,
        refresh_selected_okx_ohlcv_readmodel_from_archive_v1,
    )

    generated_at = datetime.now(timezone.utc)
    phase_slots = bind_market_universe_slots(generated_at=generated_at, git_sha=None)
    page = _READ_SERVICE.load_page_snapshot(
        generated_at=generated_at,
        git_sha=None,
        slot_overrides=phase_slots,
    )
    selected = page.market_instrument.instrument_id or page.universe_ranking.selected_instrument_id
    selected_venue = page.market_instrument.venue
    archive_root = resolve_landscape_archive_root()
    refresh_meta: dict[str, Any] = {
        "status": "NO_ARCHIVE",
        "refresh_attempted": False,
        "refresh_error": None,
    }
    if archive_root is None:
        return {
            "schema_name": "market_landscape_ohlcv_poll_response.v1",
            "schema_version": 1,
            "status": "MISSING_SOURCE",
            "availability": Availability.MISSING_SOURCE.value,
            "poll_path": OHLCV_POLL_PATH,
            "poll_interval_seconds": DEFAULT_DASHBOARD_OHLCV_POLL_INTERVAL_SECONDS,
            "selected_instrument_id": selected,
            "venue": selected_venue,
            "refresh": refresh_meta,
            "browser_payload": None,
            "write_methods": [],
            "orders": False,
            "runtime_activation": False,
            "direct_browser_okx": False,
        }

    try:
        refresh_meta = refresh_selected_okx_ohlcv_readmodel_from_archive_v1(
            archive_root=archive_root,
            client=client,
            force=force_refresh,
            min_interval_seconds=0
            if force_refresh
            else DEFAULT_DASHBOARD_OHLCV_POLL_INTERVAL_SECONDS,
        )
    except OkxOhlcvReadmodelError as exc:
        refresh_meta = {
            "status": "REFRESH_FAILED",
            "refresh_attempted": True,
            "refresh_error": str(exc),
            "fabricated": False,
        }

    # Prefer page-bound identity; fall back to refresh/resolution identity so a
    # transient universe MANIFEST drift cannot unbind an authentic OHLCV tip.
    selected = selected or refresh_meta.get("selected_instrument")
    selected_venue = selected_venue or refresh_meta.get("selected_venue")
    ohlcv = load_bound_okx_ohlcv_readmodel_v1(
        selected_instrument_id=selected,
        selected_venue=selected_venue,
    )
    if ohlcv is None and isinstance(refresh_meta.get("ohlcv"), dict):
        # Retained prior snapshot after failed refresh, when identity still matches.
        retained = refresh_meta["ohlcv"]
        retained_id = str(retained.get("instrument_id") or "")
        if retained_id and (selected is None or retained_id == str(selected)):
            ohlcv = retained
            selected = selected or retained_id
            if selected_venue is None:
                selected_venue = retained.get("venue")

    browser_payload = serialize_ohlcv_browser_payload_v1(ohlcv)
    availability = _chart_availability_for_ohlcv(ohlcv)
    status = str(refresh_meta.get("status") or "OK")
    if ohlcv is None and selected is None:
        status = "MISSING_SOURCE"
        availability = Availability.MISSING_SOURCE
    elif ohlcv is None:
        status = "MISSING_SOURCE"
        availability = Availability.MISSING_SOURCE
    elif str(refresh_meta.get("refresh_error") or "").startswith("INVALID:"):
        status = "INVALID"
        availability = Availability.INVALID
    elif status == "REFRESH_FAILED" and ohlcv is not None:
        # Honest failure: retain prior candles but do not claim a successful refresh.
        availability = (
            Availability.STALE if availability is Availability.AVAILABLE else availability
        )

    return {
        "schema_name": "market_landscape_ohlcv_poll_response.v1",
        "schema_version": 1,
        "status": status,
        "availability": availability.value,
        "poll_path": OHLCV_POLL_PATH,
        "poll_interval_seconds": DEFAULT_DASHBOARD_OHLCV_POLL_INTERVAL_SECONDS,
        "selected_instrument_id": selected
        or (None if ohlcv is None else ohlcv.get("instrument_id")),
        "venue": "OKX"
        if (selected_venue and str(selected_venue).lower().startswith("okx"))
        or (ohlcv and str(ohlcv.get("venue") or "").lower().startswith("okx"))
        else selected_venue,
        "interval": None if ohlcv is None else ohlcv.get("interval"),
        "captured_at": None if ohlcv is None else ohlcv.get("captured_at"),
        "effective_at": None if ohlcv is None else ohlcv.get("effective_at"),
        "last_timestamp": None if ohlcv is None else ohlcv.get("last_timestamp"),
        "last_closed_timestamp": None if ohlcv is None else ohlcv.get("last_closed_timestamp"),
        "freshness_state": None if ohlcv is None else ohlcv.get("freshness_state"),
        "is_stale": False if ohlcv is None else bool(ohlcv.get("is_stale")),
        "payload_digest": None
        if browser_payload is None
        else browser_payload.get("payload_digest"),
        "chart_digest": None if browser_payload is None else browser_payload.get("chart_digest"),
        "candle_series_digest": None
        if browser_payload is None
        else browser_payload.get("candle_series_digest"),
        "metadata_digest": None
        if browser_payload is None
        else browser_payload.get("metadata_digest"),
        "live_mark_price": None
        if browser_payload is None
        else browser_payload.get("live_mark_price"),
        "refresh": {
            "status": refresh_meta.get("status"),
            "refresh_attempted": bool(refresh_meta.get("refresh_attempted")),
            "refresh_error": refresh_meta.get("refresh_error"),
            "fabricated": bool(refresh_meta.get("fabricated", False)),
        },
        "browser_payload": browser_payload,
        "write_methods": [],
        "orders": False,
        "runtime_activation": False,
        "direct_browser_okx": False,
        "data_connection_state": (
            "STALE"
            if availability is Availability.STALE or status in {"REFRESH_FAILED", "INVALID"}
            else _ohlcv_data_connection_state(
                browser_payload=browser_payload,
                ohlcv_payload=ohlcv,
                chart_availability=availability,
            )
        ),
    }


@router.get("/market", response_class=HTMLResponse, name="market_landscape_v2")
async def market_landscape_dashboard(request: Request) -> Any:
    """Read-only Landscape surface with Phase 4.1+4.2+4.3A+4.3B producer binding."""
    # Lazy import avoids circular import during create_app().
    from .app import get_project_status

    generated_at = datetime.now(timezone.utc)
    # Observation clock only — never used as producer freshness inside binding.
    phase_slots = bind_market_universe_slots(generated_at=generated_at, git_sha=None)
    page = _READ_SERVICE.load_page_snapshot(
        generated_at=generated_at,
        git_sha=None,
        slot_overrides=phase_slots,
    )
    ohlcv = load_bound_okx_ohlcv_readmodel_v1(
        selected_instrument_id=page.market_instrument.instrument_id
        or page.universe_ranking.selected_instrument_id,
        selected_venue=page.market_instrument.venue,
    )
    context = present_market_landscape_v2(page, ohlcv_readmodel=ohlcv)
    if ohlcv is not None:
        eng = context.setdefault("engineering", {})
        eng["okx_ohlcv"] = {
            "schema_name": ohlcv.get("schema_name"),
            "selection_bundle_id": ohlcv.get("selection_bundle_id"),
            "raw_capture_digest": ohlcv.get("raw_capture_digest"),
            "captured_at": ohlcv.get("captured_at"),
            "effective_at": ohlcv.get("effective_at"),
            "freshness_state": ohlcv.get("freshness_state"),
            "interval": ohlcv.get("interval"),
            "bar_count": ohlcv.get("bar_count"),
            "gap_count": ohlcv.get("gap_count"),
        }
    return get_templates().TemplateResponse(
        request,
        "market_landscape_v2.html",
        {
            "request": request,
            "status": get_project_status(),
            **context,
        },
    )


@router.get("/api/market/landscape/ohlcv", name="market_landscape_ohlcv_poll_v1")
async def market_landscape_ohlcv_poll(
    force: bool = Query(default=False, description="Bypass min-interval skip (tests/ops)."),
) -> JSONResponse:
    """Read-only OHLCV snapshot poll; may rematerialize public OKX candles server-side."""
    payload = build_ohlcv_poll_response_v1(force_refresh=force)
    return JSONResponse(payload)
