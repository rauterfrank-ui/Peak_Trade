"""
demo_strategy_research: canonical load_strategy() migration (offline, fail-closed).
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import scripts.demo_strategy_research as research_script
from scripts.demo_strategy_research import (
    MEAN_REVERSION_CHANNEL_DEFAULT_PARAMS,
    MEAN_REVERSION_CHANNEL_STRATEGY_KEY,
    MEAN_REVERSION_CHANNEL_TIGHT_PARAMS,
    RSI_REVERSION_SIMPLE_PARAMS,
    RSI_REVERSION_STRATEGY_KEY,
    RSI_REVERSION_TREND_FILTER_PARAMS,
    RSI_REVERSION_WILDER_PARAMS,
    VOL_BREAKOUT_DEFAULT_PARAMS,
    VOL_BREAKOUT_LONG_ONLY_PARAMS,
    VOL_BREAKOUT_STRATEGY_KEY,
    create_synthetic_ohlcv,
)

TARGET_SCRIPT = project_root / "scripts/demo_strategy_research.py"

FORBIDDEN_CLASS_IMPORTS = (
    "VolBreakoutStrategy",
    "MeanReversionChannelStrategy",
    "RsiReversionStrategy",
)

CANONICAL_KEYS = (
    VOL_BREAKOUT_STRATEGY_KEY,
    MEAN_REVERSION_CHANNEL_STRATEGY_KEY,
    RSI_REVERSION_STRATEGY_KEY,
)


def _read_source() -> str:
    return TARGET_SCRIPT.read_text(encoding="utf-8")


def _sample_ohlcv(n: int = 120) -> pd.DataFrame:
    return create_synthetic_ohlcv(n_bars=n, seed=42)


def test_module_imports_without_main_side_effects() -> None:
    with patch.object(research_script, "main") as main_mock:
        importlib.reload(research_script)
    main_mock.assert_not_called()


def test_source_has_no_direct_strategy_class_imports() -> None:
    tree = ast.parse(_read_source())
    imported_names = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("src.strategies")
        ):
            for alias in node.names:
                imported_names.add(alias.name)
    for forbidden in FORBIDDEN_CLASS_IMPORTS:
        assert forbidden not in imported_names


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


def test_all_three_strategies_resolve_via_load_strategy() -> None:
    from src.strategies import load_strategy

    for key in CANONICAL_KEYS:
        fn = load_strategy(key)
        assert callable(fn)


def test_load_strategy_vol_breakout_default_matches_direct_oop_output() -> None:
    from src.strategies import load_strategy
    from src.strategies.vol_breakout import VolBreakoutStrategy

    df = _sample_ohlcv()
    canonical = load_strategy(VOL_BREAKOUT_STRATEGY_KEY)(df, VOL_BREAKOUT_DEFAULT_PARAMS)
    legacy = VolBreakoutStrategy(
        lookback_breakout=20,
        vol_window=14,
        vol_percentile=50.0,
        side="both",
    ).generate_signals(df)
    pd.testing.assert_series_equal(canonical, legacy)


def test_load_strategy_vol_breakout_long_only_matches_direct_oop_output() -> None:
    from src.strategies import load_strategy
    from src.strategies.vol_breakout import VolBreakoutStrategy

    df = _sample_ohlcv()
    canonical = load_strategy(VOL_BREAKOUT_STRATEGY_KEY)(df, VOL_BREAKOUT_LONG_ONLY_PARAMS)
    legacy = VolBreakoutStrategy(side="long").generate_signals(df)
    pd.testing.assert_series_equal(canonical, legacy)


def test_load_strategy_mean_reversion_channel_default_matches_direct_oop_output() -> None:
    from src.strategies import load_strategy
    from src.strategies.mean_reversion_channel import MeanReversionChannelStrategy

    df = _sample_ohlcv()
    canonical = load_strategy(MEAN_REVERSION_CHANNEL_STRATEGY_KEY)(
        df, MEAN_REVERSION_CHANNEL_DEFAULT_PARAMS
    )
    legacy = MeanReversionChannelStrategy(
        window=20,
        num_std=2.0,
        exit_at_mean=True,
    ).generate_signals(df)
    pd.testing.assert_series_equal(canonical, legacy)


def test_load_strategy_mean_reversion_channel_tight_matches_direct_oop_output() -> None:
    from src.strategies import load_strategy
    from src.strategies.mean_reversion_channel import MeanReversionChannelStrategy

    df = _sample_ohlcv()
    canonical = load_strategy(MEAN_REVERSION_CHANNEL_STRATEGY_KEY)(
        df, MEAN_REVERSION_CHANNEL_TIGHT_PARAMS
    )
    legacy = MeanReversionChannelStrategy(
        window=15,
        num_std=1.5,
        exit_at_mean=False,
    ).generate_signals(df)
    pd.testing.assert_series_equal(canonical, legacy)


def test_load_strategy_rsi_reversion_wilder_matches_direct_oop_output() -> None:
    from src.strategies import load_strategy
    from src.strategies.rsi_reversion import RsiReversionStrategy

    df = _sample_ohlcv()
    canonical = load_strategy(RSI_REVERSION_STRATEGY_KEY)(df, RSI_REVERSION_WILDER_PARAMS)
    legacy = RsiReversionStrategy(
        rsi_window=14,
        lower=30.0,
        upper=70.0,
        use_wilder=True,
    ).generate_signals(df)
    pd.testing.assert_series_equal(canonical, legacy)


def test_load_strategy_rsi_reversion_simple_matches_direct_oop_output() -> None:
    from src.strategies import load_strategy
    from src.strategies.rsi_reversion import RsiReversionStrategy

    df = _sample_ohlcv()
    canonical = load_strategy(RSI_REVERSION_STRATEGY_KEY)(df, RSI_REVERSION_SIMPLE_PARAMS)
    legacy = RsiReversionStrategy(
        rsi_window=14,
        lower=30.0,
        upper=70.0,
        use_wilder=False,
    ).generate_signals(df)
    pd.testing.assert_series_equal(canonical, legacy)


def test_load_strategy_rsi_reversion_trend_filter_matches_direct_oop_output() -> None:
    from src.strategies import load_strategy
    from src.strategies.rsi_reversion import RsiReversionStrategy

    df = _sample_ohlcv()
    canonical = load_strategy(RSI_REVERSION_STRATEGY_KEY)(df, RSI_REVERSION_TREND_FILTER_PARAMS)
    legacy = RsiReversionStrategy(
        rsi_window=14,
        lower=30.0,
        upper=70.0,
        use_trend_filter=True,
        trend_ma_window=50,
    ).generate_signals(df)
    pd.testing.assert_series_equal(canonical, legacy)


def test_unknown_strategy_fails_closed() -> None:
    from src.strategies import load_strategy

    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("not_a_real_strategy_key")


def test_import_smoke_no_main_execution() -> None:
    import scripts.demo_strategy_research as mod

    assert hasattr(mod, "main")
    assert hasattr(mod, "create_synthetic_ohlcv")
