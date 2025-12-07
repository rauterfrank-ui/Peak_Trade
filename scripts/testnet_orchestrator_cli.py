#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/testnet_orchestrator_cli.py
"""
Peak_Trade: Testnet-Orchestrator CLI (Phase 64)
===============================================

CLI für Shadow- & Testnet-Run-Orchestrierung.

Subcommands:
- start-shadow: Startet einen Shadow-Run
- start-testnet: Startet einen Testnet-Run
- status: Zeigt Status von Runs
- stop: Stoppt einen Run
- tail: Zeigt letzte Events eines Runs

Usage:
    python scripts/testnet_orchestrator_cli.py start-shadow --strategy ma_crossover --symbol BTC/EUR --timeframe 1m
    python scripts/testnet_orchestrator_cli.py status
    python scripts/testnet_orchestrator_cli.py stop --run-id shadow_20251207_120000_abc123
    python scripts/testnet_orchestrator_cli.py tail --run-id shadow_20251207_120000_abc123 --limit 50
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, List

# Projekt-Root zum Python-Path hinzufügen
CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.peak_config import load_config, PeakConfig
from src.live.testnet_orchestrator import (
    TestnetOrchestrator,
    RunInfo,
    RunNotFoundError,
    ReadinessCheckFailedError,
    InvalidModeError,
    OrchestratorError,
)


def build_parser() -> argparse.ArgumentParser:
    """Baut den Argument-Parser für Testnet-Orchestrator CLI."""
    parser = argparse.ArgumentParser(
        prog="testnet_orchestrator",
        description="Peak_Trade Testnet-Orchestrator CLI\n\n"
                    "WICHTIG: Dieses Script ist für Shadow/Testnet-Runs gedacht.\n"
                    "Keine echten Live-Orders werden gesendet.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Shadow-Run starten
  python scripts/testnet_orchestrator_cli.py start-shadow \\
    --strategy ma_crossover \\
    --symbol BTC/EUR \\
    --timeframe 1m \\
    --config config/config.toml

  # Testnet-Run starten
  python scripts/testnet_orchestrator_cli.py start-testnet \\
    --strategy ma_crossover \\
    --symbol BTC/EUR \\
    --timeframe 1m

  # Status aller Runs
  python scripts/testnet_orchestrator_cli.py status

  # Status eines Runs
  python scripts/testnet_orchestrator_cli.py status --run-id shadow_20251207_120000_abc123

  # Run stoppen
  python scripts/testnet_orchestrator_cli.py stop --run-id shadow_20251207_120000_abc123

  # Alle Runs stoppen
  python scripts/testnet_orchestrator_cli.py stop --all

  # Events tailen
  python scripts/testnet_orchestrator_cli.py tail --run-id shadow_20251207_120000_abc123 --limit 50
        """,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Orchestrator Subcommand",
    )

    # start-shadow
    start_shadow_parser = subparsers.add_parser(
        "start-shadow",
        help="Startet einen Shadow-Run",
    )
    add_start_shadow_args(start_shadow_parser)

    # start-testnet
    start_testnet_parser = subparsers.add_parser(
        "start-testnet",
        help="Startet einen Testnet-Run",
    )
    add_start_testnet_args(start_testnet_parser)

    # status
    status_parser = subparsers.add_parser(
        "status",
        help="Zeigt Status von Runs",
    )
    add_status_args(status_parser)

    # stop
    stop_parser = subparsers.add_parser(
        "stop",
        help="Stoppt einen Run",
    )
    add_stop_args(stop_parser)

    # tail
    tail_parser = subparsers.add_parser(
        "tail",
        help="Zeigt letzte Events eines Runs",
    )
    add_tail_args(tail_parser)

    return parser


