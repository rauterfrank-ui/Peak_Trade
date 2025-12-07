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
    else:
        parser.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

