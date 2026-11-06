#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# tests/test_reporting_v2.py
"""
Tests für Reporting v2 – HTML Dashboards & CLI-UX (Phase 21).

Testet:
- Dataclasses: ReportFigure, ReportTable, ReportSection, HtmlReport
- HtmlReportBuilder und Report-Generierung
- Plot-Funktionen (mit Matplotlib-Mock falls nicht verfügbar)
- Convenience-Funktionen
- CLI-Tools (Argument-Parsing)
"""

from __future__ import annotations

import tempfile
import pytest
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pandas as pd
import numpy as np


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_dir():
    """Temporäres Verzeichnis für Test-Output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_experiment_summary():
    """Mock ExperimentSummary für Tests."""
    from src.analytics.explorer import ExperimentSummary

    return ExperimentSummary(
        experiment_id="test-exp-12345678-abcd-1234-5678-abcdef123456",
        run_type="backtest",
        run_name="test_backtest_run",
        strategy_name="ma_crossover",
        sweep_name=None,
        symbol="BTC/EUR",
        tags=["test", "dev"],
        created_at=datetime(2024, 12, 15, 10, 30, 0),
        metrics={
            "total_return": 0.25,
            "sharpe": 1.5,
            "max_drawdown": -0.15,
            "cagr": 0.18,
            "win_rate": 0.55,
            "total_trades": 42,
        },
        params={
            "fast_period": 10,
            "slow_period": 30,
            "stop_loss": 0.02,
        },
    )


@pytest.fixture
def mock_sweep_overview():
    """Mock SweepOverview für Tests."""
    from src.analytics.explorer import SweepOverview, RankedExperiment, ExperimentSummary

    best_runs = []
    for i in range(5):
        summary = ExperimentSummary(
            experiment_id=f"sweep-run-{i:04d}-abcd-1234-5678-abcdef12345{i}",
            run_type="sweep",
            run_name=f"sweep_run_{i}",
            strategy_name="ma_crossover",
            sweep_name="test_sweep_v1",
            symbol="BTC/EUR",
            tags=["sweep"],
            created_at=datetime(2024, 12, 15, 10, 30, i),
            metrics={
                "total_return": 0.20 + i * 0.05,
                "sharpe": 1.2 + i * 0.2,
                "max_drawdown": -0.10 - i * 0.01,
            },
            params={
                "fast_period": 5 + i * 2,
                "slow_period": 20 + i * 5,
            },
        )
        best_runs.append(
            RankedExperiment(
                summary=summary,
                rank=i + 1,
                sort_key="sharpe",
                sort_value=1.2 + i * 0.2,
            )
        )

    return SweepOverview(
        sweep_name="test_sweep_v1",
        strategy_key="ma_crossover",
        run_count=50,
        best_runs=best_runs,
        metric_stats={
            "min": 0.5,
            "max": 2.2,
            "mean": 1.4,
            "median": 1.35,
            "std": 0.3,
        },
        param_ranges={
            "fast_period": {"values": [5, 7, 9, 11, 13], "count": 5},
            "slow_period": {"values": [20, 25, 30, 35, 40, 45, 50], "count": 7},
        },
    )


@pytest.fixture
def sample_equity_curve():
    """Sample equity curve für Chart-Tests."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    values = 10000 * (1 + np.random.randn(100).cumsum() * 0.01)
    return pd.Series(values, index=dates, name="equity")


# =============================================================================
# DATACLASS TESTS
# =============================================================================


class TestReportFigure:
    """Tests für ReportFigure Dataclass."""

    def test_create_minimal(self):
        """Test minimale Erstellung."""
        from src.reporting.html_reports import ReportFigure

        fig = ReportFigure(title="Test Figure")
        assert fig.title == "Test Figure"
        assert fig.description is None
        assert fig.image_path == ""

    def test_create_full(self):
        """Test vollständige Erstellung."""
        from src.reporting.html_reports import ReportFigure

        fig = ReportFigure(
            title="Equity Curve",
            description="Portfolio value over time",
            image_path="figures/equity.png",
        )
        assert fig.title == "Equity Curve"
        assert fig.description == "Portfolio value over time"
        assert fig.image_path == "figures/equity.png"


