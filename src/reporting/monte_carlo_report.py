# src/reporting/monte_carlo_report.py
"""
Peak_Trade Monte-Carlo Reporting (Phase 45)
============================================

Reporting-Funktionen für Monte-Carlo-Robustness-Analysen.

Komponenten:
- build_monte_carlo_report: Erstellt kompletten Monte-Carlo-Report
- Integration mit bestehender Report-Infrastruktur (Report, ReportSection)

Usage:
    from src.reporting.monte_carlo_report import build_monte_carlo_report
    from src.experiments.monte_carlo import MonteCarloSummaryResult

    summary = run_monte_carlo_from_returns(returns, config)
    paths = build_monte_carlo_report(
        summary,
        title="RSI Reversion Monte-Carlo",
        output_dir=Path("reports/monte_carlo"),
        format="both",
    )
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Literal, Optional

import pandas as pd

from .base import Report, ReportSection, df_to_markdown, format_metric
from .plots import save_histogram

try:
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# =============================================================================
# REPORT BUILDING
# =============================================================================


def build_monte_carlo_report(
    summary: "MonteCarloSummaryResult",  # Forward reference
    *,
    title: str,
    output_dir: Path,
    format: Literal["md", "html", "both"] = "both",
) -> Dict[str, Path]:
    """
    Erzeugt einen Monte-Carlo-Report mit Kennzahlen-Tabellen und Quantilen.

    Args:
        summary: MonteCarloSummaryResult aus run_monte_carlo_from_returns
        title: Report-Titel
        output_dir: Zielverzeichnis für Reports und Plots
        format: Output-Format ("md", "html", oder "both")

    Returns:
        Dict mit Pfaden, z.B. {"md": path_to_md, "html": path_to_html}

    Example:
        >>> from src.experiments.monte_carlo import run_monte_carlo_from_returns, MonteCarloConfig
        >>> summary = run_monte_carlo_from_returns(returns, MonteCarloConfig(num_runs=1000))
        >>> paths = build_monte_carlo_report(
        ...     summary,
        ...     title="RSI Monte-Carlo",
        ...     output_dir=Path("reports/monte_carlo"),
        ...     format="both",
        ... )
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Erstelle Report
    report = Report(
        title=title,
        metadata={
            "num_runs": summary.num_runs,
            "method": summary.config.method,
            "block_size": summary.config.block_size if summary.config.method == "block_bootstrap" else None,
            "seed": summary.config.seed,
        },
    )

    # 1. Overview Section
    overview_lines = [
        f"- **Monte-Carlo Runs:** {summary.num_runs}",
        f"- **Bootstrap-Methode:** {summary.config.method}",
    ]
    if summary.config.method == "block_bootstrap":
        overview_lines.append(f"- **Block-Größe:** {summary.config.block_size}")
    overview_lines.append(
        f"- **Analysierte Metriken:** {len(summary.metric_distributions)}"
    )
    overview_lines.append("")
    overview_lines.append(
        "Diese Analyse basiert auf Bootstrap-Resampling der originalen Returns. "
        "Die Quantilen (p5, p50, p95) geben Konfidenzintervalle für die jeweiligen Metriken an."
    )

    report.add_section(ReportSection(title="Overview", content_markdown="\n".join(overview_lines)))

    # 2. Metric Summary Table
    metric_data: list[Dict[str, any]] = []
    for metric_name, quantiles in summary.metric_quantiles.items():
        metric_data.append({
            "Metric": metric_name,
            "Mean": quantiles["mean"],
            "Std": quantiles["std"],
            "p5": quantiles["p5"],
            "p25": quantiles["p25"],
            "p50": quantiles["p50"],
            "p75": quantiles["p75"],
            "p95": quantiles["p95"],
        })

    if metric_data:
        df_metrics = pd.DataFrame(metric_data)
        # Format für bessere Lesbarkeit
        for col in ["Mean", "Std", "p5", "p25", "p50", "p75", "p95"]:
            if col in df_metrics.columns:
                df_metrics[col] = df_metrics[col].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "-")

        content = df_to_markdown(df_metrics, float_format=".4f")
        report.add_section(ReportSection(
            title="Metric Summary (Quantiles)",
            content_markdown=content,
        ))

    # 3. Visualizations
    charts_content: list[str] = []

    if MATPLOTLIB_AVAILABLE:
        # Erstelle Histogramme für wichtige Metriken
        priority_metrics = ["sharpe", "cagr", "max_drawdown", "total_return", "volatility"]
        for metric_name in priority_metrics:
            if metric_name in summary.metric_distributions:
                dist = summary.metric_distributions[metric_name]
                hist_path = output_dir / f"{metric_name}_distribution.png"

                try:
                    save_histogram(
                        dist.tolist(),
                        hist_path,
                        title=f"{metric_name.title()} Distribution (n={summary.num_runs})",
                        xlabel=metric_name,
                        ylabel="Frequency",
                    )
                    rel_path = os.path.relpath(hist_path, output_dir.parent)
                    charts_content.append(
                        f"### {metric_name.title()} Distribution\n\n![{metric_name} Distribution]({rel_path})"
                    )
                except Exception as e:
                    # Fehler beim Plotting nicht fatal
                    pass

    if charts_content:
        report.add_section(ReportSection(
            title="Distributions",
            content_markdown="\n\n".join(charts_content),
        ))

    # 4. Interpretation Section
    interpretation_lines = [
        "### Interpretation der Quantilen",
        "",
        "- **p5 (5. Perzentil):** Nur 5% der Runs haben einen schlechteren Wert",
        "- **p50 (Median):** 50% der Runs haben einen besseren/schlechteren Wert",
        "- **p95 (95. Perzentil):** 95% der Runs haben einen schlechteren Wert",
        "",
        "Ein robustes Setup sollte:",
        "- Hohen Median (p50) haben",
        "- Kleine Spannweite zwischen p5 und p95 haben (niedrige Unsicherheit)",
        "- Positive p5-Werte für Return-Metriken haben",
    ]

    report.add_section(ReportSection(
        title="Interpretation",
        content_markdown="\n".join(interpretation_lines),
    ))

    # Speichere Report
    paths: Dict[str, Path] = {}

    if format in ("md", "both"):
        md_path = output_dir / "monte_carlo_report.md"
        md_path.write_text(report.to_markdown(), encoding="utf-8")
        paths["md"] = md_path

    if format in ("html", "both"):
        html_path = output_dir / "monte_carlo_report.html"
        html_path.write_text(report.to_html(), encoding="utf-8")
        paths["html"] = html_path

    return paths








