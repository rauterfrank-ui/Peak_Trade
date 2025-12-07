#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/live_monitor_cli.py
"""
Peak_Trade: Live Monitor CLI (Phase 65)
========================================

CLI für Monitoring von Shadow- und Testnet-Runs.

Subcommands:
- overview: Übersicht aller Runs
- run: Details zu einem Run
- follow: Live-Tailing-Modus

Usage:
    python scripts/live_monitor_cli.py overview --only-active
    python scripts/live_monitor_cli.py run --run-id shadow_20251207_120000_abc123
    python scripts/live_monitor_cli.py follow --run-id shadow_20251207_120000_abc123 --refresh-interval 2.0
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, List

# Projekt-Root zum Python-Path hinzufügen
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.peak_config import load_config, PeakConfig
from src.live.monitoring import (
    list_runs,
    get_run_snapshot,
    get_run_timeseries,
    tail_events,
    RunNotFoundError,
    RunSnapshot,
)
from src.live.run_logging import load_shadow_paper_logging_config


def build_parser() -> argparse.ArgumentParser:
    """Baut den Argument-Parser für Live-Monitor CLI."""
    parser = argparse.ArgumentParser(
        prog="live_monitor",
        description="Peak_Trade Live Monitor CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Übersicht aller aktiven Runs
  python scripts/live_monitor_cli.py overview --only-active

  # Übersicht aller Runs (inkl. inaktive)
  python scripts/live_monitor_cli.py overview --include-inactive

  # Übersicht der letzten 24 Stunden
  python scripts/live_monitor_cli.py overview --max-age-hours 24

  # Run-Details
  python scripts/live_monitor_cli.py run --run-id shadow_20251207_120000_abc123

  # Live-Tailing
  python scripts/live_monitor_cli.py follow --run-id shadow_20251207_120000_abc123 --refresh-interval 2.0
        """,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Monitor Subcommand",
    )

    # overview
    overview_parser = subparsers.add_parser(
        "overview",
        help="Übersicht aller Runs",
    )
    add_overview_args(overview_parser)

    # run
    run_parser = subparsers.add_parser(
        "run",
        help="Details zu einem Run",
    )
    add_run_args(run_parser)

    # follow
    follow_parser = subparsers.add_parser(
        "follow",
        help="Live-Tailing-Modus",
    )
    add_follow_args(follow_parser)

    return parser


def add_overview_args(parser: argparse.ArgumentParser) -> None:
    """Fügt Argumente für overview hinzu."""
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Config-Datei (Default: config/config.toml)",
    )
    parser.add_argument(
        "--only-active",
        action="store_true",
        default=True,
        help="Nur aktive Runs anzeigen (Default: True)",
    )
    parser.add_argument(
        "--include-inactive",
        action="store_true",
        help="Auch inaktive Runs anzeigen",
    )
    parser.add_argument(
        "--max-age-hours",
        type=int,
        help="Maximales Alter der Runs in Stunden",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON-Output",
    )


def add_run_args(parser: argparse.ArgumentParser) -> None:
    """Fügt Argumente für run hinzu."""
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
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON-Output",
    )


def add_follow_args(parser: argparse.ArgumentParser) -> None:
    """Fügt Argumente für follow hinzu."""
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
    parser.add_argument(
        "--refresh-interval",
        type=float,
        default=2.0,
        help="Refresh-Intervall in Sekunden (Default: 2.0)",
    )


def format_equity(equity: Optional[float]) -> str:
    """Formatiert Equity-Wert."""
    if equity is None:
        return "N/A"
    if equity >= 1000:
        return f"{equity/1000:.1f}k"
    return f"{equity:.0f}"


def format_pnl(pnl: Optional[float]) -> str:
    """Formatiert PnL-Wert."""
    if pnl is None:
        return "N/A"
    sign = "+" if pnl >= 0 else ""
    return f"{sign}{pnl:.0f}"


def format_drawdown(dd: Optional[float]) -> str:
    """Formatiert Drawdown-Wert."""
    if dd is None:
        return "N/A"
    return f"{dd*100:.1f}%"


def cmd_overview(args: argparse.Namespace, config: PeakConfig) -> int:
    """Führt overview aus."""
    try:
        # Base-Dir aus Config
        logging_cfg = load_shadow_paper_logging_config(config)
        base_dir = logging_cfg.base_dir

        # Max-Age
        max_age = None
        if args.max_age_hours:
            max_age = timedelta(hours=args.max_age_hours)

        # Include-Inactive
        include_inactive = args.include_inactive or not args.only_active

        # Runs laden
        runs = list_runs(
            base_dir=base_dir,
            include_inactive=include_inactive,
            max_age=max_age,
        )

        if args.json:
            print(json.dumps([r.to_dict() for r in runs], indent=2))
            return 0

        if not runs:
            print("Keine Runs gefunden")
            return 0

        # Tabelle ausgeben
        print(f"\n{'Run-ID':<40} {'Mode':<10} {'Strategy':<20} {'Symbol':<12} {'TF':<6} {'Active':<8} {'Last Event':<20} {'Equity':<10} {'PnL':<10} {'DD':<10}")
        print("-" * 150)

        for run in runs:
            run_id_short = run.run_id[:38] + ".." if len(run.run_id) > 40 else run.run_id
            mode = run.mode or "N/A"
            strategy = (run.strategy or "N/A")[:18]
            symbol = (run.symbol or "N/A")[:10]
            timeframe = run.timeframe or "N/A"
            active = "yes" if run.is_active else "no"
            last_event = run.last_event_time.strftime("%Y-%m-%d %H:%M:%S") if run.last_event_time else "N/A"
            equity = format_equity(run.equity)
            pnl = format_pnl(run.pnl)
            dd = format_drawdown(run.drawdown)

            print(f"{run_id_short:<40} {mode:<10} {strategy:<20} {symbol:<12} {timeframe:<6} {active:<8} {last_event:<20} {equity:<10} {pnl:<10} {dd:<10}")

        print()
        return 0

    except Exception as e:
        print(f"❌ Fehler: {e}", file=sys.stderr)
        return 1


