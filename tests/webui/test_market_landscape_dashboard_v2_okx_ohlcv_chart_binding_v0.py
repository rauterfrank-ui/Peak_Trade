"""Regression: OKX OHLCV must reach presenter + visible browser chart geometry.

Guards against false PASS on text like "chart bound" without rendered series.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.ops.primary_evidence_retention_v0 import (
    write_manifest_sha256 as _write_manifest_sha256,
)
from src.webui.app import create_app
from src.webui.market_dashboard_landscape_producer_binding_v2 import (
    bind_market_universe_slots,
    load_bound_okx_ohlcv_readmodel_v1,
)
from src.webui.market_dashboard_landscape_v2 import (
    Availability,
    MarketDashboardReadServiceV1,
    present_market_landscape_v2,
)
from src.webui.market_dashboard_landscape_v2.presenter import (
    serialize_ohlcv_browser_payload_v1,
)
from src.webui.workflow_dashboard_archive_root_v1 import ENV_ARCHIVE_ROOT

REPO = Path(__file__).resolve().parents[2]
STAMP = datetime(2026, 7, 24, 22, 0, 0, tzinfo=timezone.utc)
BAR_COUNT = 100
FIRST_TS = "2026-07-20T18:00:00Z"
LAST_TS = "2026-07-24T21:00:00Z"
INSTRUMENT = "SATS-USDT-SWAP"


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_okx_universe_and_ohlcv(archive_root: Path) -> Path:
    readmodels = archive_root / "readmodels"
    readmodels.mkdir(parents=True, exist_ok=True)
    universe = {
        "schema_name": "universe_selection_readmodel.v1",
        "schema_version": 1,
        "generated_at": "2026-07-24T21:48:23Z",
        "source_run_id": "okx_chart_geometry_v1",
        "source_stage": "paper",
        "non_authorizing": True,
        "fixture_marked": False,
        "universe": [
            {
                "row_id": "c-SATS-USDT-SWAP",
                "symbol": INSTRUMENT,
                "rank": 1,
                "exchange": "okx",
            }
        ],
        "ranking": [
            {
                "row_id": "r-c-SATS-USDT-SWAP",
                "symbol": INSTRUMENT,
                "rank": 1,
                "notes": "futures_upstream_adapter_v1",
            }
        ],
        "selected_future": {
            "row_id": "s-c-SATS-USDT-SWAP",
            "symbol": INSTRUMENT,
            "rank": 1,
            "truth_status": "PERSISTED",
            "selection_reason": "upstream_explicit_selection",
        },
        # Canonical OKX intake leaves captured_at null; venue still in exchange.
        "market_snapshot": {
            "truth_status": "PERSISTED",
            "source_kind": "futures_upstream_adapter_v1",
            "snapshot_id": "u2c-SATS-USDT-SWAP",
            "exchange": "okx",
            "captured_at": None,
        },
        "evidence": {
            "producer_contract": "universe_selection_producer.v1",
            "storage_target": "readmodels/universe_selection_readmodel.v1.json",
            "links": [],
        },
        "missing_truth": {
            "universe": "PERSISTED",
            "ranking": "PERSISTED",
            "selected_future": "PERSISTED",
            "future_detail": "AVAILABLE",
            "orders_fills_pnl": "NOT_PERSISTED",
        },
    }
    (readmodels / "universe_selection_readmodel.v1.json").write_text(
        json.dumps(universe, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_manifest_sha256(readmodels)

    start = datetime(2026, 7, 20, 18, 0, 0, tzinfo=timezone.utc)
    bars = []
    for i in range(BAR_COUNT):
        ts = start + timedelta(hours=i)
        # Decimal strings as in canonical OKX OHLCV readmodel.
        base = 0.000000009663 + (i * 1e-15)
        open_v = f"{base:.15f}".rstrip("0").rstrip(".")
        high_v = f"{base * 1.002:.15f}".rstrip("0").rstrip(".")
        low_v = f"{base * 0.998:.15f}".rstrip("0").rstrip(".")
        close_v = f"{base * 1.001:.15f}".rstrip("0").rstrip(".")
        bars.append(
            {
                "ts": _iso(ts),
                "open": open_v,
                "high": high_v,
                "low": low_v,
                "close": close_v,
                "volume": "1000",
                "volume_ccy": "1000",
                "confirm": i < BAR_COUNT - 1,
                "provider_ts_ms": str(int(ts.timestamp() * 1000)),
            }
        )
    assert bars[0]["ts"] == FIRST_TS
    assert bars[-1]["ts"] == LAST_TS
    ohlcv = {
        "schema_name": "okx_selected_instrument_ohlcv_readmodel.v1",
        "schema_version": 1,
        "non_authorizing": True,
        "fixture_only": False,
        "venue": "okx",
        "market_type": "perpetual",
        "interval": "PT1H",
        "provider_bar": "1H",
        "instrument_id": INSTRUMENT,
        "provider_instrument_id": INSTRUMENT,
        "selection_bundle_id": "okx_chart_geometry_v1",
        "captured_at": "2026-07-24T21:48:24Z",
        "effective_at": "2026-07-24T21:48:24Z",
        "freshness_state": "fresh",
        "is_stale": False,
        "stale_reason": None,
        "gap_count": 0,
        "bar_count": BAR_COUNT,
        "closed_bar_count": BAR_COUNT - 1,
        "first_timestamp": bars[0]["ts"],
        "last_timestamp": bars[-1]["ts"],
        "last_closed_timestamp": bars[-2]["ts"],
        "bars": bars,
        "notes": [],
    }
    (readmodels / "okx_selected_instrument_ohlcv_readmodel.v1.json").write_text(
        json.dumps(ohlcv, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return archive_root


def test_route_presenter_receives_100_canonical_ohlcv_bars(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = _write_okx_universe_and_ohlcv(tmp_path / "archive")
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))

    slots = bind_market_universe_slots(generated_at=STAMP, archive_root=archive)
    assert slots["market_instrument"].availability is Availability.AVAILABLE
    assert slots["market_instrument"].venue == "okx"
    assert slots["market_instrument"].instrument_id == INSTRUMENT

    page = MarketDashboardReadServiceV1().load_page_snapshot(
        generated_at=STAMP,
        git_sha=None,
        slot_overrides=slots,
    )
    ohlcv = load_bound_okx_ohlcv_readmodel_v1(
        archive_root=archive,
        selected_instrument_id=page.market_instrument.instrument_id
        or page.universe_ranking.selected_instrument_id,
        selected_venue=page.market_instrument.venue,
    )
    assert ohlcv is not None
    assert ohlcv["bar_count"] == BAR_COUNT
    assert len(ohlcv["bars"]) == BAR_COUNT

    ctx = present_market_landscape_v2(page, ohlcv_readmodel=ohlcv)
    assert ctx["chart"]["bar_count"] == BAR_COUNT
    assert ctx["chart"]["has_browser_series"] is True
    assert ctx["chart"]["browser_payload"] is not None
    assert len(ctx["chart"]["browser_payload"]["bars"]) == BAR_COUNT
    assert ctx["global_strip"]["venue"] == "OKX"

    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "Primary chart bound to materialized OKX OHLCV readmodel" in html
    assert f"(bars={BAR_COUNT}" in html
    assert 'data-mdl-field="venue">OKX</dd>' in html
    assert 'data-mdl-ohlcv-json="true"' in html
    assert 'data-mdl-chart-canvas="true"' in html
    assert INSTRUMENT in html


def test_serialize_ohlcv_browser_payload_finite_numeric_ohlc() -> None:
    raw = {
        "instrument_id": INSTRUMENT,
        "venue": "okx",
        "interval": "PT1H",
        "bars": [
            {
                "ts": FIRST_TS,
                "open": "0.000000009663",
                "high": "0.000000009731",
                "low": "0.000000009654",
                "close": "0.000000009675",
                "volume": "12.5",
            },
            {
                "ts": LAST_TS,
                "open": "0.000000009199",
                "high": "0.000000009201",
                "low": "0.000000009155",
                "close": "0.000000009176",
                "volume": "8.25",
            },
        ],
    }
    payload = serialize_ohlcv_browser_payload_v1(raw)
    assert payload is not None
    assert payload["bar_count"] == 2
    assert payload["venue"] == "OKX"
    assert payload["first_timestamp"] == FIRST_TS
    assert payload["last_timestamp"] == LAST_TS
    for bar in payload["bars"]:
        for key in ("open", "high", "low", "close"):
            value = bar[key]
            assert isinstance(value, float)
            assert math.isfinite(value)
    assert (
        serialize_ohlcv_browser_payload_v1(
            {"bars": [{"ts": FIRST_TS, "open": "nan", "high": "1", "low": "1", "close": "1"}]}
        )
        is None
    )


def test_real_chrome_visible_chart_geometry_and_venue_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("playwright")
    from playwright.sync_api import sync_playwright

    archive = _write_okx_universe_and_ohlcv(tmp_path / "archive")
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    client = TestClient(create_app())
    html = client.get("/market").text
    assert "chart bound" in html.lower()
    assert 'data-mdl-ohlcv-json="true"' in html

    console_errors: list[str] = []
    page_errors: list[str] = []
    failed_requests: list[str] = []

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True)
        try:
            for width, height in ((1512, 982), (1920, 1080)):
                context = browser.new_context(viewport={"width": width, "height": height})
                page = context.new_page()
                page.on(
                    "console",
                    lambda msg: (
                        console_errors.append(f"{msg.type}:{msg.text}")
                        if msg.type == "error"
                        else None
                    ),
                )
                page.on("pageerror", lambda exc: page_errors.append(str(exc)))
                page.on(
                    "requestfailed",
                    lambda req: failed_requests.append(f"{req.url}:{req.failure}"),
                )

                def _handler(route, request, _html=html):  # type: ignore[no-untyped-def]
                    url = request.url
                    if url.endswith("/market") or url.rstrip("/").endswith(":8765"):
                        route.fulfill(status=200, content_type="text/html", body=_html)
                        return
                    if "/static/" in url:
                        rel = url.split("/static/", 1)[1]
                        path = REPO / "static" / rel
                        if path.is_file():
                            ctype = (
                                "text/css"
                                if path.suffix == ".css"
                                else "application/javascript"
                                if path.suffix == ".js"
                                else "application/octet-stream"
                            )
                            route.fulfill(status=200, content_type=ctype, body=path.read_bytes())
                            return
                    route.fulfill(status=404, body=b"missing")

                page.route("**/*", _handler)
                page.goto("http://127.0.0.1:8765/market", wait_until="networkidle")

                venue = page.locator('[data-mdl-field="venue"]')
                assert venue.inner_text().strip() == "OKX"
                assert "MISSING_SOURCE" not in venue.inner_text()

                canvas = page.locator("[data-mdl-chart-canvas='true']")
                assert canvas.count() == 1
                page.wait_for_function(
                    """() => {
                      const c = document.querySelector('[data-mdl-chart-canvas="true"]');
                      return c && c.getAttribute('data-mdl-chart-geometry') === 'nonzero';
                    }"""
                )
                metrics = page.evaluate(
                    """() => {
                      const c = document.querySelector('[data-mdl-chart-canvas="true"]');
                      const msg = document.querySelector('[data-mdl-chart-message="true"]');
                      const root = document.querySelector('[data-market-landscape-v2="true"]');
                      return {
                        bar_count: Number(c.getAttribute('data-mdl-chart-bar-count') || 0),
                        geometry: c.getAttribute('data-mdl-chart-geometry'),
                        blank: c.getAttribute('data-mdl-chart-blank'),
                        first_ts: c.getAttribute('data-mdl-chart-first-ts'),
                        last_ts: c.getAttribute('data-mdl-chart-last-ts'),
                        width: c.width,
                        height: c.height,
                        message: (msg && msg.textContent) || '',
                        bound_without_geometry:
                          root && root.getAttribute('data-mdl-chart-bound-without-geometry'),
                        overflow:
                          document.documentElement.scrollWidth >
                          document.documentElement.clientWidth + 1,
                      };
                    }"""
                )
                assert metrics["bar_count"] == BAR_COUNT
                assert metrics["geometry"] == "nonzero"
                assert metrics["blank"] == "false"
                assert metrics["first_ts"] == FIRST_TS
                assert metrics["last_ts"] == LAST_TS
                assert metrics["width"] > 0 and metrics["height"] > 0
                assert "chart bound" in metrics["message"].lower()
                assert metrics["bound_without_geometry"] == "false"
                assert metrics["overflow"] is False
                context.close()
        finally:
            browser.close()

    assert console_errors == [], console_errors
    assert page_errors == [], page_errors
    assert failed_requests == [], failed_requests


def test_chart_bound_text_cannot_pass_without_embedded_series(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Static guard: bound message requires browser payload embedding."""
    archive = _write_okx_universe_and_ohlcv(tmp_path / "archive")
    monkeypatch.setenv(ENV_ARCHIVE_ROOT, str(archive))
    html = TestClient(create_app()).get("/market").text
    assert "chart bound" in html.lower()
    assert 'data-mdl-ohlcv-json="true"' in html
    assert 'data-mdl-chart-canvas="true"' in html
    # Message alone is insufficient without series mount points.
    assert 'data-mdl-chart-has-series="true"' in html
