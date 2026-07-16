"""Composition-first visual refactor v1: anti-card-wall markers and type ladder."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

from src.webui.app import create_app
from src.webui.futures_read_only_market_dashboard_runtime_v0 import (
    ENV_BUNDLE_ROOT as F5_ENV_BUNDLE_ROOT,
    ENV_ENABLED as F5_ENV_ENABLED,
)
from src.webui.market_futures_ohlcv_runtime_v0 import (
    ENV_BUNDLE_ROOT as OHLCV_ENV_BUNDLE_ROOT,
    ENV_ENABLED as OHLCV_ENV_ENABLED,
)
from src.webui.market_ranking_funnel_runtime_v0 import (
    ENV_BUNDLE_ROOT as RANKING_ENV_BUNDLE_ROOT,
    ENV_ENABLED as RANKING_ENV_ENABLED,
)
from src.webui.market_visual_operator_surface_v1 import ENV_EVIDENCE_ROOT

RANKING_FIXTURE = (
    project_root / "tests" / "fixtures" / "market_ranking_funnel_readmodel_v0" / "complete_minimal"
).resolve()
OHLCV_FIXTURE = (
    project_root / "tests" / "fixtures" / "market_futures_ohlcv_readmodel_v0" / "complete_minimal"
).resolve()
F5_FIXTURE = (
    project_root
    / "tests"
    / "fixtures"
    / "futures_read_only_market_dashboard_v0"
    / "complete_minimal"
).resolve()
TOKENS = (project_root / "static" / "css" / "peak_trade_dashboard_design_tokens_v1.css").resolve()
LAYOUT = (project_root / "static" / "css" / "peak_trade_dashboard_layout_v1.css").resolve()
HERO = (
    project_root
    / "templates"
    / "peak_trade_dashboard"
    / "partials"
    / "market_primary_operator_hero_v1.html"
).resolve()
CHART = (
    project_root
    / "templates"
    / "peak_trade_dashboard"
    / "partials"
    / "market_primary_close_chart_v1.html"
).resolve()


@pytest.fixture()
def client_composition(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[TestClient]:
    evidence = tmp_path / "economic_evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "compact_decision_funnel.json").write_text(
        '{"bar_count": 0, "trade_count": 0, "stages": {}}', encoding="utf-8"
    )
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2030-01-15T12:34:56.000000+00:00")
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    monkeypatch.setenv(OHLCV_ENV_ENABLED, "1")
    monkeypatch.setenv(OHLCV_ENV_BUNDLE_ROOT, str(OHLCV_FIXTURE))
    monkeypatch.setenv(F5_ENV_ENABLED, "1")
    monkeypatch.setenv(F5_ENV_BUNDLE_ROOT, str(F5_FIXTURE))
    monkeypatch.setenv(ENV_EVIDENCE_ROOT, str(evidence))
    monkeypatch.setattr(
        "src.data.kraken.fetch_ohlcv_df",
        MagicMock(side_effect=AssertionError("no request-time kraken")),
    )
    with TestClient(create_app()) as test_client:
        yield test_client


def _html(client: TestClient) -> str:
    resp = client.get("/market?timeframe=1h")
    assert resp.status_code == 200
    return resp.text


def test_composition_tokens_and_layout_contract() -> None:
    css = TOKENS.read_text(encoding="utf-8")
    assert "--pt-type-hero-title:" in css
    assert "--pt-type-decision:" in css
    assert "--pt-type-section:" in css
    assert "--pt-type-meta:" in css
    layout = LAYOUT.read_text(encoding="utf-8")
    assert 'data-market-composition-first-v1="true"' in layout or "composition-first" in layout
    assert "pt-composition-section-title" in layout
    assert "pt-operator-overview-decision-sentence" in layout


def test_composition_markers_and_anti_card_wall(client_composition: TestClient) -> None:
    body = re.sub(r"<style>.*?</style>", "", _html(client_composition), flags=re.S)
    assert 'data-market-composition-first-v1="true"' in body
    assert 'data-market-card-first-v1="false"' in body
    assert 'data-market-composition-primary-stage-v1="true"' in body
    assert 'data-market-composition-hero-fused-v1="true"' in body
    assert 'data-market-composition-decision-fused-v1="true"' in body
    assert 'data-market-composition-blocker-fused-v1="true"' in body
    assert 'data-market-composition-chart-stage-v1="true"' in body
    assert 'data-market-composition-ranking-secondary-v1="true"' in body
    assert "System decision" in body
    assert "Primary blocker" in body
    # Existing foundation markers remain.
    assert 'data-market-foundation-hero-panel-v1="true"' in body
    assert 'data-market-foundation-primary-chart-v1="true"' in body


def test_hero_and_chart_templates_drop_card_chrome() -> None:
    hero = HERO.read_text(encoding="utf-8")
    chart = CHART.read_text(encoding="utf-8")
    assert 'id="market-primary-operator-hero-v1"' in hero
    assert "rounded-md border border-slate-800/70 bg-slate-950/85" not in hero
    assert "rounded border border-slate-700/50 bg-slate-900/45" not in hero
    assert "rounded-lg border border-slate-800/70 ring-1 ring-sky-900/10" not in chart
    assert 'data-market-composition-chart-frame-v1="true"' in chart


def test_composition_dom_order_market_to_detail(client_composition: TestClient) -> None:
    body = re.sub(r"<style>.*?</style>", "", _html(client_composition), flags=re.S)
    hero_i = body.find('data-market-composition-hero-fused-v1="true"')
    decision_i = body.find('data-market-composition-decision-fused-v1="true"')
    blocker_i = body.find('data-market-composition-blocker-fused-v1="true"')
    chart_i = body.find('data-market-composition-chart-stage-v1="true"')
    ranking_i = body.find('data-market-composition-ranking-secondary-v1="true"')
    assert min(hero_i, decision_i, blocker_i, chart_i, ranking_i) >= 0
    assert hero_i < decision_i < blocker_i < chart_i < ranking_i
