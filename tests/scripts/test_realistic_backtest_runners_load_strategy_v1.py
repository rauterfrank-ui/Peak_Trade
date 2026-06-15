"""
Realistic backtest runners: canonical load_strategy() and load_ohlcv_data reuse (offline, fail-closed).
"""

from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

TARGET_SCRIPTS: dict[str, Path] = {
    "run_ma_realistic": project_root / "scripts/run_ma_realistic.py",
    "run_donchian_realistic": project_root / "scripts/run_donchian_realistic.py",
    "run_rsi_realistic": project_root / "scripts/run_rsi_realistic.py",
}

MA_CROSSOVER_KEY = "ma_crossover"
DONCHIAN_KEY = "breakout_donchian"
RSI_REVERSION_KEY = "rsi_reversion"

FORBIDDEN_CLASS_IMPORTS = (
    "MACrossoverStrategy",
    "DonchianBreakoutStrategy",
    "RsiReversionStrategy",
)

DATA_LOADER_OWNER = "scripts/run_backtest.py:load_ohlcv_data"
FORBIDDEN_LOCAL_LOADER_DEFS = frozenset(
    {"load_ohlcv_data", "generate_dummy_ohlcv", "create_dummy_data", "load_data_from_file"}
)
REALISTIC_RUNNER_N_BARS = 200


def _read_source(name: str) -> str:
    return TARGET_SCRIPTS[name].read_text(encoding="utf-8")


def _local_function_defs(name: str) -> set[str]:
    tree = ast.parse(_read_source(name))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


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


@pytest.mark.parametrize("name", TARGET_SCRIPTS)
def test_module_imports_without_main_side_effects(name: str) -> None:
    module = importlib.import_module(f"scripts.{name}")
    with patch.object(module, "main") as main_mock:
        importlib.reload(module)
    main_mock.assert_not_called()


@pytest.mark.parametrize("name", TARGET_SCRIPTS)
def test_source_has_no_local_loader_or_dummy_definitions(name: str) -> None:
    local_defs = _local_function_defs(name)
    assert FORBIDDEN_LOCAL_LOADER_DEFS.isdisjoint(local_defs)


@pytest.mark.parametrize("name", TARGET_SCRIPTS)
def test_source_imports_canonical_data_loader(name: str) -> None:
    source = _read_source(name)
    assert "load_ohlcv_data" in source
    assert "scripts.run_backtest" in source


@pytest.mark.parametrize("name", TARGET_SCRIPTS)
def test_load_ohlcv_data_import_identity_is_canonical_owner(name: str) -> None:
    import scripts.run_backtest as run_backtest_script

    module = importlib.import_module(f"scripts.{name}")
    assert module.load_ohlcv_data is run_backtest_script.load_ohlcv_data


def _mock_cfg_for_runner(name: str) -> MagicMock:
    cfg = MagicMock()
    if name == "run_ma_realistic":
        cfg.get.side_effect = lambda path, default=None: {
            "backtest.initial_cash": 10000.0,
            "risk.risk_per_trade": 0.01,
            "risk.max_position_size": 0.25,
            "strategy.ma_crossover.fast_window": 20,
            "strategy.ma_crossover.slow_window": 50,
            "strategy.ma_crossover.stop_pct": 0.02,
            "strategy.ma_crossover.price_col": "close",
        }.get(path, default)
    elif name == "run_rsi_realistic":
        cfg.get.side_effect = lambda path, default=None: {
            "backtest.initial_cash": 10000.0,
            "risk.risk_per_trade": 0.01,
            "risk.max_position_size": 0.25,
            "strategy.rsi_reversion.rsi_window": 14,
            "strategy.rsi_reversion.lower": 30.0,
            "strategy.rsi_reversion.upper": 70.0,
            "strategy.rsi_reversion.stop_pct": 0.02,
            "strategy.rsi_reversion.price_col": "close",
        }.get(path, default)
    else:
        cfg.get.side_effect = lambda path, default=None: {
            "backtest.initial_cash": 10000.0,
            "risk.risk_per_trade": 0.01,
            "risk.max_position_size": 0.25,
            "strategy.breakout_donchian.lookback": 20,
            "strategy.breakout_donchian.stop_pct": 0.02,
            "strategy.breakout_donchian.price_col": "close",
        }.get(path, default)
    return cfg


def _mock_backtest_result() -> MagicMock:
    result = MagicMock()
    result.equity_curve = pd.Series([10000.0, 10100.0])
    result.stats = {
        "total_return": 0.01,
        "max_drawdown": -0.02,
        "sharpe": 1.0,
        "total_trades": 1,
        "win_rate": 1.0,
        "profit_factor": 2.0,
        "blocked_trades": 0,
    }
    result.trades = None
    result.blocked_trades = 0
    return result


