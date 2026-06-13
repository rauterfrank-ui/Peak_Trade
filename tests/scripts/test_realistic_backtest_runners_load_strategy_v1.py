"""
Realistic backtest runners: canonical load_strategy() migration (offline, fail-closed).
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


def _read_source(name: str) -> str:
    return TARGET_SCRIPTS[name].read_text(encoding="utf-8")


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
