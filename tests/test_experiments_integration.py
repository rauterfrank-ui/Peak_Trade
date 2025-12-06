# tests/test_experiments_integration.py
"""
Integration Tests für src/experiments/ (Phase 29)
=================================================

Testet das Zusammenspiel aller Experiment-Komponenten.
"""
import pytest
from datetime import datetime
from typing import Dict, Any
import os
import tempfile

import pandas as pd

from src.experiments import (
    ParamSweep,
    ExperimentConfig,
    ExperimentResult,
    ExperimentRunner,
    get_strategy_sweeps,
    get_regime_detector_sweeps,
    get_combined_regime_strategy_sweeps,
    STRATEGY_SWEEP_REGISTRY,
)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestExperimentWorkflow:
    """Tests für den kompletten Experiment-Workflow."""

    def create_mock_backtest(self, base_return: float = 0.1):
        """Erstellt eine Mock-Backtest-Funktion."""
        call_count = [0]

        def mock_backtest(
            strategy_name: str,
            params: Dict[str, Any],
            symbol: str,
            timeframe: str,
            start_date: str,
            end_date: str,
            initial_capital: float,
        ) -> Dict[str, float]:
            call_count[0] += 1
            # Variiere Returns basierend auf Parametern
            param_sum = sum(v for v in params.values() if isinstance(v, (int, float)))
            return {
                "total_return": base_return + (param_sum * 0.001),
                "sharpe_ratio": 1.0 + (param_sum * 0.01),
                "max_drawdown": -0.1,
                "win_rate": 0.55,
                "num_trades": 50,
                "profit_factor": 1.2,
            }

        return mock_backtest, call_count

    def test_simple_strategy_sweep(self):
        """Einfacher Strategy-Sweep funktioniert."""
        mock_fn, call_count = self.create_mock_backtest()

        config = ExperimentConfig(
            name="Simple Sweep Test",
            strategy_name="ma_crossover",
            param_sweeps=[
                ParamSweep("fast_period", [5, 10, 15]),
                ParamSweep("slow_period", [50, 100]),
            ],
            symbols=["BTC/EUR"],
            save_results=False,
        )

        runner = ExperimentRunner(backtest_fn=mock_fn)
        result = runner.run(config)

        assert result.num_runs == 6  # 3 * 2
        assert result.num_successful == 6
        assert call_count[0] == 6

    def test_multiple_symbols_sweep(self):
        """Sweep mit mehreren Symbolen."""
        mock_fn, call_count = self.create_mock_backtest()

        config = ExperimentConfig(
            name="Multi Symbol Test",
            strategy_name="ma_crossover",
            param_sweeps=[ParamSweep("fast_period", [5, 10])],
            symbols=["BTC/EUR", "ETH/EUR", "SOL/EUR"],
            save_results=False,
        )

        runner = ExperimentRunner(backtest_fn=mock_fn)
        result = runner.run(config)

        assert result.num_runs == 6  # 2 * 3 symbols
        assert call_count[0] == 6

    def test_with_base_params(self):
        """Sweep mit Base-Parameters."""
        params_received = []

        def capturing_backtest(strategy_name, params, *args, **kwargs):
            params_received.append(params.copy())
            return {"total_return": 0.1}

        config = ExperimentConfig(
            name="Base Params Test",
            strategy_name="ma_crossover",
            param_sweeps=[ParamSweep("fast_period", [5, 10])],
            base_params={"ma_type": "ema", "fixed_param": 42},
            save_results=False,
        )

        runner = ExperimentRunner(backtest_fn=capturing_backtest)
        runner.run(config)

        assert all("ma_type" in p for p in params_received)
        assert all(p["ma_type"] == "ema" for p in params_received)
        assert all(p["fixed_param"] == 42 for p in params_received)

    def test_results_dataframe_structure(self):
        """DataFrame hat korrekte Struktur."""
        mock_fn, _ = self.create_mock_backtest()

        config = ExperimentConfig(
            name="DataFrame Test",
            strategy_name="bollinger",
            param_sweeps=[
                ParamSweep("period", [10, 20]),
                ParamSweep("num_std", [2.0, 2.5]),
            ],
            save_results=False,
        )

        runner = ExperimentRunner(backtest_fn=mock_fn)
        result = runner.run(config)

        df = result.to_dataframe()

        # Prüfe Struktur
        assert len(df) == 4
        assert "param_period" in df.columns
        assert "param_num_std" in df.columns
        assert "metric_total_return" in df.columns
        assert "metric_sharpe_ratio" in df.columns
        assert "success" in df.columns
        assert "symbol" in df.columns

    def test_best_results_ranking(self):
        """Best-Results werden korrekt gerankt."""
        def predictable_backtest(strategy_name, params, *args, **kwargs):
            # Higher fast_period = higher return
            return {
                "total_return": params["fast_period"] * 0.01,
                "sharpe_ratio": params["fast_period"] * 0.1,
            }

        config = ExperimentConfig(
            name="Ranking Test",
            strategy_name="ma_crossover",
            param_sweeps=[ParamSweep("fast_period", [5, 10, 15, 20, 25])],
            save_results=False,
        )

        runner = ExperimentRunner(backtest_fn=predictable_backtest)
        result = runner.run(config)

        best = result.get_best_by_metric("sharpe_ratio", top_n=3)

        assert len(best) == 3
        assert best[0].params["fast_period"] == 25
        assert best[1].params["fast_period"] == 20
        assert best[2].params["fast_period"] == 15

    def test_error_handling(self):
        """Fehler werden korrekt behandelt."""
        fail_on = [2, 4]
        call_count = [0]

        def failing_backtest(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] in fail_on:
                raise ValueError(f"Simulated error on run {call_count[0]}")
            return {"total_return": 0.1}

        config = ExperimentConfig(
            name="Error Test",
            strategy_name="ma_crossover",
            param_sweeps=[ParamSweep("fast_period", [5, 10, 15, 20, 25])],
            save_results=False,
        )

        runner = ExperimentRunner(backtest_fn=failing_backtest)
        result = runner.run(config)

        assert result.num_runs == 5
        assert result.num_successful == 3
        assert result.num_failed == 2

        # Fehler-Details prüfen
        failed = [r for r in result.results if not r.success]
        assert len(failed) == 2
        assert all("Simulated error" in r.error_message for r in failed)


