"""Static architecture contracts for PR-C dashboard adapters."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from src.webui.app import create_app

REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTERS_DIR = REPO_ROOT / "src" / "webui" / "market_dashboard_readmodels_v1" / "adapters"
PACKAGE_DIR = REPO_ROOT / "src" / "webui" / "market_dashboard_readmodels_v1"
MARKET_SURFACE = REPO_ROOT / "src" / "webui" / "market_surface.py"
RESET_TEMPLATE = REPO_ROOT / "templates" / "peak_trade_dashboard" / "market_v0.html"

FORBIDDEN_ADAPTER_IMPORT_PREFIXES = (
    "jinja2",
    "flask",
    "src.webui.app",
    "src.trading.master_v2.integrated_offline_trading_logic_replay_v1",
    "src.execution",
    "src.strategies",
    "src.governance.capital_risk_sizing_v1",
    "src.governance.canonical_order_intent_v1",
    "src.governance.promotion_loop",
    "src.risk_layer",
    "src.backtest.engine",
)

FORBIDDEN_ADAPTER_TOKENS = (
    "TemplateResponse",
    "render_template",
    "place_order",
    "submit_order",
    "create_order",
    "build_static_dashboard_display_dict",
    "market_dashboard_current_state_snapshot_v0",
    "run_integrated_offline_trading_logic_replay_v1",
    "evaluate_double_play_composition_matrix_v1",
    "write_integrated_offline_replay_evidence_bundle_v1",
)

FORBIDDEN_DOMAIN_IMPORT_OF_ADAPTERS = ("src.webui.market_dashboard_readmodels_v1.adapters",)

RESET_SHELL_MARKERS = (
    "Market Dashboard",
    "ARCHITECTURE RESET IN PROGRESS",
    "READ ONLY",
    "NO TRADING AUTHORITY",
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


def _py_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.py"))


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


def test_adapters_forbid_static_dp_hardcoded_snapshot_templates_and_replay() -> None:
    assert ADAPTERS_DIR.is_dir()
    for path in _py_files(ADAPTERS_DIR):
        text = path.read_text(encoding="utf-8")
        imports = _import_names(path)
        for prefix in FORBIDDEN_ADAPTER_IMPORT_PREFIXES:
            for name in imports:
                assert not (name == prefix or name.startswith(prefix + ".")), (
                    f"{path.name} imports forbidden module {name}"
                )
        for token in FORBIDDEN_ADAPTER_TOKENS:
            assert token not in text, f"{path.name} contains forbidden token {token}"
        assert "requests." not in text
        assert "httpx" not in text
        assert "socket." not in text


def test_adapters_do_not_import_templates_package() -> None:
    for path in _py_files(ADAPTERS_DIR):
        imports = _import_names(path)
        for name in imports:
            assert "templates" not in name.split("."), f"{path.name} imports {name}"
            assert not name.startswith("jinja2")


def test_domain_owners_do_not_import_adapter_package() -> None:
    domain_roots = [
        REPO_ROOT / "src" / "trading" / "master_v2",
        REPO_ROOT / "src" / "governance",
        REPO_ROOT / "src" / "execution",
        REPO_ROOT / "src" / "risk_layer",
        REPO_ROOT / "src" / "strategies",
        REPO_ROOT / "src" / "backtest",
    ]
    for root in domain_roots:
        if not root.exists():
            continue
        for path in _py_files(root):
            text = path.read_text(encoding="utf-8")
            for token in FORBIDDEN_DOMAIN_IMPORT_OF_ADAPTERS:
                assert token not in text, f"{path} imports adapter package"


def test_top_level_readmodel_package_still_forbids_domain_compute_imports() -> None:
    for path in sorted(PACKAGE_DIR.glob("*.py")):
        imports = _import_names(path)
        for name in imports:
            assert "integrated_offline_trading_logic_replay_v1" not in name
            assert "double_play_composition_matrix_v1" not in name
            assert not name.startswith("jinja2")
            assert not name.startswith("flask")


def test_get_market_uses_product_surface_after_pr_d() -> None:
    route_text = MARKET_SURFACE.read_text(encoding="utf-8")
    product_template = (
        REPO_ROOT / "templates" / "peak_trade_dashboard" / "market_dashboard_product_v1.html"
    )
    template_text = product_template.read_text(encoding="utf-8")
    assert "market_dashboard_product_surface_v1" in route_text
    assert "build_market_dashboard_product_template_context_v1" in route_text
    assert "ARCHITECTURE RESET IN PROGRESS" not in template_text
    assert "data-market-dashboard-product-surface-v1" in template_text
    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "ARCHITECTURE RESET IN PROGRESS" not in html
    assert 'data-market-dashboard-product-surface-v1="true"' in html
    assert "NOT BOUND" in html
    assert 'type="submit"' not in html


def test_forbidden_domain_owners_untouched_vs_origin_main() -> None:
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


def test_no_final_dashboard_aggregate_wiring_in_adapters() -> None:
    for path in _py_files(ADAPTERS_DIR):
        text = path.read_text(encoding="utf-8")
        assert "new_market_dashboard_page_snapshot_v1" not in text
        assert "MarketDashboardPageSnapshotV1" not in text
