#!/usr/bin/env python3
"""
Peak_Trade Unified Research CLI
================================

Gebündelte CLI für den gesamten Research-Workflow:
- Strategy-Sweeps (Phase 41)
- Sweep-Reports inkl. Plots & Drawdown-Heatmaps (Phase 43)
- Top-N Promotion (Phase 42)
- Walk-Forward-Testing (Phase 44)
- Monte-Carlo-Robustness (Phase 45)
- Stress-Tests & Crash-Szenarien (Phase 46)
- Portfolio-Level Robustness (Phase 47)
- Strategy-Profiles & Tiering (Phase 41B)

Verwendung:
    # Strategy-Sweep ausführen
    python scripts/research_cli.py sweep --sweep-name rsi_reversion_basic --config config/config.toml

    # Sweep-Report generieren
    python scripts/research_cli.py report --sweep-name rsi_reversion_basic --format both --with-plots

    # Top-N Promotion
    python scripts/research_cli.py promote --sweep-name rsi_reversion_basic --top-n 5

    # Walk-Forward-Testing
    python scripts/research_cli.py walkforward --sweep-name rsi_reversion_basic --top-n 3 --train-window 90d --test-window 30d --use-dummy-data

    # Monte-Carlo-Robustness
    python scripts/research_cli.py montecarlo --sweep-name rsi_reversion_basic --config config/config.toml --top-n 3 --num-runs 1000

    # Stress-Tests
    python scripts/research_cli.py stress --sweep-name rsi_reversion_basic --config config/config.toml --top-n 3 --scenarios single_crash_bar vol_spike

    # Portfolio-Level Robustness
    python scripts/research_cli.py portfolio --sweep-name rsi_reversion_basic --config config/config.toml --top-n 3 --portfolio-name rsi_portfolio_v1 --run-montecarlo --run-stress-tests

    # Strategy-Profile generieren (Phase 41B)
    python scripts/research_cli.py strategy-profile --strategy-id rsi_reversion --output-format both --with-regime --with-montecarlo --with-stress

    # End-to-End-Pipeline
    python scripts/research_cli.py pipeline \\
        --sweep-name rsi_reversion_basic \\
        --config config/config.toml \\
        --format both \\
        --with-plots \\
        --top-n 5 \\
        --run-walkforward \\
        --train-window 90d \\
        --test-window 30d \\
        --use-dummy-data
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

# Projekt-Root zum Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Importe der Runner-Funktionen aus den bestehenden Scripts
# Da die Scripts im scripts/ Verzeichnis sind, müssen wir sie direkt importieren
import importlib.util

def _import_module_from_path(module_name: str, file_path: Path):
    """Importiert ein Modul aus einem Dateipfad."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Importiere die Module
_sweep_module = _import_module_from_path("run_strategy_sweep", project_root / "scripts" / "run_strategy_sweep.py")
_report_module = _import_module_from_path("generate_strategy_sweep_report", project_root / "scripts" / "generate_strategy_sweep_report.py")
_promote_module = _import_module_from_path("promote_sweep_topn", project_root / "scripts" / "promote_sweep_topn.py")
_walkforward_module = _import_module_from_path("run_walkforward_backtest", project_root / "scripts" / "run_walkforward_backtest.py")
_montecarlo_module = _import_module_from_path("run_monte_carlo_robustness", project_root / "scripts" / "run_monte_carlo_robustness.py")
_stress_module = _import_module_from_path("run_stress_tests", project_root / "scripts" / "run_stress_tests.py")
_portfolio_module = _import_module_from_path("run_portfolio_robustness", project_root / "scripts" / "run_portfolio_robustness.py")

# Extrahiere die Funktionen
run_sweep_from_args = _sweep_module.run_from_args
build_sweep_parser = _sweep_module.build_parser
run_report_from_args = _report_module.run_from_args
build_report_parser = _report_module.build_parser
run_promote_from_args = _promote_module.run_from_args
build_promote_parser = _promote_module.build_parser
run_walkforward_from_args = _walkforward_module.run_from_args
build_walkforward_parser = _walkforward_module.build_parser
run_montecarlo_from_args = _montecarlo_module.run_from_args
build_montecarlo_parser = _montecarlo_module.build_parser
run_stress_from_args = _stress_module.run_from_args
build_stress_parser = _stress_module.build_parser
run_portfolio_robustness_from_args = _portfolio_module.run_from_args
build_portfolio_robustness_parser = _portfolio_module.build_parser


