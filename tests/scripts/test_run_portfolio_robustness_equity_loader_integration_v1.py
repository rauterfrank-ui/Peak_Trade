"""
Portfolio robustness CLI: canonical equity_loader integration (fail-closed).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import scripts.run_portfolio_robustness as pr_script
from src.experiments.portfolio_robustness import (
    PortfolioComponent,
    build_portfolio_returns,
)


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


def test_import_run_portfolio_robustness_no_side_effects() -> None:
    assert pr_script.build_returns_loader is not None
    assert pr_script.load_returns_for_config is not None


def test_load_returns_for_config_uses_canonical_equity_loader(tmp_path: Path) -> None:
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    run_dir = experiments_dir / "expABC"
    run_dir.mkdir()
    _write_events_parquet(run_dir)

    returns = pr_script.load_returns_for_config(
        {"config_id": "expABC", "rank": 1},
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
        pr_script.load_returns_for_config(
            {"config_id": "expABC", "rank": 1},
            experiments_dir,
            use_dummy_data=False,
        )


def test_load_returns_for_config_invalid_config_id_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no usable experiment_id"):
        pr_script.load_returns_for_config(
            {"config_id": "config_1", "rank": 1},
            tmp_path,
            use_dummy_data=False,
        )


def test_build_returns_loader_loader_error_no_silent_none(tmp_path: Path) -> None:
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    config_by_id = {"expABC": {"config_id": "expABC", "rank": 1}}
    loader = pr_script.build_returns_loader(
        config_by_id=config_by_id,
        experiments_dir=experiments_dir,
        use_dummy_data=False,
    )

    with pytest.raises(ValueError, match="Equity load failed"):
        loader("rsi", "expABC")


def test_build_returns_loader_unknown_config_id_fails_closed(tmp_path: Path) -> None:
    loader = pr_script.build_returns_loader(
        config_by_id={"expABC": {"config_id": "expABC", "rank": 1}},
        experiments_dir=tmp_path,
        use_dummy_data=False,
    )

    with pytest.raises(ValueError, match="config_id not found"):
        loader("rsi", "missing_config")


def test_missing_component_not_silently_skipped(tmp_path: Path) -> None:
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    run_dir = experiments_dir / "expABC"
    run_dir.mkdir()
    _write_events_parquet(run_dir)

    config_by_id = {"expABC": {"config_id": "expABC", "rank": 1}}
    loader = pr_script.build_returns_loader(
        config_by_id=config_by_id,
        experiments_dir=experiments_dir,
        use_dummy_data=False,
    )
    components = [
        PortfolioComponent(strategy_name="rsi", config_id="expABC", weight=0.5),
        PortfolioComponent(strategy_name="ma", config_id="missing", weight=0.5),
    ]

    with pytest.raises(ValueError, match="config_id not found"):
        build_portfolio_returns(components, loader)


def test_incomplete_return_matrix_not_accepted(tmp_path: Path) -> None:
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    only_dir = experiments_dir / "expABC"
    only_dir.mkdir()
    _write_events_parquet(only_dir)

    config_by_id = {
        "expABC": {"config_id": "expABC", "rank": 1},
        "expDEF": {"config_id": "expDEF", "rank": 2},
    }
    loader = pr_script.build_returns_loader(
        config_by_id=config_by_id,
        experiments_dir=experiments_dir,
        use_dummy_data=False,
    )
    components = [
        PortfolioComponent(strategy_name="rsi", config_id="expABC", weight=0.5),
        PortfolioComponent(strategy_name="ma", config_id="expDEF", weight=0.5),
    ]

    with pytest.raises(ValueError, match="Equity load failed"):
        build_portfolio_returns(components, loader)


def test_synthetic_only_with_explicit_opt_in(tmp_path: Path) -> None:
    returns = pr_script.load_returns_for_config(
        {"config_id": "ignored", "rank": 1},
        tmp_path,
        use_dummy_data=True,
        dummy_bars=40,
    )
    assert len(returns) == 40


def test_default_path_does_not_use_synthetic(tmp_path: Path) -> None:
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    with pytest.raises(ValueError):
        pr_script.load_returns_for_config(
            {"config_id": "missing", "rank": 1},
            experiments_dir,
            use_dummy_data=False,
        )


def test_no_network_calls(tmp_path: Path) -> None:
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    run_dir = experiments_dir / "expABC"
    run_dir.mkdir()
    _write_events_parquet(run_dir)

    with patch("urllib.request.urlopen") as urlopen:
        pr_script.load_returns_for_config(
            {"config_id": "expABC", "rank": 1},
            experiments_dir,
            use_dummy_data=False,
        )
    urlopen.assert_not_called()


def test_valid_fixture_path_deterministic_order(tmp_path: Path) -> None:
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    for exp_id in ("expB", "expA"):
        run_dir = experiments_dir / exp_id
        run_dir.mkdir()
        _write_events_parquet(run_dir)

    config_by_id = {
        "expA": {"config_id": "expA", "rank": 1},
        "expB": {"config_id": "expB", "rank": 2},
    }
    loader = pr_script.build_returns_loader(
        config_by_id=config_by_id,
        experiments_dir=experiments_dir,
        use_dummy_data=False,
    )
    components = [
        PortfolioComponent(strategy_name="s1", config_id="expA", weight=0.5),
        PortfolioComponent(strategy_name="s2", config_id="expB", weight=0.5),
    ]
    out = build_portfolio_returns(components, loader)
    assert isinstance(out, pd.Series)
    assert len(out) >= 2
    assert out.index.is_monotonic_increasing


def test_load_returns_for_config_no_silent_dummy_fallback(tmp_path: Path) -> None:
    experiments_dir = tmp_path / "experiments"
    experiments_dir.mkdir()
    run_dir = experiments_dir / "expABC"
    run_dir.mkdir()

    with patch.object(
        pr_script,
        "load_equity_curves_from_run_dir",
        side_effect=FileNotFoundError("no artifacts"),
    ):
        with pytest.raises(ValueError, match="Equity load failed"):
            pr_script.load_returns_for_config(
                {"config_id": "expABC", "rank": 1},
                experiments_dir,
                use_dummy_data=False,
            )
