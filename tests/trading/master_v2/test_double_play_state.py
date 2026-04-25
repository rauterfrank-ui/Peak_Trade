# tests/trading/master_v2/test_double_play_state.py
from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from trading.master_v2.double_play_state import (
    ActiveSide,
    DOUBLE_PLAY_STATE_LAYER_VERSION,
    DynamicScopeRules,
    RuntimeEnvelope,
    RuntimeScopeState,
    ScopeEvent,
    SideState,
    StaticHardLimits,
    TransitionDecision,
    derive_active_side,
    envelope_valid,
    rules_valid,
    transition_state,
    update_dynamic_boundaries,
    clamp_band_width,
)

GOOD = StaticHardLimits(
    max_notional=1.0,
    max_leverage=1.0,
    max_switches_per_window=100,
    min_band_width=1.0,
    max_band_width=100.0,
)
GOOD_ENVELOPE = RuntimeEnvelope(static=GOOD, live_authorization=False)
GOOD_RULES = DynamicScopeRules(
    min_band_width=1.0,
    max_band_width=50.0,
    min_switch_cooldown_ticks=0,
    max_switches_per_window=1_000_000,
    volatility_estimate=0.1,
)
EMPTY_ST = RuntimeScopeState()


def _t(
    side: SideState,
    event: ScopeEvent,
    st: RuntimeScopeState,
    now: int = 0,
) -> tuple[SideState, RuntimeScopeState, TransitionDecision]:
    return transition_state(
        side_state=side,
        event=event,
        scope_state=st,
        rules=GOOD_RULES,
        envelope=GOOD_ENVELOPE,
        now_tick=now,
    )


def test_version_constant():
    assert DOUBLE_PLAY_STATE_LAYER_VERSION == "v0"


def test_both_sides_cannot_both_be_active_invariant_expressed_in_derivation():
    """Invariant 1: at most one of LONG/SHORT is ActiveSide active."""
    assert derive_active_side(SideState.LONG_ACTIVE) == ActiveSide.LONG
    assert derive_active_side(SideState.SHORT_ACTIVE) == ActiveSide.SHORT
    assert derive_active_side(SideState.LONG_ARMED) == ActiveSide.NEUTRAL
    assert derive_active_side(SideState.KILL_ALL) == ActiveSide.NEUTRAL
    for s in SideState:
        ab = derive_active_side(s) == ActiveSide.LONG
        be = derive_active_side(s) == ActiveSide.SHORT
        assert not (ab and be)


def test_downscope_pipeline_from_long_active():
    """Downscope from LONG_ACTIVE moves through pending and blocked to SHORT (tests 2)."""
    st = EMPTY_ST
    s, st2, d = _t(SideState.LONG_ACTIVE, ScopeEvent.DOWNSCOPE_CONFIRMED, st, 0)
    assert s == SideState.SWITCH_LONG_TO_SHORT_PENDING and d.allowed
    s, st2, d = _t(s, ScopeEvent.DOWNSCOPE_CONFIRMED, st2, 1)
    assert s == SideState.LONG_BLOCKED and d.allowed
    s, st2, d = _t(s, ScopeEvent.DOWNSCOPE_CONFIRMED, st2, 2)
    assert s == SideState.SHORT_ARMED
    s, st2, d = _t(s, ScopeEvent.DOWNSCOPE_CONFIRMED, st2, 3)
    assert s == SideState.SHORT_ACTIVE and d.reason_code == "SHORT_ACTIVE"


def test_upscope_pipeline_from_short_active():
    """Upscope from SHORT_ACTIVE moves through pending/ blocked to LONG (test 3)."""
    st = EMPTY_ST
    s, st2, d = _t(SideState.SHORT_ACTIVE, ScopeEvent.UPSCOPE_CONFIRMED, st, 0)
    assert s == SideState.SWITCH_SHORT_TO_LONG_PENDING
    s, st2, d = _t(s, ScopeEvent.UPSCOPE_CONFIRMED, st2, 1)
    assert s == SideState.SHORT_BLOCKED
    s, st2, d = _t(s, ScopeEvent.UPSCOPE_CONFIRMED, st2, 2)
    assert s == SideState.LONG_ARMED
    s, st2, d = _t(s, ScopeEvent.UPSCOPE_CONFIRMED, st2, 3)
    assert s == SideState.LONG_ACTIVE


