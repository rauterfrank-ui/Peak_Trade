#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/generate_forward_signals.py
"""
Peak_Trade: Forward-/Paper-Trading-Signale für ein Symbol-Universum erzeugen
=============================================================================

Erzeugt Forward-Signale für eine Strategie über ein Symbol-Universum.
Die Signale werden als CSV gespeichert und in der Experiment-Registry geloggt.

Usage:
    python scripts/generate_forward_signals.py --strategy ma_crossover
    python scripts/generate_forward_signals.py --strategy ma_crossover --symbols BTC/EUR,ETH/EUR
    python scripts/generate_forward_signals.py --strategy ma_crossover --run-name forward_daily_2025-12-04
"""

from __future__ import annotations

import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Projekt-Root und scripts/-Verzeichnis (shared loader) zum Python-Path
_root = Path(__file__).resolve().parent.parent
_scripts = Path(__file__).resolve().parent
sys.path.insert(0, str(_root))
sys.path.insert(0, str(_scripts))

import pandas as pd

from src.core.peak_config import load_config, PeakConfig
from src.core.experiments import log_generic_experiment
from src.forward.signals import ForwardSignal, save_signals_to_csv
from src.strategies.registry import create_strategy_from_config, get_available_strategy_keys
from src.analytics.risk_monitor import (
    RiskPolicy,
    load_experiments_df as load_experiments_df_risk,
    filter_by_lookback,
    annotate_runs_with_risk,
    aggregate_strategy_risk,
)
from src.analytics.filter_flow import SelectionPolicy, build_strategy_selection
from _shared_ohlcv_loader import load_dummy_ohlcv


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Forward-/Paper-Trading-Signale für ein Symbol-Universum erzeugen.",
    )
    parser.add_argument(
        "--strategy",
        required=True,
        help="Strategy-Key (wie in der Registry), z.B. ma_crossover.",
    )
    parser.add_argument(
        "--symbols",
        help=(
            "Kommagetrennte Liste von Symbolen, z.B. 'BTC/EUR,ETH/EUR'. "
            "Wenn nicht gesetzt, wird versucht, [scan].universe aus config.toml zu verwenden."
        ),
    )
    parser.add_argument(
        "--run-name",
        help="Name dieses Forward-Runs (z.B. forward_daily_2025-12-04).",
    )
    parser.add_argument(
        "--config-path",
        default="config.toml",
        help="Pfad zur TOML-Config (Default: config.toml).",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/forward",
        help="Zielverzeichnis für Signal-CSV (Default: reports/forward).",
    )
    parser.add_argument(
        "--n-bars",
        type=int,
        default=200,
        help="Anzahl Bars für Daten-Simulation (Default: 200).",
    )
    parser.add_argument(
        "--enforce-selection",
        action="store_true",
        help=(
            "Wenn gesetzt, wird der angegebene Strategy-Key gegen den Filter-Flow geprüft "
            "und nur zugelassen, wenn selection_status='APPROVED' ist."
        ),
    )
    return parser.parse_args(argv)


def load_data_for_symbol(symbol: str, n_bars: int = 200) -> pd.DataFrame:
    """
    Lädt Daten für ein bestimmtes Symbol.

    J1 Slice 1: Dummy-OHLCV über ``scripts/_shared_ohlcv_loader.load_dummy_ohlcv``
    (read-only, keine Orders/Keys, kein C1-Bezug; Vertrag siehe Modul-Docstring dort).
    Später: echte Kraken-Daten (J1 weiter); evaluate/portfolio in Slice 2/3 auf denselben Loader.

    Args:
        symbol: Trading-Pair (z.B. "BTC/EUR")
        n_bars: Anzahl Bars

    Returns:
        DataFrame mit OHLCV-Daten
    """
    return load_dummy_ohlcv(symbol, n_bars=n_bars)


def determine_universe(cfg: Any, symbols_arg: str | None) -> List[str]:
    if symbols_arg:
        return [s.strip() for s in symbols_arg.split(",") if s.strip()]

    # Fallback: [scan].universe aus config.toml
    universe = cfg.get("scan.universe", [])
    if not universe:
        raise ValueError(
            "Keine Symbole angegeben und [scan].universe in config.toml ist leer. "
            "Bitte --symbols setzen oder scan.universe konfigurieren."
        )
    return list(universe)


