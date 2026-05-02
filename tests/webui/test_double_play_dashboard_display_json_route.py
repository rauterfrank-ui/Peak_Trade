# tests/webui/test_double_play_dashboard_display_json_route.py
"""HTTP contract for Master V2 Double Play dashboard display JSON (read-only v0)."""

from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

ROUTE_PATH = "/api/master-v2/double-play/dashboard-display.json"

_EXPECTED_TOP_LEVEL_KEYS = frozenset(
    {
        "display_layer_version",
        "display_snapshot_meta",
        "panels",
        "overall_status",
        "no_live_banner_visible",
        "display_only",
        "trading_ready",
        "testnet_ready",
        "live_ready",
        "live_authorization",
        "warnings",
    }
)

_EXPECTED_DISPLAY_SNAPSHOT_META_KEYS = frozenset(
    {"source_kind", "source_id", "assembled_at_iso"},
)

_EXPECTED_PANEL_KEYS = frozenset(
    {
        "name",
        "status",
        "summary",
        "blockers",
        "missing_inputs",
        "live_authorization",
        "is_authority",
        "is_signal",
        "ordinal",
        "panel_group",
        "severity_rank",
    }
)

# Dict keys anywhere in the payload must not include these (control / runtime / secrets).
# Keys that are legitimate DTO safety flags (e.g. live_authorization) are asserted false separately.
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
        "order",
        "orders",
        "execute",
        "execution",
        "live_enable",
        "live_enabled",
        "live_armed",
        "confirm_token",
        "api_key",
        "secret",
        "exchange",
        "provider",
        "scanner",
        "runtime_handle",
        "session_id",
        "testnet_authorization",
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


def test_dashboard_display_json_top_level_key_surface_is_display_only_contract(
    client: TestClient,
) -> None:
    """Payload top-level keys match the read-only DTO serialization exactly (no extra control fields)."""
    r = client.get(ROUTE_PATH)
    data = r.json()
    assert set(data.keys()) == _EXPECTED_TOP_LEVEL_KEYS
    assert data["display_layer_version"] == "v2"
    meta = data["display_snapshot_meta"]
    assert set(meta.keys()) == _EXPECTED_DISPLAY_SNAPSHOT_META_KEYS
    assert meta["source_kind"] == "static_display_v0"
    assert meta["source_id"] == "webui_dashboard_display_static_v0"
    assembled = meta["assembled_at_iso"]
    assert isinstance(assembled, str)
    datetime.fromisoformat(assembled.replace("Z", "+00:00"))
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


def test_dashboard_display_json_panel_key_surface_and_no_panel_authority_flags(
    client: TestClient,
) -> None:
    r = client.get(ROUTE_PATH)
    data = r.json()
    for panel in data["panels"]:
        assert isinstance(panel, dict)
        assert set(panel.keys()) == _EXPECTED_PANEL_KEYS
        assert panel["live_authorization"] is False
        assert panel["is_authority"] is False
        assert panel["is_signal"] is False
        assert panel["status"] == "display_ready"
        assert isinstance(panel["ordinal"], int)
        assert isinstance(panel["panel_group"], str)
        assert panel["severity_rank"] == 0


def test_dashboard_display_json_display_layer_panel_order_and_groups(client: TestClient) -> None:
    r = client.get(ROUTE_PATH)
    data = r.json()
    expected = (
        ("futures_input", "input", 0),
        ("state_transition", "state", 1),
        ("survival_envelope", "scope", 2),
        ("strategy_suitability", "strategy", 3),
        ("capital_slot_ratchet", "capital", 4),
        ("capital_slot_release", "capital", 5),
        ("composition", "composition", 6),
    )
    by_name = {p["name"]: p for p in data["panels"]}
    for name, group, ordinal in expected:
        p = by_name[name]
        assert p["panel_group"] == group
        assert p["ordinal"] == ordinal


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
            "subprocess",
            "backtest",
        }
    )
    banned_modules = frozenset(
        {
            "src.live",
            "src.live.web",
            "src.data.kraken",
            "src.execution",
            "src.exchange",
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
