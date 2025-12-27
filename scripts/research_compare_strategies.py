#!/usr/bin/env python3
"""
Peak_Trade Research Compare Strategies
=======================================
Phase 18: Strategy Research Playground

Vergleicht mehrere Strategien auf demselben Dataset.
Führt parallele Backtests durch und gibt eine Vergleichstabelle aus.

Features:
- Vergleicht mehrere Strategien auf denselben Daten
- Tabellen-Output mit wichtigsten Kennzahlen
- Sortierung nach frei wählbarer Metrik
- Registry-Logging aller Runs mit gemeinsamer Group-ID
- Optional: Export als CSV

Usage:
    # Alle verfügbaren Strategien vergleichen
    python scripts/research_compare_strategies.py --all

    # Nur bestimmte Strategien vergleichen
    python scripts/research_compare_strategies.py --strategies ma_crossover,trend_following,mean_reversion

    # Mit CSV-Daten
    python scripts/research_compare_strategies.py --all --data-file data/btc_eur_1h.csv

    # Nach Sharpe sortieren
    python scripts/research_compare_strategies.py --all --sort-by sharpe

    # Ergebnis als CSV exportieren
    python scripts/research_compare_strategies.py --all --export results/comparison.csv
"""

from __future__ import annotations

import argparse
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

# Projekt-Root zum Path hinzufügen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.peak_config import load_config
from src.core.position_sizing import build_position_sizer_from_config
from src.core.risk import build_risk_manager_from_config
from src.core.experiments import (
    log_experiment_from_result,
    RUN_TYPE_BACKTEST,
)
from src.backtest.engine import BacktestEngine
from src.backtest.stats import validate_for_live_trading
from src.data import DataNormalizer, CsvLoader, KrakenCsvLoader
from src.strategies.registry import (
    get_available_strategy_keys,
    get_strategy_spec,
    create_strategy_from_config,
    list_strategies,
)


def parse_args() -> argparse.Namespace:
    """CLI-Argumente parsen."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Research Strategy Comparison (Phase 18)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Alle Strategien vergleichen
  python scripts/research_compare_strategies.py --all

  # Nur bestimmte Strategien
  python scripts/research_compare_strategies.py --strategies ma_crossover,trend_following

  # Mit CSV-Daten und Sharpe-Sortierung
  python scripts/research_compare_strategies.py --all --data-file data/btc_eur_1h.csv --sort-by sharpe

  # Ergebnis exportieren
  python scripts/research_compare_strategies.py --all --export results/comparison.csv
        """,
    )

    parser.add_argument(
        "--strategies",
        type=str,
        default=None,
        help="Komma-getrennte Liste von Strategie-Keys (z.B. 'ma_crossover,trend_following')",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Alle verfügbaren Strategien vergleichen",
    )
    parser.add_argument(
        "--data-file",
        type=str,
        default=None,
        help="Pfad zur CSV-Datei mit OHLCV-Daten. Wenn nicht angegeben: Dummy-Daten",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="BTC/EUR",
        help="Trading-Symbol (default: BTC/EUR)",
    )
    parser.add_argument(
        "--timeframe",
        type=str,
        default="1h",
        help="Timeframe (default: 1h)",
    )
    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Startdatum (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="Enddatum (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--bars",
        type=int,
        default=500,
        help="Anzahl Bars für Dummy-Daten (default: 500)",
    )
    parser.add_argument(
        "--sort-by",
        type=str,
        default="total_return",
        choices=[
            "total_return",
            "sharpe",
            "max_drawdown",
            "win_rate",
            "profit_factor",
            "total_trades",
        ],
        help="Sortiermetrik (default: total_return)",
    )
    parser.add_argument(
        "--sort-asc",
        action="store_true",
        help="Aufsteigend sortieren (default: absteigend)",
    )
    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Tag für Registry-Logging",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.toml",
        help="Pfad zur TOML-Config-Datei",
    )
    parser.add_argument(
        "--export",
        type=str,
        default=None,
        help="Pfad für CSV-Export der Ergebnisse",
    )
    parser.add_argument(
        "--no-registry",
        action="store_true",
        help="Keine Registry-Logs schreiben",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Ausführliche Ausgabe",
    )

    return parser.parse_args()


