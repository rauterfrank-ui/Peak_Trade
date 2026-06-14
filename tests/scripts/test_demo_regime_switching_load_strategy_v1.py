"""
demo_regime_switching: canonical load_strategy() migration (offline, fail-closed).
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

import scripts.demo_regime_switching as regime_script
from scripts.demo_regime_switching import (
    MA_CROSSOVER_STRATEGY_KEY,
    MEAN_REVERSION_CHANNEL_STRATEGY_KEY,
    REGIME_DEMO_AVAILABLE_STRATEGY_KEYS,
    RSI_REVERSION_STRATEGY_KEY,
    TREND_FOLLOWING_STRATEGY_KEY,
    VOL_BREAKOUT_STRATEGY_KEY,
    StrategySwitchingConfig,
    generate_synthetic_market_data,
    get_regime_demo_available_strategies,
    simulate_switching_decisions,
    validate_regime_mapped_strategy_keys,
)
from src.regime import make_regime_detector, RegimeDetectorConfig
from src.strategies import STRATEGY_REGISTRY, load_strategy

TARGET_SCRIPT = project_root / "scripts/demo_regime_switching.py"

REGIME_BRANCHES = ("breakout", "ranging", "trending", "unknown")

CANONICAL_REGIME_KEYS = (
    VOL_BREAKOUT_STRATEGY_KEY,
    MEAN_REVERSION_CHANNEL_STRATEGY_KEY,
    RSI_REVERSION_STRATEGY_KEY,
    TREND_FOLLOWING_STRATEGY_KEY,
    MA_CROSSOVER_STRATEGY_KEY,
)


def _read_source() -> str:
    return TARGET_SCRIPT.read_text(encoding="utf-8")


def _default_switching_config() -> StrategySwitchingConfig:
    return StrategySwitchingConfig(
        enabled=True,
        policy_name="simple_regime_mapping",
        regime_to_strategies={
            "breakout": [VOL_BREAKOUT_STRATEGY_KEY],
            "ranging": [
                MEAN_REVERSION_CHANNEL_STRATEGY_KEY,
                RSI_REVERSION_STRATEGY_KEY,
            ],
            "trending": [TREND_FOLLOWING_STRATEGY_KEY],
            "unknown": [MA_CROSSOVER_STRATEGY_KEY],
        },
        regime_to_weights={
            "ranging": {
                MEAN_REVERSION_CHANNEL_STRATEGY_KEY: 0.6,
                RSI_REVERSION_STRATEGY_KEY: 0.4,
            },
        },
        default_strategies=[MA_CROSSOVER_STRATEGY_KEY],
    )


def test_module_imports_without_main_side_effects() -> None:
    with patch.object(regime_script, "main") as main_mock:
        importlib.reload(regime_script)
    main_mock.assert_not_called()


def test_source_has_no_strategy_registry_import_or_access() -> None:
    tree = ast.parse(_read_source())
    imported = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module
        for alias in node.names
    }
    assert "STRATEGY_REGISTRY" not in imported
    assert "STRATEGY_REGISTRY" not in {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    }


def test_source_uses_load_strategy() -> None:
    assert "load_strategy" in _read_source()


def test_source_declares_all_canonical_regime_keys() -> None:
    source = _read_source()
    for key in CANONICAL_REGIME_KEYS:
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


def test_regime_demo_available_keys_match_canonical_registry() -> None:
    assert tuple(sorted(REGIME_DEMO_AVAILABLE_STRATEGY_KEYS)) == tuple(
        sorted(STRATEGY_REGISTRY.keys())
    )


def test_get_regime_demo_available_strategies_delegates_to_load_strategy() -> None:
    with patch.object(regime_script, "load_strategy") as load_mock:
        load_mock.return_value = lambda df, params: df["close"] * 0
        keys = get_regime_demo_available_strategies()
    assert load_mock.call_count == len(REGIME_DEMO_AVAILABLE_STRATEGY_KEYS)
    assert keys == list(REGIME_DEMO_AVAILABLE_STRATEGY_KEYS)


def test_validate_regime_mapped_strategy_keys_delegates_to_load_strategy() -> None:
    config = _default_switching_config()
    with patch.object(regime_script, "load_strategy") as load_mock:
        load_mock.return_value = lambda df, params: df["close"] * 0
        validate_regime_mapped_strategy_keys(config)
    called_keys = [call.args[0] for call in load_mock.call_args_list]
    assert set(called_keys) == set(CANONICAL_REGIME_KEYS)


def test_all_regime_mapped_keys_resolve_via_load_strategy() -> None:
    for key in CANONICAL_REGIME_KEYS:
        fn = load_strategy(key)
        assert callable(fn)


def test_unknown_strategy_fails_closed() -> None:
    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("definitely_not_a_strategy_xyz")


def test_no_silent_strategy_fallback_on_unknown_name() -> None:
    with patch.object(regime_script, "load_strategy") as load_mock:
        load_mock.side_effect = ValueError("Unbekannte Strategie 'bad_name'")
        with pytest.raises(ValueError, match="Unbekannte Strategie"):
            validate_regime_mapped_strategy_keys(
                StrategySwitchingConfig(
                    enabled=True,
                    policy_name="simple_regime_mapping",
                    regime_to_strategies={"unknown": ["bad_name"]},
                    default_strategies=["bad_name"],
                )
            )
    load_mock.assert_called()


@pytest.mark.parametrize("regime_label", REGIME_BRANCHES)
def test_all_regime_branches_produce_switching_decisions(regime_label: str) -> None:
    config = _default_switching_config()
    regimes = pd.Series([regime_label] * 20)
    available = get_regime_demo_available_strategies()
    stats = simulate_switching_decisions(regimes, config, available)
    assert stats["total_decisions"] == 20
    assert stats["unique_strategies_used"] >= 1


def test_switching_decisions_bind_loader_keys_into_usage_structure() -> None:
    config = _default_switching_config()
    regimes = pd.Series(["breakout", "ranging", "trending", "unknown"] * 5)
    available = get_regime_demo_available_strategies()
    stats = simulate_switching_decisions(regimes, config, available)
    used = {k for k, count in stats["strategy_usage"].items() if count > 0}
    assert used.issubset(set(available))
    assert VOL_BREAKOUT_STRATEGY_KEY in used
    assert MA_CROSSOVER_STRATEGY_KEY in used


def test_regime_detection_output_feeds_switching_without_strategy_execution() -> None:
    df = generate_synthetic_market_data(n_bars=120)
    detector = make_regime_detector(
        RegimeDetectorConfig(
            enabled=True,
            detector_name="volatility_breakout",
            lookback_window=50,
            min_history_bars=50,
            vol_window=20,
            vol_percentile_breakout=0.75,
            vol_percentile_ranging=0.30,
        )
    )
    assert detector is not None
    regimes = detector.detect_regimes(df)
    config = _default_switching_config()
    validate_regime_mapped_strategy_keys(config)
    stats = simulate_switching_decisions(
        regimes,
        config,
        get_regime_demo_available_strategies(),
    )
    assert stats["total_decisions"] == len(regimes)


def test_load_strategy_no_network_calls() -> None:
    with patch("urllib.request.urlopen") as urlopen:
        for key in CANONICAL_REGIME_KEYS:
            load_strategy(key)
    urlopen.assert_not_called()


def test_resolve_strategy_no_network_calls() -> None:
    with patch("urllib.request.urlopen") as urlopen:
        get_regime_demo_available_strategies()
    urlopen.assert_not_called()
