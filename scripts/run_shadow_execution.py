#!/usr/bin/env python3
"""
Peak_Trade - Shadow-/Dry-Run-Execution Script (Phase 24)
========================================================

Führt einen Shadow-Run aus, der die Execution-Pipeline nutzt,
aber KEINE echten API-Calls an Exchanges macht.

Features:
- Nutzt ShadowOrderExecutor für simulierte Order-Ausführung
- Konfigurierbare Fee-/Slippage-Simulation
- Logging in der Experiments-Registry (run_type="shadow_run")
- Kompatibel mit allen OOP-Strategien

Anwendungsfälle:
- Shadow-Live: Strategien parallel zum Markt simulieren
- Dry-Run vor echtem Testnet/Live-Einsatz
- Quasi-realistische Ausführungssimulation

WICHTIG: Dieser Script sendet NIEMALS echte Orders an Exchanges!
         Alles ist zu 100% simulativ.

Usage:
    # Einfachster Aufruf (defaults aus config.toml)
    python scripts/run_shadow_execution.py

    # Mit CLI-Argumenten
    python scripts/run_shadow_execution.py --strategy ma_crossover --start 2023-01-01 --end 2023-12-31

    # Mit Tag für Registry
    python scripts/run_shadow_execution.py --strategy rsi_strategy --tag shadow_test_v1

    # Mit alternativer Config
    python scripts/run_shadow_execution.py --config custom_config.toml
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

# Projekt-Root zum Path hinzufügen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.peak_config import PeakConfig, load_config
from src.core.position_sizing import build_position_sizer_from_config
from src.core.risk import build_risk_manager_from_config
from src.backtest.engine import BacktestEngine
from src.backtest.stats import compute_backtest_stats
from src.data import DataNormalizer, CsvLoader, KrakenCsvLoader
from src.execution.pipeline import ExecutionPipeline
from src.orders.shadow import ShadowOrderExecutor, ShadowMarketContext
from src.core.experiments import log_shadow_run, RUN_TYPE_SHADOW_RUN
from src.strategies.registry import (
    get_available_strategy_keys,
    create_strategy_from_config,
)


def parse_args() -> argparse.Namespace:
    """CLI-Argumente parsen."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Shadow-/Dry-Run-Execution (Phase 24)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
WICHTIG: Dieser Script sendet NIEMALS echte Orders an Exchanges!
         Alles ist zu 100% simulativ (Shadow-/Dry-Run-Modus).

Beispiele:
  # Standard Shadow-Run mit ma_crossover
  python scripts/run_shadow_execution.py

  # RSI-Strategie mit CSV-Daten
  python scripts/run_shadow_execution.py --strategy rsi_strategy --data-file data/eth_1h.csv

  # Mit Datumsbeschränkung und Tag
  python scripts/run_shadow_execution.py --start 2023-06-01 --end 2023-12-31 --tag shadow_test_v1

  # Mit Fee- und Slippage-Überschreibung
  python scripts/run_shadow_execution.py --fee-rate 0.001 --slippage-bps 10
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.toml",
        help="Pfad zur TOML-Config-Datei (default: config.toml)",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default=None,
        help="Strategie-Name (z.B. ma_crossover, rsi_strategy). Default: aus Config",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="BTC/EUR",
        help="Trading-Symbol (default: BTC/EUR)",
    )
    parser.add_argument(
        "--data-file",
        type=str,
        default=None,
        help="Pfad zur CSV-Datei mit OHLCV-Daten. Wenn nicht angegeben: Dummy-Daten",
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
        "--tag",
        type=str,
        default=None,
        help="Optionaler Tag für Registry-Logging (z.B. 'shadow_test_v1')",
    )
    parser.add_argument(
        "--fee-rate",
        type=float,
        default=None,
        help="Fee-Rate (z.B. 0.0005 = 5 bps). Default: aus Config",
    )
    parser.add_argument(
        "--slippage-bps",
        type=float,
        default=None,
        help="Slippage in bps (z.B. 5). Default: aus Config",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Ausführliche Ausgabe",
    )
    parser.add_argument(
        "--no-registry",
        action="store_true",
        help="Kein Logging in der Experiments-Registry",
    )

    return parser.parse_args()


