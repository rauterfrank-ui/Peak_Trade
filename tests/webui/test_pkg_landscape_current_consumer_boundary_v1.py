"""PKG-LANDSCAPE-CURRENT-CONSUMER-AND-TOMBSTONE-RETIREMENT-V1 boundary.

Protects OWNER_GO=PEAK_TRADE_LANDSCAPE_REMOVE_CURRENT_DASHBOARD_TOMBSTONE_SEMANTICS_V1

    PACKAGE_D_CLASS=TESTS_ONLY_PLUS_CANONICAL_DOCS_AND_CI_SEMANTIC_CORRECTION
    WORKPACKAGE_ID=PKG-LANDSCAPE-CURRENT-CONSUMER-AND-TOMBSTONE-RETIREMENT-V1

Positive current Landscape V2 consumer/visual-ops boundary. This module does
not conserve a historical dashboard tombstone as today's architecture
contract. It does not require DELETED_PACKAGES, market_visual_operator_surface_v1,
MARKET_DASHBOARD_REMOVED.md, or tests/webui/test_market_dashboard_tombstone_v1.py.

It inspects the current Landscape structure directly:

    LANDSCAPE_V2_CURRENT_VISUAL_CONSUMER=true
    LANDSCAPE_CONSUMER_ONLY=true
    DASHBOARD_AUTHORITY_EFFECT=NONE
    LANDSCAPE_TRADING_AUTHORITY=false
    LANDSCAPE_SIGNAL_AUTHORITY=false
    LANDSCAPE_SELECTION_AUTHORITY=false
    LANDSCAPE_RISK_AUTHORITY=false
    LANDSCAPE_PLANNING_AUTHORITY=false
    LANDSCAPE_EXECUTION_AUTHORITY=false
    LANDSCAPE_LIVE_PERMIT_AUTHORITY=false

Slot reuse_status values are read from the current owner registry. This
package does not invent producers, bind NOT_BOUND slots, or treat
NOT_BOUND as an implementation gap.
"""

from __future__ import annotations

import ast
from pathlib import Path

from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_landscape_v2 import PACKAGE_MARKER
from src.webui.market_dashboard_landscape_v2.owner_registry import (
    CANONICAL_OWNER_REGISTRY_V1,
    REQUIRED_PROJECTION_SLOTS,
    owner_registry_by_slot,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LANDSCAPE_PKG = REPO_ROOT / "src" / "webui" / "market_dashboard_landscape_v2"
SHELL_ROUTER = REPO_ROOT / "src" / "webui" / "market_dashboard_landscape_shell_router_v2.py"
PRODUCER_BINDING = REPO_ROOT / "src" / "webui" / "market_dashboard_landscape_producer_binding_v2.py"
APP_PATH = REPO_ROOT / "src" / "webui" / "app.py"
LANDSCAPE_TEMPLATE = REPO_ROOT / "templates" / "peak_trade_dashboard" / "market_landscape_v2.html"
LANDSCAPE_CHART_JS = REPO_ROOT / "static" / "js" / "market_dashboard_landscape_v2.js"
R_AND_D_CHARTS_TEMPLATE = REPO_ROOT / "templates" / "peak_trade_dashboard" / "r_and_d_charts.html"
CHARTJS_VENDOR_PRIMARY = "/static/vendor/chartjs/4.4.1/chart.umd.min.js"
LANDSCAPE_RUNBOOK = (
    REPO_ROOT
    / "docs"
    / "ops"
    / "market_dashboard"
    / "PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md"
)

_VALID_REUSE_STATUSES: frozenset[str] = frozenset({"REUSED", "PROJECTION_ONLY", "NOT_BOUND"})
_FORBIDDEN_AUTHORITY_TOKENS: frozenset[str] = frozenset(
    {
        "submit_order",
        "place_order",
        "create_order",
        "LIVE_ENABLED",
        "LIVE_ARMED",
        "LIVE_AUTHORIZED",
        "TESTNET_AUTHORIZED",
        "CANARY_AUTHORIZED",
        "enable_live_trading",
        "Permit",
        "ExecutionPermit",
        "compute_decision",
        "recompute_decision",
        "compute_risk",
        "recompute_risk",
        "select_direction",
        "switch_scope",
    }
)

# Required non-claims. Do not invert these in this surface.
LANDSCAPE_V2_CURRENT_VISUAL_CONSUMER = True
LANDSCAPE_CONSUMER_ONLY = True
DASHBOARD_AUTHORITY_EFFECT = "NONE"
LANDSCAPE_TRADING_AUTHORITY = False
LANDSCAPE_SIGNAL_AUTHORITY = False
LANDSCAPE_SELECTION_AUTHORITY = False
LANDSCAPE_RISK_AUTHORITY = False
LANDSCAPE_PLANNING_AUTHORITY = False
LANDSCAPE_EXECUTION_AUTHORITY = False
LANDSCAPE_LIVE_PERMIT_AUTHORITY = False
HISTORICAL_DASHBOARD_REQUIRED_FOR_CURRENT_CONTRACT = False
HISTORICAL_TOMBSTONE_REQUIRED_FOR_CURRENT_CONTRACT = False
PRODUCTIVE_MUTATION_PERFORMED_BY_THIS_PACKAGE = False


def _iter_python_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts))


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _collected_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Call):
            call_name = _call_name(node)
            if call_name:
                names.add(call_name)
        elif isinstance(node, ast.ClassDef):
            names.add(node.name)
    return names