def add_start_shadow_args(parser: argparse.ArgumentParser) -> None:
    """Fügt Argumente für start-shadow hinzu."""
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Config-Datei (Default: config/config.toml)",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        required=True,
        help="Name der Strategie (z.B. 'ma_crossover')",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        required=True,
        help="Trading-Symbol (z.B. 'BTC/EUR')",
    )
    parser.add_argument(
        "--timeframe",
        type=str,
        required=True,
        help="Timeframe (z.B. '1m', '5m', '1h')",
    )
    parser.add_argument(
        "--notes",
        type=str,
        default="",
        help="Optionale Notizen für den Run",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON-Output (nur Run-ID)",
    )


def add_start_testnet_args(parser: argparse.ArgumentParser) -> None:
    """Fügt Argumente für start-testnet hinzu."""
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Config-Datei (Default: config/config.toml)",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        required=True,
        help="Name der Strategie (z.B. 'ma_crossover')",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        required=True,
        help="Trading-Symbol (z.B. 'BTC/EUR')",
    )
    parser.add_argument(
        "--timeframe",
        type=str,
        required=True,
        help="Timeframe (z.B. '1m', '5m', '1h')",
    )
    parser.add_argument(
        "--notes",
        type=str,
        default="",
        help="Optionale Notizen für den Run",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON-Output (nur Run-ID)",
    )


def add_status_args(parser: argparse.ArgumentParser) -> None:
    """Fügt Argumente für status hinzu."""
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Config-Datei (Default: config/config.toml)",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        help="Run-ID (optional, sonst alle Runs)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON-Output",
    )


def add_stop_args(parser: argparse.ArgumentParser) -> None:
    """Fügt Argumente für stop hinzu."""
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Config-Datei (Default: config/config.toml)",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        help="Run-ID (erforderlich wenn --all nicht gesetzt)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Stoppt alle aktiven Runs",
    )


def add_tail_args(parser: argparse.ArgumentParser) -> None:
    """Fügt Argumente für tail hinzu."""
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
        "--limit",
        type=int,
        default=100,
        help="Maximale Anzahl Events (Default: 100)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON-Output",
    )


def cmd_start_shadow(args: argparse.Namespace, orchestrator: TestnetOrchestrator) -> int:
    """Führt start-shadow aus."""
    try:
        run_id = orchestrator.start_shadow_run(
            strategy_name=args.strategy,
            symbol=args.symbol,
            timeframe=args.timeframe,
            notes=args.notes,
        )

        if args.json:
            print(json.dumps({"run_id": run_id}))
        else:
            print(f"✅ Shadow-Run gestartet: {run_id}")
            print(f"   Strategie: {args.strategy}")
            print(f"   Symbol: {args.symbol}")
            print(f"   Timeframe: {args.timeframe}")

        return 0

    except (ReadinessCheckFailedError, InvalidModeError, OrchestratorError) as e:
        print(f"❌ Fehler: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}", file=sys.stderr)
        return 1


def cmd_start_testnet(args: argparse.Namespace, orchestrator: TestnetOrchestrator) -> int:
    """Führt start-testnet aus."""
    try:
        run_id = orchestrator.start_testnet_run(
            strategy_name=args.strategy,
            symbol=args.symbol,
            timeframe=args.timeframe,
            notes=args.notes,
        )

        if args.json:
            print(json.dumps({"run_id": run_id}))
        else:
            print(f"✅ Testnet-Run gestartet: {run_id}")
            print(f"   Strategie: {args.strategy}")
            print(f"   Symbol: {args.symbol}")
            print(f"   Timeframe: {args.timeframe}")

        return 0

    except (ReadinessCheckFailedError, InvalidModeError, OrchestratorError) as e:
        print(f"❌ Fehler: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}", file=sys.stderr)
        return 1


