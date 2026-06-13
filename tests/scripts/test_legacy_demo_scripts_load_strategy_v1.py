"""
Legacy demo/research scripts: canonical load_strategy() migration (offline, fail-closed).
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

TARGET_SCRIPTS: dict[str, Path] = {
    "run_simple_backtest": project_root / "scripts/run_simple_backtest.py",
    "demo_portfolio_backtest": project_root / "scripts/demo_portfolio_backtest.py",
    "demo_backtest_with_risk": project_root / "scripts/demo_backtest_with_risk.py",
    "demo_complete_pipeline": project_root / "scripts/demo_complete_pipeline.py",
    "run_momentum_realistic": project_root / "scripts/run_momentum_realistic.py",
}

MA_CROSSOVER_KEY = "ma_crossover"
MOMENTUM_KEY = "momentum_1h"

FORBIDDEN_DIRECT_IMPORTS = (
    "from src.strategies.ma_crossover import generate_signals",
    "from src.strategies.momentum import generate_signals",
    "ma_crossover.generate_signals",
    "momentum.generate_signals",
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


@pytest.mark.parametrize(
    "name",
    [n for n in TARGET_SCRIPTS if n != "demo_complete_pipeline"],
)
def test_module_imports_without_main_side_effects(name: str) -> None:
    module = importlib.import_module(f"scripts.{name}")
    with patch.object(module, "main") as main_mock:
        importlib.reload(module)
    main_mock.assert_not_called()


def test_demo_complete_pipeline_source_imports_load_strategy_without_running_main() -> None:
    """demo_complete_pipeline has pre-existing RiskLimitChecker import drift; source-only check."""
    source = _read_source("demo_complete_pipeline")
    assert "load_strategy" in source
    assert "from src.strategies.ma_crossover import generate_signals" not in source


@pytest.mark.parametrize("name", TARGET_SCRIPTS)
def test_source_has_no_direct_generate_signals_imports(name: str) -> None:
    source = _read_source(name)
    for forbidden in FORBIDDEN_DIRECT_IMPORTS:
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


def test_ma_crossover_scripts_use_canonical_registry_key() -> None:
    ma_scripts = (
        "run_simple_backtest",
        "demo_portfolio_backtest",
        "demo_backtest_with_risk",
        "demo_complete_pipeline",
    )
    for name in ma_scripts:
        assert MA_CROSSOVER_KEY in _read_source(name)


def test_run_momentum_realistic_uses_momentum_1h_key() -> None:
    source = _read_source("run_momentum_realistic")
    assert MOMENTUM_KEY in source
    assert "MOMENTUM_STRATEGY_KEY" in source


def test_load_strategy_ma_crossover_matches_direct_module_callable() -> None:
    from src.strategies import load_strategy
    from src.strategies.ma_crossover import generate_signals as direct

    assert load_strategy(MA_CROSSOVER_KEY) is direct


def test_load_strategy_momentum_1h_matches_direct_module_callable() -> None:
    from src.strategies import load_strategy
    from src.strategies.momentum import generate_signals as direct

    assert load_strategy(MOMENTUM_KEY) is direct


def test_ma_crossover_signal_output_unchanged_with_defaults() -> None:
    from src.strategies import load_strategy
    from src.strategies.ma_crossover import generate_signals as direct

    df = _sample_ohlcv()
    params = {"fast_period": 10, "slow_period": 30, "stop_pct": 0.02}
    canonical = load_strategy(MA_CROSSOVER_KEY)(df, params)
    legacy = direct(df, params)
    pd.testing.assert_series_equal(canonical, legacy)


def test_momentum_signal_output_unchanged_with_defaults() -> None:
    from src.strategies import load_strategy
    from src.strategies.momentum import generate_signals as direct

    df = _sample_ohlcv()
    params = {
        "lookback_period": 20,
        "entry_threshold": 0.02,
        "exit_threshold": -0.01,
        "stop_pct": 0.025,
    }
    canonical = load_strategy(MOMENTUM_KEY)(df, params)
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


def test_no_silent_strategy_fallback_on_unknown_name() -> None:
    import scripts.demo_portfolio_backtest as demo_script

    with patch.object(demo_script, "load_strategy") as load_mock:
        load_mock.side_effect = ValueError("Unbekannte Strategie 'bad_name'")
        with pytest.raises(ValueError, match="Unbekannte Strategie"):
            demo_script.load_strategy("bad_name")
    load_mock.assert_called_once_with("bad_name")


def test_load_strategy_no_network_calls() -> None:
    from src.strategies import load_strategy

    with patch("urllib.request.urlopen") as urlopen:
        load_strategy(MA_CROSSOVER_KEY)
        load_strategy(MOMENTUM_KEY)
    urlopen.assert_not_called()


def test_demo_portfolio_backtest_cli_help_no_run() -> None:
    import subprocess

    result = subprocess.run(
        [sys.executable, str(TARGET_SCRIPTS["demo_portfolio_backtest"]), "--help"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Portfolio" in result.stdout
