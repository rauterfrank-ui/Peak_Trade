# tests/test_experiments_base.py
"""
Tests für src/experiments/base.py (Phase 29)
============================================

Testet ParamSweep, ExperimentConfig, SweepResultRow,
ExperimentResult und ExperimentRunner.
"""

import pandas as pd
import pytest

from src.experiments.base import (
    ExperimentConfig,
    ExperimentResult,
    ExperimentRunner,
    ParamSweep,
    SweepResultRow,
)

# ============================================================================
# PARAM SWEEP TESTS
# ============================================================================

class TestParamSweep:
    """Tests für ParamSweep."""

    def test_basic_creation(self):
        """Einfache Erstellung funktioniert."""
        sweep = ParamSweep("fast_period", [5, 10, 20])

        assert sweep.name == "fast_period"
        assert sweep.values == [5, 10, 20]
        assert sweep.description is None

    def test_with_description(self):
        """Erstellung mit Beschreibung."""
        sweep = ParamSweep(
            "threshold",
            [0.1, 0.2, 0.3],
            "Entry threshold for signals",
        )

        assert sweep.description == "Entry threshold for signals"

    def test_empty_name_raises(self):
        """Leerer Name wirft ValueError."""
        with pytest.raises(ValueError, match="name darf nicht leer"):
            ParamSweep("", [1, 2, 3])

    def test_empty_values_raises(self):
        """Leere Werte-Liste wirft ValueError."""
        with pytest.raises(ValueError, match="mindestens einen Wert"):
            ParamSweep("param", [])

    def test_from_range(self):
        """from_range() generiert korrekte Werte."""
        sweep = ParamSweep.from_range("period", 5, 25, 5)

        assert sweep.name == "period"
        assert sweep.values == [5, 10, 15, 20, 25]

    def test_from_range_float(self):
        """from_range() mit Float-Werten."""
        sweep = ParamSweep.from_range("threshold", 0.1, 0.5, 0.1)

        assert sweep.name == "threshold"
        assert len(sweep.values) == 5
        assert abs(sweep.values[0] - 0.1) < 0.01

    def test_from_logspace(self):
        """from_logspace() generiert logarithmisch verteilte Werte."""
        sweep = ParamSweep.from_logspace("window", 10, 1000, 4)

        assert sweep.name == "window"
        assert len(sweep.values) == 4
        assert sweep.values[0] == 10
        assert sweep.values[-1] == 1000

    def test_to_dict(self):
        """to_dict() gibt korrektes Dictionary zurück."""
        sweep = ParamSweep("period", [5, 10, 20], "Test")
        d = sweep.to_dict()

        assert d["name"] == "period"
        assert d["values"] == [5, 10, 20]
        assert d["description"] == "Test"
        assert d["num_values"] == 3


# ============================================================================
# EXPERIMENT CONFIG TESTS
# ============================================================================