def cmd_status(args: argparse.Namespace, orchestrator: TestnetOrchestrator) -> int:
    """Führt status aus."""
    try:
        status = orchestrator.get_status(run_id=args.run_id)

        if args.json:
            if isinstance(status, list):
                print(json.dumps([s.to_dict() for s in status], indent=2))
            else:
                print(json.dumps(status.to_dict(), indent=2))
        else:
            if isinstance(status, list):
                if not status:
                    print("Keine aktiven Runs")
                    return 0

                print(f"\n{'Run-ID':<40} {'Mode':<10} {'Strategy':<20} {'State':<10} {'Started':<20}")
                print("-" * 100)
                for s in status:
                    started_str = s.started_at.strftime("%Y-%m-%d %H:%M:%S") if s.started_at else "N/A"
                    print(f"{s.run_id:<40} {s.mode:<10} {s.strategy_name:<20} {s.state.value:<10} {started_str:<20}")
            else:
                print(f"\nRun-ID: {status.run_id}")
                print(f"Mode: {status.mode}")
                print(f"Strategy: {status.strategy_name}")
                print(f"Symbol: {status.symbol}")
                print(f"Timeframe: {status.timeframe}")
                print(f"State: {status.state.value}")
                print(f"Started: {status.started_at.isoformat() if status.started_at else 'N/A'}")
                if status.stopped_at:
                    print(f"Stopped: {status.stopped_at.isoformat()}")
                if status.last_error:
                    print(f"Last Error: {status.last_error}")
                if status.notes:
                    print(f"Notes: {status.notes}")

        return 0

    except RunNotFoundError as e:
        print(f"❌ Fehler: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}", file=sys.stderr)
        return 1


def cmd_stop(args: argparse.Namespace, orchestrator: TestnetOrchestrator) -> int:
    """Führt stop aus."""
    try:
        if args.all:
            # Alle Runs stoppen
            all_runs = orchestrator.get_status()
            if isinstance(all_runs, list):
                stopped_count = 0
                for run_info in all_runs:
                    if run_info.state.value in ("running", "pending"):
                        try:
                            orchestrator.stop_run(run_info.run_id)
                            stopped_count += 1
                        except Exception as e:
                            print(f"⚠️  Fehler beim Stoppen von {run_info.run_id}: {e}", file=sys.stderr)

                print(f"✅ {stopped_count} Run(s) gestoppt")
                return 0
            else:
                print("❌ Keine Runs gefunden", file=sys.stderr)
                return 1
        else:
            if not args.run_id:
                print("❌ --run-id oder --all erforderlich", file=sys.stderr)
                return 1

            orchestrator.stop_run(args.run_id)
            print(f"✅ Run gestoppt: {args.run_id}")
            return 0

    except RunNotFoundError as e:
        print(f"❌ Fehler: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}", file=sys.stderr)
        return 1


def cmd_tail(args: argparse.Namespace, orchestrator: TestnetOrchestrator) -> int:
    """Führt tail aus."""
    try:
        events = orchestrator.tail_events(run_id=args.run_id, limit=args.limit)

        if args.json:
            print(json.dumps(events, indent=2, default=str))
        else:
            if not events:
                print("Keine Events gefunden")
                return 0

            print(f"\nLetzte {len(events)} Events für Run: {args.run_id}")
            print("-" * 100)
            for event in events[-10:]:  # Zeige nur letzte 10 in Text-Format
                step = event.get("step", "N/A")
                ts = event.get("ts_event", "N/A")
                signal = event.get("signal", "N/A")
                equity = event.get("equity", "N/A")
                print(f"Step {step} | {ts} | Signal: {signal} | Equity: {equity}")

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

    # Orchestrator erstellen
    orchestrator = TestnetOrchestrator(config=config)

    # Command ausführen
    if args.command == "start-shadow":
        return cmd_start_shadow(args, orchestrator)
    elif args.command == "start-testnet":
        return cmd_start_testnet(args, orchestrator)
    elif args.command == "status":
        return cmd_status(args, orchestrator)
    elif args.command == "stop":
        return cmd_stop(args, orchestrator)
    elif args.command == "tail":
        return cmd_tail(args, orchestrator)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

