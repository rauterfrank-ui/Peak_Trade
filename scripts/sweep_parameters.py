#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Peak_Trade: Strategy Hyperparameter Sweeps
===========================================
Testet Parameter-Kombinationen automatisiert und erstellt Ranking-Reports.

Usage:
    python scripts/sweep_parameters.py
    python scripts/sweep_parameters.py --strategy ma_crossover --symbol BTC/EUR
    python scripts/sweep_parameters.py --top-k-reports 3 --max-runs 10
"""

from __future__ import annotations

import sys
import argparse
from itertools import product
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Projekt-Root zum Python-Path hinzuf�gen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.core.peak_config import load_config, PeakConfig
from src.core.position_sizing import build_position_sizer_from_config
from src.core.risk import build_risk_manager_from_config
from src.core.experiments import log_experiment_from_result
from src.backtest.engine import BacktestEngine
from src.backtest.result import BacktestResult
from src.strategies.registry import create_strategy_from_config


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Hyperparameter-Sweeps f�r Strategien.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard-Sweep aus config.toml
  python scripts/sweep_parameters.py

  # Sweep mit expliziter Strategie und Symbol
  python scripts/sweep_parameters.py --strategy ma_crossover --symbol BTC/EUR

  # Nur Top-2 Konfigurationen mit vollst�ndigen Reports
  python scripts/sweep_parameters.py --top-k-reports 2

  # Anzahl getesteter Kombinationen limitieren
  python scripts/sweep_parameters.py --max-runs 10
        """,
    )
    parser.add_argument(
        "-s",
        "--strategy",
        help="Strategie-Key (�berschreibt [sweep].strategy_key)",
    )
    parser.add_argument(
        "--symbol",
        help="Symbol (�berschreibt [sweep].symbol)",
    )
    parser.add_argument(
        "--run-name",
        help="Optionaler Name f�r diesen Sweep-Run (f�r Reports)",
    )
    parser.add_argument(
        "--sort-by",
        help=(
            "Stats-Feld zum Sortieren "
            "(z.B. total_return, cagr, max_drawdown, sharpe). "
            "Standard: [sweep].sort_by"
        ),
    )
    parser.add_argument(
        "--ascending",
        action="store_true",
        help="Aufsteigend sortieren (Standard: absteigend)",
    )
    parser.add_argument(
        "--top-k-reports",
        type=int,
        default=3,
        help="F�r die Top-K-Konfigurationen vollst�ndige Reports schreiben (0 = keine)",
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        help="Optional: maximale Anzahl getesteter Kombinationen",
    )
    parser.add_argument(
        "--bars",
        type=int,
        default=200,
        help="Anzahl Bars pro Backtest (default: 200)",
    )
    return parser.parse_args(argv)


def load_data_for_symbol(symbol: str, n_bars: int = 200) -> pd.DataFrame:
    """
    L�dt Daten f�r ein bestimmtes Symbol.

    Aktuell: Dummy-Daten mit symbol-spezifischem Seed.
    TODO: Sp�ter mit echten Kraken-Daten ersetzen.

    Args:
        symbol: Trading-Pair (z.B. "BTC/EUR")
        n_bars: Anzahl Bars

    Returns:
        DataFrame mit OHLCV-Daten
    """
    # Symbol-spezifischer Seed f�r reproduzierbare aber unterschiedliche Daten
    seed = hash(symbol) % (2**32)
    np.random.seed(seed)

    # Start-Zeitpunkt
    start = datetime.now() - timedelta(hours=n_bars)
    dates = pd.date_range(start, periods=n_bars, freq="1h")

    # Preis-Simulation mit symbol-spezifischen Eigenschaften
    if "BTC" in symbol:
        base_price = 50000
        volatility = 0.003
    elif "ETH" in symbol:
        base_price = 3000
        volatility = 0.004
    elif "LTC" in symbol:
        base_price = 100
        volatility = 0.005
    else:
        base_price = 1000
        volatility = 0.003

    # Langfristiger Trend
    trend = np.linspace(0, base_price * 0.06, n_bars)

    # Oszillation
    cycle = np.sin(np.linspace(0, 4 * np.pi, n_bars)) * base_price * 0.04

    # Random Walk Noise
    noise = np.random.randn(n_bars).cumsum() * base_price * volatility

    close_prices = base_price + trend + cycle + noise

    # OHLC generieren
    df = pd.DataFrame(
        {
            "open": close_prices * (1 + np.random.randn(n_bars) * volatility),
            "high": close_prices * (1 + abs(np.random.randn(n_bars)) * volatility * 1.5),
            "low": close_prices * (1 - abs(np.random.randn(n_bars)) * volatility * 1.5),
            "close": close_prices,
            "volume": np.random.randint(10, 100, n_bars),
        },
        index=dates,
    )

    return df


