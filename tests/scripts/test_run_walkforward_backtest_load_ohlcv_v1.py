"""
run_walkforward_backtest: canonical load_ohlcv_data reuse (offline, fail-closed).
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

import run_walkforward_backtest as walkforward_runner

TARGET_SCRIPT = project_root / "scripts/run_walkforward_backtest.py"
DATA_LOADER_OWNER = "scripts/run_backtest.py:load_ohlcv_data"
FORBIDDEN_LOCAL_LOADER_DEFS = frozenset(
    {"load_ohlcv_data", "generate_dummy_ohlcv", "create_dummy_data", "load_data_from_file"}
)


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


def test_module_imports_without_main_side_effects() -> None:
    with patch.object(walkforward_runner, "main") as main_mock:
        importlib.reload(walkforward_runner)
    main_mock.assert_not_called()


def test_source_has_no_local_loader_or_dummy_definitions() -> None:
    local_defs = _local_function_defs()
    assert FORBIDDEN_LOCAL_LOADER_DEFS.isdisjoint(local_defs)


def test_source_imports_canonical_data_loader() -> None:
    source = _read_source()
    assert "load_ohlcv_data" in source
    assert "scripts.run_backtest" in source


def test_load_ohlcv_data_import_identity_is_canonical_owner() -> None:
    import scripts.run_backtest as run_backtest_script

    assert walkforward_runner.load_ohlcv_data is run_backtest_script.load_ohlcv_data


def test_run_from_args_forwards_dummy_path_to_canonical_loader() -> None:
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

    args = MagicMock()
    args.verbose = False
    args.use_dummy_data = True
    args.data_file = None
    args.dummy_bars = 500
    args.start_date = "2024-01-01"
    args.end_date = "2024-06-01"
    args.train_window = "90d"
    args.test_window = "30d"
    args.step_size = None
    args.symbol = "BTC/EUR"
    args.output_dir = "reports/walkforward"
    args.sweep_name = "test_sweep"
    args.candidate_presets = None
    args.top_n = 1
    args.metric_primary = "metric_sharpe_ratio"
    args.metric_fallback = "metric_total_return"

    with (
        patch.object(walkforward_runner, "load_ohlcv_data", side_effect=capture_loader),
        patch.object(
            walkforward_runner,
            "run_walkforward_for_top_n_from_sweep",
            return_value=[],
        ),
    ):
        rc = walkforward_runner.run_from_args(args)

    assert rc == 0
    assert captured == {
        "data_file": None,
        "start_date": "2024-01-01",
        "end_date": "2024-06-01",
        "n_bars": 500,
        "verbose": False,
    }


def test_run_from_args_forwards_file_path_to_canonical_loader() -> None:
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

    args = MagicMock()
    args.verbose = False
    args.use_dummy_data = False
    args.data_file = "data/btc_eur_1h.parquet"
    args.dummy_bars = 1000
    args.start_date = None
    args.end_date = None
    args.train_window = "90d"
    args.test_window = "30d"
    args.step_size = None
    args.symbol = "BTC/EUR"
    args.output_dir = "reports/walkforward"
    args.sweep_name = "test_sweep"
    args.candidate_presets = None
    args.top_n = 1
    args.metric_primary = "metric_sharpe_ratio"
    args.metric_fallback = "metric_total_return"

    with (
        patch.object(walkforward_runner, "load_ohlcv_data", side_effect=capture_loader),
        patch.object(
            walkforward_runner,
            "run_walkforward_for_top_n_from_sweep",
            return_value=[],
        ),
    ):
        rc = walkforward_runner.run_from_args(args)

    assert rc == 0
    assert captured == {
        "data_file": "data/btc_eur_1h.parquet",
        "start_date": None,
        "end_date": None,
        "n_bars": 1000,
        "verbose": False,
    }


def test_run_from_args_requires_data_source() -> None:
    args = MagicMock()
    args.verbose = False
    args.use_dummy_data = False
    args.data_file = None

    rc = walkforward_runner.run_from_args(args)
    assert rc == 1


def test_import_smoke_no_main_execution() -> None:
    result = subprocess.run(
        [sys.executable, "-c", "import run_walkforward_backtest"],
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
    assert "--use-dummy-data" in result.stdout
    assert "--data-file" in result.stdout
