"""Matrix URL view-state contract on canonical GET /market (SSR, view-only)."""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from html import unescape
from pathlib import Path
from unittest.mock import MagicMock
from urllib.parse import parse_qs, urlparse

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
    AVAILABLE_SORT_FIELDS,
    CANONICAL_FILTER_OWNER,
    CANONICAL_MARKET_ROUTE,
    CANONICAL_MATRIX_TEMPLATE_OWNER,
    CANONICAL_SORT_OWNER,
    CANONICAL_URL_BUILDER_OWNER,
    DEFAULT_TOP_N,
    MATRIX_VIEW_QUERY_PARAM_NAMES,
    apply_matrix_view_state,
    build_market_canonical_href,
    build_market_governed_top20_display_context,
    build_market_matrix_reset_filters_href,
    build_market_matrix_reset_sort_href,
    build_market_matrix_sort_toggle_href,
    build_market_matrix_view_href,
    build_market_view_query_extras,
    normalize_matrix_view_extras,
    normalize_top_n,
    MarketViewQueryExtras,
    resolve_matrix_sort_state,
    sort_matrix_rows,
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
SCRIPT_BLOCK_RE = re.compile(r"<script\b", re.IGNORECASE)


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


def _governed_ctx(monkeypatch: pytest.MonkeyPatch, **kwargs: object) -> dict[str, object]:
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    monkeypatch.setenv(OHLCV_ENV_ENABLED, "1")
    monkeypatch.setenv(OHLCV_ENV_BUNDLE_ROOT, str(OHLCV_FIXTURE))
    monkeypatch.setenv(F5_ENV_ENABLED, "1")
    monkeypatch.setenv(F5_ENV_BUNDLE_ROOT, str(F5_FIXTURE))
    from src.webui.futures_read_only_market_dashboard_runtime_v0 import (
        build_futures_read_only_market_dashboard_display_context,
    )
    from src.webui.market_futures_ohlcv_runtime_v0 import build_market_futures_ohlcv_display_context
    from src.webui.market_ranking_funnel_runtime_v0 import (
        build_market_ranking_funnel_display_context,
    )

    return build_market_governed_top20_display_context(
        ranking_funnel=build_market_ranking_funnel_display_context(),
        f5_dashboard=build_futures_read_only_market_dashboard_display_context(),
        futures_ohlcv=build_market_futures_ohlcv_display_context(),
        **kwargs,
    )


def test_canonical_owner_constants() -> None:
    assert CANONICAL_URL_BUILDER_OWNER.endswith("market_surface.py")
    assert CANONICAL_FILTER_OWNER.endswith("market_surface.py")
    assert CANONICAL_SORT_OWNER.endswith("market_surface.py")
    assert CANONICAL_MATRIX_TEMPLATE_OWNER.endswith("market_governed_top20_primary_v1.html")
    assert MATRIX_VIEW_QUERY_PARAM_NAMES == (
        "matrix_filter_symbol",
        "matrix_filter_f5_status",
        "matrix_filter_freshness",
        "matrix_sort_field",
        "matrix_sort_direction",
    )


def test_canonical_href_deterministic_order_and_encoding() -> None:
    extras = build_market_view_query_extras(
        matrix_filter_symbol="ETH/US",
        matrix_filter_freshness="fresh",
        matrix_sort_field="score",
        matrix_sort_direction="desc",
    )
    href = build_market_canonical_href(
        source="futures",
        symbol="ETHUSDT",
        timeframe="1d",
        limit=120,
        top_n=50,
        extras=extras,
        include_default_top_n=True,
    )
    assert href.startswith("/market?")
    assert href == build_market_canonical_href(
        source="futures",
        symbol="ETHUSDT",
        timeframe="1d",
        limit=120,
        top_n=50,
        extras=extras,
        include_default_top_n=True,
    )
    assert "matrix_filter_symbol=ETH%2FUS" in href or "matrix_filter_symbol=ETH/US" in href


