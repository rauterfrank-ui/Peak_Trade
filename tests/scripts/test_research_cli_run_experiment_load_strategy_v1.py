"""
research_cli.run_experiment: canonical load_strategy() migration (offline, fail-closed).
"""

from __future__ import annotations

import ast
import subprocess
import sys
from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import scripts.research_cli as research_cli

TARGET_MODULE = project_root / "scripts/research_cli.py"
PRESET_ID = "armstrong_ecm_btc_longterm_v1"
PRESET_STRATEGY_KEY = "armstrong_cycle"
FORBIDDEN_NAMES = ("create_strategy_from_config",)


def _read_source() -> str:
    return TARGET_MODULE.read_text(encoding="utf-8")


def _run_experiment_source() -> str:
    tree = ast.parse(_read_source())
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "run_experiment":
            segment = ast.get_source_segment(_read_source(), node)
            assert segment is not None
            return segment
    raise AssertionError("run_experiment not found")


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


def _experiment_args(tmp_path: Path, **overrides: object) -> Namespace:
    defaults = {
        "preset": PRESET_ID,
        "symbol": None,
        "timeframe": None,
        "from_date": None,
        "to_date": None,
        "tag": "exp_test",
        "config": "config/config.toml",
        "presets_file": "config/r_and_d_presets.toml",
        "output_dir": str(tmp_path / "out"),
        "use_dummy_data": True,
        "dummy_bars": 80,
        "dry_run": False,
        "list_presets": False,
        "seed": 42,
        "verbose": False,
    }
    defaults.update(overrides)
    return Namespace(**defaults)


def test_run_experiment_source_has_no_create_strategy_from_config() -> None:
    source = _run_experiment_source()
    for forbidden in FORBIDDEN_NAMES:
        assert forbidden not in source


def test_run_experiment_source_uses_load_strategy() -> None:
    assert "load_strategy" in _run_experiment_source()


def test_run_experiment_source_is_distinct_from_prior_migration_owners() -> None:
    prior_owners = (
        "research_compare_strategies.py",
        "research_run_strategy.py",
        "run_market_scan.py",
        "scan_markets.py",
        "run_forward_signals.py",
        "run_sweep.py",
        "run_strategy_from_config.py",
        "demo_strategy_research.py",
    )
    assert TARGET_MODULE.name == "research_cli.py"
    for owner in prior_owners:
        assert TARGET_MODULE.name != owner


def test_run_strategy_profile_still_uses_registry_not_load_strategy() -> None:
    tree = ast.parse(_read_source())
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "run_strategy_profile":
            segment = ast.get_source_segment(_read_source(), node)
            assert segment is not None
            assert "get_strategy_spec" in segment
            assert "load_strategy" not in segment
            return
    raise AssertionError("run_strategy_profile not found")


def test_run_experiment_calls_load_strategy_and_passes_preset_parameters(
    tmp_path,
) -> None:
    captured: dict[str, object] = {}

    def fake_signal_fn(df, params):
        captured["params"] = dict(params)
        return pd.Series(np.zeros(len(df)), index=df.index)

    mock_result = MagicMock()
    mock_result.stats = {
        "total_return": 0.0,
        "max_drawdown": 0.0,
        "sharpe": 0.0,
        "total_trades": 0,
        "win_rate": 0.0,
        "profit_factor": 0.0,
    }
    mock_result.equity_curve = pd.Series([10000.0] * 80)

    args = _experiment_args(tmp_path)

    with (
        patch("src.strategies.load_strategy", return_value=fake_signal_fn) as load_strategy_mock,
        patch("src.core.peak_config.load_config") as load_config_mock,
        patch(
            "src.core.position_sizing.build_position_sizer_from_config",
            return_value=MagicMock(),
        ),
        patch(
            "src.core.risk.build_risk_manager_from_config",
            return_value=MagicMock(),
        ),
        patch("src.backtest.engine.BacktestEngine") as engine_cls,
    ):
        from src.core.peak_config import PeakConfig

        load_config_mock.return_value = PeakConfig(
            raw={
                "environment": {"mode": "backtest"},
                "strategy": {
                    PRESET_STRATEGY_KEY: {
                        "cycle_period_days": 100,
                    },
                },
            }
        )

        def run_realistic_side_effect(df, strategy_signal_fn, strategy_params, **kwargs):
            strategy_signal_fn(df, strategy_params)
            return mock_result

        engine_cls.return_value.run_realistic.side_effect = run_realistic_side_effect

        code = research_cli.run_experiment(args)

    assert code == 0
    load_strategy_mock.assert_called_once_with(PRESET_STRATEGY_KEY)
    assert captured["params"]["cycle_period_days"] == 3141
    assert captured["params"]["entry_threshold"] == 0.8


def test_isolated_load_strategy_binding_per_run_experiment_call(tmp_path) -> None:
    load_calls: list[str] = []

    def fake_signal_fn(df, params):
        return pd.Series(np.zeros(len(df)), index=df.index)

    def load_strategy_side_effect(strategy_key: str):
        load_calls.append(strategy_key)
        return fake_signal_fn

    mock_result = MagicMock()
    mock_result.stats = {
        "total_return": 0.0,
        "max_drawdown": 0.0,
        "sharpe": 0.0,
        "total_trades": 0,
        "win_rate": 0.0,
        "profit_factor": 0.0,
    }
    mock_result.equity_curve = pd.Series([10000.0] * 80)

    args = _experiment_args(tmp_path)

    with (
        patch(
            "src.strategies.load_strategy",
            side_effect=load_strategy_side_effect,
        ),
        patch("src.core.peak_config.load_config") as load_config_mock,
        patch(
            "src.core.position_sizing.build_position_sizer_from_config",
            return_value=MagicMock(),
        ),
        patch(
            "src.core.risk.build_risk_manager_from_config",
            return_value=MagicMock(),
        ),
        patch("src.backtest.engine.BacktestEngine") as engine_cls,
    ):
        from src.core.peak_config import PeakConfig

        load_config_mock.return_value = PeakConfig(raw={"environment": {"mode": "backtest"}})
        engine_cls.return_value.run_realistic.return_value = mock_result

        assert research_cli.run_experiment(args) == 0
        assert research_cli.run_experiment(args) == 0

    assert load_calls == [PRESET_STRATEGY_KEY, PRESET_STRATEGY_KEY]


def test_run_experiment_unknown_strategy_fail_closed(tmp_path) -> None:
    args = _experiment_args(tmp_path, preset="does_not_exist_preset_xyz")
    assert research_cli.run_experiment(args) == 1


def test_load_strategy_unknown_key_fail_closed() -> None:
    from src.strategies import load_strategy

    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("definitely_not_a_research_cli_experiment_strategy_xyz")


def test_load_strategy_no_network_calls() -> None:
    from src.strategies import load_strategy

    with patch("socket.socket.connect") as connect_mock:
        load_strategy(PRESET_STRATEGY_KEY)
    connect_mock.assert_not_called()


def test_ruff_format_check() -> None:
    targets = [
        str(project_root / "scripts/research_cli.py"),
        str(project_root / "tests/scripts/test_research_cli_run_experiment_load_strategy_v1.py"),
    ]
    subprocess.run(
        ["ruff", "format", "--check", *targets],
        check=True,
        cwd=project_root,
    )


def test_ruff_check() -> None:
    targets = [
        str(project_root / "scripts/research_cli.py"),
        str(project_root / "tests/scripts/test_research_cli_run_experiment_load_strategy_v1.py"),
    ]
    subprocess.run(
        ["ruff", "check", *targets],
        check=True,
        cwd=project_root,
    )
