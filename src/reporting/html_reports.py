# src/reporting/html_reports.py
"""
Peak_Trade – HTML Reporting v2 (Phase 21)
==========================================
Generiert statische HTML-Reports für Experimente und Sweeps.

Hauptkomponenten:
- ReportFigure, ReportTable, ReportSection, HtmlReport: Dataclasses für Report-Struktur
- HtmlReportBuilder: Zentrale Klasse zum Erzeugen von HTML-Reports
- Hilfsfunktionen für Equity-Plots, Drawdown-Plots, Parameter-Heatmaps

WICHTIG: Nur lesender Zugriff auf Registry/Analytics-Daten.
Keine Order-/Execution-Pfade werden verändert.

Usage:
    from src.reporting.html_reports import HtmlReportBuilder
    from src.analytics.explorer import ExperimentExplorer

    explorer = ExperimentExplorer()
    summary = explorer.get_experiment_details(experiment_id)

    builder = HtmlReportBuilder(output_dir=Path("reports"))
    report_path = builder.build_experiment_report(summary)
    print(f"Report: {report_path}")
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, TYPE_CHECKING

import numpy as np
import pandas as pd

try:
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None  # type: ignore

if TYPE_CHECKING:
    from src.analytics.explorer import ExperimentSummary, RankedExperiment, SweepOverview


# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass
class ReportFigure:
    """
    Repräsentiert eine Grafik im Report.

    Attributes:
        title: Titel der Grafik
        description: Optionale Beschreibung
        image_path: Relativer Pfad zum PNG (relativ zum HTML-Report)
    """

    title: str
    description: Optional[str] = None
    image_path: str = ""


@dataclass
class ReportTable:
    """
    Repräsentiert eine Tabelle im Report.

    Attributes:
        title: Titel der Tabelle
        description: Optionale Beschreibung
        headers: Liste der Spaltenüberschriften
        rows: Liste von Zeilen (jede Zeile ist eine Liste von String-Werten)
    """

    title: str
    description: Optional[str] = None
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)


@dataclass
class ReportSection:
    """
    Repräsentiert einen Abschnitt im Report.

    Attributes:
        title: Titel des Abschnitts
        description: Optionale Beschreibung
        figures: Liste von ReportFigure-Objekten
        tables: Liste von ReportTable-Objekten
        extra_html: Optionaler zusätzlicher HTML-Code
    """

    title: str
    description: Optional[str] = None
    figures: List[ReportFigure] = field(default_factory=list)
    tables: List[ReportTable] = field(default_factory=list)
    extra_html: Optional[str] = None


@dataclass
class HtmlReport:
    """
    Repräsentiert einen vollständigen HTML-Report.

    Attributes:
        title: Titel des Reports
        experiment_id: Optionale Experiment-ID
        sweep_name: Optionaler Sweep-Name
        created_at: Erstellungszeitpunkt
        sections: Liste von ReportSection-Objekten
        metadata: Zusätzliche Metadaten
    """

    title: str
    experiment_id: Optional[str] = None
    sweep_name: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    sections: List[ReportSection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# HTML TEMPLATES (inline, keine externe Template-Engine)
# =============================================================================


_CSS_STYLES = """
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f8f9fa;
    --text-primary: #212529;
    --text-secondary: #6c757d;
    --border-color: #dee2e6;
    --accent-color: #0d6efd;
    --success-color: #198754;
    --danger-color: #dc3545;
    --warning-color: #ffc107;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background-color: var(--bg-secondary);
    color: var(--text-primary);
    line-height: 1.6;
    padding: 20px;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    background-color: var(--bg-primary);
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    padding: 30px;
}

header {
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 20px;
    margin-bottom: 30px;
}

header h1 {
    font-size: 2rem;
    color: var(--text-primary);
    margin-bottom: 10px;
}

