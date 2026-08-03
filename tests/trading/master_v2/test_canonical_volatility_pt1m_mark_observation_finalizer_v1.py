"""Focused tests for PT1M mark observation finalizer v1."""

from __future__ import annotations

import math

import pytest

from trading.master_v2.canonical_volatility_estimate_materializer_v1 import (
    BAR_INTERVAL_SECONDS,
)
from trading.master_v2.canonical_volatility_pt1m_mark_observation_finalizer_v1 import (
    CanonicalVolatilityPt1mMarkObservationFinalizerV1,
    Pt1mMarkObservationFinalizerError,
    pt1m_bucket_start_unix_seconds_v1,
)

T0 = 1_700_000_040.0  # minute-aligned
assert T0 % BAR_INTERVAL_SECONDS == 0.0


def _finalizer() -> CanonicalVolatilityPt1mMarkObservationFinalizerV1:
    return CanonicalVolatilityPt1mMarkObservationFinalizerV1.create(
        venue="okx_europe",
        canonical_instrument_id="ETH-USD_UM_XPERP-310404",
        venue_instrument_id="ETH-USD_UM_XPERP-310404",
    )


def test_same_bucket_updates_without_emit() -> None:
    fin = _finalizer()
    assert fin.observe_mark_v1(event_time_unix_seconds=T0 + 10.0, mark_price=100.0) is None
    assert fin.observe_mark_v1(event_time_unix_seconds=T0 + 40.0, mark_price=101.0) is None
    assert fin.finalized_count == 0


def test_bucket_rollover_emits_prior_last_mark() -> None:
    fin = _finalizer()
    fin.observe_mark_v1(event_time_unix_seconds=T0 + 10.0, mark_price=100.0)
    fin.observe_mark_v1(event_time_unix_seconds=T0 + 40.0, mark_price=101.5)
    emitted = fin.observe_mark_v1(event_time_unix_seconds=T0 + 70.0, mark_price=102.0)
    assert emitted is not None
    assert emitted.mark_price == 101.5
    assert emitted.event_time_unix_seconds == T0 + BAR_INTERVAL_SECONDS
    assert emitted.bucket_start_unix_seconds == T0
    assert fin.finalized_count == 1


def test_out_of_order_bucket_fail_closed() -> None:
    fin = _finalizer()
    fin.observe_mark_v1(event_time_unix_seconds=T0 + 70.0, mark_price=100.0)
    with pytest.raises(Pt1mMarkObservationFinalizerError, match="OUT_OF_ORDER_BUCKET"):
        fin.observe_mark_v1(event_time_unix_seconds=T0 + 10.0, mark_price=99.0)


def test_invalid_mark_fail_closed() -> None:
    fin = _finalizer()
    with pytest.raises(Pt1mMarkObservationFinalizerError):
        fin.observe_mark_v1(event_time_unix_seconds=T0 + 1.0, mark_price=float("nan"))
    with pytest.raises(Pt1mMarkObservationFinalizerError):
        fin.observe_mark_v1(event_time_unix_seconds=T0 + 1.0, mark_price=-1.0)


def test_instrument_reset_isolates_state() -> None:
    fin = _finalizer()
    fin.observe_mark_v1(event_time_unix_seconds=T0 + 10.0, mark_price=100.0)
    fin.observe_mark_v1(event_time_unix_seconds=T0 + 70.0, mark_price=101.0)
    assert fin.finalized_count == 1
    fin.reset_for_instrument_v1(
        venue="okx_europe",
        canonical_instrument_id="OTHER",
        venue_instrument_id="OTHER",
    )
    assert fin.finalized_count == 0
    assert fin.open_bucket_start_unix_seconds is None


def test_bucket_start_helper_aligned() -> None:
    assert pt1m_bucket_start_unix_seconds_v1(T0 + 59.9) == T0
    assert math.isclose(
        pt1m_bucket_start_unix_seconds_v1(T0 + 60.0),
        T0 + BAR_INTERVAL_SECONDS,
        abs_tol=0.0,
    )
