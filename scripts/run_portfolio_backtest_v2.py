#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Peak_Trade: Multi-Asset Portfolio Backtest
==========================================
Führt Backtests für mehrere Symbole parallel durch und berechnet
eine kombinierte Portfolio-Equity-Curve.

Features:
- Mehrere Symbole mit konfigurierbaren Gewichten
- Optionale symbol-spezifische Strategien
- Vollständige Reports (CSV, JSON, PNG, HTML)
- Integration mit bestehenden Backtest-Komponenten

Usage:
    python scripts/run_portfolio_backtest_v2.py
    python scripts/run_portfolio_backtest_v2.py --strategy ma_crossover
    python scripts/run_portfolio_backtest_v2.py --use-portfolio-strategies
    python scripts/run_portfolio_backtest_v2.py --run-name crypto_portfolio --no-symbol-reports
"""

from __future__ import annotations

import sys
import argparse
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

from src.core.peak_config import load_config, PeakConfig
from src.core.position_sizing import build_position_sizer_from_config
from src.core.risk import build_risk_manager_from_config
from src.backtest.engine import BacktestEngine
from src.backtest.result import BacktestResult
from src.backtest import stats as stats_mod
from src.backtest.reporting import save_full_report
from src.strategies.registry import (
    create_strategy_from_config,
    get_available_strategy_keys,
)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """Parse CLI-Argumente."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Portfolio-Backtest über mehrere Symbole.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard-Portfolio aus config.toml
  python scripts/run_portfolio_backtest_v2.py

  # Portfolio mit explizitem Strategie-Key
  python scripts/run_portfolio_backtest_v2.py --strategy ma_crossover

  # Portfolio mit symbol-spezifischen Strategien
  python scripts/run_portfolio_backtest_v2.py --use-portfolio-strategies

  # Ohne Einzel-Reports pro Symbol
  python scripts/run_portfolio_backtest_v2.py --no-symbol-reports

  # Mit benutzerdefiniertem Run-Namen
  python scripts/run_portfolio_backtest_v2.py --run-name my_crypto_portfolio
        """
    )
    parser.add_argument(
        "--run-name",
        help="Optionaler Name für diesen Portfolio-Run (für Reports).",
    )
    parser.add_argument(
        "--use-portfolio-strategies",
        action="store_true",
        help=(
            "Wenn gesetzt, werden Strategien aus [portfolio.strategies] verwendet, "
            "falls vorhanden. Sonst wird eine globale Strategie verwendet."
        ),
    )
    parser.add_argument(
        "-s",
        "--strategy",
        help=(
            "Globaler Strategie-Key, der [portfolio.strategy_key] überschreibt. "
            "Verfügbare Werte: " + ", ".join(get_available_strategy_keys())
        ),
    )
    parser.add_argument(
        "--bars",
        type=int,
        default=200,
        help="Anzahl Bars pro Symbol (default: 200)",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Wenn gesetzt, werden keine Portfolio-Reports geschrieben.",
    )
    parser.add_argument(
        "--no-symbol-reports",
        action="store_true",
        help="Wenn gesetzt, werden keine Einzel-Reports pro Symbol geschrieben.",
    )
    return parser.parse_args(argv)


def load_data_for_symbol(cfg: PeakConfig, symbol: str, n_bars: int = 200) -> pd.DataFrame:
    """
    Lädt Marktdaten für ein Symbol.

    Aktuell: Dummy-Daten mit symbol-spezifischem Seed.
    Die gleiche Logik wie in scan_markets.py und sweep_parameters.py.

    TODO: Später mit echten Kraken-Daten ersetzen.

    Args:
        cfg: PeakConfig-Objekt
        symbol: Trading-Pair (z.B. "BTC/EUR")
        n_bars: Anzahl Bars

    Returns:
        DataFrame mit OHLCV-Daten (DatetimeIndex)
    """
    # Symbol-spezifischer Seed für reproduzierbare aber unterschiedliche Daten
    seed = hash(symbol) % (2**32)
    np.random.seed(seed)

    # Start-Zeitpunkt
    start = datetime.now() - timedelta(hours=n_bars)
    dates = pd.date_range(start, periods=n_bars, freq='1h')

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
    df = pd.DataFrame({
        'open': close_prices * (1 + np.random.randn(n_bars) * volatility),
        'high': close_prices * (1 + abs(np.random.randn(n_bars)) * volatility * 1.5),
        'low': close_prices * (1 - abs(np.random.randn(n_bars)) * volatility * 1.5),
        'close': close_prices,
        'volume': np.random.randint(10, 100, n_bars)
    }, index=dates)

    return df



def get_portfolio_definition(cfg: PeakConfig) -> Tuple[str, List[str], List[float], float, Dict[str, str]]:
    """
    Liest die Portfolio-Definition aus der Config.

    Returns:
        Tuple von (portfolio_name, symbols, weights, initial_equity, symbol_strategies)
    """
    portfolio_name = str(cfg.get("portfolio.name", "portfolio"))
    symbols = cfg.get("portfolio.symbols", [])
    weights = cfg.get("portfolio.asset_weights", [])
    initial_equity = float(cfg.get("portfolio.initial_equity", 10000.0))

    # Fallback auf alte Struktur, falls vorhanden
    if not symbols:
        symbols = cfg.get("scan.universe", ["BTC/EUR", "ETH/EUR", "LTC/EUR"])

    if not weights:
        # Gleichgewichtung wenn keine Weights definiert
        weights = [1.0 / len(symbols)] * len(symbols) if symbols else []

    if not symbols or not weights or len(symbols) != len(weights):
        raise ValueError(
            "Ungültige Portfolio-Definition: [portfolio].symbols und [portfolio].asset_weights "
            "müssen vorhanden sein und die gleiche Länge haben. "
            f"Gefunden: symbols={symbols}, weights={weights}"
        )

    # Normiere Gewichte
    weights_arr = np.array(weights, dtype=float)
    if weights_arr.sum() <= 0:
        raise ValueError("Summe der Portfolio-Gewichte muss > 0 sein.")
    weights_arr = weights_arr / weights_arr.sum()
    weights = weights_arr.tolist()

    # Optionale symbol-spezifische Strategien
    symbol_strategies = cfg.get("portfolio.strategies", {}) or {}

    return portfolio_name, list(symbols), weights, initial_equity, symbol_strategies


def run_single_symbol_backtest(
    cfg: PeakConfig,
    symbol: str,
    strategy_key: str,
    n_bars: int = 200,
) -> BacktestResult:
    """
    Führt einen einzelnen Backtest für ein Symbol durch.

    Args:
        cfg: PeakConfig-Objekt
        symbol: Trading-Pair (z.B. "BTC/EUR")
        strategy_key: Strategie-Key aus Registry
        n_bars: Anzahl Bars

    Returns:
        BacktestResult mit allen Metriken
    """
    # Daten laden
    data = load_data_for_symbol(cfg, symbol, n_bars=n_bars)

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
        df=data,
        strategy_signal_fn=strategy_signal_fn,
        strategy_params=strategy_params
    )

    # Metadaten anreichern
    result.metadata.setdefault("symbol", symbol)
    result.metadata.setdefault("strategy_key", strategy_key)
    result.metadata.setdefault("name", f"{symbol} – {strategy_key}")

    return result


def build_portfolio_equity(
    symbol_results: Dict[str, BacktestResult],
    symbols: List[str],
    weights: List[float],
    initial_equity: float,
) -> pd.Series:
    """
    Baut aus mehreren Symbol-Equity-Curves eine Portfolio-Equity-Curve.

    Vorgehen:
    - Alle Equity-Curves auf ihren Startwert normalisieren.
    - Nach Index ausrichten (Outer Join, fehlende Werte ffill).
    - Portfolio-Equity = initial_equity * Sum(w_i * norm_equity_i).

    Args:
        symbol_results: Dict von symbol -> BacktestResult
        symbols: Liste der Symbole (für Reihenfolge)
        weights: Normalisierte Gewichte (gleiche Reihenfolge)
        initial_equity: Anfangskapital des Portfolios

    Returns:
        pd.Series mit Portfolio-Equity-Curve
    """
    if not symbol_results:
        raise ValueError("Keine Symbol-Resultate für Portfolio-Berechnung vorhanden.")

    equity_frames: Dict[str, pd.Series] = {}
    for symbol in symbols:
        res = symbol_results[symbol]
        eq = res.equity_curve.astype(float)
        if eq.empty:
            raise ValueError(f"Leere Equity-Curve für Symbol {symbol}.")
        
        # Duplikate im Index entfernen (behalte letzten Wert)
        if eq.index.duplicated().any():
            eq = eq[~eq.index.duplicated(keep='last')]
        
        # Normalisieren auf Startwert
        norm_eq = eq / eq.iloc[0]
        equity_frames[symbol] = norm_eq

    # DataFrame aus einzelnen Series erstellen
    df = pd.DataFrame(equity_frames)

    # Index sortieren und Lücken füllen
    df = df.sort_index().ffill().bfill()

    # Gewichte anwenden
    w = np.array(weights, dtype=float)
    w = w / w.sum()

    # Sicherstellen, dass Reihenfolge von w der Spaltenreihenfolge entspricht
    df = df[symbols]
    portfolio_norm = (df * w).sum(axis=1)

    portfolio_equity = initial_equity * portfolio_norm
    portfolio_equity.name = "portfolio_equity"
    return portfolio_equity



def aggregate_regime_distribution(
    symbol_results: Dict[str, BacktestResult],
    symbols: List[str],
    weights: List[float],
) -> Dict[str, float]:
    """
    Aggregiert Regime-Verteilungen über alle Symbole gewichtet.

    Args:
        symbol_results: Dict von symbol -> BacktestResult
        symbols: Liste der Symbole
        weights: Normalisierte Gewichte

    Returns:
        Dict mit aggregierter Regime-Verteilung
    """
    regime_counter: Counter = Counter()
    weight_by_symbol = {s: w for s, w in zip(symbols, weights)}

    for symbol, res in symbol_results.items():
        regime_dist = res.metadata.get("regime_distribution", {})
        w = weight_by_symbol.get(symbol, 0.0)
        for regime_key, frac in regime_dist.items():
            regime_counter[regime_key] += w * frac

    total_weight = sum(weight_by_symbol.values()) or 1.0
    portfolio_regime_dist = {k: float(v / total_weight) for k, v in regime_counter.items()}

    return portfolio_regime_dist


def print_portfolio_summary(
    portfolio_name: str,
    symbols: List[str],
    weights: List[float],
    symbol_results: Dict[str, BacktestResult],
    portfolio_stats: Dict[str, Any],
) -> None:
    """Druckt eine formatierte Portfolio-Zusammenfassung."""

    print("\n" + "="*80)
    print(f"PORTFOLIO BACKTEST SUMMARY – {portfolio_name.upper()}")
    print("="*80)

    print("\n📊 PORTFOLIO ALLOCATION")
    print("-"*80)
    print(f"{'Symbol':<15} {'Gewicht':<10} {'Return':<12} {'Sharpe':<10} {'Max DD':<12} {'Trades':<8}")
    print("-"*80)

    for symbol, weight in zip(symbols, weights):
        res = symbol_results.get(symbol)
        if res:
            ret = res.stats.get('total_return', 0.0)
            sharpe = res.stats.get('sharpe', 0.0)
            max_dd = res.stats.get('max_drawdown', 0.0)
            trades = res.stats.get('total_trades', 0)
            print(f"{symbol:<15} {weight:>8.1%}   {ret:>9.2%}   {sharpe:>8.2f}   {max_dd:>9.2%}   {trades:>6}")

    print("-"*80)

    print("\n💼 PORTFOLIO PERFORMANCE")
    print("-"*80)
    print(f"  Total Return:     {portfolio_stats.get('total_return', 0.0):>8.2%}")
    print(f"  CAGR:             {portfolio_stats.get('cagr', 0.0):>8.2%}")
    print(f"  Max Drawdown:     {portfolio_stats.get('max_drawdown', 0.0):>8.2%}")
    print(f"  Sharpe Ratio:     {portfolio_stats.get('sharpe', 0.0):>8.2f}")

    print("\n" + "="*80 + "\n")


def main(argv: List[str] | None = None) -> None:
    """Main-Funktion für Portfolio-Backtest."""
    args = parse_args(argv)

    print("\n🚀 Peak_Trade Multi-Asset Portfolio Backtest")
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

    # Portfolio-Definition laden
    try:
        portfolio_name, symbols, weights, initial_equity, symbol_strategies = get_portfolio_definition(cfg)
    except ValueError as e:
        print(f"\n❌ FEHLER bei Portfolio-Definition: {e}")
        return

    # Strategie bestimmen
    global_strategy_key_cfg = cfg.get("portfolio.strategy_key", None)
    default_strategy_key_cfg = cfg.get("general.active_strategy", "ma_crossover")
    global_strategy_key = args.strategy or global_strategy_key_cfg or default_strategy_key_cfg
    global_strategy_key = str(global_strategy_key)

    print(f"\n📋 Portfolio-Konfiguration:")
    print(f"  - Portfolio-Name:   {portfolio_name}")
    print(f"  - Symbole:          {symbols}")
    print(f"  - Gewichte:         {[f'{w:.1%}' for w in weights]}")
    print(f"  - Initial Equity:   {initial_equity:,.2f}")
    print(f"  - Global Strategy:  {global_strategy_key}")
    print(f"  - Bars pro Symbol:  {args.bars}")
    if symbol_strategies:
        print(f"  - Symbol-Strategien: {symbol_strategies}")

    # Backtests pro Symbol durchführen
    print(f"\n🔄 Starte Backtests für {len(symbols)} Symbole...")
    print("-"*70)

    symbol_results: Dict[str, BacktestResult] = {}

    for symbol, weight in zip(symbols, weights):
        # Strategie für dieses Symbol bestimmen
        if args.use_portfolio_strategies and symbol in symbol_strategies:
            strategy_key = str(symbol_strategies[symbol])
        else:
            strategy_key = global_strategy_key

        print(f"\n📈 {symbol} (Gewicht={weight:.1%}, Strategie={strategy_key})")

        try:
            res = run_single_symbol_backtest(
                cfg=cfg,
                symbol=symbol,
                strategy_key=strategy_key,
                n_bars=args.bars,
            )
        except Exception as e:
            print(f"  ❌ FEHLER: {e}")
            continue

        # Kurze Zusammenfassung
        print(f"  ✅ Return: {res.stats.get('total_return', 0.0):>7.2%} | "
              f"Sharpe: {res.stats.get('sharpe', 0.0):>6.2f} | "
              f"Trades: {res.stats.get('total_trades', 0):>4}")

        symbol_results[symbol] = res

    if not symbol_results:
        print("\n❌ Keine Symbol-Resultate vorhanden – Portfolio-Backtest abgebrochen.")
        return


    # Portfolio-Equity berechnen
    print("\n📊 Berechne Portfolio-Equity...")
    try:
        portfolio_equity = build_portfolio_equity(
            symbol_results=symbol_results,
            symbols=list(symbol_results.keys()),
            weights=[weights[symbols.index(s)] for s in symbol_results.keys()],
            initial_equity=initial_equity,
        )
    except Exception as e:
        print(f"❌ FEHLER bei Portfolio-Equity-Berechnung: {e}")
        return

    # Portfolio-Stats berechnen
    portfolio_dd = stats_mod.compute_drawdown(portfolio_equity)
    portfolio_stats = stats_mod.compute_basic_stats(portfolio_equity)

    # Aggregierte Regime-Infos
    portfolio_regime_dist = aggregate_regime_distribution(
        symbol_results=symbol_results,
        symbols=list(symbol_results.keys()),
        weights=[weights[symbols.index(s)] for s in symbol_results.keys()],
    )

    # Portfolio-Metadata zusammenbauen
    portfolio_metadata: Dict[str, Any] = {
        "name": f"Portfolio – {portfolio_name}",
        "portfolio_name": portfolio_name,
        "symbols": list(symbol_results.keys()),
        "weights": [weights[symbols.index(s)] for s in symbol_results.keys()],
        "initial_equity": initial_equity,
        "global_strategy_key": global_strategy_key,
        "regime_distribution": portfolio_regime_dist,
        "symbols_stats": {
            symbol: res.stats for symbol, res in symbol_results.items()
        },
        "symbols_regimes": {
            symbol: res.metadata.get("regime_distribution", {})
            for symbol, res in symbol_results.items()
        },
    }

    # Portfolio-BacktestResult erstellen
    portfolio_result = BacktestResult(
        equity_curve=portfolio_equity,
        drawdown=portfolio_dd,
        trades=None,  # Portfolio-Level hat keine direkten Trades
        stats=portfolio_stats,
        metadata=portfolio_metadata,
    )

    # Summary ausgeben
    print_portfolio_summary(
        portfolio_name=portfolio_name,
        symbols=list(symbol_results.keys()),
        weights=[weights[symbols.index(s)] for s in symbol_results.keys()],
        symbol_results=symbol_results,
        portfolio_stats=portfolio_stats,
    )

    # Reports speichern
    if args.no_report:
        print("ℹ️  Portfolio-Report wurde aufgrund von --no-report nicht geschrieben.")
        return

    print("\n💾 Speichere Reports...")

    reports_dir = Path("reports") / "portfolio"
    reports_dir.mkdir(parents=True, exist_ok=True)

    base_name = args.run_name or portfolio_name
    run_name = f"portfolio_{base_name}"

    # Portfolio-Report (inkl. HTML)
    try:
        save_full_report(
            result=portfolio_result,
            output_dir=str(reports_dir),
            run_name=run_name,
            save_plots_flag=True,
            save_html_flag=True,
        )
        print(f"  ✅ Portfolio-Report: {reports_dir}/{run_name}_*.[csv/json/png/html]")
    except Exception as e:
        print(f"  ⚠️  Warnung: Konnte Portfolio-Report nicht erstellen: {e}")

    # Einzel-Reports pro Symbol (optional)
    if not args.no_symbol_reports:
        symbols_dir = reports_dir / "symbols"
        symbols_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n💾 Erstelle Einzel-Reports pro Symbol...")
        for symbol, res in symbol_results.items():
            symbol_safe = symbol.replace("/", "_")
            symbol_run_name = f"{base_name}_{symbol_safe}"

            try:
                save_full_report(
                    result=res,
                    output_dir=str(symbols_dir),
                    run_name=symbol_run_name,
                    save_plots_flag=True,
                    save_html_flag=True,
                )
                print(f"  ✅ {symbol}: {symbols_dir}/{symbol_run_name}_* [csv/json/png/html]")
            except Exception as e:
                print(f"  ⚠️  Warnung: Konnte Report für {symbol} nicht erstellen: {e}")

    print(f"\n✅ Portfolio-Backtest abgeschlossen!")
    print(f"   Reports: {reports_dir}")
    print()


if __name__ == "__main__":
    main()
