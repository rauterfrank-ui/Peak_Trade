from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.experiments.equity_loader import equity_to_returns, load_equity_curves_from_run_dir


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


def _write_equity_csv(run_dir: Path) -> None:
    df = pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=10, freq="1h", tz="UTC"),
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
    df.to_csv(run_dir / "demo_equity.csv", index=False)


def test_load_equity_from_events_parquet(tmp_path: Path) -> None:
    run_dir = tmp_path / "run1"
    run_dir.mkdir()
    _write_events_parquet(run_dir)

    curves = load_equity_curves_from_run_dir(run_dir)
    assert len(curves) >= 1

    s = curves[0]
    assert isinstance(s.index, pd.DatetimeIndex)
    assert s.index.tz is not None
    assert len(s) >= 3

    r = equity_to_returns(s)
    assert len(r) >= 2


def test_load_equity_from_equity_csv(tmp_path: Path) -> None:
    run_dir = tmp_path / "run2"
    run_dir.mkdir()
    _write_equity_csv(run_dir)

    curves = load_equity_curves_from_run_dir(run_dir)
    assert len(curves) >= 1

    s = curves[0]
    assert isinstance(s.index, pd.DatetimeIndex)
    assert s.index.tz is not None
    assert len(s) >= 3


def test_load_equity_no_artifacts_raises(tmp_path: Path) -> None:
    run_dir = tmp_path / "empty"
    run_dir.mkdir()
    with pytest.raises(FileNotFoundError, match="No supported equity artifacts"):
        load_equity_curves_from_run_dir(run_dir)


def test_monte_carlo_loader_returns_from_run_dir(tmp_path: Path) -> None:
    from src.experiments.monte_carlo import load_returns_for_experiment_run

    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    run_dir = experiments_dir / "exp123"
    run_dir.mkdir()
    _write_events_parquet(run_dir)

    returns = load_returns_for_experiment_run("exp123", experiments_dir)
    assert isinstance(returns, pd.Series)
    assert isinstance(returns.index, pd.DatetimeIndex)
    assert len(returns) >= 2


def test_stress_loader_uses_topn_config_id_as_run_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.experiments import topn_promotion
    from src.experiments.stress_tests import load_returns_for_top_config

    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    run_dir = experiments_dir / "expABC"
    run_dir.mkdir()
    _write_equity_csv(run_dir)

    def fake_load_top_n_configs_for_sweep(*args, **kwargs):
        return [
            {
                "config_id": "expABC",
                "rank": 1,
                "params": {},
                "metrics": {},
                "strategy_name": "dummy",
            }
        ]

    monkeypatch.setattr(
        topn_promotion, "load_top_n_configs_for_sweep", fake_load_top_n_configs_for_sweep
    )

    returns = load_returns_for_top_config(
        sweep_name="any_sweep",
        config_rank=1,
        experiments_dir=experiments_dir,
        use_dummy_data=False,
    )
    assert isinstance(returns, pd.Series)
    assert isinstance(returns.index, pd.DatetimeIndex)
    assert len(returns) >= 2
