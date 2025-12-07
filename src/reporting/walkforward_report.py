"""
Peak_Trade Walk-Forward Reporting
==================================

Funktionen zum Erstellen von Markdown-Reports für Walk-Forward-Analysen.

Komponenten:
- build_walkforward_report: Erstellt Report für einzelne WalkForwardResult
- build_multi_config_report: Erstellt Vergleichs-Report für mehrere WalkForwardResult
- save_walkforward_report: Speichert Report als Markdown-Datei

Usage:
    from src.reporting.walkforward_report import (
        build_walkforward_report,
        save_walkforward_report,
    )

    report = build_walkforward_report(result, sweep_name="rsi_reversion_basic")
    save_walkforward_report(report, output_path)
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from .base import Report, ReportSection, format_metric

logger = logging.getLogger(__name__)


# =============================================================================
# SINGLE CONFIG REPORT
# =============================================================================


def build_walkforward_report(
    result: Any,  # WalkForwardResult
    *,
    sweep_name: Optional[str] = None,
    wf_config: Optional[Any] = None,  # WalkForwardConfig
) -> Report:
    """
    Erstellt einen Markdown-Report für ein WalkForwardResult.

    Args:
        result: WalkForwardResult mit Fenster-Ergebnissen
        sweep_name: Optionaler Sweep-Name (für Metadaten)
        wf_config: Optional WalkForwardConfig (für Konfigurations-Details)

    Returns:
        Report-Objekt mit allen Sections

    Example:
        >>> from src.backtest.walkforward import WalkForwardResult
        >>> from src.reporting.walkforward_report import build_walkforward_report
        >>>
        >>> report = build_walkforward_report(result, sweep_name="rsi_reversion_basic")
        >>> print(report.to_markdown())
    """
    # Titel
    title = f"Walk-Forward Analysis: {result.config_id}"
    if result.strategy_name:
        title += f" ({result.strategy_name})"

    report = Report(
        title=title,
        metadata={
            "config_id": result.config_id,
            "strategy_name": result.strategy_name,
            "sweep_name": sweep_name,
            "generated_at": datetime.now().isoformat(),
            "num_windows": len(result.windows),
        },
    )

    # 1. Zusammenfassung
    summary_section = _build_summary_section(result, wf_config)
    report.add_section(summary_section)

    # 2. Aggregierte Metriken
    aggregate_section = _build_aggregate_metrics_section(result)
    report.add_section(aggregate_section)

    # 3. Fenster-Details
    windows_section = _build_windows_table_section(result)
    report.add_section(windows_section)

    # 4. Strategie-Parameter
    if result.config_params:
        params_section = _build_parameters_section(result)
        report.add_section(params_section)

    return report


def _build_summary_section(
    result: Any,  # WalkForwardResult
    wf_config: Optional[Any] = None,  # WalkForwardConfig
) -> ReportSection:
    """Erstellt Summary-Section."""
    lines = []

    # Basis-Info
    lines.append(f"**Config ID:** {result.config_id}")
    lines.append(f"**Strategy:** {result.strategy_name}")
    lines.append(f"**Windows:** {len(result.windows)}")

    # Walk-Forward-Config (falls vorhanden)
    if wf_config:
        lines.append("")
        lines.append("**Walk-Forward Configuration:**")
        lines.append(f"- Train Window: {wf_config.train_window}")
        lines.append(f"- Test Window: {wf_config.test_window}")
        if wf_config.step_size:
            lines.append(f"- Step Size: {wf_config.step_size}")

    # Quick Stats
    if result.aggregate_metrics:
        lines.append("")
        lines.append("**Quick Stats:**")
        avg_sharpe = result.aggregate_metrics.get("avg_sharpe", 0.0)
        avg_return = result.aggregate_metrics.get("avg_return", 0.0)
        win_rate = result.aggregate_metrics.get("win_rate_windows", 0.0)
        lines.append(f"- Avg Sharpe: {avg_sharpe:.2f}")
        lines.append(f"- Avg Return: {avg_return:.2%}")
        lines.append(f"- Win Rate: {win_rate:.1%}")

    return ReportSection(title="Summary", content_markdown="\n".join(lines))


def _build_aggregate_metrics_section(result: Any) -> ReportSection:
    """Erstellt Section mit aggregierten Metriken."""
    if not result.aggregate_metrics:
        return ReportSection(title="Aggregate Metrics", content_markdown="No metrics available.")

    # Tabelle erstellen
    table_lines = ["| Metric | Value |", "|--------|-------|"]

    metrics = result.aggregate_metrics
    metric_order = [
        ("avg_sharpe", "Avg Sharpe"),
        ("avg_return", "Avg Return"),
        ("avg_max_drawdown", "Avg Max Drawdown"),
        ("min_sharpe", "Min Sharpe"),
        ("max_sharpe", "Max Sharpe"),
        ("min_return", "Min Return"),
        ("max_return", "Max Return"),
        ("positive_windows", "Positive Windows"),
        ("total_windows", "Total Windows"),
        ("win_rate_windows", "Win Rate"),
    ]

    for key, label in metric_order:
        if key in metrics:
            value = metrics[key]
            if "return" in key or "drawdown" in key:
                formatted = f"{value:.2%}"
            elif "rate" in key:
                formatted = f"{value:.1%}"
            elif "sharpe" in key:
                formatted = f"{value:.2f}"
            else:
                formatted = str(int(value) if isinstance(value, float) and value.is_integer() else value)
            table_lines.append(f"| {label} | {formatted} |")

    return ReportSection(title="Aggregate Metrics", content_markdown="\n".join(table_lines))


def _build_windows_table_section(result: Any) -> ReportSection:
    """Erstellt Section mit Fenster-Details-Tabelle."""
    if not result.windows:
        return ReportSection(title="Window Details", content_markdown="No windows available.")

    # Tabelle erstellen
    table_lines = [
        "| Window | Train Period | Test Period | Sharpe | Return | Max DD | Trades |",
        "|--------|--------------|-------------|--------|--------|--------|--------|",
    ]

    for window in result.windows:
        train_period = f"{window.train_start.date()} - {window.train_end.date()}"
        test_period = f"{window.test_start.date()} - {window.test_end.date()}"

        metrics = window.metrics
        sharpe = metrics.get("sharpe", 0.0)
        total_return = metrics.get("total_return", 0.0)
        max_drawdown = metrics.get("max_drawdown", 0.0)
        total_trades = metrics.get("total_trades", 0)

        table_lines.append(
            f"| {window.window_index + 1} | {train_period} | {test_period} | "
            f"{sharpe:.2f} | {total_return:.2%} | {max_drawdown:.2%} | {total_trades} |"
        )

    return ReportSection(title="Window Details", content_markdown="\n".join(table_lines))


def _build_parameters_section(result: Any) -> ReportSection:
    """Erstellt Section mit Strategie-Parametern."""
    if not result.config_params:
        return ReportSection(title="Parameters", content_markdown="No parameters available.")

    lines = []
    for key, value in sorted(result.config_params.items()):
        if isinstance(value, float):
            lines.append(f"- **{key}:** {value:.4f}")
        else:
            lines.append(f"- **{key}:** {value}")

    return ReportSection(title="Strategy Parameters", content_markdown="\n".join(lines))


# =============================================================================
# MULTI-CONFIG REPORT
# =============================================================================


def build_multi_config_report(
    results: List[Any],  # List[WalkForwardResult]
    *,
    sweep_name: Optional[str] = None,
) -> Report:
    """
    Erstellt einen Vergleichs-Report für mehrere WalkForwardResult.

    Args:
        results: Liste von WalkForwardResult
        sweep_name: Optionaler Sweep-Name

    Returns:
        Report-Objekt mit Vergleichs-Tabelle

    Example:
        >>> results = [result1, result2, result3]
        >>> report = build_multi_config_report(results, sweep_name="rsi_reversion_basic")
    """
    title = "Walk-Forward Analysis: Top-N Comparison"
    if sweep_name:
        title += f" ({sweep_name})"

    report = Report(
        title=title,
        metadata={
            "sweep_name": sweep_name,
            "num_configs": len(results),
            "generated_at": datetime.now().isoformat(),
        },
    )

    # Vergleichs-Tabelle
    comparison_section = _build_comparison_table_section(results)
    report.add_section(comparison_section)

    return report


def _build_comparison_table_section(results: List[Any]) -> ReportSection:
    """Erstellt Vergleichs-Tabelle für mehrere Konfigurationen."""
    if not results:
        return ReportSection(title="Comparison", content_markdown="No results available.")

    # Tabelle erstellen
    table_lines = [
        "| Config ID | Strategy | Avg Sharpe | Avg Return | Avg Max DD | "
        "Win Rate | Positive Windows | Total Windows |",
        "|-----------|----------|------------|------------|------------|"
        "----------|-----------------|--------------|",
    ]

    for result in results:
        metrics = result.aggregate_metrics
        avg_sharpe = metrics.get("avg_sharpe", 0.0)
        avg_return = metrics.get("avg_return", 0.0)
        avg_max_dd = metrics.get("avg_max_drawdown", 0.0)
        win_rate = metrics.get("win_rate_windows", 0.0)
        positive_windows = int(metrics.get("positive_windows", 0))
        total_windows = int(metrics.get("total_windows", 0))

        table_lines.append(
            f"| {result.config_id} | {result.strategy_name} | "
            f"{avg_sharpe:.2f} | {avg_return:.2%} | {avg_max_dd:.2%} | "
            f"{win_rate:.1%} | {positive_windows} | {total_windows} |"
        )

    return ReportSection(title="Configuration Comparison", content_markdown="\n".join(table_lines))


# =============================================================================
# SAVE FUNCTIONS
# =============================================================================


def save_walkforward_report(
    report: Report,
    output_path: Path,
    *,
    sweep_name: Optional[str] = None,
    config_id: Optional[str] = None,
) -> Path:
    """
    Speichert Walk-Forward-Report als Markdown-Datei.

    Args:
        report: Report-Objekt
        output_path: Ausgabe-Verzeichnis oder vollständiger Pfad
        sweep_name: Optionaler Sweep-Name (für Verzeichnisstruktur)
        config_id: Optionaler Config-ID (für Dateinamen)

    Returns:
        Pfad zur gespeicherten Datei

    Example:
        >>> report = build_walkforward_report(result)
        >>> output_path = save_walkforward_report(
        ...     report,
        ...     Path("reports/walkforward"),
        ...     sweep_name="rsi_reversion_basic",
        ...     config_id="config_1",
        ... )
    """
    # Bestimme vollständigen Pfad
    # Prüfe ob output_path ein Verzeichnispfad ist (kein .md Suffix) oder bereits existiert als Dir
    is_directory_path = output_path.is_dir() or (not output_path.suffix and not output_path.is_file())

    if is_directory_path:
        # Verzeichnisstruktur: reports/walkforward/{sweep_name}/{config_id}_walkforward_YYYYMMDD.md
        if sweep_name:
            output_path = output_path / sweep_name
        output_path.mkdir(parents=True, exist_ok=True)

        # Dateiname
        if config_id:
            filename = f"{config_id}_walkforward_{datetime.now().strftime('%Y%m%d')}.md"
        else:
            filename = f"walkforward_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        output_path = output_path / filename
    else:
        # Vollständiger Pfad übergeben (hat .md oder andere Extension)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Speichere Report
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report.to_markdown())

    logger.info(f"Walk-Forward-Report gespeichert: {output_path}")
    return output_path