def generate_dummy_ohlcv(
    n_bars: int = 500,
    base_price: float = 50000.0,
    volatility: float = 0.015,
) -> pd.DataFrame:
    """
    Generiert synthetische OHLCV-Daten für Research/Tests.

    Die Daten enthalten sowohl Trends als auch Seitwärtsphasen.
    """
    np.random.seed(42)

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
    start_date: Optional[str],
    end_date: Optional[str],
    n_bars: int,
    verbose: bool = False,
) -> pd.DataFrame:
    """Lädt OHLCV-Daten aus CSV oder generiert Dummy-Daten."""
    if data_file:
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

    if start_date:
        start_dt = pd.to_datetime(start_date).tz_localize("UTC")
        df = df[df.index >= start_dt]

    if end_date:
        end_dt = pd.to_datetime(end_date).tz_localize("UTC")
        df = df[df.index <= end_dt]

    if len(df) == 0:
        raise ValueError("Keine Daten nach Filterung übrig!")

    return df


def run_single_backtest(
    strategy_key: str,
    df: pd.DataFrame,
    cfg,
    symbol: str,
    verbose: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Führt einen einzelnen Backtest für eine Strategie aus.

    Returns:
        Dict mit Ergebnis oder None bei Fehler
    """
    try:
        # Strategie laden
        spec = get_strategy_spec(strategy_key)
        strategy = create_strategy_from_config(strategy_key, cfg)

        # Position-Sizer und Risk-Manager
        position_sizer = build_position_sizer_from_config(cfg)
        risk_manager = build_risk_manager_from_config(cfg, section="risk_management")

        # Wrapper für Engine
        def strategy_signal_fn(data, params):
            return strategy.generate_signals(data)

        stop_pct = cfg.get(f"strategy.{strategy_key}.stop_pct", 0.02)
        strategy_params = {"stop_pct": stop_pct}

        # Engine und Backtest
        engine = BacktestEngine(
            core_position_sizer=position_sizer,
            risk_manager=risk_manager,
        )

        result = engine.run_realistic(
            df=df,
            strategy_signal_fn=strategy_signal_fn,
            strategy_params=strategy_params,
            symbol=symbol,
        )
        result.strategy_name = strategy_key

        # Ergebnis zusammenstellen
        stats = result.stats
        passed, _ = validate_for_live_trading(stats)

        return {
            "strategy": strategy_key,
            "description": spec.description,
            "total_return": stats.get("total_return", 0),
            "max_drawdown": stats.get("max_drawdown", 0),
            "sharpe": stats.get("sharpe", 0),
            "win_rate": stats.get("win_rate", 0),
            "profit_factor": stats.get("profit_factor", 0),
            "total_trades": stats.get("total_trades", 0),
            "cagr": stats.get("cagr", 0),
            "live_ready": passed,
            "result": result,  # Für Registry-Logging
        }

    except Exception as e:
        if verbose:
            print(f"  FEHLER bei {strategy_key}: {e}")
        return {
            "strategy": strategy_key,
            "description": "ERROR",
            "total_return": 0,
            "max_drawdown": 0,
            "sharpe": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "total_trades": 0,
            "cagr": 0,
            "live_ready": False,
            "error": str(e),
            "result": None,
        }


def print_comparison_table(
    results: List[Dict[str, Any]],
    sort_by: str,
    sort_asc: bool,
) -> pd.DataFrame:
    """
    Gibt eine Vergleichstabelle aus und gibt sie als DataFrame zurück.
    """
    # DataFrame erstellen
    data = []
    for r in results:
        data.append(
            {
                "Strategy": r["strategy"],
                "Return": r["total_return"],
                "MaxDD": r["max_drawdown"],
                "Sharpe": r["sharpe"],
                "WinRate": r["win_rate"],
                "PF": r["profit_factor"],
                "Trades": r["total_trades"],
                "Live": "OK" if r["live_ready"] else "NO",
            }
        )

    df = pd.DataFrame(data)

    # Sortieren
    sort_col_map = {
        "total_return": "Return",
        "max_drawdown": "MaxDD",
        "sharpe": "Sharpe",
        "win_rate": "WinRate",
        "profit_factor": "PF",
        "total_trades": "Trades",
    }
    sort_col = sort_col_map.get(sort_by, "Return")
    df = df.sort_values(sort_col, ascending=sort_asc)

    # Formatierung
    print("\n" + "=" * 90)
    print("  STRATEGY COMPARISON")
    print("=" * 90)

    # Header
    print(
        f"\n{'Strategy':<20} {'Return':>10} {'MaxDD':>10} {'Sharpe':>8} {'WinRate':>8} {'PF':>8} {'Trades':>7} {'Live':>6}"
    )
    print("-" * 90)

    # Zeilen
    for _, row in df.iterrows():
        return_str = f"{row['Return']:.2%}"
        maxdd_str = f"{row['MaxDD']:.2%}"
        sharpe_str = f"{row['Sharpe']:.2f}"
        winrate_str = f"{row['WinRate']:.1%}"
        pf_str = f"{row['PF']:.2f}"
        trades_str = str(int(row["Trades"]))
        live_str = row["Live"]

        print(
            f"{row['Strategy']:<20} {return_str:>10} {maxdd_str:>10} {sharpe_str:>8} {winrate_str:>8} {pf_str:>8} {trades_str:>7} {live_str:>6}"
        )

    print("-" * 90)

    # Best/Worst
    best_idx = df["Return"].idxmax()
    worst_idx = df["Return"].idxmin()
    print(f"\nBester (Return):   {df.loc[best_idx, 'Strategy']} ({df.loc[best_idx, 'Return']:.2%})")
    print(f"Schlechtester:     {df.loc[worst_idx, 'Strategy']} ({df.loc[worst_idx, 'Return']:.2%})")

    best_sharpe_idx = df["Sharpe"].idxmax()
    print(
        f"Bester (Sharpe):   {df.loc[best_sharpe_idx, 'Strategy']} ({df.loc[best_sharpe_idx, 'Sharpe']:.2f})"
    )

    print("\n" + "=" * 90 + "\n")

    return df


def main() -> int:
    """Hauptfunktion."""
    args = parse_args()

    # Strategieliste bestimmen
    if args.all:
        strategy_keys = get_available_strategy_keys()
    elif args.strategies:
        strategy_keys = [s.strip() for s in args.strategies.split(",")]
    else:
        print("FEHLER: Bitte --all oder --strategies angeben.")
        print("        Nutze --help für Details.")
        return 1

    if len(strategy_keys) < 2:
        print("WARNUNG: Mindestens 2 Strategien für Vergleich empfohlen.")

    print("\n" + "=" * 70)
    print("  Peak_Trade Strategy Comparison (Phase 18)")
    print("=" * 70)

    # Config laden
    print("\n[1/4] Config laden...")
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"\nFEHLER: Config nicht gefunden: {config_path}")
        return 1

    try:
        cfg = load_config(config_path)
    except Exception as e:
        print(f"\nFEHLER beim Laden der Config: {e}")
        return 1

    # Daten laden
    print("\n[2/4] Daten laden...")
    try:
        df = load_ohlcv_data(
            data_file=args.data_file,
            start_date=args.start,
            end_date=args.end,
            n_bars=args.bars,
            verbose=args.verbose,
        )
        print(f"  {len(df)} Bars geladen")
        print(f"  Zeitraum: {df.index[0]} - {df.index[-1]}")
    except Exception as e:
        print(f"\nFEHLER beim Laden der Daten: {e}")
        return 1

    # Backtests ausführen
    print(f"\n[3/4] Backtests für {len(strategy_keys)} Strategien...")
    print(f"  Strategien: {', '.join(strategy_keys)}")

    results = []
    group_id = str(uuid.uuid4())[:8]  # Group-ID für zusammengehörige Runs

    for i, strategy_key in enumerate(strategy_keys, 1):
        print(f"  [{i}/{len(strategy_keys)}] {strategy_key}...", end=" ", flush=True)

        result = run_single_backtest(
            strategy_key=strategy_key,
            df=df,
            cfg=cfg,
            symbol=args.symbol,
            verbose=args.verbose,
        )

        if result.get("error"):
            print(f"FEHLER: {result['error']}")
        else:
            print(f"OK (Return: {result['total_return']:.2%})")

        results.append(result)

    # Ergebnis-Tabelle ausgeben
    print("\n[4/4] Ergebnis ausgeben...")
    comparison_df = print_comparison_table(
        results=results,
        sort_by=args.sort_by,
        sort_asc=args.sort_asc,
    )

    # Registry-Logging
    if not args.no_registry:
        print("Registry-Logging...")
        data_source = "csv" if args.data_file else "dummy"
        start_date_str = df.index[0].strftime("%Y-%m-%d")
        end_date_str = df.index[-1].strftime("%Y-%m-%d")

        for r in results:
            if r.get("result") is not None:
                log_experiment_from_result(
                    result=r["result"],
                    run_type=RUN_TYPE_BACKTEST,
                    run_name=f"compare_{r['strategy']}_{group_id}",
                    strategy_key=r["strategy"],
                    symbol=args.symbol,
                    extra_metadata={
                        "runner": "research_compare_strategies.py",
                        "tag": args.tag,
                        "group_id": group_id,
                        "data_source": data_source,
                        "timeframe": args.timeframe,
                        "start_date": start_date_str,
                        "end_date": end_date_str,
                        "comparison_strategies": strategy_keys,
                        "phase": "18_research_playground",
                    },
                )

        print(f"  {len(results)} Runs geloggt (Group-ID: {group_id})")

    # Export
    if args.export:
        export_path = Path(args.export)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        comparison_df.to_csv(export_path, index=False)
        print(f"\nErgebnis exportiert: {args.export}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
