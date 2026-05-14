"""Market Dashboard read-only structure contract v0.

This module is intentionally UI/HTML-structure only. It must not authorize
runtime, scheduler, paper/testnet/live, broker, exchange, or order flows.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

pytestmark = pytest.mark.web

from src.webui.app import create_app

FORM_ACTION_RE = re.compile(
    r"<form\b[^>]*\baction\s*=\s*[\"']([^\"']*)[\"']",
    re.IGNORECASE,
)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    with TestClient(create_app()) as test_client:
        yield test_client


def _html(client: TestClient, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200
    ctype = response.headers.get("content-type", "")
    assert "text/html" in ctype
    return response.text


def test_market_dashboard_keeps_depth_ssr_without_client_depth_fetch(
    client: TestClient,
) -> None:
    html = _html(client, "/market")

    assert 'data-market-depth-panel="true"' in html
    assert "data-market-depth-status=" in html
    assert 'data-market-depth-summary="true"' in html

    assert "/api/market/depth" not in html
    assert "fetch(" not in html
    assert "XMLHttpRequest" not in html


def test_double_play_market_dashboard_does_not_embed_market_depth_api_fetch(
    client: TestClient,
) -> None:
    html = _html(client, "/market/double-play")

    assert "/api/market/depth" not in html
    assert "fetch(" not in html
    assert "XMLHttpRequest" not in html


def test_double_play_dashboard_excludes_market_depth_ssr_markers_v0(
    client: TestClient,
) -> None:
    """Double-Play page must not carry `/market` SSR Market Depth strip markup."""
    html = _html(client, "/market/double-play")

    assert "data-market-depth-panel" not in html
    assert "market-v0-depth-ssr" not in html


def test_market_and_double_play_chartjs_cdn_failure_attribution_v0(
    client: TestClient,
) -> None:
    """Chart.js loads from CDN; templates attribute CDN load failures (read-only markers)."""
    for path, cdn_id, shell_id in (
        ("/market", "peak-trade-market-chartjs-cdn-v0", "market-v0-shell"),
        (
            "/market/double-play",
            "peak-trade-double-play-chartjs-cdn-v0",
            "double-play-market-v0-shell",
        ),
    ):
        html = _html(client, path)
        assert "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js" in html
        assert f'id="{cdn_id}"' in html
        assert f'id="{shell_id}"' in html
        assert 'data-chartjs-cdn-script-v0="true"' in html
        assert 'data-chartjs-cdn-monitored-v0="true"' in html
        assert "data-chartjs-cdn-load-error" in html
        assert "onerror=" in html.lower()
        assert "fetch(" not in html
        assert "XMLHttpRequest" not in html


def test_market_dashboard_has_no_trade_action_affordance(client: TestClient) -> None:
    combined_html = "\n".join(
        [
            _html(client, "/market"),
            _html(client, "/market/double-play"),
        ]
    ).lower()

    forbidden_action_terms = [
        "place order",
        "submit order",
        "send order",
        "buy now",
        "sell now",
        "go long",
        "go short",
        "execute trade",
        "live authorize",
        "authorize live",
        "broker submit",
        "exchange submit",
    ]

    for term in forbidden_action_terms:
        assert term not in combined_html


def test_market_dashboard_readonly_banner_markers(client: TestClient) -> None:
    market_html = _html(client, "/market")
    assert 'data-market-readonly="true"' in market_html
    assert 'data-market-non-authorizing="true"' in market_html


def test_market_dashboard_ranking_funnel_empty_state_v0_marker(client: TestClient) -> None:
    """Contract-first funnel panel: stable marker only; no ranking data wired on /market."""
    market_html = _html(client, "/market")
    assert 'data-market-v0-ranking-funnel-empty-state-v0="true"' in market_html


def test_market_dashboard_ranking_funnel_dynamic_labels_v0_marker(client: TestClient) -> None:
    """Funnel stages use dynamic labels (no fixed final-count wording in UI contract)."""
    market_html = _html(client, "/market")
    assert 'data-market-v0-ranking-funnel-dynamic-labels-v0="true"' in market_html


def test_market_dashboard_pro_panel_shell_structure_v0(client: TestClient) -> None:
    """Read-only IA shell on GET /market: stable markers, no order-affordance attributes."""
    market_html = _html(client, "/market")

    assert 'data-market-v0-visual-density-lower-band-v1="true"' in market_html
    assert 'data-market-v0-pro-shell="true"' in market_html
    assert 'data-market-v0-one-page-link-cleanup-v1="true"' in market_html
    assert 'data-market-v0-pro-grid="true"' in market_html
    assert 'data-market-v0-chart-panel="true"' in market_html
    assert 'data-market-v0-chart-candle-stack="true"' in market_html
    assert 'data-market-v0-orderbook-placeholder="true"' in market_html
    assert 'data-market-v0-depth-chart-placeholder="true"' in market_html
    assert 'data-market-v0-pro-boundary="true"' in market_html
    assert 'data-market-v0-status-panel="true"' in market_html
    assert 'data-market-v0-status-diagnostics-visual-rails-v1="true"' in market_html

    assert 'data-market-v0-orderbook-topn="true"' in market_html
    assert 'data-market-v0-orderbook-has-levels="false"' in market_html
    assert 'data-market-v0-orderbook-empty="true"' in market_html

    assert 'data-market-v0-surface-links="true"' in market_html
    assert 'data-market-v0-dashboard-surface="true"' in market_html
    assert 'data-market-v0-rd-charts-surface="true"' in market_html
    assert 'data-market-v0-data-surfaces="true"' in market_html
    assert 'data-market-v0-ohlcv-surface="true"' in market_html
    assert 'data-market-v0-depth-surface="true"' in market_html
    assert 'data-market-v0-visual-cockpit="true"' in market_html
    assert 'data-market-v0-visual-cockpit-v1="true"' in market_html
    assert 'data-market-v0-lower-depth-orderbook-visuals-v1="true"' in market_html
    assert 'data-market-v0-lower-disabled-depth-visual-state-v1="true"' in market_html
    assert 'data-market-v0-visual-surface-strip="true"' in market_html
    assert 'data-market-v0-dashboard-preview="true"' in market_html
    assert 'data-market-v0-rd-preview="true"' in market_html
    assert 'data-market-v0-ohlcv-preview="true"' in market_html
    assert 'data-market-v0-depth-preview="true"' in market_html
    assert 'data-market-v0-ssr-metrics-strip="true"' in market_html
    assert 'data-market-v0-close-chart-integrated-frame="true"' in market_html
    assert 'data-market-v0-in-chart-ohlc-svg-v1="true"' in market_html
    assert 'data-market-v0-in-chart-ohlc-svg-root="true"' in market_html
    assert (
        'data-market-v0-in-chart-ohlc-candle-up="true"' in market_html
        or 'data-market-v0-in-chart-ohlc-candle-down="true"' in market_html
    )
    assert "chartjs-chart-financial" not in market_html.lower()

    lowered = market_html.lower()
    assert "place order" not in lowered
    assert "data-order-form" not in lowered
    assert "data-order-submit" not in lowered
    assert "market-v0-order-form" not in lowered


def test_market_dashboard_landmarks_and_labelled_regions_v0(client: TestClient) -> None:
    """Stable region landmarks + aria-labelledby hooks; read-only markers unchanged."""
    html = _html(client, "/market")
    assert 'id="market-v0-shell"' in html
    assert 'role="region"' in html
    assert 'aria-labelledby="market-v0-landmark-page-title"' in html
    assert 'id="market-v0-landmark-page-title"' in html
    assert 'id="market-v0-landmark-readonly-constraints-h2"' in html
    assert 'aria-labelledby="market-v0-landmark-readonly-constraints-h2"' in html
    assert 'id="market-v0-landmark-safety-banner-h2"' in html
    assert 'aria-labelledby="market-v0-landmark-safety-banner-h2"' in html
    assert 'id="market-v0-landmark-ranking-funnel-h2"' in html
    assert 'aria-labelledby="market-v0-landmark-ranking-funnel-h2"' in html
    assert 'id="market-v0-landmark-visual-cockpit-h2"' in html
    assert 'aria-labelledby="market-v0-landmark-visual-cockpit-h2"' in html
    assert 'id="market-v0-landmark-surface-links-h2"' in html
    assert 'aria-labelledby="market-v0-landmark-surface-links-h2"' in html
    assert 'id="market-v0-landmark-data-rails-h2"' in html
    assert 'aria-labelledby="market-v0-landmark-data-rails-h2"' in html
    assert 'id="market-v0-landmark-query-context-h2"' in html
    assert 'aria-labelledby="market-v0-landmark-query-context-h2"' in html
    assert 'id="market-v0-landmark-close-chart-h2"' in html
    assert 'aria-labelledby="market-v0-landmark-close-chart-h2"' in html
    assert 'data-market-readonly="true"' in html
    assert 'data-market-non-authorizing="true"' in html
    lowered = html.lower()
    assert "<form" not in lowered
    assert "<button" not in lowered


def test_double_play_market_dashboard_landmarks_and_labelled_regions_v0(
    client: TestClient,
) -> None:
    html = _html(client, "/market/double-play")
    assert 'id="double-play-market-v0-shell"' in html
    assert 'aria-labelledby="double-play-market-v0-landmark-page-title"' in html
    assert 'id="double-play-market-v0-landmark-page-title"' in html
    assert 'id="double-play-market-v0-landmark-safety-h2"' in html
    assert 'aria-labelledby="double-play-market-v0-landmark-safety-h2"' in html
    assert 'id="double-play-market-v0-landmark-reading-guide-h2"' in html
    assert 'aria-labelledby="double-play-market-v0-landmark-reading-guide-h2"' in html
    assert 'id="double-play-market-v0-landmark-candlestick-h2"' in html
    assert 'aria-labelledby="double-play-market-v0-landmark-candlestick-h2"' in html
    assert 'aria-labelledby="double-play-market-v0-landmark-rail-h2"' in html
    assert 'id="double-play-market-v0-landmark-rail-h2"' in html
    assert 'data-double-play-market-readonly="true"' in html
    assert 'data-double-play-market-no-orders="true"' in html
    assert 'data-double-play-market-no-authority="true"' in html
    lowered = html.lower()
    assert "<form" not in lowered


def test_market_dashboard_forms_do_not_target_order_or_live_paths(
    client: TestClient,
) -> None:
    combined_html = "\n".join(
        [
            _html(client, "/market"),
            _html(client, "/market/double-play"),
        ]
    )

    form_actions = [m for m in FORM_ACTION_RE.findall(combined_html) if m.strip()]

    forbidden_fragments = [
        "order",
        "broker",
        "exchange",
        "live",
        "testnet",
        "kill",
        "scheduler",
        "runtime",
    ]

    for action in form_actions:
        lowered = action.lower()
        for fragment in forbidden_fragments:
            assert fragment not in lowered
