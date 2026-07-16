"""Phase 3 Market Chart polish: contracts, real OHLCV, overlays, self-only safety."""

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
from src.webui.market_visual_operator_surface_v1.chart_display_v1 import (
    build_chart_display_v1,
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


@pytest.fixture()
def client_phase_3(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[TestClient]:
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


def _html(client: TestClient, path: str = "/market?timeframe=1d&limit=120") -> str:
    resp = client.get(path)
    assert resp.status_code == 200
    return resp.text


def test_chart_display_adapter_windows_and_gaps_unit() -> None:
    bars = [
        {
            "ts": "2030-01-01T00:00:00Z",
            "open": 1,
            "high": 2,
            "low": 0.5,
            "close": 1.5,
            "volume": 10,
        },
        {
            "ts": "2030-01-01T01:00:00Z",
            "open": 1.5,
            "high": 2,
            "low": 1,
            "close": 1.2,
            "volume": 11,
        },
        {
            "ts": "2030-01-01T04:00:00Z",
            "open": 1.2,
            "high": 2,
            "low": 1,
            "close": 1.8,
            "volume": 12,
        },
    ]
    vm = build_chart_display_v1(
        payload={
            "bars": bars,
            "bars_returned": 3,
            "symbol": "AAAUSDT",
            "source": "futures",
            "meta": {"data_source": "fixture_ohlcv", "freshness": "2030-01-01T04:00:00Z"},
        },
        primary_values={
            "symbol": "AAAUSDT",
            "timeframe": "1h",
            "generated_at_utc": "2030-01-01T04:00:00Z",
        },
        selected_instrument_workspace={"ohlcv_status": "ready"},
        futures_ohlcv={"source": "fixture_ohlcv", "stale": False},
        query={
            "symbol": "AAAUSDT",
            "source": "futures",
            "timeframe": "1h",
            "limit": 120,
            "top_n": 20,
        },
    )
    assert vm["candle_chart_real_data"] is True
    assert vm["volume_real_data"] is True
    assert vm["timezone"] == "UTC"
    assert vm["source"] == "fixture_ohlcv"
    assert vm["gap_count"] == 1
    assert 2 in vm["gap_indices"]
    assert vm["no_visual_interpolation"] is True
    labels = [w["label"] for w in vm["window_controls"]]
    assert labels == ["50", "120", "250", "ALL"]
    assert any("limit=120" in w["href"] for w in vm["window_controls"])
    assert any("limit=720" in w["href"] for w in vm["window_controls"] if w["label"] == "ALL")


def test_chart_display_stale_overlay_without_invented_bars() -> None:
    vm = build_chart_display_v1(
        payload={"bars": [], "bars_returned": 0, "symbol": "AAAUSDT", "meta": {}},
        primary_values={"symbol": "AAAUSDT", "timeframe": "1h"},
        selected_instrument_workspace={"ohlcv_status": "stale"},
        futures_ohlcv={"stale": True, "source": "fixture"},
        query={"symbol": "AAAUSDT", "source": "futures", "timeframe": "1h", "limit": 120},
    )
    assert vm["stale"] is True
    assert vm["overlay_state"] == "stale"
    assert vm["candle_chart_real_data"] is False
    assert vm["has_real_bars"] is False


def test_phase_3_markers_and_meta_in_html(client_phase_3: TestClient) -> None:
    body = _html(client_phase_3)
    assert 'data-market-phase-3-chart-v1="true"' in body
    assert 'data-market-phase-3-chart-meta-v1="true"' in body
    assert 'data-market-phase-3-meta-source-v1="true"' in body
    assert 'data-market-phase-3-meta-timezone-v1="true"' in body
    assert 'data-market-phase-3-meta-freshness-v1="true"' in body
    assert 'data-market-phase-3-meta-bars-v1="true"' in body
    assert 'data-market-phase-3-chart-windows-v1="true"' in body
    assert 'data-market-phase-3-chart-window-v1="120"' in body
    assert "UTC" in body
    assert "cdn.tailwindcss.com" not in body
    assert "cdn.jsdelivr.net" not in body
    assert "bitcoin" not in body.lower()


def test_phase_3_real_candles_and_tooltips(client_phase_3: TestClient) -> None:
    body = _html(client_phase_3)
    assert 'data-market-v0-in-chart-ohlc-candle="true"' in body
    assert 'data-market-chart-volume-bar-v1="true"' in body
    assert 'data-market-phase-3-candle-v1="true"' in body
    assert "<title>" in body
    assert "no interpolation" in body.lower() or "no-interpolation" in body


def test_phase_3_selected_instrument_sync(client_phase_3: TestClient) -> None:
    body = _html(client_phase_3)
    # fixture first symbol typically present in ranking + ohlcv
    assert 'data-market-phase-3-meta-symbol-v1="true"' in body
    assert 'data-market-trading-authority-v1="false"' in body
    assert re.search(r'type=["\']submit["\']', body, re.I) is None


def test_phase_3_preserves_above_fold_order(client_phase_3: TestClient) -> None:
    body = re.sub(r"<style>.*?</style>", "", _html(client_phase_3), flags=re.S)
    header_i = body.find('data-market-phase-1a-global-header-v1="true"')
    hero_i = body.find('data-market-phase-2-hero-v1="true"')
    chart_i = body.find('data-market-phase-1a-chart-above-fold-v1="true"')
    assert min(header_i, hero_i, chart_i) >= 0
    assert header_i < hero_i < chart_i


def test_phase_3_adapter_is_presentation_only() -> None:
    src = (
        project_root / "src" / "webui" / "market_visual_operator_surface_v1" / "chart_display_v1.py"
    ).read_text(encoding="utf-8")
    assert "presentation-only" in src
    assert "fetch_ohlcv" not in src
    assert "api_key" not in src.lower()
    assert "kraken" not in src.lower()


def test_phase_3_bar_count_and_timeframe_sync(client_phase_3: TestClient) -> None:
    body = _html(client_phase_3, "/market?timeframe=1d&limit=120")
    assert 'data-market-phase-3-meta-timeframe-v1="true"' in body
    assert ">1d<" in body or " TF </span> 1d" in body or "TF</span> 1d" in body
    m = re.search(r'data-market-chart-bar-count-v1="(\d+)"', body)
    assert m is not None
    rendered = int(m.group(1))
    assert rendered > 0
    meta_bars = re.search(
        r'data-market-phase-3-meta-bars-v1="true"[^>]*>.*?<span class="text-slate-500">Bars</span>\s*(\d+)',
        body,
        re.S,
    )
    assert meta_bars is not None
    assert int(meta_bars.group(1)) == rendered


def test_phase_3_missing_state_is_explicit(client_phase_3: TestClient) -> None:
    # Fixture OHLCV is 1d; 1h yields fail-closed empty chart (no synthetic bars).
    body = _html(client_phase_3, "/market?timeframe=1h&limit=120")
    assert 'data-market-phase-3-empty-chart-v1="true"' in body
    assert 'data-market-v0-in-chart-ohlc-candle="true"' not in body
    assert "Keine OHLCV-Bars" in body or "No embedded OHLCV" in body


def test_phase_3_stale_overlay_html(
    client_phase_3: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _stale_ctx() -> dict:
        return {
            "enabled": True,
            "available": False,
            "stale": True,
            "stale_reason": "fixture_stale_for_phase3",
            "source": "fixture_ohlcv",
            "generated_at_iso": "2030-01-01T00:00:00+00:00",
            "readmodel_id": "stale_fixture",
            "series": [],
        }

    monkeypatch.setattr(
        "src.webui.market_surface.build_market_futures_ohlcv_display_context",
        _stale_ctx,
    )
    body = _html(client_phase_3, "/market?timeframe=1d&limit=120")
    assert 'data-market-phase-3-overlay-state-v1="stale"' in body
    assert 'data-market-phase-3-stale-overlay-v1="true"' in body
    assert 'data-market-v0-in-chart-ohlc-candle="true"' not in body


def test_phase_3_no_spot_or_bitcoin_direction(client_phase_3: TestClient) -> None:
    body = _html(client_phase_3).lower()
    assert "spot-fallback" not in body
    assert "synthetic candle" not in body
    assert "bitcoin direction" not in body
    assert "cdn.jsdelivr" not in body
    assert "cdn.tailwindcss" not in body
