# tests/test_portfolio_builder_smoke.py
"""
Smoke-Tests für den Auto-Portfolio-Builder.

Testet:
- Dataclasses (PortfolioComponentCandidate, PortfolioCandidate)
- Selektionsfunktionen (select_top_sweep_components, select_top_market_scan_components)
- Builder-Funktion (build_portfolio_candidates_from_sweeps_and_scans)
- TOML-Export (write_portfolio_candidate_to_toml)
- CLI-Script Dry-Run
"""

from __future__ import annotations

import json
import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime


class TestDataclasses:
    """Tests für Dataclasses."""

    def test_portfolio_component_candidate_creation(self):
        """PortfolioComponentCandidate kann erstellt werden."""
        from src.analytics.portfolio_builder import PortfolioComponentCandidate

        comp = PortfolioComponentCandidate(
            symbol="BTC/EUR",
            strategy_key="ma_crossover",
            timeframe="1h",
            weight=0.33,
            source_run_id="abc-123",
            metric_score=1.5,
            params={"short_window": 10, "long_window": 50},
        )

        assert comp.symbol == "BTC/EUR"
        assert comp.strategy_key == "ma_crossover"
        assert comp.weight == 0.33
        assert comp.metric_score == 1.5
        assert comp.params["short_window"] == 10

    def test_portfolio_candidate_creation(self):
        """PortfolioCandidate kann erstellt werden."""
        from src.analytics.portfolio_builder import (
            PortfolioCandidate,
            PortfolioComponentCandidate,
        )

        comp1 = PortfolioComponentCandidate(
            symbol="BTC/EUR",
            strategy_key="ma_crossover",
            timeframe="1h",
            weight=0.5,
            source_run_id="abc-123",
            metric_score=1.5,
        )
        comp2 = PortfolioComponentCandidate(
            symbol="ETH/EUR",
            strategy_key="ma_crossover",
            timeframe="1h",
            weight=0.5,
            source_run_id="def-456",
            metric_score=1.2,
        )

        portfolio = PortfolioCandidate(
            name="test_portfolio",
            components=[comp1, comp2],
            allocation_method="equal",
            initial_equity=10000.0,
        )

        assert portfolio.name == "test_portfolio"
        assert len(portfolio.components) == 2
        assert portfolio.allocation_method == "equal"
        assert portfolio.initial_equity == 10000.0

    def test_portfolio_candidate_default_created_at(self):
        """PortfolioCandidate hat automatisches created_at."""
        from src.analytics.portfolio_builder import PortfolioCandidate

        portfolio = PortfolioCandidate(
            name="test",
            components=[],
        )

        assert portfolio.created_at is not None
        assert "T" in portfolio.created_at  # ISO format


