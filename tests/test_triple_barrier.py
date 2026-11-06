"""Tests for triple_barrier labeling (research-only)."""

from __future__ import annotations

import pandas as pd
import pytest

from src.research.ml.labeling.triple_barrier import (
    apply_pnl_stop_loss,
    compute_triple_barrier_labels,
    get_horizontal_barriers,
    get_vertical_barrier,
)


def test_long_hits_take_profit_first():
    prices = pd.Series([100.0, 101.0, 102.0, 99.0, 98.0, 103.0])
    signals = pd.Series([1, 0, 0, 0, 0, 0])
    labels = compute_triple_barrier_labels(
        prices, signals, take_profit=0.02, stop_loss=0.01, vertical_barrier_bars=5
    )
    assert labels.iloc[0] == 1
    assert pd.isna(labels.iloc[1])


def test_long_hits_stop_first():
    prices = pd.Series([100.0, 99.0, 98.0, 97.0])
    signals = pd.Series([1, 0, 0, 0])
    labels = compute_triple_barrier_labels(
        prices, signals, take_profit=0.02, stop_loss=0.01, vertical_barrier_bars=5
    )
    assert labels.iloc[0] == -1


def test_vertical_barrier_timeout():
    prices = pd.Series([100.0, 100.1, 100.05, 100.08, 100.02])
    signals = pd.Series([1, 0, 0, 0, 0])
    labels = compute_triple_barrier_labels(
        prices, signals, take_profit=0.50, stop_loss=0.50, vertical_barrier_bars=2
    )
    assert labels.iloc[0] == 0


def test_short_hits_tp():
    prices = pd.Series([100.0, 99.0, 98.0])
    signals = pd.Series([-1, 0, 0])
    labels = compute_triple_barrier_labels(
        prices, signals, take_profit=0.02, stop_loss=0.01, vertical_barrier_bars=5
    )
    assert labels.iloc[0] == 1


def test_get_vertical_barrier():
    idx = pd.date_range("2024-01-01", periods=2, freq="h")
    out = get_vertical_barrier(idx, max_holding_period=3, freq="h")
    assert len(out) == 2
    assert out.iloc[0] == idx[0] + pd.Timedelta(hours=3)


def test_get_horizontal_barriers_long():
    events = pd.DataFrame({"entry": [100.0, 50.0]})
    upper, lower = get_horizontal_barriers(
        pd.Series(dtype=float), events, take_profit=0.1, stop_loss=0.05
    )
    assert upper.iloc[0] == pytest.approx(110.0)
    assert lower.iloc[0] == pytest.approx(95.0)


def test_get_horizontal_barriers_short_side():
    events = pd.DataFrame({"entry": [100.0], "side": [-1]})
    upper, lower = get_horizontal_barriers(
        pd.Series(dtype=float), events, take_profit=0.02, stop_loss=0.01
    )
    assert upper.iloc[0] == pytest.approx(101.0)
    assert lower.iloc[0] == pytest.approx(98.0)


def test_apply_pnl_stop_loss_without_exit_column():
    prices = pd.Series([1.0, 2.0])
    events = pd.DataFrame({"x": [1]})
    out = apply_pnl_stop_loss(prices, events, max_loss=0.1)
    assert pd.isna(out.iloc[0])


def test_invalid_tp_sl():
    prices = pd.Series([100.0])
    signals = pd.Series([1])
    with pytest.raises(ValueError):
        compute_triple_barrier_labels(prices, signals, take_profit=-0.1, stop_loss=0.01)
