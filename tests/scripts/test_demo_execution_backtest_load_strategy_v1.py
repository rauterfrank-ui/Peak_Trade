"""
demo_execution_backtest: canonical load_strategy() migration (offline, fail-closed).
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import scripts.demo_execution_backtest as demo_script
from scripts.demo_execution_backtest import (
    DEMO_SUPPORTED_STRATEGY_NAMES,
    get_default_strategy_params,
    get_strategy_fn,
)
from scripts.run_backtest import load_ohlcv_data

DEMO_EXECUTION_BACKTEST_SCRIPT = project_root / "scripts/demo_execution_backtest.py"
FORBIDDEN_LOCAL_LOADER_DEFS = frozenset(
    {
        "load_ohlcv_data",
        "generate_dummy_ohlcv",
        "create_dummy_data",
        "create_test_data",
        "generate_sample_data",
    }
)
DEMO_EXECUTION_BACKTEST_DEFAULT_N_BARS = 200
EXECUTION_SEMANTICS_MARKERS = (
    "BacktestEngine",
    "run_backtest",
    "run_realistic",
    "use_execution_pipeline",
    "fee_bps",
    "slippage_bps",
    "log_executions",
    "from_execution_results",
    '"stop_pct": 0.02',
)


def _local_function_defs() -> set[str]:
    tree = ast.parse(DEMO_EXECUTION_BACKTEST_SCRIPT.read_text(encoding="utf-8"))
    return {
        node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_module_imports_without_main_side_effects() -> None:
    with patch.object(demo_script, "main") as main_mock:
        importlib.reload(demo_script)
    main_mock.assert_not_called()


def test_source_has_no_strategy_map() -> None:
    source = Path(demo_script.__file__).read_text(encoding="utf-8")
    assert "strategy_map" not in source


def test_source_has_no_parallel_strategy_registry() -> None:
    source = Path(demo_script.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    assigned_names = {
        node.targets[0].id
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    }
    assert "STRATEGY_REGISTRY" not in assigned_names
    assert "load_strategy" in source


def test_get_strategy_fn_delegates_to_load_strategy() -> None:
    with patch.object(
        demo_script, "load_strategy", return_value=lambda df, p: df["close"] * 0
    ) as load_mock:
        fn = get_strategy_fn("ma_crossover")
    load_mock.assert_called_once_with("ma_crossover")
    assert callable(fn)


def test_supported_demo_strategies_resolve_via_load_strategy() -> None:
    for name in DEMO_SUPPORTED_STRATEGY_NAMES:
        fn = get_strategy_fn(name)
        assert callable(fn)


def test_breakout_canonical_name_resolves() -> None:
    fn = get_strategy_fn("breakout")
    df = load_ohlcv_data(None, None, None, n_bars=80)
    params = get_default_strategy_params("breakout")
    signals = fn(df, params)
    assert isinstance(signals, pd.Series)
    assert len(signals) == len(df)


def test_strategy_params_passed_to_signal_fn() -> None:
    df = load_ohlcv_data(None, None, None, n_bars=80)
    fn = get_strategy_fn("ma_crossover")
    params = get_default_strategy_params("ma_crossover")
    params["fast_period"] = 5
    params["slow_period"] = 15
    signals = fn(df, params)
    assert isinstance(signals, pd.Series)


def test_unknown_strategy_fails_closed() -> None:
    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        get_strategy_fn("definitely_not_a_strategy_xyz")


def test_unknown_strategy_defaults_fail_closed() -> None:
    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        get_default_strategy_params("definitely_not_a_strategy_xyz")


def test_invalid_strategy_params_fail_closed() -> None:
    df = load_ohlcv_data(None, None, None, n_bars=80)
    fn = get_strategy_fn("macd")
    invalid_params = {
        "fast_ema": 30,
        "slow_ema": 10,
        "signal_ema": 9,
        "stop_pct": 0.02,
    }
    with pytest.raises(ValueError, match="fast_ema"):
        fn(df, invalid_params)


def test_no_silent_strategy_fallback_on_unknown_name() -> None:
    with patch.object(demo_script, "load_strategy") as load_mock:
        load_mock.side_effect = ValueError("Unbekannte Strategie 'bad_name'")
        with pytest.raises(ValueError, match="Unbekannte Strategie"):
            get_strategy_fn("bad_name")
    load_mock.assert_called_once_with("bad_name")


def test_resolve_strategy_no_network_calls() -> None:
    with patch("urllib.request.urlopen") as urlopen:
        get_strategy_fn("ma_crossover")
    urlopen.assert_not_called()


def test_breakout_donchian_is_canonical_registry_key_not_silent_alias_to_breakout() -> None:
    from src.strategies import STRATEGY_REGISTRY
    from src.strategies.breakout import generate_signals as breakout_generate_signals

    fn_donchian = get_strategy_fn("breakout_donchian")
    fn_breakout = get_strategy_fn("breakout")

    assert callable(fn_donchian)
    assert callable(fn_breakout)
    assert fn_breakout is breakout_generate_signals
    assert fn_donchian is not breakout_generate_signals
    assert fn_donchian is not fn_breakout
    assert STRATEGY_REGISTRY["breakout_donchian"] != STRATEGY_REGISTRY["breakout"]


def test_source_has_no_local_loader_definitions() -> None:
    local_defs = _local_function_defs()
    assert FORBIDDEN_LOCAL_LOADER_DEFS.isdisjoint(local_defs)


def test_source_imports_canonical_data_loader() -> None:
    source = DEMO_EXECUTION_BACKTEST_SCRIPT.read_text(encoding="utf-8")
    assert "load_ohlcv_data" in source
    assert "scripts.run_backtest" in source


def test_load_ohlcv_data_import_identity_is_canonical_owner() -> None:
    import scripts.run_backtest as run_backtest_script

    source = DEMO_EXECUTION_BACKTEST_SCRIPT.read_text(encoding="utf-8")
    assert "from scripts.run_backtest import load_ohlcv_data" in source
    assert "load_ohlcv_data" not in _local_function_defs()
    assert demo_script.load_ohlcv_data is run_backtest_script.load_ohlcv_data


def test_main_wires_canonical_loader_with_n_bars_from_cli() -> None:
    captured: dict[str, object] = {}
    sample_df = load_ohlcv_data(None, None, None, n_bars=50)
    mock_result = MagicMock()
    mock_engine = MagicMock()

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
        patch.object(demo_script, "load_ohlcv_data", side_effect=capture_loader),
        patch.object(demo_script, "run_backtest", return_value=(mock_result, mock_engine)),
        patch.object(demo_script, "print_core_stats"),
        patch.object(demo_script, "print_trade_stats"),
    ):
        demo_script.main(["--strategy", "ma_crossover", "--bars", "50"])

    assert captured == {
        "data_file": None,
        "start_date": None,
        "end_date": None,
        "n_bars": 50,
        "verbose": False,
    }


def test_main_wires_canonical_loader_with_default_n_bars_200() -> None:
    captured: dict[str, object] = {}
    sample_df = load_ohlcv_data(None, None, None, n_bars=DEMO_EXECUTION_BACKTEST_DEFAULT_N_BARS)
    mock_result = MagicMock()
    mock_engine = MagicMock()

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
        patch.object(demo_script, "load_ohlcv_data", side_effect=capture_loader),
        patch.object(demo_script, "run_backtest", return_value=(mock_result, mock_engine)),
        patch.object(demo_script, "print_core_stats"),
        patch.object(demo_script, "print_trade_stats"),
    ):
        demo_script.main(["--strategy", "ma_crossover"])

    assert captured["n_bars"] == DEMO_EXECUTION_BACKTEST_DEFAULT_N_BARS


def test_main_wires_start_end_dates_to_canonical_loader() -> None:
    captured: dict[str, object] = {}
    sample_df = load_ohlcv_data(None, None, None, n_bars=100)
    mock_result = MagicMock()
    mock_engine = MagicMock()

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
        patch.object(demo_script, "load_ohlcv_data", side_effect=capture_loader),
        patch.object(demo_script, "run_backtest", return_value=(mock_result, mock_engine)),
        patch.object(demo_script, "print_core_stats"),
        patch.object(demo_script, "print_trade_stats"),
    ):
        demo_script.main(
            [
                "--strategy",
                "ma_crossover",
                "--start",
                "2024-01-01",
                "--end",
                "2024-02-01",
                "--bars",
                "100",
            ]
        )

    assert captured == {
        "data_file": None,
        "start_date": "2024-01-01",
        "end_date": "2024-02-01",
        "n_bars": 100,
        "verbose": False,
    }


def test_execution_semantics_preserved_in_source() -> None:
    source = DEMO_EXECUTION_BACKTEST_SCRIPT.read_text(encoding="utf-8")
    for marker in EXECUTION_SEMANTICS_MARKERS:
        assert marker in source, f"missing execution semantics marker: {marker}"
    assert "generate_sample_data" not in source
