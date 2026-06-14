"""
research_compare_strategies: canonical load_strategy() migration (offline, fail-closed).
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

import research_compare_strategies as compare_runner

TARGET_SCRIPT = project_root / "scripts/research_compare_strategies.py"
MA_CROSSOVER_KEY = "ma_crossover"
TREND_FOLLOWING_KEY = "trend_following"
MEAN_REVERSION_KEY = "mean_reversion"

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
    with patch.object(compare_runner, "main") as main_mock:
        importlib.reload(compare_runner)
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


def test_source_is_distinct_from_prior_migration_owners() -> None:
    prior_owners = (
        "research_run_strategy.py",
        "run_market_scan.py",
        "scan_markets.py",
        "run_forward_signals.py",
        "run_sweep.py",
        "run_strategy_from_config.py",
        "demo_strategy_research.py",
    )
    assert TARGET_SCRIPT.name == "research_compare_strategies.py"
    for owner in prior_owners:
        assert TARGET_SCRIPT.name != owner


def test_build_strategy_params_includes_section_and_stop_pct() -> None:
    cfg = _minimal_cfg(
        MA_CROSSOVER_KEY,
        fast_window=10,
        slow_window=50,
        price_col="close",
        stop_pct=0.03,
    )
    params = compare_runner._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    assert params["fast_window"] == 10
    assert params["slow_window"] == 50
    assert params["price_col"] == "close"
    assert params["stop_pct"] == 0.03


def test_build_strategy_params_source_uses_load_strategy_not_from_config_bypass() -> None:
    source = inspect.getsource(compare_runner._build_strategy_params_from_config)
    assert "load_strategy" in source
    assert "get_strategy_spec" not in source
    assert ".from_config" not in source


def test_build_strategy_params_calls_load_strategy_for_registry_validation() -> None:
    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=10, slow_window=50, price_col="close")

    with patch.object(compare_runner, "load_strategy") as load_mock:
        load_mock.return_value = MagicMock()
        params = compare_runner._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)

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
                TREND_FOLLOWING_KEY: {"adx_period": 14, "adx_threshold": 25.0},
            },
        }
    )
    ma_params = compare_runner._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    trend_params = compare_runner._build_strategy_params_from_config(cfg, TREND_FOLLOWING_KEY)

    assert "adx_period" not in ma_params
    assert "fast_window" not in trend_params
    assert ma_params["fast_window"] == 10
    assert trend_params["adx_period"] == 14


def test_build_strategy_params_unknown_strategy_fails_closed() -> None:
    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=10, slow_window=50, price_col="close")
    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        compare_runner._build_strategy_params_from_config(
            cfg, "definitely_not_a_research_compare_strategy_xyz"
        )


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
    params = compare_runner._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    canonical = load_strategy(MA_CROSSOVER_KEY)(df, params)

    pd.testing.assert_series_equal(canonical, legacy)


def test_load_strategy_trend_following_matches_create_strategy_from_config_signals() -> None:
    from src.strategies import load_strategy
    from src.strategies.registry import create_strategy_from_config

    cfg = _minimal_cfg(TREND_FOLLOWING_KEY, adx_period=14, adx_threshold=25.0)
    df = _sample_ohlcv(n=120)

    legacy = create_strategy_from_config(TREND_FOLLOWING_KEY, cfg).generate_signals(df)
    params = compare_runner._build_strategy_params_from_config(cfg, TREND_FOLLOWING_KEY)
    canonical = load_strategy(TREND_FOLLOWING_KEY)(df, params)

    pd.testing.assert_series_equal(canonical, legacy)


def test_run_single_backtest_calls_load_strategy_with_params() -> None:
    captured: dict[str, object] = {}
    call_count = 0

    def fake_signal_fn(df, params):
        nonlocal call_count
        call_count += 1
        captured["params"] = dict(params)
        return pd.Series(np.zeros(len(df)), index=df.index)

    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=10, slow_window=50, price_col="close")
    df = _sample_ohlcv()

    mock_result = MagicMock()
    mock_result.stats = {
        "total_return": 0.1,
        "max_drawdown": -0.05,
        "sharpe": 1.0,
        "win_rate": 0.5,
        "profit_factor": 1.2,
        "total_trades": 3,
        "cagr": 0.08,
    }

    with (
        patch.object(
            compare_runner, "load_strategy", return_value=fake_signal_fn
        ) as load_strategy_mock,
        patch.object(compare_runner, "build_position_sizer_from_config", return_value=MagicMock()),
        patch.object(compare_runner, "build_risk_manager_from_config", return_value=MagicMock()),
        patch.object(compare_runner, "BacktestEngine") as engine_cls,
        patch.object(compare_runner, "validate_for_live_trading", return_value=(True, [])),
    ):

        def run_realistic_side_effect(df, strategy_signal_fn, strategy_params, **kwargs):
            strategy_signal_fn(df, strategy_params)
            return mock_result

        engine_cls.return_value.run_realistic.side_effect = run_realistic_side_effect
        result = compare_runner.run_single_backtest(
            strategy_key=MA_CROSSOVER_KEY,
            df=df,
            cfg=cfg,
            symbol="BTC/EUR",
            verbose=False,
        )

    assert result is not None
    assert result["strategy"] == MA_CROSSOVER_KEY
    load_strategy_mock.assert_has_calls([call(MA_CROSSOVER_KEY), call(MA_CROSSOVER_KEY)])
    assert load_strategy_mock.call_count == 2
    assert captured["params"]["fast_window"] == 10
    assert captured["params"]["stop_pct"] == 0.02
    assert call_count == 1


def test_isolated_load_strategy_binding_per_comparison_candidate(tmp_path, monkeypatch) -> None:
    from src.core.peak_config import PeakConfig

    cfg_path = tmp_path / "cfg.toml"
    cfg_path.write_text("[environment]\nmode = 'backtest'\n", encoding="utf-8")

    load_calls: list[str] = []

    def fake_signal_fn_factory(key: str):
        def fake_signal_fn(df, params):
            return pd.Series(np.zeros(len(df)), index=df.index)

        return fake_signal_fn

    def load_strategy_side_effect(strategy_key: str):
        load_calls.append(strategy_key)
        return fake_signal_fn_factory(strategy_key)

    mock_result = MagicMock()
    mock_result.stats = {
        "total_return": 0.0,
        "max_drawdown": 0.0,
        "sharpe": 0.0,
        "win_rate": 0.0,
        "profit_factor": 0.0,
        "total_trades": 0,
        "cagr": 0.0,
    }

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "research_compare_strategies.py",
            "--config",
            str(cfg_path),
            "--strategies",
            f"{MA_CROSSOVER_KEY},{TREND_FOLLOWING_KEY}",
            "--no-registry",
        ],
    )

    with (
        patch.object(compare_runner, "load_config") as load_config_mock,
        patch.object(compare_runner, "load_ohlcv_data", return_value=_sample_ohlcv()),
        patch.object(compare_runner, "load_strategy", side_effect=load_strategy_side_effect),
        patch.object(compare_runner, "build_position_sizer_from_config", return_value=MagicMock()),
        patch.object(compare_runner, "build_risk_manager_from_config", return_value=MagicMock()),
        patch.object(compare_runner, "BacktestEngine") as engine_cls,
        patch.object(compare_runner, "validate_for_live_trading", return_value=(True, [])),
        patch.object(compare_runner, "get_strategy_spec") as get_spec_mock,
    ):
        load_config_mock.return_value = PeakConfig(
            raw={
                "environment": {"mode": "backtest"},
                "strategy": {
                    MA_CROSSOVER_KEY: {},
                    TREND_FOLLOWING_KEY: {},
                },
            }
        )
        get_spec_mock.return_value = MagicMock(description="test strategy")

        def run_realistic_side_effect(df, strategy_signal_fn, strategy_params, **kwargs):
            return mock_result

        engine_cls.return_value.run_realistic.side_effect = run_realistic_side_effect

        code = compare_runner.main()

    assert code == 0
    assert load_calls == [
        MA_CROSSOVER_KEY,
        MA_CROSSOVER_KEY,
        TREND_FOLLOWING_KEY,
        TREND_FOLLOWING_KEY,
    ]


def test_strategy_order_preserved_in_main_loop(tmp_path, monkeypatch) -> None:
    from src.core.peak_config import PeakConfig

    cfg_path = tmp_path / "cfg.toml"
    cfg_path.write_text("[environment]\nmode = 'backtest'\n", encoding="utf-8")
    strategy_order = [MA_CROSSOVER_KEY, TREND_FOLLOWING_KEY, MEAN_REVERSION_KEY]
    processed: list[str] = []

    mock_result = MagicMock()
    mock_result.stats = {
        "total_return": 0.0,
        "max_drawdown": 0.0,
        "sharpe": 0.0,
        "win_rate": 0.0,
        "profit_factor": 0.0,
        "total_trades": 0,
        "cagr": 0.0,
    }

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "research_compare_strategies.py",
            "--config",
            str(cfg_path),
            "--strategies",
            ",".join(strategy_order),
            "--no-registry",
        ],
    )

    def run_single_backtest_side_effect(strategy_key, **kwargs):
        processed.append(strategy_key)
        return {
            "strategy": strategy_key,
            "description": "test",
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "total_trades": 0,
            "cagr": 0.0,
            "live_ready": False,
            "result": mock_result,
        }

    with (
        patch.object(compare_runner, "load_config") as load_config_mock,
        patch.object(compare_runner, "load_ohlcv_data", return_value=_sample_ohlcv()),
        patch.object(
            compare_runner, "run_single_backtest", side_effect=run_single_backtest_side_effect
        ),
    ):
        load_config_mock.return_value = PeakConfig(
            raw={"environment": {"mode": "backtest"}, "strategy": {}}
        )
        code = compare_runner.main()

    assert code == 0
    assert processed == strategy_order
    assert len(processed) == 3


def test_unknown_strategy_fails_closed() -> None:
    from src.strategies import load_strategy

    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("definitely_not_a_research_compare_strategy_xyz")


def test_load_strategy_no_network_calls() -> None:
    from src.strategies import load_strategy

    with patch("urllib.request.urlopen") as urlopen:
        load_strategy(MA_CROSSOVER_KEY)
        load_strategy(TREND_FOLLOWING_KEY)
    urlopen.assert_not_called()


def test_import_smoke_no_main_execution() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import research_compare_strategies"],
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
    assert "--strategies" in result.stdout
    assert "--all" in result.stdout
    assert "--sort-by" in result.stdout


def test_cli_schema_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "research_compare_strategies.py",
            "--strategies",
            f"{MA_CROSSOVER_KEY},{TREND_FOLLOWING_KEY}",
            "--data-file",
            "data/btc.csv",
            "--symbol",
            "ETH/EUR",
            "--timeframe",
            "4h",
            "--start",
            "2023-01-01",
            "--end",
            "2023-12-31",
            "--bars",
            "300",
            "--sort-by",
            "sharpe",
            "--sort-asc",
            "--tag",
            "compare",
            "--config",
            "my.toml",
            "--export",
            "results/out.csv",
            "--no-registry",
            "--verbose",
        ],
    )
    args = compare_runner.parse_args()
    assert args.strategies == f"{MA_CROSSOVER_KEY},{TREND_FOLLOWING_KEY}"
    assert args.data_file == "data/btc.csv"
    assert args.symbol == "ETH/EUR"
    assert args.timeframe == "4h"
    assert args.start == "2023-01-01"
    assert args.end == "2023-12-31"
    assert args.bars == 300
    assert args.sort_by == "sharpe"
    assert args.sort_asc is True
    assert args.tag == "compare"
    assert args.config == "my.toml"
    assert args.export == "results/out.csv"
    assert args.no_registry is True
    assert args.verbose is True