def test_kill_all_overrides_switch():
    """Test 4: KILL_ALL_REQUIRED from PENDING or ACTIVE -> KILL_ALL."""
    s, _, d = _t(SideState.SWITCH_LONG_TO_SHORT_PENDING, ScopeEvent.KILL_ALL_REQUIRED, EMPTY_ST, 0)
    assert s == SideState.KILL_ALL and d.allowed
    s, _, d = _t(SideState.LONG_ACTIVE, ScopeEvent.KILL_ALL_REQUIRED, EMPTY_ST, 0)
    assert s == SideState.KILL_ALL
    s, _, d = _t(SideState.KILL_ALL, ScopeEvent.DOWNSCOPE_CONFIRMED, EMPTY_ST, 0)
    assert s == SideState.KILL_ALL and not d.allowed


def test_chop_blocks_from_short_armed():
    """Test 5: CHOP on armed blocks activation path."""
    s, _, d = _t(SideState.SHORT_ARMED, ScopeEvent.CHOP_DETECTED, EMPTY_ST, 0)
    assert s == SideState.CHOP_GUARD_BLOCK
    s2, _, d2 = _t(s, ScopeEvent.DOWNSCOPE_CONFIRMED, EMPTY_ST, 1)
    assert s2 == SideState.CHOP_GUARD_BLOCK and not d2.allowed


def test_cooldown_prevents_immediate_reversal():
    """Test 6: min_switch_cooldown_ticks blocks starting opposite switch too soon after activation."""
    r = DynamicScopeRules(
        min_band_width=1.0,
        max_band_width=50.0,
        min_switch_cooldown_ticks=5,
        max_switches_per_window=1_000_000,
        volatility_estimate=0.1,
    )
    # Just landed LONG_ACTIVE: last_completed records entry at tick 10
    st_long = replace(EMPTY_ST, last_completed_side_switch_tick=10, last_switch_tick=10)
    s, _, d = transition_state(
        side_state=SideState.LONG_ACTIVE,
        event=ScopeEvent.DOWNSCOPE_CONFIRMED,
        scope_state=st_long,
        rules=r,
        envelope=GOOD_ENVELOPE,
        now_tick=12,  # 12-10 < 5
    )
    assert s == SideState.LONG_ACTIVE and d.reason_code == "COOLDOWN_BLOCK"
    s, _, d = transition_state(
        side_state=SideState.LONG_ACTIVE,
        event=ScopeEvent.DOWNSCOPE_CONFIRMED,
        scope_state=st_long,
        rules=r,
        envelope=GOOD_ENVELOPE,
        now_tick=16,  # 16-10 >= 5
    )
    assert s == SideState.SWITCH_LONG_TO_SHORT_PENDING and d.allowed


def test_invalid_envelope_fails_closed():
    """Test 7: bad envelope / live_auth blocks."""
    bad = RuntimeEnvelope(
        static=StaticHardLimits(min_band_width=10.0, max_band_width=1.0),
        live_authorization=False,
    )
    s, _, d = transition_state(
        side_state=SideState.LONG_ACTIVE,
        event=ScopeEvent.DOWNSCOPE_CONFIRMED,
        scope_state=EMPTY_ST,
        rules=GOOD_RULES,
        envelope=bad,
        now_tick=0,
    )
    assert s == SideState.LONG_ACTIVE and not d.allowed
    live_env = RuntimeEnvelope(static=GOOD, live_authorization=True)
    assert not envelope_valid(live_env)
    s2, _, d2 = transition_state(
        side_state=SideState.LONG_ACTIVE,
        event=ScopeEvent.DOWNSCOPE_CONFIRMED,
        scope_state=EMPTY_ST,
        rules=GOOD_RULES,
        envelope=live_env,
        now_tick=0,
    )
    assert s2 == SideState.LONG_ACTIVE and not d2.allowed