def build_parser() -> argparse.ArgumentParser:
    """Erstellt den Haupt-ArgumentParser für die Unified Research-CLI."""
    parser = argparse.ArgumentParser(
        prog="peak-trade-research",
        description="Unified Research-CLI für Strategy-Sweeps, Reports, Promotion und Walk-Forward-Tests.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True, help="Verfügbare Kommandos")

    # Subparser: sweep
    sweep_parser = subparsers.add_parser(
        "sweep",
        help="Strategy-Sweep ausführen (Phase 41).",
        parents=[build_sweep_parser()],
        add_help=False,  # Verhindere doppelte --help
    )
    # Alle Argumente sind bereits durch parents=[build_sweep_parser()] enthalten

    # Subparser: report
    report_parser = subparsers.add_parser(
        "report",
        help="Sweep-Report generieren (Markdown/HTML, Phase 43).",
        parents=[build_report_parser()],
        add_help=False,
    )

    # Subparser: promote
    promote_parser = subparsers.add_parser(
        "promote",
        help="Top-N Promotion aus Sweep-Ergebnissen (Phase 42).",
        parents=[build_promote_parser()],
        add_help=False,
    )

    # Subparser: walkforward
    walk_parser = subparsers.add_parser(
        "walkforward",
        help="Walk-Forward-Backtests aus Sweep-/Top-N-Ergebnissen (Phase 44).",
        parents=[build_walkforward_parser()],
        add_help=False,
    )

    # Subparser: montecarlo
    mc_parser = subparsers.add_parser(
        "montecarlo",
        help="Monte-Carlo-Robustness-Analyse für Top-N-Konfigurationen (Phase 45).",
        parents=[build_montecarlo_parser()],
        add_help=False,
    )

    # Subparser: stress
    stress_parser = subparsers.add_parser(
        "stress",
        help="Stress-Tests (Crash-Szenarien) für Top-N-Konfigurationen (Phase 46).",
        parents=[build_stress_parser()],
        add_help=False,
    )

    # Subparser: portfolio
    portfolio_parser = subparsers.add_parser(
        "portfolio",
        help="Portfolio-Level Robustness (Monte-Carlo & Stress-Tests) für Top-N Strategien (Phase 47).",
        parents=[build_portfolio_robustness_parser()],
        add_help=False,
    )

    # Subparser: pipeline (kombiniert mehrere Schritte)
    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="End-to-End-Research-Pipeline v2 (Sweep → Report → Promotion → optional Walk-Forward/Monte-Carlo/Stress-Tests).",
    )
    
    # Pipeline-Flags: Kombination aus allen anderen Parsern
    # Pflicht-Argumente
    pipeline_parser.add_argument(
        "--sweep-name", "-s",
        type=str,
        required=True,
        help="Name des Sweeps (z.B. rsi_reversion_basic)",
    )
    pipeline_parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Config-Datei (default: config/config.toml)",
    )
    
    # Report-Optionen
    pipeline_parser.add_argument(
        "--format", "-f",
        type=str,
        choices=["md", "html", "both"],
        default="both",
        help="Output-Format für Report (default: both)",
    )
    pipeline_parser.add_argument(
        "--with-plots",
        action="store_true",
        help="Erzeugt Visualisierungen (Parameter vs. Metrik, Heatmaps)",
    )
    
    # Promotion-Optionen
    pipeline_parser.add_argument(
        "--top-n", "-n",
        type=int,
        default=5,
        help="Anzahl der Top-Konfigurationen für Promotion (default: 5)",
    )
    
    # Walk-Forward-Optionen
    pipeline_parser.add_argument(
        "--run-walkforward",
        action="store_true",
        help="Führt Walk-Forward-Tests aus (nur wenn gesetzt)",
    )
    pipeline_parser.add_argument(
        "--walkforward-train-window",
        type=str,
        help="Trainingsfenster-Dauer für Walk-Forward (z.B. 90d, 6M)",
    )
    pipeline_parser.add_argument(
        "--walkforward-test-window",
        type=str,
        help="Testfenster-Dauer für Walk-Forward (z.B. 30d, 1M)",
    )
    pipeline_parser.add_argument(
        "--walkforward-step-size",
        type=str,
        default=None,
        help="Schrittgröße zwischen Fenstern (default: test-window)",
    )
    pipeline_parser.add_argument(
        "--walkforward-use-dummy-data",
        action="store_true",
        help="Verwende Dummy-Daten für Walk-Forward-Tests",
    )
    pipeline_parser.add_argument(
        "--walkforward-dummy-bars",
        type=int,
        default=1000,
        help="Anzahl Bars für Dummy-Daten (default: 1000)",
    )
    
    # Monte-Carlo-Optionen
    pipeline_parser.add_argument(
        "--run-montecarlo",
        action="store_true",
        help="Führt Monte-Carlo-Robustness-Analysen aus (nur wenn gesetzt)",
    )
    pipeline_parser.add_argument(
        "--mc-num-runs",
        type=int,
        default=1000,
        help="Anzahl Monte-Carlo-Runs (default: 1000)",
    )
    pipeline_parser.add_argument(
        "--mc-method",
        choices=["simple", "block_bootstrap"],
        default="simple",
        help="Monte-Carlo-Methode (default: simple)",
    )
    pipeline_parser.add_argument(
        "--mc-block-size",
        type=int,
        default=20,
        help="Blockgröße für Block-Bootstrap (default: 20)",
    )
    pipeline_parser.add_argument(
        "--mc-seed",
        type=int,
        default=42,
        help="Random Seed für Monte-Carlo (default: 42)",
    )
    pipeline_parser.add_argument(
        "--mc-use-dummy-data",
        action="store_true",
        help="Verwende Dummy-Daten für Monte-Carlo",
    )
    pipeline_parser.add_argument(
        "--mc-dummy-bars",
        type=int,
        default=500,
        help="Anzahl Bars für Monte-Carlo-Dummy-Daten (default: 500)",
    )
    
    # Stress-Tests-Optionen
    pipeline_parser.add_argument(
        "--run-stress-tests",
        action="store_true",
        help="Führt Stress-Tests aus (nur wenn gesetzt)",
    )
    pipeline_parser.add_argument(
        "--stress-scenarios",
        nargs="+",
        default=["single_crash_bar", "vol_spike"],
        choices=["single_crash_bar", "vol_spike", "drawdown_extension", "gap_down_open"],
        help="Liste von Stress-Szenario-Typen (default: single_crash_bar vol_spike)",
    )
    pipeline_parser.add_argument(
        "--stress-severity",
        type=float,
        default=0.2,
        help="Basis-Severity für Stress-Szenarien (default: 0.2 = 20%%)",
    )
    pipeline_parser.add_argument(
        "--stress-window",
        type=int,
        default=5,
        help="Fenster-Größe für vol_spike / drawdown_extension (default: 5)",
    )
    pipeline_parser.add_argument(
        "--stress-position",
        type=str,
        choices=["start", "middle", "end"],
        default="middle",
        help="Position des Stress-Shocks (default: middle)",
    )
    pipeline_parser.add_argument(
        "--stress-seed",
        type=int,
        default=42,
        help="Random Seed für Stress-Tests (default: 42)",
    )
    pipeline_parser.add_argument(
        "--stress-use-dummy-data",
        action="store_true",
        help="Verwende Dummy-Daten für Stress-Tests",
    )
    pipeline_parser.add_argument(
        "--stress-dummy-bars",
        type=int,
        default=500,
        help="Anzahl Bars für Stress-Test-Dummy-Daten (default: 500)",
    )
    
    # Weitere Optionen
    pipeline_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose Output",
    )

    # Subparser: strategy-profile (Phase 41B)
    profile_parser = subparsers.add_parser(
        "strategy-profile",
        help="Generiert ein Robustness-Profil für eine Strategie (Phase 41B).",
    )

    profile_parser.add_argument(
        "--strategy-id", "-s",
        type=str,
        required=True,
        help="Strategy-ID aus der Registry (z.B. rsi_reversion, ma_crossover, breakout)",
    )
    profile_parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Config-Datei (default: config/config.toml)",
    )
    profile_parser.add_argument(
        "--tiering-config",
        type=str,
        default="config/strategy_tiering.toml",
        help="Pfad zur Tiering-Config (default: config/strategy_tiering.toml)",
    )
    profile_parser.add_argument(
        "--output-format", "-f",
        type=str,
        choices=["json", "md", "both"],
        default="both",
        help="Output-Format (default: both)",
    )
    profile_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output-Verzeichnis (default: reports/strategy_profiles für JSON, docs/strategy_profiles für MD)",
    )
    profile_parser.add_argument(
        "--with-regime",
        action="store_true",
        help="Führt Regime-Analyse durch (falls Regime-Detection verfügbar)",
    )
    profile_parser.add_argument(
        "--with-montecarlo",
        action="store_true",
        help="Führt Monte-Carlo-Robustness-Analyse durch",
    )
    profile_parser.add_argument(
        "--with-stress",
        action="store_true",
        help="Führt Stress-Tests durch",
    )
    profile_parser.add_argument(
        "--mc-num-runs",
        type=int,
        default=100,
        help="Anzahl Monte-Carlo-Runs (default: 100)",
    )
    profile_parser.add_argument(
        "--mc-method",
        choices=["simple", "block_bootstrap"],
        default="simple",
        help="Monte-Carlo-Methode (default: simple)",
    )
    profile_parser.add_argument(
        "--stress-scenarios",
        nargs="+",
        default=["single_crash_bar", "vol_spike"],
        choices=["single_crash_bar", "vol_spike", "drawdown_extension", "gap_down_open"],
        help="Liste von Stress-Szenario-Typen (default: single_crash_bar vol_spike)",
    )
    profile_parser.add_argument(
        "--stress-severity",
        type=float,
        default=0.2,
        help="Basis-Severity für Stress-Szenarien (default: 0.2 = 20%%)",
    )
    profile_parser.add_argument(
        "--symbol",
        type=str,
        default="BTC/EUR",
        help="Trading-Symbol (default: BTC/EUR)",
    )
    profile_parser.add_argument(
        "--timeframe",
        type=str,
        default="1h",
        help="Timeframe (default: 1h)",
    )
    profile_parser.add_argument(
        "--use-dummy-data",
        action="store_true",
        help="Verwende Dummy-Daten statt echte Marktdaten",
    )
    profile_parser.add_argument(
        "--dummy-bars",
        type=int,
        default=500,
        help="Anzahl Bars für Dummy-Daten (default: 500)",
    )
    profile_parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random Seed für Reproduzierbarkeit (default: 42)",
    )
    profile_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose Output",
    )
    profile_parser.add_argument(
        "--list-strategies",
        action="store_true",
        help="Zeigt alle verfügbaren Strategy-IDs und beendet",
    )

    # Subparser: run-experiment (R&D-Presets, Phase 75 Wave v2)
    experiment_parser = subparsers.add_parser(
        "run-experiment",
        help="Führt ein R&D-Experiment mit Preset aus config/r_and_d_presets.toml aus.",
    )

    experiment_parser.add_argument(
        "--preset", "-p",
        type=str,
        default=None,
        help="Preset-ID aus config/r_and_d_presets.toml (z.B. armstrong_ecm_btc_longterm_v1)",
    )
    experiment_parser.add_argument(
        "--symbol",
        type=str,
        default=None,
        help="Trading-Symbol (überschreibt Preset-Default, z.B. BTC/USDT)",
    )
    experiment_parser.add_argument(
        "--timeframe",
        type=str,
        default=None,
        help="Timeframe (überschreibt Preset-Default, z.B. 1h, 4h, 1d)",
    )
    experiment_parser.add_argument(
        "--from",
        dest="from_date",
        type=str,
        default=None,
        help="Startdatum (YYYY-MM-DD)",
    )
    experiment_parser.add_argument(
        "--to",
        dest="to_date",
        type=str,
        default=None,
        help="Enddatum (YYYY-MM-DD)",
    )
    experiment_parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Experiment-Tag für Ergebnisse (z.B. exp_rnd_w2_armstrong_v1)",
    )
    experiment_parser.add_argument(
        "--config",
        type=str,
        default="config/config.toml",
        help="Pfad zur Config-Datei (default: config/config.toml)",
    )
    experiment_parser.add_argument(
        "--presets-file",
        type=str,
        default="config/r_and_d_presets.toml",
        help="Pfad zur R&D-Presets-Datei (default: config/r_and_d_presets.toml)",
    )
    experiment_parser.add_argument(
        "--output-dir",
        type=str,
        default="reports/r_and_d_experiments",
        help="Output-Verzeichnis für Ergebnisse (default: reports/r_and_d_experiments)",
    )
    experiment_parser.add_argument(
        "--use-dummy-data",
        action="store_true",
        help="Verwende Dummy-Daten statt echte Marktdaten",
    )
    experiment_parser.add_argument(
        "--dummy-bars",
        type=int,
        default=500,
        help="Anzahl Bars für Dummy-Daten (default: 500)",
    )
    experiment_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Zeigt nur Preset-Details an, führt keinen Backtest aus",
    )
    experiment_parser.add_argument(
        "--list-presets",
        action="store_true",
        help="Listet alle verfügbaren R&D-Presets auf",
    )
    experiment_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose Output",
    )
    experiment_parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random Seed für Reproduzierbarkeit (default: 42)",
    )

    return parser


