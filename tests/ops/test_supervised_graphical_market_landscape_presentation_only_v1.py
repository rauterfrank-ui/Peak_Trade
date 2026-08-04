"""Contract tests: supervised graphical Market Landscape presentation-only v1.

Proves:
- Existing JSON routes (/health, /market, /api/market/landscape/ohlcv) stay
  semantically compatible (keys/flags unchanged).
- GET /landscape returns text/html with visible Landscape root.
- Static CSS/JS return HTTP 200.
- Canonical session_id / repository_sha / instrument / OHLCV mappings work.
- Legacy browser_payload is not required.
- No direct_browser_okx path exists in JS.
- Failures are visible.
"""

from __future__ import annotations

import asyncio
import json
import socket
import threading
import time
from pathlib import Path
from typing import Any

import httpx
import pytest

from src.ops.canonical_local_launcher_and_process_supervision_v1.dashboard_http_host_v1 import (
    create_o2_dashboard_http_app_v1,
    run_uvicorn_loopback_v1,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.constants_v1 import (
    CONNECTION_HEALTHY,
    READ_MODEL_SCHEMA_NAME,
)
from src.ops.canonical_read_model_and_market_dashboard_rebuild_v1.durable_read_model_store_v1 import (
    commit_durable_read_model_v1,
)

REPO = Path(__file__).resolve().parents[2]
HOST_SRC = (
    REPO / "src/ops/canonical_local_launcher_and_process_supervision_v1/dashboard_http_host_v1.py"
)
JS_SRC = REPO / "static/js/market_dashboard_landscape_v2.js"
TEMPLATE_SRC = REPO / "templates/peak_trade_dashboard/market_landscape_v2.html"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


async def _asgi_get(app: Any, path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=app, client=("127.0.0.1", 50000))
    async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1") as client:
        return await client.get(path)


def _get(app: Any, path: str) -> httpx.Response:
    return asyncio.run(_asgi_get(app, path))


def _healthy_read_model(*, session_id: str, repository_sha: str) -> dict[str, Any]:
    bars = [
        {
            "ts": "2026-08-01T00:00:00Z",
            "open": 100.0,
            "high": 101.0,
            "low": 99.5,
            "close": 100.5,
            "volume": 12.0,
            "confirm": True,
        },
        {
            "ts": "2026-08-01T01:00:00Z",
            "open": 100.5,
            "high": 102.0,
            "low": 100.0,
            "close": 101.25,
            "volume": 15.0,
            "confirm": True,
        },
    ]
    return {
        "schema_name": READ_MODEL_SCHEMA_NAME,
        "schema_version": 1,
        "authority_classification": "DERIVED",
        "read_model_classification": "DERIVED",
        "read_model_ssot": False,
        "read_model_authority_effect": "NONE",
        "authoritative_bar_producer": "o4",
        "dashboard_transport": "o2_dashboard_http",
        "selection_bundle_id": "supervised-landscape-fixture",
        "source_session_id": session_id,
        "repository_sha": repository_sha,
        "config_digest": "cfg-supervised-landscape",
        "instrument": "ETH-USDT-SWAP",
        "instrument_id": "ETH-USDT-SWAP",
        "interval": "PT1H",
        "venue": "okx",
        "last_event_time_unix": 1_700_000_100.0,
        "last_event_time": "2023-11-14T22:15:00Z",
        "last_projection_time_unix": 1_700_000_110.0,
        "last_projection_time": "2023-11-14T22:15:10Z",
        "freshness_age_seconds": 1.0,
        "connection_state": CONNECTION_HEALTHY,
        "is_stale": False,
        "bar_count": len(bars),
        "bars": bars,
        "ohlcv_projection": {
            "bars": bars,
            "bar_count": len(bars),
            "interval": "PT1H",
            "instrument_id": "ETH-USDT-SWAP",
            "venue": "okx",
        },
        "trading_authority": False,
        "orders": False,
        "runtime_mutation": False,
        "risk_authority": False,
        "write_methods": [],
        "may_render_healthy": True,
    }


@pytest.fixture()
def empty_app(tmp_path: Path) -> Any:
    return create_o2_dashboard_http_app_v1(
        state_root=tmp_path / "state_empty",
        session_id="sess-empty",
    )


@pytest.fixture()
def seeded_app(tmp_path: Path) -> Any:
    state_root = tmp_path / "state_seeded"
    commit_durable_read_model_v1(
        state_root,
        _healthy_read_model(
            session_id="sess-seeded",
            repository_sha="a" * 40,
        ),
    )
    return create_o2_dashboard_http_app_v1(
        state_root=state_root,
        session_id="sess-seeded",
    )


def test_existing_json_routes_semantic_keys_unchanged(empty_app: Any) -> None:
    health = _get(empty_app, "/health")
    market = _get(empty_app, "/market")
    ohlcv = _get(empty_app, "/api/market/landscape/ohlcv")

    assert health.status_code in {200, 503}
    assert market.status_code == 200
    assert ohlcv.status_code == 200

    health_body = health.json()
    market_body = market.json()
    ohlcv_body = ohlcv.json()

    for key in (
        "ok",
        "status",
        "connection_state",
        "session_id",
        "dashboard_authority_effect",
        "trading_authority",
        "transport",
        "timestamp_chain",
    ):
        assert key in health_body

    for key in (
        "schema_name",
        "route",
        "session_id",
        "connection_state",
        "may_render_healthy",
        "read_model",
        "backend_binding",
        "trading_authority",
        "orders",
        "write_methods",
    ):
        assert key in market_body

    for key in (
        "schema_name",
        "schema_version",
        "poll_path",
        "status",
        "availability",
        "connection_state",
        "may_render_healthy",
        "session_id",
        "ohlcv",
        "read_model",
        "trading_authority",
        "independent_authoritative_recompute",
        "parallel_ohlcv_producer",
    ):
        assert key in ohlcv_body

    assert market_body["schema_name"] == "o2_dashboard_market_json_v1"
    assert market_body["trading_authority"] is False
    assert market_body["orders"] is False
    assert market_body["write_methods"] == []
    assert "browser_payload" not in market_body
    assert ohlcv_body["schema_name"] == "market_landscape_ohlcv_poll_response.v1"
    assert ohlcv_body["parallel_ohlcv_producer"] is False
    assert ohlcv_body["independent_authoritative_recompute"] is False
    assert "browser_payload" not in ohlcv_body
    assert health_body["trading_authority"] is False


def test_json_content_type_unchanged(empty_app: Any) -> None:
    for path in ("/health", "/market", "/api/market/landscape/ohlcv"):
        response = _get(empty_app, path)
        assert "application/json" in response.headers.get("content-type", "")


def test_landscape_route_returns_text_html(empty_app: Any) -> None:
    response = _get(empty_app, "/landscape")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    html = response.text
    assert 'data-market-landscape-v2="true"' in html
    assert 'data-supervised-presentation-only="true"' in html
    assert 'data-canonical-market-path="/market"' in html
    assert 'data-canonical-ohlcv-path="/api/market/landscape/ohlcv"' in html
    assert 'data-mdl-ohlcv-poll-path="/api/market/landscape/ohlcv"' in html
    assert "NOT_BOUND" in html
    assert 'data-orders="false"' in html
    assert 'data-live-authorized="false"' in html
    assert "market_dashboard_landscape_v2.css" in html
    assert "market_dashboard_landscape_v2.js" in html


def test_static_css_js_return_200(empty_app: Any) -> None:
    css = _get(empty_app, "/static/css/market_dashboard_landscape_v2.css")
    js = _get(empty_app, "/static/js/market_dashboard_landscape_v2.js")
    assert css.status_code == 200
    assert js.status_code == 200
    assert len(css.content) > 100
    assert len(js.content) > 100


def test_canonical_session_instrument_ohlcv_mappings(seeded_app: Any) -> None:
    market = _get(seeded_app, "/market").json()
    ohlcv = _get(seeded_app, "/api/market/landscape/ohlcv").json()
    html = _get(seeded_app, "/landscape").text

    assert market["session_id"] == "sess-seeded"
    assert market["read_model"]["repository_sha"] == "a" * 40
    assert market["read_model"]["instrument_id"] == "ETH-USDT-SWAP"
    assert ohlcv["session_id"] == "sess-seeded"
    assert ohlcv["repository_sha"] == "a" * 40
    assert ohlcv["ohlcv"]["bars"]
    assert "browser_payload" not in ohlcv
    assert 'data-session-id="sess-seeded"' in html
    assert market["read_model"]["bars"][0]["ts"] == ohlcv["ohlcv"]["bars"][0]["ts"]


def test_js_accepts_canonical_without_browser_payload() -> None:
    js = JS_SRC.read_text(encoding="utf-8")
    assert "extractCanonicalOhlcvPayload" in js
    assert "body.ohlcv" in js or "picked.kind" in js
    assert "browser_payload" in js  # legacy still accepted
    assert "never substitute candle close" in js.lower() or "Never substitute" in js
    assert "direct_browser_okx" in js
    assert "poll_forbidden_direct_okx" in js
    assert "okx.com" not in js.lower()
    assert 'fetch("https://' not in js
    assert "CANONICAL_DATA_UNAVAILABLE" in js
    assert "bootstrapFromCanonicalMarket" in js
    assert 'marketPath !== "/market"' in js
    assert "isCanonicalHtmlShellHostDocument" in js
    assert "ssr_html_shell" in js


def test_js_connection_state_poll_arm_fail_closed_presentation_contract() -> None:
    """Presentation-only: poll arm / payload must not invent HEALTHY."""
    js = JS_SRC.read_text(encoding="utf-8")
    assert "readExistingConnectionState" in js
    assert "resolveConnectionStateForPollPayload" in js
    assert 'readExistingConnectionState() || "MISSING_SOURCE"' in js
    assert "resolveConnectionStateForPollPayload(body)" in js
    # Honest presentation: arming must not promote arbitrary availability to HEALTHY.
    arm_idx = js.index('data-mdl-ohlcv-poll-armed", "true"')
    arm_block = js[arm_idx : arm_idx + 450]
    assert 'setConnectionState(readExistingConnectionState() || "MISSING_SOURCE")' in arm_block
    assert ': "HEALTHY"' not in arm_block
    assert "DEGRADED" in js
    assert "DISCONNECTED" in js
    assert "MISSING_SOURCE" in js
    assert "HEALTHY" in js  # explicit canonical HEALTHY still in vocabulary


def test_template_and_host_forbid_legacy_hot_path_wiring() -> None:
    host = HOST_SRC.read_text(encoding="utf-8")
    template = TEMPLATE_SRC.read_text(encoding="utf-8")
    assert "market_dashboard_landscape_shell_router_v2" not in host
    assert "market_dashboard_landscape_producer_binding_v2" not in host
    assert "run_web_dashboard" not in host
    assert "refresh_selected_okx" not in host
    assert 'data-market-landscape-v2="true"' in template
    assert "non_authoritative_bootstrap" in template


def test_fail_visible_when_canonical_absent(empty_app: Any) -> None:
    market = _get(empty_app, "/market").json()
    assert market["connection_state"] == "MISSING_SOURCE"
    html = _get(empty_app, "/landscape").text
    # Empty bootstrap — JS fail-visible path depends on runtime; HTML itself
    # must not pretend healthy OHLCV series are bound.
    assert "non_authoritative_bootstrap" in html
    assert 'data-mdl-chart-has-series="false"' in html or "NOT_BOUND" in html


def test_no_second_host_or_forbidden_imports_in_host() -> None:
    host = HOST_SRC.read_text(encoding="utf-8")
    assert "create_app()" not in host
    assert "uvicorn.workers" not in host
    assert "exchange_credentials" not in host
    assert "submit_order" not in host
    assert "place_order" not in host


def test_uvicorn_loopback_serves_landscape_and_json(tmp_path: Path) -> None:
    state_root = tmp_path / "uv_state"
    commit_durable_read_model_v1(
        state_root,
        _healthy_read_model(session_id="uv-sess", repository_sha="b" * 40),
    )
    app = create_o2_dashboard_http_app_v1(state_root=state_root, session_id="uv-sess")
    port = _free_port()
    server = run_uvicorn_loopback_v1(app=app, host="127.0.0.1", port=port)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    try:
        deadline = time.time() + 5.0
        last_err: Exception | None = None
        while time.time() < deadline:
            try:
                with httpx.Client(base_url=base, timeout=1.0) as client:
                    landscape = client.get("/landscape")
                    market = client.get("/market")
                    css = client.get("/static/css/market_dashboard_landscape_v2.css")
                    js = client.get("/static/js/market_dashboard_landscape_v2.js")
                assert landscape.status_code == 200
                assert "text/html" in landscape.headers.get("content-type", "")
                assert 'data-market-landscape-v2="true"' in landscape.text
                assert market.status_code == 200
                assert market.json()["session_id"] == "uv-sess"
                assert css.status_code == 200
                assert js.status_code == 200
                return
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                time.sleep(0.05)
        raise AssertionError(f"uvicorn landscape serve failed: {last_err}")
    finally:
        server.should_exit = True
