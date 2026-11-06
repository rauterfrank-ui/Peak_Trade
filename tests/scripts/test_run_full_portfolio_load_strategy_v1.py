"""
run_full_portfolio: canonical load_strategy() migration (offline, fail-closed).
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import scripts.run_full_portfolio as portfolio_script
from src.portfolio import PortfolioManager

LEGACY_SIGNAL_IMPORTS = (
    "ma_crossover_signals",
    "momentum_signals",
    "rsi_signals",
    "bollinger_signals",
    "macd_signals",
    "ecm_signals",
)


def test_module_imports_without_main_side_effects() -> None:
    with patch.object(portfolio_script, "main") as main_mock:
        import importlib

        importlib.reload(portfolio_script)
    main_mock.assert_not_called()


def test_source_has_no_legacy_signal_imports() -> None:
    source = Path(portfolio_script.__file__).read_text(encoding="utf-8")
    for legacy_name in LEGACY_SIGNAL_IMPORTS:
        assert legacy_name not in source


def test_source_has_no_parallel_strategy_registry() -> None:
    source = Path(portfolio_script.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    assigned_names = {
        node.targets[0].id
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    }
    assert "STRATEGY_REGISTRY" not in assigned_names
    assert "load_strategy" in source


def test_resolve_portfolio_strategy_loads_all_demo_strategies() -> None:
    for name in portfolio_script.DEMO_PORTFOLIO_STRATEGY_NAMES:
        signal_fn, params = portfolio_script.resolve_portfolio_strategy(name)
        assert callable(signal_fn)
        assert isinstance(params, dict)
        assert params


def test_resolve_portfolio_strategy_passes_config_params() -> None:
    signal_fn, params = portfolio_script.resolve_portfolio_strategy("ma_crossover")
    assert callable(signal_fn)
    assert "fast_period" in params or "fast_window" in params


def test_unknown_strategy_fails_closed() -> None:
    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        portfolio_script.resolve_portfolio_strategy("definitely_not_a_strategy_xyz")


def test_missing_config_strategy_fails_closed() -> None:
    with patch.object(
        portfolio_script, "load_strategy", return_value=lambda df, p: df["close"] * 0
    ):
        with pytest.raises(KeyError, match="nicht in config.toml"):
            portfolio_script.resolve_portfolio_strategy("definitely_not_a_strategy_xyz")


def test_no_silent_strategy_fallback_on_unknown_name() -> None:
    with patch.object(portfolio_script, "load_strategy") as load_mock:
        load_mock.side_effect = ValueError("Unbekannte Strategie 'bad_name'")
        with pytest.raises(ValueError, match="Unbekannte Strategie"):
            portfolio_script.resolve_portfolio_strategy("bad_name")
    load_mock.assert_called_once_with("bad_name")


def test_resolve_portfolio_strategy_no_network_calls() -> None:
    with patch("urllib.request.urlopen") as urlopen:
        portfolio_script.resolve_portfolio_strategy("ma_crossover")
    urlopen.assert_not_called()


def test_add_configured_strategies_registers_all_demo_strategies() -> None:
    pm = PortfolioManager()
    portfolio_script.add_configured_strategies(pm)
    loaded_names = [allocation.name for allocation in pm.strategies]
    assert loaded_names == list(portfolio_script.DEMO_PORTFOLIO_STRATEGY_NAMES)


def test_offline_portfolio_backtest_with_dummy_data() -> None:
    pm = PortfolioManager()
    pm.total_capital = 10_000.0
    portfolio_script.add_configured_strategies(pm)

    df = portfolio_script.create_rich_dummy_data(n_bars=300)
    result = pm.run_backtest(df=df, allocation_method="equal")

    assert len(result.strategy_results) == len(portfolio_script.DEMO_PORTFOLIO_STRATEGY_NAMES)
    assert len(result.portfolio_equity) >= len(df)
    assert result.stats["total_trades"] >= 0
