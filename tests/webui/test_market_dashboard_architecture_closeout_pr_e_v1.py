"""PR-E closeout guards: Market Dashboard architecture reset final static contracts."""

from __future__ import annotations

import ast
import inspect
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui import market_surface
from src.webui.market_dashboard_product_surface_v1 import (
    PRODUCT_TEMPLATE_NAME,
    build_market_dashboard_product_template_context_v1,
)
from src.webui.market_dashboard_readmodels_v1.page_builder import PAGE_AGGREGATE_OWNER

REPO_ROOT = Path(__file__).resolve().parents[2]
MARKET_SURFACE = REPO_ROOT / "src" / "webui" / "market_surface.py"
PRODUCT_TEMPLATE = (
    REPO_ROOT / "templates" / "peak_trade_dashboard" / "market_dashboard_product_v1.html"
)
PRODUCT_PACKAGE = REPO_ROOT / "src" / "webui" / "market_dashboard_product_surface_v1"
PRESENTER = PRODUCT_PACKAGE / "presenter.py"
ROUTE_COMPOSITION = PRODUCT_PACKAGE / "route_composition.py"

DELETED_LEGACY_TEMPLATES = (
    "templates/peak_trade_dashboard/double_play_market_dashboard_v0.html",
    "templates/peak_trade_dashboard/futures_read_only_market_dashboard_v0.html",
)

FORBIDDEN_DOMAIN_OWNER_PATHS = (
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    "src/trading/master_v2/double_play_composition_matrix_v1.py",
    "src/governance/capital_risk_sizing_v1.py",
    "src/execution/pipeline.py",
)

PROHIBITED_ROUTE_CALLS = (
    "build_market_v0_page_template_context",
    "build_static_dashboard_display_dict",
    "build_market_dashboard_current_state_display_context",
    "resolve_market_page_data",
    "load_ohlcv_dataframe",
    "build_market_payload",
)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def _route_handler_source() -> str:
    src = inspect.getsource(market_surface.create_market_router)
    assert "async def market_dashboard_product_page_v1" in src
    start = src.index("async def market_dashboard_product_page_v1")
    rest = src[start:]
    end = len(rest)
    for marker in ("\n    @router.get", "\n    return router", "\ndef "):
        idx = rest.find(marker, 1)
        if idx != -1:
            end = min(end, idx)
    return rest[:end]


def test_market_resolves_only_through_product_surface(client: TestClient) -> None:
    html = client.get("/market").text
    assert 'data-market-dashboard-product-surface-v1="true"' in html
    assert "ARCHITECTURE RESET IN PROGRESS" not in html
    assert 'data-market-architecture-reset-shell-v1="true"' not in html
    assert 'id="market-v0-shell"' not in html
    assert (
        PRODUCT_TEMPLATE_NAME.replace(".html", "") in market_surface.CANONICAL_MARKET_TEMPLATE_OWNER
    )


def test_deleted_legacy_standalone_shells_absent() -> None:
    for rel in DELETED_LEGACY_TEMPLATES:
        assert not (REPO_ROOT / rel).exists(), f"deleted shell reintroduced: {rel}"


def test_static_dp_and_current_state_unreachable_from_routed_handler() -> None:
    route_src = _route_handler_source()
    for name in PROHIBITED_ROUTE_CALLS:
        assert name not in route_src
    composition = ROUTE_COMPOSITION.read_text(encoding="utf-8")
    assert "build_static_dashboard_display_dict" not in composition
    assert "market_dashboard_current_state" not in composition
    assert "source=dummy" not in composition


def test_one_page_aggregate_and_presenter_owners(client: TestClient) -> None:
    ctx = build_market_dashboard_product_template_context_v1()
    assert ctx["page_aggregate_owner"] == PAGE_AGGREGATE_OWNER
    assert "presenter" in ctx["presenter_owner"]
    html = client.get("/market").text
    assert 'data-page-aggregate-owner="' in html
    assert PAGE_AGGREGATE_OWNER.split(".")[-1] in html or "page_builder" in html


def test_canonical_consumers_bound_via_adapters() -> None:
    ctx = build_market_dashboard_product_template_context_v1()
    # Bound as consumers: sections exist; missing sources remain explicit unavailable.
    assert ctx["decision"]["availability_state"] in {
        "MISSING_SOURCE",
        "UNAVAILABLE",
        "NOT_BOUND",
        "AVAILABLE",
        "STALE",
        "MALFORMED_SOURCE",
    }
    assert ctx["double_play"]["availability_state"] in {
        "MISSING_SOURCE",
        "UNAVAILABLE",
        "NOT_BOUND",
        "AVAILABLE",
        "STALE",
        "MALFORMED_SOURCE",
    }
    assert ctx["safety_authority"]["safety_authority_state"] == "NOT_BOUND"


def test_missing_sources_fail_closed_and_no_order_controls(client: TestClient) -> None:
    html = client.get("/market").text
    assert "SOURCE MISSING" in html or "NOT BOUND" in html
    assert 'type="submit"' not in html.lower()
    assert "<button" not in html.lower()
    assert "Place Order" not in html


def test_presenter_and_template_have_no_domain_owner_imports() -> None:
    for path in (PRESENTER, PRODUCT_TEMPLATE, ROUTE_COMPOSITION):
        text = path.read_text(encoding="utf-8")
        assert "src.trading" not in text
        assert "src.governance" not in text
        assert "src.execution" not in text
        assert "integrated_offline_trading_logic_replay_v1" not in text


def test_routed_handler_ast_only_calls_product_composition() -> None:
    module = ast.parse(MARKET_SURFACE.read_text(encoding="utf-8"))
    route_fn = None
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == "create_market_router":
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if child.name == "market_dashboard_product_page_v1":
                        route_fn = child
                        break
    assert route_fn is not None
    called: set[str] = set()
    for node in ast.walk(route_fn):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                called.add(func.id)
            elif isinstance(func, ast.Attribute):
                called.add(func.attr)
    for name in PROHIBITED_ROUTE_CALLS:
        assert name not in called
    assert "build_market_dashboard_product_template_context_v1" in called


def test_domain_owner_files_unchanged_vs_origin_main() -> None:
    for rel in FORBIDDEN_DOMAIN_OWNER_PATHS:
        result = subprocess.run(
            ["git", "diff", "origin/main", "--", rel],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout == "", f"forbidden domain owner changed: {rel}"


def test_legacy_redirects_land_on_product_surface(client: TestClient) -> None:
    for path in ("/market/double-play", "/market/futures"):
        response = client.get(path, follow_redirects=True)
        assert response.status_code == 200
        assert 'data-market-dashboard-product-surface-v1="true"' in response.text
        assert "ARCHITECTURE RESET IN PROGRESS" not in response.text
