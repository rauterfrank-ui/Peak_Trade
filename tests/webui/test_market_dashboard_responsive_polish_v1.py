"""Responsive polish and accessibility contract for canonical GET /market (SSR, view-only)."""

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
BITCOIN_RE = re.compile(r"\b(BTC|XBT|BITCOIN)\b", re.IGNORECASE)
SIDE_ROUTE_RE = re.compile(r'href=["\']/(?:market/50|top50|market/top50)', re.IGNORECASE)
SCRIPT_BLOCK_RE = re.compile(r"<script\b", re.IGNORECASE)
INVALID_ARIA_ROLE_RE = re.compile(r'role=["\'](?:presentation|none)["\']', re.IGNORECASE)
GLOBAL_OVERFLOW_RE = re.compile(
    r'data-market-global-horizontal-overflow-v1=["\']true["\']',
    re.IGNORECASE,
)
MATRIX_TOOLBAR_WRAP_RE = re.compile(
    r'class="[^"]*flex-wrap[^"]*"[^>]*data-market-matrix-toolbar-responsive-v1="true"',
    re.IGNORECASE,
)
SECONDARY_GRID_RE = re.compile(
    r'class="[^"]*grid-cols-1[^"]*lg:grid-cols-4[^"]*"[^>]*data-market-remodel-secondary-grid-v2="true"',
    re.IGNORECASE,
)


