"""Reductive Market Dashboard composition contracts (fail-closed above-the-fold)."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

from src.webui.app import app

REPO = Path(__file__).resolve().parents[2]
HERO = REPO / "templates/peak_trade_dashboard/partials/market_primary_operator_hero_v1.html"
CHART = REPO / "templates/peak_trade_dashboard/partials/market_primary_close_chart_v1.html"
LAYOUT_CSS = REPO / "static/css/peak_trade_dashboard_layout_v1.css"


def test_reductive_markers_in_templates() -> None:
    hero = HERO.read_text(encoding="utf-8")
    chart = CHART.read_text(encoding="utf-8")
    css = LAYOUT_CSS.read_text(encoding="utf-8")
    assert "data-market-reductive-primary-surface-v1" in hero
    assert "data-market-reductive-secondary-surface-v1" in chart
    assert "pt-reductive-primary-surface" in css
    assert "max-height: 240px" in css
    assert "pt-operator-decision-card" not in hero
    assert "pt-operator-primary-status-card" not in hero


def test_blocker_and_action_precede_chart_in_template() -> None:
    hero = HERO.read_text(encoding="utf-8")
    blocker_i = hero.find("data-market-product-primary-blocker-v1")
    action_i = hero.find("data-market-product-operator-action-v1")
    chart_include_i = hero.find('include "partials/market_primary_close_chart_v1.html"')
    assert min(blocker_i, action_i, chart_include_i) >= 0
    assert blocker_i < chart_include_i
    assert action_i < chart_include_i


def test_tech_details_default_closed_in_template() -> None:
    hero = HERO.read_text(encoding="utf-8")
    m = re.search(r"<details[^>]*data-market-product-tech-details-v1=\"true\"[^>]*>", hero)
    assert m is not None
    assert " open" not in m.group(0)


def test_no_nested_empty_chart_frame_in_template() -> None:
    chart = CHART.read_text(encoding="utf-8")
    # Empty branch must not open an inner bordered frame.
    empty_branch = chart.split("{% if chart_empty %}", 1)[1].split("{% else %}", 1)[0]
    assert "data-market-v0-close-chart-integrated-frame" not in empty_branch
    assert "rounded-lg border" not in empty_branch
    assert "Chart-Diagnostik" not in empty_branch


def test_ranking_f5_gated_to_snapshot_available() -> None:
    hero = HERO.read_text(encoding="utf-8")
    assert "governed_top20.snapshot_available" in hero
    assert "data-market-reductive-ranking-below-fold-v1" in hero


def test_fail_closed_html_reductive_surface() -> None:
    client = TestClient(app)
    resp = client.get("/market?timeframe=1h")
    assert resp.status_code == 200
    body = resp.text
    assert 'data-market-reductive-primary-surface-v1="true"' in body
    assert 'data-market-reductive-secondary-surface-v1="true"' in body
    assert "Marktdaten nicht verfügbar" in body
    assert "BLOCKIERT" in body
    assert "Datenquelle prüfen oder später erneut laden" in body
    assert "Keine Orders · Kein Live · Read-only" in body
    assert body.count("data-market-product-primary-blocker-v1") == 1
    assert body.count("data-market-product-operator-action-v1") == 1
    assert 'data-market-chart-empty-compact-v1="true"' in body
    assert "data-market-workspace-ranking-f5-compact-v1" not in body
    assert 'data-market-reductive-deferred-modules-v1="true"' in body
    m_def = re.search(
        r"<details[^>]*data-market-reductive-deferred-modules-v1=\"true\"[^>]*>", body
    )
    assert m_def is not None
    assert " open" not in m_def.group(0)
    m = re.search(r"<details[^>]*data-market-product-tech-details-v1=\"true\"[^>]*>", body)
    assert m is not None
    assert " open" not in m.group(0)
    primary_i = body.find("data-market-reductive-primary-surface-v1")
    chart_i = body.find("data-market-reductive-secondary-surface-v1")
    assert 0 <= primary_i < chart_i
