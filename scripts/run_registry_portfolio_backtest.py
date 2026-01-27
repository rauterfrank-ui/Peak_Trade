#!/usr/bin/env python3
"""
Peak_Trade - End-to-End Registry Portfolio Backtest
=====================================================
Vollständiger Backtest mit echten Marktdaten über Registry + Portfolio + Engine.

Features:
- Lädt echte Kraken-Daten über Data-Layer (mit Caching)
- Nutzt Portfolio-Config aus config.toml
- Multi-Strategie-Backtest mit Registry-Integration
- Export von Ergebnissen (CSV/JSON)
- CLI-Interface für flexible Konfiguration

Usage:
    # Einfachster Aufruf (mit Defaults)
    python scripts/run_registry_portfolio_backtest.py

    # Mit Custom-Parametern
    python scripts/run_registry_portfolio_backtest.py \
        --symbol BTC/EUR \
        --timeframe 4h \
        --limit 500 \
        --portfolio default \
        --output-dir results/portfolio_backtest

    # Nur bestimmte Strategien
    python scripts/run_registry_portfolio_backtest.py \
        --strategies ma_crossover momentum_1h

    # Regime-Filter
    python scripts/run_registry_portfolio_backtest.py \
        --regime trending

    # Dry-Run (nur Config anzeigen)
    python scripts/run_registry_portfolio_backtest.py --dry-run
"""

import sys
from pathlib import Path

# Projekt-Root zum Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse
import pandas as pd
import json
import logging
from datetime import datetime
from typing import Optional, List

from src.core.config_registry import (
    get_config,
    get_active_strategies,
    get_strategies_by_regime,
    list_strategies,
)
from src.data import fetch_kraken_data, test_kraken_connection
from src.backtest.engine import run_portfolio_from_config, PortfolioResult
from src.backtest.portfolio_resolver import resolve_portfolio_cfg
from src.backtest.stats import validate_for_live_trading


# Logging einrichten
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

ALLOWED_TIMEFRAMES = ("1m", "5m", "15m", "1h", "4h", "1d")
MAX_KRAKEN_LIMIT_BARS = 720


def _limit_bars_type(value: str) -> int:
    """argparse type: int in (1..MAX_KRAKEN_LIMIT_BARS]."""
    try:
        n = int(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"--limit muss eine ganze Zahl sein (gegeben: {value!r})"
        ) from e

    if n <= 0:
        raise argparse.ArgumentTypeError("--limit muss > 0 sein")
    if n > MAX_KRAKEN_LIMIT_BARS:
        raise argparse.ArgumentTypeError(f"--limit darf max. {MAX_KRAKEN_LIMIT_BARS} sein")
    return n


