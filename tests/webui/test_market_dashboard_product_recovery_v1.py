"""Product recovery v1 — empty-state, CONFIGURED projection, DE locale, consumer-only."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.webui.app import app
from src.webui.market_surface import (
    _MATRIX_DISPLAY_STATUS_ALLOWLIST,
    _normalize_matrix_display_status,
)

REPO = Path(__file__).resolve().parents[2]
CHART = REPO / "templates/peak_trade_dashboard/partials/market_primary_close_chart_v1.html"
HERO = REPO / "templates/peak_trade_dashboard/partials/market_primary_operator_hero_v1.html"
WATCHLIST = REPO / "templates/peak_trade_dashboard/partials/market_watchlist_compact_v1.html"
LAYOUT_CSS = REPO / "static/css/peak_trade_dashboard_layout_v1.css"
REVIEW_SH = REPO / "scripts/webui/review_server.sh"


def test_display_ready_projects_configured_not_active() -> None:
    cat, label = _MATRIX_DISPLAY_STATUS_ALLOWLIST["display_ready"]
    assert cat == "configured"
    assert label == "CONFIGURED"
    cat2, label2 = _normalize_matrix_display_status("display_ready")
    assert cat2 == "configured"
    assert "Active" not in label2
    assert "ACTIVE" not in label2


def test_ready_projects_configured() -> None:
    cat, label = _MATRIX_DISPLAY_STATUS_ALLOWLIST["ready"]
    assert cat == "configured"
    assert label == "CONFIGURED"


def test_empty_chart_compact_markers_in_template() -> None:
    text = CHART.read_text(encoding="utf-8")
    assert 'data-market-chart-empty-compact-v1="true"' in text
    assert "min-h-[20rem]" not in text
    assert "Keine OHLCV" in text
    assert "Keine synthetischen Kerzen" in text
    assert "Marktchart" in text
    assert "Chart-Diagnostik (sekundär)" in text
    assert "Market chart" not in text
    assert "Chart diagnostics (secondary)" not in text
    assert "No OHLCV bars for this query" not in text


def test_layout_css_empty_chart_compact_override() -> None:
    css = LAYOUT_CSS.read_text(encoding="utf-8")
    assert "data-market-chart-empty-compact-v1" in css
    assert "8.5rem" in css


def test_hero_empty_and_decision_above_fold_markers() -> None:
    text = HERO.read_text(encoding="utf-8")
    assert "data-market-product-recovery-empty-hero-v1" in text
    assert "data-market-product-recovery-decision-above-fold-v1" in text
    assert "data-market-product-recovery-canonical-blocker-v1" in text
    assert "Governed Futures-Snapshot fehlt" in text or "Instrument-Kontext" in text
    assert "Kein Spot-OHLCV" in text
    assert "No spot OHLCV" not in text
    assert "is ranked #" not in text


def test_watchlist_german_locale() -> None:
    text = WATCHLIST.read_text(encoding="utf-8")
    assert "Weitere Märkte" in text
    assert "Additional markets not loaded" not in text


def test_review_server_fixture_binding_and_no_orphan_adopt() -> None:
    text = REVIEW_SH.read_text(encoding="utf-8")
    assert "PEAK_TRADE_WEBUI_REVIEW_BIND_FIXTURES" in text
    assert "adopt_identity_ok_listener_if_any" not in text
    assert "REVIEW_BIND_FIXTURES" in text


def test_market_unavailable_html_product_recovery_surface() -> None:
    client = TestClient(app)
    resp = client.get("/market?timeframe=1h")
    assert resp.status_code == 200
    body = resp.text
    assert 'data-market-readonly="true"' in body
    assert 'data-market-trading-authority-v1="false"' in body
    assert 'data-market-non-authorizing="true"' in body
    assert "data-market-chart-empty-compact-v1" in body
    assert "data-market-product-recovery-decision-above-fold-v1" in body
    assert "data-market-product-recovery-canonical-blocker-v1" in body
    assert "Keine OHLCV" in body
    # Double-play must not paint misleading Active for display_ready projection.
    assert ">Active<" not in body or 'data-matrix-status-category="configured"' in body
