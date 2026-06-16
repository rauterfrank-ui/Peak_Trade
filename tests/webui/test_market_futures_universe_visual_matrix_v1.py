"""Contract tests: futures universe visual matrix (view-only) on governed Top-N /market."""

from __future__ import annotations

import json
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
    AVAILABLE_FILTER_FIELDS,
    AVAILABLE_SORT_FIELDS,
    CANONICAL_CLIENT_INTERACTION_OWNER,
    CANONICAL_ELIGIBILITY_OWNER,
    CANONICAL_MATRIX_TEMPLATE_OWNER,
    CANONICAL_RANKING_FUNNEL_OWNER,
    CANONICAL_STYLE_OWNER,
    DEFAULT_TOP_N,
    MATRIX_ROW_SCHEMA,
    build_market_governed_top20_display_context,
    build_market_ranking_funnel_display_context,
    build_market_v0_page_template_context,
    resolve_market_page_data,
)
from src.webui.futures_read_only_market_dashboard_runtime_v0 import (
    build_futures_read_only_market_dashboard_display_context,
)
from src.webui.market_futures_ohlcv_runtime_v0 import build_market_futures_ohlcv_display_context

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
MATRIX_PARTIAL = (
    project_root
    / "templates"
    / "peak_trade_dashboard"
    / "partials"
    / "market_governed_top20_primary_v1.html"
)
FORBIDDEN_AUTHORITY_RE = re.compile(
    r'(?:type=["\']submit["\']|data-market-(?:order|execute|arm))',
    re.IGNORECASE,
)
PARALLEL_MATRIX_PARTIAL_RE = re.compile(
    r"market_governed_top\d+_(?!primary_v1)",
    re.IGNORECASE,
)


@pytest.fixture()
def client_matrix_on(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
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


def _governed_ctx(
    monkeypatch: pytest.MonkeyPatch,
    *,
    ranking_root: Path = RANKING_FIXTURE,
    top_n: int = DEFAULT_TOP_N,
) -> dict[str, object]:
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(ranking_root))
    monkeypatch.setenv(OHLCV_ENV_ENABLED, "1")
    monkeypatch.setenv(OHLCV_ENV_BUNDLE_ROOT, str(OHLCV_FIXTURE))
    monkeypatch.setenv(F5_ENV_ENABLED, "1")
    monkeypatch.setenv(F5_ENV_BUNDLE_ROOT, str(F5_FIXTURE))
    ranking = build_market_ranking_funnel_display_context()
    f5 = build_futures_read_only_market_dashboard_display_context()
    ohlcv = build_market_futures_ohlcv_display_context()
    return build_market_governed_top20_display_context(
        ranking_funnel=ranking,
        f5_dashboard=f5,
        futures_ohlcv=ohlcv,
        top_n=top_n,
    )


def test_single_matrix_owner_partial_only() -> None:
    partials = list(
        (project_root / "templates" / "peak_trade_dashboard" / "partials").glob(
            "market_governed_top*.html"
        )
    )
    assert partials == [MATRIX_PARTIAL]


def test_canonical_owner_constants() -> None:
    assert CANONICAL_MATRIX_TEMPLATE_OWNER.endswith("market_governed_top20_primary_v1.html")
    assert CANONICAL_RANKING_FUNNEL_OWNER.endswith("market_ranking_funnel_runtime_v0.py")
    assert CANONICAL_ELIGIBILITY_OWNER.endswith("market_instrument_eligibility_v0.py")
    assert CANONICAL_STYLE_OWNER == CANONICAL_MATRIX_TEMPLATE_OWNER
    assert CANONICAL_CLIENT_INTERACTION_OWNER == CANONICAL_MATRIX_TEMPLATE_OWNER


def test_matrix_schema_constants() -> None:
    assert "rank" in MATRIX_ROW_SCHEMA
    assert "symbol" in MATRIX_ROW_SCHEMA
    assert "score_display" in MATRIX_ROW_SCHEMA
    assert "rank" in AVAILABLE_SORT_FIELDS
    assert "symbol" in AVAILABLE_FILTER_FIELDS
    assert "freshness" in AVAILABLE_FILTER_FIELDS


def test_top20_default_top50_selectable(client_matrix_on: TestClient) -> None:
    body_default = _html(client_matrix_on)
    assert 'data-market-governed-top-n-default="20"' in body_default
    assert 'data-market-governed-top-n="20"' in body_default
    body50 = _html(client_matrix_on, "/market?top_n=50")
    assert 'data-market-governed-top-n="50"' in body50
    assert 'data-market-governed-top50-toggle-v1="true"' in body50


