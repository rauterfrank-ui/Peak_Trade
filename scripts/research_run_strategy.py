#!/usr/bin/env python3
"""
Peak_Trade Research Run Strategy
=================================
Phase 18: Strategy Research Playground

Ein standardisierter Research-Runner für einzelne Strategien.
Führt einen Backtest für eine Strategie auf einem Dataset aus und
loggt das Ergebnis in der Experiment-Registry.

Features:
- Lädt Strategie aus der OOP-Registry
- Unterstützt CSV-Daten oder generierte Dummy-Daten
- Nutzt Position-Sizing und Risk-Management aus Config
- Loggt Runs in der Experiment-Registry
- Gibt CLI-Summary mit wichtigsten Kennzahlen aus

Usage:
    # Mit Standard-Strategie und Dummy-Daten
    python scripts/research_run_strategy.py

    # Mit spezifischer Strategie
    python scripts/research_run_strategy.py --strategy trend_following

    # Mit CSV-Daten
    python scripts/research_run_strategy.py --strategy mean_reversion --data-file data/btc_eur_1h.csv

    # Mit Datumsfilter
    python scripts/research_run_strategy.py --strategy ma_crossover --start 2023-01-01 --end 2023-12-31

    # Verfügbare Strategien anzeigen
    python scripts/research_run_strategy.py --list-strategies

    # Mit Custom-Parametern (überschreiben Config)
    python scripts/research_run_strategy.py --strategy ma_crossover --param fast_window=10 --param slow_window=30
"""
from __future__ import annotations

import argparse
import sys
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
        description="Peak_Trade Research Strategy Runner (Phase 18)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Standard-Backtest mit ma_crossover
  python scripts/research_run_strategy.py

  # Mit spezifischer Strategie
  python scripts/research_run_strategy.py --strategy trend_following

  # Mit CSV-Daten und Datumsfilter
  python scripts/research_run_strategy.py --strategy mean_reversion \\
      --data-file data/btc_eur_1h.csv --start 2023-01-01 --end 2023-12-31

  # Mit Custom-Parametern
  python scripts/research_run_strategy.py --strategy ma_crossover \\
      --param fast_window=10 --param slow_window=30

  # Verfügbare Strategien anzeigen
  python scripts/research_run_strategy.py --list-strategies
        """,
    )

    parser.add_argument(
        "--strategy",
        type=str,
        default=None,
        help="Strategie-Key (z.B. ma_crossover, trend_following). Default: aus Config",
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
        help="Startdatum (YYYY-MM-DD), filtert Daten",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="Enddatum (YYYY-MM-DD), filtert Daten",
    )
    parser.add_argument(
        "--bars",
        type=int,
        default=500,
        help="Anzahl Bars für Dummy-Daten (default: 500)",
    )
    parser.add_argument(
        "--param",
        type=str,
        action="append",
        default=[],
        help="Custom Parameter (Format: key=value). Kann mehrfach verwendet werden.",
    )
    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Optionaler Tag für Registry-Logging (z.B. 'research', 'experiment')",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.toml",
        help="Pfad zur TOML-Config-Datei (default: config.toml)",
    )
    parser.add_argument(
        "--list-strategies",
        action="store_true",
        help="Zeigt alle verfügbaren Strategien und beendet",
    )
    parser.add_argument(
        "--no-registry",
        action="store_true",
        help="Wenn gesetzt, wird Run NICHT in Registry geloggt",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Ausführliche Ausgabe",
    )

    return parser.parse_args()


def parse_custom_params(param_list: List[str]) -> Dict[str, Any]:
    """
    Parst Custom-Parameter aus CLI.

    Args:
        param_list: Liste von Strings im Format 'key=value'

    Returns:
        Dict mit geparsten Parametern
    """
    params = {}
    for param in param_list:
        if "=" not in param:
            print(f"WARNUNG: Ungültiges Parameterformat: {param} (erwartet key=value)")
            continue

        key, value = param.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Typ-Konvertierung versuchen
        try:
            # Int?
            params[key] = int(value)
        except ValueError:
            try:
                # Float?
                params[key] = float(value)
            except ValueError:
                # Bool?
                if value.lower() in ("true", "false"):
                    params[key] = value.lower() == "true"
                else:
                    # String
                    params[key] = value

    return params


def generate_dummy_ohlcv(
    n_bars: int = 500,
    base_price: float = 50000.0,
    volatility: float = 0.015,
) -> pd.DataFrame:
    """
    Generiert synthetische OHLCV-Daten für Research/Tests.

    Die Daten enthalten sowohl Trends als auch Seitwärtsphasen,
    was für verschiedene Strategietypen geeignet ist.

    Args:
        n_bars: Anzahl Bars
        base_price: Startpreis
        volatility: Volatilität (Standardabweichung der Returns)

    Returns:
        OHLCV-DataFrame mit DatetimeIndex (UTC)
    """
    np.random.seed(42)  # Reproduzierbarkeit

    # Zeitindex (stündlich)
    end = datetime.now()
    start = end - timedelta(hours=n_bars)
    index = pd.date_range(start=start, periods=n_bars, freq="1h", tz="UTC")

    # Random Walk für Close mit Trend-Komponente
    returns = np.random.normal(0, volatility, n_bars)

    # Trend + Zyklen für interessantere Strategietests
    trend = np.sin(np.linspace(0, 4 * np.pi, n_bars)) * 0.001
    returns = returns + trend

    close_prices = base_price * np.exp(np.cumsum(returns))

    # OHLC generieren
    df = pd.DataFrame(index=index)
    df["close"] = close_prices
    df["open"] = df["close"].shift(1).fillna(base_price)

    # High = max(open, close) + random bump
    high_bump = np.random.uniform(0, 0.005, n_bars)
    df["high"] = np.maximum(df["open"], df["close"]) * (1 + high_bump)

    # Low = min(open, close) - random dip
    low_dip = np.random.uniform(0, 0.005, n_bars)
    df["low"] = np.minimum(df["open"], df["close"]) * (1 - low_dip)

    # Volume
    df["volume"] = np.random.uniform(100, 1000, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


def load_ohlcv_data(
    data_file: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    n_bars: int,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Lädt OHLCV-Daten aus CSV oder generiert Dummy-Daten.

    Args:
        data_file: Pfad zur CSV-Datei (None = Dummy-Daten)
        start_date: Startdatum-Filter
        end_date: Enddatum-Filter
        n_bars: Anzahl Bars für Dummy-Daten
        verbose: Ausführliche Ausgabe

    Returns:
        Normalisierter OHLCV-DataFrame
    """
    if data_file:
        path = Path(data_file)
        if not path.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {data_file}")

        if verbose:
            print(f"  Lade Daten aus: {data_file}")

        # Kraken-spezifisches Format erkennen
        if "kraken" in str(path).lower():
            loader = KrakenCsvLoader()
        else:
            loader = CsvLoader()

        df = loader.load(str(path))

        # Normalisieren
        normalizer = DataNormalizer()
        df = normalizer.normalize(df)
    else:
        if verbose:
            print(f"  Generiere {n_bars} Dummy-Bars")
        df = generate_dummy_ohlcv(n_bars=n_bars)

    # Datums-Filter anwenden
    if start_date:
        start_dt = pd.to_datetime(start_date).tz_localize("UTC")
        df = df[df.index >= start_dt]
        if verbose:
            print(f"  Filter: >= {start_date}")

    if end_date:
        end_dt = pd.to_datetime(end_date).tz_localize("UTC")
        df = df[df.index <= end_dt]
        if verbose:
            print(f"  Filter: <= {end_date}")

    if len(df) == 0:
        raise ValueError("Keine Daten nach Filterung übrig!")

    return df


