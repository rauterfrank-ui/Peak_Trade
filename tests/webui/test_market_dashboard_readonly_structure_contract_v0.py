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
from tests.fixtures.ops import market_registry_projection_overlay_v0 as overlay_fixtures

FORM_ACTION_RE = re.compile(
    r"<form\b[^>]*\baction\s*=\s*[\"']([^\"']*)[\"']",
    re.IGNORECASE,
)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.delenv("PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED", raising=False)
    monkeypatch.delenv("PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT", raising=False)
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture()
def client_ranking_funnel_fixture_bundle_on(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    """Offline ranking funnel SSR enabled with repo complete_minimal fixture."""
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
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture()
def client_depth_and_ranking_funnel_fixtures_on(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    """Depth and ranking funnel SSR enabled with repo offline fixtures."""
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "1")
    depth_bundle = (
        project_root / "tests" / "fixtures" / "market_depth_readmodel_v0" / "complete_minimal"
    ).resolve()
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT", str(depth_bundle))
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2030-01-15T12:34:56.000000+00:00")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED", "1")
    ranking_bundle = (
        project_root
        / "tests"
        / "fixtures"
        / "market_ranking_funnel_readmodel_v0"
        / "complete_minimal"
    ).resolve()
    monkeypatch.setenv("PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT", str(ranking_bundle))
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


def test_market_dashboard_depth_ssr_region_role_contract_v0(client: TestClient) -> None:
    """SSR depth strip section exposes role=region and aria-labelledby to landmark h2."""
    html = _html(client, "/market")
    assert re.search(
        r'id="market-v0-depth-ssr"\s+role="region"\s+aria-labelledby="market-v0-landmark-depth-ssr-h2"',
        html,
    )
    assert 'id="market-v0-landmark-depth-ssr-h2"' in html
    assert 'data-market-v0-depth-landmark-heading-v0="true"' in html


def test_double_play_market_dashboard_excludes_depth_ssr_region_role_contract_v0(
    client: TestClient,
) -> None:
    """Double-Play uses dp-specific depth landmarks; must not carry `/market` depth region markup."""
    html = _html(client, "/market/double-play")
    assert not re.search(
        r'id="market-v0-depth-ssr"\s+role="region"\s+aria-labelledby="market-v0-landmark-depth-ssr-h2"',
        html,
    )
    assert re.search(
        r'id="double-play-market-v0-depth-ssr"\s+role="region"\s+aria-labelledby="double-play-market-v0-landmark-depth-ssr-h2"',
        html,
    )
    assert 'data-double-play-market-depth-panel="true"' in html
    assert 'data-double-play-market-depth-landmark-heading-v0="true"' in html
    assert 'data-double-play-market-depth-non-authorizing="true"' in html
    assert 'data-double-play-market-depth-readonly-copy-v0="true"' in html
    assert "does not authorize trades" in html


def test_double_play_market_dashboard_depth_ssr_with_fixture_bundle_v0(
    client_depth_fixture_bundle_on: TestClient,
) -> None:
    """Enabled offline depth fixture surfaces on Double-Play via shared display context."""
    html = _html(client_depth_fixture_bundle_on, "/market/double-play")
    assert 'data-double-play-market-depth-panel="true"' in html
    assert 'data-double-play-market-depth-status="ok"' in html
    assert 'data-double-play-market-depth-summary="true"' in html
    assert 'id="market-v0-depth-ssr"' not in html
    assert "data-market-depth-panel" not in html
    assert "/api/market/depth" not in html
    assert "fetch(" not in html


def test_double_play_market_dashboard_depth_ssr_default_disabled_post_merge_v0(
    client: TestClient,
) -> None:
    """Post-merge: Double-Play depth strip is always present; default env stays disabled."""
    html = _html(client, "/market/double-play")
    assert re.search(
        r'id="double-play-market-v0-depth-ssr"\s+role="region"\s+aria-labelledby="double-play-market-v0-landmark-depth-ssr-h2"',
        html,
    )
    assert 'data-double-play-market-depth-panel="true"' in html
    assert 'data-double-play-market-depth-status="disabled"' in html
    assert 'data-double-play-market-depth-non-authorizing="true"' in html
    assert 'data-double-play-market-depth-operator-hint="true"' in html
    assert 'id="market-v0-depth-ssr"' not in html
    assert "data-market-v0-ranking-funnel" not in html


def test_double_play_market_dashboard_depth_ssr_post_merge_contract_v0(
    client_depth_fixture_bundle_on: TestClient,
) -> None:
    """Post-merge #3725: fixture depth, dp markers, OHLC shell coexistence, /market exclusions, no fetch."""
    html = _html(client_depth_fixture_bundle_on, "/market/double-play")

    assert re.search(
        r'id="double-play-market-v0-depth-ssr"\s+role="region"\s+aria-labelledby="double-play-market-v0-landmark-depth-ssr-h2"',
        html,
    )
    assert 'data-double-play-market-depth-panel="true"' in html
    assert 'data-double-play-market-depth-status="ok"' in html
    assert 'data-double-play-market-depth-summary="true"' in html
    assert 'data-double-play-market-depth-non-authorizing="true"' in html
    assert 'data-double-play-market-depth-readonly-copy-v0="true"' in html
    assert 'data-double-play-market-depth-landmark-heading-v0="true"' in html
    assert 'data-double-play-market-depth-readmodel-id="market_depth_readmodel.v0"' in html
    assert 'id="double-play-market-v0-landmark-depth-ssr-h2"' in html
    assert 'data-double-play-market-depth-operator-hint="true"' not in html
    assert "does not authorize trades" in html

    assert 'id="double-play-market-v0-shell"' in html
    assert 'data-double-play-market-ssr-only="true"' in html
    assert 'data-double-play-market-no-fetch="true"' in html
    assert 'data-double-play-market-embedded-chart="true"' in html
    assert 'data-double-play-market-candlestick-v1-2="true"' in html
    assert 'data-double-play-market-composition-ssr-v1="true"' in html

    assert 'id="market-v0-depth-ssr"' not in html
    assert "data-market-depth-panel" not in html
    assert "data-market-v0-depth-" not in html
    assert 'id="market-v0-landmark-depth-ssr-h2"' not in html
    assert "data-market-v0-ranking-funnel" not in html
    assert "market-v0-landmark-ranking-funnel-h2" not in html
    assert 'id="market-v0-ranking-funnel-ssr"' not in html

    assert "/api/market/depth" not in html
    assert "fetch(" not in html
    assert "XMLHttpRequest" not in html


