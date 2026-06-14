"""
run_market_scan: canonical load_strategy() migration (offline, fail-closed).
"""

from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import numpy as np
import pandas as pd
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

import run_market_scan as market_scan_runner

TARGET_SCRIPT = project_root / "scripts/run_market_scan.py"
MA_CROSSOVER_KEY = "ma_crossover"
RSI_REVERSION_KEY = "rsi_reversion"

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


def _minimal_cfg(strategy_key: str, **strategy_params: object):
    from src.core.peak_config import PeakConfig

    raw = {
        "environment": {"mode": "backtest"},
        "strategy": {
            strategy_key: dict(strategy_params),
        },
    }
    return PeakConfig(raw=raw)


def test_module_imports_without_main_side_effects() -> None:
    with patch.object(market_scan_runner, "main") as main_mock:
        importlib.reload(market_scan_runner)
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


def test_build_strategy_params_includes_section_and_stop_pct() -> None:
    cfg = _minimal_cfg(
        MA_CROSSOVER_KEY,
        fast_window=10,
        slow_window=50,
        price_col="close",
        stop_pct=0.03,
    )
    params = market_scan_runner._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    assert params["fast_window"] == 10
    assert params["slow_window"] == 50
    assert params["price_col"] == "close"
    assert params["stop_pct"] == 0.03


def test_build_strategy_params_source_uses_load_strategy_not_from_config_bypass() -> None:
    source = inspect.getsource(market_scan_runner._build_strategy_params_from_config)
    assert "load_strategy" in source
    assert "get_strategy_spec" not in source
    assert ".from_config" not in source


def test_build_strategy_params_calls_load_strategy_for_registry_validation() -> None:
    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=10, slow_window=50, price_col="close")

    with patch.object(market_scan_runner, "load_strategy") as load_mock:
        load_mock.return_value = MagicMock()
        params = market_scan_runner._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)

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
    ma_params = market_scan_runner._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    rsi_params = market_scan_runner._build_strategy_params_from_config(cfg, RSI_REVERSION_KEY)

    assert "rsi_period" not in ma_params
    assert "fast_window" not in rsi_params
    assert ma_params["fast_window"] == 10
    assert rsi_params["rsi_period"] == 14


def test_build_strategy_params_unknown_strategy_fails_closed() -> None:
    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=10, slow_window=50, price_col="close")
    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        market_scan_runner._build_strategy_params_from_config(cfg, "definitely_not_a_strategy_xyz")


def test_load_strategy_ma_crossover_matches_create_strategy_from_config_signals() -> None:
    from src.strategies import load_strategy
    from src.strategies.registry import create_strategy_from_config

    cfg = _minimal_cfg(
        MA_CROSSOVER_KEY,
        fast_window=10,
        slow_window=50,
        price_col="close",
        stop_pct=0.03,
    )
    df = _sample_ohlcv()

    legacy = create_strategy_from_config(MA_CROSSOVER_KEY, cfg).generate_signals(df)
    params = market_scan_runner._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    canonical = load_strategy(MA_CROSSOVER_KEY)(df, params)

    pd.testing.assert_series_equal(canonical, legacy)


def test_load_strategy_rsi_reversion_matches_create_strategy_from_config_signals() -> None:
    from src.strategies import load_strategy
    from src.strategies.registry import create_strategy_from_config

    cfg = _minimal_cfg(
        RSI_REVERSION_KEY,
        rsi_period=14,
        oversold=30,
        overbought=70,
        stop_pct=0.02,
    )
    df = _sample_ohlcv(n=120)

    legacy = create_strategy_from_config(RSI_REVERSION_KEY, cfg).generate_signals(df)
    params = market_scan_runner._build_strategy_params_from_config(cfg, RSI_REVERSION_KEY)
    canonical = load_strategy(RSI_REVERSION_KEY)(df, params)

    pd.testing.assert_series_equal(canonical, legacy)


def test_scan_symbol_forward_calls_load_strategy_with_params() -> None:
    captured: dict[str, object] = {}

    def fake_signal_fn(df, params):
        captured["params"] = dict(params)
        return pd.Series([0.0, 1.0], index=df.index[-2:])

    mock_client = MagicMock()
    mock_client.fetch_ohlcv.return_value = _sample_ohlcv()

    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=10, slow_window=50, price_col="close")

    with (
        patch(
            "src.exchange.build_exchange_client_from_config",
            return_value=mock_client,
        ),
        patch(
            "run_market_scan.load_strategy",
            return_value=fake_signal_fn,
        ) as load_strategy_mock,
    ):
        result = market_scan_runner.scan_symbol_forward(
            symbol="BTC/EUR",
            strategy_key=MA_CROSSOVER_KEY,
            timeframe="1h",
            bars=80,
            cfg=cfg,
        )

    assert "error" not in result
    assert result["signal"] == 1.0
    load_strategy_mock.assert_has_calls([call(MA_CROSSOVER_KEY), call(MA_CROSSOVER_KEY)])
    assert load_strategy_mock.call_count == 2
    assert captured["params"]["fast_window"] == 10
    assert captured["params"]["slow_window"] == 50
    assert captured["params"]["stop_pct"] == 0.02


