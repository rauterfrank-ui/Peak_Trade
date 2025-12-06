#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/run_sweep_strategy.py
"""
Peak_Trade: Strategy Hyperparameter Sweep Runner (Phase 20)
============================================================

Führt systematische Hyperparameter-Sweeps für Strategien durch.

Dieses Script ist Teil von Phase 20 (Hyperparameter-Sweeps & Experiment-Orchestrierung)
und nutzt die neue Sweep-Engine aus src/sweeps/.

Features:
- Grid-Search über alle Parameterkombinationen
- Volle Integration mit Experiments-Registry
- Flexible Parameter-Spezifikation (TOML, JSON, CLI)
- Ranking und Top-N Ausgabe
- CSV-Export der Ergebnisse

Safety:
- Nur Backtest-Runs, keine Live- oder Testnet-Orders
- SafetyGuard und TradingEnvironment bleiben unverändert

Usage:
    # Mit TOML-Grid-Datei
    python scripts/run_sweep_strategy.py --strategy ma_crossover \\
        --grid config/sweeps/ma_crossover.toml

    # Mit CLI-Parametern
    python scripts/run_sweep_strategy.py --strategy my_strategy \\
        --param lookback_window=15,20,25 --param entry_multiplier=1.2,1.5,2.0

    # Mit JSON-String
    python scripts/run_sweep_strategy.py --strategy trend_following \\
        --grid '{"adx_threshold": [20, 25, 30], "ma_period": [50, 100]}'

    # Mit Daten und Limits
    python scripts/run_sweep_strategy.py --strategy mean_reversion \\
        --grid config/sweeps/mean_reversion.toml \\
        --data-file data/btc_eur_1h.csv \\
        --max-runs 20 --top-n 5

    # Verfügbare Strategien anzeigen
    python scripts/run_sweep_strategy.py --list-strategies

    # Dry-Run (nur Kombinationen anzeigen)
    python scripts/run_sweep_strategy.py --strategy ma_crossover \\
        --grid config/sweeps/ma_crossover.toml --dry-run
"""
from __future__ import annotations

import argparse
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

from src.sweeps import (
    SweepConfig,
    SweepEngine,
    SweepSummary,
    expand_parameter_grid,
)
from src.strategies.registry import (
    get_available_strategy_keys,
    get_strategy_spec,
)


