#!/usr/bin/env python3
"""
Peak_Trade Test Health Profile Runner (CLI) - v1
==================================================

Command-Line-Interface für Test Health Automation v1.

Usage:
    python scripts/run_test_health_profile.py
    python scripts/run_test_health_profile.py --profile weekly_core
    python scripts/run_test_health_profile.py --profile daily_quick --config config/test_health_profiles.toml
    python scripts/run_test_health_profile.py --no-strategy-coverage --no-switch-sanity

v1-Features:
  - Strategy-Coverage-Checks (Backtests & Paper-Runs pro Strategie)
  - Strategy-Switch Sanity Check (Governance-Prüfung)
  - Erweiterte Slack-Notifications

Zweck:
  - Lädt Test-Health-Profil aus TOML-Config
  - Führt alle definierten Checks aus
  - v1: Strategy-Coverage und Switch-Sanity prüfen
  - Erzeugt Reports (JSON, Markdown, HTML)
  - Gibt Health-Score und Exit-Code zurück

Exit-Codes:
  - 0: Alle Checks erfolgreich (failed_checks == 0)
  - 1: Mindestens ein Check fehlgeschlagen

Stand: Dezember 2024
Version: v1
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
        description="Peak_Trade Test Health Profile Runner (v1)",
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

  # v1: Ohne Strategy-Coverage und Switch-Sanity (z.B. für lokale Tests)
  python scripts/run_test_health_profile.py --no-strategy-coverage --no-switch-sanity

  # v1: Ohne Slack-Notification
  python scripts/run_test_health_profile.py --no-slack
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
    
    # v1: Neue Optionen
    parser.add_argument(
        "--no-strategy-coverage",
        action="store_true",
        help="v1: Strategy-Coverage-Check überspringen",
    )
    
    parser.add_argument(
        "--no-switch-sanity",
        action="store_true",
        help="v1: Strategy-Switch Sanity Check überspringen",
    )
    
    parser.add_argument(
        "--no-slack",
        action="store_true",
        help="v1: Slack-Notification deaktivieren (für lokale Tests)",
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
    Hauptfunktion: CLI-Entry-Point (v1).

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
    print("🏥 Peak_Trade Test Health Automation v1")
    print("=" * 70)
    print(f"Profil:       {profile_name}")
    print(f"Config:       {config_path}")
    print(f"Report-Root:  {report_root}")
    
    # v1: Zeige aktivierte Features
    features = []
    if not args.no_strategy_coverage:
        features.append("Strategy-Coverage")
    if not args.no_switch_sanity:
        features.append("Switch-Sanity")
    if not args.no_slack:
        features.append("Slack")
    print(f"v1-Features:  {', '.join(features) if features else '(alle deaktiviert)'}")
    print("=" * 70)
    print()

    # v1: Slack temporär deaktivieren wenn --no-slack
    # Wir setzen die ENV-Variable temporär auf leer
    import os
    original_slack_env = None
    if args.no_slack:
        original_slack_env = os.environ.get("PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH")
        os.environ["PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH"] = ""

    # Test-Health-Profil ausführen
    try:
        summary, report_dir = run_test_health_profile(
            profile_name=profile_name,
            config_path=config_path,
            report_root=report_root,
            skip_strategy_coverage=args.no_strategy_coverage,
            skip_switch_sanity=args.no_switch_sanity,
        )
    except Exception as e:
        print(f"\n❌ Fehler beim Ausführen des Test-Health-Profils: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        # Restore Slack ENV
        if args.no_slack and original_slack_env is not None:
            os.environ["PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH"] = original_slack_env

    # Zusammenfassung ausgeben
    print()
    print("=" * 70)
    print("📊 Test Health Summary (v1)")
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
    if summary.health_score >= 80 and not summary.has_any_violations():
        ampel = "🟢 Grün (gesund)"
    elif summary.health_score >= 50:
        ampel = "🟡 Gelb (teilweise gesund / genauer hinsehen)"
    else:
        ampel = "🔴 Rot (kritisch)"

    print(f"Ampel:           {ampel}")
    
    # v1: Trigger-Violations
    if summary.has_trigger_violations():
        print(f"\n⚠️  Trigger-Violations: {len(summary.trigger_violations)}")
    
    # v1: Strategy-Coverage
    if summary.strategy_coverage and summary.strategy_coverage.enabled:
        coverage = summary.strategy_coverage
        status = "✅ OK" if coverage.is_healthy else f"❌ {len(coverage.all_violations)} Violations"
        print(f"Strategy-Coverage: {status}")
    
    # v1: Switch-Sanity
    if summary.switch_sanity and summary.switch_sanity.enabled:
        sanity = summary.switch_sanity
        status = "✅ OK" if sanity.is_ok else f"❌ {len(sanity.violations)} Violations"
        print(f"Switch-Sanity:     {status}")
    
    print()
    print(f"Reports:         {report_dir}")
    print("=" * 70)

    # Exit-Code bestimmen
    if summary.failed_checks == 0 and not summary.has_any_violations():
        print("\n✅ Alle Checks erfolgreich!")
        return 0
    else:
        issues = []
        if summary.failed_checks > 0:
            issues.append(f"{summary.failed_checks} Check(s) fehlgeschlagen")
        if summary.has_trigger_violations():
            issues.append(f"{len(summary.trigger_violations)} Trigger-Violation(s)")
        if summary.has_strategy_coverage_violations():
            issues.append("Strategy-Coverage-Violations")
        if summary.has_switch_sanity_violations():
            issues.append("Switch-Sanity-Violations")
        
        print(f"\n❌ Probleme: {', '.join(issues)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
