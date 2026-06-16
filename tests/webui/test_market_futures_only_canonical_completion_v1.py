"""Canonical futures-only /market completion contracts: selector, Top50, OHLCV, single-owner guards."""

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
from src.webui.market_futures_ohlcv_runtime_v0 import (
    ENV_BUNDLE_ROOT as OHLCV_ENV_BUNDLE_ROOT,
    ENV_ENABLED as OHLCV_ENV_ENABLED,
)
from src.webui.market_ranking_funnel_runtime_v0 import (
    ENV_BUNDLE_ROOT as RANKING_ENV_BUNDLE_ROOT,
    ENV_ENABLED as RANKING_ENV_ENABLED,
)
from src.webui.market_surface import (
    ALLOWED_TOP_N_VALUES,
    CANONICAL_CHART_OWNER,
    CANONICAL_F5_METADATA_OWNER,
    CANONICAL_FUTURES_OHLCV_OWNER,
    CANONICAL_FUTURES_RANKING_OWNER,
    CANONICAL_FUTURES_UNIVERSE_OWNER,
    CANONICAL_MARKET_ROUTE,
    CANONICAL_MARKET_ROUTE_OWNER,
    CANONICAL_MARKET_TEMPLATE_OWNER,
    CANONICAL_MARKET_VIEWMODEL_OWNER,
    CANONICAL_SELECTED_INSTRUMENT_OWNER,
    CANONICAL_TOP_N_OWNER,
    DEFAULT_TOP_N,
    FORBIDDEN_IMPLICIT_SPOT_DEFAULT_SYMBOL,
    build_market_governed_top20_display_context,
    build_market_ranking_funnel_display_context,
    collect_governed_futures_symbols,
    is_valid_governed_futures_symbol,
    normalize_top_n,
    resolve_market_page_data,
)
from src.webui.futures_read_only_market_dashboard_runtime_v0 import (
    ENV_BUNDLE_ROOT as F5_ENV_BUNDLE_ROOT,
    ENV_ENABLED as F5_ENV_ENABLED,
    build_futures_read_only_market_dashboard_display_context,
)

