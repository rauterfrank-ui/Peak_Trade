"""
scan_markets: canonical load_strategy() migration (offline, fail-closed).
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

import scan_markets as scan_markets_runner

TARGET_SCRIPT = project_root / "scripts/scan_markets.py"
MA_CROSSOVER_KEY = "ma_crossover"
RSI_REVERSION_KEY = "rsi_reversion"

FORBIDDEN_IMPORTS = ("create_strategy_from_config", "list_strategies")


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
    with patch.object(scan_markets_runner, "main") as main_mock:
        importlib.reload(scan_markets_runner)
    main_mock.assert_not_called()


def test_source_has_no_forbidden_strategy_imports() -> None:
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


def test_source_is_distinct_from_run_market_scan_owner() -> None:
    run_market_scan_script = project_root / "scripts/run_market_scan.py"
    assert TARGET_SCRIPT != run_market_scan_script
    assert TARGET_SCRIPT.name == "scan_markets.py"
    assert run_market_scan_script.name == "run_market_scan.py"


def test_build_strategy_params_includes_section_and_stop_pct() -> None:
    cfg = _minimal_cfg(
        MA_CROSSOVER_KEY,
        fast_window=10,
        slow_window=50,
        price_col="close",
        stop_pct=0.03,
    )
    params = scan_markets_runner._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    assert params["fast_window"] == 10
    assert params["slow_window"] == 50
    assert params["price_col"] == "close"
    assert params["stop_pct"] == 0.03


def test_build_strategy_params_source_uses_load_strategy_not_from_config_bypass() -> None:
    source = inspect.getsource(scan_markets_runner._build_strategy_params_from_config)
    assert "load_strategy" in source
    assert "get_strategy_spec" not in source
    assert ".from_config" not in source


def test_build_strategy_params_calls_load_strategy_for_registry_validation() -> None:
    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=10, slow_window=50, price_col="close")

    with patch.object(scan_markets_runner, "load_strategy") as load_mock:
        load_mock.return_value = MagicMock()
        params = scan_markets_runner._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)

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
    ma_params = scan_markets_runner._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    rsi_params = scan_markets_runner._build_strategy_params_from_config(cfg, RSI_REVERSION_KEY)

    assert "rsi_period" not in ma_params
    assert "fast_window" not in rsi_params
    assert ma_params["fast_window"] == 10
    assert rsi_params["rsi_period"] == 14


def test_build_strategy_params_unknown_strategy_fails_closed() -> None:
    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=10, slow_window=50, price_col="close")
    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        scan_markets_runner._build_strategy_params_from_config(cfg, "definitely_not_a_strategy_xyz")


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
    params = scan_markets_runner._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
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
    params = scan_markets_runner._build_strategy_params_from_config(cfg, RSI_REVERSION_KEY)
    canonical = load_strategy(RSI_REVERSION_KEY)(df, params)

    pd.testing.assert_series_equal(canonical, legacy)


def test_run_backtest_for_symbol_calls_load_strategy_with_params() -> None:
    captured: dict[str, object] = {}
    call_count = 0

    def fake_signal_fn(df, params):
        nonlocal call_count
        call_count += 1
        captured["params"] = dict(params)
        return pd.Series(np.zeros(len(df)), index=df.index)

    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=10, slow_window=50, price_col="close")

    mock_result = MagicMock()
    mock_result.stats = {
        "total_return": 0.1,
        "sharpe": 1.0,
        "max_drawdown": -0.05,
        "total_trades": 3,
        "profit_factor": 1.2,
        "win_rate": 0.5,
        "cagr": 0.08,
    }
    mock_result.metadata = {"regime_distribution": {}}

    with (
        patch(
            "scan_markets.load_strategy",
            return_value=fake_signal_fn,
        ) as load_strategy_mock,
        patch(
            "scan_markets.load_data_for_symbol",
            return_value=_sample_ohlcv(),
        ),
        patch(
            "scan_markets.BacktestEngine",
        ) as engine_cls,
        patch(
            "scan_markets.build_position_sizer_from_config",
            return_value=MagicMock(),
        ),
        patch(
            "scan_markets.build_risk_manager_from_config",
            return_value=MagicMock(),
        ),
    ):

        def run_realistic_side_effect(df, strategy_signal_fn, strategy_params):
            strategy_signal_fn(df, strategy_params)
            return mock_result

        engine_cls.return_value.run_realistic.side_effect = run_realistic_side_effect
        result = scan_markets_runner.run_backtest_for_symbol(
            symbol="BTC/EUR",
            strategy_key=MA_CROSSOVER_KEY,
            cfg=cfg,
            n_bars=80,
            verbose=False,
        )

    assert result["symbol"] == "BTC/EUR"
    load_strategy_mock.assert_has_calls([call(MA_CROSSOVER_KEY), call(MA_CROSSOVER_KEY)])
    assert load_strategy_mock.call_count == 2
    assert captured["params"]["fast_window"] == 10
    assert captured["params"]["stop_pct"] == 0.02
    assert call_count >= 1


def test_isolated_signal_fn_binding_per_symbol_scan() -> None:
    def fake_signal_fn(df, params):
        return pd.Series([1.0], index=df.index[-1:])

    cfg = _minimal_cfg(MA_CROSSOVER_KEY)

    mock_result = MagicMock()
    mock_result.stats = {
        "total_return": 0.0,
        "sharpe": 0.0,
        "max_drawdown": 0.0,
        "total_trades": 0,
        "profit_factor": 0.0,
        "win_rate": 0.0,
        "cagr": 0.0,
    }
    mock_result.metadata = {"regime_distribution": {}}

    with (
        patch(
            "scan_markets.load_strategy",
            return_value=fake_signal_fn,
        ) as load_strategy_mock,
        patch(
            "scan_markets.load_data_for_symbol",
            return_value=_sample_ohlcv(n=50),
        ),
        patch("scan_markets.BacktestEngine") as engine_cls,
        patch("scan_markets.build_position_sizer_from_config", return_value=MagicMock()),
        patch("scan_markets.build_risk_manager_from_config", return_value=MagicMock()),
    ):
        engine_cls.return_value.run_realistic.return_value = mock_result
        scan_markets_runner.run_backtest_for_symbol(
            symbol="BTC/EUR",
            strategy_key=MA_CROSSOVER_KEY,
            cfg=cfg,
            n_bars=50,
            verbose=False,
        )
        scan_markets_runner.run_backtest_for_symbol(
            symbol="ETH/EUR",
            strategy_key=MA_CROSSOVER_KEY,
            cfg=cfg,
            n_bars=50,
            verbose=False,
        )

    assert load_strategy_mock.call_count == 4


def test_unknown_strategy_fails_closed() -> None:
    from src.strategies import load_strategy

    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("definitely_not_a_scan_markets_strategy_xyz")


def test_load_strategy_no_network_calls() -> None:
    from src.strategies import load_strategy

    with patch("urllib.request.urlopen") as urlopen:
        load_strategy(MA_CROSSOVER_KEY)
        load_strategy(RSI_REVERSION_KEY)
    urlopen.assert_not_called()


def test_import_smoke_no_main_execution() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import scan_markets"],
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
    assert "--sort-by" in result.stdout


def test_cli_schema_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "scan_markets.py",
            "--strategy",
            MA_CROSSOVER_KEY,
            "--sort-by",
            "sharpe",
            "--ascending",
            "--no-individual-reports",
            "--bars",
            "300",
            "--run-name",
            "test-scan",
        ],
    )
    args = scan_markets_runner.parse_args()
    assert args.strategy == MA_CROSSOVER_KEY
    assert args.sort_by == "sharpe"
    assert args.ascending is True
    assert args.no_individual_reports is True
    assert args.bars == 300
    assert args.run_name == "test-scan"
