#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/run_sweep.py
"""
Peak_Trade: Strategy Parameter Sweep Runner
============================================

Führt Parameter-Sweeps für Strategien durch und loggt Ergebnisse in der Registry.

Ein Sweep testet systematisch alle Kombinationen eines Parameter-Grids:
- z.B. short_window ∈ {5, 10, 20} × long_window ∈ {50, 100, 200}
- Jede Kombination wird als Backtest ausgeführt
- Ergebnisse werden als run_type="sweep" in der Registry geloggt

Usage:
    # Mit TOML-Grid-Datei
    python scripts/run_sweep.py --config config/config.toml --strategy ma_crossover --symbol BTC/EUR --grid config/sweeps/ma_crossover.toml

    # Mit JSON-String
    python scripts/run_sweep.py --config config/config.toml --strategy ma_crossover --symbol BTC/EUR --grid '{"short_window":[5,10,20],"long_window":[50,100]}'

    # Mit Limit und Tag
    python scripts/run_sweep.py --config config/config.toml --strategy ma_crossover --symbol BTC/EUR --grid ... --max-runs 10 --tag grid-test

    # Dry-Run (nur Kombinationen anzeigen)
    python scripts/run_sweep.py --config config/config.toml --strategy ma_crossover --symbol BTC/EUR --grid ... --dry-run
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

# Projekt-Root zum Python-Path hinzufügen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.peak_config import PeakConfig, load_config
from src.core.position_sizing import build_position_sizer_from_config
from src.core.risk import build_risk_manager_from_config
from src.core.experiments import log_sweep_run, RUN_TYPE_SWEEP
from src.backtest.engine import BacktestEngine
from src.strategies.registry import create_strategy_from_config, get_available_strategy_keys
from src.strategies.base import BaseStrategy


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parst CLI-Argumente."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Strategy Parameter Sweep Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Mit TOML-Grid
    python scripts/run_sweep.py --strategy ma_crossover --symbol BTC/EUR \\
        --grid config/sweeps/ma_crossover.toml --tag optimization

    # Mit JSON-Grid
    python scripts/run_sweep.py --strategy ma_crossover --symbol BTC/EUR \\
        --grid '{"short_window":[5,10,20],"long_window":[50,100]}' --tag quick-test

    # Dry-Run
    python scripts/run_sweep.py --strategy ma_crossover --symbol BTC/EUR \\
        --grid config/sweeps/ma_crossover.toml --dry-run
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Basis-Config (Default: config/config.toml)",
    )

    parser.add_argument(
        "--strategy",
        type=str,
        required=True,
        help="Strategie-Key aus der Registry (z.B. ma_crossover, rsi_reversion)",
    )

    parser.add_argument(
        "--symbol",
        type=str,
        default="BTC/EUR",
        help="Symbol für den Backtest (Default: BTC/EUR)",
    )

    parser.add_argument(
        "--timeframe",
        type=str,
        default="1h",
        help="Timeframe für OHLCV-Daten (Default: 1h)",
    )

    parser.add_argument(
        "--grid",
        type=str,
        required=True,
        help="Parameter-Grid: Pfad zu TOML-Datei oder JSON-String",
    )

    parser.add_argument(
        "--data-file",
        type=str,
        default=None,
        help="Pfad zur CSV-Datei mit OHLCV-Daten (optional, sonst Dummy-Daten)",
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=500,
        help="Anzahl Bars für Dummy-Daten (Default: 500)",
    )

    parser.add_argument(
        "--max-runs",
        type=int,
        default=None,
        help="Maximale Anzahl der Kombinationen (optional)",
    )

    parser.add_argument(
        "--sweep-name",
        type=str,
        default=None,
        help="Name für den Sweep (optional, für Gruppierung)",
    )

    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Optionaler Tag für Registry-Logging",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur Kombinationen anzeigen, keine Backtests ausführen",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Ausführliche Ausgabe",
    )

    return parser.parse_args(argv)


def expand_parameter_grid(grid: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    """
    Erzeugt das kartesische Produkt aller Parameterwerte.

    Args:
        grid: Dict mit Parameternamen als Keys und Listen von Werten als Values

    Returns:
        Liste von Dicts, jedes Dict ist eine Parameterkombination

    Example:
        >>> grid = {"short_window": [5, 10], "long_window": [50, 100]}
        >>> expand_parameter_grid(grid)
        [
            {"short_window": 5, "long_window": 50},
            {"short_window": 5, "long_window": 100},
            {"short_window": 10, "long_window": 50},
            {"short_window": 10, "long_window": 100},
        ]
    """
    if not grid:
        return [{}]

    keys = list(grid.keys())
    values = list(grid.values())

    combinations = []
    for combo in itertools.product(*values):
        param_dict = dict(zip(keys, combo))
        combinations.append(param_dict)

    return combinations


def load_parameter_grid(grid_arg: str) -> Dict[str, List[Any]]:
    """
    Lädt ein Parameter-Grid aus TOML-Datei oder JSON-String.

    Args:
        grid_arg: Pfad zu TOML-Datei oder JSON-String

    Returns:
        Parameter-Grid als Dict
    """
    # Versuche als Datei zu laden
    grid_path = Path(grid_arg)
    if grid_path.is_file():
        if grid_path.suffix == ".toml":
            # tomllib ist Python 3.11+, tomli ist Fallback
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib
            with grid_path.open("rb") as f:
                data = tomllib.load(f)
            # Erwarte "grid" Sektion oder Top-Level
            return data.get("grid", data)
        elif grid_path.suffix == ".json":
            with grid_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        else:
            raise ValueError(f"Unbekanntes Dateiformat: {grid_path.suffix}")

    # Versuche als JSON-String zu parsen
    try:
        return json.loads(grid_arg)
    except json.JSONDecodeError as e:
        raise ValueError(f"Konnte Grid nicht laden. Weder gültige Datei noch JSON-String: {e}")


def generate_dummy_ohlcv(
    n_bars: int = 500,
    base_price: float = 50000.0,
    volatility: float = 0.015,
) -> pd.DataFrame:
    """Generiert synthetische OHLCV-Daten für Tests."""
    np.random.seed(42)  # Reproduzierbarkeit

    end = datetime.now()
    start = end - timedelta(hours=n_bars)
    index = pd.date_range(start=start, periods=n_bars, freq="1h", tz="UTC")

    returns = np.random.normal(0, volatility, n_bars)
    trend = np.sin(np.linspace(0, 4 * np.pi, n_bars)) * 0.001
    returns = returns + trend
    close_prices = base_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame(index=index)
    df["close"] = close_prices
    df["open"] = df["close"].shift(1).fillna(base_price)

    high_bump = np.random.uniform(0, 0.005, n_bars)
    df["high"] = np.maximum(df["open"], df["close"]) * (1 + high_bump)

    low_dip = np.random.uniform(0, 0.005, n_bars)
    df["low"] = np.minimum(df["open"], df["close"]) * (1 - low_dip)

    df["volume"] = np.random.uniform(100, 1000, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


def load_ohlcv_data(
    data_file: Optional[str],
    n_bars: int,
    verbose: bool = False,
) -> pd.DataFrame:
    """Lädt OHLCV-Daten aus CSV oder generiert Dummy-Daten."""
    if data_file:
        from src.data import DataNormalizer, CsvLoader, KrakenCsvLoader

        path = Path(data_file)
        if not path.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {data_file}")

        if verbose:
            print(f"  Lade Daten aus: {data_file}")

        if "kraken" in str(path).lower():
            loader = KrakenCsvLoader()
        else:
            loader = CsvLoader()

        df = loader.load(str(path))
        normalizer = DataNormalizer()
        df = normalizer.normalize(df)

    else:
        if verbose:
            print(f"  Generiere {n_bars} Dummy-Bars")
        df = generate_dummy_ohlcv(n_bars=n_bars)

    return df


def run_single_backtest(
    df: pd.DataFrame,
    strategy_key: str,
    params: Dict[str, Any],
    cfg: PeakConfig,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Führt einen einzelnen Backtest mit spezifischen Parametern aus.

    Returns:
        Dict mit Stats (total_return, sharpe, max_drawdown, etc.)
    """
    # Position-Sizer und Risk-Manager aus Config
    position_sizer = build_position_sizer_from_config(cfg)
    risk_manager = build_risk_manager_from_config(cfg, section="risk_management")

    # Strategie erstellen und Parameter überschreiben
    strategy = create_strategy_from_config(strategy_key, cfg)

    # Parameter auf Strategie anwenden
    for key, value in params.items():
        if hasattr(strategy, key):
            setattr(strategy, key, value)

    # Backtest-Engine
    engine = BacktestEngine(
        core_position_sizer=position_sizer,
        risk_manager=risk_manager,
    )

    def strategy_signal_fn(data, _params):
        return strategy.generate_signals(data)

    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=strategy_signal_fn,
        strategy_params=params,
    )

    return result.stats or {}


