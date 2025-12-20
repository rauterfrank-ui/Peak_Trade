# tests/test_reporting_backtest_report.py
"""
Tests für src/reporting/backtest_report.py (Phase 30)
=====================================================

Testet:
- build_backtest_summary_section
- build_trade_stats_section
- build_parameters_section
- build_backtest_report
- Plot-Funktionen (mit tmp_path)
"""
from __future__ import annotations

import pytest
pytest.importorskip("matplotlib")

import os
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import numpy as np
import pytest

from src.reporting.base import Report, ReportSection
from src.reporting.backtest_report import (
    build_backtest_summary_section,
    build_trade_stats_section,
    build_parameters_section,
    build_backtest_report,
    save_backtest_report,
    build_quick_backtest_report,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_metrics() -> Dict[str, float]:
    """Sample Backtest-Metriken."""
    return {
        "total_return": 0.15,
        "sharpe": 1.52,
        "max_drawdown": -0.08,
        "cagr": 0.12,
        "win_rate": 0.55,
        "total_trades": 100,
        "profit_factor": 1.8,
    }


@pytest.fixture
def sample_equity_curve() -> pd.Series:
    """Sample Equity-Curve."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    returns = np.random.normal(0.001, 0.02, 100)
    equity = 10000 * (1 + pd.Series(returns)).cumprod()
    return pd.Series(equity.values, index=dates)


@pytest.fixture
def sample_trades() -> List[Dict[str, Any]]:
    """Sample Trade-Liste."""
    return [
        {"pnl": 100, "side": "buy"},
        {"pnl": -50, "side": "sell"},
        {"pnl": 75, "side": "buy"},
        {"pnl": 200, "side": "buy"},
        {"pnl": -30, "side": "sell"},
    ]


@pytest.fixture
def sample_params() -> Dict[str, Any]:
    """Sample Strategie-Parameter."""
    return {
        "fast_period": 10,
        "slow_period": 50,
        "symbol": "BTC/EUR",
        "timeframe": "1h",
    }


# =============================================================================
# Section Builder Tests
# =============================================================================


class TestBuildBacktestSummarySection:
    """Tests für build_backtest_summary_section()."""

    def test_basic_metrics(self, sample_metrics: Dict[str, float]) -> None:
        """Test: Section wird korrekt erstellt."""
        section = build_backtest_summary_section(sample_metrics)

        assert isinstance(section, ReportSection)
        assert section.title == "Performance Summary"
        assert section.content_markdown != ""

    def test_metrics_in_markdown(self, sample_metrics: Dict[str, float]) -> None:
        """Test: Alle Metriken erscheinen in Markdown."""
        section = build_backtest_summary_section(sample_metrics)
        md = section.content_markdown

        # Check table structure
        assert "| Metric | Value |" in md
        assert "|" in md

        # Check some metrics appear (formatted)
        assert "Return" in md or "return" in md.lower()
        assert "Sharpe" in md or "sharpe" in md.lower()

    def test_empty_metrics(self) -> None:
        """Test: Leere Metriken ergeben leere Tabelle."""
        section = build_backtest_summary_section({})
        # Sollte immer noch eine gültige Section sein
        assert isinstance(section, ReportSection)

    def test_custom_title(self, sample_metrics: Dict[str, float]) -> None:
        """Test: Custom Title funktioniert."""
        section = build_backtest_summary_section(sample_metrics, title="Custom Summary")
        assert section.title == "Custom Summary"


class TestBuildTradeStatsSection:
    """Tests für build_trade_stats_section()."""

    def test_with_trades(self, sample_trades: List[Dict[str, Any]]) -> None:
        """Test: Trade-Stats werden korrekt berechnet."""
        section = build_trade_stats_section(sample_trades)

        assert isinstance(section, ReportSection)
        md = section.content_markdown

        # Check calculated stats
        assert "Total Trades" in md
        assert "5" in md  # 5 trades
        assert "Win Rate" in md

    def test_empty_trades(self) -> None:
        """Test: Leere Trade-Liste."""
        section = build_trade_stats_section([])
        assert "No trades" in section.content_markdown

    def test_all_wins(self) -> None:
        """Test: Alle Trades sind Gewinner."""
        trades = [{"pnl": 100}, {"pnl": 50}]
        section = build_trade_stats_section(trades)
        md = section.content_markdown

        # Win rate sollte 100% sein
        assert "100" in md  # 100%

    def test_all_losses(self) -> None:
        """Test: Alle Trades sind Verlierer."""
        trades = [{"pnl": -100}, {"pnl": -50}]
        section = build_trade_stats_section(trades)
        md = section.content_markdown

        # Win rate sollte 0% sein
        assert "0" in md


class TestBuildParametersSection:
    """Tests für build_parameters_section()."""

    def test_with_params(self, sample_params: Dict[str, Any]) -> None:
        """Test: Parameter werden angezeigt."""
        section = build_parameters_section(sample_params)

        assert isinstance(section, ReportSection)
        md = section.content_markdown

        assert "Parameter" in md or "parameter" in md.lower()
        assert "10" in md  # fast_period
        assert "50" in md  # slow_period

    def test_empty_params(self) -> None:
        """Test: Leere Parameter."""
        section = build_parameters_section({})
        assert "No parameters" in section.content_markdown


# =============================================================================
# Full Report Builder Tests
# =============================================================================


class TestBuildBacktestReport:
    """Tests für build_backtest_report()."""

    def test_basic_report(self, sample_metrics: Dict[str, float], tmp_path: Path) -> None:
        """Test: Basis-Report wird erstellt."""
        report = build_backtest_report(
            title="Test Backtest",
            metrics=sample_metrics,
            output_dir=tmp_path / "images",
        )

        assert isinstance(report, Report)
        assert report.title == "Test Backtest"
        assert len(report.sections) >= 1  # mindestens Summary

    def test_report_with_equity(
        self,
        sample_metrics: Dict[str, float],
        sample_equity_curve: pd.Series,
        tmp_path: Path,
    ) -> None:
        """Test: Report mit Equity-Curve."""
        report = build_backtest_report(
            title="Equity Test",
            metrics=sample_metrics,
            equity_curve=sample_equity_curve,
            output_dir=tmp_path / "images",
        )

        # Sollte Charts-Section haben
        section_titles = [s.title for s in report.sections]
        assert "Charts" in section_titles

        # Sollte Plot-Datei erstellt haben
        assert (tmp_path / "images" / "equity_curve.png").exists()

    def test_report_with_drawdown(
        self,
        sample_metrics: Dict[str, float],
        sample_equity_curve: pd.Series,
        tmp_path: Path,
    ) -> None:
        """Test: Report mit Drawdown-Plot."""
        # Berechne Drawdown
        running_max = sample_equity_curve.cummax()
        drawdown = (sample_equity_curve - running_max) / running_max

        report = build_backtest_report(
            title="Drawdown Test",
            metrics=sample_metrics,
            drawdown_series=drawdown,
            output_dir=tmp_path / "images",
        )

        # Sollte Drawdown-Plot erstellt haben
        assert (tmp_path / "images" / "drawdown.png").exists()

    def test_report_with_trades(
        self,
        sample_metrics: Dict[str, float],
        sample_trades: List[Dict[str, Any]],
        tmp_path: Path,
    ) -> None:
        """Test: Report mit Trade-Stats."""
        report = build_backtest_report(
            title="Trades Test",
            metrics=sample_metrics,
            trades=sample_trades,
            output_dir=tmp_path / "images",
        )

        section_titles = [s.title for s in report.sections]
        assert "Trade Statistics" in section_titles

    def test_report_with_params(
        self,
        sample_metrics: Dict[str, float],
        sample_params: Dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """Test: Report mit Parametern."""
        report = build_backtest_report(
            title="Params Test",
            metrics=sample_metrics,
            params=sample_params,
            output_dir=tmp_path / "images",
        )

        section_titles = [s.title for s in report.sections]
        assert "Strategy Parameters" in section_titles

    def test_report_to_markdown(self, sample_metrics: Dict[str, float], tmp_path: Path) -> None:
        """Test: Report kann zu Markdown konvertiert werden."""
        report = build_backtest_report(
            title="MD Test",
            metrics=sample_metrics,
            output_dir=tmp_path / "images",
        )

        md = report.to_markdown()
        assert "# MD Test" in md
        assert "## Performance Summary" in md


class TestSaveBacktestReport:
    """Tests für save_backtest_report()."""

    def test_save_markdown(self, sample_metrics: Dict[str, float], tmp_path: Path) -> None:
        """Test: Report wird als Markdown gespeichert."""
        report = build_backtest_report(
            title="Save Test",
            metrics=sample_metrics,
            output_dir=tmp_path / "images",
        )

        output_file = tmp_path / "report.md"
        path = save_backtest_report(report, output_file, format="markdown")

        assert Path(path).exists()
        content = Path(path).read_text()
        assert "# Save Test" in content

    def test_save_html(self, sample_metrics: Dict[str, float], tmp_path: Path) -> None:
        """Test: Report wird als HTML gespeichert."""
        report = build_backtest_report(
            title="HTML Test",
            metrics=sample_metrics,
            output_dir=tmp_path / "images",
        )

        output_file = tmp_path / "report.html"
        path = save_backtest_report(report, output_file, format="html")

        assert Path(path).exists()
        content = Path(path).read_text()
        assert "<!DOCTYPE html>" in content


class TestBuildQuickBacktestReport:
    """Tests für build_quick_backtest_report()."""

    def test_quick_report(self, sample_equity_curve: pd.Series, tmp_path: Path) -> None:
        """Test: Quick Report aus Equity-Curve."""
        report = build_quick_backtest_report(
            equity_curve=sample_equity_curve,
            strategy_name="MA Crossover",
            symbol="BTC/EUR",
            output_dir=tmp_path / "images",
        )

        assert isinstance(report, Report)
        assert "MA Crossover" in report.title
        assert "BTC/EUR" in report.title

        # Sollte automatisch Metriken berechnet haben
        section_titles = [s.title for s in report.sections]
        assert "Performance Summary" in section_titles
