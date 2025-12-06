#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/run_idea_strategy.py
"""
Peak_Trade: Idea Strategy Runner
=================================

Führt eine Idea-Strategie aus dem `src/strategies/ideas/` Verzeichnis aus
und integriert sie mit der vollen Pipeline (Data, Engine, Risk, Regime, Reporting, Experiments).

Usage:
    # Minimales Beispiel
    python scripts/run_idea_strategy.py \\
        --module rsi_keltner \\
        --symbol BTC/EUR

    # Mit allen Optionen
    python scripts/run_idea_strategy.py \\
        --module rsi_keltner \\
        --class-name RsiKeltnerStrategy \\
        --symbol ETH/EUR \\
        --run-name idea_rsi_keltner_demo \\
        --config-path config.toml \\
        --n-bars 500 \\
        --no-report
"""
from __future__ import annotations

import sys
import argparse
import importlib
from pathlib import Path
from typing import List, Any, Callable

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.core.peak_config import load_config
from src.core.position_sizing import build_position_sizer_from_config
from src.core.risk import build_risk_manager_from_config
from src.core.experiments import log_experiment_from_result
from src.backtest.engine import BacktestEngine
from src.backtest.reporting import save_full_report
from src.strategies.base import BaseStrategy


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Peak_Trade: Testet Idea-Strategien mit voller Pipeline-Integration.",
    )
    parser.add_argument(
        "--module",
        required=True,
        help="Modul-Name der Strategie (ohne .py, z.B. 'rsi_keltner'). Wird in src/strategies/ideas/ gesucht.",
    )
    parser.add_argument(
        "--class-name",
        help="Klassenname der Strategie (z.B. 'RsiKeltnerStrategy'). Default: auto-detect aus Modul.",
    )
    parser.add_argument(
        "--symbol",
        default="BTC/EUR",
        help="Trading-Pair (z.B. 'BTC/EUR', 'ETH/EUR'). Default: BTC/EUR",
    )
    parser.add_argument(
        "--run-name",
        help="Name für diesen Run (für Reporting/Experiments). Default: auto-generiert.",
    )
    parser.add_argument(
        "--config-path",
        default="config.toml",
        help="Pfad zur Config-Datei. Default: config.toml",
    )
    parser.add_argument(
        "--n-bars",
        type=int,
        default=200,
        help="Anzahl Bars für Backtest. Default: 200",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Keine HTML/PNG-Reports generieren (nur Stats ausgeben).",
    )
    return parser.parse_args(argv)


def snake_to_camel(snake_str: str) -> str:
    """
    Konvertiert snake_case zu CamelCase.

    Args:
        snake_str: String in snake_case (z.B. "rsi_keltner")

    Returns:
        String in CamelCase (z.B. "RsiKeltner")
    """
    components = snake_str.split("_")
    return "".join(c.capitalize() for c in components)


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

    # Sicherstellen dass High/Low korrekt sind
    df['high'] = df[['open', 'close', 'high']].max(axis=1)
    df['low'] = df[['open', 'close', 'low']].min(axis=1)

    return df


def resolve_strategy_class(module_name: str, class_name: str | None = None) -> type[BaseStrategy]:
    """
    Lädt dynamisch die Strategy-Klasse aus dem Ideas-Modul.

    Args:
        module_name: Modul-Name (z.B. "rsi_keltner")
        class_name: Optional: exakter Klassenname. Falls None, wird "{CamelCase}Strategy" verwendet.

    Returns:
        Strategy-Klasse

    Raises:
        ImportError: Wenn Modul nicht gefunden
        AttributeError: Wenn Klasse nicht im Modul existiert
    """
    # Vollständiger Modul-Pfad
    full_module_path = f"src.strategies.ideas.{module_name}"

    print(f"\n🔍 Lade Strategie-Modul: {full_module_path}")

    try:
        module = importlib.import_module(full_module_path)
    except ImportError as e:
        raise ImportError(
            f"Konnte Modul '{full_module_path}' nicht laden. "
            f"Existiert 'src/strategies/ideas/{module_name}.py'? "
            f"Original-Fehler: {e}"
        )

    # Klassenname ermitteln
    if class_name is None:
        # Auto-detect: {CamelCase}Strategy
        camel = snake_to_camel(module_name)
        class_name = f"{camel}Strategy"

    print(f"🔍 Suche Klasse: {class_name}")

    # Klasse aus Modul holen
    try:
        strategy_class = getattr(module, class_name)
    except AttributeError:
        # Versuche alle Klassen im Modul zu finden
        available_classes = [
            name for name in dir(module)
            if isinstance(getattr(module, name), type)
            and issubclass(getattr(module, name), BaseStrategy)
            and name != "BaseStrategy"
        ]
        raise AttributeError(
            f"Klasse '{class_name}' nicht in Modul '{full_module_path}' gefunden. "
            f"Verfügbare Strategy-Klassen: {available_classes}"
        )

    # Validierung: muss von BaseStrategy erben
    if not issubclass(strategy_class, BaseStrategy):
        raise TypeError(
            f"Klasse '{class_name}' muss von BaseStrategy erben, ist aber {type(strategy_class)}"
        )

    print(f"✅ Strategie-Klasse geladen: {strategy_class}")

    return strategy_class


