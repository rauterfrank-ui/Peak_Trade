# tests/test_reporting_base.py
"""
Tests für src/reporting/base.py (Phase 30)
==========================================

Testet:
- ReportSection Konstruktion und to_markdown()
- Report Konstruktion und to_markdown() / to_html()
- Helper-Funktionen (df_to_markdown, dict_to_markdown_table, format_metric)
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.reporting.base import (
    Report,
    ReportSection,
    df_to_markdown,
    dict_to_markdown_table,
    format_metric,
)


# =============================================================================
# ReportSection Tests
# =============================================================================


class TestReportSection:
    """Tests für ReportSection."""

    def test_section_basic_construction(self) -> None:
        """Test: Section kann konstruiert werden."""
        section = ReportSection(
            title="Test Section",
            content_markdown="This is content.",
        )
        assert section.title == "Test Section"
        assert section.content_markdown == "This is content."

    def test_section_empty_content(self) -> None:
        """Test: Section mit leerem Content."""
        section = ReportSection(title="Empty Section")
        assert section.title == "Empty Section"
        assert section.content_markdown == ""

    def test_section_to_markdown(self) -> None:
        """Test: to_markdown() erzeugt korrektes Format."""
        section = ReportSection(
            title="Summary",
            content_markdown="| Metric | Value |\n|--------|-------|\n| Sharpe | 1.5 |",
        )
        md = section.to_markdown()

        assert "## Summary" in md
        assert "| Metric | Value |" in md
        assert "| Sharpe | 1.5 |" in md

    def test_section_to_markdown_empty_content(self) -> None:
        """Test: to_markdown() mit leerem Content."""
        section = ReportSection(title="Empty")
        md = section.to_markdown()

        assert "## Empty" in md
        # Sollte keine extra Leerzeilen erzeugen
        assert md.strip() == "## Empty"


# =============================================================================
# Report Tests
# =============================================================================


class TestReport:
    """Tests für Report."""

    def test_report_basic_construction(self) -> None:
        """Test: Report kann konstruiert werden."""
        report = Report(title="Test Report")
        assert report.title == "Test Report"
        assert report.sections == []
        assert report.metadata == {}

    def test_report_with_sections(self) -> None:
        """Test: Report mit Sections."""
        sections = [
            ReportSection("Section 1", "Content 1"),
            ReportSection("Section 2", "Content 2"),
        ]
        report = Report(title="Multi-Section Report", sections=sections)

        assert len(report.sections) == 2
        assert report.sections[0].title == "Section 1"

    def test_report_with_metadata(self) -> None:
        """Test: Report mit Metadata."""
        report = Report(
            title="Metadata Test",
            metadata={"strategy": "ma_crossover", "symbol": "BTC/EUR"},
        )
        assert report.metadata["strategy"] == "ma_crossover"
        assert report.metadata["symbol"] == "BTC/EUR"

    def test_report_add_section(self) -> None:
        """Test: add_section() funktioniert."""
        report = Report(title="Test")
        report.add_section(ReportSection("Added", "Content"))

        assert len(report.sections) == 1
        assert report.sections[0].title == "Added"

    def test_report_to_markdown(self) -> None:
        """Test: to_markdown() erzeugt korrektes Format."""
        report = Report(
            title="Backtest Report",
            sections=[
                ReportSection("Summary", "Sharpe: 1.5"),
                ReportSection("Parameters", "fast_period: 10"),
            ],
            metadata={"strategy": "ma_crossover"},
        )
        md = report.to_markdown()

        # Prüfe Struktur
        assert "# Backtest Report" in md
        assert "## Summary" in md
        assert "## Parameters" in md
        assert "Sharpe: 1.5" in md
        assert "fast_period: 10" in md

        # Prüfe Metadata
        assert "strategy: ma_crossover" in md

        # Prüfe Generated timestamp
        assert "Generated:" in md

    def test_report_to_html(self) -> None:
        """Test: to_html() erzeugt valides HTML."""
        report = Report(
            title="HTML Test",
            sections=[
                ReportSection(
                    "Summary", "| Metric | Value |\n|--------|-------|\n| Sharpe | 1.5 |"
                ),
            ],
        )
        html = report.to_html()

        # Prüfe HTML-Struktur
        assert "<!DOCTYPE html>" in html
        assert "<html>" in html
        assert "</html>" in html
        assert "<title>HTML Test</title>" in html
        assert "<h1>HTML Test</h1>" in html
        assert "<h2>Summary</h2>" in html

        # Prüfe Tabellen-Konvertierung
        assert "<table>" in html
        assert "</table>" in html


# =============================================================================
# Helper Functions Tests
# =============================================================================


class TestDfToMarkdown:
    """Tests für df_to_markdown()."""

    def test_basic_dataframe(self) -> None:
        """Test: Einfaches DataFrame."""
        df = pd.DataFrame(
            {
                "Metric": ["Sharpe", "Return"],
                "Value": [1.5, 0.15],
            }
        )
        md = df_to_markdown(df)

        assert "| Metric | Value |" in md
        assert "| Sharpe |" in md
        assert "| Return |" in md
        assert "|" in md

    def test_empty_dataframe(self) -> None:
        """Test: Leeres DataFrame."""
        df = pd.DataFrame()
        md = df_to_markdown(df)
        assert "No data" in md

    def test_float_format(self) -> None:
        """Test: Float-Formatierung."""
        df = pd.DataFrame({"Value": [1.23456789]})
        md = df_to_markdown(df, float_format=".2f")

        assert "1.23" in md

    def test_max_rows(self) -> None:
        """Test: max_rows limitiert Output."""
        df = pd.DataFrame({"Value": range(100)})
        md = df_to_markdown(df, max_rows=5)

        # Sollte nur 5 Datenzeilen haben (+ Header + Separator)
        lines = [l for l in md.split("\n") if l.startswith("|")]
        assert len(lines) == 7  # Header + Separator + 5 data rows


class TestDictToMarkdownTable:
    """Tests für dict_to_markdown_table()."""

    def test_basic_dict(self) -> None:
        """Test: Einfaches Dictionary."""
        data = {"sharpe": 1.5, "return": 0.15}
        md = dict_to_markdown_table(data)

        assert "| Metric | Value |" in md
        assert "| sharpe |" in md
        assert "| return |" in md

    def test_empty_dict(self) -> None:
        """Test: Leeres Dictionary."""
        md = dict_to_markdown_table({})
        assert "No data" in md

    def test_custom_headers(self) -> None:
        """Test: Custom Header."""
        data = {"fast_period": 10}
        md = dict_to_markdown_table(data, key_header="Parameter", value_header="Setting")

        assert "| Parameter | Setting |" in md


class TestFormatMetric:
    """Tests für format_metric()."""

    def test_return_as_percent(self) -> None:
        """Test: Return wird als Prozent formatiert."""
        result = format_metric(0.15, "total_return")
        assert "%" in result
        assert "15" in result

    def test_drawdown_as_percent(self) -> None:
        """Test: Drawdown wird als Prozent formatiert."""
        result = format_metric(-0.10, "max_drawdown")
        assert "%" in result
        assert "-10" in result

    def test_sharpe_as_float(self) -> None:
        """Test: Sharpe wird als Float formatiert."""
        result = format_metric(1.523, "sharpe")
        assert "%" not in result
        assert "1.52" in result

    def test_trades_as_int(self) -> None:
        """Test: Trade counts werden als Int formatiert."""
        result = format_metric(100.0, "total_trades")
        assert result == "100"

    def test_win_rate_as_percent(self) -> None:
        """Test: Win rate wird als Prozent formatiert."""
        result = format_metric(0.55, "win_rate")
        assert "%" in result
        assert "55" in result
