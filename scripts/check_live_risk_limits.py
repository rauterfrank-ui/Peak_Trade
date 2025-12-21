#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/check_live_risk_limits.py
"""
Peak_Trade: Check Live-Risk-Limits für eine Orders-CSV.
========================================================

Eigenständiges Tool zum Prüfen einer bestehenden Orders-CSV gegen die
konfigurierten Live-Risk-Limits, ohne Preview- oder Paper-Trade-Scripts
auszuführen.

Workflow-Empfehlung:

    1. Order-Preview erstellen (generiert Orders-CSV):
       python scripts/preview_live_orders.py --signals reports/forward/..._signals.csv

    2. Standalone Risk-Check durchführen:
       python scripts/check_live_risk_limits.py --orders reports/live/..._orders.csv --tag daily-check

    3. Bei Bedarf mit Enforcement:
       python scripts/check_live_risk_limits.py --orders ... --starting-cash 10000 --enforce-live-risk

Usage:
    python scripts/check_live_risk_limits.py --orders reports/live/preview_..._orders.csv
    python scripts/check_live_risk_limits.py --orders ... --starting-cash 10000 --tag daily
    python scripts/check_live_risk_limits.py --orders ... --enforce-live-risk
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Pfad-Setup wie in anderen Scripts
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.peak_config import load_config
from src.live.orders import load_orders_csv
from src.live.workflows import (
    run_live_risk_check,
    RiskCheckContext,
    validate_risk_flags,
    LiveRiskViolationError,
)
from src.notifications import ConsoleNotifier, FileNotifier, CombinedNotifier

# Default Alert-Logdatei
DEFAULT_ALERT_LOG = Path("logs/alerts.log")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Check Live-Risk-Limits für eine Orders-CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python scripts/check_live_risk_limits.py --orders reports/live/..._orders.csv
  python scripts/check_live_risk_limits.py --orders ... --starting-cash 10000 --tag daily
  python scripts/check_live_risk_limits.py --orders ... --enforce-live-risk
        """,
    )
    parser.add_argument(
        "orders_csv",
        nargs="?",
        help="Pfad zur Orders-CSV (z.B. aus preview_live_orders.py).",
    )
    parser.add_argument(
        "--orders",
        dest="orders_csv_opt",
        help="Alternative zu positional 'orders_csv' (Pfad zur Orders-CSV).",
    )
    # Kern-Argumente (konsistent mit anderen Scripts)
    parser.add_argument(
        "--config",
        dest="config_path",
        default="config.toml",
        help="Pfad zur TOML-Config (Default: config.toml).",
    )
    parser.add_argument(
        "--tag",
        help="Optionaler Tag für Registry-Logging (z.B. 'daily-check', 'precheck').",
    )
    parser.add_argument(
        "--starting-cash",
        dest="start_cash",
        type=float,
        help="Startkapital für Daily-Loss-%%-Limits (wichtig für max_daily_loss_pct).",
    )
    parser.add_argument(
        "--enforce-live-risk",
        action="store_true",
        help=(
            "Bei Verletzung mit Exit-Code 1 abbrechen. "
            "Ohne dieses Flag werden Verletzungen nur als Warnung ausgegeben."
        ),
    )
    parser.add_argument(
        "--skip-live-risk",
        action="store_true",
        help="Live-Risk-Check komplett überspringen (z.B. für Debug-Zwecke).",
    )

    parser.add_argument(
        "--alert-log",
        type=Path,
        default=DEFAULT_ALERT_LOG,
        help=f"Pfad zur Alert-Logdatei (Default: {DEFAULT_ALERT_LOG})",
    )

    parser.add_argument(
        "--no-alerts",
        action="store_true",
        help="Alert-Benachrichtigungen deaktivieren",
    )

    args = parser.parse_args(argv)

    # orders_csv bestimmen: --orders hat Vorrang vor positional
    if args.orders_csv_opt:
        args.orders_csv = args.orders_csv_opt
    elif not args.orders_csv:
        parser.error("Bitte entweder positional 'orders_csv' oder --orders angeben.")

    return args


def main(argv: Optional[List[str]] = None) -> int:
    """
    Hauptfunktion.

    Returns:
        Exit-Code: 0 = OK, 1 = Fehler oder Verletzung mit --enforce
    """
    args = parse_args(argv)

    orders_path = Path(args.orders_csv)
    if not orders_path.is_file():
        print(f"❌ Orders-CSV nicht gefunden: {orders_path}")
        return 1

    print("\n📋 Peak_Trade Live-Risk-Limits Check")
    print("=" * 70)

    cfg = load_config(args.config_path)
    orders = load_orders_csv(orders_path)

    if not orders:
        print("⚠️  Keine Orders in CSV gefunden – nichts zu prüfen.")
        return 0

    print(f"\n📥 Orders geladen: {len(orders)} aus {orders_path}")

    # Flags validieren
    try:
        validate_risk_flags(args.enforce_live_risk, args.skip_live_risk)
    except ValueError as e:
        print(f"\n❌ FEHLER: {e}")
        return 1

    # Notifier konfigurieren (wenn Alerts aktiviert)
    notifier = None
    if not args.no_alerts:
        notifiers = [ConsoleNotifier(show_context=True)]
        if args.alert_log:
            notifiers.append(FileNotifier(args.alert_log))
        notifier = CombinedNotifier(notifiers)

    # Risk-Check durchführen
    ctx = RiskCheckContext(
        config=cfg,
        starting_cash=args.start_cash,
        enforce=args.enforce_live_risk,
        skip=args.skip_live_risk,
        tag=args.tag,
        config_path=args.config_path,
        log_to_registry=True,
        runner_name="check_live_risk_limits.py",
        notifier=notifier,
    )

    try:
        risk_result = run_live_risk_check(
            orders=orders,
            ctx=ctx,
            orders_csv=str(orders_path),
            extra_metadata={"starting_cash": args.start_cash},
        )
    except LiveRiskViolationError as e:
        print(f"\n❌ ABBRUCH: {e}")
        return 1

    # Ergebnis-Status
    if risk_result is None:
        # Skip-Modus
        print("\n✅ Live-Risk-Check übersprungen.")
        return 0

    if risk_result.allowed:
        print(f"\n✅ Live-Risk-Check bestanden!")
    else:
        if args.enforce_live_risk:
            # Sollte durch Exception oben abgefangen sein, aber sicherheitshalber
            print(f"\n❌ Live-Risk-Check NICHT bestanden (--enforce-live-risk)")
            return 1
        else:
            print(f"\n⚠️  Live-Risk-Check NICHT bestanden (nur Warnung)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
