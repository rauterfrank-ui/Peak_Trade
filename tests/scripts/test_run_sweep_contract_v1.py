"""
run_sweep.py: legacy contract-first static tests (offline, fail-closed).

Locks current create_strategy_from_config() bypass semantics and known
False-Confidence risks. EQUIVALENCE_NOT_PROVEN vs load_strategy() migration.
"""

from __future__ import annotations

import ast
import importlib
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import scripts.run_sweep as run_sweep_script

TARGET_SCRIPT = project_root / "scripts/run_sweep.py"
MA_CROSSOVER_KEY = "ma_crossover"
EQUIVALENCE_NOT_PROVEN = "EQUIVALENCE_NOT_PROVEN"


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


def _minimal_cfg(strategy_key: str, **strategy_params: object) -> MagicMock:
    raw: dict[str, Any] = {
        "environment": {"mode": "backtest"},
        "strategy": {
            strategy_key: dict(strategy_params),
        },
    }
    cfg = MagicMock()
    cfg.raw = raw

    def _get(path: str, default=None):
        node = raw
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    cfg.get.side_effect = _get
    return cfg


def _apply_grid_params_like_run_sweep(strategy: object, params: dict[str, Any]) -> None:
    for key, value in params.items():
        if hasattr(strategy, key):
            setattr(strategy, key, value)


class DummyConfig:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def get(self, key: str, default=None):
        node = self._data
        for part in key.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return default
        return node


# ---------------------------------------------------------------------------
# AST / static guards — migration not completed
# ---------------------------------------------------------------------------


def test_module_imports_without_main_side_effects() -> None:
    with patch.object(run_sweep_script, "main") as main_mock:
        importlib.reload(run_sweep_script)
    main_mock.assert_not_called()


def test_source_still_uses_create_strategy_from_config_bypass() -> None:
    tree = ast.parse(_read_source())
    imported = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module
        for alias in node.names
    }
    assert "create_strategy_from_config" in imported


def test_source_has_no_load_strategy_migration() -> None:
    assert "load_strategy" not in _read_source()


def test_equivalence_not_proven_marker_present_in_test_owner() -> None:
    owner_source = Path(__file__).read_text(encoding="utf-8")
    assert EQUIVALENCE_NOT_PROVEN in owner_source


def test_run_single_backtest_has_no_long_only_replace_wrapper() -> None:
    tree = ast.parse(_read_source())
    fn = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_single_backtest"
    )
    fn_source = ast.get_source_segment(_read_source(), fn) or ""
    assert "replace(-1, 0)" not in fn_source
    assert "replace({-1: 0})" not in fn_source


# ---------------------------------------------------------------------------
# Grid override loss + parameter alias mismatch
# ---------------------------------------------------------------------------


def test_grid_short_window_long_window_not_applied_to_ma_crossover() -> None:
    from src.strategies.registry import create_strategy_from_config

    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=20, slow_window=50)
    strategy = create_strategy_from_config(MA_CROSSOVER_KEY, cfg)
    baseline_fast = strategy.fast_window
    baseline_slow = strategy.slow_window

    grid_params = {"short_window": 5, "long_window": 100}
    _apply_grid_params_like_run_sweep(strategy, grid_params)

    assert not hasattr(strategy, "short_window")
    assert not hasattr(strategy, "long_window")
    assert strategy.fast_window == baseline_fast
    assert strategy.slow_window == baseline_slow


def test_short_window_long_window_not_equivalent_to_fast_window_slow_window() -> None:
    from src.strategies.registry import create_strategy_from_config

    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=20, slow_window=50)
    strategy = create_strategy_from_config(MA_CROSSOVER_KEY, cfg)

    canonical_attrs = {"fast_window", "slow_window", "price_col"}
    grid_alias_attrs = {"short_window", "long_window"}

    assert grid_alias_attrs.isdisjoint(canonical_attrs)
    for alias in grid_alias_attrs:
        assert not hasattr(strategy, alias)


