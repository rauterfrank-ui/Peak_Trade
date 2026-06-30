"""RUNBOOK STEP 29M — deterministic offline funding model v1 tests."""

from __future__ import annotations

import math
from typing import Any, Mapping

import pandas as pd
import pytest

from src.backtest import funding_model_v1 as fm


def _bars(
    *,
    n: int = 24,
    start: str = "2026-06-01",
    funding_rates: list[float] | None = None,
    mark_prices: list[float] | None = None,
) -> pd.DataFrame:
    idx = pd.date_range(start, periods=n, freq="1h", tz="UTC")
    close = [100.0 + float(i) for i in range(n)]
    rates = funding_rates if funding_rates is not None else [0.0001 for _ in range(n)]
    marks = mark_prices if mark_prices is not None else close
    return pd.DataFrame(
        {
            "open": close,
            "high": [v + 0.5 for v in close],
            "low": [v - 0.5 for v in close],
            "close": close,
            "mark_price": marks,
            "index_price": [v - 0.1 for v in close],
            "best_bid": [v - 0.05 for v in close],
            "best_ask": [v + 0.05 for v in close],
            "spread": [0.1 for _ in close],
            "volume": [1000.0 for _ in close],
            "open_interest": [10000.0 for _ in close],
            "funding_rate": rates,
            "volatility_estimate": [0.2 for _ in close],
            "is_final": [True for _ in close],
            "bar_interval": ["1h" for _ in close],
        },
        index=idx,
    )


def _positions(bars: pd.DataFrame, sign: int) -> pd.Series:
    return pd.Series([sign for _ in bars.index], index=bars.index, dtype=int)


def _cfg_with_funding() -> Mapping[str, Any]:
    return {
        "backtest": {
            "initial_cash": 10_000.0,
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
            "funding": {
                "bind": True,
                "model_version": fm.FUNDING_MODEL_VERSION,
            },
        }
    }


class TestFundingModelConfig:
    def test_default_config_version_bound(self) -> None:
        cfg = fm.default_funding_model_config_v1()
        assert cfg.model_version == fm.FUNDING_MODEL_VERSION
        assert len(cfg.config_digest()) == 64

    def test_load_from_cfg(self) -> None:
        loaded = fm.load_funding_model_config_v1(_cfg_with_funding())
        assert loaded.payment_interval_hours == fm.DEFAULT_PAYMENT_INTERVAL_HOURS

    def test_binding_requested(self) -> None:
        assert fm.funding_binding_requested(_cfg_with_funding()) is True
        assert fm.funding_binding_requested({"backtest": {"fee_bps": 1.0}}) is False


class TestFundingRateClassification:
    def test_explicit_zero_distinct_from_missing(self) -> None:
        assert fm.classify_funding_rate_value(0.0) is fm.FundingRatePresence.EXPLICIT_ZERO
        assert fm.classify_funding_rate_value(None) is fm.FundingRatePresence.MISSING
        assert fm.classify_funding_rate_value(float("nan")) is fm.FundingRatePresence.MISSING

    def test_positive_rate_present(self) -> None:
        assert fm.classify_funding_rate_value(0.0001) is fm.FundingRatePresence.PRESENT

    def test_negative_rate_present(self) -> None:
        assert fm.classify_funding_rate_value(-0.0002) is fm.FundingRatePresence.PRESENT