def test_market_dashboard_orderbook_topn_region_role_contract_v0(
    client: TestClient,
) -> None:
    """Orderbook Top-N ladder section exposes role=region and aria-labelledby to landmark h2."""
    html = _html(client, "/market")
    assert re.search(
        r'id="market-v0-orderbook-topn"\s+role="region"\s+aria-labelledby="market-v0-landmark-orderbook-topn-h2"',
        html,
    )
    assert 'id="market-v0-landmark-orderbook-topn-h2"' in html
    assert 'data-market-v0-orderbook-landmark-heading-v0="true"' in html
    assert 'data-market-v0-orderbook-topn="true"' in html
    assert 'data-market-v0-orderbook-placeholder="true"' in html


def test_double_play_market_dashboard_excludes_orderbook_topn_landmark_region_v0(
    client: TestClient,
) -> None:
    """Double-Play page must not carry `/market` Orderbook Top-N landmark region markup."""
    html = _html(client, "/market/double-play")
    assert not re.search(
        r'id="market-v0-orderbook-topn"\s+role="region"\s+aria-labelledby="market-v0-landmark-orderbook-topn-h2"',
        html,
    )
    assert "market-v0-landmark-orderbook-topn-h2" not in html
    assert "data-market-v0-orderbook-landmark-heading-v0" not in html
    assert "data-market-v0-orderbook-topn" not in html
    assert "data-market-v0-orderbook-placeholder" not in html


def test_market_dashboard_depth_chart_placeholder_region_role_contract_v0(
    client: TestClient,
) -> None:
    """Depth-chart placeholder section exposes role=region and aria-labelledby to landmark h2."""
    html = _html(client, "/market")
    assert 'data-market-v0-depth-chart-placeholder="true"' in html
    assert re.search(
        r'id="market-v0-depth-chart-placeholder"\s+role="region"\s+aria-labelledby="market-v0-landmark-depth-chart-placeholder-h2"',
        html,
    )
    assert 'id="market-v0-landmark-depth-chart-placeholder-h2"' in html
    assert 'data-market-v0-depth-chart-placeholder-landmark-heading-v0="true"' in html


def test_double_play_market_dashboard_excludes_depth_chart_placeholder_landmark_region_v0(
    client: TestClient,
) -> None:
    """Double-Play page must not carry `/market` depth-chart placeholder landmark region markup."""
    html = _html(client, "/market/double-play")
    assert not re.search(
        r'id="market-v0-depth-chart-placeholder"\s+role="region"\s+aria-labelledby="market-v0-landmark-depth-chart-placeholder-h2"',
        html,
    )
    assert "market-v0-landmark-depth-chart-placeholder-h2" not in html
    assert "data-market-v0-depth-chart-placeholder-landmark-heading-v0" not in html
    assert "data-market-v0-depth-chart-placeholder" not in html


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
    assert 'id="market-v0-depth-ssr"' not in html
    assert 'id="market-v0-landmark-depth-ssr-h2"' not in html
    assert "data-market-v0-depth-landmark-heading-v0" not in html
    assert 'data-double-play-market-depth-panel="true"' in html
    assert 'id="double-play-market-v0-depth-ssr"' in html


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


def test_market_dashboard_v11_chart_diagnostics_readonly_structure_contract_v0(
    client: TestClient,
) -> None:
    """v1.1 chart diagnostics SSR markers on GET /market (structure-only, non-authorizing)."""
    html = _html(client, "/market")
    lowered = html.lower()

    assert 'data-market-v11-chart-diagnostics="true"' in html
    assert 'data-market-v11-diagnostics-inner="true"' in html
    assert 'data-market-v11-render-fallback="true"' in html
    assert "data-market-v11-fallback-mode=" in html
    assert 'data-market-v11-chart-library-status="true"' in html
    assert 'data-market-v11-payload-bars="true"' in html
    assert 'data-market-v11-diagnostics-visual-rails="true"' in html
    assert 'id="market-v11-render-fallback"' in html

    assert "Chart diagnostics" in html
    assert "No backend/API/provider change" in html
    assert "Dominant panel · keine Order-UI" in html
    assert "SSR only — verified in browser" in html

    assert 'data-market-readonly="true"' in html
    assert 'data-market-non-authorizing="true"' in html

    assert "fetch(" not in html
    assert "XMLHttpRequest" not in html
    assert "<form" not in lowered
    assert "place order" not in lowered
    assert "ready for live" not in lowered
    assert "testnet approved" not in lowered


def test_double_play_market_dashboard_v11_chart_diagnostics_readonly_structure_contract_v0(
    client: TestClient,
) -> None:
    """v1.1 chart diagnostics SSR markers on GET /market/double-play (dp-specific shell)."""
    html = _html(client, "/market/double-play")
    lowered = html.lower()

    assert 'data-market-v11-chart-diagnostics="true"' in html
    assert 'data-market-v11-diagnostics-inner="true"' in html
    assert 'data-market-v11-render-fallback="true"' in html
    assert "data-market-v11-fallback-mode=" in html
    assert 'data-market-v11-chart-library-status="true"' in html
    assert 'data-market-v11-payload-bars="true"' in html
    assert 'data-double-play-market-cockpit-diagnostics-secondary="true"' in html
    assert 'id="dp-market-v11-render-fallback"' in html

    assert "Diagnostics" in html
    assert "SSR only — verified in browser" in html

    assert 'data-double-play-market-readonly="true"' in html
    assert 'data-double-play-market-no-authority="true"' in html
    assert 'data-double-play-market-no-orders="true"' in html

    assert "fetch(" not in html
    assert "XMLHttpRequest" not in html
    assert "<form" not in lowered
    assert "place order" not in lowered


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


def test_market_dashboard_guardrails_visibility_v0(client: TestClient) -> None:
    """Both market routes render shared Guardrails non-authority copy (MARKET_SURFACE_V0)."""
    guardrails_core = "Dashboard ≠ Freigabe · AI ≠ Authority · Signal ≠ Trade · Docs ≠ Approval"
    for path in ("/market", "/market/double-play"):
        html = _html(client, path)
        assert "Guardrails:" in html
        assert guardrails_core in html
        assert "keine Broker-/Order-/Live-Autorität" in html