def test_grid_fast_window_slow_window_are_applied_when_present() -> None:
    from src.strategies.registry import create_strategy_from_config

    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=20, slow_window=50)
    strategy = create_strategy_from_config(MA_CROSSOVER_KEY, cfg)

    _apply_grid_params_like_run_sweep(strategy, {"fast_window": 8, "slow_window": 40})

    assert strategy.fast_window == 8
    assert strategy.slow_window == 40


# ---------------------------------------------------------------------------
# strategy.config drift
# ---------------------------------------------------------------------------


def test_setattr_does_not_sync_strategy_config() -> None:
    from src.strategies.registry import create_strategy_from_config

    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=20, slow_window=50)
    strategy = create_strategy_from_config(MA_CROSSOVER_KEY, cfg)
    config_before = dict(strategy.config)

    _apply_grid_params_like_run_sweep(strategy, {"fast_window": 7, "slow_window": 35})

    assert strategy.fast_window == 7
    assert strategy.slow_window == 35
    assert strategy.config["fast_window"] == config_before["fast_window"]
    assert strategy.config["slow_window"] == config_before["slow_window"]


# ---------------------------------------------------------------------------
# Engine strategy_params ignored by closure
# ---------------------------------------------------------------------------


def test_closure_ignores_engine_strategy_params_for_signal_generation() -> None:
    from src.core.peak_config import PeakConfig
    from src.strategies.registry import create_strategy_from_config

    raw = {
        "environment": {"mode": "backtest"},
        "strategy": {MA_CROSSOVER_KEY: {"fast_window": 20, "slow_window": 50}},
    }
    cfg = PeakConfig(raw=raw)
    df = _sample_ohlcv()
    grid_params = {"fast_window": 5, "slow_window": 30}

    strategy = create_strategy_from_config(MA_CROSSOVER_KEY, cfg)
    _apply_grid_params_like_run_sweep(strategy, grid_params)
    expected_from_setattr = strategy.generate_signals(df)

    strategy_engine_would_use = create_strategy_from_config(MA_CROSSOVER_KEY, cfg)
    strategy_engine_would_use.fast_window = 5
    strategy_engine_would_use.slow_window = 70
    expected_if_engine_params_used = strategy_engine_would_use.generate_signals(df)

    captured: dict[str, Any] = {}

    def fake_run_realistic(**kwargs):
        captured["engine_params"] = dict(kwargs["strategy_params"])
        out = kwargs["strategy_signal_fn"](kwargs["df"], {"fast_window": 5, "slow_window": 70})
        captured["closure_output"] = out
        mock_result = MagicMock()
        mock_result.stats = {}
        return mock_result

    with (
        patch.object(
            run_sweep_script, "build_position_sizer_from_config", return_value=MagicMock()
        ),
        patch.object(run_sweep_script, "build_risk_manager_from_config", return_value=MagicMock()),
        patch.object(
            run_sweep_script.BacktestEngine, "run_realistic", side_effect=fake_run_realistic
        ),
    ):
        run_sweep_script.run_single_backtest(
            df=df,
            strategy_key=MA_CROSSOVER_KEY,
            params=grid_params,
            cfg=cfg,
        )

    pd.testing.assert_series_equal(captured["closure_output"], expected_from_setattr)
    assert not captured["closure_output"].equals(expected_if_engine_params_used)
    assert captured["engine_params"] == grid_params


# ---------------------------------------------------------------------------
# Closure binding — single OOP instance
# ---------------------------------------------------------------------------