class TestReportTable:
    """Tests für ReportTable Dataclass."""

    def test_create_minimal(self):
        """Test minimale Erstellung."""
        from src.reporting.html_reports import ReportTable

        table = ReportTable(title="Test Table")
        assert table.title == "Test Table"
        assert table.headers == []
        assert table.rows == []

    def test_create_with_data(self):
        """Test mit Daten."""
        from src.reporting.html_reports import ReportTable

        table = ReportTable(
            title="Metrics",
            description="Performance metrics",
            headers=["Metric", "Value"],
            rows=[
                ["Sharpe", "1.5"],
                ["Return", "25%"],
            ],
        )
        assert len(table.headers) == 2
        assert len(table.rows) == 2
        assert table.rows[0][0] == "Sharpe"


class TestReportSection:
    """Tests für ReportSection Dataclass."""

    def test_create_minimal(self):
        """Test minimale Erstellung."""
        from src.reporting.html_reports import ReportSection

        section = ReportSection(title="Test Section")
        assert section.title == "Test Section"
        assert section.figures == []
        assert section.tables == []

    def test_create_with_content(self):
        """Test mit Inhalt."""
        from src.reporting.html_reports import ReportSection, ReportFigure, ReportTable

        section = ReportSection(
            title="Overview",
            description="Section description",
            figures=[ReportFigure(title="Fig1")],
            tables=[ReportTable(title="Tab1")],
            extra_html="<p>Custom HTML</p>",
        )
        assert len(section.figures) == 1
        assert len(section.tables) == 1
        assert section.extra_html == "<p>Custom HTML</p>"


class TestHtmlReport:
    """Tests für HtmlReport Dataclass."""

    def test_create_minimal(self):
        """Test minimale Erstellung."""
        from src.reporting.html_reports import HtmlReport

        report = HtmlReport(title="Test Report")
        assert report.title == "Test Report"
        assert report.experiment_id is None
        assert report.sweep_name is None
        assert report.sections == []

    def test_create_experiment_report(self):
        """Test Experiment-Report."""
        from src.reporting.html_reports import HtmlReport

        report = HtmlReport(
            title="Experiment Report",
            experiment_id="abc-123",
            created_at=datetime(2024, 12, 15),
        )
        assert report.experiment_id == "abc-123"
        assert report.created_at.year == 2024

    def test_create_sweep_report(self):
        """Test Sweep-Report."""
        from src.reporting.html_reports import HtmlReport

        report = HtmlReport(
            title="Sweep Report",
            sweep_name="my_sweep_v1",
        )
        assert report.sweep_name == "my_sweep_v1"


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================


class TestHelperFunctions:
    """Tests für interne Helper-Funktionen."""

    def test_html_escape(self):
        """Test HTML-Escaping."""
        from src.reporting.html_reports import _html_escape

        assert _html_escape("<script>") == "&lt;script&gt;"
        assert _html_escape("a & b") == "a &amp; b"
        assert _html_escape('"test"') == "&quot;test&quot;"
        assert _html_escape("normal text") == "normal text"

    def test_format_percent(self):
        """Test Prozent-Formatierung."""
        from src.reporting.html_reports import _format_percent

        assert _format_percent(0.25) == "25.00%"
        assert _format_percent(-0.15) == "-15.00%"
        assert _format_percent(None) == "-"
        assert _format_percent(0.25, decimals=1) == "25.0%"

    def test_format_float(self):
        """Test Float-Formatierung."""
        from src.reporting.html_reports import _format_float

        assert _format_float(1.5) == "1.50"
        assert _format_float(-0.123, decimals=3) == "-0.123"
        assert _format_float(None) == "-"