# =============================================================================
# CLI ARGUMENT PARSING
# =============================================================================


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parst CLI-Argumente."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Strategy Hyperparameter Sweep Runner (Phase 20)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Mit TOML-Grid
    python scripts/run_sweep_strategy.py --strategy ma_crossover \\
        --grid config/sweeps/ma_crossover.toml

    # Mit CLI-Parametern
    python scripts/run_sweep_strategy.py --strategy my_strategy \\
        --param lookback_window=15,20,25 --param entry_multiplier=1.2,1.5,2.0

    # Mit JSON-Grid
    python scripts/run_sweep_strategy.py --strategy trend_following \\
        --grid '{"adx_threshold": [20, 25, 30]}'

    # Dry-Run
    python scripts/run_sweep_strategy.py --strategy ma_crossover \\
        --grid config/sweeps/ma_crossover.toml --dry-run
        """,
    )

    # Hauptargumente
    parser.add_argument(
        "--strategy",
        type=str,
        help="Strategie-Key aus der Registry (z.B. ma_crossover, my_strategy)",
    )

    parser.add_argument(
        "--list-strategies",
        action="store_true",
        help="Zeigt alle verfügbaren Strategien an",
    )

    # Grid-Spezifikation
    grid_group = parser.add_argument_group("Parameter-Grid")
    grid_group.add_argument(
        "--grid",
        type=str,
        help="Parameter-Grid: Pfad zu TOML/JSON-Datei oder JSON-String",
    )
    grid_group.add_argument(
        "--param",
        action="append",
        dest="params",
        metavar="KEY=VALUES",
        help="Parameter mit Werten (komma-separiert), z.B. --param fast_window=10,20,30",
    )

    # Daten-Optionen
    data_group = parser.add_argument_group("Daten")
    data_group.add_argument(
        "--data-file",
        type=str,
        help="Pfad zur CSV-Datei mit OHLCV-Daten (optional, sonst Dummy-Daten)",
    )
    data_group.add_argument(
        "--symbol",
        type=str,
        default="BTC/EUR",
        help="Symbol für den Backtest (Default: BTC/EUR)",
    )
    data_group.add_argument(
        "--timeframe",
        type=str,
        default="1h",
        help="Timeframe für OHLCV-Daten (Default: 1h)",
    )
    data_group.add_argument(
        "--bars",
        type=int,
        default=500,
        help="Anzahl Bars für Dummy-Daten (Default: 500)",
    )

    # Sweep-Optionen
    sweep_group = parser.add_argument_group("Sweep-Optionen")
    sweep_group.add_argument(
        "--sweep-name",
        type=str,
        help="Name für den Sweep (optional, für Gruppierung in Registry)",
    )
    sweep_group.add_argument(
        "--tag",
        type=str,
        help="Optionaler Tag für Registry-Logging",
    )
    sweep_group.add_argument(
        "--max-runs",
        type=int,
        help="Maximale Anzahl der Kombinationen",
    )
    sweep_group.add_argument(
        "--sort-by",
        type=str,
        default="sharpe",
        choices=["sharpe", "total_return", "max_drawdown", "profit_factor", "total_trades"],
        help="Metrik für Ergebnis-Sortierung (Default: sharpe)",
    )
    sweep_group.add_argument(
        "--sort-asc",
        action="store_true",
        help="Aufsteigend sortieren (Default: absteigend = beste zuerst)",
    )
    sweep_group.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Anzahl Top-Ergebnisse in der Ausgabe (Default: 10)",
    )

    # Output-Optionen
    output_group = parser.add_argument_group("Output")
    output_group.add_argument(
        "--export",
        type=str,
        metavar="PATH",
        help="CSV-Export der Ergebnisse",
    )
    output_group.add_argument(
        "--no-registry",
        action="store_true",
        help="Kein Registry-Logging (für Tests)",
    )
    output_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur Kombinationen anzeigen, keine Backtests ausführen",
    )
    output_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Ausführliche Ausgabe",
    )

    # Config
    parser.add_argument(
        "--config",
        type=str,
        default="config.toml",
        help="Pfad zur Basis-Config (Default: config.toml)",
    )

    return parser.parse_args(argv)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def load_parameter_grid(grid_arg: str) -> Dict[str, List[Any]]:
    """
    Lädt ein Parameter-Grid aus TOML-Datei, JSON-Datei oder JSON-String.

    Args:
        grid_arg: Pfad zu TOML/JSON-Datei oder JSON-String

    Returns:
        Parameter-Grid als Dict
    """
    grid_path = Path(grid_arg)

    # Versuche als Datei zu laden
    if grid_path.is_file():
        if grid_path.suffix == ".toml":
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
        raise ValueError(
            f"Konnte Grid nicht laden. Weder gültige Datei noch JSON-String: {e}"
        )


def parse_cli_params(params: List[str]) -> Dict[str, List[Any]]:
    """
    Parst CLI-Parameter im Format KEY=VALUE1,VALUE2,...

    Args:
        params: Liste von Strings im Format "key=val1,val2,val3"

    Returns:
        Parameter-Grid als Dict

    Example:
        >>> parse_cli_params(["fast_window=10,20,30", "slow_window=50,100"])
        {"fast_window": [10, 20, 30], "slow_window": [50, 100]}
    """
    grid = {}
    for param in params:
        if "=" not in param:
            raise ValueError(f"Ungültiges Parameter-Format: {param}. Erwartet: KEY=VALUE1,VALUE2,...")

        key, values_str = param.split("=", 1)
        key = key.strip()
        values_str = values_str.strip()

        # Werte parsen
        values = []
        for val in values_str.split(","):
            val = val.strip()
            # Versuche verschiedene Typen
            try:
                # Integer?
                values.append(int(val))
            except ValueError:
                try:
                    # Float?
                    values.append(float(val))
                except ValueError:
                    # Boolean?
                    if val.lower() in ("true", "false"):
                        values.append(val.lower() == "true")
                    else:
                        # String
                        values.append(val)

        grid[key] = values

    return grid


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
        return df

    if verbose:
        print(f"  Generiere {n_bars} Dummy-Bars")
    return generate_dummy_ohlcv(n_bars=n_bars)


def list_strategies_detailed() -> None:
    """Zeigt alle verfügbaren Strategien mit Details an."""
    print("\n" + "=" * 70)
    print("Peak_Trade Strategy Registry (Phase 20)")
    print("=" * 70)
    print("\nVerfügbare Strategien:\n")

    for key in sorted(get_available_strategy_keys()):
        spec = get_strategy_spec(key)
        print(f"  {key}")
        print(f"    Beschreibung: {spec.description}")
        print(f"    Config: {spec.config_section}")
        print()


def print_summary_table(
    summary: SweepSummary,
    top_n: int = 10,
    sort_by: str = "sharpe",
    ascending: bool = False,
) -> None:
    """Gibt eine Zusammenfassungstabelle der Top-Ergebnisse aus."""
    top_results = summary.get_top_results(n=top_n, sort_by=sort_by, ascending=ascending)

    if not top_results:
        print("\nKeine erfolgreichen Ergebnisse.")
        return

    print(f"\n{'='*80}")
    print(f"TOP {len(top_results)} ERGEBNISSE (sortiert nach {sort_by})")
    print(f"{'='*80}")

    header = f"{'#':>3} {'Return':>10} {'Sharpe':>8} {'MaxDD':>10} {'Trades':>7} | Parameter"
    print(header)
    print("-" * 80)

    for i, res in enumerate(top_results, 1):
        total_ret = res.total_return
        sharpe = res.sharpe
        max_dd = res.max_drawdown
        trades = res.total_trades

        # Parameter-String (kompakt)
        param_str = ", ".join(f"{k}={v}" for k, v in res.params.items())
        if len(param_str) > 35:
            param_str = param_str[:32] + "..."

        print(
            f"{i:>3} {total_ret:>10.2%} {sharpe:>8.2f} {max_dd:>10.2%} {trades:>7} | {param_str}"
        )


def export_results(summary: SweepSummary, export_path: str) -> None:
    """Exportiert Sweep-Ergebnisse als CSV."""
    df = summary.to_dataframe()
    df.to_csv(export_path, index=False)
    print(f"\nErgebnisse exportiert nach: {export_path}")


# =============================================================================
# MAIN
# =============================================================================


def main(argv: Optional[List[str]] = None) -> int:
    """Main-Entry-Point für Strategy Sweep (Phase 20)."""
    args = parse_args(argv)

    # List strategies mode
    if args.list_strategies:
        list_strategies_detailed()
        return 0

    # Strategie validieren
    if not args.strategy:
        print("FEHLER: --strategy ist erforderlich (oder --list-strategies)")
        return 1

    available = get_available_strategy_keys()
    if args.strategy not in available:
        print(f"FEHLER: Unbekannte Strategie '{args.strategy}'")
        print(f"Verfügbar: {', '.join(sorted(available))}")
        return 1

    print("\n" + "=" * 70)
    print("Peak_Trade: Hyperparameter Sweep (Phase 20)")
    print("=" * 70)

    # 1) Parameter-Grid laden
    print(f"\n[1/4] Parameter-Grid laden...")
    try:
        if args.grid:
            param_grid = load_parameter_grid(args.grid)
            print(f"  Grid aus: {args.grid}")
        elif args.params:
            param_grid = parse_cli_params(args.params)
            print(f"  Grid aus CLI-Parametern")
        else:
            print("FEHLER: Kein Parameter-Grid angegeben.")
            print("  Verwende --grid <DATEI/JSON> oder --param KEY=VAL1,VAL2,...")
            return 1

        combinations = expand_parameter_grid(param_grid)
        print(f"  Parameter: {list(param_grid.keys())}")
        print(f"  Kombinationen: {len(combinations)}")

        if args.max_runs and len(combinations) > args.max_runs:
            print(f"  Limitiert auf: {args.max_runs} Runs")

    except Exception as e:
        print(f"FEHLER beim Laden des Grids: {e}")
        return 1

    # Dry-Run: nur Kombinationen anzeigen
    if args.dry_run:
        print(f"\n[DRY-RUN] Folgende {len(combinations)} Kombinationen würden getestet:")
        for i, combo in enumerate(combinations[:50], 1):
            print(f"  {i:>3}. {combo}")
        if len(combinations) > 50:
            print(f"  ... und {len(combinations) - 50} weitere")
        print("\n(Kein Backtest ausgeführt)")
        return 0

    # 2) Config validieren
    print(f"\n[2/4] Config validieren...")
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"FEHLER: Config nicht gefunden: {config_path}")
        return 1
    print(f"  Config: {config_path}")

    # 3) Daten laden
    print(f"\n[3/4] OHLCV-Daten laden...")
    try:
        data = load_ohlcv_data(
            data_file=args.data_file,
            n_bars=args.bars,
            verbose=args.verbose,
        )
        print(f"  {len(data)} Bars geladen")
        print(f"  Zeitraum: {data.index[0]} bis {data.index[-1]}")
    except Exception as e:
        print(f"FEHLER: {e}")
        return 1

    # 4) Sweep ausführen
    print(f"\n[4/4] Sweep ausführen...")
    print(f"  Strategie: {args.strategy}")
    print(f"  Symbol: {args.symbol}")
    print(f"  Timeframe: {args.timeframe}")

    # Progress-Callback
    def progress_callback(current: int, total: int, params: Dict) -> None:
        if args.verbose:
            print(f"  [{current}/{total}] {params}")
        else:
            pct = current / total * 100
            print(f"\r  Fortschritt: {current}/{total} ({pct:.0f}%)", end="", flush=True)

    try:
        config = SweepConfig(
            strategy_key=args.strategy,
            param_grid=param_grid,
            symbol=args.symbol,
            timeframe=args.timeframe,
            sweep_name=args.sweep_name,
            tag=args.tag,
            max_runs=args.max_runs,
            sort_by=args.sort_by,
            sort_ascending=args.sort_asc,
            config_path=str(config_path),
        )

        engine = SweepEngine(
            verbose=args.verbose,
            progress_callback=None if args.verbose else progress_callback,
        )

        summary = engine.run_sweep(
            config=config,
            data=data,
            skip_registry=args.no_registry,
        )

    except Exception as e:
        print(f"\nFEHLER beim Sweep: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    print()  # Newline nach Fortschrittsanzeige

    # Zusammenfassung
    print(f"\n{'='*70}")
    print("SWEEP ABGESCHLOSSEN")
    print(f"{'='*70}")
    print(f"  Strategie:     {summary.strategy_key}")
    print(f"  Symbol:        {summary.symbol}")
    print(f"  Timeframe:     {summary.timeframe}")
    print(f"  Sweep-ID:      {summary.sweep_id}")
    print(f"  Sweep-Name:    {summary.sweep_name}")
    print(f"  Erfolgreich:   {summary.successful_runs}/{summary.runs_executed}")
    print(f"  Dauer:         {summary.duration_seconds:.1f}s")

    if summary.failed_runs > 0:
        print(f"  Fehlgeschlagen: {summary.failed_runs}")

    # Top-Ergebnisse anzeigen
    print_summary_table(
        summary,
        top_n=args.top_n,
        sort_by=args.sort_by,
        ascending=args.sort_asc,
    )

    # Bestes Ergebnis
    if summary.best_result:
        print(f"\n{'='*70}")
        print("BESTES ERGEBNIS")
        print(f"{'='*70}")
        best = summary.best_result
        print(f"  Parameter:     {best.params}")
        print(f"  Total Return:  {best.total_return:.2%}")
        print(f"  Sharpe Ratio:  {best.sharpe:.2f}")
        print(f"  Max Drawdown:  {best.max_drawdown:.2%}")
        print(f"  Trades:        {best.total_trades}")

    # Registry-Info
    if not args.no_registry:
        print(f"\nErgebnisse in Registry gespeichert:")
        print(f"  sweep_name='{summary.sweep_name}'")
        if args.tag:
            print(f"  tag='{args.tag}'")

        print("\nNächste Schritte:")
        print(f"  python scripts/list_experiments.py --run-type sweep")
        print(f"  python scripts/analyze_experiments.py --mode top-runs --run-type sweep --metric {args.sort_by}")

    # Export
    if args.export:
        export_results(summary, args.export)

    return 0


if __name__ == "__main__":
    sys.exit(main())