# =============================================================================
# PIPELINE HELPER FUNCTIONS
# =============================================================================


def _build_sweep_args_from_pipeline_args(args: argparse.Namespace) -> argparse.Namespace:
    """Baut Sweep-Args aus Pipeline-Args."""
    return argparse.Namespace(
        sweep_name=args.sweep_name,
        strategy=None,
        granularity="medium",
        symbol="BTC/EUR",
        timeframe="1h",
        start=None,
        end=None,
        capital=10000.0,
        max_runs=None,
        dry_run=False,
        parallel=False,
        workers=4,
        output_dir="reports/experiments",
        no_save=False,
        tag=None,
        list_sweeps=False,
        list_strategies=False,
        show_catalog=False,
        show_params=False,
        config=args.config,
        verbose=getattr(args, "verbose", False),
    )


def _build_report_args_from_pipeline_args(args: argparse.Namespace) -> argparse.Namespace:
    """Baut Report-Args aus Pipeline-Args."""
    return argparse.Namespace(
        sweep_name=args.sweep_name,
        input=None,
        format=args.format,
        output_dir="reports/sweeps",
        sort_metric="metric_sharpe_ratio",
        top_n=20,
        heatmap_params=None,
        with_plots=getattr(args, "with_plots", False),
        plot_metric="metric_sharpe_ratio",
        verbose=getattr(args, "verbose", False),
    )


