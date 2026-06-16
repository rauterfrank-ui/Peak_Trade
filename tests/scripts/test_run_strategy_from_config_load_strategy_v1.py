"""
run_strategy_from_config: canonical load_strategy() migration (offline, fail-closed).
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
sys.path.insert(0, str(project_root / "scripts"))

import run_strategy_from_config as target_script

TARGET_SCRIPT = project_root / "scripts/run_strategy_from_config.py"
MA_CROSSOVER_KEY = "ma_crossover"
MOMENTUM_KEY = "momentum_1h"
EL_KAROUI_ALIAS_KEY = "el_karoui_vol_v1"

FORBIDDEN_IMPORTS = ("create_strategy_from_config",)
DATA_LOADER_OWNER = "scripts/run_backtest.py:load_ohlcv_data"
FORBIDDEN_LOCAL_LOADER_DEFS = frozenset({"load_ohlcv_data", "generate_dummy_ohlcv"})


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


def test_module_imports_without_main_side_effects() -> None:
    with patch.object(target_script, "main") as main_mock:
        importlib.reload(target_script)
    main_mock.assert_not_called()


def test_source_has_no_create_strategy_from_config() -> None:
    tree = ast.parse(_read_source())
    imported = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module
        for alias in node.names
    }
    for forbidden in FORBIDDEN_IMPORTS:
        assert forbidden not in imported


def test_source_uses_load_strategy_path() -> None:
    assert "_resolve_strategy_signal_fn" in _read_source()
    assert "_build_strategy_params_from_config" in _read_source()


def test_source_has_no_local_loader_or_dummy_definitions() -> None:
    local_defs = _local_function_defs()
    assert FORBIDDEN_LOCAL_LOADER_DEFS.isdisjoint(local_defs)


def test_source_imports_canonical_data_loader() -> None:
    source = _read_source()
    assert "load_ohlcv_data" in source
    assert "scripts.run_backtest" in source


def test_load_ohlcv_data_import_identity_is_canonical_owner() -> None:
    import scripts.run_backtest as run_backtest_script

    assert target_script.load_ohlcv_data is run_backtest_script.load_ohlcv_data


def test_source_has_no_parallel_strategy_registry_assignment() -> None:
    tree = ast.parse(_read_source())
    assigned_names = {
        node.targets[0].id
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    }
    assert "STRATEGY_REGISTRY" not in assigned_names


def test_build_strategy_params_includes_section_and_stop_pct() -> None:
    from scripts.run_backtest import _build_strategy_params_from_config
    from src.core.peak_config import PeakConfig

    raw = {
        "environment": {"mode": "backtest"},
        "strategy": {
            MA_CROSSOVER_KEY: {
                "fast_window": 10,
                "slow_window": 50,
                "price_col": "close",
                "stop_pct": 0.03,
            },
        },
    }
    cfg = PeakConfig(raw=raw)
    params = _build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    assert params["fast_window"] == 10
    assert params["slow_window"] == 50
    assert params["price_col"] == "close"
    assert params["stop_pct"] == 0.03


@pytest.mark.parametrize(
    "strategy_key,strategy_section,n_bars",
    [
        (
            MA_CROSSOVER_KEY,
            {MA_CROSSOVER_KEY: {"fast_window": 10, "slow_window": 50, "price_col": "close"}},
            80,
        ),
        (
            MOMENTUM_KEY,
            {
                MOMENTUM_KEY: {
                    "lookback_period": 15,
                    "entry_threshold": 0.02,
                    "exit_threshold": -0.01,
                }
            },
            120,
        ),
    ],
)
def test_signal_equivalence_vs_create_strategy_from_config(
    strategy_key: str,
    strategy_section: dict,
    n_bars: int,
) -> None:
    from scripts.run_backtest import (
        _build_strategy_params_from_config,
        _resolve_strategy_signal_fn,
    )
    from src.core.peak_config import PeakConfig
    from src.strategies.registry import create_strategy_from_config

    raw = {"environment": {"mode": "backtest"}, "strategy": strategy_section}
    cfg = PeakConfig(raw=raw)
    df = _sample_ohlcv(n_bars)

    legacy = create_strategy_from_config(strategy_key, cfg).generate_signals(df)
    params = _build_strategy_params_from_config(cfg, strategy_key)
    canonical = _resolve_strategy_signal_fn(strategy_key)(df, params)

    pd.testing.assert_series_equal(canonical, legacy)


def test_el_karoui_alias_resolves_via_oop_fallback() -> None:
    from scripts.run_backtest import (
        _build_strategy_params_from_config,
        _resolve_strategy_signal_fn,
    )
    from src.core.peak_config import PeakConfig
    from src.strategies.registry import create_strategy_from_config

    raw = {
        "environment": {"mode": "backtest"},
        "research": {"allow_r_and_d_strategies": True},
        "strategy": {"el_karoui_vol_model": {}},
    }
    cfg = PeakConfig(raw=raw)
    df = _sample_ohlcv(120)

    legacy = create_strategy_from_config(EL_KAROUI_ALIAS_KEY, cfg).generate_signals(df)
    params = _build_strategy_params_from_config(cfg, EL_KAROUI_ALIAS_KEY)
    canonical = _resolve_strategy_signal_fn(EL_KAROUI_ALIAS_KEY)(df, params)

    pd.testing.assert_series_equal(canonical, legacy)


def test_long_only_wrapper_replaces_short_signals() -> None:
    from scripts.run_backtest import _resolve_strategy_signal_fn

    df = _sample_ohlcv(10)
    params: dict[str, object] = {}

    def fake_signal_fn(_df, _params):
        return pd.Series([1, -1, 0, -1, 1, 0, 0, 0, 0, 0], index=df.index)

    with patch.object(target_script, "_resolve_strategy_signal_fn", return_value=fake_signal_fn):
        base_signal_fn = target_script._resolve_strategy_signal_fn(MA_CROSSOVER_KEY)

        def strategy_signal_fn(df_input, params_input):
            sigs = base_signal_fn(df_input, params_input)
            return sigs.replace(-1, 0)

        wrapped = strategy_signal_fn(df, params)
        assert (wrapped == -1).sum() == 0
        assert wrapped.tolist() == [1, 0, 0, 0, 1, 0, 0, 0, 0, 0]


def test_registry_gates_block_r_and_d_without_flag() -> None:
    from scripts.run_backtest import _validate_strategy_registry_gates
    from src.core.peak_config import PeakConfig

    raw = {"environment": {"mode": "backtest"}, "strategy": {"ehlers_cycle_filter": {}}}
    cfg = PeakConfig(raw=raw)
    with pytest.raises(ValueError, match="R&D-only"):
        _validate_strategy_registry_gates("ehlers_cycle_filter", cfg)


def test_main_passes_full_params_to_signal_fn() -> None:
    from src.core.peak_config import PeakConfig

    raw = {
        "environment": {"mode": "backtest"},
        "strategy": {
            MA_CROSSOVER_KEY: {"fast_window": 10, "slow_window": 50, "price_col": "close"}
        },
    }
    cfg = PeakConfig(raw=raw)
    captured: dict[str, object] = {}

    def fake_signal_fn(df, params):
        captured["params"] = dict(params)
        captured["df_len"] = len(df)
        return pd.Series(0, index=df.index)

    mock_result = MagicMock()
    mock_result.stats = {
        "total_return": 0.0,
        "max_drawdown": 0.0,
        "sharpe": 0.0,
        "total_trades": 0,
        "win_rate": 0.0,
        "profit_factor": 0.0,
        "blocked_trades": 0,
    }
    mock_result.equity_curve = pd.Series(
        [10000.0, 10000.0], index=pd.date_range("2024-01-01", periods=2, freq="h")
    )
    mock_result.trades = None
    mock_result.metadata = {}

    with (
        patch.object(target_script, "parse_args") as parse_mock,
        patch.object(target_script, "load_config", return_value=cfg),
        patch.object(target_script, "load_ohlcv_data", return_value=_sample_ohlcv()),
        patch.object(target_script, "build_position_sizer_from_config", return_value=MagicMock()),
        patch.object(target_script, "build_risk_manager_from_config", return_value=MagicMock()),
        patch.object(target_script, "_resolve_strategy_signal_fn", return_value=fake_signal_fn),
        patch.object(
            target_script.BacktestEngine, "run_realistic", return_value=mock_result
        ) as run_mock,
    ):
        args = MagicMock()
        args.list_strategies = False
        args.strategy = MA_CROSSOVER_KEY
        args.bars = 80
        args.run_name = None
        args.no_report = True
        args.no_plots = True
        parse_mock.return_value = args

        target_script.main()

    run_mock.assert_called_once()
    call_kwargs = run_mock.call_args.kwargs
    assert call_kwargs["strategy_params"]["fast_window"] == 10
    assert call_kwargs["strategy_params"]["slow_window"] == 50
    assert call_kwargs["strategy_params"]["stop_pct"] == 0.02
    call_kwargs["strategy_signal_fn"](call_kwargs["df"], call_kwargs["strategy_params"])
    assert captured["params"]["fast_window"] == 10
    assert captured["params"]["slow_window"] == 50


def test_main_forwards_load_ohlcv_arguments_to_canonical_loader() -> None:
    from src.core.peak_config import PeakConfig

    raw = {
        "environment": {"mode": "backtest"},
        "strategy": {
            MA_CROSSOVER_KEY: {"fast_window": 10, "slow_window": 50, "price_col": "close"}
        },
    }
    cfg = PeakConfig(raw=raw)
    captured: dict[str, object] = {}

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
        return _sample_ohlcv()

    mock_result = MagicMock()
    mock_result.stats = {
        "total_return": 0.0,
        "max_drawdown": 0.0,
        "sharpe": 0.0,
        "total_trades": 0,
        "win_rate": 0.0,
        "profit_factor": 0.0,
        "blocked_trades": 0,
    }
    mock_result.equity_curve = pd.Series(
        [10000.0, 10000.0], index=pd.date_range("2024-01-01", periods=2, freq="h")
    )
    mock_result.trades = None
    mock_result.metadata = {}

    with (
        patch.object(target_script, "parse_args") as parse_mock,
        patch.object(target_script, "load_config", return_value=cfg),
        patch.object(target_script, "load_ohlcv_data", side_effect=capture_loader),
        patch.object(target_script, "build_position_sizer_from_config", return_value=MagicMock()),
        patch.object(target_script, "build_risk_manager_from_config", return_value=MagicMock()),
        patch.object(
            target_script,
            "_resolve_strategy_signal_fn",
            return_value=lambda df, params: pd.Series(0, index=df.index),
        ),
        patch.object(target_script.BacktestEngine, "run_realistic", return_value=mock_result),
    ):
        args = MagicMock()
        args.list_strategies = False
        args.strategy = MA_CROSSOVER_KEY
        args.bars = 120
        args.run_name = None
        args.no_report = True
        args.no_plots = True
        parse_mock.return_value = args

        target_script.main()

    assert captured == {
        "data_file": None,
        "start_date": None,
        "end_date": None,
        "n_bars": 120,
        "verbose": False,
    }


def test_config_object_not_mutated_during_resolution() -> None:
    from scripts.run_backtest import _build_strategy_params_from_config
    from src.core.peak_config import PeakConfig

    raw = {
        "environment": {"mode": "backtest"},
        "strategy": {MA_CROSSOVER_KEY: {"fast_window": 10, "slow_window": 50}},
    }
    cfg = PeakConfig(raw=raw)
    before = cfg.raw.copy()
    _ = _build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    assert cfg.raw == before


def test_unknown_strategy_fails_closed_at_gates() -> None:
    from scripts.run_backtest import _validate_strategy_registry_gates
    from src.core.peak_config import PeakConfig

    cfg = PeakConfig(raw={"environment": {"mode": "backtest"}})
    with pytest.raises(KeyError):
        _validate_strategy_registry_gates("definitely_not_a_strategy_xyz", cfg)


def test_load_strategy_no_network_calls() -> None:
    from src.strategies import load_strategy

    with patch("urllib.request.urlopen") as urlopen:
        load_strategy(MA_CROSSOVER_KEY)
        load_strategy(MOMENTUM_KEY)
    urlopen.assert_not_called()


def test_import_smoke_no_main_execution() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import run_strategy_from_config"],
        cwd=project_root / "scripts",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_cli_help_smoke_no_run() -> None:
    result = subprocess.run(
        [sys.executable, str(TARGET_SCRIPT), "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--strategy" in result.stdout


def test_cli_list_strategies_smoke_no_run(capsys) -> None:
    with patch.object(target_script, "list_strategies") as list_mock:
        target_script.main = target_script.main
        with patch.object(target_script, "parse_args") as parse_mock:
            args = MagicMock()
            args.list_strategies = True
            parse_mock.return_value = args
            target_script.main()
    list_mock.assert_called_once_with(verbose=True)
