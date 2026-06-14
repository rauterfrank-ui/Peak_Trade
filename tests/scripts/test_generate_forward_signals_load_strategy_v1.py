"""
generate_forward_signals: canonical load_strategy() migration (offline, fail-closed).
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
sys.path.insert(0, str(project_root / "scripts"))

import generate_forward_signals as forward_script

TARGET_SCRIPT = project_root / "scripts/generate_forward_signals.py"
MA_CROSSOVER_KEY = "ma_crossover"
MOMENTUM_KEY = "momentum_1h"

FORBIDDEN_IMPORTS = ("create_strategy_from_config",)


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


def test_module_imports_without_main_side_effects() -> None:
    with patch.object(forward_script, "main") as main_mock:
        importlib.reload(forward_script)
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


def test_build_strategy_params_includes_section_and_stop_pct() -> None:
    from src.core.peak_config import PeakConfig

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
    params = forward_script._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    assert params["fast_window"] == 10
    assert params["slow_window"] == 50
    assert params["price_col"] == "close"
    assert params["stop_pct"] == 0.03


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
    params = forward_script._build_strategy_params_from_config(cfg, MA_CROSSOVER_KEY)
    canonical = load_strategy(MA_CROSSOVER_KEY)(df, params)

    pd.testing.assert_series_equal(canonical, legacy)


def test_load_strategy_momentum_matches_create_strategy_from_config_signals() -> None:
    from src.core.peak_config import PeakConfig
    from src.strategies import load_strategy
    from src.strategies.registry import create_strategy_from_config

    raw = {
        "environment": {"mode": "backtest"},
        "strategy": {
            MOMENTUM_KEY: {
                "lookback_period": 15,
                "entry_threshold": 0.02,
                "exit_threshold": -0.01,
                "stop_pct": 0.02,
            },
        },
    }
    cfg = PeakConfig(raw=raw)
    df = _sample_ohlcv(n=120)

    legacy = create_strategy_from_config(MOMENTUM_KEY, cfg).generate_signals(df)
    params = forward_script._build_strategy_params_from_config(cfg, MOMENTUM_KEY)
    canonical = load_strategy(MOMENTUM_KEY)(df, params)

    pd.testing.assert_series_equal(canonical, legacy)


def test_main_calls_load_strategy_and_passes_full_params(tmp_path, monkeypatch) -> None:
    from src.core.peak_config import PeakConfig

    cfg_path = tmp_path / "cfg.toml"
    cfg_path.write_text("[environment]\nmode = 'backtest'\n", encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_signal_fn(df, params):
        captured["params"] = dict(params)
        return pd.Series([0.0, 1.0], index=df.index[-2:])

    ohlcv_meta = {
        "symbol": "BTC/EUR",
        "ohlcv_source": "dummy",
        "timeframe": "1h",
        "n_bars_requested": 200,
        "bars_loaded": 80,
        "kraken_pagination_used": None,
        "kraken_bars_shortfall": None,
    }

    with (
        patch.object(forward_script, "load_config") as load_config_mock,
        patch.object(forward_script, "load_data_for_symbol") as load_data,
        patch.object(
            forward_script, "load_strategy", return_value=fake_signal_fn
        ) as load_strategy_mock,
        patch.object(forward_script, "log_generic_experiment"),
        patch.object(forward_script, "save_signals_to_csv") as save_csv,
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
        load_data.return_value = (_sample_ohlcv(), ohlcv_meta)
        save_csv.return_value = pd.DataFrame({"symbol": ["BTC/EUR"]})

        out_dir = tmp_path / "forward"
        code = forward_script.main(
            [
                "--strategy",
                MA_CROSSOVER_KEY,
                "--symbols",
                "BTC/EUR",
                "--config-path",
                str(cfg_path),
                "--output-dir",
                str(out_dir),
                "--run-name",
                "probe_load_strategy",
                "--n-bars",
                "80",
            ]
        )

    assert code == 0
    load_strategy_mock.assert_called_once_with(MA_CROSSOVER_KEY)
    assert captured["params"]["fast_window"] == 10
    assert captured["params"]["slow_window"] == 50
    assert captured["params"]["stop_pct"] == 0.02


def test_isolated_signal_fn_binding_per_symbol(tmp_path, monkeypatch) -> None:
    from src.core.peak_config import PeakConfig

    call_count = 0

    def fake_signal_fn(df, params):
        nonlocal call_count
        call_count += 1
        return pd.Series([1.0], index=df.index[-1:])

    ohlcv_meta = {
        "symbol": "BTC/EUR",
        "ohlcv_source": "dummy",
        "timeframe": "1h",
        "n_bars_requested": 200,
        "bars_loaded": 80,
        "kraken_pagination_used": None,
        "kraken_bars_shortfall": None,
    }

    with (
        patch.object(forward_script, "load_config") as load_config_mock,
        patch.object(forward_script, "load_data_for_symbol") as load_data,
        patch.object(
            forward_script, "load_strategy", return_value=fake_signal_fn
        ) as load_strategy_mock,
        patch.object(forward_script, "log_generic_experiment"),
        patch.object(forward_script, "save_signals_to_csv") as save_csv,
    ):
        load_config_mock.return_value = PeakConfig(
            raw={"environment": {"mode": "backtest"}, "strategy": {MA_CROSSOVER_KEY: {}}}
        )
        load_data.return_value = (_sample_ohlcv(), ohlcv_meta)
        save_csv.return_value = pd.DataFrame({"symbol": ["BTC/EUR", "ETH/EUR"]})

        out_dir = tmp_path / "forward"
        code = forward_script.main(
            [
                "--strategy",
                MA_CROSSOVER_KEY,
                "--symbols",
                "BTC/EUR,ETH/EUR",
                "--config-path",
                str(tmp_path / "cfg.toml"),
                "--output-dir",
                str(out_dir),
                "--run-name",
                "probe_isolation",
            ]
        )

    assert code == 0
    load_strategy_mock.assert_called_once_with(MA_CROSSOVER_KEY)
    assert call_count == 2


def test_unknown_strategy_fails_closed() -> None:
    from src.strategies import load_strategy

    with pytest.raises(ValueError, match="Unbekannte Strategie"):
        load_strategy("definitely_not_a_forward_strategy_xyz")


def test_load_strategy_no_network_calls() -> None:
    from src.strategies import load_strategy

    with patch("urllib.request.urlopen") as urlopen:
        load_strategy(MA_CROSSOVER_KEY)
        load_strategy(MOMENTUM_KEY)
    urlopen.assert_not_called()


def test_import_smoke_no_main_execution() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import generate_forward_signals"],
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
    assert "ma_crossover" in result.stdout or "--strategy" in result.stdout


def test_cli_schema_unchanged() -> None:
    args = forward_script.parse_args(["--strategy", MA_CROSSOVER_KEY, "--symbols", "BTC/EUR"])
    assert args.strategy == MA_CROSSOVER_KEY
    assert args.symbols == "BTC/EUR"
    assert args.n_bars == 200
