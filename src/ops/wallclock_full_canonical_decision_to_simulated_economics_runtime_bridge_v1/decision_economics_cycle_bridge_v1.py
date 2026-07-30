"""Session-stateful wallclock decision→economics cycle bridge.

Sole decision authority: run_integrated_offline_trading_logic_replay_v1.
Analytical portfolio only. No orders / credentials / live activation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Mapping, Optional, Sequence

from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    SimulatedFillV1,
    SimulatedPortfolioEconomicsModelV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.constants_v1 import (
    AUTHORITY_EFFECT_NONE,
    CAPABILITY_ID,
    DECISION_AUTHORITY_OWNER,
    ECONOMIC_VALIDITY_PASS,
    EXECUTION_CLASS_ANALYTICAL,
    FEATURE_WINDOW_MIN,
    LIVE_AUTHORIZED,
    MIN_PRICE_PATH_LEN,
    ORDER_EFFECT_NONE,
    ORDERS_AUTHORIZED,
    OWNER,
    PACKAGE_MARKER,
    PAPER_EXECUTION_AUTHORIZED,
    PRICE_PATH_MAX_LEN,
    PROMOTION_PASS,
    RUNTIME_BRIDGE_LIVE_ACTIVATED,
    RUNTIME_EFFECT_NONE,
    SCHEMA_VERSION,
    TESTNET_AUTHORIZED,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.feature_regime_pipeline_v1 import (
    compute_feature_regime_from_mid_prices_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.intended_action_mapper_v1 import (
    IntendedAnalyticalActionV1,
    map_replay_result_to_intended_analytical_action_v1,
)
from trading.master_v2.canonical_market_context_v1 import (
    CANONICAL_MARKET_CONTEXT_LAYER_VERSION,
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
    CANONICAL_SCOPE_INITIALIZATION_LAYER_VERSION,
    CanonicalScopeInitializationPolicyV1,
    SCOPE_INITIALIZATION_POLICY_VERSION,
    ScopeInitializationPrerequisitesV1,
    ScopeReinitializationGuardV1,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CANONICAL_TRADING_DECISION_EVIDENCE_LAYER_VERSION,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    DETERMINISTIC_SCOPE_EVENT_GENERATOR_LAYER_VERSION,
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
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
    IntegratedOfflineReplayPoliciesV1,
    build_integrated_offline_replay_input_v1,
    run_integrated_offline_trading_logic_replay_v1,
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

_CONFIG_DIGEST = hashlib.sha256(
    b"wallclock-full-canonical-decision-to-simulated-economics-runtime-bridge-v1-config"
).hexdigest()
_IMPL_DIGEST = hashlib.sha256(
    b"wallclock-full-canonical-decision-to-simulated-economics-runtime-bridge-v1-impl"
).hexdigest()


def _default_policies() -> IntegratedOfflineReplayPoliciesV1:
    return IntegratedOfflineReplayPoliciesV1(
        scope_initialization=CanonicalScopeInitializationPolicyV1(
            min_scope_band=50.0,
            max_scope_band=500.0,
            policy_version=SCOPE_INITIALIZATION_POLICY_VERSION,
        ),
        scope_event_generator=ScopeEventGeneratorPolicyV1(
            hard_max_scope_distance=1000.0,
            hard_max_adverse_distance=500.0,
            hard_max_reversal_distance=800.0,
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
            min_net_edge=0.001,
            min_volatility_survival_ratio=0.5,
            min_sequence_survival_ratio=0.5,
            min_drawdown_survival_ratio=0.5,
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


def _component_versions() -> dict[str, str]:
    return {
        "canonical_market_context": CANONICAL_MARKET_CONTEXT_LAYER_VERSION,
        "canonical_scope_initialization": CANONICAL_SCOPE_INITIALIZATION_LAYER_VERSION,
        "deterministic_scope_event_generator": DETERMINISTIC_SCOPE_EVENT_GENERATOR_LAYER_VERSION,
        "directional_assessment": "v1",
        "survival_assessment": "v1",
        "suitability_binding": "v1",
        "double_play_composition_matrix": "v1",
        "double_play_entry_exit_policy": "v0",
        "double_play_state": "v0",
        "integrated_offline_trading_logic_replay": INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
        "canonical_trading_decision_evidence": CANONICAL_TRADING_DECISION_EVIDENCE_LAYER_VERSION,
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


def _strategy_registry() -> SuitabilityStrategyRegistryV1:
    return SuitabilityStrategyRegistryV1(
        entries=(
            SuitabilityStrategyEntryV1(
                strategy_id="strat-momentum-v1",
                supported_regime_ids=("trending", "ranging", "volatile"),
                supported_sides=(DirectionalAssessmentSide.LONG, DirectionalAssessmentSide.SHORT),
                priority_rank=10,
                disabled=False,
                confidence_score=0.75,
            ),
        )
    )


def _iso_now(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


@dataclass
class BridgeSessionStateV1:
    instrument_id: str = PRODUCTION_INSTRUMENT_ID
    trading_epoch: int = 1
    mid_prices: list[float] = field(default_factory=list)
    side_state: SideState = SideState.LONG_ARMED
    direction_state: EntryExitDirectionState = EntryExitDirectionState.LONG_ARMED
    scope_direction_state: ScopeDirectionState = ScopeDirectionState.LONG
    previous_composition_direction_state: CompositionDirectionState = (
        CompositionDirectionState.NEUTRAL
    )
    position_state: PositionState = PositionState.FLAT_RECONCILED
    existing_position_side: ExistingPositionSide = ExistingPositionSide.NONE
    position_management_context: PositionManagementContext = PositionManagementContext.FLAT
    venue_flat: bool = True
    last_evaluated_trading_epoch: int = 0
    cycle_index: int = 0
    portfolio: SimulatedPortfolioEconomicsModelV1 = field(
        default_factory=SimulatedPortfolioEconomicsModelV1
    )
    fill_ledger: list[dict[str, Any]] = field(default_factory=list)
    cycle_ledger: list[dict[str, Any]] = field(default_factory=list)

    def append_mid(self, mid: float) -> None:
        self.mid_prices.append(float(mid))
        if len(self.mid_prices) > PRICE_PATH_MAX_LEN:
            self.mid_prices = self.mid_prices[-PRICE_PATH_MAX_LEN:]


@dataclass
class BridgeCycleResultV1:
    ok: bool
    capability_id: str
    package_marker: str
    schema_version: str
    owner: str
    cycle_index: int
    trading_epoch: int
    instrument_id: str
    decision_authority_owner: str
    feature_regime: dict[str, Any]
    decision_outcome: str
    direction: str
    selected_side: str
    risk_sizing_result: str
    safety_result: str
    intended_action: dict[str, Any]
    fill: Optional[dict[str, Any]]
    portfolio_snapshot: dict[str, Any]
    economic_metrics: dict[str, Any]
    reason_codes: tuple[str, ...]
    blockers: tuple[str, ...]
    call_graph: tuple[str, ...]
    authority_effect: str
    runtime_effect: str
    order_effect: str
    orders_authorized: bool
    testnet_authorized: bool
    live_authorized: bool
    paper_execution_authorized: bool
    economic_validity_pass: bool
    promotion_pass: bool
    runtime_bridge_live_activated: bool
    execution_class: str
    execution_eligible: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "capability_id": self.capability_id,
            "package_marker": self.package_marker,
            "schema_version": self.schema_version,
            "owner": self.owner,
            "cycle_index": self.cycle_index,
            "trading_epoch": self.trading_epoch,
            "instrument_id": self.instrument_id,
            "decision_authority_owner": self.decision_authority_owner,
            "feature_regime": dict(self.feature_regime),
            "decision_outcome": self.decision_outcome,
            "direction": self.direction,
            "selected_side": self.selected_side,
            "risk_sizing_result": self.risk_sizing_result,
            "safety_result": self.safety_result,
            "intended_action": dict(self.intended_action),
            "fill": None if self.fill is None else dict(self.fill),
            "portfolio_snapshot": dict(self.portfolio_snapshot),
            "economic_metrics": dict(self.economic_metrics),
            "reason_codes": list(self.reason_codes),
            "blockers": list(self.blockers),
            "call_graph": list(self.call_graph),
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
            "order_effect": self.order_effect,
            "orders_authorized": self.orders_authorized,
            "testnet_authorized": self.testnet_authorized,
            "live_authorized": self.live_authorized,
            "paper_execution_authorized": self.paper_execution_authorized,
            "economic_validity_pass": self.economic_validity_pass,
            "promotion_pass": self.promotion_pass,
            "runtime_bridge_live_activated": self.runtime_bridge_live_activated,
            "execution_class": self.execution_class,
            "execution_eligible": self.execution_eligible,
            "notes": list(self.notes),
        }


def _fill_to_dict(fill: SimulatedFillV1) -> dict[str, Any]:
    return {
        "instrument_id": fill.instrument_id,
        "side": fill.side,
        "quantity": str(fill.quantity),
        "mark_price": str(fill.mark_price),
        "fill_price": str(fill.fill_price),
        "fee": str(fill.fee),
        "slippage_cost": str(fill.slippage_cost),
        "notional": str(fill.notional),
    }


def _position_fields_from_portfolio(
    portfolio: SimulatedPortfolioEconomicsModelV1, instrument_id: str
) -> tuple[PositionState, ExistingPositionSide, PositionManagementContext, bool]:
    snap = portfolio.snapshot()
    state = snap.get("state") or {}
    positions = state.get("positions") or {}
    pos = positions.get(instrument_id) or {}
    try:
        qty = Decimal(str(pos.get("quantity", "0")))
    except Exception:  # noqa: BLE001
        qty = Decimal("0")
    if qty == 0:
        return (
            PositionState.FLAT_RECONCILED,
            ExistingPositionSide.NONE,
            PositionManagementContext.FLAT,
            True,
        )
    if qty > 0:
        return (
            PositionState.OPEN_FULL,
            ExistingPositionSide.LONG,
            PositionManagementContext.LONG_POSITION,
            False,
        )
    return (
        PositionState.OPEN_FULL,
        ExistingPositionSide.SHORT,
        PositionManagementContext.SHORT_POSITION,
        False,
    )


def _update_session_state_from_replay(
    state: BridgeSessionStateV1,
    *,
    result: Any,
) -> None:
    if result.intermediate is None:
        state.last_evaluated_trading_epoch = state.trading_epoch
        state.trading_epoch += 1
        (
            state.position_state,
            state.existing_position_side,
            state.position_management_context,
            state.venue_flat,
        ) = _position_fields_from_portfolio(state.portfolio, state.instrument_id)
        return
    inter = result.intermediate
    try:
        state.side_state = SideState(inter.state_switch.next_side_state)
    except Exception:  # noqa: BLE001
        pass
    # Map next side into entry/exit direction for the following cycle.
    side_map = {
        SideState.LONG_ARMED: EntryExitDirectionState.LONG_ARMED,
        SideState.LONG_ACTIVE: EntryExitDirectionState.LONG_ACTIVE,
        SideState.SHORT_ARMED: EntryExitDirectionState.SHORT_ARMED,
        SideState.SHORT_ACTIVE: EntryExitDirectionState.SHORT_ACTIVE,
        SideState.NEUTRAL_OBSERVE: EntryExitDirectionState.NEUTRAL,
        SideState.LONG_BLOCKED: EntryExitDirectionState.NEUTRAL,
        SideState.SHORT_BLOCKED: EntryExitDirectionState.NEUTRAL,
        SideState.CHOP_GUARD_BLOCK: EntryExitDirectionState.NEUTRAL,
        SideState.KILL_ALL: EntryExitDirectionState.NEUTRAL,
        SideState.SWITCH_LONG_TO_SHORT_PENDING: EntryExitDirectionState.LONG_ACTIVE,
        SideState.SWITCH_SHORT_TO_LONG_PENDING: EntryExitDirectionState.SHORT_ACTIVE,
    }
    state.direction_state = side_map.get(state.side_state, state.direction_state)
    sel = str(inter.composition_result.selected_side.value).lower()
    if sel == "long":
        state.previous_composition_direction_state = CompositionDirectionState.LONG
        state.scope_direction_state = ScopeDirectionState.LONG
    elif sel == "short":
        state.previous_composition_direction_state = CompositionDirectionState.SHORT
        state.scope_direction_state = ScopeDirectionState.SHORT
    else:
        state.previous_composition_direction_state = CompositionDirectionState.NEUTRAL
    state.last_evaluated_trading_epoch = state.trading_epoch
    state.trading_epoch += 1
    (
        state.position_state,
        state.existing_position_side,
        state.position_management_context,
        state.venue_flat,
    ) = _position_fields_from_portfolio(state.portfolio, state.instrument_id)


CALL_GRAPH_V1: tuple[str, ...] = (
    "okx_public_market_data",
    "feature_pipeline",
    "regime_pipeline",
    "master_v2_double_play_integrated_offline_replay",
    "risk_position_sizing",
    "safety_kernel",
    "intended_side_quantity",
    "analytical_simulated_execution",
    "simulated_fill_fee_slippage",
    "session_persistent_portfolio",
    "realized_unrealized_pnl_equity_drawdown",
    "evidence",
    "full_economic_reconstruction_verifier",
)


def run_bridge_cycle_v1(
    state: BridgeSessionStateV1,
    *,
    mid_price: float,
    event_ts_unix: float,
    session_id: str = "wallclock-bridge-session",
) -> BridgeCycleResultV1:
    """Execute one full analytical decision→economics cycle on a mid tick."""
    if ORDERS_AUTHORIZED or LIVE_AUTHORIZED or TESTNET_AUTHORIZED or PAPER_EXECUTION_AUTHORIZED:
        raise RuntimeError("INVARIANT_VIOLATION_AUTHORITY_FLAGS")

    state.append_mid(mid_price)
    state.cycle_index += 1
    features = compute_feature_regime_from_mid_prices_v1(state.mid_prices)
    price_path = tuple(state.mid_prices[-PRICE_PATH_MAX_LEN:])
    if len(price_path) < MIN_PRICE_PATH_LEN:
        # Seed deterministic second point for contract (warmup still incomplete for features).
        price_path = (float(mid_price), float(mid_price))

    warmup_status = (
        WarmupStatus.WARMUP_COMPLETE if features.warmup_complete else WarmupStatus.WARMUP_REQUIRED
    )
    mark = float(features.mark_price or mid_price)
    input_material = json.dumps(
        {
            "capability_id": CAPABILITY_ID,
            "session_id": session_id,
            "cycle": state.cycle_index,
            "trading_epoch": state.trading_epoch,
            "mid": mark,
            "regime": features.regime_id,
        },
        sort_keys=True,
    )
    input_digest = hashlib.sha256(input_material.encode("utf-8")).hexdigest()

    market_context = with_computed_input_digest(
        CanonicalMarketContextV1(
            context_id=f"ctx-{state.instrument_id}-epoch{state.trading_epoch}-wc-bridge-v1",
            instrument_id=state.instrument_id,
            market_type=FuturesMarketType.PERPETUAL,
            trading_epoch=state.trading_epoch,
            market_event_time=_iso_now(event_ts_unix),
            decision_time=_iso_now(event_ts_unix + 0.001),
            bar_interval="tick",
            bar_finality_status=BarFinalityStatus.FINALIZED,
            mark_price=mark,
            index_price=mark,
            best_bid=mark * 0.9999,
            best_ask=mark * 1.0001,
            spread=mark * 0.0002,
            volume=1_000_000.0,
            open_interest=50_000_000.0,
            funding_rate=0.0001,
            volatility_estimate=float(features.volatility_estimate),
            trend_feature_set=dict(features.trend_features),
            momentum_feature_set=dict(features.momentum_features),
            liquidity_feature_set=dict(features.liquidity_features),
            market_structure_feature_set=dict(features.market_structure_features),
            data_integrity_status=DataIntegrityStatus.TRUSTED,
            clock_trust_status=ClockTrustStatus.TRUSTED,
            warmup_status=warmup_status,
            feature_contract_version=FEATURE_CONTRACT_VERSION,
            input_digest="",
        )
    )

    replay_input = build_integrated_offline_replay_input_v1(
        replay_id=f"{session_id}-cycle-{state.cycle_index}",
        instrument_id=state.instrument_id,
        trading_epoch=state.trading_epoch,
        canonical_market_context=market_context,
        market_context_binding_state=CanonicalMarketContextBindingStateV1(),
        scope_prerequisites=ScopeInitializationPrerequisitesV1(
            required_window_complete=features.warmup_complete,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
        scope_reinitialization_guard=ScopeReinitializationGuardV1(),
        existing_scope=None,
        scope_direction_state=state.scope_direction_state,
        scope_confirmation_state=ScopeConfirmationStateV1(
            candidate_kind=None,
            candidate_count=1 if features.warmup_complete else 0,
            last_evaluated_trading_epoch=state.last_evaluated_trading_epoch,
        ),
        scope_cooldown_state=ScopeCooldownStateV1(
            active=False,
            remaining_epochs=0,
            policy_version=SCOPE_EVENT_GENERATOR_POLICY_VERSION,
        ),
        up_distance=200.0,
        adverse_exit_distance=80.0,
        reversal_distance=120.0,
        confirmation_epochs=2,
        current_price=mark,
        price_path=price_path,
        directional_confirmation_state=DirectionalConfirmationStateV1(
            candidate_count=1 if features.warmup_complete else 0,
            last_evaluated_trading_epoch=state.last_evaluated_trading_epoch,
            last_signal_strength=float(features.momentum_features.get("roc", 0.0)),
        ),
        strategy_registry=_strategy_registry(),
        regime_id=features.regime_id if features.ok else "trending",
        regime_status=(
            SuitabilityRegimeStatus.KNOWN if features.ok else SuitabilityRegimeStatus.UNKNOWN
        ),
        previous_composition_direction_state=state.previous_composition_direction_state,
        position_management_context=state.position_management_context,
        last_evaluated_trading_epoch=state.last_evaluated_trading_epoch,
        side_state=state.side_state,
        direction_state=state.direction_state,
        position_state=state.position_state,
        reconciliation_state=ReconciliationState.RECONCILED,
        trading_gate=TradingGate.ENTRY_ALLOWED,
        safety_mode=SafetyMode.NORMAL,
        existing_position_side=state.existing_position_side,
        venue_flat=state.venue_flat,
        cooldown_pass=True,
        scope_adverse_exit_signal=PolicySignalV0(triggered=False),
        profit_protection_signal=PolicySignalV0(triggered=False),
        time_exit_signal=PolicySignalV0(triggered=False),
        strategy_invalidation_signal=PolicySignalV0(triggered=False),
        hard_risk_reduction_signal=PolicySignalV0(triggered=False),
        safety_exit_signal=PolicySignalV0(triggered=False),
        policies=_default_policies(),
        component_versions=_component_versions(),
        policy_versions=_policy_versions(),
        config_digest=_CONFIG_DIGEST,
        implementation_digest=_IMPL_DIGEST,
        input_digest=input_digest,
        expected_component_contracts=_component_versions(),
        context_reference=f"wallclock-bridge-context-epoch-{state.trading_epoch}",
        now_tick=state.cycle_index,
    )

    replay = run_integrated_offline_trading_logic_replay_v1(replay_input)
    intended = map_replay_result_to_intended_analytical_action_v1(
        replay,
        instrument_id=state.instrument_id,
        portfolio_snapshot=state.portfolio.snapshot(),
    )

    fill_obj = state.portfolio.apply_intended_action(
        instrument_id=state.instrument_id,
        side=intended.intended_side,
        quantity=intended.intended_quantity,
        mark_price=Decimal(str(mark)),
    )
    fill_dict = None if fill_obj is None else _fill_to_dict(fill_obj)
    if fill_dict is not None:
        fill_dict["cycle_index"] = state.cycle_index
        fill_dict["trading_epoch"] = state.trading_epoch
        state.fill_ledger.append(dict(fill_dict))

    _update_session_state_from_replay(state, result=replay)

    sizing_result = str(replay.evidence.risk_sizing_effect or "NONE")
    if replay.intermediate and replay.intermediate.capital_risk_sizing_decision is not None:
        sizing_result = str(replay.intermediate.capital_risk_sizing_decision.outcome.value)

    safety_result = "PASS"
    if any("safety" in str(x).lower() for x in replay.evidence.reason_codes):
        safety_result = "BOUND_SAFETY"
    if intended.safety_blocked:
        safety_result = "BLOCKED_HOLD"

    blockers: list[str] = []
    if not features.warmup_complete:
        blockers.append("FEATURE_WARMUP_INCOMPLETE")
    if not replay.replay_pass and features.warmup_complete:
        blockers.extend(str(x) for x in replay.fail_reasons)

    cycle = BridgeCycleResultV1(
        ok=True,  # analytical cycle completed; warmup/observe is still ok for bridge
        capability_id=CAPABILITY_ID,
        package_marker=PACKAGE_MARKER,
        schema_version=SCHEMA_VERSION,
        owner=OWNER,
        cycle_index=state.cycle_index,
        trading_epoch=state.trading_epoch - 1,  # epoch used for this cycle
        instrument_id=state.instrument_id,
        decision_authority_owner=DECISION_AUTHORITY_OWNER,
        feature_regime=features.to_dict(),
        decision_outcome=str(replay.evidence.decision_outcome),
        direction=str(
            replay.evidence.next_direction_state or replay.evidence.previous_direction_state
        ),
        selected_side=str(replay.evidence.selected_side),
        risk_sizing_result=sizing_result,
        safety_result=safety_result,
        intended_action=intended.to_dict(),
        fill=fill_dict,
        portfolio_snapshot=dict(state.portfolio.snapshot()),
        economic_metrics=state.portfolio.economic_metrics().to_dict(),
        reason_codes=tuple(replay.evidence.reason_codes),
        blockers=tuple(blockers),
        call_graph=CALL_GRAPH_V1,
        authority_effect=AUTHORITY_EFFECT_NONE,
        runtime_effect=RUNTIME_EFFECT_NONE,
        order_effect=ORDER_EFFECT_NONE,
        orders_authorized=ORDERS_AUTHORIZED,
        testnet_authorized=TESTNET_AUTHORIZED,
        live_authorized=LIVE_AUTHORIZED,
        paper_execution_authorized=PAPER_EXECUTION_AUTHORIZED,
        economic_validity_pass=ECONOMIC_VALIDITY_PASS,
        promotion_pass=PROMOTION_PASS,
        runtime_bridge_live_activated=RUNTIME_BRIDGE_LIVE_ACTIVATED,
        execution_class=EXECUTION_CLASS_ANALYTICAL,
        execution_eligible=bool(replay.evidence.execution_eligible),
        notes=(
            "ANALYTICAL_SIMULATION_ONLY",
            "NO_ORDERS",
            "NO_BROKER_WRITES",
            "SOLE_DECISION_AUTHORITY_INTEGRATED_OFFLINE_REPLAY",
            f"FEATURE_WINDOW_MIN={FEATURE_WINDOW_MIN}",
        ),
    )
    if cycle.execution_eligible:
        # Hard fail-closed: bridge must never claim broker execution eligibility.
        raise RuntimeError("EXECUTION_ELIGIBLE_MUST_REMAIN_FALSE")

    state.cycle_ledger.append(cycle.to_dict())
    return cycle


def run_bridge_cycles_from_mids_v1(
    mid_prices: Sequence[float],
    *,
    start_ts_unix: float = 1_700_000_000.0,
    session_id: str = "wallclock-bridge-probe",
    instrument_id: str = PRODUCTION_INSTRUMENT_ID,
) -> tuple[BridgeSessionStateV1, list[BridgeCycleResultV1]]:
    state = BridgeSessionStateV1(instrument_id=instrument_id)
    results: list[BridgeCycleResultV1] = []
    for i, mid in enumerate(mid_prices):
        results.append(
            run_bridge_cycle_v1(
                state,
                mid_price=float(mid),
                event_ts_unix=start_ts_unix + float(i),
                session_id=session_id,
            )
        )
    return state, results
