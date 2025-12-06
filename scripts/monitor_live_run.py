#!/usr/bin/env python3
"""
Peak_Trade: Live Run Monitor CLI (Phase 33 + 34)
=================================================

Command-Line-Tool zum Überwachen laufender oder abgeschlossener
Shadow-/Paper-Runs in (nahezu) Echtzeit.

Features:
- Summary-Ansicht: Run-Infos, Equity, PnL, Position, Orders
- Tail-Ansicht: Letzte N Events mit Risk-Status
- Auto-Refresh im konfigurierbaren Intervall
- ANSI-Farben für visuelle Hervorhebung
- Phase 34: Alert-System mit konfigurierbaren Regeln

Usage:
    # Neuesten Run monitoren:
    python -m scripts.monitor_live_run --latest

    # Spezifischen Run monitoren:
    python -m scripts.monitor_live_run --run-id 20251204_180000_paper_ma_crossover_BTC-EUR_1m

    # Mit Run-Directory:
    python -m scripts.monitor_live_run --run-dir live_runs/my_run

    # Nur Summary:
    python -m scripts.monitor_live_run --latest --view summary

    # Längeres Refresh-Intervall:
    python -m scripts.monitor_live_run --latest --interval 5

    # Mehr Tail-Zeilen:
    python -m scripts.monitor_live_run --latest --rows 25

    # Alerts deaktivieren:
    python -m scripts.monitor_live_run --latest --no-alerts

WICHTIG: Dieses Tool ist read-only und trifft keine Trading-Entscheidungen.

Zum Beenden: Ctrl+C
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Projekt-Root zum Path hinzufügen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.peak_config import load_config, PeakConfig
from src.live.run_logging import list_runs
from src.live.monitoring import (
    LiveMonitoringConfig,
    LiveRunSnapshot,
    LiveRunTailRow,
    load_live_monitoring_config,
    load_run_snapshot,
    load_run_tail,
    get_latest_run_dir,
    render_summary,
    render_tail,
    Colors,
)
from src.live.alerts import (
    AlertEngine,
    AlertEvent,
    create_alert_engine_from_config,
    append_alerts_to_file,
    render_alerts,
)


# =============================================================================
# Logging Setup
# =============================================================================


def setup_logging(level: str = "WARNING") -> logging.Logger:
    """Konfiguriert minimales Logging für Monitor."""
    log_level = getattr(logging, level.upper(), logging.WARNING)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger("monitor")


# =============================================================================
# Monitor Functions
# =============================================================================


def clear_screen() -> None:
    """Löscht den Terminal-Bildschirm."""
    # Cross-platform clear
    os.system("cls" if os.name == "nt" else "clear")


def render_status_line(
    run_dir: Path,
    interval: float,
    use_colors: bool = True,
) -> str:
    """Rendert die Status-Zeile am unteren Rand."""
    c = Colors if use_colors else type("NoColors", (), {k: "" for k in dir(Colors) if not k.startswith("_")})()
    return (
        f"{c.GRAY}[monitor] run_dir={run_dir} | "
        f"refresh in {interval:.1f}s | Ctrl+C to exit{c.RESET}"
    )


def render_error(message: str, use_colors: bool = True) -> str:
    """Rendert eine Fehlermeldung."""
    c = Colors if use_colors else type("NoColors", (), {k: "" for k in dir(Colors) if not k.startswith("_")})()
    return f"{c.RED}ERROR: {message}{c.RESET}"


def monitor_run(
    run_dir: Path,
    interval: float,
    rows: int,
    view: str,
    use_colors: bool,
    alert_engine: Optional[AlertEngine] = None,
) -> None:
    """
    Haupt-Monitor-Loop.

    Args:
        run_dir: Pfad zum Run-Verzeichnis
        interval: Refresh-Intervall in Sekunden
        rows: Anzahl Tail-Zeilen
        view: Ansicht ("summary", "tail", "both")
        use_colors: ANSI-Farben verwenden
        alert_engine: Optional AlertEngine für Alert-Auswertung
    """
    c = Colors if use_colors else type("NoColors", (), {k: "" for k in dir(Colors) if not k.startswith("_")})()

    print(f"{c.CYAN}Starting monitor for: {run_dir}{c.RESET}")
    print(f"Interval: {interval}s, Rows: {rows}, View: {view}")
    if alert_engine:
        print(f"Alerts: {c.GREEN}enabled{c.RESET} ({len(alert_engine.rules)} rules)")
    else:
        print(f"Alerts: {c.GRAY}disabled{c.RESET}")
    print("Press Ctrl+C to exit...")
    time.sleep(1)

    while True:
        clear_screen()

        # Header
        print(f"{c.BOLD}{c.CYAN}Peak_Trade Live Monitor (Phase 33 + 34){c.RESET}")
        print(f"{c.GRAY}{'=' * 60}{c.RESET}")
        print()

        try:
            # Snapshot laden
            snapshot = load_run_snapshot(run_dir)

            # Tail laden
            tail_rows = load_run_tail(run_dir, n=rows)

        except FileNotFoundError as e:
            print(render_error(f"Run directory not found: {run_dir}", use_colors))
            print(f"\n{c.GRAY}Waiting for data...{c.RESET}")
            print(f"\n{render_status_line(run_dir, interval, use_colors)}")
            try:
                time.sleep(interval)
                continue
            except KeyboardInterrupt:
                print(f"\n{c.YELLOW}Monitor stopped.{c.RESET}")
                break

        except Exception as exc:
            print(render_error(f"Error loading data: {exc!r}", use_colors))
            print(f"\n{render_status_line(run_dir, interval, use_colors)}")
            try:
                time.sleep(interval)
                continue
            except KeyboardInterrupt:
                print(f"\n{c.YELLOW}Monitor stopped.{c.RESET}")
                break

        # Summary rendern
        if view in ("summary", "both"):
            print(render_summary(snapshot, use_colors=use_colors))

        # Alerts auswerten und anzeigen (Phase 34)
        if alert_engine is not None:
            try:
                new_alerts = alert_engine.evaluate_snapshot(snapshot)
                if new_alerts:
                    # Alerts in Datei schreiben
                    append_alerts_to_file(run_dir, new_alerts)
                    # Alerts im Terminal anzeigen
                    print(render_alerts(new_alerts, use_colors=use_colors))
            except Exception as e:
                print(f"{c.RED}Alert evaluation error: {e}{c.RESET}")

        # Tail rendern
        if view in ("tail", "both"):
            print(render_tail(tail_rows, use_colors=use_colors))

        # Status-Zeile
        print(render_status_line(run_dir, interval, use_colors))

        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            print(f"\n{c.YELLOW}Monitor stopped.{c.RESET}")
            break


def list_available_runs(base_dir: str | Path, use_colors: bool = True) -> None:
    """Listet alle verfügbaren Runs auf."""
    c = Colors if use_colors else type("NoColors", (), {k: "" for k in dir(Colors) if not k.startswith("_")})()

    print(f"{c.BOLD}Available Runs in: {base_dir}{c.RESET}")
    print(f"{c.GRAY}{'=' * 60}{c.RESET}")

    runs = list_runs(base_dir)

    if not runs:
        print(f"{c.YELLOW}No runs found.{c.RESET}")
        return

    for i, run_id in enumerate(runs[:20], 1):  # Max 20 anzeigen
        print(f"  {i:2}. {run_id}")

    if len(runs) > 20:
        print(f"  ... and {len(runs) - 20} more")

    print()
    print(f"Total: {len(runs)} runs")


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> int:
    """
    Haupteinstiegspunkt für den Live Monitor.

    Returns:
        Exit-Code (0 = Success, 1 = Error)
    """
    parser = argparse.ArgumentParser(
        description="Monitor Peak_Trade Shadow/Paper Runs in real-time.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Monitor latest run:
  python -m scripts.monitor_live_run --latest

  # Monitor specific run:
  python -m scripts.monitor_live_run --run-id 20251204_180000_paper_ma_crossover_BTC-EUR_1m

  # Monitor with custom settings:
  python -m scripts.monitor_live_run --latest --interval 5 --rows 20

  # List available runs:
  python -m scripts.monitor_live_run --list

NOTE: This tool is read-only and does not affect trading.
        """,
    )

    # Config
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Path to config file (default: config/config.toml)",
    )

    # Run Selection (mutually exclusive group)
    run_group = parser.add_mutually_exclusive_group()
    run_group.add_argument(
        "--run-dir",
        type=str,
        default=None,
        help="Direct path to run directory",
    )
    run_group.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Run ID (will be resolved to run directory)",
    )
    run_group.add_argument(
        "--latest",
        action="store_true",
        help="Automatically select the latest run",
    )
    run_group.add_argument(
        "--list",
        action="store_true",
        dest="list_runs",
        help="List available runs and exit",
    )

    # Display options
    parser.add_argument(
        "--interval",
        type=float,
        default=None,
        help="Refresh interval in seconds (default: from config)",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=None,
        help="Number of tail rows to display (default: from config)",
    )
    parser.add_argument(
        "--view",
        type=str,
        choices=["summary", "tail", "both"],
        default="both",
        help="View mode: summary, tail, or both (default: both)",
    )
    parser.add_argument(
        "--no-colors",
        action="store_true",
        help="Disable ANSI colors",
    )
    parser.add_argument(
        "--no-alerts",
        action="store_true",
        help="Disable alert evaluation",
    )

    # Logging
    parser.add_argument(
        "--log-level",
        type=str,
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: WARNING)",
    )

    args = parser.parse_args()

    # Setup
    logger = setup_logging(args.log_level)

    # Config laden
    try:
        config_path = Path(args.config)
        if config_path.exists():
            cfg = load_config(config_path)
            monitoring_cfg = load_live_monitoring_config(cfg)
            base_dir = cfg.get("shadow_paper_logging.base_dir", "live_runs")
        else:
            logger.warning(f"Config not found: {config_path}, using defaults")
            monitoring_cfg = LiveMonitoringConfig()
            base_dir = "live_runs"
    except Exception as e:
        logger.warning(f"Error loading config: {e}, using defaults")
        monitoring_cfg = LiveMonitoringConfig()
        base_dir = "live_runs"

    # Defaults aus Config übernehmen
    interval = args.interval if args.interval is not None else monitoring_cfg.default_interval_seconds
    rows = args.rows if args.rows is not None else monitoring_cfg.default_tail_rows
    use_colors = not args.no_colors and monitoring_cfg.use_colors

    # Alert-Engine erstellen (Phase 34)
    alert_engine: Optional[AlertEngine] = None
    if not args.no_alerts:
        try:
            if config_path.exists():
                alert_engine = create_alert_engine_from_config(cfg)
        except Exception as e:
            logger.warning(f"Error creating alert engine: {e}")

    # List-Modus
    if args.list_runs:
        list_available_runs(base_dir, use_colors=use_colors)
        return 0

    # Run-Directory bestimmen
    run_dir: Optional[Path] = None

    if args.run_dir:
        run_dir = Path(args.run_dir)
        if not run_dir.exists():
            print(f"Error: Run directory not found: {run_dir}")
            return 1

    elif args.run_id:
        run_dir = Path(base_dir) / args.run_id
        if not run_dir.exists():
            print(f"Error: Run not found: {args.run_id}")
            print(f"Base directory: {base_dir}")
            print("\nAvailable runs:")
            list_available_runs(base_dir, use_colors=use_colors)
            return 1

    elif args.latest:
        run_dir = get_latest_run_dir(base_dir)
        if run_dir is None:
            print(f"Error: No runs found in: {base_dir}")
            return 1

    else:
        # Keine Auswahl -> Hilfe anzeigen
        print("Error: You must specify --run-dir, --run-id, --latest, or --list")
        print()
        parser.print_help()
        return 1

    # Monitor starten
    try:
        monitor_run(
            run_dir=run_dir,
            interval=interval,
            rows=rows,
            view=args.view,
            use_colors=use_colors,
            alert_engine=alert_engine,
        )
        return 0

    except KeyboardInterrupt:
        print("\nMonitor stopped by user.")
        return 0

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