def print_summary_table(
    results: List[Dict[str, Any]],
    top_n: int = 10,
) -> None:
    """Gibt eine Zusammenfassungstabelle der Top-Ergebnisse aus."""
    if not results:
        print("\nKeine Ergebnisse.")
        return

    # Nach Sharpe sortieren
    sorted_results = sorted(
        results,
        key=lambda x: x.get("stats", {}).get("sharpe", -999),
        reverse=True,
    )

    print(f"\n{'=' * 80}")
    print(f"TOP {min(top_n, len(sorted_results))} ERGEBNISSE (nach Sharpe)")
    print(f"{'=' * 80}")

    header = f"{'#':>3} {'Return':>10} {'Sharpe':>8} {'MaxDD':>10} {'Trades':>7} | Parameter"
    print(header)
    print("-" * 80)

    for i, res in enumerate(sorted_results[:top_n], 1):
        stats = res.get("stats", {})
        params = res.get("params", {})

        total_ret = stats.get("total_return", 0)
        sharpe = stats.get("sharpe", 0)
        max_dd = stats.get("max_drawdown", 0)
        trades = stats.get("total_trades", 0)

        # Parameter-String (kompakt)
        param_str = ", ".join(f"{k}={v}" for k, v in params.items())
        if len(param_str) > 35:
            param_str = param_str[:32] + "..."

        print(f"{i:>3} {total_ret:>10.2%} {sharpe:>8.2f} {max_dd:>10.2%} {trades:>7} | {param_str}")


