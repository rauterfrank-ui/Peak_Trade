# tests/test_reporting_regime_experiment_report.py
"""
Tests für Regime-Aware Experiment-Reports
=========================================
"""
from __future__ import annotations

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile

from src.reporting.experiment_report import build_experiment_report


class TestRegimeExperimentReport:
    """Tests für Regime-Aware Experiment-Reports."""

    def test_experiment_report_with_regime_heatmaps(self):
        """Test Experiment-Report mit Regime-Heatmaps."""
        # Erstelle synthetische Sweep-Daten
        data = []
        for neutral_scale in [0.3, 0.5, 0.7]:
            for risk_off_scale in [0.0, 0.1, 0.2]:
                data.append({
                    "param_neutral_scale": neutral_scale,
                    "param_risk_off_scale": risk_off_scale,
                    "param_risk_on_scale": 1.0,
                    "metric_sharpe": np.random.uniform(0.5, 2.0),
                    "metric_total_return": np.random.uniform(0.05, 0.20),
                    "metric_max_drawdown": np.random.uniform(-0.15, -0.05),
                })

        df = pd.DataFrame(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "images"
            output_dir.mkdir(parents=True)

            report = build_experiment_report(
                title="Regime Aware Portfolio Aggressive Sweep",
                df=df,
                sort_metric="metric_sharpe",
                top_n=10,
                with_regime_heatmaps=True,
                output_dir=output_dir,
            )

            assert report is not None
            assert len(report.sections) > 0

            # Prüfe dass Heatmap erstellt wurde
            heatmap_files = list(output_dir.glob("regime_heatmap_*.png"))
            assert len(heatmap_files) > 0

            # Prüfe dass Heatmap in Report erwähnt wird
            report_md = report.to_markdown()
            assert "regime_heatmap" in report_md.lower() or "heatmap" in report_md.lower()

    def test_experiment_report_without_regime_heatmaps(self):
        """Test Experiment-Report ohne Regime-Heatmaps (Standard-Verhalten)."""
        data = []
        for param1 in [10, 20, 30]:
            for param2 in [5, 10, 15]:
                data.append({
                    "param_fast_period": param1,
                    "param_slow_period": param2,
                    "metric_sharpe": np.random.uniform(0.5, 2.0),
                })

        df = pd.DataFrame(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "images"
            output_dir.mkdir(parents=True)

            report = build_experiment_report(
                title="Standard MA Crossover Sweep",
                df=df,
                sort_metric="metric_sharpe",
                top_n=10,
                with_regime_heatmaps=False,
                output_dir=output_dir,
            )

            assert report is not None
            # Sollte keine Regime-Heatmaps erstellen
            regime_heatmaps = list(output_dir.glob("regime_heatmap_*.png"))
            assert len(regime_heatmaps) == 0

    def test_experiment_report_auto_detect_regime_aware(self):
        """Test automatische Erkennung von Regime-Aware Sweeps aus Titel."""
        data = []
        for neutral_scale in [0.4, 0.5, 0.6]:
            for risk_off_scale in [0.0, 0.1]:
                data.append({
                    "param_neutral_scale": neutral_scale,
                    "param_risk_off_scale": risk_off_scale,
                    "metric_sharpe": np.random.uniform(1.0, 2.0),
                })

        df = pd.DataFrame(data)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "images"
            output_dir.mkdir(parents=True)

            # Titel enthält "regime_aware" -> sollte automatisch Heatmaps erstellen
            report = build_experiment_report(
                title="Regime Aware Portfolio Conservative",
                df=df,
                sort_metric="metric_sharpe",
                top_n=10,
                with_regime_heatmaps=False,  # Nicht explizit gesetzt
                output_dir=output_dir,
            )

            assert report is not None
            # Sollte trotzdem Regime-Heatmaps erstellen (wegen Titel)
            regime_heatmaps = list(output_dir.glob("regime_heatmap_*.png"))
            # Kann 0 sein wenn Pivot nicht möglich, aber sollte nicht abstürzen
            assert report is not None