RANKING_FIXTURE = (
    project_root / "tests" / "fixtures" / "market_ranking_funnel_readmodel_v0" / "complete_minimal"
).resolve()
RANKING_TOP50_FIXTURE = (
    project_root / "tests" / "fixtures" / "market_ranking_funnel_readmodel_v0" / "top50_minimal"
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
APP_PATH = project_root / "src" / "webui" / "app.py"
MARKET_SURFACE_PATH = project_root / "src" / "webui" / "market_surface.py"

FORBIDDEN_PARALLEL_ROUTE_RE = re.compile(
    r'@(?:app|router)\.(?:get|post|put|delete|patch)\(\s*["\']/(?:real-market|market-v2|market-v3|futures-dashboard)["\']',
    re.MULTILINE,
)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.delenv(RANKING_ENV_ENABLED, raising=False)
    monkeypatch.delenv(RANKING_ENV_BUNDLE_ROOT, raising=False)
    monkeypatch.delenv(OHLCV_ENV_ENABLED, raising=False)
    monkeypatch.delenv(OHLCV_ENV_BUNDLE_ROOT, raising=False)
    monkeypatch.delenv(F5_ENV_ENABLED, raising=False)
    monkeypatch.delenv(F5_ENV_BUNDLE_ROOT, raising=False)
    kraken_mock = MagicMock(
        side_effect=AssertionError("fetch_ohlcv_df must not run on futures-first /market")
    )
    monkeypatch.setattr("src.data.kraken.fetch_ohlcv_df", kraken_mock)
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture()
def client_full_wiring_on(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
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


def test_single_route_contract_canonical_market_only() -> None:
    app_text = APP_PATH.read_text(encoding="utf-8")
    assert FORBIDDEN_PARALLEL_ROUTE_RE.search(app_text) is None
    assert CANONICAL_MARKET_ROUTE == "/market"


def test_single_owner_contract_constants() -> None:
    assert CANONICAL_MARKET_ROUTE_OWNER == "src/webui/market_surface.py"
    assert CANONICAL_MARKET_VIEWMODEL_OWNER == CANONICAL_MARKET_ROUTE_OWNER
    assert CANONICAL_MARKET_TEMPLATE_OWNER.endswith("market_v0.html")
    assert CANONICAL_FUTURES_UNIVERSE_OWNER.endswith("market_ranking_funnel_runtime_v0.py")
    assert CANONICAL_FUTURES_RANKING_OWNER == CANONICAL_FUTURES_UNIVERSE_OWNER
    assert CANONICAL_TOP_N_OWNER == CANONICAL_MARKET_ROUTE_OWNER
    assert CANONICAL_F5_METADATA_OWNER.endswith("futures_read_only_market_dashboard_runtime_v0.py")
    assert CANONICAL_SELECTED_INSTRUMENT_OWNER == CANONICAL_MARKET_ROUTE_OWNER
    assert CANONICAL_FUTURES_OHLCV_OWNER.endswith("market_futures_ohlcv_runtime_v0.py")
    assert CANONICAL_CHART_OWNER.endswith("market_primary_close_chart_v1.html")


def test_no_parallel_build_guard_no_second_market_surface_module() -> None:
    candidates = list((project_root / "src" / "webui").glob("market_surface*.py"))
    assert candidates == [MARKET_SURFACE_PATH]


def test_futures_only_no_btc_eur_in_default_path(client: TestClient) -> None:
    body = _html(client)
    assert FORBIDDEN_IMPLICIT_SPOT_DEFAULT_SYMBOL not in body
    assert 'data-market-source="futures"' in body


def test_top_n_default_is_20(client_full_wiring_on: TestClient) -> None:
    body = _html(client_full_wiring_on)
    assert 'data-market-governed-top-n="20"' in body
    assert 'data-market-governed-top20-toggle-v1="true"' in body


def test_top50_selectable_and_not_padded(client_full_wiring_on: TestClient) -> None:
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_TOP50_FIXTURE))
    monkeypatch.setenv(OHLCV_ENV_ENABLED, "1")
    monkeypatch.setenv(OHLCV_ENV_BUNDLE_ROOT, str(OHLCV_FIXTURE))
    monkeypatch.setenv(F5_ENV_ENABLED, "1")
    monkeypatch.setenv(F5_ENV_BUNDLE_ROOT, str(F5_FIXTURE))
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    with TestClient(create_app()) as test_client:
        body = _html(test_client, "/market?top_n=50")
    assert 'data-market-governed-top-n="50"' in body
    assert 'data-market-governed-top50-toggle-v1="true"' in body
    assert 'data-market-governed-top20-row-count="5"' in body
    assert "no padding to 50" in body


def test_invalid_top_n_fail_closed_to_default(client: TestClient) -> None:
    for bad in ("99", "abc", "0", "-1", "null", "99999"):
        resp = client.get("/market", params={"top_n": bad})
        assert resp.status_code == 200
        assert 'data-market-governed-top-n="20"' in resp.text
    resp_blank = client.get("/market?top_n=")
    assert resp_blank.status_code == 200
    assert 'data-market-governed-top-n="20"' in resp_blank.text


def test_futures_selector_links_and_selected_highlight(client_full_wiring_on: TestClient) -> None:
    body = _html(client_full_wiring_on, "/market?symbol=ETHUSDT")
    assert 'data-market-futures-selector-v1="true"' in body
    assert 'data-market-futures-selector-link-v1="true"' in body
    assert 'data-market-futures-selector-selected-v1="true"' in body
    assert "href=" in body and "symbol=ETHUSDT" in body


def test_invalid_futures_symbol_fail_closed(client_full_wiring_on: TestClient) -> None:
    body = _html(client_full_wiring_on, "/market?symbol=DOGEUSDT")
    assert 'data-market-futures-selector-invalid-v1="true"' in body
    assert "Invalid futures instrument selection" in body


def test_futures_ohlcv_chart_wired_with_fixture(client_full_wiring_on: TestClient) -> None:
    body = _html(client_full_wiring_on, "/market?symbol=ETHUSDT")
    assert 'data-market-futures-ohlcv-wired-v1="true"' in body
    assert 'data-market-futures-chart-complete-v1="true"' in body
    assert 'data-market-chart-status="ready"' in body
    assert 'data-market-v0-in-chart-ohlc-svg-root="true"' in body
    assert 'data-market-futures-ohlcv-not-wired-v1="true"' not in body


