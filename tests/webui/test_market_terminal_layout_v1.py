"""Contract tests: Market Terminal layout v1 — trading-app shell on GET /market."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

from src.webui.app import create_app
from src.webui.market_surface import (
    DEFAULT_LIMIT,
    DEFAULT_SOURCE,
    DEFAULT_SYMBOL,
    DEFAULT_TIMEFRAME,
    PAGE_TITLE,
)


def _sample_ohlcv_df(n: int = 5) -> pd.DataFrame:
    idx = pd.date_range("2026-01-01", periods=n, freq="1D", tz="UTC")
    return pd.DataFrame(
        {
            "open": [100.0 + i for i in range(n)],
            "high": [101.0 + i for i in range(n)],
            "low": [99.0 + i for i in range(n)],
            "close": [100.5 + i for i in range(n)],
            "volume": [10.0 + i for i in range(n)],
        },
        index=idx,
    )


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.delenv("PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_MARKET_SINGLE_PAGE_CONSOLIDATION_V1_ENABLED", raising=False)

    def _fake_fetch(*_a, **_k):
        return _sample_ohlcv_df(10)

    monkeypatch.setattr("src.data.kraken.fetch_ohlcv_df", _fake_fetch)

    with TestClient(create_app()) as test_client:
        yield test_client


def test_market_terminal_layout_markers(client: TestClient) -> None:
    html = client.get("/market").text
    assert PAGE_TITLE in html
    assert 'data-market-terminal-v1="true"' in html
    assert 'data-market-terminal-layout-v1="true"' in html
    assert 'data-market-trading-app-terminal-v1="true"' in html
    assert 'data-market-chart-dominant-v1="true"' in html
    assert 'data-market-metrics-above-fold-v1="true"' in html
    assert 'data-market-detail-click-required="false"' in html


def test_primary_chart_before_diagnostics_drawer(client: TestClient) -> None:
    html = client.get("/market").text
    chart_pos = html.find('data-market-chart-dominant-v1="true"')
    drawer_pos = html.find('data-market-diagnostics-drawer-v1="true"')
    assert chart_pos >= 0 and drawer_pos >= 0
    assert chart_pos < drawer_pos


def test_compact_panels_present(client: TestClient) -> None:
    html = client.get("/market").text
    assert 'data-market-double-play-compact-v1="true"' in html
    assert 'data-market-futures-compact-v1="true"' in html
    assert 'data-market-safety-rail-compact-v1="true"' in html
    assert 'data-market-terminal-watchlist-v1="true"' in html


def test_defaults_visible(client: TestClient) -> None:
    html = client.get("/market").text
    assert f'data-market-source="{DEFAULT_SOURCE}"' in html
    assert DEFAULT_SOURCE == "futures"
    assert "BTC/EUR" not in html
    assert 'data-market-futures-first-v1="true"' in html
    assert DEFAULT_TIMEFRAME in html
    assert str(DEFAULT_LIMIT) in html


def test_no_primary_detail_click_cta(client: TestClient) -> None:
    html = client.get("/market").text
    assert "Double-Play detail →" not in html
    assert "Jetzt traden" not in html


def test_diagnostics_collapsed_secondary(client: TestClient) -> None:
    html = client.get("/market").text
    assert 'data-market-diagnostics-drawer-v1="true"' in html
    assert "Diagnostics / internals" in html


def test_dummy_clearly_labeled(client: TestClient) -> None:
    html = client.get("/market", params={"source": "dummy"}).text
    assert 'data-market-dummy-explicit-synthetic-v1="true"' in html
    assert "SYNTHETIC" in html or "synthetisch" in html.lower()