class TestExperimentConfig:
    """Tests für ExperimentConfig."""

    def test_basic_creation(self):
        """Einfache Erstellung funktioniert."""
        config = ExperimentConfig(
            name="Test Experiment",
            strategy_name="ma_crossover",
        )

        assert config.name == "Test Experiment"
        assert config.strategy_name == "ma_crossover"
        assert config.symbols == ["BTC/EUR"]
        assert config.timeframe == "1h"

    def test_with_param_sweeps(self):
        """Erstellung mit ParamSweeps."""
        config = ExperimentConfig(
            name="Test",
            strategy_name="ma_crossover",
            param_sweeps=[
                ParamSweep("fast", [5, 10]),
                ParamSweep("slow", [50, 100]),
            ],
        )

        assert len(config.param_sweeps) == 2
        assert config.num_combinations == 4  # 2 * 2 * 1 symbol

    def test_num_combinations_multiple_symbols(self):
        """num_combinations berücksichtigt Symbole."""
        config = ExperimentConfig(
            name="Test",
            strategy_name="ma_crossover",
            param_sweeps=[
                ParamSweep("fast", [5, 10]),
                ParamSweep("slow", [50, 100]),
            ],
            symbols=["BTC/EUR", "ETH/EUR"],
        )

        assert config.num_combinations == 8  # 2 * 2 * 2 symbols

    def test_generate_param_combinations(self):
        """generate_param_combinations() generiert kartesisches Produkt."""
        config = ExperimentConfig(
            name="Test",
            strategy_name="ma_crossover",
            param_sweeps=[
                ParamSweep("fast", [5, 10]),
                ParamSweep("slow", [50, 100]),
            ],
        )

        combos = config.generate_param_combinations()

        assert len(combos) == 4
        assert {"fast": 5, "slow": 50} in combos
        assert {"fast": 5, "slow": 100} in combos
        assert {"fast": 10, "slow": 50} in combos
        assert {"fast": 10, "slow": 100} in combos

    def test_generate_combinations_with_base_params(self):
        """base_params werden in Kombinationen gemerged."""
        config = ExperimentConfig(
            name="Test",
            strategy_name="ma_crossover",
            param_sweeps=[ParamSweep("fast", [5, 10])],
            base_params={"ma_type": "ema"},
        )

        combos = config.generate_param_combinations()

        assert all("ma_type" in c for c in combos)
        assert all(c["ma_type"] == "ema" for c in combos)

    def test_empty_sweeps_returns_empty_dict(self):
        """Leere Sweeps geben ein leeres Dict zurück."""
        config = ExperimentConfig(
            name="Test",
            strategy_name="ma_crossover",
        )

        combos = config.generate_param_combinations()

        assert combos == [{}]

    def test_get_experiment_id(self):
        """get_experiment_id() generiert konsistente ID."""
        config = ExperimentConfig(
            name="Test",
            strategy_name="ma_crossover",
        )

        id1 = config.get_experiment_id()
        id2 = config.get_experiment_id()

        assert id1 == id2
        assert len(id1) == 12  # MD5 hash truncated

    def test_to_dict(self):
        """to_dict() gibt alle Felder zurück."""
        config = ExperimentConfig(
            name="Test",
            strategy_name="ma_crossover",
            param_sweeps=[ParamSweep("fast", [5, 10])],
        )

        d = config.to_dict()

        assert d["name"] == "Test"
        assert d["strategy_name"] == "ma_crossover"
        assert "param_sweeps" in d
        assert "num_combinations" in d


# ============================================================================
# SWEEP RESULT ROW TESTS
# ============================================================================

class TestSweepResultRow:
    """Tests für SweepResultRow."""

    def test_basic_creation(self):
        """Einfache Erstellung funktioniert."""
        result = SweepResultRow(
            experiment_id="abc123",
            run_id="abc123_001",
            strategy_name="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1h",
            params={"fast": 10, "slow": 50},
            metrics={"total_return": 0.15},
        )

        assert result.experiment_id == "abc123"
        assert result.success is True
        assert result.params["fast"] == 10

    def test_failed_result(self):
        """Fehlgeschlagener Run."""
        result = SweepResultRow(
            experiment_id="abc123",
            run_id="abc123_002",
            strategy_name="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1h",
            params={},
            metrics={},
            success=False,
            error_message="Test error",
        )

        assert result.success is False
        assert result.error_message == "Test error"

    def test_to_flat_dict(self):
        """to_flat_dict() flacht params und metrics."""
        result = SweepResultRow(
            experiment_id="abc123",
            run_id="abc123_001",
            strategy_name="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1h",
            params={"fast": 10, "slow": 50},
            metrics={"total_return": 0.15, "sharpe_ratio": 1.2},
        )

        flat = result.to_flat_dict()

        assert "param_fast" in flat
        assert "param_slow" in flat
        assert "metric_total_return" in flat
        assert "metric_sharpe_ratio" in flat
        assert flat["param_fast"] == 10
        assert flat["metric_total_return"] == 0.15

    def test_to_dict(self):
        """to_dict() gibt nested Dict zurück."""
        result = SweepResultRow(
            experiment_id="abc123",
            run_id="abc123_001",
            strategy_name="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1h",
            params={"fast": 10},
            metrics={"sharpe_ratio": 1.0},
        )

        d = result.to_dict()

        assert d["params"] == {"fast": 10}
        assert d["metrics"] == {"sharpe_ratio": 1.0}


# ============================================================================
# EXPERIMENT RESULT TESTS
# ============================================================================

