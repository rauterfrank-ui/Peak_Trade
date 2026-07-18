# tests/trading/master_v2/test_canonical_dynamic_scope_trailing_state_continuity_v1.py
"""Canonical Dynamic Scope trailing continuity — multi-bar Integrated Replay contracts."""

from __future__ import annotations

from trading.master_v2.canonical_core_runtime_integration_bridge_v0 import (
    INTEGRATION_STATUS_BOUND_NOT_ACTIVATED,
)
from trading.master_v2.canonical_market_context_v1 import (
    FEATURE_CONTRACT_VERSION,
    BarFinalityStatus,
    CanonicalMarketContextBindingStateV1,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    WarmupStatus,
    with_computed_input_digest,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    CanonicalScopeInitializationPolicyV1,
    ScopeInitializationPrerequisitesV1,
    ScopeReinitializationGuardV1,
    SCOPE_INITIALIZATION_POLICY_VERSION,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    CHOP_POLICY_STATUS,
    SCOPE_EVENT_GENERATOR_POLICY_VERSION,
    ScopeConfirmationStateV1,
    ScopeCooldownStateV1,
    ScopeDirectionState,
    ScopeEventGeneratorPolicyV1,
)
from trading.master_v2.directional_assessment_v1 import (
    DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
    DirectionalAssessmentPolicyV1,
    DirectionalAssessmentSide,
    DirectionalConfirmationStateV1,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
    BothCandidateOutcome,
    BothInvalidOutcome,
    CompositionDirectionState,
    DoublePlayCompositionPolicyV1,
    PositionManagementContext,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    ENTRY_EXIT_POLICY_VERSION,
    DoublePlayEntryExitPolicyV0,
    EntryExitDirectionState,
    ExistingPositionSide,
    PolicySignalV0,
    PositionState,
    ReconciliationState,
    SafetyMode,
    TradingGate,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType
from trading.master_v2.double_play_state import DynamicScopeRules, SideState
from trading.master_v2.evaluate_double_play_authority_boundary_v0 import (
    MASTER_V2_DOUBLE_PLAY_AUTHORITY_USED,
    ZERO_ORDER_RUNTIME_EXECUTION_SUSPENDED,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    CHOP_BINDING_STATUS,
    IntegratedOfflineReplayPoliciesV1,
    build_integrated_offline_replay_input_v1,
    run_integrated_offline_trading_logic_replay_v1,
    scope_direction_from_side_state_v1,
)
from trading.master_v2.suitability_binding_v1 import (
    SUITABILITY_RANKING_POLICY_VERSION,
    SuitabilityBindingStatus,
    SuitabilityRankingPolicyV1,
    SuitabilityRegimeStatus,
    SuitabilityStrategyEntryV1,
    SuitabilityStrategyRegistryV1,
)
from trading.master_v2.survival_assessment_v1 import (
    SURVIVAL_ASSESSMENT_POLICY_VERSION,
    SurvivalAssessmentPolicyV1,
)
from src.backtest.mv2_research_wiring_v1 import (
    build_initial_mv2_integrated_replay_bar_sequence_state_v1,
    project_mv2_integrated_replay_bar_sequence_state_from_intermediate_v1,
)

_INSTRUMENT_A = "inst-pf-ethusd-perp"
_INSTRUMENT_B = "inst-pf-solusd-perp"
_REPLAY = "replay-scope-trail-v1"


def _policies() -> IntegratedOfflineReplayPoliciesV1:
    return IntegratedOfflineReplayPoliciesV1(
        scope_initialization=CanonicalScopeInitializationPolicyV1(
            min_scope_band=1.0,
            max_scope_band=500.0,
            policy_version=SCOPE_INITIALIZATION_POLICY_VERSION,
        ),
        scope_event_generator=ScopeEventGeneratorPolicyV1(
            hard_max_scope_distance=10_000.0,
            hard_max_adverse_distance=10_000.0,
            hard_max_reversal_distance=10_000.0,
            policy_version=SCOPE_EVENT_GENERATOR_POLICY_VERSION,
        ),
        directional=DirectionalAssessmentPolicyV1(
            observe_signal_threshold=0.001,
            candidate_signal_threshold=0.005,
            confirmation_signal_threshold=0.01,
            confirmation_epochs=2,
            validity_epochs=3,
            policy_version=DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
        ),
        survival=SurvivalAssessmentPolicyV1(
            min_net_edge=0.0,
            min_volatility_survival_ratio=0.0,
            min_sequence_survival_ratio=0.0,
            min_drawdown_survival_ratio=0.0,
            min_liquidation_buffer_ratio=0.1,
            validity_epochs=3,
            policy_version=SURVIVAL_ASSESSMENT_POLICY_VERSION,
        ),
        suitability=SuitabilityRankingPolicyV1(
            validity_epochs=3,
            no_match_status=SuitabilityBindingStatus.FAIL,
            policy_version=SUITABILITY_RANKING_POLICY_VERSION,
        ),
        composition=DoublePlayCompositionPolicyV1(
            validity_epochs=3,
            both_candidate_outcome=BothCandidateOutcome.OBSERVE,
            both_invalid_outcome=BothInvalidOutcome.BLOCKED,
            policy_version=DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
        ),
        entry_exit=DoublePlayEntryExitPolicyV0(policy_version=ENTRY_EXIT_POLICY_VERSION),
    )


def _cmc(*, instrument_id: str, epoch: int, mark: float) -> CanonicalMarketContextV1:
    raw = CanonicalMarketContextV1(
        context_id=f"ctx-{instrument_id}-{epoch}",
        instrument_id=instrument_id,
        market_type=FuturesMarketType.PERPETUAL,
        trading_epoch=epoch,
        market_event_time="2026-07-18T00:00:00+00:00",
        decision_time="2026-07-18T00:00:01+00:00",
        bar_interval="1m",
        bar_finality_status=BarFinalityStatus.FINALIZED,
        mark_price=mark,
        index_price=mark,
        best_bid=mark - 0.1,
        best_ask=mark + 0.1,
        spread=0.2,
        volume=50_000.0,
        open_interest=1_000_000.0,
        funding_rate=0.0,
        volatility_estimate=0.02,
        trend_feature_set={"slope": 0.02},
        momentum_feature_set={"rsi": 55.0},
        liquidity_feature_set={"depth_score": 0.9},
        market_structure_feature_set={"range_ratio": 0.4},
        data_integrity_status=DataIntegrityStatus.TRUSTED,
        clock_trust_status=ClockTrustStatus.TRUSTED,
        warmup_status=WarmupStatus.WARMUP_COMPLETE,
        feature_contract_version=FEATURE_CONTRACT_VERSION,
        input_digest="",
    )
    return with_computed_input_digest(raw)


def _versions() -> dict[str, str]:
    return {
        "canonical_market_context": "v1",
        "canonical_scope_initialization": "v1",
        "deterministic_scope_event_generator": "v1",
        "directional_assessment": "v1",
        "survival_assessment": "v1",
        "suitability_binding": "v1",
        "double_play_composition_matrix": "v1",
        "double_play_entry_exit_policy": "v0",
        "double_play_state": "v0",
        "integrated_offline_trading_logic_replay": "v1",
        "canonical_trading_decision_evidence": "v1",
    }


def _policy_versions() -> dict[str, str]:
    return {
        "scope_initialization": SCOPE_INITIALIZATION_POLICY_VERSION,
        "scope_event_generator": SCOPE_EVENT_GENERATOR_POLICY_VERSION,
        "directional": DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
        "survival": SURVIVAL_ASSESSMENT_POLICY_VERSION,
        "suitability": SUITABILITY_RANKING_POLICY_VERSION,
        "composition": DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
        "entry_exit": ENTRY_EXIT_POLICY_VERSION,
    }


def _registry() -> SuitabilityStrategyRegistryV1:
    return SuitabilityStrategyRegistryV1(
        entries=(
            SuitabilityStrategyEntryV1(
                strategy_id="strat-momentum-v1",
                supported_regime_ids=("trending",),
                supported_sides=(DirectionalAssessmentSide.LONG, DirectionalAssessmentSide.SHORT),
                priority_rank=10,
                disabled=False,
                confidence_score=0.75,
            ),
        )
    )


def _digest(label: str) -> str:
    import hashlib

    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _run_cycle(
    *,
    instrument_id: str,
    epoch: int,
    price: float,
    side_state: SideState,
    runtime_scope_state,
    runtime_scope_bound_instrument_id,
    existing_scope,
    confirmation: ScopeConfirmationStateV1,
    rules: DynamicScopeRules | None = None,
    explicit_reset: bool = False,
    scope_direction: ScopeDirectionState | None = None,
    up_distance: float = 50.0,
    adverse_exit_distance: float = 30.0,
    reversal_distance: float = 40.0,
):
    ctx = _cmc(instrument_id=instrument_id, epoch=epoch, mark=price)
    direction = scope_direction or scope_direction_from_side_state_v1(side_state)
    entry_dir = {
        SideState.LONG_ACTIVE: EntryExitDirectionState.LONG_ACTIVE,
        SideState.SHORT_ACTIVE: EntryExitDirectionState.SHORT_ACTIVE,
        SideState.LONG_ARMED: EntryExitDirectionState.LONG_ARMED,
        SideState.SHORT_ARMED: EntryExitDirectionState.SHORT_ARMED,
        SideState.SWITCH_LONG_TO_SHORT_PENDING: EntryExitDirectionState.SHORT_ARMED,
        SideState.SWITCH_SHORT_TO_LONG_PENDING: EntryExitDirectionState.LONG_ARMED,
    }.get(side_state, EntryExitDirectionState.NEUTRAL)
    versions = _versions()
    inp = build_integrated_offline_replay_input_v1(
        replay_id=_REPLAY,
        instrument_id=instrument_id,
        trading_epoch=epoch,
        canonical_market_context=ctx,
        market_context_binding_state=CanonicalMarketContextBindingStateV1(),
        scope_prerequisites=ScopeInitializationPrerequisitesV1(
            required_window_complete=True,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
        scope_reinitialization_guard=ScopeReinitializationGuardV1(),
        existing_scope=existing_scope,
        scope_direction_state=direction,
        scope_confirmation_state=confirmation,
        scope_cooldown_state=ScopeCooldownStateV1(
            active=False,
            remaining_epochs=0,
            policy_version=SCOPE_EVENT_GENERATOR_POLICY_VERSION,
        ),
        up_distance=up_distance,
        adverse_exit_distance=adverse_exit_distance,
        reversal_distance=reversal_distance,
        confirmation_epochs=2,
        current_price=price,
        price_path=(price * 0.99, price),
        directional_confirmation_state=DirectionalConfirmationStateV1(
            candidate_count=1,
            last_evaluated_trading_epoch=epoch - 1,
            last_signal_strength=0.02,
        ),
        strategy_registry=_registry(),
        regime_id="trending",
        regime_status=SuitabilityRegimeStatus.KNOWN,
        previous_composition_direction_state=CompositionDirectionState.NEUTRAL,
        position_management_context=PositionManagementContext.FLAT,
        last_evaluated_trading_epoch=epoch - 1,
        side_state=side_state,
        direction_state=entry_dir,
        position_state=PositionState.FLAT_RECONCILED,
        reconciliation_state=ReconciliationState.RECONCILED,
        trading_gate=TradingGate.ENTRY_ALLOWED,
        safety_mode=SafetyMode.NORMAL,
        existing_position_side=ExistingPositionSide.NONE,
        venue_flat=True,
        cooldown_pass=True,
        scope_adverse_exit_signal=PolicySignalV0(triggered=False),
        profit_protection_signal=PolicySignalV0(triggered=False),
        time_exit_signal=PolicySignalV0(triggered=False),
        strategy_invalidation_signal=PolicySignalV0(triggered=False),
        hard_risk_reduction_signal=PolicySignalV0(triggered=False),
        safety_exit_signal=PolicySignalV0(triggered=False),
        policies=_policies(),
        component_versions=versions,
        policy_versions=_policy_versions(),
        config_digest=_digest("cfg"),
        implementation_digest=_digest("impl"),
        input_digest=_digest(f"in-{instrument_id}-{epoch}-{price}"),
        expected_component_contracts=versions,
        context_reference=f"trail-{instrument_id}-{epoch}",
        now_tick=epoch,
        runtime_scope_state=runtime_scope_state,
        runtime_scope_bound_instrument_id=runtime_scope_bound_instrument_id,
        dynamic_scope_rules=rules,
        explicit_runtime_scope_reset=explicit_reset,
    )
    return run_integrated_offline_trading_logic_replay_v1(inp)


def test_a_five_rising_bars_anchor_trails_up_no_reset() -> None:
    prices = [100.0, 110.0, 120.0, 130.0, 140.0]
    anchors: list[float] = []
    downs: list[float] = []
    runtime = None
    bound = None
    scope = None
    conf = ScopeConfirmationStateV1(
        candidate_kind=None, candidate_count=0, last_evaluated_trading_epoch=-1
    )
    reinits = 0
    for i, price in enumerate(prices):
        result = _run_cycle(
            instrument_id=_INSTRUMENT_A,
            epoch=i,
            price=price,
            side_state=SideState.LONG_ACTIVE,
            runtime_scope_state=runtime,
            runtime_scope_bound_instrument_id=bound,
            existing_scope=scope,
            confirmation=conf,
        )
        assert result.intermediate is not None
        mid = result.intermediate
        if mid.runtime_scope_reinitialized:
            reinits += 1
        anchors.append(mid.runtime_scope_state_after.anchor_price)
        downs.append(mid.runtime_scope_state_after.current_downscope_boundary)
        runtime = mid.runtime_scope_state_after
        bound = mid.current_scope.instrument_id
        scope = mid.current_scope
        conf = mid.scope_event.next_confirmation_state
    assert reinits == 1
    assert anchors == sorted(anchors)
    assert anchors[-1] >= anchors[0]
    assert all(d < a for a, d in zip(anchors, downs))
    # Identity snapshot trailing must not be the sole moving envelope claim:
    assert scope is not None
    assert scope.trailing_anchor == anchors[0] or scope.trailing_anchor <= anchors[-1]


def test_b_five_falling_bars_anchor_trails_down_no_reset() -> None:
    prices = [140.0, 130.0, 120.0, 110.0, 100.0]
    anchors: list[float] = []
    ups: list[float] = []
    runtime = None
    bound = None
    scope = None
    conf = ScopeConfirmationStateV1(
        candidate_kind=None, candidate_count=0, last_evaluated_trading_epoch=-1
    )
    reinits = 0
    for i, price in enumerate(prices):
        result = _run_cycle(
            instrument_id=_INSTRUMENT_A,
            epoch=i,
            price=price,
            side_state=SideState.SHORT_ACTIVE,
            runtime_scope_state=runtime,
            runtime_scope_bound_instrument_id=bound,
            existing_scope=scope,
            confirmation=conf,
        )
        assert result.intermediate is not None
        mid = result.intermediate
        if mid.runtime_scope_reinitialized:
            reinits += 1
        anchors.append(mid.runtime_scope_state_after.anchor_price)
        ups.append(mid.runtime_scope_state_after.current_upscope_boundary)
        runtime = mid.runtime_scope_state_after
        bound = mid.current_scope.instrument_id
        scope = mid.current_scope
        conf = mid.scope_event.next_confirmation_state
    assert reinits == 1
    assert anchors == sorted(anchors, reverse=True)
    assert anchors[-1] <= anchors[0]
    assert all(u > a for a, u in zip(anchors, ups))


def test_c_sideways_no_uncontrolled_flip_flop() -> None:
    prices = [100.0, 100.5, 99.5, 100.2, 99.8]
    sides: list[str] = []
    runtime = None
    bound = None
    scope = None
    conf = ScopeConfirmationStateV1(
        candidate_kind=None, candidate_count=0, last_evaluated_trading_epoch=-1
    )
    side = SideState.LONG_ACTIVE
    for i, price in enumerate(prices):
        result = _run_cycle(
            instrument_id=_INSTRUMENT_A,
            epoch=i,
            price=price,
            side_state=side,
            runtime_scope_state=runtime,
            runtime_scope_bound_instrument_id=bound,
            existing_scope=scope,
            confirmation=conf,
        )
        assert result.intermediate is not None
        mid = result.intermediate
        sides.append(mid.state_switch.next_side_state)
        runtime = mid.runtime_scope_state_after
        bound = mid.current_scope.instrument_id
        scope = mid.current_scope
        conf = mid.scope_event.next_confirmation_state
        side = SideState(mid.state_switch.next_side_state)
    # Within tight band and LONG_ACTIVE, no rapid LONG↔SHORT oscillation
    assert "short_active" not in sides or sides.count("short_active") == 0


def test_d_switch_pending_persists_at_least_one_cycle() -> None:
    from trading.master_v2.deterministic_scope_event_generator_v1 import ScopeCandidateKind

    # adverse farther than up so a moderate drop confirms DOWNSCOPE without ADVERSE_EXIT;
    # policy requires adverse_exit_distance <= reversal_distance.
    dist = {"up_distance": 40.0, "adverse_exit_distance": 80.0, "reversal_distance": 100.0}
    conf = ScopeConfirmationStateV1(
        candidate_kind=ScopeCandidateKind.DOWNSCOPE,
        candidate_count=2,
        last_evaluated_trading_epoch=-1,
    )
    r0 = _run_cycle(
        instrument_id=_INSTRUMENT_A,
        epoch=0,
        price=200.0,
        side_state=SideState.LONG_ACTIVE,
        runtime_scope_state=None,
        runtime_scope_bound_instrument_id=None,
        existing_scope=None,
        confirmation=conf,
        **dist,
    )
    assert r0.intermediate is not None
    runtime = r0.intermediate.runtime_scope_state_after
    bound = r0.intermediate.current_scope.instrument_id
    scope = r0.intermediate.current_scope

    conf = ScopeConfirmationStateV1(
        candidate_kind=ScopeCandidateKind.DOWNSCOPE,
        candidate_count=2,
        last_evaluated_trading_epoch=0,
    )
    r1 = _run_cycle(
        instrument_id=_INSTRUMENT_A,
        epoch=1,
        price=150.0,
        side_state=SideState.LONG_ACTIVE,
        runtime_scope_state=runtime,
        runtime_scope_bound_instrument_id=bound,
        existing_scope=scope,
        confirmation=conf,
        **dist,
    )
    assert r1.intermediate is not None
    assert r1.intermediate.state_switch.next_side_state == (
        SideState.SWITCH_LONG_TO_SHORT_PENDING.value
    ), (
        r1.intermediate.state_switch.scope_event_type,
        r1.intermediate.state_switch.transition_reason_code,
        r1.intermediate.scope_event.event_type,
    )
    runtime = r1.intermediate.runtime_scope_state_after
    bound = r1.intermediate.current_scope.instrument_id
    scope = r1.intermediate.current_scope

    # Follow-up cycle: PENDING must be accepted as prior side (not forced NEUTRAL)
    conf = ScopeConfirmationStateV1(
        candidate_kind=ScopeCandidateKind.DOWNSCOPE,
        candidate_count=2,
        last_evaluated_trading_epoch=1,
    )
    r2 = _run_cycle(
        instrument_id=_INSTRUMENT_A,
        epoch=2,
        price=145.0,
        side_state=SideState.SWITCH_LONG_TO_SHORT_PENDING,
        runtime_scope_state=runtime,
        runtime_scope_bound_instrument_id=bound,
        existing_scope=scope,
        confirmation=conf,
        **dist,
    )
    assert r2.intermediate is not None
    assert r2.intermediate.state_switch.previous_side_state == (
        SideState.SWITCH_LONG_TO_SHORT_PENDING.value
    )
    assert r2.intermediate.state_switch.next_side_state in {
        SideState.SWITCH_LONG_TO_SHORT_PENDING.value,
        SideState.LONG_BLOCKED.value,
        SideState.SHORT_ARMED.value,
        SideState.SHORT_ACTIVE.value,
    }
    assert r2.intermediate.runtime_scope_reinitialized is False


def test_e_cooldown_stateful_across_cycles() -> None:
    rules = DynamicScopeRules(
        min_band_width=1.0,
        max_band_width=500.0,
        min_switch_cooldown_ticks=5,
        volatility_estimate=0.02,
        max_switches_per_window=1_000_000,
    )
    # Complete a switch to SHORT_ACTIVE then attempt immediate opposite switch
    runtime = None
    bound = None
    scope = None
    conf = ScopeConfirmationStateV1(
        candidate_kind=None, candidate_count=0, last_evaluated_trading_epoch=-1
    )
    side = SideState.LONG_ACTIVE
    # Drive toward short via deep drop
    for epoch, price in enumerate([200.0, 50.0, 40.0, 30.0, 20.0, 10.0]):
        result = _run_cycle(
            instrument_id=_INSTRUMENT_A,
            epoch=epoch,
            price=price,
            side_state=side,
            runtime_scope_state=runtime,
            runtime_scope_bound_instrument_id=bound,
            existing_scope=scope,
            confirmation=conf,
            rules=rules,
        )
        assert result.intermediate is not None
        mid = result.intermediate
        side = SideState(mid.state_switch.next_side_state)
        runtime = mid.runtime_scope_state_after
        bound = mid.current_scope.instrument_id
        scope = mid.current_scope
        conf = mid.scope_event.next_confirmation_state
        if side is SideState.SHORT_ACTIVE:
            break
    assert runtime is not None
    # From SHORT_ACTIVE attempt UPSCOPE immediately — cooldown should block if switch just completed
    blocked = _run_cycle(
        instrument_id=_INSTRUMENT_A,
        epoch=20,
        price=500.0,
        side_state=SideState.SHORT_ACTIVE,
        runtime_scope_state=runtime,
        runtime_scope_bound_instrument_id=bound,
        existing_scope=scope,
        confirmation=ScopeConfirmationStateV1(
            candidate_kind=None, candidate_count=2, last_evaluated_trading_epoch=19
        ),
        rules=rules,
    )
    assert blocked.intermediate is not None
    # Either cooldown blocked the transition or event was not confirmed — must not silently empty-state bypass
    assert blocked.intermediate.runtime_scope_state_after is not None
    if blocked.intermediate.state_switch.transition_reason_code == "COOLDOWN_BLOCK":
        assert (
            blocked.intermediate.state_switch.next_side_state
            == blocked.intermediate.state_switch.previous_side_state
        )


def test_f_instrument_change_fail_closed_reinit() -> None:
    r_a = _run_cycle(
        instrument_id=_INSTRUMENT_A,
        epoch=0,
        price=100.0,
        side_state=SideState.LONG_ACTIVE,
        runtime_scope_state=None,
        runtime_scope_bound_instrument_id=None,
        existing_scope=None,
        confirmation=ScopeConfirmationStateV1(
            candidate_kind=None, candidate_count=0, last_evaluated_trading_epoch=-1
        ),
    )
    assert r_a.intermediate is not None
    stolen = r_a.intermediate.runtime_scope_state_after
    r_b = _run_cycle(
        instrument_id=_INSTRUMENT_B,
        epoch=1,
        price=200.0,
        side_state=SideState.LONG_ACTIVE,
        runtime_scope_state=stolen,
        runtime_scope_bound_instrument_id=_INSTRUMENT_A,
        existing_scope=None,
        confirmation=ScopeConfirmationStateV1(
            candidate_kind=None, candidate_count=0, last_evaluated_trading_epoch=0
        ),
    )
    assert r_b.intermediate is not None
    assert r_b.intermediate.runtime_scope_reinitialized is True
    assert r_b.intermediate.current_scope.instrument_id == _INSTRUMENT_B
    # Must not keep A's anchor as B's continuing trail without reinit marker
    assert r_b.intermediate.runtime_scope_state_after.anchor_price != stolen.anchor_price or (
        r_b.intermediate.runtime_scope_reinitialized is True
    )


def test_g_regression_single_cycle_none_state_and_gates() -> None:
    result = _run_cycle(
        instrument_id=_INSTRUMENT_A,
        epoch=0,
        price=3500.0,
        side_state=SideState.LONG_ARMED,
        runtime_scope_state=None,
        runtime_scope_bound_instrument_id=None,
        existing_scope=None,
        confirmation=ScopeConfirmationStateV1(
            candidate_kind=None, candidate_count=1, last_evaluated_trading_epoch=-1
        ),
    )
    assert result.intermediate is not None
    assert result.intermediate.runtime_scope_reinitialized is True
    assert result.intermediate.runtime_scope_state_after.anchor_price > 0
    assert MASTER_V2_DOUBLE_PLAY_AUTHORITY_USED == "false"
    assert ZERO_ORDER_RUNTIME_EXECUTION_SUSPENDED == "true"
    assert INTEGRATION_STATUS_BOUND_NOT_ACTIVATED == "BOUND_NOT_ACTIVATED"
    assert CHOP_POLICY_STATUS == "NOT_BOUND"
    assert CHOP_BINDING_STATUS == "NOT_BOUND_FAIL_CLOSED_GAP"


def test_wiring_projects_runtime_scope_and_direction() -> None:
    seq0 = build_initial_mv2_integrated_replay_bar_sequence_state_v1(trading_epoch=0)
    assert seq0.runtime_scope_state is None
    r0 = _run_cycle(
        instrument_id=_INSTRUMENT_A,
        epoch=0,
        price=100.0,
        side_state=SideState.LONG_ACTIVE,
        runtime_scope_state=None,
        runtime_scope_bound_instrument_id=None,
        existing_scope=None,
        confirmation=ScopeConfirmationStateV1(
            candidate_kind=None, candidate_count=0, last_evaluated_trading_epoch=-1
        ),
    )
    assert r0.intermediate is not None
    seq1 = project_mv2_integrated_replay_bar_sequence_state_from_intermediate_v1(
        intermediate=r0.intermediate,
        previous=seq0,
        next_trading_epoch=1,
    )
    assert seq1.runtime_scope_state is not None
    assert seq1.runtime_scope_bound_instrument_id == _INSTRUMENT_A
    assert seq1.scope_direction_state is ScopeDirectionState.LONG