def test_scan_symbol_backtest_lite_calls_load_strategy_with_params() -> None:
    captured: dict[str, object] = {}
    call_count = 0

    def fake_signal_fn(df, params):
        nonlocal call_count
        call_count += 1
        captured["params"] = dict(params)
        return pd.Series(np.zeros(len(df)), index=df.index)

    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=10, slow_window=50, price_col="close")

    mock_result = MagicMock()
    mock_result.stats = {"total_return": 0.1, "sharpe": 1.0, "max_drawdown": -0.05}

    with (
        patch(
            "run_market_scan.load_strategy",
            return_value=fake_signal_fn,
        ) as load_strategy_mock,
        patch(
            "run_market_scan.BacktestEngine",
        ) as engine_cls,
        patch(
            "run_market_scan.build_position_sizer_from_config",
            return_value=MagicMock(),
        ),
        patch(
            "run_market_scan.build_risk_manager_from_config",
            return_value=MagicMock(),
        ),
    ):
        engine_cls.return_value.run_realistic.return_value = mock_result
        result = market_scan_runner.scan_symbol_backtest_lite(
            symbol="BTC/EUR",
            strategy_key=MA_CROSSOVER_KEY,
            timeframe="1h",
            bars=80,
            cfg=cfg,
        )

    assert "error" not in result
    assert result["signal"] == 0.0
    load_strategy_mock.assert_has_calls([call(MA_CROSSOVER_KEY), call(MA_CROSSOVER_KEY)])
    assert load_strategy_mock.call_count == 2
    assert captured["params"]["fast_window"] == 10
    assert call_count >= 1


def test_isolated_signal_fn_binding_per_scan_call() -> None:
    def fake_signal_fn(df, params):
        return pd.Series([1.0], index=df.index[-1:])

    cfg = _minimal_cfg(MA_CROSSOVER_KEY)

    mock_result = MagicMock()
    mock_result.stats = {"total_return": 0.0}

    with (
        patch(
            "run_market_scan.load_strategy",
            return_value=fake_signal_fn,
        ) as load_strategy_mock,
        patch("run_market_scan.BacktestEngine") as engine_cls,
        patch("run_market_scan.build_position_sizer_from_config", return_value=MagicMock()),
        patch("run_market_scan.build_risk_manager_from_config", return_value=MagicMock()),
    ):
        engine_cls.return_value.run_realistic.return_value = mock_result
        market_scan_runner.scan_symbol_backtest_lite(
            symbol="BTC/EUR",
            strategy_key=MA_CROSSOVER_KEY,
            timeframe="1h",
            bars=50,
            cfg=cfg,
        )
        market_scan_runner.scan_symbol_backtest_lite(
            symbol="ETH/EUR",
            strategy_key=MA_CROSSOVER_KEY,
            timeframe="1h",
            bars=50,
            cfg=cfg,
        )

    assert load_strategy_mock.call_count == 4


def test_main_dry_run_calls_load_strategy_not_executed() -> None:
    cfg_path = project_root / "config" / "config.toml"
    if not cfg_path.exists():
        pytest.skip("config/config.toml not available")

    with patch.object(market_scan_runner, "load_strategy") as load_strategy_mock:
        code = market_scan_runner.main(
            [
                "--config",
                str(cfg_path),
                "--strategy",
                MA_CROSSOVER_KEY,
                "--symbols",
                "BTC/EUR,ETH/EUR",
                "--mode",
                "backtest-lite",
                "--dry-run",
            ]
        )

    assert code == 0
    load_strategy_mock.assert_not_called()


def test_unknown_strategy_fails_closed() -> None:
    from src.strategies import load_strategy

    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("definitely_not_a_market_scan_strategy_xyz")


def test_load_strategy_no_network_calls() -> None:
    from src.strategies import load_strategy

    with patch("urllib.request.urlopen") as urlopen:
        load_strategy(MA_CROSSOVER_KEY)
        load_strategy(RSI_REVERSION_KEY)
    urlopen.assert_not_called()


def test_import_smoke_no_main_execution() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import run_market_scan"],
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
    assert "--symbols" in result.stdout


def test_cli_schema_unchanged() -> None:
    args = market_scan_runner.parse_args(
        [
            "--strategy",
            MA_CROSSOVER_KEY,
            "--symbols",
            "BTC/EUR,ETH/EUR",
            "--mode",
            "backtest-lite",
        ]
    )
    assert args.strategy == MA_CROSSOVER_KEY
    assert args.symbols == "BTC/EUR,ETH/EUR"
    assert args.mode == "backtest-lite"
    assert args.bars == 200
    assert args.timeframe == "1h"