def cmd_run(args: argparse.Namespace, config: PeakConfig) -> int:
    """Führt run aus."""
    try:
        # Base-Dir aus Config
        logging_cfg = load_shadow_paper_logging_config(config)
        base_dir = logging_cfg.base_dir

        # Snapshot laden
        snapshot = get_run_snapshot(args.run_id, base_dir=base_dir)

        # Events laden
        events = tail_events(args.run_id, limit=50, base_dir=base_dir)

        if args.json:
            output = {
                "snapshot": snapshot.to_dict(),
                "recent_events": events,
            }
            print(json.dumps(output, indent=2, default=str))
            return 0

        # Run-Zusammenfassung
        print(f"\n{'='*80}")
        print(f"Run: {snapshot.run_id}")
        print(f"{'='*80}")
        print(f"Mode:           {snapshot.mode}")
        print(f"Strategy:       {snapshot.strategy or 'N/A'}")
        print(f"Symbol:         {snapshot.symbol or 'N/A'}")
        print(f"Timeframe:      {snapshot.timeframe or 'N/A'}")
        print(f"Active:         {'yes' if snapshot.is_active else 'no'}")
        print(f"Started:        {snapshot.started_at.isoformat() if snapshot.started_at else 'N/A'}")
        if snapshot.ended_at:
            print(f"Ended:          {snapshot.ended_at.isoformat()}")
        print(f"Last Event:     {snapshot.last_event_time.isoformat() if snapshot.last_event_time else 'N/A'}")
        print(f"Events:         {snapshot.num_events}")
        print()
        print(f"Equity:         {format_equity(snapshot.equity)}")
        print(f"PnL:            {format_pnl(snapshot.pnl)}")
        if snapshot.unrealized_pnl is not None:
            print(f"Unrealized PnL: {format_pnl(snapshot.unrealized_pnl)}")
        print(f"Drawdown:       {format_drawdown(snapshot.drawdown)}")
        if snapshot.last_error:
            print(f"Last Error:     {snapshot.last_error}")
        print()

        # Letzte Events
        if events:
            print(f"\nLetzte {len(events)} Events:")
            print("-" * 80)
            print(f"{'Step':<6} {'Time':<20} {'Signal':<8} {'Equity':<12} {'PnL':<12} {'Orders':<10}")
            print("-" * 80)

            for event in events[-20:]:  # Zeige nur letzte 20
                step = event.get("step", "N/A")
                ts = event.get("ts_event") or event.get("ts_bar") or "N/A"
                if isinstance(ts, str) and len(ts) > 19:
                    ts = ts[:19]  # Kürze auf YYYY-MM-DD HH:MM:SS
                signal = event.get("signal", "N/A")
                equity = format_equity(event.get("equity"))
                pnl = format_pnl(event.get("realized_pnl") or event.get("pnl"))
                orders = f"{event.get('orders_filled', 0)}/{event.get('orders_generated', 0)}"

                print(f"{step:<6} {ts:<20} {signal:<8} {equity:<12} {pnl:<12} {orders:<10}")

        print()
        return 0

    except RunNotFoundError as e:
        print(f"❌ Fehler: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}", file=sys.stderr)
        return 1


def cmd_follow(args: argparse.Namespace, config: PeakConfig) -> int:
    """Führt follow aus."""
    try:
        # Base-Dir aus Config
        logging_cfg = load_shadow_paper_logging_config(config)
        base_dir = logging_cfg.base_dir

        print(f"Monitoring Run: {args.run_id}")
        print(f"Refresh-Intervall: {args.refresh_interval}s")
        print("Drücke Ctrl+C zum Beenden\n")

        last_event_count = 0

        try:
            while True:
                # Snapshot laden
                snapshot = get_run_snapshot(args.run_id, base_dir=base_dir)

                # Events laden
                events = tail_events(args.run_id, limit=20, base_dir=base_dir)

                # Clear Screen (einfach: neue Zeilen)
                if len(events) > last_event_count:
                    print("\n" * 2)  # Etwas Platz

                # Aktueller Status
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Run: {snapshot.run_id[:30]}...")
                print(f"  Active: {snapshot.is_active} | Events: {snapshot.num_events} | Equity: {format_equity(snapshot.equity)} | PnL: {format_pnl(snapshot.pnl)} | DD: {format_drawdown(snapshot.drawdown)}")

                # Neue Events
                if len(events) > last_event_count:
                    new_events = events[last_event_count:]
                    for event in new_events:
                        step = event.get("step", "N/A")
                        ts = event.get("ts_event") or event.get("ts_bar") or "N/A"
                        if isinstance(ts, str) and len(ts) > 19:
                            ts = ts[11:19]  # Nur HH:MM:SS
                        signal = event.get("signal", "N/A")
                        equity = format_equity(event.get("equity"))
                        pnl = format_pnl(event.get("realized_pnl") or event.get("pnl"))

                        print(f"  Step {step} | {ts} | Signal: {signal} | Equity: {equity} | PnL: {pnl}")

                last_event_count = len(events)

                time.sleep(args.refresh_interval)

        except KeyboardInterrupt:
            print("\n\nMonitoring beendet")
            return 0

    except RunNotFoundError as e:
        print(f"❌ Fehler: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}", file=sys.stderr)
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
    if args.command == "overview":
        return cmd_overview(args, config)
    elif args.command == "run":
        return cmd_run(args, config)
    elif args.command == "follow":
        return cmd_follow(args, config)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

