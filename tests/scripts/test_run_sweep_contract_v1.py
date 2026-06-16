"""
run_sweep.py: legacy contract-first static tests (offline, fail-closed).

Locks bounded parameter normalization, load_strategy() binding, and known
False-Confidence risks from PR #4230/#4232.
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
FORBIDDEN_IMPORTS = ("create_strategy_from_config",)
DATA_LOADER_OWNER = "scripts/run_backtest.py:load_ohlcv_data"
CANONICAL_REGISTRY_GATE_OWNER = "scripts/run_backtest.py:_validate_strategy_registry_gates"
FORBIDDEN_LOCAL_LOADER_DEFS = frozenset({"load_ohlcv_data", "generate_dummy_ohlcv"})
FORBIDDEN_LOCAL_REGISTRY_GATE_DEFS = frozenset({"_validate_strategy_registry_gates"})


def _read_source() -> str:
    return TARGET_SCRIPT.read_text(encoding="utf-8")


def _local_function_defs() -> set[str]:
    tree = ast.parse(_read_source())
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


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


def _apply_effective_params_like_run_sweep(
    strategy: object,
    strategy_key: str,
    effective: dict[str, Any],
) -> None:
    run_sweep_script._apply_effective_params_to_strategy(strategy, strategy_key, effective)


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


def test_source_has_no_local_loader_or_dummy_definitions() -> None:
    local_defs = _local_function_defs()
    assert FORBIDDEN_LOCAL_LOADER_DEFS.isdisjoint(local_defs)


def test_source_imports_canonical_data_loader() -> None:
    source = _read_source()
    assert "load_ohlcv_data" in source
    assert "scripts.run_backtest" in source


def test_load_ohlcv_data_import_identity_is_canonical_owner() -> None:
    import scripts.run_backtest as run_backtest_script

    assert run_sweep_script.load_ohlcv_data is run_backtest_script.load_ohlcv_data


def test_main_forwards_load_ohlcv_arguments_to_canonical_loader(tmp_path, monkeypatch) -> None:
    cfg_path = tmp_path / "cfg.toml"
    cfg_path.write_text("[environment]\nmode = 'backtest'\n", encoding="utf-8")
    captured: dict[str, object] = {}
    sample_df = _sample_ohlcv()

    def capture_loader(
        data_file,
        start_date,
        end_date,
        n_bars,
        verbose=False,
    ):
        captured.update(
            {
                "data_file": data_file,
                "start_date": start_date,
                "end_date": end_date,
                "n_bars": n_bars,
                "verbose": verbose,
            }
        )
        return sample_df

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_sweep.py",
            "--config",
            str(cfg_path),
            "--strategy",
            MA_CROSSOVER_KEY,
            "--grid",
            '{"fast_window":[5], "slow_window":[20]}',
            "--data-file",
            "data/btc.csv",
            "--bars",
            "250",
            "--verbose",
        ],
    )

    backtest_calls: list[dict[str, object]] = []

    def capture_backtest(**kwargs):
        backtest_calls.append(dict(kwargs))
        return {}

    with (
        patch.object(run_sweep_script, "load_ohlcv_data", side_effect=capture_loader),
        patch.object(run_sweep_script, "run_single_backtest", side_effect=capture_backtest),
        patch.object(run_sweep_script, "log_sweep_run", return_value=1),
    ):
        rc = run_sweep_script.main()

    assert rc == 0
    assert captured == {
        "data_file": "data/btc.csv",
        "start_date": None,
        "end_date": None,
        "n_bars": 250,
        "verbose": True,
    }
    assert len(backtest_calls) == 1
    assert backtest_calls[0]["df"] is sample_df


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


def test_grid_short_window_long_window_normalized_for_ma_crossover() -> None:
    normalized = run_sweep_script._normalize_sweep_grid_params(
        MA_CROSSOVER_KEY,
        {"short_window": 5, "long_window": 100},
    )
    assert normalized == {"fast_window": 5, "slow_window": 100}


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
    effective = run_sweep_script._merge_effective_parameters(
        MA_CROSSOVER_KEY,
        {"fast_window": 8, "slow_window": 40},
        strategy_defaults=run_sweep_script._strategy_class_defaults(MA_CROSSOVER_KEY),
        strategy_config=run_sweep_script._strategy_config_section(cfg, MA_CROSSOVER_KEY),
    )
    _apply_effective_params_like_run_sweep(strategy, MA_CROSSOVER_KEY, effective)

    assert strategy.fast_window == 8
    assert strategy.slow_window == 40


# ---------------------------------------------------------------------------
# strategy.config drift
# ---------------------------------------------------------------------------


def test_effective_params_sync_strategy_config() -> None:
    from src.strategies.registry import create_strategy_from_config

    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=20, slow_window=50)
    strategy = create_strategy_from_config(MA_CROSSOVER_KEY, cfg)
    effective = run_sweep_script._merge_effective_parameters(
        MA_CROSSOVER_KEY,
        {"fast_window": 7, "slow_window": 35},
        strategy_defaults=run_sweep_script._strategy_class_defaults(MA_CROSSOVER_KEY),
        strategy_config=run_sweep_script._strategy_config_section(cfg, MA_CROSSOVER_KEY),
    )
    _apply_effective_params_like_run_sweep(strategy, MA_CROSSOVER_KEY, effective)

    assert strategy.fast_window == 7
    assert strategy.slow_window == 35
    assert strategy.config["fast_window"] == 7
    assert strategy.config["slow_window"] == 35


# ---------------------------------------------------------------------------
# Engine strategy_params ignored by closure
# ---------------------------------------------------------------------------


def test_closure_uses_engine_strategy_params_for_signal_generation() -> None:
    from src.core.peak_config import PeakConfig
    from src.strategies import load_strategy

    raw = {
        "environment": {"mode": "backtest"},
        "strategy": {MA_CROSSOVER_KEY: {"fast_window": 20, "slow_window": 50}},
    }
    cfg = PeakConfig(raw=raw)
    df = _sample_ohlcv()
    grid_params = {"fast_window": 5, "slow_window": 30}

    effective = run_sweep_script._merge_effective_parameters(
        MA_CROSSOVER_KEY,
        grid_params,
        strategy_defaults=run_sweep_script._strategy_class_defaults(MA_CROSSOVER_KEY),
        strategy_config=run_sweep_script._strategy_config_section(cfg, MA_CROSSOVER_KEY),
    )
    expected_if_engine_params_used = load_strategy(MA_CROSSOVER_KEY)(df, effective)

    captured: dict[str, Any] = {}

    def fake_run_realistic(**kwargs):
        captured["engine_params"] = dict(kwargs["strategy_params"])
        out = kwargs["strategy_signal_fn"](kwargs["df"], kwargs["strategy_params"])
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

    pd.testing.assert_series_equal(captured["closure_output"], expected_if_engine_params_used)
    assert captured["engine_params"]["fast_window"] == 5
    assert captured["engine_params"]["slow_window"] == 30
    assert captured["engine_params"]["stop_pct"] == run_sweep_script._ENGINE_STOP_PCT_DEFAULT


# ---------------------------------------------------------------------------
# Closure binding — single OOP instance
# ---------------------------------------------------------------------------


def test_closure_creates_fresh_load_strategy_binding_per_call() -> None:
    from src.core.peak_config import PeakConfig

    raw = {
        "environment": {"mode": "backtest"},
        "strategy": {MA_CROSSOVER_KEY: {"fast_window": 20, "slow_window": 50}},
    }
    cfg = PeakConfig(raw=raw)
    df = _sample_ohlcv()
    binding: dict[str, Any] = {"call_count": 0, "param_snapshots": []}

    def tracking_signal_fn(data: pd.DataFrame, params: dict[str, Any]) -> pd.Series:
        binding["call_count"] += 1
        binding["param_snapshots"].append(dict(params))
        return pd.Series(0, index=data.index)

    mock_result = MagicMock()
    mock_result.stats = {}

    with (
        patch.object(run_sweep_script, "load_strategy", return_value=tracking_signal_fn),
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

    assert binding["call_count"] == 1
    assert binding["param_snapshots"][0]["fast_window"] == 10
    assert binding["param_snapshots"][0]["slow_window"] == 30


# ---------------------------------------------------------------------------
# Registry gates — canonical _validate_strategy_registry_gates reuse
# ---------------------------------------------------------------------------


def test_source_has_no_local_registry_gate_definition() -> None:
    local_defs = _local_function_defs()
    assert FORBIDDEN_LOCAL_REGISTRY_GATE_DEFS.isdisjoint(local_defs)


def test_validate_strategy_registry_gates_import_identity_is_canonical_owner() -> None:
    import scripts.run_backtest as run_backtest_script

    assert (
        run_sweep_script._validate_strategy_registry_gates
        is run_backtest_script._validate_strategy_registry_gates
    )


def test_source_imports_canonical_registry_gate_validator() -> None:
    source = _read_source()
    assert "_validate_strategy_registry_gates" in source
    assert "scripts.run_backtest" in source


def test_unknown_strategy_fails_closed_at_registry_gates() -> None:
    from src.core.peak_config import PeakConfig

    cfg = PeakConfig(raw={"environment": {"mode": "backtest"}})
    with pytest.raises(KeyError):
        run_sweep_script._validate_strategy_registry_gates("definitely_not_a_strategy_xyz", cfg)


def test_run_single_backtest_invokes_registry_gates_before_parameter_merge() -> None:
    cfg = DummyConfig(
        {
            "environment": {"mode": "backtest"},
            "strategy": {MA_CROSSOVER_KEY: {"fast_window": 10, "slow_window": 30}},
        }
    )
    df = _sample_ohlcv()
    call_order: list[str] = []
    gate_mock = MagicMock(side_effect=lambda key, config: call_order.append("gates"))
    defaults_mock = MagicMock(
        side_effect=lambda key: (
            call_order.append("defaults"),
            {"fast_window": 20, "slow_window": 50},
        )[1]
    )
    merge_mock = MagicMock(
        side_effect=lambda key, params, **kwargs: (
            call_order.append("merge"),
            {"fast_window": 10, "slow_window": 30, "stop_pct": 0.02},
        )[1]
    )

    with (
        patch.object(
            run_sweep_script, "build_position_sizer_from_config", return_value=MagicMock()
        ),
        patch.object(run_sweep_script, "build_risk_manager_from_config", return_value=MagicMock()),
        patch.object(run_sweep_script, "_validate_strategy_registry_gates", gate_mock),
        patch.object(run_sweep_script, "_strategy_class_defaults", defaults_mock),
        patch.object(run_sweep_script, "_merge_effective_parameters", merge_mock),
        patch.object(
            run_sweep_script,
            "load_strategy",
            return_value=lambda data, params: pd.Series(0, index=data.index),
        ),
        patch.object(run_sweep_script.BacktestEngine, "run_realistic") as run_realistic,
    ):
        run_realistic.return_value = MagicMock(stats={})
        run_sweep_script.run_single_backtest(
            df=df,
            strategy_key=MA_CROSSOVER_KEY,
            params={"fast_window": 10, "slow_window": 30},
            cfg=cfg,
        )

    gate_mock.assert_called_once_with(MA_CROSSOVER_KEY, cfg)
    assert call_order == ["gates", "defaults", "merge"]


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


def test_validate_strategy_registry_gates_live_gate_blocks_non_live_ready() -> None:
    cfg = DummyConfig(
        {
            "environment": {"mode": "live"},
            "research": {"allow_r_and_d_strategies": True},
            "strategy": {"ehlers_cycle_filter": {}},
        }
    )
    with pytest.raises(ValueError, match="IS_LIVE_READY=False"):
        run_sweep_script._validate_strategy_registry_gates("ehlers_cycle_filter", cfg)


def test_validate_strategy_registry_gates_environment_gate_blocks_disallowed_env() -> None:
    cfg = DummyConfig(
        {
            "environment": {"mode": "testnet"},
            "research": {"allow_r_and_d_strategies": True},
            "strategy": {"ehlers_cycle_filter": {}},
        }
    )
    with pytest.raises(ValueError, match="not allowed in environment"):
        run_sweep_script._validate_strategy_registry_gates("ehlers_cycle_filter", cfg)


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
            run_sweep_script, "build_position_sizer_from_config", return_value=MagicMock()
        ),
        patch.object(run_sweep_script, "build_risk_manager_from_config", return_value=MagicMock()),
        patch.object(
            run_sweep_script.BacktestEngine, "run_realistic", side_effect=fake_run_realistic
        ),
        patch.object(
            run_sweep_script,
            "load_strategy",
            return_value=lambda data, params: negative_signals,
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
            "load_strategy",
            return_value=lambda data, params: pd.Series(0, index=data.index),
        ),
    ):
        run_sweep_script.run_single_backtest(
            df=_sample_ohlcv(),
            strategy_key=MA_CROSSOVER_KEY,
            params={"fast_window": 10, "slow_window": 30},
            cfg=_minimal_cfg(MA_CROSSOVER_KEY),
        )

    assert captured["strategy_params"]["stop_pct"] == run_sweep_script._ENGINE_STOP_PCT_DEFAULT


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
            "load_strategy",
            return_value=lambda data, params: pd.Series(0, index=data.index),
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
            "load_strategy",
            return_value=lambda data, params: pd.Series(0, index=data.index),
        ),
    ):
        run_sweep_script.run_single_backtest(
            df=_sample_ohlcv(),
            strategy_key=MA_CROSSOVER_KEY,
            params={"fast_window": 10, "slow_window": 30},
            cfg=_minimal_cfg(MA_CROSSOVER_KEY, stop_pct=0.03),
        )

    assert captured["strategy_params"]["stop_pct"] == run_sweep_script._ENGINE_STOP_PCT_DEFAULT
    assert captured["strategy_params"]["stop_pct"] != 0.03


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
    expected_params = run_sweep_script._merge_effective_parameters(
        MA_CROSSOVER_KEY,
        params,
        strategy_defaults=run_sweep_script._strategy_class_defaults(MA_CROSSOVER_KEY),
        strategy_config=run_sweep_script._strategy_config_section(cfg, MA_CROSSOVER_KEY),
    )
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
    assert captured["strategy_params"] == expected_params
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


# ---------------------------------------------------------------------------
# Target parameter normalization contract (test-local reference only)
# ---------------------------------------------------------------------------
# Defines the intended post-normalization semantics for a future production
# slice. Does NOT claim scripts/run_sweep.py already satisfies this contract.
# ---------------------------------------------------------------------------

TARGET_PARAMETER_ALIAS_TABLE: dict[str, dict[str, str]] = {
    MA_CROSSOVER_KEY: {
        "short_window": "fast_window",
        "long_window": "slow_window",
    },
    "rsi_reversion": {
        "rsi_period": "rsi_window",
        "entry_threshold": "lower",
        "exit_threshold": "upper",
    },
}

TARGET_ENGINE_STOP_PCT_DEFAULT = 0.02

TARGET_STRATEGY_CANONICAL_KEYS: dict[str, frozenset[str]] = {
    MA_CROSSOVER_KEY: frozenset({"fast_window", "slow_window", "price_col"}),
    "rsi_reversion": frozenset(
        {
            "rsi_window",
            "lower",
            "upper",
            "exit_lower",
            "exit_upper",
            "use_trend_filter",
            "trend_ma_window",
            "use_wilder",
            "price_col",
        }
    ),
}

TARGET_SWEEP_ENGINE_KEYS = frozenset({"stop_pct"})

LONG_ONLY_DECISION_STATUS = "UNRESOLVED_REQUIRES_SEMANTIC_GO"

TARGET_PARAMETER_SOURCE_PRECEDENCE = (
    "strategy_defaults",
    "strategy_config",
    "normalized_sweep_grid",
    "engine_params_stop_pct_only",
)


class TargetNormalizationContractError(ValueError):
    """Test-local fail-closed rejection for target normalization contract."""


def _allowed_keys_for_strategy(strategy_key: str) -> frozenset[str]:
    aliases = TARGET_PARAMETER_ALIAS_TABLE.get(strategy_key, {})
    return (
        TARGET_STRATEGY_CANONICAL_KEYS[strategy_key]
        | TARGET_SWEEP_ENGINE_KEYS
        | frozenset(aliases.keys())
    )


def _resolve_aliases_target_contract(
    strategy_key: str,
    raw_params: dict[str, Any],
) -> dict[str, Any]:
    if strategy_key not in TARGET_PARAMETER_ALIAS_TABLE:
        raise TargetNormalizationContractError(
            f"unsupported strategy_key for alias table: {strategy_key!r}"
        )

    alias_table = TARGET_PARAMETER_ALIAS_TABLE[strategy_key]
    allowed = _allowed_keys_for_strategy(strategy_key)
    normalized: dict[str, Any] = {}

    for key in sorted(raw_params.keys()):
        value = raw_params[key]
        if key not in allowed:
            raise TargetNormalizationContractError(f"unknown key rejected: {key!r}")

        canonical = alias_table.get(key, key)
        if canonical in normalized and normalized[canonical] != value:
            raise TargetNormalizationContractError(
                f"conflicting alias/canonical for {canonical!r}: "
                f"{normalized[canonical]!r} vs {value!r}"
            )
        normalized[canonical] = value

    return normalized


def _resolve_stop_pct_target_contract(
    *,
    normalized_grid: dict[str, Any],
    engine_stop_pct: float | None = None,
) -> float:
    if "stop_pct" in normalized_grid:
        return float(normalized_grid["stop_pct"])
    if engine_stop_pct is not None:
        return float(engine_stop_pct)
    return TARGET_ENGINE_STOP_PCT_DEFAULT


def _merge_parameter_sources_target_contract(
    strategy_key: str,
    raw_grid: dict[str, Any],
    *,
    strategy_defaults: dict[str, Any] | None = None,
    strategy_config: dict[str, Any] | None = None,
    engine_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    defaults = dict(strategy_defaults or {})
    config = dict(strategy_config or {})
    normalized_grid = _resolve_aliases_target_contract(strategy_key, raw_grid)

    effective: dict[str, Any] = {**defaults, **config, **normalized_grid}
    effective["stop_pct"] = _resolve_stop_pct_target_contract(
        normalized_grid=normalized_grid,
        engine_stop_pct=(engine_params or {}).get("stop_pct"),
    )
    return effective


def _apply_target_contract_strategy_surface(
    strategy_key: str,
    effective: dict[str, Any],
) -> dict[str, Any]:
    canonical = TARGET_STRATEGY_CANONICAL_KEYS[strategy_key]
    attrs = {k: effective[k] for k in canonical if k in effective}
    return {"attrs": attrs, "config": dict(attrs)}


def _target_engine_binding_uses_normalized_params(
    effective: dict[str, Any],
    engine_strategy_params: dict[str, Any],
) -> bool:
    return engine_strategy_params == effective


@pytest.mark.parametrize(
    ("alias", "canonical", "value"),
    [
        ("short_window", "fast_window", 5),
        ("long_window", "slow_window", 100),
    ],
)
def test_target_ma_crossover_alias_matrix_maps_each_alias(
    alias: str, canonical: str, value: int
) -> None:
    result = _resolve_aliases_target_contract(MA_CROSSOVER_KEY, {alias: value})
    assert result == {canonical: value}


def test_target_ma_crossover_alias_matrix_full_grid_combo() -> None:
    result = _resolve_aliases_target_contract(
        MA_CROSSOVER_KEY,
        {"short_window": 8, "long_window": 40},
    )
    assert result == {"fast_window": 8, "slow_window": 40}


@pytest.mark.parametrize(
    ("alias", "canonical", "value"),
    [
        ("rsi_period", "rsi_window", 14),
        ("entry_threshold", "lower", 25.0),
        ("exit_threshold", "upper", 55.0),
    ],
)
def test_target_rsi_reversion_alias_matrix_maps_each_alias(
    alias: str, canonical: str, value: float | int
) -> None:
    result = _resolve_aliases_target_contract("rsi_reversion", {alias: value})
    assert result == {canonical: value}


def test_target_rsi_reversion_alias_matrix_full_grid_combo() -> None:
    result = _resolve_aliases_target_contract(
        "rsi_reversion",
        {"rsi_period": 21, "entry_threshold": 30.0, "exit_threshold": 50.0},
    )
    assert result == {"rsi_window": 21, "lower": 30.0, "upper": 50.0}


def test_target_canonical_keys_pass_through_unchanged() -> None:
    ma = _resolve_aliases_target_contract(MA_CROSSOVER_KEY, {"fast_window": 12, "slow_window": 48})
    rsi = _resolve_aliases_target_contract(
        "rsi_reversion", {"rsi_window": 14, "lower": 30.0, "upper": 70.0}
    )
    assert ma == {"fast_window": 12, "slow_window": 48}
    assert rsi == {"rsi_window": 14, "lower": 30.0, "upper": 70.0}


def test_target_unknown_key_rejected_by_contract() -> None:
    with pytest.raises(TargetNormalizationContractError, match="unknown key"):
        _resolve_aliases_target_contract(MA_CROSSOVER_KEY, {"unknown_param": 1})


def test_target_conflicting_alias_and_canonical_rejected() -> None:
    with pytest.raises(TargetNormalizationContractError, match="conflicting"):
        _resolve_aliases_target_contract(
            MA_CROSSOVER_KEY,
            {"short_window": 5, "fast_window": 10},
        )


def test_target_identical_alias_canonical_double_spec_is_deterministic() -> None:
    result = _resolve_aliases_target_contract(
        MA_CROSSOVER_KEY,
        {"short_window": 7, "fast_window": 7, "long_window": 35, "slow_window": 35},
    )
    assert result == {"fast_window": 7, "slow_window": 35}


def test_target_no_cross_strategy_alias_application() -> None:
    with pytest.raises(TargetNormalizationContractError, match="unknown key"):
        _resolve_aliases_target_contract("rsi_reversion", {"short_window": 5})


def test_target_no_fuzzy_key_mapping() -> None:
    with pytest.raises(TargetNormalizationContractError, match="unknown key"):
        _resolve_aliases_target_contract(MA_CROSSOVER_KEY, {"fast_win": 10})


@pytest.mark.parametrize(
    "raw_params",
    [
        {"long_window": 100, "short_window": 5},
        {"short_window": 5, "long_window": 100},
    ],
)
def test_target_normalization_independent_of_dict_insertion_order(
    raw_params: dict[str, int],
) -> None:
    result = _resolve_aliases_target_contract(MA_CROSSOVER_KEY, raw_params)
    assert result == {"fast_window": 5, "slow_window": 100}


def test_target_stop_pct_source_precedence_contract() -> None:
    grid_only = _merge_parameter_sources_target_contract(
        MA_CROSSOVER_KEY,
        {"fast_window": 10, "slow_window": 30, "stop_pct": 0.05},
        strategy_config={"stop_pct": 0.03},
    )
    assert grid_only["stop_pct"] == 0.05

    engine_layer = _merge_parameter_sources_target_contract(
        MA_CROSSOVER_KEY,
        {"fast_window": 10, "slow_window": 30},
        engine_params={"stop_pct": 0.04},
    )
    assert engine_layer["stop_pct"] == 0.04


def test_target_missing_stop_pct_uses_engine_default_0_02() -> None:
    effective = _merge_parameter_sources_target_contract(
        MA_CROSSOVER_KEY,
        {"fast_window": 10, "slow_window": 30},
        strategy_config={"stop_pct": 0.03},
    )
    assert effective["stop_pct"] == TARGET_ENGINE_STOP_PCT_DEFAULT
    assert "stop_pct" not in _resolve_aliases_target_contract(
        MA_CROSSOVER_KEY, {"fast_window": 10, "slow_window": 30}
    )


def test_target_parameter_source_precedence_order() -> None:
    effective = _merge_parameter_sources_target_contract(
        MA_CROSSOVER_KEY,
        {"fast_window": 15},
        strategy_defaults={"fast_window": 5, "slow_window": 20},
        strategy_config={"slow_window": 25},
    )
    assert effective["fast_window"] == 15
    assert effective["slow_window"] == 25


def test_target_strategy_config_consistency_invariant() -> None:
    effective = _merge_parameter_sources_target_contract(
        MA_CROSSOVER_KEY,
        {"short_window": 9, "long_window": 45},
    )
    surface = _apply_target_contract_strategy_surface(MA_CROSSOVER_KEY, effective)
    assert surface["attrs"] == surface["config"]
    assert surface["attrs"]["fast_window"] == 9
    assert surface["attrs"]["slow_window"] == 45


def test_target_no_stateful_strategy_reuse_invariant() -> None:
    combo_a = _merge_parameter_sources_target_contract(
        MA_CROSSOVER_KEY, {"fast_window": 5, "slow_window": 20}
    )
    combo_b = _merge_parameter_sources_target_contract(
        MA_CROSSOVER_KEY, {"fast_window": 10, "slow_window": 40}
    )
    surface_a = _apply_target_contract_strategy_surface(MA_CROSSOVER_KEY, combo_a)
    surface_b = _apply_target_contract_strategy_surface(MA_CROSSOVER_KEY, combo_b)
    assert surface_a["attrs"] != surface_b["attrs"]
    assert surface_a is not surface_b


def test_target_engine_strategy_params_consumed_contract() -> None:
    effective = _merge_parameter_sources_target_contract(
        MA_CROSSOVER_KEY,
        {"short_window": 6, "long_window": 30},
    )
    assert _target_engine_binding_uses_normalized_params(effective, effective)
    legacy_grid_params = {"short_window": 6, "long_window": 30}
    assert legacy_grid_params != effective


def test_target_long_only_decision_unresolved_requires_semantic_go() -> None:
    assert LONG_ONLY_DECISION_STATUS == "UNRESOLVED_REQUIRES_SEMANTIC_GO"
    fn_source = ast.get_source_segment(
        _read_source(),
        next(
            n
            for n in ast.parse(_read_source()).body
            if isinstance(n, ast.FunctionDef) and n.name == "run_single_backtest"
        ),
    )
    assert fn_source is not None
    assert "replace(-1, 0)" not in fn_source


def test_production_implements_bounded_parameter_normalization() -> None:
    fn_source = ast.get_source_segment(
        _read_source(),
        next(
            n
            for n in ast.parse(_read_source()).body
            if isinstance(n, ast.FunctionDef) and n.name == "run_single_backtest"
        ),
    )
    assert fn_source is not None
    assert "_normalize_sweep_grid_params" in _read_source()
    assert "_merge_effective_parameters" in _read_source()
    assert "load_strategy" in fn_source
    assert "create_strategy_from_config" not in fn_source
    assert "hasattr(strategy, key)" not in fn_source

    ma_alias = run_sweep_script._normalize_sweep_grid_params(
        MA_CROSSOVER_KEY,
        {"short_window": 7, "long_window": 35},
    )
    assert ma_alias == {"fast_window": 7, "slow_window": 35}

    with pytest.raises(run_sweep_script.SweepParameterNormalizationError, match="unknown key"):
        run_sweep_script._normalize_sweep_grid_params(MA_CROSSOVER_KEY, {"unknown_param": 1})


def test_load_strategy_migration_completed() -> None:
    assert "load_strategy" in _read_source()
    tree = ast.parse(_read_source())
    imported = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module
        for alias in node.names
    }
    assert "create_strategy_from_config" not in imported