class TestSelectTopSweepComponents:
    """Tests für select_top_sweep_components()."""

    def _create_sweep_df(self) -> pd.DataFrame:
        """Erstellt ein Beispiel-DataFrame mit Sweep-Daten."""
        return pd.DataFrame(
            {
                "run_id": ["run-1", "run-2", "run-3", "run-4"],
                "run_type": ["sweep", "sweep", "sweep", "backtest"],
                "strategy_key": ["ma_crossover", "ma_crossover", "rsi_reversion", "ma_crossover"],
                "symbol": ["BTC/EUR", "ETH/EUR", "BTC/EUR", "BTC/EUR"],
                "sharpe": [1.5, 1.2, 0.9, 2.0],
                "total_return": [0.15, 0.10, 0.08, 0.20],
                "max_drawdown": [-0.10, -0.08, -0.12, -0.05],
                "params_json": [
                    '{"short_window": 10, "long_window": 50}',
                    '{"short_window": 20, "long_window": 100}',
                    '{"rsi_period": 14}',
                    '{"short_window": 15}',
                ],
                "metadata_json": [
                    '{"timeframe": "1h", "tag": "test"}',
                    '{"timeframe": "1h", "tag": "test"}',
                    '{"timeframe": "4h", "tag": "other"}',
                    '{"timeframe": "1h"}',
                ],
            }
        )

    def test_select_from_sweeps(self):
        """Selektiert Komponenten aus Sweeps."""
        from src.analytics.portfolio_builder import select_top_sweep_components

        df = self._create_sweep_df()
        components = select_top_sweep_components(df, metric="sharpe", max_total=3)

        # Nur Sweeps werden selektiert (run-4 ist backtest)
        assert len(components) <= 3
        assert all(c.source_run_id != "run-4" for c in components)

    def test_select_sorts_by_metric(self):
        """Komponenten werden nach Metrik sortiert."""
        from src.analytics.portfolio_builder import select_top_sweep_components

        df = self._create_sweep_df()
        components = select_top_sweep_components(df, metric="sharpe", max_total=10)

        # Höchster Sharpe zuerst
        if len(components) >= 2:
            assert components[0].metric_score >= components[1].metric_score

    def test_select_with_min_sharpe(self):
        """min_sharpe Filter funktioniert."""
        from src.analytics.portfolio_builder import select_top_sweep_components

        df = self._create_sweep_df()
        components = select_top_sweep_components(df, metric="sharpe", min_sharpe=1.0, max_total=10)

        # Nur Komponenten mit Sharpe >= 1.0
        assert all(c.metric_score >= 1.0 for c in components)

    def test_select_with_tag_filter(self):
        """Tag-Filter funktioniert."""
        from src.analytics.portfolio_builder import select_top_sweep_components

        df = self._create_sweep_df()
        components = select_top_sweep_components(df, metric="sharpe", tag="test", max_total=10)

        # Nur 2 Runs haben tag="test"
        assert len(components) <= 2

    def test_select_extracts_params(self):
        """Parameter werden korrekt extrahiert."""
        from src.analytics.portfolio_builder import select_top_sweep_components

        df = self._create_sweep_df()
        components = select_top_sweep_components(df, metric="sharpe", max_total=1)

        assert len(components) == 1
        assert "short_window" in components[0].params or "rsi_period" in components[0].params


class TestSelectTopMarketScanComponents:
    """Tests für select_top_market_scan_components()."""

    def _create_scan_df(self) -> pd.DataFrame:
        """Erstellt ein Beispiel-DataFrame mit Market-Scan-Daten."""
        return pd.DataFrame(
            {
                "run_id": ["scan-1", "scan-2", "scan-3"],
                "run_type": ["market_scan", "market_scan", "market_scan"],
                "strategy_key": ["ma_crossover", "ma_crossover", "rsi_reversion"],
                "symbol": ["BTC/EUR", "ETH/EUR", "LTC/EUR"],
                "stats_json": [
                    '{"sharpe": 1.2, "total_return": 0.12}',
                    '{"sharpe": 0.9, "total_return": 0.08}',
                    '{"sharpe": 1.5, "total_return": 0.15}',
                ],
                "metadata_json": [
                    '{"mode": "backtest-lite", "timeframe": "1h"}',
                    '{"mode": "backtest-lite", "timeframe": "1h"}',
                    '{"mode": "backtest-lite", "timeframe": "4h"}',
                ],
            }
        )

    def test_select_from_scans(self):
        """Selektiert Komponenten aus Market-Scans."""
        from src.analytics.portfolio_builder import select_top_market_scan_components

        df = self._create_scan_df()
        components = select_top_market_scan_components(
            df, mode="backtest-lite", metric="sharpe", max_total=3
        )

        assert len(components) == 3

    def test_select_scans_sorts_by_metric(self):
        """Scan-Komponenten werden nach Metrik sortiert."""
        from src.analytics.portfolio_builder import select_top_market_scan_components

        df = self._create_scan_df()
        components = select_top_market_scan_components(
            df, mode="backtest-lite", metric="sharpe", max_total=10
        )

        if len(components) >= 2:
            # Höchster Sharpe zuerst (LTC/EUR hat 1.5)
            assert components[0].metric_score >= components[1].metric_score


