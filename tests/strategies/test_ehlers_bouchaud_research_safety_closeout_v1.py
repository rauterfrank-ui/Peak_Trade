"""Research safety / input-contract closeout for Ehlers and Bouchaud (Long/Flat only)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.strategies.bouchaud import BouchaudMicrostructureStrategy
from src.strategies.ehlers import EhlersCycleFilterStrategy
from src.strategies.registry import get_strategy_registry_entry, get_strategy_spec

_RESEARCH_KEYS = ("ehlers_cycle_filter", "bouchaud_microstructure")


def _ehlers_valid_frame(n: int = 150, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    close = 100.0 + np.cumsum(rng.normal(0.0, 0.5, n))
    return pd.DataFrame({"close": close}, index=idx)


def _bouchaud_valid_ohlc_frame(n: int = 150) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n, freq="h", tz="UTC")
    close = np.linspace(100.0, 150.0, n)
    return pd.DataFrame(
        {
            "open": close - 1.0,
            "high": close + 0.2,
            "low": close - 1.2,
            "close": close,
            "volume": np.full(n, 1000.0),
        },
        index=idx,
    )


# =============================================================================
# Registry / Non-Authority metadata
# =============================================================================


@pytest.mark.parametrize("key", _RESEARCH_KEYS)
def test_registry_research_only_non_live(key: str) -> None:
    spec = get_strategy_spec(key)
    assert spec.is_live_ready is False
    assert spec.tier == "r_and_d"
    assert "live" not in spec.allowed_environments
    assert "paper" not in spec.allowed_environments
    assert set(spec.allowed_environments) <= {"offline_backtest", "research", "backtest"}
    assert "offline_backtest" in spec.allowed_environments
    assert "research" in spec.allowed_environments
    assert "Non-Authority" in spec.description or "R&D" in spec.description
    entry = get_strategy_registry_entry(key)
    assert "live_ready" not in entry.capability_tags
    assert "production" not in entry.capability_tags


def test_class_flags_match_registry() -> None:
    assert EhlersCycleFilterStrategy.IS_LIVE_READY is False
    assert EhlersCycleFilterStrategy.TIER == "r_and_d"
    assert BouchaudMicrostructureStrategy.IS_LIVE_READY is False
    assert BouchaudMicrostructureStrategy.TIER == "r_and_d"
    assert get_strategy_spec("ehlers_cycle_filter").is_live_ready is False
    assert get_strategy_spec("bouchaud_microstructure").is_live_ready is False


# =============================================================================
# Ehlers
# =============================================================================


class TestEhlersResearchSafetyCloseout:
    def test_ehlers_valid_input_output_parity_exact(self) -> None:
        """Golden capture from pre-change Super-Smoother path (seed=42, n=150)."""
        expected = [
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            1,
            1,
            0,
            1,
            1,
            1,
            1,
            1,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            1,
            1,
            0,
            0,
            1,
            1,
            1,
            1,
            1,
            1,
            0,
            0,
            1,
            1,
            1,
            0,
            0,
            1,
            1,
            1,
            0,
            0,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            1,
            0,
            0,
            0,
            0,
            0,
            1,
            0,
            1,
            0,
            0,
            0,
            1,
            1,
            1,
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            1,
            1,
            1,
            0,
            1,
            1,
            0,
            1,
            0,
            0,
            0,
            0,
            1,
            0,
            0,
            1,
            1,
            1,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            0,
            0,
            1,
            1,
            1,
            0,
            0,
            0,
            0,
            1,
            0,
            0,
            1,
            0,
            0,
            0,
            0,
            1,
            1,
            1,
            1,
            0,
            0,
            1,
            1,
            1,
            1,
            1,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
            0,
            0,
            0,
            1,
            1,
            1,
            1,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            1,
            1,
        ]
        strategy = EhlersCycleFilterStrategy(lookback=100, min_cycle_length=6)
        signals = strategy.generate_signals(_ehlers_valid_frame())
        assert signals.tolist() == expected
        assert set(signals.unique()).issubset({0, 1})

    def test_ehlers_empty_input_safe_neutral(self) -> None:
        strategy = EhlersCycleFilterStrategy()
        out = strategy.generate_signals(pd.DataFrame({"close": []}))
        assert len(out) == 0
        assert out.attrs.get("is_research_stub") is False

    def test_ehlers_missing_close_fail_closed(self) -> None:
        strategy = EhlersCycleFilterStrategy()
        with pytest.raises(ValueError, match="close"):
            strategy.generate_signals(pd.DataFrame({"open": [1.0, 2.0]}))

    def test_ehlers_nan_inf_no_entry_intent(self) -> None:
        strategy = EhlersCycleFilterStrategy(lookback=10)
        idx = pd.date_range("2024-01-01", periods=20, freq="h", tz="UTC")
        for bad in (np.nan, np.inf, -np.inf):
            close = np.linspace(100.0, 110.0, 20)
            close[5] = bad
            out = strategy.generate_signals(pd.DataFrame({"close": close}, index=idx))
            assert (out == 0).all()
            assert out.attrs.get("invalid_input") is True

    def test_ehlers_insufficient_history_flat(self) -> None:
        strategy = EhlersCycleFilterStrategy(lookback=100)
        idx = pd.date_range("2024-01-01", periods=10, freq="h", tz="UTC")
        out = strategy.generate_signals(pd.DataFrame({"close": [100.0] * 10}, index=idx))
        assert (out == 0).all()
        assert out.attrs.get("insufficient_history") is True

    def test_ehlers_constant_series_deterministic(self) -> None:
        strategy = EhlersCycleFilterStrategy(lookback=20, min_cycle_length=6)
        idx = pd.date_range("2024-01-01", periods=40, freq="h", tz="UTC")
        df = pd.DataFrame({"close": [100.0] * 40}, index=idx)
        a = strategy.generate_signals(df)
        b = strategy.generate_signals(df)
        assert a.equals(b)
        assert set(a.unique()).issubset({0, 1})

    def test_ehlers_no_lookahead_prefix_consistency(self) -> None:
        strategy = EhlersCycleFilterStrategy(lookback=30, min_cycle_length=6)
        df = _ehlers_valid_frame(n=80)
        full = strategy.generate_signals(df)
        for t in (40, 50, 60, 70):
            prefix = strategy.generate_signals(df.iloc[: t + 1])
            assert int(prefix.iloc[-1]) == int(full.iloc[t])

    def test_ehlers_long_flat_vocabulary_only(self) -> None:
        strategy = EhlersCycleFilterStrategy(lookback=20)
        out = strategy.generate_signals(_ehlers_valid_frame(n=50))
        assert set(map(int, out.unique())).issubset({0, 1})
        assert -1 not in set(map(int, out.unique()))

    def test_ehlers_duplicate_index_flat(self) -> None:
        strategy = EhlersCycleFilterStrategy(lookback=5)
        idx = pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02"] * 4)
        out = strategy.generate_signals(pd.DataFrame({"close": list(range(12))}, index=idx))
        assert (out == 0).all()
        assert out.attrs.get("invalid_input") is True


# =============================================================================
# Bouchaud
# =============================================================================


class TestBouchaudResearchSafetyCloseout:
    def test_bouchaud_valid_ohlc_output_parity_exact(self) -> None:
        strategy = BouchaudMicrostructureStrategy(lookback_ticks=20, imbalance_threshold=0.3)
        out = strategy.generate_signals(_bouchaud_valid_ohlc_frame())
        assert (out == 1).all()
        assert set(out.unique()).issubset({0, 1})
        assert out.attrs.get("proxy_data_risk") == "HIGH"

    def test_bouchaud_empty_input_safe_neutral(self) -> None:
        strategy = BouchaudMicrostructureStrategy()
        out = strategy.generate_signals(pd.DataFrame({"close": []}))
        assert len(out) == 0

    def test_bouchaud_missing_close_fail_closed(self) -> None:
        strategy = BouchaudMicrostructureStrategy()
        with pytest.raises(ValueError, match="close"):
            strategy.generate_signals(pd.DataFrame({"volume": [1.0]}))

    def test_bouchaud_zero_range_candle_no_division_error(self) -> None:
        strategy = BouchaudMicrostructureStrategy(lookback_ticks=5, imbalance_threshold=0.0)
        idx = pd.date_range("2024-01-01", periods=10, freq="h", tz="UTC")
        df = pd.DataFrame(
            {
                "open": [100.0] * 10,
                "high": [100.0] * 10,
                "low": [100.0] * 10,
                "close": [100.0] * 10,
                "volume": [1000.0] * 10,
            },
            index=idx,
        )
        out = strategy.generate_signals(df)
        assert len(out) == 10
        assert set(map(int, out.unique())).issubset({0, 1})

    def test_bouchaud_nan_inf_no_entry_intent(self) -> None:
        strategy = BouchaudMicrostructureStrategy(lookback_ticks=5)
        idx = pd.date_range("2024-01-01", periods=10, freq="h", tz="UTC")
        df = _bouchaud_valid_ohlc_frame(n=10)
        df.loc[idx[3], "close"] = np.inf
        out = strategy.generate_signals(df)
        assert (out == 0).all()
        assert out.attrs.get("invalid_input") is True

    def test_bouchaud_negative_volume_fail_closed_flat(self) -> None:
        strategy = BouchaudMicrostructureStrategy(lookback_ticks=5)
        df = _bouchaud_valid_ohlc_frame(n=10)
        df.iloc[2, df.columns.get_loc("volume")] = -1.0
        out = strategy.generate_signals(df)
        assert (out == 0).all()
        assert out.attrs.get("invalid_reason") == "invalid_volume"

    def test_bouchaud_insufficient_history_flat(self) -> None:
        strategy = BouchaudMicrostructureStrategy(lookback_ticks=50)
        df = _bouchaud_valid_ohlc_frame(n=10)
        out = strategy.generate_signals(df)
        assert (out == 0).all()
        assert out.attrs.get("insufficient_history") is True

    def test_bouchaud_no_lookahead_prefix_consistency(self) -> None:
        strategy = BouchaudMicrostructureStrategy(lookback_ticks=20, imbalance_threshold=0.3)
        df = _bouchaud_valid_ohlc_frame(n=80)
        full = strategy.generate_signals(df)
        for t in (40, 50, 60, 70):
            prefix = strategy.generate_signals(df.iloc[: t + 1])
            assert int(prefix.iloc[-1]) == int(full.iloc[t])

    def test_bouchaud_long_flat_vocabulary_only(self) -> None:
        strategy = BouchaudMicrostructureStrategy(lookback_ticks=20)
        out = strategy.generate_signals(_bouchaud_valid_ohlc_frame(n=50))
        assert set(map(int, out.unique())).issubset({0, 1})
        assert -1 not in set(map(int, out.unique()))

    def test_bouchaud_high_lt_low_flat(self) -> None:
        strategy = BouchaudMicrostructureStrategy(lookback_ticks=5)
        df = _bouchaud_valid_ohlc_frame(n=10)
        df.iloc[1, df.columns.get_loc("high")] = 90.0
        df.iloc[1, df.columns.get_loc("low")] = 110.0
        out = strategy.generate_signals(df)
        assert (out == 0).all()
        assert out.attrs.get("invalid_reason") == "high_lt_low"
