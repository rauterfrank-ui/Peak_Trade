# tests/strategies/wrappers/test_vol_regime_wrapper.py
"""Tests for VolRegimeWrapper: regime gating of signals/positions."""

from __future__ import annotations

import pandas as pd
import pytest

from src.strategies.wrappers.vol_regime_wrapper import VolRegimeWrapper


class _DummyStrategy:
    """Minimal stub that returns a given signal series or constant."""

    def __init__(self, signals: pd.Series | None = None, constant: int = 0):
        self.signals = signals
        self.constant = constant

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if self.signals is not None:
            return self.signals.reindex(data.index, fill_value=0).astype(int)
        return pd.Series(self.constant, index=data.index, dtype=int)


# --- 1) allowed regimes pass-through (no masking) ---
def test_allowed_regimes_passthrough():
    idx = pd.date_range("2020-01-01", periods=4, freq="D")
    data = pd.DataFrame({"close": [1.0, 2.0, 3.0, 4.0]}, index=idx)
    signals = pd.Series([1, -1, 0, 1], index=idx)
    base = _DummyStrategy(signals=signals)
    regime_labels = pd.Series(["low", "low", "high", "high"], index=idx)
    wrapper = VolRegimeWrapper(base, regime_labels, allowed_regimes={"low", "high"}, mode="signals")
    out = wrapper.generate_signals(data)
    pd.testing.assert_series_equal(out, signals, check_names=False)


# --- 2) disallowed regimes masked (zeros) ---
def test_disallowed_regimes_masked():
    idx = pd.date_range("2020-01-01", periods=4, freq="D")
    data = pd.DataFrame({"close": [1.0, 2.0, 3.0, 4.0]}, index=idx)
    signals = pd.Series([1, -1, 1, -1], index=idx)
    base = _DummyStrategy(signals=signals)
    regime_labels = pd.Series(["low", "mid", "low", "mid"], index=idx)
    wrapper = VolRegimeWrapper(base, regime_labels, allowed_regimes={"low"}, mode="signals")
    out = wrapper.generate_signals(data)
    expected = pd.Series([1, 0, 1, 0], index=idx, dtype=int)
    pd.testing.assert_series_equal(out, expected, check_names=False)


# --- 3) NaN labels masked when allow_unknown=False ---
def test_nan_labels_masked_when_allow_unknown_false():
    idx = pd.date_range("2020-01-01", periods=3, freq="D")
    data = pd.DataFrame({"close": [1.0, 2.0, 3.0]}, index=idx)
    signals = pd.Series([1, 1, 1], index=idx)
    base = _DummyStrategy(signals=signals)
    regime_labels = pd.Series(["low", float("nan"), "low"], index=idx)
    wrapper = VolRegimeWrapper(
        base, regime_labels, allowed_regimes={"low"}, mode="signals", allow_unknown=False
    )
    out = wrapper.generate_signals(data)
    expected = pd.Series([1, 0, 1], index=idx, dtype=int)
    pd.testing.assert_series_equal(out, expected, check_names=False)


# --- 4) NaN labels allowed when allow_unknown=True ---
def test_nan_labels_allowed_when_allow_unknown_true():
    idx = pd.date_range("2020-01-01", periods=3, freq="D")
    data = pd.DataFrame({"close": [1.0, 2.0, 3.0]}, index=idx)
    signals = pd.Series([1, 1, 1], index=idx)
    base = _DummyStrategy(signals=signals)
    regime_labels = pd.Series(["low", float("nan"), "high"], index=idx)
    wrapper = VolRegimeWrapper(
        base, regime_labels, allowed_regimes={"low"}, mode="signals", allow_unknown=True
    )
    out = wrapper.generate_signals(data)
    # low=pass, nan=pass (allow_unknown), high=block
    expected = pd.Series([1, 1, 0], index=idx, dtype=int)
    pd.testing.assert_series_equal(out, expected, check_names=False)


# --- 5) empty allowed_regimes -> all zeros ---
def test_empty_allowed_regimes_all_zeros():
    idx = pd.date_range("2020-01-01", periods=3, freq="D")
    data = pd.DataFrame({"close": [1.0, 2.0, 3.0]}, index=idx)
    signals = pd.Series([1, -1, 1], index=idx)
    base = _DummyStrategy(signals=signals)
    regime_labels = pd.Series(["low", "high", "low"], index=idx)
    wrapper = VolRegimeWrapper(base, regime_labels, allowed_regimes=set(), mode="signals")
    out = wrapper.generate_signals(data)
    expected = pd.Series([0, 0, 0], index=idx, dtype=int)
    pd.testing.assert_series_equal(out, expected, check_names=False)


# --- 6) index mismatch raises ValueError ---
def test_index_mismatch_raises_value_error():
    idx = pd.date_range("2020-01-01", periods=3, freq="D")
    data = pd.DataFrame({"close": [1.0, 2.0, 3.0]}, index=idx)
    signals = pd.Series([1, 1, 1], index=idx)
    base = _DummyStrategy(signals=signals)
    # regime_labels has different index (missing one)
    wrong_idx = pd.date_range("2020-01-02", periods=2, freq="D")  # no 2020-01-01
    regime_labels = pd.Series(["low", "low"], index=wrong_idx)
    wrapper = VolRegimeWrapper(base, regime_labels, allowed_regimes={"low"}, mode="signals")
    with pytest.raises(ValueError, match="does not cover all signal index"):
        wrapper.generate_signals(data)


# --- 7) determinism: same inputs -> same outputs ---
def test_determinism_same_inputs_same_outputs():
    idx = pd.date_range("2020-01-01", periods=5, freq="D")
    data = pd.DataFrame({"close": [1.0, 2.0, 3.0, 4.0, 5.0]}, index=idx)
    signals = pd.Series([1, -1, 0, 1, -1], index=idx)
    base = _DummyStrategy(signals=signals)
    regime_labels = pd.Series(["a", "b", "a", "b", "a"], index=idx)
    wrapper = VolRegimeWrapper(base, regime_labels, allowed_regimes={"a"}, mode="signals")
    out1 = wrapper.generate_signals(data)
    out2 = wrapper.generate_signals(data)
    pd.testing.assert_series_equal(out1, out2, check_names=False)
