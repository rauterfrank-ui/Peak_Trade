#!/usr/bin/env python3
# scripts/demo_regime_switching.py
"""
Peak_Trade Regime Detection & Strategy Switching Demo (Phase 28)
=================================================================

Dieses Script demonstriert den Regime-Layer fuer marktphasenbasiertes
Strategy Switching im Research/Backtest-Kontext.

Features:
- Regime Detection (breakout, ranging, trending, unknown)
- Strategy Switching basierend auf Regime
- Vergleich: Mit vs. Ohne Regime-Layer
- Regime-Statistiken und Visualisierung

Usage:
    # Mit Regime-Layer (aktiviert Regime Detection + Strategy Switching)
    python scripts/demo_regime_switching.py --use-regime-layer

    # Ohne Regime-Layer (klassischer Single-Strategy-Backtest)
    python scripts/demo_regime_switching.py --no-regime-layer

    # Mit spezifischem Symbol
    python scripts/demo_regime_switching.py --use-regime-layer --symbol BTC/EUR

WICHTIG: Nur fuer Research/Backtest/Shadow, NICHT fuer Live-Trading!
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd

# Projekt-Root zum Path hinzufuegen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.peak_config import load_config, PeakConfig
from src.regime import (
    RegimeDetectorConfig,
    StrategySwitchingConfig,
    make_regime_detector,
    make_switching_policy,
    StrategySwitchDecision,
)
from src.strategies import STRATEGY_REGISTRY

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ============================================================================
# SYNTHETIC DATA GENERATION
# ============================================================================

def generate_synthetic_market_data(
    n_bars: int = 500,
    base_price: float = 50000.0,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generiert synthetische Marktdaten mit verschiedenen Marktphasen.

    Phasen:
    - Phase 1: Ranging (niedrige Vol, seitwaerts)
    - Phase 2: Breakout (hohe Vol, starke Moves)
    - Phase 3: Trending (mittlere Vol, klarer Trend)
    - Phase 4: Ranging wieder

    Args:
        n_bars: Anzahl der Bars
        base_price: Startpreis
        seed: Random Seed fuer Reproduzierbarkeit

    Returns:
        OHLCV-DataFrame mit DatetimeIndex
    """
    np.random.seed(seed)

    dates = pd.date_range(start="2024-01-01", periods=n_bars, freq="1h")

    prices = np.zeros(n_bars)
    prices[0] = base_price

    phase_length = n_bars // 4

    for i in range(1, n_bars):
        phase = i // phase_length

        if phase == 0:
            # Ranging: niedrige Vol, kein Trend
            prices[i] = prices[i-1] * (1 + np.random.normal(0, 0.002))
        elif phase == 1:
            # Breakout: hohe Vol, starke Moves
            prices[i] = prices[i-1] * (1 + np.random.normal(0.003, 0.025))
        elif phase == 2:
            # Trending: mittlere Vol, positiver Trend
            prices[i] = prices[i-1] * (1 + np.random.normal(0.0015, 0.01))
        else:
            # Ranging wieder
            prices[i] = prices[i-1] * (1 + np.random.normal(0, 0.003))

    # OHLCV erstellen
    high = prices * (1 + np.abs(np.random.normal(0, 0.004, n_bars)))
    low = prices * (1 - np.abs(np.random.normal(0, 0.004, n_bars)))
    open_prices = prices * (1 + np.random.normal(0, 0.002, n_bars))
    volume = np.random.randint(100, 1000, n_bars)

    # Ensure high >= close >= low
    high = np.maximum(high, prices)
    low = np.minimum(low, prices)

    df = pd.DataFrame({
        "open": open_prices,
        "high": high,
        "low": low,
        "close": prices,
        "volume": volume,
    }, index=dates)

    return df


# ============================================================================
# REGIME ANALYSIS
# ============================================================================

def analyze_regime_distribution(regimes: pd.Series) -> Dict[str, Any]:
    """
    Analysiert die Verteilung der Regime-Labels.

    Args:
        regimes: Series mit Regime-Labels

    Returns:
        Dict mit Statistiken
    """
    distribution = regimes.value_counts(normalize=True)

    # Regime-Wechsel zaehlen
    changes = (regimes != regimes.shift(1)).sum() - 1  # -1 fuer erste Bar

    # Durchschnittliche Regime-Dauer
    regime_runs = []
    current_regime = regimes.iloc[0]
    current_length = 1

    for regime in regimes.iloc[1:]:
        if regime == current_regime:
            current_length += 1
        else:
            regime_runs.append({"regime": current_regime, "length": current_length})
            current_regime = regime
            current_length = 1
    regime_runs.append({"regime": current_regime, "length": current_length})

    avg_duration = np.mean([r["length"] for r in regime_runs])

    return {
        "distribution": distribution.to_dict(),
        "total_bars": len(regimes),
        "regime_changes": int(changes),
        "avg_regime_duration": float(avg_duration),
        "num_regime_runs": len(regime_runs),
    }


