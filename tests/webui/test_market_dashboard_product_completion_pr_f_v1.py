"""PR-F: Market Dashboard full product completion — loaders, route, DOM, review harness."""

from __future__ import annotations

import ast
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.webui.app import create_app
from src.webui.market_dashboard_product_surface_v1.route_composition import (
    build_market_dashboard_product_template_context_v1,
)
from src.webui.market_dashboard_product_surface_v1.source_loader import (
    ENV_REVIEW_EVIDENCE_ROOT,
    ENV_VENUE,
    load_market_dashboard_readonly_sources_v1,
)
from src.webui.market_dashboard_readmodels_v1 import DashboardAvailabilityStateV1
from src.webui.market_dashboard_readmodels_v1.contracts import UnavailableSnapshotV1
from src.webui.market_dashboard_readmodels_v1.page_builder import (
    MarketDashboardPageSourceInputsV1,
    build_market_dashboard_page_snapshot_v1,
)

REPO = Path(__file__).resolve().parents[2]
OHLCV = REPO / "tests/fixtures/market_futures_ohlcv_readmodel_v0/complete_minimal"
RANKING = REPO / "tests/fixtures/market_ranking_funnel_readmodel_v0/complete_minimal"
EVIDENCE = REPO / "tests/fixtures/market_dashboard_review_evidence_v1/complete_minimal"
REVIEW_SH = REPO / "scripts/webui/review_server.sh"
ROUTE_PATH = REPO / "src/webui/market_dashboard_product_surface_v1/route_composition.py"
TEMPLATE = REPO / "templates/peak_trade_dashboard/market_dashboard_product_v1.html"
TS = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)

FORBIDDEN_DOMAIN_OWNER_PATHS = (
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    "src/trading/master_v2/double_play_composition_matrix_v1.py",
    "src/governance/capital_risk_sizing_v1.py",
    "src/governance/canonical_order_intent_v1.py",
    "src/execution/pipeline.py",
)


@pytest.fixture()
def review_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT", str(RANKING))
    monkeypatch.setenv("PEAK_TRADE_MARKET_FUTURES_OHLCV_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_FUTURES_OHLCV_BUNDLE_ROOT", str(OHLCV))
    monkeypatch.setenv(ENV_VENUE, "binance_usdm_futures")
    monkeypatch.setenv(ENV_REVIEW_EVIDENCE_ROOT, str(EVIDENCE))


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_app())


def test_source_loader_binds_all_available_review_sources(review_env: None) -> None:
    loaded = load_market_dashboard_readonly_sources_v1(generated_at=TS)
    assert loaded.venue == "binance_usdm_futures"
    assert loaded.instrument_id == "ETHUSDT"
    assert loaded.market_ohlcv_source is not None
    assert loaded.ranking_source is not None
    assert loaded.canonical_decision_source is not None
    assert loaded.double_play_composition is not None
    assert loaded.double_play_bull_assessment is not None
    assert loaded.double_play_bear_assessment is not None
    assert loaded.execution_source is not None
    assert loaded.economic_source is not None
    assert loaded.diagnostics_source is not None
    assert loaded.safety_authority_source is None
    assert len(loaded.chart_bars) > 0
    assert loaded.decision_evidence_reference is not None
    assert "review_evidence" in loaded.decision_evidence_reference
    assert "safety_authority_not_bound_no_consolidated_producer" in loaded.loader_notes


