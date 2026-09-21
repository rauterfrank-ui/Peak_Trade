"""Primitive tests for naked_mv2_dp_single_boundary_purification_v1 (no legacy generator)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    WarmupStatus,
    with_computed_input_digest,
)
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    build_canonical_volatility_estimate_v1,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeDirectionState
from trading.master_v2.double_play_entry_exit_policy_v0 import PolicySignalV0
from trading.master_v2.double_play_futures_input import FuturesMarketType
from trading.master_v2.double_play_state import ActiveSide, RuntimeScopeState, SideState
from trading.master_v2.naked_mv2_dp_single_boundary_purification_v1 import (
    compute_counter_move_v1,
    compute_single_boundary_distance_v1,
    resolve_typed_sigma_for_naked_boundary_v1,
    suppress_naked_active_profit_protection_signal_v1,
    update_scope_internal_reference_state_v1,
)
from tests.trading.master_v2.naked_single_boundary_replay_test_support_v1 import (
    with_typed_volatility_for_replay_tests_v1,
)

_AS_OF = datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc)


def _cmc(**overrides: object) -> CanonicalMarketContextV1:
    base: dict = {
        "context_id": "ctx-1",
        "instrument_id": "inst-x",
        "market_type": FuturesMarketType.PERPETUAL,
        "trading_epoch": 10,
        "market_event_time": "2026-06-30T12:00:00+00:00",
        "decision_time": "2026-06-30T12:00:01+00:00",
        "bar_interval": "1m",
        "bar_finality_status": BarFinalityStatus.FINALIZED,
        "mark_price": 100.0,
        "index_price": 99.0,
        "best_bid": 99.9,
        "best_ask": 100.1,
        "spread": 0.2,
        "volume": 1.0,
        "open_interest": 1.0,
        "funding_rate": 0.0,
        "volatility_estimate": 0.01,
        "trend_feature_set": {"slope": 0.0},
        "momentum_feature_set": {"rsi": 50.0},
        "liquidity_feature_set": {"depth_score": 1.0},
        "market_structure_feature_set": {"range_ratio": 0.5},
        "data_integrity_status": DataIntegrityStatus.TRUSTED,
        "clock_trust_status": ClockTrustStatus.TRUSTED,
        "warmup_status": WarmupStatus.WARMUP_COMPLETE,
        "feature_contract_version": "v1",
        "input_digest": "",
    }
    base.update(overrides)
    return with_computed_input_digest(CanonicalMarketContextV1(**base))


def test_nulline_mark_follows_trusted_cmc() -> None:
    ctx = with_typed_volatility_for_replay_tests_v1(_cmc(mark_price=123.45))
    sigma, blocks = resolve_typed_sigma_for_naked_boundary_v1(ctx)
    assert not blocks
    assert sigma is not None
    assert ctx.mark_price == pytest.approx(123.45)
    assert compute_single_boundary_distance_v1(sigma_t=sigma, mark_price=ctx.mark_price) is None


def test_numeric_formula_authority_none_productive_distance() -> None:
    from trading.master_v2.naked_mv2_dp_single_boundary_purification_v1 import (
        NUMERIC_FORMULA_AUTHORITY,
    )

    assert NUMERIC_FORMULA_AUTHORITY == "NONE"
    assert compute_single_boundary_distance_v1(sigma_t=0.01, mark_price=100.0) is None


def test_bull_favorable_continuation_cm_zero() -> None:
    st = RuntimeScopeState(anchor_price=100.0)
    st = update_scope_internal_reference_state_v1(mark_price=110.0, side=ActiveSide.LONG, st=st)
    assert st.anchor_price == 110.0
    cm = compute_counter_move_v1(
        direction=ScopeDirectionState.LONG, mark_price=110.0, reference_price=st.anchor_price
    )
    assert cm == 0.0


def test_countermove_from_r_not_mark_alone() -> None:
    cm = compute_counter_move_v1(
        direction=ScopeDirectionState.LONG, mark_price=95.0, reference_price=100.0
    )
    assert cm == 5.0


def test_typed_sigma_only_missing_fail_closed() -> None:
    ctx = _cmc()
    sigma, blocks = resolve_typed_sigma_for_naked_boundary_v1(ctx)
    assert sigma is None
    assert "naked_typed_sigma_missing" in blocks


def test_sigma_zero_fail_closed() -> None:
    est = build_canonical_volatility_estimate_v1(
        value=0.0,
        observation_count=60,
        as_of_event_time=_AS_OF,
        fallback_used=False,
    )
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(_cmc(), est)
    sigma, blocks = resolve_typed_sigma_for_naked_boundary_v1(ctx)
    assert sigma is None
    assert "naked_typed_sigma_non_positive" in blocks


def test_profit_protection_suppressed_on_active() -> None:
    sig = suppress_naked_active_profit_protection_signal_v1(
        SideState.LONG_ACTIVE, PolicySignalV0(triggered=True)
    )
    assert sig.triggered is False


def test_bull_bear_symmetry_counter_move() -> None:
    bull = compute_counter_move_v1(
        direction=ScopeDirectionState.LONG, mark_price=90.0, reference_price=100.0
    )
    bear = compute_counter_move_v1(
        direction=ScopeDirectionState.SHORT, mark_price=110.0, reference_price=100.0
    )
    assert bull == bear == 10.0
