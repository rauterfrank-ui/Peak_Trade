"""Visual system transparency contract for canonical GET /market (SSR, view-only)."""

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


def test_visual_transparency_shell_and_status_rail(client_full: TestClient) -> None:
    body = _html(client_full)
    assert 'data-market-visual-transparency-v1="true"' in body
    assert 'data-market-system-status-rail-v1="true"' in body
    assert 'data-market-system-status-node-v1="true"' in body
    assert "Preflight blocked" in body
    assert "Authority · false" in body


def test_instrument_live_tile_and_kpi_visuals(client_full: TestClient) -> None:
    body = _html(client_full)
    assert 'data-market-instrument-live-tile-v1="true"' in body
    assert 'data-market-kpi-rank-badge-v1="true"' in body
    assert 'data-market-kpi-score-bar-v1="true"' in body


def test_matrix_scan_detail_visual_encodings(client_full: TestClient) -> None:
    body = _html(client_full)
    assert 'data-market-matrix-scan-layer-v1="true"' in body
    assert 'data-market-matrix-detail-layer-v1="true"' in body
    assert 'data-market-matrix-score-bar-v1="true"' in body
    assert 'data-market-matrix-freshness-dot-v1="true"' in body


def test_double_play_safety_f5_visual_wrappers(client_full: TestClient) -> None:
    body = _html(client_full)
    assert 'data-market-double-play-visual-grid-v1="true"' in body
    assert 'data-market-double-play-matrix-v1="true"' in body
    assert 'data-market-safety-gate-pipeline-v1="true"' in body
    assert 'data-market-safety-gate-node-v1="true"' in body
    assert 'data-market-f5-pipeline-strip-v1="true"' in body
    assert 'data-f5-market-dashboard-v0="true"' in body


def test_watchlist_tiles_and_f5_stages(client_full: TestClient) -> None:
    body = _html(client_full)
    assert 'data-market-watchlist-visual-v1="true"' in body
    assert 'data-market-watchlist-tile-v1="true"' in body
    assert (
        'data-market-f5-stage-v1="true"' in body
        or 'data-market-workspace-f5-card-v1="true"' in body
    )


def test_chart_visual_primary_preserved(client_full: TestClient) -> None:
    body = _html(client_full)
    assert 'data-market-chart-visual-primary-v1="true"' in body
    assert 'data-market-workspace-chart-v1="true"' in body
    assert 'data-market-workspace-volume-strip-v1="true"' in body


def test_url_state_and_controls_preserved(client_full: TestClient) -> None:
    path = "/market?top_n=50&symbol=ETHUSDT&matrix_filter_symbol=ETH&matrix_sort_field=score"
    body = unescape(_html(client_full, path))
    assert 'data-market-governed-top-n="50"' in body
    assert 'data-market-matrix-reset-filters-v1="true"' in body
    assert 'data-market-governed-top50-toggle-v1="true"' in body


def test_no_information_reduction_core_surfaces(client_full: TestClient) -> None:
    body = _html(client_full)
    assert 'data-market-governed-top20-primary-v1="true"' in body
    assert 'data-market-double-play-matrix-table-v1="true"' in body
    assert 'data-market-safety-matrix-table-v1="true"' in body
    assert 'data-market-workspace-ranking-f5-compact-v1="true"' in body


def test_futures_only_no_bitcoin_no_actions(client_full: TestClient) -> None:
    body = _html(client_full)
    assert 'data-market-futures-first-v1="true"' in body
    assert not BITCOIN_RE.search(body)
    assert not FORBIDDEN_AUTHORITY_RE.search(body)


def test_status_text_not_color_only(client_full: TestClient) -> None:
    body = _html(client_full)
    assert 'data-matrix-status-category="' in body
    assert "BLOCKED" in body or "blocked" in body
    assert "NOT AUTHORIZED" in body or "not authorized" in body.lower()


def test_determinism_default_and_top50(client_full: TestClient) -> None:
    default = [_html(client_full) for _ in range(3)]
    assert default[0] == default[1] == default[2]
    path = "/market?top_n=50&matrix_filter_freshness=fresh&matrix_sort_field=rank"
    top50 = [_html(client_full, path) for _ in range(3)]
    assert top50[0] == top50[1] == top50[2]