class TestExperimentResult:
    """Tests für ExperimentResult."""

    @pytest.fixture
    def sample_config(self) -> ExperimentConfig:
        """Sample ExperimentConfig."""
        return ExperimentConfig(
            name="Test",
            strategy_name="ma_crossover",
            param_sweeps=[ParamSweep("fast", [5, 10])],
        )

    @pytest.fixture
    def sample_results(self) -> list[SweepResultRow]:
        """Sample SweepResultRows."""
        return [
            SweepResultRow(
                experiment_id="abc123",
                run_id="abc123_001",
                strategy_name="ma_crossover",
                symbol="BTC/EUR",
                timeframe="1h",
                params={"fast": 5},
                metrics={"total_return": 0.10, "sharpe_ratio": 0.8},
            ),
            SweepResultRow(
                experiment_id="abc123",
                run_id="abc123_002",
                strategy_name="ma_crossover",
                symbol="BTC/EUR",
                timeframe="1h",
                params={"fast": 10},
                metrics={"total_return": 0.20, "sharpe_ratio": 1.5},
            ),
            SweepResultRow(
                experiment_id="abc123",
                run_id="abc123_003",
                strategy_name="ma_crossover",
                symbol="BTC/EUR",
                timeframe="1h",
                params={"fast": 15},
                metrics={},
                success=False,
                error_message="Test error",
            ),
        ]

    def test_basic_creation(self, sample_config, sample_results):
        """Einfache Erstellung funktioniert."""
        result = ExperimentResult(
            experiment_id="abc123",
            config=sample_config,
            results=sample_results,
        )

        assert result.experiment_id == "abc123"
        assert result.num_runs == 3

    def test_success_metrics(self, sample_config, sample_results):
        """Erfolgs-Metriken werden korrekt berechnet."""
        result = ExperimentResult(
            experiment_id="abc123",
            config=sample_config,
            results=sample_results,
        )

        assert result.num_successful == 2
        assert result.num_failed == 1
        assert abs(result.success_rate - 2/3) < 0.01

    def test_to_dataframe(self, sample_config, sample_results):
        """to_dataframe() gibt korrekten DataFrame."""
        result = ExperimentResult(
            experiment_id="abc123",
            config=sample_config,
            results=sample_results,
        )

        df = result.to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "param_fast" in df.columns
        assert "metric_total_return" in df.columns

    def test_get_best_by_metric(self, sample_config, sample_results):
        """get_best_by_metric() gibt Top-Ergebnisse."""
        result = ExperimentResult(
            experiment_id="abc123",
            config=sample_config,
            results=sample_results,
        )

        best = result.get_best_by_metric("sharpe_ratio", top_n=1)

        assert len(best) == 1
        assert best[0].params["fast"] == 10  # Höchste Sharpe

    def test_get_best_ascending(self, sample_config, sample_results):
        """get_best_by_metric() mit ascending=True."""
        result = ExperimentResult(
            experiment_id="abc123",
            config=sample_config,
            results=sample_results,
        )

        best = result.get_best_by_metric("total_return", ascending=True, top_n=1)

        assert len(best) == 1
        assert best[0].params["fast"] == 5  # Niedrigster Return

    def test_get_summary_stats(self, sample_config, sample_results):
        """get_summary_stats() berechnet Statistiken."""
        result = ExperimentResult(
            experiment_id="abc123",
            config=sample_config,
            results=sample_results,
        )

        summary = result.get_summary_stats()

        assert "num_runs" in summary
        assert "success_rate" in summary
        assert "sharpe_ratio_mean" in summary
        assert "total_return_max" in summary


# ============================================================================
# EXPERIMENT RUNNER TESTS
# ============================================================================

