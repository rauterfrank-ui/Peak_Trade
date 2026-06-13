"""
demo_execution_backtest: canonical load_strategy() migration (offline, fail-closed).
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import scripts.demo_execution_backtest as demo_script
from scripts.demo_execution_backtest import (
    DEMO_SUPPORTED_STRATEGY_NAMES,
    generate_sample_data,
    get_default_strategy_params,
    get_strategy_fn,
)


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
    df = generate_sample_data(symbol="BTC/EUR", bars=80)
    params = get_default_strategy_params("breakout")
    signals = fn(df, params)
    assert isinstance(signals, pd.Series)
    assert len(signals) == len(df)


def test_strategy_params_passed_to_signal_fn() -> None:
    df = generate_sample_data(symbol="BTC/EUR", bars=80)
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
    df = generate_sample_data(symbol="BTC/EUR", bars=80)
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
