"""Contract tests: Double Play + Safety read-only matrices on canonical GET /market."""

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
from src.webui.double_play_dashboard_display_json_route_v0 import (
    build_static_dashboard_display_dict,
)
from src.webui.futures_read_only_market_dashboard_runtime_v0 import (
    ENV_BUNDLE_ROOT as F5_ENV_BUNDLE_ROOT,
    ENV_ENABLED as F5_ENV_ENABLED,
    build_futures_read_only_market_dashboard_display_context,
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
    CANONICAL_DOUBLE_PLAY_TEMPLATE_OWNER,
    CANONICAL_DP_DATA_OWNER,
    CANONICAL_F5_METADATA_OWNER,
    CANONICAL_MARKET_ROUTE_OWNER,
    CANONICAL_MARKET_VIEWMODEL_OWNER,
    CANONICAL_SAFETY_DATA_OWNER,
    CANONICAL_SAFETY_TEMPLATE_OWNER,
    build_market_double_play_matrix_display_context,
    build_market_safety_matrix_display_context,
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
DP_PARTIAL = (
    project_root
    / "templates"
    / "peak_trade_dashboard"
    / "partials"
    / "double_play_market_compact_v1.html"
)
SAFETY_PARTIAL = (
    project_root
    / "templates"
    / "peak_trade_dashboard"
    / "partials"
    / "market_safety_compact_v1.html"
)
FORBIDDEN_AUTHORITY_RE = re.compile(
    r'(?:type=["\']submit["\']|data-market-(?:order|execute|arm)|(?:buy|sell|long|short).*(?:button|btn))',
    re.IGNORECASE,
)
RECOMMENDATION_RE = re.compile(
    r"(?:recommend|prioritiz|activate|switch side|go long|go short)",
    re.IGNORECASE,
)
BITCOIN_RE = re.compile(r"\b(BTC|XBT|BITCOIN)\b", re.IGNORECASE)
PARALLEL_DP_SURFACE_RE = re.compile(r"data-market-double-play-matrix-v[2-9]", re.IGNORECASE)
PARALLEL_SAFETY_SURFACE_RE = re.compile(r"data-market-safety-matrix-v[2-9]", re.IGNORECASE)


@pytest.fixture()
def client_matrix_on(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
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
    assert resp.status_code == 200, f"{path} -> {resp.status_code}"
    return resp.text


def _matrix_contexts(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[str, object], dict[str, object]]:
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    monkeypatch.setenv(OHLCV_ENV_ENABLED, "1")
    monkeypatch.setenv(OHLCV_ENV_BUNDLE_ROOT, str(OHLCV_FIXTURE))
    monkeypatch.setenv(F5_ENV_ENABLED, "1")
    monkeypatch.setenv(F5_ENV_BUNDLE_ROOT, str(F5_FIXTURE))
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2030-01-15T12:34:56.000000+00:00")
    dp_display = build_static_dashboard_display_dict()
    f5_dashboard = build_futures_read_only_market_dashboard_display_context()
    return (
        build_market_double_play_matrix_display_context(dp_display=dp_display),
        build_market_safety_matrix_display_context(
            dp_display=dp_display,
            f5_dashboard=f5_dashboard,
        ),
    )


def test_canonical_owner_constants() -> None:
    assert CANONICAL_MARKET_ROUTE_OWNER.endswith("market_surface.py")
    assert CANONICAL_MARKET_VIEWMODEL_OWNER.endswith("market_surface.py")
    assert CANONICAL_DOUBLE_PLAY_TEMPLATE_OWNER.endswith("double_play_market_compact_v1.html")
    assert CANONICAL_SAFETY_TEMPLATE_OWNER.endswith("market_safety_compact_v1.html")
    assert CANONICAL_DP_DATA_OWNER.endswith("double_play_dashboard_display_json_route_v0.py")
    assert CANONICAL_SAFETY_DATA_OWNER.endswith("futures_read_only_market_dashboard_runtime_v0.py")
    assert CANONICAL_F5_METADATA_OWNER.endswith("futures_read_only_market_dashboard_runtime_v0.py")


def test_viewmodel_matrix_projection_no_new_computation(monkeypatch: pytest.MonkeyPatch) -> None:
    dp_matrix, safety_matrix = _matrix_contexts(monkeypatch)
    assert dp_matrix["read_only"] is True
    assert safety_matrix["read_only"] is True
    assert safety_matrix["preflight_blocked"] is True
    assert safety_matrix["execution_authorized"] is False
    assert safety_matrix["live_authorized"] is False
    assert len(dp_matrix["rows"]) >= 4
    assert len(safety_matrix["rows"]) >= 5
    preflight = next(row for row in safety_matrix["rows"] if row["dimension_slug"] == "preflight")
    assert preflight["status"] == "blocked"
    execution = next(
        row for row in safety_matrix["rows"] if row["dimension_slug"] == "execution_authorization"
    )
    assert execution["status"] == "not_authorized"
    live = next(row for row in safety_matrix["rows"] if row["dimension_slug"] == "live_gate")
    assert live["status"] == "not_authorized"


def test_double_play_and_safety_matrix_structure(client_matrix_on: TestClient) -> None:
    html = _html(client_matrix_on)
    assert 'data-market-double-play-matrix-v1="true"' in html
    assert 'data-market-safety-matrix-v1="true"' in html
    assert 'data-market-double-play-matrix-table-v1="true"' in html
    assert 'data-market-safety-matrix-table-v1="true"' in html
    assert "Bull / Long" in html
    assert "Bear / Short" in html
    assert "Common status" in html
    assert "Evidence / Freshness" in html
    assert "Safety rail" in html
    assert 'data-market-double-play-readonly-marker-v1="true"' in html
    assert 'data-market-safety-readonly-marker-v1="true"' in html
    assert 'data-market-double-play-bull-long-v1="true"' in html
    assert 'data-market-double-play-bear-short-v1="true"' in html
    assert 'data-market-double-play-common-status-v1="true"' in html
    assert 'data-market-double-play-evidence-freshness-v1="true"' in html
    assert 'data-market-safety-matrix-status-v1="true"' in html
    assert 'data-market-safety-matrix-authority-v1="true"' in html


def test_status_categories_distinct_in_markup(client_matrix_on: TestClient) -> None:
    html = _html(client_matrix_on)
    for category in (
        "active",
        "blocked",
        "unavailable",
        "partial",
        "unknown",
        "not_authorized",
    ):
        assert (
            f'data-matrix-status-category="{category}"' in html
            or f"market-matrix-status-{category}" in html
        )
    assert 'data-matrix-status-category="blocked"' in html
    assert 'data-matrix-status-category="not_authorized"' in html


def test_no_side_recommendation_or_action_controls(client_matrix_on: TestClient) -> None:
    html = unescape(_html(client_matrix_on))
    start = html.index('data-market-double-play-matrix-v1="true"')
    end = html.index('data-market-safety-matrix-v1="true"', start)
    dp_block = html[start:end]
    assert not FORBIDDEN_AUTHORITY_RE.search(dp_block)
    assert not RECOMMENDATION_RE.search(dp_block)
    assert 'type="submit"' not in dp_block.lower()


def test_futures_only_no_bitcoin_no_spot(client_matrix_on: TestClient) -> None:
    html = _html(client_matrix_on)
    assert 'data-market-futures-first-v1="true"' in html
    assert not BITCOIN_RE.search(html)


def test_matrix_url_state_and_topn_preserved(client_matrix_on: TestClient) -> None:
    html = _html(
        client_matrix_on,
        "/market?top_n=50&matrix_filter_freshness=stale&matrix_sort_field=score&matrix_sort_direction=desc",
    )
    assert 'data-market-double-play-matrix-v1="true"' in html
    assert 'data-market-safety-matrix-v1="true"' in html
    assert 'data-market-governed-top20-primary-v1="true"' in html


def test_no_parallel_matrix_surfaces(client_matrix_on: TestClient) -> None:
    html = _html(client_matrix_on)
    assert not PARALLEL_DP_SURFACE_RE.search(html)
    assert not PARALLEL_SAFETY_SURFACE_RE.search(html)


def test_safety_preflight_execution_live_and_killswitch_rows(client_matrix_on: TestClient) -> None:
    html = _html(client_matrix_on)
    assert 'data-market-safety-matrix-row-v1="preflight"' in html
    assert 'data-market-safety-matrix-row-v1="execution_authorization"' in html
    assert 'data-market-safety-matrix-row-v1="live_gate"' in html
    assert 'data-market-safety-matrix-row-v1="kill_switch"' in html
    assert 'data-market-safety-matrix-row-v1="risk"' in html
    assert "PREFLIGHT_REMAINS_BLOCKED" in html


def test_double_play_side_rows_present(client_matrix_on: TestClient) -> None:
    html = _html(client_matrix_on)
    assert 'data-market-double-play-matrix-row-v1="side_summary"' in html
    assert 'data-market-double-play-matrix-row-v1="scope_state"' in html
    assert 'data-market-double-play-matrix-row-v1="eligibility"' in html
    assert 'data-market-double-play-matrix-row-v1="block_reason"' in html


def test_determinism_double_play_matrix_html(client_matrix_on: TestClient) -> None:
    first = _html(client_matrix_on)
    second = _html(client_matrix_on)
    third = _html(client_matrix_on)
    marker = 'data-market-double-play-matrix-v1="true"'
    assert first.count(marker) == second.count(marker) == third.count(marker) == 1
    start = first.index('data-market-double-play-matrix-table-v1="true"')
    end = first.index("</table>", start)
    block = first[start:end]
    assert block == second[start : second.index("</table>", start)]
    assert block == third[start : third.index("</table>", start)]


def test_determinism_safety_matrix_html(client_matrix_on: TestClient) -> None:
    first = _html(client_matrix_on)
    second = _html(client_matrix_on)
    start = first.index('data-market-safety-matrix-table-v1="true"')
    end = first.index("</table>", start)
    block = first[start:end]
    assert block == second[start : second.index("</table>", start)]


def test_determinism_missing_unknown_states(monkeypatch: pytest.MonkeyPatch) -> None:
    dp_matrix, safety_matrix = _matrix_contexts(monkeypatch)
    dp_html_a = str(dp_matrix)
    dp_html_b = str(
        build_market_double_play_matrix_display_context(
            dp_display=build_static_dashboard_display_dict()
        )
    )
    assert dp_html_a == dp_html_b
    unavailable_rows = [row for row in safety_matrix["rows"] if row["status"] == "unavailable"]
    assert unavailable_rows
    assert all(row["status_label"] != "Active" for row in unavailable_rows)


def test_template_context_includes_matrix_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(RANKING_ENV_ENABLED, "1")
    monkeypatch.setenv(RANKING_ENV_BUNDLE_ROOT, str(RANKING_FIXTURE))
    monkeypatch.setenv(OHLCV_ENV_ENABLED, "1")
    monkeypatch.setenv(OHLCV_ENV_BUNDLE_ROOT, str(OHLCV_FIXTURE))
    monkeypatch.setenv(F5_ENV_ENABLED, "1")
    monkeypatch.setenv(F5_ENV_BUNDLE_ROOT, str(F5_FIXTURE))
    _sym, _src, payload, data_unavailable = resolve_market_page_data(
        symbol="ETH/USD",
        timeframe="1d",
        limit=120,
        source="futures",
        top_n=20,
    )
    ctx = build_market_v0_page_template_context(
        get_project_status=lambda: {"ok": True},
        symbol="ETH/USD",
        timeframe="1d",
        limit=120,
        source="futures",
        payload=payload,
        data_unavailable=data_unavailable,
        top_n=20,
    )
    assert "double_play_matrix" in ctx
    assert "safety_matrix" in ctx
    assert ctx["double_play_matrix"]["matrix_visible"] is True
    assert ctx["safety_matrix"]["matrix_visible"] is True


def test_partials_reference_matrix_tokens() -> None:
    dp_text = DP_PARTIAL.read_text(encoding="utf-8")
    safety_text = SAFETY_PARTIAL.read_text(encoding="utf-8")
    assert "double_play_matrix" in dp_text
    assert "safety_matrix" in safety_text
    assert "data-market-double-play-matrix-v1" in dp_text
    assert "data-market-safety-matrix-v1" in safety_text