def print_summary(
    result,
    strategy_name: str,
    strategy_desc: str,
    df: pd.DataFrame,
    custom_params: Dict[str, Any],
    verbose: bool = False,
) -> None:
    """
    Gibt eine kompakte Zusammenfassung des Research-Runs aus.
    """
    print("\n" + "=" * 70)
    print("RESEARCH RUN ABGESCHLOSSEN")
    print("=" * 70)

    # Strategie-Info
    print(f"\nStrategie:  {strategy_name}")
    print(f"            {strategy_desc}")

    if custom_params:
        print("\nCustom-Parameter:")
        for k, v in custom_params.items():
            print(f"  - {k}: {v}")

    # Zeitraum
    print(f"\nZeitraum:   {df.index[0].strftime('%Y-%m-%d %H:%M')} bis {df.index[-1].strftime('%Y-%m-%d %H:%M')}")
    print(f"Bars:       {len(df)}")

    # Kennzahlen
    print("\n--- KENNZAHLEN ---")
    stats = result.stats

    print(f"  Total Return:    {stats['total_return']:>10.2%}")
    print(f"  Max Drawdown:    {stats['max_drawdown']:>10.2%}")
    print(f"  Sharpe Ratio:    {stats['sharpe']:>10.2f}")
    print(f"  CAGR:            {stats.get('cagr', 0):>10.2%}")

    print("\n--- TRADE-STATISTIKEN ---")
    print(f"  Total Trades:    {stats['total_trades']:>10}")
    print(f"  Win Rate:        {stats['win_rate']:>10.2%}")
    print(f"  Profit Factor:   {stats['profit_factor']:>10.2f}")

    blocked = stats.get("blocked_trades", 0)
    if blocked > 0:
        print(f"  Blocked Trades:  {blocked:>10}")

    # Sortino/Calmar falls vorhanden
    if "sortino" in stats:
        print(f"  Sortino Ratio:   {stats['sortino']:>10.2f}")
    if "calmar" in stats:
        print(f"  Calmar Ratio:    {stats['calmar']:>10.2f}")

    # Live-Trading-Validierung
    print("\n--- LIVE-TRADING-CHECK ---")
    passed, warnings = validate_for_live_trading(stats)
    if passed:
        print("  Status: FREIGEGEBEN")
    else:
        print("  Status: NICHT FREIGEGEBEN")
        for w in warnings:
            print(f"    - {w}")

    # Equity Start/End
    if verbose:
        print("\n--- EQUITY ---")
        start_eq = result.equity_curve.iloc[0]
        end_eq = result.equity_curve.iloc[-1]
        print(f"  Start:  {start_eq:>12,.2f}")
        print(f"  End:    {end_eq:>12,.2f}")

    print("\n" + "=" * 70 + "\n")