class TestRenderFunctions:
    """Tests für Render-Funktionen."""

    def test_render_table(self):
        """Test Table-Rendering."""
        from src.reporting.html_reports import _render_table, ReportTable

        table = ReportTable(
            title="Test Table",
            headers=["A", "B"],
            rows=[["1", "2"]],
        )
        html = _render_table(table)
        assert "<table>" in html
        assert "<th>A</th>" in html
        assert "<td>1</td>" in html

    def test_render_figure(self):
        """Test Figure-Rendering."""
        from src.reporting.html_reports import _render_figure, ReportFigure

        fig = ReportFigure(
            title="Test Fig",
            description="Description",
            image_path="test.png",
        )
        html = _render_figure(fig)
        assert '<img src="test.png"' in html
        assert 'class="figure-container"' in html

    def test_render_section(self):
        """Test Section-Rendering."""
        from src.reporting.html_reports import _render_section, ReportSection, ReportTable

        section = ReportSection(
            title="Test Section",
            description="Desc",
            tables=[ReportTable(title="T1", headers=["X"], rows=[["1"]])],
        )
        html = _render_section(section)
        assert "<section>" in html
        assert "<h2>Test Section</h2>" in html
        assert "Desc" in html

    def test_render_html_report(self):
        """Test vollständiges Report-Rendering."""
        from src.reporting.html_reports import _render_html_report, HtmlReport, ReportSection

        report = HtmlReport(
            title="Full Report",
            experiment_id="test-123",
            sections=[
                ReportSection(title="Section 1"),
            ],
        )
        html = _render_html_report(report)
        assert "<!DOCTYPE html>" in html
        assert "<title>Full Report</title>" in html
        assert "Section 1" in html
        assert "Peak_Trade Reporting v2" in html  # Footer


# =============================================================================
# HTML REPORT BUILDER TESTS
# =============================================================================


class TestHtmlReportBuilder:
    """Tests für HtmlReportBuilder Klasse."""

    def test_init_default(self):
        """Test Standard-Initialisierung."""
        from src.reporting.html_reports import HtmlReportBuilder

        builder = HtmlReportBuilder()
        assert builder.output_dir == Path("reports")
        assert builder.figures_subdir == "figures"

    def test_init_custom(self, temp_dir):
        """Test benutzerdefinierte Initialisierung."""
        from src.reporting.html_reports import HtmlReportBuilder

        builder = HtmlReportBuilder(
            output_dir=temp_dir / "custom",
            figures_subdir="images",
        )
        assert builder.output_dir == temp_dir / "custom"
        assert builder.figures_subdir == "images"

    def test_ensure_dirs(self, temp_dir):
        """Test Verzeichnis-Erstellung."""
        from src.reporting.html_reports import HtmlReportBuilder

        builder = HtmlReportBuilder(output_dir=temp_dir)
        figures_dir = builder._ensure_dirs(temp_dir / "test_report")

        assert figures_dir.exists()
        assert figures_dir == temp_dir / "test_report" / "figures"

    def test_build_experiment_report(self, temp_dir, mock_experiment_summary):
        """Test Experiment-Report-Generierung."""
        from src.reporting.html_reports import HtmlReportBuilder

        builder = HtmlReportBuilder(output_dir=temp_dir)
        report_path = builder.build_experiment_report(mock_experiment_summary)

        assert report_path.exists()
        assert report_path.name == "report.html"

        content = report_path.read_text()
        assert "test_backtest_run" in content
        assert "ma_crossover" in content
        assert "BTC/EUR" in content
        assert "25.00%" in content  # total_return formatted

    def test_build_experiment_report_with_equity(
        self, temp_dir, mock_experiment_summary, sample_equity_curve
    ):
        """Test Experiment-Report mit Equity-Kurve."""
        from src.reporting.html_reports import HtmlReportBuilder, MATPLOTLIB_AVAILABLE

        builder = HtmlReportBuilder(output_dir=temp_dir)
        report_path = builder.build_experiment_report(
            mock_experiment_summary,
            equity_curve=sample_equity_curve,
        )

        assert report_path.exists()

        # Bei verfügbarem Matplotlib sollten Plots erstellt werden
        if MATPLOTLIB_AVAILABLE:
            figures_dir = report_path.parent / "figures"
            assert figures_dir.exists()
            # Prüfen ob zumindest versucht wurde, Plots zu erstellen
            content = report_path.read_text()
            # Chart-Sektion sollte erwähnt sein
            assert "Charts" in content or "equity" in content.lower()

    def test_build_sweep_report(self, temp_dir, mock_sweep_overview):
        """Test Sweep-Report-Generierung."""
        from src.reporting.html_reports import HtmlReportBuilder

        builder = HtmlReportBuilder(output_dir=temp_dir)
        report_path = builder.build_sweep_report(
            mock_sweep_overview,
            mock_sweep_overview.best_runs,
            metric="sharpe",
        )

        assert report_path.exists()
        assert report_path.name == "report.html"

        content = report_path.read_text()
        assert "test_sweep_v1" in content
        assert "ma_crossover" in content
        assert "50" in content  # run_count
        assert "fast_period" in content

    def test_create_metrics_section(self, temp_dir):
        """Test Metrics-Sektion-Erstellung."""
        from src.reporting.html_reports import HtmlReportBuilder

        builder = HtmlReportBuilder(output_dir=temp_dir)
        section = builder._create_metrics_section(
            {
                "total_return": 0.25,
                "sharpe": 1.5,
                "max_drawdown": -0.15,
            }
        )

        assert section.title == "Performance Metrics"
        assert section.extra_html is not None
        assert "25.00%" in section.extra_html
        assert "1.50" in section.extra_html

    def test_create_params_section(self, temp_dir):
        """Test Parameter-Sektion-Erstellung."""
        from src.reporting.html_reports import HtmlReportBuilder

        builder = HtmlReportBuilder(output_dir=temp_dir)
        section = builder._create_params_section(
            {
                "fast_period": 10,
                "slow_period": 30,
            }
        )

        assert section.title == "Strategy Parameters"
        assert "fast_period" in section.extra_html
        assert "10" in section.extra_html

    def test_create_params_section_empty(self, temp_dir):
        """Test leere Parameter-Sektion."""
        from src.reporting.html_reports import HtmlReportBuilder

        builder = HtmlReportBuilder(output_dir=temp_dir)
        section = builder._create_params_section({})

        assert "No parameters available" in section.description