def enforce_strategy_selection(cfg: PeakConfig, strategy_key: str) -> None:
    """
    Prüft, ob eine Strategie laut Filter-Flow als APPROVED gilt.
    Falls nicht, wird eine ValueError geworfen.
    """
    risk_policy = RiskPolicy.from_config(cfg)
    sel_policy = SelectionPolicy.from_config(cfg)

    df = load_experiments_df_risk()
    df = filter_by_lookback(df, risk_policy)
    if df.empty:
        raise ValueError(
            "Filter-Flow Enforcement: Keine Experimente im Lookback – kann Strategie nicht bewerten."
        )

    df_runs = annotate_runs_with_risk(df, risk_policy)
    df_strat_risk = aggregate_strategy_risk(df_runs, risk_policy)

    df_sel = build_strategy_selection(df_runs, df_strat_risk, sel_policy)

    row = df_sel[df_sel["strategy_key"] == strategy_key]
    if row.empty:
        raise ValueError(
            f"Filter-Flow Enforcement: Strategy-Key {strategy_key!r} hat keine Daten im Lookback."
        )

    status = row["selection_status"].iloc[0]
    reasons = row["selection_reasons"].iloc[0]
    if status != "APPROVED":
        raise ValueError(
            f"Filter-Flow Enforcement: Strategy-Key {strategy_key!r} ist nicht APPROVED "
            f"(selection_status={status}, reasons={reasons})."
        )

    print(
        f"Filter-Flow Enforcement: Strategy-Key {strategy_key!r} ist APPROVED (reasons={reasons})."
    )


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    print("\n🔮 Peak_Trade Forward Signal Generator")
    print("=" * 70)

    cfg = load_config(args.config_path)

    strategy_key = args.strategy
    available = get_available_strategy_keys()
    if strategy_key not in available:
        raise ValueError(f"Unbekannter Strategy-Key {strategy_key!r}. Verfügbar: {available}")

    # Filter-Flow Enforcement (optional)
    if args.enforce_selection:
        enforce_strategy_selection(cfg, strategy_key)

    universe = determine_universe(cfg, args.symbols)
    run_name = (
        args.run_name or f"forward_{strategy_key}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    )

    print(f"\n⚙️  Konfiguration:")
    print(f"  Strategy:      {strategy_key}")
    print(f"  Universe:      {universe}")
    print(f"  Run-Name:      {run_name}")
    print(f"  Bars:          {args.n_bars}")

    signals: List[ForwardSignal] = []

    generated_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    for symbol in universe:
        print(f"\n📊 Verarbeite Symbol: {symbol}")
        data = load_data_for_symbol(symbol, n_bars=args.n_bars)
        if data.empty:
            print(f"  ⚠️  Keine Daten für {symbol}, überspringe.")
            continue

        strategy = create_strategy_from_config(strategy_key, cfg)

        if not hasattr(strategy, "generate_signals"):
            raise AttributeError(
                f"Strategy {strategy!r} hat keine Methode generate_signals(data). "
                "Bitte sicherstellen, dass die Strategie diese API unterstützt."
            )

        # Vollständige Signale berechnen
        signals_series = strategy.generate_signals(data)
        if signals_series is None or signals_series.empty:
            print(f"  ⚠️  generate_signals() liefert keine Signale für {symbol}, überspringe.")
            continue

        # Letztes Signal als Forward-Signal verwenden
        last_ts = signals_series.index[-1]
        last_val = float(signals_series.iloc[-1])

        print(f"  ✅ Letztes Signal: {last_val} @ {last_ts}")

        sig = ForwardSignal(
            generated_at=generated_at,
            as_of=str(last_ts),
            strategy_key=strategy_key,
            run_name=run_name,
            symbol=symbol,
            direction=last_val,
            size_hint=None,
            comment=None,
            extra={
                "raw_last_signal": last_val,
            },
        )
        signals.append(sig)

    if not signals:
        print("\n⚠️  Keine Forward-Signale erzeugt – nichts zu speichern.")
        return

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{run_name}_signals.csv"

    df_signals = save_signals_to_csv(signals, out_path)
    print(f"\n💾 Forward-Signale gespeichert: {out_path}")
    print(f"\n📋 Generierte Signale:")
    print(df_signals.to_string(index=False))

    # Experiment-Registry-Log (ohne klassische Backtest-Stats)
    log_generic_experiment(
        run_type="forward_signals",
        run_name=run_name,
        strategy_key=strategy_key,
        symbol=None,  # mehrere Symbole → im metadata-Block
        stats=None,
        report_dir=out_dir,
        report_prefix=run_name,
        extra_metadata={
            "runner": "generate_forward_signals.py",
            "universe": universe,
            "signal_csv": str(out_path),
            "n_signals": len(signals),
        },
    )
    print(f"\n📝 Forward-Signal-Run in Registry geloggt (run_type='forward_signals')")
    print(f"✅ Forward-Signal-Generierung abgeschlossen!\n")


if __name__ == "__main__":
    main()
