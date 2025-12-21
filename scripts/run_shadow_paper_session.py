#!/usr/bin/env python3
"""
Peak_Trade: Shadow/Paper Session CLI (Phase 31 + 32)
=====================================================

Command-Line-Interface zum Starten einer Shadow-/Paper-Trading-Session
mit echten Exchange-Marktdaten (nur public data, keine echten Orders).

Phase 32: Erweiterung um Run-Logging mit strukturierten Events.

Usage:
    python -m scripts.run_shadow_paper_session --config config/config.toml --strategy ma_crossover

    # Mit anderem Symbol und Timeframe:
    python -m scripts.run_shadow_paper_session --symbol ETH/EUR --timeframe 5m

    # Für begrenzte Dauer (z.B. 30 Minuten):
    python -m scripts.run_shadow_paper_session --duration 30

    # Mit spezifischer Run-ID (Phase 32):
    python -m scripts.run_shadow_paper_session --run-id my_test_run_001

    # Logging deaktivieren:
    python -m scripts.run_shadow_paper_session --no-logging

    # Alternatives Log-Verzeichnis:
    python -m scripts.run_shadow_paper_session --log-dir /tmp/runs

WICHTIG: Diese Session sendet NIEMALS echte Orders!
         Nur PAPER Environment-Modus ist erlaubt.

Verfügbare Strategien:
- ma_crossover: Moving Average Crossover
- momentum_1h: Momentum Strategie
- rsi_strategy: RSI Mean-Reversion
- macd: MACD Trend-Following

Zum Beenden: Ctrl+C (SIGINT) oder SIGTERM
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Projekt-Root zum Path hinzufügen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.peak_config import load_config, PeakConfig
from src.core.environment import (
    get_environment_from_config,
    TradingEnvironment,
    EnvironmentConfig,
)
from src.live.risk_limits import LiveRiskLimits
from src.live.shadow_session import (
    ShadowPaperSession,
    ShadowPaperSessionMetrics,
    EnvironmentNotAllowedError,
    ALLOWED_ENVIRONMENT_MODES,
    create_shadow_paper_session,
)
from src.live.run_logging import (
    LiveRunLogger,
    LiveRunMetadata,
    ShadowPaperLoggingConfig,
    load_shadow_paper_logging_config,
    generate_run_id,
    create_run_logger_from_config,
)
from src.data.kraken_live import (
    KrakenLiveCandleSource,
    ShadowPaperConfig,
    LiveExchangeConfig,
    load_shadow_paper_config,
    load_live_exchange_config,
)
from src.orders.shadow import ShadowMarketContext, ShadowOrderExecutor
from src.execution.pipeline import ExecutionPipeline
from src.strategies.base import BaseStrategy


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

    # Weniger Noise von requests/urllib3
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    return logging.getLogger("shadow_paper_session")


# =============================================================================
# Strategy Factory
# =============================================================================


def create_strategy(strategy_name: str, cfg: PeakConfig) -> BaseStrategy:
    """
    Factory für Trading-Strategien.

    Args:
        strategy_name: Name der Strategie
        cfg: PeakConfig für Parameter

    Returns:
        Strategie-Instanz

    Raises:
        ValueError: Bei unbekannter Strategie
    """
    from src.strategies.ma_crossover import MACrossoverStrategy

    strategy_map = {
        "ma_crossover": lambda: MACrossoverStrategy.from_config(cfg, "strategy.ma_crossover"),
    }

    # Versuche weitere Strategien zu importieren
    try:
        from src.strategies.momentum import MomentumStrategy

        strategy_map["momentum_1h"] = lambda: MomentumStrategy.from_config(
            cfg, "strategy.momentum_1h"
        )
    except ImportError:
        pass

    try:
        from src.strategies.rsi_reversion import RSIStrategy

        strategy_map["rsi_strategy"] = lambda: RSIStrategy.from_config(cfg, "strategy.rsi_strategy")
    except ImportError:
        pass

    try:
        from src.strategies.macd import MACDStrategy

        strategy_map["macd"] = lambda: MACDStrategy.from_config(cfg, "strategy.macd")
    except ImportError:
        pass

    if strategy_name not in strategy_map:
        available = list(strategy_map.keys())
        raise ValueError(f"Unbekannte Strategie: '{strategy_name}'. Verfügbar: {available}")

    return strategy_map[strategy_name]()


# =============================================================================
# Session Builder
# =============================================================================


def build_session(
    cfg: PeakConfig,
    strategy_name: str,
    symbol_override: Optional[str] = None,
    timeframe_override: Optional[str] = None,
    run_id: Optional[str] = None,
    enable_logging: bool = True,
    log_dir_override: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> ShadowPaperSession:
    """
    Baut eine komplett konfigurierte ShadowPaperSession.

    Args:
        cfg: PeakConfig
        strategy_name: Name der Strategie
        symbol_override: Optionales Symbol-Override
        timeframe_override: Optionales Timeframe-Override
        run_id: Optionale Run-ID für Logging (sonst automatisch generiert)
        enable_logging: Run-Logging aktivieren (default: True)
        log_dir_override: Optionales Log-Verzeichnis-Override
        logger: Logger-Instanz

    Returns:
        ShadowPaperSession-Instanz

    Raises:
        EnvironmentNotAllowedError: Bei nicht erlaubtem Environment
        ValueError: Bei ungültiger Konfiguration
    """
    logger = logger or logging.getLogger(__name__)

    # 1. Configs laden
    shadow_cfg = load_shadow_paper_config(cfg)
    exchange_cfg = load_live_exchange_config(cfg)
    env_config = get_environment_from_config(cfg)
    logging_cfg = load_shadow_paper_logging_config(cfg)

    # Overrides anwenden
    if symbol_override:
        shadow_cfg.symbol = symbol_override
    if timeframe_override:
        shadow_cfg.timeframe = timeframe_override

    # 2. Environment-Check
    logger.info(f"Environment-Modus: {env_config.environment.value}")

    if env_config.environment not in ALLOWED_ENVIRONMENT_MODES:
        raise EnvironmentNotAllowedError(
            f"Environment '{env_config.environment.value}' nicht erlaubt. "
            f"Setze [environment] mode = 'paper' in config.toml"
        )

    # 3. Strategie erstellen
    logger.info(f"Lade Strategie: {strategy_name}")
    strategy = create_strategy(strategy_name, cfg)
    logger.info(f"Strategie geladen: {strategy}")

    # 4. Datenquelle erstellen
    logger.info(f"Initialisiere Datenquelle: {shadow_cfg.symbol} @ {shadow_cfg.timeframe}")
    data_source = KrakenLiveCandleSource(
        symbol=shadow_cfg.symbol,
        timeframe=shadow_cfg.timeframe,
        base_url=exchange_cfg.base_url,
        warmup_candles=shadow_cfg.warmup_candles,
        max_retries=exchange_cfg.max_retries,
        retry_delay=exchange_cfg.retry_delay_seconds,
        rate_limit_ms=exchange_cfg.rate_limit_ms,
    )

    # 5. Execution-Pipeline mit Shadow-Executor
    logger.info("Initialisiere Execution-Pipeline (Shadow-Modus)")
    market_context = ShadowMarketContext(
        fee_rate=shadow_cfg.fee_rate,
        slippage_bps=shadow_cfg.slippage_bps,
    )
    pipeline = ExecutionPipeline.for_shadow(
        market_context=market_context,
        fee_rate=shadow_cfg.fee_rate,
        slippage_bps=shadow_cfg.slippage_bps,
    )

    # 6. Risk-Limits
    logger.info("Initialisiere Risk-Limits")
    risk_limits = LiveRiskLimits.from_config(cfg, starting_cash=shadow_cfg.start_balance)

    # 7. Run-Logger erstellen (Phase 32)
    run_logger: Optional[LiveRunLogger] = None
    effective_run_id: Optional[str] = None

    if enable_logging and logging_cfg.enabled:
        # Run-ID generieren falls nicht übergeben
        effective_run_id = run_id or generate_run_id(
            mode=shadow_cfg.mode,
            strategy_name=strategy_name,
            symbol=shadow_cfg.symbol,
            timeframe=shadow_cfg.timeframe,
        )

        # Config-Snapshot für Metadaten
        config_snapshot = {
            "shadow_paper": {
                "mode": shadow_cfg.mode,
                "symbol": shadow_cfg.symbol,
                "timeframe": shadow_cfg.timeframe,
                "start_balance": shadow_cfg.start_balance,
                "position_fraction": shadow_cfg.position_fraction,
                "fee_rate": shadow_cfg.fee_rate,
                "slippage_bps": shadow_cfg.slippage_bps,
            },
            "strategy": {"key": strategy_name},
        }

        metadata = LiveRunMetadata(
            run_id=effective_run_id,
            mode=shadow_cfg.mode,
            strategy_name=strategy_name,
            symbol=shadow_cfg.symbol,
            timeframe=shadow_cfg.timeframe,
            config_snapshot=config_snapshot,
        )

        run_logger = LiveRunLogger(
            logging_cfg=logging_cfg,
            metadata=metadata,
            base_dir_override=log_dir_override,
        )
        run_logger.initialize()

        logger.info(f"Run-Logging aktiviert: run_id={effective_run_id}")
        logger.info(f"Run-Verzeichnis: {run_logger.run_dir}")
        logger.info("")
        logger.info("Tip: You can monitor this run in real-time with:")
        logger.info(f"  python -m scripts.monitor_live_run --run-dir {run_logger.run_dir}")
        logger.info("Or monitor the latest run:")
        logger.info("  python -m scripts.monitor_live_run --latest")
        logger.info("")
    else:
        logger.info("Run-Logging deaktiviert")

    # 8. Session erstellen
    session = ShadowPaperSession(
        env_config=env_config,
        shadow_cfg=shadow_cfg,
        exchange_cfg=exchange_cfg,
        data_source=data_source,
        strategy=strategy,
        pipeline=pipeline,
        risk_limits=risk_limits,
        run_logger=run_logger,
    )

    return session


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> int:
    """
    Haupteinstiegspunkt für Shadow/Paper Session CLI.

    Returns:
        Exit-Code (0 = Success, 1 = Error)
    """
    parser = argparse.ArgumentParser(
        description="Run Peak_Trade Shadow/Paper Session with live exchange data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Standard-Start mit MA-Crossover:
  python -m scripts.run_shadow_paper_session

  # Mit anderer Strategie:
  python -m scripts.run_shadow_paper_session --strategy rsi_strategy

  # Mit anderem Symbol:
  python -m scripts.run_shadow_paper_session --symbol ETH/EUR

  # Für begrenzte Zeit (30 Minuten):
  python -m scripts.run_shadow_paper_session --duration 30

WICHTIG: Es werden KEINE echten Orders gesendet!
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Config-Datei (default: config/config.toml)",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default="ma_crossover",
        help="Strategie-Name (default: ma_crossover)",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default=None,
        help="Trading-Symbol override (z.B. ETH/EUR)",
    )
    parser.add_argument(
        "--timeframe",
        type=str,
        default=None,
        help="Timeframe override (z.B. 5m, 1h)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Laufzeit in Minuten (default: unbegrenzt)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log-Level (default: INFO)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur Config laden und validieren, keine Session starten",
    )

    # Phase 32: Logging-Optionen
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Spezifische Run-ID für Logging (default: automatisch generiert)",
    )
    parser.add_argument(
        "--no-logging",
        action="store_true",
        help="Run-Logging deaktivieren",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help="Alternatives Verzeichnis für Run-Logs (default: aus Config)",
    )

    args = parser.parse_args()

    # Logging setup
    logger = setup_logging(args.log_level)

    logger.info("=" * 60)
    logger.info("Peak_Trade Shadow/Paper Session (Phase 31 + 32)")
    logger.info("=" * 60)
    logger.info("WICHTIG: Es werden KEINE echten Orders gesendet!")
    logger.info("Phase 32: Run-Logging mit strukturierten Events")
    logger.info("=" * 60)

    try:
        # Config laden
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"Config-Datei nicht gefunden: {config_path}")
            return 1

        logger.info(f"Lade Config: {config_path}")
        cfg = load_config(config_path)

        # Session bauen
        session = build_session(
            cfg=cfg,
            strategy_name=args.strategy,
            symbol_override=args.symbol,
            timeframe_override=args.timeframe,
            run_id=args.run_id,
            enable_logging=not args.no_logging,
            log_dir_override=args.log_dir,
            logger=logger,
        )

        if args.dry_run:
            logger.info("Dry-Run: Session erfolgreich konfiguriert, keine Ausführung.")
            return 0

        # Warmup
        logger.info("Starte Warmup...")
        session.warmup()

        # Session starten
        if args.duration:
            logger.info(f"Starte Session für {args.duration} Minuten...")
            results = session.run_for_duration(args.duration)
            logger.info(f"Session beendet. {len(results)} Orders ausgeführt.")
        else:
            logger.info("Starte Session (Ctrl+C zum Beenden)...")
            session.run_forever()

        # Zusammenfassung ausgeben
        summary = session.get_execution_summary()
        logger.info(f"Session-Summary: {summary}")

        # Run-Logger-Info ausgeben (Phase 32)
        if session.run_logger:
            logger.info(
                f"Run-Logs gespeichert: {session.run_logger.run_dir}, "
                f"events={session.run_logger.total_events_logged}"
            )

        return 0

    except EnvironmentNotAllowedError as e:
        logger.error(f"Environment-Fehler: {e}")
        logger.error("Lösung: Setze [environment] mode = 'paper' in config/config.toml")
        return 1

    except ValueError as e:
        logger.error(f"Konfigurations-Fehler: {e}")
        return 1

    except KeyboardInterrupt:
        logger.info("Session durch Benutzer beendet (Ctrl+C)")
        return 0

    except Exception as e:
        logger.exception(f"Unerwarteter Fehler: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
