# tests/test_portfolio_robustness_dummy_path_smoke.py
"""
Integration smoke: Portfolio-Robustness-Read-Path mit Dummy-Daten (scripts-Loader → build_portfolio_returns).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import scripts.run_portfolio_robustness as portfolio_script
from src.experiments.dummy_returns_timeline import (
    DUMMY_RETURNS_TIMELINE_START,
    create_dummy_returns,
)
from src.experiments.portfolio_robustness import (
    PortfolioComponent,
    build_portfolio_returns,
)


def test_dummy_returns_timeline_stable_across_seeds() -> None:
    """Gleiche n_bars + verschiedene Seeds → identischer Index, unterschiedliche Werte."""
    a = create_dummy_returns(48, seed=1)
    b = create_dummy_returns(48, seed=99)
    pd.testing.assert_index_equal(a.index, b.index)
    assert a.index[0] == DUMMY_RETURNS_TIMELINE_START
    assert not np.allclose(a.to_numpy(), b.to_numpy())


def test_dummy_returns_loader_single_component_portfolio_smoke(tmp_path: Path) -> None:
    """Offline: Dummy-Loader aus run_portfolio_robustness + Portfolio-Synthese ohne Sweep-Artefakte."""
    loader = portfolio_script.build_returns_loader(
        sweep_name="smoke_sweep",
        experiments_dir=tmp_path,
        use_dummy_data=True,
        dummy_bars=48,
    )
    components = [
        PortfolioComponent(strategy_name="rsi", config_id="config_1", weight=1.0),
    ]
    out = build_portfolio_returns(components, loader)
    assert isinstance(out, pd.Series)
    assert len(out) == 48
    assert out.notna().all()
    assert np.isfinite(out.to_numpy(dtype=float)).all()


def test_dummy_returns_loader_two_component_portfolio_smoke(tmp_path: Path) -> None:
    """Zwei Komponenten: gemeinsame deterministische Zeitachse → voller Inner-Join über alle Bars."""
    loader = portfolio_script.build_returns_loader(
        sweep_name="smoke_sweep",
        experiments_dir=tmp_path,
        use_dummy_data=True,
        dummy_bars=48,
    )
    components = [
        PortfolioComponent(strategy_name="rsi", config_id="config_1", weight=0.5),
        PortfolioComponent(strategy_name="ma", config_id="config_2", weight=0.5),
    ]
    out = build_portfolio_returns(components, loader)
    assert isinstance(out, pd.Series)
    assert len(out) == 48
    assert out.notna().all()
    assert np.isfinite(out.to_numpy(dtype=float)).all()