class TestBuildPortfolioCandidates:
    """Tests für build_portfolio_candidates_from_sweeps_and_scans()."""

    def _create_sweep_df(self) -> pd.DataFrame:
        """Erstellt Sweep-DataFrame."""
        return pd.DataFrame(
            {
                "run_id": ["run-1", "run-2", "run-3"],
                "run_type": ["sweep", "sweep", "sweep"],
                "strategy_key": ["ma_crossover", "ma_crossover", "rsi_reversion"],
                "symbol": ["BTC/EUR", "ETH/EUR", "LTC/EUR"],
                "sharpe": [1.5, 1.2, 0.9],
                "total_return": [0.15, 0.10, 0.08],
                "params_json": [
                    '{"short_window": 10}',
                    '{"short_window": 20}',
                    '{"rsi_period": 14}',
                ],
                "metadata_json": [
                    '{"timeframe": "1h"}',
                    '{"timeframe": "1h"}',
                    '{"timeframe": "4h"}',
                ],
            }
        )

    def test_build_creates_portfolio(self):
        """Builder erzeugt mindestens ein Portfolio."""
        from src.analytics.portfolio_builder import build_portfolio_candidates_from_sweeps_and_scans

        df = self._create_sweep_df()
        candidates = build_portfolio_candidates_from_sweeps_and_scans(
            df_sweeps=df,
            metric="sharpe",
            max_components=3,
        )

        assert len(candidates) >= 1
        assert len(candidates[0].components) <= 3

    def test_build_with_min_sharpe(self):
        """Builder respektiert min_sharpe."""
        from src.analytics.portfolio_builder import build_portfolio_candidates_from_sweeps_and_scans

        df = self._create_sweep_df()
        candidates = build_portfolio_candidates_from_sweeps_and_scans(
            df_sweeps=df,
            metric="sharpe",
            min_sharpe=1.0,
            max_components=5,
        )

        if candidates:
            for comp in candidates[0].components:
                assert comp.metric_score >= 1.0

    def test_build_equal_weights(self):
        """Equal allocation erzeugt gleiche Gewichte."""
        from src.analytics.portfolio_builder import build_portfolio_candidates_from_sweeps_and_scans

        df = self._create_sweep_df()
        candidates = build_portfolio_candidates_from_sweeps_and_scans(
            df_sweeps=df,
            metric="sharpe",
            max_components=3,
            allocation_method="equal",
        )

        assert len(candidates) == 1
        portfolio = candidates[0]
        n = len(portfolio.components)

        expected_weight = 1.0 / n
        for comp in portfolio.components:
            assert abs(comp.weight - expected_weight) < 0.01

    def test_build_metric_weighted(self):
        """Metric-weighted allocation gewichtet nach Score."""
        from src.analytics.portfolio_builder import build_portfolio_candidates_from_sweeps_and_scans

        df = self._create_sweep_df()
        candidates = build_portfolio_candidates_from_sweeps_and_scans(
            df_sweeps=df,
            metric="sharpe",
            max_components=3,
            allocation_method="metric_weighted",
        )

        assert len(candidates) == 1
        portfolio = candidates[0]

        # Gewichte sollten zu 1.0 summieren
        total_weight = sum(c.weight for c in portfolio.components)
        assert abs(total_weight - 1.0) < 0.01

    def test_build_with_name_prefix(self):
        """Name-Prefix wird verwendet."""
        from src.analytics.portfolio_builder import build_portfolio_candidates_from_sweeps_and_scans

        df = self._create_sweep_df()
        candidates = build_portfolio_candidates_from_sweeps_and_scans(
            df_sweeps=df,
            name_prefix="my_custom",
            max_components=2,
        )

        assert candidates[0].name.startswith("my_custom_")