class TestStrategySpecificSweeps:
    """Tests für strategie-spezifische Sweeps."""

    @pytest.mark.parametrize("strategy_name", list(STRATEGY_SWEEP_REGISTRY.keys()))
    def test_strategy_sweeps_work(self, strategy_name):
        """Alle registrierten Strategien können gesweept werden."""
        def simple_backtest(*args, **kwargs):
            return {"total_return": 0.1, "sharpe_ratio": 1.0}

        sweeps = get_strategy_sweeps(strategy_name, "coarse")

        config = ExperimentConfig(
            name=f"{strategy_name} Test",
            strategy_name=strategy_name,
            param_sweeps=sweeps,
            save_results=False,
        )

        runner = ExperimentRunner(backtest_fn=simple_backtest)
        result = runner.run(config)

        assert result.num_runs > 0
        assert result.success_rate > 0


class TestRegimeSweepsIntegration:
    """Tests für Regime-Sweeps Integration."""

    def test_combined_sweeps_work(self):
        """Kombinierte Strategy+Regime Sweeps funktionieren."""
        def simple_backtest(*args, **kwargs):
            return {"total_return": 0.1, "sharpe_ratio": 1.0}

        sweeps = get_combined_regime_strategy_sweeps(
            "vol_breakout",
            "volatility_breakout",
            "coarse",
        )

        config = ExperimentConfig(
            name="Combined Sweep Test",
            strategy_name="vol_breakout",
            param_sweeps=sweeps[:4],  # Limit für schnelle Tests
            regime_config={"enabled": True},
            save_results=False,
        )

        runner = ExperimentRunner(backtest_fn=simple_backtest)
        result = runner.run(config)

        assert result.num_runs > 0


class TestOutputFormats:
    """Tests für Output-Formate."""

    def test_csv_export(self):
        """CSV-Export funktioniert."""
        def simple_backtest(*args, **kwargs):
            return {"total_return": 0.1}

        config = ExperimentConfig(
            name="CSV Test",
            strategy_name="ma_crossover",
            param_sweeps=[ParamSweep("fast", [5, 10])],
            save_results=False,
        )

        runner = ExperimentRunner(backtest_fn=simple_backtest)
        result = runner.run(config)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            result.save_csv(f.name)
            assert os.path.exists(f.name)

            df = pd.read_csv(f.name)
            assert len(df) == 2
            os.unlink(f.name)

    def test_summary_stats(self):
        """Summary-Stats werden korrekt berechnet."""
        returns = [0.05, 0.10, 0.15, 0.20, 0.25]
        call_count = [0]

        def varying_backtest(*args, **kwargs):
            r = returns[call_count[0] % len(returns)]
            call_count[0] += 1
            return {"total_return": r, "sharpe_ratio": r * 10}

        config = ExperimentConfig(
            name="Summary Test",
            strategy_name="ma_crossover",
            param_sweeps=[ParamSweep("fast", [5, 10, 15, 20, 25])],
            save_results=False,
        )

        runner = ExperimentRunner(backtest_fn=varying_backtest)
        result = runner.run(config)

        summary = result.get_summary_stats()

        assert "total_return_mean" in summary
        assert "total_return_min" in summary
        assert "total_return_max" in summary
        assert abs(summary["total_return_mean"] - 0.15) < 0.01


class TestProgressTracking:
    """Tests für Progress-Tracking."""

    def test_progress_callback_called(self):
        """Progress-Callback wird aufgerufen."""
        progress_calls = []

        def progress_cb(current, total, msg):
            progress_calls.append((current, total))

        def simple_backtest(*args, **kwargs):
            return {"total_return": 0.1}

        config = ExperimentConfig(
            name="Progress Test",
            strategy_name="ma_crossover",
            param_sweeps=[ParamSweep("fast", [5, 10, 15])],
            save_results=False,
        )

        runner = ExperimentRunner(
            backtest_fn=simple_backtest,
            progress_callback=progress_cb,
        )
        runner.run(config)

        assert len(progress_calls) == 3
        assert progress_calls[0] == (1, 3)
        assert progress_calls[-1] == (3, 3)


class TestExperimentIds:
    """Tests für Experiment-IDs."""

    def test_same_config_same_id(self):
        """Gleiche Config ergibt gleiche ID."""
        config1 = ExperimentConfig(
            name="Test",
            strategy_name="ma_crossover",
            param_sweeps=[ParamSweep("fast", [5, 10])],
        )
        config2 = ExperimentConfig(
            name="Test",
            strategy_name="ma_crossover",
            param_sweeps=[ParamSweep("fast", [5, 10])],
        )

        assert config1.get_experiment_id() == config2.get_experiment_id()

    def test_different_config_different_id(self):
        """Unterschiedliche Config ergibt unterschiedliche ID."""
        config1 = ExperimentConfig(
            name="Test",
            strategy_name="ma_crossover",
            param_sweeps=[ParamSweep("fast", [5, 10])],
        )
        config2 = ExperimentConfig(
            name="Test",
            strategy_name="bollinger",
            param_sweeps=[ParamSweep("period", [10, 20])],
        )

        assert config1.get_experiment_id() != config2.get_experiment_id()
