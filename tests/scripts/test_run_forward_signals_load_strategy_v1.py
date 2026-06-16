"""
run_forward_signals: canonical load_strategy() migration (offline, fail-closed).
"""

from __future__ import annotations

import ast
import importlib
import inspect
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import numpy as np
import pandas as pd
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

import run_forward_signals as forward_runner

TARGET_SCRIPT = project_root / "scripts/run_forward_signals.py"
MA_CROSSOVER_KEY = "ma_crossover"
RSI_REVERSION_KEY = "rsi_reversion"

FORBIDDEN_IMPORTS = ("create_strategy_from_config",)
STRATEGY_PARAMS_BUILDER_OWNER = "scripts/run_backtest.py:_build_strategy_params_from_config"
FORBIDDEN_LOCAL_BUILDER_DEFS = frozenset({"_build_strategy_params_from_config"})
CANONICAL_REGISTRY_GATE_OWNER = "scripts/run_backtest.py:_validate_strategy_registry_gates"
FORBIDDEN_LOCAL_REGISTRY_GATE_DEFS = frozenset({"_validate_strategy_registry_gates"})


def _read_source() -> str:
    return TARGET_SCRIPT.read_text(encoding="utf-8")


def _local_function_defs() -> set[str]:
    tree = ast.parse(_read_source())
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def _minimal_cfg(strategy_key: str, **strategy_params: object) -> MagicMock:
    raw = {
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
    cfg.with_overrides.return_value = cfg
    return cfg


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


def test_module_imports_without_main_side_effects() -> None:
    with patch.object(forward_runner, "main") as main_mock:
        importlib.reload(forward_runner)
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


def test_source_has_no_local_builder_definition() -> None:
    local_defs = _local_function_defs()
    assert FORBIDDEN_LOCAL_BUILDER_DEFS.isdisjoint(local_defs)


def test_build_strategy_params_import_identity_is_canonical_owner() -> None:
    import scripts.run_backtest as run_backtest_script

    assert (
        forward_runner._build_strategy_params_from_config
        is run_backtest_script._build_strategy_params_from_config
    )


def test_source_imports_canonical_strategy_params_builder() -> None:
    source = _read_source()
    assert "_build_strategy_params_from_config" in source
    assert "scripts.run_backtest" in source


def test_build_strategy_params_includes_section_and_stop_pct() -> None:
    cfg = _minimal_cfg(
        MA_CROSSOVER_KEY,
        fast_window=10,
        slow_window=50,
        price_col="close",
        stop_pct=0.03,
    )
    params = forward_runner._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    assert params["fast_window"] == 10
    assert params["slow_window"] == 50
    assert params["price_col"] == "close"
    assert params["stop_pct"] == 0.03


def test_build_strategy_params_source_uses_load_strategy_not_from_config_bypass() -> None:
    import scripts.run_backtest as run_backtest_script

    source = inspect.getsource(run_backtest_script._build_strategy_params_from_config)
    assert "load_strategy" in source
    assert "spec.cls.from_config" not in source


def test_build_strategy_params_calls_load_strategy_for_registry_validation() -> None:
    import scripts.run_backtest as run_backtest_script

    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=10, slow_window=50, price_col="close")

    with patch.object(run_backtest_script, "load_strategy") as load_mock:
        load_mock.return_value = MagicMock()
        params = forward_runner._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)

    load_mock.assert_called_once_with(MA_CROSSOVER_KEY)
    assert params["fast_window"] == 10
    assert params["stop_pct"] == 0.02


def test_build_strategy_params_isolated_per_strategy_key() -> None:
    from src.core.peak_config import PeakConfig

    cfg = PeakConfig(
        raw={
            "environment": {"mode": "backtest"},
            "strategy": {
                MA_CROSSOVER_KEY: {"fast_window": 10, "slow_window": 50, "price_col": "close"},
                RSI_REVERSION_KEY: {
                    "rsi_period": 14,
                    "oversold": 30,
                    "overbought": 70,
                },
            },
        }
    )
    ma_params = forward_runner._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    rsi_params = forward_runner._build_strategy_params_from_config(cfg, RSI_REVERSION_KEY)

    assert "rsi_period" not in ma_params
    assert "fast_window" not in rsi_params
    assert ma_params["fast_window"] == 10
    assert rsi_params["rsi_period"] == 14