def generate_dummy_ohlcv(
    n_bars: int = 500,
    base_price: float = 50000.0,
    volatility: float = 0.015,
) -> pd.DataFrame:
    """
    Generiert synthetische OHLCV-Daten für Tests.

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

    # Random Walk für Close
    returns = np.random.normal(0, volatility, n_bars)
    # Trend hinzufügen für interessantere Crossovers
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
        # CSV laden
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
        # Dummy-Daten generieren
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
    stats: dict,
    execution_summary: dict,
    strategy_name: str,
    symbol: str,
    df: pd.DataFrame,
    verbose: bool = False,
) -> None:
    """
    Gibt eine kompakte Zusammenfassung des Shadow-Runs aus.
    """
    print("\n" + "=" * 70)
    print("SHADOW-RUN ABGESCHLOSSEN")
    print("=" * 70)

    # Zeitraum
    print(f"\nZeitraum:   {df.index[0].strftime('%Y-%m-%d')} bis {df.index[-1].strftime('%Y-%m-%d')}")
    print(f"Strategie:  {strategy_name}")
    print(f"Symbol:     {symbol}")
    print(f"Bars:       {len(df)}")
    print(f"Modus:      SHADOW (keine echten Orders)")

    # Performance-Kennzahlen
    print("\n--- PERFORMANCE ---")
    print(f"  Total Return:    {stats.get('total_return', 0):>10.2%}")
    print(f"  Max Drawdown:    {stats.get('max_drawdown', 0):>10.2%}")
    print(f"  Sharpe Ratio:    {stats.get('sharpe', 0):>10.2f}")
    print(f"  CAGR:            {stats.get('cagr', 0):>10.2%}")

    # Execution-Statistiken
    print("\n--- EXECUTION (SHADOW) ---")
    print(f"  Total Orders:    {execution_summary.get('total_orders', 0):>10}")
    print(f"  Filled Orders:   {execution_summary.get('filled_orders', 0):>10}")
    print(f"  Rejected Orders: {execution_summary.get('rejected_orders', 0):>10}")
    print(f"  Fill Rate:       {execution_summary.get('fill_rate', 0):>10.2%}")
    print(f"  Total Notional:  {execution_summary.get('total_notional', 0):>10,.2f}")
    print(f"  Total Fees:      {execution_summary.get('total_fees', 0):>10,.2f}")

    # Execution-Parameter
    print("\n--- SHADOW-PARAMETER ---")
    print(f"  Fee Rate:        {execution_summary.get('fee_rate', 0)*10000:>10.1f} bps")
    print(f"  Slippage:        {execution_summary.get('slippage_bps', 0):>10.1f} bps")

    # Trade-Statistiken (falls vorhanden)
    if "total_trades" in stats:
        print("\n--- TRADE-STATISTIKEN ---")
        print(f"  Total Trades:    {stats.get('total_trades', 0):>10}")
        print(f"  Win Rate:        {stats.get('win_rate', 0):>10.2%}")
        print(f"  Profit Factor:   {stats.get('profit_factor', 0):>10.2f}")

    if verbose:
        print("\n--- HINWEIS ---")
        print("  Dies war ein SHADOW-RUN - keine echten Orders wurden gesendet.")
        print("  Die Execution-Pipeline wurde simuliert, aber keine API-Calls gemacht.")

    print("\n" + "=" * 70 + "\n")


def main() -> int:
    """
    Hauptfunktion.

    Returns:
        Exit-Code (0 = Erfolg, 1 = Fehler)
    """
    args = parse_args()

    print("\n" + "=" * 70)
    print("  Peak_Trade Shadow-/Dry-Run-Execution (Phase 24)")
    print("  WICHTIG: KEINE echten Orders werden gesendet!")
    print("=" * 70)

    # 1. Config laden
    print("\n[1/5] Config laden...")
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"\nFEHLER: Config nicht gefunden: {config_path}")
        print("Bitte erstelle eine config.toml im Projekt-Root.")
        return 1

    try:
        cfg = load_config(config_path)
        if args.verbose:
            print(f"  Config geladen: {config_path}")
    except Exception as e:
        print(f"\nFEHLER beim Laden der Config: {e}")
        return 1

    # Shadow-Konfiguration aus Config lesen
    shadow_enabled = cfg.get("shadow.enabled", True)
    fee_rate = args.fee_rate or cfg.get("shadow.fee_rate", 0.0005)
    slippage_bps = args.slippage_bps if args.slippage_bps is not None else cfg.get("shadow.slippage_bps", 0.0)
    base_currency = cfg.get("shadow.base_currency", "EUR")

    if args.verbose:
        print(f"  Shadow enabled: {shadow_enabled}")
        print(f"  Fee rate: {fee_rate} ({fee_rate * 10000:.1f} bps)")
        print(f"  Slippage: {slippage_bps} bps")

    # 2. Strategie bestimmen
    print("\n[2/5] Strategie bestimmen...")
    strategy_name = args.strategy or cfg.get("general.active_strategy", "ma_crossover")
    if args.verbose:
        print(f"  Strategie: {strategy_name}")

    # Strategie-Parameter aus Config holen
    strategy_section = f"strategy.{strategy_name}"
    strategy_params = cfg.get(strategy_section, {})
    if not strategy_params:
        print(f"\nWARNUNG: Keine Config-Sektion [{strategy_section}] gefunden.")
        print("  Nutze Default-Parameter.")

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

    # 4. Shadow-Execution ausführen
    print("\n[4/5] Shadow-Execution ausführen...")
    try:
        # OOP-Position-Sizer und Risk-Manager aus Config erstellen
        position_sizer = build_position_sizer_from_config(cfg)
        risk_manager = build_risk_manager_from_config(cfg, section="risk_management")

        if args.verbose:
            print(f"  Position Sizer: {position_sizer}")
            print(f"  Risk Manager: {risk_manager}")

        # OOP-Strategie aus Registry erstellen
        strategy = create_strategy_from_config(strategy_name, cfg)
        if args.verbose:
            print(f"  Strategie: {strategy}")

        # Shadow-Pipeline erstellen
        pipeline = ExecutionPipeline.for_shadow(
            fee_rate=fee_rate,
            slippage_bps=slippage_bps,
        )

        if args.verbose:
            print(f"  Shadow-Pipeline erstellt")
            print(f"  Executor: {type(pipeline.executor).__name__}")

        # Signale generieren
        signals = strategy.generate_signals(df)

        # Shadow-Execution über Pipeline
        # Preise im Shadow-Context setzen
        for ts, row in df.iterrows():
            pipeline.executor.context.set_price(args.symbol, row["close"])

        # Execution durchführen
        results = pipeline.execute_from_signals(
            signals=signals,
            prices=df["close"],
            symbol=args.symbol,
            base_currency=base_currency,
        )

        # Execution-Summary vom Shadow-Executor holen
        if hasattr(pipeline.executor, "get_execution_summary"):
            execution_summary = pipeline.executor.get_execution_summary()
        else:
            execution_summary = pipeline.get_execution_summary()

        # Backtest für Stats ausführen (parallel zur Shadow-Execution)
        engine = BacktestEngine(
            core_position_sizer=position_sizer,
            risk_manager=risk_manager,
        )

        def strategy_signal_fn(data, params):
            return strategy.generate_signals(data)

        backtest_result = engine.run_realistic(
            df=df,
            strategy_signal_fn=strategy_signal_fn,
            strategy_params=strategy_params,
        )

        stats = backtest_result.stats

    except KeyError as e:
        print(f"\nFEHLER: Strategie nicht gefunden: {e}")
        available = ", ".join(get_available_strategy_keys())
        print(f"  Verfügbare Strategien: {available}")
        return 1
    except Exception as e:
        print(f"\nFEHLER bei der Shadow-Execution: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # 5. Ergebnis ausgeben
    print("\n[5/5] Ergebnis ausgeben...")
    print_summary(
        stats=stats,
        execution_summary=execution_summary,
        strategy_name=strategy_name,
        symbol=args.symbol,
        df=df,
        verbose=args.verbose,
    )

    # Registry-Logging
    if not args.no_registry:
        start_date_str = df.index[0].strftime("%Y-%m-%d")
        end_date_str = df.index[-1].strftime("%Y-%m-%d")

        run_id = log_shadow_run(
            strategy_key=strategy_name,
            symbol=args.symbol,
            timeframe="1h",  # NOTE: Siehe docs/TECH_DEBT_BACKLOG.md (Eintrag "Timeframe aus Daten ableiten")
            stats=stats,
            execution_summary=execution_summary,
            start_date=start_date_str,
            end_date=end_date_str,
            tag=args.tag,
            config_path=str(config_path),
        )

        print(f"Registry-Run-ID: {run_id}")
        print(f"Run-Type: {RUN_TYPE_SHADOW_RUN}")
        if args.tag:
            print(f"Tag: {args.tag}")

    print("\nHINWEIS: Dies war ein SHADOW-RUN. Keine echten Orders wurden gesendet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
