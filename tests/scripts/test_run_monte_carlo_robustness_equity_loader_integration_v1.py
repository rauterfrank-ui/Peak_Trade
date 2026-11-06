"""
Monte-Carlo robustness CLI: canonical equity_loader integration (fail-closed).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import scripts.run_monte_carlo_robustness as mc_script


def _write_events_parquet(run_dir: Path) -> None:
    df = pd.DataFrame(
        {
            "ts_bar": pd.date_range("2024-01-01", periods=10, freq="1h", tz="UTC"),
            "equity": [
                100.0,
                101.0,
                100.5,
                102.0,
                103.0,
                104.0,
                103.5,
                105.0,
                106.0,
                107.0,
            ],
        }
    )
    df.to_parquet(run_dir / "events.parquet", index=False)


def test_load_returns_for_config_uses_canonical_equity_loader(tmp_path: Path) -> None:
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    run_dir = experiments_dir / "expABC"
    run_dir.mkdir()
    _write_events_parquet(run_dir)

    returns = mc_script.load_returns_for_config(
        {"config_id": "expABC"},
        experiments_dir,
        use_dummy_data=False,
    )
    assert isinstance(returns, pd.Series)
    assert isinstance(returns.index, pd.DatetimeIndex)
    assert len(returns) >= 2


def test_load_returns_for_config_missing_artifacts_fails_closed(tmp_path: Path) -> None:
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    run_dir = experiments_dir / "expABC"
    run_dir.mkdir()

    with pytest.raises(ValueError, match="Equity load failed"):
        mc_script.load_returns_for_config(
            {"config_id": "expABC"},
            experiments_dir,
            use_dummy_data=False,
        )


def test_load_returns_for_config_invalid_config_id_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no usable experiment_id"):
        mc_script.load_returns_for_config(
            {"config_id": "config_1"},
            tmp_path,
            use_dummy_data=False,
        )


def test_load_returns_for_config_loader_error_no_silent_dummy_fallback(tmp_path: Path) -> None:
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    run_dir = experiments_dir / "expABC"
    run_dir.mkdir()

    with patch.object(
        mc_script,
        "load_equity_curves_from_run_dir",
        side_effect=FileNotFoundError("no artifacts"),
    ):
        with pytest.raises(ValueError, match="Equity load failed"):
            mc_script.load_returns_for_config(
                {"config_id": "expABC"},
                experiments_dir,
                use_dummy_data=False,
            )


def test_load_returns_for_config_synthetic_only_with_explicit_opt_in(tmp_path: Path) -> None:
    returns = mc_script.load_returns_for_config(
        {"config_id": "ignored"},
        tmp_path,
        use_dummy_data=True,
        dummy_bars=40,
    )
    assert len(returns) == 40


def test_load_returns_for_config_default_path_does_not_use_synthetic(tmp_path: Path) -> None:
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    with pytest.raises(ValueError):
        mc_script.load_returns_for_config(
            {"config_id": "missing"},
            experiments_dir,
            use_dummy_data=False,
        )


def test_load_returns_for_config_no_network_calls(tmp_path: Path) -> None:
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    run_dir = experiments_dir / "expABC"
    run_dir.mkdir()
    _write_events_parquet(run_dir)

    with patch("urllib.request.urlopen") as urlopen:
        mc_script.load_returns_for_config(
            {"config_id": "expABC"},
            experiments_dir,
            use_dummy_data=False,
        )
    urlopen.assert_not_called()


@patch("scripts.run_monte_carlo_robustness.load_top_n_configs_for_sweep")
def test_mc_equity_loader_integration_writes_report(mock_load, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    run_dir = experiments_dir / "expABC"
    run_dir.mkdir()
    _write_events_parquet(run_dir)

    mock_load.return_value = [{"config_id": "expABC", "rank": 1}]
    out = tmp_path / "mc_out"
    args = mc_script.build_parser().parse_args(
        [
            "--sweep-name",
            "smoke",
            "--top-n",
            "1",
            "--num-runs",
            "20",
            "--format",
            "md",
            "--output-dir",
            str(out),
            "--experiments-dir",
            str(experiments_dir),
        ]
    )

    rc = mc_script.run_from_args(args)
    assert rc == 0
    assert list(out.rglob("*.md"))