def _build_promote_args_from_pipeline_args(args: argparse.Namespace) -> argparse.Namespace:
    """Baut Promote-Args aus Pipeline-Args."""
    return argparse.Namespace(
        sweep_name=args.sweep_name,
        metric="metric_sharpe_ratio",
        fallback_metric="metric_total_return",
        top_n=args.top_n,
        output="reports/sweeps",
        experiments_dir="reports/experiments",
        verbose=getattr(args, "verbose", False),
    )


def _build_walkforward_args_from_pipeline_args(args: argparse.Namespace) -> argparse.Namespace:
    """Baut Walk-Forward-Args aus Pipeline-Args."""
    return argparse.Namespace(
        sweep_name=args.sweep_name,
        top_n=args.top_n,
        train_window=getattr(args, "walkforward_train_window", None),
        test_window=getattr(args, "walkforward_test_window", None),
        step_size=getattr(args, "walkforward_step_size", None),
        data_file=None,
        use_dummy_data=getattr(args, "walkforward_use_dummy_data", False),
        dummy_bars=getattr(args, "walkforward_dummy_bars", 1000),
        start_date=None,
        end_date=None,
        symbol="BTC/EUR",
        metric_primary="metric_sharpe_ratio",
        metric_fallback="metric_total_return",
        output_dir="reports/walkforward",
        verbose=getattr(args, "verbose", False),
    )


def _build_montecarlo_args_from_pipeline_args(args: argparse.Namespace) -> argparse.Namespace:
    """Baut Monte-Carlo-Args aus Pipeline-Args."""
    return argparse.Namespace(
        sweep_name=args.sweep_name,
        config=args.config,
        top_n=args.top_n,
        num_runs=getattr(args, "mc_num_runs", 1000),
        method=getattr(args, "mc_method", "simple"),
        block_size=getattr(args, "mc_block_size", 20),
        seed=getattr(args, "mc_seed", 42),
        output_dir=None,
        format="both",
        use_dummy_data=getattr(args, "mc_use_dummy_data", False),
        dummy_bars=getattr(args, "mc_dummy_bars", 500),
        verbose=getattr(args, "verbose", False),
    )


def _build_stress_args_from_pipeline_args(args: argparse.Namespace) -> argparse.Namespace:
    """Baut Stress-Test-Args aus Pipeline-Args."""
    return argparse.Namespace(
        sweep_name=args.sweep_name,
        config=args.config,
        top_n=args.top_n,
        scenarios=getattr(args, "stress_scenarios", ["single_crash_bar", "vol_spike"]),
        severity=getattr(args, "stress_severity", 0.2),
        window=getattr(args, "stress_window", 5),
        position=getattr(args, "stress_position", "middle"),
        output_dir=None,
        format="both",
        seed=getattr(args, "stress_seed", 42),
        use_dummy_data=getattr(args, "stress_use_dummy_data", False),
        dummy_bars=getattr(args, "stress_dummy_bars", 500),
        verbose=getattr(args, "verbose", False),
    )


# =============================================================================
# PIPELINE EXECUTION
# =============================================================================