def run_idea_backtest(
    strategy_class: type[BaseStrategy],
    symbol: str,
    cfg: Any,
    n_bars: int = 200,
    run_name: str | None = None,
    generate_report: bool = True,
) -> None:
    """
    Führt Backtest für eine Idea-Strategie aus.

    Args:
        strategy_class: Strategy-Klasse (von BaseStrategy erbend)
        symbol: Trading-Pair
        cfg: Config-Objekt
        n_bars: Anzahl Bars
        run_name: Name für diesen Run (für Reporting/Experiments)
        generate_report: Ob HTML/PNG-Report erstellt werden soll
    """
    print("\n🚀 Peak_Trade Idea Strategy Backtest")
    print("=" * 70)

    # Daten laden
    print(f"\n📊 Lade Daten für {symbol} ({n_bars} Bars)...")
    df = load_data_for_symbol(symbol, n_bars=n_bars)
    print(f"✅ {len(df)} Bars geladen (von {df.index[0]} bis {df.index[-1]})")

    # Strategie instanziieren (Default-Parameter)
    print(f"\n🎯 Instanziiere Strategie: {strategy_class.__name__}...")
    strategy = strategy_class()
    print(f"✅ Strategie-Config: {strategy.config}")

    # Position Sizer & Risk Manager
    print(f"\n⚙️  Baue Position Sizer & Risk Manager...")
    position_sizer = build_position_sizer_from_config(cfg)
    risk_manager = build_risk_manager_from_config(cfg, section="risk_management")
    print(f"✅ Position Sizer: {type(position_sizer).__name__}")
    print(f"✅ Risk Manager: {type(risk_manager).__name__}")

    # Wrapper für Legacy-API (BacktestEngine erwartet Callable)
    def strategy_signal_fn(df_input: pd.DataFrame, params: dict) -> pd.Series:
        """Wrapper für Strategy.generate_signals()."""
        signals = strategy.generate_signals(df_input)
        # Long-Only: short (-1) → flat (0)
        return signals.replace(-1, 0)

    # Strategy-Params (z.B. stop_pct)
    strategy_params = {"stop_pct": 0.02}  # Default 2% Stop-Loss

    # Backtest ausführen
    print(f"\n🔬 Führe Backtest aus...")
    engine = BacktestEngine(
        core_position_sizer=position_sizer,
        risk_manager=risk_manager
    )
    result = engine.run_realistic(
        df=df,
        strategy_signal_fn=strategy_signal_fn,
        strategy_params=strategy_params
    )

    # Stats ausgeben
    print("\n📈 Backtest-Ergebnisse:")
    print("=" * 70)
    stats = result.stats
    print(f"  Total Return:   {stats.get('total_return', 0.0):>10.2%}")
    print(f"  CAGR:           {stats.get('cagr', 0.0):>10.2%}")
    print(f"  Sharpe Ratio:   {stats.get('sharpe', 0.0):>10.2f}")
    print(f"  Max Drawdown:   {stats.get('max_drawdown', 0.0):>10.2%}")
    print(f"  Total Trades:   {stats.get('total_trades', 0):>10}")
    print(f"  Win Rate:       {stats.get('win_rate', 0.0):>10.2%}")
    print(f"  Profit Factor:  {stats.get('profit_factor', 0.0):>10.2f}")

    # Regime-Distribution falls vorhanden
    regime_dist = result.metadata.get('regime_distribution', {})
    if regime_dist:
        print(f"\n  Regime-Distribution:")
        for regime, pct in regime_dist.items():
            print(f"    - {regime}: {pct:.1%}")

    # Report generieren
    if generate_report:
        if run_name is None:
            # Auto-generiere run_name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_name = f"idea_{strategy_class.__name__.lower()}_{symbol.replace('/', '_')}_{timestamp}"

        report_dir = Path("reports") / "ideas" / run_name
        report_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n💾 Speichere Report nach {report_dir}...")
        save_full_report(
            result=result,
            output_dir=report_dir,
            run_name=run_name,
        )
        print(f"✅ Report gespeichert:")
        print(f"  - HTML: {report_dir / f'{run_name}.html'}")
        print(f"  - CSV:  {report_dir / f'{run_name}.csv'}")
        print(f"  - PNG:  {report_dir / f'{run_name}_equity.png'}")

    # Experiment loggen
    print(f"\n📝 Logge Experiment in Registry...")
    log_experiment_from_result(
        result=result,
        run_type="idea_backtest",
        run_name=run_name or "unnamed_idea_run",
        strategy_key=strategy_class.__name__,
        symbol=symbol,
    )
    print(f"✅ Experiment geloggt in reports/experiments/experiments.csv")

    print("\n🎉 Idea Backtest abgeschlossen!\n")


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    # Config laden
    print(f"\n⚙️  Lade Config: {args.config_path}")
    cfg = load_config(args.config_path)
    print(f"✅ Config geladen")

    # Strategie-Klasse laden
    try:
        strategy_class = resolve_strategy_class(
            module_name=args.module,
            class_name=args.class_name,
        )
    except (ImportError, AttributeError, TypeError) as e:
        print(f"\n❌ Fehler beim Laden der Strategie: {e}")
        sys.exit(1)

    # Backtest ausführen
    try:
        run_idea_backtest(
            strategy_class=strategy_class,
            symbol=args.symbol,
            cfg=cfg,
            n_bars=args.n_bars,
            run_name=args.run_name,
            generate_report=not args.no_report,
        )
    except Exception as e:
        print(f"\n❌ Fehler beim Backtest: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
