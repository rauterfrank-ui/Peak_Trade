"""
sweep_parameters: canonical load_strategy() migration (offline, fail-closed).
"""

from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import scripts.sweep_parameters as sweep_script

TARGET_SCRIPT = project_root / "scripts/sweep_parameters.py"
MA_CROSSOVER_KEY = "ma_crossover"
MOMENTUM_KEY = "momentum_1h"
RSI_REVERSION_KEY = "rsi_reversion"

FORBIDDEN_IMPORTS = ("create_strategy_from_config",)
STRATEGY_PARAMS_BUILDER_OWNER = "scripts/run_backtest.py:_build_strategy_params_from_config"
FORBIDDEN_LOCAL_BUILDER_DEFS = frozenset({"_build_strategy_params_from_config"})


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


def _minimal_cfg(strategy_key: str, **strategy_params: object) -> MagicMock:
    raw = {
        "strategy": {
            strategy_key: dict(strategy_params),
        },
    }
    cfg = MagicMock()
    cfg.raw = raw

    def _get(path: str, default=None):
        node = raw
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    cfg.get.side_effect = _get
    cfg.with_overrides.return_value = cfg
    return cfg


def test_module_imports_without_main_side_effects() -> None:
    with patch.object(sweep_script, "main") as main_mock:
        importlib.reload(sweep_script)
    main_mock.assert_not_called()


def test_source_has_no_create_strategy_from_config() -> None:
    source = _read_source()
    for forbidden in FORBIDDEN_IMPORTS:
        assert forbidden not in source


def test_source_uses_load_strategy() -> None:
    assert "load_strategy" in _read_source()


def test_source_has_no_parallel_strategy_registry() -> None:
    tree = ast.parse(_read_source())
    assigned_names = {
        node.targets[0].id
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    }
    assert "STRATEGY_REGISTRY" not in assigned_names


def test_source_has_no_local_builder_definition() -> None:
    local_defs = _local_function_defs()
    assert FORBIDDEN_LOCAL_BUILDER_DEFS.isdisjoint(local_defs)


def test_build_strategy_params_import_identity_is_canonical_owner() -> None:
    import scripts.run_backtest as run_backtest_script

    assert (
        sweep_script._build_strategy_params_from_config
        is run_backtest_script._build_strategy_params_from_config
    )


def test_source_imports_canonical_strategy_params_builder() -> None:
    source = _read_source()
    assert "_build_strategy_params_from_config" in source
    assert "scripts.run_backtest" in source


def test_build_strategy_params_includes_section_and_stop_pct() -> None:
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
    params = sweep_script._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    assert params["fast_window"] == 10
    assert params["slow_window"] == 50
    assert params["price_col"] == "close"
    assert params["stop_pct"] == 0.03


def test_build_strategy_params_source_uses_load_strategy_not_from_config_bypass() -> None:
    import scripts.run_backtest as run_backtest_script

    source = inspect.getsource(run_backtest_script._build_strategy_params_from_config)
    assert "load_strategy" in source
    assert "spec.cls.from_config" not in source


def test_build_strategy_params_calls_load_strategy_for_registry_validation() -> None:
    import scripts.run_backtest as run_backtest_script
    from src.core.peak_config import PeakConfig

    cfg = PeakConfig(
        raw={
            "environment": {"mode": "backtest"},
            "strategy": {
                MA_CROSSOVER_KEY: {
                    "fast_window": 10,
                    "slow_window": 50,
                    "price_col": "close",
                },
            },
        }
    )

    with patch.object(run_backtest_script, "load_strategy") as load_mock:
        load_mock.return_value = MagicMock()
        params = sweep_script._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)

    load_mock.assert_called_once_with(MA_CROSSOVER_KEY)
    assert params["fast_window"] == 10
    assert params["stop_pct"] == 0.02


