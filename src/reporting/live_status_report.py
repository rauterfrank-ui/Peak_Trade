# src/reporting/live_status_report.py
"""
Peak_Trade Live Status Report Formatter (Phase 57)
===================================================

Formatter-Funktionen für Live-Status-Reports (Markdown/HTML).

Dieses Modul stellt pure Python-Funktionen bereit, die aus bereits vorliegenden
Datenstrukturen (dict aus JSON der `live_ops`-Kommandos) Markdown-/HTML-Strings generieren.

Usage:
    from src.reporting.live_status_report import LiveStatusInput, build_markdown_report

    data = LiveStatusInput(
        ts_iso="2025-12-07T09:00:00Z",
        config_path="config/config.toml",
        tag="daily",
        health={"overall_status": "OK", ...},
        portfolio={"as_of": "...", "positions": [...], ...},
    )
    md_text = build_markdown_report(data, notes="Optional notes")
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LiveStatusInput:
    """Input-Datenstruktur für Live-Status-Reports."""

    ts_iso: str
    config_path: str
    tag: Optional[str]
    health: Dict[str, Any]
    portfolio: Dict[str, Any]


def build_markdown_report(data: LiveStatusInput, notes: Optional[str] = None) -> str:
    """
    Baut einen Markdown-Report aus Live-Status-Daten.

    Args:
        data: LiveStatusInput mit Health- und Portfolio-Daten
        notes: Optionaler Freitext für Operator-Notizen

    Returns:
        Markdown-formatierter Report-String
    """
    lines = []

    # Header
    lines.append("# Peak_Trade Live Status Report")
    lines.append("")
    lines.append(f"- Timestamp: {data.ts_iso}")
    lines.append(f"- Config: `{data.config_path}`")
    if data.tag:
        lines.append(f"- Tag: `{data.tag}`")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 1. Health Overview
    lines.append("## 1. Health Overview")
    lines.append("")
    overall_status = data.health.get("overall_status", "UNKNOWN")
    status_emoji = {"OK": "✅", "DEGRADED": "⚠️", "FAIL": "❌"}.get(overall_status, "❓")
    lines.append(f"**Overall Status:** {status_emoji} {overall_status}")
    lines.append("")
    lines.append("| Check | Status | Details |")
    lines.append("|-------|--------|---------|")

    # Config Check
    config_ok = data.health.get("config_ok", False)
    config_status = "OK" if config_ok else "FAIL"
    config_details = (
        "Config geladen" if config_ok else ", ".join(data.health.get("config_errors", []))
    )
    lines.append(f"| config | {config_status} | {config_details} |")

    # Exchange Check
    exchange_ok = data.health.get("exchange_ok", False)
    exchange_status = "OK" if exchange_ok else "FAIL"
    exchange_details = (
        "Exchange verbunden" if exchange_ok else ", ".join(data.health.get("exchange_errors", []))
    )
    lines.append(f"| exchange | {exchange_status} | {exchange_details} |")

    # Alerts Check
    alerts_enabled = data.health.get("alerts_enabled", False)
    alerts_status = "OK" if alerts_enabled else "WARN"
    alert_sinks = data.health.get("alert_sinks_configured", [])
    alerts_details = (
        f"{len(alert_sinks)} Sink(s) konfiguriert" if alert_sinks else "Keine Sinks konfiguriert"
    )
    if data.health.get("alert_config_warnings"):
        alerts_details += f" ({', '.join(data.health['alert_config_warnings'])})"
    lines.append(f"| alerts | {alerts_status} | {alerts_details} |")

    # Live Risk Check
    live_risk_ok = data.health.get("live_risk_ok", False)
    live_risk_status = "OK" if live_risk_ok else "WARN"
    live_risk_details = "Limits geladen, keine Errors"
    if data.health.get("live_risk_warnings"):
        live_risk_details = ", ".join(data.health["live_risk_warnings"])
    lines.append(f"| live_risk | {live_risk_status} | {live_risk_details} |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # 2. Portfolio Snapshot
    lines.append("## 2. Portfolio Snapshot")
    lines.append("")

    portfolio = data.portfolio
    mode = portfolio.get("mode", "unknown")
    as_of = portfolio.get("as_of", "N/A")
    lines.append(f"- Mode: `{mode}`")
    lines.append(f"- As of: `{as_of}`")
    lines.append("")

    # 2.1 Aggregate
    lines.append("### 2.1 Aggregate")
    lines.append("")

    totals = portfolio.get("totals", {})
    total_exposure = totals.get("total_notional", 0.0)
    free_cash = portfolio.get("free_cash", None)
    if free_cash is None:
        # Fallback: Schätze free_cash basierend auf Exposure
        free_cash = total_exposure * 0.3 if total_exposure > 0 else 0.0
    equity = total_exposure + free_cash

    lines.append(f"- Equity: {_format_number(equity)}")
    lines.append(f"- Total Exposure: {_format_number(total_exposure)}")
    lines.append(f"- Free Cash: {_format_number(free_cash)}")
    lines.append("")

    # 2.2 Per-Symbol Exposure
    lines.append("### 2.2 Per-Symbol Exposure")
    lines.append("")

    positions = portfolio.get("positions", [])
    if positions:
        lines.append("| Symbol | Position | Notional | Side | Unrealized PnL |")
        lines.append("|--------|----------|----------|------|-----------------|")

        for pos in positions:
            symbol = pos.get("symbol", "N/A")
            size = pos.get("size", 0.0)
            notional = pos.get("notional", 0.0)
            side = pos.get("side", "flat")
            unrealized_pnl = pos.get("unrealized_pnl", 0.0)

            if side != "flat":
                lines.append(
                    f"| {symbol} | {size:.4f} | {_format_number(notional)} | {side} | {_format_number(unrealized_pnl, sign=True)} |"
                )
        lines.append("")
    else:
        lines.append("*(Keine offenen Positionen)*")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 3. Risk & Alerts
    lines.append("## 3. Risk & Alerts")
    lines.append("")

    risk = portfolio.get("risk")
    if risk:
        allowed = risk.get("allowed", True)
        reasons = risk.get("reasons", [])
        if allowed and not reasons:
            lines.append("- Live-Risk Limits: ✅ Innerhalb definierter Grenzen")
        else:
            lines.append(
                f"- Live-Risk Limits: ⚠️ {'Nicht erlaubt' if not allowed else 'Warnungen vorhanden'}"
            )
            if reasons:
                lines.append(f"  - Gründe: {', '.join(reasons)}")
    else:
        lines.append("- Live-Risk Limits: ℹ️ Keine Risk-Check-Daten verfügbar")

    lines.append(f"- Letzter Risk-Check: Health-Check {'OK' if live_risk_ok else 'WARN'}")

    # Alerts (vereinfacht, da wir keine Alert-Historie haben)
    lines.append("- Alerts (letzte Periode):")
    lines.append("  - ℹ️ Keine Alert-Historie im aktuellen System verfügbar")
    lines.append("  - Hinweis: Prüfe Logs für aktuelle Alerts")

    lines.append("")
    lines.append("---")
    lines.append("")

    # 4. Notes (Operator)
    lines.append("## 4. Notes (Operator)")
    lines.append("")

    if notes:
        lines.append(notes)
    else:
        lines.append("*(Optionaler Freitext – z.B. aus --notes-file oder manuell ergänzt)*")

    lines.append("")

    return "\n".join(lines)


def build_html_report(data: LiveStatusInput, notes: Optional[str] = None) -> str:
    """
    Baut einen HTML-Report aus Live-Status-Daten.

    Args:
        data: LiveStatusInput mit Health- und Portfolio-Daten
        notes: Optionaler Freitext für Operator-Notizen

    Returns:
        HTML-formatierter Report-String
    """
    lines = []

    # HTML Header
    lines.append("<!DOCTYPE html>")
    lines.append("<html lang='de'>")
    lines.append("<head>")
    lines.append("  <meta charset='UTF-8'>")
    lines.append("  <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
    lines.append("  <title>Peak_Trade Live Status Report</title>")
    lines.append("  <style>")
    lines.append("    body { font-family: Arial, sans-serif; margin: 20px; }")
    lines.append("    h1 { color: #2c3e50; }")
    lines.append(
        "    h2 { color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 5px; }"
    )
    lines.append("    h3 { color: #7f8c8d; }")
    lines.append("    table { border-collapse: collapse; width: 100%; margin: 10px 0; }")
    lines.append("    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
    lines.append("    th { background-color: #3498db; color: white; }")
    lines.append("    tr:nth-child(even) { background-color: #f2f2f2; }")
    lines.append("    .status-ok { color: #27ae60; }")
    lines.append("    .status-warn { color: #f39c12; }")
    lines.append("    .status-fail { color: #e74c3c; }")
    lines.append("    .metadata { background-color: #ecf0f1; padding: 10px; border-radius: 5px; }")
    lines.append("  </style>")
    lines.append("</head>")
    lines.append("<body>")

    # Title
    lines.append("  <h1>Peak_Trade Live Status Report</h1>")
    lines.append("")

    # Metadata
    lines.append("  <div class='metadata'>")
    lines.append(f"    <p><strong>Timestamp:</strong> {data.ts_iso}</p>")
    lines.append(f"    <p><strong>Config:</strong> <code>{data.config_path}</code></p>")
    if data.tag:
        lines.append(f"    <p><strong>Tag:</strong> <code>{data.tag}</code></p>")
    lines.append("  </div>")
    lines.append("")

    # 1. Health Overview
    lines.append("  <h2>1. Health Overview</h2>")
    overall_status = data.health.get("overall_status", "UNKNOWN")
    status_class = {"OK": "status-ok", "DEGRADED": "status-warn", "FAIL": "status-fail"}.get(
        overall_status, ""
    )
    lines.append(
        f"  <p><strong>Overall Status:</strong> <span class='{status_class}'>{overall_status}</span></p>"
    )
    lines.append("")

    lines.append("  <table>")
    lines.append("    <thead>")
    lines.append("      <tr><th>Check</th><th>Status</th><th>Details</th></tr>")
    lines.append("    </thead>")
    lines.append("    <tbody>")

    # Config Check
    config_ok = data.health.get("config_ok", False)
    config_status = "OK" if config_ok else "FAIL"
    config_details = (
        "Config geladen" if config_ok else ", ".join(data.health.get("config_errors", []))
    )
    lines.append(f"      <tr><td>config</td><td>{config_status}</td><td>{config_details}</td></tr>")

    # Exchange Check
    exchange_ok = data.health.get("exchange_ok", False)
    exchange_status = "OK" if exchange_ok else "FAIL"
    exchange_details = (
        "Exchange verbunden" if exchange_ok else ", ".join(data.health.get("exchange_errors", []))
    )
    lines.append(
        f"      <tr><td>exchange</td><td>{exchange_status}</td><td>{exchange_details}</td></tr>"
    )

    # Alerts Check
    alerts_enabled = data.health.get("alerts_enabled", False)
    alerts_status = "OK" if alerts_enabled else "WARN"
    alert_sinks = data.health.get("alert_sinks_configured", [])
    alerts_details = (
        f"{len(alert_sinks)} Sink(s) konfiguriert" if alert_sinks else "Keine Sinks konfiguriert"
    )
    if data.health.get("alert_config_warnings"):
        alerts_details += f" ({', '.join(data.health['alert_config_warnings'])})"
    lines.append(f"      <tr><td>alerts</td><td>{alerts_status}</td><td>{alerts_details}</td></tr>")

    # Live Risk Check
    live_risk_ok = data.health.get("live_risk_ok", False)
    live_risk_status = "OK" if live_risk_ok else "WARN"
    live_risk_details = "Limits geladen, keine Errors"
    if data.health.get("live_risk_warnings"):
        live_risk_details = ", ".join(data.health["live_risk_warnings"])
    lines.append(
        f"      <tr><td>live_risk</td><td>{live_risk_status}</td><td>{live_risk_details}</td></tr>"
    )

    lines.append("    </tbody>")
    lines.append("  </table>")
    lines.append("")

    # 2. Portfolio Snapshot
    lines.append("  <h2>2. Portfolio Snapshot</h2>")
    portfolio = data.portfolio
    mode = portfolio.get("mode", "unknown")
    as_of = portfolio.get("as_of", "N/A")
    lines.append(f"  <p><strong>Mode:</strong> <code>{mode}</code></p>")
    lines.append(f"  <p><strong>As of:</strong> <code>{as_of}</code></p>")
    lines.append("")

    # 2.1 Aggregate
    lines.append("  <h3>2.1 Aggregate</h3>")
    totals = portfolio.get("totals", {})
    total_exposure = totals.get("total_notional", 0.0)
    free_cash = portfolio.get("free_cash", None)
    if free_cash is None:
        # Fallback: Schätze free_cash basierend auf Exposure
        free_cash = total_exposure * 0.3 if total_exposure > 0 else 0.0
    equity = total_exposure + free_cash

    lines.append("  <ul>")
    lines.append(f"    <li><strong>Equity:</strong> {_format_number(equity)}</li>")
    lines.append(f"    <li><strong>Total Exposure:</strong> {_format_number(total_exposure)}</li>")
    lines.append(f"    <li><strong>Free Cash:</strong> {_format_number(free_cash)}</li>")
    lines.append("  </ul>")
    lines.append("")

    # 2.2 Per-Symbol Exposure
    lines.append("  <h3>2.2 Per-Symbol Exposure</h3>")
    positions = portfolio.get("positions", [])
    if positions:
        lines.append("  <table>")
        lines.append("    <thead>")
        lines.append(
            "      <tr><th>Symbol</th><th>Position</th><th>Notional</th><th>Side</th><th>Unrealized PnL</th></tr>"
        )
        lines.append("    </thead>")
        lines.append("    <tbody>")

        for pos in positions:
            symbol = pos.get("symbol", "N/A")
            size = pos.get("size", 0.0)
            notional = pos.get("notional", 0.0)
            side = pos.get("side", "flat")
            unrealized_pnl = pos.get("unrealized_pnl", 0.0)

            if side != "flat":
                lines.append(
                    f"      <tr><td>{symbol}</td><td>{size:.4f}</td><td>{_format_number(notional)}</td>"
                    f"<td>{side}</td><td>{_format_number(unrealized_pnl, sign=True)}</td></tr>"
                )

        lines.append("    </tbody>")
        lines.append("  </table>")
    else:
        lines.append("  <p><em>(Keine offenen Positionen)</em></p>")
    lines.append("")

    # 3. Risk & Alerts
    lines.append("  <h2>3. Risk & Alerts</h2>")
    lines.append("  <ul>")

    risk = portfolio.get("risk")
    if risk:
        allowed = risk.get("allowed", True)
        reasons = risk.get("reasons", [])
        if allowed and not reasons:
            lines.append(
                "    <li><strong>Live-Risk Limits:</strong> <span class='status-ok'>✅ Innerhalb definierter Grenzen</span></li>"
            )
        else:
            lines.append(
                f"    <li><strong>Live-Risk Limits:</strong> <span class='status-warn'>⚠️ {'Nicht erlaubt' if not allowed else 'Warnungen vorhanden'}</span></li>"
            )
            if reasons:
                lines.append(f"      <ul><li>Gründe: {', '.join(reasons)}</li></ul>")
    else:
        lines.append(
            "    <li><strong>Live-Risk Limits:</strong> ℹ️ Keine Risk-Check-Daten verfügbar</li>"
        )

    lines.append(
        f"    <li><strong>Letzter Risk-Check:</strong> Health-Check {'OK' if live_risk_ok else 'WARN'}</li>"
    )
    lines.append("    <li><strong>Alerts (letzte Periode):</strong>")
    lines.append("      <ul>")
    lines.append("        <li>ℹ️ Keine Alert-Historie im aktuellen System verfügbar</li>")
    lines.append("        <li>Hinweis: Prüfe Logs für aktuelle Alerts</li>")
    lines.append("      </ul>")
    lines.append("    </li>")
    lines.append("  </ul>")
    lines.append("")

    # 4. Notes
    lines.append("  <h2>4. Notes (Operator)</h2>")
    if notes:
        lines.append(f"  <pre>{notes}</pre>")
    else:
        lines.append(
            "  <p><em>(Optionaler Freitext – z.B. aus --notes-file oder manuell ergänzt)</em></p>"
        )

    lines.append("")
    lines.append("</body>")
    lines.append("</html>")

    return "\n".join(lines)


def _format_number(value: float, sign: bool = False) -> str:
    """Formatiert eine Zahl mit Tausender-Trennzeichen."""
    if value is None:
        return "N/A"
    formatted = f"{value:,.2f}"
    if sign and value != 0:
        formatted = f"{'+' if value > 0 else ''}{formatted}"
    return formatted
