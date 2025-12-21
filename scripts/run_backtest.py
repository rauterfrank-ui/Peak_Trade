#!/usr/bin/env python3
"""
Peak_Trade – Zentrales Backtest-Script
======================================
Einziger Standard-Einstiegspunkt für Backtests.

Workflow:
1. Config laden (TOML)
2. Daten-Pipeline aufbauen (CSV oder Kraken API)
3. Strategie instanziieren
4. Backtest ausführen (run_realistic)
5. Stats berechnen
6. Ergebnis ausgeben

Usage:
    # Einfachster Aufruf (defaults aus config.toml)
    python scripts/run_backtest.py

    # Mit CLI-Argumenten
    python scripts/run_backtest.py --strategy ma_crossover --start-date 2023-01-01

    # Mit alternativer Config
    python scripts/run_backtest.py --config custom_config.toml

    # Mit CSV-Daten
    python scripts/run_backtest.py --data-file data/btc_eur_1h.csv
"""

import argparse
import subprocess
import sys
import uuid
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
from src.backtest.stats import compute_backtest_stats, validate_for_live_trading
from src.data import DataNormalizer, CsvLoader, KrakenCsvLoader
from src.core.experiments import log_backtest_result
from src.strategies.registry import (
    get_available_strategy_keys,
    create_strategy_from_config,
)
from src.experiments.evidence_chain import (
    ensure_run_dir,
    write_config_snapshot,
    write_stats_json,
    write_equity_csv,
    write_trades_parquet_optional,
    write_report_snippet_md,
    get_optional_tracker,
)