def test_market_dashboard_readonly_banner_markers(client: TestClient) -> None:
    market_html = _html(client, "/market")
    assert 'data-market-readonly="true"' in market_html
    assert 'data-market-non-authorizing="true"' in market_html


def test_market_dashboard_readonly_banner_chip_rhythm_v0(client: TestClient) -> None:
    """Top read-only banner uses grouped chip rows + rhythm marker; /market only."""
    html = _html(client, "/market")
    assert 'data-market-v0-readonly-banner-chip-rhythm-v0="true"' in html
    assert 'data-market-v0-readonly-banner-chip-rows-v0="true"' in html
    assert 'data-market-v0-readonly-banner-chip-divider-v0="true"' in html


def test_double_play_market_dashboard_excludes_market_readonly_banner_chip_rhythm_v0(
    client: TestClient,
) -> None:
    """Double-Play must not carry `/market` read-only banner rhythm contract markers."""
    html = _html(client, "/market/double-play")
    assert "data-market-v0-readonly-banner-chip-rhythm-v0" not in html
    assert "data-market-v0-readonly-banner-chip-rows-v0" not in html
    assert "data-market-v0-readonly-banner-chip-divider-v0" not in html


def test_market_dashboard_embedded_snapshot_generated_at_visibility_v0(
    client: TestClient,
) -> None:
    """Embedded OHLCV payload timestamp visible on `/market`; same field as SSR API surface."""
    html = _html(client, "/market")
    assert 'data-market-v0-embedded-snapshot-generated-at-v0="true"' in html
    assert "Snapshot bei Seitenladen" in html
    assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", html)


def test_double_play_market_dashboard_excludes_market_embedded_snapshot_generated_at_marker_v0(
    client: TestClient,
) -> None:
    """`/market`-specific embedded-snapshot marker must not leak onto Double-Play."""
    html = _html(client, "/market/double-play")
    assert "data-market-v0-embedded-snapshot-generated-at-v0" not in html


def test_market_dashboard_payload_meta_note_visibility_dummy_v0(client: TestClient) -> None:
    """Dummy OHLCV meta.note is surfaced on /market next to SSR snapshot cues (bounded)."""
    html = _html(client, "/market?source=dummy&timeframe=5m")
    assert 'data-market-v0-payload-meta-note-v0="true"' in html
    assert "Datenhinweis" in html
    assert "dummy: synthetische 1h-Bars" in html
    assert "nur kraken-pfad nutzt timeframe" in html.lower()


def test_double_play_market_dashboard_excludes_market_payload_meta_note_marker_v0(
    client: TestClient,
) -> None:
    """`/market` payload-meta marker must not appear on Double-Play."""
    html = _html(client, "/market/double-play")
    assert "data-market-v0-payload-meta-note-v0" not in html


@pytest.fixture()
def client_depth_fixture_bundle_on(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[TestClient]:
    """Offline depth SSR enabled pointing at repo fixture (deterministic timestamps via env)."""
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "1")
    bundle = (
        project_root / "tests" / "fixtures" / "market_depth_readmodel_v0" / "complete_minimal"
    ).resolve()
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT", str(bundle))
    monkeypatch.setenv("PEAK_TRADE_FIXED_GENERATED_AT_UTC", "2030-01-15T12:34:56.000000+00:00")
    with TestClient(create_app()) as test_client:
        yield test_client


def test_market_dashboard_depth_bundle_provenance_visibility_default_depth_disabled_v0(
    client: TestClient,
) -> None:
    """`/market`: depth envelope provenance is visible and distinct from OHLC snapshot wording."""
    html = _html(client, "/market?source=dummy")
    assert 'data-market-v0-depth-bundle-provenance-v0="true"' in html
    assert 'data-market-v0-depth-bundle-stale="true"' in html
    assert "Tiefen-Bundle-Provenienz" in html
    assert "Bundle-Zeitstempel" in html
    assert "offline_bundle_scan" not in html
    assert "source_disabled" in html
    assert "Snapshot bei Seitenladen" in html


def test_market_dashboard_depth_bundle_provenance_with_offline_fixture_stale_reason_v0(
    client_depth_fixture_bundle_on: TestClient,
) -> None:
    """SSR depth bundle path surfaces fixture stale_reason and deterministic generated_at_iso."""
    html = _html(client_depth_fixture_bundle_on, "/market?source=dummy")
    assert 'data-market-v0-depth-bundle-provenance-v0="true"' in html
    assert 'data-market-v0-depth-bundle-stale="true"' in html
    assert "2030-01-15T12:34:56.000000+00:00" in html
    assert "offline_bundle_scan" in html


def test_double_play_market_dashboard_excludes_market_depth_bundle_provenance_marker_v0(
    client: TestClient,
) -> None:
    """`/market`-only depth-bundle provenance marker must not leak onto Double-Play."""
    html = _html(client, "/market/double-play")
    assert "data-market-v0-depth-bundle-provenance-v0" not in html


def test_market_dashboard_depth_cockpit_tile_readmodel_identity_default_depth_disabled_v0(
    client: TestClient,
) -> None:
    """Visual Cockpit Depth tile echoes readmodel + bundle diagnostics from SSR context."""
    html = _html(client, "/market")
    assert 'data-market-v0-depth-tile-readmodel-identity-v0="true"' in html
    assert "market_depth_readmodel.v0" in html
    assert "Readmodel" in html
    assert "Bundle" in html
    assert "unavailable" in html


def test_market_dashboard_depth_cockpit_tile_readmodel_identity_fixture_bundle_v0(
    client_depth_fixture_bundle_on: TestClient,
) -> None:
    """Fixture depth SSR exposes dummy bundle label in cockpit depth tile."""
    html = _html(client_depth_fixture_bundle_on, "/market")
    assert 'data-market-v0-depth-tile-readmodel-identity-v0="true"' in html
    assert "market_depth_readmodel.v0" in html
    anchor = html.index("data-market-v0-depth-tile-readmodel-identity-v0")
    window = html[anchor : anchor + 900]
    assert "Bundle" in window
    assert "dummy" in window


def test_double_play_market_dashboard_excludes_depth_cockpit_readmodel_identity_marker_v0(
    client: TestClient,
) -> None:
    """`/market`-only cockpit-depth identity marker stays off Double-Play."""
    html = _html(client, "/market/double-play")
    assert "data-market-v0-depth-tile-readmodel-identity-v0" not in html