def parse_args() -> argparse.Namespace:
    """Parst CLI-Argumente."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Registry Portfolio Backtest mit echten Daten",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Standard-Backtest mit Portfolio-Default
  %(prog)s

  # BTC/EUR, 4h-Timeframe, 500 Bars
  %(prog)s --symbol BTC/EUR --timeframe 4h --limit 500

  # Nur Trending-Strategien
  %(prog)s --regime trending

  # Custom Strategie-Liste
  %(prog)s --strategies ma_crossover momentum_1h

  # Mit Export
  %(prog)s --output-dir results/my_backtest --export-trades
        """,
    )

    # === Data-Parameter ===
    data_group = parser.add_argument_group("Data-Parameter")
    data_group.add_argument(
        "--symbol",
        type=str,
        default="BTC/USD",
        help="Trading-Pair (z.B. BTC/USD, ETH/EUR) (default: BTC/USD)",
    )
    data_group.add_argument(
        "--timeframe",
        type=str,
        choices=list(ALLOWED_TIMEFRAMES),
        default="1h",
        help="Timeframe (1m, 5m, 15m, 1h, 4h, 1d) (default: 1h)",
    )
    data_group.add_argument(
        "--limit",
        type=_limit_bars_type,
        default=720,
        help="Anzahl Bars (max. 720) (default: 720)",
    )
    data_group.add_argument(
        "--no-cache",
        action="store_true",
        help="Cache deaktivieren (immer frisch von Kraken holen)",
    )

    # === Portfolio-Parameter ===
    portfolio_group = parser.add_argument_group("Portfolio-Parameter")
    portfolio_group.add_argument(
        "--portfolio",
        type=str,
        default="default",
        help="Portfolio-Name aus config.toml (default: default)",
    )
    portfolio_group.add_argument(
        "--strategies",
        nargs="+",
        type=str,
        default=None,
        help="Spezifische Strategien (überschreibt active-Liste)",
    )
    portfolio_group.add_argument(
        "--regime",
        type=str,
        choices=["trending", "ranging", "any"],
        default=None,
        help="Filtere Strategien nach Marktregime",
    )

    # === Output-Parameter ===
    output_group = parser.add_argument_group("Output-Parameter")
    output_group.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output-Verzeichnis für Ergebnisse (wenn nicht gesetzt: Default bei Export aus config.backtest.results_dir)",
    )
    output_group.add_argument(
        "--export-trades",
        action="store_true",
        help="Trades als CSV exportieren",
    )
    output_group.add_argument(
        "--export-equity",
        action="store_true",
        help="Equity-Curve als CSV exportieren",
    )
    output_group.add_argument(
        "--export-stats",
        action="store_true",
        help="Stats als JSON exportieren",
    )
    output_group.add_argument(
        "--export-all",
        action="store_true",
        help="Alle Exports aktivieren (Trades + Equity + Stats)",
    )

    # === Kontrolle ===
    control_group = parser.add_argument_group("Kontrolle")
    control_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur Config/Setup anzeigen, keinen Backtest ausführen",
    )
    control_group.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose Logging (DEBUG-Level)",
    )
    control_group.add_argument(
        "--test-connection",
        action="store_true",
        help="Nur Kraken-Verbindung testen und beenden",
    )

    return parser.parse_args()


def print_header():
    """Gibt Header aus."""
    print("\n" + "=" * 70)
    print("  Peak_Trade - Registry Portfolio Backtest")
    print("  " + "=" * 66)
    print("=" * 70 + "\n")


def print_config_summary(args: argparse.Namespace, cfg: dict):
    """Gibt Config-Zusammenfassung aus."""
    print("📋 KONFIGURATION")
    print("-" * 70)
    print(f"  Symbol:          {args.symbol}")
    print(f"  Timeframe:       {args.timeframe}")
    print(f"  Bars:            {args.limit}")
    print(f"  Cache:           {'Nein' if args.no_cache else 'Ja'}")
    print()

    # Portfolio-Info
    portfolio_cfg = resolve_portfolio_cfg(cfg, args.portfolio)
    print(f"  Portfolio:       {args.portfolio}")
    print(f"  Allocation:      {portfolio_cfg.get('allocation_method', 'N/A')}")
    print(f"  Total Capital:   ${portfolio_cfg.get('total_capital', 0):,.2f}")
    print()

    # Strategien
    if args.strategies:
        strategies = args.strategies
        source = "CLI (--strategies)"
    elif args.regime:
        strategies = get_strategies_by_regime(args.regime)
        source = f"Regime-Filter ({args.regime})"
    else:
        strategies = get_active_strategies()
        source = "config.toml (strategies.active)"

    print(f"  Strategien:      {len(strategies)} aktiv")
    print(f"  Quelle:          {source}")
    for i, name in enumerate(strategies, 1):
        print(f"    {i}. {name}")
    print()

    # Output
    if args.output_dir:
        print(f"  Output:          {args.output_dir}")
        exports = []
        if args.export_all or args.export_trades:
            exports.append("Trades")
        if args.export_all or args.export_equity:
            exports.append("Equity")
        if args.export_all or args.export_stats:
            exports.append("Stats")
        if exports:
            print(f"  Exports:         {', '.join(exports)}")
    print("-" * 70 + "\n")