def parse_args() -> argparse.Namespace:
    """CLI-Argumente parsen."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Backtest Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Standard-Backtest mit ma_crossover
  python scripts/run_backtest.py

  # RSI-Strategie mit CSV-Daten
  python scripts/run_backtest.py --strategy rsi_strategy --data-file data/eth_1h.csv

  # Mit Datumsbeschränkung
  python scripts/run_backtest.py --start-date 2023-06-01 --end-date 2023-12-31
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
        "--data-file",
        type=str,
        default=None,
        help="Pfad zur CSV-Datei mit OHLCV-Daten. Wenn nicht angegeben: Dummy-Daten",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Startdatum (YYYY-MM-DD), filtert Daten",
    )
    parser.add_argument(
        "--end-date",
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
        help="Optionaler Tag für Registry-Logging (z.B. 'dev-test')",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Ausführliche Ausgabe",
    )
    parser.add_argument(
        "--save-report",
        type=str,
        default=None,
        help="Pfad zum Speichern des Reports (z.B. results/backtest_2024.html)",
    )
    # P1 Evidence Chain arguments
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Run-ID für Evidence Chain (default: auto-generated UUID)",
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="results",
        help="Basis-Verzeichnis für Results (default: results)",
    )
    parser.add_argument(
        "--tracker",
        type=str,
        choices=["auto", "null", "mlflow"],
        default="auto",
        help="Tracker-Typ (auto=try mlflow/fallback null, null=kein tracking, mlflow=force mlflow)",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Quarto-Report-Rendering überspringen",
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
    result,
    strategy_name: str,
    df: pd.DataFrame,
    verbose: bool = False,
) -> None:
    """
    Gibt eine kompakte Zusammenfassung des Backtests aus.
    """
    print("\n" + "=" * 70)
    print("BACKTEST ABGESCHLOSSEN")
    print("=" * 70)

    # Zeitraum
    print(
        f"\nZeitraum:   {df.index[0].strftime('%Y-%m-%d')} bis {df.index[-1].strftime('%Y-%m-%d')}"
    )
    print(f"Strategie:  {strategy_name}")
    print(f"Bars:       {len(df)}")

    # Kennzahlen
    print("\n--- KENNZAHLEN ---")
    stats = result.stats

    print(f"  Total Return:    {stats['total_return']:>10.2%}")
    print(f"  Max Drawdown:    {stats['max_drawdown']:>10.2%}")
    print(f"  Sharpe Ratio:    {stats['sharpe']:>10.2f}")
    print(f"  CAGR:            {stats.get('cagr', 0):>10.2%}")

    print("\n--- TRADE-STATISTIKEN ---")
    print(f"  Total Trades:    {stats['total_trades']:>10}")
    print(f"  Win Rate:        {stats['win_rate']:>10.2%}")
    print(f"  Profit Factor:   {stats['profit_factor']:>10.2f}")

    # Blocked Trades (falls vorhanden)
    blocked = stats.get("blocked_trades", 0)
    if blocked > 0:
        print(f"  Blocked Trades:  {blocked:>10}")

    # Sortino/Calmar falls vorhanden
    if "sortino" in stats:
        print(f"  Sortino Ratio:   {stats['sortino']:>10.2f}")
    if "calmar" in stats:
        print(f"  Calmar Ratio:    {stats['calmar']:>10.2f}")

    # Live-Trading-Validierung
    print("\n--- LIVE-TRADING-CHECK ---")
    passed, warnings = validate_for_live_trading(stats)
    if passed:
        print("  Status: FREIGEGEBEN")
    else:
        print("  Status: NICHT FREIGEGEBEN")
        for w in warnings:
            print(f"    - {w}")

    # Equity Start/End
    if verbose:
        print("\n--- EQUITY ---")
        start_eq = result.equity_curve.iloc[0]
        end_eq = result.equity_curve.iloc[-1]
        print(f"  Start:  {start_eq:>12,.2f}")
        print(f"  End:    {end_eq:>12,.2f}")

    print("\n" + "=" * 70 + "\n")


def main() -> int:
    """
    Hauptfunktion.

    Returns:
        Exit-Code (0 = Erfolg, 1 = Fehler)
    """
    args = parse_args()

    # P1 Evidence Chain: Generate run_id
    run_id = (
        args.run_id
        or f"backtest_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    )

    print("\n" + "=" * 70)
    print("  Peak_Trade Backtest Runner")
    print(f"  Run ID: {run_id}")
    print("=" * 70)

    # 1. Config laden
    print("\n[1/7] Config laden...")
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

    # 2. Strategie bestimmen
    print("\n[2/7] Strategie bestimmen...")
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
    print("\n[3/7] Daten laden...")
    try:
        df = load_ohlcv_data(
            data_file=args.data_file,
            start_date=args.start_date,
            end_date=args.end_date,
            n_bars=args.bars,
            verbose=args.verbose,
        )
        print(f"  {len(df)} Bars geladen")
        print(f"  Zeitraum: {df.index[0]} - {df.index[-1]}")
    except Exception as e:
        print(f"\nFEHLER beim Laden der Daten: {e}")
        return 1

    # 4. Backtest ausführen
    print("\n[4/7] Backtest ausführen...")
    try:
        # OOP-Position-Sizer und Risk-Manager aus Config erstellen
        position_sizer = build_position_sizer_from_config(cfg)
        risk_manager = build_risk_manager_from_config(cfg, section="risk_management")

        if args.verbose:
            print(f"  Position Sizer: {position_sizer}")
            print(f"  Risk Manager: {risk_manager}")

        # OOP-Strategie aus Registry erstellen
        # Alle Strategien sind jetzt OOP-basiert (migriert in Phase 7)
        strategy = create_strategy_from_config(strategy_name, cfg)
        if args.verbose:
            print(f"  Strategie: {strategy}")

        # Backtest mit OOP-Strategie
        engine = BacktestEngine(
            core_position_sizer=position_sizer,
            risk_manager=risk_manager,
        )

        # Wrapper-Funktion für Engine (erwartet (df, params) -> signals)
        def strategy_signal_fn(data, params):
            return strategy.generate_signals(data)

        result = engine.run_realistic(
            df=df,
            strategy_signal_fn=strategy_signal_fn,
            strategy_params=strategy_params,
        )
        result.strategy_name = strategy_name

    except KeyError as e:
        print(f"\nFEHLER: Strategie nicht gefunden: {e}")
        available = ", ".join(get_available_strategy_keys())
        print(f"  Verfügbare Strategien: {available}")
        return 1
    except Exception as e:
        print(f"\nFEHLER beim Backtest: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1

    # 5. Ergebnis ausgeben
    print("\n[5/7] Ergebnis ausgeben...")
    print_summary(
        result=result,
        strategy_name=strategy_name,
        df=df,
        verbose=args.verbose,
    )

    # Optional: Report speichern
    if args.save_report:
        try:
            output_dir = Path(args.save_report).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            result.save_all_reports(
                output_dir=output_dir,
                run_name=f"backtest_{strategy_name}",
                save_plots=True,
                save_html=True,
            )
            print(f"Report gespeichert: {args.save_report}")
        except Exception as e:
            print(f"WARNUNG: Report konnte nicht gespeichert werden: {e}")

    # Registry-Logging
    data_source = "csv" if args.data_file else "dummy"
    start_date_str = df.index[0].strftime("%Y-%m-%d")
    end_date_str = df.index[-1].strftime("%Y-%m-%d")

    registry_run_id = log_backtest_result(
        result=result,
        strategy_name=strategy_name,
        tag=args.tag,
        config_path=str(config_path),
        data_source=data_source,
        start_date=start_date_str,
        end_date=end_date_str,
    )

    print(f"Registry-Run-ID: {registry_run_id}")
    if args.tag:
        print(f"Tag: {args.tag}")

    # ============================================================================
    # P1 Evidence Chain: Write Artifacts
    # ============================================================================
    print("\n[6/6] Writing Evidence Chain artifacts...")

    # 1. Ensure run directory
    run_dir = ensure_run_dir(run_id, base_dir=Path(args.results_dir))
    print(f"  Run directory: {run_dir}")

    # 2. Get git SHA (if in git repo)
    git_sha = None
    try:
        git_sha = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=PROJECT_ROOT,
                stderr=subprocess.DEVNULL,
            )
            .decode("utf-8")
            .strip()[:8]
        )
    except Exception:
        pass  # Not in git repo or git not available

    # 3. Write config_snapshot.json
    meta = {
        "run_id": run_id,
        "strategy": strategy_name,
        "symbol": "BTC/EUR",  # TODO: extract from config or args
        "git_sha": git_sha,
        "argv": sys.argv,
        "stage": "backtest",
        "runner": "run_backtest.py",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data_source": data_source,
        "start_date": start_date_str,
        "end_date": end_date_str,
    }
    params = strategy_params
    config_snapshot_path = write_config_snapshot(run_dir, meta, params)
    print(f"  ✓ {config_snapshot_path.name}")

    # 4. Write stats.json
    stats_path = write_stats_json(run_dir, result.stats)
    print(f"  ✓ {stats_path.name}")

    # 5. Write equity.csv
    equity_data = pd.DataFrame(
        {
            "timestamp": result.equity_curve.index.strftime("%Y-%m-%dT%H:%M:%S"),
            "equity": result.equity_curve.values,
        }
    )
    equity_path = write_equity_csv(run_dir, equity_data)
    print(f"  ✓ {equity_path.name}")

    # 6. Write trades.parquet (optional)
    trades_df = None
    if hasattr(result, "trades") and result.trades is not None and len(result.trades) > 0:
        trades_df = result.trades
    trades_path = write_trades_parquet_optional(run_dir, trades_df)
    if trades_path:
        print(f"  ✓ {trades_path.name}")
    else:
        print(f"  ⊘ trades.parquet (skipped)")

    # 7. Write report_snippet.md
    summary = {
        "run_id": run_id,
        "strategy": strategy_name,
        "symbol": meta["symbol"],
        "timestamp": meta["timestamp"],
        **result.stats,
    }
    snippet_path = write_report_snippet_md(run_dir, summary)
    print(f"  ✓ {snippet_path.name}")

    # 8. Optional: Tracker logging (mlflow)
    if args.tracker != "null":
        tracker = get_optional_tracker()
        try:
            tracker.log_params(params)
            tracker.log_metrics(result.stats)
            tracker.log_artifact(config_snapshot_path)
            tracker.log_artifact(stats_path)
            tracker.log_artifact(equity_path)
            tracker.set_tag("run_id", run_id)
            tracker.set_tag("stage", "backtest")
            print(f"  ✓ Tracker logged (type: {type(tracker).__name__})")
        except Exception as e:
            if args.tracker == "mlflow":
                # Force mlflow mode, so fail hard
                print(f"  ✗ Tracker failed: {e}")
                return 1
            else:
                # Auto mode, graceful degradation
                print(f"  ⊘ Tracker failed (graceful degradation): {e}")

    # 9. Optional: Render Quarto report
    if not args.no_report:
        print("\n[7/7] Rendering Quarto report...")
        try:
            render_script = PROJECT_ROOT / "scripts" / "render_last_report.sh"
            result_code = subprocess.call(
                ["bash", str(render_script), run_id],
                cwd=PROJECT_ROOT,
            )
            if result_code == 0:
                print(f"  ✓ Report rendered: {run_dir}/report/backtest.html")
            else:
                print(f"  ⊘ Report rendering skipped or failed (exit code {result_code})")
        except Exception as e:
            print(f"  ⊘ Report rendering failed: {e}")

    print("\n" + "=" * 70)
    print("✅ Backtest + Evidence Chain abgeschlossen")
    print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