class TestExperimentRunner:
    """Tests für ExperimentRunner."""

    def test_basic_creation(self):
        """Einfache Erstellung funktioniert."""
        runner = ExperimentRunner()

        assert runner.backtest_fn is not None

    def test_custom_backtest_fn(self):
        """Custom backtest_fn wird verwendet."""
        def custom_fn(*args, **kwargs):
            return {"total_return": 0.5, "sharpe_ratio": 2.0}

        runner = ExperimentRunner(backtest_fn=custom_fn)

        assert runner.backtest_fn == custom_fn

    def test_dry_run(self):
        """dry_run generiert keine Ergebnisse."""
        runner = ExperimentRunner()
        config = ExperimentConfig(
            name="Test",
            strategy_name="ma_crossover",
            param_sweeps=[ParamSweep("fast", [5, 10])],
            save_results=False,
        )

        result = runner.run(config, dry_run=True)

        assert result.num_runs == 0
        assert result.results == []

    def test_run_with_mock_backtest(self):
        """Run mit Mock-Backtest funktioniert."""
        call_count = 0

        def mock_backtest(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return {
                "total_return": 0.1 * call_count,
                "sharpe_ratio": 1.0,
                "max_drawdown": -0.05,
            }

        runner = ExperimentRunner(backtest_fn=mock_backtest)
        config = ExperimentConfig(
            name="Test",
            strategy_name="ma_crossover",
            param_sweeps=[ParamSweep("fast", [5, 10])],
            save_results=False,
        )

        result = runner.run(config)

        assert result.num_runs == 2
        assert result.num_successful == 2
        assert call_count == 2

    def test_run_handles_errors(self):
        """Run fängt Fehler einzelner Backtests."""
        call_count = 0

        def failing_backtest(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Test error")
            return {"total_return": 0.1}

        runner = ExperimentRunner(backtest_fn=failing_backtest)
        config = ExperimentConfig(
            name="Test",
            strategy_name="ma_crossover",
            param_sweeps=[ParamSweep("fast", [5, 10])],
            save_results=False,
        )

        result = runner.run(config)

        assert result.num_runs == 2
        assert result.num_successful == 1
        assert result.num_failed == 1

    def test_progress_callback(self):
        """Progress callback wird aufgerufen."""
        progress_calls = []

        def progress_cb(current, total, msg):
            progress_calls.append((current, total))

        def mock_backtest(*args, **kwargs):
            return {"total_return": 0.1}

        runner = ExperimentRunner(
            backtest_fn=mock_backtest,
            progress_callback=progress_cb,
        )
        config = ExperimentConfig(
            name="Test",
            strategy_name="ma_crossover",
            param_sweeps=[ParamSweep("fast", [5, 10, 15])],
            save_results=False,
        )

        runner.run(config)

        assert len(progress_calls) == 3
        assert progress_calls[-1] == (3, 3)

    def test_multiple_symbols(self):
        """Run mit mehreren Symbolen."""
        calls = []

        def mock_backtest(strategy_name, params, symbol, *args, **kwargs):
            calls.append(symbol)
            return {"total_return": 0.1}

        runner = ExperimentRunner(backtest_fn=mock_backtest)
        config = ExperimentConfig(
            name="Test",
            strategy_name="ma_crossover",
            param_sweeps=[ParamSweep("fast", [5, 10])],
            symbols=["BTC/EUR", "ETH/EUR"],
            save_results=False,
        )

        result = runner.run(config)

        assert result.num_runs == 4  # 2 params * 2 symbols
        assert "BTC/EUR" in calls
        assert "ETH/EUR" in calls


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestExperimentRunnerIntegration:
    """Integrationstests für ExperimentRunner."""

    def test_full_workflow(self):
        """Kompletter Workflow von Config bis Result."""
        # Setup
        def mock_backtest(strategy_name, params, symbol, timeframe, *args, **kwargs):
            # Simuliere dass größere Perioden besser sind
            fast = params.get("fast", 10)
            return {
                "total_return": fast * 0.01,
                "sharpe_ratio": fast * 0.1,
                "max_drawdown": -0.1,
                "win_rate": 0.55,
                "num_trades": 100,
                "profit_factor": 1.2,
            }

        runner = ExperimentRunner(backtest_fn=mock_backtest)

        config = ExperimentConfig(
            name="Integration Test",
            strategy_name="ma_crossover",
            param_sweeps=[
                ParamSweep("fast", [5, 10, 15, 20]),
            ],
            symbols=["BTC/EUR"],
            timeframe="1h",
            initial_capital=10000.0,
            save_results=False,
        )

        # Execute
        result = runner.run(config)

        # Verify
        assert result.num_runs == 4
        assert result.num_successful == 4
        assert result.success_rate == 1.0

        # Best result should be fast=20
        best = result.get_best_by_metric("sharpe_ratio", top_n=1)
        assert best[0].params["fast"] == 20

        # DataFrame should have all runs
        df = result.to_dataframe()
        assert len(df) == 4
        assert "param_fast" in df.columns
        assert "metric_sharpe_ratio" in df.columns

        # Summary stats
        summary = result.get_summary_stats()
        assert summary["num_runs"] == 4
        assert "sharpe_ratio_mean" in summary
