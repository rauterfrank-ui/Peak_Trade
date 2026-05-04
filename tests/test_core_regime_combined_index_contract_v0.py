"""Contract tests for ``label_combined_regime`` index alignment (v0)."""

from __future__ import annotations

import pandas as pd
import pytest

from src.core.regime import label_combined_regime


def test_label_combined_regime_same_index_contract_v0() -> None:
    idx = pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC")
    trend = pd.Series(
        ["TREND_UP", "RANGE", "TREND_DOWN"], index=idx, dtype="object", name="trend_regime"
    )
    vol = pd.Series(
        ["HIGH_VOL", "LOW_VOL", "LOW_VOL"], index=idx, dtype="object", name="vol_regime"
    )

    out = label_combined_regime(trend, vol)

    assert out.name == "regime"
    assert str(out.dtype) == "string"
    pd.testing.assert_index_equal(out.index, idx)
    assert list(out) == ["TREND_UP_HIGH_VOL", "RANGE_LOW_VOL", "TREND_DOWN_LOW_VOL"]


def test_label_combined_regime_rejects_mismatched_index_contract_v0() -> None:
    idx_a = pd.date_range("2024-01-01", periods=2, freq="D", tz="UTC")
    idx_b = pd.date_range("2024-01-02", periods=2, freq="D", tz="UTC")
    trend = pd.Series(["RANGE", "RANGE"], index=idx_a, dtype="object")
    vol = pd.Series(["LOW_VOL", "LOW_VOL"], index=idx_b, dtype="object")

    with pytest.raises(ValueError, match="trend and volatility label indexes must match"):
        label_combined_regime(trend, vol)


def test_label_combined_regime_rejects_mismatched_length_contract_v0() -> None:
    idx_a = pd.date_range("2024-01-01", periods=2, freq="D", tz="UTC")
    idx_b = pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC")
    trend = pd.Series(["RANGE", "RANGE"], index=idx_a, dtype="object")
    vol = pd.Series(["LOW_VOL", "LOW_VOL", "LOW_VOL"], index=idx_b, dtype="object")

    with pytest.raises(ValueError, match="trend and volatility label indexes must match"):
        label_combined_regime(trend, vol)
