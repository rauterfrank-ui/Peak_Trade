#!/usr/bin/env python3
"""
Peak_Trade Stress-Tests CLI (Phase 46)
======================================

Führt Stress-Tests (Crash-Szenarien) für Top-N-Konfigurationen aus Sweeps durch.

Verwendung:
    # Stress-Tests für Top-3 aus Sweep
    python scripts/run_stress_tests.py \
        --sweep-name rsi_reversion_basic \
        --config config/config.toml \
        --top-n 3 \
        --scenarios single_crash_bar vol_spike \
        --severity 0.2

    # Mit mehreren Szenarien
    python scripts/run_stress_tests.py \
        --sweep-name ma_crossover_basic \
        --config config/config.toml \
        --top-n 5 \
        --scenarios single_crash_bar vol_spike drawdown_extension \
        --severity 0.3 \
        --format both

    # Mit Dummy-Daten (für Tests)
    python scripts/run_stress_tests.py \
        --sweep-name test_sweep \
        --config config/config.toml \
        --top-n 3 \
        --scenarios single_crash_bar \
        --use-dummy-data \
        --dummy-bars 500

Output:
    - reports/stress/{sweep_name}/config_1/stress_test_report.md
    - reports/stress/{sweep_name}/config_1/stress_test_report.html
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Sequence

import pandas as pd
import numpy as np

# Projekt-Root zum Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.experiments.stress_tests import (
    StressScenarioConfig,
    StressTestSuiteResult,
    apply_stress_scenario_to_returns,
    run_stress_test_suite,
    load_returns_for_top_config,
)
from src.experiments.topn_promotion import load_top_n_configs_for_sweep
from src.experiments.monte_carlo import run_monte_carlo_from_returns
from src.reporting.stress_test_report import build_stress_test_report
from src.backtest import stats as stats_mod


def setup_logging(verbose: bool = False) -> None:
    """Konfiguriert Logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )


def create_dummy_returns(n_bars: int = 500, seed: int = 42) -> pd.Series:
    """
    Erstellt Dummy-Returns für Tests.

    Args:
        n_bars: Anzahl der Bars
        seed: Random Seed

    Returns:
        Returns-Serie mit DatetimeIndex
    """
    np.random.seed(seed)
    from datetime import datetime, timedelta
    start = datetime.now() - timedelta(hours=n_bars)
    dates = pd.date_range(start, periods=n_bars, freq='1h')

    # Simuliere Returns (leicht positiv mit Volatilität)
    returns = np.random.normal(0.0005, 0.02, n_bars)  # ~0.05% pro Stunde, 2% Vol
    returns_series = pd.Series(returns, index=dates)

    return returns_series


def build_stats_fn() -> callable:
    """
    Erstellt eine Stats-Funktion für Stress-Tests.

    Returns:
        Funktion, die aus Returns Kennzahlen berechnet
    """
    def stats_fn(returns_series: pd.Series) -> dict[str, float]:
        # Konvertiere Returns zu Equity-Curve für compute_basic_stats
        equity = (1 + returns_series).cumprod() * 10000  # Startkapital = 10000
        stats = stats_mod.compute_basic_stats(equity)
        # Füge zusätzliche Metriken hinzu
        if len(returns_series) > 0:
            stats["volatility"] = float(returns_series.std() * np.sqrt(252))  # Annualisiert
            stats["mean_return"] = float(returns_series.mean() * 252)  # Annualisiert
        return stats

    return stats_fn


def build_parser() -> argparse.ArgumentParser:
    """Erstellt den ArgumentParser für Stress-Tests."""
    parser = argparse.ArgumentParser(
        description="Stress-Tests (Crash-Szenarien) für Top-N-Konfigurationen aus einem Sweep.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--sweep-name",
        type=str,
        required=True,
        help="Name des Sweeps (z.B. rsi_reversion_basic)",
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Peak_Trade-Konfigurationsdatei (TOML).",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=3,
        help="Anzahl Top-Konfigurationen (default: 3)",
    )
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=["single_crash_bar", "vol_spike"],
        choices=["single_crash_bar", "vol_spike", "drawdown_extension", "gap_down_open"],
        help="Liste von Szenario-Typen (default: single_crash_bar vol_spike)",
    )
    parser.add_argument(
        "--severity",
        type=float,
        default=0.2,
        help="Basis-Severity für Szenarien (default: 0.2 = 20%%)",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=5,
        help="Fenster-Größe für vol_spike / drawdown_extension (default: 5)",
    )
    parser.add_argument(
        "--position",
        type=str,
        choices=["start", "middle", "end"],
        default="middle",
        help="Position des Shocks (default: middle)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Root-Verzeichnis für Stress-Reports (default: reports/stress)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["md", "html", "both"],
        default="both",
        help="Output-Format (default: both)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random Seed für Reproduzierbarkeit (default: 42)",
    )
    parser.add_argument(
        "--use-dummy-data",
        action="store_true",
        help="Verwende Dummy-Daten für Tests",
    )
    parser.add_argument(
        "--dummy-bars",
        type=int,
        default=500,
        help="Anzahl Bars für Dummy-Daten (default: 500)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose Output",
    )

    return parser


