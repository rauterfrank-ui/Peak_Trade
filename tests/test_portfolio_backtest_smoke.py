"""
Peak_Trade Portfolio-Backtest Smoke Tests
==========================================
Smoke-Tests für die Portfolio-Backtest-Pipeline.

Diese Tests prüfen:
- log_portfolio_backtest_result() Funktion
- Portfolio-Equity-Aggregation
- RUN_TYPE_PORTFOLIO_BACKTEST in Registry
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.core.peak_config import PeakConfig
from src.core.experiments import (
    RUN_TYPE_PORTFOLIO_BACKTEST,
    log_portfolio_backtest_result,
    EXPERIMENTS_DIR,
    EXPERIMENTS_CSV,
)


def create_dummy_equity_curve(n_bars: int = 100, initial: float = 10000.0) -> pd.Series:
    """Erzeugt synthetische Equity-Curve für Tests."""
    np.random.seed(42)

    idx = pd.date_range("2025-01-01", periods=n_bars, freq="1h", tz="UTC")
    returns = np.random.normal(0.0002, 0.01, n_bars)
    equity = initial * np.exp(np.cumsum(returns))

    return pd.Series(equity, index=idx)


class TestPortfolioBacktestConstants:
    """Tests für Portfolio-Backtest-Konstanten."""

    def test_run_type_portfolio_backtest_exists(self):
        """Test: RUN_TYPE_PORTFOLIO_BACKTEST ist definiert."""
        assert RUN_TYPE_PORTFOLIO_BACKTEST == "portfolio_backtest"

    def test_run_type_in_valid_types(self):
        """Test: portfolio_backtest ist in VALID_RUN_TYPES."""
        from src.core.experiments import VALID_RUN_TYPES

        assert RUN_TYPE_PORTFOLIO_BACKTEST in VALID_RUN_TYPES


class TestLogPortfolioBacktestResult:
    """Tests für log_portfolio_backtest_result()."""

    def test_log_portfolio_backtest_returns_run_id(self, tmp_path, monkeypatch):
        """Test: log_portfolio_backtest_result gibt eine run_id zurück."""
        temp_experiments_dir = tmp_path / "experiments"
        temp_experiments_csv = temp_experiments_dir / "experiments.csv"
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_DIR", temp_experiments_dir)
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_CSV", temp_experiments_csv)

        equity_curve = create_dummy_equity_curve(100, 10000.0)
        component_runs = [
            {"symbol": "BTC/EUR", "strategy_key": "ma_crossover", "weight": 0.5},
            {"symbol": "ETH/EUR", "strategy_key": "rsi_reversion", "weight": 0.5},
        ]

        run_id = log_portfolio_backtest_result(
            portfolio_name="test_portfolio",
            equity_curve=equity_curve,
            component_runs=component_runs,
            tag="test-run",
        )

        assert isinstance(run_id, str)
        assert len(run_id) > 0

    def test_log_portfolio_backtest_writes_csv(self, tmp_path, monkeypatch):
        """Test: log_portfolio_backtest_result schreibt in CSV."""
        temp_experiments_dir = tmp_path / "experiments"
        temp_experiments_csv = temp_experiments_dir / "experiments.csv"
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_DIR", temp_experiments_dir)
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_CSV", temp_experiments_csv)

        equity_curve = create_dummy_equity_curve(100, 10000.0)
        component_runs = [
            {"symbol": "BTC/EUR", "strategy_key": "ma_crossover", "weight": 0.33},
            {"symbol": "ETH/EUR", "strategy_key": "rsi_reversion", "weight": 0.33},
            {"symbol": "LTC/EUR", "strategy_key": "breakout_donchian", "weight": 0.34},
        ]

        run_id = log_portfolio_backtest_result(
            portfolio_name="core_3-strat",
            equity_curve=equity_curve,
            component_runs=component_runs,
            allocation_method="equal",
        )

        # CSV sollte existieren
        assert temp_experiments_csv.exists()

        # CSV lesen und prüfen
        df = pd.read_csv(temp_experiments_csv)
        assert len(df) == 1
        assert df.iloc[0]["run_id"] == run_id
        assert df.iloc[0]["run_type"] == "portfolio_backtest"
        assert df.iloc[0]["portfolio_name"] == "core_3-strat"

    def test_log_portfolio_backtest_with_stats(self, tmp_path, monkeypatch):
        """Test: log_portfolio_backtest_result speichert Stats korrekt."""
        temp_experiments_dir = tmp_path / "experiments"
        temp_experiments_csv = temp_experiments_dir / "experiments.csv"
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_DIR", temp_experiments_dir)
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_CSV", temp_experiments_csv)

        equity_curve = create_dummy_equity_curve(100, 10000.0)
        component_runs = [
            {"symbol": "BTC/EUR", "strategy_key": "ma_crossover", "weight": 1.0},
        ]
        portfolio_stats = {
            "total_return": 0.12,
            "max_drawdown": -0.08,
            "sharpe": 1.25,
            "cagr": 0.10,
        }

        run_id = log_portfolio_backtest_result(
            portfolio_name="single_asset",
            equity_curve=equity_curve,
            component_runs=component_runs,
            portfolio_stats=portfolio_stats,
        )

        df = pd.read_csv(temp_experiments_csv)
        row = df.iloc[0]

        # Stats sollten in Top-Level-Feldern stehen
        assert abs(row["total_return"] - 0.12) < 0.001
        assert abs(row["max_drawdown"] - (-0.08)) < 0.001
        assert abs(row["sharpe"] - 1.25) < 0.001

    def test_log_portfolio_backtest_calculates_stats_from_equity(self, tmp_path, monkeypatch):
        """Test: log_portfolio_backtest_result berechnet Stats aus equity_curve."""
        temp_experiments_dir = tmp_path / "experiments"
        temp_experiments_csv = temp_experiments_dir / "experiments.csv"
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_DIR", temp_experiments_dir)
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_CSV", temp_experiments_csv)

        # Equity-Curve mit bekanntem Return
        idx = pd.date_range("2025-01-01", periods=10, freq="1h", tz="UTC")
        equity_curve = pd.Series(
            [
                10000.0,
                10100.0,
                10200.0,
                10300.0,
                10400.0,
                10500.0,
                10600.0,
                10700.0,
                10800.0,
                11000.0,
            ],
            index=idx,
        )

        component_runs = []

        run_id = log_portfolio_backtest_result(
            portfolio_name="calc_test",
            equity_curve=equity_curve,
            component_runs=component_runs,
            # Keine portfolio_stats übergeben -> werden berechnet
        )

        df = pd.read_csv(temp_experiments_csv)
        row = df.iloc[0]

        # Return sollte 10% sein (11000 / 10000 - 1)
        assert abs(row["total_return"] - 0.10) < 0.001


class TestPortfolioEquityAggregation:
    """Tests für Portfolio-Equity-Aggregation."""

    def test_aggregate_equal_weight_portfolios(self):
        """Test: Gleichgewichtete Equity-Curves summieren korrekt."""
        idx = pd.date_range("2025-01-01", periods=5, freq="1h", tz="UTC")

        # Zwei identische Curves mit verschiedenen Skalierungen
        eq1 = pd.Series([1000.0, 1010.0, 1020.0, 1030.0, 1040.0], index=idx)
        eq2 = pd.Series([1000.0, 990.0, 980.0, 970.0, 960.0], index=idx)

        # Gleichgewichtete Kombination
        weights = {"asset1": 0.5, "asset2": 0.5}
        combined = eq1 * weights["asset1"] + eq2 * weights["asset2"]

        # Bei 50/50 sollte es ausgeglichen sein
        assert combined.iloc[0] == 1000.0  # 500 + 500
        assert combined.iloc[-1] == 1000.0  # 520 + 480

    def test_portfolio_drawdown_calculation(self):
        """Test: Portfolio-Drawdown wird korrekt berechnet."""
        idx = pd.date_range("2025-01-01", periods=6, freq="1h", tz="UTC")
        equity = pd.Series([10000.0, 10500.0, 10200.0, 10800.0, 10400.0, 11000.0], index=idx)

        # Drawdown berechnen
        rolling_max = equity.expanding().max()
        drawdown = (equity - rolling_max) / rolling_max

        # Max Drawdown sollte bei Index 4 sein (10400 vs Peak 10800)
        expected_max_dd = (10400.0 - 10800.0) / 10800.0
        assert abs(drawdown.min() - expected_max_dd) < 0.0001


class TestPortfolioComponents:
    """Tests für Portfolio-Komponenten."""

    def test_component_runs_structure(self, tmp_path, monkeypatch):
        """Test: Component-Runs werden korrekt gespeichert."""
        import json

        temp_experiments_dir = tmp_path / "experiments"
        temp_experiments_csv = temp_experiments_dir / "experiments.csv"
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_DIR", temp_experiments_dir)
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_CSV", temp_experiments_csv)

        equity_curve = create_dummy_equity_curve(50, 10000.0)
        component_runs = [
            {
                "run_id": "abc-123",
                "symbol": "BTC/EUR",
                "strategy_key": "ma_crossover",
                "weight": 0.5,
                "total_return": 0.08,
            },
            {
                "run_id": "def-456",
                "symbol": "ETH/EUR",
                "strategy_key": "rsi_reversion",
                "weight": 0.5,
                "total_return": 0.04,
            },
        ]

        run_id = log_portfolio_backtest_result(
            portfolio_name="test_components",
            equity_curve=equity_curve,
            component_runs=component_runs,
        )

        df = pd.read_csv(temp_experiments_csv)
        row = df.iloc[0]

        # Metadata prüfen
        metadata = json.loads(row["metadata_json"])
        assert "components" in metadata
        assert len(metadata["components"]) == 2
        assert metadata["components"][0]["symbol"] == "BTC/EUR"
        assert metadata["components"][1]["symbol"] == "ETH/EUR"


class TestEndToEndPortfolioBacktest:
    """End-to-End Test für den Portfolio-Backtest-Flow."""

    def test_full_portfolio_backtest_flow(self, tmp_path, monkeypatch):
        """Test: Kompletter Portfolio-Backtest-Flow."""
        temp_experiments_dir = tmp_path / "experiments"
        temp_experiments_csv = temp_experiments_dir / "experiments.csv"
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_DIR", temp_experiments_dir)
        monkeypatch.setattr("src.core.experiments.EXPERIMENTS_CSV", temp_experiments_csv)

        # 1. Simuliere mehrere Asset-Backtests
        assets = ["BTC/EUR", "ETH/EUR", "LTC/EUR"]
        weights = {"BTC/EUR": 0.5, "ETH/EUR": 0.3, "LTC/EUR": 0.2}
        initial_capital = 10000.0

        # Dummy equity curves
        np.random.seed(42)
        idx = pd.date_range("2025-01-01", periods=100, freq="1h", tz="UTC")

        equity_curves = {}
        for asset in assets:
            returns = np.random.normal(0.0002, 0.01, 100)
            equity_curves[asset] = pd.Series(
                initial_capital * weights[asset] * np.exp(np.cumsum(returns)), index=idx
            )

        # 2. Portfolio-Equity aggregieren
        portfolio_equity = sum(equity_curves.values())

        # 3. Component-Runs vorbereiten
        component_runs = []
        for asset in assets:
            eq = equity_curves[asset]
            total_return = (eq.iloc[-1] / eq.iloc[0]) - 1.0
            component_runs.append(
                {
                    "symbol": asset,
                    "strategy_key": "ma_crossover",
                    "weight": weights[asset],
                    "total_return": total_return,
                }
            )

        # 4. Portfolio-Stats berechnen
        portfolio_stats = {
            "total_return": (portfolio_equity.iloc[-1] / portfolio_equity.iloc[0]) - 1.0,
        }

        # 5. In Registry loggen
        run_id = log_portfolio_backtest_result(
            portfolio_name="e2e_test_portfolio",
            equity_curve=portfolio_equity,
            component_runs=component_runs,
            portfolio_stats=portfolio_stats,
            tag="e2e-test",
            allocation_method="manual",
        )

        # 6. Prüfungen
        assert isinstance(run_id, str)
        assert temp_experiments_csv.exists()

        df = pd.read_csv(temp_experiments_csv)
        assert len(df) == 1
        assert df.iloc[0]["run_type"] == "portfolio_backtest"
        assert df.iloc[0]["portfolio_name"] == "e2e_test_portfolio"