def test_closure_binds_single_strategy_instance_without_rebind() -> None:
    from src.core.peak_config import PeakConfig

    raw = {
        "environment": {"mode": "backtest"},
        "strategy": {MA_CROSSOVER_KEY: {"fast_window": 20, "slow_window": 50}},
    }
    cfg = PeakConfig(raw=raw)
    df = _sample_ohlcv()
    binding: dict[str, Any] = {"instance_ids": [], "generate_calls": 0}

    class TrackingStrategy:
        _instances = 0

        def __init__(self) -> None:
            TrackingStrategy._instances += 1
            self._id = id(self)
            self.fast_window = 20
            self.slow_window = 50
            self.config = {"fast_window": 20, "slow_window": 50}

        def generate_signals(self, data: pd.DataFrame) -> pd.Series:
            binding["generate_calls"] += 1
            binding["instance_ids"].append(self._id)
            return pd.Series(0, index=data.index)

    mock_result = MagicMock()
    mock_result.stats = {}

    with (
        patch.object(
            run_sweep_script,
            "create_strategy_from_config",
            return_value=TrackingStrategy(),
        ),
        patch.object(
            run_sweep_script, "build_position_sizer_from_config", return_value=MagicMock()
        ),
        patch.object(run_sweep_script, "build_risk_manager_from_config", return_value=MagicMock()),
        patch.object(
            run_sweep_script.BacktestEngine,
            "run_realistic",
            side_effect=lambda **kwargs: (
                kwargs["strategy_signal_fn"](kwargs["df"], kwargs["strategy_params"]),
                mock_result,
            )[1],
        ),
    ):
        run_sweep_script.run_single_backtest(
            df=df,
            strategy_key=MA_CROSSOVER_KEY,
            params={"fast_window": 10, "slow_window": 30},
            cfg=cfg,
        )

    assert TrackingStrategy._instances == 1
    assert binding["generate_calls"] == 1
    assert len(set(binding["instance_ids"])) == 1


# ---------------------------------------------------------------------------
# Registry gates — create_strategy_from_config path preserved
# ---------------------------------------------------------------------------


def test_run_single_backtest_propagates_registry_gate_failure() -> None:
    cfg = DummyConfig(
        {
            "environment": {"mode": "backtest"},
            "strategy": {"ehlers_cycle_filter": {}},
        }
    )
    df = _sample_ohlcv()

    with (
        patch.object(
            run_sweep_script, "build_position_sizer_from_config", return_value=MagicMock()
        ),
        patch.object(run_sweep_script, "build_risk_manager_from_config", return_value=MagicMock()),
        pytest.raises(ValueError, match="R&D-only"),
    ):
        run_sweep_script.run_single_backtest(
            df=df,
            strategy_key="ehlers_cycle_filter",
            params={},
            cfg=cfg,
        )


def test_create_strategy_from_config_live_gate_blocks_non_live_ready() -> None:
    from src.strategies.registry import create_strategy_from_config

    cfg = DummyConfig(
        {
            "environment": {"mode": "live"},
            "research": {"allow_r_and_d_strategies": True},
            "strategy": {"ehlers_cycle_filter": {}},
        }
    )
    with pytest.raises(ValueError, match="IS_LIVE_READY=False"):
        create_strategy_from_config("ehlers_cycle_filter", cfg)


def test_create_strategy_from_config_environment_gate_blocks_disallowed_env() -> None:
    from src.strategies.registry import create_strategy_from_config

    cfg = DummyConfig(
        {
            "environment": {"mode": "testnet"},
            "research": {"allow_r_and_d_strategies": True},
            "strategy": {"ehlers_cycle_filter": {}},
        }
    )
    with pytest.raises(ValueError, match="not allowed in environment"):
        create_strategy_from_config("ehlers_cycle_filter", cfg)


# ---------------------------------------------------------------------------
# Long-only wrapper absent vs sweep_parameters
# ---------------------------------------------------------------------------


