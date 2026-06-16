"""Permanent regression guards: futures-first /market default, no implicit spot fallback."""

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
from src.webui.market_surface import (
    DEFAULT_SOURCE,
    DEFAULT_SYMBOL,
    FORBIDDEN_IMPLICIT_SPOT_DEFAULT_SYMBOL,
    LEGACY_DEMO_SOURCES,
    build_futures_first_empty_payload,
    resolve_market_page_data,
)

MARKET_SURFACE_PATH = project_root / "src/webui/market_surface.py"
FORBIDDEN_DEFAULT_RE = re.compile(
    r'^DEFAULT_SYMBOL\s*=\s*["\']BTC/EUR["\']',
    re.MULTILINE,
)
IMPLICIT_KRAKEN_DEFAULT_RE = re.compile(
    r'DEFAULT_SOURCE[^=]*=\s*["\']kraken["\']',
)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.delenv("PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT", raising=False)

    kraken_mock = MagicMock(
        side_effect=AssertionError("fetch_ohlcv_df must not run on default /market")
    )
    monkeypatch.setattr("src.data.kraken.fetch_ohlcv_df", kraken_mock)

    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture()
def client_ranking_funnel_fixture_on(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED", "1")
    bundle = (
        project_root
        / "tests"
        / "fixtures"
        / "market_ranking_funnel_readmodel_v0"
        / "complete_minimal"
    ).resolve()
    monkeypatch.setenv("PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT", str(bundle))
    kraken_mock = MagicMock(
        side_effect=AssertionError("fetch_ohlcv_df must not run on futures-first /market")
    )
    monkeypatch.setattr("src.data.kraken.fetch_ohlcv_df", kraken_mock)
    with TestClient(create_app()) as test_client:
        yield test_client


def test_static_regression_guard_no_btc_eur_default_symbol() -> None:
    text = MARKET_SURFACE_PATH.read_text(encoding="utf-8")
    match = FORBIDDEN_DEFAULT_RE.search(text)
    assert match is None, (
        f"Forbidden spot default in {MARKET_SURFACE_PATH}: "
        f"DEFAULT_SYMBOL must not be {FORBIDDEN_IMPLICIT_SPOT_DEFAULT_SYMBOL!r}"
    )


def test_static_regression_guard_no_implicit_kraken_default_source() -> None:
    text = MARKET_SURFACE_PATH.read_text(encoding="utf-8")
    match = IMPLICIT_KRAKEN_DEFAULT_RE.search(text)
    assert match is None, (
        f"Forbidden implicit kraken default in {MARKET_SURFACE_PATH}: "
        "DEFAULT_SOURCE must not be 'kraken'"
    )


def test_default_constants_are_futures_first() -> None:
    assert DEFAULT_SOURCE == "futures"
    assert DEFAULT_SYMBOL == ""
    assert FORBIDDEN_IMPLICIT_SPOT_DEFAULT_SYMBOL == "BTC/EUR"
    assert "kraken" in LEGACY_DEMO_SOURCES
    assert "dummy" in LEGACY_DEMO_SOURCES


def test_market_default_is_futures_first_no_spot_ohlcv(client: TestClient) -> None:
    resp = client.get("/market")
    assert resp.status_code == 200
    body = resp.text
    assert 'data-market-futures-first-v1="true"' in body
    assert 'data-market-source="futures"' in body
    assert FORBIDDEN_IMPLICIT_SPOT_DEFAULT_SYMBOL not in body
    assert "BTC%2FEUR" not in body


def test_market_default_shows_futures_empty_state_without_snapshot(client: TestClient) -> None:
    body = client.get("/market").text
    assert 'data-market-futures-empty-state-v1="true"' in body
    assert 'data-market-futures-first-fail-closed-v1="true"' in body
    assert 'data-market-futures-data-unavailable-v1="true"' in body
    assert "Futures data unavailable" in body
    assert "No spot OHLCV" in body or "no spot" in body.lower()


def test_market_default_no_synthetic_fallback(client: TestClient) -> None:
    body = client.get("/market").text
    assert 'data-market-dummy-explicit-synthetic-v1="true"' not in body
    assert 'data-market-source-kind="dummy-offline-synthetic"' not in body


def test_market_ranking_funnel_top20_symbol_without_spot_fallback(
    client_ranking_funnel_fixture_on: TestClient,
) -> None:
    body = client_ranking_funnel_fixture_on.get("/market").text
    assert 'data-market-source="futures"' in body
    assert "ETHUSDT" in body
    assert FORBIDDEN_IMPLICIT_SPOT_DEFAULT_SYMBOL not in body
    assert 'data-market-v0-ranking-funnel-has-rows-v0="true"' in body


def test_api_market_ohlcv_default_rejects_futures_ssr_only(client: TestClient) -> None:
    resp = client.get("/api/market/ohlcv")
    assert resp.status_code == 422
    assert "futures" in resp.json()["detail"].lower()


def test_api_market_ohlcv_legacy_requires_explicit_symbol(client: TestClient) -> None:
    resp = client.get("/api/market/ohlcv", params={"source": "dummy"})
    assert resp.status_code == 422
    assert "symbol" in resp.json()["detail"].lower()


def test_demo_dummy_explicit_opt_in_only(client: TestClient) -> None:
    resp = client.get("/market", params={"source": "dummy", "symbol": "ETHUSDT", "limit": 20})
    assert resp.status_code == 200
    body = resp.text
    assert 'data-market-dummy-explicit-synthetic-v1="true"' in body
    assert FORBIDDEN_IMPLICIT_SPOT_DEFAULT_SYMBOL not in body


def test_resolve_market_page_data_fail_closed_without_ranking_snapshot() -> None:
    sym, src, payload, unavailable = resolve_market_page_data(
        symbol=None,
        timeframe="1d",
        limit=120,
        source=None,
    )
    assert src == "futures"
    assert sym == ""
    assert unavailable is True
    assert payload["bars_returned"] == 0
    assert payload["meta"]["futures_empty_state"] is True
    assert payload["meta"]["fail_closed"] is True


def test_build_futures_first_empty_payload_contract() -> None:
    payload = build_futures_first_empty_payload(
        symbol="",
        timeframe="1d",
        limit=120,
        unavailable_reason="futures_snapshot_unavailable",
    )
    assert payload["source"] == "futures"
    assert payload["bars"] == []
    assert payload["meta"]["source_mode"] == "futures_read_only_ssr"
