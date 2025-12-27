#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/run_live_dry_run_drills.py
"""
Peak_Trade: Live-Dry-Run Drills & Safety-Validation CLI (Phase 73)
===================================================================

CLI zum Ausführen von Sicherheits-Drills im Dry-Run-Modus.

WICHTIG: Phase 73 - Read-Only Simulation
    - Keine Config-Dateien ändern
    - Keine echten Orders
    - Keine Exchange-API-Calls
    - Nur Simulation & Validierung

Usage:
    python scripts/run_live_dry_run_drills.py
    python scripts/run_live_dry_run_drills.py --scenario "A - Voll gebremst"
    python scripts/run_live_dry_run_drills.py --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.live.drills import (
    LiveDrillRunner,
    get_default_live_drill_scenarios,
)


def format_drill_report_text(results: list) -> str:
    """
    Formatiert Drill-Report als Text.

    Args:
        results: Liste von LiveDrillResult-Objekten

    Returns:
        Formatierter Report als String
    """
    lines = []

    # Header
    lines.append("=" * 70)
    lines.append("Peak_Trade - Live-Dry-Run Drills & Safety-Validation (Phase 73)")
    lines.append("=" * 70)
    lines.append("Phase 73 – Read-Only Simulation, keine echten Orders")
    lines.append("")

    # Übersicht
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    lines.append("─" * 70)
    lines.append("Übersicht")
    lines.append("─" * 70)
    lines.append(f"Anzahl Drills:            {total}")
    lines.append(f"Bestanden:                {passed} ✓")
    lines.append(f"Fehlgeschlagen:           {failed} ✗")
    lines.append("")

    # Pro Drill
    for result in results:
        lines.append("─" * 70)
        lines.append(f"Drill: {result.scenario_name}")
        lines.append("─" * 70)
        lines.append(f"Status:                  {'✓ PASSED' if result.passed else '✗ FAILED'}")
        lines.append(f"is_live_execution_allowed: {result.is_live_execution_allowed}")
        lines.append(f"Reason:                  {result.reason}")
        lines.append(f"Effective Mode:          {result.effective_mode}")
        lines.append("")

        if result.notes:
            lines.append("Details:")
            for note in result.notes:
                lines.append(f"  • {note}")
            lines.append("")

        if result.violations:
            lines.append("⚠️  Violations:")
            for violation in result.violations:
                lines.append(f"  ✗ {violation}")
            lines.append("")

    # Footer
    lines.append("=" * 70)
    lines.append("Phase 73: Alle Drills sind Simulationen im Dry-Run-Modus.")
    lines.append("Keine echten Orders werden gesendet, keine Config-Dateien geändert.")
    lines.append("=" * 70)

    return "\n".join(lines)


def format_drill_report_json(results: list) -> str:
    """
    Formatiert Drill-Report als JSON.

    Args:
        results: Liste von LiveDrillResult-Objekten

    Returns:
        JSON-String
    """
    data = {
        "phase": "73",
        "description": "Live-Dry-Run Drills & Safety-Validation",
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r.passed),
            "failed": sum(1 for r in results if not r.passed),
        },
        "results": [
            {
                "scenario_name": r.scenario_name,
                "passed": r.passed,
                "is_live_execution_allowed": r.is_live_execution_allowed,
                "reason": r.reason,
                "effective_mode": r.effective_mode,
                "notes": r.notes,
                "violations": r.violations,
            }
            for r in results
        ],
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def build_parser() -> argparse.ArgumentParser:
    """Baut den Argument-Parser."""
    parser = argparse.ArgumentParser(
        prog="run_live_dry_run_drills",
        description="Peak_Trade Live-Dry-Run Drills & Safety-Validation CLI (Phase 73)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Alle Standard-Drills ausführen
  python scripts/run_live_dry_run_drills.py

  # Nur einen bestimmten Drill
  python scripts/run_live_dry_run_drills.py --scenario "A - Voll gebremst"

  # JSON-Output
  python scripts/run_live_dry_run_drills.py --format json

WICHTIG: Phase 73 - Read-Only Simulation
  • Keine Config-Dateien ändern
  • Keine echten Orders
  • Keine Exchange-API-Calls
  • Nur Simulation & Validierung
        """,
    )

    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Nur einen bestimmten Drill ausführen (Name oder Teil-String)",
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output-Format (Default: text)",
    )

    return parser


def main() -> int:
    """Hauptfunktion."""
    parser = build_parser()
    args = parser.parse_args()

    try:
        # Standard-Szenarien laden
        all_scenarios = get_default_live_drill_scenarios()

        # Szenarien filtern (wenn --scenario angegeben)
        scenarios = all_scenarios
        if args.scenario:
            scenarios = [s for s in all_scenarios if args.scenario.lower() in s.name.lower()]
            if not scenarios:
                print(
                    f"ERROR: Kein Drill gefunden mit Name '{args.scenario}'",
                    file=sys.stderr,
                )
                print(f"Verfügbare Drills:", file=sys.stderr)
                for s in all_scenarios:
                    print(f"  - {s.name}", file=sys.stderr)
                return 1

        # Drill-Runner erstellen und ausführen
        runner = LiveDrillRunner()
        results = runner.run_all(scenarios)

        # Report formatieren und ausgeben
        if args.format == "json":
            report = format_drill_report_json(results)
        else:
            report = format_drill_report_text(results)

        print(report)

        # Exit-Code: 0 wenn alle bestanden, 1 wenn mindestens einer fehlgeschlagen
        all_passed = all(r.passed for r in results)
        return 0 if all_passed else 1

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

