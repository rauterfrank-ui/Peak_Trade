# src/reporting/experiment_report.py
"""
Peak_Trade Experiment/Sweep Reporting (Phase 30)
=================================================

Funktionen zum Erstellen von Markdown-Reports für Parameter-Sweeps und Experiments.

Komponenten:
- summarize_experiment_results: Aggregiert Sweep-Ergebnisse
- build_experiment_report: Erstellt kompletten Experiment-Report

Usage:
    from src.reporting.experiment_report import build_experiment_report

    report = build_experiment_report(
        title="RSI Sweep",
        df=results_df,
        sort_metric="metric_sharpe",
        top_n=20,
        heatmap_params=("param_rsi_window", "param_lower_threshold"),
    )
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import pandas as pd
import numpy as np

from .base import Report, ReportSection, df_to_markdown, format_metric
from .plots import save_heatmap, save_histogram, save_scatter_plot


# =============================================================================
# RESULT SUMMARIZATION
# =============================================================================


def summarize_experiment_results(
    df: pd.DataFrame,
    top_n: int = 20,
    sort_metric: str = "metric_sharpe",
    ascending: bool = False,
) -> Dict[str, pd.DataFrame]:
    """
    Aggregiert Experiment/Sweep-Ergebnisse.

    Args:
        df: DataFrame mit Sweep-Ergebnissen
            - Spalten mit Prefix "param_*" = Parameter
            - Spalten mit Prefix "metric_*" = Metriken
        top_n: Anzahl der Top-Runs für Ranking
        sort_metric: Metrik für Sortierung
        ascending: True = aufsteigend sortieren (z.B. für max_drawdown)

    Returns:
        Dictionary mit:
        - 'summary': DataFrame mit Statistiken (min, max, mean, std) pro Metrik
        - 'top_runs': DataFrame mit Top-N-Runs
        - 'param_stats': DataFrame mit Parameter-Verteilungen
        - 'correlation': DataFrame mit Korrelationen (Params vs. Metriken)

    Example:
        >>> results = summarize_experiment_results(df, top_n=10, sort_metric="metric_sharpe")
        >>> print(results['summary'])
        >>> print(results['top_runs'])
    """
    results: Dict[str, pd.DataFrame] = {}

    # Identifiziere Param- und Metrik-Spalten
    param_cols = [c for c in df.columns if c.startswith("param_")]
    metric_cols = [c for c in df.columns if c.startswith("metric_")]

    # 1. Metrik-Summary (Statistiken)
    if metric_cols:
        summary_data: List[Dict[str, Any]] = []
        for col in metric_cols:
            values = df[col].dropna()
            if len(values) > 0:
                summary_data.append({
                    "metric": col.replace("metric_", ""),
                    "count": len(values),
                    "mean": values.mean(),
                    "std": values.std(),
                    "min": values.min(),
                    "max": values.max(),
                    "median": values.median(),
                    "q25": values.quantile(0.25),
                    "q75": values.quantile(0.75),
                })
        results["summary"] = pd.DataFrame(summary_data)

    # 2. Top-N Runs
    if sort_metric in df.columns:
        top_runs = df.nlargest(top_n, sort_metric) if not ascending else df.nsmallest(top_n, sort_metric)
        # Füge Rank hinzu
        top_runs = top_runs.copy()
        top_runs.insert(0, "rank", range(1, len(top_runs) + 1))
        results["top_runs"] = top_runs
    else:
        # Fallback: erste N Zeilen
        results["top_runs"] = df.head(top_n).copy()

    # 3. Parameter-Statistiken
    if param_cols:
        param_data: List[Dict[str, Any]] = []
        for col in param_cols:
            values = df[col].dropna()
            param_data.append({
                "parameter": col.replace("param_", ""),
                "unique_values": values.nunique(),
                "min": values.min(),
                "max": values.max(),
                "most_common": values.mode().iloc[0] if len(values.mode()) > 0 else None,
            })
        results["param_stats"] = pd.DataFrame(param_data)

    # 4. Korrelation zwischen Parametern und Metriken
    if param_cols and metric_cols:
        corr_data: List[Dict[str, Any]] = []
        for p_col in param_cols:
            for m_col in metric_cols:
                # Nur numerische Korrelationen
                try:
                    corr = df[[p_col, m_col]].dropna().corr().iloc[0, 1]
                    if not pd.isna(corr):
                        corr_data.append({
                            "parameter": p_col.replace("param_", ""),
                            "metric": m_col.replace("metric_", ""),
                            "correlation": corr,
                        })
                except (ValueError, TypeError):
                    pass
        if corr_data:
            results["correlation"] = pd.DataFrame(corr_data)

    return results


def find_best_params(
    df: pd.DataFrame,
    sort_metric: str = "metric_sharpe",
    ascending: bool = False,
) -> Dict[str, Any]:
    """
    Findet die beste Parameter-Kombination.

    Args:
        df: DataFrame mit Sweep-Ergebnissen
        sort_metric: Metrik für Bewertung
        ascending: True = niedrigster Wert ist besser

    Returns:
        Dictionary mit besten Parametern und deren Metriken
    """
    if sort_metric not in df.columns:
        return {}

    if ascending:
        best_idx = df[sort_metric].idxmin()
    else:
        best_idx = df[sort_metric].idxmax()

    best_row = df.loc[best_idx]

    # Extrahiere Parameter
    params = {}
    metrics = {}
    for col, val in best_row.items():
        if col.startswith("param_"):
            params[col.replace("param_", "")] = val
        elif col.startswith("metric_"):
            metrics[col.replace("metric_", "")] = val

    return {
        "params": params,
        "metrics": metrics,
        "sort_metric_value": best_row[sort_metric],
    }


# =============================================================================
# REPORT BUILDING
# =============================================================================


def build_experiment_summary_section(
    summary_df: pd.DataFrame,
    title: str = "Metric Statistics",
) -> ReportSection:
    """
    Erstellt eine Section mit Metrik-Zusammenfassung.

    Args:
        summary_df: DataFrame aus summarize_experiment_results['summary']
        title: Section-Titel

    Returns:
        ReportSection
    """
    if summary_df.empty:
        return ReportSection(title=title, content_markdown="*No metrics available*")

    # Format für bessere Lesbarkeit
    display_df = summary_df.copy()
    for col in ["mean", "std", "min", "max", "median", "q25", "q75"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "-")

    content = df_to_markdown(display_df, float_format=".4f")
    return ReportSection(title=title, content_markdown=content)


def build_top_runs_section(
    top_runs_df: pd.DataFrame,
    title: str = "Top Runs",
    display_columns: Optional[List[str]] = None,
) -> ReportSection:
    """
    Erstellt eine Section mit Top-N-Runs.

    Args:
        top_runs_df: DataFrame mit Top-Runs
        title: Section-Titel
        display_columns: Optionale Liste der anzuzeigenden Spalten

    Returns:
        ReportSection
    """
    if top_runs_df.empty:
        return ReportSection(title=title, content_markdown="*No runs available*")

    display_df = top_runs_df.copy()

    # Wähle Spalten zum Anzeigen
    if display_columns:
        cols = [c for c in display_columns if c in display_df.columns]
        display_df = display_df[cols]
    else:
        # Automatisch: rank, params, wichtige Metriken
        cols = ["rank"]
        cols += [c for c in display_df.columns if c.startswith("param_")]
        # Wichtige Metriken zuerst
        priority_metrics = ["metric_sharpe", "metric_total_return", "metric_max_drawdown", "metric_win_rate"]
        cols += [c for c in priority_metrics if c in display_df.columns]
        # Dann restliche Metriken
        cols += [c for c in display_df.columns if c.startswith("metric_") and c not in cols]
        display_df = display_df[[c for c in cols if c in display_df.columns]]

    # Kürze Spaltennamen für bessere Lesbarkeit
    display_df.columns = [
        c.replace("param_", "").replace("metric_", "") for c in display_df.columns
    ]

    content = df_to_markdown(display_df, max_rows=30)
    return ReportSection(title=title, content_markdown=content)


def build_best_params_section(
    best: Dict[str, Any],
    title: str = "Best Parameters",
) -> ReportSection:
    """
    Erstellt eine Section mit der besten Parameter-Kombination.

    Args:
        best: Dict aus find_best_params()
        title: Section-Titel

    Returns:
        ReportSection
    """
    if not best or "params" not in best:
        return ReportSection(title=title, content_markdown="*No best parameters found*")

    lines: List[str] = []

    # Parameter
    lines.append("**Parameters:**")
    lines.append("")
    lines.append("| Parameter | Value |")
    lines.append("|-----------|-------|")
    for k, v in best["params"].items():
        lines.append(f"| {k} | {v} |")
    lines.append("")

    # Metriken
    lines.append("**Metrics:**")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    for k, v in best.get("metrics", {}).items():
        formatted = format_metric(v, k) if isinstance(v, (int, float)) else str(v)
        lines.append(f"| {k} | {formatted} |")

    return ReportSection(title=title, content_markdown="\n".join(lines))


def build_experiment_report(
    title: str,
    df: pd.DataFrame,
    sort_metric: str = "metric_sharpe",
    ascending: bool = False,
    top_n: int = 20,
    heatmap_params: Optional[Tuple[str, str]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Report:
    """
    Erstellt einen kompletten Experiment/Sweep-Report.

    Args:
        title: Report-Titel
        df: DataFrame mit Sweep-Ergebnissen
            - Spalten mit Prefix "param_*" = Parameter
            - Spalten mit Prefix "metric_*" = Metriken
        sort_metric: Metrik für Sortierung/Ranking
        ascending: True = aufsteigend sortieren (z.B. für max_drawdown)
        top_n: Anzahl der Top-Runs
        heatmap_params: Tuple mit zwei Parameter-Spaltennamen für Heatmap
        output_dir: Verzeichnis für Plot-Dateien
        metadata: Optionale Metadaten

    Returns:
        Report-Objekt

    Example:
        >>> report = build_experiment_report(
        ...     title="RSI Reversion Sweep",
        ...     df=results_df,
        ...     sort_metric="metric_sharpe",
        ...     top_n=20,
        ...     heatmap_params=("param_rsi_window", "param_lower_threshold"),
        ... )
        >>> print(report.to_markdown())
    """
    output_dir = Path(output_dir or "reports/images")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Analysiere Ergebnisse
    summary = summarize_experiment_results(df, top_n=top_n, sort_metric=sort_metric, ascending=ascending)
    best = find_best_params(df, sort_metric=sort_metric, ascending=ascending)

    # Erstelle Report
    report = Report(
        title=title,
        metadata={
            "total_runs": len(df),
            "sort_metric": sort_metric,
            "top_n": top_n,
            **(metadata or {}),
        },
    )

    # 1. Overview Section
    param_cols = [c for c in df.columns if c.startswith("param_")]
    metric_cols = [c for c in df.columns if c.startswith("metric_")]

    overview_lines = [
        f"- **Total Runs:** {len(df)}",
        f"- **Parameters Swept:** {len(param_cols)}",
        f"- **Metrics Collected:** {len(metric_cols)}",
        f"- **Sort Metric:** {sort_metric.replace('metric_', '')}",
    ]
    report.add_section(ReportSection(
        title="Overview",
        content_markdown="\n".join(overview_lines),
    ))

    # 2. Best Parameters
    report.add_section(build_best_params_section(best, title="Best Parameter Combination"))

    # 3. Top Runs
    if "top_runs" in summary:
        report.add_section(build_top_runs_section(
            summary["top_runs"],
            title=f"Top {top_n} Runs by {sort_metric.replace('metric_', '').title()}",
        ))

    # 4. Metric Statistics
    if "summary" in summary:
        report.add_section(build_experiment_summary_section(summary["summary"]))

    # 5. Parameter Statistics
    if "param_stats" in summary:
        content = df_to_markdown(summary["param_stats"])
        report.add_section(ReportSection(title="Parameter Statistics", content_markdown=content))

    # 6. Charts Section
    charts_content: List[str] = []

    # Heatmap
    if heatmap_params and len(heatmap_params) == 2:
        x_param, y_param = heatmap_params
        if x_param in df.columns and y_param in df.columns and sort_metric in df.columns:
            try:
                pivot = df.pivot_table(
                    values=sort_metric,
                    index=y_param,
                    columns=x_param,
                    aggfunc="mean",
                )
                heatmap_path = output_dir / "heatmap.png"
                save_heatmap(
                    pivot,
                    heatmap_path,
                    title=f"{sort_metric.replace('metric_', '')} Heatmap",
                    xlabel=x_param.replace("param_", ""),
                    ylabel=y_param.replace("param_", ""),
                    cbar_label=sort_metric.replace("metric_", ""),
                )
                rel_path = os.path.relpath(heatmap_path, output_dir.parent)
                charts_content.append(f"### Parameter Heatmap\n\n![Heatmap]({rel_path})")
            except Exception:
                pass  # Pivot nicht möglich

    # Metrik-Verteilung
    if sort_metric in df.columns:
        values = df[sort_metric].dropna().tolist()
        if values:
            hist_path = output_dir / "metric_distribution.png"
            save_histogram(
                values,
                hist_path,
                title=f"{sort_metric.replace('metric_', '')} Distribution",
                xlabel=sort_metric.replace("metric_", ""),
            )
            rel_path = os.path.relpath(hist_path, output_dir.parent)
            charts_content.append(f"### Metric Distribution\n\n![Distribution]({rel_path})")

    # Parameter vs. Metrik Scatter (für wichtigste Korrelation)
    if "correlation" in summary and not summary["correlation"].empty:
        corr_df = summary["correlation"]
        best_corr = corr_df.iloc[corr_df["correlation"].abs().argmax()]
        param_col = f"param_{best_corr['parameter']}"
        metric_col = f"metric_{best_corr['metric']}"

        if param_col in df.columns and metric_col in df.columns:
            scatter_path = output_dir / "param_vs_metric.png"
            save_scatter_plot(
                df[param_col].tolist(),
                df[metric_col].tolist(),
                scatter_path,
                title=f"{best_corr['parameter']} vs {best_corr['metric']}",
                xlabel=best_corr["parameter"],
                ylabel=best_corr["metric"],
                show_trend=True,
            )
            rel_path = os.path.relpath(scatter_path, output_dir.parent)
            charts_content.append(
                f"### Parameter vs Metric (r={best_corr['correlation']:.3f})\n\n![Scatter]({rel_path})"
            )

    if charts_content:
        report.add_section(ReportSection(
            title="Visualizations",
            content_markdown="\n\n".join(charts_content),
        ))

    # 7. Correlation Analysis
    if "correlation" in summary and not summary["correlation"].empty:
        corr_df = summary["correlation"].copy()
        corr_df["correlation"] = corr_df["correlation"].apply(lambda x: f"{x:.4f}")
        content = df_to_markdown(corr_df)
        report.add_section(ReportSection(
            title="Parameter-Metric Correlations",
            content_markdown=content,
        ))

    return report


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def save_experiment_report(
    report: Report,
    output_path: Union[str, Path],
    format: str = "markdown",
) -> str:
    """
    Speichert einen Experiment-Report als Datei.

    Args:
        report: Report-Objekt
        output_path: Ausgabe-Pfad
        format: "markdown" oder "html"

    Returns:
        Pfad zur gespeicherten Datei
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format == "html":
        content = report.to_html()
    else:
        content = report.to_markdown()

    output_path.write_text(content, encoding="utf-8")
    return str(output_path)


def load_experiment_results(
    filepath: Union[str, Path],
) -> pd.DataFrame:
    """
    Lädt Experiment-Ergebnisse aus CSV oder Parquet.

    Args:
        filepath: Pfad zur Datei

    Returns:
        DataFrame mit Ergebnissen
    """
    filepath = Path(filepath)

    if filepath.suffix == ".parquet":
        return pd.read_parquet(filepath)
    elif filepath.suffix == ".csv":
        return pd.read_csv(filepath)
    else:
        raise ValueError(f"Unsupported file format: {filepath.suffix}")
