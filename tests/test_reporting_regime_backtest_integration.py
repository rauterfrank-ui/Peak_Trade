# tests/test_reporting_regime_backtest_integration.py
"""
Integrationstests für Regime-Aware Backtest-Reports
===================================================
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from src.reporting.backtest_report import build_backtest_report


class TestRegimeBacktestIntegration:
    """Tests für Integration von Regime-Analyse in Backtest-Reports."""

    def test_backtest_report_with_regimes(self):
        """Test Backtest-Report mit Regime-Daten."""
        # Erstelle synthetische Daten
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        equity = pd.Series(10000.0, index=dates)
        equity.iloc[0:50] = np.linspace(10000, 11000, 50)
        equity.iloc[50:100] = np.linspace(11000, 10800, 50)

        drawdown = equity / equity.expanding().max() - 1.0

        # Regime: 50 Risk-On, 50 Neutral
        regimes = pd.Series([1] * 50 + [0] * 50, index=dates)

        metrics = {
            "total_return": 0.08,
            "sharpe": 1.2,
            "max_drawdown": -0.02,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "images"
            output_dir.mkdir(parents=True)

            report = build_backtest_report(
                title="Test Backtest with Regimes",
                metrics=metrics,
                equity_curve=equity,
                drawdown_series=drawdown,
                regimes=regimes,
                output_dir=output_dir,
            )

            # Prüfe dass Report erstellt wurde
            assert report is not None
            assert len(report.sections) > 0

            # Prüfe dass Regime-Section vorhanden ist
            regime_sections = [s for s in report.sections if "Regime" in s.title]
            assert len(regime_sections) > 0

            # Prüfe dass Equity-Plot mit Regimes erstellt wurde
            equity_plot = output_dir / "equity_with_regimes.png"
            assert equity_plot.exists()

            # Prüfe dass Contribution-Plot erstellt wurde
            contribution_plot = output_dir / "regime_contribution.png"
            assert contribution_plot.exists()

            # Prüfe dass Contribution-Plot im Report erwähnt wird
            report_md = report.to_markdown()
            assert "contribution" in report_md.lower() or "Contribution" in report_md

            # Prüfe dass Regime-Section Contribution & Time-Share enthält
            regime_section = regime_sections[0]
            assert "Contribution" in regime_section.content_markdown or "contribution" in regime_section.content_markdown.lower()
            assert "Bars [%]" in regime_section.content_markdown or "Time Share" in regime_section.content_markdown

    def test_backtest_report_without_regimes(self):
        """Test Backtest-Report ohne Regime-Daten (sollte normal funktionieren)."""
        dates = pd.date_range(start="2023-01-01", periods=50, freq="D")
        equity = pd.Series(10000.0, index=dates)
        drawdown = equity / equity.expanding().max() - 1.0

        metrics = {
            "total_return": 0.05,
            "sharpe": 1.0,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "images"
            output_dir.mkdir(parents=True)

            report = build_backtest_report(
                title="Test Backtest without Regimes",
                metrics=metrics,
                equity_curve=equity,
                drawdown_series=drawdown,
                regimes=None,  # Keine Regime-Daten
                output_dir=output_dir,
            )

            assert report is not None
            # Sollte keine Regime-Section haben
            regime_sections = [s for s in report.sections if "Regime" in s.title]
            assert len(regime_sections) == 0

            # Standard Equity-Plot sollte existieren
            equity_plot = output_dir / "equity_curve.png"
            assert equity_plot.exists()

    def test_backtest_report_with_invalid_regimes(self):
        """Test Backtest-Report mit ungültigen Regime-Daten (sollte nicht abstürzen)."""
        dates = pd.date_range(start="2023-01-01", periods=50, freq="D")
        equity = pd.Series(10000.0, index=dates)
        drawdown = equity / equity.expanding().max() - 1.0

        # Regime mit falscher Länge
        regimes = pd.Series([1, 0, -1], index=dates[:3])

        metrics = {
            "total_return": 0.05,
            "sharpe": 1.0,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "images"
            output_dir.mkdir(parents=True)

            # Sollte nicht abstürzen, sondern Fehler abfangen
            report = build_backtest_report(
                title="Test Backtest with Invalid Regimes",
                metrics=metrics,
                equity_curve=equity,
                drawdown_series=drawdown,
                regimes=regimes,
                output_dir=output_dir,
            )

            assert report is not None
            # Sollte eine Regime-Section mit Fehler-Hinweis haben
            regime_sections = [s for s in report.sections if "Regime" in s.title]
            if len(regime_sections) > 0:
                # Wenn Section vorhanden, sollte sie einen Fehler-Hinweis enthalten
                assert "konnte nicht" in regime_sections[0].content_markdown.lower() or \
                       "nicht erstellt" in regime_sections[0].content_markdown.lower()

