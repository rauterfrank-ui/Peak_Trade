#!/usr/bin/env python3
"""
Strategy-Switch Sanity Check CLI für Peak_Trade.

Governance-Prüfung für die [live_profile.strategy_switch] Konfiguration.
Prüft:
  1. active_strategy_id ist in der allowed-Liste
  2. Keine R&D-Strategien (tier=r_and_d / is_live_ready=False) in allowed
  3. Keine unbekannten Strategy-IDs in allowed (gegen Registry validiert)

Exit-Codes:
  0 = OK (alles gesund)
  1 = FAIL (kritische Violations)
  2 = WARN (Warnungen, aber nicht kritisch)

Beispiel:
  python scripts/run_strategy_switch_sanity_check.py --config config/config.toml
  python scripts/run_strategy_switch_sanity_check.py --json

Stand: Dezember 2024
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

# Ensure src is in path (for imports to work)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def main() -> int:
    """
    Hauptfunktion für den Strategy-Switch Sanity Check.

    Returns:
        Exit-Code: 0=OK, 1=FAIL, 2=WARN
    """
    parser = argparse.ArgumentParser(
        description="Run Strategy-Switch Sanity Check for live_profile.",
        epilog="Exit-Codes: 0=OK, 1=FAIL, 2=WARN",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/config.toml"),
        help="Pfad zur Haupt-Config-Datei (default: config/config.toml)",
    )
    parser.add_argument(
        "--section",
        type=str,
        default="live_profile.strategy_switch",
        help="TOML-Pfad zur strategy_switch Sektion (default: live_profile.strategy_switch)",
    )
    parser.add_argument(
        "--max-allowed",
        type=int,
        default=5,
        help="Anzahl Strategien in allowed ab der WARN gemeldet wird (default: 5)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Ausgabe als JSON statt formatiertem Text",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Nur Exit-Code ausgeben, keine Textausgabe",
    )
    args = parser.parse_args()

    # Import hier, damit CLI-Parse-Fehler schneller sichtbar sind
    from src.governance.strategy_switch_sanity_check import (
        print_result,
        run_strategy_switch_sanity_check,
    )

    # Check ausführen
    result = run_strategy_switch_sanity_check(
        config_path=str(args.config),
        section_path=args.section,
        max_allowed_strategies_warn=args.max_allowed,
    )

    # Ausgabe
    if args.json:
        data = asdict(result)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif not args.quiet:
        print_result(result)

    # Exit-Code entsprechend Status
    if result.status == "FAIL":
        return 1
    elif result.status == "WARN":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
