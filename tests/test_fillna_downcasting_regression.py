"""
Regression tests for pandas FutureWarning:
  "Downcasting object dtype arrays on .fillna, .ffill, .bfill ..."

Goal (Item D / PR1):
- Ensure strategy patterns like `cond.shift(1).fillna(False)` are implemented
  without triggering pandas downcasting FutureWarnings.
- Keep behavior identical (no lookahead; only dtype stability).
"""

from __future__ import annotations

import warnings

import pandas as pd

from src.core.peak_config import load_config
from src.strategies.registry import create_strategy_from_config

# Reuse the same OHLCV generator used by the smoke test to ensure we exercise
# the same integration path / shapes.
from tests.test_strategies_smoke import create_dummy_ohlcv


def test_shift_fillna_false_pattern_no_futurewarning_and_equivalent_semantics():
    """
    Contract:
    - New pattern `shift(1, fill_value=False)` must not emit FutureWarning.
    - Semantics should match the historical intent: missing previous value => False.
    """

    warnings.simplefilter("error", FutureWarning)

    idx = pd.date_range("2024-01-01", periods=10, freq="1h", tz="UTC")
    cond = pd.Series([True, False, True, True, False, False, True, False, True, False], index=idx)

    # New safe expression (should not warn).
    new = cond.shift(1, fill_value=False)

    # "Old intent" expressed without the downcast warning:
    # shift introduces NA; we make dtype explicit first, then fill.
    old_intent = cond.shift(1).astype("boolean").fillna(False)

    pd.testing.assert_series_equal(old_intent.astype(bool), new.astype(bool))
    assert new.dtype != object


def test_strategies_no_downcasting_futurewarning_and_output_dtype_stable():
    """
    Run a minimal set of strategies through the same path as the smoke test and
    treat FutureWarning as errors.
    """

    warnings.simplefilter("error", FutureWarning)

    cfg = load_config()
    df = create_dummy_ohlcv(200)

    # Minimal triggering set from discovery (Cluster B).
    for key in ("trend_following", "mean_reversion", "my_strategy"):
        strategy = create_strategy_from_config(key, cfg)
        signals = strategy.generate_signals(df)

        # Output should never be object; strategies are expected to produce
        # numeric/boolean-ish stable dtypes.
        assert hasattr(signals, "dtype")
        assert signals.dtype != object
