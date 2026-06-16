"""Contract tests: selected instrument view-only workspace on canonical GET /market."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

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
from src.webui.market_surface import (
    CANONICAL_CHART_OWNER,
    CANONICAL_CONTRACT_METADATA_OWNER,
    CANONICAL_F5_METADATA_OWNER,
    CANONICAL_FRESHNESS_OWNER,
    CANONICAL_FUTURES_OHLCV_OWNER,
    CANONICAL_HERO_TEMPLATE_OWNER,
    CANONICAL_MARKET_ROUTE_OWNER,
    CANONICAL_MARKET_VIEWMODEL_OWNER,
    CANONICAL_RANKING_CONTEXT_OWNER,
    CANONICAL_SELECTED_INSTRUMENT_OWNER,
    CANONICAL_VOLUME_OWNER,
    CANONICAL_WORKSPACE_TEMPLATE_OWNER,
    build_market_selected_instrument_workspace_display_context,
    build_market_v0_page_template_context,
    resolve_market_page_data,
)

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
HERO_PARTIAL = (
    project_root
    / "templates"
    / "peak_trade_dashboard"
    / "partials"
    / "market_primary_operator_hero_v1.html"
)
CHART_PARTIAL = (
    project_root
    / "templates"
    / "peak_trade_dashboard"
    / "partials"
    / "market_primary_close_chart_v1.html"
)
FORBIDDEN_AUTHORITY_RE = re.compile(
    r'(?:type=["\']submit["\']|data-market-(?:order|execute|arm))',
    re.IGNORECASE,
)
PARALLEL_WORKSPACE_RE = re.compile(
    r"market-selected-instrument-workspace-v[2-9]\d*",
    re.IGNORECASE,
)
BITCOIN_RE = re.compile(r"\b(BTC|XBT|BITCOIN)\b", re.IGNORECASE)


@pytest.fixture()
def client_workspace_on(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2030-01-15T12:34:56.000000+00:00")
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    monkeypatch.setenv(OHLCV_ENV_ENABLED, "1")
    monkeypatch.setenv(OHLCV_ENV_BUNDLE_ROOT, str(OHLCV_FIXTURE))
    monkeypatch.setenv(F5_ENV_ENABLED, "1")
    monkeypatch.setenv(F5_ENV_BUNDLE_ROOT, str(F5_FIXTURE))
    kraken_mock = MagicMock(
        side_effect=AssertionError("fetch_ohlcv_df must not run on futures-first /market")
    )
    monkeypatch.setattr("src.data.kraken.fetch_ohlcv_df", kraken_mock)
    with TestClient(create_app()) as test_client:
        yield test_client


def _html(client: TestClient, path: str = "/market") -> str:
    resp = client.get(path)
    assert resp.status_code == 200
    return resp.text


def test_canonical_workspace_owner_constants() -> None:
    assert CANONICAL_WORKSPACE_TEMPLATE_OWNER.endswith("market_primary_operator_hero_v1.html")
    assert CANONICAL_HERO_TEMPLATE_OWNER == CANONICAL_WORKSPACE_TEMPLATE_OWNER
    assert CANONICAL_CHART_OWNER.endswith("market_primary_close_chart_v1.html")
    assert CANONICAL_VOLUME_OWNER == CANONICAL_CHART_OWNER
    assert CANONICAL_FUTURES_OHLCV_OWNER.endswith("market_futures_ohlcv_runtime_v0.py")
    assert CANONICAL_F5_METADATA_OWNER.endswith("futures_read_only_market_dashboard_runtime_v0.py")
    assert CANONICAL_RANKING_CONTEXT_OWNER.endswith("market_surface.py")
    assert CANONICAL_CONTRACT_METADATA_OWNER == CANONICAL_F5_METADATA_OWNER
    assert CANONICAL_FRESHNESS_OWNER == CANONICAL_FUTURES_OHLCV_OWNER
    assert CANONICAL_SELECTED_INSTRUMENT_OWNER.endswith("market_surface.py")
    assert CANONICAL_MARKET_ROUTE_OWNER.endswith("market_surface.py")
    assert CANONICAL_MARKET_VIEWMODEL_OWNER.endswith("market_surface.py")


def test_single_workspace_partial_owner() -> None:
    hero_text = HERO_PARTIAL.read_text(encoding="utf-8")
    assert hero_text.count('data-market-selected-instrument-workspace-v1="true"') == 1
    assert not PARALLEL_WORKSPACE_RE.search(hero_text)


def test_selected_instrument_workspace_present_on_market(client_workspace_on: TestClient) -> None:
    html = _html(client_workspace_on)
    assert 'data-market-selected-instrument-workspace-v1="true"' in html
    assert 'data-market-selected-instrument="ETHUSDT"' in html
    assert 'data-market-workspace-hero-v1="true"' in html
    assert 'data-market-workspace-chart-v1="true"' in html
    assert 'data-market-workspace-ranking-context-v1="true"' in html
    assert 'data-market-workspace-f5-strip-v1="true"' in html
    assert 'data-market-workspace-contract-metadata-v1="true"' in html
    assert 'data-market-workspace-freshness-v1="true"' in html
    assert not FORBIDDEN_AUTHORITY_RE.search(html)
    assert not BITCOIN_RE.search(html)


def test_hero_chart_ranking_f5_consistent_symbol(client_workspace_on: TestClient) -> None:
    html = _html(client_workspace_on)
    assert "ETHUSDT" in html
    assert 'data-market-workspace-kpi-last-price-v1="true"' in html
    assert 'data-market-workspace-kpi-change-v1="true"' in html
    assert 'data-market-workspace-kpi-rank-v1="true"' in html
    assert 'data-market-workspace-kpi-score-v1="true"' in html
    assert 'data-market-workspace-f5-card-id="f1"' in html
    assert 'data-market-workspace-f5-card-id="f4"' in html
    assert 'data-market-workspace-volume-value-v1="true"' in html
    assert 'data-market-v0-in-chart-ohlc-candle="true"' in html


def test_workspace_view_model_consistency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    monkeypatch.setenv(OHLCV_ENV_ENABLED, "1")
    monkeypatch.setenv(OHLCV_ENV_BUNDLE_ROOT, str(OHLCV_FIXTURE))
    monkeypatch.setenv(F5_ENV_ENABLED, "1")
    monkeypatch.setenv(F5_ENV_BUNDLE_ROOT, str(F5_FIXTURE))

    sym, src, payload, unavailable = resolve_market_page_data(
        symbol="",
        timeframe="1d",
        limit=120,
        source="futures",
    )
    assert sym == "ETHUSDT"
    assert unavailable is False

    ctx = build_market_v0_page_template_context(
        get_project_status=lambda: {},
        symbol=sym,
        timeframe="1d",
        limit=120,
        source=src,
        payload=payload,
        data_unavailable=unavailable,
    )
    ws = ctx["selected_instrument_workspace"]
    assert ws["symbol"] == "ETHUSDT"
    assert ws["selected_instrument"] == "ETHUSDT"
    assert ws["ranking_rank"] == 1
    assert ws["ohlcv_status"] == "ready"
    assert ws["volume_status"] == "available"
    assert ws["view_only"] is True
    assert ws["read_only"] is True
    assert ctx["governed_top20"]["selected_symbol"] == "ETHUSDT"
    assert ctx["primary_values"]["symbol"] == "ETHUSDT"


def test_empty_ohlcv_explicit_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    monkeypatch.setenv(OHLCV_ENV_ENABLED, "1")
    monkeypatch.setenv(OHLCV_ENV_BUNDLE_ROOT, str(OHLCV_FIXTURE))
    monkeypatch.setenv(F5_ENV_ENABLED, "1")
    monkeypatch.setenv(F5_ENV_BUNDLE_ROOT, str(F5_FIXTURE))

    sym, src, payload, unavailable = resolve_market_page_data(
        symbol="SOLUSDT",
        timeframe="1h",
        limit=120,
        source="futures",
    )
    assert unavailable is True
    ws = build_market_selected_instrument_workspace_display_context(
        symbol=sym,
        source=src,
        primary_values={
            "symbol": sym,
            "status": "unavailable",
            "unavailable_reason": "futures_ohlcv_timeframe_mismatch",
            "change_status": "unavailable",
            "bars_returned": 0,
        },
        governed_top20={
            "rows": [],
            "top_n": 20,
            "stale": False,
            "stale_reason": "",
            "data_source": "fixture",
        },
        f5_dashboard={
            "gate_enabled": True,
            "display_status": "ready",
            "f1": {},
            "f2": {},
            "f3": {},
            "f4": {},
        },
        futures_ohlcv={"display_status": "ready", "stale": False},
        payload=payload,
        data_unavailable=unavailable,
    )
    assert ws["ohlcv_status"] in ("unavailable", "empty")


def test_malformed_ohlcv_explicit_state() -> None:
    ws = build_market_selected_instrument_workspace_display_context(
        symbol="ETHUSDT",
        source="futures",
        primary_values={
            "symbol": "ETHUSDT",
            "status": "unavailable",
            "unavailable_reason": "futures_ohlcv_malformed",
            "change_status": "unavailable",
            "bars_returned": 0,
        },
        governed_top20={
            "rows": [],
            "top_n": 20,
            "stale": False,
            "stale_reason": "",
            "data_source": "x",
        },
        f5_dashboard={
            "gate_enabled": True,
            "display_status": "builder_error",
            "f1": {},
            "f2": {},
            "f3": {},
            "f4": {},
        },
        futures_ohlcv={"display_status": "builder_error", "stale": False},
        payload={"bars_returned": 0, "meta": {}},
        data_unavailable=True,
    )
    assert ws["ohlcv_status"] == "malformed"
    assert ws["data_quality_status"] == "malformed"


def test_stale_ohlcv_explicit_state() -> None:
    ws = build_market_selected_instrument_workspace_display_context(
        symbol="ETHUSDT",
        source="futures",
        primary_values={
            "symbol": "ETHUSDT",
            "status": "unavailable",
            "unavailable_reason": "futures_ohlcv_stale",
            "change_status": "unavailable",
            "bars_returned": 0,
        },
        governed_top20={
            "rows": [],
            "top_n": 20,
            "stale": True,
            "stale_reason": "fixture",
            "data_source": "x",
        },
        f5_dashboard={
            "gate_enabled": True,
            "display_status": "ready",
            "f1": {},
            "f2": {},
            "f3": {},
            "f4": {},
        },
        futures_ohlcv={"display_status": "ready", "stale": True, "stale_reason": "fixture"},
        payload={"bars_returned": 0, "meta": {}},
        data_unavailable=True,
    )
    assert ws["ohlcv_status"] == "stale"
    assert ws["data_quality_status"] == "stale"


def test_no_parallel_chart_owner() -> None:
    chart_text = CHART_PARTIAL.read_text(encoding="utf-8")
    assert chart_text.count('data-market-chart-primary-v1="true"') == 1
    assert chart_text.count('data-market-workspace-chart-v1="true"') == 1


def test_workspace_determinism_triple_run(client_workspace_on: TestClient) -> None:
    snapshots = [_html(client_workspace_on) for _ in range(3)]
    assert snapshots[0] == snapshots[1] == snapshots[2]


def test_preview_matrix_at_least_eight_futures(client_workspace_on: TestClient) -> None:
    html = _html(client_workspace_on)
    matrix_rows = html.count('data-market-governed-matrix-row-v1="true"')
    assert matrix_rows >= 8
    assert 'data-market-futures-selector-selected-v1="true"' in html


def test_preview_chart_at_least_forty_bars(client_workspace_on: TestClient) -> None:
    html = _html(client_workspace_on)
    chart_section = html.split('data-market-workspace-chart-v1="true"', 1)[1]
    chart_section = chart_section.split('data-market-diagnostics-secondary-v1="true"', 1)[0]
    candles = chart_section.count('data-market-v0-in-chart-ohlc-candle="true"')
    volume_bars = chart_section.count('data-market-chart-volume-bar-v1="true"')
    assert candles >= 40
    assert volume_bars >= 40
    assert candles == volume_bars


def test_chart_axes_and_alignment(client_workspace_on: TestClient) -> None:
    html = _html(client_workspace_on)
    chart_section = html.split('data-market-workspace-chart-v1="true"', 1)[1]
    chart_section = chart_section.split('data-market-diagnostics-secondary-v1="true"', 1)[0]
    assert 'data-market-chart-price-axis-v1="true"' in chart_section
    assert 'data-market-chart-time-axis-v1="true"' in chart_section
    price_labels = chart_section.count('data-market-chart-price-label-v1="true"')
    time_labels = chart_section.count('data-market-chart-time-label-v1="true"')
    assert 5 <= price_labels <= 7
    assert time_labels >= 4
    candle_x = re.findall(r'data-market-chart-candle-x-v1="([0-9.]+)"', chart_section)
    volume_x = re.findall(r'data-market-chart-volume-x-v1="([0-9.]+)"', chart_section)
    assert len(candle_x) >= 40
    assert candle_x == volume_x


def test_kpi_hierarchy_and_f5_operator_status(client_workspace_on: TestClient) -> None:
    html = _html(client_workspace_on)
    assert 'data-market-workspace-kpi-band-v1="true"' in html
    assert 'data-market-workspace-kpi-primary-v1="true"' in html
    assert 'data-market-workspace-f5-operator-status-v1="true"' in html
    assert 'data-market-workspace-contract-unavailable-compact-v1="true"' in html
    assert 'data-market-workspace-visual-summary-v1="true"' in html


def test_chart_height_bounded(client_workspace_on: TestClient) -> None:
    html = _html(client_workspace_on)
    assert 'data-market-chart-height-v1="420"' in html
    assert "min-h-[60vh]" not in html


def test_no_bitcoin_spot_or_authority(client_workspace_on: TestClient) -> None:
    html = _html(client_workspace_on)
    assert not BITCOIN_RE.search(html)
    assert "BTC/EUR" not in html
    assert "spot-only" not in html.lower()
    assert not FORBIDDEN_AUTHORITY_RE.search(html)


def test_flat_price_single_bar_states() -> None:
    ws = build_market_selected_instrument_workspace_display_context(
        symbol="ETHUSDT",
        source="futures",
        primary_values={
            "symbol": "ETHUSDT",
            "status": "available",
            "last_close_display": "100.0",
            "change_status": "unavailable",
            "bars_returned": 1,
        },
        governed_top20={
            "rows": [],
            "top_n": 20,
            "stale": False,
            "stale_reason": "",
            "data_source": "x",
        },
        f5_dashboard={
            "gate_enabled": True,
            "display_status": "ready",
            "f1": {},
            "f2": {},
            "f3": {},
            "f4": {},
        },
        futures_ohlcv={"display_status": "ready", "stale": False},
        payload={
            "bars_returned": 1,
            "bars": [
                {
                    "ts": "2026-05-27T00:00:00+00:00",
                    "open": 100.0,
                    "high": 100.0,
                    "low": 100.0,
                    "close": 100.0,
                    "volume": 10.0,
                }
            ],
            "meta": {},
        },
        data_unavailable=False,
    )
    assert ws["visual_summary"]["implemented"] is True
    assert ws["visual_summary"]["visible_bar_count"] == 1
