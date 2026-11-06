"""
Legacy demo/research scripts: canonical load_strategy() migration (offline, fail-closed).
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

TARGET_SCRIPTS: dict[str, Path] = {
    "run_simple_backtest": project_root / "scripts/run_simple_backtest.py",
    "demo_portfolio_backtest": project_root / "scripts/demo_portfolio_backtest.py",
    "run_momentum_realistic": project_root / "scripts/run_momentum_realistic.py",
}

MA_CROSSOVER_KEY = "ma_crossover"
MOMENTUM_KEY = "momentum_1h"
DATA_LOADER_OWNER = "scripts/run_backtest.py:load_ohlcv_data"
FORBIDDEN_LOCAL_LOADER_DEFS = frozenset(
    {"load_ohlcv_data", "generate_dummy_ohlcv", "create_dummy_data", "create_test_data"}
)
RUN_SIMPLE_BACKTEST_N_BARS = 200
RUN_SIMPLE_BACKTEST_RISK_SEMANTICS_MARKERS = (
    "BacktestEngine",
    "RiskLimits",
    "RiskLimitsConfig",
    "PositionSizer",
    "PositionSizerConfig",
    "run_realistic",
    'cfg["risk"]["position_sizing_method"]',
    "max_drawdown_pct=cfg",
    "max_position_pct=cfg",
    "daily_loss_limit_pct=cfg",
    "get_strategy_config",
)
FORBIDDEN_DIRECT_IMPORTS = (
    "from src.strategies.ma_crossover import generate_signals",
    "from src.strategies.momentum import generate_signals",
    "ma_crossover.generate_signals",
    "momentum.generate_signals",
)


def _read_source(name: str) -> str:
    return TARGET_SCRIPTS[name].read_text(encoding="utf-8")


def _sample_ohlcv(n: int = 80) -> pd.DataFrame:
    np.random.seed(42)
    index = pd.date_range("2024-01-01", periods=n, freq="h")
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


def _local_function_defs(name: str) -> set[str]:
    tree = ast.parse(_read_source(name))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_run_simple_backtest_source_has_no_local_loader_definitions() -> None:
    local_defs = _local_function_defs("run_simple_backtest")
    assert FORBIDDEN_LOCAL_LOADER_DEFS.isdisjoint(local_defs)


def test_run_simple_backtest_source_imports_canonical_data_loader() -> None:
    source = _read_source("run_simple_backtest")
    assert "load_ohlcv_data" in source
    assert "scripts.run_backtest" in source


def test_run_simple_backtest_load_ohlcv_data_import_identity_is_canonical_owner() -> None:
    import scripts.run_backtest as run_backtest_script
    import scripts.run_simple_backtest as simple_script

    source = _read_source("run_simple_backtest")
    assert "from scripts.run_backtest import load_ohlcv_data" in source
    assert "load_ohlcv_data" not in _local_function_defs("run_simple_backtest")
    assert simple_script.load_ohlcv_data is run_backtest_script.load_ohlcv_data


def test_main_wires_canonical_loader_with_n_bars_200() -> None:
    import scripts.run_simple_backtest as simple_script

    captured: dict[str, object] = {}
    sample_df = _sample_ohlcv(RUN_SIMPLE_BACKTEST_N_BARS)
    mock_cfg = {
        "backtest": {"initial_cash": 10000.0, "results_dir": "results"},
        "risk": {
            "risk_per_trade": 0.02,
            "max_position_size": 0.5,
            "max_drawdown_pct": 30.0,
            "daily_loss_limit_pct": 10.0,
            "max_position_pct": 5.0,
            "min_position_value": 100.0,
            "position_sizing_method": "fixed_fractional",
        },
    }
    mock_engine = MagicMock()
    mock_result = MagicMock()
    mock_result.stats = {
        "total_return": 0.01,
        "max_drawdown": -0.02,
        "sharpe": 1.0,
        "total_trades": 1,
        "win_rate": 1.0,
        "profit_factor": 2.0,
    }
    mock_result.blocked_trades = 0
    mock_result.equity_curve = pd.Series([10000.0, 10100.0])
    mock_result.trades = []
    mock_engine.run_realistic.return_value = mock_result

    def capture_loader(data_file, start_date, end_date, n_bars, verbose=False):
        captured.update(
            {
                "data_file": data_file,
                "start_date": start_date,
                "end_date": end_date,
                "n_bars": n_bars,
                "verbose": verbose,
            }
        )
        return sample_df

    with (
        patch.object(simple_script, "load_ohlcv_data", side_effect=capture_loader),
        patch.object(simple_script, "load_config", return_value=mock_cfg),
        patch.object(simple_script, "list_strategies", return_value=["ma_crossover"]),
        patch.object(
            simple_script,
            "get_strategy_config",
            return_value={"fast_period": 10, "slow_period": 30, "stop_pct": 0.02},
        ),
        patch.object(simple_script, "BacktestEngine", return_value=mock_engine),
        patch.object(simple_script, "load_strategy", return_value=MagicMock()),
    ):
        simple_script.main()

    assert captured == {
        "data_file": None,
        "start_date": None,
        "end_date": None,
        "n_bars": RUN_SIMPLE_BACKTEST_N_BARS,
        "verbose": False,
    }
    mock_engine.run_realistic.assert_called_once()


def test_run_simple_backtest_risk_semantics_preserved_in_source() -> None:
    source = _read_source("run_simple_backtest")
    for marker in RUN_SIMPLE_BACKTEST_RISK_SEMANTICS_MARKERS:
        assert marker in source, f"missing risk semantics marker: {marker}"
    assert "create_test_data" not in source


@pytest.mark.parametrize(
    "name",
    list(TARGET_SCRIPTS),
)
def test_module_imports_without_main_side_effects(name: str) -> None:
    module = importlib.import_module(f"scripts.{name}")
    with patch.object(module, "main") as main_mock:
        importlib.reload(module)
    main_mock.assert_not_called()


@pytest.mark.parametrize("name", TARGET_SCRIPTS)
def test_source_has_no_direct_generate_signals_imports(name: str) -> None:
    source = _read_source(name)
    for forbidden in FORBIDDEN_DIRECT_IMPORTS:
        assert forbidden not in source


@pytest.mark.parametrize("name", TARGET_SCRIPTS)
def test_source_uses_load_strategy(name: str) -> None:
    assert "load_strategy" in _read_source(name)


@pytest.mark.parametrize("name", TARGET_SCRIPTS)
def test_source_has_no_strategy_map(name: str) -> None:
    assert "strategy_map" not in _read_source(name)


@pytest.mark.parametrize("name", TARGET_SCRIPTS)
def test_source_has_no_parallel_strategy_registry(name: str) -> None:
    tree = ast.parse(_read_source(name))
    assigned_names = {
        node.targets[0].id
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    }
    assert "STRATEGY_REGISTRY" not in assigned_names


def test_ma_crossover_scripts_use_canonical_registry_key() -> None:
    ma_scripts = (
        "run_simple_backtest",
        "demo_portfolio_backtest",
    )
    for name in ma_scripts:
        assert MA_CROSSOVER_KEY in _read_source(name)


def test_run_momentum_realistic_uses_momentum_1h_key() -> None:
    source = _read_source("run_momentum_realistic")
    assert MOMENTUM_KEY in source
    assert "MOMENTUM_STRATEGY_KEY" in source


def test_load_strategy_ma_crossover_matches_direct_module_callable() -> None:
    from src.strategies import load_strategy
    from src.strategies.ma_crossover import generate_signals as direct

    assert load_strategy(MA_CROSSOVER_KEY) is direct


def test_load_strategy_momentum_1h_matches_direct_module_callable() -> None:
    from src.strategies import load_strategy
    from src.strategies.momentum import generate_signals as direct

    assert load_strategy(MOMENTUM_KEY) is direct


def test_ma_crossover_signal_output_unchanged_with_defaults() -> None:
    from src.strategies import load_strategy
    from src.strategies.ma_crossover import generate_signals as direct

    df = _sample_ohlcv()
    params = {"fast_period": 10, "slow_period": 30, "stop_pct": 0.02}
    canonical = load_strategy(MA_CROSSOVER_KEY)(df, params)
    legacy = direct(df, params)
    pd.testing.assert_series_equal(canonical, legacy)


def test_momentum_signal_output_unchanged_with_defaults() -> None:
    from src.strategies import load_strategy
    from src.strategies.momentum import generate_signals as direct

    df = _sample_ohlcv()
    params = {
        "lookback_period": 20,
        "entry_threshold": 0.02,
        "exit_threshold": -0.01,
        "stop_pct": 0.025,
    }
    canonical = load_strategy(MOMENTUM_KEY)(df, params)
    legacy = direct(df, params)
    pd.testing.assert_series_equal(canonical, legacy)


def test_unknown_strategy_fails_closed() -> None:
    from src.strategies import load_strategy

    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("definitely_not_a_strategy_xyz")


def test_invalid_ma_crossover_params_fail_closed() -> None:
    from src.strategies import load_strategy

    df = _sample_ohlcv()
    fn = load_strategy(MA_CROSSOVER_KEY)
    invalid_params = {"fast_period": 30, "slow_period": 10, "stop_pct": 0.02}
    with pytest.raises(ValueError, match="fast_window|fast_period"):
        fn(df, invalid_params)


def test_no_silent_strategy_fallback_on_unknown_name() -> None:
    import scripts.demo_portfolio_backtest as demo_script

    with patch.object(demo_script, "load_strategy") as load_mock:
        load_mock.side_effect = ValueError("Unbekannte Strategie 'bad_name'")
        with pytest.raises(ValueError, match="Unbekannte Strategie"):
            demo_script.load_strategy("bad_name")
    load_mock.assert_called_once_with("bad_name")


def test_load_strategy_no_network_calls() -> None:
    from src.strategies import load_strategy

    with patch("urllib.request.urlopen") as urlopen:
        load_strategy(MA_CROSSOVER_KEY)
        load_strategy(MOMENTUM_KEY)
    urlopen.assert_not_called()


def test_demo_portfolio_backtest_cli_help_no_run() -> None:
    import subprocess

    result = subprocess.run(
        [sys.executable, str(TARGET_SCRIPTS["demo_portfolio_backtest"]), "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Portfolio" in result.stdout
