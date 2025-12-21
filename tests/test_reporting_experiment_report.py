# tests/test_reporting_experiment_report.py
"""
Tests für src/reporting/experiment_report.py (Phase 30)
========================================================

Testet:
- summarize_experiment_results
- find_best_params
- build_experiment_report
- Plot-Funktionen (Heatmap, Histogram)
"""

from __future__ import annotations

import pytest

pytest.importorskip("matplotlib")

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import numpy as np
import pytest

from src.reporting.base import Report, ReportSection
from src.reporting.experiment_report import (
    summarize_experiment_results,
    find_best_params,
    build_experiment_summary_section,
    build_top_runs_section,
    build_best_params_section,
    build_experiment_report,
    save_experiment_report,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_sweep_df() -> pd.DataFrame:
    """Sample Sweep-Ergebnisse DataFrame."""
    np.random.seed(42)
    n_runs = 50

    # Generiere Parameter-Kombinationen
    rsi_windows = [10, 14, 20, 25, 30]
    thresholds = [25, 30, 35, 40]

    data: List[Dict[str, Any]] = []
    for i in range(n_runs):
        rsi_window = rsi_windows[i % len(rsi_windows)]
        threshold = thresholds[i % len(thresholds)]

        # Simuliere Metriken (mit etwas Korrelation)
        base_sharpe = 0.5 + (rsi_window / 100) + np.random.normal(0, 0.3)
        base_return = 0.05 + (threshold / 200) + np.random.normal(0, 0.05)

        data.append(
            {
                "run_id": f"run_{i:04d}",
                "param_rsi_window": rsi_window,
                "param_lower_threshold": threshold,
                "param_upper_threshold": 100 - threshold,
                "metric_sharpe": base_sharpe,
                "metric_total_return": base_return,
                "metric_max_drawdown": -abs(np.random.normal(0.1, 0.03)),
                "metric_win_rate": 0.45 + np.random.normal(0, 0.1),
            }
        )

    return pd.DataFrame(data)


@pytest.fixture
def minimal_sweep_df() -> pd.DataFrame:
    """Minimales Sweep-DataFrame für einfache Tests."""
    return pd.DataFrame(
        {
            "param_fast": [5, 10, 15],
            "param_slow": [50, 100, 150],
            "metric_sharpe": [1.0, 1.5, 0.8],
            "metric_return": [0.10, 0.15, 0.05],
        }
    )


# =============================================================================
# summarize_experiment_results Tests
# =============================================================================


class TestSummarizeExperimentResults:
    """Tests für summarize_experiment_results()."""

    def test_returns_dict(self, sample_sweep_df: pd.DataFrame) -> None:
        """Test: Gibt Dictionary mit erwarteten Keys zurück."""
        result = summarize_experiment_results(sample_sweep_df)

        assert isinstance(result, dict)
        assert "summary" in result
        assert "top_runs" in result

    def test_summary_contains_metric_stats(self, sample_sweep_df: pd.DataFrame) -> None:
        """Test: Summary enthält Statistiken für jede Metrik."""
        result = summarize_experiment_results(sample_sweep_df)
        summary = result["summary"]

        assert isinstance(summary, pd.DataFrame)
        assert len(summary) > 0

        # Sollte Spalten haben
        assert "metric" in summary.columns
        assert "mean" in summary.columns
        assert "min" in summary.columns
        assert "max" in summary.columns

    def test_top_runs_sorted(self, minimal_sweep_df: pd.DataFrame) -> None:
        """Test: Top-Runs sind sortiert nach Metrik."""
        result = summarize_experiment_results(
            minimal_sweep_df,
            top_n=3,
            sort_metric="metric_sharpe",
        )
        top_runs = result["top_runs"]

        assert len(top_runs) == 3
        # Höchster Sharpe sollte zuerst sein
        assert top_runs.iloc[0]["metric_sharpe"] == 1.5

    def test_top_n_limit(self, sample_sweep_df: pd.DataFrame) -> None:
        """Test: top_n limitiert Ergebnisse."""
        result = summarize_experiment_results(sample_sweep_df, top_n=5)
        assert len(result["top_runs"]) == 5

    def test_param_stats(self, sample_sweep_df: pd.DataFrame) -> None:
        """Test: Parameter-Statistiken werden berechnet."""
        result = summarize_experiment_results(sample_sweep_df)

        assert "param_stats" in result
        param_stats = result["param_stats"]

        assert "parameter" in param_stats.columns
        assert "unique_values" in param_stats.columns


# =============================================================================
# find_best_params Tests
# =============================================================================


class TestFindBestParams:
    """Tests für find_best_params()."""

    def test_finds_best(self, minimal_sweep_df: pd.DataFrame) -> None:
        """Test: Findet beste Parameter-Kombination."""
        best = find_best_params(minimal_sweep_df, sort_metric="metric_sharpe")

        assert "params" in best
        assert "metrics" in best
        assert best["params"]["fast"] == 10  # Hat Sharpe 1.5
        assert best["params"]["slow"] == 100

    def test_ascending(self, minimal_sweep_df: pd.DataFrame) -> None:
        """Test: ascending=True findet niedrigsten Wert."""
        # Für max_drawdown wäre niedrigster Wert "besser" (weniger negativ)
        df = minimal_sweep_df.copy()
        df["metric_drawdown"] = [-0.10, -0.05, -0.15]

        best = find_best_params(df, sort_metric="metric_drawdown", ascending=True)
        assert best["metrics"]["drawdown"] == -0.15  # Niedrigster (schlechtester) Wert

    def test_missing_metric(self, minimal_sweep_df: pd.DataFrame) -> None:
        """Test: Fehlende Metrik gibt leeres Dict zurück."""
        best = find_best_params(minimal_sweep_df, sort_metric="metric_nonexistent")
        assert best == {}


# =============================================================================
# Section Builder Tests
# =============================================================================


class TestBuildExperimentSummarySectionFunc:
    """Tests für build_experiment_summary_section()."""

    def test_creates_section(self, sample_sweep_df: pd.DataFrame) -> None:
        """Test: Section wird erstellt."""
        result = summarize_experiment_results(sample_sweep_df)
        section = build_experiment_summary_section(result["summary"])

        assert isinstance(section, ReportSection)
        assert section.title == "Metric Statistics"

    def test_empty_df(self) -> None:
        """Test: Leeres DataFrame."""
        section = build_experiment_summary_section(pd.DataFrame())
        assert "No metrics" in section.content_markdown


class TestBuildTopRunsSection:
    """Tests für build_top_runs_section()."""

    def test_creates_section(self, sample_sweep_df: pd.DataFrame) -> None:
        """Test: Section wird erstellt."""
        result = summarize_experiment_results(sample_sweep_df, top_n=10)
        section = build_top_runs_section(result["top_runs"])

        assert isinstance(section, ReportSection)
        assert section.content_markdown != ""

    def test_empty_df(self) -> None:
        """Test: Leeres DataFrame."""
        section = build_top_runs_section(pd.DataFrame())
        assert "No runs" in section.content_markdown


class TestBuildBestParamsSection:
    """Tests für build_best_params_section()."""

    def test_creates_section(self, minimal_sweep_df: pd.DataFrame) -> None:
        """Test: Section wird erstellt."""
        best = find_best_params(minimal_sweep_df, sort_metric="metric_sharpe")
        section = build_best_params_section(best)

        assert isinstance(section, ReportSection)
        assert "Parameters" in section.content_markdown
        assert "Metrics" in section.content_markdown

    def test_empty_best(self) -> None:
        """Test: Leeres best-Dict."""
        section = build_best_params_section({})
        assert "No best parameters" in section.content_markdown


# =============================================================================
# Full Report Builder Tests
# =============================================================================


class TestBuildExperimentReport:
    """Tests für build_experiment_report()."""

    def test_basic_report(self, sample_sweep_df: pd.DataFrame, tmp_path: Path) -> None:
        """Test: Basis-Report wird erstellt."""
        report = build_experiment_report(
            title="Sweep Test",
            df=sample_sweep_df,
            output_dir=tmp_path / "images",
        )

        assert isinstance(report, Report)
        assert report.title == "Sweep Test"
        assert len(report.sections) >= 3  # Overview, Best, Top Runs

    def test_report_sections(self, sample_sweep_df: pd.DataFrame, tmp_path: Path) -> None:
        """Test: Report enthält erwartete Sections."""
        report = build_experiment_report(
            title="Section Test",
            df=sample_sweep_df,
            top_n=10,
            output_dir=tmp_path / "images",
        )

        section_titles = [s.title for s in report.sections]

        assert "Overview" in section_titles
        assert "Best Parameter Combination" in section_titles
        # Top Runs sollte den Metrik-Namen enthalten
        assert any("Top" in t and "Sharpe" in t for t in section_titles)

    def test_report_with_heatmap(self, sample_sweep_df: pd.DataFrame, tmp_path: Path) -> None:
        """Test: Report mit Heatmap-Visualisierung."""
        report = build_experiment_report(
            title="Heatmap Test",
            df=sample_sweep_df,
            heatmap_params=("param_rsi_window", "param_lower_threshold"),
            output_dir=tmp_path / "images",
        )

        # Sollte Visualizations-Section haben
        section_titles = [s.title for s in report.sections]
        assert "Visualizations" in section_titles

        # Sollte Heatmap-Datei erstellt haben
        assert (tmp_path / "images" / "heatmap.png").exists()

    def test_report_metadata(self, sample_sweep_df: pd.DataFrame, tmp_path: Path) -> None:
        """Test: Metadata wird korrekt gesetzt."""
        report = build_experiment_report(
            title="Meta Test",
            df=sample_sweep_df,
            metadata={"experiment": "test123"},
            output_dir=tmp_path / "images",
        )

        assert "experiment" in report.metadata
        assert report.metadata["total_runs"] == len(sample_sweep_df)

    def test_report_ascending_sort(self, minimal_sweep_df: pd.DataFrame, tmp_path: Path) -> None:
        """Test: ascending=True für Sortierung."""
        df = minimal_sweep_df.copy()
        df["metric_drawdown"] = [-0.10, -0.05, -0.15]

        report = build_experiment_report(
            title="Ascending Test",
            df=df,
            sort_metric="metric_drawdown",
            ascending=True,
            output_dir=tmp_path / "images",
        )

        assert isinstance(report, Report)


class TestSaveExperimentReport:
    """Tests für save_experiment_report()."""

    def test_save_markdown(self, sample_sweep_df: pd.DataFrame, tmp_path: Path) -> None:
        """Test: Report wird als Markdown gespeichert."""
        report = build_experiment_report(
            title="Save Test",
            df=sample_sweep_df,
            output_dir=tmp_path / "images",
        )

        output_file = tmp_path / "report.md"
        path = save_experiment_report(report, output_file)

        assert Path(path).exists()
        content = Path(path).read_text()
        assert "# Save Test" in content

    def test_save_html(self, sample_sweep_df: pd.DataFrame, tmp_path: Path) -> None:
        """Test: Report wird als HTML gespeichert."""
        report = build_experiment_report(
            title="HTML Test",
            df=sample_sweep_df,
            output_dir=tmp_path / "images",
        )

        output_file = tmp_path / "report.html"
        path = save_experiment_report(report, output_file, format="html")

        assert Path(path).exists()
        content = Path(path).read_text()
        assert "<!DOCTYPE html>" in content


# =============================================================================
# Integration Tests
# =============================================================================


class TestExperimentReportIntegration:
    """Integration-Tests für kompletten Workflow."""

    def test_full_workflow(self, sample_sweep_df: pd.DataFrame, tmp_path: Path) -> None:
        """Test: Kompletter Workflow von DataFrame zu Report."""
        # 1. Analysiere Ergebnisse
        summary = summarize_experiment_results(
            sample_sweep_df,
            top_n=10,
            sort_metric="metric_sharpe",
        )

        assert "summary" in summary
        assert "top_runs" in summary
        assert len(summary["top_runs"]) == 10

        # 2. Baue Report
        report = build_experiment_report(
            title="Integration Test",
            df=sample_sweep_df,
            sort_metric="metric_sharpe",
            top_n=10,
            heatmap_params=("param_rsi_window", "param_lower_threshold"),
            output_dir=tmp_path / "images",
        )

        # 3. Speichere Report
        output_file = tmp_path / "integration_report.md"
        save_experiment_report(report, output_file)

        # 4. Verifiziere Output
        assert output_file.exists()
        content = output_file.read_text()

        # Sollte alle wichtigen Sections enthalten
        assert "# Integration Test" in content
        assert "## Overview" in content
        assert "## Best Parameter Combination" in content
        assert "Total Runs" in content
        assert "50" in content  # 50 runs
