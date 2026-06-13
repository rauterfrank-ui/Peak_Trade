"""
demo_phase40_portfolio_backtest: canonical load_strategy() migration (offline, fail-closed).
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

import scripts.demo_phase40_portfolio_backtest as phase40_script
from scripts.demo_phase40_portfolio_backtest import (
    BREAKOUT_PARAMS,
    BREAKOUT_STRATEGY_KEY,
    COMPOSITE_AGGREGATION,
    COMPOSITE_BREAKOUT_CONFIG,
    COMPOSITE_MA_CONFIG,
    COMPOSITE_RSI_CONFIG,
    COMPOSITE_SIGNAL_THRESHOLD,
    COMPOSITE_STRATEGY_KEY,
    COMPOSITE_WEIGHTS,
    MA_CROSSOVER_STRATEGY_KEY,
    RSI_REVERSION_STRATEGY_KEY,
    RSI_VOL_FILTER_PARAMS,
    RSI_VOL_RSI_PARAMS,
    VOL_REGIME_FILTER_STRATEGY_KEY,
    _apply_vol_regime_filter,
    generate_demo_data,
)

TARGET_SCRIPT = project_root / "scripts/demo_phase40_portfolio_backtest.py"

FORBIDDEN_CLASS_IMPORTS = (
    "BreakoutStrategy",
    "VolRegimeFilter",
    "CompositeStrategy",
    "RsiReversionStrategy",
    "MACrossoverStrategy",
)

CANONICAL_KEYS = (
    BREAKOUT_STRATEGY_KEY,
    VOL_REGIME_FILTER_STRATEGY_KEY,
    COMPOSITE_STRATEGY_KEY,
    RSI_REVERSION_STRATEGY_KEY,
    MA_CROSSOVER_STRATEGY_KEY,
)


def _read_source() -> str:
    return TARGET_SCRIPT.read_text(encoding="utf-8")


def _sample_ohlcv(n: int = 120) -> pd.DataFrame:
    return generate_demo_data(n_bars=n, seed=42, include_trends=True)


def test_module_imports_without_main_side_effects() -> None:
    with patch.object(phase40_script, "main") as main_mock:
        importlib.reload(phase40_script)
    main_mock.assert_not_called()


def test_source_has_no_direct_strategy_class_imports() -> None:
    source = _read_source()
    for forbidden in FORBIDDEN_CLASS_IMPORTS:
        assert forbidden not in source


def test_source_uses_load_strategy() -> None:
    assert "load_strategy" in _read_source()


def test_source_declares_all_canonical_registry_keys() -> None:
    source = _read_source()
    for key in CANONICAL_KEYS:
        assert key in source


def test_source_has_no_strategy_map() -> None:
    assert "strategy_map" not in _read_source()


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


def test_source_has_no_broad_except_soft_return() -> None:
    assert "except Exception" not in _read_source()


def test_all_five_strategies_resolve_via_load_strategy() -> None:
    from src.strategies import load_strategy

    for key in CANONICAL_KEYS:
        fn = load_strategy(key)
        assert callable(fn)


def test_load_strategy_breakout_matches_direct_oop_output() -> None:
    from src.strategies import load_strategy
    from src.strategies.breakout import BreakoutStrategy

    df = _sample_ohlcv()
    canonical = load_strategy(BREAKOUT_STRATEGY_KEY)(df, BREAKOUT_PARAMS)
    legacy = BreakoutStrategy(
        lookback_breakout=20,
        stop_loss_pct=0.03,
        take_profit_pct=0.06,
        side="both",
    ).generate_signals(df)
    pd.testing.assert_series_equal(canonical, legacy)


def test_load_strategy_rsi_reversion_matches_direct_oop_output() -> None:
    from src.strategies import load_strategy
    from src.strategies.rsi_reversion import RsiReversionStrategy

    df = _sample_ohlcv()
    canonical = load_strategy(RSI_REVERSION_STRATEGY_KEY)(df, RSI_VOL_RSI_PARAMS)
    legacy = RsiReversionStrategy(
        rsi_window=14,
        lower=30.0,
        upper=70.0,
    ).generate_signals(df)
    pd.testing.assert_series_equal(canonical, legacy)


def test_load_strategy_vol_regime_filter_matches_direct_oop_output() -> None:
    from src.strategies import load_strategy
    from src.strategies.rsi_reversion import RsiReversionStrategy
    from src.strategies.vol_regime_filter import VolRegimeFilter

    df = _sample_ohlcv()
    rsi = RsiReversionStrategy(rsi_window=14, lower=30.0, upper=70.0)
    vol_filter = VolRegimeFilter(
        vol_window=14,
        vol_percentile_low=25,
        vol_percentile_high=75,
    )
    vol_fn = load_strategy(VOL_REGIME_FILTER_STRATEGY_KEY)
    raw = rsi.generate_signals(df)
    legacy_filtered = vol_filter.apply_to_signals(df, raw)
    canonical_filtered = _apply_vol_regime_filter(df, raw, vol_fn, RSI_VOL_FILTER_PARAMS)
    pd.testing.assert_series_equal(canonical_filtered, legacy_filtered)


def test_load_strategy_ma_crossover_matches_direct_oop_output() -> None:
    from src.strategies import load_strategy
    from src.strategies.ma_crossover import MACrossoverStrategy

    df = _sample_ohlcv()
    params = {
        "fast_period": COMPOSITE_MA_CONFIG["fast_window"],
        "slow_period": COMPOSITE_MA_CONFIG["slow_window"],
    }
    canonical = load_strategy(MA_CROSSOVER_STRATEGY_KEY)(df, params)
    legacy = MACrossoverStrategy(fast_window=20, slow_window=50).generate_signals(df)
    pd.testing.assert_series_equal(canonical, legacy)


def test_load_strategy_composite_matches_direct_oop_output() -> None:
    from src.strategies import load_strategy
    from src.strategies.breakout import BreakoutStrategy
    from src.strategies.composite import CompositeStrategy
    from src.strategies.ma_crossover import MACrossoverStrategy
    from src.strategies.rsi_reversion import RsiReversionStrategy

    df = _sample_ohlcv()
    rsi_strategy = RsiReversionStrategy(rsi_window=14, lower=30, upper=70)
    breakout_strategy = BreakoutStrategy(lookback_breakout=20, stop_loss_pct=0.02)
    ma_strategy = MACrossoverStrategy(fast_window=20, slow_window=50)
    legacy = CompositeStrategy(
        strategies=[
            (rsi_strategy, COMPOSITE_WEIGHTS[0]),
            (breakout_strategy, COMPOSITE_WEIGHTS[1]),
            (ma_strategy, COMPOSITE_WEIGHTS[2]),
        ],
        aggregation=COMPOSITE_AGGREGATION,
        signal_threshold=COMPOSITE_SIGNAL_THRESHOLD,
    ).generate_signals(df)
    composite_params = {
        "strategies": [
            (rsi_strategy, COMPOSITE_WEIGHTS[0]),
            (breakout_strategy, COMPOSITE_WEIGHTS[1]),
            (ma_strategy, COMPOSITE_WEIGHTS[2]),
        ],
        "aggregation": COMPOSITE_AGGREGATION,
        "signal_threshold": COMPOSITE_SIGNAL_THRESHOLD,
    }
    canonical = load_strategy(COMPOSITE_STRATEGY_KEY)(df, composite_params)
    pd.testing.assert_series_equal(canonical, legacy)


def test_composite_portfolio_weights_unchanged() -> None:
    assert COMPOSITE_WEIGHTS == (0.4, 0.3, 0.3)
    assert COMPOSITE_AGGREGATION == "weighted"
    assert COMPOSITE_SIGNAL_THRESHOLD == 0.3


def test_unknown_strategy_fails_closed() -> None:
    from src.strategies import load_strategy

    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("definitely_not_a_strategy_xyz")


def test_invalid_ma_crossover_params_fail_closed() -> None:
    from src.strategies import load_strategy

    df = _sample_ohlcv()
    fn = load_strategy(MA_CROSSOVER_STRATEGY_KEY)
    invalid_params = {"fast_period": 50, "slow_period": 20}
    with pytest.raises(ValueError, match="fast_window|fast_period"):
        fn(df, invalid_params)


def test_no_silent_strategy_fallback_on_unknown_name() -> None:
    from src.strategies import load_strategy

    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("bad_phase40_strategy_name")


def test_load_strategy_no_network_calls() -> None:
    from src.strategies import load_strategy

    with patch("urllib.request.urlopen") as urlopen:
        for key in CANONICAL_KEYS:
            load_strategy(key)
    urlopen.assert_not_called()


def test_import_smoke_no_main_execution() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import scripts.demo_phase40_portfolio_backtest"],
        cwd=project_root,
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
    assert "breakout" in result.stdout


def test_run_functions_use_backtest_engine_with_mocked_run() -> None:
    df = _sample_ohlcv()
    with patch.object(phase40_script, "BacktestEngine") as engine_cls:
        engine_cls.return_value.run_realistic.return_value = MagicMock(
            stats={},
            equity_curve=pd.Series(dtype=float),
            trades=pd.DataFrame(),
        )
        phase40_script.run_breakout_backtest(df)
        phase40_script.run_rsi_with_vol_filter_backtest(df)
        phase40_script.run_composite_backtest(df)
    assert engine_cls.call_count == 3