def load_market_data(symbol: str, timeframe: str, limit: int, use_cache: bool) -> pd.DataFrame:
    """
    Lädt Marktdaten von Kraken.

    Args:
        symbol: Trading-Pair
        timeframe: Timeframe
        limit: Anzahl Bars
        use_cache: Cache verwenden?

    Returns:
        OHLCV-DataFrame

    Raises:
        Exception: Bei Kraken-Fehler
    """
    logger.info(f"🌐 Lade Daten von Kraken: {symbol} {timeframe} (limit={limit})")

    try:
        df = fetch_kraken_data(symbol=symbol, timeframe=timeframe, limit=limit, use_cache=use_cache)

        logger.info(f"✅ Daten geladen: {len(df)} Bars ({df.index[0]} bis {df.index[-1]})")

        # Validierung
        if len(df) < 100:
            logger.warning(f"⚠️  Nur {len(df)} Bars - zu wenig für sinnvollen Backtest!")

        return df

    except Exception as e:
        logger.error(f"❌ Fehler beim Laden der Daten: {e}")
        raise


def run_backtest(
    df: pd.DataFrame,
    args: argparse.Namespace,
    cfg: dict,
) -> PortfolioResult:
    """
    Führt Portfolio-Backtest aus.

    Args:
        df: OHLCV-DataFrame
        args: CLI-Args
        cfg: Config-Dict

    Returns:
        PortfolioResult
    """
    logger.info("🚀 Starte Portfolio-Backtest...")

    # Strategie-Filter bestimmen
    strategy_filter = args.strategies if args.strategies else None
    regime_filter = args.regime if args.regime else None

    result = run_portfolio_from_config(
        df=df,
        cfg=cfg,
        portfolio_name=args.portfolio,
        strategy_filter=strategy_filter,
        regime_filter=regime_filter,
    )

    logger.info("✅ Backtest abgeschlossen!")
    return result


def print_results(result: PortfolioResult):
    """Gibt Backtest-Ergebnisse aus."""
    print("\n" + "=" * 70)
    print("  ERGEBNISSE")
    print("=" * 70 + "\n")

    stats = result.portfolio_stats

    # Portfolio-Level Stats
    print("📊 PORTFOLIO-PERFORMANCE")
    print("-" * 70)
    print(f"  Total Return:    {stats['total_return']:>10.2%}")
    print(f"  Sharpe Ratio:    {stats['sharpe']:>10.2f}")
    print(f"  Max Drawdown:    {stats['max_drawdown']:>10.2%}")
    print(f"  Strategien:      {stats['num_strategies']:>10d}")
    print(f"  Allocation:      {stats['allocation_method']:>10s}")
    print()

    # Individual Strategy Results
    print("📋 STRATEGIE-EINZELERGEBNISSE")
    print("-" * 70)

    for name, strat_result in result.strategy_results.items():
        weight = result.allocation.get(name, 0) * 100
        s = strat_result.stats

        print(f"\n  {name} (Allocation: {weight:.1f}%)")
        print(f"    Return:         {s['total_return']:>10.2%}")
        print(f"    Sharpe:         {s['sharpe']:>10.2f}")
        print(f"    Max DD:         {s['max_drawdown']:>10.2%}")
        print(f"    Trades:         {s['total_trades']:>10d}")
        print(f"    Win Rate:       {s['win_rate']:>10.1%}")
        print(f"    Profit Factor:  {s['profit_factor']:>10.2f}")
        print(f"    Blocked:        {strat_result.blocked_trades:>10d}")

    print("\n" + "-" * 70 + "\n")

    # Live-Trading-Validierung
    print("🔍 LIVE-TRADING-VALIDIERUNG")
    print("-" * 70)

    passed, warnings = validate_for_live_trading(stats)

    if passed:
        print("  ✅ Strategie ERFÜLLT Mindestanforderungen für Live-Trading")
    else:
        print("  ❌ Strategie NICHT bereit für Live-Trading")
        print("\n  Warnungen:")
        for w in warnings:
            print(f"    • {w}")

    print("-" * 70 + "\n")


