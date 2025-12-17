# src/reporting/base.py
"""
Peak_Trade Reporting Base Types (Phase 30)
==========================================

Zentrale Dataclasses und Helper für Markdown- und HTML-Reports.

Komponenten:
- ReportSection: Ein logischer Abschnitt (Titel + Markdown-Content)
- Report: Kompletter Report mit mehreren Sections
- Helper-Funktionen für DataFrame -> Markdown Konvertierung

Usage:
    from src.reporting.base import Report, ReportSection, df_to_markdown

    section = ReportSection(
        title="Summary",
        content_markdown="| Metric | Value |\\n|--------|-------|\\n| Sharpe | 1.5 |"
    )
    report = Report(title="Backtest Report", sections=[section])
    print(report.to_markdown())
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd

# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass
class ReportSection:
    """
    Ein logischer Abschnitt in einem Report.

    Attributes:
        title: Titel des Abschnitts (wird als ## Header gerendert)
        content_markdown: Markdown-formatierter Inhalt

    Example:
        >>> section = ReportSection(
        ...     title="Performance Summary",
        ...     content_markdown="| Metric | Value |\\n|--------|-------|\\n| Sharpe | 1.5 |"
        ... )
    """

    title: str
    content_markdown: str = ""

    def to_markdown(self) -> str:
        """Rendert die Section als Markdown."""
        lines = [f"## {self.title}", ""]
        if self.content_markdown:
            lines.append(self.content_markdown)
            lines.append("")
        return "\n".join(lines)


@dataclass
class Report:
    """
    Ein kompletter Report, bestehend aus mehreren Sections.

    Attributes:
        title: Haupttitel des Reports (wird als # Header gerendert)
        sections: Liste von ReportSection-Objekten
        metadata: Zusätzliche Metadaten (z.B. timestamp, author)

    Example:
        >>> report = Report(
        ...     title="MA Crossover Backtest",
        ...     sections=[
        ...         ReportSection("Summary", "Total Return: 15%"),
        ...         ReportSection("Parameters", "fast_period: 10"),
        ...     ],
        ...     metadata={"strategy": "ma_crossover", "symbol": "BTC/EUR"}
        ... )
        >>> print(report.to_markdown())
    """

    title: str
    sections: list[ReportSection] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_section(self, section: ReportSection) -> None:
        """Fügt eine Section hinzu."""
        self.sections.append(section)

    def to_markdown(self) -> str:
        """
        Rendert den kompletten Report als Markdown.

        Returns:
            Markdown-String mit Titel, Metadaten und allen Sections.
        """
        lines = [f"# {self.title}", ""]

        # Metadaten als Infobox
        if self.metadata:
            lines.append("**Report Metadata:**")
            for key, value in self.metadata.items():
                lines.append(f"- {key}: {value}")
            lines.append("")

        # Generierungszeitpunkt
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Sections
        for section in self.sections:
            lines.append(section.to_markdown())

        return "\n".join(lines)

    def to_html(self) -> str:
        """
        Rendert den Report als einfaches HTML.

        Konvertiert Markdown-Elemente in HTML-Tags.
        Kein komplexes Styling - einfache, lesbare Ausgabe.

        Returns:
            HTML-String
        """
        lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset=\"UTF-8\">",
            f"<title>{_escape_html(self.title)}</title>",
            "<style>",
            "body { font-family: sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; line-height: 1.6; }",
            "h1 { border-bottom: 2px solid #333; padding-bottom: 10px; }",
            "h2 { color: #333; margin-top: 30px; }",
            "table { border-collapse: collapse; width: 100%; margin: 15px 0; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #f5f5f5; }",
            "tr:hover { background-color: #f9f9f9; }",
            "pre { background: #f5f5f5; padding: 10px; overflow-x: auto; }",
            "code { background: #f0f0f0; padding: 2px 4px; }",
            ".meta { color: #666; font-size: 0.9em; }",
            "hr { border: none; border-top: 1px solid #ddd; margin: 20px 0; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{_escape_html(self.title)}</h1>",
        ]

        # Metadaten
        if self.metadata:
            lines.append("<div class=\"meta\">")
            lines.append("<p><strong>Report Metadata:</strong></p>")
            lines.append("<ul>")
            for key, value in self.metadata.items():
                lines.append(f"<li>{_escape_html(key)}: {_escape_html(str(value))}</li>")
            lines.append("</ul>")
            lines.append("</div>")

        lines.append(f"<p class=\"meta\"><em>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>")
        lines.append("<hr>")

        # Sections
        for section in self.sections:
            lines.append(f"<h2>{_escape_html(section.title)}</h2>")
            html_content = _markdown_to_html(section.content_markdown)
            lines.append(html_content)

        lines.append("</body>")
        lines.append("</html>")

        return "\n".join(lines)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _escape_html(text: str) -> str:
    """Escaped HTML-Sonderzeichen."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _markdown_to_html(markdown: str) -> str:
    """
    Konvertiert einfaches Markdown zu HTML.

    Unterstützt:
    - Tabellen (| col1 | col2 |)
    - Fettschrift (**text**)
    - Kursiv (*text*)
    - Code-Blöcke (```...```)
    - Inline-Code (`code`)
    - Bilder (![alt](src))
    - Links ([text](url))
    """
    lines = markdown.split("\n")
    html_lines: list[str] = []
    in_table = False
    in_code_block = False
    table_lines: list[str] = []

    for line in lines:
        # Code-Block Start/Ende
        if line.strip().startswith("```"):
            if in_code_block:
                html_lines.append("</pre>")
                in_code_block = False
            else:
                html_lines.append("<pre>")
                in_code_block = True
            continue

        if in_code_block:
            html_lines.append(_escape_html(line))
            continue

        # Tabellen-Zeilen sammeln
        if line.strip().startswith("|"):
            if not in_table:
                in_table = True
                table_lines = []
            table_lines.append(line)
            continue
        elif in_table:
            # Tabelle abschließen
            html_lines.append(_render_markdown_table(table_lines))
            in_table = False
            table_lines = []

        # Bilder: ![alt](src)
        import re
        line = re.sub(
            r"!\[([^\]]*)\]\(([^)]+)\)",
            r'<img src="\2" alt="\1" style="max-width: 100%;">',
            line,
        )

        # Links: [text](url)
        line = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', line)

        # Fettschrift: **text**
        line = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", line)

        # Kursiv: *text*
        line = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", line)

        # Inline-Code: `code`
        line = re.sub(r"`([^`]+)`", r"<code>\1</code>", line)

        # Leere Zeilen als Absatz-Trenner
        if line.strip() == "":
            html_lines.append("<br>")
        else:
            html_lines.append(f"<p>{line}</p>")

    # Falls Tabelle am Ende nicht abgeschlossen
    if in_table and table_lines:
        html_lines.append(_render_markdown_table(table_lines))

    return "\n".join(html_lines)


def _render_markdown_table(table_lines: list[str]) -> str:
    """Rendert Markdown-Tabellenzeilen als HTML-Tabelle."""
    if not table_lines:
        return ""

    html = ["<table>"]

    for i, line in enumerate(table_lines):
        cells = [c.strip() for c in line.split("|")]
        # Entferne leere Zellen am Anfang/Ende (durch | am Rand)
        cells = [c for c in cells if c or i == 0]

        # Separator-Zeile (|---|---|) überspringen
        if all(set(c) <= {"-", ":"} for c in cells if c):
            continue

        tag = "th" if i == 0 else "td"
        html.append("<tr>")
        for cell in cells:
            html.append(f"<{tag}>{_escape_html(cell)}</{tag}>")
        html.append("</tr>")

    html.append("</table>")
    return "\n".join(html)


def df_to_markdown(
    df: pd.DataFrame,
    float_format: str = ".4f",
    max_rows: int | None = None,
) -> str:
    """
    Konvertiert ein Pandas DataFrame zu einer Markdown-Tabelle.

    Args:
        df: DataFrame zu konvertieren
        float_format: Format-String für Float-Werte
        max_rows: Maximale Anzahl Zeilen (None = alle)

    Returns:
        Markdown-Tabelle als String

    Example:
        >>> df = pd.DataFrame({"Metric": ["Sharpe", "Return"], "Value": [1.5, 0.15]})
        >>> print(df_to_markdown(df))
        | Metric | Value |
        |--------|-------|
        | Sharpe | 1.5000 |
        | Return | 0.1500 |
    """
    if df.empty:
        return "*No data*"

    if max_rows is not None and len(df) > max_rows:
        df = df.head(max_rows)

    # Header
    headers = df.columns.tolist()
    header_line = "| " + " | ".join(str(h) for h in headers) + " |"

    # Separator
    separator = "| " + " | ".join("-" * max(3, len(str(h))) for h in headers) + " |"

    # Rows
    rows: list[str] = []
    for _, row in df.iterrows():
        cells: list[str] = []
        for val in row:
            if isinstance(val, float):
                cells.append(format(val, float_format))
            else:
                cells.append(str(val))
        rows.append("| " + " | ".join(cells) + " |")

    return "\n".join([header_line, separator, *rows])


def dict_to_markdown_table(
    data: dict[str, Any],
    key_header: str = "Metric",
    value_header: str = "Value",
    float_format: str = ".4f",
) -> str:
    """
    Konvertiert ein Dictionary zu einer Markdown-Tabelle.

    Args:
        data: Dictionary mit Key-Value Paaren
        key_header: Header für die Key-Spalte
        value_header: Header für die Value-Spalte
        float_format: Format-String für Float-Werte

    Returns:
        Markdown-Tabelle als String

    Example:
        >>> metrics = {"sharpe": 1.5, "return": 0.15, "max_drawdown": -0.10}
        >>> print(dict_to_markdown_table(metrics))
        | Metric | Value |
        |--------|-------|
        | sharpe | 1.5000 |
        | return | 0.1500 |
        | max_drawdown | -0.1000 |
    """
    if not data:
        return "*No data*"

    header = f"| {key_header} | {value_header} |"
    separator = f"| {'-' * len(key_header)} | {'-' * len(value_header)} |"

    rows: list[str] = []
    for key, value in data.items():
        if isinstance(value, float):
            value_str = format(value, float_format)
        else:
            value_str = str(value)
        rows.append(f"| {key} | {value_str} |")

    return "\n".join([header, separator, *rows])


def format_metric(value: float, metric_name: str) -> str:
    """
    Formatiert einen Metrik-Wert kontextabhängig.

    Args:
        value: Der Wert
        metric_name: Name der Metrik (für kontextabhängige Formatierung)

    Returns:
        Formatierter String

    Example:
        >>> format_metric(0.15, "total_return")
        '15.00%'
        >>> format_metric(1.523, "sharpe")
        '1.52'
    """
    metric_lower = metric_name.lower()

    # Prozent-Metriken
    percent_metrics = [
        "return",
        "drawdown",
        "cagr",
        "win_rate",
        "rate",
        "pct",
        "percent",
    ]
    if any(pm in metric_lower for pm in percent_metrics):
        return f"{value * 100:.2f}%"

    # Ganzzahlen
    int_metrics = ["trades", "count", "wins", "losses", "winning", "losing", "n_"]
    if any(im in metric_lower for im in int_metrics):
        return str(int(value))

    # Standard: 2-4 Dezimalstellen
    if abs(value) >= 100:
        return f"{value:.1f}"
    elif abs(value) >= 1:
        return f"{value:.2f}"
    else:
        return f"{value:.4f}"
