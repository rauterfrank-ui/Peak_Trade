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
from src.experiments.portfolio_robustness import (
    PortfolioComponent,
    build_portfolio_returns,
)


def test_dummy_returns_loader_single_component_portfolio_smoke(tmp_path: Path) -> None:
    """Offline: Dummy-Loader aus run_portfolio_robustness + Portfolio-Synthese ohne Sweep-Artefakte.

    Eine Komponente: create_dummy_returns nutzt pro Aufruf datetime.now() für den Index;
    mehrere Komponenten hätten disjunkte Zeitachsen und keinen inner join.
    """
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
