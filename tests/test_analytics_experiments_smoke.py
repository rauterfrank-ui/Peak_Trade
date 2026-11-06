"""
Peak_Trade Analytics Experiments Smoke Tests
=============================================
Smoke-Tests für den Analytics-Layer (experiments_analysis.py).

Diese Tests verwenden Mock-DataFrames, um keine echte Registry zu benötigen.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.analytics.experiments_analysis import (
    StrategySummary,
    PortfolioSummary,
    load_experiments_df_filtered,
    filter_backtest_runs,
    filter_portfolio_backtest_runs,
    summarize_strategies,
    summarize_portfolios,
    top_runs_by_metric,
    compare_strategies,
    write_markdown_report,
    write_portfolio_markdown_report,
    write_top_runs_markdown_report,
)
from src.core import experiments


def create_mock_experiments_df() -> pd.DataFrame:
    """Erstellt ein Mock-DataFrame mit Experiment-Daten."""
    return pd.DataFrame(
        [
            {
                "run_id": "run-001",
                "run_type": "backtest",
                "strategy_key": "ma_crossover",
                "symbol": "BTC/EUR",
                "total_return": 0.10,
                "sharpe": 1.2,
                "max_drawdown": -0.08,
                "timestamp": "2025-01-01T10:00:00",
                "metadata_json": '{"tag": "test"}',
            },
            {
                "run_id": "run-002",
                "run_type": "backtest",
                "strategy_key": "ma_crossover",
                "symbol": "ETH/EUR",
                "total_return": 0.15,
                "sharpe": 1.5,
                "max_drawdown": -0.10,
                "timestamp": "2025-01-02T10:00:00",
                "metadata_json": '{"tag": "test"}',
            },
            {
                "run_id": "run-003",
                "run_type": "backtest",
                "strategy_key": "rsi_reversion",
                "symbol": "BTC/EUR",
                "total_return": 0.05,
                "sharpe": 0.8,
                "max_drawdown": -0.05,
                "timestamp": "2025-01-03T10:00:00",
                "metadata_json": '{"tag": "other"}',
            },
            {
                "run_id": "run-004",
                "run_type": "portfolio_backtest",
                "strategy_key": None,
                "portfolio_name": "core_portfolio",
                "symbol": None,
                "total_return": 0.12,
                "sharpe": 1.3,
                "max_drawdown": -0.07,
                "timestamp": "2025-01-04T10:00:00",
                "metadata_json": "{}",
            },
            {
                "run_id": "run-005",
                "run_type": "portfolio_backtest",
                "strategy_key": None,
                "portfolio_name": "core_portfolio",
                "symbol": None,
                "total_return": 0.08,
                "sharpe": 1.1,
                "max_drawdown": -0.06,
                "timestamp": "2025-01-05T10:00:00",
                "metadata_json": "{}",
            },
        ]
    )


class TestStrategySummary:
    """Tests für StrategySummary Dataclass."""

    def test_strategy_summary_creation(self):
        """Test: StrategySummary kann erstellt werden."""
        summary = StrategySummary(
            strategy_key="ma_crossover",
            run_count=5,
            avg_total_return=0.10,
            avg_sharpe=1.2,
            avg_max_drawdown=-0.08,
            best_run_id="run-001",
        )

        assert summary.strategy_key == "ma_crossover"
        assert summary.run_count == 5
        assert summary.avg_total_return == 0.10


class TestLoadExperimentsFiltered:
    """Tests für load_experiments_df_filtered()."""

    def test_filter_by_run_type(self, monkeypatch):
        """Test: Filter nach run_type funktioniert."""
        mock_df = create_mock_experiments_df()
        # Patch im richtigen Modul
        import src.analytics.experiments_analysis as ea_module

        monkeypatch.setattr(ea_module, "load_experiments_df", lambda: mock_df)

        df = load_experiments_df_filtered(run_types=["backtest"])

        assert len(df) == 3
        assert all(df["run_type"] == "backtest")

    def test_filter_by_strategy(self, monkeypatch):
        """Test: Filter nach strategy_key funktioniert."""
        mock_df = create_mock_experiments_df()
        import src.analytics.experiments_analysis as ea_module

        monkeypatch.setattr(ea_module, "load_experiments_df", lambda: mock_df)

        df = load_experiments_df_filtered(strategy_keys=["ma_crossover"])

        assert len(df) == 2
        assert all(df["strategy_key"] == "ma_crossover")

    def test_filter_by_tag(self, monkeypatch):
        """Test: Filter nach Tag funktioniert."""
        mock_df = create_mock_experiments_df()
        import src.analytics.experiments_analysis as ea_module

        monkeypatch.setattr(ea_module, "load_experiments_df", lambda: mock_df)

        df = load_experiments_df_filtered(tags=["test"])

        assert len(df) == 2

    def test_filter_combined(self, monkeypatch):
        """Test: Kombinierte Filter funktionieren."""
        mock_df = create_mock_experiments_df()
        import src.analytics.experiments_analysis as ea_module

        monkeypatch.setattr(ea_module, "load_experiments_df", lambda: mock_df)

        df = load_experiments_df_filtered(
            run_types=["backtest"],
            strategy_keys=["ma_crossover"],
        )

        assert len(df) == 2


class TestFilterFunctions:
    """Tests für filter_backtest_runs und filter_portfolio_backtest_runs."""

    def test_filter_backtest_runs(self):
        """Test: filter_backtest_runs filtert korrekt."""
        mock_df = create_mock_experiments_df()
        filtered = filter_backtest_runs(mock_df)

        assert len(filtered) == 3
        assert all(filtered["run_type"] == "backtest")

    def test_filter_portfolio_backtest_runs(self):
        """Test: filter_portfolio_backtest_runs filtert korrekt."""
        mock_df = create_mock_experiments_df()
        filtered = filter_portfolio_backtest_runs(mock_df)

        assert len(filtered) == 2
        assert all(filtered["run_type"] == "portfolio_backtest")


class TestSummarizeStrategies:
    """Tests für summarize_strategies()."""

    def test_summarize_strategies_basic(self, monkeypatch):
        """Test: summarize_strategies aggregiert korrekt."""
        mock_df = create_mock_experiments_df()
        import src.analytics.experiments_analysis as ea_module

        monkeypatch.setattr(ea_module, "load_experiments_df", lambda: mock_df)

        df = load_experiments_df_filtered(run_types=["backtest"])
        summaries = summarize_strategies(df)

        assert len(summaries) == 2  # ma_crossover und rsi_reversion

        # Nach Sharpe sortiert - ma_crossover sollte erste sein
        assert summaries[0].strategy_key == "ma_crossover"
        assert summaries[0].run_count == 2
        assert summaries[0].avg_total_return == pytest.approx(0.125, rel=0.01)  # (0.10 + 0.15) / 2
        assert summaries[0].avg_sharpe == pytest.approx(1.35, rel=0.01)  # (1.2 + 1.5) / 2

    def test_summarize_strategies_best_worst_run(self, monkeypatch):
        """Test: Best/Worst Run IDs werden korrekt ermittelt."""
        mock_df = create_mock_experiments_df()
        import src.analytics.experiments_analysis as ea_module

        monkeypatch.setattr(ea_module, "load_experiments_df", lambda: mock_df)

        df = load_experiments_df_filtered(run_types=["backtest"])
        summaries = summarize_strategies(df)

        ma_summary = next(s for s in summaries if s.strategy_key == "ma_crossover")

        # Best Run ist run-002 (höchster Return)
        assert ma_summary.best_run_id == "run-002"
        # Worst Run ist run-001 (niedrigster Return)
        assert ma_summary.worst_run_id == "run-001"

    def test_summarize_strategies_empty(self):
        """Test: Leeres DataFrame gibt leere Liste zurück."""
        empty_df = pd.DataFrame()
        summaries = summarize_strategies(empty_df)

        assert summaries == []


class TestSummarizePortfolios:
    """Tests für summarize_portfolios()."""

    def test_summarize_portfolios_basic(self, monkeypatch):
        """Test: summarize_portfolios aggregiert korrekt."""
        mock_df = create_mock_experiments_df()
        import src.analytics.experiments_analysis as ea_module

        monkeypatch.setattr(ea_module, "load_experiments_df", lambda: mock_df)

        df = load_experiments_df_filtered(run_types=["portfolio_backtest"])
        summaries = summarize_portfolios(df)

        assert len(summaries) == 1  # core_portfolio
        assert summaries[0].portfolio_name == "core_portfolio"
        assert summaries[0].run_count == 2
        assert summaries[0].avg_total_return == pytest.approx(0.10, rel=0.01)  # (0.12 + 0.08) / 2


class TestTopRunsByMetric:
    """Tests für top_runs_by_metric()."""

    def test_top_runs_by_sharpe(self):
        """Test: Top-Runs nach Sharpe."""
        mock_df = create_mock_experiments_df()
        top_df = top_runs_by_metric(mock_df, metric="sharpe", n=3, ascending=False)

        assert len(top_df) == 3
        # Höchster Sharpe sollte erste Zeile sein
        assert top_df.iloc[0]["sharpe"] >= top_df.iloc[1]["sharpe"]

    def test_top_runs_by_return(self):
        """Test: Top-Runs nach Return."""
        mock_df = create_mock_experiments_df()
        top_df = top_runs_by_metric(mock_df, metric="total_return", n=2, ascending=False)

        assert len(top_df) == 2
        # Höchster Return sollte run-002 sein (0.15)
        assert top_df.iloc[0]["run_id"] == "run-002"

    def test_top_runs_ascending(self):
        """Test: Top-Runs aufsteigend (für max_drawdown)."""
        mock_df = create_mock_experiments_df()
        top_df = top_runs_by_metric(mock_df, metric="max_drawdown", n=3, ascending=True)

        assert len(top_df) == 3
        # Niedrigster (bester) Drawdown sollte erste Zeile sein
        assert top_df.iloc[0]["max_drawdown"] <= top_df.iloc[1]["max_drawdown"]


class TestCompareStrategies:
    """Tests für compare_strategies()."""

    def test_compare_two_strategies(self):
        """Test: Zwei Strategien vergleichen."""
        mock_df = create_mock_experiments_df()
        comparison_df = compare_strategies(
            mock_df,
            strategies=["ma_crossover", "rsi_reversion"],
        )

        assert len(comparison_df) == 2
        assert "strategy_key" in comparison_df.columns
        assert "run_count" in comparison_df.columns
        assert "avg_total_return" in comparison_df.columns


class TestMarkdownReports:
    """Tests für Markdown-Report-Generierung."""

    def test_write_markdown_report(self, tmp_path):
        """Test: Markdown-Report wird geschrieben."""
        summaries = [
            StrategySummary(
                strategy_key="ma_crossover",
                run_count=10,
                avg_total_return=0.10,
                avg_sharpe=1.2,
                avg_max_drawdown=-0.08,
                best_run_id="run-001",
            ),
        ]

        report_path = tmp_path / "test_report.md"
        write_markdown_report(summaries, report_path, title="Test Report")

        assert report_path.exists()
        content = report_path.read_text()
        assert "Test Report" in content
        assert "ma_crossover" in content
        assert "10" in content  # run_count

    def test_write_portfolio_markdown_report(self, tmp_path):
        """Test: Portfolio-Markdown-Report wird geschrieben."""
        summaries = [
            PortfolioSummary(
                portfolio_name="core_portfolio",
                run_count=5,
                avg_total_return=0.12,
                avg_sharpe=1.3,
                avg_max_drawdown=-0.07,
            ),
        ]

        report_path = tmp_path / "test_portfolio_report.md"
        write_portfolio_markdown_report(summaries, report_path)

        assert report_path.exists()
        content = report_path.read_text()
        assert "core_portfolio" in content

    def test_write_top_runs_markdown_report(self, tmp_path):
        """Test: Top-Runs-Markdown-Report wird geschrieben."""
        df = pd.DataFrame(
            [
                {
                    "run_id": "run-001",
                    "run_type": "backtest",
                    "strategy_key": "ma_crossover",
                    "total_return": 0.15,
                    "sharpe": 1.5,
                    "max_drawdown": -0.08,
                },
            ]
        )

        report_path = tmp_path / "test_top_runs.md"
        write_top_runs_markdown_report(df, report_path, metric="sharpe")

        assert report_path.exists()
        content = report_path.read_text()
        assert "run-001" in content
        assert "sharpe" in content.lower()


class TestCLIScript:
    """Tests für das CLI-Script."""

    def test_cli_help(self):
        """Test: CLI zeigt Hilfe an."""
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

        from analyze_experiments import parse_args

        # Sollte ohne Exception parsen
        args = parse_args(["--mode", "summary"])
        assert args.mode == "summary"

    def test_cli_top_runs_mode(self):
        """Test: CLI parst top-runs Modus."""
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

        from analyze_experiments import parse_args

        args = parse_args(["--mode", "top-runs", "--metric", "sharpe", "--limit", "10"])
        assert args.mode == "top-runs"
        assert args.metric == "sharpe"
        assert args.limit == 10
