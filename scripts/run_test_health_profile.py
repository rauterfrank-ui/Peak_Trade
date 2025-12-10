#!/usr/bin/env python3
"""
Peak_Trade Test Health Profile Runner (CLI)
============================================

Command-Line-Interface für Test Health Automation.

Usage:
    python scripts/run_test_health_profile.py
    python scripts/run_test_health_profile.py --profile weekly_core
    python scripts/run_test_health_profile.py --profile daily_quick --config config/test_health_profiles.toml

Zweck:
  - Lädt Test-Health-Profil aus TOML-Config
  - Führt alle definierten Checks aus
  - Erzeugt Reports (JSON, Markdown, HTML)
  - Gibt Health-Score und Exit-Code zurück

Exit-Codes:
  - 0: Alle Checks erfolgreich (failed_checks == 0)
  - 1: Mindestens ein Check fehlgeschlagen

Stand: Dezember 2024
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure src is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ops.test_health_runner import run_test_health_profile


def parse_args() -> argparse.Namespace:
    """Parst Command-Line-Argumente."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Test Health Profile Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Default-Profil (weekly_core) ausführen
  python scripts/run_test_health_profile.py

  # Spezifisches Profil ausführen
  python scripts/run_test_health_profile.py --profile daily_quick

  # Custom-Config und Report-Root
  python scripts/run_test_health_profile.py \\
      --profile full_suite \\
      --config config/test_health_profiles.toml \\
      --report-root reports/test_health
        """,
    )

    parser.add_argument(
        "--profile",
        type=str,
        default=None,
        help=(
            "Name des Test-Health-Profils (z.B. 'weekly_core', 'daily_quick'). "
            "Wenn nicht angegeben, wird 'default_profile' aus der TOML-Config verwendet."
        ),
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/test_health_profiles.toml",
        help="Pfad zur Test-Health-Profiles-TOML-Config (default: config/test_health_profiles.toml)",
    )

    parser.add_argument(
        "--report-root",
        type=str,
        default="reports/test_health",
        help="Basis-Verzeichnis für Reports (default: reports/test_health)",
    )

    return parser.parse_args()


def load_default_profile(config_path: Path) -> str:
    """
    Lädt den default_profile aus der TOML-Config.

    Parameters
    ----------
    config_path : Path
        Pfad zur TOML-Config

    Returns
    -------
    str
        Name des Default-Profils
    """
    # Python 3.11+: tomllib ist built-in
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        try:
            import tomli as tomllib  # type: ignore
        except ImportError:
            raise ImportError(
                "Python <3.11 benötigt 'tomli' package: pip install tomli"
            )

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    default_profile = config.get("default_profile")
    if not default_profile:
        raise ValueError(
            "Kein 'default_profile' in config definiert. "
            "Bitte --profile explizit angeben."
        )

    return default_profile


def main() -> int:
    """
    Hauptfunktion: CLI-Entry-Point.

    Returns
    -------
    int
        Exit-Code (0 = success, 1 = failure)
    """
    args = parse_args()

    config_path = Path(args.config)
    report_root = Path(args.report_root)

    # Profil bestimmen
    if args.profile:
        profile_name = args.profile
    else:
        try:
            profile_name = load_default_profile(config_path)
            print(f"[TestHealth] Verwende default_profile: {profile_name}")
        except Exception as e:
            print(f"[TestHealth] ❌ Fehler beim Laden von default_profile: {e}")
            return 1

    # Header ausgeben
    print("=" * 70)
    print("🏥 Peak_Trade Test Health Automation v0")
    print("=" * 70)
    print(f"Profil:       {profile_name}")
    print(f"Config:       {config_path}")
    print(f"Report-Root:  {report_root}")
    print("=" * 70)
    print()

    # Test-Health-Profil ausführen
    try:
        summary, report_dir = run_test_health_profile(
            profile_name=profile_name,
            config_path=config_path,
            report_root=report_root,
        )
    except Exception as e:
        print(f"\n❌ Fehler beim Ausführen des Test-Health-Profils: {e}")
        import traceback

        traceback.print_exc()
        return 1

    # Zusammenfassung ausgeben
    print()
    print("=" * 70)
    print("📊 Test Health Summary")
    print("=" * 70)
    print(f"Profile:         {summary.profile_name}")
    print(f"Health-Score:    {summary.health_score:.1f} / 100.0")
    print()
    print(f"Passed Checks:   {summary.passed_checks}")
    print(f"Failed Checks:   {summary.failed_checks}")
    print(f"Skipped Checks:  {summary.skipped_checks}")
    print()
    print(f"Passed Weight:   {summary.passed_weight} / {summary.total_weight}")
    print()

    # Ampel-Interpretation
    if summary.health_score >= 80:
        ampel = "🟢 Grün (gesund)"
    elif summary.health_score >= 50:
        ampel = "🟡 Gelb (teilweise gesund / genauer hinsehen)"
    else:
        ampel = "🔴 Rot (kritisch)"

    print(f"Ampel:           {ampel}")
    print()
    print(f"Reports:         {report_dir}")
    print("=" * 70)

    # Exit-Code bestimmen
    if summary.failed_checks == 0:
        print("\n✅ Alle Checks erfolgreich!")
        return 0
    else:
        print(f"\n❌ {summary.failed_checks} Check(s) fehlgeschlagen!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