@pytest.fixture()
def client_full(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
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


def test_responsive_container_and_overflow_contract(client_full: TestClient) -> None:
    body = _html(client_full)
    assert 'data-market-responsive-polish-v1="true"' in body
    assert 'data-market-responsive-container-v1="true"' in body
    assert 'data-market-global-overflow-contained-v1="true"' in body
    assert GLOBAL_OVERFLOW_RE.search(body) is None
    assert "overflow-x-clip" in body


def test_matrix_scroll_containment_and_toolbar_wrapping(client_full: TestClient) -> None:
    body = _html(client_full)
    assert 'data-market-matrix-scroll-contained-v1="true"' in body
    assert 'data-market-governed-matrix-scroll-contained-v1="true"' in body
    assert 'data-market-matrix-toolbar-responsive-v1="true"' in body
    assert 'data-market-matrix-toolbar-filters-v1="true"' in body
    assert MATRIX_TOOLBAR_WRAP_RE.search(body) is not None
    assert "min-h-[2rem]" in body


def test_secondary_grid_stack_and_mobile_classes(client_full: TestClient) -> None:
    body = _html(client_full)
    assert 'data-market-secondary-grid-responsive-v1="true"' in body
    assert 'data-market-secondary-cards-stack-v1="true"' in body
    assert SECONDARY_GRID_RE.search(body) is not None
    assert "sm:grid-cols-2" in body


def test_chart_and_dp_safety_responsive_contract(client_full: TestClient) -> None:
    body = _html(client_full)
    assert 'data-market-chart-responsive-v1="true"' in body
    assert 'data-market-safety-responsive-v1="true"' in body
    assert 'data-market-safety-matrix-scroll-contained-v1="true"' in body
    assert 'data-market-double-play-matrix-scroll-v1="true"' in body
    assert 'data-market-double-play-matrix-v1="true"' in body
    assert 'data-market-safety-matrix-v1="true"' in body


def test_focus_visible_and_accessible_labels(client_full: TestClient) -> None:
    body = _html(client_full)
    assert ":focus-visible" in body
    matrix = body.split('data-market-governed-top20-primary-v1="true"', 1)[1][:14000]
    assert 'aria-label="Filter matrix by futures symbol"' in matrix
    assert 'scope="col"' in matrix
    assert INVALID_ARIA_ROLE_RE.search(matrix) is None


def test_status_text_not_color_only_and_table_headers(client_full: TestClient) -> None:
    body = _html(client_full)
    assert 'data-matrix-status-category="' in body
    assert "status_label" not in body  # SSR uses rendered labels, not raw keys
    assert ">ready<" in body.lower() or ">stale<" in body.lower() or ">partial<" in body.lower()
    matrix = body.split('data-market-governed-matrix-table-v1="true"', 1)[1][:6000]
    assert matrix.count('scope="col"') >= 8


def test_active_control_states_and_keyboard_dom_order(client_full: TestClient) -> None:
    body = unescape(
        _html(client_full, "/market?top_n=20&matrix_sort_field=score&matrix_sort_direction=desc")
    )
    matrix = body.split('data-market-governed-top20-primary-v1="true"', 1)[1][:16000]
    assert 'data-market-governed-top20-toggle-v1="true"' in matrix
    assert 'data-market-governed-top50-toggle-v1="true"' in matrix
    assert 'aria-current="page"' in matrix or 'aria-current="true"' in matrix
    top20_pos = matrix.index('data-market-governed-top20-toggle-v1="true"')
    filter_pos = matrix.index('data-market-matrix-filter-symbol-v1="true"')
    reset_pos = matrix.index('data-market-matrix-reset-filters-v1="true"')
    assert top20_pos < filter_pos < reset_pos


def test_url_state_topn_filters_sort_reset_selected_symbol(client_full: TestClient) -> None:
    path = (
        "/market?top_n=50&symbol=ETHUSDT&matrix_filter_symbol=ETH"
        "&matrix_filter_freshness=fresh&matrix_sort_field=symbol&matrix_sort_direction=desc"
    )
    body = unescape(_html(client_full, path))
    assert 'data-market-governed-top-n="50"' in body
    assert 'value="ETH"' in body
    assert 'data-market-matrix-reset-filters-v1="true"' in body
    assert 'data-market-matrix-reset-sort-v1="true"' in body
    assert 'data-market-futures-selector-link-v1="true"' in body
    top20 = re.search(r'href=["\'](/market\?[^"\']*top_n=20[^"\']*)["\']', body)
    assert top20 is not None
    assert "matrix_filter_symbol=ETH" in top20.group(1)


def test_preservation_chart_volume_workspace_matrices_f5(client_full: TestClient) -> None:
    body = _html(client_full)
    assert 'data-market-workspace-chart-v1="true"' in body
    assert 'data-market-workspace-volume-strip-v1="true"' in body
    assert 'data-market-selected-instrument-workspace-v1="true"' in body
    assert 'data-market-governed-top20-primary-v1="true"' in body
    assert 'data-market-double-play-matrix-v1="true"' in body
    assert 'data-market-safety-matrix-v1="true"' in body
    assert 'data-market-workspace-f5-strip-v1="true"' in body or "F5" in body


def test_futures_only_no_bitcoin_no_action_controls(client_full: TestClient) -> None:
    body = _html(client_full, "/market?top_n=50")
    assert 'data-market-futures-first-v1="true"' in body
    assert not BITCOIN_RE.search(body)
    assert SIDE_ROUTE_RE.search(body) is None
    assert not FORBIDDEN_AUTHORITY_RE.search(body)


def test_ssr_without_javascript(client_full: TestClient) -> None:
    body = _html(client_full)
    matrix = body.split('data-market-governed-top20-primary-v1="true"', 1)[1][:12000]
    assert SCRIPT_BLOCK_RE.search(matrix) is None
    assert 'method="get"' in matrix


def test_determinism_default_top50_and_matrix_states(client_full: TestClient) -> None:
    default_runs = [_html(client_full) for _ in range(3)]
    assert default_runs[0] == default_runs[1] == default_runs[2]

    top50_path = (
        "/market?top_n=50&symbol=ETHUSDT&matrix_filter_symbol=E"
        "&matrix_filter_freshness=fresh&matrix_sort_field=score&matrix_sort_direction=desc"
    )
    top50_runs = [_html(client_full, top50_path) for _ in range(3)]
    assert top50_runs[0] == top50_runs[1] == top50_runs[2]

    matrix_runs = [_html(client_full) for _ in range(3)]
    marker = 'data-market-double-play-matrix-table-v1="true"'
    start = matrix_runs[0].index(marker)
    end = matrix_runs[0].index("</table>", start)
    block = matrix_runs[0][start:end]
    assert block == matrix_runs[1][start : matrix_runs[1].index("</table>", start)]
    assert block == matrix_runs[2][start : matrix_runs[2].index("</table>", start)]
