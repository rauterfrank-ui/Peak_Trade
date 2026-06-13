"""
demo_order_pipeline_backtest: registry logging + fail-closed strategy loading (offline).
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import scripts.demo_order_pipeline_backtest as demo_script
from scripts.demo_order_pipeline_backtest import (
    format_available_strategy_hints,
    generate_sample_data,
    get_available_strategy_hint_keys,
    main,
    parse_args,
)
from src.strategies import STRATEGY_REGISTRY, load_strategy


def test_module_imports_without_main_side_effects() -> None:
    with patch.object(demo_script, "main") as main_mock:
        importlib.reload(demo_script)
    main_mock.assert_not_called()


def test_source_uses_load_strategy() -> None:
    source = Path(demo_script.__file__).read_text(encoding="utf-8")
    assert "load_strategy" in source
    assert "log_backtest_result" in source


def test_source_has_no_strategy_map() -> None:
    source = Path(demo_script.__file__).read_text(encoding="utf-8")
    assert "strategy_map" not in source


def test_source_has_no_parallel_strategy_registry_assignment() -> None:
    source = Path(demo_script.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    assigned_names = {
        node.targets[0].id
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    }
    assert "STRATEGY_REGISTRY" not in assigned_names


def test_source_has_no_broad_except_return_on_strategy_load() -> None:
    source = Path(demo_script.__file__).read_text(encoding="utf-8")
    assert "except Exception as e:" not in source
    assert "log_backtest_run" not in source


def test_strategy_hints_from_canonical_registry() -> None:
    hints = get_available_strategy_hint_keys()
    assert hints == sorted(STRATEGY_REGISTRY.keys())


def test_strategy_hints_deterministically_sorted() -> None:
    hints = get_available_strategy_hint_keys()
    assert hints == sorted(hints)


def test_obsolete_non_canonical_names_not_in_hints() -> None:
    hints = get_available_strategy_hint_keys()
    assert "momentum" not in hints
    assert "bollinger" not in hints
    assert "momentum_1h" in hints
    assert "bollinger_bands" in hints


def test_format_available_strategy_hints_matches_registry() -> None:
    expected = ", ".join(sorted(STRATEGY_REGISTRY.keys()))
    assert format_available_strategy_hints() == expected


def test_unknown_strategy_fails_closed_via_load_strategy() -> None:
    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("definitely_not_a_strategy_xyz")


def test_unknown_strategy_main_returns_non_zero_exit() -> None:
    exit_code = main(["--strategy", "definitely_not_a_strategy_xyz", "--bars", "50"])
    assert exit_code == 1


def test_no_silent_strategy_fallback_on_unknown_name() -> None:
    with patch.object(demo_script, "load_strategy") as load_mock:
        load_mock.side_effect = ValueError("Unbekannte Strategie 'bad_name'")
        exit_code = main(["--strategy", "bad_name", "--bars", "50"])
    load_mock.assert_called_once_with("bad_name")
    assert exit_code == 1


def test_invalid_strategy_params_fail_closed() -> None:
    df = generate_sample_data(symbol="BTC/EUR", bars=80)
    strategy_fn = load_strategy("macd")
    invalid_params = {
        "fast_ema": 30,
        "slow_ema": 10,
        "signal_ema": 9,
        "stop_pct": 0.02,
    }
    with pytest.raises(ValueError, match="fast_ema"):
        strategy_fn(df, invalid_params)


def test_log_backtest_result_called_once_on_success() -> None:
    mock_result = MagicMock()
    mock_result.stats = {
        "total_return": 0.1,
        "cagr": 0.05,
        "max_drawdown": -0.02,
        "sharpe": 1.0,
        "total_trades": 3,
        "win_rate": 0.5,
        "profit_factor": 1.2,
        "total_orders": 4,
        "filled_orders": 3,
        "rejected_orders": 1,
        "total_fees": 1.5,
    }
    mock_result.trades = pd.DataFrame()
    mock_engine = MagicMock()
    mock_engine.run_with_order_layer.return_value = mock_result
    mock_engine.execution_results = []

    with (
        patch.object(demo_script, "BacktestEngine", return_value=mock_engine),
        patch.object(demo_script, "load_strategy", return_value=lambda df, p: df["close"] * 0),
        patch.object(demo_script, "log_backtest_result", return_value="run-test-123") as log_mock,
    ):
        exit_code = main(["--strategy", "ma_crossover", "--bars", "50", "--tag", "unit-test"])

    assert exit_code == 0
    log_mock.assert_called_once()
    kwargs = log_mock.call_args.kwargs
    assert kwargs["strategy_name"] == "ma_crossover"
    assert kwargs["tag"] == "unit-test"
    assert kwargs["symbol"] == "BTC/EUR"
    assert kwargs["timeframe"] == "1h"
    assert kwargs["data_source"] == "synthetic"
    assert kwargs["extra_metadata"]["runner"] == "demo_order_pipeline_backtest.py"


def test_log_backtest_result_not_called_on_strategy_error() -> None:
    with (
        patch.object(
            demo_script,
            "load_strategy",
            side_effect=ValueError("Unbekannte Strategie 'bad'"),
        ),
        patch.object(demo_script, "log_backtest_result") as log_mock,
        patch.object(demo_script, "BacktestEngine") as engine_mock,
    ):
        exit_code = main(["--strategy", "bad", "--bars", "50"])
    assert exit_code == 1
    log_mock.assert_not_called()
    engine_mock.assert_not_called()


def test_logging_error_not_swallowed() -> None:
    mock_result = MagicMock()
    mock_result.stats = {
        "total_return": 0.0,
        "max_drawdown": 0.0,
        "sharpe": 0.0,
        "total_trades": 0,
        "win_rate": 0.0,
        "profit_factor": 0.0,
        "total_orders": 0,
        "filled_orders": 0,
        "rejected_orders": 0,
        "total_fees": 0.0,
    }
    mock_result.trades = pd.DataFrame()
    mock_engine = MagicMock()
    mock_engine.run_with_order_layer.return_value = mock_result
    mock_engine.execution_results = []

    with (
        patch.object(demo_script, "BacktestEngine", return_value=mock_engine),
        patch.object(demo_script, "load_strategy", return_value=lambda df, p: df["close"] * 0),
        patch.object(
            demo_script,
            "log_backtest_result",
            side_effect=RuntimeError("registry write failed"),
        ),
    ):
        with pytest.raises(RuntimeError, match="registry write failed"):
            main(["--strategy", "ma_crossover", "--bars", "50"])


def test_no_real_registry_write_when_mocked() -> None:
    mock_result = MagicMock()
    mock_result.stats = {
        "total_return": 0.0,
        "max_drawdown": 0.0,
        "sharpe": 0.0,
        "total_trades": 0,
        "win_rate": 0.0,
        "profit_factor": 0.0,
        "total_orders": 0,
        "filled_orders": 0,
        "rejected_orders": 0,
        "total_fees": 0.0,
    }
    mock_result.trades = pd.DataFrame()
    mock_engine = MagicMock()
    mock_engine.run_with_order_layer.return_value = mock_result
    mock_engine.execution_results = []

    with (
        patch.object(demo_script, "BacktestEngine", return_value=mock_engine),
        patch.object(demo_script, "load_strategy", return_value=lambda df, p: df["close"] * 0),
        patch.object(demo_script, "log_backtest_result", return_value="mock-run-id") as log_mock,
        patch("src.core.experiments.append_experiment_record") as append_mock,
    ):
        main(["--strategy", "ma_crossover", "--bars", "50"])

    log_mock.assert_called_once()
    append_mock.assert_not_called()


def test_resolve_strategy_no_network_calls() -> None:
    with patch("urllib.request.urlopen") as urlopen:
        load_strategy("ma_crossover")
    urlopen.assert_not_called()


def test_parse_args_defaults_unchanged() -> None:
    args = parse_args([])
    assert args.strategy == "ma_crossover"
    assert args.symbol == "BTC/EUR"
    assert args.bars == 200
