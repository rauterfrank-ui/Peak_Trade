#!/usr/bin/env python3
"""
Peak_Trade Market Scanner / Screener
======================================
Scannt mehrere Märkte mit einer Strategie und erstellt eine Ranking-Tabelle.

Nutzt alle Bausteine:
- Strategy-Registry
- Position Sizing
- Risk Management
- Data-Pipeline

Usage:
    python scripts/scan_markets.py
    python scripts/scan_markets.py --strategy rsi_reversion
    python scripts/scan_markets.py --sort-by sharpe --ascending
    python scripts/scan_markets.py --run-name crypto_scan --no-individual-reports
"""

import sys
import argparse
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any

from src.core.peak_config import load_config
from src.core.position_sizing import build_position_sizer_from_config
from src.core.risk import build_risk_manager_from_config
from src.core.experiments import log_experiment_from_result
from src.strategies.registry import (
    create_strategy_from_config,
    list_strategies,
)
from src.backtest.engine import BacktestEngine
from src.backtest.reporting import save_full_report


def load_data_for_symbol(symbol: str, n_bars: int = 200) -> pd.DataFrame:
    """
    Lädt Daten für ein bestimmtes Symbol.

    Aktuell: Dummy-Daten mit symbol-spezifischem Seed.
    TODO: Später mit echten Kraken-Daten ersetzen.

    Args:
        symbol: Trading-Pair (z.B. "BTC/EUR")
        n_bars: Anzahl Bars

    Returns:
        DataFrame mit OHLCV-Daten
    """
    # Symbol-spezifischer Seed für reproduzierbare aber unterschiedliche Daten
    seed = hash(symbol) % (2**32)
    np.random.seed(seed)

    # Start-Zeitpunkt
    start = datetime.now() - timedelta(hours=n_bars)
    dates = pd.date_range(start, periods=n_bars, freq='1h')

    # Preis-Simulation mit symbol-spezifischen Eigenschaften
    # BTC: höherer Preis, ETH: mittlerer Preis, LTC: niedriger Preis
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
    df = pd.DataFrame({
        'open': close_prices * (1 + np.random.randn(n_bars) * volatility),
        'high': close_prices * (1 + abs(np.random.randn(n_bars)) * volatility * 1.5),
        'low': close_prices * (1 - abs(np.random.randn(n_bars)) * volatility * 1.5),
        'close': close_prices,
        'volume': np.random.randint(10, 100, n_bars)
    }, index=dates)

    return df


