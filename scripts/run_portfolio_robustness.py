#!/usr/bin/env python3
"""
Peak_Trade Portfolio-Level Robustness CLI (Phase 47)
=====================================================

Führt Portfolio-Level Robustness-Analysen (Monte-Carlo & Stress-Tests) für Multi-Strategy-Portfolios durch.

Verwendung:
    # Portfolio-Robustness für Top-3 aus Sweep
    python scripts/run_portfolio_robustness.py \
        --sweep-name rsi_reversion_basic \
        --config config/config.toml \
        --top-n 3 \
        --portfolio-name rsi_portfolio_v1 \
        --weights 0.4 0.3 0.3 \
        --run-montecarlo \
        --mc-num-runs 1000 \
        --run-stress-tests \
        --stress-scenarios single_crash_bar vol_spike

    # Mit Equal-Weight (keine --weights)
    python scripts/run_portfolio_robustness.py \
        --sweep-name ma_crossover_basic \
        --config config/config.toml \
        --top-n 5 \
        --portfolio-name ma_portfolio_equal \
        --run-montecarlo \
        --mc-num-runs 2000

Output:
    - reports/portfolio_robustness/{portfolio_name}/portfolio_robustness_report.md
    - reports/portfolio_robustness/{portfolio_name}/portfolio_robustness_report.html
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

from src.experiments.portfolio_robustness import (
    PortfolioComponent,
    PortfolioDefinition,
    PortfolioRobustnessConfig,
    run_portfolio_robustness,
)
from src.experiments.topn_promotion import load_top_n_configs_for_sweep
from src.experiments.stress_tests import load_returns_for_top_config
from src.reporting.portfolio_robustness_report import build_portfolio_robustness_report


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


def build_returns_loader(
    sweep_name: str,
    experiments_dir: Path,
    use_dummy_data: bool = False,
    dummy_bars: int = 500,
) -> callable:
    """
    Baut eine Returns-Loader-Funktion für Portfolio-Komponenten.

    Args:
        sweep_name: Name des Sweeps
        experiments_dir: Verzeichnis mit Experiment-Ergebnissen
        use_dummy_data: Wenn True, werden Dummy-Daten verwendet
        dummy_bars: Anzahl Bars für Dummy-Daten

    Returns:
        Funktion (strategy_name: str, config_id: str) -> Optional[pd.Series]
    """
    def returns_loader(strategy_name: str, config_id: str) -> Optional[pd.Series]:
        """
        Lädt Returns für eine Strategie-Konfiguration.

        Args:
            strategy_name: Name der Strategie (aktuell nicht verwendet, für zukünftige Erweiterungen)
            config_id: Config-ID (z.B. "config_1" oder Registry-ID)

        Returns:
            Returns-Serie oder None
        """
        if use_dummy_data:
            # Für Tests: Erstelle Dummy-Returns basierend auf config_id
            config_rank = int(config_id.split("_")[-1]) if config_id.split("_")[-1].isdigit() else 1
            return create_dummy_returns(dummy_bars, seed=42 + config_rank)

        # Versuche, Returns aus Top-N-Konfigurationen zu laden
        # config_id sollte z.B. "config_1", "config_2" etc. sein
        try:
            config_rank = int(config_id.split("_")[-1]) if config_id.split("_")[-1].isdigit() else 1
            returns = load_returns_for_top_config(
                sweep_name=sweep_name,
                config_rank=config_rank,
                experiments_dir=experiments_dir,
                use_dummy_data=False,
                dummy_bars=dummy_bars,
            )
            return returns
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Konnte Returns nicht laden für {strategy_name}/{config_id}: {e}")
            return None

    return returns_loader


def build_parser() -> argparse.ArgumentParser:
    """Erstellt den ArgumentParser für Portfolio-Robustness."""
    parser = argparse.ArgumentParser(
        description="Portfolio-Level Robustness (Monte-Carlo & Stress-Tests) auf Basis von Top-N Strategie-Konfigurationen.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Pflicht-Argumente
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
        help="Anzahl Top-Konfigurationen für das Portfolio (default: 3)",
    )
    parser.add_argument(
        "--portfolio-name",
        type=str,
        required=True,
        help="Name des Portfolios (z.B. rsi_portfolio_v1)",
    )

    # Portfolio-Konfiguration
    parser.add_argument(
        "--weights",
        nargs="+",
        type=float,
        default=None,
        help="Liste von Gewichten für die Top-N Strategien (gleiche Länge wie top-n). Wenn leer, equal-weight.",
    )

    # Monte-Carlo-Flags
    parser.add_argument(
        "--run-montecarlo",
        action="store_true",
        help="Führt Monte-Carlo-Robustness-Analysen aus",
    )
    parser.add_argument(
        "--mc-num-runs",
        type=int,
        default=1000,
        help="Anzahl Monte-Carlo-Runs (default: 1000)",
    )
    parser.add_argument(
        "--mc-method",
        choices=["simple", "block_bootstrap"],
        default="simple",
        help="Monte-Carlo-Methode (default: simple)",
    )
    parser.add_argument(
        "--mc-block-size",
        type=int,
        default=20,
        help="Blockgröße für Block-Bootstrap (default: 20)",
    )
    parser.add_argument(
        "--mc-seed",
        type=int,
        default=42,
        help="Random Seed für Monte-Carlo (default: 42)",
    )

    # Stress-Tests-Flags
    parser.add_argument(
        "--run-stress-tests",
        action="store_true",
        help="Führt Stress-Tests aus",
    )
    parser.add_argument(
        "--stress-scenarios",
        nargs="+",
        default=["single_crash_bar", "vol_spike"],
        choices=["single_crash_bar", "vol_spike", "drawdown_extension", "gap_down_open"],
        help="Liste von Stress-Szenario-Typen (default: single_crash_bar vol_spike)",
    )
    parser.add_argument(
        "--stress-severity",
        type=float,
        default=0.2,
        help="Basis-Severity für Stress-Szenarien (default: 0.2 = 20%%)",
    )
    parser.add_argument(
        "--stress-window",
        type=int,
        default=5,
        help="Fenster-Größe für vol_spike / drawdown_extension (default: 5)",
    )
    parser.add_argument(
        "--stress-position",
        type=str,
        choices=["start", "middle", "end"],
        default="middle",
        help="Position des Stress-Shocks (default: middle)",
    )
    parser.add_argument(
        "--stress-seed",
        type=int,
        default=42,
        help="Random Seed für Stress-Tests (default: 42)",
    )

    # Output-Optionen
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Root-Verzeichnis für Portfolio-Reports (default: reports/portfolio_robustness)",
    )
    parser.add_argument(
        "--format",
        type=str,
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
    Führt Portfolio-Robustness-Analyse basierend auf Command-Line-Argumenten aus.

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
            output_root = Path("reports/portfolio_robustness")

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
                    {"config_id": f"config_{i+1}", "rank": i+1}
                    for i in range(args.top_n)
                ]
            else:
                return 1

        if not top_configs:
            logger.error(f"Keine Top-N-Konfigurationen gefunden für Sweep '{args.sweep_name}'")
            return 1

        logger.info(f"Gefunden: {len(top_configs)} Konfigurationen")

        # 4. Erstelle Portfolio-Definition
        components = []
        if args.weights:
            if len(args.weights) != args.top_n:
                logger.error(f"Anzahl Gewichte ({len(args.weights)}) stimmt nicht mit top-n ({args.top_n}) überein")
                return 1
            weights = args.weights
        else:
            # Equal-weight
            weights = [1.0 / args.top_n] * args.top_n

        for i, config in enumerate(top_configs):
            config_id = config.get("config_id", f"config_{i+1}")
            # Versuche, Strategie-Name aus config zu extrahieren (für zukünftige Erweiterungen)
            strategy_name = config.get("strategy_name", args.sweep_name.split("_")[0] if "_" in args.sweep_name else "unknown")
            components.append(
                PortfolioComponent(
                    strategy_name=strategy_name,
                    config_id=config_id,
                    weight=weights[i],
                )
            )

        portfolio = PortfolioDefinition(
            name=args.portfolio_name,
            components=components,
        )

        logger.info(f"Portfolio '{portfolio.name}' definiert mit {len(components)} Komponenten:")
        for comp in components:
            logger.info(f"  - {comp.strategy_name}/{comp.config_id}: {comp.weight:.1%}")

        # 5. Erstelle Robustness-Config
        robustness_config = PortfolioRobustnessConfig(
            portfolio=portfolio,
            num_mc_runs=args.mc_num_runs if args.run_montecarlo else 0,
            mc_method=args.mc_method,  # type: ignore
            mc_block_size=args.mc_block_size,
            mc_seed=args.mc_seed,
            run_stress_tests=args.run_stress_tests,
            stress_scenarios=args.stress_scenarios if args.run_stress_tests else None,
            stress_severity=args.stress_severity,
            stress_window=args.stress_window,
            stress_position=args.stress_position,  # type: ignore
            stress_seed=args.stress_seed,
        )

        # 6. Erstelle Returns-Loader
        returns_loader = build_returns_loader(
            sweep_name=args.sweep_name,
            experiments_dir=experiments_dir,
            use_dummy_data=args.use_dummy_data,
            dummy_bars=args.dummy_bars,
        )

        # 7. Führe Portfolio-Robustness aus
        logger.info("=" * 70)
        logger.info("Starte Portfolio-Robustness-Analyse")
        logger.info("=" * 70)

        result = run_portfolio_robustness(robustness_config, returns_loader)

        # 8. Erstelle Report
        output_dir = output_root / args.portfolio_name
        title = f"Portfolio Robustness: {args.portfolio_name}"

        try:
            paths = build_portfolio_robustness_report(
                result,
                title=title,
                output_dir=output_dir,
                format=args.format,
            )

            logger.info(f"✅ Report erstellt:")
            for fmt, path in paths.items():
                logger.info(f"   {fmt.upper()}: {path}")

        except Exception as e:
            logger.error(f"Fehler bei Report-Generierung: {e}")
            return 1

        logger.info("=" * 70)
        logger.info("✅ Portfolio-Robustness-Analyse abgeschlossen")
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

