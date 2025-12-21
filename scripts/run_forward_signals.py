#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/run_forward_signals.py
"""
Peak_Trade: Forward-Signal-Generierung mit echtem Exchange-Client
==================================================================

Dieses Script holt aktuelle Marktdaten über den Exchange-Layer,
führt eine Strategie darauf aus und generiert Forward-Signale
(virtuelle Trades ohne Order-Placement).

Jeder Run wird in der Registry als `RUN_TYPE_FORWARD_SIGNAL` geloggt.

Usage:
    # Standard: Strategie & Symbol aus CLI
    python scripts/run_forward_signals.py --strategy ma_crossover --symbol BTC/EUR

    # Mit optionalem Tag
    python scripts/run_forward_signals.py --strategy ma_crossover --symbol BTC/EUR --tag morning-scan

    # Mit spezifischem Timeframe
    python scripts/run_forward_signals.py --strategy rsi_reversion --symbol ETH/EUR --timeframe 4h --bars 300

    # Mit spezifischer Config
    python scripts/run_forward_signals.py --config my_config.toml --strategy ma_crossover --symbol BTC/EUR
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from src.core.peak_config import load_config, PeakConfig
from src.core.experiments import log_forward_signal_run, RUN_TYPE_FORWARD_SIGNAL
from src.exchange import build_exchange_client_from_config
from src.strategies.registry import create_strategy_from_config, get_available_strategy_keys
from src.notifications import Alert, ConsoleNotifier, FileNotifier, CombinedNotifier
from src.notifications.base import signal_level_from_value

# Default Alert-Logdatei
DEFAULT_ALERT_LOG = Path("logs/alerts.log")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parst CLI-Argumente."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Forward-Signal-Generierung mit Exchange-Daten.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/run_forward_signals.py --strategy ma_crossover --symbol BTC/EUR
    python scripts/run_forward_signals.py --strategy rsi_reversion --symbol ETH/EUR --timeframe 4h
    python scripts/run_forward_signals.py --strategy ma_crossover --symbol BTC/EUR --tag morning-scan
        """,
    )

    parser.add_argument(
        "--config",
        default="config.toml",
        help="Pfad zur TOML-Config (Default: config.toml)",
    )

    parser.add_argument(
        "--strategy",
        required=True,
        help="Strategie-Key aus der Registry (z.B. ma_crossover, rsi_reversion)",
    )

    parser.add_argument(
        "--symbol",
        required=True,
        help="Trading-Pair (z.B. BTC/EUR, ETH/USDT)",
    )

    parser.add_argument(
        "--timeframe",
        default="1h",
        help="Timeframe für OHLCV-Daten (z.B. 1m, 5m, 1h, 4h, 1d). Default: 1h",
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=200,
        help="Anzahl der letzten Bars für Signal-Berechnung (Default: 200)",
    )

    parser.add_argument(
        "--tag",
        default=None,
        help="Optionaler Tag für Registry-Logging (z.B. morning-scan, daily)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur Signal berechnen, nicht in Registry loggen (für Tests)",
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

    return parser.parse_args(argv)


def format_signal(signal: float) -> str:
    """Formatiert einen Signal-Wert als lesbare Richtungsangabe."""
    if signal > 0:
        return f"+{signal:.0f} (LONG)"
    elif signal < 0:
        return f"{signal:.0f} (SHORT)"
    return "0 (FLAT)"


def print_summary(
    *,
    run_id: Optional[str],
    exchange_name: str,
    symbol: str,
    timeframe: str,
    last_timestamp: pd.Timestamp,
    last_price: float,
    last_signal: float,
    strategy_key: str,
    tag: Optional[str],
    dry_run: bool = False,
) -> None:
    """Gibt eine formatierte Summary auf der CLI aus."""
    print()
    if dry_run:
        print("[Forward Signal] DRY-RUN (nicht geloggt)")
    else:
        print(f"[Forward Signal] run_id={run_id}")

    print(f"  Exchange   : {exchange_name}")
    print(f"  Symbol     : {symbol}")
    print(f"  Timeframe  : {timeframe}")
    print(f"  Timestamp  : {last_timestamp.isoformat()}")
    print(f"  Last Close : {last_price:.2f}")
    print(f"  Signal     : {format_signal(last_signal)}")
    print(f"  Strategy   : {strategy_key}")
    if tag:
        print(f"  Tag        : {tag}")
    print()


def main(argv: Optional[List[str]] = None) -> int:
    """Main-Entry-Point für Forward-Signal-Generierung."""
    args = parse_args(argv)

    print("\n" + "=" * 70)
    print("Peak_Trade: Forward-Signal Generator")
    print("=" * 70)

    # 1) Config laden
    print(f"\n[1/6] Lade Config: {args.config}")
    try:
        cfg = load_config(args.config)
        print(f"      Config erfolgreich geladen.")
    except FileNotFoundError as e:
        print(f"      FEHLER: {e}")
        return 1

    # 2) Strategie validieren
    print(f"\n[2/6] Validiere Strategie: {args.strategy}")
    available = get_available_strategy_keys()
    if args.strategy not in available:
        print(f"      FEHLER: Unbekannter Strategy-Key '{args.strategy}'")
        print(f"      Verfuegbar: {', '.join(available)}")
        return 1
    print(f"      Strategie '{args.strategy}' ist registriert.")

    # 3) Exchange-Client bauen
    print(f"\n[3/6] Baue Exchange-Client...")
    try:
        ex_client = build_exchange_client_from_config(cfg)
        exchange_name = ex_client.get_name()
        print(f"      Exchange: {exchange_name}")
    except Exception as e:
        print(f"      FEHLER beim Erstellen des Exchange-Clients: {e}")
        return 1

    # 4) OHLCV-Daten holen
    print(f"\n[4/6] Hole OHLCV-Daten: {args.symbol} @ {args.timeframe} (limit={args.bars})")
    try:
        df = ex_client.fetch_ohlcv(
            symbol=args.symbol,
            timeframe=args.timeframe,
            limit=args.bars,
        )
        if df.empty:
            print(f"      FEHLER: Keine Daten fuer {args.symbol} erhalten.")
            return 1
        print(f"      {len(df)} Bars empfangen (von {df.index[0]} bis {df.index[-1]})")
    except Exception as e:
        print(f"      FEHLER beim Abrufen von OHLCV: {e}")
        return 1

    # 5) Strategie erstellen und Signale generieren
    print(f"\n[5/6] Generiere Signale mit Strategie '{args.strategy}'...")
    try:
        strategy = create_strategy_from_config(args.strategy, cfg)
        print(f"      Strategie instanziiert: {strategy}")

        signals = strategy.generate_signals(df)
        if signals is None or signals.empty:
            print(f"      FEHLER: Strategie liefert keine Signale.")
            return 1

        # Letztes Signal extrahieren
        last_ts = signals.index[-1]
        last_signal = float(signals.iloc[-1])
        last_price = float(df["close"].iloc[-1])

        print(f"      Signale berechnet: {len(signals)} Werte")
        print(f"      Letztes Signal: {format_signal(last_signal)} @ {last_ts}")
    except Exception as e:
        print(f"      FEHLER bei Signalberechnung: {e}")
        import traceback

        traceback.print_exc()
        return 1

    # 6) In Registry loggen (wenn nicht dry-run)
    print(f"\n[6/6] Registry-Logging...")
    run_id: Optional[str] = None

    if args.dry_run:
        print(f"      DRY-RUN: Ueberspringe Registry-Logging.")
    else:
        try:
            run_id = log_forward_signal_run(
                strategy_key=args.strategy,
                symbol=args.symbol,
                timeframe=args.timeframe,
                last_timestamp=last_ts,
                last_signal=last_signal,
                last_price=last_price,
                tag=args.tag,
                config_path=str(args.config),
                exchange_name=exchange_name,
                bars_fetched=len(df),
            )
            print(f"      Run geloggt mit ID: {run_id}")
        except Exception as e:
            print(f"      WARNUNG: Registry-Logging fehlgeschlagen: {e}")
            # Kein Exit, Signal wurde trotzdem berechnet

    # Summary ausgeben
    print_summary(
        run_id=run_id,
        exchange_name=exchange_name,
        symbol=args.symbol,
        timeframe=args.timeframe,
        last_timestamp=last_ts,
        last_price=last_price,
        last_signal=last_signal,
        strategy_key=args.strategy,
        tag=args.tag,
        dry_run=args.dry_run,
    )

    # =========================================================================
    # ALERT SENDEN
    # =========================================================================
    if not args.no_alerts:
        from datetime import datetime

        # Notifier konfigurieren
        notifiers = [ConsoleNotifier(show_context=True)]
        if args.alert_log:
            notifiers.append(FileNotifier(args.alert_log))
        notifier = CombinedNotifier(notifiers)

        # Alert-Level basierend auf Signalstärke
        alert_level = signal_level_from_value(last_signal)

        # Signal-Richtung für Message
        if last_signal > 0:
            direction = "LONG"
        elif last_signal < 0:
            direction = "SHORT"
        else:
            direction = "FLAT"

        alert = Alert(
            level=alert_level,
            source="forward_signal",
            message=f"{args.strategy} on {args.symbol} ({args.timeframe}): {direction} @ {last_price:.2f}",
            timestamp=datetime.utcnow(),
            context={
                "strategy_key": args.strategy,
                "symbol": args.symbol,
                "timeframe": args.timeframe,
                "last_signal": float(last_signal),
                "last_price": float(last_price),
                "last_timestamp": last_ts.isoformat(),
                "run_id": run_id,
                "tag": args.tag,
            },
        )
        notifier.send(alert)

    print("Forward-Signal-Generierung erfolgreich abgeschlossen!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