def run_backtest_for_symbol(
    symbol: str,
    strategy_key: str,
    cfg: Any,
    n_bars: int = 200,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Führt Backtest für ein Symbol aus.

    Args:
        symbol: Trading-Pair
        strategy_key: Strategie-Key aus Registry
        cfg: Config-Objekt
        n_bars: Anzahl Bars
        verbose: Detaillierte Ausgabe

    Returns:
        Dict mit Ergebnissen: {
            'symbol': str,
            'total_return': float,
            'sharpe': float,
            'max_drawdown': float,
            'total_trades': int,
            'profit_factor': float,
            'win_rate': float,
            'result': BacktestResult
        }
    """
    if verbose:
        print(f"\n🔍 Scanne {symbol}...")

    # Daten laden
    df = load_data_for_symbol(symbol, n_bars=n_bars)

    # Strategie erstellen
    strategy = create_strategy_from_config(strategy_key, cfg)

    # Position Sizer & Risk Manager
    position_sizer = build_position_sizer_from_config(cfg)
    risk_manager = build_risk_manager_from_config(cfg, section="risk_management")

    # Wrapper für Legacy-API
    def strategy_signal_fn(df, params):
        sigs = strategy.generate_signals(df)
        return sigs.replace(-1, 0)  # Long-Only

    # Stop-Loss aus Config
    stop_pct = cfg.get(f"strategy.{strategy_key}.stop_pct", 0.02)
    strategy_params = {"stop_pct": stop_pct}

    # Backtest durchführen
    engine = BacktestEngine(
        core_position_sizer=position_sizer,
        risk_manager=risk_manager
    )
    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=strategy_signal_fn,
        strategy_params=strategy_params
    )

    # Ergebnis-Dict erstellen (inkl. Regime-Infos aus metadata)
    regime_dist = result.metadata.get('regime_distribution', {})
    
    return {
        'symbol': symbol,
        'total_return': result.stats.get('total_return', 0.0),
        'sharpe': result.stats.get('sharpe', 0.0),
        'max_drawdown': result.stats.get('max_drawdown', 0.0),
        'total_trades': result.stats.get('total_trades', 0),
        'profit_factor': result.stats.get('profit_factor', 0.0),
        'win_rate': result.stats.get('win_rate', 0.0),
        'cagr': result.stats.get('cagr', 0.0),
        'regime_distribution': regime_dist,
        'result': result,
    }


def print_scan_table(results_df: pd.DataFrame, strategy_name: str):
    """Druckt formatierte Scan-Tabelle."""

    print("\n" + "="*90)
    print(f"MARKET SCAN RESULTS - {strategy_name.upper()}")
    print("="*90)

    if len(results_df) == 0:
        print("Keine Ergebnisse verfügbar.")
        return

    print(f"\n{'Rank':<6} {'Symbol':<12} {'Return':<10} {'Sharpe':<8} {'Max DD':<10} {'Trades':<8} {'PF':<8} {'Win %':<8}")
    print("-"*90)

    for i, row in results_df.iterrows():
        rank = i + 1
        symbol = row['symbol']
        ret = f"{row['total_return']:>7.2%}"
        sharpe = f"{row['sharpe']:>6.2f}"
        dd = f"{row['max_drawdown']:>7.2%}"
        trades = f"{int(row['total_trades']):>6}"
        pf = f"{row['profit_factor']:>6.2f}"
        wr = f"{row['win_rate']:>6.1%}"

        print(f"{rank:<6} {symbol:<12} {ret:<10} {sharpe:<8} {dd:<10} {trades:<8} {pf:<8} {wr:<8}")

    print("="*90 + "\n")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Market Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default strategy and universe from config.toml
  python scripts/scan_markets.py

  # Run with specific strategy
  python scripts/scan_markets.py --strategy rsi_reversion

  # Sort by Sharpe Ratio (descending)
  python scripts/scan_markets.py --sort-by sharpe

  # Sort ascending (worst first)
  python scripts/scan_markets.py --sort-by max_drawdown --ascending

  # Disable individual reports per symbol
  python scripts/scan_markets.py --no-individual-reports
        """
    )

    parser.add_argument(
        "--strategy",
        type=str,
        default=None,
        help="Strategy key (overrides config.toml)"
    )

    parser.add_argument(
        "--run-name",
        type=str,
        default=None,
        help="Optional name for this scan (for reports)"
    )

    parser.add_argument(
        "--sort-by",
        type=str,
        default=None,
        help="Sort metric (overrides config.toml). Options: total_return, sharpe, max_drawdown, profit_factor, total_trades"
    )

    parser.add_argument(
        "--ascending",
        action="store_true",
        help="Sort ascending (default: descending)"
    )

    parser.add_argument(
        "--no-individual-reports",
        action="store_true",
        help="If set, no individual reports per symbol will be saved"
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=None,
        help="Number of bars per backtest (overrides config.toml)"
    )

    return parser.parse_args()


