# tests/webui/test_double_play_dashboard_display_json_route.py
"""HTTP contract for Master V2 Double Play dashboard display JSON (read-only v0)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

ROUTE_PATH = "/api/master-v2/double-play/dashboard-display.json"

_FORBIDDEN_JSON_KEYS = frozenset(
    {
        "start",
        "stop",
        "arm",
        "enable",
        "allocate",
        "release",
        "trade",
        "fetch",
        "scan",
        "select",
        "promote",
        "approve",
        "sign_off",
        "live",
    }
)


def _collect_object_keys(obj, out: set[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                out.add(k)
            _collect_object_keys(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_object_keys(item, out)


@pytest.fixture
def client() -> TestClient:
    from src.webui.app import create_app

    return TestClient(create_app())


def test_dashboard_display_json_returns_200(client: TestClient) -> None:
    r = client.get(ROUTE_PATH)
    assert r.status_code == 200


def test_dashboard_display_json_content_type_and_cache_control(client: TestClient) -> None:
    r = client.get(ROUTE_PATH)
    assert "application/json" in (r.headers.get("content-type") or "")
    assert r.headers.get("cache-control") == "no-store"


def test_dashboard_display_json_required_no_live_fields(client: TestClient) -> None:
    r = client.get(ROUTE_PATH)
    data = r.json()
    assert data["display_only"] is True
    assert data["no_live_banner_visible"] is True
    assert data["trading_ready"] is False
    assert data["testnet_ready"] is False
    assert data["live_ready"] is False
    assert data["live_authorization"] is False


def test_dashboard_display_json_panels_and_warnings(client: TestClient) -> None:
    r = client.get(ROUTE_PATH)
    data = r.json()
    assert "panels" in data
    assert isinstance(data["panels"], list)
    assert len(data["panels"]) == 7
    assert "warnings" in data
    assert isinstance(data["warnings"], list)
    assert "overall_status" in data


def test_dashboard_display_json_representative_panels_are_display_ready(client: TestClient) -> None:
    r = client.get(ROUTE_PATH)
    data = r.json()
    by_name = {p["name"]: p for p in data["panels"]}
    expected = (
        "futures_input",
        "state_transition",
        "survival_envelope",
        "strategy_suitability",
        "capital_slot_ratchet",
        "capital_slot_release",
        "composition",
    )
    for name in expected:
        assert name in by_name
        assert by_name[name]["status"] == "display_ready"
    assert data["overall_status"] == "display_ready"


def test_dashboard_display_json_no_forbidden_control_keys(client: TestClient) -> None:
    r = client.get(ROUTE_PATH)
    data = r.json()
    keys: set[str] = set()
    _collect_object_keys(data, keys)
    assert keys.isdisjoint(_FORBIDDEN_JSON_KEYS)


def test_route_module_import_surface_is_safe() -> None:
    root = Path(__file__).resolve().parents[2] / "src" / "webui"
    path = root / "double_play_dashboard_display_json_route_v0.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    banned_roots = frozenset(
        {
            "ccxt",
            "requests",
            "aiohttp",
            "httpx",
            "urllib3",
            "socket",
        }
    )
    banned_modules = frozenset(
        {
            "src.live",
            "src.live.web",
            "src.data.kraken",
            "src.execution",
            "scripts",
        }
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                base = n.name.split(".")[0]
                if base in banned_roots:
                    raise AssertionError(f"unexpected import: {n.name}")
                if base == "trading" and not n.name.startswith("trading.master_v2"):
                    raise AssertionError(f"unexpected import: {n.name}")
        if isinstance(node, ast.ImportFrom) and node.module:
            mod = node.module
            if mod in banned_modules or any(mod.startswith(p + ".") for p in banned_modules):
                raise AssertionError(f"unexpected from-import: {mod}")
            if (
                mod.startswith("trading.")
                and mod != "trading.master_v2"
                and not mod.startswith("trading.master_v2.")
            ):
                raise AssertionError(f"unexpected from-import: {mod}")
            top = mod.split(".")[0]
            if top in banned_roots:
                raise AssertionError(f"unexpected from-import: {mod}")
