"""
Peak_Trade – Tests für Phase 20: Hyperparameter-Sweeps
=======================================================

Testet:
- Parameter-Grid-Generierung
- Sweep-Engine Core-Logik
- SweepConfig Validierung
- Registry-Integration (mit skip_registry)
- CLI-Script Struktur
"""

import ast
import pytest
import pandas as pd
import numpy as np
import inspect
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch

from tests.utils.dt import normalize_dt_index


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_ohlcv_data() -> pd.DataFrame:
    """Erstellt synthetische OHLCV-Daten für Tests."""
    np.random.seed(42)
    n_bars = 200

    end = datetime.now()
    start = end - timedelta(hours=n_bars)
    index = pd.date_range(start=start, periods=n_bars, freq="1h", tz="UTC")

    returns = np.random.normal(0, 0.015, n_bars)
    trend = np.sin(np.linspace(0, 4 * np.pi, n_bars)) * 0.001
    returns = returns + trend
    close_prices = 50000 * np.exp(np.cumsum(returns))

    df = pd.DataFrame(index=index)
    df["close"] = close_prices
    df["open"] = df["close"].shift(1).fillna(50000)
    df["high"] = np.maximum(df["open"], df["close"]) * (1 + np.random.uniform(0, 0.005, n_bars))
    df["low"] = np.minimum(df["open"], df["close"]) * (1 - np.random.uniform(0, 0.005, n_bars))
    df["volume"] = np.random.uniform(100, 1000, n_bars)

    return df[["open", "high", "low", "close", "volume"]]


@pytest.fixture
def simple_param_grid() -> dict:
    """Einfaches Parameter-Grid für Tests."""
    return {
        "lookback_window": [15, 20],
        "entry_multiplier": [1.5, 2.0],
    }


@pytest.fixture
def minimal_param_grid() -> dict:
    """Minimales Grid für schnelle Tests."""
    return {
        "lookback_window": [20],
        "entry_multiplier": [1.5],
    }


# =============================================================================
# TESTS: PARAMETER GRID FUNCTIONS
# =============================================================================


class TestExpandParameterGrid:
    """Tests für expand_parameter_grid Funktion."""

    def test_import(self):
        """Funktion kann importiert werden."""
        from src.sweeps import expand_parameter_grid

        assert expand_parameter_grid is not None

    def test_single_param(self):
        """Grid mit einem Parameter."""
        from src.sweeps import expand_parameter_grid

        grid = {"param1": [1, 2, 3]}
        result = expand_parameter_grid(grid)

        assert len(result) == 3
        assert {"param1": 1} in result
        assert {"param1": 2} in result
        assert {"param1": 3} in result

    def test_two_params(self):
        """Grid mit zwei Parametern."""
        from src.sweeps import expand_parameter_grid

        grid = {"a": [1, 2], "b": [10, 20]}
        result = expand_parameter_grid(grid)

        assert len(result) == 4
        assert {"a": 1, "b": 10} in result
        assert {"a": 1, "b": 20} in result
        assert {"a": 2, "b": 10} in result
        assert {"a": 2, "b": 20} in result

    def test_three_params(self):
        """Grid mit drei Parametern (kartesisches Produkt)."""
        from src.sweeps import expand_parameter_grid

        grid = {"x": [1, 2], "y": [10, 20], "z": [100]}
        result = expand_parameter_grid(grid)

        assert len(result) == 2 * 2 * 1  # 4
        for combo in result:
            assert "x" in combo
            assert "y" in combo
            assert "z" in combo
            assert combo["z"] == 100

    def test_empty_grid(self):
        """Leeres Grid gibt eine leere Kombination."""
        from src.sweeps import expand_parameter_grid

        result = expand_parameter_grid({})
        assert result == [{}]

    def test_mixed_types(self):
        """Grid mit verschiedenen Datentypen."""
        from src.sweeps import expand_parameter_grid

        grid = {
            "int_param": [10, 20],
            "float_param": [1.5, 2.5],
            "bool_param": [True, False],
        }
        result = expand_parameter_grid(grid)

        assert len(result) == 2 * 2 * 2  # 8


# =============================================================================
# TESTS: SWEEP CONFIG
# =============================================================================


class TestSweepConfig:
    """Tests für SweepConfig Datenklasse."""

    def test_import(self):
        """SweepConfig kann importiert werden."""
        from src.sweeps import SweepConfig

        assert SweepConfig is not None

    def test_basic_instantiation(self, simple_param_grid):
        """SweepConfig kann mit Basics instantiiert werden."""
        from src.sweeps import SweepConfig

        config = SweepConfig(
            strategy_key="my_strategy",
            param_grid=simple_param_grid,
        )

        assert config.strategy_key == "my_strategy"
        assert config.param_grid == simple_param_grid
        assert config.symbol == "BTC/EUR"  # Default
        assert config.timeframe == "1h"  # Default

    def test_custom_values(self, simple_param_grid):
        """SweepConfig mit Custom-Werten."""
        from src.sweeps import SweepConfig

        config = SweepConfig(
            strategy_key="my_strategy",
            param_grid=simple_param_grid,
            symbol="ETH/EUR",
            timeframe="4h",
            sweep_name="test_sweep",
            tag="unittest",
            max_runs=5,
            sort_by="total_return",
        )

        assert config.symbol == "ETH/EUR"
        assert config.timeframe == "4h"
        assert config.sweep_name == "test_sweep"
        assert config.tag == "unittest"
        assert config.max_runs == 5
        assert config.sort_by == "total_return"

    def test_total_combinations(self, simple_param_grid):
        """total_combinations Property funktioniert."""
        from src.sweeps import SweepConfig

        config = SweepConfig(
            strategy_key="my_strategy",
            param_grid=simple_param_grid,
        )

        assert config.total_combinations == 4  # 2 × 2

    def test_effective_runs_no_limit(self, simple_param_grid):
        """effective_runs ohne max_runs."""
        from src.sweeps import SweepConfig

        config = SweepConfig(
            strategy_key="my_strategy",
            param_grid=simple_param_grid,
        )

        assert config.effective_runs == 4

    def test_effective_runs_with_limit(self, simple_param_grid):
        """effective_runs mit max_runs."""
        from src.sweeps import SweepConfig

        config = SweepConfig(
            strategy_key="my_strategy",
            param_grid=simple_param_grid,
            max_runs=2,
        )

        assert config.effective_runs == 2

    def test_invalid_strategy_raises(self, simple_param_grid):
        """Ungültige Strategie wirft ValueError."""
        from src.sweeps import SweepConfig

        with pytest.raises(ValueError, match="Unbekannte Strategie"):
            SweepConfig(
                strategy_key="nonexistent_strategy",
                param_grid=simple_param_grid,
            )

    def test_empty_grid_raises(self):
        """Leeres param_grid wirft ValueError."""
        from src.sweeps import SweepConfig

        with pytest.raises(ValueError, match="param_grid darf nicht leer"):
            SweepConfig(
                strategy_key="my_strategy",
                param_grid={},
            )