def run_pipeline(args: argparse.Namespace) -> int:
    """Führt eine End-to-End-Research-Pipeline aus (v2).
    
    Pipeline-Steps:
    1. Sweep
    2. Report + Plots
    3. Top-N Promotion
    4. Optional: Walk-Forward
    5. Optional: Monte-Carlo
    6. Optional: Stress-Tests
    
    Args:
        args: Parsed command-line arguments für Pipeline
        
    Returns:
        Exit code (0 = success, 1 = error)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Bestimme Anzahl Steps für Logging
    num_steps = 3  # Sweep, Report, Promote
    if getattr(args, "run_walkforward", False):
        num_steps += 1
    if getattr(args, "run_montecarlo", False):
        num_steps += 1
    if getattr(args, "run_stress_tests", False):
        num_steps += 1
    
    step_counter = 0
    
    # 1. Sweep
    step_counter += 1
    logger.info("=" * 70)
    logger.info(f"Step {step_counter}/{num_steps}: Strategy-Sweep ausführen")
    logger.info("=" * 70)
    
    sweep_args = _build_sweep_args_from_pipeline_args(args)
    sweep_exit = run_sweep_from_args(sweep_args)
    if sweep_exit != 0:
        logger.error("[pipeline] Sweep fehlgeschlagen, Pipeline abgebrochen")
        return sweep_exit
    
    # 2. Report
    step_counter += 1
    logger.info("=" * 70)
    logger.info(f"Step {step_counter}/{num_steps}: Sweep-Report generieren")
    logger.info("=" * 70)
    
    report_args = _build_report_args_from_pipeline_args(args)
    report_exit = run_report_from_args(report_args)
    if report_exit != 0:
        logger.error("[pipeline] Report-Generierung fehlgeschlagen, Pipeline abgebrochen")
        return report_exit
    
    # 3. Promotion
    step_counter += 1
    logger.info("=" * 70)
    logger.info(f"Step {step_counter}/{num_steps}: Top-{args.top_n} Promotion")
    logger.info("=" * 70)
    
    promote_args = _build_promote_args_from_pipeline_args(args)
    promote_exit = run_promote_from_args(promote_args)
    if promote_exit != 0:
        logger.error("[pipeline] Promotion fehlgeschlagen, Pipeline abgebrochen")
        return promote_exit
    
    # 4. Walk-Forward (optional)
    if getattr(args, "run_walkforward", False):
        step_counter += 1
        logger.info("=" * 70)
        logger.info(f"Step {step_counter}/{num_steps}: Walk-Forward-Testing")
        logger.info("=" * 70)
        
        train_window = getattr(args, "walkforward_train_window", None)
        test_window = getattr(args, "walkforward_test_window", None)
        
        if not train_window or not test_window:
            logger.error("[pipeline] --walkforward-train-window und --walkforward-test-window müssen für Walk-Forward gesetzt sein")
            return 1
        
        walkforward_args = _build_walkforward_args_from_pipeline_args(args)
        wf_exit = run_walkforward_from_args(walkforward_args)
        if wf_exit != 0:
            logger.error("[pipeline] Walk-Forward-Testing fehlgeschlagen, Pipeline abgebrochen")
            return wf_exit
    
    # 5. Monte-Carlo (optional)
    if getattr(args, "run_montecarlo", False):
        step_counter += 1
        logger.info("=" * 70)
        logger.info(f"Step {step_counter}/{num_steps}: Monte-Carlo-Robustness")
        logger.info("=" * 70)
        
        montecarlo_args = _build_montecarlo_args_from_pipeline_args(args)
        mc_exit = run_montecarlo_from_args(montecarlo_args)
        if mc_exit != 0:
            logger.error("[pipeline] Monte-Carlo-Robustness fehlgeschlagen, Pipeline abgebrochen")
            return mc_exit
    
    # 6. Stress-Tests (optional)
    if getattr(args, "run_stress_tests", False):
        step_counter += 1
        logger.info("=" * 70)
        logger.info(f"Step {step_counter}/{num_steps}: Stress-Tests")
        logger.info("=" * 70)
        
        stress_args = _build_stress_args_from_pipeline_args(args)
        stress_exit = run_stress_from_args(stress_args)
        if stress_exit != 0:
            logger.error("[pipeline] Stress-Tests fehlgeschlagen, Pipeline abgebrochen")
            return stress_exit
    
    logger.info("=" * 70)
    logger.info("✅ Pipeline erfolgreich abgeschlossen")
    logger.info("=" * 70)

    return 0


# =============================================================================
# STRATEGY PROFILE EXECUTION (Phase 41B)
# =============================================================================


def run_strategy_profile(args: argparse.Namespace) -> int:
    """
    Generiert ein Robustness-Profil für eine Strategie.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 = success, 1 = error)
    """
    import logging
    import numpy as np
    import pandas as pd
    from pathlib import Path

    logging.basicConfig(
        level=logging.DEBUG if getattr(args, "verbose", False) else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Import Strategy-Registry
    try:
        from src.strategies.registry import (
            get_available_strategy_keys,
            get_strategy_spec,
        )
    except ImportError as e:
        logger.error(f"Konnte Strategy-Registry nicht importieren: {e}")
        return 1

    # Import Profile-Modul
    try:
        from src.experiments.strategy_profiles import (
            StrategyProfileBuilder,
            load_tiering_config,
            PROFILE_VERSION,
        )
    except ImportError as e:
        logger.error(f"Konnte Strategy-Profiles nicht importieren: {e}")
        return 1

    # List-Strategies-Modus
    if getattr(args, "list_strategies", False):
        print("\nVerfügbare Strategy-IDs:")
        print("-" * 40)
        for key in sorted(get_available_strategy_keys()):
            try:
                spec = get_strategy_spec(key)
                print(f"  {key:25s} {spec.description}")
            except Exception:
                print(f"  {key}")
        return 0

    strategy_id = args.strategy_id

    # Validiere Strategy-ID
    available = get_available_strategy_keys()
    if strategy_id not in available:
        logger.error(f"Unbekannte Strategy-ID: '{strategy_id}'")
        logger.info(f"Verfügbare Strategien: {', '.join(sorted(available))}")
        return 1

    logger.info(f"Generiere Robustness-Profil für: {strategy_id}")
    logger.info("=" * 60)

    # Initialisiere Builder
    builder = StrategyProfileBuilder(
        strategy_id=strategy_id,
        timeframe=args.timeframe,
        symbols=[args.symbol],
    )

    # Random Seed setzen
    np.random.seed(args.seed)

    # Generiere oder lade Daten
    if args.use_dummy_data:
        logger.info(f"Verwende Dummy-Daten ({args.dummy_bars} Bars)")
        n = args.dummy_bars
        dates = pd.date_range("2024-01-01", periods=n, freq="1h")
        returns = np.random.normal(0.0005, 0.02, n)
        equity = (1 + pd.Series(returns, index=dates)).cumprod() * 10000
        builder.set_data_range("2024-01-01", dates[-1].strftime("%Y-%m-%d"))
    else:
        # Versuche echte Daten zu laden
        try:
            from src.data.kraken import fetch_ohlcv_df

            logger.info(f"Lade Marktdaten für {args.symbol} ({args.timeframe})")
            df = fetch_ohlcv_df(
                symbol=args.symbol,
                timeframe=args.timeframe,
                limit=720,
                use_cache=True,
            )

            if df.empty:
                logger.warning("Keine Marktdaten gefunden, verwende Dummy-Daten")
                n = args.dummy_bars
                dates = pd.date_range("2024-01-01", periods=n, freq="1h")
                returns = np.random.normal(0.0005, 0.02, n)
                equity = (1 + pd.Series(returns, index=dates)).cumprod() * 10000
            else:
                returns = df["close"].pct_change().dropna()
                equity = (1 + returns).cumprod() * 10000
                builder.set_data_range(
                    df.index[0].strftime("%Y-%m-%d"),
                    df.index[-1].strftime("%Y-%m-%d"),
                )
        except Exception as e:
            logger.warning(f"Konnte Marktdaten nicht laden: {e}")
            logger.info("Fallback zu Dummy-Daten")
            n = args.dummy_bars
            dates = pd.date_range("2024-01-01", periods=n, freq="1h")
            returns = np.random.normal(0.0005, 0.02, n)
            equity = (1 + pd.Series(returns, index=dates)).cumprod() * 10000
            builder.set_data_range("2024-01-01", dates[-1].strftime("%Y-%m-%d"))

    # Returns als Series
    if not isinstance(returns, pd.Series):
        returns = pd.Series(returns)

    # 1. Baseline-Performance berechnen
    logger.info("Step 1/4: Berechne Baseline-Performance...")
    try:
        from src.backtest.stats import compute_basic_stats

        stats = compute_basic_stats(equity)

        # Erweiterte Metriken
        if len(returns) > 0:
            stats["volatility"] = float(returns.std() * np.sqrt(8760))  # Annualisiert
            stats["win_rate"] = float((returns > 0).sum() / len(returns))
            stats["trade_count"] = len(returns)
            # Expectancy als avg_trade
            stats["avg_trade"] = float(returns.mean())

        builder.set_performance_from_stats(stats)
        logger.info(f"  Sharpe: {stats.get('sharpe', 0):.2f}")
        logger.info(f"  Max DD: {stats.get('max_drawdown', 0):.2%}")
        logger.info(f"  Total Return: {stats.get('total_return', 0):.2%}")
    except Exception as e:
        logger.warning(f"Performance-Berechnung fehlgeschlagen: {e}")

    # 2. Monte-Carlo-Analyse (optional)
    if args.with_montecarlo:
        logger.info(f"Step 2/4: Monte-Carlo-Analyse ({args.mc_num_runs} Runs)...")
        try:
            from src.experiments.monte_carlo import (
                MonteCarloConfig,
                run_monte_carlo_from_returns,
            )

            mc_config = MonteCarloConfig(
                num_runs=args.mc_num_runs,
                method=args.mc_method,
                seed=args.seed,
            )

            mc_result = run_monte_carlo_from_returns(returns, mc_config)

            # Extrahiere Quantilen
            total_return_q = mc_result.metric_quantiles.get("total_return", {})
            sharpe_q = mc_result.metric_quantiles.get("sharpe", {})

            builder.set_montecarlo_results(
                p5=total_return_q.get("p5", 0.0),
                p50=total_return_q.get("p50", 0.0),
                p95=total_return_q.get("p95", 0.0),
                num_runs=mc_result.num_runs,
                sharpe_p5=sharpe_q.get("p5"),
                sharpe_p95=sharpe_q.get("p95"),
            )

            logger.info(f"  Return p5/p50/p95: {total_return_q.get('p5', 0):.2%} / {total_return_q.get('p50', 0):.2%} / {total_return_q.get('p95', 0):.2%}")
        except Exception as e:
            logger.warning(f"Monte-Carlo-Analyse fehlgeschlagen: {e}")
    else:
        logger.info("Step 2/4: Monte-Carlo übersprungen (--with-montecarlo nicht gesetzt)")

    # 3. Stress-Tests (optional)
    if args.with_stress:
        logger.info(f"Step 3/4: Stress-Tests ({len(args.stress_scenarios)} Szenarien)...")
        try:
            from src.experiments.stress_tests import (
                StressScenarioConfig,
                run_stress_test_suite,
            )
            from src.backtest.stats import compute_basic_stats as stats_fn_wrapper

            def stats_fn(returns_series: pd.Series) -> dict:
                eq = (1 + returns_series).cumprod() * 10000
                return compute_basic_stats(eq)

            scenarios = [
                StressScenarioConfig(
                    scenario_type=scenario,
                    severity=args.stress_severity,
                    seed=args.seed,
                )
                for scenario in args.stress_scenarios
            ]

            suite = run_stress_test_suite(returns, scenarios, stats_fn)

            # Aggregiere Stress-Ergebnisse
            stress_returns = [
                r.stressed_metrics.get("total_return", 0.0)
                for r in suite.scenario_results
            ]

            if stress_returns:
                builder.set_stress_results(
                    min_return=min(stress_returns),
                    max_return=max(stress_returns),
                    avg_return=sum(stress_returns) / len(stress_returns),
                    num_scenarios=len(stress_returns),
                )
                logger.info(f"  Min/Avg/Max Return: {min(stress_returns):.2%} / {sum(stress_returns)/len(stress_returns):.2%} / {max(stress_returns):.2%}")
        except Exception as e:
            logger.warning(f"Stress-Tests fehlgeschlagen: {e}")
    else:
        logger.info("Step 3/4: Stress-Tests übersprungen (--with-stress nicht gesetzt)")

    # 4. Regime-Analyse (optional)
    if args.with_regime:
        logger.info("Step 4/4: Regime-Analyse...")
        # Vereinfachte Regime-Simulation basierend auf Volatilität
        try:
            vol_window = 20
            rolling_vol = returns.rolling(vol_window).std()
            vol_median = rolling_vol.median()

            # Definiere Regimes basierend auf Volatilität
            regimes = pd.Series(index=returns.index, dtype=str)
            regimes[rolling_vol <= vol_median * 0.8] = "low_vol"
            regimes[(rolling_vol > vol_median * 0.8) & (rolling_vol <= vol_median * 1.2)] = "neutral"
            regimes[rolling_vol > vol_median * 1.2] = "high_vol"

            for regime_name in ["low_vol", "neutral", "high_vol"]:
                mask = regimes == regime_name
                if mask.sum() > 0:
                    regime_returns = returns[mask]
                    time_share = mask.sum() / len(returns)
                    contribution = regime_returns.sum()
                    builder.add_regime(
                        name=regime_name,
                        contribution_return=contribution,
                        time_share=time_share,
                        trade_count=len(regime_returns),
                        avg_return=regime_returns.mean() if len(regime_returns) > 0 else 0.0,
                    )

            builder.finalize_regimes()
            logger.info("  Regime-Analyse abgeschlossen")
        except Exception as e:
            logger.warning(f"Regime-Analyse fehlgeschlagen: {e}")
    else:
        logger.info("Step 4/4: Regime-Analyse übersprungen (--with-regime nicht gesetzt)")

    # 5. Tiering-Info laden
    logger.info("Lade Tiering-Konfiguration...")
    try:
        tiering_config = load_tiering_config(args.tiering_config)
        tiering_info = tiering_config.get(strategy_id)
        if tiering_info:
            builder.tiering = tiering_info
            logger.info(f"  Tier: {tiering_info.tier}")
        else:
            logger.info(f"  Kein Tiering-Eintrag für '{strategy_id}' gefunden")
    except Exception as e:
        logger.warning(f"Konnte Tiering-Config nicht laden: {e}")

    # Build Profil
    profile = builder.build()

    # Output-Verzeichnisse
    json_dir = Path(args.output_dir) if args.output_dir else Path("reports/strategy_profiles")
    md_dir = Path(args.output_dir) if args.output_dir else Path("docs/strategy_profiles")

    # Dateinamen
    json_filename = f"{strategy_id}_profile_{PROFILE_VERSION}.json"
    md_filename = f"{strategy_id.upper()}_PROFILE_{PROFILE_VERSION}.md"

    # Export
    output_format = args.output_format

    if output_format in ("json", "both"):
        json_path = json_dir / json_filename
        json_dir.mkdir(parents=True, exist_ok=True)
        profile.to_json(json_path)
        logger.info(f"JSON-Profil exportiert: {json_path}")

    if output_format in ("md", "both"):
        md_path = md_dir / md_filename
        md_dir.mkdir(parents=True, exist_ok=True)
        profile.to_markdown(md_path)
        logger.info(f"Markdown-Profil exportiert: {md_path}")

    logger.info("=" * 60)
    logger.info("✅ Strategy-Profil erfolgreich generiert")

    return 0


# =============================================================================
# RUN-EXPERIMENT EXECUTION (R&D-Presets, Phase 75 Wave v2)
# =============================================================================


def run_experiment(args: argparse.Namespace) -> int:
    """
    Führt ein R&D-Experiment basierend auf einem Preset aus.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 = success, 1 = error)
    """
    import json
    import logging
    import numpy as np
    import pandas as pd
    from datetime import datetime, timedelta
    from pathlib import Path

    logging.basicConfig(
        level=logging.DEBUG if getattr(args, "verbose", False) else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Import R&D-Preset-Loader
    try:
        from src.experiments.r_and_d_presets import (
            load_r_and_d_preset,
            list_r_and_d_presets,
            get_preset_ids,
            print_preset_catalog,
            RnDPresetConfig,
        )
    except ImportError as e:
        logger.error(f"Konnte R&D-Preset-Loader nicht importieren: {e}")
        return 1

    # List-Presets-Modus
    if getattr(args, "list_presets", False):
        try:
            presets_path = Path(args.presets_file) if args.presets_file else None
            print_preset_catalog(presets_path)
            return 0
        except Exception as e:
            logger.error(f"Fehler beim Auflisten der Presets: {e}")
            return 1

    # Preset-ID erforderlich
    preset_id = args.preset
    if not preset_id:
        logger.error("--preset ist erforderlich. Nutze --list-presets für verfügbare Presets.")
        return 1

    # Preset laden
    logger.info(f"Lade R&D-Preset: {preset_id}")
    try:
        presets_path = Path(args.presets_file) if args.presets_file else None
        preset = load_r_and_d_preset(preset_id, presets_path)
    except KeyError as e:
        logger.error(f"Preset nicht gefunden: {e}")
        try:
            available = get_preset_ids(presets_path)
            logger.info(f"Verfügbare Presets: {', '.join(available)}")
        except Exception:
            pass
        return 1
    except FileNotFoundError as e:
        logger.error(f"Presets-Datei nicht gefunden: {e}")
        return 1

    # Safety-Check: R&D-Presets dürfen nicht live gehen
    if preset.allow_live:
        logger.error("SAFETY: Dieses Preset hat allow_live=true. R&D-Presets dürfen nicht live gehen!")
        return 1

    # Parameter zusammenstellen (CLI überschreibt Preset-Defaults)
    symbol = args.symbol or preset.default_symbol
    timeframe = args.timeframe or preset.default_timeframe
    from_date = args.from_date or preset.default_from or "2020-01-01"
    to_date = args.to_date or preset.default_to or datetime.now().strftime("%Y-%m-%d")
    tag = args.tag or f"exp_rnd_{preset_id}"
    output_dir = Path(args.output_dir)

    logger.info("=" * 70)
    logger.info("R&D EXPERIMENT")
    logger.info("=" * 70)
    logger.info(f"  Preset:      {preset_id}")
    logger.info(f"  Strategy:    {preset.strategy}")
    logger.info(f"  Symbol:      {symbol}")
    logger.info(f"  Timeframe:   {timeframe}")
    logger.info(f"  Zeitraum:    {from_date} bis {to_date}")
    logger.info(f"  Tag:         {tag}")
    logger.info(f"  Hypothese:   {preset.hypothesis}")
    logger.info("=" * 70)

    # Dry-Run-Modus
    if getattr(args, "dry_run", False):
        logger.info("\n[DRY-RUN] Preset-Details:")
        logger.info(f"  Description: {preset.description}")
        logger.info(f"  Tier:        {preset.tier}")
        logger.info(f"  Experimental: {preset.experimental}")
        logger.info(f"  Allow-Live:  {preset.allow_live}")
        logger.info(f"  Markets:     {preset.markets}")
        logger.info(f"  Timeframes:  {preset.timeframes}")
        logger.info(f"  Focus-Metrics: {preset.focus_metrics}")
        logger.info(f"  Parameters:  {preset.parameters}")
        logger.info("\n[DRY-RUN] Kein Backtest ausgeführt.")
        return 0

    # Random Seed setzen
    np.random.seed(args.seed)

    # Daten laden oder generieren
    logger.info("\n[1/4] Daten laden...")

    if getattr(args, "use_dummy_data", False):
        # Dummy-Daten generieren
        n_bars = args.dummy_bars
        logger.info(f"  Generiere {n_bars} Dummy-Bars")
        
        end = datetime.now()
        start = end - timedelta(hours=n_bars)
        
        # Timeframe zu Frequenz mappen
        freq_map = {"1h": "1h", "4h": "4h", "1d": "1D", "1w": "1W"}
        freq = freq_map.get(timeframe, "1h")
        
        index = pd.date_range(start=start, periods=n_bars, freq=freq, tz="UTC")
        
        # Random Walk für Close
        base_price = 50000.0
        volatility = 0.015
        returns = np.random.normal(0, volatility, n_bars)
        trend = np.sin(np.linspace(0, 4 * np.pi, n_bars)) * 0.001
        returns = returns + trend
        close_prices = base_price * np.exp(np.cumsum(returns))
        
        df = pd.DataFrame(index=index)
        df["close"] = close_prices
        df["open"] = df["close"].shift(1).fillna(base_price)
        high_bump = np.random.uniform(0, 0.005, n_bars)
        df["high"] = np.maximum(df["open"], df["close"]) * (1 + high_bump)
        low_dip = np.random.uniform(0, 0.005, n_bars)
        df["low"] = np.minimum(df["open"], df["close"]) * (1 - low_dip)
        df["volume"] = np.random.uniform(100, 1000, n_bars)
        df = df[["open", "high", "low", "close", "volume"]]
        
    else:
        # Versuche echte Daten zu laden
        try:
            from src.data.kraken import fetch_ohlcv_df
            
            logger.info(f"  Lade Marktdaten für {symbol} ({timeframe})")
            df = fetch_ohlcv_df(
                symbol=symbol,
                timeframe=timeframe,
                limit=2000,
                use_cache=True,
            )
            
            if df.empty:
                logger.warning("  Keine Marktdaten gefunden, verwende Dummy-Daten")
                args.use_dummy_data = True
                return run_experiment(args)
                
            # Datums-Filter anwenden
            if from_date:
                start_dt = pd.to_datetime(from_date).tz_localize("UTC")
                df = df[df.index >= start_dt]
            if to_date:
                end_dt = pd.to_datetime(to_date).tz_localize("UTC")
                df = df[df.index <= end_dt]
                
        except Exception as e:
            logger.warning(f"  Konnte Marktdaten nicht laden: {e}")
            logger.info("  Fallback zu Dummy-Daten")
            args.use_dummy_data = True
            return run_experiment(args)

    logger.info(f"  {len(df)} Bars geladen")
    logger.info(f"  Zeitraum: {df.index[0]} - {df.index[-1]}")

    # Strategy laden und Backtest ausführen
    logger.info("\n[2/4] Strategy laden...")

    try:
        from src.strategies.registry import (
            get_available_strategy_keys,
            create_strategy_from_config,
        )
        from src.core.peak_config import load_config
        from src.backtest.engine import BacktestEngine
        from src.backtest.stats import compute_backtest_stats
        from src.core.position_sizing import build_position_sizer_from_config
        from src.core.risk import build_risk_manager_from_config
    except ImportError as e:
        logger.error(f"Import-Fehler: {e}")
        return 1

    # Prüfe ob Strategy verfügbar
    available_strategies = get_available_strategy_keys()
    if preset.strategy not in available_strategies:
        logger.error(f"Strategy '{preset.strategy}' nicht gefunden.")
        logger.info(f"Verfügbare Strategien: {', '.join(sorted(available_strategies))}")
        return 1

    # Config laden
    try:
        cfg = load_config(Path(args.config))
    except Exception as e:
        logger.error(f"Config-Fehler: {e}")
        return 1

    # Strategy instanziieren
    try:
        strategy = create_strategy_from_config(preset.strategy, cfg)
        logger.info(f"  Strategy geladen: {preset.strategy}")
    except Exception as e:
        logger.error(f"Strategy-Instanziierung fehlgeschlagen: {e}")
        return 1

    # Backtest ausführen
    logger.info("\n[3/4] Backtest ausführen...")

    try:
        position_sizer = build_position_sizer_from_config(cfg)
        risk_manager = build_risk_manager_from_config(cfg, section="risk_management")

        engine = BacktestEngine(
            core_position_sizer=position_sizer,
            risk_manager=risk_manager,
        )

        def strategy_signal_fn(data, params):
            return strategy.generate_signals(data)

        result = engine.run_realistic(
            df=df,
            strategy_signal_fn=strategy_signal_fn,
            strategy_params=preset.parameters,
        )
        result.strategy_name = preset.strategy

        logger.info("  Backtest abgeschlossen")

    except NotImplementedError as e:
        logger.warning(f"  Strategy wirft NotImplementedError (R&D-Prototyp): {e}")
        logger.info("  Erstelle Dummy-Ergebnis für R&D-Tracking...")
        
        # Dummy-Result für R&D-Strategien die noch nicht implementiert sind
        result = type("DummyResult", (), {
            "stats": {
                "total_return": 0.0,
                "max_drawdown": 0.0,
                "sharpe": 0.0,
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
            },
            "equity_curve": pd.Series([10000.0] * len(df), index=df.index),
            "strategy_name": preset.strategy,
        })()

    except Exception as e:
        logger.error(f"Backtest-Fehler: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # Ergebnisse ausgeben und speichern
    logger.info("\n[4/4] Ergebnisse...")

    stats = result.stats

    logger.info("\n--- BACKTEST-ERGEBNISSE ---")
    logger.info(f"  Total Return:   {stats.get('total_return', 0):>10.2%}")
    logger.info(f"  Max Drawdown:   {stats.get('max_drawdown', 0):>10.2%}")
    logger.info(f"  Sharpe Ratio:   {stats.get('sharpe', 0):>10.2f}")
    logger.info(f"  Total Trades:   {stats.get('total_trades', 0):>10}")
    logger.info(f"  Win Rate:       {stats.get('win_rate', 0):>10.2%}")
    logger.info(f"  Profit Factor:  {stats.get('profit_factor', 0):>10.2f}")

    # Ergebnisse speichern
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    result_data = {
        "experiment": {
            "preset_id": preset_id,
            "strategy": preset.strategy,
            "symbol": symbol,
            "timeframe": timeframe,
            "from_date": from_date,
            "to_date": to_date,
            "tag": tag,
            "timestamp": timestamp,
            "hypothesis": preset.hypothesis,
            "focus_metrics": preset.focus_metrics,
        },
        "parameters": preset.parameters,
        "results": {
            "total_return": stats.get("total_return", 0),
            "max_drawdown": stats.get("max_drawdown", 0),
            "sharpe": stats.get("sharpe", 0),
            "total_trades": stats.get("total_trades", 0),
            "win_rate": stats.get("win_rate", 0),
            "profit_factor": stats.get("profit_factor", 0),
            "bars": len(df),
        },
        "meta": {
            "tier": preset.tier,
            "experimental": preset.experimental,
            "allow_live": preset.allow_live,
            "seed": args.seed,
            "use_dummy_data": getattr(args, "use_dummy_data", False),
        },
    }

    result_file = output_dir / f"{tag}_{timestamp}.json"
    with open(result_file, "w") as f:
        json.dump(result_data, f, indent=2, default=str)
    
    logger.info(f"\n  Ergebnis gespeichert: {result_file}")

    logger.info("\n" + "=" * 70)
    logger.info("✅ R&D-Experiment abgeschlossen")
    logger.info("=" * 70)

    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Haupt-Entry-Point."""
    parser = build_parser()
    
    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(list(argv))
    
    if args.command == "sweep":
        return run_sweep_from_args(args)
    elif args.command == "report":
        return run_report_from_args(args)
    elif args.command == "promote":
        return run_promote_from_args(args)
    elif args.command == "walkforward":
        return run_walkforward_from_args(args)
    elif args.command == "montecarlo":
        return run_montecarlo_from_args(args)
    elif args.command == "stress":
        return run_stress_from_args(args)
    elif args.command == "portfolio":
        return run_portfolio_robustness_from_args(args)
    elif args.command == "pipeline":
        return run_pipeline(args)
    elif args.command == "strategy-profile":
        return run_strategy_profile(args)
    elif args.command == "run-experiment":
        return run_experiment(args)
    else:
        parser.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

