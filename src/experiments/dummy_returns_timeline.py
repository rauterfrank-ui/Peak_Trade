# src/experiments/dummy_returns_timeline.py
"""Deterministic dummy return series for offline portfolio/research CLIs."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd

# Fixed UTC anchor: for a given ``n_bars``, every series shares this hourly DatetimeIndex;
# only pseudo-random values differ by ``seed``. Enables reproducible tests and multi-component
# portfolio inner joins without relying on ``datetime.now()`` per call.
DUMMY_RETURNS_TIMELINE_START = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def create_dummy_returns(n_bars: int = 500, seed: int = 42) -> pd.Series:
    """
    Erstellt Dummy-Returns für Tests mit fester Zeitachse.

    Args:
        n_bars: Anzahl der Bars
        seed: Random Seed (beeinflusst nur die Werte, nicht den Index)

    Returns:
        Returns-Serie mit DatetimeIndex (UTC, stündlich ab DUMMY_RETURNS_TIMELINE_START)
    """
    np.random.seed(seed)
    dates = pd.date_range(DUMMY_RETURNS_TIMELINE_START, periods=n_bars, freq="1h")
    returns = np.random.normal(0.0005, 0.02, n_bars)
    return pd.Series(returns, index=dates)
