"""Static ownership and import guards for market_dashboard_readmodels_v1 (PR-B)."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from src.webui.app import create_app

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "src" / "webui" / "market_dashboard_readmodels_v1"
PACKAGE_DOC = REPO_ROOT / "docs" / "webui" / "MARKET_DASHBOARD_READMODELS_V1.md"
MARKET_SURFACE = REPO_ROOT / "src" / "webui" / "market_surface.py"
RESET_TEMPLATE = REPO_ROOT / "templates" / "peak_trade_dashboard" / "market_v0.html"

FORBIDDEN_IMPORT_PREFIXES = (
    "jinja2",
    "flask",
    "src.webui.app",
    "src.trading.master_v2.integrated_offline_trading_logic_replay_v1",
    "src.trading.master_v2.double_play_composition_matrix_v1",
    "src.trading.master_v2.canonical_market_context_v1",
    "src.execution",
    "src.strategies",
    "src.governance.capital_risk_sizing_v1",
    "src.governance.canonical_order_intent_v1",
    "src.governance.promotion_loop",
    "src.risk_layer",
    "src.backtest.engine",
)

FORBIDDEN_SOURCE_TOKENS = (
    "TemplateResponse",
    "render_template",
    "place_order",
    "submit_order",
    "create_order",
    "integrated_offline_trading_logic_replay_v1",
    "double_play_composition_matrix_v1",
    "build_static_dashboard_display_dict",
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

FORBIDDEN_TREE_PREFIXES = (
    "src/risk_layer/",
    "src/governance/promotion_loop/",
    "src/strategies/",
)

RESET_SHELL_MARKERS = (
    "Market Dashboard",
    "ARCHITECTURE RESET IN PROGRESS",
    "READ ONLY",
    "NO TRADING AUTHORITY",
)


def _package_py_files() -> list[Path]:
    # Top-level contract modules only; adapters have dedicated PR-C guards.
    return sorted(PACKAGE_DIR.glob("*.py"))


def _adapter_py_files() -> list[Path]:
    adapters = PACKAGE_DIR / "adapters"
    if not adapters.is_dir():
        return []
    return sorted(adapters.rglob("*.py"))


def _import_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module)
    return names


def test_package_does_not_import_templates_flask_jinja_or_domain_owners() -> None:
    for path in _package_py_files():
        imports = _import_names(path)
        text = path.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_IMPORT_PREFIXES:
            for name in imports:
                assert not (name == prefix or name.startswith(prefix + ".")), (
                    f"{path.name} imports forbidden module {name}"
                )
        for token in FORBIDDEN_SOURCE_TOKENS:
            assert token not in text, f"{path.name} contains forbidden token {token}"


def test_package_readme_states_pr_c_and_pr_d_boundaries() -> None:
    assert PACKAGE_DOC.is_file()
    readme = PACKAGE_DOC.read_text(encoding="utf-8")
    assert "PR-C" in readme
    assert "PR-D" in readme
    assert "Producer binding" in readme
    assert "Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook" in readme
    assert not (PACKAGE_DIR / "README.md").exists()


def test_market_route_binds_product_surface_not_legacy_composition() -> None:
    route_text = MARKET_SURFACE.read_text(encoding="utf-8")
    product_template = (
        REPO_ROOT / "templates" / "peak_trade_dashboard" / "market_dashboard_product_v1.html"
    )
    template_text = product_template.read_text(encoding="utf-8")
    assert "build_market_dashboard_product_template_context_v1" in route_text
    assert "MarketDashboardPageSnapshotV1" not in template_text
    assert "import " not in template_text
    assert "ARCHITECTURE RESET IN PROGRESS" not in template_text
    assert "data-market-dashboard-product-surface-v1" in template_text


def test_get_market_renders_product_surface() -> None:
    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "ARCHITECTURE RESET IN PROGRESS" not in html
    assert 'data-market-dashboard-product-surface-v1="true"' in html
    assert "NOT BOUND" in html
    assert 'type="submit"' not in html


def test_forbidden_domain_owner_files_have_no_diff_vs_origin_main() -> None:
    for rel in FORBIDDEN_DOMAIN_OWNER_PATHS:
        result = subprocess.run(
            ["git", "diff", "origin/main", "--", rel],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert result.stdout == "", f"forbidden domain owner changed: {rel}"


def test_forbidden_trees_have_no_diff_vs_origin_main() -> None:
    result = subprocess.run(
        ["git", "diff", "--name-only", "origin/main"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    changed = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    for path in changed:
        for prefix in FORBIDDEN_TREE_PREFIXES:
            assert not path.startswith(prefix), f"forbidden tree path changed: {path}"


def test_legacy_prohibited_producers_unreachable_from_market_route() -> None:
    text = MARKET_SURFACE.read_text(encoding="utf-8")
    assert "async def market_dashboard_product_page_v1" in text
    start = text.index("async def market_dashboard_product_page_v1")
    end_markers = ("\n    return router", "\ndef ")
    end = len(text)
    for marker in end_markers:
        idx = text.find(marker, start + 1)
        if idx != -1:
            end = min(end, idx)
    route_body = text[start:end]
    for token in (
        "build_market_v0_page_template_context",
        "build_static_dashboard_display_dict",
        "market_dashboard_current_state_snapshot_v0",
        "resolve_market_page_data",
        "load_ohlcv_dataframe",
    ):
        assert token not in route_body
    assert "build_market_dashboard_product_template_context_v1" in route_body
