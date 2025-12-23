# tests/test_sweep_visualization.py
"""
Tests für src/reporting/sweep_visualization.py (Phase 43)
==========================================================

Testet Sweep-Visualisierungsfunktionen.
"""

import pytest

pytest.importorskip("matplotlib")

from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import numpy as np

from src.reporting.sweep_visualization import (
    plot_metric_vs_single_param,
    plot_metric_heatmap_two_params,
    create_drawdown_heatmap,
    generate_default_sweep_plots,
)


# =============================================================================
# PLOT METRIC VS SINGLE PARAM TESTS
# =============================================================================


class TestPlotMetricVsSingleParam:
    """Tests für plot_metric_vs_single_param()."""

    def test_plot_metric_vs_single_param_creates_file(self):
        """Plot wird erstellt."""
        df = pd.DataFrame(
            {
                "param_rsi_period": [7, 14, 21, 28],
                "metric_total_return": [0.1, 0.15, 0.12, 0.18],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = plot_metric_vs_single_param(
                df=df,
                param_name="rsi_period",
                metric_name="total_return",
                sweep_name="test_sweep",
                output_dir=output_dir,
            )

            assert result is not None
            assert result.exists()
            assert result.suffix == ".png"
            assert "test_sweep" in result.name
            assert "rsi_period" in result.name

    def test_plot_metric_vs_single_param_with_prefix(self):
        """Funktioniert auch mit param_/metric_ Prefix."""
        df = pd.DataFrame(
            {
                "param_rsi_period": [7, 14, 21],
                "metric_sharpe_ratio": [1.2, 1.5, 1.3],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = plot_metric_vs_single_param(
                df=df,
                param_name="param_rsi_period",
                metric_name="metric_sharpe_ratio",
                sweep_name="test",
                output_dir=output_dir,
            )

            assert result is not None
            assert result.exists()

    def test_plot_metric_vs_single_param_missing_param_raises(self):
        """Fehler wenn Parameter fehlt."""
        df = pd.DataFrame(
            {
                "metric_total_return": [0.1, 0.15],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            with pytest.raises(ValueError, match=".*nicht im DataFrame gefunden"):
                plot_metric_vs_single_param(
                    df=df,
                    param_name="nonexistent",
                    metric_name="total_return",
                    sweep_name="test",
                    output_dir=output_dir,
                )

    def test_plot_metric_vs_single_param_missing_metric_raises(self):
        """Fehler wenn Metrik fehlt."""
        df = pd.DataFrame(
            {
                "param_rsi_period": [7, 14],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            with pytest.raises(ValueError, match=".*nicht im DataFrame gefunden"):
                plot_metric_vs_single_param(
                    df=df,
                    param_name="rsi_period",
                    metric_name="nonexistent",
                    sweep_name="test",
                    output_dir=output_dir,
                )

    def test_plot_metric_vs_single_param_filters_nan(self):
        """NaN-Werte werden gefiltert."""
        df = pd.DataFrame(
            {
                "param_rsi_period": [7, 14, 21, 28],
                "metric_total_return": [0.1, float("nan"), 0.12, 0.18],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = plot_metric_vs_single_param(
                df=df,
                param_name="rsi_period",
                metric_name="total_return",
                sweep_name="test",
                output_dir=output_dir,
            )

            # Sollte trotzdem funktionieren (NaN wird gefiltert)
            assert result is not None


# =============================================================================
# PLOT METRIC HEATMAP TWO PARAMS TESTS
# =============================================================================


class TestPlotMetricHeatmapTwoParams:
    """Tests für plot_metric_heatmap_two_params()."""

    def test_plot_metric_heatmap_two_params_creates_file(self):
        """Heatmap wird erstellt."""
        df = pd.DataFrame(
            {
                "param_fast_period": [5, 5, 10, 10, 20, 20],
                "param_slow_period": [50, 100, 50, 100, 50, 100],
                "metric_sharpe_ratio": [1.2, 1.5, 1.3, 1.6, 1.1, 1.4],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = plot_metric_heatmap_two_params(
                df=df,
                param_x="fast_period",
                param_y="slow_period",
                metric_name="sharpe_ratio",
                sweep_name="test_sweep",
                output_dir=output_dir,
            )

            assert result is not None
            assert result.exists()
            assert result.suffix == ".png"
            assert "heatmap" in result.name.lower()

    def test_plot_metric_heatmap_two_params_missing_param_raises(self):
        """Fehler wenn Parameter fehlt."""
        df = pd.DataFrame(
            {
                "param_fast_period": [5, 10],
                "metric_sharpe_ratio": [1.2, 1.5],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            with pytest.raises(ValueError, match=".*nicht im DataFrame gefunden"):
                plot_metric_heatmap_two_params(
                    df=df,
                    param_x="fast_period",
                    param_y="nonexistent",
                    metric_name="sharpe_ratio",
                    sweep_name="test",
                    output_dir=output_dir,
                )

    def test_plot_metric_heatmap_two_params_filters_nan(self):
        """NaN-Werte werden gefiltert."""
        df = pd.DataFrame(
            {
                "param_fast_period": [5, 5, 10],
                "param_slow_period": [50, 100, 50],
                "metric_sharpe_ratio": [1.2, float("nan"), 1.3],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = plot_metric_heatmap_two_params(
                df=df,
                param_x="fast_period",
                param_y="slow_period",
                metric_name="sharpe_ratio",
                sweep_name="test",
                output_dir=output_dir,
            )

            # Sollte trotzdem funktionieren
            assert result is not None


# =============================================================================
# GENERATE DEFAULT SWEEP PLOTS TESTS
# =============================================================================


class TestGenerateDefaultSweepPlots:
    """Tests für generate_default_sweep_plots()."""

    def test_generate_default_sweep_plots_creates_plots(self):
        """Standard-Plots werden erstellt."""
        df = pd.DataFrame(
            {
                "param_rsi_period": [7, 14, 21, 7, 14, 21],
                "param_oversold_level": [20, 20, 20, 30, 30, 30],
                "metric_total_return": [0.1, 0.15, 0.12, 0.11, 0.16, 0.13],
                "metric_sharpe_ratio": [1.2, 1.5, 1.3, 1.25, 1.55, 1.35],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            plots = generate_default_sweep_plots(
                df=df,
                sweep_name="test_sweep",
                output_dir=output_dir,
                metric_primary="metric_total_return",
            )

            assert isinstance(plots, dict)
            assert len(plots) > 0
            # Prüfe dass alle Pfade existieren
            for plot_path in plots.values():
                assert plot_path.exists()
                assert plot_path.suffix == ".png"

    def test_generate_default_sweep_plots_with_fallback(self):
        """Fallback-Metrik wird verwendet wenn primary fehlt."""
        df = pd.DataFrame(
            {
                "param_rsi_period": [7, 14, 21],
                "metric_total_return": [0.1, 0.15, 0.12],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            plots = generate_default_sweep_plots(
                df=df,
                sweep_name="test",
                output_dir=output_dir,
                metric_primary="metric_sharpe_ratio",  # Fehlt
                metric_fallback="metric_total_return",
            )

            # Sollte trotzdem Plots erzeugen (mit Fallback)
            assert len(plots) > 0

    def test_generate_default_sweep_plots_no_params_returns_empty(self):
        """Leeres Dict wenn keine Parameter vorhanden."""
        df = pd.DataFrame(
            {
                "metric_total_return": [0.1, 0.15],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            plots = generate_default_sweep_plots(
                df=df,
                sweep_name="test",
                output_dir=output_dir,
            )

            assert plots == {}

    def test_generate_default_sweep_plots_creates_heatmap(self):
        """Heatmap wird erstellt wenn mindestens 2 Parameter vorhanden."""
        df = pd.DataFrame(
            {
                "param_fast_period": [5, 5, 10, 10],
                "param_slow_period": [50, 100, 50, 100],
                "metric_sharpe_ratio": [1.2, 1.5, 1.3, 1.6],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            plots = generate_default_sweep_plots(
                df=df,
                sweep_name="test",
                output_dir=output_dir,
            )

            # Sollte Heatmap enthalten
            assert "heatmap_2d" in plots
            assert plots["heatmap_2d"].exists()


# =============================================================================
# CREATE DRAWDOWN HEATMAP TESTS
# =============================================================================


class TestCreateDrawdownHeatmap:
    """Tests für create_drawdown_heatmap()."""

    def test_create_drawdown_heatmap_creates_file(self):
        """Drawdown-Heatmap wird erstellt."""
        df = pd.DataFrame(
            {
                "param_fast_period": [5, 5, 10, 10, 20, 20],
                "param_slow_period": [50, 100, 50, 100, 50, 100],
                "metric_max_drawdown": [-0.05, -0.10, -0.08, -0.12, -0.06, -0.09],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = create_drawdown_heatmap(
                df=df,
                param_x="fast_period",
                param_y="slow_period",
                metric_col="max_drawdown",
                sweep_name="test_sweep",
                output_dir=output_dir,
            )

            assert result is not None
            assert result.exists()
            assert result.suffix == ".png"
            assert "drawdown" in result.name.lower()
            assert "fast_period" in result.name or "fast" in result.name
            assert "slow_period" in result.name or "slow" in result.name

    def test_create_drawdown_heatmap_with_prefix(self):
        """Funktioniert auch mit param_/metric_ Prefix."""
        df = pd.DataFrame(
            {
                "param_rsi_period": [7, 14, 21, 7, 14, 21],
                "param_oversold_level": [20, 20, 20, 30, 30, 30],
                "metric_max_drawdown": [-0.05, -0.10, -0.08, -0.06, -0.12, -0.09],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = create_drawdown_heatmap(
                df=df,
                param_x="param_rsi_period",
                param_y="param_oversold_level",
                metric_col="metric_max_drawdown",
                sweep_name="test",
                output_dir=output_dir,
            )

            assert result is not None
            assert result.exists()

    def test_create_drawdown_heatmap_missing_param_raises(self):
        """Fehler wenn Parameter fehlt."""
        df = pd.DataFrame(
            {
                "param_fast_period": [5, 10],
                "metric_max_drawdown": [-0.05, -0.10],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            with pytest.raises(ValueError, match=".*nicht im DataFrame gefunden"):
                create_drawdown_heatmap(
                    df=df,
                    param_x="fast_period",
                    param_y="nonexistent",
                    metric_col="max_drawdown",
                    sweep_name="test",
                    output_dir=output_dir,
                )

    def test_create_drawdown_heatmap_missing_metric_raises(self):
        """Fehler wenn Drawdown-Metrik fehlt."""
        df = pd.DataFrame(
            {
                "param_fast_period": [5, 5, 10, 10],
                "param_slow_period": [50, 100, 50, 100],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            with pytest.raises(ValueError, match=".*nicht im DataFrame gefunden"):
                create_drawdown_heatmap(
                    df=df,
                    param_x="fast_period",
                    param_y="slow_period",
                    metric_col="max_drawdown",
                    sweep_name="test",
                    output_dir=output_dir,
                )

    def test_create_drawdown_heatmap_filters_nan(self):
        """NaN-Werte werden gefiltert."""
        df = pd.DataFrame(
            {
                "param_fast_period": [5, 5, 10],
                "param_slow_period": [50, 100, 50],
                "metric_max_drawdown": [-0.05, float("nan"), -0.08],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = create_drawdown_heatmap(
                df=df,
                param_x="fast_period",
                param_y="slow_period",
                metric_col="max_drawdown",
                sweep_name="test",
                output_dir=output_dir,
            )

            # Sollte trotzdem funktionieren
            assert result is not None

    def test_create_drawdown_heatmap_with_custom_title(self):
        """Funktioniert mit benutzerdefiniertem Titel."""
        df = pd.DataFrame(
            {
                "param_fast_period": [5, 5, 10, 10],
                "param_slow_period": [50, 100, 50, 100],
                "metric_max_drawdown": [-0.05, -0.10, -0.08, -0.12],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = create_drawdown_heatmap(
                df=df,
                param_x="fast_period",
                param_y="slow_period",
                metric_col="max_drawdown",
                title="Custom Drawdown Heatmap",
                sweep_name="test",
                output_dir=output_dir,
            )

            assert result is not None
            assert result.exists()


# =============================================================================
# INTEGRATION TESTS: DRAWDOWN HEATMAP IN DEFAULT PLOTS
# =============================================================================


class TestDrawdownHeatmapIntegration:
    """Integrationstests für Drawdown-Heatmaps in generate_default_sweep_plots()."""

    def test_generate_default_sweep_plots_creates_drawdown_heatmap(self):
        """Drawdown-Heatmap wird automatisch erstellt wenn max_drawdown vorhanden."""
        df = pd.DataFrame(
            {
                "param_fast_period": [5, 5, 10, 10],
                "param_slow_period": [50, 100, 50, 100],
                "metric_sharpe_ratio": [1.2, 1.5, 1.3, 1.6],
                "metric_max_drawdown": [-0.05, -0.10, -0.08, -0.12],
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            plots = generate_default_sweep_plots(
                df=df,
                sweep_name="test",
                output_dir=output_dir,
            )

            # Sollte Drawdown-Heatmap enthalten
            drawdown_heatmaps = [k for k in plots.keys() if "drawdown" in k.lower()]
            assert len(drawdown_heatmaps) > 0, "Drawdown-Heatmap sollte erstellt werden"

            # Prüfe dass alle Drawdown-Heatmaps existieren
            for key in drawdown_heatmaps:
                assert plots[key].exists()
                assert plots[key].suffix == ".png"

    def test_generate_default_sweep_plots_no_drawdown_metric_no_heatmap(self):
        """Keine Drawdown-Heatmap wenn max_drawdown fehlt."""
        df = pd.DataFrame(
            {
                "param_fast_period": [5, 5, 10, 10],
                "param_slow_period": [50, 100, 50, 100],
                "metric_sharpe_ratio": [1.2, 1.5, 1.3, 1.6],
                # Keine max_drawdown Spalte
            }
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            plots = generate_default_sweep_plots(
                df=df,
                sweep_name="test",
                output_dir=output_dir,
            )

            # Sollte keine Drawdown-Heatmap enthalten
            drawdown_heatmaps = [k for k in plots.keys() if "drawdown" in k.lower()]
            assert (
                len(drawdown_heatmaps) == 0
            ), "Keine Drawdown-Heatmap sollte erstellt werden wenn max_drawdown fehlt"
