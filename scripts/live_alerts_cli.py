#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/live_alerts_cli.py
"""
Peak_Trade: Live Alerts CLI (Phase 66)
======================================

CLI für Alert-Regeln und Incident-Notifications.

Subcommands:
- run-rules: Führt Alert-Regeln für einen Run aus

Usage:
    python scripts/live_alerts_cli.py run-rules \
      --run-id shadow_20251207_... \
      --pnl-drop-threshold-pct 5.0 \
      --no-events-max-minutes 10
"""
from __future__ import annotations

import argparse
import sys
from datetime import timedelta
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.peak_config import load_config, PeakConfig
from src.live.alert_manager import AlertManager, LoggingAlertSink, ConsoleAlertNotifier
from src.live.alert_rules import (
    check_pnl_drop,
    check_no_events,
    check_error_spike,
    MonitoringAPI,
)
from src.live.alerts import AlertLevel
from src.live.run_logging import load_shadow_paper_logging_config


def build_parser() -> argparse.ArgumentParser:
    """Baut den Argument-Parser für Live-Alerts CLI."""
    parser = argparse.ArgumentParser(
        prog="live_alerts",
        description="Peak_Trade Live Alerts CLI\n\n"
                    "WICHTIG: Alert-System für Shadow/Testnet-Runs.\n"
                    "Sendet nur Notifications, keine Trading-Operationen.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # PnL-Drop-Check (5% Drop in 1 Stunde)
  python scripts/live_alerts_cli.py run-rules \
    --run-id shadow_20251207_120000_abc123 \
    --pnl-drop-threshold-pct 5.0 \
    --pnl-drop-window-hours 1

  # No-Events-Check (10 Minuten Stille)
  python scripts/live_alerts_cli.py run-rules \
    --run-id shadow_20251207_120000_abc123 \
    --no-events-max-minutes 10

  # Alle Checks
  python scripts/live_alerts_cli.py run-rules \
    --run-id shadow_20251207_120000_abc123 \
    --pnl-drop-threshold-pct 5.0 \
    --no-events-max-minutes 10 \
    --error-spike-max-errors 5 \
    --error-spike-window-minutes 10
        """,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Alert Subcommand",
    )

    # run-rules
    run_rules_parser = subparsers.add_parser(
        "run-rules",
        help="Führt Alert-Regeln für einen Run aus",
    )
    add_run_rules_args(run_rules_parser)

    return parser


def add_run_rules_args(parser: argparse.ArgumentParser) -> None:
    """Fügt Argumente für run-rules hinzu."""
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Config-Datei (Default: config/config.toml)",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        required=True,
        help="Run-ID",
    )

    # PnL-Drop
    parser.add_argument(
        "--pnl-drop-threshold-pct",
        type=float,
        help="PnL-Drop-Schwellenwert in Prozent (z.B. 5.0 für 5%)",
    )
    parser.add_argument(
        "--pnl-drop-window-hours",
        type=float,
        default=1.0,
        help="Zeitfenster für PnL-Drop-Check in Stunden (Default: 1.0)",
    )

    # No-Events
    parser.add_argument(
        "--no-events-max-minutes",
        type=float,
        help="Maximale Stille-Zeit in Minuten (z.B. 10.0 für 10 Minuten)",
    )

    # Error-Spike
    parser.add_argument(
        "--error-spike-max-errors",
        type=int,
        help="Maximale Anzahl Fehler im Zeitfenster",
    )
    parser.add_argument(
        "--error-spike-window-minutes",
        type=float,
        default=10.0,
        help="Zeitfenster für Error-Spike-Check in Minuten (Default: 10.0)",
    )


def cmd_run_rules(args: argparse.Namespace, config: PeakConfig) -> int:
    """Führt run-rules aus."""
    try:
        # Base-Dir aus Config
        logging_cfg = load_shadow_paper_logging_config(config)
        base_dir = logging_cfg.base_dir

        # AlertManager initialisieren
        logger = __import__("logging").getLogger("peak_trade.live.alerts")
        notifiers = [
            LoggingAlertSink(logger, min_level=AlertLevel.INFO),
            ConsoleAlertNotifier(min_level=AlertLevel.WARNING),
        ]
        alert_manager = AlertManager(notifiers=notifiers)

        # MonitoringAPI initialisieren
        monitoring = MonitoringAPI(base_dir=base_dir)

        # Exit-Code (0 = keine kritischen Alerts, 1 = mindestens ein kritischer Alert)
        exit_code = 0
        alerts_raised = 0

        print(f"Führe Alert-Regeln für Run '{args.run_id}' aus...\n")

        # PnL-Drop-Check
        if args.pnl_drop_threshold_pct is not None:
            window = timedelta(hours=args.pnl_drop_window_hours)
            print(f"  ✓ PnL-Drop-Check (Threshold: {args.pnl_drop_threshold_pct}%, Window: {window})")
            if check_pnl_drop(
                run_id=args.run_id,
                threshold_pct=args.pnl_drop_threshold_pct,
                window=window,
                monitoring=monitoring,
                alert_manager=alert_manager,
            ):
                alerts_raised += 1
                exit_code = 1  # Mindestens ein kritischer Alert
            else:
                print("    → Kein PnL-Drop erkannt")

        # No-Events-Check
        if args.no_events_max_minutes is not None:
            max_silence = timedelta(minutes=args.no_events_max_minutes)
            print(f"  ✓ No-Events-Check (Max Silence: {max_silence})")
            if check_no_events(
                run_id=args.run_id,
                max_silence=max_silence,
                monitoring=monitoring,
                alert_manager=alert_manager,
            ):
                alerts_raised += 1
                exit_code = 1  # Mindestens ein kritischer Alert
            else:
                print("    → Run produziert Events")

        # Error-Spike-Check
        if args.error_spike_max_errors is not None:
            window = timedelta(minutes=args.error_spike_window_minutes)
            print(f"  ✓ Error-Spike-Check (Max Errors: {args.error_spike_max_errors}, Window: {window})")
            if check_error_spike(
                run_id=args.run_id,
                max_errors=args.error_spike_max_errors,
                window=window,
                monitoring=monitoring,
                alert_manager=alert_manager,
            ):
                alerts_raised += 1
                exit_code = 1  # Mindestens ein kritischer Alert
            else:
                print("    → Keine Error-Spikes erkannt")

        print(f"\n✓ Alert-Checks abgeschlossen. Alerts ausgelöst: {alerts_raised}")

        return exit_code

    except Exception as e:
        print(f"❌ Fehler: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main-Funktion."""
    parser = build_parser()
    args = parser.parse_args()

    # Config laden
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"❌ Fehler beim Laden der Config: {e}", file=sys.stderr)
        return 1

    # Command ausführen
    if args.command == "run-rules":
        return cmd_run_rules(args, config)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

