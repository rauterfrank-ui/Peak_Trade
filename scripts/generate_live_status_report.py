#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/generate_live_status_report.py
"""
Peak_Trade: Live Status Report Generator (Phase 57)
====================================================

Generiert Daily/Weekly Live-Status-Reports (Markdown/HTML) basierend auf
live_ops health und portfolio Commands.

Usage:
    python scripts/generate_live_status_report.py \
      --config config/config.toml \
      --output-dir reports/live_status \
      --format both \
      --tag daily \
      --notes-file docs/live_status_notes.md
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Projekt-Root zum Python-Path hinzufügen
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.reporting.live_status_report import LiveStatusInput, build_html_report, build_markdown_report


def build_parser() -> argparse.ArgumentParser:
    """Baut den Argument-Parser."""
    parser = argparse.ArgumentParser(
        prog="generate_live_status_report",
        description="Peak_Trade Live Status Report Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Daily-Report (Markdown only)
  python scripts/generate_live_status_report.py \\
    --config config/config.toml \\
    --output-dir reports/live_status \\
    --format markdown \\
    --tag daily

  # Weekly-Report (Markdown + HTML)
  python scripts/generate_live_status_report.py \\
    --config config/config.toml \\
    --output-dir reports/live_status \\
    --format both \\
    --tag weekly

  # Report mit Operator-Notizen
  python scripts/generate_live_status_report.py \\
    --config config/config.toml \\
    --output-dir reports/live_status \\
    --format markdown \\
    --tag daily \\
    --notes-file docs/live_status_notes.md
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Config-Datei (Default: config/config.toml)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports/live_status",
        help="Ausgabe-Verzeichnis für Reports (Default: reports/live_status)",
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["markdown", "html", "both"],
        default="markdown",
        help="Report-Format (Default: markdown)",
    )

    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Optionaler Tag für den Report (z.B. 'daily', 'weekly', 'incident')",
    )

    parser.add_argument(
        "--notes-file",
        type=str,
        default=None,
        help="Optionaler Pfad zu einer Datei mit Operator-Notizen",
    )

    return parser


def run_subprocess_json(command: list[str]) -> Dict[str, Any]:
    """
    Führt ein Subprocess-Command aus und parst JSON-Ausgabe.

    Args:
        command: Liste von Command-Argumenten

    Returns:
        Parsed JSON als Dict

    Raises:
        SystemExit: Bei Fehlern
    """
    import subprocess

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )

        # Parse JSON
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"❌ Fehler beim Parsen der JSON-Ausgabe: {e}", file=sys.stderr)
            print(f"   Command: {' '.join(command)}", file=sys.stderr)
            print(f"   Output: {result.stdout[:500]}", file=sys.stderr)
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler beim Ausführen des Commands: {e}", file=sys.stderr)
        print(f"   Command: {' '.join(command)}", file=sys.stderr)
        if e.stderr:
            print(f"   Stderr: {e.stderr[:500]}", file=sys.stderr)
        sys.exit(1)


def load_notes(notes_file: str | None) -> str | None:
    """
    Lädt Operator-Notizen aus einer Datei.

    Args:
        notes_file: Pfad zur Notes-Datei

    Returns:
        Inhalt der Datei oder None
    """
    if notes_file is None:
        return None

    notes_path = Path(notes_file)
    if not notes_path.exists():
        print(f"⚠️  Notes-Datei nicht gefunden: {notes_file}", file=sys.stderr)
        return None

    try:
        return notes_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"⚠️  Fehler beim Lesen der Notes-Datei: {e}", file=sys.stderr)
        return None


def main() -> int:
    """Hauptfunktion."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        # 1. Timestamp & Output-Pfade bestimmen
        now = datetime.utcnow()
        timestamp_iso = now.isoformat() + "Z"
        timestamp_file = now.strftime("%Y-%m-%d_%H%M")

        tag_suffix = f"_{args.tag}" if args.tag else ""
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 2. Health- & Portfolio-Daten via live_ops holen
        config_path = Path(args.config).resolve()

        if not config_path.exists():
            print(f"❌ Config-Datei nicht gefunden: {config_path}", file=sys.stderr)
            return 1

        print("📊 Sammle Health-Daten...", file=sys.stderr)
        health_data = run_subprocess_json(
            [sys.executable, "scripts/live_ops.py", "health", "--config", str(config_path), "--json"]
        )

        print("📊 Sammle Portfolio-Daten...", file=sys.stderr)
        portfolio_data = run_subprocess_json(
            [sys.executable, "scripts/live_ops.py", "portfolio", "--config", str(config_path), "--json"]
        )

        # 3. Notes laden (optional)
        notes = load_notes(args.notes_file)

        # 4. LiveStatusInput aufbauen & Formatter aufrufen
        data = LiveStatusInput(
            ts_iso=timestamp_iso,
            config_path=str(config_path),
            tag=args.tag,
            health=health_data,
            portfolio=portfolio_data,
        )

        generated_files = []

        if args.format in ("markdown", "both"):
            md_text = build_markdown_report(data, notes=notes)
            md_file = output_dir / f"live_status_{timestamp_file}{tag_suffix}.md"
            md_file.write_text(md_text, encoding="utf-8")
            generated_files.append(md_file)
            print(f"✅ Markdown-Report erstellt: {md_file}", file=sys.stderr)

        if args.format in ("html", "both"):
            html_text = build_html_report(data, notes=notes)
            html_file = output_dir / f"live_status_{timestamp_file}{tag_suffix}.html"
            html_file.write_text(html_text, encoding="utf-8")
            generated_files.append(html_file)
            print(f"✅ HTML-Report erstellt: {html_file}", file=sys.stderr)

        # 5. CLI-Exit mit Summary
        overall_status = health_data.get("overall_status", "UNKNOWN")
        totals = portfolio_data.get("totals", {})
        total_exposure = totals.get("total_notional", 0.0)

        print("", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        print("📋 Live Status Report Summary", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        print(f"Overall Status: {overall_status}", file=sys.stderr)
        print(f"Total Exposure: {total_exposure:,.2f}", file=sys.stderr)
        print(f"Generated Files: {len(generated_files)}", file=sys.stderr)
        for f in generated_files:
            print(f"  - {f}", file=sys.stderr)

        return 0

    except KeyboardInterrupt:
        print("\n❌ Abgebrochen durch Benutzer", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"❌ Fehler: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())