def test_invalid_matrix_values_fail_closed() -> None:
    normalized = normalize_matrix_view_extras(
        build_market_view_query_extras(
            matrix_filter_f5_status="not_a_real_status",
            matrix_filter_freshness="ancient",
            matrix_sort_field="free_field",
            matrix_sort_direction="sideways",
        ),
        allowed_f5_statuses=("futures_metadata_partial",),
    )
    assert normalized.matrix_filter_f5_status == ""
    assert normalized.matrix_filter_freshness == ""
    assert normalized.matrix_sort_field == ""
    assert normalized.matrix_sort_direction == ""


def test_top_n_invalid_values_fail_closed() -> None:
    for bad in (99, "abc", 0, -1, "null", 99999):
        assert normalize_top_n(bad) == DEFAULT_TOP_N


def test_symbol_filter_ssr_reduces_visible_rows(client_full: TestClient) -> None:
    body = _html(client_full, "/market?matrix_filter_symbol=ZZZZNOTFOUND")
    assert 'data-market-matrix-visible-count-v1="0"' in body
    assert 'data-market-governed-matrix-no-results-v1="true"' in body
    assert "hidden" not in body.split('data-market-governed-matrix-no-results-v1="true"')[1][:80]


def test_freshness_filter_ssr(client_full: TestClient) -> None:
    body = _html(client_full, "/market?matrix_filter_freshness=fresh")
    assert 'data-market-matrix-filter-freshness-v1="true"' in body
    assert 'aria-current="true"' in body
    assert 'data-market-matrix-visible-count-v1="8"' in body


def test_sort_by_score_desc_ssr(client_full: TestClient) -> None:
    body = _html(client_full, "/market?matrix_sort_field=score&matrix_sort_direction=desc")
    first_row = body.split('data-market-governed-matrix-row-v1="true"', 1)[1]
    assert "ETHUSDT" in first_row or "SOLUSDT" in first_row
    assert 'data-market-matrix-sort-field="score"' in body
    assert 'href="/market?' in body


def test_reset_filters_and_sort_hrefs_preserve_other_state() -> None:
    extras = build_market_view_query_extras(
        matrix_filter_symbol="ETH",
        matrix_filter_freshness="fresh",
        matrix_sort_field="symbol",
        matrix_sort_direction="desc",
    )
    reset_filters = build_market_matrix_reset_filters_href(
        source="futures",
        symbol="ETHUSDT",
        timeframe="1d",
        limit=120,
        top_n=50,
        extras=extras,
    )
    assert "matrix_filter_symbol=" not in reset_filters
    assert "matrix_sort_field=symbol" in reset_filters
    reset_sort = build_market_matrix_reset_sort_href(
        source="futures",
        symbol="ETHUSDT",
        timeframe="1d",
        limit=120,
        top_n=50,
        extras=extras,
    )
    assert "matrix_filter_symbol=ETH" in reset_sort
    assert "matrix_sort_field=" not in reset_sort


def test_sort_toggle_href_flips_direction() -> None:
    extras = build_market_view_query_extras(
        matrix_sort_field="score",
        matrix_sort_direction="desc",
    )
    toggled = build_market_matrix_sort_toggle_href(
        field="score",
        source="futures",
        symbol="ETHUSDT",
        timeframe="1d",
        limit=120,
        top_n=20,
        extras=extras,
        active_sort_field="score",
        active_sort_direction="desc",
    )
    assert "matrix_sort_field=score" in toggled
    assert "matrix_sort_direction=asc" in toggled


