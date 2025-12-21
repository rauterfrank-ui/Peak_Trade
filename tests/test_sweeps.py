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

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path


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