class TestBuildMultiplePortfolioCandidates:
    """Tests für build_multiple_portfolio_candidates()."""

    def _create_multi_strategy_df(self) -> pd.DataFrame:
        """Erstellt DataFrame mit mehreren Strategien."""
        return pd.DataFrame(
            {
                "run_id": [f"run-{i}" for i in range(6)],
                "run_type": ["sweep"] * 6,
                "strategy_key": [
                    "ma_crossover",
                    "ma_crossover",
                    "rsi_reversion",
                    "rsi_reversion",
                    "macd",
                    "macd",
                ],
                "symbol": ["BTC/EUR", "ETH/EUR", "BTC/EUR", "ETH/EUR", "BTC/EUR", "ETH/EUR"],
                "sharpe": [1.5, 1.2, 0.9, 1.1, 0.8, 0.7],
                "total_return": [0.15, 0.10, 0.08, 0.12, 0.05, 0.04],
                "params_json": ["{}"] * 6,
                "metadata_json": ['{"timeframe": "1h"}'] * 6,
            }
        )

    def test_builds_per_strategy_portfolios(self):
        """Erzeugt ein Portfolio pro Strategie."""
        from src.analytics.portfolio_builder import build_multiple_portfolio_candidates

        df = self._create_multi_strategy_df()
        candidates = build_multiple_portfolio_candidates(
            df=df,
            metric="sharpe",
            max_components_per_portfolio=3,
        )

        # Sollte 3 Portfolios erzeugen (eine pro Strategie)
        assert len(candidates) == 3

        # Jedes Portfolio hat nur Komponenten einer Strategie
        for portfolio in candidates:
            strategies = {c.strategy_key for c in portfolio.components}
            assert len(strategies) == 1


class TestWritePortfolioCandidateToToml:
    """Tests für write_portfolio_candidate_to_toml()."""

    def test_writes_toml_file(self, tmp_path: Path):
        """TOML-Datei wird geschrieben."""
        from src.analytics.portfolio_builder import (
            PortfolioCandidate,
            PortfolioComponentCandidate,
            write_portfolio_candidate_to_toml,
        )

        comp = PortfolioComponentCandidate(
            symbol="BTC/EUR",
            strategy_key="ma_crossover",
            timeframe="1h",
            weight=1.0,
            source_run_id="abc-123",
            metric_score=1.5,
            params={"short_window": 10},
        )
        portfolio = PortfolioCandidate(
            name="test_portfolio",
            components=[comp],
            initial_equity=10000.0,
        )

        toml_path = tmp_path / "test_portfolio.toml"
        write_portfolio_candidate_to_toml(portfolio, toml_path)

        assert toml_path.exists()

    def test_toml_contains_portfolio_section(self, tmp_path: Path):
        """TOML enthält [portfolio] Section."""
        from src.analytics.portfolio_builder import (
            PortfolioCandidate,
            PortfolioComponentCandidate,
            write_portfolio_candidate_to_toml,
        )

        comp = PortfolioComponentCandidate(
            symbol="BTC/EUR",
            strategy_key="ma_crossover",
            timeframe="1h",
            weight=0.5,
            source_run_id="abc",
            metric_score=1.0,
        )
        portfolio = PortfolioCandidate(
            name="test",
            components=[comp],
        )

        toml_path = tmp_path / "test.toml"
        write_portfolio_candidate_to_toml(portfolio, toml_path)

        content = toml_path.read_text()
        assert "[portfolio]" in content
        assert 'name = "test"' in content

    def test_toml_contains_symbols_list(self, tmp_path: Path):
        """TOML enthält symbols Liste."""
        from src.analytics.portfolio_builder import (
            PortfolioCandidate,
            PortfolioComponentCandidate,
            write_portfolio_candidate_to_toml,
        )

        comp1 = PortfolioComponentCandidate(
            symbol="BTC/EUR",
            strategy_key="ma_crossover",
            timeframe="1h",
            weight=0.5,
            source_run_id="abc",
            metric_score=1.0,
        )
        comp2 = PortfolioComponentCandidate(
            symbol="ETH/EUR",
            strategy_key="rsi_reversion",
            timeframe="1h",
            weight=0.5,
            source_run_id="def",
            metric_score=0.8,
        )
        portfolio = PortfolioCandidate(
            name="multi",
            components=[comp1, comp2],
        )

        toml_path = tmp_path / "multi.toml"
        write_portfolio_candidate_to_toml(portfolio, toml_path)

        content = toml_path.read_text()
        assert "BTC/EUR" in content
        assert "ETH/EUR" in content
        assert "symbols = [" in content

    def test_toml_contains_strategies_section(self, tmp_path: Path):
        """TOML enthält [portfolio.strategies] Section."""
        from src.analytics.portfolio_builder import (
            PortfolioCandidate,
            PortfolioComponentCandidate,
            write_portfolio_candidate_to_toml,
        )

        comp = PortfolioComponentCandidate(
            symbol="BTC/EUR",
            strategy_key="ma_crossover",
            timeframe="1h",
            weight=1.0,
            source_run_id="abc",
            metric_score=1.0,
        )
        portfolio = PortfolioCandidate(
            name="test",
            components=[comp],
        )

        toml_path = tmp_path / "test.toml"
        write_portfolio_candidate_to_toml(portfolio, toml_path)

        content = toml_path.read_text()
        assert "[portfolio.strategies]" in content
        assert '"BTC/EUR" = "ma_crossover"' in content


