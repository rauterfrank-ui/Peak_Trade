#!/usr/bin/env python3
"""
Peak_Trade Strategy Sweep Report Generator (Phase 41)
======================================================

Generiert aggregierte Reports für Strategy-Sweeps.

Verwendung:
    # Report für einen spezifischen Sweep generieren
    python scripts/generate_strategy_sweep_report.py --sweep-name rsi_reversion_basic

    # Report aus CSV-Datei generieren
    python scripts/generate_strategy_sweep_report.py --input reports/experiments/rsi_reversion_123.csv

    # Mit Heatmap-Parametern
    python scripts/generate_strategy_sweep_report.py \\
        --sweep-name breakout_basic \\
        --heatmap-params lookback_breakout stop_loss_pct

    # Markdown und HTML Report
    python scripts/generate_strategy_sweep_report.py --sweep-name ma_crossover_basic --format both

Output:
    - reports/sweeps/{sweep_name}_report.md
    - reports/sweeps/{sweep_name}_report.html (optional)
    - reports/sweeps/images/{sweep_name}_heatmap.png
    - reports/sweeps/images/{sweep_name}_distribution.png
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import pandas as pd

# Projekt-Root zum Path hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.reporting.experiment_report import (
    build_experiment_report,
    save_experiment_report,
    load_experiment_results,
    summarize_experiment_results,
    find_best_params,
)
from src.reporting.base import Report, ReportSection
from src.reporting.sweep_visualization import generate_default_sweep_plots


def setup_logging(verbose: bool = False) -> None:
    """Konfiguriert Logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )


def build_parser() -> argparse.ArgumentParser:
    """Erstellt den ArgumentParser für Sweep-Reports."""
    parser = argparse.ArgumentParser(
        description="Peak_Trade Strategy Sweep Report Generator (Phase 41)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Input-Optionen
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--sweep-name", "-s",
        type=str,
        help="Name des Sweeps (sucht nach passenden Ergebnis-Dateien)",
    )
    input_group.add_argument(
        "--input", "-i",
        type=str,
        help="Pfad zur Ergebnis-Datei (CSV oder Parquet)",
    )

    # Report-Optionen
    parser.add_argument(
        "--format", "-f",
        type=str,
        choices=["markdown", "html", "both"],
        default="markdown",
        help="Output-Format (default: markdown)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="reports/sweeps",
        help="Ausgabe-Verzeichnis (default: reports/sweeps)",
    )

    # Analyse-Optionen
    parser.add_argument(
        "--sort-metric",
        type=str,
        default="metric_sharpe_ratio",
        help="Metrik für Sortierung (default: metric_sharpe_ratio)",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="Anzahl Top-Runs im Report (default: 20)",
    )
    parser.add_argument(
        "--heatmap-params",
        type=str,
        nargs=2,
        help="Zwei Parameter für Heatmap (z.B. param_fast_period param_slow_period)",
    )
    parser.add_argument(
        "--with-plots",
        action="store_true",
        help="Erzeugt Visualisierungen (Parameter vs. Metrik, Heatmaps)",
    )
    parser.add_argument(
        "--plot-metric",
        type=str,
        default="metric_sharpe_ratio",
        help="Metrik für Plots (default: metric_sharpe_ratio)",
    )

    # Logging
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose Output",
    )

    return parser


def parse_args() -> argparse.Namespace:
    """Parst Kommandozeilen-Argumente."""
    return build_parser().parse_args()