def test_package_contract_does_not_normalize_authority_claims() -> None:
    assert LANDSCAPE_V2_CURRENT_VISUAL_CONSUMER is True
    assert LANDSCAPE_CONSUMER_ONLY is True
    assert DASHBOARD_AUTHORITY_EFFECT == "NONE"
    assert LANDSCAPE_TRADING_AUTHORITY is False
    assert LANDSCAPE_SIGNAL_AUTHORITY is False
    assert LANDSCAPE_SELECTION_AUTHORITY is False
    assert LANDSCAPE_RISK_AUTHORITY is False
    assert LANDSCAPE_PLANNING_AUTHORITY is False
    assert LANDSCAPE_EXECUTION_AUTHORITY is False
    assert LANDSCAPE_LIVE_PERMIT_AUTHORITY is False
    assert HISTORICAL_DASHBOARD_REQUIRED_FOR_CURRENT_CONTRACT is False
    assert HISTORICAL_TOMBSTONE_REQUIRED_FOR_CURRENT_CONTRACT is False
    assert PRODUCTIVE_MUTATION_PERFORMED_BY_THIS_PACKAGE is False


def test_current_visual_consumer_is_landscape_v2_package_and_route() -> None:
    assert LANDSCAPE_PKG.is_dir()
    assert (LANDSCAPE_PKG / "owner_registry.py").is_file()
    assert (LANDSCAPE_PKG / "presenter.py").is_file()
    assert SHELL_ROUTER.is_file()
    assert PRODUCER_BINDING.is_file()
    assert LANDSCAPE_TEMPLATE.is_file()
    assert PACKAGE_MARKER == "MARKET_DASHBOARD_LANDSCAPE_V2_READMODEL_CONTRACTS=true"

    app_text = APP_PATH.read_text(encoding="utf-8")
    assert "market_dashboard_landscape_shell_router_v2" in app_text
    assert "app.include_router(market_dashboard_landscape_shell_router_v2)" in app_text
    assert "create_market_router" not in app_text

    router_text = SHELL_ROUTER.read_text(encoding="utf-8")
    assert '@router.get("/market"' in router_text
    assert 'name="market_landscape_v2"' in router_text
    assert "@router.post" not in router_text
    assert "@router.put" not in router_text
    assert "@router.patch" not in router_text
    assert "@router.delete" not in router_text
    assert '"trading_authority": False' in router_text
    assert '"risk_authority": False' in router_text

    template = LANDSCAPE_TEMPLATE.read_text(encoding="utf-8")
    assert 'data-market-landscape-v2="true"' in template
    assert 'data-market-dashboard-authority="false"' in template


def test_get_market_serves_landscape_v2_consumer_shell() -> None:
    client = TestClient(create_app())
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert 'data-market-landscape-v2="true"' in html
    assert 'data-market-dashboard-authority="false"' in html
    assert "text/html" in response.headers.get("content-type", "")


def test_landscape_runbook_states_read_only_consumer_without_trading_authority() -> None:
    text = LANDSCAPE_RUNBOOK.read_text(encoding="utf-8")
    assert "DASHBOARD=READ_ONLY_CONSUMER" in text
    assert "DASHBOARD_AUTHORITY_EFFECT=NONE" in text
    assert "DASHBOARD_TRADING_INPUT=false" in text
    assert "DASHBOARD_IS_CURRENTLY_PURE_CONSUMER=true" in text
    assert "CANONICAL_ROUTE=GET_/market" in text
    assert "CANONICAL_SHELL_ROUTER=src/webui/market_dashboard_landscape_shell_router_v2.py" in text
    assert "LIVE_AUTHORIZED=false" in text
    assert "ORDERS=false" in text
    assert "ACTIVE_TOMBSTONE_SURFACE=false" in text
    assert "CURRENT_NEGATIVE_NON_REGRESSION_GUARD=false" in text
    assert "CURRENT_TOMBSTONE_CONTRACT=false" in text
    assert "CURRENT_VISUAL_CONSUMER=LANDSCAPE_V2" in text
    assert "LEGACY_MARKET_SURFACE_STATUS=REMOVED_WITH_NEGATIVE_NON_REGRESSION_GUARDS" not in text
    assert LANDSCAPE_CONSUMER_ONLY is True
    assert DASHBOARD_AUTHORITY_EFFECT == "NONE"


