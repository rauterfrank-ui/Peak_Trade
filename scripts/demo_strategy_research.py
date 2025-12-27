#!/usr/bin/env python3
# scripts/demo_strategy_research.py
"""
Peak_Trade Phase 27: Strategy Research Track Demo
==================================================
Demonstriert die neuen Research-Strategien (Phase 27):

1. VolBreakoutStrategy - ATR-basierte Volatility Breakouts
2. MeanReversionChannelStrategy - Bollinger-ähnliche Channel Reversion
3. RsiReversionStrategy - RSI Mean-Reversion mit optionalem Trendfilter

Usage:
    .venv/bin/python scripts/demo_strategy_research.py

WICHTIG: Nur für Research/Backtest/Shadow - NICHT für Live-Trading!
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.strategies.vol_breakout import VolBreakoutStrategy
from src.strategies.mean_reversion_channel import MeanReversionChannelStrategy
from src.strategies.rsi_reversion import RsiReversionStrategy


def create_synthetic_ohlcv(n_bars: int = 500, seed: int = 42) -> pd.DataFrame:
    """Erzeugt synthetische OHLCV-Daten für Demo."""
    np.random.seed(seed)

    idx = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")

    # Random Walk mit Drift und Volatilitätsclustern
    returns = np.random.randn(n_bars) * 0.01
    # Simuliere Volatilitätscluster
    vol_regime = np.where(np.sin(np.linspace(0, 4 * np.pi, n_bars)) > 0, 1.5, 0.5)
    returns = returns * vol_regime

    close = 50000 * np.exp(np.cumsum(returns))

    df = pd.DataFrame(index=idx)
    df["close"] = close
    df["open"] = df["close"].shift(1).fillna(50000)
    df["high"] = df[["open", "close"]].max(axis=1) * (1 + np.abs(np.random.randn(n_bars)) * 0.003)
    df["low"] = df[["open", "close"]].min(axis=1) * (1 - np.abs(np.random.randn(n_bars)) * 0.003)
    df["volume"] = np.random.uniform(100, 500, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


def compute_simple_pnl(df: pd.DataFrame, signals: pd.Series) -> pd.Series:
    """Berechnet einfache P&L basierend auf Signalen."""
    returns = df["close"].pct_change().fillna(0)
    # Signal vom Vortag (wir können nicht in die Zukunft schauen)
    position = signals.shift(1).fillna(0)
    pnl = position * returns
    return pnl.cumsum()


def print_strategy_stats(name: str, df: pd.DataFrame, signals: pd.Series) -> None:
    """Gibt einfache Statistiken zur Strategie aus."""
    print(f"\n{'=' * 60}")
    print(f"Strategie: {name}")
    print("=" * 60)

    # Signal-Verteilung
    value_counts = signals.value_counts().sort_index()
    total = len(signals)
    print(f"\nSignal-Verteilung (n={total}):")
    for val, count in value_counts.items():
        label = {1: "Long", -1: "Short", 0: "Flat"}[val]
        print(f"  {label:6s}: {count:5d} ({100 * count / total:.1f}%)")

    # Einfache P&L
    cumulative_pnl = compute_simple_pnl(df, signals)
    final_pnl = cumulative_pnl.iloc[-1]
    max_dd = (cumulative_pnl.cummax() - cumulative_pnl).max()

    print(f"\nPerformance (einfache Simulation):")
    print(f"  Total Return:   {100 * final_pnl:+.2f}%")
    print(f"  Max Drawdown:   {100 * max_dd:.2f}%")

    # Signal-Wechsel zählen
    signal_changes = (signals != signals.shift(1)).sum()
    print(f"  Signal-Wechsel: {signal_changes}")


def demo_vol_breakout(df: pd.DataFrame) -> None:
    """Demo: Volatility Breakout Strategy."""
    print("\n" + "=" * 70)
    print("1. VOLATILITY BREAKOUT STRATEGY")
    print("=" * 70)
    print(
        """
Konzept:
- Identifiziere Breakouts über n-Bar Hoch/Tief
- Nutze ATR-Perzentil als Volatilitäts-Filter
- Nur Breakouts bei erhöhter Volatilität

Ideal für: Märkte mit klaren Konsolidierungs- und Ausbruchsphasen
"""
    )

    # Default-Parameter
    strategy = VolBreakoutStrategy(
        lookback_breakout=20,
        vol_window=14,
        vol_percentile=50.0,
        side="both",
    )
    signals = strategy.generate_signals(df)
    print_strategy_stats("Vol Breakout (default)", df, signals)

    # Long-Only
    strategy_long = VolBreakoutStrategy(side="long")
    signals_long = strategy_long.generate_signals(df)
    print_strategy_stats("Vol Breakout (long only)", df, signals_long)


def demo_mean_reversion_channel(df: pd.DataFrame) -> None:
    """Demo: Mean Reversion Channel Strategy."""
    print("\n" + "=" * 70)
    print("2. MEAN REVERSION CHANNEL STRATEGY")
    print("=" * 70)
    print(
        """