def build_param_grid(
    cfg: PeakConfig,
    strategy_key: str,
) -> Tuple[List[str], List[Tuple[Any, ...]]]:
    """
    Liest [sweep.parameters] aus der Config und baut Parameter-Grid.

    Returns:
        (param_names, combos) - Namen und alle Wert-Kombinationen

    Example:
        [sweep.parameters]
        fast_window = [10, 20]
        slow_window = [50, 100]

        -> param_names = ["fast_window", "slow_window"]
           combos = [(10, 50), (10, 100), (20, 50), (20, 100)]
    """
    params_section = cfg.get("sweep.parameters", {}) or {}
    if not isinstance(params_section, dict):
        raise ValueError("[sweep.parameters] muss ein Table/Dictionary sein.")

    param_names: List[str] = []
    param_values: List[List[Any]] = []

    for name, values in params_section.items():
        # Single-Value � Liste
        if isinstance(values, (list, tuple)):
            vlist = list(values)
        else:
            vlist = [values]
        if not vlist:
            continue
        param_names.append(str(name))
        param_values.append(vlist)

    if not param_names:
        raise ValueError("Keine Parameter in [sweep.parameters] definiert.")

    combos = list(product(*param_values))
    return param_names, combos


def run_backtest_for_params(
    base_cfg: PeakConfig,
    strategy_key: str,
    symbol: str,
    param_names: List[str],
    param_values: Tuple[Any, ...],
    n_bars: int = 200,
) -> BacktestResult:
    """
    F�hrt Backtest mit �berschriebenen Strategy-Parametern aus.

    Args:
        base_cfg: Basis-Config
        strategy_key: Strategie-Name
        symbol: Trading-Pair
        param_names: Parameter-Namen
        param_values: Parameter-Werte
        n_bars: Anzahl Bars

    Returns:
        BacktestResult mit Metadaten
    """
    # Dotted-Keys f�r Strategy-Section bauen
    overrides: Dict[str, Any] = {}
    for name, value in zip(param_names, param_values):
        path = f"strategy.{strategy_key}.{name}"
        overrides[path] = value

    cfg = base_cfg.with_overrides(overrides)

    # Daten laden
    data = load_data_for_symbol(symbol, n_bars=n_bars)

    # Strategie erstellen
    strategy = create_strategy_from_config(strategy_key, cfg)

    # Position Sizer & Risk Manager
    position_sizer = build_position_sizer_from_config(cfg)
    risk_manager = build_risk_manager_from_config(cfg, section="risk_management")

    # Wrapper f�r Legacy-API
    def strategy_signal_fn(df, params):
        sigs = strategy.generate_signals(df)
        return sigs.replace(-1, 0)  # Long-Only

    # Stop-Loss aus Config
    stop_pct = cfg.get(f"strategy.{strategy_key}.stop_pct", 0.02)
    strategy_params = {"stop_pct": stop_pct}

    # Backtest durchf�hren
    engine = BacktestEngine(core_position_sizer=position_sizer, risk_manager=risk_manager)
    result = engine.run_realistic(
        df=data, strategy_signal_fn=strategy_signal_fn, strategy_params=strategy_params
    )

    # Metadaten anreichern
    result.metadata.setdefault("symbol", symbol)
    result.metadata.setdefault("strategy_key", strategy_key)
    result.metadata.setdefault("params", {})
    result.metadata["params"].update(
        {name: value for name, value in zip(param_names, param_values)}
    )

    return result