def test_build_strategy_params_unknown_strategy_fails_closed() -> None:
    cfg = _minimal_cfg(MA_CROSSOVER_KEY, fast_window=10, slow_window=50, price_col="close")
    with pytest.raises(KeyError):
        forward_runner._build_strategy_params_from_config(cfg, "definitely_not_a_strategy_xyz")


def test_main_forwards_config_to_canonical_builder(tmp_path) -> None:
    from src.core.peak_config import PeakConfig

    cfg_path = tmp_path / "cfg.toml"
    cfg_path.write_text("[environment]\nmode = 'backtest'\n", encoding="utf-8")
    cfg = PeakConfig(
        raw={
            "environment": {"mode": "backtest"},
            "strategy": {
                MA_CROSSOVER_KEY: {
                    "fast_window": 10,
                    "slow_window": 50,
                    "price_col": "close",
                },
            },
        }
    )
    captured: dict[str, object] = {}

    def capture_builder(config, strategy_key):
        captured["cfg"] = config
        captured["strategy_key"] = strategy_key
        return {"fast_window": 10, "slow_window": 50, "stop_pct": 0.02}

    mock_client = MagicMock()
    mock_client.get_name.return_value = "mock"
    mock_client.fetch_ohlcv.return_value = _sample_ohlcv()

    with (
        patch.object(forward_runner, "load_config", return_value=cfg),
        patch.object(forward_runner, "build_exchange_client_from_config", return_value=mock_client),
        patch.object(
            forward_runner,
            "_build_strategy_params_from_config",
            side_effect=capture_builder,
        ),
        patch.object(
            forward_runner,
            "load_strategy",
            return_value=lambda df, params: pd.Series([1.0], index=df.index[-1:]),
        ),
        patch.object(forward_runner, "log_forward_signal_run", return_value="run-1"),
    ):
        code = forward_runner.main(
            [
                "--config",
                str(cfg_path),
                "--strategy",
                MA_CROSSOVER_KEY,
                "--symbol",
                "BTC/EUR",
                "--dry-run",
                "--no-alerts",
            ]
        )

    assert code == 0
    assert captured["cfg"] is cfg
    assert captured["strategy_key"] == MA_CROSSOVER_KEY


def test_load_strategy_ma_crossover_matches_create_strategy_from_config_signals() -> None:
    from src.core.peak_config import PeakConfig
    from src.strategies import load_strategy
    from src.strategies.registry import create_strategy_from_config

    raw = {
        "environment": {"mode": "backtest"},
        "strategy": {
            MA_CROSSOVER_KEY: {
                "fast_window": 10,
                "slow_window": 50,
                "price_col": "close",
                "stop_pct": 0.03,
            },
        },
    }
    cfg = PeakConfig(raw=raw)
    df = _sample_ohlcv()

    legacy = create_strategy_from_config(MA_CROSSOVER_KEY, cfg).generate_signals(df)
    params = forward_runner._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    canonical = load_strategy(MA_CROSSOVER_KEY)(df, params)

    pd.testing.assert_series_equal(canonical, legacy)


def test_load_strategy_rsi_reversion_matches_create_strategy_from_config_signals() -> None:
    from src.core.peak_config import PeakConfig
    from src.strategies import load_strategy
    from src.strategies.registry import create_strategy_from_config

    raw = {
        "environment": {"mode": "backtest"},
        "strategy": {
            RSI_REVERSION_KEY: {
                "rsi_period": 14,
                "oversold": 30,
                "overbought": 70,
                "stop_pct": 0.02,
            },
        },
    }
    cfg = PeakConfig(raw=raw)
    df = _sample_ohlcv(n=120)

    legacy = create_strategy_from_config(RSI_REVERSION_KEY, cfg).generate_signals(df)
    params = forward_runner._build_strategy_params_from_config(cfg, RSI_REVERSION_KEY)
    canonical = load_strategy(RSI_REVERSION_KEY)(df, params)

    pd.testing.assert_series_equal(canonical, legacy)


