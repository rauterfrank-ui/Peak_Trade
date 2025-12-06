#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/send_alerts_demo.py
"""
Peak_Trade: Demo-Script für Notification-Layer
==============================================

Demonstriert die verschiedenen Alert-Typen und Notifier des Notification-Systems.

Usage:
    python scripts/send_alerts_demo.py
    python scripts/send_alerts_demo.py --alert-log logs/custom_alerts.log
    python scripts/send_alerts_demo.py --console-only
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Projekt-Root zum Python-Path hinzufügen
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.notifications import Alert, ConsoleNotifier, FileNotifier, CombinedNotifier

# Default Alert-Logdatei
DEFAULT_ALERT_LOG = Path("logs/alerts.log")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parst CLI-Argumente."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Demo-Script für Notification-Layer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/send_alerts_demo.py
    python scripts/send_alerts_demo.py --alert-log logs/custom_alerts.log
    python scripts/send_alerts_demo.py --console-only
        """,
    )

    parser.add_argument(
        "--alert-log",
        type=Path,
        default=DEFAULT_ALERT_LOG,
        help=f"Pfad zur Alert-Logdatei (Default: {DEFAULT_ALERT_LOG})",
    )

    parser.add_argument(
        "--console-only",
        action="store_true",
        help="Nur Console-Ausgabe, keine Datei-Logs",
    )

    parser.add_argument(
        "--json-format",
        action="store_true",
        help="JSON-Format für Datei-Logs verwenden (statt TSV)",
    )

    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    """Main-Entry-Point für Alert-Demo."""
    args = parse_args(argv)

    print("\n" + "=" * 70)
    print("Peak_Trade: Notification Layer Demo")
    print("=" * 70)

    # Notifier konfigurieren
    notifiers = [ConsoleNotifier(show_context=True)]

    if not args.console_only:
        file_format = "json" if args.json_format else "tsv"
        notifiers.append(FileNotifier(args.alert_log, format=file_format))
        print(f"\nAlerts werden geschrieben nach: {args.alert_log}")
        print(f"Format: {file_format.upper()}")
    else:
        print("\nNur Console-Ausgabe (--console-only)")

    notifier = CombinedNotifier(notifiers)

    print("\n--- Sende Demo-Alerts ---\n")

    # 1. INFO Alert: Forward-Signal
    alert_info = Alert(
        level="info",
        source="forward_signal",
        message="ma_crossover on BTC/EUR (1h): FLAT @ 43250.00",
        timestamp=datetime.utcnow(),
        context={
            "strategy_key": "ma_crossover",
            "symbol": "BTC/EUR",
            "timeframe": "1h",
            "last_signal": 0.0,
            "last_price": 43250.00,
        },
    )
    notifier.send(alert_info)

    # 2. WARNING Alert: Starkes Signal
    alert_warning = Alert(
        level="warning",
        source="forward_signal",
        message="rsi_reversion on ETH/EUR (4h): LONG @ 2450.00",
        timestamp=datetime.utcnow(),
        context={
            "strategy_key": "rsi_reversion",
            "symbol": "ETH/EUR",
            "timeframe": "4h",
            "last_signal": 1.0,
            "last_price": 2450.00,
        },
    )
    notifier.send(alert_warning)

    # 3. CRITICAL Alert: Risk-Verletzung
    alert_critical = Alert(
        level="critical",
        source="live_risk",
        message="Live-Risk-Verletzung: max_order_notional exceeded, max_daily_loss exceeded",
        timestamp=datetime.utcnow(),
        context={
            "allowed": False,
            "n_orders": 5,
            "n_violations": 2,
            "reasons": ["max_order_notional exceeded", "max_daily_loss exceeded"],
            "total_notional": 15000.00,
        },
    )
    notifier.send(alert_critical)

    # 4. INFO Alert: Risk-Check bestanden
    alert_risk_ok = Alert(
        level="info",
        source="live_risk",
        message="Live-Risk-Check bestanden: 3 Orders geprueft",
        timestamp=datetime.utcnow(),
        context={
            "allowed": True,
            "n_orders": 3,
            "n_violations": 0,
            "total_notional": 5000.00,
        },
    )
    notifier.send(alert_risk_ok)

    # 5. WARNING Alert: Analytics (schlechter Sharpe)
    alert_analytics = Alert(
        level="warning",
        source="analytics",
        message="Strategie ma_crossover hat negativen Sharpe Ratio: -0.35",
        timestamp=datetime.utcnow(),
        context={
            "strategy_key": "ma_crossover",
            "avg_sharpe": -0.35,
            "run_count": 12,
            "alert_trigger": "sharpe < 0",
        },
    )
    notifier.send(alert_analytics)

    print("\n--- Demo abgeschlossen ---")

    if not args.console_only:
        print(f"\nPrüfe Logdatei: cat {args.alert_log}")

    print("\nDie folgenden Alert-Levels wurden demonstriert:")
    print("  - INFO: Normale Signale und bestandene Checks")
    print("  - WARNING: Starke Signale und Analytics-Warnungen")
    print("  - CRITICAL: Risk-Verletzungen und Fehler")

    return 0


if __name__ == "__main__":
    sys.exit(main())