def export_results(result: PortfolioResult, args: argparse.Namespace):
    """Exportiert Ergebnisse in Dateien."""
    if not args.output_dir:
        return

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_all = args.export_all

    logger.info(f"💾 Exportiere Ergebnisse nach: {output_dir}")

    # === Stats als JSON ===
    if export_all or args.export_stats:
        stats_file = output_dir / f"portfolio_stats_{timestamp}.json"

        # Portfolio-Stats + Individual Stats
        export_data = {
            "portfolio_stats": result.portfolio_stats,
            "allocation": result.allocation,
            "strategy_stats": {},
        }

        for name, strat_result in result.strategy_results.items():
            export_data["strategy_stats"][name] = {
                "stats": strat_result.stats,
                "blocked_trades": strat_result.blocked_trades,
                "mode": strat_result.mode,
            }

        with open(stats_file, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

        logger.info(f"  ✅ Stats → {stats_file}")

    # === Equity-Curve als CSV ===
    if export_all or args.export_equity:
        equity_file = output_dir / f"portfolio_equity_{timestamp}.csv"

        # Kombinierte Equity + Individual Equities
        equity_df = pd.DataFrame({"portfolio": result.combined_equity})

        for name, strat_result in result.strategy_results.items():
            equity_df[name] = strat_result.equity_curve

        equity_df.to_csv(equity_file)
        logger.info(f"  ✅ Equity → {equity_file}")

    # === Trades als CSV ===
    if export_all or args.export_trades:
        for name, strat_result in result.strategy_results.items():
            if not strat_result.trades:
                continue

            trades_file = output_dir / f"trades_{name}_{timestamp}.csv"

            trades_data = []
            for trade in strat_result.trades:
                trades_data.append(
                    {
                        "entry_time": trade.entry_time,
                        "entry_price": trade.entry_price,
                        "size": trade.size,
                        "stop_price": trade.stop_price,
                        "exit_time": trade.exit_time,
                        "exit_price": trade.exit_price,
                        "pnl": trade.pnl,
                        "pnl_pct": trade.pnl_pct,
                        "exit_reason": trade.exit_reason,
                    }
                )

            trades_df = pd.DataFrame(trades_data)
            trades_df.to_csv(trades_file, index=False)
            logger.info(f"  ✅ Trades ({name}) → {trades_file}")

    logger.info("✅ Export abgeschlossen!")


def main():
    """Haupt-Funktion."""
    args = parse_args()

    # Verbose Logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    print_header()

    # === Test-Connection-Mode ===
    if args.test_connection:
        logger.info("🔌 Teste Kraken-Verbindung...")
        if test_kraken_connection():
            print("✅ Kraken-Verbindung OK!\n")
            return 0
        else:
            print("❌ Kraken-Verbindung fehlgeschlagen!\n")
            return 1

    # === Config laden ===
    try:
        cfg = get_config()
    except Exception as e:
        logger.error(f"❌ Fehler beim Laden der Config: {e}")
        return 1

    # === Config-Summary ===
    print_config_summary(args, cfg)

    # === Dry-Run ===
    if args.dry_run:
        logger.info("🏃 Dry-Run: Setup OK, kein Backtest ausgeführt")
        print("✅ Dry-Run erfolgreich! Konfiguration sieht gut aus.\n")
        return 0

    # === Daten laden ===
    try:
        df = load_market_data(
            symbol=args.symbol,
            timeframe=args.timeframe,
            limit=args.limit,
            use_cache=not args.no_cache,
        )
    except Exception as e:
        logger.error(f"❌ Konnte Daten nicht laden: {e}")
        return 1

    # === Backtest ausführen ===
    try:
        result = run_backtest(df, args, cfg)
    except Exception as e:
        logger.error(f"❌ Backtest fehlgeschlagen: {e}")
        import traceback

        traceback.print_exc()
        return 1

    # === Ergebnisse anzeigen ===
    print_results(result)

    # === Export ===
    if args.output_dir or args.export_all:
        # Default Output-Dir falls nicht angegeben
        if not args.output_dir:
            args.output_dir = Path(cfg["backtest"]["results_dir"]) / "portfolio"

        try:
            export_results(result, args)
        except Exception as e:
            logger.error(f"❌ Export fehlgeschlagen: {e}")
            return 1

    print("✅ Backtest erfolgreich abgeschlossen!\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
