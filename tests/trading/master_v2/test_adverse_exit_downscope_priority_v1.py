"""Contract: preserve DOWNSCOPE_* alongside adverse exit (dual-dimension)."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from src.backtest.mv2_research_wiring_v1 import (
    compute_mv2_research_scope_distances_absolute_from_mark_v1,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    CanonicalScopeEventType,
    ScopeCandidateKind,
    ScopeConfirmationStateV1,
    ScopeCooldownStateV1,
    ScopeDirectionState,
    ScopeEventGeneratorInputV1,
    ScopeEventGeneratorPolicyV1,
    generate_deterministic_scope_event,
)
from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    ClockTrustStatus,
    DataIntegrityStatus,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    CanonicalScopeLifecycleState,
    CanonicalScopeSnapshotV1,
    SCOPE_INITIALIZATION_POLICY_VERSION,
    with_computed_semantic_digest,
)
from trading.master_v2.double_play_sole_authority_quarantine_v1 import (
    CANONICAL_BULL_BEAR_STATE_OWNER,
    CANONICAL_COMPOSITION_AUTHORITY,
    CANONICAL_SWITCH_AUTHORITY,
    LIVE_AUTHORIZED,
    ORDERS_ENABLED,
    RUNTIME_BRIDGE_STATUS,
)
from trading.master_v2.double_play_state import (
    DynamicScopeRules,
    RuntimeEnvelope,
    RuntimeScopeState,
    ScopeEvent,
    SideState,
    StaticHardLimits,
    transition_state,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    _canonical_scope_event_to_scope_event,
)
from trading.master_v2.scope_event_generator_scenario_binding_adapter_v0 import (
    derive_scope_adverse_exit_signal_v0,
)
from trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyEntrySideCarrierV1,
)

_GENERATOR = Path("src/trading/master_v2/deterministic_scope_event_generator_v1.py")
_REPLAY = Path("src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py")
_WIRING = Path("src/backtest/mv2_research_wiring_v1.py")


def _scope() -> CanonicalScopeSnapshotV1:
    scope = CanonicalScopeSnapshotV1(
        scope_id="scope-test-epoch0",
        instrument_id="inst-eth-usdt-perp",
        initialized_at_trading_epoch=0,
        source_market_context_id="ctx-test",
        source_input_digest="a" * 64,
        lifecycle_state=CanonicalScopeLifecycleState.SCOPE_VALID,
        reference_price=100.0,
        volatility_estimate=0.2,
        initial_volatility_distance=20.0,
        scope_band=50.0,
        neutral_upper_boundary=150.0,
        neutral_lower_boundary=50.0,
        trailing_anchor=100.0,
        min_scope_band=10.0,
        max_scope_band=200.0,
        policy_version=SCOPE_INITIALIZATION_POLICY_VERSION,
        semantic_digest="",
        reason_codes=(),
    )
    return with_computed_semantic_digest(scope)


def _policy() -> ScopeEventGeneratorPolicyV1:
    return ScopeEventGeneratorPolicyV1(
        hard_max_scope_distance=1000.0,
        hard_max_adverse_distance=500.0,
        hard_max_reversal_distance=800.0,
    )


def _generate(
    *,
    current_price: float,
    up_distance: float = 2.0,
    adverse_exit_distance: float = 1.0,
    reversal_distance: float = 1.5,
    confirmation_state: ScopeConfirmationStateV1 | None = None,
    trading_epoch: int = 1,
    direction: ScopeDirectionState = ScopeDirectionState.LONG,
) -> object:
    conf = confirmation_state or ScopeConfirmationStateV1(
        candidate_kind=None,
        candidate_count=0,
        last_evaluated_trading_epoch=trading_epoch - 1,
    )
    inp = ScopeEventGeneratorInputV1(
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=trading_epoch,
        market_context_id="ctx-test",
        market_context_digest="b" * 64,
        current_scope=_scope(),
        current_direction_state=direction,
        reference_price=100.0,
        current_price=current_price,
        trailing_anchor=100.0,
        up_distance=up_distance,
        adverse_exit_distance=adverse_exit_distance,
        reversal_distance=reversal_distance,
        confirmation_epochs=2,
        confirmation_state=conf,
        cooldown_state=ScopeCooldownStateV1(
            active=False,
            remaining_epochs=0,
            policy_version="deterministic_scope_event_generator_policy_v1",
        ),
        cooldown_remaining_epochs=0,
        data_integrity_status=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        bar_finality_status=BarFinalityStatus.FINALIZED,
        policy_version="deterministic_scope_event_generator_policy_v1",
    )
    return generate_deterministic_scope_event(inp, _policy())


def _transition(side: SideState, event: ScopeEvent, now: int = 0):
    return transition_state(
        side_state=side,
        event=event,
        scope_state=RuntimeScopeState(),
        rules=DynamicScopeRules(),
        envelope=RuntimeEnvelope(static=StaticHardLimits(), live_authorization=False),
        now_tick=now,
    )


def test_adverse_plus_valid_downscope_preserves_both_dimensions() -> None:
    # adverse=1, up=2 => nested; price 97 hits both.
    first = _generate(current_price=97.0, trading_epoch=1)
    assert first.event_type is CanonicalScopeEventType.DOWNSCOPE_CANDIDATE
    assert ScopeCandidateKind.ADVERSE_EXIT.value in first.matched_conditions
    signal = derive_scope_adverse_exit_signal_v0(first)
    assert signal.triggered is True
    mapped = _canonical_scope_event_to_scope_event(
        first.event_type,
        matched_conditions=tuple(first.matched_conditions),
    )
    assert mapped is ScopeEvent.DOWNSCOPE_CANDIDATE
    second = _generate(
        current_price=96.5,
        trading_epoch=2,
        confirmation_state=first.next_confirmation_state,
    )
    assert second.event_type is CanonicalScopeEventType.DOWNSCOPE_CONFIRMED
    mapped2 = _canonical_scope_event_to_scope_event(
        second.event_type,
        matched_conditions=tuple(second.matched_conditions),
    )
    assert mapped2 is ScopeEvent.DOWNSCOPE_CONFIRMED
    nxt, _, dec = _transition(SideState.NEUTRAL_OBSERVE, mapped2, now=2)
    assert nxt is SideState.SHORT_ARMED
    assert dec.allowed is True
    assert derive_scope_adverse_exit_signal_v0(second).triggered is True


def test_adverse_without_downscope_context_fail_closed_scope() -> None:
    # price between adverse and downscope: adverse only.
    evidence = _generate(current_price=98.5, up_distance=2.0, adverse_exit_distance=1.0)
    assert evidence.event_type is CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE
    assert ScopeCandidateKind.DOWNSCOPE.value not in evidence.matched_conditions
    assert derive_scope_adverse_exit_signal_v0(evidence).triggered is True
    mapped = _canonical_scope_event_to_scope_event(
        evidence.event_type,
        matched_conditions=tuple(evidence.matched_conditions),
    )
    assert mapped is ScopeEvent.SCOPE_UNKNOWN
    nxt, _, dec = _transition(SideState.LONG_ACTIVE, mapped, now=1)
    assert nxt is SideState.LONG_ACTIVE
    assert dec.allowed is False
    assert dec.reason_code == "SCOPE_UNKNOWN_FAIL_CLOSED"


def test_downscope_without_adverse_unchanged() -> None:
    # adverse farther than up (fixture style): downscope alone at moderate drop.
    evidence = _generate(
        current_price=97.5,
        up_distance=2.0,
        adverse_exit_distance=4.0,
        reversal_distance=5.0,
    )
    assert evidence.event_type is CanonicalScopeEventType.DOWNSCOPE_CANDIDATE
    assert ScopeCandidateKind.ADVERSE_EXIT.value not in evidence.matched_conditions
    assert derive_scope_adverse_exit_signal_v0(evidence).triggered is False


def test_upscope_not_invented_as_downscope() -> None:
    evidence = _generate(current_price=103.0, up_distance=2.0, adverse_exit_distance=1.0)
    assert evidence.event_type is CanonicalScopeEventType.UPSCOPE_CANDIDATE
    mapped = _canonical_scope_event_to_scope_event(
        evidence.event_type,
        matched_conditions=tuple(evidence.matched_conditions),
    )
    assert mapped is ScopeEvent.UPSCOPE_CANDIDATE
    nxt, _, dec = _transition(SideState.NEUTRAL_OBSERVE, mapped, now=0)
    assert nxt is SideState.NEUTRAL_OBSERVE
    assert dec.reason_code == "CANDIDATE_ACK"


def test_bull_upscope_and_bear_downscope_paths() -> None:
    bull = _generate(current_price=103.0)
    assert bull.event_type is CanonicalScopeEventType.UPSCOPE_CANDIDATE
    bear = _generate(current_price=97.0)
    assert bear.event_type is CanonicalScopeEventType.DOWNSCOPE_CANDIDATE
    assert StrategyEntrySideCarrierV1.NONE.value == "NONE"


def test_short_direction_adverse_nested_preserves_downscope() -> None:
    # SHORT: upscope is below, downscope above; adverse nested inside downscope.
    evidence = _generate(
        current_price=103.0,
        direction=ScopeDirectionState.SHORT,
        up_distance=2.0,
        adverse_exit_distance=1.0,
        reversal_distance=1.5,
    )
    assert evidence.event_type is CanonicalScopeEventType.DOWNSCOPE_CANDIDATE
    assert ScopeCandidateKind.ADVERSE_EXIT.value in evidence.matched_conditions
    assert derive_scope_adverse_exit_signal_v0(evidence).triggered is True


def test_mapper_does_not_invent_downscope_without_matched_fact() -> None:
    mapped = _canonical_scope_event_to_scope_event(
        CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE,
        matched_conditions=("adverse_exit",),
    )
    assert mapped is ScopeEvent.SCOPE_UNKNOWN
    mapped2 = _canonical_scope_event_to_scope_event(
        CanonicalScopeEventType.ADVERSE_EXIT_CANDIDATE,
        matched_conditions=("adverse_exit", "downscope"),
    )
    assert mapped2 is ScopeEvent.DOWNSCOPE_CANDIDATE


def test_authority_and_bridge_invariants() -> None:
    assert CANONICAL_BULL_BEAR_STATE_OWNER.endswith("transition_state")
    assert CANONICAL_SWITCH_AUTHORITY.endswith("transition_state")
    assert "double_play_composition_matrix_v1" in CANONICAL_COMPOSITION_AUTHORITY
    assert RUNTIME_BRIDGE_STATUS == "BOUND_NOT_ACTIVATED"
    assert LIVE_AUTHORIZED == "false"
    assert ORDERS_ENABLED == "false"
    assert callable(transition_state)
    gen_src = _GENERATOR.read_text(encoding="utf-8")
    assert "def _select_directional_kind" in gen_src
    assert "ADVERSE_EXIT in matched" in gen_src
    # Directional kinds selected before adverse in source order after DOWNSCOPE/UPSCOPE checks.
    sel = inspect.getsource(
        __import__(
            "trading.master_v2.deterministic_scope_event_generator_v1",
            fromlist=["_select_directional_kind"],
        )._select_directional_kind
    )
    assert sel.index("DOWNSCOPE") < sel.index("ADVERSE_EXIT")
    replay_tree = ast.parse(_REPLAY.read_text(encoding="utf-8"))
    assert isinstance(replay_tree, ast.Module)


def test_pr5338_mark_relative_bps_regression() -> None:
    wiring = _WIRING.read_text(encoding="utf-8")
    assert "up_distance=120.0" not in wiring
    assert "adverse_exit_distance=60.0" not in wiring
    assert "_MV2_RESEARCH_SCOPE_UP_DISTANCE_BPS" in wiring
    low = compute_mv2_research_scope_distances_absolute_from_mark_v1(0.4)
    high = compute_mv2_research_scope_distances_absolute_from_mark_v1(4.0)
    assert high.up_distance / low.up_distance == pytest.approx(10.0)
    with pytest.raises(ValueError, match="mv2_research_scope_distance_mark_"):
        compute_mv2_research_scope_distances_absolute_from_mark_v1(0.0)
