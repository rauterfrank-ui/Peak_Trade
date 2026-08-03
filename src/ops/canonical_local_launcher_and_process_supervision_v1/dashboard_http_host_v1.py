"""O2 dashboard-only FastAPI HTTP host (loopback, read-only, O5-bound).

Serves GET /market, GET /api/market/landscape/ohlcv, and GET /health from the
durable O5 derived read model. Additionally serves presentation-only
GET /landscape (text/html) plus static assets. Never fetches exchange candles
or mutates trading state. Authority effect remains NONE.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.connection_state_v1 import (
    assert_no_healthy_render_for_cached_bad_state_v1,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.constants_v1 import (
    CANONICAL_MARKET_ROUTE,
    CANONICAL_OHLCV_API,
    CONNECTION_DISCONNECTED,
    CONNECTION_MISSING_SOURCE,
    CONNECTION_STALE,
    DASHBOARD_TRANSPORT,
    NON_HEALTHY_RENDER_STATES,
    READ_MODEL_AUTHORITY_EFFECT,
    READ_MODEL_CLASSIFICATION,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.dashboard_lifecycle_v1 import (
    assert_dashboard_has_no_trading_authority_v1,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.durable_read_model_store_v1 import (
    load_durable_read_model_v1,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.read_model_v1 import (
    bind_dashboard_backend_to_read_model_v1,
    build_missing_source_read_model_v1,
)


LOOPBACK_HOSTS = frozenset({"127.0.0.1", "::1", "localhost"})

# Fixed non-authoritative SSR stamp — never wall-clock; never persists.
_LANDSCAPE_BOOTSTRAP_STAMP = datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def _repository_root_v1() -> Path:
    """Repo root from this module path (…/src/ops/<pkg>/<file>)."""
    return Path(__file__).resolve().parents[3]


def _load_or_missing(state_root: Path) -> dict[str, Any]:
    loaded = load_durable_read_model_v1(state_root)
    if loaded is None:
        return build_missing_source_read_model_v1(
            selection_bundle_id="o2-dashboard-http",
            projection_time_unix=time.time(),
            reason="DURABLE_READ_MODEL_ABSENT",
        )
    return loaded


def _stamp_http_observation(read_model: dict[str, Any]) -> dict[str, Any]:
    observed = time.time()
    out = dict(read_model)
    out["http_response_observed_time_unix"] = observed
    chain = {
        "market_event_time": out.get("market_event_time_unix", out.get("last_event_time_unix")),
        "ingestion_time": out.get("ingestion_time_unix"),
        "bar_projection_time": out.get(
            "bar_projection_time_unix", out.get("last_projection_time_unix")
        ),
        "read_model_commit_time": out.get("read_model_commit_time_unix"),
        "http_response_observed_time": observed,
    }
    # Fail closed: do not invent missing upstream timestamps.
    unsupported = [k for k, v in chain.items() if v is None and k != "http_response_observed_time"]
    out["timestamp_chain"] = {
        **chain,
        "unsupported_segments": unsupported,
        "full_chain_joined": len(unsupported) == 0,
        "notes": ["NO_TIMESTAMP_FABRICATION"],
    }
    return out


def render_supervised_landscape_html_v1(*, session_id: str) -> str:
    """Render presentation-only Landscape HTML with empty/non-authoritative bootstrap.

    Does not mutate JSON APIs, durable state, producers, or trading authority.
    Unavailable rails remain NOT_BOUND until the browser binds canonical JSON.
    """
    from src.webui.market_dashboard_landscape_v2 import (
        MarketDashboardReadServiceV1,
        present_market_landscape_v2,
    )

    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=_LANDSCAPE_BOOTSTRAP_STAMP
    )
    context = present_market_landscape_v2(page)
    # Presentation-only overlays — never authoritative, never persisted.
    # Use bare URL paths (constants include a "GET " prefix for contracts).
    context["supervised_presentation_only"] = True
    context["canonical_market_path"] = "/market"
    context["canonical_ohlcv_path"] = "/api/market/landscape/ohlcv"
    context["bootstrap_session_id"] = session_id
    context["bootstrap_repository_sha"] = ""
    context["non_authoritative_bootstrap"] = True

    repo = _repository_root_v1()
    env = Environment(
        loader=FileSystemLoader(str(repo / "templates" / "peak_trade_dashboard")),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("market_landscape_v2.html")
    return template.render(status={"project": "Peak_Trade"}, **context)


def create_o2_dashboard_http_app_v1(*, state_root: Path, session_id: str) -> FastAPI:
    """Build the supervised read-only FastAPI app bound to durable O5 state."""
    state_root = Path(state_root)
    app = FastAPI(
        title="Peak_Trade O2 Dashboard-Only HTTP Host",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.o2_state_root = state_root
    app.state.o2_session_id = session_id
    app.state.dashboard_authority_effect = READ_MODEL_AUTHORITY_EFFECT
    app.state.read_model_classification = READ_MODEL_CLASSIFICATION

    static_root = _repository_root_v1() / "static"
    if static_root.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_root)), name="static")

    @app.middleware("http")
    async def _loopback_only(request: Request, call_next):  # type: ignore[no-untyped-def]
        client_host = request.client.host if request.client else ""
        # Bind enforcement is primarily at uvicorn host=127.0.0.1; reject non-loopback clients.
        if client_host and client_host not in LOOPBACK_HOSTS:
            return JSONResponse(
                {"ok": False, "error": "LOOPBACK_ONLY", "client_host": client_host},
                status_code=403,
            )
        return await call_next(request)

    @app.get("/health")
    async def health() -> JSONResponse:
        rm = _stamp_http_observation(_load_or_missing(state_root))
        connection_state = str(rm.get("connection_state") or CONNECTION_MISSING_SOURCE)
        may_render_healthy = connection_state not in NON_HEALTHY_RENDER_STATES
        if not may_render_healthy:
            assert_no_healthy_render_for_cached_bad_state_v1(
                connection_state=connection_state, render_as_healthy=False
            )
        payload = {
            "ok": may_render_healthy,
            "status": "healthy" if may_render_healthy else "unhealthy",
            "connection_state": connection_state,
            "session_id": session_id,
            "dashboard_authority_effect": READ_MODEL_AUTHORITY_EFFECT,
            "trading_authority": False,
            "transport": DASHBOARD_TRANSPORT,
            "timestamp_chain": rm.get("timestamp_chain"),
        }
        code = 200 if may_render_healthy else 503
        return JSONResponse(payload, status_code=code)

    @app.get("/market")
    async def market() -> JSONResponse:
        rm = _stamp_http_observation(_load_or_missing(state_root))
        assert_dashboard_has_no_trading_authority_v1(
            {
                "trading_authority": False,
                "overall_connection_state": rm.get("connection_state"),
            }
        )
        bind = bind_dashboard_backend_to_read_model_v1(rm)
        connection_state = str(rm.get("connection_state") or CONNECTION_MISSING_SOURCE)
        if connection_state in NON_HEALTHY_RENDER_STATES:
            assert_no_healthy_render_for_cached_bad_state_v1(
                connection_state=connection_state, render_as_healthy=False
            )
        return JSONResponse(
            {
                "schema_name": "o2_dashboard_market_json_v1",
                "route": CANONICAL_MARKET_ROUTE,
                "session_id": session_id,
                "connection_state": connection_state,
                "may_render_healthy": connection_state not in NON_HEALTHY_RENDER_STATES,
                "read_model": rm,
                "backend_binding": bind,
                "trading_authority": False,
                "orders": False,
                "write_methods": [],
            }
        )

    @app.get("/api/market/landscape/ohlcv")
    async def ohlcv() -> JSONResponse:
        rm = _stamp_http_observation(_load_or_missing(state_root))
        connection_state = str(rm.get("connection_state") or CONNECTION_MISSING_SOURCE)
        if connection_state in {
            CONNECTION_STALE,
            CONNECTION_DISCONNECTED,
            CONNECTION_MISSING_SOURCE,
        }:
            assert_no_healthy_render_for_cached_bad_state_v1(
                connection_state=connection_state, render_as_healthy=False
            )
        ohlcv_proj = rm.get("ohlcv_projection") or {
            "bars": rm.get("bars") or [],
            "bar_count": rm.get("bar_count") or 0,
            "interval": rm.get("interval"),
            "instrument_id": rm.get("instrument_id"),
            "venue": rm.get("venue"),
        }
        return JSONResponse(
            {
                "schema_name": "market_landscape_ohlcv_poll_response.v1",
                "schema_version": 1,
                "poll_path": CANONICAL_OHLCV_API,
                "status": connection_state,
                "availability": connection_state,
                "connection_state": connection_state,
                "may_render_healthy": connection_state not in NON_HEALTHY_RENDER_STATES,
                "session_id": session_id,
                "source_session_id": rm.get("source_session_id"),
                "repository_sha": rm.get("repository_sha"),
                "config_digest": rm.get("config_digest"),
                "ohlcv": ohlcv_proj,
                "read_model": rm,
                "timestamp_chain": rm.get("timestamp_chain"),
                "trading_authority": False,
                "independent_authoritative_recompute": False,
                "parallel_ohlcv_producer": False,
            }
        )

    @app.get("/landscape", response_class=HTMLResponse)
    async def landscape() -> HTMLResponse:
        """Owner graphical Market Landscape — presentation only, authority NONE."""
        html = render_supervised_landscape_html_v1(session_id=session_id)
        return HTMLResponse(
            content=html,
            media_type="text/html",
            headers={
                "Cache-Control": "no-store",
                "X-Peak-Trade-Dashboard-Authority": "NONE",
                "X-Peak-Trade-Trading-Authority": "false",
            },
        )

    return app


def run_uvicorn_loopback_v1(
    *,
    app: FastAPI,
    host: str,
    port: int,
) -> Any:
    """Start uvicorn bound to loopback only. Raises if host is not loopback."""
    if host not in LOOPBACK_HOSTS:
        raise ValueError(f"LOOPBACK_BIND_REQUIRED:{host}")
    import uvicorn

    config = uvicorn.Config(
        app,
        host=host,
        port=int(port),
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    return server