class TestFormatPortfolioCandidateSummary:
    """Tests für format_portfolio_candidate_summary()."""

    def test_format_returns_string(self):
        """Formatierung gibt String zurück."""
        from src.analytics.portfolio_builder import (
            PortfolioCandidate,
            PortfolioComponentCandidate,
            format_portfolio_candidate_summary,
        )

        comp = PortfolioComponentCandidate(
            symbol="BTC/EUR",
            strategy_key="ma_crossover",
            timeframe="1h",
            weight=1.0,
            source_run_id="abc",
            metric_score=1.5,
        )
        portfolio = PortfolioCandidate(
            name="test",
            components=[comp],
        )

        result = format_portfolio_candidate_summary(portfolio)

        assert isinstance(result, str)
        assert "test" in result
        assert "BTC/EUR" in result


class TestCLIScriptDryRun:
    """Tests für build_auto_portfolios.py Script im Dry-Run-Modus."""

    def test_dry_run_returns_valid_exit_code(self):
        """Dry-Run gibt einen gültigen Exit-Code zurück."""
        from scripts.build_auto_portfolios import main

        # Dry-Run sollte 0 (mit Daten) oder 1 (ohne Daten) zurückgeben
        exit_code = main(["--dry-run"])

        assert exit_code in (0, 1)

    def test_dry_run_shows_help(self):
        """Help-Flag funktioniert."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "scripts/build_auto_portfolios.py", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Auto-generate portfolio candidates" in result.stdout


class TestEmptyDataHandling:
    """Tests für leere Daten."""

    def test_select_from_empty_df(self):
        """Leeres DataFrame gibt leere Liste zurück."""
        from src.analytics.portfolio_builder import select_top_sweep_components

        df = pd.DataFrame()
        components = select_top_sweep_components(df, metric="sharpe")

        assert components == []

    def test_build_from_empty_df(self):
        """Builder mit leerem DataFrame gibt leere Liste."""
        from src.analytics.portfolio_builder import build_portfolio_candidates_from_sweeps_and_scans

        df = pd.DataFrame()
        candidates = build_portfolio_candidates_from_sweeps_and_scans(
            df_sweeps=df,
            max_components=5,
        )

        assert candidates == []