# =============================================================================
# TESTS: SWEEP RESULT
# =============================================================================


class TestSweepResult:
    """Tests für SweepResult Datenklasse."""

    def test_import(self):
        """SweepResult kann importiert werden."""
        from src.sweeps.engine import SweepResult

        assert SweepResult is not None

    def test_basic_instantiation(self):
        """SweepResult kann instantiiert werden."""
        from src.sweeps.engine import SweepResult

        result = SweepResult(
            params={"lookback_window": 20},
            stats={"total_return": 0.15, "sharpe": 1.5, "max_drawdown": -0.08},
            run_id="test-123",
        )

        assert result.params == {"lookback_window": 20}
        assert result.success is True
        assert result.error is None

    def test_shortcuts(self):
        """Shortcut-Properties funktionieren."""
        from src.sweeps.engine import SweepResult

        result = SweepResult(
            params={},
            stats={
                "total_return": 0.15,
                "sharpe": 1.5,
                "max_drawdown": -0.08,
                "total_trades": 42,
            },
            run_id="test-123",
        )

        assert result.total_return == 0.15
        assert result.sharpe == 1.5
        assert result.max_drawdown == -0.08
        assert result.total_trades == 42

    def test_failed_result(self):
        """Fehlgeschlagenes Ergebnis."""
        from src.sweeps.engine import SweepResult

        result = SweepResult(
            params={"lookback_window": 1},
            stats={},
            run_id="",
            success=False,
            error="lookback_window muss > 1 sein",
        )

        assert result.success is False
        assert result.error is not None


# =============================================================================
# TESTS: SWEEP ENGINE
# =============================================================================


class TestSweepEngine:
    """Tests für SweepEngine."""

    def test_import(self):
        """SweepEngine kann importiert werden."""
        from src.sweeps import SweepEngine

        assert SweepEngine is not None

    def test_instantiation(self):
        """SweepEngine kann instantiiert werden."""
        from src.sweeps import SweepEngine

        engine = SweepEngine()
        assert engine is not None
        assert engine.verbose is False

    def test_instantiation_verbose(self):
        """SweepEngine mit verbose."""
        from src.sweeps import SweepEngine

        engine = SweepEngine(verbose=True)
        assert engine.verbose is True

    def test_mini_sweep(self, sample_ohlcv_data, minimal_param_grid):
        """Minimaler Sweep funktioniert."""
        from src.sweeps import SweepConfig, SweepEngine

        config = SweepConfig(
            strategy_key="my_strategy",
            param_grid=minimal_param_grid,
        )

        engine = SweepEngine(verbose=False)
        summary = engine.run_sweep(config, data=sample_ohlcv_data, skip_registry=True)

        assert summary is not None
        assert summary.strategy_key == "my_strategy"
        assert summary.runs_executed == 1
        assert summary.successful_runs >= 0

    def test_sweep_with_multiple_combinations(self, sample_ohlcv_data, simple_param_grid):
        """Sweep mit mehreren Kombinationen."""
        from src.sweeps import SweepConfig, SweepEngine

        config = SweepConfig(
            strategy_key="my_strategy",
            param_grid=simple_param_grid,
            max_runs=4,
        )

        engine = SweepEngine(verbose=False)
        summary = engine.run_sweep(config, data=sample_ohlcv_data, skip_registry=True)

        assert summary.runs_executed == 4
        assert len(summary.results) == 4

    def test_sweep_summary_has_best_result(self, sample_ohlcv_data, simple_param_grid):
        """Sweep-Summary hat best_result."""
        from src.sweeps import SweepConfig, SweepEngine

        config = SweepConfig(
            strategy_key="my_strategy",
            param_grid=simple_param_grid,
        )

        engine = SweepEngine(verbose=False)
        summary = engine.run_sweep(config, data=sample_ohlcv_data, skip_registry=True)

        if summary.successful_runs > 0:
            assert summary.best_result is not None
            assert "lookback_window" in summary.best_result.params

    def test_sweep_summary_get_top_results(self, sample_ohlcv_data, simple_param_grid):
        """get_top_results funktioniert."""
        from src.sweeps import SweepConfig, SweepEngine

        config = SweepConfig(
            strategy_key="my_strategy",
            param_grid=simple_param_grid,
        )

        engine = SweepEngine(verbose=False)
        summary = engine.run_sweep(config, data=sample_ohlcv_data, skip_registry=True)

        top_2 = summary.get_top_results(n=2, sort_by="sharpe")
        assert len(top_2) <= 2

    def test_sweep_summary_to_dataframe(self, sample_ohlcv_data, simple_param_grid):
        """to_dataframe funktioniert."""
        from src.sweeps import SweepConfig, SweepEngine

        config = SweepConfig(
            strategy_key="my_strategy",
            param_grid=simple_param_grid,
        )

        engine = SweepEngine(verbose=False)
        summary = engine.run_sweep(config, data=sample_ohlcv_data, skip_registry=True)

        df = summary.to_dataframe()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == summary.runs_executed

    def test_sweep_with_tag(self, sample_ohlcv_data, minimal_param_grid):
        """Sweep mit Tag."""
        from src.sweeps import SweepConfig, SweepEngine

        config = SweepConfig(
            strategy_key="my_strategy",
            param_grid=minimal_param_grid,
            tag="unittest",
        )

        engine = SweepEngine(verbose=False)
        summary = engine.run_sweep(config, data=sample_ohlcv_data, skip_registry=True)

        assert summary is not None


# =============================================================================
# TESTS: CONVENIENCE FUNCTION
# =============================================================================


class TestRunStrategySweep:
    """Tests für run_strategy_sweep Convenience-Funktion."""

    def test_import(self):
        """Funktion kann importiert werden."""
        from src.sweeps.engine import run_strategy_sweep

        assert run_strategy_sweep is not None

    def test_basic_usage(self, sample_ohlcv_data, minimal_param_grid):
        """Convenience-Funktion funktioniert."""
        from src.sweeps.engine import run_strategy_sweep

        summary = run_strategy_sweep(
            strategy_key="my_strategy",
            param_grid=minimal_param_grid,
            data=sample_ohlcv_data,
            skip_registry=True,
        )

        assert summary is not None
        assert summary.strategy_key == "my_strategy"


# =============================================================================
# TESTS: HELPER FUNCTIONS
# =============================================================================


