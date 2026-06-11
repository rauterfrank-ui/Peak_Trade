"""Web UI tests for env-gated cumulative market depth chart SSR v0 on GET /market."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

from src.webui.app import create_app
from src.webui.market_surface import build_market_depth_display_context

FIXTURE_ROOT = (
    project_root / "tests" / "fixtures" / "market_depth_readmodel_v0" / "complete_minimal"
)
MALFORMED_ROOT = (
    project_root / "tests" / "fixtures" / "market_depth_readmodel_v0" / "malformed_levels"
)

CUMULATIVE_MARKERS = (
    'data-market-v0-depth-chart-cumulative="true"',
    'data-market-v0-depth-chart-ready="true"',
    'data-market-v0-depth-chart-readonly="true"',
    'data-market-v0-depth-chart-authority="false"',
    'data-market-v0-depth-chart-non-authorizing="true"',
    'data-market-v0-depth-chart-provider-truth-blocked="true"',
    'data-market-v0-depth-chart-dashboard-truth-blocked="true"',
    'data-market-v0-depth-chart-trading-readiness-blocked="true"',
    'data-market-v0-depth-chart-selected-future-truth-blocked="true"',
    'data-market-v0-depth-chart-liquidity-truth-blocked="true"',
    'data-market-v0-depth-chart-slippage-truth-blocked="true"',
    'data-market-v0-depth-chart-depth-truth-blocked="true"',
    'data-market-v0-depth-chart-execution-readiness-blocked="true"',
    'data-market-v0-depth-chart-double-play-protected="true"',
    'data-market-v0-depth-chart-market-airport-excluded="true"',
    'data-market-v0-depth-chart-cumulative-svg-v0="true"',
)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.delenv("PEAK_TRADE_MARKET_DEPTH_CHART_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_MARKET_TAPE_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_MARKET_RUN_PROJECTION_ENABLED", raising=False)
    with TestClient(create_app()) as test_client:
        yield test_client


def _html(client: TestClient, path: str = "/market") -> str:
    response = client.get(path)
    assert response.status_code == 200
    return response.text


def _enable_depth_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT", str(FIXTURE_ROOT.resolve()))


def test_chart_sub_gate_off_no_cumulative_markers(client: TestClient) -> None:
    html = _html(client)
    for marker in CUMULATIVE_MARKERS:
        assert marker not in html
    assert "data-market-v0-depth-chart-enabled" not in html


def test_chart_sub_gate_off_depth_fixture_shows_non_cumulative_placeholder(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _enable_depth_fixture(monkeypatch)
    html = _html(client)
    assert 'data-market-v0-depth-chart-placeholder="true"' in html
    assert "Not cumulative" in html
    assert 'data-market-v0-depth-chart-cumulative="true"' not in html


def test_chart_gate_on_valid_fixture_shows_cumulative_ssr(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _enable_depth_fixture(monkeypatch)
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_CHART_ENABLED", "1")
    html = _html(client)

    for marker in CUMULATIVE_MARKERS:
        assert marker in html
    assert 'data-market-v0-depth-chart-enabled="true"' in html
    assert "Cumulative depth (display-only, offline fixture)" in html
    assert "not liquidity truth" in html
    svg_idx = html.index('data-market-v0-depth-chart-cumulative-svg-v0="true"')
    chart_window = html[svg_idx : svg_idx + 4000]
    assert "Chart(" not in chart_window
    assert "fetch(" not in html
    assert "/api/market/depth" not in html


def test_chart_gate_on_depth_disabled_fail_closed(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_CHART_ENABLED", "1")
    html = _html(client)
    assert 'data-market-v0-depth-chart-cumulative="true"' not in html
    assert 'data-market-v0-depth-chart-ready="true"' not in html


def test_chart_gate_on_malformed_fixture_fail_closed(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT", str(MALFORMED_ROOT.resolve()))
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_CHART_ENABLED", "1")
    html = _html(client)
    assert 'data-market-v0-depth-chart-cumulative="true"' not in html
    assert 'data-market-v0-depth-chart-ready="true"' not in html


def test_double_play_excludes_cumulative_depth_chart_markers(client: TestClient) -> None:
    html = _html(client, "/market/double-play")
    for marker in CUMULATIVE_MARKERS:
        assert marker not in html
    assert 'data-market-v0-depth-chart-cumulative="true"' not in html


def test_build_market_depth_display_context_cumulative_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_depth_fixture(monkeypatch)
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_CHART_ENABLED", "1")
    ctx = build_market_depth_display_context()
    assert ctx["chart_gate_enabled"] is True
    assert ctx["chart_cumulative_ready"] is True
    assert ctx["chart_has_svg_paths"] is True
    assert "M120" in ctx["chart_bid_path_d"]
    assert "M120" in ctx["chart_ask_path_d"]


def test_build_market_depth_display_context_chart_gate_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_depth_fixture(monkeypatch)
    monkeypatch.delenv("PEAK_TRADE_MARKET_DEPTH_CHART_ENABLED", raising=False)
    ctx = build_market_depth_display_context()
    assert ctx["chart_gate_enabled"] is False
    assert ctx["chart_cumulative_ready"] is False
