#!/usr/bin/env python3
"""
Peak_Trade: Live Run Report Generator CLI (Phase 32)
====================================================

Generiert Markdown- oder HTML-Reports aus Shadow-/Paper-Run-Logs.

Usage:
    # Report für spezifischen Run generieren
    python -m scripts.generate_live_run_report live_runs/20251204_180000_paper_ma_crossover_BTC-EUR_1m

    # HTML-Format
    python -m scripts.generate_live_run_report live_runs/RUN_ID --format html

    # In Datei speichern
    python -m scripts.generate_live_run_report live_runs/RUN_ID --output report.md

    # Alle Runs auflisten
    python -m scripts.generate_live_run_report --list

    # Letzten Run anzeigen
    python -m scripts.generate_live_run_report --latest
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

# Projekt-Root zum Path hinzufügen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.reporting.live_run_report import (
    build_live_run_report,
    load_and_build_report,
    save_report,
)
from src.live.run_logging import list_runs, load_run_metadata


def main() -> int:
    """
    Haupteinstiegspunkt für Live Run Report Generator.

    Returns:
        Exit-Code (0 = Success, 1 = Error)
    """
    parser = argparse.ArgumentParser(
        description="Generate reports from Peak_Trade Shadow/Paper run logs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Report für spezifischen Run:
  python -m scripts.generate_live_run_report live_runs/20251204_180000_paper_ma_crossover_BTC-EUR_1m

  # Als HTML speichern:
  python -m scripts.generate_live_run_report live_runs/RUN_ID --format html --output report.html

  # Alle Runs auflisten:
  python -m scripts.generate_live_run_report --list

  # Letzten Run anzeigen:
  python -m scripts.generate_live_run_report --latest
        """,
    )

    parser.add_argument(
        "run_dir",
        type=str,
        nargs="?",
        default=None,
        help="Pfad zum Run-Verzeichnis (z.B. live_runs/RUN_ID)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["markdown", "html"],
        default="markdown",
        help="Output-Format (default: markdown)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Ausgabe-Datei (default: stdout)",
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default="live_runs",
        help="Basis-Verzeichnis für Runs (default: live_runs)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Alle verfügbaren Runs auflisten",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Report für den neuesten Run generieren",
    )
    parser.add_argument(
        "--no-trades",
        action="store_true",
        help="Trade-Liste nicht anzeigen",
    )
    parser.add_argument(
        "--max-trades",
        type=int,
        default=50,
        help="Maximale Anzahl angezeigter Trades (default: 50)",
    )

    args = parser.parse_args()

    try:
        # Liste aller Runs
        if args.list:
            return list_all_runs(args.base_dir)

        # Letzten Run finden
        run_dir: Optional[Path] = None
        if args.latest:
            runs = list_runs(args.base_dir)
            if not runs:
                print(f"Keine Runs gefunden in: {args.base_dir}", file=sys.stderr)
                return 1
            run_dir = Path(args.base_dir) / runs[0]
            print(f"Neuester Run: {runs[0]}", file=sys.stderr)
        elif args.run_dir:
            run_dir = Path(args.run_dir)
        else:
            print("Fehler: Kein Run-Verzeichnis angegeben.", file=sys.stderr)
            print("Verwende --list um verfügbare Runs zu sehen.", file=sys.stderr)
            return 1

        if not run_dir.exists():
            print(f"Run-Verzeichnis nicht gefunden: {run_dir}", file=sys.stderr)
            return 1

        # Report generieren
        print(f"Generiere Report für: {run_dir}", file=sys.stderr)

        report = load_and_build_report(run_dir)

        # Output
        if args.format == "html":
            content = report.to_html()
        else:
            content = report.to_markdown()

        if args.output:
            output_path = Path(args.output)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Report gespeichert: {output_path}", file=sys.stderr)
        else:
            print(content)

        return 0

    except FileNotFoundError as e:
        print(f"Datei nicht gefunden: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"Fehler: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


def list_all_runs(base_dir: str) -> int:
    """
    Listet alle verfügbaren Runs auf.

    Args:
        base_dir: Basis-Verzeichnis

    Returns:
        Exit-Code
    """
    runs = list_runs(base_dir)

    if not runs:
        print(f"Keine Runs gefunden in: {base_dir}")
        return 0

    print(f"Verfügbare Runs in '{base_dir}' ({len(runs)} gefunden):")
    print("-" * 60)

    for run_id in runs:
        run_dir = Path(base_dir) / run_id
        try:
            meta = load_run_metadata(run_dir)
            print(
                f"  {run_id}\n"
                f"    Strategy: {meta.strategy_name}, Symbol: {meta.symbol}, "
                f"Mode: {meta.mode}"
            )
            if meta.started_at:
                print(f"    Started: {meta.started_at}")
        except Exception:
            print(f"  {run_id} (Metadaten nicht lesbar)")

    print("-" * 60)
    print(f"Total: {len(runs)} Runs")

    return 0


if __name__ == "__main__":
    sys.exit(main())