def test_market_dashboard_depth_cockpit_tile_topn_microtable_marker_default_depth_disabled_v0(
    client: TestClient,
) -> None:
    """Visual Cockpit Depth tile exposes SSR Top-N microtable anchor even when depth ladder empty."""
    html = _html(client, "/market")
    assert 'data-market-v0-depth-tile-topn-microtable-v0="true"' in html


def test_market_dashboard_depth_cockpit_tile_topn_microtable_fixture_prices_v0(
    client_depth_fixture_bundle_on: TestClient,
) -> None:
    """Fixture SSR renders bid/ask labels and deterministic fixture prices/sizes in cockpit tile."""
    html = _html(client_depth_fixture_bundle_on, "/market")
    assert 'data-market-v0-depth-tile-topn-microtable-v0="true"' in html
    anchor = html.index("data-market-v0-depth-tile-topn-microtable-v0")
    window = html[anchor : anchor + 4500]
    assert "Bid" in window
    assert "Ask" in window
    assert "63000" in window
    assert "0.5" in window
    assert "63030" in window
    assert "0.4" in window


def test_double_play_market_dashboard_excludes_depth_cockpit_topn_microtable_marker_v0(
    client: TestClient,
) -> None:
    """`/market`-only cockpit-depth Top-N microtable marker stays off Double-Play."""
    html = _html(client, "/market/double-play")
    assert "data-market-v0-depth-tile-topn-microtable-v0" not in html


def test_market_dashboard_depth_cockpit_tile_freshness_mirror_default_depth_disabled_v0(
    client: TestClient,
) -> None:
    """Cockpit Depth tile mirrors bundle freshness/stale cues without scanning lower SSR."""
    html = _html(client, "/market?source=dummy")
    assert 'data-market-v0-depth-tile-freshness-mirror-v0="true"' in html
    assert 'data-market-v0-depth-tile-freshness-stale="true"' in html
    anchor = html.index("data-market-v0-depth-tile-freshness-mirror-v0")
    window = html[anchor : anchor + 2800]
    assert "Depth bundle freshness (SSR)" in window
    assert "Stale (diag)" in window
    assert "source_disabled" in window
    assert "Not the embedded OHLC" in window


def test_market_dashboard_depth_cockpit_tile_freshness_mirror_fixture_bundle_v0(
    client_depth_fixture_bundle_on: TestClient,
) -> None:
    """Fixture SSR exposes deterministic bundle time + stale_reason inside cockpit mirror."""
    html = _html(client_depth_fixture_bundle_on, "/market?source=dummy")
    assert 'data-market-v0-depth-tile-freshness-mirror-v0="true"' in html
    assert 'data-market-v0-depth-tile-freshness-stale="true"' in html
    anchor = html.index("data-market-v0-depth-tile-freshness-mirror-v0")
    window = html[anchor : anchor + 1200]
    assert "2030-01-15T12:34:56.000000+00:00" in window
    assert "offline_bundle_scan" in window


def test_double_play_market_dashboard_excludes_depth_cockpit_freshness_mirror_marker_v0(
    client: TestClient,
) -> None:
    """`/market`-only cockpit freshness mirror stays off Double-Play."""
    html = _html(client, "/market/double-play")
    assert "data-market-v0-depth-tile-freshness-mirror-v0" not in html


def test_market_dashboard_depth_chart_placeholder_fixture_mini_bars_contract_v0(
    client_depth_fixture_bundle_on: TestClient,
) -> None:
    """Fixture SSR locks depth-chart placeholder mini bid/ask bars from offline bundle."""
    html = _html(client_depth_fixture_bundle_on, "/market")
    assert 'data-market-v0-depth-chart-placeholder="true"' in html
    placeholder_idx = html.index('data-market-v0-depth-chart-placeholder="true"')
    window = html[placeholder_idx : placeholder_idx + 6000]
    assert "Displayed top-level depth (static)" in window
    assert "Not cumulative" in window
    assert 'aria-label="Miniature SSR bid versus ask displayed sizes, top levels only"' in window
    assert "Bids (display)" in window
    assert "Asks (display)" in window
    assert "63000" in window
    assert "63030" in window
    assert "data-market-v0-depth-chart-disabled-envelope" not in window
    assert "fetch(" not in html
    assert "/api/market/depth" not in html


def test_market_dashboard_orderbook_fixture_levels_contract_v0(
    client_depth_fixture_bundle_on: TestClient,
) -> None:
    """Fixture SSR renders lower orderbook ladder with bid/ask rows from complete_minimal."""
    html = _html(client_depth_fixture_bundle_on, "/market")
    assert 'data-market-v0-orderbook-placeholder="true"' in html
    assert 'data-market-v0-lower-depth-orderbook-visuals-v1="true"' in html
    assert 'data-market-v0-orderbook-topn="true"' in html
    assert 'data-market-v0-orderbook-has-levels="true"' in html
    assert 'data-market-v0-orderbook-bids="true"' in html
    assert 'data-market-v0-orderbook-asks="true"' in html
    assert 'data-market-v0-orderbook-empty="true"' not in html

    topn_idx = html.index('data-market-v0-orderbook-topn="true"')
    window = html[topn_idx : topn_idx + 8000]
    placeholder_idx = html.index('data-market-v0-orderbook-placeholder="true"')
    header_window = html[placeholder_idx : topn_idx + 200]
    assert "Read-only · offline depth bundle" in header_window
    assert "63010" in window
    assert "63020" in window
    assert "63000" in window
    assert "63030" in window
    assert "Levels · bid-side (display only)" in window
    assert "Levels · ask-side (display only)" in window
    assert "Horizontal bars = displayed size" in window
    assert "fetch(" not in html
    assert "/api/market/depth" not in html
    assert 'data-market-readonly="true"' in html
    assert 'data-market-non-authorizing="true"' in html


def test_double_play_market_dashboard_excludes_depth_chart_placeholder_marker_v0(
    client: TestClient,
) -> None:
    """`/market`-only depth-chart placeholder marker stays off Double-Play."""
    html = _html(client, "/market/double-play")
    assert 'data-market-v0-depth-chart-placeholder="true"' not in html


