"""Contract tests: canonical /market short URL, title, real-values UI v1."""

from __future__ import annotations

import re
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


class TestCanonicalShortUrlDefaults:
    def test_market_without_query_uses_futures_first_defaults(self, client: TestClient) -> None:
        resp = client.get("/market")
        assert resp.status_code == 200
        body = resp.text
        assert f'data-market-source="{DEFAULT_SOURCE}"' in body
        assert DEFAULT_SOURCE == "futures"
        assert DEFAULT_SYMBOL == ""
        assert "BTC/EUR" not in body
        assert "BTC%2FEUR" not in body
        assert 'data-market-futures-first-v1="true"' in body
        assert DEFAULT_TIMEFRAME in body
        assert str(DEFAULT_LIMIT) in body

    def test_page_title_and_h1(self, client: TestClient) -> None:
        resp = client.get("/market")
        body = resp.text
        assert PAGE_TITLE in body
        assert f"<title>{PAGE_TITLE}</title>" in body
        assert 'data-market-page-title-v1="true"' in body
        assert f">{PAGE_TITLE}<" in body

    def test_primary_values_and_chart_before_diagnostics(self, client: TestClient) -> None:
        resp = client.get("/market")
        body = resp.text
        assert 'data-market-primary-market-values-v1="true"' in body
        assert 'data-market-chart-above-fold-v1="true"' in body
        assert 'data-market-operator-real-values-v1="true"' in body
        assert 'data-market-detail-click-required="false"' in body
        assert "Double-Play detail →" not in body
        values_pos = body.find('data-market-primary-market-values-v1="true"')
        chart_pos = body.find('data-market-chart-primary-v1="true"')
        diag_pos = body.find('data-market-diagnostics-secondary-v1="true"')
        assert values_pos >= 0 and chart_pos >= 0 and diag_pos >= 0
        assert values_pos < chart_pos < diag_pos

    def test_double_play_and_futures_summary_visible(self, client: TestClient) -> None:
        resp = client.get("/market")
        body = resp.text
        assert 'data-market-double-play-summary-visible-v1="true"' in body
        assert 'data-market-futures-summary-visible-v1="true"' in body

    def test_legacy_long_query_url_compatible(self, client: TestClient) -> None:
        resp = client.get(
            "/market",
            params={
                "source": "kraken",
                "symbol": "BTC/EUR",
                "timeframe": "1d",
                "limit": 120,
            },
        )
        assert resp.status_code == 200
        assert PAGE_TITLE in resp.text

    def test_dummy_explicit_synthetic_label(self, client: TestClient) -> None:
        resp = client.get(
            "/market",
            params={"source": "dummy", "symbol": "BTCUSDT", "limit": 20},
        )
        body = resp.text
        assert 'data-market-dummy-explicit-synthetic-v1="true"' in body
        assert 'data-market-source-kind="dummy-offline-synthetic"' in body
        assert "SYNTHETIC" in body or "synthetisch" in body.lower()

    def test_kraken_unavailable_honest_state(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from src.core.errors import ProviderError

        monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")

        def _fail(*_a, **_k):
            raise ProviderError("kraken unavailable in test")

        monkeypatch.setattr("src.data.kraken.fetch_ohlcv_df", _fail)
        with TestClient(create_app()) as client:
            resp = client.get("/market", params={"source": "kraken", "symbol": "BTC/USD"})
        assert resp.status_code == 200
        body = resp.text
        assert 'data-market-unavailable-compact-v1="true"' in body
        assert "unavailable" in body.lower()

    def test_legacy_double_play_redirect(self, client: TestClient) -> None:
        resp = client.get("/market/double-play", follow_redirects=False)
        assert resp.status_code == 302
        assert "/market" in resp.headers["location"]
        assert "#double-play" in resp.headers["location"]

    def test_legacy_futures_redirect(self, client: TestClient) -> None:
        resp = client.get("/market/futures", follow_redirects=False)
        assert resp.status_code == 302
        assert "/market" in resp.headers["location"]
        assert "#futures" in resp.headers["location"]

    def test_no_protected_imports_in_diff_scope(self) -> None:
        forbidden = re.compile(
            r"src/(execution|governance|risk|strategy)/",
            re.I,
        )
        touched = [
            project_root / "src/webui/market_surface.py",
        ]
        for path in touched:
            assert not forbidden.search(path.read_text(encoding="utf-8"))
