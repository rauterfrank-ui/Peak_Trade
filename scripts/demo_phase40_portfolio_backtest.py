#!/usr/bin/env python3
"""
Peak_Trade Phase 40 - Strategy Library & Portfolio Demo
========================================================

Demo-Script für die neuen Strategien aus Phase 40:
- Breakout Strategy
- Vol Regime Filter
- Composite Strategy (Multi-Strategy Portfolio)

Usage:
    python scripts/demo_phase40_portfolio_backtest.py
    python scripts/demo_phase40_portfolio_backtest.py --config config/config.toml
    python scripts/demo_phase40_portfolio_backtest.py --strategy breakout
    python scripts/demo_phase40_portfolio_backtest.py --strategy composite

Outputs:
    - Console-Output mit Backtest-Ergebnissen
    - Optional: Markdown-Report in reports/
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

# Project imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.peak_config import load_config, PeakConfig
from src.backtest.engine import BacktestEngine
from src.backtest.stats import compute_basic_stats
from src.strategies import load_strategy
from src.strategies.registry import get_strategy_spec

BREAKOUT_STRATEGY_KEY = "breakout"
VOL_REGIME_FILTER_STRATEGY_KEY = "vol_regime_filter"
COMPOSITE_STRATEGY_KEY = "composite"
RSI_REVERSION_STRATEGY_KEY = "rsi_reversion"
MA_CROSSOVER_STRATEGY_KEY = "ma_crossover"

BREAKOUT_PARAMS: Dict[str, Any] = {
    "lookback_breakout": 20,
    "stop_loss_pct": 0.03,
    "take_profit_pct": 0.06,
    "side": "both",
}

RSI_VOL_RSI_PARAMS: Dict[str, Any] = {
    "rsi_window": 14,
    "lower": 30.0,
    "upper": 70.0,
}

RSI_VOL_FILTER_PARAMS: Dict[str, Any] = {
    "vol_window": 14,
    "vol_percentile_low": 25,
    "vol_percentile_high": 75,
}

COMPOSITE_RSI_CONFIG: Dict[str, Any] = {
    "rsi_window": 14,
    "lower": 30,
    "upper": 70,
}

COMPOSITE_BREAKOUT_CONFIG: Dict[str, Any] = {
    "lookback_breakout": 20,
    "stop_loss_pct": 0.02,
}

COMPOSITE_MA_CONFIG: Dict[str, Any] = {
    "fast_window": 20,
    "slow_window": 50,
}

COMPOSITE_WEIGHTS = (0.4, 0.3, 0.3)
COMPOSITE_AGGREGATION = "weighted"
COMPOSITE_SIGNAL_THRESHOLD = 0.3

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA GENERATION (Synthetisch für Demo)
# ============================================================================


def generate_demo_data(
    n_bars: int = 500,
    seed: int = 42,
    include_trends: bool = True,
) -> pd.DataFrame:
    """
    Generiert synthetische OHLCV-Daten für Demo-Zwecke.

    Args:
        n_bars: Anzahl Bars
        seed: Random Seed für Reproduzierbarkeit
        include_trends: Wenn True, werden Trendphasen eingebaut

    Returns:
        DataFrame mit OHLCV-Daten
    """
    np.random.seed(seed)

    idx = pd.date_range("2024-01-01", periods=n_bars, freq="1h", tz="UTC")

    # Basis-Preisbewegung
    if include_trends:
        # Verschiedene Phasen: Trend, Seitwärts, Reversal
        phase1 = np.linspace(50000, 55000, n_bars // 4)  # Aufwärtstrend
        phase2 = 55000 + np.sin(np.linspace(0, 6 * np.pi, n_bars // 4)) * 1000  # Seitwärts
        phase3 = np.linspace(55000, 48000, n_bars // 4)  # Abwärtstrend
        phase4 = 48000 + np.cumsum(np.random.randn(n_bars - 3 * (n_bars // 4)) * 50)

        base = np.concatenate([phase1, phase2, phase3, phase4])
    else:
        base = 50000 + np.cumsum(np.random.randn(n_bars) * 100)

    # Noise hinzufügen
    noise = np.random.randn(n_bars) * 50
    close = base + noise

    df = pd.DataFrame(index=idx)
    df["close"] = close
    df["open"] = df["close"].shift(1).fillna(50000)
    df["high"] = df[["open", "close"]].max(axis=1) * (1 + np.abs(np.random.randn(n_bars)) * 0.003)
    df["low"] = df[["open", "close"]].min(axis=1) * (1 - np.abs(np.random.randn(n_bars)) * 0.003)
    df["volume"] = np.random.uniform(100, 500, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


def _apply_vol_regime_filter(
    data: pd.DataFrame,
    signals: pd.Series,
    vol_filter_fn,
    vol_params: Dict[str, Any],
) -> pd.Series:
    """Wendet Vol-Regime-Filter auf Trading-Signale an (äquivalent zu apply_to_signals)."""
    filter_mask = vol_filter_fn(data, vol_params)
    aligned_filter = filter_mask.reindex(signals.index, fill_value=0)
    return signals * aligned_filter


# ============================================================================
# BACKTEST RUNNERS
# ============================================================================


def run_breakout_backtest(
    df: pd.DataFrame,
    config: Optional[PeakConfig] = None,
) -> Dict[str, Any]:
    """
    Führt Backtest mit Breakout-Strategie durch.

    Args:
        df: OHLCV-DataFrame
        config: Optional PeakConfig

    Returns:
        Dict mit Backtest-Ergebnissen
    """
    logger.info("=" * 60)
    logger.info("BREAKOUT STRATEGY BACKTEST")
    logger.info("=" * 60)

    breakout_fn = load_strategy(BREAKOUT_STRATEGY_KEY)
    breakout_spec = get_strategy_spec(BREAKOUT_STRATEGY_KEY)

    logger.info(f"Strategie: {breakout_spec.description}")
    logger.info(
        "Parameter: lookback=%s, SL=%s, TP=%s",
        BREAKOUT_PARAMS["lookback_breakout"],
        BREAKOUT_PARAMS["stop_loss_pct"],
        BREAKOUT_PARAMS["take_profit_pct"],
    )

    # Backtest Engine (ohne ExecutionPipeline für einfacheren Demo-Modus)
    engine = BacktestEngine(use_execution_pipeline=False)

    def signal_fn(data: pd.DataFrame, params: Dict) -> pd.Series:
        return breakout_fn(data, BREAKOUT_PARAMS)

    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=signal_fn,
        strategy_params={},
    )

    # Ergebnisse ausgeben
    _print_backtest_results(result.stats, "Breakout Strategy")

    return {
        "strategy": "breakout",
        "stats": result.stats,
        "equity_curve": result.equity_curve,
        "trades": result.trades,
    }


def run_rsi_with_vol_filter_backtest(
    df: pd.DataFrame,
    config: Optional[PeakConfig] = None,
) -> Dict[str, Any]:
    """
    Führt Backtest mit RSI-Reversion und Vol-Regime-Filter durch.

    Args:
        df: OHLCV-DataFrame
        config: Optional PeakConfig

    Returns:
        Dict mit Backtest-Ergebnissen
    """
    logger.info("=" * 60)
    logger.info("RSI REVERSION + VOL REGIME FILTER BACKTEST")
    logger.info("=" * 60)

    rsi_fn = load_strategy(RSI_REVERSION_STRATEGY_KEY)
    vol_filter_fn = load_strategy(VOL_REGIME_FILTER_STRATEGY_KEY)
    rsi_spec = get_strategy_spec(RSI_REVERSION_STRATEGY_KEY)
    vol_spec = get_strategy_spec(VOL_REGIME_FILTER_STRATEGY_KEY)

    logger.info(f"Trading-Strategie: {rsi_spec.description}")
    logger.info(f"Filter: {vol_spec.description}")

    # Signale generieren und filtern
    raw_signals = rsi_fn(df, RSI_VOL_RSI_PARAMS)
    filtered_signals = _apply_vol_regime_filter(
        df, raw_signals, vol_filter_fn, RSI_VOL_FILTER_PARAMS
    )

    # Statistiken
    raw_trades = (raw_signals != 0).sum()
    filtered_trades = (filtered_signals != 0).sum()
    blocked_ratio = 1 - (filtered_trades / raw_trades) if raw_trades > 0 else 0

    logger.info(f"Raw Signals (non-zero): {raw_trades}")
    logger.info(f"Filtered Signals (non-zero): {filtered_trades}")
    logger.info(f"Blockiert durch Filter: {blocked_ratio:.1%}")

    # Backtest mit gefilterten Signalen
    engine = BacktestEngine(use_execution_pipeline=False)

    def signal_fn(data: pd.DataFrame, params: Dict) -> pd.Series:
        raw = rsi_fn(data, RSI_VOL_RSI_PARAMS)
        return _apply_vol_regime_filter(data, raw, vol_filter_fn, RSI_VOL_FILTER_PARAMS)

    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=signal_fn,
        strategy_params={},
    )

    _print_backtest_results(result.stats, "RSI + Vol Filter")

    return {
        "strategy": "rsi_with_vol_filter",
        "stats": result.stats,
        "equity_curve": result.equity_curve,
        "blocked_ratio": blocked_ratio,
    }


def run_composite_backtest(
    df: pd.DataFrame,
    config: Optional[PeakConfig] = None,
) -> Dict[str, Any]:
    """
    Führt Backtest mit Composite-Strategie durch.

    Args:
        df: OHLCV-DataFrame
        config: Optional PeakConfig

    Returns:
        Dict mit Backtest-Ergebnissen
    """
    logger.info("=" * 60)
    logger.info("COMPOSITE STRATEGY BACKTEST (Portfolio)")
    logger.info("=" * 60)

    rsi_fn = load_strategy(RSI_REVERSION_STRATEGY_KEY)
    breakout_fn = load_strategy(BREAKOUT_STRATEGY_KEY)
    ma_fn = load_strategy(MA_CROSSOVER_STRATEGY_KEY)
    composite_fn = load_strategy(COMPOSITE_STRATEGY_KEY)

    rsi_strategy = get_strategy_spec(RSI_REVERSION_STRATEGY_KEY).cls(config=COMPOSITE_RSI_CONFIG)
    breakout_strategy = get_strategy_spec(BREAKOUT_STRATEGY_KEY).cls(
        config=COMPOSITE_BREAKOUT_CONFIG
    )
    ma_strategy = get_strategy_spec(MA_CROSSOVER_STRATEGY_KEY).cls(config=COMPOSITE_MA_CONFIG)
    composite_params: Dict[str, Any] = {
        "strategies": [
            (rsi_strategy, COMPOSITE_WEIGHTS[0]),
            (breakout_strategy, COMPOSITE_WEIGHTS[1]),
            (ma_strategy, COMPOSITE_WEIGHTS[2]),
        ],
        "aggregation": COMPOSITE_AGGREGATION,
        "signal_threshold": COMPOSITE_SIGNAL_THRESHOLD,
    }
    composite_spec = get_strategy_spec(COMPOSITE_STRATEGY_KEY)

    logger.info(f"Strategie: {composite_spec.description}")
    logger.info("Komponenten: RSI (40%), Breakout (30%), MA Crossover (30%)")
    logger.info(
        "Aggregation: %s, Threshold: %s",
        COMPOSITE_AGGREGATION,
        COMPOSITE_SIGNAL_THRESHOLD,
    )

    # Komponenten-Signale für Analyse
    ma_signal_params = {
        "fast_period": COMPOSITE_MA_CONFIG["fast_window"],
        "slow_period": COMPOSITE_MA_CONFIG["slow_window"],
    }
    component_signals = {
        rsi_strategy.key: rsi_fn(df, COMPOSITE_RSI_CONFIG),
        breakout_strategy.key: breakout_fn(df, COMPOSITE_BREAKOUT_CONFIG),
        ma_strategy.key: ma_fn(df, ma_signal_params),
    }

    logger.info("\nKomponenten-Signal-Verteilung:")
    for name, comp_signals in component_signals.items():
        long_pct = (comp_signals == 1).mean() * 100
        short_pct = (comp_signals == -1).mean() * 100
        flat_pct = (comp_signals == 0).mean() * 100
        logger.info(f"  {name}: Long={long_pct:.1f}%, Short={short_pct:.1f}%, Flat={flat_pct:.1f}%")

    # Backtest
    engine = BacktestEngine(use_execution_pipeline=False)

    def signal_fn(data: pd.DataFrame, params: Dict) -> pd.Series:
        return composite_fn(data, composite_params)

    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=signal_fn,
        strategy_params={},
    )

    _print_backtest_results(result.stats, "Composite Portfolio")

    return {
        "strategy": "composite",
        "stats": result.stats,
        "equity_curve": result.equity_curve,
        "component_signals": {name: sig.tolist() for name, sig in component_signals.items()},
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _print_backtest_results(stats: Dict[str, Any], strategy_name: str) -> None:
    """Gibt Backtest-Ergebnisse formatiert aus."""
    print("\n" + "-" * 50)
    print(f"  ERGEBNISSE: {strategy_name}")
    print("-" * 50)
    print(f"  Total Return:    {stats.get('total_return', 0):.2%}")
    print(f"  Sharpe Ratio:    {stats.get('sharpe', 0):.2f}")
    print(f"  Max Drawdown:    {stats.get('max_drawdown', 0):.2%}")
    print(f"  Total Trades:    {stats.get('total_trades', 0)}")
    print(f"  Win Rate:        {stats.get('win_rate', 0):.1%}")
    print(f"  Profit Factor:   {stats.get('profit_factor', 0):.2f}")
    if "blocked_trades" in stats:
        print(f"  Blocked Trades:  {stats['blocked_trades']}")
    print("-" * 50 + "\n")


def generate_markdown_report(
    results: list[Dict[str, Any]],
    output_path: Path,
) -> None:
    """
    Generiert einen Markdown-Report aus den Backtest-Ergebnissen.

    Args:
        results: Liste von Backtest-Ergebnissen
        output_path: Pfad für den Report
    """
    lines = [
        "# Peak_Trade Phase 40 - Strategy Library Demo Report",
        f"\nGeneriert: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "\n## Zusammenfassung\n",
        "| Strategie | Return | Sharpe | Max DD | Trades | Win Rate |",
        "|-----------|--------|--------|--------|--------|----------|",
    ]

    for r in results:
        stats = r["stats"]
        lines.append(
            f"| {r['strategy']} | "
            f"{stats.get('total_return', 0):.2%} | "
            f"{stats.get('sharpe', 0):.2f} | "
            f"{stats.get('max_drawdown', 0):.2%} | "
            f"{stats.get('total_trades', 0)} | "
            f"{stats.get('win_rate', 0):.1%} |"
        )

    lines.extend(
        [
            "\n## Strategien\n",
            "### Breakout Strategy",
            "- Trend-Following basierend auf N-Bar High/Low Breakouts",
            "- Stop-Loss und Take-Profit integriert",
            "- Geeignet für trending markets\n",
            "### RSI + Vol Filter",
            "- Mean-Reversion basierend auf RSI",
            "- Vol-Regime-Filter blockiert Trades bei extremer Volatilität",
            "- Kombination von Trading-Strategie und Filter\n",
            "### Composite (Portfolio)",
            "- Kombiniert RSI, Breakout und MA Crossover",
            "- Weighted Aggregation der Signale",
            "- Diversifikation über mehrere Strategien\n",
        ]
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines))
    logger.info(f"Report geschrieben: {output_path}")


# ============================================================================
# MAIN
# ============================================================================


def main() -> None:
    """Hauptfunktion."""
    parser = argparse.ArgumentParser(description="Peak_Trade Phase 40 - Strategy Library Demo")
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Config-Datei",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["breakout", "rsi_vol_filter", "composite", "all"],
        default="all",
        help="Welche Strategie(n) testen",
    )
    parser.add_argument(
        "--bars",
        type=int,
        default=500,
        help="Anzahl Bars für synthetische Daten",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random Seed",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=None,
        help="Pfad für Markdown-Report (optional)",
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  PEAK_TRADE PHASE 40 - STRATEGY LIBRARY DEMO")
    print("=" * 60 + "\n")

    # Config laden (optional)
    config = None
    try:
        config = load_config(args.config)
        logger.info(f"Config geladen: {args.config}")
    except FileNotFoundError:
        logger.warning(f"Config nicht gefunden: {args.config}, nutze Defaults")

    # Demo-Daten generieren
    logger.info(f"Generiere {args.bars} Bars synthetische Daten (Seed: {args.seed})")
    df = generate_demo_data(n_bars=args.bars, seed=args.seed)

    print(f"\nDaten: {len(df)} Bars")
    print(f"Zeitraum: {df.index[0]} bis {df.index[-1]}")
    print(f"Preis-Range: {df['close'].min():.2f} - {df['close'].max():.2f}\n")

    # Backtests ausführen
    results = []

    if args.strategy in ("breakout", "all"):
        result = run_breakout_backtest(df, config)
        results.append(result)

    if args.strategy in ("rsi_vol_filter", "all"):
        result = run_rsi_with_vol_filter_backtest(df, config)
        results.append(result)

    if args.strategy in ("composite", "all"):
        result = run_composite_backtest(df, config)
        results.append(result)

    # Report generieren (optional)
    if args.report:
        generate_markdown_report(results, Path(args.report))
    elif args.strategy == "all":
        # Default Report-Pfad
        report_path = Path("reports/phase40_demo_report.md")
        generate_markdown_report(results, report_path)

    print("\n" + "=" * 60)
    print("  DEMO ABGESCHLOSSEN")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
