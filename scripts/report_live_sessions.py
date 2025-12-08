#!/usr/bin/env python3
"""
Peak_Trade: Live Session Registry Report CLI (Phase 81)
========================================================

Command-Line-Interface zum Generieren von Reports aus der Live-Session-Registry.

Dieses Tool liest Session-Records aus der Registry und erzeugt Markdown-
und/oder HTML-Reports.

Usage:
    # Alle Sessions als Markdown-Report:
    python scripts/report_live_sessions.py

    # Nur Shadow-Sessions:
    python scripts/report_live_sessions.py --run-type live_session_shadow

    # Nur abgeschlossene Sessions:
    python scripts/report_live_sessions.py --status completed

    # Limit auf letzte 10 Sessions:
    python scripts/report_live_sessions.py --limit 10

    # HTML-Report generieren:
    python scripts/report_live_sessions.py --output-format html

    # Beide Formate:
    python scripts/report_live_sessions.py --output-format both

    # Nur Summary (keine Einzel-Reports):
    python scripts/report_live_sessions.py --summary-only

    # Report nach stdout:
    python scripts/report_live_sessions.py --stdout

    # Report in spezifisches Verzeichnis:
    python scripts/report_live_sessions.py --output-dir reports/custom/
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Projekt-Root zum Path hinzufuegen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# Logging Setup
# =============================================================================


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Konfiguriert Logging fuer CLI."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    return logging.getLogger("report_live_sessions")


# =============================================================================
# Summary Formatter
# =============================================================================


def format_summary_markdown(summary: dict) -> str:
    """Formatiert Summary als Markdown-String."""
    lines = [
        "# Live-Session Registry Summary",
        "",
        f"**Anzahl Sessions:** {summary.get('num_sessions', 0)}",
        "",
    ]

    # Status-Breakdown
    by_status = summary.get("by_status", {})
    if by_status:
        lines.append("## Sessions nach Status")
        lines.append("")
        for status, count in sorted(by_status.items()):
            lines.append(f"- **{status}:** {count}")
        lines.append("")

    # Metrics
    total_pnl = summary.get("total_realized_pnl")
    avg_dd = summary.get("avg_max_drawdown")

    if total_pnl is not None or avg_dd is not None:
        lines.append("## Aggregierte Metriken")
        lines.append("")
        if total_pnl is not None:
            lines.append(f"- **Total Realized PnL:** {total_pnl:.2f}")
        if avg_dd is not None:
            lines.append(f"- **Avg Max Drawdown:** {avg_dd:.4f}")
        lines.append("")

    # Zeitraum
    first_started = summary.get("first_started_at")
    last_started = summary.get("last_started_at")

    if first_started or last_started:
        lines.append("## Zeitraum")
        lines.append("")
        if first_started:
            lines.append(f"- **Erste Session:** {first_started}")
        if last_started:
            lines.append(f"- **Letzte Session:** {last_started}")
        lines.append("")

    return "\n".join(lines)


def format_summary_html(summary: dict) -> str:
    """Formatiert Summary als HTML-String."""
    num_sessions = summary.get("num_sessions", 0)
    by_status = summary.get("by_status", {})
    total_pnl = summary.get("total_realized_pnl")
    avg_dd = summary.get("avg_max_drawdown")
    first_started = summary.get("first_started_at")
    last_started = summary.get("last_started_at")

    status_rows = ""
    for status, count in sorted(by_status.items()):
        status_rows += f"<tr><td>{status}</td><td>{count}</td></tr>\n"

    metrics_section = ""
    if total_pnl is not None or avg_dd is not None:
        metrics_section = "<h2>Aggregierte Metriken</h2><ul>"
        if total_pnl is not None:
            metrics_section += f"<li><strong>Total Realized PnL:</strong> {total_pnl:.2f}</li>"
        if avg_dd is not None:
            metrics_section += f"<li><strong>Avg Max Drawdown:</strong> {avg_dd:.4f}</li>"
        metrics_section += "</ul>"

    time_section = ""
    if first_started or last_started:
        time_section = "<h2>Zeitraum</h2><ul>"
        if first_started:
            time_section += f"<li><strong>Erste Session:</strong> {first_started}</li>"
        if last_started:
            time_section += f"<li><strong>Letzte Session:</strong> {last_started}</li>"
        time_section += "</ul>"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Live-Session Registry Summary</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #555; margin-top: 20px; }}
        table {{ border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f4f4f4; }}
        ul {{ list-style-type: none; padding-left: 0; }}
        li {{ margin: 5px 0; }}
    </style>
</head>
<body>
    <h1>Live-Session Registry Summary</h1>
    <p><strong>Anzahl Sessions:</strong> {num_sessions}</p>

    <h2>Sessions nach Status</h2>
    <table>
        <tr><th>Status</th><th>Anzahl</th></tr>
        {status_rows}
    </table>

    {metrics_section}
    {time_section}
</body>
</html>"""
    return html


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> int:
    """
    Haupteinstiegspunkt fuer Live Session Report CLI.

    Returns:
        Exit-Code (0 = Success, 1 = Error)
    """
    parser = argparse.ArgumentParser(
        description="Generate reports from Peak_Trade Live Session Registry (Phase 81).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Alle Sessions als Markdown-Report:
  python scripts/report_live_sessions.py

  # Nur Shadow-Sessions:
  python scripts/report_live_sessions.py --run-type live_session_shadow

  # Nur abgeschlossene Sessions:
  python scripts/report_live_sessions.py --status completed

  # Limit auf letzte 10 Sessions:
  python scripts/report_live_sessions.py --limit 10

  # HTML-Report generieren:
  python scripts/report_live_sessions.py --output-format html

  # Nur Summary:
  python scripts/report_live_sessions.py --summary-only

  # Report nach stdout:
  python scripts/report_live_sessions.py --stdout
        """,
    )

    # Filter-Optionen
    parser.add_argument(
        "--run-type",
        type=str,
        default=None,
        help="Filter nach Run-Type (z.B. live_session_shadow, live_session_testnet)",
    )
    parser.add_argument(
        "--status",
        type=str,
        default=None,
        help="Filter nach Status (z.B. completed, failed, aborted)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit auf N neueste Sessions",
    )

    # Output-Optionen
    parser.add_argument(
        "--output-format",
        type=str,
        default="markdown",
        choices=["markdown", "html", "both"],
        help="Output-Format: markdown, html, oder both (default: markdown)",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Nur Summary generieren (keine Einzel-Session-Reports)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Verzeichnis fuer Output-Dateien (default: reports/experiments/live_sessions/)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Report nach stdout ausgeben (keine Datei schreiben)",
    )

    # Logging
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log-Level (default: INFO)",
    )

    args = parser.parse_args()

    # Logging setup
    logger = setup_logging(args.log_level)

    # Imports hier um Startup-Zeit zu optimieren
    from src.experiments.live_session_registry import (
        list_session_records,
        get_session_summary,
        render_sessions_markdown,
        render_sessions_html,
        DEFAULT_LIVE_SESSION_DIR,
    )

    logger.info("=" * 60)
    logger.info("Peak_Trade: Live Session Registry Report (Phase 81)")
    logger.info("=" * 60)

    # Output-Verzeichnis bestimmen
    output_dir = Path(args.output_dir) if args.output_dir else DEFAULT_LIVE_SESSION_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sessions laden
    logger.info("Lade Sessions aus Registry...")
    logger.info(f"  Filter: run_type={args.run_type}, status={args.status}, limit={args.limit}")

    records = list_session_records(
        run_type=args.run_type,
        status=args.status,
        limit=args.limit,
    )

    logger.info(f"  {len(records)} Sessions gefunden")

    # Keine Sessions gefunden?
    if not records:
        msg = "Keine Sessions gefunden mit den angegebenen Filtern."
        logger.warning(msg)

        if args.stdout:
            print(f"\n{msg}\n")
        else:
            # Leeren Report schreiben
            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
            if args.output_format in ("markdown", "both"):
                empty_md = f"# Live-Session Report\n\n{msg}\n"
                md_path = output_dir / f"{timestamp}_sessions_report.md"
                md_path.write_text(empty_md, encoding="utf-8")
                logger.info(f"Leerer Report geschrieben: {md_path}")

        return 0

    # Summary generieren?
    if args.summary_only:
        logger.info("Generiere Summary...")
        summary = get_session_summary(run_type=args.run_type)

        if args.stdout:
            if args.output_format in ("markdown", "both"):
                print(format_summary_markdown(summary))
            if args.output_format == "html":
                print(format_summary_html(summary))
        else:
            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
            if args.output_format in ("markdown", "both"):
                md_content = format_summary_markdown(summary)
                md_path = output_dir / f"{timestamp}_sessions_summary.md"
                md_path.write_text(md_content, encoding="utf-8")
                logger.info(f"Summary (Markdown) geschrieben: {md_path}")

            if args.output_format in ("html", "both"):
                html_content = format_summary_html(summary)
                html_path = output_dir / f"{timestamp}_sessions_summary.html"
                html_path.write_text(html_content, encoding="utf-8")
                logger.info(f"Summary (HTML) geschrieben: {html_path}")

        return 0

    # Vollstaendige Reports generieren
    logger.info("Generiere Reports...")

    if args.stdout:
        if args.output_format in ("markdown", "both"):
            md_content = render_sessions_markdown(records)
            print(md_content)
        if args.output_format == "html":
            html_content = render_sessions_html(records)
            print(html_content)
    else:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

        if args.output_format in ("markdown", "both"):
            md_content = render_sessions_markdown(records)
            md_path = output_dir / f"{timestamp}_sessions_report.md"
            md_path.write_text(md_content, encoding="utf-8")
            logger.info(f"Report (Markdown) geschrieben: {md_path}")
            print(f"Markdown-Report: {md_path}")

        if args.output_format in ("html", "both"):
            html_content = render_sessions_html(records)
            html_path = output_dir / f"{timestamp}_sessions_report.html"
            html_path.write_text(html_content, encoding="utf-8")
            logger.info(f"Report (HTML) geschrieben: {html_path}")
            print(f"HTML-Report: {html_path}")

    logger.info("=" * 60)
    logger.info("Report-Generierung abgeschlossen")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