def test_clamp_dynamic_band():
    """Test 8: band width clamped to [min, max] across rules + static."""
    r = DynamicScopeRules(
        min_band_width=1.0,
        max_band_width=10.0,
        min_switch_cooldown_ticks=0,
        max_switches_per_window=1_000_000,
        volatility_estimate=1e6,
    )
    w = clamp_band_width(1e9, r, GOOD_ENVELOPE)
    assert w <= 100.0 and w >= 1.0


def test_trailing_long_anchor_upward():
    """Test 9: long anchor ratchets up; downscope boundary follows below anchor."""
    st = RuntimeScopeState(anchor_price=100.0, now_tick=0)
    r = DynamicScopeRules(
        min_band_width=2.0,
        max_band_width=20.0,
        min_switch_cooldown_ticks=0,
        max_switches_per_window=1_000_000,
        volatility_estimate=0.05,
    )
    st2 = update_dynamic_boundaries(
        mark_price=120.0, side=ActiveSide.LONG, st=st, rules=r, env=GOOD_ENVELOPE
    )
    assert st2.anchor_price == 120.0
    assert st2.current_downscope_boundary < st2.anchor_price
    assert (st2.anchor_price - st2.current_downscope_boundary) == pytest.approx(
        st2.current_hysteresis_band
    )


def test_trailing_short_anchor_downward():
    """Test 10: short anchor ratchets down; upscope boundary follows above."""
    st = RuntimeScopeState(anchor_price=100.0, now_tick=0)
    r = DynamicScopeRules(
        min_band_width=2.0,
        max_band_width=20.0,
        min_switch_cooldown_ticks=0,
        max_switches_per_window=1_000_000,
        volatility_estimate=0.05,
    )
    st2 = update_dynamic_boundaries(
        mark_price=80.0, side=ActiveSide.SHORT, st=st, rules=r, env=GOOD_ENVELOPE
    )
    assert st2.anchor_price == 80.0
    assert st2.current_upscope_boundary > st2.anchor_price


def test_no_transition_grants_live():
    """Test 11: TransitionDecision always has live_authorization_granted False."""
    for ev in ScopeEvent:
        s, _, d = _t(SideState.LONG_ACTIVE, ev, EMPTY_ST, 0)
        assert d.live_authorization_granted is False
        s, _, d = _t(SideState.NEUTRAL_OBSERVE, ev, EMPTY_ST, 0)
        assert d.live_authorization_granted is False


def test_pure_module_no_network_side_effect_imports():
    """Test 12: module uses stdlib + local imports only; transition is referentially transparent."""
    p = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src"
        / "trading"
        / "master_v2"
        / "double_play_state.py"
    )
    tree = ast.parse(p.read_text(encoding="utf-8"))
    bad = {"requests", "urllib", "ccxt", "httpx", "socket"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                assert n.name.split(".")[0] not in bad
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in bad:
                raise AssertionError(node.module)
    a = _t(SideState.LONG_ACTIVE, ScopeEvent.NOOP, EMPTY_ST, 0)
    b = _t(SideState.LONG_ACTIVE, ScopeEvent.NOOP, EMPTY_ST, 0)
    assert a == b


def test_invalid_rules_fails():
    r = DynamicScopeRules(
        min_band_width=20.0,
        max_band_width=1.0,
    )
    assert not rules_valid(r)
    s, _, d = transition_state(
        side_state=SideState.LONG_ACTIVE,
        event=ScopeEvent.DOWNSCOPE_CONFIRMED,
        scope_state=EMPTY_ST,
        rules=r,
        envelope=GOOD_ENVELOPE,
        now_tick=0,
    )
    assert not d.allowed
