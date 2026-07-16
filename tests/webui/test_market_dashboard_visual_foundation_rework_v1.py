"""Visual foundation rework v1: composition contract markers and anti-badge-wall."""

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


@pytest.fixture()
def client_foundation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[TestClient]:
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


def test_foundation_composition_tokens_present() -> None:
    css = TOKENS.read_text(encoding="utf-8")
    assert "--pt-header-height: 64px;" in css
    assert "--pt-safety-rail-max-height: 32px;" in css
    assert "--pt-hero-min-height: 210px;" in css
    assert "--pt-hero-max-height: 290px;" in css
    assert "--pt-primary-chart-min-height: 390px;" in css
    layout = LAYOUT.read_text(encoding="utf-8")
    assert "pt-foundation-safety-rail-line" in layout
    assert "pt-foundation-instrument-title" in layout


def test_foundation_markers_and_anti_badge_wall(client_foundation: TestClient) -> None:
    body = re.sub(r"<style>.*?</style>", "", _html(client_foundation), flags=re.S)
    assert 'data-market-foundation-global-header-v1="true"' in body
    assert 'data-market-foundation-safety-rail-v1="true"' in body
    assert 'data-market-foundation-hero-v1="true"' in body
    assert 'data-market-foundation-primary-chart-v1="true"' in body
    assert 'data-market-phase-1a-primary-status-count-v1="3"' in body
    assert 'data-market-chart-height-v1="390"' in body
    assert "lg:grid-cols-8" not in body
    assert "Peak Trade / Operator Console" in body
    assert "System decision" in body
    assert "Primary blocker" in body
    assert 'data-market-foundation-chart-meta-v1="true"' in body
    # Authority/orders/live remain truthful but are not a badge wall in the rail.
    assert "Futures only" in body
    assert "Execution / Orders / Live disabled" in body
    assert "ORDERS_DISABLED" in body
    assert "LIVE_DISABLED" in body


def test_foundation_dom_order_preserved(client_foundation: TestClient) -> None:
    body = re.sub(r"<style>.*?</style>", "", _html(client_foundation), flags=re.S)
    header_i = body.find('data-market-foundation-global-header-v1="true"')
    rail_i = body.find('data-market-foundation-safety-rail-v1="true"')
    hero_i = body.find('data-market-foundation-hero-panel-v1="true"')
    chart_i = body.find('data-market-foundation-primary-chart-v1="true"')
    assert min(header_i, rail_i, hero_i, chart_i) >= 0
    assert header_i < rail_i < hero_i < chart_i
