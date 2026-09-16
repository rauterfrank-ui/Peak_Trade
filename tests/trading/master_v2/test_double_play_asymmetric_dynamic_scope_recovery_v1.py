"""DS-A/DS-B/DS-C recovery contracts for Dynamic Scope non-collapse and typed vol.

MODEL_C Scope→Switch distance coupling remains unbound. This suite must not
claim that bind is complete.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.ops.single_selected_future_policy_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    SELECTED_FUTURE_COUNT,
    SINGLE_SELECTED_FUTURE,
)
from trading.master_v2.canonical_market_context_v1 import (
    FEATURE_CONTRACT_VERSION,
    BarFinalityStatus,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    WarmupStatus,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    CanonicalScopeLifecycleState,
    CanonicalScopeSnapshotV1,
)
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    CanonicalVolatilityBindingError,
    CanonicalVolatilityBindingErrorCode,
    bind_typed_canonical_volatility_estimate_into_market_context_v1,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    build_canonical_volatility_estimate_v1,
    with_mutated_field_for_tests_v1,
)
from trading.master_v2.chop_scope_event_policy_binding_v1 import (
    CHOP_CAN_MUTATE_SIDE_STATE,
    SOLE_BULL_BEAR_STATE_OWNER,
    SOLE_SWITCH_AUTHORITY,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType
from trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
    TYPED_VOLATILITY_ESTIMATE_MISSING_REASON,
    evaluate_double_play_runtime_typed_volatility_presence_gate_v1,
)
from trading.master_v2.double_play_state import (
    ActiveSide,
    DynamicScopeRules,
    RuntimeScopeState,
    ScopeEvent,
    SideState,
    clamp_band_width,
    derive_active_side,
    transition_state,
    update_dynamic_boundaries,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    _DEFAULT_RUNTIME_ENVELOPE,
    _effective_dynamic_scope_band_window_v1,
    _resolve_runtime_scope_state_for_cycle_v1,
    _rules_for_cycle_v1,
    _runtime_envelope_containing_scope_v1,
)

ROOT = Path(__file__).resolve().parents[3]
AS_OF = datetime(2026, 6, 1, 1, 0, tzinfo=timezone.utc)
CANONICAL_MIN_SCOPE_BAND = 50.0
CANONICAL_MAX_SCOPE_BAND = 500.0
REPLAY_PATH = ROOT / "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
STATE_PATH = ROOT / "src/trading/master_v2/double_play_state.py"
ENTRY_EXIT_PATH = ROOT / "src/trading/master_v2/double_play_entry_exit_policy_v0.py"


def _typed(*, value: float):
    return build_canonical_volatility_estimate_v1(
        value=value,
        observation_count=60,
        as_of_event_time=AS_OF,
        fallback_used=False,
    )


def _snapshot(
    *,
    min_scope_band: float = CANONICAL_MIN_SCOPE_BAND,
    max_scope_band: float = CANONICAL_MAX_SCOPE_BAND,
    volatility_estimate: float = 0.02,
    mark: float = 2000.0,
) -> CanonicalScopeSnapshotV1:
    band = max(volatility_estimate * mark, min_scope_band)
    return CanonicalScopeSnapshotV1(
        scope_id="scope-ds-recovery",
        instrument_id="inst-eth-usdt-perp",
        initialized_at_trading_epoch=1,
        source_market_context_id="ctx-ds-recovery",
        source_input_digest="a" * 64,
        lifecycle_state=CanonicalScopeLifecycleState.SCOPE_VALID,
        reference_price=mark,
        volatility_estimate=volatility_estimate,
        initial_volatility_distance=volatility_estimate * mark,
        scope_band=band,
        neutral_upper_boundary=mark + band,
        neutral_lower_boundary=mark - band,
        trailing_anchor=mark,
        min_scope_band=min_scope_band,
        max_scope_band=max_scope_band,
        policy_version="v1",
        semantic_digest="b" * 64,
        reason_codes=(),
    )


def _context(**overrides: object) -> CanonicalMarketContextV1:
    base: dict = {
        "context_id": "ctx-ds-recovery-epoch1",
        "instrument_id": "inst-eth-usdt-perp",
        "market_type": FuturesMarketType.PERPETUAL,
        "trading_epoch": 1,
        "market_event_time": "2026-06-30T12:00:00+00:00",
        "decision_time": "2026-06-30T12:00:01+00:00",
        "bar_interval": "1m",
        "bar_finality_status": BarFinalityStatus.FINALIZED,
        "mark_price": 2000.0,
        "index_price": 1999.5,
        "best_bid": 1999.8,
        "best_ask": 2000.2,
        "spread": 0.4,
        "volume": 1_250_000.0,
        "open_interest": 85_000_000.0,
        "funding_rate": 0.00012,
        "volatility_estimate": 0.02,
        "trend_feature_set": {"slope": 0.02},
        "momentum_feature_set": {"rsi": 55.0},
        "liquidity_feature_set": {"depth_score": 0.88},
        "market_structure_feature_set": {"range_ratio": 0.42},
        "data_integrity_status": DataIntegrityStatus.TRUSTED,
        "clock_trust_status": ClockTrustStatus.TRUSTED,
        "warmup_status": WarmupStatus.WARMUP_COMPLETE,
        "feature_contract_version": FEATURE_CONTRACT_VERSION,
        "input_digest": "",
        "canonical_volatility_estimate": None,
    }
    base.update(overrides)
    return CanonicalMarketContextV1(**base)


def _productive_rules(
    *,
    bound_context: CanonicalMarketContextV1 | None = None,
    snapshot: CanonicalScopeSnapshotV1 | None = None,
) -> tuple[DynamicScopeRules, CanonicalScopeSnapshotV1]:
    snap = snapshot or _snapshot()
    rules = _rules_for_cycle_v1(provided=None, snapshot=snap, bound_context=bound_context)
    return rules, snap


# --- DS-A ---


def test_canonical_productive_defaults_do_not_collapse_min_equals_max() -> None:
    rules, snap = _productive_rules()
    env = _runtime_envelope_containing_scope_v1(snap)
    lo, hi = _effective_dynamic_scope_band_window_v1(rules=rules, env=env)
    assert lo == pytest.approx(CANONICAL_MIN_SCOPE_BAND)
    assert hi == pytest.approx(CANONICAL_MAX_SCOPE_BAND)
    assert hi > lo


def test_two_admissible_vol_mark_inputs_produce_distinct_bands_inside_window() -> None:
    rules, snap = _productive_rules()
    env = _runtime_envelope_containing_scope_v1(snap)
    band_a = clamp_band_width(0.05 * 2000.0, rules, env)  # 100
    band_b = clamp_band_width(0.10 * 3000.0, rules, env)  # 300
    assert band_a != band_b
    assert CANONICAL_MIN_SCOPE_BAND <= band_a <= CANONICAL_MAX_SCOPE_BAND
    assert CANONICAL_MIN_SCOPE_BAND <= band_b <= CANONICAL_MAX_SCOPE_BAND


def test_lower_and_upper_snapshot_bounds_respected() -> None:
    rules, snap = _productive_rules()
    env = _runtime_envelope_containing_scope_v1(snap)
    below = clamp_band_width(1.0, rules, env)
    above = clamp_band_width(10_000.0, rules, env)
    assert below == pytest.approx(CANONICAL_MIN_SCOPE_BAND)
    assert above == pytest.approx(CANONICAL_MAX_SCOPE_BAND)


def test_long_active_anchor_still_max_previous_mark() -> None:
    rules, snap = _productive_rules()
    env = _runtime_envelope_containing_scope_v1(snap)
    st = RuntimeScopeState(anchor_price=100.0, now_tick=0)
    st2 = update_dynamic_boundaries(
        mark_price=120.0, side=ActiveSide.LONG, st=st, rules=rules, env=env
    )
    assert st2.anchor_price == 120.0


def test_short_active_anchor_still_min_previous_mark() -> None:
    rules, snap = _productive_rules()
    env = _runtime_envelope_containing_scope_v1(snap)
    st = RuntimeScopeState(anchor_price=100.0, now_tick=0)
    st2 = update_dynamic_boundaries(
        mark_price=80.0, side=ActiveSide.SHORT, st=st, rules=rules, env=env
    )
    assert st2.anchor_price == 80.0


def test_neutral_and_armed_still_freeze() -> None:
    rules, snap = _productive_rules()
    env = _runtime_envelope_containing_scope_v1(snap)
    st = RuntimeScopeState(anchor_price=100.0, now_tick=0)
    frozen_neutral = update_dynamic_boundaries(
        mark_price=180.0, side=ActiveSide.NEUTRAL, st=st, rules=rules, env=env
    )
    assert frozen_neutral.anchor_price == 100.0
    for side in (
        SideState.LONG_ARMED,
        SideState.LONG_ARMED_NEUTRAL_START,
        SideState.LONG_ARMED_SWITCH_TERMINAL,
        SideState.SHORT_ARMED,
        SideState.SHORT_ARMED_NEUTRAL_START,
        SideState.SHORT_ARMED_SWITCH_TERMINAL,
        SideState.NEUTRAL_OBSERVE,
    ):
        assert derive_active_side(side) is ActiveSide.NEUTRAL


def test_prior_runtime_scope_state_not_silently_reseeded() -> None:
    snap = _snapshot()
    prior = RuntimeScopeState(anchor_price=123.0, now_tick=4, current_hysteresis_band=80.0)
    resolved, reinitialized = _resolve_runtime_scope_state_for_cycle_v1(
        instrument_id="inst-eth-usdt-perp",
        current_scope=snap,
        now_tick=5,
        prior_state=prior,
        bound_instrument_id="inst-eth-usdt-perp",
        explicit_reset=False,
    )
    assert reinitialized is False
    assert resolved is prior
    assert resolved.anchor_price == 123.0


# --- DS-B ---


def test_typed_admitted_volatility_reaches_dynamic_scope_rules() -> None:
    snap = _snapshot(volatility_estimate=0.02)
    typed = _typed(value=0.05)
    ctx = bind_typed_canonical_volatility_estimate_into_market_context_v1(_context(), typed)
    rules = _rules_for_cycle_v1(provided=None, snapshot=snap, bound_context=ctx)
    assert rules.volatility_estimate == pytest.approx(0.05)


def test_different_typed_volatility_changes_runtime_band_inside_window() -> None:
    snap = _snapshot()
    env = _runtime_envelope_containing_scope_v1(snap)
    ctx_a = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        _context(mark_price=2000.0), _typed(value=0.05)
    )
    ctx_b = bind_typed_canonical_volatility_estimate_into_market_context_v1(
        _context(mark_price=3000.0), _typed(value=0.10)
    )
    rules_a = _rules_for_cycle_v1(provided=None, snapshot=snap, bound_context=ctx_a)
    rules_b = _rules_for_cycle_v1(provided=None, snapshot=snap, bound_context=ctx_b)
    band_a = clamp_band_width(float(rules_a.volatility_estimate) * 2000.0, rules_a, env)
    band_b = clamp_band_width(float(rules_b.volatility_estimate) * 3000.0, rules_b, env)
    assert band_a != band_b
    assert CANONICAL_MIN_SCOPE_BAND <= band_a <= CANONICAL_MAX_SCOPE_BAND
    assert CANONICAL_MIN_SCOPE_BAND <= band_b <= CANONICAL_MAX_SCOPE_BAND


def test_missing_required_typed_volatility_fails_closed_via_existing_gate() -> None:
    ctx = _context(canonical_volatility_estimate=None)
    gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(ctx)
    assert gate.alpha_scope_entry_authority_allowed is False
    assert TYPED_VOLATILITY_ESTIMATE_MISSING_REASON in gate.reason_codes


def test_invalid_nonfinite_typed_volatility_fails_closed() -> None:
    valid = _typed(value=0.05)
    invalid = with_mutated_field_for_tests_v1(valid, value=float("nan"))
    ctx = _context(
        canonical_volatility_estimate=invalid,
        volatility_estimate=0.05,
    )
    snap = _snapshot()
    with pytest.raises(CanonicalVolatilityBindingError) as exc:
        _rules_for_cycle_v1(provided=None, snapshot=snap, bound_context=ctx)
    assert exc.value.code is CanonicalVolatilityBindingErrorCode.INVALID_ESTIMATE
    assert math.isnan(invalid.value)


def test_legacy_float_cannot_silently_override_admitted_typed_value() -> None:
    typed = _typed(value=0.05)
    bound = bind_typed_canonical_volatility_estimate_into_market_context_v1(_context(), typed)
    mismatched = CanonicalMarketContextV1(
        **{
            **bound.__dict__,
            "volatility_estimate": 0.99,
        }
    )
    snap = _snapshot(volatility_estimate=0.99)
    with pytest.raises(CanonicalVolatilityBindingError) as exc:
        _rules_for_cycle_v1(provided=None, snapshot=snap, bound_context=mismatched)
    assert exc.value.code is CanonicalVolatilityBindingErrorCode.LEGACY_FLOAT_MISMATCH


def test_no_new_volatility_estimator_in_replay_owner() -> None:
    src = REPLAY_PATH.read_text(encoding="utf-8")
    assert "compute_canonical_volatility_estimate_from_mark_prices_v1" not in src
    assert "derive_scope_event_distances_v1" not in src
    assert "resolve_legacy_volatility_float_for_consumer_v1" in src


# --- DS-C ---


def test_one_selected_future_and_max_positions_unchanged() -> None:
    assert SINGLE_SELECTED_FUTURE is True
    assert SELECTED_FUTURE_COUNT == 1
    assert MAX_POSITIONS_EFFECTIVE == 1


def test_sole_sidestate_owner_remains_transition_state() -> None:
    assert SOLE_SWITCH_AUTHORITY == "trading.master_v2.double_play_state.transition_state"
    assert SOLE_BULL_BEAR_STATE_OWNER == "trading.master_v2.double_play_state.transition_state"


def test_candidate_does_not_switch_state_confirmed_does() -> None:
    rules, snap = _productive_rules()
    env = _runtime_envelope_containing_scope_v1(snap)
    st = RuntimeScopeState(anchor_price=100.0, now_tick=0)
    cand_side, _, cand = transition_state(
        side_state=SideState.LONG_ACTIVE,
        event=ScopeEvent.DOWNSCOPE_CANDIDATE,
        scope_state=st,
        rules=rules,
        envelope=env,
        now_tick=1,
    )
    assert cand_side is SideState.LONG_ACTIVE
    assert cand.reason_code == "CANDIDATE_ACK"
    conf_side, _, conf = transition_state(
        side_state=SideState.LONG_ACTIVE,
        event=ScopeEvent.DOWNSCOPE_CONFIRMED,
        scope_state=st,
        rules=rules,
        envelope=env,
        now_tick=1,
    )
    assert conf_side is SideState.SWITCH_LONG_TO_SHORT_PENDING
    assert conf.allowed is True


def test_chop_cannot_write_sidestate() -> None:
    assert CHOP_CAN_MUTATE_SIDE_STATE == "false"
    rules, snap = _productive_rules()
    env = _runtime_envelope_containing_scope_v1(snap)
    st = RuntimeScopeState(anchor_price=100.0, now_tick=0)
    next_side, next_st, _ = transition_state(
        side_state=SideState.LONG_ACTIVE,
        event=ScopeEvent.CHOP_DETECTED,
        scope_state=st,
        rules=rules,
        envelope=env,
        now_tick=1,
    )
    assert next_side is SideState.LONG_ACTIVE
    assert next_st.chop_latched is True


def test_killswitch_is_not_direction_authority_in_state_owner() -> None:
    state_src = STATE_PATH.read_text(encoding="utf-8")
    assert "kill_switch_should_block_trading" not in state_src
    assert "FILEGATE" not in state_src
    replay_src = REPLAY_PATH.read_text(encoding="utf-8")
    assert "kill_switch_should_block_trading" not in replay_src


def test_entry_exit_remains_downstream_and_position_flip_forbidden() -> None:
    replay_src = REPLAY_PATH.read_text(encoding="utf-8")
    switch_at = replay_src.index("transition_state(")
    entry_at = replay_src.index("evaluate_double_play_entry_exit_policy_v0(")
    assert switch_at < entry_at
    entry_src = ENTRY_EXIT_PATH.read_text(encoding="utf-8")
    assert "position_flip_allowed=True" not in entry_src
    assert "position_flip_allowed=False" in entry_src


def test_model_c_remains_unbound_zero_productive_consumers() -> None:
    replay_src = REPLAY_PATH.read_text(encoding="utf-8")
    assert "derive_scope_event_distances_v1" not in replay_src
    assert "up_distance=float(inp.up_distance)" in replay_src
    consumers = []
    for path in (
        REPLAY_PATH,
        ROOT
        / "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py",
        ROOT
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
        / "decision_economics_cycle_bridge_v1.py",
        ROOT / "src/trading/master_v2/deterministic_scope_event_generator_v1.py",
    ):
        text = path.read_text(encoding="utf-8")
        if "derive_scope_event_distances_v1" in text:
            consumers.append(str(path.relative_to(ROOT)))
    assert consumers == []


def test_model_c_bind_not_claimed_complete() -> None:
    # Distance coupling stays Dual Envelope / MODEL_B. Do not treat band restore as bind.
    replay_src = REPLAY_PATH.read_text(encoding="utf-8")
    assert "MODEL_C_BOUND=true" not in replay_src
    assert _DEFAULT_RUNTIME_ENVELOPE.live_authorization is False


def test_owner_recalled_parameter_one_not_bound() -> None:
    replay_src = REPLAY_PATH.read_text(encoding="utf-8")
    assert "OWNER_RECALLED_SWITCH_REGION_PARAMETER" not in replay_src
    rules, snap = _productive_rules()
    assert rules.min_band_width == pytest.approx(CANONICAL_MIN_SCOPE_BAND)
    assert rules.max_band_width == pytest.approx(CANONICAL_MAX_SCOPE_BAND)
