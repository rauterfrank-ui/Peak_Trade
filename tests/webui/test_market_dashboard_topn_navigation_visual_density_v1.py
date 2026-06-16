"""Top-N navigation contract and visual-density markers on canonical GET /market."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from html import unescape
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
    CANONICAL_MARKET_ROUTE,
    CANONICAL_MARKET_TEMPLATE_OWNER,
    CANONICAL_TOP_N_OWNER,
    DEFAULT_TOP_N,
    build_market_canonical_href,
    build_market_top_n_toggle_href,
    build_market_view_query_extras,
    normalize_top_n,
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

FORBIDDEN_AUTHORITY_RE = re.compile(
    r'(?:type=["\']submit["\']|data-market-(?:order|execute|arm))',
    re.IGNORECASE,
)
SIDE_ROUTE_RE = re.compile(r'href=["\']/(?:market/50|top50|market/top50)', re.IGNORECASE)
TOP_N_HREF_RE = re.compile(
    r'href=["\'](/market\?[^"\']*top_n=(?:20|50)[^"\']*)["\']', re.IGNORECASE
)


@pytest.fixture()
def client_full(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
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
    assert resp.status_code == 200, f"{path} -> {resp.status_code}"
    return resp.text


def _extract_top_n_hrefs(body: str) -> dict[int, str]:
    hrefs: dict[int, str] = {}
    for match in TOP_N_HREF_RE.finditer(body):
        href = unescape(match.group(1))
        if "top_n=20" in href:
            hrefs[20] = href
        if "top_n=50" in href:
            hrefs[50] = href
    return hrefs


def test_top_n_owner_constants() -> None:
    assert CANONICAL_TOP_N_OWNER.endswith("market_surface.py")
    assert CANONICAL_MARKET_ROUTE == "/market"
    assert CANONICAL_MARKET_TEMPLATE_OWNER.endswith("market_v0.html")


def test_normalize_top_n_fail_closed() -> None:
    assert normalize_top_n(None) == DEFAULT_TOP_N
    assert normalize_top_n(20) == 20
    assert normalize_top_n(50) == 50
    assert normalize_top_n("50") == 50
    for bad in (99, "abc", 0, -1, "null", 99999, ""):
        assert normalize_top_n(bad) == DEFAULT_TOP_N


def test_toggle_hrefs_are_canonical_absolute_market_urls() -> None:
    extras = build_market_view_query_extras(
        matrix_filter_symbol="ETH",
        matrix_filter_f5_status="futures_metadata_ready",
        matrix_filter_freshness="fresh",
        matrix_sort_field="rank",
        matrix_sort_direction="asc",
    )
    top20 = build_market_top_n_toggle_href(
        top_n=20,
        symbol="ETHUSDT",
        source="futures",
        timeframe="1d",
        limit=120,
        extras=extras,
    )
    top50 = build_market_top_n_toggle_href(
        top_n=50,
        symbol="ETHUSDT",
        source="futures",
        timeframe="1d",
        limit=120,
        extras=extras,
    )
    assert top20.startswith("/market?")
    assert top50.startswith("/market?")
    assert "top_n=20" in top20
    assert "top_n=50" in top50
    assert "symbol=ETHUSDT" in top20
    assert "matrix_filter_symbol=ETH" in top50
    assert "matrix_sort_field=rank" in top50


def test_top20_and_top50_requests_return_same_template(client_full: TestClient) -> None:
    body_default = _html(client_full)
    body20 = _html(client_full, "/market?top_n=20")
    body50 = _html(client_full, "/market?top_n=50")
    for marker in (
        'data-market-terminal-shell-v1="true"',
        'data-market-governed-top20-primary-v1="true"',
        'data-market-selected-instrument-workspace-v1="true"',
    ):
        assert marker in body_default
        assert marker in body20
        assert marker in body50


def test_rendered_toggle_hrefs_and_active_state(client_full: TestClient) -> None:
    body20 = _html(client_full, "/market?symbol=ETHUSDT&top_n=20")
    hrefs20 = _extract_top_n_hrefs(body20)
    assert hrefs20[20].startswith("/market?")
    assert hrefs20[50].startswith("/market?")
    assert "symbol=ETHUSDT" in hrefs20[50]
    assert 'data-market-governed-top-n="20"' in body20
    assert 'aria-current="page"' in body20
    assert 'data-market-governed-top20-toggle-v1="true"' in body20

    body50 = _html(client_full, "/market?symbol=ETHUSDT&top_n=50")
    assert 'data-market-governed-top-n="50"' in body50
    assert 'data-market-governed-top50-toggle-v1="true"' in body50
    assert 'aria-current="page"' in body50
    assert SIDE_ROUTE_RE.search(body50) is None


def test_query_preservation_in_top50_toggle_href(client_full: TestClient) -> None:
    path = (
        "/market?symbol=SOLUSDT&top_n=20"
        "&matrix_filter_symbol=SOL"
        "&matrix_filter_f5_status=futures_metadata_ready"
        "&matrix_filter_freshness=fresh"
        "&matrix_sort_field=symbol"
        "&matrix_sort_direction=desc"
    )
    body = _html(client_full, path)
    hrefs = _extract_top_n_hrefs(body)
    top50 = hrefs[50]
    assert "symbol=SOLUSDT" in top50
    assert "matrix_filter_symbol=SOL" in top50
    assert "matrix_filter_f5_status=futures_metadata_ready" in top50
    assert "matrix_filter_freshness=fresh" in top50
    assert "matrix_sort_field=symbol" in top50
    assert "matrix_sort_direction=desc" in top50


def test_invalid_top_n_http_200_fail_closed(client_full: TestClient) -> None:
    for bad in ("99", "abc", "-1", "0", "99999"):
        body = _html(client_full, f"/market?top_n={bad}")
        assert 'data-market-governed-top-n="20"' in body


def test_no_padding_and_no_bitcoin(client_full: TestClient) -> None:
    body = _html(client_full, "/market?top_n=50")
    assert 'data-market-governed-top20-row-count="8"' in body
    assert "no padding to 50" in body
    assert "BTCUSDT" not in body
    assert "XBT" not in body
    assert FORBIDDEN_AUTHORITY_RE.search(body) is None


def test_visual_density_markers_present(client_full: TestClient) -> None:
    body = _html(client_full)
    assert 'data-market-operator-diagnostics-compact-v1="true"' in body
    assert 'data-market-governed-topn-toolbar-v1="true"' in body
    assert 'data-market-workspace-kpi-band-v1="true"' in body
    assert 'data-market-workspace-ranking-f5-compact-v1="true"' in body
    assert 'data-market-chart-primary-v2="true"' in body


def _stable_topn_markers(body: str) -> tuple[str, ...]:
    hrefs = _extract_top_n_hrefs(body)
    return (
        body.count('data-market-governed-top-n="20"'),
        body.count('data-market-governed-top-n="50"'),
        hrefs.get(20, ""),
        hrefs.get(50, ""),
        'aria-current="page"' in body,
        body.count('data-market-governed-matrix-row-v1="true"'),
    )


def test_determinism_top20_top50_and_query_preservation(client_full: TestClient) -> None:
    paths = [
        "/market",
        "/market?top_n=20",
        "/market?top_n=50",
        "/market?symbol=ETHUSDT&top_n=50&matrix_filter_symbol=ETH",
    ]
    for path in paths:
        markers = [_stable_topn_markers(_html(client_full, path)) for _ in range(3)]
        assert markers[0] == markers[1] == markers[2]
        _path, href20, href50 = path, markers[0][2], markers[0][3]
        if href20:
            assert href20.startswith("/market?")
        if href50:
            assert href50.startswith("/market?")


def test_build_market_canonical_href_matches_route() -> None:
    href = build_market_canonical_href(
        source="futures",
        symbol="ETHUSDT",
        timeframe="1d",
        limit=120,
        top_n=50,
        include_default_top_n=True,
    )
    assert href == build_market_top_n_toggle_href(
        top_n=50,
        symbol="ETHUSDT",
        source="futures",
        timeframe="1d",
        limit=120,
    )