def print_regime_stats(stats: Dict[str, Any]) -> None:
    """Gibt Regime-Statistiken aus."""
    print("\n" + "=" * 60)
    print("REGIME-STATISTIKEN")
    print("=" * 60)

    print(f"\nGesamt-Bars: {stats['total_bars']}")
    print(f"Regime-Wechsel: {stats['regime_changes']}")
    print(f"Anzahl Regime-Phasen: {stats['num_regime_runs']}")
    print(f"Durchschn. Regime-Dauer: {stats['avg_regime_duration']:.1f} Bars")

    print("\nRegime-Verteilung:")
    for regime, pct in stats["distribution"].items():
        bar = "█" * int(pct * 30)
        print(f"  {regime:12} {pct:6.1%} {bar}")


# ============================================================================
# STRATEGY SWITCHING SIMULATION
# ============================================================================

def simulate_switching_decisions(
    regimes: pd.Series,
    switching_config: StrategySwitchingConfig,
    available_strategies: List[str],
) -> Dict[str, Any]:
    """
    Simuliert Strategy-Switching-Entscheidungen fuer alle Bars.

    Args:
        regimes: Series mit Regime-Labels
        switching_config: Switching-Konfiguration
        available_strategies: Verfuegbare Strategien

    Returns:
        Dict mit Switching-Statistiken
    """
    policy = make_switching_policy(switching_config)
    if policy is None:
        return {"error": "Switching Policy ist deaktiviert"}

    decisions = []
    strategy_usage: Dict[str, int] = {s: 0 for s in available_strategies}

    for regime in regimes:
        decision = policy.decide(regime, available_strategies)
        decisions.append(decision)

        # Track strategy usage
        primary = decision.primary_strategy
        if primary and primary in strategy_usage:
            strategy_usage[primary] += 1

    # Strategy-Wechsel zaehlen
    prev_primary = None
    strategy_switches = 0
    for d in decisions:
        if prev_primary is not None and d.primary_strategy != prev_primary:
            strategy_switches += 1
        prev_primary = d.primary_strategy

    return {
        "total_decisions": len(decisions),
        "strategy_switches": strategy_switches,
        "strategy_usage": strategy_usage,
        "unique_strategies_used": len([s for s, c in strategy_usage.items() if c > 0]),
    }


def print_switching_stats(stats: Dict[str, Any]) -> None:
    """Gibt Switching-Statistiken aus."""
    print("\n" + "=" * 60)
    print("STRATEGY-SWITCHING-STATISTIKEN")
    print("=" * 60)

    if "error" in stats:
        print(f"\n  {stats['error']}")
        return

    print(f"\nGesamt-Entscheidungen: {stats['total_decisions']}")
    print(f"Strategy-Wechsel: {stats['strategy_switches']}")
    print(f"Verwendete Strategien: {stats['unique_strategies_used']}")

    print("\nStrategy-Nutzung:")
    total = sum(stats["strategy_usage"].values())
    for strategy, count in sorted(stats["strategy_usage"].items(), key=lambda x: -x[1]):
        if count > 0:
            pct = count / total if total > 0 else 0
            bar = "█" * int(pct * 30)
            print(f"  {strategy:25} {count:5} ({pct:5.1%}) {bar}")


# ============================================================================
# MAIN DEMO
# ============================================================================