def main():
    """Main-Funktion."""

    args = parse_args()

    print("\n🔍 Peak_Trade Market Scanner")
    print("="*70)

    # Config laden
    print("\n⚙️  Lade Konfiguration...")
    try:
        cfg = load_config("config.toml")
        print("✅ config.toml erfolgreich geladen")
    except FileNotFoundError as e:
        print(f"\n❌ FEHLER: {e}")
        print("\nBitte erstelle eine config.toml im Projekt-Root.")
        return

    # Scan-Settings
    universe = cfg.get("scan.universe", ["BTC/EUR", "ETH/EUR", "LTC/EUR"])
    scan_name = cfg.get("scan.name", "default_universe")
    sort_by = args.sort_by or cfg.get("scan.sort_by", "total_return")
    sort_desc = not args.ascending if args.ascending else cfg.get("scan.sort_desc", True)
    n_bars = args.bars or cfg.get("scan.scan_bars", 200)

    print(f"  - Universe: {scan_name}")
    print(f"  - Symbole: {', '.join(universe)}")
    print(f"  - Bars pro Symbol: {n_bars}")
    print(f"  - Sortierung: {sort_by} ({'DESC' if sort_desc else 'ASC'})")

    # Strategie auswählen
    if args.strategy:
        strategy_key = args.strategy
        print(f"\n📊 CLI-Override: Nutze Strategie '{strategy_key}'")
    else:
        strategy_key = cfg.get("general.active_strategy", "ma_crossover")
        print(f"\n📊 Nutze aktive Strategie: '{strategy_key}'")

    # Strategie validieren
    print(f"\n🔨 Validiere Strategie '{strategy_key}'...")
    try:
        strategy = create_strategy_from_config(strategy_key, cfg)
        print(f"✅ {strategy}")
    except KeyError as e:
        print(f"\n❌ FEHLER: {e}")
        print("\nVerfügbare Strategien:")
        list_strategies(verbose=False)
        return
    except Exception as e:
        print(f"\n❌ FEHLER beim Erstellen der Strategie: {e}")
        return

    # Scan durchführen
    print(f"\n🚀 Starte Market Scan für {len(universe)} Symbole...")
    print("-"*70)

    results = []
    for symbol in universe:
        try:
            result = run_backtest_for_symbol(
                symbol=symbol,
                strategy_key=strategy_key,
                cfg=cfg,
                n_bars=n_bars,
                verbose=True
            )
            results.append(result)

            # Kurze Zusammenfassung
            print(f"  ✅ Return: {result['total_return']:>7.2%} | "
                  f"Sharpe: {result['sharpe']:>6.2f} | "
                  f"Trades: {result['total_trades']:>4}")

            # Experiment-Record pro Symbol-Scan loggen
            run_name_symbol = f"{strategy_key}_{symbol.replace('/', '_')}_{scan_name}"
            log_experiment_from_result(
                result=result['result'],
                run_type="market_scan",
                run_name=run_name_symbol,
                strategy_key=strategy_key,
                symbol=symbol,
                scan_name=scan_name,
                report_dir=Path("reports"),
                report_prefix=run_name_symbol,
                extra_metadata={
                    "runner": "scan_markets.py",
                    "universe": universe,
                },
            )

        except Exception as e:
            print(f"  ❌ FEHLER bei {symbol}: {e}")
            continue

    if len(results) == 0:
        print("\n❌ Keine erfolgreichen Backtests. Scan abgebrochen.")
        return

    # Ergebnisse als DataFrame
    # Regime-Verteilungen in einzelne Spalten extrahieren
    rows = []
    for r in results:
        # Basis-Stats (ohne 'result' und 'regime_distribution')
        row = {k: v for k, v in r.items() if k not in ['result', 'regime_distribution']}
        
        # Regime-Verteilungen als separate Spalten hinzufügen
        regime_dist = r.get('regime_distribution', {})
        for regime_key in [
            "TREND_UP_LOW_VOL",
            "TREND_UP_HIGH_VOL",
            "TREND_DOWN_LOW_VOL",
            "TREND_DOWN_HIGH_VOL",
            "RANGE_LOW_VOL",
            "RANGE_HIGH_VOL",
        ]:
            col_name = f"regime_{regime_key.lower()}"
            row[col_name] = regime_dist.get(regime_key, 0.0)
        
        rows.append(row)
    
    results_df = pd.DataFrame(rows)

    # Sortieren
    results_df = results_df.sort_values(by=sort_by, ascending=not sort_desc)
    results_df = results_df.reset_index(drop=True)

    # Tabelle drucken
    print_scan_table(results_df, strategy_key)

    # Reports speichern
    print("💾 Speichere Reports...")
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    # Summary CSV
    run_name = args.run_name or "scan"
    summary_filename = f"{strategy_key}_{run_name}_summary.csv"
    summary_path = reports_dir / summary_filename
    results_df.to_csv(summary_path, index=False)
    print(f"  ✅ Summary gespeichert: {summary_path}")

    # Individual Reports (optional)
    if not args.no_individual_reports:
        print("\n💾 Erstelle individuelle Reports pro Symbol...")
        for i, result in enumerate(results):
            symbol = result['symbol']
            symbol_safe = symbol.replace("/", "_")
            report_name = f"{strategy_key}_{run_name}_{symbol_safe}"

            try:
                save_full_report(
                    result=result['result'],
                    output_dir="reports",
                    run_name=report_name,
                    save_plots_flag=True,
                    save_html_flag=True,
                )
                print(f"  ✅ {symbol} Report: {report_name}_* [csv/json/png/html]")
            except Exception as e:
                print(f"  ⚠️  Warnung: Konnte Report für {symbol} nicht erstellen: {e}")

    print(f"\n✅ Market Scan abgeschlossen!")
    print(f"   Beste Performance: {results_df.iloc[0]['symbol']} "
          f"({results_df.iloc[0]['total_return']:.2%})")
    print()


if __name__ == "__main__":
    main()