def main(argv: Optional[List[str]] = None) -> int:
    """Main-Entry-Point für Strategy Sweep."""
    args = parse_args(argv)

    print("\n" + "=" * 70)
    print("Peak_Trade: Strategy Parameter Sweep")
    print("=" * 70)

    # 1) Config laden
    print(f"\n[1/5] Lade Config: {args.config}")
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"  FEHLER: Config nicht gefunden: {config_path}")
        return 1

    try:
        cfg = load_config(config_path)
    except Exception as e:
        print(f"  FEHLER: {e}")
        return 1

    # 2) Strategie validieren
    print(f"\n[2/5] Validiere Strategie: {args.strategy}")
    available = get_available_strategy_keys()
    if args.strategy not in available:
        print(f"  FEHLER: Unbekannter Strategy-Key '{args.strategy}'")
        print(f"  Verfügbar: {', '.join(available)}")
        return 1

    # 3) Parameter-Grid laden
    print(f"\n[3/5] Lade Parameter-Grid...")
    try:
        grid = load_parameter_grid(args.grid)
        combinations = expand_parameter_grid(grid)
        print(f"  Grid: {grid}")
        print(f"  Kombinationen: {len(combinations)}")

        if args.max_runs and len(combinations) > args.max_runs:
            print(f"  Limitiert auf: {args.max_runs} Runs")
            combinations = combinations[: args.max_runs]

    except Exception as e:
        print(f"  FEHLER beim Laden des Grids: {e}")
        return 1

    # Dry-Run: nur Kombinationen anzeigen
    if args.dry_run:
        print("\n[DRY-RUN] Folgende Kombinationen würden getestet:")
        for i, combo in enumerate(combinations, 1):
            print(f"  {i:>3}. {combo}")
        print(f"\nGesamt: {len(combinations)} Kombinationen")
        print("(Kein Backtest ausgeführt)")
        return 0

    # 4) Daten laden
    print(f"\n[4/5] Lade OHLCV-Daten...")
    try:
        df = load_ohlcv_data(
            data_file=args.data_file,
            n_bars=args.bars,
            verbose=args.verbose,
        )
        print(f"  {len(df)} Bars geladen")
    except Exception as e:
        print(f"  FEHLER: {e}")
        return 1

    # 5) Sweeps ausführen
    print(f"\n[5/5] Führe {len(combinations)} Backtests aus...")

    results = []
    sweep_name = args.sweep_name or f"{args.strategy}_sweep"

    for i, params in enumerate(combinations, 1):
        if args.verbose:
            print(f"  [{i}/{len(combinations)}] {params}")
        else:
            # Fortschrittsanzeige
            pct = i / len(combinations) * 100
            print(f"\r  Fortschritt: {i}/{len(combinations)} ({pct:.0f}%)", end="", flush=True)

        try:
            stats = run_single_backtest(
                df=df,
                strategy_key=args.strategy,
                params=params,
                cfg=cfg,
                verbose=args.verbose,
            )

            # In Registry loggen
            run_id = log_sweep_run(
                strategy_key=args.strategy,
                symbol=args.symbol,
                timeframe=args.timeframe,
                params=params,
                stats=stats,
                sweep_name=sweep_name,
                tag=args.tag,
                config_path=str(config_path),
            )

            results.append(
                {
                    "params": params,
                    "stats": stats,
                    "run_id": run_id,
                }
            )

        except Exception as e:
            if args.verbose:
                print(f"    FEHLER: {e}")
            results.append(
                {
                    "params": params,
                    "stats": {},
                    "error": str(e),
                }
            )

    print()  # Newline nach Fortschrittsanzeige

    # Zusammenfassung
    successful = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]

    print(f"\n{'=' * 70}")
    print("SWEEP ABGESCHLOSSEN")
    print(f"{'=' * 70}")
    print(f"  Strategie:   {args.strategy}")
    print(f"  Symbol:      {args.symbol}")
    print(f"  Sweep-Name:  {sweep_name}")
    print(f"  Erfolgreich: {len(successful)}/{len(combinations)}")
    if failed:
        print(f"  Fehlgeschlagen: {len(failed)}")

    # Top-Ergebnisse anzeigen
    print_summary_table(successful, top_n=10)

    print(f"\nErgebnisse in Registry gespeichert mit sweep_name='{sweep_name}'")
    if args.tag:
        print(f"Tag: {args.tag}")

    print("\nNächste Schritte:")
    print(f"  python scripts/list_experiments.py --run-type sweep")
    print(
        f"  python scripts/analyze_experiments.py --mode top-runs --run-type sweep --metric sharpe"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