def test_combined_url_state_reload_reproducible(
    client_full: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2026-06-16T22:00:00Z")
    path = (
        "/market?top_n=50&symbol=ETHUSDT&matrix_filter_symbol=ETH"
        "&matrix_filter_freshness=fresh&matrix_sort_field=symbol&matrix_sort_direction=desc"
    )
    bodies = [_html(client_full, path) for _ in range(3)]
    assert bodies[0] == bodies[1] == bodies[2]
    assert 'data-market-governed-top-n="50"' in bodies[0]
    assert 'value="ETH"' in bodies[0]
    assert SIDE_ROUTE_RE.search(bodies[0]) is None


def test_top_n_change_preserves_matrix_query(client_full: TestClient) -> None:
    path = (
        "/market?symbol=SOLUSDT&top_n=20&matrix_filter_symbol=SOL"
        "&matrix_filter_freshness=fresh&matrix_sort_field=volume&matrix_sort_direction=desc"
    )
    body = _html(client_full, path)
    top50_match = re.search(r'href=["\'](/market\?[^"\']*top_n=50[^"\']*)["\']', body)
    assert top50_match is not None
    href = unescape(top50_match.group(1))
    assert "matrix_filter_symbol=SOL" in href
    assert "matrix_sort_field=volume" in href


def test_symbol_selection_preserves_matrix_query(client_full: TestClient) -> None:
    path = "/market?symbol=ETHUSDT&matrix_filter_symbol=ET&matrix_sort_field=rank"
    body = _html(client_full, path)
    sol_link = re.search(
        r'href=["\'](/market\?[^"\']*symbol=SOLUSDT[^"\']*)["\']',
        body,
        re.IGNORECASE,
    )
    assert sol_link is not None
    href = unescape(sol_link.group(1))
    assert "matrix_filter_symbol=ET" in href


def test_ssr_controls_without_inline_script(client_full: TestClient) -> None:
    body = _html(client_full)
    matrix = body.split('data-market-matrix-url-state-v1="true"', 1)[1][:12000]
    assert SCRIPT_BLOCK_RE.search(matrix) is None
    assert 'method="get"' in matrix
    assert 'data-market-matrix-filter-form-v1="true"' in matrix
    assert 'data-market-matrix-reset-filters-v1="true"' in matrix
    assert 'data-market-matrix-reset-sort-v1="true"' in matrix
    assert FORBIDDEN_AUTHORITY_RE.search(matrix) is None


def test_no_bitcoin_spot_or_parallel_route(client_full: TestClient) -> None:
    body = _html(
        client_full,
        "/market?top_n=50&matrix_filter_symbol=ETH&matrix_sort_field=symbol",
    )
    assert "BTCUSDT" not in body
    assert "XBT" not in body
    assert "BTC/EUR" not in body
    assert SIDE_ROUTE_RE.search(body) is None


def test_apply_matrix_view_state_unit(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _governed_ctx(monkeypatch)
    rows = ctx["producer_rows"]
    filtered, normalized, field, direction, no_results = apply_matrix_view_state(
        rows,
        build_market_view_query_extras(matrix_filter_symbol="ETH"),
        allowed_f5_statuses=ctx["f5_filter_values"],
    )
    assert len(filtered) < len(rows)
    assert no_results is False
    assert field == "rank"
    assert direction == "asc"


def test_sort_matrix_rows_tie_break_by_rank() -> None:
    rows = [
        {"rank_sort": 2, "score_sort": 1.0, "symbol": "B"},
        {"rank_sort": 1, "score_sort": 1.0, "symbol": "A"},
    ]
    sorted_rows = sort_matrix_rows(rows, field="score", direction="asc")
    assert [r["symbol"] for r in sorted_rows] == ["A", "B"]


def test_resolve_matrix_sort_state_defaults() -> None:
    field, direction, explicit = resolve_matrix_sort_state(MarketViewQueryExtras())
    assert field == "rank"
    assert direction == "asc"
    assert explicit is False


def test_matrix_view_href_unknown_params_not_propagated() -> None:
    href = build_market_matrix_view_href(
        source="futures",
        symbol="ETHUSDT",
        timeframe="1d",
        limit=120,
        top_n=20,
        extras=build_market_view_query_extras(matrix_filter_symbol="ETH"),
    )
    parsed = parse_qs(urlparse(href).query)
    assert set(parsed.keys()).issubset(
        {
            "source",
            "symbol",
            "timeframe",
            "limit",
            "top_n",
            *MATRIX_VIEW_QUERY_PARAM_NAMES,
        }
    )


def test_determinism_combined_query_state(client_full: TestClient) -> None:
    path = (
        "/market?top_n=50&symbol=ETHUSDT&matrix_filter_symbol=E"
        "&matrix_filter_freshness=fresh&matrix_sort_field=score&matrix_sort_direction=desc"
    )

    def _snap() -> tuple[int, int, str]:
        body = _html(client_full, path)
        visible = body.split('data-market-matrix-visible-count-v1="')[1].split('"', 1)[0]
        producer = body.split('data-market-governed-top20-row-count="')[1].split('"', 1)[0]
        return int(visible), int(producer), body.count('data-market-governed-matrix-row-v1="true"')

    assert _snap() == _snap() == _snap()