def test_build_strategy_params_isolated_per_strategy_key() -> None:
    from src.core.peak_config import PeakConfig

    cfg = PeakConfig(
        raw={
            "environment": {"mode": "backtest"},
            "strategy": {
                MA_CROSSOVER_KEY: {"fast_window": 10, "slow_window": 50, "price_col": "close"},
                RSI_REVERSION_KEY: {
                    "rsi_period": 14,
                    "oversold": 30,
                    "overbought": 70,
                },
            },
        }
    )
    ma_params = sweep_script._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    rsi_params = sweep_script._build_strategy_params_from_config(cfg, RSI_REVERSION_KEY)

    assert "rsi_period" not in ma_params
    assert "fast_window" not in rsi_params
    assert ma_params["fast_window"] == 10
    assert rsi_params["rsi_period"] == 14


def test_build_strategy_params_unknown_strategy_fails_closed() -> None:
    from src.core.peak_config import PeakConfig

    cfg = PeakConfig(
        raw={
            "environment": {"mode": "backtest"},
            "strategy": {MA_CROSSOVER_KEY: {"fast_window": 10, "slow_window": 50}},
        }
    )
    with pytest.raises(KeyError):
        sweep_script._build_strategy_params_from_config(cfg, "definitely_not_a_strategy_xyz")


def test_load_strategy_ma_crossover_matches_create_strategy_from_config_signals() -> None:
    from src.core.peak_config import PeakConfig
    from src.strategies import load_strategy
    from src.strategies.registry import create_strategy_from_config

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
    df = _sample_ohlcv()

    legacy = create_strategy_from_config(MA_CROSSOVER_KEY, cfg).generate_signals(df)
    legacy = legacy.replace(-1, 0)

    params = sweep_script._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    canonical = load_strategy(MA_CROSSOVER_KEY)(df, params).replace(-1, 0)

    pd.testing.assert_series_equal(canonical, legacy)


def test_load_strategy_momentum_matches_create_strategy_from_config_signals() -> None:
    from src.core.peak_config import PeakConfig
    from src.strategies import load_strategy
    from src.strategies.registry import create_strategy_from_config

    raw = {
        "environment": {"mode": "backtest"},
        "strategy": {
            MOMENTUM_KEY: {
                "lookback_period": 15,
                "entry_threshold": 0.02,
                "exit_threshold": -0.01,
                "stop_pct": 0.02,
            },
        },
    }
    cfg = PeakConfig(raw=raw)
    df = _sample_ohlcv(n=120)

    legacy = create_strategy_from_config(MOMENTUM_KEY, cfg).generate_signals(df)
    legacy = legacy.replace(-1, 0)

    params = sweep_script._build_strategy_params_from_config(cfg, MOMENTUM_KEY)
    canonical = load_strategy(MOMENTUM_KEY)(df, params).replace(-1, 0)

    pd.testing.assert_series_equal(canonical, legacy)


def test_run_backtest_for_params_forwards_config_to_canonical_builder() -> None:
    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=10, slow_window=50, price_col="close")
    captured: dict[str, object] = {}

    def capture_builder(config, strategy_key):
        captured["cfg"] = config
        captured["strategy_key"] = strategy_key
        return {"fast_window": 10, "slow_window": 50, "stop_pct": 0.02}

    mock_result = MagicMock()
    mock_result.stats = {"total_return": 0.0, "sharpe": 0.0, "total_trades": 0}
    mock_result.metadata = {}

    with (
        patch.object(sweep_script, "load_data_for_symbol", return_value=_sample_ohlcv()),
        patch.object(
            sweep_script,
            "_build_strategy_params_from_config",
            side_effect=capture_builder,
        ),
        patch.object(
            sweep_script,
            "load_strategy",
            return_value=lambda df, params: pd.Series(0, index=df.index),
        ),
        patch.object(sweep_script, "build_position_sizer_from_config", return_value=MagicMock()),
        patch.object(sweep_script, "build_risk_manager_from_config", return_value=MagicMock()),
        patch.object(sweep_script.BacktestEngine, "run_realistic", return_value=mock_result),
    ):
        sweep_script.run_backtest_for_params(
            base_cfg=cfg,
            strategy_key=MA_CROSSOVER_KEY,
            symbol="BTC/EUR",
            param_names=["fast_window", "slow_window"],
            param_values=(10, 50),
            n_bars=80,
        )

    assert captured["cfg"] is cfg
    assert captured["strategy_key"] == MA_CROSSOVER_KEY