def test_closure_preserves_negative_signals_without_replace_wrapper() -> None:
    df = _sample_ohlcv()[:5]
    negative_signals = pd.Series([1, -1, 0, -1, 1], index=df.index)

    class NegativeSignalStrategy:
        fast_window = 20
        slow_window = 50
        config = {"fast_window": 20, "slow_window": 50}

        def generate_signals(self, data: pd.DataFrame) -> pd.Series:
            return negative_signals

    mock_result = MagicMock()
    mock_result.stats = {}
    captured: dict[str, Any] = {}

    def fake_run_realistic(**kwargs):
        captured["signals"] = kwargs["strategy_signal_fn"](kwargs["df"], kwargs["strategy_params"])
        return mock_result

    with (
        patch.object(
            run_sweep_script,
            "create_strategy_from_config",
            return_value=NegativeSignalStrategy(),
        ),
        patch.object(
            run_sweep_script, "build_position_sizer_from_config", return_value=MagicMock()
        ),
        patch.object(run_sweep_script, "build_risk_manager_from_config", return_value=MagicMock()),
        patch.object(
            run_sweep_script.BacktestEngine, "run_realistic", side_effect=fake_run_realistic
        ),
    ):
        run_sweep_script.run_single_backtest(
            df=df,
            strategy_key=MA_CROSSOVER_KEY,
            params={},
            cfg=_minimal_cfg(MA_CROSSOVER_KEY),
        )

    assert captured["signals"].tolist() == [1, -1, 0, -1, 1]


def test_sweep_parameters_applies_long_only_wrapper_contrast() -> None:
    import scripts.sweep_parameters as sweep_parameters_script

    source = (project_root / "scripts/sweep_parameters.py").read_text(encoding="utf-8")
    assert "replace(-1, 0)" in source
    run_sweep_fn_source = ast.get_source_segment(
        _read_source(),
        next(
            n
            for n in ast.parse(_read_source()).body
            if isinstance(n, ast.FunctionDef) and n.name == "run_single_backtest"
        ),
    )
    assert run_sweep_fn_source is not None
    assert "replace(-1, 0)" not in run_sweep_fn_source
    assert hasattr(sweep_parameters_script, "run_backtest_for_params")


# ---------------------------------------------------------------------------
# stop_pct contract
# ---------------------------------------------------------------------------


def test_stop_pct_falls_back_to_engine_default_when_absent_from_grid() -> None:
    captured: dict[str, Any] = {}
    mock_result = MagicMock()
    mock_result.stats = {}

    def fake_run_realistic(**kwargs):
        captured["strategy_params"] = dict(kwargs["strategy_params"])
        return mock_result

    with (
        patch.object(
            run_sweep_script, "build_position_sizer_from_config", return_value=MagicMock()
        ),
        patch.object(run_sweep_script, "build_risk_manager_from_config", return_value=MagicMock()),
        patch.object(
            run_sweep_script.BacktestEngine, "run_realistic", side_effect=fake_run_realistic
        ),
        patch.object(
            run_sweep_script,
            "create_strategy_from_config",
            return_value=MagicMock(generate_signals=lambda data: pd.Series(0, index=data.index)),
        ),
    ):
        run_sweep_script.run_single_backtest(
            df=_sample_ohlcv(),
            strategy_key=MA_CROSSOVER_KEY,
            params={"fast_window": 10, "slow_window": 30},
            cfg=_minimal_cfg(MA_CROSSOVER_KEY),
        )

    assert "stop_pct" not in captured["strategy_params"]


def test_stop_pct_passes_through_when_present_in_grid_params() -> None:
    captured: dict[str, Any] = {}
    mock_result = MagicMock()
    mock_result.stats = {}

    def fake_run_realistic(**kwargs):
        captured["strategy_params"] = dict(kwargs["strategy_params"])
        return mock_result

    grid = {"fast_window": 10, "slow_window": 30, "stop_pct": 0.05}

    with (
        patch.object(
            run_sweep_script, "build_position_sizer_from_config", return_value=MagicMock()
        ),
        patch.object(run_sweep_script, "build_risk_manager_from_config", return_value=MagicMock()),
        patch.object(
            run_sweep_script.BacktestEngine, "run_realistic", side_effect=fake_run_realistic
        ),
        patch.object(
            run_sweep_script,
            "create_strategy_from_config",
            return_value=MagicMock(generate_signals=lambda data: pd.Series(0, index=data.index)),
        ),
    ):
        run_sweep_script.run_single_backtest(
            df=_sample_ohlcv(),
            strategy_key=MA_CROSSOVER_KEY,
            params=grid,
            cfg=_minimal_cfg(MA_CROSSOVER_KEY, stop_pct=0.03),
        )

    assert captured["strategy_params"]["stop_pct"] == 0.05


