"""
CLI --ohlcv-file für MC- und Stress-Runner (narrow propagation und Loader-Sanity).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import scripts.run_monte_carlo_robustness as mc_script
import scripts.run_stress_tests as stress_script
from src.experiments import ohlcv_returns_file


def test_monte_carlo_passes_shared_returns_from_ohlcv(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)

    pqf = tmp_path / "tiny.parquet"
    idx = pd.date_range("2024-01-01", periods=20, tz="UTC", freq="min")
    pd.DataFrame({"close": np.linspace(100.0, 119.0, 20)}, index=idx).to_parquet(pqf)

    with patch.object(
        mc_script, "load_top_n_configs_for_sweep", return_value=[{"config_id": "one", "rank": 1}]
    ):
        with patch.object(mc_script, "run_monte_carlo_from_returns") as mc_run:
            with patch.object(mc_script, "build_monte_carlo_report"):
                mc_run.return_value = MagicMock()
                parser = mc_script.build_parser()
                args = parser.parse_args(
                    [
                        "--sweep-name",
                        "smoke_sweep",
                        "--top-n",
                        "1",
                        "--num-runs",
                        "5",
                        "--format",
                        "md",
                        "--ohlcv-file",
                        str(pqf),
                        "--output-dir",
                        str(tmp_path / "out"),
                    ]
                )
                rc = mc_script.run_from_args(args)

    assert rc == 0
    fed = mc_run.call_args[0][0]
    assert isinstance(fed, pd.Series)
    assert len(fed) == 19


def test_stress_passes_shared_returns_kwarg(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)

    pqf = tmp_path / "tiny2.parquet"
    idx = pd.date_range("2024-06-01", periods=12, tz="UTC", freq="min")
    pd.DataFrame({"close": np.linspace(50.0, 55.0, 12)}, index=idx).to_parquet(pqf)

    with patch.object(
        stress_script,
        "load_top_n_configs_for_sweep",
        return_value=[{"config_id": "one", "rank": 1}],
    ):
        with patch.object(stress_script, "run_stress_test_suite") as suite_run:
            with patch.object(stress_script, "build_stress_test_report") as brep:
                suite_run.return_value = MagicMock()
                brep.return_value = {}
                parser = stress_script.build_parser()
                args = parser.parse_args(
                    [
                        "--sweep-name",
                        "smoke_sweep",
                        "--config",
                        "config/config.toml",
                        "--top-n",
                        "1",
                        "--scenarios",
                        "single_crash_bar",
                        "--format",
                        "md",
                        "--ohlcv-file",
                        str(pqf),
                        "--output-dir",
                        str(tmp_path / "sout"),
                    ]
                )
                rc = stress_script.run_from_args(args)

    assert rc == 0
    baseline_returns = suite_run.call_args[0][0]
    assert len(baseline_returns) == 11


def test_loader_missing_close_column(tmp_path) -> None:
    p = tmp_path / "noclose.parquet"
    pd.DataFrame({"open": [1.0]}, index=pd.DatetimeIndex(["2020-01-01"], tz="UTC")).to_parquet(p)
    with pytest.raises(ValueError):
        ohlcv_returns_file.load_close_returns_from_ohlcv_parquet(p)


def test_loader_raises_missing_file(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        ohlcv_returns_file.load_close_returns_from_ohlcv_parquet(tmp_path / "none.parquet")
