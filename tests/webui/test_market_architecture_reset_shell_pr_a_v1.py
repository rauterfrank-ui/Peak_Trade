"""PR-A legacy non-reintroduction guards retained after PR-D product surface.

Reset-shell markers must remain absent from GET /market. Prohibited producers
must stay unreachable from the routed handler.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui import market_surface

REPO_ROOT = Path(__file__).resolve().parents[2]
MARKET_SURFACE_PATH = REPO_ROOT / "src" / "webui" / "market_surface.py"
RESET_TEMPLATE_PATH = REPO_ROOT / "templates" / "peak_trade_dashboard" / "market_v0.html"

OLD_LANDMARK_MARKERS = (
    'id="market-v0-shell"',
    "data-market-phase1a-composition-v1",
    "data-market-governed-top20-primary-v1",
    "data-market-decision-funnel-visual-v1",
    "data-market-double-play-matrix",
    "data-market-safety-matrix",
    "double-play-market-v0-shell",
    "build_static_dashboard_display_dict",
    "market_dashboard_current_state_snapshot_v0",
)

PROHIBITED_ROUTE_CALLS = (
    "build_market_v0_page_template_context",
    "build_static_dashboard_display_dict",
    "resolve_market_page_data",
    "build_market_dashboard_current_state_display_context",
    "load_ohlcv_dataframe",
    "build_market_payload",
)

FORBIDDEN_DOMAIN_OWNER_PATHS = (
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    "src/trading/master_v2/double_play_composition_matrix_v1.py",
    "src/trading/master_v2/canonical_market_context_v1.py",
    "src/governance/capital_risk_sizing_v1.py",
    "src/governance/canonical_order_intent_v1.py",
    "src/execution/pipeline.py",
    "src/backtest/engine.py",
)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def _market_route_source() -> str:
    src = inspect.getsource(market_surface.create_market_router)
    assert "async def market_dashboard_product_page_v1" in src
    start = src.index("async def market_dashboard_product_page_v1")
    rest = src[start:]
    end_markers = ("\n    @router.get", "\n    return router", "\ndef ")
    end = len(rest)
    for marker in end_markers:
        idx = rest.find(marker, 1)
        if idx != -1:
            end = min(end, idx)
    return rest[:end]


def test_get_market_no_longer_renders_reset_shell(client: TestClient) -> None:
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "ARCHITECTURE RESET IN PROGRESS" not in html
    assert 'data-market-architecture-reset-shell-v1="true"' not in html
    assert 'id="market-architecture-reset-shell-v1"' not in html
    assert 'data-market-dashboard-product-surface-v1="true"' in html


def test_old_market_v0_composition_not_routed(client: TestClient) -> None:
    html = client.get("/market").text
    for marker in OLD_LANDMARK_MARKERS:
        assert marker not in html, f"old composition still routed: {marker}"


def test_reset_shell_template_preserved_offline_not_routed() -> None:
    text = RESET_TEMPLATE_PATH.read_text(encoding="utf-8")
    assert "ARCHITECTURE RESET IN PROGRESS" in text
    assert "market-v0-shell" not in text


def test_market_route_source_does_not_call_prohibited_producers() -> None:
    route_src = _market_route_source()
    for name in PROHIBITED_ROUTE_CALLS:
        assert name not in route_src, f"/market still references {name}"


def test_routed_dependency_path_ast_guard() -> None:
    module = ast.parse(MARKET_SURFACE_PATH.read_text(encoding="utf-8"))
    route_fn = None
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == "create_market_router":
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if child.name == "market_dashboard_product_page_v1":
                        route_fn = child
                        break
    assert route_fn is not None, "product page handler missing"
    called: set[str] = set()
    for node in ast.walk(route_fn):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                called.add(func.id)
            elif isinstance(func, ast.Attribute):
                called.add(func.attr)
    for name in PROHIBITED_ROUTE_CALLS:
        assert name not in called, f"AST: /market calls prohibited {name}"
    assert "TemplateResponse" in called


def test_static_prohibited_import_patterns_not_in_route_handler() -> None:
    route_src = _market_route_source()
    prohibited_patterns = (
        "build_static_dashboard_display_dict",
        "market_dashboard_current_state_snapshot_v0",
        "source=dummy",
        "load_dummy_ohlcv",
        "build_market_v0_page_template_context",
    )
    for pattern in prohibited_patterns:
        assert pattern not in route_src


def test_forbidden_domain_owner_files_unchanged_vs_origin_main() -> None:
    import subprocess

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


def test_legacy_redirects_do_not_restore_reset_shell(client: TestClient) -> None:
    for path in ("/market/double-play", "/market/futures"):
        response = client.get(path, follow_redirects=True)
        assert response.status_code == 200
        assert "ARCHITECTURE RESET IN PROGRESS" not in response.text
        assert 'id="market-v0-shell"' not in response.text


def test_query_params_cannot_reintroduce_dummy_composition(client: TestClient) -> None:
    response = client.get("/market?source=dummy&symbol=ETHUSDT&timeframe=5m")
    assert response.status_code == 200
    html = response.text
    assert "ARCHITECTURE RESET IN PROGRESS" not in html
    assert "source=dummy" not in html
    assert 'id="market-v0-shell"' not in html
