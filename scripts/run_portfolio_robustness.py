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

import numpy as np
import pandas as pd

# Projekt-Root zum Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.experiments.portfolio_recipes import get_portfolio_recipe
from src.experiments.portfolio_robustness import (
    PortfolioComponent,
    PortfolioDefinition,
    PortfolioRobustnessConfig,
    run_portfolio_robustness,
)
from src.experiments.stress_tests import load_returns_for_top_config
from src.experiments.topn_promotion import load_top_n_configs_for_sweep
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
    dates = pd.date_range(start, periods=n_bars, freq="1h")

    # Simuliere Returns (leicht positiv mit Volatilität)
    returns = np.random.normal(0.0005, 0.02, n_bars)  # ~0.05% pro Stunde, 2% Vol
    returns_series = pd.Series(returns, index=dates)

    return returns_series


def _build_strategy_returns_cache(
    strategy_config_ids: list[str],
    *,
    dummy_bars: int,
    seed: int = 42,
) -> dict[str, pd.Series]:
    """
    Erzeugt deterministische Dummy-Returns pro Strategy-Config-ID.

    Dieser Pfad ist absichtlich offline-fähig und dient dazu, Phase-53-Presets
    mit `strategies=[...]` end-to-end lauffähig zu machen, auch wenn keine
    Sweep/Top-N-Artefakte vorhanden sind.
    """
    cache: dict[str, pd.Series] = {}
    for i, cfg_id in enumerate(strategy_config_ids):
        stable_offset = sum(ord(c) for c in cfg_id) % 10_000
        cache[cfg_id] = create_dummy_returns(
            n_bars=dummy_bars,
            seed=seed + i + stable_offset,
        )
    return cache


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

    # Portfolio-Recipes (Presets)
    parser.add_argument(
        "--portfolio-preset",
        type=str,
        default=None,
        help="Name/ID eines vordefinierten Portfolio-Recipes (z.B. rsi_reversion_balanced). "
        "Wenn gesetzt, werden Default-Werte aus dem Preset geladen.",
    )
    parser.add_argument(
        "--recipes-config",
        type=str,
        default="config/portfolio_recipes.toml",
        help="Pfad zur TOML-Datei mit Portfolio-Recipes (default: config/portfolio_recipes.toml).",
    )

    # Pflicht-Argumente (werden optional, wenn --portfolio-preset gesetzt ist)
    parser.add_argument(
        "--sweep-name",
        type=str,
        default=None,
        help="Name des Sweeps (z.B. rsi_reversion_basic). "
        "Wird überschrieben, wenn --portfolio-preset gesetzt ist.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Peak_Trade-Konfigurationsdatei (TOML).",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=None,
        help="Anzahl Top-Konfigurationen für das Portfolio (default: 3). "
        "Wird überschrieben, wenn --portfolio-preset gesetzt ist.",
    )
    parser.add_argument(
        "--portfolio-name",
        type=str,
        default=None,
        help="Name des Portfolios (z.B. rsi_portfolio_v1). "
        "Wird überschrieben, wenn --portfolio-preset gesetzt ist.",
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
        default=None,
        help="Output-Format (default: both). "
        "Wird überschrieben, wenn --portfolio-preset gesetzt ist.",
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
        "--verbose",
        "-v",
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
        # 0. Lade Portfolio-Recipe (Preset), falls gesetzt
        recipe = None
        if args.portfolio_preset:
            recipes_config_path = Path(args.recipes_config)
            if not recipes_config_path.exists():
                logger.error(f"Recipes-Config-Datei nicht gefunden: {recipes_config_path}")
                return 1

            try:
                recipe = get_portfolio_recipe(recipes_config_path, args.portfolio_preset)
                logger.info(f"✅ Portfolio-Recipe geladen: {recipe.portfolio_name}")
                logger.info(f"   Beschreibung: {recipe.description or '(keine)'}")
            except KeyError as e:
                logger.error(f"Fehler beim Laden des Portfolio-Recipe: {e}")
                return 1
            except Exception as e:
                logger.error(f"Unerwarteter Fehler beim Laden des Portfolio-Recipe: {e}")
                return 1

        strategies_mode = bool(recipe and recipe.strategies)

        # Merge: Preset-Werte als Defaults, CLI-Argumente überschreiben
        # 1. sweep_name (nur Legacy: Sweep-basiert)
        sweep_name = args.sweep_name
        if not strategies_mode:
            if recipe and sweep_name is None:
                sweep_name = recipe.sweep_name
            if not sweep_name:
                logger.error("--sweep-name ist erforderlich (oder via --portfolio-preset)")
                return 1

        # 2. config
        config_path_str = args.config
        if recipe and config_path_str is None:
            # Recipe hat kein config-Feld, also muss es explizit gesetzt werden
            config_path_str = "config/config.toml"  # Default
        if not config_path_str:
            logger.error("--config ist erforderlich")
            return 1

        # 3. top_n (Legacy) / inferred Komponentenzahl (strategies)
        top_n = args.top_n
        if strategies_mode:
            if top_n is not None:
                logger.warning(
                    "--top-n ist bei Presets mit 'strategies' nicht anwendbar und wird ignoriert "
                    "(Komponentenzahl = len(strategies))."
                )
            top_n = len(recipe.strategies or [])
        else:
            if recipe and top_n is None:
                top_n = recipe.top_n
            if top_n is None:
                top_n = 3  # Fallback

        # 4. portfolio_name
        portfolio_name = args.portfolio_name
        if recipe and portfolio_name is None:
            portfolio_name = recipe.portfolio_name
        if not portfolio_name:
            logger.error("--portfolio-name ist erforderlich (oder via --portfolio-preset)")
            return 1

        # 5. weights
        weights = args.weights
        if recipe and weights is None:
            weights = recipe.weights
        # weights kann None bleiben (wird später zu equal-weight)

        # 6. Monte-Carlo-Flags
        run_montecarlo = args.run_montecarlo
        if recipe and not run_montecarlo:
            run_montecarlo = recipe.run_montecarlo

        mc_num_runs = args.mc_num_runs
        # Wenn Preset gesetzt ist und mc_num_runs nicht explizit überschrieben wurde (Default = 1000),
        # verwende Preset-Wert
        if recipe and recipe.mc_num_runs is not None:
            # Nur überschreiben, wenn es der Default-Wert ist (d.h. nicht explizit gesetzt)
            # argparse setzt Defaults auch wenn nicht gesetzt, daher prüfen wir ob es der Default ist
            if mc_num_runs == 1000:  # Default-Wert aus Parser
                mc_num_runs = recipe.mc_num_runs

        # 7. Stress-Test-Flags
        run_stress_tests = args.run_stress_tests
        if recipe and not run_stress_tests:
            run_stress_tests = recipe.run_stress_tests

        stress_scenarios = args.stress_scenarios
        # Wenn Preset gesetzt ist und stress_scenarios nicht explizit überschrieben wurde,
        # verwende Preset-Wert
        if recipe and recipe.stress_scenarios:
            # Nur überschreiben, wenn es der Default-Wert ist
            if stress_scenarios == ["single_crash_bar", "vol_spike"]:  # Default aus Parser
                stress_scenarios = recipe.stress_scenarios

        stress_severity = args.stress_severity
        # Wenn Preset gesetzt ist und stress_severity nicht explizit überschrieben wurde,
        # verwende Preset-Wert
        if recipe and recipe.stress_severity is not None:
            # Nur überschreiben, wenn es der Default-Wert ist
            if stress_severity == 0.2:  # Default-Wert aus Parser
                stress_severity = recipe.stress_severity

        # 8. format
        format_str = args.format
        if recipe and format_str is None:
            format_str = recipe.format
        if format_str is None:
            format_str = "both"  # Fallback

        # Validierung: weights Länge muss mit Komponentenzahl übereinstimmen
        if weights and len(weights) != top_n:
            label = "len(strategies)" if strategies_mode else "top-n"
            logger.error(
                f"Anzahl Gewichte ({len(weights)}) stimmt nicht mit {label} ({top_n}) überein"
            )
            return 1

        # 1. Lade Peak-Config (optional, für zukünftige Erweiterungen)
        config_path = Path(config_path_str)
        if not config_path.exists():
            logger.warning(f"Config-Datei nicht gefunden: {config_path}, verwende Defaults")

        # 2. Bestimme Output-Verzeichnis
        if args.output_dir:
            output_root = Path(args.output_dir)
        else:
            output_root = Path("reports/portfolio_robustness")

        experiments_dir = Path("reports/experiments")
        strategies: list[str] = []
        top_configs: list[dict] = []

        if strategies_mode:
            strategies = list(recipe.strategies or [])
            if not strategies:
                logger.error("Preset enthält 'strategies', aber Liste ist leer.")
                return 1
            logger.info(f"Preset nutzt direkte Strategien: {len(strategies)} Komponente(n)")
        else:
            # 3. Lade Top-N-Konfigurationen
            logger.info(f"Lade Top-{top_n} Konfigurationen für Sweep '{sweep_name}'...")
            try:
                top_configs = load_top_n_configs_for_sweep(
                    sweep_name=sweep_name,
                    n=top_n,
                    experiments_dir=experiments_dir,
                )
            except Exception as e:
                logger.error(f"Fehler beim Laden der Top-N-Konfigurationen: {e}")
                if args.use_dummy_data:
                    logger.info("Erstelle Dummy-Konfigurationen für Tests...")
                    top_configs = [
                        {"config_id": f"config_{i + 1}", "rank": i + 1} for i in range(top_n)
                    ]
                else:
                    return 1

            if not top_configs:
                logger.error(f"Keine Top-N-Konfigurationen gefunden für Sweep '{sweep_name}'")
                return 1

            logger.info(f"Gefunden: {len(top_configs)} Konfigurationen")

        # 4. Erstelle Portfolio-Definition
        components = []
        if weights:
            # weights wurde bereits validiert (Länge = top_n)
            pass
        else:
            # Equal-weight
            weights = [1.0 / top_n] * top_n

        if strategies_mode:
            for i, strategy_config_id in enumerate(strategies):
                components.append(
                    PortfolioComponent(
                        strategy_name=strategy_config_id,
                        config_id=strategy_config_id,
                        weight=weights[i],
                    )
                )
        else:
            for i, config in enumerate(top_configs):
                config_id = config.get("config_id", f"config_{i + 1}")
                # Versuche, Strategie-Name aus config zu extrahieren (für zukünftige Erweiterungen)
                strategy_name = config.get(
                    "strategy_name", sweep_name.split("_")[0] if "_" in sweep_name else "unknown"
                )
                components.append(
                    PortfolioComponent(
                        strategy_name=strategy_name,
                        config_id=config_id,
                        weight=weights[i],
                    )
                )

        portfolio = PortfolioDefinition(
            name=portfolio_name,
            components=components,
        )

        logger.info(f"Portfolio '{portfolio.name}' definiert mit {len(components)} Komponenten:")
        for comp in components:
            logger.info(f"  - {comp.strategy_name}/{comp.config_id}: {comp.weight:.1%}")

        # 5. Erstelle Robustness-Config
        robustness_config = PortfolioRobustnessConfig(
            portfolio=portfolio,
            num_mc_runs=mc_num_runs if run_montecarlo else 0,
            mc_method=args.mc_method,  # type: ignore
            mc_block_size=args.mc_block_size,
            mc_seed=args.mc_seed,
            run_stress_tests=run_stress_tests,
            stress_scenarios=stress_scenarios if run_stress_tests else None,
            stress_severity=stress_severity,
            stress_window=args.stress_window,
            stress_position=args.stress_position,  # type: ignore
            stress_seed=args.stress_seed,
        )

        # 6. Erstelle Returns-Loader
        if strategies_mode:
            if not args.use_dummy_data:
                logger.error(
                    "Presets mit 'strategies' benötigen aktuell --use-dummy-data, "
                    "da kein data-backed Returns-Loader implementiert ist."
                )
                return 1

            cache = _build_strategy_returns_cache(
                strategies,
                dummy_bars=args.dummy_bars,
                seed=42,
            )

            def returns_loader(strategy_name: str, config_id: str) -> Optional[pd.Series]:
                return cache.get(config_id)

        else:
            returns_loader = build_returns_loader(
                sweep_name=sweep_name,
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
        output_dir = output_root / portfolio_name
        title = f"Portfolio Robustness: {portfolio_name}"

        try:
            paths = build_portfolio_robustness_report(
                result,
                title=title,
                output_dir=output_dir,
                format=format_str,
            )

            logger.info("Report erstellt:")
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