header .meta {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

header .meta span {
    margin-right: 20px;
}

section {
    margin-bottom: 40px;
}

section h2 {
    font-size: 1.5rem;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 10px;
    margin-bottom: 20px;
}

section h3 {
    font-size: 1.2rem;
    color: var(--text-primary);
    margin: 20px 0 10px 0;
}

section p {
    color: var(--text-secondary);
    margin-bottom: 15px;
}

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.metric-card {
    background-color: var(--bg-secondary);
    border-radius: 8px;
    padding: 20px;
    text-align: center;
}

.metric-card .label {
    font-size: 0.85rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.metric-card .value {
    font-size: 1.8rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-top: 5px;
}

.metric-card .value.positive {
    color: var(--success-color);
}

.metric-card .value.negative {
    color: var(--danger-color);
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
    font-size: 0.95rem;
}

table thead {
    background-color: var(--bg-secondary);
}

table th, table td {
    padding: 12px 15px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}

table th {
    font-weight: 600;
    color: var(--text-primary);
}

table tbody tr:hover {
    background-color: var(--bg-secondary);
}

.figure-container {
    margin: 20px 0;
    text-align: center;
}

.figure-container img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.figure-container .caption {
    margin-top: 10px;
    font-size: 0.9rem;
    color: var(--text-secondary);
}

footer {
    border-top: 1px solid var(--border-color);
    padding-top: 20px;
    margin-top: 40px;
    text-align: center;
    color: var(--text-secondary);
    font-size: 0.85rem;
}

.badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 500;
}

.badge-primary {
    background-color: var(--accent-color);
    color: white;
}

.badge-success {
    background-color: var(--success-color);
    color: white;
}

.badge-danger {
    background-color: var(--danger-color);
    color: white;
}

.params-list {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 15px 0;
}

.param-item {
    background-color: var(--bg-secondary);
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 0.9rem;
}

.param-item .key {
    font-weight: 600;
    color: var(--text-primary);
}

.param-item .value {
    color: var(--text-secondary);
}
"""


def _html_escape(text: str) -> str:
    """Escaped HTML-Sonderzeichen."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _format_percent(value: Optional[float], decimals: int = 2) -> str:
    """Formatiert einen Wert als Prozent."""
    if value is None:
        return "-"
    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except (ValueError, TypeError):
        return "-"


def _format_float(value: Optional[float], decimals: int = 2) -> str:
    """Formatiert einen Float-Wert."""
    if value is None:
        return "-"
    try:
        return f"{float(value):.{decimals}f}"
    except (ValueError, TypeError):
        return "-"


def _render_table(table: ReportTable) -> str:
    """Rendert eine ReportTable als HTML."""
    lines = []
    lines.append(f"<h3>{_html_escape(table.title)}</h3>")
    if table.description:
        lines.append(f"<p>{_html_escape(table.description)}</p>")

    lines.append("<table>")
    lines.append("<thead><tr>")
    for header in table.headers:
        lines.append(f"<th>{_html_escape(header)}</th>")
    lines.append("</tr></thead>")

    lines.append("<tbody>")
    for row in table.rows:
        lines.append("<tr>")
        for cell in row:
            lines.append(f"<td>{_html_escape(cell)}</td>")
        lines.append("</tr>")
    lines.append("</tbody>")
    lines.append("</table>")

    return "\n".join(lines)


def _render_figure(figure: ReportFigure) -> str:
    """Rendert eine ReportFigure als HTML."""
    lines = []
    lines.append('<div class="figure-container">')
    lines.append(
        f'<img src="{_html_escape(figure.image_path)}" alt="{_html_escape(figure.title)}">'
    )
    caption_parts = [figure.title]
    if figure.description:
        caption_parts.append(figure.description)
    lines.append(f'<div class="caption">{_html_escape(" - ".join(caption_parts))}</div>')
    lines.append("</div>")
    return "\n".join(lines)


def _render_section(section: ReportSection) -> str:
    """Rendert eine ReportSection als HTML."""
    lines = []
    lines.append("<section>")
    lines.append(f"<h2>{_html_escape(section.title)}</h2>")
    if section.description:
        lines.append(f"<p>{_html_escape(section.description)}</p>")

    for figure in section.figures:
        lines.append(_render_figure(figure))

    for table in section.tables:
        lines.append(_render_table(table))

    if section.extra_html:
        lines.append(section.extra_html)

    lines.append("</section>")
    return "\n".join(lines)


def _render_html_report(report: HtmlReport) -> str:
    """Rendert einen kompletten HtmlReport als HTML-String."""
    lines = []
    lines.append("<!DOCTYPE html>")
    lines.append('<html lang="en">')
    lines.append("<head>")
    lines.append('<meta charset="UTF-8">')
    lines.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    lines.append(f"<title>{_html_escape(report.title)}</title>")
    lines.append(f"<style>{_CSS_STYLES}</style>")
    lines.append("</head>")
    lines.append("<body>")
    lines.append('<div class="container">')

    # Header
    lines.append("<header>")
    lines.append(f"<h1>{_html_escape(report.title)}</h1>")
    lines.append('<div class="meta">')
    if report.experiment_id:
        lines.append(
            f"<span><strong>Experiment:</strong> {_html_escape(report.experiment_id[:12])}...</span>"
        )
    if report.sweep_name:
        lines.append(f"<span><strong>Sweep:</strong> {_html_escape(report.sweep_name)}</span>")
    lines.append(
        f"<span><strong>Generated:</strong> {report.created_at.strftime('%Y-%m-%d %H:%M:%S')}</span>"
    )
    lines.append("</div>")
    lines.append("</header>")

    # Sections
    for section in report.sections:
        lines.append(_render_section(section))

    # Footer
    lines.append("<footer>")
    lines.append("<p>Generated by Peak_Trade Reporting v2</p>")
    lines.append("</footer>")

    lines.append("</div>")
    lines.append("</body>")
    lines.append("</html>")

    return "\n".join(lines)


# =============================================================================
# PLOT FUNCTIONS
# =============================================================================


def plot_equity_curve(
    equity: pd.Series,
    title: str = "Equity Curve",
    output_path: Optional[Path] = None,
    figsize: tuple = (12, 6),
) -> Optional[Path]:
    """
    Erstellt einen Equity-Kurven-Plot.

    Args:
        equity: Equity-Series mit DatetimeIndex
        title: Plot-Titel
        output_path: Pfad zum Speichern (PNG)
        figsize: Figure-Größe

    Returns:
        Pfad zur gespeicherten PNG-Datei oder None
    """
    if not MATPLOTLIB_AVAILABLE or equity is None or len(equity) == 0:
        return None

    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(equity.index, equity.values, color="#0d6efd", linewidth=1.5, label="Equity")
    ax.fill_between(equity.index, equity.values, alpha=0.1, color="#0d6efd")

    # Start-Linie
    ax.axhline(equity.iloc[0], color="gray", linestyle="--", linewidth=1, alpha=0.5, label="Start")

    ax.set_xlabel("Date")
    ax.set_ylabel("Equity")
    ax.set_title(title)
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    # X-Achse formatieren
    if isinstance(equity.index, pd.DatetimeIndex):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.xticks(rotation=45)

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return output_path

    plt.close(fig)
    return None


def plot_drawdown(
    equity: pd.Series,
    title: str = "Drawdown",
    output_path: Optional[Path] = None,
    figsize: tuple = (12, 4),
) -> Optional[Path]:
    """
    Erstellt einen Drawdown-Plot.

    Args:
        equity: Equity-Series mit DatetimeIndex
        title: Plot-Titel
        output_path: Pfad zum Speichern (PNG)
        figsize: Figure-Größe

    Returns:
        Pfad zur gespeicherten PNG-Datei oder None
    """
    if not MATPLOTLIB_AVAILABLE or equity is None or len(equity) == 0:
        return None

    # Drawdown berechnen
    running_max = equity.cummax()
    drawdown = (equity - running_max) / running_max

    fig, ax = plt.subplots(figsize=figsize)

    ax.fill_between(drawdown.index, drawdown.values, 0, color="#dc3545", alpha=0.3)
    ax.plot(drawdown.index, drawdown.values, color="#dc3545", linewidth=1)

    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    # Y-Achse als Prozent formatieren
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))

    if isinstance(drawdown.index, pd.DatetimeIndex):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        plt.xticks(rotation=45)

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return output_path

    plt.close(fig)
    return None