def test_source_loader_malformed_decision_fails_closed(
    review_env: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bad = tmp_path / "bad_evidence"
    bad.mkdir()
    (bad / "canonical_decision.json").write_text("{not-json", encoding="utf-8")
    monkeypatch.setenv(ENV_REVIEW_EVIDENCE_ROOT, str(bad))
    loaded = load_market_dashboard_readonly_sources_v1(generated_at=TS)
    assert loaded.canonical_decision_source is None
    assert any("decision_evidence_absent_or_malformed" in n for n in loaded.loader_notes)
    # Other sources still load from ranking/ohlcv env.
    assert loaded.ranking_source is not None


def test_source_loader_no_silent_dummy_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PEAK_TRADE_MARKET_FUTURES_OHLCV_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED", raising=False)
    monkeypatch.delenv(ENV_VENUE, raising=False)
    monkeypatch.delenv(ENV_REVIEW_EVIDENCE_ROOT, raising=False)
    loaded = load_market_dashboard_readonly_sources_v1(generated_at=TS)
    assert loaded.market_ohlcv_source is None
    assert loaded.ranking_source is None
    assert loaded.canonical_decision_source is None
    assert loaded.chart_bars == ()


def test_route_composition_populated_review_snapshot(review_env: None) -> None:
    ctx = build_market_dashboard_product_template_context_v1()
    assert ctx["product_gate_pass"] is False
    assert ctx["header"]["instrument_id"] == "ETHUSDT"
    assert ctx["header"]["venue"] == "binance_usdm_futures"
    assert ctx["market_workspace"]["chart_available"] is True
    assert ctx["market_workspace"]["bar_count"] > 0
    assert ctx["decision"]["available"] is True
    assert ctx["decision"]["decision_status"] == "HOLD"
    assert ctx["decision"]["blockers"]
    assert ctx["double_play"]["available"] is True
    assert ctx["ranking"]["available"] is True
    assert ctx["economic"]["available"] is True
    assert ctx["diagnostics"]["available"] is True
    assert ctx["execution"]["available"] is True
    assert ctx["safety_authority"]["availability_state"] == "NOT_BOUND"


def test_route_composition_source_text_has_no_hardcoded_none_for_available() -> None:
    text = ROUTE_PATH.read_text(encoding="utf-8")
    # Must wire loaded.* fields; residual safety may still be loaded.safety_authority_source.
    assert "canonical_decision_source=loaded.canonical_decision_source" in text
    assert "double_play_composition=loaded.double_play_composition" in text
    assert "execution_source=loaded.execution_source" in text
    assert "economic_source=loaded.economic_source" in text
    assert "diagnostics_source=loaded.diagnostics_source" in text
    assert "canonical_decision_source=None" not in text
    assert "double_play_composition=None" not in text


def test_missing_individual_source_isolation(review_env: None) -> None:
    loaded = load_market_dashboard_readonly_sources_v1(generated_at=TS)
    inputs = MarketDashboardPageSourceInputsV1(
        generated_at=TS,
        market_ohlcv_source=loaded.market_ohlcv_source,
        instrument_id=loaded.instrument_id,
        venue=loaded.venue,
        ranking_source=loaded.ranking_source,
        canonical_decision_source=None,
        double_play_composition=loaded.double_play_composition,
        double_play_bull_assessment=loaded.double_play_bull_assessment,
        double_play_bear_assessment=loaded.double_play_bear_assessment,
        execution_source=loaded.execution_source,
        economic_source=None,
        diagnostics_source=loaded.diagnostics_source,
        market_source_reference=loaded.market_source_reference,
        ranking_source_reference=loaded.ranking_source_reference,
    )
    snap = build_market_dashboard_page_snapshot_v1(inputs)
    assert isinstance(snap.decision, UnavailableSnapshotV1)
    assert snap.decision.availability_state == DashboardAvailabilityStateV1.MISSING_SOURCE
    assert not isinstance(snap.market, UnavailableSnapshotV1)
    assert not isinstance(snap.double_play, UnavailableSnapshotV1)
    assert isinstance(snap.economic, UnavailableSnapshotV1)


def test_product_dom_populated_review(client: TestClient, review_env: None) -> None:
    html = client.get("/market").text
    assert 'data-market-dashboard-product-surface-v1="true"' in html
    assert 'data-market-chart-candles-v1="true"' in html
    assert 'data-market-chart-candle-v1="true"' in html
    assert 'data-market-chart-price-axis-v1="true"' in html
    assert 'data-market-chart-time-axis-v1="true"' in html
    assert 'data-market-header-instrument-v1="true">ETHUSDT' in html
    assert "binance_usdm_futures" in html
    assert 'data-market-decision-status-v1="true"' in html
    assert "HOLD" in html
    assert 'data-market-decision-reason-codes-v1="true"' in html
    assert 'data-market-decision-blockers-v1="true"' in html
    assert 'data-market-ranking-v1="true"' in html
    assert 'data-market-double-play-v1="true"' in html
    assert "hold_selected" in html
    assert 'data-market-economic-v1="true"' in html
    assert 'data-market-diagnostics-v1="true"' in html
    assert 'data-diagnostic-non-authority-marker-v1="true"' in html
    assert 'data-market-engineering-provenance-v1="true"' in html
    assert "<details" in html
    assert 'data-market-chart-unavailable-panel-v1="true"' not in html


def test_no_order_controls_product_template() -> None:
    html = TEMPLATE.read_text(encoding="utf-8")
    assert 'type="submit"' not in html.lower()
    assert "<button" not in html.lower()
    assert not re.search(r"\b(Buy|Sell|Submit|Execute|Arm)\b", html)


def test_static_guards_no_domain_imports_and_no_dummy() -> None:
    for rel in (
        "src/webui/market_dashboard_product_surface_v1/source_loader.py",
        "src/webui/market_dashboard_product_surface_v1/route_composition.py",
        "src/webui/market_dashboard_product_surface_v1/presenter.py",
    ):
        text = (REPO / rel).read_text(encoding="utf-8")
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("src.trading")
                assert not node.module.startswith("src.governance")
                assert not node.module.startswith("src.execution")
        assert "build_dummy" not in text
        assert "source=dummy" not in text
        assert "random.random" not in text
    for path in FORBIDDEN_DOMAIN_OWNER_PATHS:
        assert (REPO / path).is_file()


def test_review_server_default_binds_venue_and_evidence() -> None:
    text = REVIEW_SH.read_text(encoding="utf-8")
    assert "PEAK_TRADE_WEBUI_REVIEW_BIND_FIXTURES:-1}" in text
    assert "PEAK_TRADE_MARKET_DASHBOARD_VENUE" in text
    assert "PEAK_TRADE_MARKET_DASHBOARD_REVIEW_EVIDENCE_ROOT" in text
    assert "REVIEW_VENUE_DEFAULT" in text
    assert "market_dashboard_review_evidence_v1/complete_minimal" in text
    # Documented command path must resolve fixture files.
    assert (RANKING / "ranking_funnel.json").is_file()
    assert (OHLCV / "futures_ohlcv.json").is_file()
    assert (EVIDENCE / "manifest.json").is_file()
    assert (EVIDENCE / "canonical_decision.json").is_file()


def test_negative_missing_dp_does_not_collapse_page(
    review_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    for name in (
        "canonical_decision.json",
        "execution.json",
        "economic.json",
        "diagnostics.json",
        "manifest.json",
    ):
        (root / name).write_text((EVIDENCE / name).read_text(encoding="utf-8"), encoding="utf-8")
    # Omit double_play.json
    monkeypatch.setenv(ENV_REVIEW_EVIDENCE_ROOT, str(root))
    ctx = build_market_dashboard_product_template_context_v1()
    assert ctx["decision"]["available"] is True
    assert ctx["market_workspace"]["chart_available"] is True
    assert ctx["double_play"]["available"] is False


def test_product_gate_remains_false(review_env: None) -> None:
    ctx = build_market_dashboard_product_template_context_v1()
    assert ctx["product_gate_pass"] is False