def test_double_play_market_dashboard_excludes_orderbook_fixture_levels_markers_v0(
    client: TestClient,
) -> None:
    """`/market`-only fixture orderbook level markers stay off Double-Play."""
    html = _html(client, "/market/double-play")
    assert 'data-market-v0-orderbook-has-levels="true"' not in html
    assert 'data-market-v0-orderbook-bids="true"' not in html
    assert 'data-market-v0-orderbook-asks="true"' not in html


def test_market_dashboard_ranking_funnel_region_role_contract_v0(client: TestClient) -> None:
    """Ranking funnel section exposes role=region and aria-labelledby to landmark h2."""
    html = _html(client, "/market")
    assert re.search(
        r'id="market-v0-ranking-funnel-ssr"\s+role="region"\s+aria-labelledby="market-v0-landmark-ranking-funnel-h2"',
        html,
    )
    assert 'id="market-v0-landmark-ranking-funnel-h2"' in html
    assert 'data-market-v0-ranking-funnel-landmark-heading-v0="true"' in html


def test_double_play_market_dashboard_excludes_ranking_funnel_region_role_contract_v0(
    client: TestClient,
) -> None:
    html = _html(client, "/market/double-play")
    assert not re.search(
        r'id="market-v0-ranking-funnel-ssr"\s+role="region"\s+aria-labelledby="market-v0-landmark-ranking-funnel-h2"',
        html,
    )
    assert "market-v0-ranking-funnel-ssr" not in html
    assert "data-market-v0-ranking-funnel-landmark-heading-v0" not in html


def test_market_dashboard_ranking_funnel_empty_state_v0_marker(client: TestClient) -> None:
    """Contract-first funnel panel: stable marker only; no ranking data wired on /market."""
    market_html = _html(client, "/market")
    assert 'data-market-v0-ranking-funnel-empty-state-v0="true"' in market_html


def test_market_dashboard_ranking_funnel_dynamic_labels_v0_marker(client: TestClient) -> None:
    """Funnel stages use dynamic labels (no fixed final-count wording in UI contract)."""
    market_html = _html(client, "/market")
    assert 'data-market-v0-ranking-funnel-v0="true"' in market_html
    assert 'data-market-v0-ranking-funnel-dynamic-labels-v0="true"' in market_html
    assert 'data-market-v0-ranking-funnel-display-only-v0="true"' in market_html
    assert 'data-market-v0-ranking-funnel-label-text-v0="true"' in market_html
    for stage_key in ("universe", "shortlist", "selected"):
        assert f'data-market-v0-ranking-funnel-label-stage-v0="{stage_key}"' in market_html
    assert "Top Universe" in market_html
    assert "Shortlist" in market_html
    assert "Top Ranking / Selected Candidates" in market_html
    assert 'data-market-v0-ranking-funnel-non-authorizing-v0="true"' in market_html


def test_market_dashboard_ranking_funnel_dynamic_labels_excluded_on_double_play_v0(
    client: TestClient,
) -> None:
    """Double-Play must not carry /market-only ranking funnel dynamic-label SSR markers."""
    html = _html(client, "/market/double-play")
    assert 'data-market-v0-ranking-funnel-v0="true"' not in html
    assert "data-market-v0-ranking-funnel-label-stage-v0" not in html
    assert "data-market-v0-ranking-funnel-label-text-v0" not in html
    assert 'data-market-v0-ranking-funnel-display-only-v0="true"' not in html


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


def test_market_dashboard_ranking_funnel_and_pro_shell_marker_families_v0(
    client: TestClient,
) -> None:
    """Positive pairing: /market carries ranking funnel and pro-shell IA marker families."""
    html = _html(client, "/market")
    assert 'data-market-v0-ranking-funnel-empty-state-v0="true"' in html
    assert 'data-market-v0-ranking-funnel-v0="true"' in html
    assert 'data-market-v0-ranking-funnel-dynamic-labels-v0="true"' in html
    assert 'data-market-v0-ranking-funnel-display-only-v0="true"' in html
    assert 'data-market-v0-ranking-funnel-stages-v0="true"' in html
    assert 'id="market-v0-landmark-ranking-funnel-h2"' in html
    assert 'data-market-v0-pro-shell="true"' in html
    assert 'data-market-v0-pro-grid="true"' in html
    assert 'data-market-v0-pro-boundary="true"' in html
    assert 'data-market-v0-visual-cockpit="true"' in html


def test_double_play_market_dashboard_excludes_ranking_funnel_markers_v0(
    client: TestClient,
) -> None:
    """Double-Play must not carry `/market`-only ranking funnel contract markers."""
    html = _html(client, "/market/double-play")
    assert "data-market-v0-ranking-funnel-empty-state-v0" not in html
    assert "data-market-v0-ranking-funnel-dynamic-labels-v0" not in html
    assert "data-market-v0-ranking-funnel-label-stage-v0" not in html
    assert "data-market-v0-ranking-funnel-label-text-v0" not in html
    assert "data-market-v0-ranking-funnel-display-only-v0" not in html
    assert "data-market-v0-ranking-funnel-stages-v0" not in html
    assert "data-market-v0-ranking-funnel-has-rows-v0" not in html
    assert "data-market-v0-ranking-funnel-enabled-v0" not in html
    assert "data-market-v0-ranking-funnel-row-v0" not in html
    assert "data-market-v0-ranking-funnel-stage-rows-v0" not in html
    assert "market-v0-landmark-ranking-funnel-h2" not in html
    assert "market-v0-ranking-funnel-ssr" not in html
    assert "data-market-v0-ranking-funnel-landmark-heading-v0" not in html
    assert "data-market-v0-" not in html
    assert 'data-market-readonly="true"' in html


def test_double_play_excludes_ranking_funnel_when_depth_and_ranking_env_enabled_v0(
    client_depth_and_ranking_funnel_fixtures_on: TestClient,
) -> None:
    """Depth+ranking fixtures enabled still render dp depth only on /market/double-play."""
    html = _html(client_depth_and_ranking_funnel_fixtures_on, "/market/double-play")

    assert re.search(
        r'id="double-play-market-v0-depth-ssr"\s+role="region"\s+aria-labelledby="double-play-market-v0-landmark-depth-ssr-h2"',
        html,
    )
    assert 'data-double-play-market-depth-panel="true"' in html
    assert 'id="market-v0-depth-ssr"' not in html
    assert "data-market-v0-ranking-funnel" not in html
    assert 'id="market-v0-ranking-funnel-ssr"' not in html


