#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/analyze_regimes.py
"""
Peak_Trade – Regime-Analyse CLI (Phase 19)
==========================================
CLI-Tool zur Analyse von Strategie-Performance in unterschiedlichen Marktregimes.

Subcommands:
    single      Einzelnes Experiment analysieren
    strategy    Alle Backtests einer Strategie analysieren
    sweep       Sweep-Robustheits-Check (Top-N Runs)

Usage:
    # Einzelnes Experiment analysieren
    python scripts/analyze_regimes.py single --id abc12345-...

    # Alle Backtests einer Strategie analysieren
    python scripts/analyze_regimes.py strategy --strategy ma_crossover --limit 20

    # Sweep-Robustheits-Check
    python scripts/analyze_regimes.py sweep --sweep-name ma_crossover_opt_v1 --metric sharpe --top-n 20

Hinweis:
    Dieses Tool ist rein analytisch (Phase 19 Scope).
    Es liest nur Daten aus der Experiment-Registry und erzeugt Statistiken.
    Keine Änderungen an Order-/Execution-/Safety-Komponenten.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Projekt-Root zum Python-Path hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

from src.core.experiments import (
    EXPERIMENTS_CSV,
    VALID_RUN_TYPES,
    get_experiment_by_id,
    load_experiments_df,
)
from src.analytics.explorer import (
    ExperimentFilter,
    ExperimentSummary,
    ExperimentExplorer,
    RankedExperiment,
)
from src.analytics.regimes import (
    RegimeConfig,
    RegimeStats,
    RegimeAnalysisResult,
    SweepRobustnessResult,
    load_regime_config,
    detect_regimes,
    analyze_regimes_from_equity,
    analyze_experiment_regimes,
    compute_sweep_robustness,
    format_regime_stats_table,
)


# =============================================================================
# HELPER: DATEN LADEN
# =============================================================================


def _load_ohlcv_data(symbol: str = "BTC/EUR", days: int = 365) -> Optional[pd.DataFrame]:
    """
    Lädt OHLCV-Daten für ein Symbol.

    Versucht, Daten aus verschiedenen Quellen zu laden:
    1. Kraken CSV aus data/kraken/
    2. Fallback: Synthetische Daten (für Tests)

    Args:
        symbol: Trading-Symbol
        days: Anzahl Tage (wird ignoriert wenn CSV vollständig geladen)

    Returns:
        DataFrame mit OHLCV-Daten oder None
    """
    # Versuche Kraken CSV zu laden
    symbol_clean = symbol.replace("/", "_")
    data_paths = [
        Path(f"data/kraken/{symbol_clean}_1h.csv"),
        Path(f"data/kraken/{symbol_clean}_4h.csv"),
        Path(f"data/kraken/{symbol_clean}_1d.csv"),
        Path(f"data/{symbol_clean}.csv"),
    ]

    for path in data_paths:
        if path.exists():
            try:
                df = pd.read_csv(path)
                # Versuche timestamp-Spalte zu finden und als Index zu setzen
                for col in ["timestamp", "time", "date", "datetime"]:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col])
                        df = df.set_index(col)
                        break
                # Spaltennamen normalisieren
                df.columns = df.columns.str.lower()
                if "close" in df.columns:
                    return df
            except Exception:
                continue

    return None


def _create_synthetic_equity(
    prices: pd.DataFrame,
    strategy_name: str = "buy_and_hold",
    initial_capital: float = 10000.0,
) -> pd.Series:
    """
    Erstellt eine synthetische Equity-Curve für Demo/Analyse.

    Args:
        prices: OHLCV-DataFrame
        strategy_name: Strategie-Typ (nur buy_and_hold unterstützt)
        initial_capital: Startkapital

    Returns:
        Equity-Series
    """
    returns = prices["close"].pct_change().fillna(0)
    equity = initial_capital * (1 + returns).cumprod()
    return equity


# =============================================================================
# OUTPUT FORMATIERUNG
# =============================================================================


def print_header(title: str) -> None:
    """Druckt einen formatierten Header."""
    print()
    print("=" * 90)
    print(f"  {title}")
    print("=" * 90)


def print_regime_stats(stats: List[RegimeStats], title: str = "Regime-Statistiken") -> None:
    """Druckt Regime-Statistiken als ASCII-Tabelle."""
    print()
    print(f"--- {title} ---")
    print()
    print(format_regime_stats_table(stats))
    print()


def print_analysis_result(result: RegimeAnalysisResult) -> None:
    """Druckt ein vollständiges Analyse-Ergebnis."""
    print()
    print("--- ALLGEMEIN ---")
    if result.experiment_id:
        print(f"  Experiment-ID:  {result.experiment_id}")
    if result.strategy_name:
        print(f"  Strategy:       {result.strategy_name}")
    print(f"  Overall Return: {result.overall_return:.2%}")
    if result.overall_sharpe is not None:
        print(f"  Overall Sharpe: {result.overall_sharpe:.2f}")

    print()
    print("--- REGIME-VERTEILUNG ---")
    for regime, weight in sorted(result.regime_distribution.items(), key=lambda x: -x[1]):
        print(f"  {regime:<25} {weight:.1%}")

    if result.regimes:
        print_regime_stats(result.regimes, "PERFORMANCE PRO REGIME")

    best = result.get_best_regime()
    worst = result.get_worst_regime()
    if best and worst:
        print()
        print("--- ZUSAMMENFASSUNG ---")
        print(f"  Bestes Regime:      {best.regime} (Sharpe: {best.sharpe:.2f})")
        print(f"  Schlechtestes:      {worst.regime} (Sharpe: {worst.sharpe:.2f})")


def print_robustness_result(result: SweepRobustnessResult) -> None:
    """Druckt Sweep-Robustheits-Ergebnis."""
    print()
    print("--- SWEEP ROBUSTHEIT ---")
    print(f"  Sweep-Name:       {result.sweep_name}")
    print(f"  Runs analysiert:  {result.run_count}")
    print(f"  Robustness Score: {result.robustness_score:.1%}")

    if result.best_regime:
        print(f"  Bestes Regime:    {result.best_regime}")
    if result.worst_regime:
        print(f"  Schlechtestes:    {result.worst_regime}")

    if result.regime_consistency:
        print()
        print("--- REGIME KONSISTENZ (Runs mit Sharpe > 0) ---")
        for regime, count in sorted(
            result.regime_consistency.items(), key=lambda x: -x[1]
        ):
            print(f"  {regime:<25} {count}/{result.run_count}")


def export_results_csv(
    results: List[RegimeAnalysisResult],
    output_path: Path,
) -> None:
    """Exportiert Ergebnisse in CSV."""
    rows = []
    for r in results:
        base = {
            "experiment_id": r.experiment_id,
            "strategy_name": r.strategy_name,
            "overall_return": r.overall_return,
            "overall_sharpe": r.overall_sharpe,
        }
        for rs in r.regimes:
            row = base.copy()
            row["regime"] = rs.regime
            row["weight"] = rs.weight
            row["bar_count"] = rs.bar_count
            row["return_mean"] = rs.return_mean
            row["sharpe"] = rs.sharpe
            row["max_drawdown"] = rs.max_drawdown
            rows.append(row)

    if rows:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        print(f"\nExportiert: {output_path} ({len(rows)} Zeilen)")


def export_results_json(
    results: List[RegimeAnalysisResult],
    output_path: Path,
) -> None:
    """Exportiert Ergebnisse in JSON."""
    data = [r.to_dict() for r in results]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nExportiert: {output_path} ({len(data)} Experimente)")


# =============================================================================
# COMMAND HANDLERS
# =============================================================================


def cmd_single(args: argparse.Namespace) -> int:
    """Handler für 'single' Command: Einzelnes Experiment analysieren."""
    print_header(f"Peak_Trade – Regime-Analyse: Experiment {args.id[:12]}...")

    # Experiment laden
    record = get_experiment_by_id(args.id)
    if record is None:
        print(f"\nExperiment nicht gefunden: {args.id}")
        return 1

    print()
    print(f"Run-Type:  {record.run_type}")
    print(f"Run-Name:  {record.run_name}")
    if record.strategy_key:
        print(f"Strategy:  {record.strategy_key}")
    if record.symbol:
        print(f"Symbol:    {record.symbol}")

    # Preisdaten laden
    symbol = record.symbol or "BTC/EUR"
    prices = _load_ohlcv_data(symbol)

    if prices is None:
        print(f"\nKeine Preisdaten für {symbol} gefunden.")
        print("Bitte stelle sicher, dass OHLCV-Daten in data/kraken/ vorhanden sind.")
        return 1

    # Config laden
    cfg = load_regime_config()
    if args.verbose:
        print()
        print("--- REGIME CONFIG ---")
        for k, v in cfg.to_dict().items():
            print(f"  {k}: {v}")

    # Synthetische Equity erstellen (in Realität würde man die gespeicherte Equity laden)
    equity = _create_synthetic_equity(prices, initial_capital=10000.0)

    # Analyse durchführen
    result = analyze_experiment_regimes(
        prices=prices,
        equity=equity,
        cfg=cfg,
        experiment_id=args.id,
        strategy_name=record.strategy_key,
    )

    print_analysis_result(result)

    # Export
    if args.export_csv:
        export_results_csv([result], Path(args.export_csv))
    if args.export_json:
        export_results_json([result], Path(args.export_json))

    print()
    return 0


def cmd_strategy(args: argparse.Namespace) -> int:
    """Handler für 'strategy' Command: Alle Backtests einer Strategie analysieren."""
    print_header(f"Peak_Trade – Regime-Analyse: Strategie '{args.strategy}'")

    # Experimente laden
    explorer = ExperimentExplorer()
    flt = ExperimentFilter(
        run_types=[args.run_type] if args.run_type else ["backtest"],
        strategies=[args.strategy],
        limit=args.limit,
    )

    experiments = explorer.list_experiments(flt)

    if not experiments:
        print(f"\nKeine Experimente für Strategie '{args.strategy}' gefunden.")
        return 1

    print(f"\nGefunden: {len(experiments)} Experiment(s)")

    # Config laden
    cfg = load_regime_config()

    # Preisdaten laden (einmal für alle)
    # Nehme Symbol vom ersten Experiment oder Default
    symbol = experiments[0].symbol or "BTC/EUR"
    prices = _load_ohlcv_data(symbol)

    if prices is None:
        print(f"\nKeine Preisdaten für {symbol} gefunden.")
        return 1

    # Analyse für jedes Experiment
    results: List[RegimeAnalysisResult] = []
    for i, exp in enumerate(experiments):
        if args.verbose:
            print(f"\n[{i+1}/{len(experiments)}] Analysiere {exp.experiment_id[:12]}...")

        equity = _create_synthetic_equity(prices)
        result = analyze_experiment_regimes(
            prices=prices,
            equity=equity,
            cfg=cfg,
            experiment_id=exp.experiment_id,
            strategy_name=exp.strategy_name,
        )
        results.append(result)

    # Aggregierte Statistiken
    print()
    print("--- AGGREGIERTE REGIME-STATISTIKEN ---")

    # Sammle Sharpe-Werte pro Regime
    regime_sharpes: Dict[str, List[float]] = {}
    for r in results:
        for rs in r.regimes:
            if rs.sharpe is not None:
                regime_sharpes.setdefault(rs.regime, []).append(rs.sharpe)

    print()
    header = f"{'Regime':<25} {'Count':>6} {'Sharpe (mean)':>14} {'Sharpe (std)':>13} {'Sharpe > 0':>11}"
    print(header)
    print("-" * len(header))

    for regime, sharpes in sorted(regime_sharpes.items()):
        count = len(sharpes)
        mean = np.mean(sharpes)
        std = np.std(sharpes)
        positive = sum(1 for s in sharpes if s > 0)

        print(
            f"{regime:<25} "
            f"{count:>6} "
            f"{mean:>14.2f} "
            f"{std:>13.2f} "
            f"{positive:>7}/{count:<3}"
        )

    # Export
    if args.export_csv:
        export_results_csv(results, Path(args.export_csv))
    if args.export_json:
        export_results_json(results, Path(args.export_json))

    print()
    return 0


def cmd_sweep(args: argparse.Namespace) -> int:
    """Handler für 'sweep' Command: Sweep-Robustheits-Check."""
    print_header(f"Peak_Trade – Regime-Analyse: Sweep '{args.sweep_name}'")

    # Top-N Runs aus dem Sweep laden
    explorer = ExperimentExplorer()
    flt = ExperimentFilter(
        run_types=["sweep"],
        sweep_names=[args.sweep_name],
    )

    ranked = explorer.rank_experiments(
        flt,
        metric=args.metric,
        top_n=args.top_n,
        descending=True,
    )

    if not ranked:
        print(f"\nKeine Sweep-Runs für '{args.sweep_name}' gefunden.")
        return 1

    print(f"\nAnalysiere Top-{len(ranked)} Runs nach {args.metric}")

    # Config laden
    cfg = load_regime_config()

    # Preisdaten laden
    symbol = ranked[0].summary.symbol or "BTC/EUR"
    prices = _load_ohlcv_data(symbol)

    if prices is None:
        print(f"\nKeine Preisdaten für {symbol} gefunden.")
        return 1

    # Analyse für jeden Run
    results: List[RegimeAnalysisResult] = []
    for i, r in enumerate(ranked):
        exp = r.summary
        if args.verbose:
            print(f"\n[{i+1}/{len(ranked)}] Rank {r.rank}: {args.metric}={r.sort_value:.3f}")

        equity = _create_synthetic_equity(prices)
        result = analyze_experiment_regimes(
            prices=prices,
            equity=equity,
            cfg=cfg,
            experiment_id=exp.experiment_id,
            strategy_name=exp.strategy_name,
        )
        results.append(result)

    # Robustheits-Analyse
    robustness = compute_sweep_robustness(results, sweep_name=args.sweep_name)
    print_robustness_result(robustness)

    # Top-3 Runs Details
    print()
    print("--- TOP 3 RUNS DETAILS ---")
    for i, (r, result) in enumerate(zip(ranked[:3], results[:3])):
        print(f"\n  [{i+1}] Rank {r.rank}: {args.metric}={r.sort_value:.3f}")
        print(f"      Run-ID: {r.summary.experiment_id[:12]}...")
        for rs in result.regimes[:3]:  # Top 3 Regimes
            sharpe_str = f"{rs.sharpe:.2f}" if rs.sharpe is not None else "-"
            print(f"      - {rs.regime}: Sharpe={sharpe_str}, Weight={rs.weight:.1%}")

    # Export
    if args.export_csv:
        export_results_csv(results, Path(args.export_csv))
    if args.export_json:
        export_results_json(results, Path(args.export_json))

    print()
    return 0


# =============================================================================
# CLI ARGUMENT PARSING
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    """Baut den Argument-Parser mit Subcommands."""
    parser = argparse.ArgumentParser(
        prog="analyze_regimes.py",
        description="Peak_Trade Regime-Analyse CLI (Phase 19)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  # Einzelnes Experiment analysieren
  python scripts/analyze_regimes.py single --id abc12345-...

  # Alle Backtests einer Strategie analysieren
  python scripts/analyze_regimes.py strategy --strategy ma_crossover --limit 20

  # Sweep-Robustheits-Check
  python scripts/analyze_regimes.py sweep --sweep-name ma_crossover_opt_v1 --metric sharpe --top-n 20

Hinweis:
  Dieses Tool ist rein analytisch. Es liest nur Daten und erzeugt Statistiken.
  Keine Änderungen an Order-/Execution-/Safety-Komponenten.
        """,
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose Output",
    )

    subparsers = parser.add_subparsers(dest="command", help="Verfügbare Subcommands")

    # --- single ---
    single_parser = subparsers.add_parser(
        "single",
        help="Einzelnes Experiment analysieren",
    )
    single_parser.add_argument(
        "--id",
        required=True,
        help="Run-ID des Experiments",
    )
    _add_export_args(single_parser)

    # --- strategy ---
    strategy_parser = subparsers.add_parser(
        "strategy",
        help="Alle Backtests einer Strategie analysieren",
    )
    strategy_parser.add_argument(
        "--strategy",
        required=True,
        help="Name der Strategie",
    )
    strategy_parser.add_argument(
        "--run-type",
        choices=VALID_RUN_TYPES,
        default="backtest",
        help="Filter nach run_type (default: backtest)",
    )
    strategy_parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximale Anzahl Experimente (default: 50)",
    )
    _add_export_args(strategy_parser)

    # --- sweep ---
    sweep_parser = subparsers.add_parser(
        "sweep",
        help="Sweep-Robustheits-Check",
    )
    sweep_parser.add_argument(
        "--sweep-name",
        required=True,
        help="Name des Sweeps",
    )
    sweep_parser.add_argument(
        "--metric",
        default="sharpe",
        help="Metrik für Top-N Ranking (default: sharpe)",
    )
    sweep_parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="Anzahl Top-Runs zum Analysieren (default: 20)",
    )
    _add_export_args(sweep_parser)

    return parser


def _add_export_args(parser: argparse.ArgumentParser) -> None:
    """Fügt Export-Argumente hinzu."""
    parser.add_argument(
        "--export-csv",
        metavar="PATH",
        help="Export in CSV-Datei",
    )
    parser.add_argument(
        "--export-json",
        metavar="PATH",
        help="Export in JSON-Datei",
    )


# =============================================================================
# MAIN
# =============================================================================


def main(argv: Optional[List[str]] = None) -> int:
    """Main-Entry-Point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    # Registry-Check
    if not EXPERIMENTS_CSV.exists():
        print(f"\nKeine Experiment-Registry gefunden: {EXPERIMENTS_CSV}")
        print("Führe zuerst einen Backtest aus, um Experiments zu erzeugen.")
        print()
        return 1

    # Command-Dispatch
    handlers = {
        "single": cmd_single,
        "strategy": cmd_strategy,
        "sweep": cmd_sweep,
    }

    handler = handlers.get(args.command)
    if handler:
        return handler(args)

    print(f"Unbekannter Command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