def plot_metric_distribution(
    values: List[float],
    title: str = "Metric Distribution",
    xlabel: str = "Value",
    output_path: Optional[Path] = None,
    figsize: tuple = (10, 5),
    bins: int = 20,
) -> Optional[Path]:
    """
    Erstellt ein Histogramm für eine Metrik-Verteilung.

    Args:
        values: Liste von Metrik-Werten
        title: Plot-Titel
        xlabel: X-Achsen-Label
        output_path: Pfad zum Speichern (PNG)
        figsize: Figure-Größe
        bins: Anzahl Bins

    Returns:
        Pfad zur gespeicherten PNG-Datei oder None
    """
    if not MATPLOTLIB_AVAILABLE or not values:
        return None

    fig, ax = plt.subplots(figsize=figsize)

    ax.hist(values, bins=bins, edgecolor="black", alpha=0.7, color="#0d6efd")

    # Durchschnitt einzeichnen
    avg = np.mean(values)
    ax.axvline(avg, color="#dc3545", linestyle="--", linewidth=2, label=f"Mean: {avg:.3f}")

    ax.set_xlabel(xlabel)
    ax.set_ylabel("Frequency")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return output_path

    plt.close(fig)
    return None


def plot_sweep_scatter(
    x_values: List[float],
    y_values: List[float],
    x_label: str,
    y_label: str,
    title: str = "Parameter vs Metric",
    output_path: Optional[Path] = None,
    figsize: tuple = (10, 6),
) -> Optional[Path]:
    """
    Erstellt einen Scatter-Plot für Parameter vs. Metrik.

    Args:
        x_values: Liste von Parameter-Werten
        y_values: Liste von Metrik-Werten
        x_label: X-Achsen-Label
        y_label: Y-Achsen-Label
        title: Plot-Titel
        output_path: Pfad zum Speichern (PNG)
        figsize: Figure-Größe

    Returns:
        Pfad zur gespeicherten PNG-Datei oder None
    """
    if not MATPLOTLIB_AVAILABLE or not x_values or not y_values:
        return None

    fig, ax = plt.subplots(figsize=figsize)

    ax.scatter(x_values, y_values, alpha=0.6, c="#0d6efd", s=50, edgecolors="black", linewidth=0.5)

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return output_path

    plt.close(fig)
    return None