def print_sweep_table(df: pd.DataFrame, param_names: List[str], n_top: int = 10):
    """Druckt formatierte Sweep-Ergebnis-Tabelle."""
    print("\n" + "=" * 100)
    print(f"PARAMETER SWEEP RESULTS (Top {min(n_top, len(df))})")
    print("=" * 100)

    if len(df) == 0:
        print("Keine Ergebnisse verf�gbar.")
        return

    # Spalten f�r Tabelle
    cols_to_show = (
        ["symbol"]
        + param_names
        + ["total_return", "sharpe", "max_drawdown", "total_trades", "profit_factor", "win_rate"]
    )

    # Nur vorhandene Spalten anzeigen
    cols_to_show = [c for c in cols_to_show if c in df.columns]

    df_display = df[cols_to_show].head(n_top)

    print(df_display.to_string(index=False))
    print("=" * 100 + "\n")


def main(argv: List[str] | None = None) -> None:
    """Main-Funktion."""
    args = parse_args(argv)

    print("\n=, Peak_Trade Parameter Sweep")
    print("=" * 70)

    # Config laden
    print("\n�  Lade Konfiguration...")
    try:
        base_cfg = load_config("config.toml")
        print(" config.toml erfolgreich geladen")
    except FileNotFoundError as e:
        print(f"\nL FEHLER: {e}")
        print("\nBitte erstelle eine config.toml im Projekt-Root.")
        return

    # Strategie bestimmen
    sweep_strategy_key = base_cfg.get("sweep.strategy_key", None)
    default_strategy_key = base_cfg.get("general.active_strategy", "ma_crossover")
    strategy_key = args.strategy or sweep_strategy_key or default_strategy_key
    strategy_key = str(strategy_key)

    # Symbol bestimmen
    sweep_symbol = base_cfg.get("sweep.symbol", None)
    symbol = args.symbol or sweep_symbol
    if not symbol:
        raise ValueError("Kein Symbol gesetzt  bitte [sweep].symbol oder --symbol verwenden.")
    symbol = str(symbol)

    # Sortierung
    sort_by_cfg = base_cfg.get("sweep.sort_by", "total_return")
    sort_by = args.sort_by or sort_by_cfg
    sort_desc_cfg = bool(base_cfg.get("sweep.sort_desc", True))
    ascending = args.ascending if args.ascending else (not sort_desc_cfg)

    sweep_name = str(base_cfg.get("sweep.name", "sweep"))
    run_name_base = args.run_name or sweep_name

    print(f"\n=� Sweep-Konfiguration:")
    print(f"  - Strategie: {strategy_key}")
    print(f"  - Symbol:    {symbol}")
    print(f"  - Sweep-Name: {run_name_base}")
    print(f"  - Sortiere nach: {sort_by} ({'ASC' if ascending else 'DESC'})")
    print(f"  - Bars pro Run: {args.bars}")

    # Parameter-Gitter bauen
    print(f"\n=( Baue Parameter-Grid...")
    try:
        param_names, combos = build_param_grid(base_cfg, strategy_key=strategy_key)
    except Exception as e:
        print(f"\nL FEHLER beim Bauen des Parameter-Grids: {e}")
        return

    total_combos = len(combos)
    print(f" Parameter: {param_names}")
    print(f" Kombinationen: {total_combos}")

    if args.max_runs is not None and args.max_runs < total_combos:
        combos = combos[: args.max_runs]
        print(f"�  max_runs={args.max_runs} gesetzt � teste nur erste {len(combos)} Kombinationen")

    # Sweeps durchf�hren
    print(f"\n=� Starte Sweep mit {len(combos)} Kombinationen...")
    print("-" * 70)

    rows: List[Dict[str, Any]] = []
    results: List[BacktestResult] = []

    for idx, combo in enumerate(combos, start=1):
        print(f"\n=== Run {idx}/{len(combos)}  {strategy_key} @ {symbol} ===")
        print("Parameter:")
        for name, value in zip(param_names, combo):
            print(f"  {name} = {value}")

        try:
            result = run_backtest_for_params(
                base_cfg=base_cfg,
                strategy_key=strategy_key,
                symbol=symbol,
                param_names=param_names,
                param_values=combo,
                n_bars=args.bars,
            )
        except Exception as e:
            print(f"L FEHLER: {e}")
            continue

        # Kurze Zusammenfassung
        print(
            f"   Return: {result.stats.get('total_return', 0.0):>7.2%} | "
            f"Sharpe: {result.stats.get('sharpe', 0.0):>6.2f} | "
            f"Trades: {result.stats.get('total_trades', 0):>4}"
        )

        # Experiment-Record für diese Parameter-Kombi loggen
        param_dict = {name: value for name, value in zip(param_names, combo)}
        param_suffix = "_".join(f"{k}{v}" for k, v in param_dict.items())
        if len(param_suffix) > 60:
            param_suffix = param_suffix[:60]
        run_name_full = f"{strategy_key}_{symbol.replace('/', '_')}_{run_name_base}_{param_suffix}"

        log_experiment_from_result(
            result=result,
            run_type="sweep",
            run_name=run_name_full,
            strategy_key=strategy_key,
            symbol=symbol,
            sweep_name=run_name_base,
            report_dir=Path("reports") / "sweeps",
            report_prefix=run_name_full,
            extra_metadata={
                "runner": "sweep_parameters.py",
                "sweep_name": sweep_name,
                "params": param_dict,
            },
        )

        stats = dict(result.stats)
        row: Dict[str, Any] = {
            "symbol": symbol,
            "strategy_key": strategy_key,
        }

        # Parameter-Werte als eigene Spalten
        for name, value in zip(param_names, combo):
            row[name] = value

        # Stats hinzuf�gen
        row.update(stats)

        # Optional: Regime-Verteilung aus metadata
        regime_dist = result.metadata.get("regime_distribution", {})
        for regime_key, frac in regime_dist.items():
            col_name = f"regime_{regime_key.lower()}"
            row[col_name] = frac

        rows.append(row)
        results.append(result)

    if not rows:
        print("\nL Keine erfolgreichen Backtests. Sweep abgebrochen.")
        return

    # DataFrame erstellen
    df = pd.DataFrame(rows)

    # Sortieren
    if sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=ascending)
    else:
        print(f"\n�  Sortierfeld {sort_by!r} nicht in Spalten  keine Sortierung")

    df = df.reset_index(drop=True)

    # Tabelle drucken
    print_sweep_table(df, param_names, n_top=10)

    # Ordner f�r Sweeps
    sweeps_dir = Path("reports") / "sweeps"
    sweeps_dir.mkdir(parents=True, exist_ok=True)

    # CSV speichern
    csv_filename = f"sweep_{strategy_key}_{run_name_base}.csv"
    csv_path = sweeps_dir / csv_filename
    df.to_csv(csv_path, index=False)
    print(f"=� Sweep-Ergebnis gespeichert: {csv_path}")

    # Optional: vollwertige Reports f�r Top-K
    top_k = max(args.top_k_reports, 0)
    if top_k > 0:
        print(f"\n=� Erstelle vollst�ndige Reports f�r Top {top_k} Konfigurationen...")
        from src.backtest.reporting import save_full_report

        top_df = df.head(top_k).copy()

        for i, row in top_df.iterrows():
            params_combo = tuple(row[name] for name in param_names)

            # Passenden BacktestResult finden
            match = None
            for res in results:
                res_params = res.metadata.get("params", {})
                if all(
                    res_params.get(name) == value for name, value in zip(param_names, params_combo)
                ):
                    match = res
                    break

            if match is None:
                continue

            # Run-Name mit Parametern
            param_tag = "_".join(f"{name}{val}" for name, val in zip(param_names, params_combo))
            if len(param_tag) > 60:
                param_tag = param_tag[:60]
            full_run_name = f"{strategy_key}_{run_name_base}_{param_tag}"

            try:
                save_full_report(
                    result=match,
                    output_dir=str(sweeps_dir),
                    run_name=full_run_name,
                    save_plots_flag=True,
                    save_html_flag=True,
                )
                print(f"   Report: {full_run_name}")
            except Exception as e:
                print(f"  �  Warnung: Konnte Report nicht erstellen: {e}")

    print(f"\n Parameter Sweep abgeschlossen!")
    print(f"   Beste Konfiguration:")
    best = df.iloc[0]
    for name in param_names:
        print(f"     {name} = {best[name]}")
    print(
        f"   Performance: {best['total_return']:.2%} Return, Sharpe {best.get('sharpe', 0.0):.2f}"
    )
    print()


if __name__ == "__main__":
    main()
