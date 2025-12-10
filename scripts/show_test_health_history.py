#!/usr/bin/env python3
"""
Peak_Trade Test Health History CLI
==================================

Zeigt Health-Score-Historie und Trend-Statistiken.

Usage:
    python scripts/show_test_health_history.py --profile weekly_core
    python scripts/show_test_health_history.py --profile daily_quick --days 7
    python scripts/show_test_health_history.py --all

Stand: Dezember 2024
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure src is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ops.test_health_history import (
    load_history,
    get_history_stats,
    print_history_summary,
    _get_default_history_path,
)


def parse_args() -> argparse.Namespace:
    """Parst Command-Line-Argumente."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Test Health History CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Historie für spezifisches Profil
  python scripts/show_test_health_history.py --profile weekly_core

  # Letzte 7 Tage
  python scripts/show_test_health_history.py --profile daily_quick --days 7

  # Alle Profile
  python scripts/show_test_health_history.py --all

  # Raw-Daten als JSON
  python scripts/show_test_health_history.py --profile weekly_core --json
        """,
    )

    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help="Name des Profils (z.B. 'weekly_core')",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Zeige Historie für alle Profile",
    )

    parser.add_argument(
        "--days",
        type=int,
        default=14,
        help="Zeitraum in Tagen (default: 14)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Ausgabe als JSON statt formatierter Text",
    )

    parser.add_argument(
        "--history-file",
        type=str,
        default=None,
        help="Pfad zur history.json (default: reports/test_health/history.json)",
    )

    return parser.parse_args()


def main() -> int:
    """Hauptfunktion."""
    args = parse_args()

    history_path = Path(args.history_file) if args.history_file else None

    if not args.profile and not args.all:
        print("❌ Bitte --profile oder --all angeben.")
        print("   Beispiel: python scripts/show_test_health_history.py --profile weekly_core")
        return 1

    # Check if history file exists
    check_path = history_path or _get_default_history_path()
    if not check_path.exists():
        print(f"⚠️ Keine Historie gefunden: {check_path}")
        print("   Führe zuerst einige Test-Health-Runs aus:")
        print("   python scripts/run_test_health_profile.py --profile weekly_core")
        return 0

    if args.all:
        # Lade alle Einträge und finde unique Profile
        entries = load_history(history_path, profile_name=None, days=args.days)
        profiles = sorted(set(e.profile_name for e in entries))

        if not profiles:
            print(f"Keine Einträge in den letzten {args.days} Tagen.")
            return 0

        print(f"\n📊 Test Health Historie – Alle Profile (letzte {args.days} Tage)")
        print("=" * 70)

        for profile in profiles:
            if args.json:
                import json
                stats = get_history_stats(profile, args.days, history_path)
                print(json.dumps(stats, indent=2))
            else:
                print_history_summary(profile, args.days, history_path)

    else:
        # Einzelnes Profil
        if args.json:
            import json
            stats = get_history_stats(args.profile, args.days, history_path)
            print(json.dumps(stats, indent=2))
        else:
            print_history_summary(args.profile, args.days, history_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
