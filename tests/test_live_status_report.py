# tests/test_live_status_report.py
"""
Tests für src/reporting/live_status_report.py (Phase 57)
========================================================

Testet die Formatter-Funktionen für Live-Status-Reports.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Pfad-Setup
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.reporting.live_status_report import (
    LiveStatusInput,
    build_html_report,
    build_markdown_report,
)

# =============================================================================
# Test Fixtures
# =============================================================================


def make_dummy_input() -> LiveStatusInput:
    """Erstellt Dummy-LiveStatusInput für Tests."""
    return LiveStatusInput(
        ts_iso="2025-12-07T09:00:00Z",
        config_path="config/config.toml",
        tag="daily",
        health={
            "overall_status": "OK",
            "config_ok": True,
            "config_errors": [],
            "exchange_ok": True,
            "exchange_errors": [],
            "alerts_enabled": True,
            "alert_sinks_configured": ["log", "slack_webhook"],
            "alert_config_warnings": [],
            "live_risk_ok": True,
            "live_risk_warnings": [],
        },
        portfolio={
            "as_of": "2025-12-07T09:00:00Z",
            "mode": "testnet",
            "free_cash": 4845.67,
            "positions": [
                {
                    "symbol": "BTCUSD",
                    "size": 0.1,
                    "side": "long",
                    "notional": 4000.0,
                    "unrealized_pnl": 120.5,
                },
                {
                    "symbol": "ETHUSD",
                    "size": 1.5,
                    "side": "long",
                    "notional": 3500.0,
                    "unrealized_pnl": -35.2,
                },
            ],
            "totals": {
                "num_open_positions": 2,
                "total_notional": 7500.0,
                "total_unrealized_pnl": 85.3,
                "total_realized_pnl": 0.0,
            },
            "symbol_notional": {
                "BTCUSD": 4000.0,
                "ETHUSD": 3500.0,
            },
            "risk": {
                "allowed": True,
                "reasons": [],
                "metrics": {},
            },
        },
    )


def make_dummy_input_degraded() -> LiveStatusInput:
    """Erstellt Dummy-LiveStatusInput mit DEGRADED-Status."""
    return LiveStatusInput(
        ts_iso="2025-12-07T09:00:00Z",
        config_path="config/config.toml",
        tag="weekly",
        health={
            "overall_status": "DEGRADED",
            "config_ok": True,
            "config_errors": [],
            "exchange_ok": True,
            "exchange_errors": [],
            "alerts_enabled": True,
            "alert_sinks_configured": ["log"],
            "alert_config_warnings": ["webhook URL fehlt"],
            "live_risk_ok": False,
            "live_risk_warnings": ["max_symbol_exposure > max_total_exposure"],
        },
        portfolio={
            "as_of": "2025-12-07T09:00:00Z",
            "mode": "testnet",
            "free_cash": 1000.0,
            "positions": [],
            "totals": {
                "num_open_positions": 0,
                "total_notional": 0.0,
                "total_unrealized_pnl": 0.0,
                "total_realized_pnl": 0.0,
            },
            "symbol_notional": {},
        },
    )


# =============================================================================
# Tests für build_markdown_report
# =============================================================================


def test_build_markdown_report_basic_structure():
    """Testet, dass der Markdown-Report die erwartete Grundstruktur hat."""
    data = make_dummy_input()
    md_text = build_markdown_report(data)

    # Header prüfen
    assert "# Peak_Trade Live Status Report" in md_text
    assert "Timestamp: 2025-12-07T09:00:00Z" in md_text
    assert "Config: `config/config.toml`" in md_text
    assert "Tag: `daily`" in md_text

    # Sektionen prüfen
    assert "## 1. Health Overview" in md_text
    assert "## 2. Portfolio Snapshot" in md_text
    assert "## 3. Risk & Alerts" in md_text
    assert "## 4. Notes (Operator)" in md_text

    # Overall Status prüfen
    assert "**Overall Status:** ✅ OK" in md_text


def test_build_markdown_report_health_checks():
    """Testet, dass Health-Checks korrekt dargestellt werden."""
    data = make_dummy_input()
    md_text = build_markdown_report(data)

    # Health-Check-Tabelle prüfen
    assert "| Check | Status | Details |" in md_text
    assert "| config | OK |" in md_text
    assert "| exchange | OK |" in md_text
    assert "| alerts | OK |" in md_text
    assert "| live_risk | OK |" in md_text


def test_build_markdown_report_portfolio_data():
    """Testet, dass Portfolio-Daten korrekt dargestellt werden."""
    data = make_dummy_input()
    md_text = build_markdown_report(data)

    # Portfolio-Mode prüfen
    assert "Mode: `testnet`" in md_text

    # Aggregate prüfen
    assert "### 2.1 Aggregate" in md_text
    assert "Equity:" in md_text
    assert "Total Exposure:" in md_text
    assert "Free Cash:" in md_text

    # Positions-Tabelle prüfen
    assert "### 2.2 Per-Symbol Exposure" in md_text
    assert "| Symbol | Position | Notional | Side | Unrealized PnL |" in md_text
    assert "BTCUSD" in md_text
    assert "ETHUSD" in md_text


def test_build_markdown_report_degraded_status():
    """Testet, dass DEGRADED-Status korrekt dargestellt wird."""
    data = make_dummy_input_degraded()
    md_text = build_markdown_report(data)

    # Overall Status prüfen
    assert "**Overall Status:** ⚠️ DEGRADED" in md_text

    # Warnings prüfen
    assert "webhook URL fehlt" in md_text
    assert "max_symbol_exposure > max_total_exposure" in md_text


def test_build_markdown_report_no_positions():
    """Testet, dass leeres Portfolio korrekt dargestellt wird."""
    data = make_dummy_input_degraded()
    md_text = build_markdown_report(data)

    assert "*(Keine offenen Positionen)*" in md_text


def test_build_markdown_report_with_notes():
    """Testet, dass Operator-Notizen korrekt eingefügt werden."""
    data = make_dummy_input()
    notes = "- [ ] TODO: Portfolio-Rebalance in 3 Tagen prüfen\n- [ ] TODO: Incident-Drill planen"
    md_text = build_markdown_report(data, notes=notes)

    assert "## 4. Notes (Operator)" in md_text
    assert "Portfolio-Rebalance" in md_text
    assert "Incident-Drill" in md_text


def test_build_markdown_report_without_notes():
    """Testet, dass Platzhalter angezeigt wird, wenn keine Notes vorhanden."""
    data = make_dummy_input()
    md_text = build_markdown_report(data, notes=None)

    assert "## 4. Notes (Operator)" in md_text
    assert "*(Optionaler Freitext" in md_text


# =============================================================================
# Tests für build_html_report
# =============================================================================


def test_build_html_report_basic_structure():
    """Testet, dass der HTML-Report die erwartete Grundstruktur hat."""
    data = make_dummy_input()
    html_text = build_html_report(data)

    # HTML-Struktur prüfen
    assert "<!DOCTYPE html>" in html_text
    assert "<html lang='de'>" in html_text
    assert "<head>" in html_text
    assert "<body>" in html_text
    assert "</body>" in html_text
    assert "</html>" in html_text

    # Titel prüfen
    assert "<h1>Peak_Trade Live Status Report</h1>" in html_text

    # Sektionen prüfen
    assert "<h2>1. Health Overview</h2>" in html_text
    assert "<h2>2. Portfolio Snapshot</h2>" in html_text
    assert "<h2>3. Risk & Alerts</h2>" in html_text
    assert "<h2>4. Notes (Operator)</h2>" in html_text


def test_build_html_report_tables():
    """Testet, dass Tabellen korrekt gerendert werden."""
    data = make_dummy_input()
    html_text = build_html_report(data)

    # Health-Check-Tabelle prüfen
    assert "<table>" in html_text
    assert "<thead>" in html_text
    assert "<th>Check</th>" in html_text
    assert "<th>Status</th>" in html_text
    assert "<th>Details</th>" in html_text

    # Positions-Tabelle prüfen
    assert "<th>Symbol</th>" in html_text
    assert "<th>Position</th>" in html_text
    assert "BTCUSD" in html_text


def test_build_html_report_css_styles():
    """Testet, dass CSS-Styles vorhanden sind."""
    data = make_dummy_input()
    html_text = build_html_report(data)

    assert "<style>" in html_text
    assert "font-family" in html_text
    assert "table" in html_text
    assert "status-ok" in html_text
    assert "status-warn" in html_text
    assert "status-fail" in html_text


def test_build_html_report_with_notes():
    """Testet, dass Operator-Notizen korrekt eingefügt werden."""
    data = make_dummy_input()
    notes = "- [ ] TODO: Test-Notiz"
    html_text = build_html_report(data, notes=notes)

    assert "<h2>4. Notes (Operator)</h2>" in html_text
    assert "<pre>" in html_text
    assert "Test-Notiz" in html_text


def test_build_html_report_without_notes():
    """Testet, dass Platzhalter angezeigt wird, wenn keine Notes vorhanden."""
    data = make_dummy_input()
    html_text = build_html_report(data, notes=None)

    assert "<h2>4. Notes (Operator)</h2>" in html_text
    assert "<em>(Optionaler Freitext" in html_text