def run_demo(
    use_regime_layer: bool = True,
    symbol: str = "BTC/EUR",
    n_bars: int = 500,
) -> None:
    """
    Fuehrt die Demo aus.

    Args:
        use_regime_layer: Ob Regime Detection + Switching aktiviert sein soll
        symbol: Trading-Symbol (fuer Anzeige)
        n_bars: Anzahl der Bars
    """
    print("\n" + "=" * 60)
    print("PEAK_TRADE REGIME DETECTION & STRATEGY SWITCHING DEMO")
    print("Phase 28 - Research/Backtest/Shadow Only")
    print("=" * 60)

    print(f"\nSymbol: {symbol}")
    print(f"Bars: {n_bars}")
    print(f"Regime-Layer: {'AKTIVIERT' if use_regime_layer else 'DEAKTIVIERT'}")

    # 1. Daten generieren
    print("\n[1/4] Generiere synthetische Marktdaten...")
    df = generate_synthetic_market_data(n_bars=n_bars)
    print(f"      Zeitraum: {df.index[0]} bis {df.index[-1]}")
    print(f"      Preis-Range: {df['close'].min():.2f} - {df['close'].max():.2f}")

    # 2. Regime Detection
    print("\n[2/4] Regime Detection...")

    detector_config = RegimeDetectorConfig(
        enabled=use_regime_layer,
        detector_name="volatility_breakout",
        lookback_window=50,
        min_history_bars=50,
        vol_window=20,
        vol_percentile_breakout=0.75,
        vol_percentile_ranging=0.30,
    )

    detector = make_regime_detector(detector_config)

    if detector is None:
        print("      Regime Detection ist deaktiviert.")
        regimes = pd.Series("unknown", index=df.index)
    else:
        regimes = detector.detect_regimes(df)
        print(f"      Detector: {detector_config.detector_name}")

    # Regime-Statistiken
    regime_stats = analyze_regime_distribution(regimes)
    print_regime_stats(regime_stats)

    # 3. Strategy Switching
    print("\n[3/4] Strategy Switching Simulation...")

    switching_config = StrategySwitchingConfig(
        enabled=use_regime_layer,
        policy_name="simple_regime_mapping",
        regime_to_strategies={
            "breakout": ["vol_breakout"],
            "ranging": ["mean_reversion_channel", "rsi_reversion"],
            "trending": ["trend_following"],
            "unknown": ["ma_crossover"],
        },
        regime_to_weights={
            "ranging": {"mean_reversion_channel": 0.6, "rsi_reversion": 0.4},
        },
        default_strategies=["ma_crossover"],
    )

    available_strategies = list(STRATEGY_REGISTRY.keys())
    switching_stats = simulate_switching_decisions(
        regimes, switching_config, available_strategies
    )
    print_switching_stats(switching_stats)

    # 4. Zusammenfassung
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)

    if use_regime_layer:
        print("""
Mit aktiviertem Regime-Layer:
- Der Detector erkennt Marktphasen basierend auf Volatilitaet
- Die Switching-Policy waehlt passende Strategien je Regime:
  * breakout -> vol_breakout (fuer Range-Ausbrueche)
  * ranging  -> mean_reversion_channel, rsi_reversion (Mean-Reversion)
  * trending -> trend_following (Trend-Following)
  * unknown  -> ma_crossover (Fallback)

Vorteile:
- Strategien werden nur in passenden Marktphasen eingesetzt
- Reduziert False Signals in ungeeigneten Phasen
- Ermooglicht Multi-Strategy-Portfolios mit intelligenter Rotation
""")
    else:
        print("""
Ohne Regime-Layer (klassischer Modus):
- Alle Strategien werden unabhaengig von der Marktphase verwendet
- Keine automatische Strategy-Rotation
- Bisheriges Verhalten bleibt erhalten (enabled=false in config.toml)
""")

    print("=" * 60)
    print("Demo abgeschlossen!")
    print("=" * 60)


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main() -> None:
    """CLI Entry Point."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Regime Detection & Strategy Switching Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Mit Regime-Layer aktiviert
  python scripts/demo_regime_switching.py --use-regime-layer

  # Ohne Regime-Layer (klassisch)
  python scripts/demo_regime_switching.py --no-regime-layer

  # Mit mehr Bars
  python scripts/demo_regime_switching.py --use-regime-layer --bars 1000
""",
    )

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--use-regime-layer",
        action="store_true",
        help="Aktiviert Regime Detection und Strategy Switching",
    )
    mode_group.add_argument(
        "--no-regime-layer",
        action="store_true",
        help="Deaktiviert Regime-Layer (klassischer Modus)",
    )

    parser.add_argument(
        "--symbol",
        type=str,
        default="BTC/EUR",
        help="Trading-Symbol (nur fuer Anzeige, Default: BTC/EUR)",
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=500,
        help="Anzahl der synthetischen Bars (Default: 500)",
    )

    args = parser.parse_args()

    run_demo(
        use_regime_layer=args.use_regime_layer,
        symbol=args.symbol,
        n_bars=args.bars,
    )


if __name__ == "__main__":
    main()
