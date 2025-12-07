#!/usr/bin/env python3
"""
Peak_Trade Monte-Carlo Robustness CLI (Phase 45)
================================================

Führt Monte-Carlo-Robustness-Analysen für Top-N-Konfigurationen aus Sweeps durch.

Verwendung:
    # Monte-Carlo für Top-3 aus Sweep
    python scripts/run_monte_carlo_robustness.py \
        --sweep-name rsi_reversion_basic \
        --config config/config.toml \
        --top-n 3 \
        --num-runs 1000

    # Mit Block-Bootstrap
    python scripts/run_monte_carlo_robustness.py \
        --sweep-name ma_crossover_basic \
        --config config/config.toml \
        --top-n 5 \
        --num-runs 2000 \
        --method block_bootstrap \
        --block-size 20

    # Mit Dummy-Daten (für Tests)
    python scripts/run_monte_carlo_robustness.py \
        --sweep-name rsi_reversion_basic \
        --config config/config.toml \
        --top-n 3 \
        --use-dummy-data \
        --dummy-bars 500

Output:
    - reports/monte_carlo/{sweep_name}/{config_id}_monte_carlo_YYYYMMDD.md
    - reports/monte_carlo/{sweep_name}/{config_id}_monte_carlo_YYYYMMDD.html
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Sequence

import pandas as pd
import numpy as np

# Projekt-Root zum Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.experiments.monte_carlo import (
    MonteCarloConfig,
    run_monte_carlo_from_returns,
    run_monte_carlo_from_equity,
)
from src.experiments.topn_promotion import load_top_n_configs_for_sweep
from src.reporting.monte_carlo_report import build_monte_carlo_report


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
    start = datetime.now() - timedelta(hours=n_bars)
    dates = pd.date_range(start, periods=n_bars, freq='1h')

    # Simuliere Returns (leicht positiv mit Volatilität)
    returns = np.random.normal(0.0005, 0.02, n_bars)  # ~0.05% pro Stunde, 2% Vol
    returns_series = pd.Series(returns, index=dates)

    return returns_series


def create_dummy_equity(n_bars: int = 500, seed: int = 42) -> pd.Series:
    """
    Erstellt Dummy-Equity-Curve für Tests.

    Args:
        n_bars: Anzahl der Bars
        seed: Random Seed

    Returns:
        Equity-Serie mit DatetimeIndex
    """
    returns = create_dummy_returns(n_bars, seed)
    equity = (1 + returns).cumprod() * 10000  # Startkapital = 10000
    return equity


def load_returns_for_config(
    config: dict,
    experiments_dir: Path,
    *,
    use_dummy_data: bool = False,
    dummy_bars: int = 500,
) -> Optional[pd.Series]:
    """
    Lädt Returns für eine Top-N-Konfiguration.

    Args:
        config: Config-Dict aus load_top_n_configs_for_sweep
        experiments_dir: Verzeichnis mit Experiment-Ergebnissen
        use_dummy_data: Wenn True, werden Dummy-Daten verwendet
        dummy_bars: Anzahl Bars für Dummy-Daten

    Returns:
        Returns-Serie oder None

    Note:
        Aktuell ist dies eine vereinfachte Implementierung. In einer vollständigen
        Implementierung würde man die Equity-Curves aus den Backtest-Result-Objekten
        laden. Für Phase 45 verwenden wir Dummy-Daten oder Approximationen.
    """
    if use_dummy_data:
        logger = logging.getLogger(__name__)
        logger.info(f"Verwende Dummy-Daten für Config {config.get('config_id', 'unknown')}")
        return create_dummy_returns(dummy_bars)

    # NOTE: Siehe docs/TECH_DEBT_BACKLOG.md (Eintrag "Vollständige Monte-Carlo-Robustness-Implementierung")
    # Aktuell: Placeholder - würde hier die Equity-Curve aus dem Experiment-Run laden
    logger = logging.getLogger(__name__)
    logger.warning(
        f"load_returns_for_config ist noch nicht vollständig implementiert "
        f"für config_id={config.get('config_id', 'unknown')}. "
        f"Verwende Dummy-Daten als Fallback."
    )
    return create_dummy_returns(dummy_bars)


def build_parser() -> argparse.ArgumentParser:
    """Erstellt den ArgumentParser für Monte-Carlo-Robustness."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Monte-Carlo Robustness CLI (Phase 45)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Pflicht-Argumente
    parser.add_argument(
        "--sweep-name", "-s",
        type=str,
        required=True,
        help="Name des Sweeps (z.B. rsi_reversion_basic)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Peak_Trade-Konfigurationsdatei (TOML, default: config/config.toml)",
    )

    # Top-N Optionen
    parser.add_argument(
        "--top-n", "-n",
        type=int,
        default=1,
        help="Anzahl Top-Konfigurationen aus dem Sweep (default: 1)",
    )

    # Monte-Carlo Optionen
    parser.add_argument(
        "--num-runs",
        type=int,
        default=1000,
        help="Anzahl Monte-Carlo-Runs (default: 1000)",
    )
    parser.add_argument(
        "--method",
        choices=["simple", "block_bootstrap"],
        default="simple",
        help="Monte-Carlo-Methode (default: simple)",
    )
    parser.add_argument(
        "--block-size",
        type=int,
        default=20,
        help="Blockgröße für Block-Bootstrap (default: 20)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random Seed für Reproduzierbarkeit (default: 42)",
    )

    # Output-Optionen
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Zielverzeichnis für Reports (default: reports/monte_carlo/{sweep_name}/)",
    )
    parser.add_argument(
        "--format",
        choices=["md", "html", "both"],
        default="both",
        help="Output-Format (default: both)",
    )

    # Dummy-Daten (für Tests)
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

    # Weitere Optionen
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose Output",
    )

    return parser


