"""
run_portfolio_backtest_v2: canonical load_strategy() migration (offline, fail-closed).
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

import run_portfolio_backtest_v2 as portfolio_v2_script

TARGET_SCRIPT = project_root / "scripts/run_portfolio_backtest_v2.py"
MA_CROSSOVER_KEY = "ma_crossover"
MOMENTUM_KEY = "momentum_1h"

FORBIDDEN_IMPORTS = ("create_strategy_from_config",)


def _read_source() -> str:
    return TARGET_SCRIPT.read_text(encoding="utf-8")


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
    with patch.object(portfolio_v2_script, "main") as main_mock:
        importlib.reload(portfolio_v2_script)
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


def test_build_strategy_params_includes_section_and_stop_pct() -> None:
    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=10, slow_window=50, price_col="close")
    params = portfolio_v2_script._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    assert params["fast_window"] == 10
    assert params["slow_window"] == 50
    assert params["price_col"] == "close"
    assert params["stop_pct"] == 0.02


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

    params = portfolio_v2_script._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
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

    params = portfolio_v2_script._build_strategy_params_from_config(cfg, MOMENTUM_KEY)
    canonical = load_strategy(MOMENTUM_KEY)(df, params).replace(-1, 0)

    pd.testing.assert_series_equal(canonical, legacy)


def test_run_single_symbol_backtest_calls_load_strategy_and_passes_full_params() -> None:
    from src.core.peak_config import PeakConfig

    repo_root = project_root
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
    captured: dict[str, object] = {}

    def fake_signal_fn(df, params):
        captured["params"] = dict(params)
        return pd.Series(0, index=df.index)

    mock_result = MagicMock()
    mock_result.stats = {"total_return": 0.0, "sharpe": 0.0, "total_trades": 0}
    mock_result.metadata = {}
    mock_result.equity_curve = pd.Series(
        [100.0, 101.0], index=pd.date_range("2024-01-01", periods=2, freq="h")
    )

    def fake_run_realistic(**kwargs):
        captured["params"] = dict(kwargs["strategy_params"])
        kwargs["strategy_signal_fn"](kwargs["df"], kwargs["strategy_params"])
        return mock_result

    with (
        patch.object(portfolio_v2_script, "load_data_for_symbol") as load_data,
        patch.object(
            portfolio_v2_script, "load_strategy", return_value=fake_signal_fn
        ) as load_strategy_mock,
        patch.object(
            portfolio_v2_script.BacktestEngine, "run_realistic", side_effect=fake_run_realistic
        ),
    ):
        load_data.return_value = (_sample_ohlcv(), {"symbol": "BTC/EUR"})
        portfolio_v2_script.run_single_symbol_backtest(
            cfg=cfg,
            symbol="BTC/EUR",
            strategy_key=MA_CROSSOVER_KEY,
            n_bars=80,
        )

    load_strategy_mock.assert_called_once_with(MA_CROSSOVER_KEY)
    assert captured["params"]["fast_window"] == 10
    assert captured["params"]["slow_window"] == 50
    assert captured["params"]["stop_pct"] == 0.02


def test_isolated_strategy_bindings_per_symbol() -> None:
    from src.core.peak_config import PeakConfig

    cfg = PeakConfig(
        raw={
            "environment": {"mode": "backtest"},
            "strategy": {
                MA_CROSSOVER_KEY: {"fast_window": 10, "slow_window": 50, "price_col": "close"},
                MOMENTUM_KEY: {
                    "lookback_period": 15,
                    "entry_threshold": 0.02,
                    "exit_threshold": -0.01,
                },
            },
        }
    )
    call_counts: dict[str, int] = {MA_CROSSOVER_KEY: 0, MOMENTUM_KEY: 0}

    def make_fn(key: str):
        def _fn(df, params):
            call_counts[key] += 1
            return pd.Series(0, index=df.index)

        return _fn

    def fake_load_strategy(key: str):
        return make_fn(key)

    mock_result = MagicMock()
    mock_result.stats = {}
    mock_result.metadata = {}
    mock_result.equity_curve = pd.Series(
        [100.0, 101.0], index=pd.date_range("2024-01-01", periods=2, freq="h")
    )

    def fake_run_realistic(**kwargs):
        kwargs["strategy_signal_fn"](kwargs["df"], kwargs["strategy_params"])
        return mock_result

    with (
        patch.object(portfolio_v2_script, "load_data_for_symbol") as load_data,
        patch.object(portfolio_v2_script, "load_strategy", side_effect=fake_load_strategy),
        patch.object(
            portfolio_v2_script.BacktestEngine,
            "run_realistic",
            side_effect=fake_run_realistic,
        ),
    ):
        load_data.return_value = (_sample_ohlcv(), {"symbol": "BTC/EUR"})
        portfolio_v2_script.run_single_symbol_backtest(cfg, "BTC/EUR", MA_CROSSOVER_KEY, n_bars=80)
        portfolio_v2_script.run_single_symbol_backtest(cfg, "BTC/EUR", MOMENTUM_KEY, n_bars=80)

    assert call_counts[MA_CROSSOVER_KEY] == 1
    assert call_counts[MOMENTUM_KEY] == 1


def test_unknown_strategy_fails_closed() -> None:
    from src.strategies import load_strategy

    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("definitely_not_a_strategy_xyz")


def test_no_silent_strategy_fallback_on_unknown_name() -> None:
    from src.strategies import load_strategy

    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("bad_portfolio_v2_strategy_name")


def test_load_strategy_no_network_calls() -> None:
    from src.strategies import load_strategy

    with patch("urllib.request.urlopen") as urlopen:
        load_strategy(MA_CROSSOVER_KEY)
        load_strategy(MOMENTUM_KEY)
    urlopen.assert_not_called()


def test_import_smoke_no_main_execution() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import run_portfolio_backtest_v2"],
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
    assert "ma_crossover" in result.stdout


def test_portfolio_weights_and_cli_schema_unchanged() -> None:
    from run_portfolio_backtest_v2 import parse_args

    args = parse_args(["--strategy", MA_CROSSOVER_KEY, "--use-portfolio-strategies"])
    assert args.strategy == MA_CROSSOVER_KEY
    assert args.use_portfolio_strategies is True
    assert args.bars == 200
