# tests/test_experiments_base.py
"""
Tests für src/experiments/base.py (Phase 29)
============================================

Testet ParamSweep, ExperimentConfig, SweepResultRow,
ExperimentResult und ExperimentRunner.
"""

import pytest
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pandas as pd

from src.experiments.base import (
    ParamSweep,
    ExperimentConfig,
    SweepResultRow,
    ExperimentResult,
    ExperimentRunner,
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
    def sample_results(self) -> List[SweepResultRow]:
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
        assert abs(result.success_rate - 2 / 3) < 0.01

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


# ============================================================================
# PHASE-41 QUIET MODE CONTRACT TESTS
# ============================================================================

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from src.experiments.base import (
    ExperimentRunOutputMode,
    apply_experiment_run_logging,
    logger as experiment_logger,
    restore_experiment_run_logging,
)


def _sample_experiment_result(config: ExperimentConfig) -> ExperimentResult:
    rows = [
        SweepResultRow(
            experiment_id=config.get_experiment_id(),
            run_id=f"{config.get_experiment_id()}_0001",
            strategy_name=config.strategy_name,
            symbol="BTC/EUR",
            timeframe="1h",
            params={"fast": 5},
            metrics={"total_return": 0.12, "sharpe_ratio": 1.1, "max_drawdown": -0.05},
        )
    ]
    return ExperimentResult(
        experiment_id=config.get_experiment_id(),
        config=config,
        results=rows,
        total_runtime_seconds=0.5,
    )


def _mock_strategy_sweep_run(monkeypatch, tmp_path, *, quiet: bool = False):
    import run_strategy_sweep as rss

    config = ExperimentConfig(
        name="mock_sweep",
        strategy_name="ma_crossover",
        param_sweeps=[ParamSweep("fast", [5])],
        save_results=True,
        output_dir=str(tmp_path / "reports" / "experiments"),
    )
    result = _sample_experiment_result(config)
    captured: dict[str, object] = {}

    class MockSweepConfig:
        name = "rsi_reversion_basic"
        strategy_name = "rsi_reversion"
        symbols = ["BTC/EUR"]
        timeframe = "1h"
        description = "mock"
        num_raw_combinations = 1
        tags: list[str] = []

        def generate_param_combinations(self):
            return [{"fast": 5}]

        def to_experiment_config(self, **kwargs):
            captured["exp_config_kwargs"] = kwargs
            return config

    class MockRunner:
        def __init__(self, **kwargs):
            captured["runner_kwargs"] = kwargs

        def run(self, exp_config):
            captured["exp_config"] = exp_config
            return result

        def run_parallel(self, exp_config):
            return self.run(exp_config)

    monkeypatch.setattr(rss, "get_predefined_sweep", lambda _name: MockSweepConfig())
    monkeypatch.setattr(rss, "ExperimentRunner", MockRunner)
    return rss, captured, result


def _mock_experiment_sweep_run(monkeypatch, tmp_path, *, quiet: bool = False):
    import run_experiment_sweep as res

    config = ExperimentConfig(
        name="MA_CROSSOVER Parameter Sweep",
        strategy_name="ma_crossover",
        param_sweeps=[ParamSweep("fast", [5])],
        save_results=True,
        output_dir=str(tmp_path / "reports" / "experiments"),
    )
    result = _sample_experiment_result(config)
    captured: dict[str, object] = {}

    class MockRunner:
        def __init__(self, **kwargs):
            captured["runner_kwargs"] = kwargs

        def run(self, exp_config):
            captured["exp_config"] = exp_config
            return result

        def run_parallel(self, exp_config):
            return self.run(exp_config)

    monkeypatch.setattr(res, "get_strategy_sweeps", lambda *_a, **_k: [ParamSweep("fast", [5])])
    monkeypatch.setattr(res, "ExperimentRunner", MockRunner)
    monkeypatch.setattr(res, "ExperimentConfig", lambda **kwargs: config)
    return res, captured, result


def test_run_strategy_sweep_quiet_flag_parsed() -> None:
    import run_strategy_sweep as rss

    args = rss.build_parser().parse_args(["--quiet", "--sweep-name", "rsi_reversion_basic"])
    assert args.quiet is True
    args_short = rss.build_parser().parse_args(["-q", "--sweep-name", "rsi_reversion_basic"])
    assert args_short.quiet is True


def test_run_experiment_sweep_quiet_flag_parsed() -> None:
    import run_experiment_sweep as res

    args = res.parse_args(["--quiet", "--strategy", "ma_crossover"])
    assert args.quiet is True
    args_short = res.parse_args(["-q", "--strategy", "ma_crossover"])
    assert args_short.quiet is True


def test_run_strategy_sweep_default_mode_preserves_pre_run_info(
    tmp_path, monkeypatch, capsys
) -> None:
    rss, _, _ = _mock_strategy_sweep_run(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)

    code = rss.main(["--sweep-name", "rsi_reversion_basic", "--no-save"])
    assert code == 0
    out = capsys.readouterr().out
    assert "Peak_Trade Strategy Sweep (Phase 41)" in out
    assert "Kombinationen:" in out


def test_run_strategy_sweep_quiet_mode_suppresses_pre_run_info(
    tmp_path, monkeypatch, capsys
) -> None:
    rss, _, _ = _mock_strategy_sweep_run(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)

    code = rss.main(["--quiet", "--sweep-name", "rsi_reversion_basic", "--no-save"])
    assert code == 0
    out = capsys.readouterr().out
    assert "Peak_Trade Strategy Sweep (Phase 41)" not in out
    assert "Kombinationen:" not in out


def test_run_strategy_sweep_quiet_mode_preserves_completion_output(
    tmp_path, monkeypatch, capsys
) -> None:
    rss, _, _ = _mock_strategy_sweep_run(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)

    code = rss.main(["--quiet", "--sweep-name", "rsi_reversion_basic", "--no-save"])
    assert code == 0
    out = capsys.readouterr().out
    assert "Ergebnisse" in out
    assert "Runs:" in out
    assert "Erfolgsrate:" in out


def test_run_experiment_sweep_default_mode_preserves_pre_run_info(
    tmp_path, monkeypatch, capsys
) -> None:
    res, _, _ = _mock_experiment_sweep_run(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)

    code = res.main(["--strategy", "ma_crossover", "--no-save"])
    assert code == 0
    out = capsys.readouterr().out
    assert "Peak_Trade Experiment Sweep" in out
    assert "Kombinationen:" in out


def test_run_experiment_sweep_quiet_mode_suppresses_pre_run_info(
    tmp_path, monkeypatch, capsys
) -> None:
    res, _, _ = _mock_experiment_sweep_run(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)

    code = res.main(["--quiet", "--strategy", "ma_crossover", "--no-save"])
    assert code == 0
    out = capsys.readouterr().out
    assert "Peak_Trade Experiment Sweep" not in out
    assert "Kombinationen:" not in out


def test_run_experiment_sweep_quiet_mode_preserves_completion_output(
    tmp_path, monkeypatch, capsys
) -> None:
    res, _, _ = _mock_experiment_sweep_run(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)

    code = res.main(["--quiet", "--strategy", "ma_crossover", "--no-save"])
    assert code == 0
    out = capsys.readouterr().out
    assert "Ergebnisse" in out
    assert "Runs:" in out
    assert "Erfolgsrate:" in out


def test_experiment_runner_quiet_mode_suppresses_high_frequency_logger_info(
    caplog,
) -> None:
    calls: list[tuple[int, int, str]] = []

    def progress_cb(current: int, total: int, message: str) -> None:
        calls.append((current, total, message))
        print(f"progress:{current}/{total}")

    runner = ExperimentRunner(
        backtest_fn=lambda *_a, **_k: {"total_return": 0.1, "sharpe_ratio": 1.0},
        progress_callback=progress_cb,
        quiet=True,
    )
    config = ExperimentConfig(
        name="quiet-runner",
        strategy_name="ma_crossover",
        param_sweeps=[ParamSweep("fast", [5, 10])],
        save_results=False,
    )

    with caplog.at_level(logging.INFO, logger=experiment_logger.name):
        result = runner.run(config)

    assert result.num_runs == 2
    assert calls == []
    assert not any("Starte Experiment" in r.message for r in caplog.records)


def test_experiment_runner_default_mode_emits_start_info(caplog) -> None:
    runner = ExperimentRunner(
        backtest_fn=lambda *_a, **_k: {"total_return": 0.1, "sharpe_ratio": 1.0},
        quiet=False,
    )
    config = ExperimentConfig(
        name="default-runner",
        strategy_name="ma_crossover",
        param_sweeps=[ParamSweep("fast", [5])],
        save_results=False,
    )

    with caplog.at_level(logging.INFO, logger=experiment_logger.name):
        runner.run(config)

    assert any("Starte Experiment" in r.message for r in caplog.records)


def test_experiment_runner_quiet_mode_preserves_artifact_path_output(tmp_path, caplog) -> None:
    runner = ExperimentRunner(
        backtest_fn=lambda *_a, **_k: {"total_return": 0.1, "sharpe_ratio": 1.0},
        quiet=True,
    )
    config = ExperimentConfig(
        name="artifact-runner",
        strategy_name="ma_crossover",
        param_sweeps=[ParamSweep("fast", [5])],
        save_results=True,
        output_dir=str(tmp_path),
    )

    with caplog.at_level(logging.INFO, logger=experiment_logger.name):
        runner.run(config)

    summary_files = list(tmp_path.glob("*_summary.json"))
    assert summary_files


def test_experiment_runner_quiet_warning_visible(caplog) -> None:
    previous_module, previous_root = apply_experiment_run_logging(True)
    try:
        with caplog.at_level(logging.WARNING, logger=experiment_logger.name):
            experiment_logger.warning("phase41-quiet-warning-check")
    finally:
        restore_experiment_run_logging(previous_module, previous_root)

    assert any("phase41-quiet-warning-check" in r.message for r in caplog.records)


def test_experiment_runner_quiet_error_visible(caplog) -> None:
    previous_module, previous_root = apply_experiment_run_logging(True)
    try:
        with caplog.at_level(logging.ERROR, logger=experiment_logger.name):
            experiment_logger.error("phase41-quiet-error-check")
    finally:
        restore_experiment_run_logging(previous_module, previous_root)

    assert any("phase41-quiet-error-check" in r.message for r in caplog.records)


def test_run_strategy_sweep_quiet_mode_restores_logging_after_success() -> None:
    import run_strategy_sweep as rss

    baseline_module = experiment_logger.level
    baseline_root = logging.getLogger().level
    with patch.object(rss, "run_from_args", return_value=0):
        assert rss.main(["--quiet", "--list-sweeps"]) == 0
    assert experiment_logger.level == baseline_module
    assert logging.getLogger().level == baseline_root


def test_run_strategy_sweep_quiet_mode_restores_logging_after_exception() -> None:
    import run_strategy_sweep as rss

    baseline_module = experiment_logger.level
    baseline_root = logging.getLogger().level
    with patch.object(rss, "run_from_args", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError, match="boom"):
            rss.main(["--quiet", "--list-sweeps"])
    assert experiment_logger.level == baseline_module
    assert logging.getLogger().level == baseline_root


def test_run_experiment_sweep_quiet_mode_restores_logging_after_success() -> None:
    import run_experiment_sweep as res

    baseline_module = experiment_logger.level
    baseline_root = logging.getLogger().level
    with patch.object(res, "run_from_args", return_value=0):
        assert res.main(["--quiet", "--list-strategies"]) == 0
    assert experiment_logger.level == baseline_module
    assert logging.getLogger().level == baseline_root


def test_run_experiment_sweep_quiet_mode_restores_logging_after_exception() -> None:
    import run_experiment_sweep as res

    baseline_module = experiment_logger.level
    baseline_root = logging.getLogger().level
    with patch.object(res, "run_from_args", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError, match="boom"):
            res.main(["--quiet", "--list-strategies"])
    assert experiment_logger.level == baseline_module
    assert logging.getLogger().level == baseline_root


def test_phase41_quiet_multiple_calls_do_not_duplicate_handlers() -> None:
    import run_strategy_sweep as rss
    import run_experiment_sweep as res

    baseline_handlers = len(experiment_logger.handlers)
    with patch.object(rss, "run_from_args", return_value=0):
        rss.main(["--quiet", "--list-sweeps"])
        rss.main(["--quiet", "--list-sweeps"])
    with patch.object(res, "run_from_args", return_value=0):
        res.main(["--quiet", "--list-strategies"])
    assert len(experiment_logger.handlers) == baseline_handlers


def test_run_strategy_sweep_quiet_binds_same_runner_contract(tmp_path, monkeypatch) -> None:
    rss, captured_default, _ = _mock_strategy_sweep_run(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)
    rss.main(["--sweep-name", "rsi_reversion_basic", "--no-save"])

    rss2, captured_quiet, _ = _mock_strategy_sweep_run(monkeypatch, tmp_path)
    rss2.main(["--quiet", "--sweep-name", "rsi_reversion_basic", "--no-save"])

    default_kwargs = captured_default["runner_kwargs"]
    quiet_kwargs = captured_quiet["runner_kwargs"]
    assert default_kwargs["quiet"] is False
    assert quiet_kwargs["quiet"] is True
    assert captured_default["exp_config"] == captured_quiet["exp_config"]


def test_run_experiment_sweep_quiet_binds_same_runner_contract(tmp_path, monkeypatch) -> None:
    res, captured_default, _ = _mock_experiment_sweep_run(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)
    res.main(["--strategy", "ma_crossover", "--no-save"])

    res2, captured_quiet, _ = _mock_experiment_sweep_run(monkeypatch, tmp_path)
    res2.main(["--quiet", "--strategy", "ma_crossover", "--no-save"])

    default_kwargs = captured_default["runner_kwargs"]
    quiet_kwargs = captured_quiet["runner_kwargs"]
    assert default_kwargs["quiet"] is False
    assert quiet_kwargs["quiet"] is True


def test_run_strategy_sweep_quiet_propagates_runner_exception(
    tmp_path, monkeypatch, caplog
) -> None:
    import run_strategy_sweep as rss

    class MockSweepConfig:
        name = "rsi_reversion_basic"
        strategy_name = "rsi_reversion"
        symbols = ["BTC/EUR"]
        timeframe = "1h"
        description = None
        num_raw_combinations = 1
        tags: list[str] = []

        def generate_param_combinations(self):
            return [{"fast": 5}]

        def to_experiment_config(self, **kwargs):
            return ExperimentConfig(
                name="mock",
                strategy_name="rsi_reversion",
                param_sweeps=[ParamSweep("fast", [5])],
                save_results=False,
            )

    class FailingRunner:
        def __init__(self, **_kwargs):
            pass

        def run(self, _config):
            raise RuntimeError("simulated strategy sweep failure")

    monkeypatch.setattr(rss, "get_predefined_sweep", lambda _name: MockSweepConfig())
    monkeypatch.setattr(rss, "ExperimentRunner", FailingRunner)
    monkeypatch.chdir(tmp_path)

    with caplog.at_level(logging.ERROR):
        code = rss.main(["--quiet", "--sweep-name", "rsi_reversion_basic"])
    assert code == 1
    assert any("Sweep fehlgeschlagen" in r.message for r in caplog.records)


def test_experiment_run_output_mode_info_suppressed_when_quiet(capsys) -> None:
    quiet = ExperimentRunOutputMode(quiet=True)
    quiet.info("should-not-appear")
    assert capsys.readouterr().out == ""

    normal = ExperimentRunOutputMode(quiet=False)
    normal.info("should-appear")
    assert "should-appear" in capsys.readouterr().out