class TestGenerateSweepId:
    """Tests für generate_sweep_id."""

    def test_import(self):
        """Funktion kann importiert werden."""
        from src.sweeps import generate_sweep_id

        assert generate_sweep_id is not None

    def test_generates_unique_ids(self):
        """IDs sind eindeutig."""
        from src.sweeps import generate_sweep_id

        ids = [generate_sweep_id() for _ in range(100)]
        assert len(set(ids)) == 100

    def test_id_format(self):
        """ID hat korrektes Format."""
        from src.sweeps import generate_sweep_id

        sweep_id = generate_sweep_id()
        assert isinstance(sweep_id, str)
        assert len(sweep_id) == 8  # 8 hex chars


# =============================================================================
# TESTS: CLI SCRIPT
# =============================================================================


class TestCLIScript:
    """Tests für CLI-Script Struktur."""

    def test_script_exists(self):
        """Script existiert."""
        script_path = Path(__file__).parent.parent / "scripts" / "run_sweep_strategy.py"
        assert script_path.exists()

    def test_script_has_main(self):
        """Script hat main() Funktion."""
        script_path = Path(__file__).parent.parent / "scripts" / "run_sweep_strategy.py"
        content = script_path.read_text()
        assert "def main(" in content
        assert "def parse_args(" in content

    def test_script_has_required_features(self):
        """Script hat erforderliche Features."""
        script_path = Path(__file__).parent.parent / "scripts" / "run_sweep_strategy.py"
        content = script_path.read_text()

        # CLI Args
        assert "--strategy" in content
        assert "--grid" in content
        assert "--param" in content
        assert "--max-runs" in content
        assert "--dry-run" in content
        assert "--no-registry" in content

        # Imports
        assert "from src.sweeps import" in content


# =============================================================================
# TESTS: GRID CONFIG FILES
# =============================================================================


class TestGridConfigFiles:
    """Tests für vordefinierte Grid-Config-Dateien."""

    def test_config_dir_exists(self):
        """Config-Verzeichnis existiert."""
        config_dir = Path(__file__).parent.parent / "config" / "sweeps"
        assert config_dir.exists()

    def test_ma_crossover_grid_exists(self):
        """MA-Crossover Grid existiert."""
        grid_path = Path(__file__).parent.parent / "config" / "sweeps" / "ma_crossover.toml"
        assert grid_path.exists()

    def test_trend_following_grid_exists(self):
        """Trend-Following Grid existiert."""
        grid_path = Path(__file__).parent.parent / "config" / "sweeps" / "trend_following.toml"
        assert grid_path.exists()

    def test_mean_reversion_grid_exists(self):
        """Mean-Reversion Grid existiert."""
        grid_path = Path(__file__).parent.parent / "config" / "sweeps" / "mean_reversion.toml"
        assert grid_path.exists()

    def test_my_strategy_grid_exists(self):
        """MyStrategy Grid existiert."""
        grid_path = Path(__file__).parent.parent / "config" / "sweeps" / "my_strategy.toml"
        assert grid_path.exists()

    def test_can_load_my_strategy_grid(self):
        """MyStrategy Grid kann geladen werden."""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        grid_path = Path(__file__).parent.parent / "config" / "sweeps" / "my_strategy.toml"
        with grid_path.open("rb") as f:
            data = tomllib.load(f)

        grid = data.get("grid", data)
        assert "lookback_window" in grid
        assert "entry_multiplier" in grid
        assert isinstance(grid["lookback_window"], list)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestIntegration:
    """Integration-Tests für Sweep-System."""

    def test_sweep_with_different_strategies(self, sample_ohlcv_data):
        """Sweep funktioniert mit verschiedenen Strategien."""
        from src.sweeps import SweepConfig, SweepEngine

        strategies_and_grids = [
            ("ma_crossover", {"fast_window": [10, 20], "slow_window": [50]}),
            ("my_strategy", {"lookback_window": [20], "entry_multiplier": [1.5]}),
        ]

        engine = SweepEngine(verbose=False)

        for strategy_key, param_grid in strategies_and_grids:
            config = SweepConfig(
                strategy_key=strategy_key,
                param_grid=param_grid,
                max_runs=2,
            )

            summary = engine.run_sweep(config, data=sample_ohlcv_data, skip_registry=True)
            assert summary is not None
            assert summary.strategy_key == strategy_key

    def test_sweep_timing(self, sample_ohlcv_data, simple_param_grid):
        """Sweep hat Timing-Info."""
        from src.sweeps import SweepConfig, SweepEngine

        config = SweepConfig(
            strategy_key="my_strategy",
            param_grid=simple_param_grid,
            max_runs=2,
        )

        engine = SweepEngine(verbose=False)
        summary = engine.run_sweep(config, data=sample_ohlcv_data, skip_registry=True)

        assert summary.duration_seconds >= 0
        assert summary.started_at is not None
        assert summary.completed_at is not None


# =============================================================================
# SWEEP ENGINE load_strategy() MIGRATION (offline, fail-closed)
# =============================================================================