# =============================================================================
# HTML REPORT BUILDER
# =============================================================================


class HtmlReportBuilder:
    """
    Builder-Klasse zum Erstellen von HTML-Reports.

    Erstellt strukturierte HTML-Reports für:
    - Einzelne Experimente (Backtests, Portfolio-Backtests)
    - Sweep-Auswertungen

    Example:
        >>> builder = HtmlReportBuilder(output_dir=Path("reports"))
        >>> report_path = builder.build_experiment_report(summary)
    """

    def __init__(
        self,
        output_dir: Path = Path("reports"),
        figures_subdir: str = "figures",
    ):
        """
        Initialisiert den ReportBuilder.

        Args:
            output_dir: Basis-Verzeichnis für Reports
            figures_subdir: Unterverzeichnis für Grafiken
        """
        self.output_dir = Path(output_dir)
        self.figures_subdir = figures_subdir

    def _ensure_dirs(self, report_dir: Path) -> Path:
        """Stellt sicher, dass Report-Verzeichnisse existieren."""
        figures_dir = report_dir / self.figures_subdir
        figures_dir.mkdir(parents=True, exist_ok=True)
        return figures_dir

    def _create_metrics_section(
        self,
        metrics: Dict[str, float],
        title: str = "Performance Metrics",
    ) -> ReportSection:
        """Erstellt eine Metrik-Sektion mit Karten."""
        metric_cards = []

        # Definiere Metrik-Formatierung
        metric_config = {
            "total_return": ("Total Return", "percent", True),
            "sharpe": ("Sharpe Ratio", "float", True),
            "max_drawdown": ("Max Drawdown", "percent", False),
            "cagr": ("CAGR", "percent", True),
            "sortino": ("Sortino Ratio", "float", True),
            "calmar": ("Calmar Ratio", "float", True),
            "win_rate": ("Win Rate", "percent", True),
            "profit_factor": ("Profit Factor", "float", True),
            "total_trades": ("Total Trades", "int", None),
        }

        for key, (label, fmt, positive_is_good) in metric_config.items():
            if key in metrics and metrics[key] is not None:
                value = metrics[key]
                if fmt == "percent":
                    value_str = _format_percent(value)
                elif fmt == "int":
                    value_str = str(int(value))
                else:
                    value_str = _format_float(value)

                # CSS-Klasse für Farbe
                css_class = ""
                if positive_is_good is not None:
                    if positive_is_good and value > 0:
                        css_class = "positive"
                    elif positive_is_good and value < 0:
                        css_class = "negative"
                    elif not positive_is_good and value < 0:
                        css_class = "negative"

                metric_cards.append(f"""
                <div class="metric-card">
                    <div class="label">{label}</div>
                    <div class="value {css_class}">{value_str}</div>
                </div>
                """)

        extra_html = f'<div class="metrics-grid">{"".join(metric_cards)}</div>'

        return ReportSection(
            title=title,
            extra_html=extra_html,
        )

    def _create_params_section(
        self,
        params: Dict[str, Any],
        title: str = "Strategy Parameters",
    ) -> ReportSection:
        """Erstellt eine Sektion mit Strategie-Parametern."""
        if not params:
            return ReportSection(title=title, description="No parameters available.")

        param_items = []
        for key, value in params.items():
            param_items.append(f"""
            <div class="param-item">
                <span class="key">{_html_escape(key)}:</span>
                <span class="value">{_html_escape(str(value))}</span>
            </div>
            """)

        extra_html = f'<div class="params-list">{"".join(param_items)}</div>'

        return ReportSection(
            title=title,
            extra_html=extra_html,
        )

    def build_experiment_report(
        self,
        summary: "ExperimentSummary",
        equity_curve: Optional[pd.Series] = None,
        extra_sections: Optional[List[ReportSection]] = None,
    ) -> Path:
        """
        Erstellt einen HTML-Report für ein einzelnes Experiment.

        Args:
            summary: ExperimentSummary aus dem Explorer
            equity_curve: Optionale Equity-Kurve für Plots
            extra_sections: Zusätzliche Report-Sektionen

        Returns:
            Pfad zur generierten HTML-Datei
        """
        # Report-Verzeichnis erstellen
        report_name = f"experiment_{summary.experiment_id[:12]}"
        report_dir = self.output_dir / report_name
        figures_dir = self._ensure_dirs(report_dir)

        # Report-Objekt initialisieren
        report = HtmlReport(
            title=f"Experiment Report: {summary.run_name}",
            experiment_id=summary.experiment_id,
            created_at=datetime.utcnow(),
        )

        # Overview-Sektion
        overview_table = ReportTable(
            title="Overview",
            headers=["Property", "Value"],
            rows=[
                ["Run ID", summary.experiment_id],
                ["Run Type", summary.run_type],
                ["Run Name", summary.run_name],
                ["Strategy", summary.strategy_name or "-"],
                ["Symbol", summary.symbol or "-"],
                [
                    "Created",
                    summary.created_at.strftime("%Y-%m-%d %H:%M:%S") if summary.created_at else "-",
                ],
            ],
        )
        report.sections.append(
            ReportSection(
                title="Overview",
                tables=[overview_table],
            )
        )

        # Metrics-Sektion
        if summary.metrics:
            report.sections.append(self._create_metrics_section(summary.metrics))

        # Parameters-Sektion
        if summary.params:
            report.sections.append(self._create_params_section(summary.params))

        # Charts-Sektion (wenn Equity-Kurve vorhanden)
        if equity_curve is not None and len(equity_curve) > 0:
            figures = []

            # Equity-Plot
            equity_path = figures_dir / "equity_curve.png"
            if plot_equity_curve(equity_curve, "Equity Curve", equity_path):
                figures.append(
                    ReportFigure(
                        title="Equity Curve",
                        description="Portfolio value over time",
                        image_path=f"{self.figures_subdir}/equity_curve.png",
                    )
                )

            # Drawdown-Plot
            dd_path = figures_dir / "drawdown.png"
            if plot_drawdown(equity_curve, "Drawdown", dd_path):
                figures.append(
                    ReportFigure(
                        title="Drawdown",
                        description="Drawdown from peak",
                        image_path=f"{self.figures_subdir}/drawdown.png",
                    )
                )

            if figures:
                report.sections.append(
                    ReportSection(
                        title="Charts",
                        figures=figures,
                    )
                )

        # Extra-Sektionen hinzufügen
        if extra_sections:
            report.sections.extend(extra_sections)

        # HTML rendern und speichern
        html_content = _render_html_report(report)
        report_path = report_dir / "report.html"
        report_path.write_text(html_content, encoding="utf-8")

        return report_path

    def build_sweep_report(
        self,
        overview: "SweepOverview",
        top_runs: List["RankedExperiment"],
        metric: str = "sharpe",
        extra_sections: Optional[List[ReportSection]] = None,
    ) -> Path:
        """
        Erstellt einen HTML-Report für einen Sweep.

        Args:
            overview: SweepOverview aus dem Explorer
            top_runs: Liste der besten Runs (RankedExperiment)
            metric: Metrik für Ranking/Anzeige
            extra_sections: Zusätzliche Report-Sektionen

        Returns:
            Pfad zur generierten HTML-Datei
        """
        # Report-Verzeichnis erstellen
        report_name = f"sweep_{overview.sweep_name}"
        report_dir = self.output_dir / report_name
        figures_dir = self._ensure_dirs(report_dir)

        # Report-Objekt initialisieren
        report = HtmlReport(
            title=f"Sweep Report: {overview.sweep_name}",
            sweep_name=overview.sweep_name,
            created_at=datetime.utcnow(),
        )

        # Overview-Sektion
        overview_table = ReportTable(
            title="Sweep Overview",
            headers=["Property", "Value"],
            rows=[
                ["Sweep Name", overview.sweep_name],
                ["Strategy", overview.strategy_key],
                ["Total Runs", str(overview.run_count)],
            ],
        )
        report.sections.append(
            ReportSection(
                title="Overview",
                tables=[overview_table],
            )
        )

        # Metric Statistics
        if overview.metric_stats:
            stats = overview.metric_stats
            stats_table = ReportTable(
                title=f"{metric.capitalize()} Statistics",
                headers=["Statistic", "Value"],
                rows=[
                    ["Min", _format_float(stats.get("min"))],
                    ["Max", _format_float(stats.get("max"))],
                    ["Mean", _format_float(stats.get("mean"))],
                    ["Median", _format_float(stats.get("median"))],
                    ["Std Dev", _format_float(stats.get("std"))],
                ],
            )
            report.sections.append(
                ReportSection(
                    title="Metric Statistics",
                    tables=[stats_table],
                )
            )

        # Parameter Ranges
        if overview.param_ranges:
            param_rows = []
            for param_name, info in overview.param_ranges.items():
                values = info.get("values", [])
                count = info.get("count", len(values))
                if len(values) <= 5:
                    values_str = ", ".join(str(v) for v in values)
                else:
                    values_str = f"{count} distinct values"
                param_rows.append([param_name, values_str])

            param_table = ReportTable(
                title="Parameter Ranges",
                headers=["Parameter", "Values"],
                rows=param_rows,
            )
            report.sections.append(
                ReportSection(
                    title="Parameter Space",
                    tables=[param_table],
                )
            )

        # Top Runs
        if top_runs:
            top_rows = []
            for r in top_runs:
                s = r.summary
                top_rows.append(
                    [
                        str(r.rank),
                        s.experiment_id[:12] + "...",
                        _format_float(r.sort_value, 4),
                        _format_percent(s.metrics.get("total_return")),
                        _format_percent(s.metrics.get("max_drawdown")),
                        json.dumps(s.params) if s.params else "-",
                    ]
                )

            top_table = ReportTable(
                title=f"Top {len(top_runs)} Runs by {metric.capitalize()}",
                headers=["Rank", "Run ID", metric.capitalize(), "Return", "Max DD", "Parameters"],
                rows=top_rows,
            )
            report.sections.append(
                ReportSection(
                    title="Best Runs",
                    tables=[top_table],
                )
            )

        # Charts
        figures = []

        # Metric Distribution
        if top_runs:
            metric_values = [r.sort_value for r in top_runs if r.sort_value is not None]
            if metric_values:
                dist_path = figures_dir / f"{metric}_distribution.png"
                if plot_metric_distribution(
                    metric_values,
                    f"{metric.capitalize()} Distribution",
                    metric.capitalize(),
                    dist_path,
                ):
                    figures.append(
                        ReportFigure(
                            title=f"{metric.capitalize()} Distribution",
                            description="Distribution of metric across sweep runs",
                            image_path=f"{self.figures_subdir}/{metric}_distribution.png",
                        )
                    )

        if figures:
            report.sections.append(
                ReportSection(
                    title="Charts",
                    figures=figures,
                )
            )

        # Extra-Sektionen hinzufügen
        if extra_sections:
            report.sections.extend(extra_sections)

        # HTML rendern und speichern
        html_content = _render_html_report(report)
        report_path = report_dir / "report.html"
        report_path.write_text(html_content, encoding="utf-8")

        return report_path


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def build_quick_experiment_report(
    experiment_id: str,
    output_dir: Path = Path("reports"),
) -> Optional[Path]:
    """
    Schnelle Report-Generierung für ein Experiment.

    Args:
        experiment_id: Experiment-ID
        output_dir: Ausgabe-Verzeichnis

    Returns:
        Pfad zum Report oder None wenn nicht gefunden
    """
    from src.analytics.explorer import ExperimentExplorer

    explorer = ExperimentExplorer()
    summary = explorer.get_experiment_details(experiment_id)

    if summary is None:
        return None

    builder = HtmlReportBuilder(output_dir=output_dir)
    return builder.build_experiment_report(summary)


def build_quick_sweep_report(
    sweep_name: str,
    metric: str = "sharpe",
    top_n: int = 20,
    output_dir: Path = Path("reports"),
) -> Optional[Path]:
    """
    Schnelle Report-Generierung für einen Sweep.

    Args:
        sweep_name: Name des Sweeps
        metric: Metrik für Ranking
        top_n: Anzahl Top-Runs
        output_dir: Ausgabe-Verzeichnis

    Returns:
        Pfad zum Report oder None wenn nicht gefunden
    """
    from src.analytics.explorer import ExperimentExplorer

    explorer = ExperimentExplorer()
    overview = explorer.summarize_sweep(sweep_name, metric=metric, top_n=top_n)

    if overview is None:
        return None

    builder = HtmlReportBuilder(output_dir=output_dir)
    return builder.build_sweep_report(overview, overview.best_runs, metric=metric)
