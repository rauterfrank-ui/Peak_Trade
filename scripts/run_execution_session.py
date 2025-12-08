#!/usr/bin/env python3
"""
Peak_Trade: Strategy-to-Execution Session CLI (Phase 80/81)
=============================================================

Command-Line-Interface zum Starten einer Shadow/Testnet-Execution-Session.

Diese CLI nutzt den LiveSessionRunner (Phase 80) für einen orchestrierten
Flow von Strategy → Signals → Orders → ExecutionPipeline.

Phase 81 Erweiterung: Sessions werden automatisch im Experiment-Registry
erfasst (run_id, Metriken, Config) - siehe --no-registry zum Deaktivieren.

Usage:
    # Shadow-Mode (Default) - nutzt Dummy/Paper-Executor:
    python scripts/run_execution_session.py --strategy ma_crossover

    # Mit spezifischem Symbol und Timeframe:
    python scripts/run_execution_session.py --strategy rsi_reversion --symbol ETH/EUR --timeframe 5m

    # Testnet-Mode - nutzt Testnet-Dry-Run (validate_only):
    python scripts/run_execution_session.py --mode testnet --strategy ma_crossover

    # Für begrenzte Dauer (30 Minuten):
    python scripts/run_execution_session.py --strategy ma_crossover --duration 30

    # Für N Schritte:
    python scripts/run_execution_session.py --strategy ma_crossover --steps 100

    # Dry-Run (nur Config validieren):
    python scripts/run_execution_session.py --strategy ma_crossover --dry-run

    # Mit Tags für Experiment-Registry:
    python scripts/run_execution_session.py --strategy ma_crossover --tags experiment_v1 test_run

    # Registry-Logging deaktivieren:
    python scripts/run_execution_session.py --strategy ma_crossover --no-registry

WICHTIG: Es werden NIEMALS echte Orders gesendet!
         - Shadow-Mode: Simulation ohne API-Calls
         - Testnet-Mode: Testnet mit validate_only=True (Phase 80: kein echter Testnet-Trade)
         - LIVE-Mode: NICHT ERLAUBT (wirft Fehler)

Verfügbare Strategien (aus Registry):
    python scripts/run_execution_session.py --list-strategies

Zum Beenden: Ctrl+C (SIGINT) oder SIGTERM
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Projekt-Root zum Path hinzufügen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# Logging Setup
# =============================================================================


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Konfiguriert Logging für CLI."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Weniger Noise von externen Libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("ccxt").setLevel(logging.WARNING)

    return logging.getLogger("execution_session")


# =============================================================================
# Strategy Listing
# =============================================================================


def list_available_strategies() -> None:
    """Listet alle verfügbaren Strategien aus der Registry."""
    from src.strategies.registry import get_available_strategy_keys, get_strategy_spec

    print("\n=== Verfügbare Strategien (Peak_Trade Registry) ===\n")

    keys = sorted(get_available_strategy_keys())

    for key in keys:
        spec = get_strategy_spec(key)
        desc = spec.description or "(keine Beschreibung)"
        print(f"  {key:25s} - {desc}")

    print(f"\n  Total: {len(keys)} Strategien verfügbar")
    print("\nBeispiel:")
    print(f"  python scripts/run_execution_session.py --strategy {keys[0]}\n")


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> int:
    """
    Haupteinstiegspunkt für Strategy-to-Execution Session CLI.

    Returns:
        Exit-Code (0 = Success, 1 = Error)
    """
    parser = argparse.ArgumentParser(
        description="Run Peak_Trade Strategy-to-Execution Session (Phase 80).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Shadow-Mode mit MA-Crossover (Default):
  python scripts/run_execution_session.py --strategy ma_crossover

  # Mit anderem Symbol:
  python scripts/run_execution_session.py --strategy rsi_reversion --symbol ETH/EUR

  # Testnet-Mode (Dry-Run):
  python scripts/run_execution_session.py --mode testnet --strategy ma_crossover

  # Für 30 Minuten laufen:
  python scripts/run_execution_session.py --strategy ma_crossover --duration 30

  # Für 100 Steps:
  python scripts/run_execution_session.py --strategy ma_crossover --steps 100

WICHTIG: Es werden KEINE echten Orders gesendet!
         LIVE-Mode ist in Phase 80 NICHT erlaubt.
        """,
    )

    # Mode
    parser.add_argument(
        "--mode",
        type=str,
        default="shadow",
        choices=["shadow", "testnet"],
        help="Ausführungsmodus: 'shadow' (Simulation) oder 'testnet' (Dry-Run). LIVE ist nicht erlaubt! (default: shadow)",
    )

    # Strategy
    parser.add_argument(
        "--strategy",
        "-s",
        type=str,
        default="ma_crossover",
        help="Strategie-Key aus Registry (default: ma_crossover)",
    )

    # Symbol & Timeframe
    parser.add_argument(
        "--symbol",
        type=str,
        default="BTC/EUR",
        help="Trading-Symbol (default: BTC/EUR)",
    )
    parser.add_argument(
        "--timeframe",
        "-t",
        type=str,
        default="1m",
        help="Candle-Timeframe (default: 1m)",
    )

    # Config
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Config-Datei (default: config/config.toml)",
    )

    # Duration / Steps
    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Laufzeit in Minuten (default: unbegrenzt)",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=None,
        help="Anzahl Steps (default: unbegrenzt)",
    )

    # Session Parameters
    parser.add_argument(
        "--warmup-candles",
        type=int,
        default=200,
        help="Anzahl Warmup-Candles (default: 200)",
    )
    parser.add_argument(
        "--position-fraction",
        type=float,
        default=0.1,
        help="Position-Size als Kapitalanteil (default: 0.1)",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=60.0,
        help="Poll-Intervall in Sekunden (default: 60.0)",
    )
    parser.add_argument(
        "--start-balance",
        type=float,
        default=10000.0,
        help="Simuliertes Startkapital (default: 10000.0)",
    )

    # Environment
    parser.add_argument(
        "--env-name",
        type=str,
        default="shadow_local",
        help="Environment-Name (z.B. kraken_futures_testnet) (default: shadow_local)",
    )

    # Flags
    parser.add_argument(
        "--no-risk-limits",
        action="store_true",
        help="Risk-Limits deaktivieren",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur Config validieren, keine Session starten",
    )
    parser.add_argument(
        "--list-strategies",
        action="store_true",
        help="Verfügbare Strategien auflisten und beenden",
    )

    # Phase 81: Experiment-Registry Integration
    parser.add_argument(
        "--no-registry",
        action="store_true",
        help="Registry-Logging deaktivieren (Phase 81)",
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        default=[],
        help="Tags für Experiment-Registry (z.B. --tags experiment_v1 test_run)",
    )
    parser.add_argument(
        "--notes",
        type=str,
        default=None,
        help="Optionale Notizen für die Session (Phase 81)",
    )

    # Logging
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log-Level (default: INFO)",
    )

    args = parser.parse_args()

    # Strategy-Liste?
    if args.list_strategies:
        list_available_strategies()
        return 0

    # Logging setup
    logger = setup_logging(args.log_level)

    logger.info("=" * 70)
    logger.info("Peak_Trade: Strategy-to-Execution Session (Phase 80/81)")
    logger.info("=" * 70)
    logger.info("WICHTIG: Es werden KEINE echten Orders gesendet!")
    logger.info(f"Mode: {args.mode.upper()} | Strategy: {args.strategy}")
    logger.info("=" * 70)

    # =========================================================================
    # Phase 81: Session mit Registry-Integration
    # =========================================================================

    # Session-Metadaten initialisieren
    started_at = datetime.utcnow()
    finished_at: Optional[datetime] = None
    status = "started"
    error: Optional[str] = None

    # Diese Dicts sammeln Session-Daten
    config: Dict[str, Any] = {}
    metrics: Dict[str, float] = {}

    # Run-Type basierend auf Mode
    run_type = f"live_session_{args.mode}"

    # Session-ID generieren
    from src.experiments.live_session_registry import generate_session_run_id

    session_id = generate_session_run_id(mode=args.mode, prefix="session")
    run_id: Optional[str] = None  # Optional: externe Run-ID

    # Runner-Referenz für finally-Block
    runner = None
    session_config = None

    try:
        # Imports hier um Startup-Zeit zu optimieren
        from src.execution.live_session import (
            LiveSessionConfig,
            LiveSessionRunner,
            LiveModeNotAllowedError,
            SessionSetupError,
            SessionRuntimeError,
        )
        from src.core.peak_config import load_config

        # Config-Datei prüfen
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"Config-Datei nicht gefunden: {config_path}")
            status = "failed"
            error = f"Config-Datei nicht gefunden: {config_path}"
            return 1

        logger.info(f"Lade Config: {config_path}")
        peak_config = load_config(config_path)

        # LiveSessionConfig erstellen
        session_config = LiveSessionConfig(
            mode=args.mode,
            strategy_key=args.strategy,
            symbol=args.symbol,
            timeframe=args.timeframe,
            config_path=str(config_path),
            warmup_candles=args.warmup_candles,
            position_fraction=args.position_fraction,
            poll_interval_seconds=args.poll_interval,
            start_balance=args.start_balance,
            enable_risk_limits=not args.no_risk_limits,
        )

        # Config Dict füllen
        config = {
            "strategy_name": args.strategy,
            "symbol": args.symbol,
            "timeframe": args.timeframe,
            "mode": args.mode,
            "warmup_candles": args.warmup_candles,
            "position_fraction": args.position_fraction,
            "poll_interval": args.poll_interval,
            "start_balance": args.start_balance,
            "enable_risk_limits": not args.no_risk_limits,
            "config_path": str(config_path),
            "env_name": args.env_name,
            "tags": args.tags,
            "notes": args.notes,
        }

        logger.info(f"Session-Config erstellt: {session_config.to_dict()}")

        # Dry-Run?
        if args.dry_run:
            logger.info("Dry-Run: Config validiert, keine Session gestartet.")
            logger.info("Session würde erstellt werden mit:")
            logger.info(f"  - Mode: {session_config.mode}")
            logger.info(f"  - Strategy: {session_config.strategy_key}")
            logger.info(f"  - Symbol: {session_config.symbol}")
            logger.info(f"  - Timeframe: {session_config.timeframe}")
            status = "completed"
            metrics["dry_run"] = 1.0
            return 0

        # LiveSessionRunner erstellen
        logger.info("Erstelle LiveSessionRunner...")
        runner = LiveSessionRunner.from_config(session_config, peak_config=peak_config)
        run_id = runner.run_id

        logger.info(f"Session erstellt: run_id={runner.run_id}")

        # Warmup
        logger.info("Starte Warmup...")
        runner.warmup()
        logger.info("Warmup abgeschlossen")

        # Session starten
        if args.steps:
            logger.info(f"Starte Session für {args.steps} Steps...")
            results = runner.run_n_steps(args.steps, sleep_between=True)
            logger.info(f"Session beendet. {len(results)} Orders ausgeführt.")

        elif args.duration:
            logger.info(f"Starte Session für {args.duration} Minuten...")
            results = runner.run_for_duration(args.duration)
            logger.info(f"Session beendet. {len(results)} Orders ausgeführt.")

        else:
            logger.info("Starte Session (Ctrl+C zum Beenden)...")
            runner.run_forever()

        # Zusammenfassung ausgeben
        summary = runner.get_summary()
        logger.info(f"Session-Summary: {summary['metrics']}")

        # Metrics aus Runner extrahieren
        if hasattr(runner, "metrics") and runner.metrics:
            runner_metrics = (
                runner.metrics.to_dict()
                if hasattr(runner.metrics, "to_dict")
                else runner.metrics
            )
            metrics.update(
                {
                    "realized_pnl": float(runner_metrics.get("realized_pnl", 0.0)),
                    "unrealized_pnl": float(runner_metrics.get("unrealized_pnl", 0.0)),
                    "max_drawdown": float(runner_metrics.get("max_drawdown", 0.0)),
                    "num_orders": float(runner_metrics.get("orders_executed", 0)),
                    "num_trades": float(runner_metrics.get("total_orders_generated", 0)),
                    "steps": float(runner_metrics.get("steps", 0)),
                    "fill_rate": float(runner_metrics.get("fill_rate", 0.0)),
                }
            )

        status = "completed"

    except KeyboardInterrupt:
        status = "aborted"
        error = "KeyboardInterrupt"
        logger.info("Session durch Benutzer beendet (Ctrl+C)")
        # KeyboardInterrupt nicht weiter werfen, da es ein normaler Abbruch ist

    except Exception as exc:
        status = "failed"
        error = f"{type(exc).__name__}: {exc}"
        logger.exception(f"Unerwarteter Fehler: {exc}")
        # Exception nicht weiter werfen, damit finally-Block ausgeführt wird

    finally:
        # finished_at setzen falls noch nicht gesetzt
        if finished_at is None:
            finished_at = datetime.utcnow()

        # =====================================================================
        # Phase 81: Registry-Eintrag erstellen
        # =====================================================================
        if not args.no_registry and not args.dry_run:
            from src.experiments.live_session_registry import (
                LiveSessionRecord,
                register_live_session_run,
            )

            record = LiveSessionRecord(
                session_id=session_id,
                run_id=run_id,
                run_type=run_type,
                mode=args.mode,
                env_name=args.env_name,
                symbol=args.symbol,
                status=status,
                started_at=started_at,
                finished_at=finished_at,
                config=config,
                metrics=metrics,
                cli_args=sys.argv,
                error=error,
            )

            # SAFETY-DESIGN: Registry-Fehler sollen Session nicht brechen
            try:
                path = register_live_session_run(record)
                logger.info("=" * 70)
                logger.info(f"Live session recorded at {path}")
                logger.info(f"  Session-ID: {session_id}")
                logger.info(f"  Run-Type: {run_type}")
                logger.info(f"  Status: {status}")
                logger.info("=" * 70)
            except Exception as registry_exc:
                logger.warning(
                    "Failed to record live session: %s",
                    registry_exc,
                    exc_info=True,
                )

    return 0 if status == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