def test_market_dashboard_ranking_funnel_rows_when_bundle_enabled_v0(
    client_ranking_funnel_fixture_bundle_on: TestClient,
) -> None:
    """Enabled ranking funnel with fixture bundle renders SSR rows on /market only."""
    html = _html(client_ranking_funnel_fixture_bundle_on, "/market")
    assert 'data-market-v0-ranking-funnel-enabled-v0="true"' in html
    assert 'data-market-v0-ranking-funnel-has-rows-v0="true"' in html
    assert 'data-market-v0-ranking-funnel-non-authorizing-v0="true"' in html
    assert 'data-market-v0-ranking-funnel-row-v0="true"' in html
    assert 'data-market-v0-ranking-funnel-stage-rows-v0="true"' in html
    assert 'data-market-v0-ranking-funnel-stage-v0="universe"' in html
    assert "BTCUSDT" in html
    assert 'data-market-v0-ranking-funnel-empty-state-v0="true"' not in html


def test_market_dashboard_ranking_funnel_non_authorizing_copy_when_rows_v0(
    client_ranking_funnel_fixture_bundle_on: TestClient,
) -> None:
    """Row rendering includes explicit non-authority copy."""
    html = _html(client_ranking_funnel_fixture_bundle_on, "/market")
    assert 'data-market-v0-ranking-funnel-readonly-copy-v0="true"' in html
    assert "does not authorize trades" in html


def test_market_dashboard_depth_and_ranking_funnel_coexistence_contract_v0(
    client_depth_and_ranking_funnel_fixtures_on: TestClient,
) -> None:
    """Depth/orderbook SSR and ranking funnel rows may coexist on /market without marker loss."""
    html = _html(client_depth_and_ranking_funnel_fixtures_on, "/market")

    assert re.search(
        r'id="market-v0-depth-ssr"\s+role="region"\s+aria-labelledby="market-v0-landmark-depth-ssr-h2"',
        html,
    )
    assert 'data-market-depth-panel="true"' in html
    assert 'data-market-depth-status="ok"' in html
    assert 'data-market-depth-readmodel-id="market_depth_readmodel.v0"' in html
    assert 'id="market-v0-orderbook-topn"' in html
    assert 'data-market-v0-orderbook-topn="true"' in html

    assert re.search(
        r'id="market-v0-ranking-funnel-ssr"\s+role="region"\s+aria-labelledby="market-v0-landmark-ranking-funnel-h2"',
        html,
    )
    assert 'data-market-v0-ranking-funnel-has-rows-v0="true"' in html
    assert 'data-market-v0-ranking-funnel-row-v0="true"' in html
    assert 'data-market-v0-ranking-funnel-stage-v0="universe"' in html
    assert 'data-market-v0-ranking-funnel-readonly-copy-v0="true"' in html
    assert 'data-market-v0-ranking-funnel-non-authorizing-v0="true"' in html