# =============================================================================
# PLOT FUNCTION TESTS
# =============================================================================


class TestPlotFunctions:
    """Tests für Plot-Funktionen."""

    def test_plot_equity_curve_empty(self):
        """Test mit leerem DataFrame."""
        from src.reporting.html_reports import plot_equity_curve

        result = plot_equity_curve(pd.Series([], dtype=float))
        assert result is None

    def test_plot_equity_curve_none(self):
        """Test mit None."""
        from src.reporting.html_reports import plot_equity_curve

        result = plot_equity_curve(None)
        assert result is None

    def test_plot_equity_curve_saves_file(self, temp_dir, sample_equity_curve):
        """Test Equity-Plot speichern."""
        from src.reporting.html_reports import plot_equity_curve, MATPLOTLIB_AVAILABLE

        if not MATPLOTLIB_AVAILABLE:
            pytest.skip("Matplotlib nicht verfügbar")

        output_path = temp_dir / "equity.png"
        result = plot_equity_curve(sample_equity_curve, output_path=output_path)

        assert result == output_path
        assert output_path.exists()

    def test_plot_drawdown_empty(self):
        """Test mit leerem DataFrame."""
        from src.reporting.html_reports import plot_drawdown

        result = plot_drawdown(pd.Series([], dtype=float))
        assert result is None

    def test_plot_drawdown_saves_file(self, temp_dir, sample_equity_curve):
        """Test Drawdown-Plot speichern."""
        from src.reporting.html_reports import plot_drawdown, MATPLOTLIB_AVAILABLE

        if not MATPLOTLIB_AVAILABLE:
            pytest.skip("Matplotlib nicht verfügbar")

        output_path = temp_dir / "drawdown.png"
        result = plot_drawdown(sample_equity_curve, output_path=output_path)

        assert result == output_path
        assert output_path.exists()

    def test_plot_metric_distribution_empty(self):
        """Test mit leerer Liste."""
        from src.reporting.html_reports import plot_metric_distribution

        result = plot_metric_distribution([])
        assert result is None

    def test_plot_metric_distribution_saves_file(self, temp_dir):
        """Test Metrik-Verteilung speichern."""
        from src.reporting.html_reports import plot_metric_distribution, MATPLOTLIB_AVAILABLE

        if not MATPLOTLIB_AVAILABLE:
            pytest.skip("Matplotlib nicht verfügbar")

        values = [1.0, 1.2, 1.5, 1.8, 2.0, 1.3, 1.4]
        output_path = temp_dir / "dist.png"
        result = plot_metric_distribution(values, output_path=output_path)

        assert result == output_path
        assert output_path.exists()

    def test_plot_sweep_scatter_empty(self):
        """Test mit leeren Listen."""
        from src.reporting.html_reports import plot_sweep_scatter

        result = plot_sweep_scatter([], [], "X", "Y")
        assert result is None

    def test_plot_sweep_scatter_saves_file(self, temp_dir):
        """Test Scatter-Plot speichern."""
        from src.reporting.html_reports import plot_sweep_scatter, MATPLOTLIB_AVAILABLE

        if not MATPLOTLIB_AVAILABLE:
            pytest.skip("Matplotlib nicht verfügbar")

        x_values = [1, 2, 3, 4, 5]
        y_values = [1.0, 1.5, 1.2, 1.8, 2.0]
        output_path = temp_dir / "scatter.png"
        result = plot_sweep_scatter(x_values, y_values, "Param", "Metric", output_path=output_path)

        assert result == output_path
        assert output_path.exists()


