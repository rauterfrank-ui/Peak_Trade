"""Session-stateful wallclock decision→economics cycle bridge.

Sole decision authority: run_integrated_offline_trading_logic_replay_v1.
Analytical portfolio only. No orders / credentials / live activation.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    SimulatedFillV1,
    SimulatedPortfolioEconomicsModelV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.bridge_binding_v1 import (
    apply_intended_action_via_canonical_accounting_v1,
    ensure_accounting_session_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.constants_v1 import (
    CALL_GRAPH_RISK_STEP as ACCOUNTING_RISK_STEP,
    CALL_GRAPH_STEP as ACCOUNTING_CALL_GRAPH_STEP,
    FUTURES_ACCOUNTING_RUNTIME_BOUND,
    SINGLE_WRITER_IDENTITY as ACCOUNTING_SINGLE_WRITER_IDENTITY,
)
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    CALL_GRAPH_STEP as RECON_CALL_GRAPH_STEP,
    SINGLE_WRITER_IDENTITY,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
    ProductiveReconciliationEvidenceV1,
    ProductiveReconciliationGateResultV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.startup_gate_v1 import (
    run_productive_reconciliation_startup_gate_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.taxonomy_v1 import (
    ProductiveReconciliationClass,
)
from src.ops.single_selected_future_runtime_binding_v1.binding_gate_v1 import (
    run_single_selected_future_runtime_binding_gate_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    CALL_GRAPH_BINDING_PREFIX as SELECTION_BINDING_PREFIX,
    CALL_GRAPH_STEP as SELECTION_BINDING_STEP,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import (
    RuntimeBindingGateResultV1,
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
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.constants_v1 import (
    CALL_GRAPH_C1_RESULT_STEP,
    CALL_GRAPH_C1_STEP,
    CALL_GRAPH_C2_STEP,
    CALL_GRAPH_C3_STEP,
    CALL_GRAPH_COMMIT_STEP,
    DEFAULT_VENUE as CONFIRMATION_DEFAULT_VENUE,
)
from src.ops.stateful_confirmation_and_c1_productive_binding_v1.host_binding_v1 import (
    HostConfirmationBindingV1,
    ObservationCycleKindV1,
    commit_host_confirmation_after_replay_v1,
    confirmation_config_digest_v1,
    ensure_host_confirmation_binding_v1,
    evaluate_host_observation_acceptance_v1,
)
from src.ops.dynamic_scope_persistence_binding_v1.constants_v1 import (
    CALL_GRAPH_PREVIOUS_SCOPE_STEP,
    CALL_GRAPH_SCOPE_COMMIT_STEP,
    CALL_GRAPH_SCOPE_TRANSITION_STEP,
    DEFAULT_VENUE as DYNAMIC_SCOPE_DEFAULT_VENUE,
    FROZEN_ADVERSE_EXIT_DISTANCE,
    FROZEN_REVERSAL_DISTANCE,
    FROZEN_UP_DISTANCE,
)
from src.ops.dynamic_scope_persistence_binding_v1.host_binding_v1 import (
    HostDynamicScopeBindingV1,
    commit_host_dynamic_scope_after_replay_v1,
    dynamic_scope_config_digest_v1,
    ensure_host_dynamic_scope_binding_v1,
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
    # Capability 1.1 — productive reconciliation startup gate (no implicit RECONCILED).
    reconciliation_gate_completed: bool = False
    reconciliation_alpha_enabled: bool = False
    reconciliation_state: ReconciliationState = ReconciliationState.RECONCILIATION_REQUIRED
    reconciliation_evidence: Optional[dict[str, Any]] = None
    reconciliation_state_root: Optional[str] = None
    portfolio_single_writer_identity: str = SINGLE_WRITER_IDENTITY
    # Capability 2.4 — single selected future runtime binding (sole productive instrument authority).
    selection_binding_completed: bool = False
    selection_alpha_enabled: bool = False
    selection_binding_evidence: Optional[dict[str, Any]] = None
    selection_state_root: Optional[str] = None
    ranking_state_root: Optional[str] = None
    universe_state_root: Optional[str] = None
    venue_native_id: str = ""
    require_selection_binding: bool = True
    mark_price_by_native_id: dict[str, Any] = field(default_factory=dict)
    # Capability 3.1 — canonical futures accounting after fill, before portfolio/risk persist.
    futures_accounting_bound: bool = FUTURES_ACCOUNTING_RUNTIME_BOUND
    accounting_session: Optional[ProductiveFuturesAccountingSessionV1] = None
    accounting_state_root: Optional[str] = None
    accounting_single_writer_identity: str = ACCOUNTING_SINGLE_WRITER_IDENTITY
    last_accounting_result: Optional[dict[str, Any]] = None
    # Capability 6.1 — stateful C1/C2/C3 confirmation binding (caller-owned durable cursor).
    confirmation_binding: HostConfirmationBindingV1 = field(
        default_factory=HostConfirmationBindingV1
    )
    confirmation_state_root: Optional[str] = None
    last_confirmation_commit: Optional[dict[str, Any]] = None
    # Capability 6.2 — Dynamic Scope persistence binding (caller-owned durable RuntimeScopeState).
    dynamic_scope_binding: HostDynamicScopeBindingV1 = field(
        default_factory=HostDynamicScopeBindingV1
    )
    dynamic_scope_state_root: Optional[str] = None
    last_dynamic_scope_commit: Optional[dict[str, Any]] = None

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
    *SELECTION_BINDING_PREFIX,
    SELECTION_BINDING_STEP,
    RECON_CALL_GRAPH_STEP,
    "okx_public_market_data",
    CALL_GRAPH_C1_STEP,
    CALL_GRAPH_C1_RESULT_STEP,
    "feature_pipeline",
    "regime_pipeline",
    CALL_GRAPH_C2_STEP,
    CALL_GRAPH_C3_STEP,
    CALL_GRAPH_PREVIOUS_SCOPE_STEP,
    "master_v2_double_play_integrated_offline_replay",
    CALL_GRAPH_SCOPE_TRANSITION_STEP,
    CALL_GRAPH_COMMIT_STEP,
    CALL_GRAPH_SCOPE_COMMIT_STEP,
    "risk_position_sizing",
    "safety_kernel",
    "intended_side_quantity",
    "analytical_simulated_execution",
    "simulated_fill_fee_slippage",
    ACCOUNTING_CALL_GRAPH_STEP,
    "session_persistent_portfolio",
    "realized_unrealized_pnl_equity_drawdown",
    ACCOUNTING_RISK_STEP,
    "simulated_economics_no_order_path",
    "evidence",
    "full_economic_reconstruction_verifier",
)


def _observed_portfolio_truth_from_bridge_state(
    state: BridgeSessionStateV1,
    *,
    event_ts_unix: float,
) -> PortfolioTruthSnapshotV1:
    """Read canonical analytical execution/position state for reconciliation."""
    snap = state.portfolio.snapshot()
    positions_raw = (snap.get("state") or {}).get("positions") or {}
    positions: list[PositionTruthV1] = []
    for instrument_id, pos in sorted(positions_raw.items()):
        positions.append(
            PositionTruthV1.from_signed(
                instrument_id=str(instrument_id),
                signed_quantity=pos.get("quantity", "0"),
                source_id="analytical_execution_state",
                mark_price=None,
                event_time_unix=event_ts_unix,
                wall_time_unix=event_ts_unix,
            )
        )
    cash = (snap.get("state") or {}).get("cash")
    return PortfolioTruthSnapshotV1(
        positions=tuple(positions),
        cash=None if cash is None else Decimal(str(cash)),
        source_id="analytical_execution_state",
        event_time_unix=event_ts_unix,
        wall_time_unix=event_ts_unix,
    )


def ensure_single_selected_future_runtime_binding_v1(
    state: BridgeSessionStateV1,
    *,
    session_id: str,
    event_ts_unix: float,
    repository_sha: str,
    observed: Optional[PortfolioTruthSnapshotV1] = None,
    direct_instrument_override: str | None = None,
) -> RuntimeBindingGateResultV1:
    """Capability 2.4: bind Cap 2.3 selection before reconciliation/alpha."""
    if state.selection_binding_completed:
        if not state.selection_alpha_enabled and state.require_selection_binding:
            raise RuntimeError("SELECTION_BINDING_ALPHA_BLOCKED")
        ev = state.selection_binding_evidence or {}
        bound = None
        if state.instrument_id:
            from src.ops.single_selected_future_runtime_binding_v1.models_v1 import (
                BoundInstrumentV1,
            )

            bound = BoundInstrumentV1(
                instrument_id=state.instrument_id,
                venue_native_id=state.venue_native_id,
                ranking_snapshot_id=str(ev.get("ranking_snapshot_id") or ""),
                ranking_integrity_digest=str(ev.get("ranking_integrity_digest") or ""),
                universe_snapshot_id=str(ev.get("universe_snapshot_id") or ""),
                selection_id=str(ev.get("selection_id") or ""),
                selection_integrity_digest=str(ev.get("selection_integrity_digest") or ""),
                selection_state=str(ev.get("selection_state") or ""),
            )
        from src.ops.single_selected_future_runtime_binding_v1.models_v1 import (
            RuntimeBindingEvidenceV1,
        )

        return RuntimeBindingGateResultV1(
            ok=True,
            alpha_enabled=bool(state.selection_alpha_enabled),
            new_alpha_allowed=bool(state.selection_alpha_enabled),
            exit_risk_safety_preserved=True,
            hard_stop=False,
            selection_state=str(ev.get("selection_state") or ""),
            bound=bound,
            evidence=RuntimeBindingEvidenceV1(
                capability_id="CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1",
                schema_version="single_selected_future_runtime_binding.v1",
                producer_version="single_selected_future_runtime_binding.v1",
                owner="ops.single_selected_future_runtime_binding_v1",
                ok=True,
                alpha_enabled=bool(state.selection_alpha_enabled),
                new_alpha_allowed=bool(state.selection_alpha_enabled),
                exit_risk_safety_preserved=True,
                hard_stop=False,
                selection_state=str(ev.get("selection_state") or ""),
                instrument_id=state.instrument_id,
                venue_native_id=state.venue_native_id,
                selection_id=str(ev.get("selection_id") or ""),
                selection_integrity_digest=str(ev.get("selection_integrity_digest") or ""),
                ranking_snapshot_id=str(ev.get("ranking_snapshot_id") or ""),
                ranking_integrity_digest=str(ev.get("ranking_integrity_digest") or ""),
                universe_snapshot_id=str(ev.get("universe_snapshot_id") or ""),
                repository_sha=repository_sha,
                config_digest=str(ev.get("config_digest") or ""),
                reconciliation_before_alpha=True,
                reconciliation_alpha_enabled=bool(state.reconciliation_alpha_enabled),
                reason_codes=("CACHED_SESSION_SELECTION_BINDING",),
                failure_codes=(),
                call_graph=SELECTION_BINDING_PREFIX,
            ),
            blockers=(),
        )

    if not state.require_selection_binding:
        # Explicit non-productive research escape hatch — not selection authority.
        state.selection_binding_completed = True
        state.selection_alpha_enabled = True
        state.selection_binding_evidence = {
            "selection_state": "LEGACY_RESEARCH_UNBOUND",
            "notes": ["REQUIRE_SELECTION_BINDING_FALSE_NON_PRODUCTIVE"],
        }
        from src.ops.single_selected_future_runtime_binding_v1.models_v1 import (
            RuntimeBindingEvidenceV1,
        )

        return RuntimeBindingGateResultV1(
            ok=True,
            alpha_enabled=True,
            new_alpha_allowed=True,
            exit_risk_safety_preserved=True,
            hard_stop=False,
            selection_state="LEGACY_RESEARCH_UNBOUND",
            bound=None,
            evidence=RuntimeBindingEvidenceV1(
                capability_id="CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1",
                schema_version="single_selected_future_runtime_binding.v1",
                producer_version="single_selected_future_runtime_binding.v1",
                owner="ops.single_selected_future_runtime_binding_v1",
                ok=True,
                alpha_enabled=True,
                new_alpha_allowed=True,
                exit_risk_safety_preserved=True,
                hard_stop=False,
                selection_state="LEGACY_RESEARCH_UNBOUND",
                instrument_id=state.instrument_id,
                venue_native_id=state.venue_native_id,
                selection_id="",
                selection_integrity_digest="",
                ranking_snapshot_id="",
                ranking_integrity_digest="",
                universe_snapshot_id="",
                repository_sha=repository_sha,
                config_digest="",
                reconciliation_before_alpha=False,
                reconciliation_alpha_enabled=False,
                reason_codes=("LEGACY_RESEARCH_UNBOUND",),
                failure_codes=(),
                call_graph=SELECTION_BINDING_PREFIX,
                notes=("NON_PRODUCTIVE_ESCAPE_HATCH",),
            ),
            blockers=(),
        )

    if direct_instrument_override:
        raise RuntimeError("DIRECT_INSTRUMENT_OVERRIDE_REJECTED")
    if (
        not state.selection_state_root
        or not state.ranking_state_root
        or not state.universe_state_root
    ):
        raise RuntimeError("SELECTION_BINDING_ROOTS_REQUIRED")
    if state.reconciliation_state_root is None:
        state.reconciliation_state_root = str(
            Path(tempfile.mkdtemp(prefix="peak_trade_recon_bridge_"))
        )

    observed_snap = observed or _observed_portfolio_truth_from_bridge_state(
        state, event_ts_unix=event_ts_unix
    )
    gate = run_single_selected_future_runtime_binding_gate_v1(
        selection_state_root=Path(state.selection_state_root),
        ranking_state_root=Path(state.ranking_state_root),
        universe_state_root=Path(state.universe_state_root),
        repository_sha=repository_sha,
        session_id=session_id,
        now_unix=event_ts_unix,
        reconciliation_state_root=Path(state.reconciliation_state_root),
        observed_portfolio=observed_snap,
        mark_price_by_native_id=state.mark_price_by_native_id,
        direct_instrument_override=direct_instrument_override,
        allow_research_direct_instrument=False,
    )
    state.selection_binding_completed = True
    state.selection_alpha_enabled = bool(gate.alpha_enabled)
    state.selection_binding_evidence = gate.evidence.to_dict()
    if gate.bound is not None:
        # Cap 2.4: venue-native id is the runtime market-data binding key.
        state.instrument_id = gate.bound.venue_native_id
        state.venue_native_id = gate.bound.venue_native_id
    # Cap 2.4 gate already executed Cap 1.1 reconciliation before alpha.
    if gate.reconciliation_result is not None:
        state.reconciliation_gate_completed = True
        state.reconciliation_alpha_enabled = bool(gate.reconciliation_result.get("alpha_enabled"))
        state.reconciliation_evidence = dict(gate.reconciliation_result)
        try:
            state.reconciliation_state = ReconciliationState(
                str(
                    gate.reconciliation_result.get("master_v2_reconciliation_state")
                    or ReconciliationState.RECONCILIATION_REQUIRED.value
                )
            )
        except Exception:  # noqa: BLE001
            state.reconciliation_state = ReconciliationState.RECONCILIATION_REQUIRED
    return gate


def ensure_productive_reconciliation_startup_gate_v1(
    state: BridgeSessionStateV1,
    *,
    session_id: str,
    event_ts_unix: float,
    repository_sha: str,
    state_root: Optional[Path] = None,
    observed: Optional[PortfolioTruthSnapshotV1] = None,
) -> ProductiveReconciliationGateResultV1:
    """Mandatory pre-alpha reconciliation; idempotent per session state."""
    if state.reconciliation_gate_completed:
        if not state.reconciliation_alpha_enabled:
            raise RuntimeError("RECONCILIATION_ALPHA_BLOCKED")
        ev = state.reconciliation_evidence or {}
        return ProductiveReconciliationGateResultV1(
            ok=True,
            alpha_enabled=True,
            classification=ProductiveReconciliationClass.MATCH,
            master_v2_reconciliation_state=state.reconciliation_state.value,
            hard_stop=False,
            evidence=ProductiveReconciliationEvidenceV1(
                capability_id="CAPABILITY_1_1_PRODUCTIVE_RECONCILIATION_RUNTIME_BINDING_V1",
                schema_version="productive_reconciliation_runtime_binding.v1",
                owner="ops.productive_reconciliation_runtime_binding_v1",
                classification=str(ev.get("classification") or "MATCH"),
                alpha_enabled=True,
                pre_state_digest=str(ev.get("pre_state_digest") or ""),
                observed_state_digest=str(ev.get("observed_state_digest") or ""),
                post_state_digest=str(ev.get("post_state_digest") or ""),
                reconciliation_decision="CACHED_SESSION_GATE",
                repository_sha=repository_sha,
                single_writer_identity=state.portfolio_single_writer_identity,
            ),
            blockers=(),
        )

    root = Path(state_root) if state_root is not None else None
    if root is None and state.reconciliation_state_root:
        root = Path(state.reconciliation_state_root)
    if root is None:
        root = Path(tempfile.mkdtemp(prefix="peak_trade_recon_bridge_"))
    state.reconciliation_state_root = str(root)

    observed_snap = observed or _observed_portfolio_truth_from_bridge_state(
        state, event_ts_unix=event_ts_unix
    )
    gate = run_productive_reconciliation_startup_gate_v1(
        state_root=root,
        observed=observed_snap,
        session_id=session_id,
        repository_sha=repository_sha,
        now_unix=event_ts_unix,
        writer_identity=state.portfolio_single_writer_identity,
    )
    state.reconciliation_gate_completed = True
    state.reconciliation_alpha_enabled = bool(gate.alpha_enabled)
    state.reconciliation_evidence = gate.evidence.to_dict()
    try:
        state.reconciliation_state = ReconciliationState(gate.master_v2_reconciliation_state)
    except Exception:  # noqa: BLE001
        state.reconciliation_state = ReconciliationState.RECONCILIATION_REQUIRED
    return gate


def run_bridge_cycle_v1(
    state: BridgeSessionStateV1,
    *,
    mid_price: float,
    event_ts_unix: float,
    session_id: str = "wallclock-bridge-session",
    repository_sha: str = "OFFLINE_DETERMINISTIC_EVIDENCE",
    reconciliation_state_root: Optional[Path] = None,
    direct_instrument_override: str | None = None,
    observation_cycle_kind: ObservationCycleKindV1 | str = ObservationCycleKindV1.MARKET_SAMPLE,
    force_observation_event_time: float | None = None,
    confirmation_state_root: Optional[Path] = None,
    persist_confirmation: bool = True,
    dynamic_scope_state_root: Optional[Path] = None,
    persist_dynamic_scope: bool = True,
) -> BridgeCycleResultV1:
    """Execute one full analytical decision→economics cycle on a mid tick."""
    if ORDERS_AUTHORIZED or LIVE_AUTHORIZED or TESTNET_AUTHORIZED or PAPER_EXECUTION_AUTHORIZED:
        raise RuntimeError("INVARIANT_VIOLATION_AUTHORITY_FLAGS")

    if reconciliation_state_root is not None:
        state.reconciliation_state_root = str(reconciliation_state_root)
    if confirmation_state_root is not None:
        state.confirmation_state_root = str(confirmation_state_root)
    if dynamic_scope_state_root is not None:
        state.dynamic_scope_state_root = str(dynamic_scope_state_root)

    # Capability 2.4: persisted selection binds the trading instrument before recon/alpha.
    selection_gate = ensure_single_selected_future_runtime_binding_v1(
        state,
        session_id=session_id,
        event_ts_unix=event_ts_unix,
        repository_sha=repository_sha,
        direct_instrument_override=direct_instrument_override,
    )
    if state.require_selection_binding and not selection_gate.alpha_enabled:
        raise RuntimeError(
            "SELECTION_BINDING_ALPHA_BLOCKED:"
            + ",".join(selection_gate.blockers or (selection_gate.selection_state,))
        )

    # Capability 1.1: reconciliation is a mandatory startup gate before alpha.
    # When Cap 2.4 already ran reconciliation, this call is idempotent/cached.
    gate = ensure_productive_reconciliation_startup_gate_v1(
        state,
        session_id=session_id,
        event_ts_unix=event_ts_unix,
        repository_sha=repository_sha,
        state_root=reconciliation_state_root,
    )
    if not gate.alpha_enabled:
        raise RuntimeError(
            "RECONCILIATION_ALPHA_BLOCKED:"
            + ",".join(gate.blockers or (gate.classification.value,))
        )
    if state.reconciliation_state is not ReconciliationState.RECONCILED:
        raise RuntimeError("RECONCILIATION_STATE_NOT_RECONCILED")

    # Capability 6.1: bind C1 acceptor + stable confirmation session before features/decision.
    kind = (
        observation_cycle_kind
        if isinstance(observation_cycle_kind, ObservationCycleKindV1)
        else ObservationCycleKindV1(str(observation_cycle_kind))
    )
    ensure_host_confirmation_binding_v1(
        state.confirmation_binding,
        instrument_id=state.instrument_id,
        venue=CONFIRMATION_DEFAULT_VENUE,
        venue_instrument_id=state.venue_native_id or state.instrument_id,
        repository_sha=repository_sha,
        config_digest=confirmation_config_digest_v1(),
        state_root=(Path(state.confirmation_state_root) if state.confirmation_state_root else None),
    )
    # Capability 6.2: reload prior RuntimeScopeState / CanonicalScopeSnapshot before decision.
    ensure_host_dynamic_scope_binding_v1(
        state.dynamic_scope_binding,
        instrument_id=state.instrument_id,
        venue=DYNAMIC_SCOPE_DEFAULT_VENUE,
        repository_sha=repository_sha,
        config_digest=dynamic_scope_config_digest_v1(),
        state_root=(
            Path(state.dynamic_scope_state_root) if state.dynamic_scope_state_root else None
        ),
    )
    if state.dynamic_scope_binding.alpha_blocked:
        raise RuntimeError(
            "DYNAMIC_SCOPE_ALPHA_BLOCKED:" + state.dynamic_scope_binding.alpha_block_reason
        )
    # Restart restore of host cursors required for scope continuity (no silent re-seed).
    if (
        state.dynamic_scope_binding.prior_commit_seen
        and state.dynamic_scope_binding.runtime_scope_state is not None
        and state.cycle_index == 0
    ):
        state.cycle_index = int(state.dynamic_scope_binding.runtime_scope_state.now_tick)
        state.trading_epoch = int(state.dynamic_scope_binding.host_trading_epoch)
        try:
            state.side_state = SideState(state.dynamic_scope_binding.side_state)
        except Exception:  # noqa: BLE001
            pass
        try:
            state.scope_direction_state = ScopeDirectionState(
                state.dynamic_scope_binding.scope_direction_state
            )
        except Exception:  # noqa: BLE001
            pass
        if state.dynamic_scope_binding.price_path_tail and not state.mid_prices:
            state.mid_prices = [float(x) for x in state.dynamic_scope_binding.price_path_tail]
    # Only market samples (incl. duplicate/out-of-order classifications) append price path.
    if (
        kind is ObservationCycleKindV1.MARKET_SAMPLE
        or kind is ObservationCycleKindV1.DUPLICATE_SAMPLE
    ):
        state.append_mid(mid_price)
    elif kind is ObservationCycleKindV1.OUT_OF_ORDER:
        state.append_mid(mid_price)
    state.cycle_index += 1
    observation_acceptance_result = evaluate_host_observation_acceptance_v1(
        state.confirmation_binding,
        mid_price=float(mid_price),
        event_ts_unix=float(event_ts_unix),
        cycle_index=int(state.cycle_index),
        kind=kind,
        force_event_time=force_observation_event_time,
    )
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
        # Capability 6.2 — previous canonical scope + RuntimeScopeState (no silent None reset).
        existing_scope=state.dynamic_scope_binding.existing_scope,
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
        up_distance=float(FROZEN_UP_DISTANCE),
        adverse_exit_distance=float(FROZEN_ADVERSE_EXIT_DISTANCE),
        reversal_distance=float(FROZEN_REVERSAL_DISTANCE),
        confirmation_epochs=2,
        current_price=mark,
        price_path=price_path,
        directional_confirmation_state=DirectionalConfirmationStateV1(
            candidate_count=1 if features.warmup_complete else 0,
            last_evaluated_trading_epoch=state.last_evaluated_trading_epoch,
            last_signal_strength=float(features.momentum_features.get("roc", 0.0)),
        ),
        strategy_registry=_strategy_registry(),
        regime_id=features.regime_id if features.ok else "unclassified",
        regime_status=(
            SuitabilityRegimeStatus.KNOWN if features.ok else SuitabilityRegimeStatus.UNKNOWN
        ),
        previous_composition_direction_state=state.previous_composition_direction_state,
        position_management_context=state.position_management_context,
        last_evaluated_trading_epoch=state.last_evaluated_trading_epoch,
        side_state=state.side_state,
        direction_state=state.direction_state,
        position_state=state.position_state,
        reconciliation_state=state.reconciliation_state,
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
        # Capability 6.1 — real C1 result + caller-owned C3 carrier (no non-advancing placeholder).
        directional_confirmation_progress=state.confirmation_binding.confirmation_side_carrier,
        observation_acceptance_result=observation_acceptance_result,
        confirmation_progress_session_id=state.confirmation_binding.confirmation_session_id,
        confirmation_progress_venue=state.confirmation_binding.venue,
        confirmation_progress_instrument=state.confirmation_binding.instrument_key(),
        # Capability 6.2 — bind previous RuntimeScopeState into the next transition.
        runtime_scope_state=state.dynamic_scope_binding.runtime_scope_state,
        runtime_scope_bound_instrument_id=(
            (state.dynamic_scope_binding.runtime_scope_bound_instrument_id or state.instrument_id)
            if state.dynamic_scope_binding.runtime_scope_state is not None
            else None
        ),
        explicit_runtime_scope_reset=False,
    )

    replay = run_integrated_offline_trading_logic_replay_v1(replay_input)
    intended = map_replay_result_to_intended_analytical_action_v1(
        replay,
        instrument_id=state.instrument_id,
        portfolio_snapshot=state.portfolio.snapshot(),
    )

    # Capability 3.1: simulated fill → canonical futures_accounting → portfolio/risk.
    if state.accounting_session is None:
        state.accounting_session = ensure_accounting_session_v1(
            instrument_id=state.instrument_id,
            state_root=(Path(state.accounting_state_root) if state.accounting_state_root else None),
        )
    accounting_apply = apply_intended_action_via_canonical_accounting_v1(
        session=state.accounting_session,
        portfolio=state.portfolio,
        instrument_id=state.instrument_id,
        side=intended.intended_side,
        quantity=intended.intended_quantity,
        mark_price=Decimal(str(mark)),
        session_id=session_id,
        cycle_index=state.cycle_index,
        reduce_only=False,
        state_root=Path(state.accounting_state_root) if state.accounting_state_root else None,
        persist=bool(state.accounting_state_root),
        writer_session_id=session_id,
    )
    state.last_accounting_result = dict(accounting_apply.get("accounting") or {})
    fill_dict = accounting_apply.get("fill")
    if fill_dict is not None:
        fill_dict = dict(fill_dict)
        fill_dict["cycle_index"] = state.cycle_index
        fill_dict["trading_epoch"] = state.trading_epoch
        fill_dict["fill_input_digest"] = (accounting_apply.get("accounting") or {}).get(
            "fill_input_digest"
        )
        fill_dict["accounting_output_digest"] = (accounting_apply.get("accounting") or {}).get(
            "accounting_output_digest"
        )
        fill_dict["canonical_futures_accounting"] = True
        state.fill_ledger.append(dict(fill_dict))

    _update_session_state_from_replay(state, result=replay)

    # Capability 6.1 — commit C1 acceptance + C3 carrier; optional durable persistence.
    carrier_after = None
    if replay.intermediate is not None:
        carrier_after = replay.intermediate.directional_confirmation_progress_after
    state.last_confirmation_commit = dict(
        commit_host_confirmation_after_replay_v1(
            state.confirmation_binding,
            observation_acceptance_result=observation_acceptance_result,
            confirmation_side_carrier_after=carrier_after,
            persist=bool(persist_confirmation and state.confirmation_state_root),
            writer_session_id=session_id,
        )
    )

    # Capability 6.2 — commit RuntimeScopeState + CanonicalScopeSnapshot; no silent reinit.
    current_scope_after = None
    runtime_scope_after = None
    runtime_scope_reinitialized = False
    if replay.intermediate is not None:
        current_scope_after = replay.intermediate.current_scope
        runtime_scope_after = replay.intermediate.runtime_scope_state_after
        runtime_scope_reinitialized = bool(replay.intermediate.runtime_scope_reinitialized)
    obs_state = state.confirmation_binding.observation_acceptance_state
    market_epoch = None if obs_state is None else int(obs_state.market_observation_epoch.value)
    last_event_time = None
    if (
        observation_acceptance_result is not None
        and observation_acceptance_result.observation_identity is not None
    ):
        last_event_time = float(observation_acceptance_result.observation_identity.venue_event_time)
    state.last_dynamic_scope_commit = dict(
        commit_host_dynamic_scope_after_replay_v1(
            state.dynamic_scope_binding,
            observation_acceptance_result=observation_acceptance_result,
            current_scope=current_scope_after,
            runtime_scope_state_after=runtime_scope_after,
            confirmation_session_id=state.confirmation_binding.confirmation_session_id,
            market_observation_epoch=market_epoch,
            last_market_event_time=last_event_time,
            position_context={
                "position_state": str(state.position_state),
                "existing_position_side": str(state.existing_position_side),
                "venue_flat": bool(state.venue_flat),
                "has_open_position": not bool(state.venue_flat),
            },
            scope_direction_state=str(state.scope_direction_state.value),
            side_state=str(state.side_state.value),
            host_trading_epoch=int(state.trading_epoch),
            price_path_tail=tuple(float(x) for x in state.mid_prices[-PRICE_PATH_MAX_LEN:]),
            persist=bool(persist_dynamic_scope and state.dynamic_scope_state_root),
            writer_session_id=session_id,
            runtime_scope_reinitialized=runtime_scope_reinitialized,
        )
    )

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
            "PRODUCTIVE_RECONCILIATION_BEFORE_ALPHA",
            "SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_BEFORE_ALPHA",
            "CANONICAL_FUTURES_ACCOUNTING_AFTER_FILL",
            "C1_C2_C3_CONFIRMATION_PRODUCTIVELY_BOUND",
            f"FUTURES_ACCOUNTING_RUNTIME_BOUND={state.futures_accounting_bound}",
            f"ACCOUNTING_SINGLE_WRITER={state.accounting_single_writer_identity}",
            f"PORTFOLIO_SINGLE_WRITER={state.portfolio_single_writer_identity}",
            f"CONFIRMATION_SESSION_ID={state.confirmation_binding.confirmation_session_id}",
            f"DYNAMIC_SCOPE_SESSION_ID={state.dynamic_scope_binding.scope_session_id}",
            f"DYNAMIC_SCOPE_ADVANCED={state.dynamic_scope_binding.last_scope_advanced}",
            f"FEATURE_WINDOW_MIN={FEATURE_WINDOW_MIN}",
            "DYNAMIC_SCOPE_PRODUCTIVELY_BOUND",
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
    repository_sha: str = "OFFLINE_DETERMINISTIC_EVIDENCE",
    reconciliation_state_root: Optional[Path] = None,
    selection_state_root: Optional[Path] = None,
    ranking_state_root: Optional[Path] = None,
    universe_state_root: Optional[Path] = None,
    mark_price_by_native_id: Optional[Mapping[str, Any]] = None,
    require_selection_binding: bool = True,
    allow_direct_instrument_override: bool = False,
    accounting_state_root: Optional[Path] = None,
) -> tuple[BridgeSessionStateV1, list[BridgeCycleResultV1]]:
    if require_selection_binding and instrument_id != PRODUCTION_INSTRUMENT_ID:
        if not allow_direct_instrument_override:
            raise RuntimeError("DIRECT_INSTRUMENT_OVERRIDE_REJECTED")
    state = BridgeSessionStateV1(
        instrument_id=instrument_id,
        require_selection_binding=require_selection_binding,
    )
    if reconciliation_state_root is not None:
        state.reconciliation_state_root = str(reconciliation_state_root)
    if selection_state_root is not None:
        state.selection_state_root = str(selection_state_root)
    if ranking_state_root is not None:
        state.ranking_state_root = str(ranking_state_root)
    if universe_state_root is not None:
        state.universe_state_root = str(universe_state_root)
    if mark_price_by_native_id is not None:
        state.mark_price_by_native_id = dict(mark_price_by_native_id)
    if accounting_state_root is not None:
        state.accounting_state_root = str(accounting_state_root)
    results: list[BridgeCycleResultV1] = []
    for i, mid in enumerate(mid_prices):
        results.append(
            run_bridge_cycle_v1(
                state,
                mid_price=float(mid),
                event_ts_unix=start_ts_unix + float(i),
                session_id=session_id,
                repository_sha=repository_sha,
                reconciliation_state_root=reconciliation_state_root,
                direct_instrument_override=(
                    instrument_id
                    if allow_direct_instrument_override
                    and instrument_id != PRODUCTION_INSTRUMENT_ID
                    else None
                ),
            )
        )
    return state, results