class TestSweepEngineLoadStrategyMigration:
    """Offline guards for canonical SweepEngine strategy binding migration."""

    TARGET_MODULE = Path(__file__).resolve().parent.parent / "src/sweeps/engine.py"
    MA_CROSSOVER_KEY = "ma_crossover"
    STRATEGY_PARAMS_BUILDER_OWNER = "scripts/run_backtest.py:_build_strategy_params_from_config"
    FORBIDDEN_LOCAL_BUILDER_DEFS = frozenset({"_build_strategy_params_from_config"})

    def _read_engine_source(self) -> str:
        return self.TARGET_MODULE.read_text(encoding="utf-8")

    def _local_function_defs(self) -> set[str]:
        tree = ast.parse(self._read_engine_source())
        return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}

    def test_engine_source_uses_load_strategy(self) -> None:
        assert "load_strategy" in self._read_engine_source()

    def test_engine_source_has_no_create_strategy_from_config(self) -> None:
        assert "create_strategy_from_config" not in self._read_engine_source()

    def test_engine_source_has_no_local_builder_definition(self) -> None:
        local_defs = self._local_function_defs()
        assert self.FORBIDDEN_LOCAL_BUILDER_DEFS.isdisjoint(local_defs)

    def test_build_strategy_params_import_identity_is_canonical_owner(self) -> None:
        import scripts.run_backtest as run_backtest_script
        from src.sweeps import engine as engine_module

        assert (
            engine_module._build_strategy_params_from_config
            is run_backtest_script._build_strategy_params_from_config
        )

    def test_engine_source_imports_canonical_strategy_params_builder(self) -> None:
        source = self._read_engine_source()
        assert "_build_strategy_params_from_config" in source
        assert "scripts.run_backtest" in source

    def test_build_strategy_params_source_uses_load_strategy_not_from_config_bypass(self) -> None:
        import scripts.run_backtest as run_backtest_script

        source = inspect.getsource(run_backtest_script._build_strategy_params_from_config)
        assert "load_strategy" in source
        assert "spec.cls.from_config" not in source

    def test_build_strategy_params_includes_section_and_stop_pct(self) -> None:
        from src.core.peak_config import PeakConfig
        from src.sweeps.engine import _build_strategy_params_from_config

        cfg = PeakConfig(
            raw={
                "environment": {"mode": "backtest"},
                "strategy": {
                    self.MA_CROSSOVER_KEY: {
                        "fast_window": 10,
                        "slow_window": 50,
                        "price_col": "close",
                        "stop_pct": 0.03,
                    },
                },
            }
        )
        params = _build_strategy_params_from_config(cfg, self.MA_CROSSOVER_KEY)
        assert params["fast_window"] == 10
        assert params["slow_window"] == 50
        assert params["price_col"] == "close"
        assert params["stop_pct"] == 0.03

    def test_build_strategy_params_calls_load_strategy_for_registry_validation(self) -> None:
        import scripts.run_backtest as run_backtest_script
        from src.core.peak_config import PeakConfig
        from src.sweeps import engine as engine_module

        cfg = PeakConfig(
            raw={
                "environment": {"mode": "backtest"},
                "strategy": {
                    self.MA_CROSSOVER_KEY: {
                        "fast_window": 10,
                        "slow_window": 50,
                        "price_col": "close",
                    },
                },
            }
        )

        with patch.object(run_backtest_script, "load_strategy") as load_mock:
            load_mock.return_value = MagicMock()
            params = engine_module._build_strategy_params_from_config(cfg, self.MA_CROSSOVER_KEY)

        load_mock.assert_called_once_with(self.MA_CROSSOVER_KEY)
        assert params["fast_window"] == 10
        assert params["stop_pct"] == 0.02

    def test_build_strategy_params_isolated_per_strategy_key(self) -> None:
        from src.core.peak_config import PeakConfig
        from src.sweeps.engine import _build_strategy_params_from_config

        cfg = PeakConfig(
            raw={
                "environment": {"mode": "backtest"},
                "strategy": {
                    self.MA_CROSSOVER_KEY: {
                        "fast_window": 10,
                        "slow_window": 50,
                        "price_col": "close",
                    },
                    "rsi_reversion": {
                        "rsi_period": 14,
                        "oversold": 30,
                        "overbought": 70,
                    },
                },
            }
        )
        ma_params = _build_strategy_params_from_config(cfg, self.MA_CROSSOVER_KEY)
        rsi_params = _build_strategy_params_from_config(cfg, "rsi_reversion")

        assert "rsi_period" not in ma_params
        assert "fast_window" not in rsi_params
        assert ma_params["fast_window"] == 10
        assert rsi_params["rsi_period"] == 14

    def test_build_strategy_params_unknown_strategy_fails_closed(self) -> None:
        from src.core.peak_config import PeakConfig
        from src.sweeps.engine import _build_strategy_params_from_config

        cfg = PeakConfig(
            raw={
                "environment": {"mode": "backtest"},
                "strategy": {self.MA_CROSSOVER_KEY: {"fast_window": 10, "slow_window": 50}},
            }
        )
        with pytest.raises(KeyError, match="definitely_not_a_strategy_xyz"):
            _build_strategy_params_from_config(cfg, "definitely_not_a_strategy_xyz")

    def test_build_strategy_params_non_dict_section_fails_closed(self) -> None:
        from src.core.peak_config import PeakConfig
        from src.sweeps.engine import _build_strategy_params_from_config

        cfg = PeakConfig(
            raw={
                "environment": {"mode": "backtest"},
                "strategy": {self.MA_CROSSOVER_KEY: "invalid"},
            }
        )
        params = _build_strategy_params_from_config(cfg, self.MA_CROSSOVER_KEY)
        assert params == {"stop_pct": 0.02}

    def test_call_chain_run_sweep_strategy_to_engine(self) -> None:
        runner = (
            Path(__file__).resolve().parent.parent / "scripts/run_sweep_strategy.py"
        ).read_text(encoding="utf-8")
        assert "SweepEngine" in runner
        assert "from src.sweeps import" in runner

    def test_run_sweep_script_unchanged_binding_path(self) -> None:
        run_sweep = (Path(__file__).resolve().parent.parent / "scripts/run_sweep.py").read_text(
            encoding="utf-8"
        )
        assert "load_strategy" in run_sweep
        assert "SweepEngine" not in run_sweep

    def test_run_single_backtest_calls_load_strategy_with_effective_params(
        self, sample_ohlcv_data
    ) -> None:
        from src.core.peak_config import PeakConfig
        from src.sweeps import SweepEngine

        captured: dict[str, object] = {}

        def fake_signal_fn(df, params):
            captured["params"] = dict(params)
            return pd.Series(np.zeros(len(df)), index=df.index)

        cfg = PeakConfig(
            raw={
                "environment": {"mode": "backtest"},
                "strategy": {
                    self.MA_CROSSOVER_KEY: {
                        "fast_window": 20,
                        "slow_window": 50,
                        "price_col": "close",
                    },
                },
            }
        )

        engine = SweepEngine(verbose=False)
        combo_params = {"fast_window": 10, "slow_window": 40}

        mock_result = MagicMock()
        mock_result.stats = {"total_return": 0.0, "sharpe": 0.0}

        load_mock = MagicMock(return_value=fake_signal_fn)
        with (
            patch("src.sweeps.engine.load_strategy", load_mock),
            patch("scripts.run_backtest.load_strategy", load_mock),
            patch("src.sweeps.engine.BacktestEngine") as engine_cls,
        ):

            def run_realistic_side_effect(df, strategy_signal_fn, strategy_params, **kwargs):
                strategy_signal_fn(df, strategy_params)
                return mock_result

            engine_cls.return_value.run_realistic.side_effect = run_realistic_side_effect
            stats, _ = engine._run_single_backtest(
                data=sample_ohlcv_data,
                strategy_key=self.MA_CROSSOVER_KEY,
                params=combo_params,
                cfg=cfg,
            )

        load_mock.assert_called()
        assert load_mock.call_count == 2
        assert load_mock.call_args_list[-1] == ((self.MA_CROSSOVER_KEY,),)
        assert captured["params"]["fast_window"] == 10
        assert captured["params"]["slow_window"] == 40
        assert captured["params"]["stop_pct"] == 0.02
        assert isinstance(stats, dict)

    def test_isolated_load_strategy_binding_per_backtest_call(self, sample_ohlcv_data) -> None:
        from src.core.peak_config import PeakConfig
        from src.sweeps import SweepEngine

        load_calls: list[str] = []

        def fake_signal_fn(df, params):
            return pd.Series(np.zeros(len(df)), index=df.index)

        def side_effect(strategy_key: str):
            load_calls.append(strategy_key)
            return fake_signal_fn

        cfg = PeakConfig(
            raw={
                "environment": {"mode": "backtest"},
                "strategy": {self.MA_CROSSOVER_KEY: {"fast_window": 20, "slow_window": 50}},
            }
        )
        engine = SweepEngine(verbose=False)

        mock_result = MagicMock()
        mock_result.stats = {"total_return": 0.0, "sharpe": 0.0}

        load_mock = MagicMock(side_effect=side_effect)
        with (
            patch("src.sweeps.engine.load_strategy", load_mock),
            patch("scripts.run_backtest.load_strategy", load_mock),
            patch("src.sweeps.engine.BacktestEngine") as engine_cls,
        ):
            engine_cls.return_value.run_realistic.return_value = mock_result
            engine._run_single_backtest(
                data=sample_ohlcv_data,
                strategy_key=self.MA_CROSSOVER_KEY,
                params={"fast_window": 10, "slow_window": 40},
                cfg=cfg,
            )
            engine._run_single_backtest(
                data=sample_ohlcv_data,
                strategy_key=self.MA_CROSSOVER_KEY,
                params={"fast_window": 12, "slow_window": 42},
                cfg=cfg,
            )

        assert load_mock.call_args_list == [
            ((self.MA_CROSSOVER_KEY,),),
            ((self.MA_CROSSOVER_KEY,),),
            ((self.MA_CROSSOVER_KEY,),),
            ((self.MA_CROSSOVER_KEY,),),
        ]

    REGIME_KEY = "regime_aware_portfolio"

    def _regime_cfg(self):
        from src.core.peak_config import PeakConfig

        return PeakConfig(
            raw={
                "environment": {"mode": "backtest"},
                "strategy": {
                    "breakout": {"lookback_breakout": 15, "side": "long"},
                    "rsi_reversion": {"rsi_window": 14, "lower": 30.0, "upper": 70.0},
                    "vol_regime_filter": {
                        "vol_window": 14,
                        "vol_percentile_low": 25,
                        "vol_percentile_high": 75,
                        "regime_mode": True,
                    },
                },
                "portfolio": {
                    "regime_aware_breakout_rsi": {
                        "components": ["breakout", "rsi_reversion"],
                        "base_weights": {"breakout": 0.6, "rsi_reversion": 0.4},
                        "regime_strategy": "vol_regime_filter",
                        "mode": "scale",
                        "risk_on_scale": 1.0,
                        "neutral_scale": 0.5,
                        "risk_off_scale": 0.0,
                        "signal_threshold": 0.3,
                    }
                },
            }
        )

    def test_regime_branch_source_has_no_direct_class_import(self) -> None:
        source = inspect.getsource(
            __import__(
                "src.sweeps.engine", fromlist=["SweepEngine"]
            ).SweepEngine._run_single_backtest
        )
        assert (
            "from src.strategies.regime_aware_portfolio import RegimeAwarePortfolioStrategy"
            not in source
        )

    def test_regime_branch_source_uses_load_strategy_and_spec_cls(self) -> None:
        source = inspect.getsource(
            __import__(
                "src.sweeps.engine", fromlist=["SweepEngine"]
            ).SweepEngine._run_single_backtest
        )
        assert "load_strategy(strategy_key)" in source
        assert "spec_ra.cls.from_config" in source

    def test_run_single_backtest_regime_branch_calls_load_strategy(self, sample_ohlcv_data) -> None:
        from src.sweeps import SweepEngine

        cfg = self._regime_cfg()
        engine = SweepEngine(verbose=False)
        combo_params = {"risk_on_scale": 0.9, "neutral_scale": 0.4}

        mock_strategy = MagicMock()
        mock_strategy.generate_signals.return_value = pd.Series(
            np.zeros(len(sample_ohlcv_data)), index=sample_ohlcv_data.index
        )
        mock_spec = MagicMock()
        mock_spec.config_section = "portfolio.regime_aware_breakout_rsi"
        mock_spec.cls.from_config.return_value = mock_strategy

        mock_result = MagicMock()
        mock_result.stats = {"total_return": 0.0, "sharpe": 0.0}

        with (
            patch("src.sweeps.engine.get_strategy_spec", return_value=mock_spec) as spec_mock,
            patch("src.sweeps.engine.load_strategy") as load_mock,
            patch("src.sweeps.engine.BacktestEngine") as engine_cls,
        ):

            def run_realistic_side_effect(df, strategy_signal_fn, strategy_params, **kwargs):
                strategy_signal_fn(df, strategy_params)
                return mock_result

            engine_cls.return_value.run_realistic.side_effect = run_realistic_side_effect
            stats, _ = engine._run_single_backtest(
                data=sample_ohlcv_data,
                strategy_key=self.REGIME_KEY,
                params=combo_params,
                cfg=cfg,
            )

        spec_mock.assert_called_once_with(self.REGIME_KEY)
        load_mock.assert_called_once_with(self.REGIME_KEY)
        mock_spec.cls.from_config.assert_called_once_with(
            cfg,
            section="portfolio.regime_aware_breakout_rsi",
            param_overrides=combo_params,
        )
        mock_strategy.generate_signals.assert_called_once()
        assert isinstance(stats, dict)

    def test_regime_branch_isolated_binding_per_backtest_call(self, sample_ohlcv_data) -> None:
        from src.sweeps import SweepEngine

        cfg = self._regime_cfg()
        engine = SweepEngine(verbose=False)
        load_calls: list[str] = []
        from_config_calls: list[dict[str, object]] = []

        def track_load(key: str):
            load_calls.append(key)

        def track_from_config(*args, **kwargs):
            from_config_calls.append(dict(kwargs))
            mock_strategy = MagicMock()
            mock_strategy.generate_signals.return_value = pd.Series(
                np.zeros(len(sample_ohlcv_data)), index=sample_ohlcv_data.index
            )
            return mock_strategy

        mock_spec = MagicMock()
        mock_spec.config_section = "portfolio.regime_aware_breakout_rsi"
        mock_spec.cls.from_config.side_effect = track_from_config

        mock_result = MagicMock()
        mock_result.stats = {"total_return": 0.0, "sharpe": 0.0}

        with (
            patch("src.sweeps.engine.get_strategy_spec", return_value=mock_spec),
            patch("src.sweeps.engine.load_strategy", side_effect=track_load),
            patch("src.sweeps.engine.BacktestEngine") as engine_cls,
        ):
            engine_cls.return_value.run_realistic.return_value = mock_result
            engine._run_single_backtest(
                data=sample_ohlcv_data,
                strategy_key=self.REGIME_KEY,
                params={"risk_on_scale": 0.8},
                cfg=cfg,
            )
            engine._run_single_backtest(
                data=sample_ohlcv_data,
                strategy_key=self.REGIME_KEY,
                params={"risk_on_scale": 0.6, "neutral_scale": 0.3},
                cfg=cfg,
            )

        assert load_calls == [self.REGIME_KEY, self.REGIME_KEY]
        assert from_config_calls[0]["param_overrides"] == {"risk_on_scale": 0.8}
        assert from_config_calls[1]["param_overrides"] == {
            "risk_on_scale": 0.6,
            "neutral_scale": 0.3,
        }