def main() -> int:
    """
    Hauptfunktion.

    Returns:
        Exit-Code (0 = Erfolg, 1 = Fehler)
    """
    args = parse_args()

    # Liste Strategien und beende
    if args.list_strategies:
        print("\n" + "=" * 70)
        print("  Peak_Trade Strategy Registry (Phase 18)")
        print("=" * 70 + "\n")
        list_strategies(verbose=True)
        print()
        return 0

    print("\n" + "=" * 70)
    print("  Peak_Trade Research Run (Phase 18)")
    print("=" * 70)

    # 1. Config laden
    print("\n[1/5] Config laden...")
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"\nFEHLER: Config nicht gefunden: {config_path}")
        return 1

    try:
        cfg = load_config(config_path)
        if args.verbose:
            print(f"  Config geladen: {config_path}")
    except Exception as e:
        print(f"\nFEHLER beim Laden der Config: {e}")
        return 1

    # 2. Strategie bestimmen und erstellen
    print("\n[2/5] Strategie laden...")
    strategy_key = args.strategy or cfg.get("general.active_strategy", "ma_crossover")

    try:
        spec = get_strategy_spec(strategy_key)
        strategy = create_strategy_from_config(strategy_key, cfg)
        strategy_desc = spec.description

        if args.verbose:
            print(f"  Strategie: {strategy}")
            print(f"  Beschreibung: {strategy_desc}")
    except KeyError as e:
        print(f"\nFEHLER: {e}")
        print("\nVerfügbare Strategien:")
        list_strategies(verbose=False)
        return 1

    # Custom-Parameter parsen und anwenden
    custom_params = parse_custom_params(args.param)
    if custom_params:
        print(f"  Custom-Parameter: {custom_params}")
        # Parameter in strategy.config überschreiben
        strategy.config.update(custom_params)
        # Auch Instanz-Attribute aktualisieren
        for k, v in custom_params.items():
            if hasattr(strategy, k):
                setattr(strategy, k, v)

    # 3. Daten laden
    print("\n[3/5] Daten laden...")
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

    # 4. Backtest ausführen
    print("\n[4/5] Backtest ausführen...")
    try:
        # Position-Sizer und Risk-Manager aus Config
        position_sizer = build_position_sizer_from_config(cfg)
        risk_manager = build_risk_manager_from_config(cfg, section="risk_management")

        if args.verbose:
            print(f"  Position Sizer: {position_sizer}")
            print(f"  Risk Manager: {risk_manager}")

        # Wrapper für Engine
        def strategy_signal_fn(data, params):
            return strategy.generate_signals(data)

        # Stop-Loss aus Config
        stop_pct = cfg.get(f"strategy.{strategy_key}.stop_pct", 0.02)
        strategy_params = {"stop_pct": stop_pct}

        # Engine erstellen und Backtest ausführen
        engine = BacktestEngine(
            core_position_sizer=position_sizer,
            risk_manager=risk_manager,
        )

        result = engine.run_realistic(
            df=df,
            strategy_signal_fn=strategy_signal_fn,
            strategy_params=strategy_params,
            symbol=args.symbol,
        )
        result.strategy_name = strategy_key

    except Exception as e:
        print(f"\nFEHLER beim Backtest: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # 5. Ergebnis ausgeben und loggen
    print("\n[5/5] Ergebnis ausgeben...")
    print_summary(
        result=result,
        strategy_name=strategy_key,
        strategy_desc=strategy_desc,
        df=df,
        custom_params=custom_params,
        verbose=args.verbose,
    )

    # Registry-Logging
    if not args.no_registry:
        data_source = "csv" if args.data_file else "dummy"
        start_date_str = df.index[0].strftime("%Y-%m-%d")
        end_date_str = df.index[-1].strftime("%Y-%m-%d")

        record = log_experiment_from_result(
            result=result,
            run_type=RUN_TYPE_BACKTEST,
            run_name=f"research_{strategy_key}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            strategy_key=strategy_key,
            symbol=args.symbol,
            extra_metadata={
                "runner": "research_run_strategy.py",
                "tag": args.tag,
                "data_source": data_source,
                "timeframe": args.timeframe,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "custom_params": custom_params,
                "phase": "18_research_playground",
            },
        )

        print(f"Registry-Run-ID: {record.run_id}")
        if args.tag:
            print(f"Tag: {args.tag}")
    else:
        print("(Registry-Logging übersprungen)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