def test_run_backtest_for_params_calls_load_strategy_and_passes_full_params() -> None:
    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=10, slow_window=50, price_col="close")
    captured: dict[str, object] = {}

    def fake_signal_fn(df, params):
        captured["params"] = dict(params)
        return pd.Series(0, index=df.index)

    mock_result = MagicMock()
    mock_result.stats = {"total_return": 0.0, "sharpe": 0.0, "total_trades": 0}
    mock_result.metadata = {}

    def fake_run_realistic(**kwargs):
        captured["params"] = dict(kwargs["strategy_params"])
        kwargs["strategy_signal_fn"](kwargs["df"], kwargs["strategy_params"])
        return mock_result

    with (
        patch.object(sweep_script, "load_data_for_symbol", return_value=_sample_ohlcv()),
        patch.object(sweep_script, "load_strategy", return_value=fake_signal_fn) as load_mock,
        patch.object(sweep_script, "build_position_sizer_from_config", return_value=MagicMock()),
        patch.object(sweep_script, "build_risk_manager_from_config", return_value=MagicMock()),
        patch.object(sweep_script.BacktestEngine, "run_realistic", side_effect=fake_run_realistic),
    ):
        sweep_script.run_backtest_for_params(
            base_cfg=cfg,
            strategy_key=MA_CROSSOVER_KEY,
            symbol="BTC/EUR",
            param_names=["fast_window", "slow_window"],
            param_values=(10, 50),
            n_bars=80,
        )

    assert load_mock.call_count == 1
    load_mock.assert_called_once_with(MA_CROSSOVER_KEY)
    assert captured["params"]["fast_window"] == 10
    assert captured["params"]["slow_window"] == 50
    assert captured["params"]["stop_pct"] == 0.02


def test_run_backtest_for_params_applies_long_only_wrapper() -> None:
    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=10, slow_window=50)

    def fake_signal_fn(df, params):
        return pd.Series([1, -1, 0], index=df.index[:3])

    mock_result = MagicMock()
    mock_result.stats = {}
    mock_result.metadata = {}

    with (
        patch.object(sweep_script, "load_data_for_symbol", return_value=_sample_ohlcv()[:3]),
        patch.object(sweep_script, "load_strategy", return_value=fake_signal_fn),
        patch.object(sweep_script, "build_position_sizer_from_config", return_value=MagicMock()),
        patch.object(sweep_script, "build_risk_manager_from_config", return_value=MagicMock()),
        patch.object(
            sweep_script.BacktestEngine, "run_realistic", return_value=mock_result
        ) as run_mock,
    ):
        sweep_script.run_backtest_for_params(
            base_cfg=cfg,
            strategy_key=MA_CROSSOVER_KEY,
            symbol="BTC/EUR",
            param_names=["fast_window"],
            param_values=(10,),
            n_bars=3,
        )

    signal_fn = run_mock.call_args.kwargs["strategy_signal_fn"]
    df = _sample_ohlcv()[:3]
    out = signal_fn(df, {"stop_pct": 0.02})
    assert out.tolist() == [1, 0, 0]


def test_unknown_strategy_fails_closed() -> None:
    from src.strategies import load_strategy

    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("definitely_not_a_strategy_xyz")


def test_load_strategy_no_network_calls() -> None:
    from src.strategies import load_strategy

    with patch("urllib.request.urlopen") as urlopen:
        load_strategy(MA_CROSSOVER_KEY)
        load_strategy(MOMENTUM_KEY)
    urlopen.assert_not_called()


def test_import_smoke_no_main_execution() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import scripts.sweep_parameters"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_cli_help_smoke(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        sweep_script.parse_args(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "Hyperparameter-Sweeps" in out