def test_row_count_not_padded(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _governed_ctx(monkeypatch, ranking_root=RANKING_FIXTURE, top_n=50)
    assert ctx["row_count"] == 1
    assert ctx["top_n"] == 50


def test_top50_fixture_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _governed_ctx(monkeypatch, ranking_root=RANKING_TOP50_FIXTURE, top_n=50)
    assert ctx["row_count"] == 5
    ranks = [r["rank"] for r in ctx["rows"]]
    assert ranks == [1, 2, 3, 4, 5]


def test_governed_ranking_order_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _governed_ctx(monkeypatch, ranking_root=RANKING_TOP50_FIXTURE, top_n=50)
    symbols = [r["symbol"] for r in ctx["rows"]]
    assert symbols == ["ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOTUSDT"]


def test_ohlcv_enrichment_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _governed_ctx(monkeypatch)
    row = ctx["rows"][0]
    assert row["last_price_display"] != "—"
    assert row["change_display"] != "—"
    assert row["volume_display"] != "—"
    assert row["data_status"] == "ready"


def test_unavailable_ohlcv_shows_dash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    monkeypatch.delenv(OHLCV_ENV_ENABLED, raising=False)
    ranking = build_market_ranking_funnel_display_context()
    f5 = build_futures_read_only_market_dashboard_display_context()
    ctx = build_market_governed_top20_display_context(
        ranking_funnel=ranking,
        f5_dashboard=f5,
        futures_ohlcv=build_market_futures_ohlcv_display_context(),
    )
    row = ctx["rows"][0]
    assert row["last_price_display"] == "—"
    assert row["data_status"] == "partial"


def test_view_only_matrix_markers(client_matrix_on: TestClient) -> None:
    body = _html(client_matrix_on)
    assert 'data-market-futures-universe-visual-matrix-v1="true"' in body
    assert 'data-market-matrix-view-only="true"' in body
    assert 'data-market-matrix-read-only="true"' in body
    assert 'data-market-governed-matrix-table-v1="true"' in body
    assert 'data-market-governed-matrix-filters-v1="true"' in body
    assert 'data-market-matrix-filter-symbol-v1="true"' in body
    assert 'data-market-matrix-sort-v1="true"' in body
    assert 'data-market-governed-matrix-no-results-v1="true"' in body


def test_no_authority_actions_in_matrix(client_matrix_on: TestClient) -> None:
    body = _html(client_matrix_on)
    matrix_section = body.split('data-market-futures-universe-visual-matrix-v1="true"', 1)[1][:8000]
    assert FORBIDDEN_AUTHORITY_RE.search(matrix_section) is None
    assert "no orders" in matrix_section.lower()


def test_bitcoin_and_spot_excluded(client_matrix_on: TestClient) -> None:
    body = _html(client_matrix_on)
    assert "BTC/EUR" not in body
    assert "bitcoin" not in body.lower()


def test_missing_malformed_stale_states(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.delenv(RANKING_ENV_ENABLED, raising=False)
    monkeypatch.delenv(RANKING_ENV_BUNDLE_ROOT, raising=False)
    kraken_mock = MagicMock(
        side_effect=AssertionError("fetch_ohlcv_df must not run on futures-first /market")
    )
    monkeypatch.setattr("src.data.kraken.fetch_ohlcv_df", kraken_mock)
    with TestClient(create_app()) as client:
        body_missing = _html(client)
    assert 'data-market-governed-top20-missing-state-v1="true"' in body_missing

    bad = tmp_path / "bad_ranking"
    bad.mkdir()
    (bad / "ranking_funnel.json").write_text("{bad", encoding="utf-8")
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(bad))
    with TestClient(create_app()) as c:
        body_malformed = _html(c)
    assert 'data-market-governed-top20-malformed-v1="true"' in body_malformed

    stale = tmp_path / "stale_ranking"
    stale.mkdir()
    payload = json.loads((RANKING_FIXTURE / "ranking_funnel.json").read_text(encoding="utf-8"))
    payload["stale"] = True
    payload["stale_reason"] = "fixture_stale"
    (stale / "ranking_funnel.json").write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(stale))
    with TestClient(create_app()) as c:
        body_stale = _html(c)
    assert 'data-market-governed-top20-stale-v1="true"' in body_stale


def test_selected_instrument_visible(client_matrix_on: TestClient) -> None:
    body = _html(client_matrix_on, "/market?symbol=ETHUSDT")
    assert 'data-market-futures-selector-selected-v1="true"' in body
    assert 'data-market-selected-instrument="ETHUSDT"' in body


def test_sort_data_attributes_present(client_matrix_on: TestClient) -> None:
    body = _html(client_matrix_on)
    assert 'data-market-matrix-sort-rank="' in body
    assert 'data-market-matrix-sort-score="' in body
    assert 'data-market-matrix-sort-field="rank"' in body


def test_no_parallel_matrix_template_in_partials_dir() -> None:
    text = (project_root / "templates" / "peak_trade_dashboard" / "market_v0.html").read_text(
        encoding="utf-8"
    )
    assert text.count("market_governed_top20_primary_v1.html") == 1
    assert PARALLEL_MATRIX_PARTIAL_RE.search(text) is None


def test_matrix_context_determinism_three_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    def _snap() -> dict[str, object]:
        ctx = _governed_ctx(monkeypatch, ranking_root=RANKING_TOP50_FIXTURE, top_n=50)
        return {
            "row_count": ctx["row_count"],
            "rows": ctx["rows"],
            "sort_fields": ctx["available_sort_fields"],
            "filter_fields": ctx["available_filter_fields"],
        }

    assert _snap() == _snap() == _snap()


def test_template_context_includes_matrix_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    sym, src, payload, unavailable = resolve_market_page_data(
        symbol=None, timeframe="1d", limit=120, source="futures"
    )
    ctx = build_market_v0_page_template_context(
        get_project_status=lambda: {"ok": True},
        symbol=sym,
        timeframe="1d",
        limit=120,
        source=src,
        payload=payload,
        data_unavailable=unavailable,
    )
    governed = ctx["governed_top20"]
    assert governed["view_only"] is True
    assert governed["read_only"] is True
    assert governed["default_sort_field"] == "rank"