def test_market_dashboard_ranking_funnel_fail_closed_missing_bundle_v0(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Enabled gate with missing bundle stays read-only empty display (no 500)."""
    monkeypatch.setenv("PEAK_TRADE_MARKET_DEPTH_ENABLED", "0")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED", "1")
    monkeypatch.setenv(
        "PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT", "/tmp/nonexistent-ranking-bundle"
    )
    with TestClient(create_app()) as test_client:
        html = _html(test_client, "/market")
    assert 'data-market-v0-ranking-funnel-enabled-v0="true"' in html
    assert 'data-market-v0-ranking-funnel-has-rows-v0="true"' not in html
    assert 'data-market-v0-ranking-funnel-empty-state-v0="true"' in html


def test_double_play_market_dashboard_excludes_pro_shell_markers_v0(
    client: TestClient,
) -> None:
    """Double-Play must not carry `/market`-only pro-shell / visual-cockpit IA markers."""
    html = _html(client, "/market/double-play")
    assert "data-market-v0-pro-shell" not in html
    assert "data-market-v0-pro-grid" not in html
    assert "data-market-v0-pro-boundary" not in html
    assert "data-market-v0-visual-cockpit" not in html
    assert "market-v0-landmark-visual-cockpit-h2" not in html
    assert "data-market-v0-" not in html
    assert 'data-market-readonly="true"' in html


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
    assert 'data-market-v0-ranking-funnel-landmark-heading-v0="true"' in html
    assert 'aria-labelledby="market-v0-landmark-ranking-funnel-h2"' in html
    assert 'id="market-v0-ranking-funnel-ssr"' in html
    assert 'id="market-v0-landmark-visual-cockpit-h2"' in html
    assert 'data-market-v0-visual-cockpit-landmark-heading-v0="true"' in html
    assert 'aria-labelledby="market-v0-landmark-visual-cockpit-h2"' in html
    assert 'id="market-v0-landmark-surface-links-h2"' in html
    assert 'aria-labelledby="market-v0-landmark-surface-links-h2"' in html
    assert 'id="market-v0-landmark-data-rails-h2"' in html
    assert 'aria-labelledby="market-v0-landmark-data-rails-h2"' in html
    assert 'id="market-v0-landmark-query-context-h2"' in html
    assert 'aria-labelledby="market-v0-landmark-query-context-h2"' in html
    assert 'id="market-v0-landmark-close-chart-h2"' in html
    assert 'aria-labelledby="market-v0-landmark-close-chart-h2"' in html
    assert 'id="market-v0-landmark-depth-ssr-h2"' in html
    assert 'data-market-v0-depth-landmark-heading-v0="true"' in html
    assert 'aria-labelledby="market-v0-landmark-depth-ssr-h2"' in html
    assert 'id="market-v0-depth-ssr"' in html
    assert 'id="market-v0-landmark-orderbook-topn-h2"' in html
    assert 'data-market-v0-orderbook-landmark-heading-v0="true"' in html
    assert 'aria-labelledby="market-v0-landmark-orderbook-topn-h2"' in html
    assert 'id="market-v0-orderbook-topn"' in html
    assert 'id="market-v0-landmark-depth-chart-placeholder-h2"' in html
    assert 'data-market-v0-depth-chart-placeholder-landmark-heading-v0="true"' in html
    assert 'aria-labelledby="market-v0-landmark-depth-chart-placeholder-h2"' in html
    assert 'id="market-v0-depth-chart-placeholder"' in html
    assert 'data-market-readonly="true"' in html
    assert 'data-market-non-authorizing="true"' in html
    lowered = html.lower()
    assert "<form" not in lowered
    assert "<button" not in lowered


def test_market_dashboard_visual_cockpit_tile_landmark_groups_v0(
    client: TestClient,
) -> None:
    """Visual cockpit tiles use labelled role=group landmarks; safety tile is non-authorizing."""
    html = _html(client, "/market")
    assert 'data-market-v0-cockpit-tiles-grid-v0="true"' in html
    assert 'data-market-v0-cockpit-tile-landmark-heading-v0="true"' in html
    assert 'data-market-v0-cockpit-tile-readonly-v0="true"' in html
    assert 'data-market-v0-cockpit-tile-non-authorizing-v0="true"' in html
    for tile_id in (
        "market-v0-landmark-cockpit-tile-snapshot-h3",
        "market-v0-landmark-cockpit-tile-chart-h3",
        "market-v0-landmark-cockpit-tile-depth-h3",
        "market-v0-landmark-cockpit-tile-safety-h3",
    ):
        assert f'id="{tile_id}"' in html
        assert f'aria-labelledby="{tile_id}"' in html
    assert html.count('data-market-v0-cockpit-tile-landmark-heading-v0="true"') == 4
    assert html.count('data-market-v0-cockpit-tile-readonly-v0="true"') == 4
    assert html.count('role="group"') >= 4


def test_double_play_excludes_visual_cockpit_tile_landmark_groups_v0(
    client: TestClient,
) -> None:
    """Double-Play must not carry `/market`-only visual cockpit tile IA markers."""
    html = _html(client, "/market/double-play")
    assert "data-market-v0-cockpit-tiles-grid-v0" not in html
    assert "data-market-v0-cockpit-tile-landmark-heading-v0" not in html
    assert "market-v0-landmark-cockpit-tile-snapshot-h3" not in html
    assert "data-market-v0-cockpit-tile-non-authorizing-v0" not in html


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


def test_market_dashboard_run_projection_landmark_region_when_enabled_v0(
    tmp_path: Path,
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Run-projection SSR keeps IA/landmark parity when the env-gated overlay is enabled."""
    payload_path, _ = overlay_fixtures.write_ready_bundle(tmp_path / "bundle")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RUN_PROJECTION_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RUN_PROJECTION_PAYLOAD_JSON", str(payload_path))
    html = _html(client, "/market")

    assert re.search(
        r'role="region"[^>]*aria-labelledby="market-v0-landmark-run-projection-h2"',
        html,
    )
    assert 'id="market-v0-landmark-run-projection-h2"' in html
    assert 'data-market-v0-run-projection="true"' in html
    assert 'data-market-v0-run-projection-readonly="true"' in html
    assert 'data-market-v0-run-projection-authority="false"' in html
    assert "Registry run projection (read-only)" in html


def test_market_dashboard_run_projection_landmark_absent_when_disabled_v0(
    client: TestClient,
) -> None:
    """Run-projection landmark is absent when the env-gated overlay is disabled (default)."""
    html = _html(client, "/market")

    assert "market-v0-landmark-run-projection-h2" not in html
    assert 'data-market-v0-run-projection="true"' not in html


def test_double_play_market_dashboard_excludes_run_projection_landmark_v0(
    tmp_path: Path,
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Double-Play market surface must not inherit /market run-projection SSR landmarks."""
    payload_path, _ = overlay_fixtures.write_ready_bundle(tmp_path / "bundle")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RUN_PROJECTION_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_RUN_PROJECTION_PAYLOAD_JSON", str(payload_path))
    html = _html(client, "/market/double-play")

    assert "market-v0-landmark-run-projection-h2" not in html
    assert 'data-market-v0-run-projection="true"' not in html


def test_market_dashboard_tape_landmark_region_when_enabled_v0(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tape SSR keeps IA/landmark parity when the env-gated overlay is enabled."""
    fixture_root = (
        project_root / "tests" / "fixtures" / "market_tape_readmodel_v0" / "complete_minimal"
    )
    monkeypatch.setenv("PEAK_TRADE_MARKET_TAPE_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_TAPE_BUNDLE_ROOT", str(fixture_root.resolve()))
    html = _html(client, "/market")

    assert re.search(
        r'role="region"[^>]*aria-labelledby="market-v0-tape-ssr-h2"',
        html,
    )
    assert 'id="market-v0-tape-ssr"' in html
    assert 'data-market-v0-tape="true"' in html
    assert 'data-market-v0-tape-readonly="true"' in html
    assert 'data-market-v0-tape-authority="false"' in html
    assert "Market tape (read-only)" in html


def test_market_dashboard_tape_landmark_absent_when_disabled_v0(
    client: TestClient,
) -> None:
    """Tape landmark is absent when the env-gated overlay is disabled (default)."""
    html = _html(client, "/market")

    assert "market-v0-tape-ssr" not in html
    assert 'data-market-v0-tape="true"' not in html


def test_double_play_market_dashboard_excludes_tape_landmark_v0(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Double-Play market surface must not inherit /market tape SSR landmarks."""
    fixture_root = (
        project_root / "tests" / "fixtures" / "market_tape_readmodel_v0" / "complete_minimal"
    )
    monkeypatch.setenv("PEAK_TRADE_MARKET_TAPE_ENABLED", "1")
    monkeypatch.setenv("PEAK_TRADE_MARKET_TAPE_BUNDLE_ROOT", str(fixture_root.resolve()))
    html = _html(client, "/market/double-play")

    assert "market-v0-tape-ssr" not in html
    assert 'data-market-v0-tape="true"' not in html


MARKET_SURFACE_DOC = project_root / "docs" / "webui" / "MARKET_SURFACE_V0.md"
STRUCTURE_CONTRACT_OWNER = "tests/webui/test_market_dashboard_readonly_structure_contract_v0.py"
MARKET_DASHBOARD_MARKER_IA_CROSSWALK_DRIFT_LOCK_V0 = (
    "MARKET_DASHBOARD_MARKER_IA_CROSSWALK_DOCS_TEST_DRIFT_LOCK_V0=true"
)


def _market_surface_doc_text() -> str:
    assert MARKET_SURFACE_DOC.is_file()
    return MARKET_SURFACE_DOC.read_text(encoding="utf-8")


def _marker_ia_crosswalk_policy_section(surface: str) -> str:
    start = surface.index("### Marker / IA crosswalk policy v0")
    end = surface.index("## Market Surface v1 visual framing", start)
    return surface[start:end]


def test_market_surface_marker_ia_crosswalk_policy_docs_test_drift_lock_v0() -> None:
    """MARKET_SURFACE_V0 Marker/IA crosswalk policy stays locked to structure-contract owner."""
    surface = _market_surface_doc_text()
    crosswalk = _marker_ia_crosswalk_policy_section(surface)

    assert MARKET_DASHBOARD_MARKER_IA_CROSSWALK_DRIFT_LOCK_V0.endswith("=true")

    required_crosswalk_tokens = [
        "### Marker / IA crosswalk policy v0",
        "MARKET_SURFACE_V0.md` is the canonical product/contract surface",
        "not a complete attribute registry",
        "Current marker families are consolidated as:",
        "**Read-only / non-authority shell**",
        "**Depth / orderbook readmodel display**",
        "**Visual Cockpit tiles**",
        "not a separate dashboard surface",
        "**Ranking funnel empty-state / dynamic labels**",
        "**Registry run projection (env-gated SSR, `GET` `/market` only):**",
        "**never** on `GET` `/market/double-play`",
        "The canonical test owner for structural marker invariants is",
        STRUCTURE_CONTRACT_OWNER,
        "Avoid creating parallel marker registries",
        "duplicate docs",
        "separate evidence/readiness/map/handoff/package/pointer surfaces",
        "**Dashboard ≠ Freigabe**",
        "no marker may imply order UI",
        "Master V2 / Double Play authority",
    ]

    for token in required_crosswalk_tokens:
        assert token in crosswalk, f"missing crosswalk token: {token!r}"

    required_surface_tokens = [
        "**Route separation:**",
        "`GET` `/market/double-play`",
        "must **not** carry `/market`-only ranking-funnel dynamic-label SSR markers",
        "**Dashboard ≠ Freigabe** · **AI ≠ Authority** · **Signal ≠ Trade** · **Docs ≠ Approval**",
        "`GET &#47;market&#47;double-play`",
        "remains a separate Master V2 / Double Play read-only composition route",
        "**`data-market-depth-*`** auf **`/market`**, **`data-double-play-market-depth-*`** auf **`/market/double-play`**",
        "**keine** Marker-Vermischung",
        "review input only",
    ]

    for token in required_surface_tokens:
        assert token in surface, f"missing surface token: {token!r}"

    assert "market-airport" not in crosswalk.lower()
    assert "market airport" not in crosswalk.lower()


def test_market_surface_ranking_funnel_producer_charter_v0() -> None:
    """Market Ranking Funnel Producer v0 charter stays read-only and non-authorizing."""
    market_surface_doc = "docs/webui/MARKET_SURFACE_V0.md"
    surface = (project_root / market_surface_doc).read_text(encoding="utf-8")

    required_tokens = [
        "### Market Ranking Funnel Producer v0 (read-only charter)",
        "market_ranking_funnel_readmodel.v0",
        "PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED=1",
        "GET &#47;market",
        "&#47;market&#47;double-play",
        "&#47;api&#47;market&#47;ranking",
        "endpoint in v0",
        "tests/webui/test_market_dashboard_readonly_structure_contract_v0.py",
        "DASHBOARD_AUTHORITY_CHANGED=false",
        "RANKING_PRODUCER_AUTHORIZES_TRADES=false",
        "FuturesRankingSnapshot",
        "must not be directly wired",
        "non_authorizing=true",
        "universe",
        "shortlist",
        "selected",
    ]

    for token in required_tokens:
        assert token in surface

    forbidden_promotions = [
        "trade signal",
        "approval",
        "readiness",
        "live authorization",
        "strategy activation",
        "Master V2",
        "Double Play trading input",
    ]

    forbidden_section_start = surface.index("Forbidden promotions:")
    forbidden_section = surface[forbidden_section_start:]

    for token in forbidden_promotions:
        assert token in forbidden_section


def test_market_operator_overview_story_markers_v1(client: TestClient) -> None:
    """Operator overview redesign: story, system bar, chart primary, secondary guardrails."""
    html = _html(client, "/market")

    assert 'data-market-operator-overview-v1="true"' in html
    assert 'data-market-operator-story-v1="true"' in html
    assert 'data-market-operator-system-bar-v1="true"' in html
    assert 'data-market-live-locked-v1="true"' in html
    assert 'data-market-trading-authority-v1="false"' in html
    assert 'data-market-guardrails-secondary-v1="true"' in html
    assert 'data-market-diagnostics-secondary-v1="true"' in html
    assert 'data-market-chart-primary-v1="true"' in html
    assert 'data-market-top20-ranking-v1="true"' in html
    assert 'data-market-ranking-source-mode-v1="fixture_offline"' in html
    assert 'data-market-observe-strip-v1="true"' in html
    assert 'data-market-ai-decision-readout-v1="true"' in html
    assert 'data-market-double-play-status-v1="true"' in html
    assert 'data-market-operator-step-v1="observe"' in html
    assert 'data-market-operator-step-v1="rank"' in html
    assert 'data-market-operator-step-v1="explain"' in html

    lowered = html.lower()
    assert "place order" not in lowered
    assert "data-order-form" not in lowered


def test_market_operator_overview_ranking_table_with_fixture_v1(
    client_ranking_funnel_fixture_bundle_on: TestClient,
) -> None:
    html = _html(client_ranking_funnel_fixture_bundle_on, "/market")
    assert 'data-market-top20-table-v1="true"' in html
    assert 'data-market-ranking-source-mode-v1="existing_readmodel"' in html
    assert "BTCUSDT" in html


def test_double_play_operator_detail_redesign_markers_v1(client: TestClient) -> None:
    html = _html(client, "/market/double-play")

    assert 'data-double-play-operator-detail-v1="true"' in html
    assert 'data-double-play-bull-bear-cards-v1="true"' in html
    assert 'data-double-play-bull-card-v1="true"' in html
    assert 'data-double-play-bear-card-v1="true"' in html
    assert 'data-double-play-scope-capital-risk-v1="true"' in html
    assert 'data-double-play-diagnostics-secondary-v1="true"' in html
    assert 'data-double-play-market-depth-panel="true"' in html

    lowered = html.lower()
    assert "place order" not in lowered