def test_stop_pct_not_sourced_from_strategy_config_section_by_default() -> None:
    captured: dict[str, Any] = {}
    mock_result = MagicMock()
    mock_result.stats = {}

    def fake_run_realistic(**kwargs):
        captured["strategy_params"] = dict(kwargs["strategy_params"])
        return mock_result

    with (
        patch.object(
            run_sweep_script, "build_position_sizer_from_config", return_value=MagicMock()
        ),
        patch.object(run_sweep_script, "build_risk_manager_from_config", return_value=MagicMock()),
        patch.object(
            run_sweep_script.BacktestEngine, "run_realistic", side_effect=fake_run_realistic
        ),
        patch.object(
            run_sweep_script,
            "create_strategy_from_config",
            return_value=MagicMock(generate_signals=lambda data: pd.Series(0, index=data.index)),
        ),
    ):
        run_sweep_script.run_single_backtest(
            df=_sample_ohlcv(),
            strategy_key=MA_CROSSOVER_KEY,
            params={"fast_window": 10, "slow_window": 30},
            cfg=_minimal_cfg(MA_CROSSOVER_KEY, stop_pct=0.03),
        )

    assert "stop_pct" not in captured["strategy_params"]


# ---------------------------------------------------------------------------
# Backtest call contract (no engine execution)
# ---------------------------------------------------------------------------


def test_backtest_call_contract_captured_without_engine_execution() -> None:
    from src.core.peak_config import PeakConfig

    raw = {
        "environment": {"mode": "backtest"},
        "strategy": {MA_CROSSOVER_KEY: {"fast_window": 20, "slow_window": 50}},
    }
    cfg = PeakConfig(raw=raw)
    df = _sample_ohlcv()
    params = {"fast_window": 12, "slow_window": 40}
    captured: dict[str, Any] = {"run_calls": 0}
    mock_result = MagicMock()
    mock_result.stats = {"total_return": 0.0}

    def fake_run_realistic(**kwargs):
        captured["run_calls"] += 1
        captured["df_is_same"] = kwargs["df"] is df
        captured["strategy_params"] = dict(kwargs["strategy_params"])
        captured["signal_fn"] = kwargs["strategy_signal_fn"]
        captured["fee_bps"] = kwargs.get("fee_bps", 0.0)
        captured["slippage_bps"] = kwargs.get("slippage_bps", 0.0)
        return mock_result

    with (
        patch.object(
            run_sweep_script, "build_position_sizer_from_config", return_value=MagicMock()
        ),
        patch.object(run_sweep_script, "build_risk_manager_from_config", return_value=MagicMock()),
        patch.object(
            run_sweep_script.BacktestEngine, "run_realistic", side_effect=fake_run_realistic
        ),
    ):
        stats = run_sweep_script.run_single_backtest(
            df=df,
            strategy_key=MA_CROSSOVER_KEY,
            params=params,
            cfg=cfg,
        )

    assert captured["run_calls"] == 1
    assert captured["df_is_same"] is True
    assert captured["strategy_params"] == params
    assert callable(captured["signal_fn"])
    assert captured["fee_bps"] == 0.0
    assert captured["slippage_bps"] == 0.0
    assert stats == {"total_return": 0.0}


def test_import_smoke_no_main_execution() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import scripts.run_sweep"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_cli_help_smoke(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        run_sweep_script.parse_args(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "Strategy Parameter Sweep" in out