@pytest.mark.parametrize("name", TARGET_SCRIPTS)
def test_main_forwards_dummy_path_to_canonical_loader(name: str) -> None:
    module = importlib.import_module(f"scripts.{name}")
    captured: dict[str, object] = {}
    sample_df = _sample_ohlcv(REALISTIC_RUNNER_N_BARS)

    def capture_loader(
        data_file,
        start_date,
        end_date,
        n_bars,
        verbose=False,
    ):
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

    signal_fn = MagicMock(return_value=pd.Series(0, index=sample_df.index))
    mock_engine = MagicMock()
    mock_engine.run_realistic.return_value = _mock_backtest_result()

    with (
        patch.object(module, "load_config", return_value=_mock_cfg_for_runner(name)),
        patch.object(module, "load_ohlcv_data", side_effect=capture_loader),
        patch.object(module, "load_strategy", return_value=signal_fn),
        patch.object(module, "build_position_sizer_from_config", return_value=MagicMock()),
        patch.object(module, "build_risk_manager_from_config", return_value=MagicMock()),
        patch.object(module, "BacktestEngine", return_value=mock_engine),
    ):
        module.main()

    assert captured == {
        "data_file": None,
        "start_date": None,
        "end_date": None,
        "n_bars": REALISTIC_RUNNER_N_BARS,
        "verbose": False,
    }


@pytest.mark.parametrize("name", TARGET_SCRIPTS)
def test_source_has_no_direct_strategy_class_imports(name: str) -> None:
    source = _read_source(name)
    for forbidden in FORBIDDEN_CLASS_IMPORTS:
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


@pytest.mark.parametrize("name", TARGET_SCRIPTS)
def test_source_has_no_broad_except_soft_return(name: str) -> None:
    source = _read_source(name)
    assert "except Exception" not in source


def test_run_ma_realistic_uses_ma_crossover_key() -> None:
    source = _read_source("run_ma_realistic")
    assert MA_CROSSOVER_KEY in source
    assert "MA_CROSSOVER_STRATEGY_KEY" in source


def test_run_donchian_realistic_uses_breakout_donchian_key() -> None:
    source = _read_source("run_donchian_realistic")
    assert DONCHIAN_KEY in source
    assert "DONCHIAN_STRATEGY_KEY" in source


def test_run_rsi_realistic_uses_rsi_reversion_key() -> None:
    source = _read_source("run_rsi_realistic")
    assert RSI_REVERSION_KEY in source
    assert "RSI_REVERSION_STRATEGY_KEY" in source


def test_load_strategy_ma_crossover_matches_direct_module_callable() -> None:
    from src.strategies import load_strategy
    from src.strategies.ma_crossover import generate_signals as direct

    assert load_strategy(MA_CROSSOVER_KEY) is direct


def test_load_strategy_rsi_reversion_matches_direct_module_callable() -> None:
    from src.strategies import load_strategy
    from src.strategies.rsi_reversion import generate_signals as direct

    assert load_strategy(RSI_REVERSION_KEY) is direct


def test_load_strategy_breakout_donchian_matches_oop_class_output() -> None:
    from src.strategies import load_strategy
    from src.strategies.breakout_donchian import DonchianBreakoutStrategy

    df = _sample_ohlcv()
    params = {"lookback": 20, "price_col": "close", "stop_pct": 0.02}
    canonical = load_strategy(DONCHIAN_KEY)(df, params)
    legacy = DonchianBreakoutStrategy(
        config={"lookback": 20, "price_col": "close"}
    ).generate_signals(df)
    pd.testing.assert_series_equal(canonical, legacy)


def test_ma_crossover_signal_output_unchanged_with_defaults() -> None:
    from src.strategies import load_strategy
    from src.strategies.ma_crossover import generate_signals as direct

    df = _sample_ohlcv()
    params = {"fast_period": 10, "slow_period": 30, "stop_pct": 0.02}
    canonical = load_strategy(MA_CROSSOVER_KEY)(df, params)
    legacy = direct(df, params)
    pd.testing.assert_series_equal(canonical, legacy)


def test_rsi_reversion_signal_output_unchanged_with_defaults() -> None:
    from src.strategies import load_strategy
    from src.strategies.rsi_reversion import generate_signals as direct

    df = _sample_ohlcv()
    params = {"rsi_window": 14, "lower": 30.0, "upper": 70.0, "stop_pct": 0.02}
    canonical = load_strategy(RSI_REVERSION_KEY)(df, params)
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


def test_run_ma_realistic_strategy_config_error_exits_nonzero() -> None:
    import scripts.run_ma_realistic as ma_script

    cfg = MagicMock()
    cfg.get.side_effect = lambda path, default=None: {
        "backtest.initial_cash": 10000.0,
        "risk.risk_per_trade": 0.01,
        "risk.max_position_size": 0.25,
        "strategy.ma_crossover.fast_window": None,
        "strategy.ma_crossover.slow_window": None,
    }.get(path, default)

    with patch.object(ma_script, "load_config", return_value=cfg):
        with patch.object(sys, "exit", side_effect=SystemExit) as exit_mock:
            with pytest.raises(SystemExit):
                ma_script.main()
    exit_mock.assert_called_once_with(1)


def test_no_silent_strategy_fallback_on_unknown_name() -> None:
    from src.strategies import load_strategy

    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("bad_realistic_runner_strategy_name")


def test_load_strategy_no_network_calls() -> None:
    from src.strategies import load_strategy

    with patch("urllib.request.urlopen") as urlopen:
        load_strategy(MA_CROSSOVER_KEY)
        load_strategy(DONCHIAN_KEY)
        load_strategy(RSI_REVERSION_KEY)
    urlopen.assert_not_called()


def test_import_smoke_no_main_execution() -> None:
    for name in TARGET_SCRIPTS:
        result = subprocess.run(
            [sys.executable, "-c", f"import scripts.{name}"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
