#!/usr/bin/env python3
"""
Peak_Trade Multi-Strategy Portfolio Backtest
==============================================
Führt Backtest mit mehreren Strategien parallel durch.

Usage:
    python scripts/run_portfolio_backtest.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.core import get_config
from src.strategies.ma_crossover import generate_signals as ma_signals
from src.strategies.momentum import generate_signals as momentum_signals
from src.strategies.rsi import generate_signals as rsi_signals
from src.portfolio import PortfolioManager
from src.backtest.stats import validate_for_live_trading


def create_dummy_data(n_bars: int = 500) -> pd.DataFrame:
    """Erstellt Dummy-Daten mit verschiedenen Markt-Phasen."""
    np.random.seed(42)
    
    start = datetime.now() - timedelta(hours=n_bars)
    dates = pd.date_range(start, periods=n_bars, freq='1h')
    
    # Multi-Phase-Preise für diverse Strategien
    base_price = 50000
    
    # Trend (gut für MA + Momentum)
    trend = np.linspace(0, 8000, n_bars)
    
    # Cycle (gut für RSI Mean-Reversion)
    cycle = np.sin(np.linspace(0, 8 * np.pi, n_bars)) * 2500
    
    # Momentum-Bursts
    bursts = np.zeros(n_bars)
    for i in range(6):
        start_idx = np.random.randint(50, n_bars - 50)
        burst_length = np.random.randint(20, 40)
        bursts[start_idx:start_idx+burst_length] = np.linspace(0, 1500, burst_length)
    
    # Random Walk
    noise = np.random.randn(n_bars).cumsum() * 100
    
    close_prices = base_price + trend + cycle + bursts + noise
    
    df = pd.DataFrame({
        'open': close_prices * (1 + np.random.randn(n_bars) * 0.002),
        'high': close_prices * (1 + abs(np.random.randn(n_bars)) * 0.003),
        'low': close_prices * (1 - abs(np.random.randn(n_bars)) * 0.003),
        'close': close_prices,
        'volume': np.random.randint(10, 100, n_bars)
    }, index=dates)
    
    return df


def print_portfolio_report(result):
    """Druckt Portfolio-Performance-Report."""
    
    print("\n" + "="*70)
    print("MULTI-STRATEGY PORTFOLIO BACKTEST REPORT")
    print("="*70)
    
    # Portfolio-Level Stats
    print("\n💼 PORTFOLIO PERFORMANCE")
    print("-"*70)
    start = result.portfolio_equity.iloc[0]
    end = result.portfolio_equity.iloc[-1]
    
    print(f"Start Capital:     ${start:,.2f}")
    print(f"End Capital:       ${end:,.2f}")
    print(f"Total Return:      {result.stats['total_return']:>7.2%}")
    print(f"Max Drawdown:      {result.stats['max_drawdown']:>7.2%}")
    print(f"Sharpe Ratio:      {result.stats['sharpe']:>7.2f}")
    print(f"Total Trades:      {result.stats['total_trades']:>7}")
    print(f"Avg Win Rate:      {result.stats['avg_win_rate']:>7.2%}")
    
    # Einzelne Strategien
    print("\n📊 INDIVIDUAL STRATEGY PERFORMANCE")
    print("-"*70)
    print(f"{'Strategy':<20} {'Return':>10} {'Sharpe':>8} {'Trades':>8} {'Win Rate':>10}")
    print("-"*70)
    
    for name, strat_result in result.strategy_results.items():
        ret = strat_result.stats['total_return']
        sharpe = strat_result.stats['sharpe']
        trades = strat_result.stats['total_trades']
        win_rate = strat_result.stats['win_rate']
        
        print(f"{name:<20} {ret:>9.2%} {sharpe:>8.2f} {trades:>8} {win_rate:>9.2%}")
    
    # Allocation
    print("\n💰 CAPITAL ALLOCATION")
    print("-"*70)
    for alloc in result.allocations:
        print(f"  {alloc.name:20s}: ${alloc.capital:>10,.2f} ({alloc.weight:>6.1%})")
    
    # Live-Trading-Validierung
    print("\n🔒 LIVE-TRADING-VALIDIERUNG")
    print("-"*70)
    
    passed, warnings = validate_for_live_trading(result.stats)
    
    if passed:
        print("✅ PORTFOLIO FREIGEGEBEN für Live-Trading!")
    else:
        print("❌ PORTFOLIO NICHT FREIGEGEBEN:")
        for w in warnings:
            print(f"  - {w}")
    
    print("\n" + "="*70 + "\n")


def main():
    """Main-Funktion."""
    
    print("\n🚀 Peak_Trade Multi-Strategy Portfolio Backtest")
    print("="*70)
    
    # Config
    cfg = get_config()
    
    print(f"\n⚙️  Portfolio-Config:")
    print(f"  - Total Capital: ${cfg.backtest.initial_cash:,.2f}")
    print(f"  - Risk per Trade: {cfg.risk.risk_per_trade:.1%}")
    
    # Portfolio-Manager erstellen
    pm = PortfolioManager()
    pm.total_capital = cfg.backtest.initial_cash
    
    # Strategien hinzufügen
    print(f"\n📋 Strategien werden geladen...")
    
    try:
        pm.add_strategy("ma_crossover", ma_signals)
        print("  ✅ MA Crossover")
        
        pm.add_strategy("momentum_1h", momentum_signals)
        print("  ✅ Momentum")
        
        pm.add_strategy("rsi_strategy", rsi_signals)
        print("  ✅ RSI")
        
    except KeyError as e:
        print(f"\n❌ FEHLER: {e}")
        return
    
    # Daten erstellen
    print("\n📥 Lade Daten...")
    df = create_dummy_data(n_bars=500)
    print(f"  - Zeitraum: {df.index[0]} bis {df.index[-1]}")
    print(f"  - Bars: {len(df)}")
    
    # Portfolio-Backtest durchführen
    print("\n⚙️  Führe Portfolio-Backtest durch...")
    
    result = pm.run_backtest(
        df=df,
        allocation_method="equal"
    )
    
    # Report drucken
    print_portfolio_report(result)
    
    # Diversifikation analysieren
    print("📈 DIVERSIFIKATIONS-ANALYSE")
    print("-"*70)
    
    # Korrelation zwischen Strategien
    equity_curves = pd.DataFrame({
        name: res.equity_curve.pct_change()
        for name, res in result.strategy_results.items()
    })
    
    correlation_matrix = equity_curves.corr()
    
    print("\nKorrelations-Matrix (Returns):")
    print(correlation_matrix.round(2))
    
    # Interpretation
    avg_corr = correlation_matrix.values[np.triu_indices_from(correlation_matrix.values, k=1)].mean()
    print(f"\nDurchschnittliche Korrelation: {avg_corr:.2f}")
    
    if avg_corr < 0.3:
        print("✅ Gute Diversifikation (niedrige Korrelation)")
    elif avg_corr < 0.6:
        print("⚠️  Moderate Diversifikation")
    else:
        print("❌ Schwache Diversifikation (hohe Korrelation)")


if __name__ == "__main__":
    main()