class TestFundingPayments:
    def test_long_positive_rate_payment(self) -> None:
        bars = _bars(n=9, funding_rates=[0.0] * 8 + [0.001])
        bars.index = pd.DatetimeIndex(
            [
                "2026-06-01T00:00:00+00:00",
                "2026-06-01T01:00:00+00:00",
                "2026-06-01T02:00:00+00:00",
                "2026-06-01T03:00:00+00:00",
                "2026-06-01T04:00:00+00:00",
                "2026-06-01T05:00:00+00:00",
                "2026-06-01T06:00:00+00:00",
                "2026-06-01T07:00:00+00:00",
                "2026-06-01T08:00:00+00:00",
            ]
        )
        result = fm.compute_funding_drag_v1(
            bars=bars,
            position_series=_positions(bars, 1),
            initial_equity=10_000.0,
        )
        assert result.payment_count == 2
        assert result.total_payment_amount < 0.0

    def test_short_positive_rate_payment(self) -> None:
        bars = _bars(n=9, funding_rates=[0.0] * 8 + [0.001])
        bars.index = pd.DatetimeIndex(
            [
                "2026-06-01T00:00:00+00:00",
                "2026-06-01T01:00:00+00:00",
                "2026-06-01T02:00:00+00:00",
                "2026-06-01T03:00:00+00:00",
                "2026-06-01T04:00:00+00:00",
                "2026-06-01T05:00:00+00:00",
                "2026-06-01T06:00:00+00:00",
                "2026-06-01T07:00:00+00:00",
                "2026-06-01T08:00:00+00:00",
            ]
        )
        long_result = fm.compute_funding_drag_v1(
            bars=bars,
            position_series=_positions(bars, 1),
            initial_equity=10_000.0,
        )
        short_result = fm.compute_funding_drag_v1(
            bars=bars,
            position_series=_positions(bars, -1),
            initial_equity=10_000.0,
        )
        assert short_result.total_payment_amount == pytest.approx(-long_result.total_payment_amount)

    def test_negative_rate(self) -> None:
        bars = _bars(n=1, funding_rates=[-0.001])
        bars.index = pd.DatetimeIndex(["2026-06-01T00:00:00+00:00"])
        result = fm.compute_funding_drag_v1(
            bars=bars,
            position_series=_positions(bars, 1),
            initial_equity=10_000.0,
        )
        assert result.total_payment_amount > 0.0

    def test_explicit_zero_rate(self) -> None:
        bars = _bars(n=1, funding_rates=[0.0])
        bars.index = pd.DatetimeIndex(["2026-06-01T00:00:00+00:00"])
        result = fm.compute_funding_drag_v1(
            bars=bars,
            position_series=_positions(bars, 1),
            initial_equity=10_000.0,
        )
        assert result.total_payment_amount == 0.0
        assert result.explicit_zero_rate_count == 1
        assert fm.REASON_EXPLICIT_ZERO_RATE in result.reason_codes

    def test_missing_rate_fail_closed(self) -> None:
        bars = _bars(n=1, funding_rates=[float("nan")])
        bars.index = pd.DatetimeIndex(["2026-06-01T00:00:00+00:00"])
        with pytest.raises(fm.FundingModelError, match=fm.REASON_MISSING_FUNDING_RATE):
            fm.compute_funding_drag_v1(
                bars=bars,
                position_series=_positions(bars, 1),
                initial_equity=10_000.0,
            )

    def test_missing_series_fail_closed(self) -> None:
        bars = _bars()
        del bars["funding_rate"]
        with pytest.raises(fm.FundingModelError, match=fm.REASON_MISSING_FUNDING_SERIES):
            fm.compute_funding_drag_v1(
                bars=bars,
                position_series=_positions(bars, 1),
                initial_equity=10_000.0,
            )

    def test_interval_boundary_only(self) -> None:
        bars = _bars(n=3, funding_rates=[0.001, 0.002, 0.003])
        bars.index = pd.DatetimeIndex(
            [
                "2026-06-01T00:00:00+00:00",
                "2026-06-01T01:00:00+00:00",
                "2026-06-01T08:00:00+00:00",
            ]
        )
        result = fm.compute_funding_drag_v1(
            bars=bars,
            position_series=_positions(bars, 1),
            initial_equity=10_000.0,
        )
        assert result.payment_count == 2

    def test_duplicate_event_fail_closed(self) -> None:
        bars = _bars(n=2, funding_rates=[0.001, 0.002])
        bars.index = pd.DatetimeIndex(
            [
                "2026-06-01T00:00:00+00:00",
                "2026-06-01T00:00:00+00:00",
            ]
        )
        with pytest.raises(fm.FundingModelError, match=fm.REASON_DUPLICATE_FUNDING_EVENT):
            fm.compute_funding_drag_v1(
                bars=bars,
                position_series=_positions(bars, 1),
                initial_equity=10_000.0,
            )

    def test_out_of_order_event_fail_closed(self) -> None:
        bars = _bars(n=2, funding_rates=[0.001, 0.002])
        bars.index = pd.DatetimeIndex(
            [
                "2026-06-01T08:00:00+00:00",
                "2026-06-01T00:00:00+00:00",
            ]
        )
        with pytest.raises(fm.FundingModelError, match=fm.REASON_OUT_OF_ORDER_FUNDING_EVENT):
            fm.compute_funding_drag_v1(
                bars=bars,
                position_series=_positions(bars, 1),
                initial_equity=10_000.0,
            )

    def test_funding_drag_aggregation(self) -> None:
        bars = _bars(n=17, funding_rates=[0.0005 for _ in range(17)])
        result = fm.compute_funding_drag_v1(
            bars=bars,
            position_series=_positions(bars, 1),
            initial_equity=10_000.0,
        )
        assert result.funding_drag == pytest.approx(result.total_payment_amount / 10_000.0)

    def test_deterministic_replay(self) -> None:
        bars = _bars()
        positions = _positions(bars, 1)
        a = fm.compute_funding_drag_v1(
            bars=bars,
            position_series=positions,
            initial_equity=10_000.0,
            data_digest="abc",
        )
        b = fm.compute_funding_drag_v1(
            bars=bars,
            position_series=positions,
            initial_equity=10_000.0,
            data_digest="abc",
        )
        assert a.to_dict() == b.to_dict()
        assert a.evidence_digest() == b.evidence_digest()

    def test_digest_binding_changes_with_data(self) -> None:
        bars_a = _bars()
        bars_b = _bars(funding_rates=[0.0002 for _ in range(24)])
        pos = _positions(bars_a, 1)
        a = fm.compute_funding_drag_v1(
            bars=bars_a,
            position_series=pos,
            initial_equity=10_000.0,
            data_digest="digest_a",
        )
        b = fm.compute_funding_drag_v1(
            bars=bars_b,
            position_series=_positions(bars_b, 1),
            initial_equity=10_000.0,
            data_digest="digest_b",
        )
        assert a.evidence_digest() != b.evidence_digest()


class TestCostConfigFundingBinding:
    def test_cost_config_binds_funding_when_requested(self) -> None:
        from src.backtest.cost_config_v0 import (
            REASON_FUNDING_BOUND,
            resolve_effective_backtest_cost_config,
        )

        cost = resolve_effective_backtest_cost_config(_cfg_with_funding())
        assert cost.funding_model_version == fm.FUNDING_MODEL_VERSION
        assert REASON_FUNDING_BOUND in cost.reason_codes

    def test_cost_config_unbound_without_funding_section(self) -> None:
        from src.backtest.cost_config_v0 import (
            FUNDING_MODEL_VERSION,
            resolve_effective_backtest_cost_config,
        )

        cost = resolve_effective_backtest_cost_config(
            {"backtest": {"fee_bps": 10.0, "slippage_bps": 5.0}}
        )
        assert cost.funding_model_version == FUNDING_MODEL_VERSION


def test_schema_contract() -> None:
    schema = fm.funding_model_schema_v1()
    assert schema["runtime_effect"] is False
    assert schema["order_effect"] is False