def find_sweep_results(sweep_name: str, experiments_dir: str = "reports/experiments") -> Optional[Path]:
    """
    Sucht nach der neuesten Ergebnis-Datei für einen Sweep.

    Args:
        sweep_name: Name des Sweeps
        experiments_dir: Verzeichnis mit Experiment-Ergebnissen

    Returns:
        Pfad zur Datei oder None
    """
    exp_dir = Path(experiments_dir)
    if not exp_dir.exists():
        return None

    # Suche nach passenden CSV-Dateien (mit sweep_name im Dateinamen)
    pattern = f"*{sweep_name}*.csv"
    matches = sorted(exp_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)

    if matches:
        return matches[0]

    # Suche nach Parquet-Dateien
    pattern = f"*{sweep_name}*.parquet"
    matches = sorted(exp_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)

    if matches:
        return matches[0]

    # Fallback: Versuche strategy_name zu extrahieren (z.B. "rsi_reversion" aus "rsi_reversion_basic")
    # Dies hilft bei alten Dateien oder wenn der Name leicht anders ist
    parts = sweep_name.split("_")
    if len(parts) >= 2:
        # Versuche mit strategy_name (z.B. "rsi_reversion" aus "rsi_reversion_basic")
        strategy_name = "_".join(parts[:-1])  # Alles außer dem letzten Teil
        pattern = f"*{strategy_name}*.csv"
        matches = sorted(exp_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        if matches:
            return matches[0]

    return None


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalisiert Spaltennamen für konsistente Verarbeitung.

    Fügt param_/metric_ Prefixe hinzu wenn nötig.
    """
    # Bekannte Parameter-Namen (ohne Prefix)
    known_params = [
        "fast_period", "slow_period", "rsi_period", "oversold_level", "overbought_level",
        "lookback_breakout", "stop_loss_pct", "take_profit_pct", "trailing_stop_pct",
        "vol_window", "vol_percentile_low", "vol_percentile_high", "entry_period",
        "exit_period", "lookback", "threshold", "period", "num_std", "atr_period",
        "atr_multiplier", "adx_period", "adx_threshold", "entry_z_score", "exit_z_score",
    ]

    # Bekannte Metrik-Namen (ohne Prefix)
    known_metrics = [
        "total_return", "sharpe_ratio", "sharpe", "max_drawdown", "win_rate",
        "num_trades", "profit_factor", "cagr", "sortino_ratio", "calmar_ratio",
    ]

    rename_map = {}
    for col in df.columns:
        if col in known_params and not col.startswith("param_"):
            rename_map[col] = f"param_{col}"
        elif col in known_metrics and not col.startswith("metric_"):
            rename_map[col] = f"metric_{col}"

    if rename_map:
        df = df.rename(columns=rename_map)

    return df


def build_sweep_summary_section(
    df: pd.DataFrame,
    sweep_name: str,
) -> ReportSection:
    """
    Erstellt eine Summary-Section für den Sweep.
    """
    param_cols = [c for c in df.columns if c.startswith("param_")]
    metric_cols = [c for c in df.columns if c.startswith("metric_")]

    lines = [
        f"**Sweep Name:** {sweep_name}",
        "",
        f"**Total Runs:** {len(df)}",
        f"**Parameters Swept:** {len(param_cols)}",
        f"**Metrics Collected:** {len(metric_cols)}",
        "",
        "**Parameter Ranges:**",
    ]

    for col in param_cols:
        param_name = col.replace("param_", "")
        values = df[col].dropna()
        if len(values) > 0:
            unique = values.nunique()
            min_val = values.min()
            max_val = values.max()
            lines.append(f"- `{param_name}`: {unique} values ({min_val} - {max_val})")

    return ReportSection(
        title="Sweep Overview",
        content_markdown="\n".join(lines),
    )


def build_constraint_analysis_section(
    df: pd.DataFrame,
) -> Optional[ReportSection]:
    """
    Analysiert potentielle Constraints zwischen Parametern.
    """
    param_cols = [c for c in df.columns if c.startswith("param_")]

    if len(param_cols) < 2:
        return None

    lines = ["**Potential Parameter Relationships:**", ""]

    # Prüfe auf typische Constraints
    constraints_found = []

    # Fast < Slow Constraint
    if "param_fast_period" in df.columns and "param_slow_period" in df.columns:
        all_valid = (df["param_fast_period"] < df["param_slow_period"]).all()
        if all_valid:
            constraints_found.append("fast_period < slow_period (enforced)")

    # Oversold < Overbought Constraint
    if "param_oversold_level" in df.columns and "param_overbought_level" in df.columns:
        all_valid = (df["param_oversold_level"] < df["param_overbought_level"]).all()
        if all_valid:
            constraints_found.append("oversold_level < overbought_level (enforced)")

    # Vol Percentile Constraint
    if "param_vol_percentile_low" in df.columns and "param_vol_percentile_high" in df.columns:
        all_valid = (df["param_vol_percentile_low"] < df["param_vol_percentile_high"]).all()
        if all_valid:
            constraints_found.append("vol_percentile_low < vol_percentile_high (enforced)")

    if constraints_found:
        for c in constraints_found:
            lines.append(f"- {c}")
        return ReportSection(
            title="Constraint Analysis",
            content_markdown="\n".join(lines),
        )

    return None


def build_recommendations_section(
    df: pd.DataFrame,
    sort_metric: str = "metric_sharpe_ratio",
) -> ReportSection:
    """
    Erstellt eine Empfehlungs-Section basierend auf den Ergebnissen.
    """
    lines = ["Based on the sweep results, here are recommendations:", ""]

    # Beste Parameter finden
    best = find_best_params(df, sort_metric=sort_metric, ascending=False)

    if best and "params" in best:
        lines.append("**Recommended Parameters (Best Sharpe):**")
        lines.append("```")
        for k, v in best["params"].items():
            lines.append(f"{k} = {v}")
        lines.append("```")
        lines.append("")

        # Performance
        if "metrics" in best:
            lines.append("**Expected Performance:**")
            for metric_name in ["sharpe_ratio", "total_return", "max_drawdown", "win_rate"]:
                if metric_name in best["metrics"]:
                    val = best["metrics"][metric_name]
                    if "return" in metric_name or "drawdown" in metric_name or "rate" in metric_name:
                        lines.append(f"- {metric_name}: {val*100:.2f}%")
                    else:
                        lines.append(f"- {metric_name}: {val:.3f}")

    # Robustheits-Check
    lines.append("")
    lines.append("**Robustness Notes:**")

    # Prüfe Varianz in Top-10
    if sort_metric in df.columns:
        top_10 = df.nlargest(10, sort_metric)
        metric_std = top_10[sort_metric].std()
        metric_mean = top_10[sort_metric].mean()
        cv = metric_std / metric_mean if metric_mean != 0 else 0

        if cv < 0.1:
            lines.append("- Top parameters show LOW variance (stable)")
        elif cv < 0.3:
            lines.append("- Top parameters show MODERATE variance")
        else:
            lines.append("- Top parameters show HIGH variance (less stable)")

    return ReportSection(
        title="Recommendations",
        content_markdown="\n".join(lines),
    )


def run_from_args(args: argparse.Namespace) -> int:
    """Generiert einen Sweep-Report basierend auf Argumenten.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 = success, 1 = error)
    """
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Input-Datei finden
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Fehler: Datei nicht gefunden: {input_path}")
            return 1
        sweep_name = input_path.stem
    else:
        input_path = find_sweep_results(args.sweep_name)
        if input_path is None:
            print(f"Fehler: Keine Ergebnisse gefunden für Sweep '{args.sweep_name}'")
            print(f"\nTipp: Führe zuerst einen Sweep aus:")
            print(f"  python scripts/run_strategy_sweep.py --sweep-name {args.sweep_name}")
            return 1
        sweep_name = args.sweep_name

    logger.info(f"Lade Ergebnisse aus: {input_path}")

    # Daten laden
    try:
        df = load_experiment_results(input_path)
    except Exception as e:
        print(f"Fehler beim Laden der Daten: {e}")
        return 1

    # Spaltennamen normalisieren
    df = normalize_column_names(df)

    logger.info(f"Geladen: {len(df)} Runs")

    # Sort-Metrik validieren
    sort_metric = args.sort_metric
    if not sort_metric.startswith("metric_"):
        sort_metric = f"metric_{sort_metric}"

    if sort_metric not in df.columns:
        # Versuche Alternativen
        alternatives = ["metric_sharpe_ratio", "metric_sharpe", "metric_total_return"]
        for alt in alternatives:
            if alt in df.columns:
                sort_metric = alt
                logger.warning(f"Metrik '{args.sort_metric}' nicht gefunden, verwende: {sort_metric}")
                break
        else:
            print(f"Fehler: Keine gültige Sort-Metrik gefunden")
            print(f"Verfügbare Metriken: {[c for c in df.columns if c.startswith('metric_')]}")
            return 1

    # Output-Verzeichnis erstellen
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Heatmap-Parameter
    heatmap_params: Optional[Tuple[str, str]] = None
    if args.heatmap_params:
        p1, p2 = args.heatmap_params
        # Normalisiere zu param_* Format
        if not p1.startswith("param_"):
            p1 = f"param_{p1}"
        if not p2.startswith("param_"):
            p2 = f"param_{p2}"

        if p1 in df.columns and p2 in df.columns:
            heatmap_params = (p1, p2)
        else:
            logger.warning(f"Heatmap-Parameter nicht gefunden: {args.heatmap_params}")

    # Report erstellen
    logger.info("Erstelle Report...")

    report = build_experiment_report(
        title=f"Strategy Sweep Report: {sweep_name}",
        df=df,
        sort_metric=sort_metric,
        ascending=False,
        top_n=args.top_n,
        heatmap_params=heatmap_params,
        output_dir=images_dir,
        metadata={
            "sweep_name": sweep_name,
            "input_file": str(input_path),
            "generated_at": datetime.now().isoformat(),
            "phase": "41",
        },
    )

    # Zusätzliche Sections hinzufügen
    constraint_section = build_constraint_analysis_section(df)
    if constraint_section:
        report.sections.insert(1, constraint_section)

    recommendations = build_recommendations_section(df, sort_metric)
    report.sections.append(recommendations)

    # Visualisierungen erzeugen (falls gewünscht)
    if args.with_plots:
        logger.info("Erstelle Visualisierungen...")
        try:
            # Extrahiere Parameter-Spalten
            param_cols = [c.replace("param_", "") for c in df.columns if c.startswith("param_")]
            
            # Erzeuge Plots
            plots = generate_default_sweep_plots(
                df=df,
                sweep_name=sweep_name,
                output_dir=images_dir,
                param_candidates=param_cols[:3] if param_cols else None,  # Erste 3 Parameter
                metric_primary=args.plot_metric,
                metric_fallback=args.sort_metric,
            )

            # Füge Visualisierungen zum Report hinzu
            if plots:
                plots_content = []
                
                # 1D-Plots
                for plot_name, plot_path in plots.items():
                    if plot_name.startswith("param_") and plot_name.endswith("_vs_metric"):
                        # Relativer Pfad vom Report-Verzeichnis
                        rel_path = plot_path.relative_to(output_dir)
                        param_display = plot_name.replace("param_", "").replace("_vs_metric", "").replace("_", " ").title()
                        plots_content.append(f"### {param_display} vs Metrik")
                        plots_content.append(f"![{param_display} vs Metrik]({rel_path})")
                        plots_content.append("")

                # 2D-Heatmap
                if "heatmap_2d" in plots:
                    rel_path = plots["heatmap_2d"].relative_to(output_dir)
                    plots_content.append("### Parameter Heatmap (2D)")
                    plots_content.append(f"![Parameter Heatmap]({rel_path})")
                    plots_content.append("")

                # Drawdown-Heatmaps
                drawdown_heatmaps = {k: v for k, v in plots.items() if "drawdown" in k.lower() and "heatmap" in k.lower()}
                if drawdown_heatmaps:
                    plots_content.append("### Drawdown-Heatmaps (Max-Drawdown über Parameter-Raum)")
                    plots_content.append("")
                    for plot_name, plot_path in drawdown_heatmaps.items():
                        rel_path = plot_path.relative_to(output_dir)
                        # Extrahiere Parameter-Namen aus dem Plot-Namen
                        # Format: drawdown_heatmap_{param_x}_vs_{param_y}
                        if "drawdown_heatmap_" in plot_name:
                            param_part = plot_name.replace("drawdown_heatmap_", "").replace("_vs_", " × ")
                            title = f"Drawdown-Heatmap: {param_part.replace('_', ' ').title()}"
                        else:
                            title = "Drawdown-Heatmap"
                        plots_content.append(f"#### {title}")
                        plots_content.append(f"![{title}]({rel_path})")
                        plots_content.append("")

                if plots_content:
                    # Prüfe ob bereits eine Visualizations-Section existiert
                    existing_viz_idx = None
                    for idx, section in enumerate(report.sections):
                        if section.title.lower() in ["visualizations", "visualisierungen"]:
                            existing_viz_idx = idx
                            break

                    if existing_viz_idx is not None:
                        # Erweitere bestehende Section
                        existing_content = report.sections[existing_viz_idx].content_markdown
                        report.sections[existing_viz_idx].content_markdown = (
                            existing_content + "\n\n" + "\n".join(plots_content)
                        )
                        logger.info(f"{len(plots)} Visualisierungen zur bestehenden Section hinzugefügt")
                    else:
                        # Neue Section hinzufügen
                        visualization_section = ReportSection(
                            title="Visualizations",
                            content_markdown="\n".join(plots_content),
                        )
                        # Füge vor Recommendations ein
                        report.sections.insert(-1, visualization_section)
                        logger.info(f"{len(plots)} Visualisierungen zum Report hinzugefügt")
                else:
                    logger.warning("Keine Plots erzeugt")
            else:
                logger.warning("Keine Plots erzeugt (möglicherweise fehlende Parameter/Metriken)")

        except Exception as e:
            logger.warning(f"Fehler beim Erstellen der Visualisierungen: {e}")
            # Füge trotzdem eine Notiz hinzu
            error_section = ReportSection(
                title="Visualisierungen",
                content_markdown="Visualisierungen konnten nicht erzeugt werden. Bitte prüfe die Logs.",
            )
            report.sections.append(error_section)

    # Report speichern
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.format in ["markdown", "both"]:
        md_path = output_dir / f"{sweep_name}_report_{timestamp}.md"
        save_experiment_report(report, md_path, format="markdown")
        print(f"Markdown-Report gespeichert: {md_path}")

    if args.format in ["html", "both"]:
        html_path = output_dir / f"{sweep_name}_report_{timestamp}.html"
        save_experiment_report(report, html_path, format="html")
        print(f"HTML-Report gespeichert: {html_path}")

    # Summary ausgeben
    print("\n" + "=" * 70)
    print(f"Strategy Sweep Report: {sweep_name}")
    print("=" * 70)
    print(f"Runs analysiert:   {len(df)}")

    # Top-3 kurz anzeigen
    summary = summarize_experiment_results(df, top_n=3, sort_metric=sort_metric)
    if "top_runs" in summary:
        print(f"\nTop 3 nach {sort_metric.replace('metric_', '')}:")
        for i, (_, row) in enumerate(summary["top_runs"].iterrows(), 1):
            metric_val = row.get(sort_metric, float("nan"))
            print(f"  {i}. {sort_metric.replace('metric_', '')}: {metric_val:.4f}")

    best = find_best_params(df, sort_metric=sort_metric)
    if best and "params" in best:
        print(f"\nBeste Parameter:")
        for k, v in best["params"].items():
            print(f"  {k}: {v}")

    print("\n" + "=" * 70)

    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Haupt-Entry-Point."""
    parser = build_parser()
    if argv is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(list(argv))
    return run_from_args(args)


if __name__ == "__main__":
    sys.exit(main())
