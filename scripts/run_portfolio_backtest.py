#!/usr/bin/env python3
"""
Peak_Trade Portfolio Backtest
==============================
Führt Multi-Asset-Portfolio-Backtests mit individuellen Strategien pro Symbol aus.

Features:
- Multi-Asset: Mehrere Symbole mit eigenen Strategien
- Capital Allocation: Equal-Weight, Risk Parity, Sharpe-Weighted, Manual
- Portfolio-Level Risk Management
- Aggregierte Portfolio-Metriken & Regime-Analyse
- Korrelations-Matrix & Asset-Performance-Breakdown

Usage:
    python scripts/run_portfolio_backtest.py
    python scripts/run_portfolio_backtest.py --bars 500
    python scripts/run_portfolio_backtest.py --allocation risk_parity
"""

import sys
import argparse
from pathlib import Path

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple

from src.core.peak_config import load_config
from src.core.position_sizing import build_position_sizer_from_config
from src.core.risk import build_risk_manager_from_config
from src.core.experiments import (
    log_portfolio_backtest_result,
    log_backtest_result,
    RUN_TYPE_PORTFOLIO_BACKTEST,
)
from src.strategies.registry import create_strategy_from_config
from src.backtest.engine import BacktestEngine
from src.backtest.result import BacktestResult


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Portfolio Backtest",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with config.toml settings
  python scripts/run_portfolio_backtest.py

  # Override number of bars
  python scripts/run_portfolio_backtest.py --bars 500

  # Override allocation method
  python scripts/run_portfolio_backtest.py --allocation sharpe_weighted

  # Custom run name
  python scripts/run_portfolio_backtest.py --run-name crypto_portfolio_q4
        """
    )

    parser.add_argument(
        "--bars",
        type=int,
        default=None,
        help="Number of bars per backtest (overrides config.toml)"
    )

    parser.add_argument(
        "--allocation",
        type=str,
        default=None,
        choices=["equal", "risk_parity", "sharpe_weighted", "manual"],
        help="Capital allocation method (overrides config.toml)"
    )

    parser.add_argument(
        "--run-name",
        type=str,
        default=None,
        help="Optional name for this portfolio run (for reports)"
    )

    parser.add_argument(
        "--save-individual",
        action="store_true",
        help="Save individual asset reports in addition to portfolio report"
    )

    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Optional tag for registry logging (e.g. 'weekend-research')"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run backtest but do not log to registry"
    )

    return parser.parse_args()


def load_data_for_symbol(
    symbol: str,
    n_bars: int = 200,
    start_time: datetime = None
) -> pd.DataFrame:
    """
    Lädt Daten für ein bestimmtes Symbol.

    Aktuell: Dummy-Daten mit symbol-spezifischem Seed.
    TODO: Später mit echten Kraken-Daten ersetzen.

    Args:
        symbol: Trading-Pair (z.B. "BTC/EUR")
        n_bars: Anzahl Bars
        start_time: Optional fester Start-Zeitpunkt (für Portfolio-Sync)

    Returns:
        DataFrame mit OHLCV-Daten
    """
    # Symbol-spezifischer Seed für reproduzierbare aber unterschiedliche Daten
    seed = hash(symbol) % (2**32)
    np.random.seed(seed)

    # Start-Zeitpunkt (fixiert für alle Symbole im Portfolio)
    if start_time is None:
        start = datetime.now() - timedelta(hours=n_bars)
    else:
        start = start_time
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


def run_single_asset_backtest(
    symbol: str,
    strategy_key: str,
    cfg: Any,
    n_bars: int = 200,
    start_time: datetime = None,
    verbose: bool = False
) -> BacktestResult:
    """
    Führt Backtest für ein einzelnes Asset aus.

    Args:
        symbol: Trading-Pair
        strategy_key: Strategie-Key aus Registry
        cfg: Config-Objekt
        n_bars: Anzahl Bars
        start_time: Fester Start-Zeitpunkt (für Portfolio-Sync)
        verbose: Detaillierte Ausgabe

    Returns:
        BacktestResult
    """
    if verbose:
        print(f"\n  🔍 Backteste {symbol} mit {strategy_key}...")

    # Daten laden
    df = load_data_for_symbol(symbol, n_bars=n_bars, start_time=start_time)

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

    if verbose:
        print(f"    ✅ Return: {result.stats.get('total_return', 0.0):>7.2%} | "
              f"Sharpe: {result.stats.get('sharpe', 0.0):>6.2f}")

    return result


def calculate_portfolio_weights(
    results: Dict[str, BacktestResult],
    method: str,
    config_weights: Dict[str, float] = None
) -> Dict[str, float]:
    """
    Berechnet Portfolio-Gewichte basierend auf Allocation-Methode.

    Args:
        results: Dict von symbol -> BacktestResult
        method: "equal", "risk_parity", "sharpe_weighted", "manual"
        config_weights: Config-definierte Gewichte (für manual/fallback)

    Returns:
        Dict von symbol -> weight (summiert zu 1.0)
    """
    symbols = list(results.keys())
    n = len(symbols)

    if method == "equal":
        weight = 1.0 / n
        return {sym: weight for sym in symbols}

    elif method == "risk_parity":
        # Inverse Volatilität
        vols = {}
        for sym, res in results.items():
            # Annualisierte Volatilität aus equity curve
            returns = res.equity_curve.pct_change().dropna()
            if len(returns) > 0:
                vol = returns.std() * np.sqrt(252 * 24)  # Hourly -> annualized
            else:
                vol = 1.0
            vols[sym] = max(vol, 1e-6)  # Avoid division by zero

        inv_vols = {sym: 1.0 / v for sym, v in vols.items()}
        total = sum(inv_vols.values())
        return {sym: iv / total for sym, iv in inv_vols.items()}

    elif method == "sharpe_weighted":
        # Gewichte proportional zu Sharpe Ratio
        sharpes = {}
        for sym, res in results.items():
            sharpe = res.stats.get("sharpe", 0.0)
            sharpes[sym] = max(sharpe, 0.0)  # Nur positive Sharpes verwenden

        total = sum(sharpes.values())
        if total > 0:
            return {sym: s / total for sym, s in sharpes.items()}
        else:
            # Fallback auf equal
            weight = 1.0 / n
            return {sym: weight for sym in symbols}

    elif method == "manual":
        # Verwende config_weights oder fallback auf equal
        if config_weights:
            # Normalisieren
            total = sum(config_weights.get(sym, 0.0) for sym in symbols)
            if total > 0:
                return {sym: config_weights.get(sym, 0.0) / total for sym in symbols}

        # Fallback
        weight = 1.0 / n
        return {sym: weight for sym in symbols}

    else:
        raise ValueError(f"Unbekannte Allocation-Methode: {method}")


def aggregate_portfolio_equity(
    results: Dict[str, BacktestResult],
    weights: Dict[str, float],
    initial_capital: float
) -> pd.Series:
    """
    Aggregiert Equity-Curves zu Portfolio-Equity.

    Args:
        results: Dict von symbol -> BacktestResult
        weights: Dict von symbol -> weight (summiert zu 1.0)
        initial_capital: Anfangskapital des Portfolios

    Returns:
        Portfolio-Equity als pd.Series
    """
    # Alle Equity-Curves normalisieren und Duplikate entfernen
    equities = {}

    for sym, res in results.items():
        eq = res.equity_curve

        # Duplikate im Index entfernen (keep first)
        if eq.index.has_duplicates:
            eq = eq[~eq.index.duplicated(keep='first')]

        # Normalisieren auf initial_capital * weight
        eq_normalized = eq * (initial_capital * weights[sym] / eq.iloc[0])
        equities[sym] = eq_normalized

    # Als DataFrame kombinieren (automatisches Alignment)
    df_eq = pd.DataFrame(equities)

    # Portfolio-Equity = Summe über Assets
    portfolio_eq = df_eq.sum(axis=1)

    return portfolio_eq


def calculate_portfolio_stats(
    portfolio_equity: pd.Series,
    initial_capital: float
) -> Dict[str, Any]:
    """
    Berechnet Portfolio-Stats aus aggregierter Equity.

    Args:
        portfolio_equity: Portfolio-Equity-Curve
        initial_capital: Anfangskapital

    Returns:
        Dict mit Stats
    """
    final_equity = portfolio_equity.iloc[-1]
    total_return = (final_equity / initial_capital) - 1.0

    # Returns
    returns = portfolio_equity.pct_change().dropna()

    # Sharpe
    if len(returns) > 0 and returns.std() > 0:
        sharpe = returns.mean() / returns.std() * np.sqrt(252 * 24)  # Annualized
    else:
        sharpe = 0.0

    # Drawdown
    rolling_max = portfolio_equity.expanding().max()
    drawdown = (portfolio_equity - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    # CAGR (approximiert)
    n_bars = len(portfolio_equity)
    years = n_bars / (252 * 24)  # Hourly bars
    if years > 0:
        cagr = (final_equity / initial_capital) ** (1 / years) - 1.0
    else:
        cagr = 0.0

    return {
        "total_return": total_return,
        "cagr": cagr,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "final_equity": final_equity,
        "initial_capital": initial_capital,
    }


def aggregate_regime_distribution(
    results: Dict[str, BacktestResult],
    weights: Dict[str, float]
) -> Dict[str, float]:
    """
    Berechnet gewichtete Regime-Verteilung des Portfolios.

    Args:
        results: Dict von symbol -> BacktestResult
        weights: Dict von symbol -> weight

    Returns:
        Dict von regime -> gewichtete Fraktion
    """
    # Alle Regime-Keys sammeln
    all_regimes = set()
    for res in results.values():
        regime_dist = res.metadata.get("regime_distribution", {})
        all_regimes.update(regime_dist.keys())

    # Gewichtete Summe berechnen
    weighted_regime = {}
    for regime in all_regimes:
        total = 0.0
        for sym, res in results.items():
            regime_dist = res.metadata.get("regime_distribution", {})
            frac = regime_dist.get(regime, 0.0)
            total += frac * weights[sym]
        weighted_regime[regime] = total

    return weighted_regime


def print_portfolio_summary(
    portfolio_stats: Dict[str, Any],
    weights: Dict[str, float],
    asset_stats: Dict[str, Dict[str, Any]],
    regime_dist: Dict[str, float]
):
    """Druckt formatierte Portfolio-Zusammenfassung."""
    print("\n" + "="*90)
    print("PORTFOLIO BACKTEST SUMMARY")
    print("="*90)

    # Portfolio-Level Stats
    print("\n📊 Portfolio Performance:")
    print(f"  Total Return:    {portfolio_stats['total_return']:>8.2%}")
    print(f"  CAGR:            {portfolio_stats['cagr']:>8.2%}")
    print(f"  Sharpe Ratio:    {portfolio_stats['sharpe']:>8.2f}")
    print(f"  Max Drawdown:    {portfolio_stats['max_drawdown']:>8.2%}")
    print(f"  Final Equity:    {portfolio_stats['final_equity']:>12,.2f} EUR")
    print(f"  Initial Capital: {portfolio_stats['initial_capital']:>12,.2f} EUR")

    # Asset Allocation
    print("\n💼 Asset Allocation:")
    print(f"  {'Symbol':<12} {'Weight':<10} {'Return':<12} {'Sharpe':<10} {'Max DD':<10}")
    print("  " + "-"*60)
    for sym, weight in weights.items():
        stats = asset_stats[sym]
        ret = stats.get('total_return', 0.0)
        sharpe = stats.get('sharpe', 0.0)
        dd = stats.get('max_drawdown', 0.0)
        print(f"  {sym:<12} {weight:>8.1%}  {ret:>10.2%}  {sharpe:>8.2f}  {dd:>8.2%}")

    # Regime Distribution
    print("\n🌍 Portfolio Regime Distribution (weighted):")
    if regime_dist:
        sorted_regimes = sorted(regime_dist.items(), key=lambda x: x[1], reverse=True)
        for regime, frac in sorted_regimes:
            print(f"  {regime:<25} {frac:>6.1%}")
    else:
        print("  No regime data available")

    print("="*90 + "\n")


def save_portfolio_report(
    portfolio_equity: pd.Series,
    portfolio_stats: Dict[str, Any],
    weights: Dict[str, float],
    asset_stats: Dict[str, Dict[str, Any]],
    regime_dist: Dict[str, float],
    output_dir: str,
    run_name: str
):
    """
    Speichert Portfolio-Report als CSV/JSON/HTML.

    Args:
        portfolio_equity: Portfolio-Equity-Curve
        portfolio_stats: Portfolio-Stats
        weights: Asset-Gewichte
        asset_stats: Individuelle Asset-Stats
        regime_dist: Regime-Verteilung
        output_dir: Output-Verzeichnis
        run_name: Name des Runs
    """
    from pathlib import Path
    import json

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Equity Curve CSV
    eq_path = out_dir / f"{run_name}_portfolio_equity.csv"
    portfolio_equity.to_frame(name="equity").to_csv(eq_path, index=True)
    print(f"  ✅ Portfolio Equity: {eq_path}")

    # 2. Drawdown CSV
    rolling_max = portfolio_equity.expanding().max()
    drawdown = (portfolio_equity - rolling_max) / rolling_max
    dd_path = out_dir / f"{run_name}_portfolio_drawdown.csv"
    drawdown.to_frame(name="drawdown").to_csv(dd_path, index=True)
    print(f"  ✅ Portfolio Drawdown: {dd_path}")

    # 3. Stats JSON
    stats_path = out_dir / f"{run_name}_portfolio_stats.json"
    payload = {
        "portfolio_stats": portfolio_stats,
        "weights": weights,
        "asset_stats": asset_stats,
        "regime_distribution": regime_dist,
    }
    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"  ✅ Portfolio Stats: {stats_path}")

    # 4. Allocation CSV
    alloc_df = pd.DataFrame([
        {
            "symbol": sym,
            "weight": weights[sym],
            "total_return": asset_stats[sym].get("total_return", 0.0),
            "sharpe": asset_stats[sym].get("sharpe", 0.0),
            "max_drawdown": asset_stats[sym].get("max_drawdown", 0.0),
        }
        for sym in weights.keys()
    ])
    alloc_path = out_dir / f"{run_name}_allocation.csv"
    alloc_df.to_csv(alloc_path, index=False)
    print(f"  ✅ Allocation: {alloc_path}")


def main():
    """Main-Funktion."""
    args = parse_args()

    print("\n💼 Peak_Trade Portfolio Backtest")
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

    # Portfolio-Settings
    initial_capital = cfg.get("portfolio.initial_equity", 10000.0)
    symbols = cfg.get("portfolio.symbols", ["BTC/EUR", "ETH/EUR", "LTC/EUR"])
    default_strategy = cfg.get("portfolio.strategy_key", cfg.get("general.active_strategy", "ma_crossover"))
    allocation_method = args.allocation or cfg.get("portfolio.allocation_method", "equal")
    n_bars = args.bars or cfg.get("scan.scan_bars", 200)

    # Symbol-spezifische Strategien (fallback auf default)
    portfolio_strategies = cfg.get("portfolio.strategies", {}) or {}

    # Config-Gewichte für manual allocation
    config_weights_raw = cfg.get("portfolio.asset_weights", [])
    config_weights = {}
    if config_weights_raw and len(config_weights_raw) == len(symbols):
        config_weights = dict(zip(symbols, config_weights_raw))

    print(f"\n📋 Portfolio-Konfiguration:")
    print(f"  - Symbole: {', '.join(symbols)}")
    print(f"  - Initial Capital: {initial_capital:,.2f} EUR")
    print(f"  - Allocation: {allocation_method}")
    print(f"  - Bars: {n_bars}")

    # Backtests durchführen
    print(f"\n🚀 Führe Backtests für {len(symbols)} Assets aus...")
    print("-"*70)

    # Fester Start-Zeitpunkt für alle Symbole (damit gleiche Indizes)
    portfolio_start_time = datetime.now() - timedelta(hours=n_bars)

    results: Dict[str, BacktestResult] = {}
    asset_stats: Dict[str, Dict[str, Any]] = {}

    for symbol in symbols:
        # Strategie für dieses Symbol bestimmen
        strategy_key = portfolio_strategies.get(symbol, default_strategy)

        try:
            result = run_single_asset_backtest(
                symbol=symbol,
                strategy_key=str(strategy_key),
                cfg=cfg,
                n_bars=n_bars,
                start_time=portfolio_start_time,
                verbose=True
            )
            results[symbol] = result
            asset_stats[symbol] = dict(result.stats)

        except Exception as e:
            print(f"  ❌ FEHLER bei {symbol}: {e}")
            continue

    if len(results) == 0:
        print("\n❌ Keine erfolgreichen Backtests. Portfolio-Backtest abgebrochen.")
        return

    # Portfolio-Gewichte berechnen
    print(f"\n⚖️  Berechne Portfolio-Gewichte ({allocation_method})...")
    weights = calculate_portfolio_weights(results, allocation_method, config_weights)

    # Portfolio-Equity aggregieren
    print("📈 Aggregiere Portfolio-Equity...")
    portfolio_equity = aggregate_portfolio_equity(results, weights, initial_capital)

    # Portfolio-Stats berechnen
    portfolio_stats = calculate_portfolio_stats(portfolio_equity, initial_capital)

    # Regime-Verteilung aggregieren
    regime_dist = aggregate_regime_distribution(results, weights)

    # Zusammenfassung drucken
    print_portfolio_summary(portfolio_stats, weights, asset_stats, regime_dist)

    # Reports speichern
    print("💾 Speichere Portfolio-Reports...")
    run_name = args.run_name or "portfolio"
    save_portfolio_report(
        portfolio_equity=portfolio_equity,
        portfolio_stats=portfolio_stats,
        weights=weights,
        asset_stats=asset_stats,
        regime_dist=regime_dist,
        output_dir="reports",
        run_name=run_name
    )

    # Optional: Individuelle Asset-Reports
    if args.save_individual:
        print("\n💾 Speichere individuelle Asset-Reports...")
        from src.backtest.reporting import save_full_report

        for symbol, result in results.items():
            symbol_safe = symbol.replace("/", "_")
            report_name = f"{run_name}_{symbol_safe}"

            try:
                save_full_report(
                    result=result,
                    output_dir="reports",
                    run_name=report_name,
                    save_plots_flag=True,
                    save_html_flag=True,
                )
                print(f"  ✅ {symbol} Report: {report_name}_*")
            except Exception as e:
                print(f"  ⚠️  Warnung: Konnte Report für {symbol} nicht erstellen: {e}")

    # Portfolio-Run in Registry loggen
    if not args.dry_run:
        # Component-Runs für Registry vorbereiten
        component_runs = []
        for sym in weights.keys():
            component_runs.append({
                "symbol": sym,
                "strategy_key": portfolio_strategies.get(sym, default_strategy),
                "weight": weights[sym],
                "total_return": asset_stats[sym].get("total_return", 0.0),
                "sharpe": asset_stats[sym].get("sharpe", 0.0),
                "max_drawdown": asset_stats[sym].get("max_drawdown", 0.0),
            })

        portfolio_name_cfg = cfg.get("portfolio.name", "portfolio")
        run_id = log_portfolio_backtest_result(
            portfolio_name=portfolio_name_cfg,
            equity_curve=portfolio_equity,
            component_runs=component_runs,
            portfolio_stats=portfolio_stats,
            tag=args.tag,
            config_path="config.toml",
            allocation_method=allocation_method,
            extra_metadata={
                "symbols": symbols,
                "regime_distribution": regime_dist,
            },
        )
        print(f"📊 Portfolio-Experiment geloggt in Registry (run_id: {run_id[:8]}...)")
    else:
        print(f"📊 DRY-RUN: Registry-Logging übersprungen")

    print(f"\n✅ Portfolio-Backtest abgeschlossen!")
    print(f"   Portfolio Return: {portfolio_stats['total_return']:.2%}")
    print(f"   Sharpe Ratio: {portfolio_stats['sharpe']:.2f}")
    print()


if __name__ == "__main__":
    main()