# =============================================================================
# SWEEP DATA PARQUET CACHE CONTRACTS (offline, fail-closed)
# =============================================================================


class TestSweepParquetCacheContracts:
    """Offline contracts for ParquetCache integration in sweep data loading."""

    def _synthetic_loader(self, df: pd.DataFrame):
        calls = {"count": 0}

        def _loader() -> pd.DataFrame:
            calls["count"] += 1
            return df.copy()

        _loader.calls = calls  # type: ignore[attr-defined]
        return _loader

    def _sample_df(self, *, seed: int = 1, n: int = 24) -> pd.DataFrame:
        np.random.seed(seed)
        index = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
        close = 100.0 + np.cumsum(np.random.randn(n))
        return pd.DataFrame(
            {
                "open": close * 0.999,
                "high": close * 1.002,
                "low": close * 0.998,
                "close": close,
                "volume": np.full(n, 1000.0),
            },
            index=index,
        )

    def test_first_identical_request_miss_single_loader_call(self, tmp_path) -> None:
        from src.data.cache import ParquetCache
        from src.sweeps.engine import load_sweep_ohlcv_data

        df = self._sample_df()
        loader = self._synthetic_loader(df)
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))

        loaded, outcome = load_sweep_ohlcv_data(
            symbol="BTC/EUR",
            timeframe="1h",
            n_bars=len(df),
            loader=loader,
            cache=cache,
            use_cache=True,
        )

        assert outcome == "miss"
        assert loader.calls["count"] == 1
        pd.testing.assert_frame_equal(loaded, df, check_freq=False)

    def test_second_identical_request_hit_no_extra_loader_call(self, tmp_path) -> None:
        from src.data.cache import ParquetCache
        from src.sweeps.engine import load_sweep_ohlcv_data

        df = self._sample_df(seed=2)
        loader = self._synthetic_loader(df)
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))

        load_sweep_ohlcv_data(
            symbol="BTC/EUR",
            timeframe="1h",
            n_bars=len(df),
            loader=loader,
            cache=cache,
            use_cache=True,
        )
        loaded, outcome = load_sweep_ohlcv_data(
            symbol="BTC/EUR",
            timeframe="1h",
            n_bars=len(df),
            loader=loader,
            cache=cache,
            use_cache=True,
        )

        assert outcome == "hit"
        assert loader.calls["count"] == 1
        pd.testing.assert_frame_equal(
            normalize_dt_index(loaded, ensure_utc=True),
            normalize_dt_index(df, ensure_utc=True),
            check_freq=False,
        )

    def test_different_symbols_have_isolated_cache_keys(self, tmp_path) -> None:
        from src.data.cache import ParquetCache
        from src.sweeps.engine import build_sweep_data_cache_key, load_sweep_ohlcv_data

        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))
        btc_loader = self._synthetic_loader(self._sample_df(seed=3))
        eth_loader = self._synthetic_loader(self._sample_df(seed=4))

        load_sweep_ohlcv_data(
            symbol="BTC/EUR",
            timeframe="1h",
            n_bars=24,
            loader=btc_loader,
            cache=cache,
        )
        load_sweep_ohlcv_data(
            symbol="ETH/EUR",
            timeframe="1h",
            n_bars=24,
            loader=eth_loader,
            cache=cache,
        )

        assert build_sweep_data_cache_key(
            symbol="BTC/EUR", timeframe="1h", n_bars=24
        ) != build_sweep_data_cache_key(symbol="ETH/EUR", timeframe="1h", n_bars=24)
        assert btc_loader.calls["count"] == 1
        assert eth_loader.calls["count"] == 1

    def test_different_timeframes_have_isolated_cache_keys(self, tmp_path) -> None:
        from src.data.cache import ParquetCache
        from src.sweeps.engine import build_sweep_data_cache_key, load_sweep_ohlcv_data

        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))
        loader_1h = self._synthetic_loader(self._sample_df(seed=5))
        loader_4h = self._synthetic_loader(self._sample_df(seed=6))

        load_sweep_ohlcv_data(
            symbol="BTC/EUR",
            timeframe="1h",
            n_bars=24,
            loader=loader_1h,
            cache=cache,
        )
        load_sweep_ohlcv_data(
            symbol="BTC/EUR",
            timeframe="4h",
            n_bars=24,
            loader=loader_4h,
            cache=cache,
        )

        assert build_sweep_data_cache_key(
            symbol="BTC/EUR", timeframe="1h", n_bars=24
        ) != build_sweep_data_cache_key(symbol="BTC/EUR", timeframe="4h", n_bars=24)
        assert loader_1h.calls["count"] == 1
        assert loader_4h.calls["count"] == 1

    def test_different_n_bars_have_isolated_cache_keys(self, tmp_path) -> None:
        from src.data.cache import ParquetCache
        from src.sweeps.engine import build_sweep_data_cache_key, load_sweep_ohlcv_data

        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))
        loader_200 = self._synthetic_loader(self._sample_df(seed=7, n=20))
        loader_400 = self._synthetic_loader(self._sample_df(seed=8, n=30))

        load_sweep_ohlcv_data(
            symbol="BTC/EUR",
            timeframe="1h",
            n_bars=200,
            loader=loader_200,
            cache=cache,
        )
        load_sweep_ohlcv_data(
            symbol="BTC/EUR",
            timeframe="1h",
            n_bars=400,
            loader=loader_400,
            cache=cache,
        )

        assert build_sweep_data_cache_key(
            symbol="BTC/EUR", timeframe="1h", n_bars=200
        ) != build_sweep_data_cache_key(symbol="BTC/EUR", timeframe="1h", n_bars=400)
        assert loader_200.calls["count"] == 1
        assert loader_400.calls["count"] == 1

    def test_cache_hit_matches_direct_loader_data(self, tmp_path) -> None:
        from src.data.cache import ParquetCache
        from src.sweeps.engine import load_sweep_ohlcv_data

        df = self._sample_df(seed=9)
        loader = self._synthetic_loader(df)
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))

        direct_df = loader()
        cached_df, outcome = load_sweep_ohlcv_data(
            symbol="BTC/EUR",
            timeframe="1h",
            n_bars=len(df),
            loader=loader,
            cache=cache,
            use_cache=True,
        )
        hit_df, hit_outcome = load_sweep_ohlcv_data(
            symbol="BTC/EUR",
            timeframe="1h",
            n_bars=len(df),
            loader=loader,
            cache=cache,
            use_cache=True,
        )

        assert outcome == "miss"
        assert hit_outcome == "hit"
        pd.testing.assert_frame_equal(
            normalize_dt_index(cached_df, ensure_utc=True),
            normalize_dt_index(direct_df, ensure_utc=True),
            check_freq=False,
        )
        pd.testing.assert_frame_equal(
            normalize_dt_index(hit_df, ensure_utc=True),
            normalize_dt_index(direct_df, ensure_utc=True),
            check_freq=False,
        )

    def test_corrupt_cache_invalidates_and_reloads_without_stale_data(self, tmp_path) -> None:
        from src.core.errors import CacheCorruptionError
        from src.data.cache import ParquetCache
        from src.sweeps.engine import (
            build_sweep_data_cache_key,
            load_sweep_ohlcv_data,
        )

        df = self._sample_df(seed=10)
        loader = self._synthetic_loader(df)
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))
        cache_key = build_sweep_data_cache_key(symbol="BTC/EUR", timeframe="1h", n_bars=len(df))

        cache.save(df, cache_key)
        corrupt_path = cache._get_cache_path(cache_key)
        Path(corrupt_path).write_text("not-a-parquet-file", encoding="utf-8")

        with pytest.raises(CacheCorruptionError):
            cache.load(cache_key)

        reloaded, outcome = load_sweep_ohlcv_data(
            symbol="BTC/EUR",
            timeframe="1h",
            n_bars=len(df),
            loader=loader,
            cache=cache,
            use_cache=True,
        )

        assert outcome == "fallback"
        assert loader.calls["count"] == 1
        pd.testing.assert_frame_equal(reloaded, df, check_freq=False)

    def test_cli_binds_cache_config_to_engine_loader(self, tmp_path) -> None:
        import scripts.sweep_parameters as sweep_script
        from src.core.peak_config import PeakConfig

        cfg = PeakConfig(
            raw={
                "data": {
                    "data_dir": str(tmp_path / "data"),
                    "use_cache": True,
                    "default_timeframe": "1h",
                },
                "strategy": {"ma_crossover": {"fast_window": 10, "slow_window": 50}},
                "sweep": {
                    "strategy_key": "ma_crossover",
                    "symbol": "BTC/EUR",
                    "parameters": {"fast_window": [10], "slow_window": [50]},
                },
            }
        )

        cache, use_cache = sweep_script.resolve_sweep_parquet_cache_from_config(cfg)
        assert use_cache is True
        assert cache is not None
        assert str(cache.cache_dir).endswith("cache")

    def test_cache_integration_does_not_mutate_strategy_config(self, tmp_path) -> None:
        from src.data.cache import ParquetCache
        from src.sweeps.engine import load_sweep_ohlcv_data

        raw = {
            "strategy": {
                "ma_crossover": {
                    "fast_window": 10,
                    "slow_window": 50,
                    "stop_pct": 0.02,
                }
            }
        }
        cfg_before = json.dumps(raw, sort_keys=True)
        df = self._sample_df(seed=11)
        loader = self._synthetic_loader(df)
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))

        load_sweep_ohlcv_data(
            symbol="BTC/EUR",
            timeframe="1h",
            n_bars=len(df),
            loader=loader,
            cache=cache,
        )

        assert json.dumps(raw, sort_keys=True) == cfg_before

    def test_no_network_or_runtime_side_effects(self, tmp_path, monkeypatch) -> None:
        from src.data.cache import ParquetCache
        from src.sweeps.engine import load_sweep_ohlcv_data

        def _forbidden_network(*_args, **_kwargs):
            raise AssertionError("network must not be used in offline sweep cache tests")

        monkeypatch.setattr("src.data.kraken.fetch_ohlcv_df", _forbidden_network)
        monkeypatch.setattr(
            "src.data.providers.kraken_ccxt_backend.KrakenCcxtBackend", _forbidden_network
        )

        df = self._sample_df(seed=12)
        loader = self._synthetic_loader(df)
        cache = ParquetCache(cache_dir=str(tmp_path / "cache"))

        loaded, outcome = load_sweep_ohlcv_data(
            symbol="BTC/EUR",
            timeframe="1h",
            n_bars=len(df),
            loader=loader,
            cache=cache,
        )

        assert outcome == "miss"
        assert len(loaded) == len(df)