# =============================================================================
# CLI TESTS
# =============================================================================


class TestReportExperimentCLI:
    """Tests für report_experiment.py CLI."""

    def test_build_parser(self):
        """Test Argument-Parser-Erstellung."""
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from report_experiment import build_parser

        parser = build_parser()
        assert parser is not None

    def test_parser_requires_id(self):
        """Test dass --id erforderlich ist."""
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from report_experiment import build_parser

        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])  # Ohne --id sollte fehlschlagen

    def test_parser_with_id(self):
        """Test Parser mit --id."""
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from report_experiment import build_parser

        parser = build_parser()
        args = parser.parse_args(["--id", "test-123"])
        assert args.id == "test-123"
        assert args.out_dir == "reports"
        assert args.open is False
        assert args.text_only is False

    def test_parser_all_options(self):
        """Test Parser mit allen Optionen."""
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from report_experiment import build_parser

        parser = build_parser()
        args = parser.parse_args(
            [
                "--id",
                "test-123",
                "--out-dir",
                "custom/reports",
                "--open",
                "--text-only",
                "--no-charts",
            ]
        )
        assert args.id == "test-123"
        assert args.out_dir == "custom/reports"
        assert args.open is True
        assert args.text_only is True
        assert args.no_charts is True


class TestReportSweepCLI:
    """Tests für report_sweep.py CLI."""

    def test_build_parser(self):
        """Test Argument-Parser-Erstellung."""
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from report_sweep import build_parser

        parser = build_parser()
        assert parser is not None

    def test_parser_defaults(self):
        """Test Standard-Werte."""
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from report_sweep import build_parser

        parser = build_parser()
        args = parser.parse_args([])
        assert args.sweep_name is None
        assert args.metric == "sharpe"
        assert args.top_n == 20

    def test_parser_with_sweep_name(self):
        """Test Parser mit --sweep-name."""
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from report_sweep import build_parser

        parser = build_parser()
        args = parser.parse_args(["--sweep-name", "my_sweep"])
        assert args.sweep_name == "my_sweep"

    def test_parser_all_options(self):
        """Test Parser mit allen Optionen."""
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from report_sweep import build_parser

        parser = build_parser()
        args = parser.parse_args(
            [
                "--sweep-name",
                "test_sweep",
                "--metric",
                "total_return",
                "--top-n",
                "50",
                "--out-dir",
                "custom/out",
                "--open",
                "--text-only",
                "--list-sweeps",
                "--no-charts",
            ]
        )
        assert args.sweep_name == "test_sweep"
        assert args.metric == "total_return"
        assert args.top_n == 50
        assert args.out_dir == "custom/out"
        assert args.open is True
        assert args.text_only is True
        assert args.list_sweeps is True
        assert args.no_charts is True


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests für Convenience-Funktionen."""

    def test_build_quick_experiment_report_not_found(self):
        """Test mit nicht existierendem Experiment."""
        from src.reporting.html_reports import build_quick_experiment_report

        # Mock den Explorer so dass er None zurückgibt
        # ExperimentExplorer wird innerhalb der Funktion importiert, also mocken wir es an der Quelle
        with patch("src.analytics.explorer.ExperimentExplorer") as MockExplorer:
            mock_explorer = MagicMock()
            mock_explorer.get_experiment_details.return_value = None
            MockExplorer.return_value = mock_explorer

            result = build_quick_experiment_report("nonexistent-id")
            assert result is None

    def test_build_quick_sweep_report_not_found(self):
        """Test mit nicht existierendem Sweep."""
        from src.reporting.html_reports import build_quick_sweep_report

        # Mock den Explorer so dass er None zurückgibt
        with patch("src.analytics.explorer.ExperimentExplorer") as MockExplorer:
            mock_explorer = MagicMock()
            mock_explorer.summarize_sweep.return_value = None
            MockExplorer.return_value = mock_explorer

            result = build_quick_sweep_report("nonexistent-sweep")
            assert result is None


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestIntegration:
    """Integrationstests für Reporting v2."""

    def test_full_experiment_report_workflow(self, temp_dir, mock_experiment_summary):
        """Test vollständiger Experiment-Report-Workflow."""
        from src.reporting.html_reports import HtmlReportBuilder, ReportSection

        builder = HtmlReportBuilder(output_dir=temp_dir)

        # Extra-Sektion hinzufügen
        extra = ReportSection(
            title="Custom Section",
            description="Additional information",
            extra_html="<p>Custom content</p>",
        )

        report_path = builder.build_experiment_report(
            mock_experiment_summary,
            extra_sections=[extra],
        )

        assert report_path.exists()
        content = report_path.read_text()

        # Prüfen dass alle Sektionen enthalten sind
        assert "Overview" in content
        assert "Performance Metrics" in content
        assert "Strategy Parameters" in content
        assert "Custom Section" in content
        assert "Custom content" in content

    def test_full_sweep_report_workflow(self, temp_dir, mock_sweep_overview):
        """Test vollständiger Sweep-Report-Workflow."""
        from src.reporting.html_reports import HtmlReportBuilder, ReportSection

        builder = HtmlReportBuilder(output_dir=temp_dir)

        # Extra-Sektion hinzufügen
        extra = ReportSection(
            title="Notes",
            description="Additional notes",
        )

        report_path = builder.build_sweep_report(
            mock_sweep_overview,
            mock_sweep_overview.best_runs,
            metric="sharpe",
            extra_sections=[extra],
        )

        assert report_path.exists()
        content = report_path.read_text()

        # Prüfen dass alle Sektionen enthalten sind
        assert "Overview" in content
        assert "Metric Statistics" in content
        assert "Parameter Space" in content
        assert "Best Runs" in content
        assert "Notes" in content

    def test_report_escapes_html_properly(self, temp_dir, mock_experiment_summary):
        """Test dass HTML korrekt escaped wird."""
        from src.reporting.html_reports import HtmlReportBuilder

        # Gefährliche Werte in Summary einfügen
        mock_experiment_summary.run_name = "<script>alert('xss')</script>"
        mock_experiment_summary.params["test_param"] = 'value<>&"'

        builder = HtmlReportBuilder(output_dir=temp_dir)
        report_path = builder.build_experiment_report(mock_experiment_summary)

        content = report_path.read_text()

        # Originale gefährliche Strings sollten NICHT enthalten sein
        assert "<script>" not in content
        assert "alert('xss')" not in content

        # Escaped Versionen sollten enthalten sein
        assert "&lt;script&gt;" in content


class TestExportedSymbols:
    """Test dass alle Symbole korrekt exportiert werden."""

    def test_reporting_module_exports(self):
        """Test src/reporting/__init__.py Exports."""
        from src.reporting import (
            ReportFigure,
            ReportTable,
            ReportSection,
            HtmlReport,
            HtmlReportBuilder,
            plot_equity_curve,
            plot_drawdown,
            plot_metric_distribution,
            plot_sweep_scatter,
            build_quick_experiment_report,
            build_quick_sweep_report,
        )

        # Alle sollten importierbar sein
        assert ReportFigure is not None
        assert ReportTable is not None
        assert ReportSection is not None
        assert HtmlReport is not None
        assert HtmlReportBuilder is not None
        assert callable(plot_equity_curve)
        assert callable(plot_drawdown)
        assert callable(plot_metric_distribution)
        assert callable(plot_sweep_scatter)
        assert callable(build_quick_experiment_report)
        assert callable(build_quick_sweep_report)


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


class TestEdgeCases:
    """Tests für Randfälle."""

    def test_report_with_empty_metrics(self, temp_dir):
        """Test Report mit leeren Metriken."""
        from src.analytics.explorer import ExperimentSummary
        from src.reporting.html_reports import HtmlReportBuilder

        summary = ExperimentSummary(
            experiment_id="empty-metrics-test",
            run_type="backtest",
            run_name="test",
            strategy_name=None,
            sweep_name=None,
            symbol=None,
            tags=[],
            created_at=None,
            metrics={},
            params={},
        )

        builder = HtmlReportBuilder(output_dir=temp_dir)
        report_path = builder.build_experiment_report(summary)

        assert report_path.exists()

    def test_report_with_none_values(self, temp_dir):
        """Test Report mit None-Werten in Metriken."""
        from src.analytics.explorer import ExperimentSummary
        from src.reporting.html_reports import HtmlReportBuilder

        summary = ExperimentSummary(
            experiment_id="none-values-test",
            run_type="backtest",
            run_name="test",
            strategy_name=None,
            sweep_name=None,
            symbol=None,
            tags=[],
            created_at=None,
            metrics={
                "total_return": None,
                "sharpe": None,
            },
            params={},
        )

        builder = HtmlReportBuilder(output_dir=temp_dir)
        report_path = builder.build_experiment_report(summary)

        assert report_path.exists()
        content = report_path.read_text()
        # None-Werte sollten als "-" dargestellt werden
        # (in den Metric Cards, aber diese werden nur für non-None erstellt)

    def test_sweep_with_empty_best_runs(self, temp_dir):
        """Test Sweep-Report mit leeren Best Runs."""
        from src.analytics.explorer import SweepOverview
        from src.reporting.html_reports import HtmlReportBuilder

        overview = SweepOverview(
            sweep_name="empty_sweep",
            strategy_key="test",
            run_count=0,
            best_runs=[],
            metric_stats={},
            param_ranges={},
        )

        builder = HtmlReportBuilder(output_dir=temp_dir)
        report_path = builder.build_sweep_report(overview, [], metric="sharpe")

        assert report_path.exists()

    def test_special_characters_in_names(self, temp_dir):
        """Test Report mit Sonderzeichen in Namen."""
        from src.analytics.explorer import ExperimentSummary
        from src.reporting.html_reports import HtmlReportBuilder

        summary = ExperimentSummary(
            experiment_id="special-chars-test",
            run_type="backtest",
            run_name='Test & Strategy <v1> "quoted"',
            strategy_name="strategy/with/slashes",
            sweep_name=None,
            symbol="BTC/EUR",
            tags=["tag<1>", "tag&2"],
            created_at=datetime.now(),
            metrics={"total_return": 0.1},
            params={"param<key>": "value&test"},
        )

        builder = HtmlReportBuilder(output_dir=temp_dir)
        report_path = builder.build_experiment_report(summary)

        assert report_path.exists()
        content = report_path.read_text()

        # Sonderzeichen sollten escaped sein
        assert "&amp;" in content
        assert "&lt;" in content
        assert "&gt;" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