def test_owner_registry_slot_statuses_are_read_from_current_landscape_authority() -> None:
    slots = tuple(entry.slot for entry in CANONICAL_OWNER_REGISTRY_V1)
    assert slots == REQUIRED_PROJECTION_SLOTS
    by_slot = owner_registry_by_slot()
    assert tuple(by_slot) == slots

    reuse_by_slot = {entry.slot: entry.reuse_status for entry in CANONICAL_OWNER_REGISTRY_V1}
    assert set(reuse_by_slot.values()) <= _VALID_REUSE_STATUSES

    reused = tuple(slot for slot, status in reuse_by_slot.items() if status == "REUSED")
    not_bound = tuple(slot for slot, status in reuse_by_slot.items() if status == "NOT_BOUND")
    projection_only = tuple(
        slot for slot, status in reuse_by_slot.items() if status == "PROJECTION_ONLY"
    )

    assert reused == (
        "market_instrument",
        "universe_ranking",
        "dynamic_scope",
        "regime_bull_bear_switch",
        "canonical_decision",
        "double_play",
        "risk_sizing_capital",
        "safety_authority",
        "execution_reconciliation",
        "economic_summary",
        "source_health",
    )
    assert not_bound == ("autonomy_stage", "diagnostics_summary")
    assert projection_only == ()

    autonomy = by_slot["autonomy_stage"]
    assert autonomy.reuse_status == "NOT_BOUND"
    assert autonomy.owner_module == "NONE"
    assert autonomy.owner_symbol == "NONE"

    diagnostics = by_slot["diagnostics_summary"]
    assert diagnostics.reuse_status == "NOT_BOUND"
    assert diagnostics.owner_module == "UNRESOLVED"
    assert diagnostics.owner_symbol == "UNRESOLVED"


def test_landscape_package_has_no_trading_selection_risk_execution_or_live_permit_authority() -> (
    None
):
    token_hits: list[tuple[str, str]] = []
    scan_paths = _iter_python_files(LANDSCAPE_PKG) + (SHELL_ROUTER,)
    for path in scan_paths:
        rel = str(path.relative_to(REPO_ROOT))
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = _collected_names(tree)
        for token in sorted(names & _FORBIDDEN_AUTHORITY_TOKENS):
            token_hits.append((rel, token))
    assert token_hits == []
    assert LANDSCAPE_TRADING_AUTHORITY is False
    assert LANDSCAPE_SIGNAL_AUTHORITY is False
    assert LANDSCAPE_SELECTION_AUTHORITY is False
    assert LANDSCAPE_RISK_AUTHORITY is False
    assert LANDSCAPE_PLANNING_AUTHORITY is False
    assert LANDSCAPE_EXECUTION_AUTHORITY is False
    assert LANDSCAPE_LIVE_PERMIT_AUTHORITY is False


def test_landscape_consumer_census_has_no_connectable_current_gap() -> None:
    """Adjudicate current Landscape consumer census. No new slot bindings."""
    by_slot = owner_registry_by_slot()
    reused = tuple(slot for slot, entry in by_slot.items() if entry.reuse_status == "REUSED")
    not_bound = tuple(slot for slot, entry in by_slot.items() if entry.reuse_status == "NOT_BOUND")
    assert reused == (
        "market_instrument",
        "universe_ranking",
        "dynamic_scope",
        "regime_bull_bear_switch",
        "canonical_decision",
        "double_play",
        "risk_sizing_capital",
        "safety_authority",
        "execution_reconciliation",
        "economic_summary",
        "source_health",
    )
    assert not_bound == ("autonomy_stage", "diagnostics_summary")
    assert "event_decision_timeline" not in by_slot
    assert "vendor_fallback" not in by_slot
    assert "last_paper_run" not in by_slot
    assert "paper_shadow_summary" not in by_slot
    assert "observability_hub" not in by_slot

    runbook = LANDSCAPE_RUNBOOK.read_text(encoding="utf-8")
    assert "CANONICAL_TIMELINE_SOURCE_EXISTS=false" in runbook
    assert "TASK_4_STATE_TRANSITION_TIMELINE=DEFERRED" in runbook
    assert "CURRENT_VISUAL_CONSUMER=LANDSCAPE_V2" in runbook


def test_vendor_fallback_is_chartjs_ui_infrastructure_not_a_landscape_slot() -> None:
    """Vendor fallback is Chart.js self-hosted primary for R&D charts, not Landscape."""
    landscape_html = LANDSCAPE_TEMPLATE.read_text(encoding="utf-8")
    landscape_js = LANDSCAPE_CHART_JS.read_text(encoding="utf-8")
    rnd_html = R_AND_D_CHARTS_TEMPLATE.read_text(encoding="utf-8")

    assert 'src="/static/js/market_dashboard_landscape_v2.js"' in landscape_html
    assert 'data-mdl-chart-canvas="true"' in landscape_html
    assert CHARTJS_VENDOR_PRIMARY not in landscape_html
    assert "peak-trade-chartjs-vendor-fallback-ready" not in landscape_html
    assert "chart.umd.min.js" not in landscape_js
    assert "Chart(" not in landscape_js

    assert CHARTJS_VENDOR_PRIMARY in rnd_html
    assert 'data-chartjs-vendor-primary-v1="true"' in rnd_html
    assert "peak-trade-chartjs-vendor-fallback-ready" in rnd_html
    assert LANDSCAPE_CONSUMER_ONLY is True
    assert DASHBOARD_AUTHORITY_EFFECT == "NONE"