def test_main_calls_load_strategy_and_passes_full_params(tmp_path) -> None:
    from src.core.peak_config import PeakConfig

    cfg_path = tmp_path / "cfg.toml"
    cfg_path.write_text("[environment]\nmode = 'backtest'\n", encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_signal_fn(df, params):
        captured["params"] = dict(params)
        return pd.Series([0.0, 1.0], index=df.index[-2:])

    mock_client = MagicMock()
    mock_client.get_name.return_value = "mock"
    mock_client.fetch_ohlcv.return_value = _sample_ohlcv()

    with (
        patch.object(forward_runner, "load_config") as load_config_mock,
        patch.object(forward_runner, "build_exchange_client_from_config", return_value=mock_client),
        patch.object(
            forward_runner, "load_strategy", return_value=fake_signal_fn
        ) as load_strategy_mock,
        patch.object(forward_runner, "log_forward_signal_run", return_value="run-1"),
    ):
        load_config_mock.return_value = PeakConfig(
            raw={
                "environment": {"mode": "backtest"},
                "strategy": {
                    MA_CROSSOVER_KEY: {
                        "fast_window": 10,
                        "slow_window": 50,
                        "price_col": "close",
                    },
                },
            }
        )

        code = forward_runner.main(
            [
                "--config",
                str(cfg_path),
                "--strategy",
                MA_CROSSOVER_KEY,
                "--symbol",
                "BTC/EUR",
                "--dry-run",
                "--no-alerts",
            ]
        )

    assert code == 0
    load_strategy_mock.assert_called_once_with(MA_CROSSOVER_KEY)
    assert captured["params"]["fast_window"] == 10
    assert captured["params"]["slow_window"] == 50
    assert captured["params"]["stop_pct"] == 0.02


def test_isolated_signal_fn_binding_per_call(tmp_path) -> None:
    from src.core.peak_config import PeakConfig

    call_count = 0

    def fake_signal_fn(df, params):
        nonlocal call_count
        call_count += 1
        return pd.Series([1.0], index=df.index[-1:])

    mock_client = MagicMock()
    mock_client.get_name.return_value = "mock"
    mock_client.fetch_ohlcv.return_value = _sample_ohlcv()

    with (
        patch.object(forward_runner, "load_config") as load_config_mock,
        patch.object(forward_runner, "build_exchange_client_from_config", return_value=mock_client),
        patch.object(
            forward_runner, "load_strategy", return_value=fake_signal_fn
        ) as load_strategy_mock,
        patch.object(forward_runner, "log_forward_signal_run", return_value="run-1"),
    ):
        load_config_mock.return_value = PeakConfig(
            raw={"environment": {"mode": "backtest"}, "strategy": {MA_CROSSOVER_KEY: {}}}
        )

        code = forward_runner.main(
            [
                "--config",
                str(tmp_path / "cfg.toml"),
                "--strategy",
                MA_CROSSOVER_KEY,
                "--symbol",
                "BTC/EUR",
                "--dry-run",
                "--no-alerts",
            ]
        )

    assert code == 0
    load_strategy_mock.assert_called_once_with(MA_CROSSOVER_KEY)
    assert call_count == 1


def test_unknown_strategy_fails_closed() -> None:
    from src.strategies import load_strategy

    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("definitely_not_a_forward_runner_strategy_xyz")


def test_load_strategy_no_network_calls() -> None:
    from src.strategies import load_strategy

    with patch("urllib.request.urlopen") as urlopen:
        load_strategy(MA_CROSSOVER_KEY)
        load_strategy(RSI_REVERSION_KEY)
    urlopen.assert_not_called()


# ---------------------------------------------------------------------------
# Registry gates — canonical _validate_strategy_registry_gates reuse
# ---------------------------------------------------------------------------


def test_source_has_no_local_registry_gate_definition() -> None:
    local_defs = _local_function_defs()
    assert FORBIDDEN_LOCAL_REGISTRY_GATE_DEFS.isdisjoint(local_defs)


def test_validate_strategy_registry_gates_import_identity_is_canonical_owner() -> None:
    import scripts.run_backtest as run_backtest_script

    assert (
        forward_runner._validate_strategy_registry_gates
        is run_backtest_script._validate_strategy_registry_gates
    )


def test_source_imports_canonical_registry_gate_validator() -> None:
    source = _read_source()
    assert "_validate_strategy_registry_gates" in source
    assert "scripts.run_backtest" in source


def test_registry_gates_block_r_and_d_without_flag() -> None:
    from src.core.peak_config import PeakConfig

    raw = {"environment": {"mode": "backtest"}, "strategy": {"ehlers_cycle_filter": {}}}
    cfg = PeakConfig(raw=raw)
    with pytest.raises(ValueError, match="R&D-only"):
        forward_runner._validate_strategy_registry_gates("ehlers_cycle_filter", cfg)


def test_unknown_strategy_fails_closed_at_registry_gates() -> None:
    from src.core.peak_config import PeakConfig

    cfg = PeakConfig(raw={"environment": {"mode": "backtest"}})
    with pytest.raises(KeyError):
        forward_runner._validate_strategy_registry_gates("definitely_not_a_strategy_xyz", cfg)


def test_main_invokes_registry_gates_before_strategy_params(tmp_path) -> None:
    from src.core.peak_config import PeakConfig

    cfg_path = tmp_path / "cfg.toml"
    cfg_path.write_text("[environment]\nmode = 'backtest'\n", encoding="utf-8")
    cfg = PeakConfig(
        raw={
            "environment": {"mode": "backtest"},
            "strategy": {
                MA_CROSSOVER_KEY: {
                    "fast_window": 10,
                    "slow_window": 50,
                    "price_col": "close",
                },
            },
        }
    )
    call_order: list[str] = []
    gate_mock = MagicMock(side_effect=lambda key, config: call_order.append("gates"))
    builder_mock = MagicMock(
        side_effect=lambda config, strategy_key: (
            call_order.append("builder"),
            {"fast_window": 10, "slow_window": 50, "stop_pct": 0.02},
        )[1]
    )
    mock_client = MagicMock()
    mock_client.get_name.return_value = "mock"
    mock_client.fetch_ohlcv.return_value = _sample_ohlcv()

    with (
        patch.object(forward_runner, "load_config", return_value=cfg),
        patch.object(forward_runner, "build_exchange_client_from_config", return_value=mock_client),
        patch.object(forward_runner, "_validate_strategy_registry_gates", gate_mock),
        patch.object(forward_runner, "_build_strategy_params_from_config", builder_mock),
        patch.object(
            forward_runner,
            "load_strategy",
            return_value=lambda df, params: pd.Series([1.0], index=df.index[-1:]),
        ),
        patch.object(forward_runner, "log_forward_signal_run", return_value="run-1"),
    ):
        code = forward_runner.main(
            [
                "--config",
                str(cfg_path),
                "--strategy",
                MA_CROSSOVER_KEY,
                "--symbol",
                "BTC/EUR",
                "--dry-run",
                "--no-alerts",
            ]
        )

    assert code == 0
    gate_mock.assert_called_once_with(MA_CROSSOVER_KEY, cfg)
    builder_mock.assert_called_once_with(cfg, MA_CROSSOVER_KEY)
    assert call_order == ["gates", "builder"]


def test_import_smoke_no_main_execution() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import run_forward_signals"],
        cwd=project_root / "scripts",
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
    assert "--strategy" in result.stdout


def test_cli_schema_unchanged() -> None:
    args = forward_runner.parse_args(["--strategy", MA_CROSSOVER_KEY, "--symbol", "BTC/EUR"])
    assert args.strategy == MA_CROSSOVER_KEY
    assert args.symbol == "BTC/EUR"
    assert args.bars == 200
    assert args.timeframe == "1h"