def test_futures_ohlcv_missing_symbol_explicit(client_full_wiring_on: TestClient) -> None:
    body = _html(client_full_wiring_on, "/market?symbol=SOLUSDT")
    assert 'data-market-futures-ohlcv-wired-v1="true"' in body
    assert 'data-market-futures-ohlcv-not-wired-v1="true"' not in body
    assert 'data-market-futures-selector-selected-v1="true"' in body


def test_futures_ohlcv_malformed_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bundle = tmp_path / "bad_ohlcv"
    bundle.mkdir()
    (bundle / "futures_ohlcv.json").write_text("{bad", encoding="utf-8")
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    monkeypatch.setenv(OHLCV_ENV_ENABLED, "1")
    monkeypatch.setenv(OHLCV_ENV_BUNDLE_ROOT, str(bundle))
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    with TestClient(create_app()) as test_client:
        body = _html(test_client, "/market?symbol=ETHUSDT")
    assert 'data-market-futures-ohlcv-malformed-v1="true"' in body


def test_end_to_end_contract_no_network(client_full_wiring_on: TestClient) -> None:
    body = _html(client_full_wiring_on)
    assert 'data-market-readonly="true"' in body or 'data-market-non-authorizing="true"' in body
    assert 'data-market-trading-authority-v1="false"' in body
    assert 'data-f5-market-dashboard-no-authority="true"' in body
    assert FORBIDDEN_IMPLICIT_SPOT_DEFAULT_SYMBOL not in body


def test_normalize_top_n_contract() -> None:
    assert normalize_top_n(None) == DEFAULT_TOP_N
    assert normalize_top_n(20) == 20
    assert normalize_top_n(50) == 50
    assert ALLOWED_TOP_N_VALUES == (20, 50)


def test_governed_symbol_validation_unit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    ranking = build_market_ranking_funnel_display_context()
    symbols = collect_governed_futures_symbols(ranking)
    assert "ETHUSDT" in symbols
    assert is_valid_governed_futures_symbol("ETHUSDT", ranking)
    assert not is_valid_governed_futures_symbol("BTC/EUR", ranking)
    assert not is_valid_governed_futures_symbol("DOGEUSDT", ranking)


def test_resolve_market_page_data_futures_ohlcv_unit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    monkeypatch.setenv(OHLCV_ENV_ENABLED, "1")
    monkeypatch.setenv(OHLCV_ENV_BUNDLE_ROOT, str(OHLCV_FIXTURE))
    sym, src, payload, unavailable = resolve_market_page_data(
        symbol="ETHUSDT",
        timeframe="1d",
        limit=120,
        source="futures",
    )
    assert src == "futures"
    assert sym == "ETHUSDT"
    assert unavailable is False
    assert payload["bars_returned"] == 45


def test_completion_contract_determinism_three_runs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    monkeypatch.setenv(OHLCV_ENV_ENABLED, "1")
    monkeypatch.setenv(OHLCV_ENV_BUNDLE_ROOT, str(OHLCV_FIXTURE))
    monkeypatch.setenv(F5_ENV_ENABLED, "1")
    monkeypatch.setenv(F5_ENV_BUNDLE_ROOT, str(F5_FIXTURE))

    def _snapshot() -> dict[str, object]:
        ranking = build_market_ranking_funnel_display_context()
        f5 = build_futures_read_only_market_dashboard_display_context()
        ctx = build_market_governed_top20_display_context(
            ranking_funnel=ranking,
            f5_dashboard=f5,
            selected_symbol="ETHUSDT",
            top_n=20,
        )
        sym, _, payload, unavailable = resolve_market_page_data(
            symbol="ETHUSDT",
            timeframe="1d",
            limit=120,
            source="futures",
        )
        return {
            "row_count": ctx["row_count"],
            "selected": ctx["selected_symbol"],
            "bars": payload["bars_returned"],
            "unavailable": unavailable,
        }

    first = _snapshot()
    second = _snapshot()
    third = _snapshot()
    assert first == second == third
