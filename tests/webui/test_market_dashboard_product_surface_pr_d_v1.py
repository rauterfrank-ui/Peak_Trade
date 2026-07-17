"""PR-D guards: Market Dashboard product surface on GET /market."""

from __future__ import annotations

import ast
import inspect
import re
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui import market_surface
from src.webui.market_dashboard_product_surface_v1.presenter import (
    PRESENTER_OWNER,
    build_market_dashboard_page_context_v1,
)
from src.webui.market_dashboard_product_surface_v1.route_composition import (
    PRODUCT_TEMPLATE_NAME,
    build_market_dashboard_product_template_context_v1,
)
from src.webui.market_dashboard_readmodels_v1 import (
    DashboardAvailabilityStateV1,
    UnavailableSnapshotV1,
)
from src.webui.market_dashboard_readmodels_v1.page_builder import (
    PAGE_AGGREGATE_OWNER,
    MarketDashboardPageSourceInputsV1,
    build_market_dashboard_page_snapshot_v1,
)
from src.webui.market_futures_ohlcv_readmodel_v0.builder import (
    build_market_futures_ohlcv_readmodel,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MARKET_SURFACE_PATH = REPO_ROOT / "src" / "webui" / "market_surface.py"
PRODUCT_TEMPLATE_PATH = (
    REPO_ROOT / "templates" / "peak_trade_dashboard" / "market_dashboard_product_v1.html"
)
PRESENTER_PATH = (
    REPO_ROOT / "src" / "webui" / "market_dashboard_product_surface_v1" / "presenter.py"
)
OHLCV_FIXTURE = REPO_ROOT / "tests/fixtures/market_futures_ohlcv_readmodel_v0/complete_minimal"
TS = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)

