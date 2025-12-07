#!/usr/bin/env python3
"""
Peak_Trade Unified Research CLI
================================

Gebündelte CLI für den gesamten Research-Workflow:
- Strategy-Sweeps (Phase 41)
- Sweep-Reports inkl. Plots & Drawdown-Heatmaps (Phase 43)
- Top-N Promotion (Phase 42)
- Walk-Forward-Testing (Phase 44)

Verwendung:
    # Strategy-Sweep ausführen
    python scripts/research_cli.py sweep --sweep-name rsi_reversion_basic --config config/config.toml

    # Sweep-Report generieren
    python scripts/research_cli.py report --sweep-name rsi_reversion_basic --format both --with-plots

    # Top-N Promotion
    python scripts/research_cli.py promote --sweep-name rsi_reversion_basic --top-n 5

    # Walk-Forward-Testing
    python scripts/research_cli.py walkforward --sweep-name rsi_reversion_basic --top-n 3 --train-window 90d --test-window 30d --use-dummy-data

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

# Extrahiere die Funktionen
run_sweep_from_args = _sweep_module.run_from_args
build_sweep_parser = _sweep_module.build_parser
run_report_from_args = _report_module.run_from_args
build_report_parser = _report_module.build_parser
run_promote_from_args = _promote_module.run_from_args
build_promote_parser = _promote_module.build_parser
run_walkforward_from_args = _walkforward_module.run_from_args
build_walkforward_parser = _walkforward_module.build_parser


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

    # Subparser: pipeline (kombiniert mehrere Schritte)
    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="End-to-End-Research-Pipeline (Sweep → Report → Promotion → optional Walk-Forward).",
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
        choices=["markdown", "html", "both"],
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
        default=None,
        help="Anzahl der Top-Konfigurationen für Promotion (optional, wenn gesetzt → Promotion aktiv)",
    )
    
    # Walk-Forward-Optionen
    pipeline_parser.add_argument(
        "--run-walkforward",
        action="store_true",
        help="Führt Walk-Forward-Tests aus (nur wenn gesetzt)",
    )
    pipeline_parser.add_argument(
        "--train-window", "-t",
        type=str,
        help="Trainingsfenster-Dauer für Walk-Forward (z.B. 90d, 6M)",
    )
    pipeline_parser.add_argument(
        "--test-window",
        type=str,
        help="Testfenster-Dauer für Walk-Forward (z.B. 30d, 1M)",
    )
    pipeline_parser.add_argument(
        "--step-size",
        type=str,
        default=None,
        help="Schrittgröße zwischen Fenstern (default: test-window)",
    )
    pipeline_parser.add_argument(
        "--use-dummy-data",
        action="store_true",
        help="Verwende Dummy-Daten für Walk-Forward-Tests",
    )
    pipeline_parser.add_argument(
        "--dummy-bars",
        type=int,
        default=1000,
        help="Anzahl Bars für Dummy-Daten (default: 1000)",
    )
    
    # Weitere Optionen
    pipeline_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose Output",
    )

    return parser


def run_pipeline(args: argparse.Namespace) -> int:
    """Führt eine End-to-End-Research-Pipeline aus.
    
    Args:
        args: Parsed command-line arguments für Pipeline
        
    Returns:
        Exit code (0 = success, 1 = error)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # 1. Sweep
    logger.info("=" * 70)
    logger.info("Step 1/4: Strategy-Sweep ausführen")
    logger.info("=" * 70)
    
    # Erstelle args für Sweep
    sweep_args = argparse.Namespace(
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
        verbose=args.verbose,
    )
    
    sweep_exit = run_sweep_from_args(sweep_args)
    if sweep_exit != 0:
        logger.error("Sweep fehlgeschlagen, Pipeline abgebrochen")
        return sweep_exit
    
    # 2. Report
    logger.info("=" * 70)
    logger.info("Step 2/4: Sweep-Report generieren")
    logger.info("=" * 70)
    
    # Erstelle args für Report
    report_args = argparse.Namespace(
        sweep_name=args.sweep_name,
        input=None,
        format=args.format,
        output_dir="reports/sweeps",
        sort_metric="metric_sharpe_ratio",
        top_n=20,
        heatmap_params=None,
        with_plots=args.with_plots,
        plot_metric="metric_sharpe_ratio",
        verbose=args.verbose,
    )
    
    report_exit = run_report_from_args(report_args)
    if report_exit != 0:
        logger.error("Report-Generierung fehlgeschlagen, Pipeline abgebrochen")
        return report_exit
    
    # 3. Promotion (nur wenn args.top_n gesetzt)
    if getattr(args, "top_n", None) is not None:
        logger.info("=" * 70)
        logger.info(f"Step 3/4: Top-{args.top_n} Promotion")
        logger.info("=" * 70)
        
        # Erstelle args für Promotion
        promote_args = argparse.Namespace(
            sweep_name=args.sweep_name,
            metric="metric_sharpe_ratio",
            fallback_metric="metric_total_return",
            top_n=args.top_n,
            output="reports/sweeps",
            experiments_dir="reports/experiments",
            verbose=args.verbose,
        )
        
        promote_exit = run_promote_from_args(promote_args)
        if promote_exit != 0:
            logger.error("Promotion fehlgeschlagen, Pipeline abgebrochen")
            return promote_exit
    else:
        logger.info("Step 3/4: Promotion übersprungen (--top-n nicht gesetzt)")
    
    # 4. Walk-Forward (nur wenn args.run_walkforward True)
    if getattr(args, "run_walkforward", False):
        logger.info("=" * 70)
        logger.info("Step 4/4: Walk-Forward-Testing")
        logger.info("=" * 70)
        
        if not args.train_window or not args.test_window:
            logger.error("--train-window und --test-window müssen für Walk-Forward gesetzt sein")
            return 1
        
        # Erstelle args für Walk-Forward
        walkforward_args = argparse.Namespace(
            sweep_name=args.sweep_name,
            top_n=getattr(args, "top_n", 3),
            train_window=args.train_window,
            test_window=args.test_window,
            step_size=args.step_size,
            data_file=None,
            use_dummy_data=args.use_dummy_data,
            dummy_bars=args.dummy_bars,
            start_date=None,
            end_date=None,
            symbol="BTC/EUR",
            metric_primary="metric_sharpe_ratio",
            metric_fallback="metric_total_return",
            output_dir="reports/walkforward",
            verbose=args.verbose,
        )
        
        wf_exit = run_walkforward_from_args(walkforward_args)
        if wf_exit != 0:
            logger.error("Walk-Forward-Testing fehlgeschlagen")
            return wf_exit
    else:
        logger.info("Step 4/4: Walk-Forward-Testing übersprungen (--run-walkforward nicht gesetzt)")
    
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
    elif args.command == "pipeline":
        return run_pipeline(args)
    else:
        parser.error(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