Konzept:
- Berechne Bollinger-ähnliche Bänder (MA ± k*Std)
- Long wenn Preis unter unterem Band (überverkauft)
- Short wenn Preis über oberem Band (überkauft)
- Exit bei Rückkehr zum Mean oder Kanal

Ideal für: Seitwärtsmärkte (Ranging Markets)
"""
    )

    # Default-Parameter
    strategy = MeanReversionChannelStrategy(
        window=20,
        num_std=2.0,
        exit_at_mean=True,
    )
    signals = strategy.generate_signals(df)
    print_strategy_stats("Mean Rev Channel (default)", df, signals)

    # Engere Bänder
    strategy_tight = MeanReversionChannelStrategy(
        window=15,
        num_std=1.5,
        exit_at_mean=False,
    )
    signals_tight = strategy_tight.generate_signals(df)
    print_strategy_stats("Mean Rev Channel (tight)", df, signals_tight)


def demo_rsi_reversion(df: pd.DataFrame) -> None:
    """Demo: RSI Reversion Strategy (Phase 27 erweitert)."""
    print("\n" + "=" * 70)
    print("3. RSI REVERSION STRATEGY (Phase 27 Enhanced)")
    print("=" * 70)
    print(
        """
Konzept:
- RSI < lower → Long (überverkauft, erwarte Reversion nach oben)
- RSI > upper → Short (überkauft, erwarte Reversion nach unten)
- Exit wenn RSI in neutralen Bereich zurückkehrt

Neue Features (Phase 27):
- Wilder-Smoothing für stabilere RSI-Berechnung
- Optionaler Trendfilter (nur Long wenn Preis > MA)
- Konfigurierbare Exit-Levels

Ideal für: Seitwärtsmärkte mit Übertreibungen
"""
    )

    # Default (mit Wilder-Smoothing)
    strategy = RsiReversionStrategy(
        rsi_window=14,
        lower=30.0,
        upper=70.0,
        use_wilder=True,
    )
    signals = strategy.generate_signals(df)
    print_strategy_stats("RSI Reversion (Wilder)", df, signals)

    # Ohne Wilder (einfaches Rolling)
    strategy_simple = RsiReversionStrategy(
        rsi_window=14,
        lower=30.0,
        upper=70.0,
        use_wilder=False,
    )
    signals_simple = strategy_simple.generate_signals(df)
    print_strategy_stats("RSI Reversion (Simple)", df, signals_simple)

    # Mit Trendfilter
    strategy_trend = RsiReversionStrategy(
        rsi_window=14,
        lower=30.0,
        upper=70.0,
        use_trend_filter=True,
        trend_ma_window=50,
    )
    signals_trend = strategy_trend.generate_signals(df)
    print_strategy_stats("RSI Reversion (Trend Filter)", df, signals_trend)


def main() -> None:
    """Hauptfunktion für Demo."""
    print("=" * 70)
    print("Peak_Trade Phase 27: Strategy Research Track Demo")
    print("=" * 70)
    print("\nGeneriere synthetische Daten...")

    df = create_synthetic_ohlcv(500)
    print(f"OHLCV-Daten: {len(df)} Bars von {df.index[0]} bis {df.index[-1]}")
    print(f"Preis-Range: {df['close'].min():.2f} - {df['close'].max():.2f}")

    # Demo aller Strategien
    demo_vol_breakout(df)
    demo_mean_reversion_channel(df)
    demo_rsi_reversion(df)

    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)
    print(
        """
Phase 27 Strategy Research Track implementiert:

1. VolBreakoutStrategy (vol_breakout)
   - ATR-basierte Volatility Breakouts
   - Konfigurierbar: long/short/both

2. MeanReversionChannelStrategy (mean_reversion_channel)
   - Bollinger-ähnliche Kanal-Reversion
   - Exit am Mean oder Band

3. RsiReversionStrategy (rsi_reversion) - ENHANCED
   - Wilder-Smoothing Option
   - Optionaler Trendfilter
   - Konfigurierbare Exit-Levels

Alle Strategien:
- Folgen dem BaseStrategy-Contract
- Haben from_config() Factory-Methode
- Haben Legacy-API für Backwards Compatibility
- Haben StrategyMetadata mit Regime-Tag

Config: config.toml unter [strategy.vol_breakout], [strategy.mean_reversion_channel], [strategy.rsi_reversion]

WICHTIG: Nur für Research/Backtest/Shadow - NICHT für Live-Trading!
"""
    )


if __name__ == "__main__":
    main()