OLD_LANDMARK_MARKERS = (
    'id="market-v0-shell"',
    "data-market-phase1a-composition-v1",
    "data-market-governed-top20-primary-v1",
    "data-market-decision-funnel-visual-v1",
    "data-market-safety-matrix",
    "double-play-market-v0-shell",
    "ARCHITECTURE RESET IN PROGRESS",
    'id="market-architecture-reset-shell-v1"',
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

UNSUPPORTED_SAFETY_CLAIMS = (
    "execution allowed",
    "execution safe",
    "risk passed",
    "kill switch inactive",
    "authority granted",
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


def test_get_market_returns_200_product_surface(client: TestClient) -> None:
    response = client.get("/market")
    assert response.status_code == 200
    html = response.text
    assert "ARCHITECTURE RESET IN PROGRESS" not in html
    assert 'data-market-dashboard-product-surface-v1="true"' in html
    assert 'data-market-primary-workspace-v1="true"' in html
    assert 'data-market-canonical-decision-v1="true"' in html
    assert 'data-market-engineering-provenance-v1="true"' in html
    assert "READ ONLY" in html
    assert "NOT BOUND" in html
    assert 'data-safety-authority-state="NOT_BOUND"' in html


def test_safety_authority_not_bound_and_no_unsupported_claims(client: TestClient) -> None:
    html = client.get("/market").text.lower()
    assert "not bound" in html
    for claim in UNSUPPORTED_SAFETY_CLAIMS:
        assert claim not in html


def test_no_order_controls(client: TestClient) -> None:
    html = client.get("/market").text
    assert 'type="submit"' not in html.lower()
    assert "<button" not in html.lower()
    assert "Place Order" not in html
    assert "Buy" not in html or "Buy" not in re.findall(r"\bBuy\b", html)
    assert not re.search(r"\b(Buy|Sell|Submit|Execute|Arm)\b", html)


def test_old_landmarks_and_reset_shell_absent(client: TestClient) -> None:
    html = client.get("/market").text
    for marker in OLD_LANDMARK_MARKERS:
        assert marker not in html, f"legacy/reset marker still present: {marker}"


def test_query_params_cannot_reintroduce_dummy(client: TestClient) -> None:
    response = client.get("/market?source=dummy&symbol=ETHUSDT&timeframe=5m")
    assert response.status_code == 200
    html = response.text
    assert "source=dummy" not in html
    assert "ARCHITECTURE RESET IN PROGRESS" not in html
    assert 'data-market-dashboard-product-surface-v1="true"' in html


def test_legacy_redirects_land_on_product_surface(client: TestClient) -> None:
    for path in ("/market/double-play", "/market/futures"):
        response = client.get(path, follow_redirects=True)
        assert response.status_code == 200
        assert "ARCHITECTURE RESET IN PROGRESS" not in response.text
        assert 'data-market-dashboard-product-surface-v1="true"' in response.text


def test_route_uses_single_aggregate_and_presenter() -> None:
    route_src = _market_route_source()
    assert "build_market_dashboard_product_template_context_v1" in route_src
    assert PRODUCT_TEMPLATE_NAME in route_src or "PRODUCT_TEMPLATE_NAME" in route_src
    for name in PROHIBITED_ROUTE_CALLS:
        assert name not in route_src


def test_routed_handler_ast_guard() -> None:
    module = ast.parse(MARKET_SURFACE_PATH.read_text(encoding="utf-8"))
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
    assert "TemplateResponse" in called


def test_template_has_no_domain_imports() -> None:
    text = PRODUCT_TEMPLATE_PATH.read_text(encoding="utf-8")
    assert "import " not in text
    assert "build_static_dashboard_display_dict" not in text
    assert "market_dashboard_current_state" not in text
    assert "{% include" not in text


def test_presenter_has_no_domain_owner_imports() -> None:
    text = PRESENTER_PATH.read_text(encoding="utf-8")
    assert "src.trading" not in text
    assert "src.governance" not in text
    assert "src.execution" not in text
    assert "src.risk" not in text
    assert "build_static_dashboard_display_dict" not in text


def test_page_aggregate_owner_and_presenter_constants() -> None:
    assert "page_builder" in PAGE_AGGREGATE_OWNER
    assert "presenter" in PRESENTER_OWNER
    ctx = build_market_dashboard_product_template_context_v1()
    assert ctx["page_aggregate_owner"] == PAGE_AGGREGATE_OWNER
    assert ctx["presenter_owner"] == PRESENTER_OWNER
    assert ctx["product_gate_pass"] is False
    assert ctx["safety_authority"]["safety_authority_state"] == "NOT_BOUND"


def test_missing_sources_render_explicit_unavailable() -> None:
    snap = build_market_dashboard_page_snapshot_v1(
        MarketDashboardPageSourceInputsV1(generated_at=TS)
    )
    assert isinstance(snap.decision, UnavailableSnapshotV1)
    assert snap.decision.availability_state == DashboardAvailabilityStateV1.MISSING_SOURCE
    assert isinstance(snap.double_play, UnavailableSnapshotV1)
    assert isinstance(snap.safety_authority, UnavailableSnapshotV1)
    assert snap.safety_authority.availability_state == DashboardAvailabilityStateV1.NOT_BOUND
    assert isinstance(snap.execution, UnavailableSnapshotV1)
    assert isinstance(snap.economic, UnavailableSnapshotV1)
    assert isinstance(snap.diagnostics, UnavailableSnapshotV1)
    ctx = build_market_dashboard_page_context_v1(snap)
    assert ctx.decision["availability_label"] == "SOURCE MISSING"
    assert ctx.safety_authority["availability_label"] == "NOT BOUND"
    assert ctx.diagnostics["non_authority_marker"] == "DIAGNOSTIC ONLY"
    assert ctx.market_workspace["chart_available"] is False


def test_stale_market_renders_stale_without_fabrication() -> None:
    readmodel = dict(build_market_futures_ohlcv_readmodel(OHLCV_FIXTURE))
    readmodel["stale"] = True
    snap = build_market_dashboard_page_snapshot_v1(
        MarketDashboardPageSourceInputsV1(
            generated_at=TS,
            market_ohlcv_source=readmodel,
            instrument_id="ETHUSDT",
            venue="binance_usdm_futures",
        )
    )
    # Adapter may mark freshness STALE when source.stale is true — or still project.
    ctx = build_market_dashboard_page_context_v1(snap)
    assert ctx.decision["availability_label"] == "SOURCE MISSING"
    # No fabricated zeros for missing change metrics when unavailable/absent
    if ctx.market_workspace.get("available"):
        assert ctx.market_workspace.get("change_pct_display") is None


def test_malformed_optional_source_fail_closed() -> None:
    snap = build_market_dashboard_page_snapshot_v1(
        MarketDashboardPageSourceInputsV1(
            generated_at=TS,
            diagnostics_source={"authority_effect": "ALTER_DECISION"},  # type: ignore[dict-item]
        )
    )
    assert isinstance(snap.diagnostics, UnavailableSnapshotV1)
    assert snap.diagnostics.availability_state in {
        DashboardAvailabilityStateV1.MALFORMED_SOURCE,
        DashboardAvailabilityStateV1.MISSING_SOURCE,
        DashboardAvailabilityStateV1.UNAVAILABLE,
    }


def test_diagnostics_do_not_alter_canonical_decision() -> None:
    snap = build_market_dashboard_page_snapshot_v1(
        MarketDashboardPageSourceInputsV1(
            generated_at=TS,
            canonical_decision_source=SimpleNamespace(
                evidence_schema_version="canonical_trading_decision_evidence_v1",
                decision_outcome="hold",
                selected_side="flat",
                reason_codes=("rc_hold",),
                semantic_digest="a" * 64,
                decision_id="dec-hold",
            ),
            diagnostics_source={
                "schema_version": "offline_productive_linear_diagnostics_support_bundle.v0",
                "aggregate_status": "WARN",
                "source_statuses": {"x": "ok"},
                "output_digest": "b" * 64,
                "diagnostic_evidence_id": "diag-1",
                "authority_effect": "NONE",
            },
        )
    )
    ctx = build_market_dashboard_page_context_v1(snap)
    assert ctx.decision["decision_status"] == "HOLD"
    assert ctx.diagnostics["non_authority_marker"] == "DIAGNOSTIC ONLY"
    assert ctx.diagnostics["available"] is True


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


def test_static_dp_and_current_state_unreachable_from_route() -> None:
    route_src = _market_route_source()
    assert "build_static_dashboard_display_dict" not in route_src
    assert "market_dashboard_current_state_snapshot_v0" not in route_src
    assert "source=dummy" not in route_src
    composition = (
        REPO_ROOT / "src/webui/market_dashboard_product_surface_v1/route_composition.py"
    ).read_text(encoding="utf-8")
    assert "build_static_dashboard_display_dict" not in composition
    assert "market_dashboard_current_state" not in composition