# =============================================================================
# BATCH PROGRESS CONTRACTS (Phase 20, offline only)
# =============================================================================


class TestSweepBatchProgressContracts:
    """Offline batch-progress contracts for Phase-20 SweepEngine."""

    MA_KEY = "my_strategy"

    @staticmethod
    def _synthetic_stats(params: dict) -> dict:
        return {
            "total_return": float(params.get("lookback_window", 1)) * 0.01,
            "sharpe": 1.0,
            "max_drawdown": -0.05,
            "total_trades": 10,
        }

    def _mock_run_single(self, engine, monkeypatch):
        def _fake_backtest(*, data, strategy_key, params, cfg):
            mock_result = MagicMock()
            mock_result.stats = self._synthetic_stats(params)
            return mock_result.stats, mock_result

        monkeypatch.setattr(engine, "_run_single_backtest", _fake_backtest)

    def _config_with_n(self, n: int, *, max_runs: Optional[int] = None):
        from src.sweeps import SweepConfig

        return SweepConfig(
            strategy_key=self.MA_KEY,
            param_grid={"lookback_window": list(range(1, n + 1))},
            max_runs=max_runs,
        )

    def _run_offline(
        self,
        monkeypatch,
        sample_ohlcv_data,
        n: int,
        *,
        progress_every: int = 10,
        verbose: bool = False,
        progress_callback=None,
    ):
        from src.sweeps import SweepEngine

        engine = SweepEngine(
            verbose=verbose,
            progress_callback=progress_callback,
            progress_every=progress_every,
        )
        self._mock_run_single(engine, monkeypatch)
        config = self._config_with_n(n)
        return engine, engine.run_sweep(config, data=sample_ohlcv_data, skip_registry=True)

    def test_fewer_emissions_than_items_when_total_gt_interval(
        self, monkeypatch, sample_ohlcv_data
    ) -> None:
        calls: list[int] = []

        def cb(current: int, total: int, params: dict) -> None:
            calls.append(current)

        self._run_offline(
            monkeypatch,
            sample_ohlcv_data,
            25,
            progress_every=10,
            progress_callback=cb,
        )
        assert len(calls) < 25
        assert calls == [10, 20, 25]

    def test_emission_at_full_batch_boundaries(self, monkeypatch, sample_ohlcv_data) -> None:
        calls: list[int] = []

        def cb(current: int, total: int, params: dict) -> None:
            calls.append(current)

        self._run_offline(
            monkeypatch,
            sample_ohlcv_data,
            20,
            progress_every=10,
            progress_callback=cb,
        )
        assert calls == [10, 20]

    def test_final_flush_for_remainder_batch(self, monkeypatch, sample_ohlcv_data) -> None:
        calls: list[int] = []

        def cb(current: int, total: int, params: dict) -> None:
            calls.append(current)

        self._run_offline(
            monkeypatch,
            sample_ohlcv_data,
            25,
            progress_every=10,
            progress_callback=cb,
        )
        assert calls[-1] == 25

    def test_no_duplicate_final_flush_when_exactly_divisible(
        self, monkeypatch, sample_ohlcv_data
    ) -> None:
        calls: list[int] = []

        def cb(current: int, total: int, params: dict) -> None:
            calls.append(current)

        self._run_offline(
            monkeypatch,
            sample_ohlcv_data,
            20,
            progress_every=10,
            progress_callback=cb,
        )
        assert calls.count(20) == 1

    def test_zero_items_no_progress_output(self, monkeypatch, sample_ohlcv_data, capsys) -> None:
        from src.sweeps import SweepConfig, SweepEngine

        engine = SweepEngine(verbose=True, progress_every=10)
        self._mock_run_single(engine, monkeypatch)
        config = SweepConfig(
            strategy_key=self.MA_KEY,
            param_grid={"lookback_window": [20]},
            max_runs=0,
        )
        summary = engine.run_sweep(config, data=sample_ohlcv_data, skip_registry=True)
        out = capsys.readouterr().out
        assert summary.runs_executed == 0
        assert "[1/" not in out

    def test_single_item_emits_one_final_progress(self, monkeypatch, sample_ohlcv_data) -> None:
        calls: list[int] = []

        def cb(current: int, total: int, params: dict) -> None:
            calls.append(current)

        self._run_offline(
            monkeypatch,
            sample_ohlcv_data,
            1,
            progress_every=10,
            progress_callback=cb,
        )
        assert calls == [1]

    def test_quiet_mode_suppresses_batch_progress(
        self, monkeypatch, sample_ohlcv_data, capsys
    ) -> None:
        from src.sweeps import SweepEngine

        engine = SweepEngine(verbose=False, progress_every=10)
        self._mock_run_single(engine, monkeypatch)
        config = self._config_with_n(15)
        engine.run_sweep(config, data=sample_ohlcv_data, skip_registry=True)
        assert capsys.readouterr().out == ""

    def test_completion_visible_in_verbose_mode(
        self, monkeypatch, sample_ohlcv_data, capsys
    ) -> None:
        self._run_offline(
            monkeypatch,
            sample_ohlcv_data,
            5,
            progress_every=10,
            verbose=True,
        )
        out = capsys.readouterr().out
        assert "[Sweep] Abgeschlossen" in out

    def test_verbose_batch_progress_visible(self, monkeypatch, sample_ohlcv_data, capsys) -> None:
        self._run_offline(
            monkeypatch,
            sample_ohlcv_data,
            15,
            progress_every=10,
            verbose=True,
        )
        out = capsys.readouterr().out
        assert "[10/15]" in out
        assert "[15/15]" in out
        assert "[1/15]" not in out

    def test_warning_visible_immediately(self, caplog) -> None:
        from src.sweeps.engine import logger as sweep_logger

        with caplog.at_level(logging.WARNING, logger=sweep_logger.name):
            sweep_logger.warning("phase20-batch-warning-check")
        assert any("phase20-batch-warning-check" in r.message for r in caplog.records)

    def test_error_visible_immediately(self, caplog) -> None:
        from src.sweeps.engine import logger as sweep_logger

        with caplog.at_level(logging.ERROR, logger=sweep_logger.name):
            sweep_logger.error("phase20-batch-error-check")
        assert any("phase20-batch-error-check" in r.message for r in caplog.records)

    def test_exception_propagates_without_false_completion(
        self, monkeypatch, sample_ohlcv_data, capsys
    ) -> None:
        from src.sweeps import SweepEngine

        engine = SweepEngine(verbose=True, progress_every=2)

        def _diag_abort(i, params, stats, success, error, result):
            if i == 3:
                raise RuntimeError("phase20-abort")

        self._mock_run_single(engine, monkeypatch)
        config = self._config_with_n(5)
        with pytest.raises(RuntimeError, match="phase20-abort"):
            engine.run_sweep(
                config,
                data=sample_ohlcv_data,
                skip_registry=True,
                diagnostics_callback=_diag_abort,
            )
        out = capsys.readouterr().out
        assert "[Sweep] Abgeschlossen" not in out

    def test_result_order_and_values_unchanged(self, monkeypatch, sample_ohlcv_data) -> None:
        _, summary_default = self._run_offline(
            monkeypatch, sample_ohlcv_data, 8, progress_every=1, verbose=True
        )
        _, summary_batched = self._run_offline(
            monkeypatch, sample_ohlcv_data, 8, progress_every=4, verbose=True
        )
        assert [r.params for r in summary_default.results] == [
            r.params for r in summary_batched.results
        ]
        assert [r.stats for r in summary_default.results] == [
            r.stats for r in summary_batched.results
        ]

    def test_invalid_progress_every_rejected(self) -> None:
        from src.sweeps import SweepEngine

        with pytest.raises(ValueError, match="progress_every must be positive"):
            SweepEngine(progress_every=0)
        with pytest.raises(ValueError, match="progress_every must be positive"):
            SweepEngine(progress_every=-3)

    def test_should_emit_batch_progress_helper(self) -> None:
        from src.sweeps.engine import _should_emit_batch_progress

        assert _should_emit_batch_progress(0, 0, 10) is False
        assert _should_emit_batch_progress(10, 20, 10) is True
        assert _should_emit_batch_progress(20, 20, 10) is True
        assert _should_emit_batch_progress(25, 25, 10) is True
        assert _should_emit_batch_progress(15, 25, 10) is False
