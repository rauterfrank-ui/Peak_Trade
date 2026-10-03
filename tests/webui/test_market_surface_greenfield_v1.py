"""Greenfield operator trading surface v1 — safety, provenance, and projection contracts."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import app
from src.webui.market_surface_greenfield_v1 import trade_counters_v1
from src.webui.market_surface_greenfield_v1.market_projection_v1 import (
    project_market_state_from_ohlcv_doc,
)
from src.webui.market_surface_greenfield_v1.router_v1 import router as greenfield_router

REPO_ROOT = Path(__file__).resolve().parents[2]
GREENFIELD_ROOT = REPO_ROOT / "src" / "webui" / "market_surface_greenfield_v1"
FORBIDDEN_V3_IMPORT_MARKERS = (
    "market_dashboard_landscape_v2",
    "landscape_dashboard_persistent_local_host_v1",
    "market_dashboard_landscape_producer_binding_v2",
    "market_dashboard_landscape_shell_router_v2",
)


def _greenfield_py_files() -> list[Path]:
    return sorted(GREENFIELD_ROOT.rglob("*.py"))


def _static_js_files() -> list[Path]:
    return sorted((REPO_ROOT / "static" / "js" / "market_surface_greenfield_v1").glob("*.js"))


def test_router_exposes_get_only_routes() -> None:
    methods: set[str] = set()
    for route in greenfield_router.routes:
        for m in route.methods or []:
            methods.add(m.upper())
    assert methods <= {"GET", "HEAD"}
    assert "POST" not in methods


def test_html_surface_has_no_card_tile_primary_markers() -> None:
    html = (
        REPO_ROOT / "templates" / "peak_trade_dashboard" / "market_surface_greenfield_v1.html"
    ).read_text(encoding="utf-8")
    assert 'data-ots-greenfield-v1="true"' in html
    assert "rounded" not in html
    assert "dashboard-card" not in html.lower()
    assert "widget-grid" not in html.lower()
    assert "okx.com" not in html.lower()


def test_browser_js_single_poll_loop_no_okx() -> None:
    app_js = REPO_ROOT / "static" / "js" / "market_surface_greenfield_v1" / "surface_app_v1.js"
    js = app_js.read_text(encoding="utf-8")
    assert js.count("fetch(") == 1
    assert "okx.com" not in js.lower()
    assert "wss://" not in js.lower()
    assert "WebSocket" not in js


def test_no_v3_landscape_imports_in_greenfield_python() -> None:
    for path in _greenfield_py_files():
        text = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_V3_IMPORT_MARKERS:
            assert marker not in text, f"{path} imports forbidden marker {marker}"


def test_trade_counter_classification_no_synthetic_ranking() -> None:
    filled = {"event_type": "filled", "payload": {"effect_class": "SIMULATED_EFFECT"}}
    assert trade_counters_v1.classify_execution_event(filled)["counts_as_trades_set"] is True
    hold = {"event_type": "validated"}
    assert trade_counters_v1.classify_execution_event(hold)["counts_as_trades_set"] is False
    assert trade_counters_v1.classify_execution_event(hold)["counts_as_trades_rejected"] is False


def test_market_projection_empty_is_not_demo_data() -> None:
    state = project_market_state_from_ohlcv_doc(
        None, refresh_meta=None, observed_at="2026-01-01T00:00:00+00:00"
    )
    assert state["candle_series"] == []
    assert state["last_price"] is None
    assert state["okx_inst_id"] is None


def test_market_projection_maps_real_bars() -> None:
    doc = {
        "instrument_id": "ETH-USDT-SWAP",
        "provider_instrument_id": "ETH-USDT-SWAP",
        "freshness_state": "FRESH",
        "bars": [
            {
                "ts": "2026-01-01T00:00:00+00:00",
                "open": "1",
                "high": "2",
                "low": "0.5",
                "close": "1.5",
                "provider_ts_ms": "1735689600000",
            }
        ],
    }
    state = project_market_state_from_ohlcv_doc(doc, refresh_meta={"status": "OK"}, observed_at="x")
    assert state["okx_inst_id"] == "ETH-USDT-SWAP"
    assert len(state["candle_series"]) == 1
    assert state["last_price"] == 1.5


def test_state_api_unknown_slots_not_synthesized() -> None:
    client = TestClient(app)
    resp = client.get("/api/operator-trading-surface/v1/state")
    assert resp.status_code == 200
    body = resp.json()
    unknown = body["system"]["unknown_sources"]
    assert unknown["top20"]["label"] == "SOURCE UNAVAILABLE"
    assert unknown["confirmation"]["label"] == "NO CANONICAL SOURCE"
    assert "synthetic" not in resp.text.lower()


def test_state_api_safety_posture_read_only() -> None:
    client = TestClient(app)
    body = client.get("/api/operator-trading-surface/v1/state").json()
    safety = body["safety"]
    assert safety["read_only_surface"] is True
    assert safety["pt_mutation_routes"] == 0
    assert safety["direct_browser_okx"] is False
    assert safety["post_allowed"] is False


def test_operator_trading_surface_html_route() -> None:
    client = TestClient(app)
    resp = client.get("/operator-trading-surface")
    assert resp.status_code == 200
    assert "data-ots-greenfield-v1" in resp.text
    assert "lightweight-charts" in resp.text


def test_lightweight_charts_vendor_present() -> None:
    vendor = (
        REPO_ROOT
        / "static"
        / "vendor"
        / "lightweight-charts"
        / "4.2.2"
        / "lightweight-charts.standalone.production.js"
    )
    assert vendor.is_file()
    assert vendor.stat().st_size > 10_000


def test_greenfield_ast_no_post_decorators() -> None:
    for path in _greenfield_py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                for dec in node.decorator_list:
                    src = ast.unparse(dec)
                    assert "post" not in src.lower()


@pytest.mark.parametrize(
    "pattern",
    [
        r"compute_top5|synthetic_top5|rank_top5",
        r"top20.*rank",
        r"confirmation_heuristic",
        r"keychain",
    ],
)
def test_greenfield_sources_exclude_forbidden_patterns(pattern: str) -> None:
    blob = "\n".join(p.read_text(encoding="utf-8") for p in _greenfield_py_files())
    blob += "\n".join(p.read_text(encoding="utf-8") for p in _static_js_files())
    assert re.search(pattern, blob, re.IGNORECASE) is None