def run_from_args(args: argparse.Namespace) -> int:
    """
    Führt Monte-Carlo-Robustness-Analyse aus.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 = success, 1 = error)
    """
    logger = logging.getLogger(__name__)

    # 1. Lade Top-N-Konfigurationen
    logger.info(f"Lade Top-{args.top_n} Konfigurationen für Sweep '{args.sweep_name}'")
    try:
        configs = load_top_n_configs_for_sweep(
            args.sweep_name,
            n=args.top_n,
            experiments_dir=Path("reports/experiments"),
            output_path=Path("reports/sweeps"),
        )
    except Exception as e:
        logger.error(f"Fehler beim Laden der Top-N-Konfigurationen: {e}")
        return 1

    if not configs:
        logger.error(f"Keine Konfigurationen gefunden für Sweep '{args.sweep_name}'")
        return 1

    logger.info(f"{len(configs)} Konfigurationen geladen")

    # 2. Erstelle Output-Verzeichnis
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path("reports/monte_carlo") / args.sweep_name

    output_dir.mkdir(parents=True, exist_ok=True)

    # 3. Führe Monte-Carlo für jede Konfiguration durch
    mc_config = MonteCarloConfig(
        num_runs=args.num_runs,
        method=args.method,
        block_size=args.block_size,
        seed=args.seed,
    )

    results_summary = []

    for i, config in enumerate(configs, 1):
        config_id = config.get("config_id", f"config_{i}")
        logger.info("=" * 70)
        logger.info(f"Analysiere Konfiguration {i}/{len(configs)}: {config_id}")
        logger.info("=" * 70)

        # Lade Returns
        returns = load_returns_for_config(
            config,
            Path("reports/experiments"),
            use_dummy_data=args.use_dummy_data,
            dummy_bars=args.dummy_bars,
        )

        if returns is None:
            logger.warning(f"Konnte Returns für {config_id} nicht laden, überspringe")
            continue

        # Führe Monte-Carlo durch
        try:
            summary = run_monte_carlo_from_returns(returns, mc_config)
        except Exception as e:
            logger.error(f"Fehler bei Monte-Carlo für {config_id}: {e}")
            continue

        # Erstelle Report
        title = f"Monte-Carlo Robustness: {args.sweep_name} - {config_id}"
        config_output_dir = output_dir / config_id
        config_output_dir.mkdir(parents=True, exist_ok=True)

        try:
            paths = build_monte_carlo_report(
                summary,
                title=title,
                output_dir=config_output_dir,
                format=args.format,
            )
            logger.info(f"Report gespeichert: {config_output_dir}")
            results_summary.append({
                "config_id": config_id,
                "rank": config.get("rank", i),
                "paths": paths,
            })
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Reports für {config_id}: {e}")
            continue

    # 4. Zusammenfassung
    logger.info("=" * 70)
    logger.info("Monte-Carlo-Analyse abgeschlossen")
    logger.info("=" * 70)
    logger.info(f"Analysierte Konfigurationen: {len(results_summary)}/{len(configs)}")
    for result in results_summary:
        logger.info(f"  - {result['config_id']} (Rank {result['rank']}): {result['paths']}")

    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Haupt-Entry-Point."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    setup_logging(verbose=args.verbose)

    return run_from_args(args)


if __name__ == "__main__":
    sys.exit(main())