def run_from_args(args: argparse.Namespace) -> int:
    """
    Führt Stress-Tests basierend auf Command-Line-Argumenten aus.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 = success, 1 = error)
    """
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # 1. Lade Peak-Config (optional, für zukünftige Erweiterungen)
        config_path = Path(args.config)
        if not config_path.exists():
            logger.warning(f"Config-Datei nicht gefunden: {config_path}, verwende Defaults")

        # 2. Bestimme Output-Verzeichnis
        if args.output_dir:
            output_root = Path(args.output_dir)
        else:
            output_root = Path("reports/stress")

        # 3. Lade Top-N-Konfigurationen
        logger.info(f"Lade Top-{args.top_n} Konfigurationen für Sweep '{args.sweep_name}'...")
        experiments_dir = Path("reports/experiments")

        try:
            top_configs = load_top_n_configs_for_sweep(
                sweep_name=args.sweep_name,
                n=args.top_n,
                experiments_dir=experiments_dir,
            )
        except Exception as e:
            logger.error(f"Fehler beim Laden der Top-N-Konfigurationen: {e}")
            if args.use_dummy_data:
                logger.info("Erstelle Dummy-Konfigurationen für Tests...")
                top_configs = [
                    {"config_id": f"dummy_config_{i+1}", "rank": i+1}
                    for i in range(args.top_n)
                ]
            else:
                return 1

        if not top_configs:
            logger.error(f"Keine Top-N-Konfigurationen gefunden für Sweep '{args.sweep_name}'")
            return 1

        logger.info(f"Gefunden: {len(top_configs)} Konfigurationen")

        # 4. Erstelle Stats-Funktion
        stats_fn = build_stats_fn()

        # 5. Erstelle Szenario-Configs
        scenarios = []
        for scenario_type in args.scenarios:
            scenarios.append(
                StressScenarioConfig(
                    scenario_type=scenario_type,  # type: ignore
                    severity=args.severity,
                    window=args.window,
                    position=args.position,  # type: ignore
                    seed=args.seed,
                )
            )

        logger.info(f"Erstellt {len(scenarios)} Szenarien: {[s.scenario_type for s in scenarios]}")

        # 6. Führe Stress-Tests für jede Top-Config durch
        for config in top_configs:
            config_rank = config.get("rank", 1)
            config_id = config.get("config_id", f"config_{config_rank}")

            logger.info("=" * 70)
            logger.info(f"Stress-Tests für Config {config_rank}: {config_id}")
            logger.info("=" * 70)

            # Lade Returns
            returns = load_returns_for_top_config(
                sweep_name=args.sweep_name,
                config_rank=config_rank,
                experiments_dir=experiments_dir,
                use_dummy_data=args.use_dummy_data,
                dummy_bars=args.dummy_bars,
            )

            if returns is None:
                logger.warning(f"Konnte Returns für Config {config_rank} nicht laden, überspringe")
                continue

            logger.info(f"Geladen: {len(returns)} Returns")

            # Führe Stress-Test-Suite aus
            try:
                suite = run_stress_test_suite(returns, scenarios, stats_fn)
            except Exception as e:
                logger.error(f"Fehler bei Stress-Test-Suite für Config {config_rank}: {e}")
                continue

            # Erstelle Report
            output_dir = output_root / args.sweep_name / f"config_{config_rank}"
            title = f"Stress-Tests: {args.sweep_name} - Config {config_rank}"

            try:
                paths = build_stress_test_report(
                    suite,
                    title=title,
                    output_dir=output_dir,
                    format=args.format,
                )

                logger.info(f"✅ Report erstellt:")
                for fmt, path in paths.items():
                    logger.info(f"   {fmt.upper()}: {path}")

            except Exception as e:
                logger.error(f"Fehler bei Report-Generierung für Config {config_rank}: {e}")
                continue

        logger.info("=" * 70)
        logger.info("✅ Stress-Tests abgeschlossen")
        logger.info("=" * 70)

        return 0

    except Exception as e:
        logger.exception(f"Unerwarteter Fehler: {e}")
        return 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Haupt-Entry-Point."""
    parser = build_parser()

    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(list(argv))

    return run_from_args(args)


if __name__ == "__main__":
    raise SystemExit(main())


