"""
run_momentum_realistic: canonical load_strategy() and load_ohlcv_data reuse (offline, fail-closed).
"""

from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import scripts.run_momentum_realistic as momentum_script

TARGET_SCRIPT = project_root / "scripts/run_momentum_realistic.py"
MOMENTUM_KEY = "momentum_1h"
DATA_LOADER_OWNER = "scripts/run_backtest.py:load_ohlcv_data"
FORBIDDEN_LOCAL_LOADER_DEFS = frozenset(
    {"load_ohlcv_data", "generate_dummy_ohlcv", "create_dummy_data", "load_data_from_file"}
)
MOMENTUM_N_BARS_DEFAULT = 300


def _read_source() -> str:
    return TARGET_SCRIPT.read_text(encoding="utf-8")


def _local_function_defs() -> set[str]:
    tree = ast.parse(_read_source())
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
    }
    result.trades = []
    return result


def test_module_imports_without_main_side_effects() -> None:
    with patch.object(momentum_script, "main") as main_mock:
        importlib.reload(momentum_script)
    main_mock.assert_not_called()


def test_source_has_no_direct_momentum_module_import() -> None:
    tree = ast.parse(_read_source())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "src.strategies.momentum":
            pytest.fail("direct momentum module import remains")


def test_source_has_no_strategy_registry_import_or_assignment() -> None:
    tree = ast.parse(_read_source())
    imported = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "src.strategies"
        for alias in node.names
    }
    assert "STRATEGY_REGISTRY" not in imported
    assigned_names = {
        node.targets[0].id
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    }
    assert "STRATEGY_REGISTRY" not in assigned_names


def test_source_has_no_direct_strategy_registry_subscript_access() -> None:
    assert "STRATEGY_REGISTRY[" not in _read_source()


def test_source_uses_load_strategy_and_momentum_key() -> None:
    source = _read_source()
    assert "load_strategy" in source
    assert MOMENTUM_KEY in source
    assert "MOMENTUM_STRATEGY_KEY" in source


def test_strategy_module_delegates_to_load_strategy() -> None:
    fake_module = ModuleType("src.strategies.momentum")
    fake_module.get_strategy_description = MagicMock(return_value="desc")
    fake_callable = MagicMock(__module__="src.strategies.momentum")

    with patch.object(momentum_script, "load_strategy", return_value=fake_callable) as load_mock:
        with patch.object(
            momentum_script.importlib, "import_module", return_value=fake_module
        ) as import_mock:
            mod = momentum_script._strategy_module(MOMENTUM_KEY)

    load_mock.assert_called_once_with(MOMENTUM_KEY)
    import_mock.assert_called_once_with("src.strategies.momentum")
    assert mod is fake_module


def test_strategy_module_resolver_returns_momentum_module() -> None:
    mod = momentum_script._strategy_module(MOMENTUM_KEY)
    assert mod.__name__ == "src.strategies.momentum"
    assert hasattr(mod, "get_strategy_description")


def test_get_strategy_description_equivalence_via_load_strategy_module() -> None:
    from src.strategies.momentum import get_strategy_description as direct

    params = {
        "lookback_period": 20,
        "entry_threshold": 0.02,
        "exit_threshold": -0.01,
        "stop_pct": 0.025,
    }
    assert momentum_script._strategy_module(MOMENTUM_KEY).get_strategy_description(
        params
    ) == direct(params)


def test_load_strategy_momentum_key_resolves() -> None:
    from src.strategies import load_strategy

    assert callable(load_strategy(MOMENTUM_KEY))


def test_unknown_strategy_fails_closed_via_load_strategy() -> None:
    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        momentum_script._strategy_module("definitely_not_a_strategy_xyz")


def test_unknown_strategy_fails_closed() -> None:
    from src.strategies import load_strategy

    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("definitely_not_a_strategy_xyz")


def test_main_call_site_uses_strategy_module_with_momentum_key() -> None:
    tree = ast.parse(_read_source())
    found = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "get_strategy_description":
            parent_call = func.value
            if (
                isinstance(parent_call, ast.Call)
                and isinstance(parent_call.func, ast.Name)
                and parent_call.func.id == "_strategy_module"
                and len(parent_call.args) == 1
                and isinstance(parent_call.args[0], ast.Name)
                and parent_call.args[0].id == "MOMENTUM_STRATEGY_KEY"
            ):
                found = True
    assert found


def test_import_smoke_no_main_execution() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import scripts.run_momentum_realistic"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_source_has_no_local_loader_or_dummy_definitions() -> None:
    local_defs = _local_function_defs()
    assert FORBIDDEN_LOCAL_LOADER_DEFS.isdisjoint(local_defs)


def test_source_imports_canonical_data_loader() -> None:
    source = _read_source()
    assert "load_ohlcv_data" in source
    assert "scripts.run_backtest" in source


def test_load_ohlcv_data_import_identity_is_canonical_owner() -> None:
    import scripts.run_backtest as run_backtest_script

    assert momentum_script.load_ohlcv_data is run_backtest_script.load_ohlcv_data


def test_main_forwards_dummy_path_to_canonical_loader() -> None:
    captured: dict[str, object] = {}
    sample_df = _sample_ohlcv(MOMENTUM_N_BARS_DEFAULT)

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

    cfg = MagicMock()
    cfg.backtest.initial_cash = 10000.0
    cfg.risk.risk_per_trade = 0.01
    cfg.risk.max_position_size = 0.25
    strategy_params = {
        "lookback_period": 20,
        "entry_threshold": 0.02,
        "exit_threshold": -0.01,
        "stop_pct": 0.025,
    }
    fake_module = ModuleType("src.strategies.momentum")
    fake_module.get_strategy_description = MagicMock(return_value="desc")
    signal_fn = MagicMock()
    mock_engine = MagicMock()
    mock_engine.run_realistic.return_value = _mock_backtest_result()

    with (
        patch.object(momentum_script, "get_config", return_value=cfg),
        patch.object(momentum_script, "get_strategy_cfg", return_value=strategy_params),
        patch.object(momentum_script, "load_ohlcv_data", side_effect=capture_loader),
        patch.object(momentum_script, "load_strategy", return_value=signal_fn),
        patch.object(momentum_script, "_strategy_module", return_value=fake_module),
        patch.object(momentum_script, "BacktestEngine", return_value=mock_engine),
        patch.object(momentum_script, "validate_for_live_trading", return_value=(True, [])),
    ):
        momentum_script.main()

    assert captured == {
        "data_file": None,
        "start_date": None,
        "end_date": None,
        "n_bars": MOMENTUM_N_BARS_DEFAULT,
        "verbose": False,
    }
