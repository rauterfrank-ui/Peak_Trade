"""Playwright owner-route acceptance for supervised Market Landscape presentation.

Bounded browser proof against the supervised O2 host (not run_web_dashboard):
- Owner URL is text/html
- CSS and JS load 200
- Root is visible
- session_id and repository_sha match canonical JSON APIs
- Selected future and OHLCV originate exclusively from canonical routes
- Browser console errors are zero
- No credentials/private/execution/order adapter is reachable
- Orders remain zero
- Only one supervised lane exists (this host)
"""

from __future__ import annotations

import socket
import threading
import time
from pathlib import Path
from typing import Any

import httpx
import pytest

pytest.importorskip("playwright")
pytest.importorskip("fastapi")

from playwright.sync_api import sync_playwright

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
JS_SRC = REPO / "static/js/market_dashboard_landscape_v2.js"
HOST_SRC = (
    REPO / "src/ops/canonical_local_launcher_and_process_supervision_v1/dashboard_http_host_v1.py"
)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _healthy_read_model(*, session_id: str, repository_sha: str) -> dict[str, Any]:
    bars = [
        {
            "ts": "2026-08-02T10:00:00Z",
            "open": 2100.0,
            "high": 2110.0,
            "low": 2095.0,
            "close": 2105.0,
            "volume": 42.0,
            "confirm": True,
        },
        {
            "ts": "2026-08-02T11:00:00Z",
            "open": 2105.0,
            "high": 2120.0,
            "low": 2100.0,
            "close": 2115.5,
            "volume": 51.0,
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
        "selection_bundle_id": "playwright-landscape",
        "source_session_id": session_id,
        "repository_sha": repository_sha,
        "config_digest": "cfg-playwright",
        "instrument": "ETH-USDT-SWAP",
        "instrument_id": "ETH-USDT-SWAP",
        "interval": "PT1H",
        "venue": "okx",
        "last_event_time_unix": 1_700_000_200.0,
        "last_event_time": "2023-11-14T22:16:40Z",
        "last_projection_time_unix": 1_700_000_210.0,
        "last_projection_time": "2023-11-14T22:16:50Z",
        "freshness_age_seconds": 0.5,
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
def supervised_landscape_base_url(tmp_path: Path) -> str:
    state_root = tmp_path / "pw_state"
    session_id = "pw-sess-landscape"
    repository_sha = "c" * 40
    commit_durable_read_model_v1(
        state_root,
        _healthy_read_model(session_id=session_id, repository_sha=repository_sha),
    )
    app = create_o2_dashboard_http_app_v1(state_root=state_root, session_id=session_id)
    port = _free_port()
    server = run_uvicorn_loopback_v1(app=app, host="127.0.0.1", port=port)
    thread = threading.Thread(target=server.run, name="pw-landscape-host", daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    deadline = time.time() + 5.0
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            with httpx.Client(base_url=base, timeout=1.0) as client:
                assert client.get("/landscape").status_code == 200
            break
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(0.05)
    else:
        server.should_exit = True
        raise AssertionError(f"supervised host failed to start: {last_err}")
    try:
        yield base
    finally:
        server.should_exit = True


def test_playwright_owner_route_supervised_landscape_acceptance(
    supervised_landscape_base_url: str,
) -> None:
    base = supervised_landscape_base_url
    with httpx.Client(base_url=base, timeout=2.0) as client:
        market = client.get("/market")
        ohlcv = client.get("/api/market/landscape/ohlcv")
        landscape_head = client.get("/landscape")
        css = client.get("/static/css/market_dashboard_landscape_v2.css")
        js = client.get("/static/js/market_dashboard_landscape_v2.js")
        # Negative reachability: no credential / order / execution adapters on this host.
        for forbidden in (
            "/api/orders",
            "/execution",
            "/credentials",
            "/private",
            "/api/exchange/order",
        ):
            assert client.get(forbidden).status_code in {404, 405, 403}

    assert landscape_head.status_code == 200
    assert "text/html" in landscape_head.headers.get("content-type", "")
    assert css.status_code == 200
    assert js.status_code == 200
    market_body = market.json()
    ohlcv_body = ohlcv.json()
    assert market_body["orders"] is False
    assert market_body["trading_authority"] is False
    assert ohlcv_body["trading_authority"] is False
    assert "browser_payload" not in ohlcv_body

    # Static proof: exactly one supervised host module (no second host created).
    host_text = HOST_SRC.read_text(encoding="utf-8")
    assert host_text.count("def create_o2_dashboard_http_app_v1") == 1
    assert "create_app()" not in host_text
    js_text = JS_SRC.read_text(encoding="utf-8")
    assert "direct_browser_okx" in js_text
    assert "okx.com" not in js_text.lower()

    console_errors: list[str] = []
    page_errors: list[str] = []
    requested_urls: list[str] = []

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except Exception:
            browser = playwright.firefox.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.on(
            "console",
            lambda msg: (
                console_errors.append(f"{msg.type}:{msg.text}") if msg.type == "error" else None
            ),
        )
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on("request", lambda req: requested_urls.append(req.url))

        page.goto(f"{base}/landscape", wait_until="networkidle")
        root = page.locator('[data-market-landscape-v2="true"]')
        assert root.count() == 1
        assert root.is_visible()
        assert page.locator("h1.mdl-v2-kicker").count() == 1

        # Wait for canonical market bootstrap binding.
        page.wait_for_function(
            """() => {
              const root = document.querySelector('[data-market-landscape-v2="true"]');
              return root && root.getAttribute('data-mdl-canonical-market-bound') === 'true';
            }""",
            timeout=5000,
        )

        session_id = root.get_attribute("data-session-id")
        repository_sha = root.get_attribute("data-repository-sha")
        assert session_id == market_body["session_id"]
        assert repository_sha == market_body["read_model"]["repository_sha"]
        assert session_id == ohlcv_body["session_id"]
        assert repository_sha == ohlcv_body["repository_sha"]

        instrument_text = page.locator('[data-mdl-field="instrument"]').inner_text()
        selected_text = page.locator('[data-mdl-field="selected_instrument"]').inner_text()
        expected_instrument = market_body["read_model"]["instrument_id"]
        assert expected_instrument in instrument_text
        assert expected_instrument in selected_text

        interval_text = page.locator('[data-mdl-field="ohlcv_interval"]').inner_text()
        assert interval_text == (ohlcv_body["ohlcv"].get("interval") or "—")
        assert page.locator('[data-mdl-field="ohlcv_live_mark"]').inner_text() == "—"

        # Selected future + OHLCV exclusively from canonical routes on this host.
        allowed_prefixes = (
            f"{base}/landscape",
            f"{base}/market",
            f"{base}/api/market/landscape/ohlcv",
            f"{base}/static/",
            f"{base}/favicon",
        )
        for url in requested_urls:
            assert any(url.startswith(prefix) for prefix in allowed_prefixes), url
            assert "okx.com" not in url.lower()
            assert "/api/v5/" not in url
            assert "credentials" not in url.lower()
            assert "submit_order" not in url.lower()

        assert console_errors == []
        assert page_errors == []
        assert root.get_attribute("data-orders") == "false"
        assert root.get_attribute("data-live-authorized") == "false"
        assert root.get_attribute("data-supervised-presentation-only") == "true"

        context.close()
        browser.close()
