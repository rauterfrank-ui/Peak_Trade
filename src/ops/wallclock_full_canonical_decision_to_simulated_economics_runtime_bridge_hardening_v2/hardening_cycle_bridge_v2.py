"""Hardened wallclock decision→economics cycle bridge v2."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
    SimulatedFillV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.constants_v2 import (
    AI_LAYER_CAN_OVERRIDE_DECISIONS,
    AI_LAYER_NON_AUTHORITY,
    AI_LAYER_ROLE,
    CAPABILITY_ID,
    DECISION_AUTHORITY_OWNER,
    ECONOMIC_VALIDITY_PASS,
    EXECUTION_CLASS_ANALYTICAL,
    FEATURE_WINDOW_MIN,
    LIVE_AUTHORIZED,
    ORDERS_AUTHORIZED,
    OWNER,
    PACKAGE_MARKER,
    PAPER_EXECUTION_AUTHORIZED,
    PRICE_PATH_MAX_LEN,
    PROMOTION_PASS,
    RUNTIME_BRIDGE_LIVE_ACTIVATED,
    SCHEMA_VERSION,
    SESSION_RESTART_POLICY,
    TESTNET_AUTHORIZED,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.feature_regime_pipeline_v2 import (
    compute_feature_regime_from_mid_prices_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.idempotent_portfolio_v2 import (
    IdempotentPortfolioV2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.market_data_price_basis_v2 import (
    ExplicitPriceBasisV2,
    build_explicit_mid_price_basis_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.provenance_v2 import (
    build_config_bundle_digest,
    make_scoped_id,
    portfolio_state_hash,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.safety_binding_v2 import (
    evaluate_bridge_safety_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.intended_action_mapper_v1 import (
    map_replay_result_to_intended_analytical_action_v1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationTransportMetadataV1,
)
from trading.market_state.time_sample_epoch_semantics_v1 import MarketSampleIdentityV1
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
from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.runtime_v1 import (
    ProductiveEvidenceAccumulationStateV1,
    accumulate_productive_research_evidence_from_cycle_v1,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    accumulate_max_age_research_evidence_record_from_cycle_v1,
)
from trading.master_v2.canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1 import (
    VolatilityRestartStatusV1,
    VolatilityReuseStatusV1,
)
from trading.master_v2.canonical_volatility_hot_path_contract_closure_v1 import (
    BRIDGE_COMPETING_PRODUCER_IDENTITY,
    build_hot_path_volatility_cycle_evidence_v1,
    productive_cmc_volatility_seed_v1,
    reject_competing_bridge_producer_as_productive_authority_v1,
)
from trading.master_v2.canonical_volatility_productive_runtime_cmc_typed_binding_v1 import (
    CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1,
)
from trading.master_v2.canonical_volatility_pt1m_mark_observation_finalizer_v1 import (
    CanonicalVolatilityPt1mMarkObservationFinalizerV1,
)
from trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
    demote_trading_gate_for_typed_presence_failure_v1,
    evaluate_double_play_runtime_typed_volatility_presence_gate_v1,
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

CALL_GRAPH_V2: tuple[str, ...] = (
    "okx_public_market_data",
    "feature_pipeline",
    "regime_pipeline",
    "canonical_volatility_productive_runtime_cmc_typed_binding",
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

_DEFAULT_VOL_TYPED_BINDING_VENUE = "okx_europe"
_DEFAULT_VOL_TYPED_BINDING_VENUE_INSTRUMENT_ID = PRODUCTION_INSTRUMENT_ID


def _ensure_typed_volatility_binding_host_v1(
    state: "HardenedBridgeSessionStateV2",
) -> CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1:
    if state.typed_volatility_cmc_binding_host is None:
        state.typed_volatility_cmc_binding_host = (
            CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1.create(
                venue=_DEFAULT_VOL_TYPED_BINDING_VENUE,
                canonical_instrument_id=str(state.instrument_id),
                venue_instrument_id=_DEFAULT_VOL_TYPED_BINDING_VENUE_INSTRUMENT_ID,
                persistence_path=state.typed_volatility_persistence_path,
            )
        )
    return state.typed_volatility_cmc_binding_host


def ensure_pt1m_mark_observation_finalizer_v1(
    state: "HardenedBridgeSessionStateV2",
) -> CanonicalVolatilityPt1mMarkObservationFinalizerV1:
    """Session-local PT1M finalizer for productive wallclock → typed-vol wiring."""
    expected_venue = _DEFAULT_VOL_TYPED_BINDING_VENUE
    expected_canon = str(state.instrument_id)
    expected_venue_inst = _DEFAULT_VOL_TYPED_BINDING_VENUE_INSTRUMENT_ID
    if state.pt1m_mark_observation_finalizer is None:
        state.pt1m_mark_observation_finalizer = (
            CanonicalVolatilityPt1mMarkObservationFinalizerV1.create(
                venue=expected_venue,
                canonical_instrument_id=expected_canon,
                venue_instrument_id=expected_venue_inst,
            )
        )
        return state.pt1m_mark_observation_finalizer
    finalizer = state.pt1m_mark_observation_finalizer
    if (
        finalizer.venue != expected_venue
        or finalizer.canonical_instrument_id != expected_canon
        or finalizer.venue_instrument_id != expected_venue_inst
    ):
        # Instrument/venue identity change: isolate state (no cross-instrument history).
        finalizer.reset_for_instrument_v1(
            venue=expected_venue,
            canonical_instrument_id=expected_canon,
            venue_instrument_id=expected_venue_inst,
        )
        state.typed_volatility_cmc_binding_host = None
    return finalizer


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


@dataclass
class HardenedBridgeSessionStateV2:
    instrument_id: str = PRODUCTION_INSTRUMENT_ID
    session_id: str = ""
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
    portfolio: IdempotentPortfolioV2 = field(default_factory=IdempotentPortfolioV2)
    fill_ledger: list[dict[str, Any]] = field(default_factory=list)
    cycle_ledger: list[dict[str, Any]] = field(default_factory=list)
    killstate_active: bool = False
    killstate_trigger: str = ""
    config_digest: str = ""
    session_restart_policy: str = SESSION_RESTART_POLICY
    typed_volatility_cmc_binding_host: (
        CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1 | None
    ) = None
    typed_volatility_persistence_path: Path | None = None
    last_typed_volatility_binding_telemetry: dict[str, Any] | None = None
    pt1m_mark_observation_finalizer: CanonicalVolatilityPt1mMarkObservationFinalizerV1 | None = None
    # Non-enforcing research evidence accumulation (threshold remains unresolved).
    max_age_research_evidence_ledger: list[dict[str, Any]] = field(default_factory=list)
    max_age_research_evidence_ledger_path: Path | None = None
    # Optional productive research-evidence accumulation (diagnostic only).
    productive_evidence_accumulation_state: ProductiveEvidenceAccumulationStateV1 | None = None

    def append_mid(self, mid: float) -> None:
        self.mid_prices.append(float(mid))
        if len(self.mid_prices) > PRICE_PATH_MAX_LEN:
            self.mid_prices = self.mid_prices[-PRICE_PATH_MAX_LEN:]

    def restore_typed_volatility_binding_host_from_persistence_v1(
        self,
        *,
        persistence_path: Path,
    ) -> CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1:
        """Restart path: restore mark history only; estimate remains fail-closed until PRODUCED."""
        self.typed_volatility_persistence_path = persistence_path
        self.typed_volatility_cmc_binding_host = (
            CanonicalVolatilityProductiveRuntimeCmcTypedBindingHostV1.restore_from_persistence_v1(
                persistence_path=persistence_path,
            )
        )
        return self.typed_volatility_cmc_binding_host


def _update_session_state_from_replay(state: HardenedBridgeSessionStateV2, *, result: Any) -> None:
    if result.intermediate is None:
        state.last_evaluated_trading_epoch = state.trading_epoch
        state.trading_epoch += 1
        return
    inter = result.intermediate
    try:
        state.side_state = SideState(inter.state_switch.next_side_state)
    except Exception:  # noqa: BLE001
        pass
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
    snap = state.portfolio.snapshot()
    positions = (snap.get("state") or {}).get("positions") or {}
    pos = positions.get(state.instrument_id) or {}
    try:
        qty = Decimal(str(pos.get("quantity", "0")))
    except Exception:  # noqa: BLE001
        qty = Decimal("0")
    if qty == 0:
        state.position_state = PositionState.FLAT_RECONCILED
        state.existing_position_side = ExistingPositionSide.NONE
        state.position_management_context = PositionManagementContext.FLAT
        state.venue_flat = True
    elif qty > 0:
        state.position_state = PositionState.OPEN_FULL
        state.existing_position_side = ExistingPositionSide.LONG
        state.position_management_context = PositionManagementContext.LONG_POSITION
        state.venue_flat = False
    else:
        state.position_state = PositionState.OPEN_FULL
        state.existing_position_side = ExistingPositionSide.SHORT
        state.position_management_context = PositionManagementContext.SHORT_POSITION
        state.venue_flat = False
    state.last_evaluated_trading_epoch = state.trading_epoch
    state.trading_epoch += 1


def run_hardened_bridge_cycle_v2(
    state: HardenedBridgeSessionStateV2,
    *,
    mid_price: float,
    event_ts_unix: float,
    session_id: str,
    price_basis: ExplicitPriceBasisV2 | None = None,
    forced_actionable: Mapping[str, Any] | None = None,
    finalized_pt1m_mark_sample: MarketSampleIdentityV1 | None = None,
    finalized_pt1m_mark_price: float | None = None,
    finalized_pt1m_event_time_unix_seconds: float | None = None,
    finalized_pt1m_transport: ObservationTransportMetadataV1 | None = None,
) -> dict[str, Any]:
    if state.session_restart_policy != SESSION_RESTART_POLICY:
        raise RuntimeError("IMPLICIT_RESUME_FORBIDDEN")
    if state.session_id and state.session_id != session_id:
        raise RuntimeError("SESSION_ID_MUTATION_FORBIDDEN_NO_IMPLICIT_RESUME")
    state.session_id = session_id
    state.cycle_index += 1
    state.append_mid(mid_price)
    cycle_id = make_scoped_id("cycle", session_id, state.cycle_index)

    basis = price_basis or build_explicit_mid_price_basis_v2(
        mid_price=float(mid_price),
        event_ts_unix=float(event_ts_unix),
        receive_ts_unix=float(event_ts_unix),
    )
    features = compute_feature_regime_from_mid_prices_v2(state.mid_prices)
    metrics0 = state.portfolio.economic_metrics()
    safety = evaluate_bridge_safety_v2(
        killstate_active=state.killstate_active,
        killstate_trigger=state.killstate_trigger,
        warmup_complete=features.warmup_complete,
        regime_ok=features.ok,
        price_basis_ok=basis.mid_price > 0,
        max_drawdown=float(metrics0.drawdown),
        bridge_enabled=True,
    )

    params = state.portfolio.model.params
    config_digest = build_config_bundle_digest(
        feature_config_version=features.feature_config_version,
        regime_config_version=features.regime_config_version,
        price_basis_contract_version=basis.price_basis_contract_version,
        fee_rate_bps=str(params.fee_rate_bps),
        slippage_bps=str(params.slippage_bps),
        initial_equity=str(params.initial_equity),
        feature_window_min=FEATURE_WINDOW_MIN,
    )
    if state.config_digest and state.config_digest != config_digest:
        raise RuntimeError(f"CONFIG_DRIFT:{state.config_digest}:{config_digest}")
    state.config_digest = config_digest

    decision_id = make_scoped_id("decision", session_id, cycle_id, state.trading_epoch)
    risk_decision_id = make_scoped_id("risk", decision_id, safety.safety_result)
    intent_id = make_scoped_id("intent", risk_decision_id, features.feature_digest)

    price_path = tuple(state.mid_prices[-FEATURE_WINDOW_MIN:])
    if len(price_path) < 2:
        price_path = (float(mid_price), float(mid_price))

    mark = float(features.mark_price or basis.mid_price)
    warmup_status = (
        WarmupStatus.WARMUP_COMPLETE if features.warmup_complete else WarmupStatus.WARMUP_REQUIRED
    )
    input_digest = hashlib.sha256(
        json.dumps(
            {
                "capability_id": CAPABILITY_ID,
                "session_id": session_id,
                "cycle_id": cycle_id,
                "mid": mark,
                "regime": features.regime_id,
                "feature_digest": features.feature_digest,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()

    market_context = with_computed_input_digest(
        CanonicalMarketContextV1(
            context_id=f"ctx-{state.instrument_id}-epoch{state.trading_epoch}-hardening-v2",
            instrument_id=state.instrument_id,
            market_type=FuturesMarketType.PERPETUAL,
            trading_epoch=state.trading_epoch,
            market_event_time=_iso_now(event_ts_unix),
            decision_time=_iso_now(event_ts_unix + 0.001),
            bar_interval="tick",
            bar_finality_status=BarFinalityStatus.FINALIZED,
            mark_price=mark,
            index_price=mark,
            best_bid=basis.best_bid,
            best_ask=basis.best_ask,
            spread=basis.spread,
            volume=1_000_000.0,
            open_interest=50_000_000.0,
            funding_rate=0.0001,
            # Hot-path closure: never seed CMC from competing feature_regime proxy
            # (sample var ddof=1 × sqrt(n)). Typed bind overwrites atomically.
            volatility_estimate=productive_cmc_volatility_seed_v1(),
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

    typed_host = _ensure_typed_volatility_binding_host_v1(state)
    ingest_sample = finalized_pt1m_mark_sample is not None or (
        finalized_pt1m_mark_price is not None and finalized_pt1m_event_time_unix_seconds is not None
    )
    typed_binding = typed_host.apply_to_market_context_v1(
        market_context,
        sample=finalized_pt1m_mark_sample,
        transport=finalized_pt1m_transport,
        venue=_DEFAULT_VOL_TYPED_BINDING_VENUE,
        canonical_instrument_id=str(state.instrument_id),
        venue_instrument_id=_DEFAULT_VOL_TYPED_BINDING_VENUE_INSTRUMENT_ID,
        event_time_unix_seconds=finalized_pt1m_event_time_unix_seconds,
        mark_price=finalized_pt1m_mark_price,
        is_final=True,
        ingest_sample=ingest_sample,
    )
    market_context = typed_binding.context
    state.last_typed_volatility_binding_telemetry = typed_binding.telemetry.to_dict()
    _ = input_digest  # retained for provenance continuity with prior bridge evidence shape
    # Competing bridge producer remains regime-only; never productive CMC authority.
    reject_competing_bridge_producer_as_productive_authority_v1(
        source_identity=BRIDGE_COMPETING_PRODUCER_IDENTITY,
        used_as_cmc_volatility_estimate=False,
    )

    # Productive Double-Play typed cutover: consume host eligibility; do not discard.
    # Wire producer/binding reuse+restart labels into non-enforcing age telemetry.
    binding_reuse = VolatilityReuseStatusV1(str(typed_binding.telemetry.reuse_status))
    binding_restart = VolatilityRestartStatusV1(str(typed_binding.telemetry.restart_status))
    presence_gate = evaluate_double_play_runtime_typed_volatility_presence_gate_v1(
        market_context,
        eligibility=typed_binding.typed_binding_eligibility,
        reuse_status=binding_reuse,
        restart_status=binding_restart,
    )
    effective_trading_gate = safety.trading_gate_enum
    if not presence_gate.alpha_scope_entry_authority_allowed:
        effective_trading_gate = demote_trading_gate_for_typed_presence_failure_v1(
            safety.trading_gate_enum
        )

    replay_input = build_integrated_offline_replay_input_v1(
        replay_id=f"{session_id}-{cycle_id}",
        instrument_id=state.instrument_id,
        trading_epoch=state.trading_epoch,
        canonical_market_context=market_context,
        market_context_binding_state=CanonicalMarketContextBindingStateV1(),
        scope_prerequisites=ScopeInitializationPrerequisitesV1(
            required_window_complete=features.warmup_complete and features.ok,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
        scope_reinitialization_guard=ScopeReinitializationGuardV1(),
        existing_scope=None,
        scope_direction_state=state.scope_direction_state,
        scope_confirmation_state=ScopeConfirmationStateV1(
            candidate_kind=None,
            candidate_count=1 if features.ok else 0,
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
            candidate_count=1 if features.ok else 0,
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
        reconciliation_state=ReconciliationState.RECONCILED,
        trading_gate=effective_trading_gate,
        safety_mode=safety.safety_mode_enum,
        existing_position_side=state.existing_position_side,
        venue_flat=state.venue_flat,
        cooldown_pass=True,
        scope_adverse_exit_signal=PolicySignalV0(triggered=False),
        profit_protection_signal=PolicySignalV0(triggered=False),
        time_exit_signal=PolicySignalV0(triggered=False),
        strategy_invalidation_signal=PolicySignalV0(triggered=False),
        hard_risk_reduction_signal=safety.hard_risk_signal_obj,
        safety_exit_signal=safety.safety_exit_signal_obj,
        policies=_default_policies(),
        component_versions=_component_versions(),
        policy_versions=_policy_versions(),
        config_digest=config_digest,
        implementation_digest=hashlib.sha256(CAPABILITY_ID.encode()).hexdigest(),
        input_digest=input_digest,
        expected_component_contracts=_component_versions(),
        context_reference=f"hardening-v2-context-epoch-{state.trading_epoch}",
        now_tick=state.cycle_index,
        require_productive_typed_volatility_presence_gate=True,
        productive_typed_volatility_binding_eligibility=(typed_binding.typed_binding_eligibility),
    )

    replay = run_integrated_offline_trading_logic_replay_v1(replay_input)
    intended = map_replay_result_to_intended_analytical_action_v1(
        replay,
        instrument_id=state.instrument_id,
        portfolio_snapshot=state.portfolio.snapshot(),
    )

    # Forced wiring overrides only when explicitly supplied (fixture path).
    if forced_actionable is not None:
        intended_side = str(forced_actionable.get("intended_side") or "BUY")
        intended_qty = Decimal(str(forced_actionable.get("intended_quantity") or "0.1"))
        intended_dict = {
            "intended_side": intended_side,
            "intended_quantity": str(intended_qty),
            "decision_outcome": "forced_wiring_fixture",
            "selected_side": intended_side.lower(),
            "intent_action": "FORCED_WIRING",
            "quantity_source": "forced_wiring_fixture",
            "safety_blocked": False,
            "reason_codes": ["FORCED_WIRING_FIXTURE"],
        }
    else:
        # Non-actionable if safety veto or incomplete regime/warmup.
        if safety.safety_result in {"BLOCKED", "EXIT_ONLY"} and intended.intended_side in {
            "BUY",
            "SELL",
        }:
            if safety.safety_result == "BLOCKED" or (
                safety.safety_result == "EXIT_ONLY" and intended.intent_action.startswith("ENTER")
            ):
                intended_dict = {
                    "intended_side": "HOLD",
                    "intended_quantity": "0",
                    "decision_outcome": str(intended.decision_outcome),
                    "selected_side": intended.selected_side,
                    "intent_action": intended.intent_action,
                    "quantity_source": "safety_veto",
                    "safety_blocked": True,
                    "reason_codes": list(intended.reason_codes)
                    + [safety.veto_reason or "SAFETY_VETO"],
                }
            else:
                intended_dict = intended.to_dict()
        else:
            intended_dict = intended.to_dict()
            if not features.warmup_complete:
                intended_dict = {
                    **intended_dict,
                    "intended_side": "HOLD",
                    "intended_quantity": "0",
                    "quantity_source": "insufficient_history",
                    "reason_codes": list(intended_dict.get("reason_codes") or [])
                    + ["INSUFFICIENT_HISTORY"],
                }

    before_hash = portfolio_state_hash(state.portfolio.snapshot())
    fill_id = None
    fill_dict = None
    side = str(intended_dict["intended_side"])
    qty = Decimal(str(intended_dict["intended_quantity"]))
    if side in {"BUY", "SELL"} and qty > 0:
        fill_id = make_scoped_id("fill", intent_id, mark, qty, side)
    fill_obj = state.portfolio.apply_intended_action(
        instrument_id=state.instrument_id,
        side=side,
        quantity=qty if side in {"BUY", "SELL"} else Decimal("0"),
        mark_price=Decimal(str(mark)),
        intent_id=intent_id,
        fill_id=fill_id,
    )
    after_hash = portfolio_state_hash(state.portfolio.snapshot())
    if fill_obj is not None:
        fill_dict = _fill_to_dict(fill_obj)
        fill_dict.update(
            {
                "session_id": session_id,
                "cycle_id": cycle_id,
                "decision_id": decision_id,
                "risk_decision_id": risk_decision_id,
                "intent_id": intent_id,
                "fill_id": fill_id,
                "reference_price": str(mark),
                "simulated_fill_price": str(fill_obj.fill_price),
                "slippage_amount": str(fill_obj.slippage_cost),
                "fee_amount": str(fill_obj.fee),
                "market_data_reference": basis.market_data_reference,
                "portfolio_state_before_hash": before_hash,
                "portfolio_state_after_hash": after_hash,
                "config_digest": config_digest,
                "cycle_index": state.cycle_index,
                "trading_epoch": state.trading_epoch,
            }
        )
        state.fill_ledger.append(dict(fill_dict))

    _update_session_state_from_replay(state, result=replay)

    sizing_result = str(replay.evidence.risk_sizing_effect or "NONE")
    if replay.intermediate and replay.intermediate.capital_risk_sizing_decision is not None:
        sizing_result = str(replay.intermediate.capital_risk_sizing_decision.outcome.value)

    econ = state.portfolio.economic_metrics().to_dict()
    cycle = {
        "ok": True,
        "capability_id": CAPABILITY_ID,
        "package_marker": PACKAGE_MARKER,
        "schema_version": SCHEMA_VERSION,
        "owner": OWNER,
        "session_id": session_id,
        "cycle_id": cycle_id,
        "cycle_index": state.cycle_index,
        "trading_epoch": state.trading_epoch - 1,
        "instrument_id": state.instrument_id,
        "decision_authority_owner": DECISION_AUTHORITY_OWNER,
        "decision_id": decision_id,
        "risk_decision_id": risk_decision_id,
        "intent_id": intent_id,
        "fill_id": fill_id,
        "feature_regime": features.to_dict(),
        "feature_digest": features.feature_digest,
        "regime_digest": features.regime_digest,
        "canonical_volatility_typed_binding": dict(
            state.last_typed_volatility_binding_telemetry or {}
        ),
        "canonical_market_context_typed_estimate_present": (
            market_context.canonical_volatility_estimate is not None
        ),
        "canonical_volatility_hot_path_evidence": build_hot_path_volatility_cycle_evidence_v1(
            market_context,
            producer_outcome=str(typed_binding.telemetry.producer_outcome),
            reason_codes=presence_gate.reason_codes,
        ).to_dict(),
        "double_play_typed_volatility_presence_gate": presence_gate.to_dict(),
        "config_digest": config_digest,
        "price_basis": basis.to_dict(),
        "market_data_reference": basis.market_data_reference,
        "decision_outcome": str(replay.evidence.decision_outcome),
        "direction": str(
            replay.evidence.next_direction_state or replay.evidence.previous_direction_state
        ),
        "selected_side": str(replay.evidence.selected_side),
        "risk_sizing_result": sizing_result,
        "safety_evaluation": safety.to_dict(),
        "safety_result": safety.safety_result,
        "intended_action": {
            **intended_dict,
            "session_id": session_id,
            "cycle_id": cycle_id,
            "decision_id": decision_id,
            "risk_decision_id": risk_decision_id,
            "intent_id": intent_id,
            "feature_digest": features.feature_digest,
            "regime_digest": features.regime_digest,
            "config_digest": config_digest,
            "decision_producer": DECISION_AUTHORITY_OWNER,
        },
        "fill": fill_dict,
        "portfolio_state_before_hash": before_hash,
        "portfolio_state_after_hash": after_hash,
        "portfolio_snapshot": dict(state.portfolio.snapshot()),
        "economic_metrics": econ,
        "reason_codes": list(replay.evidence.reason_codes),
        "blockers": list(features.blockers),
        "call_graph": list(CALL_GRAPH_V2),
        "orders_authorized": ORDERS_AUTHORIZED,
        "testnet_authorized": TESTNET_AUTHORIZED,
        "live_authorized": LIVE_AUTHORIZED,
        "paper_execution_authorized": PAPER_EXECUTION_AUTHORIZED,
        "economic_validity_pass": ECONOMIC_VALIDITY_PASS,
        "promotion_pass": PROMOTION_PASS,
        "runtime_bridge_live_activated": RUNTIME_BRIDGE_LIVE_ACTIVATED,
        "execution_class": EXECUTION_CLASS_ANALYTICAL,
        "execution_eligible": False,
        "session_restart_policy": SESSION_RESTART_POLICY,
        "default_regime_fallback_active": features.default_regime_fallback_active,
        "synthetic_bid_ask_fallback_active": basis.synthetic_bid_ask_fallback_active,
        "forced_wiring": forced_actionable is not None,
        "ai_layer_non_authority": AI_LAYER_NON_AUTHORITY,
        "ai_layer_can_override_decisions": AI_LAYER_CAN_OVERRIDE_DECISIONS,
        "ai_layer_role": AI_LAYER_ROLE,
        "notes": [
            "HARDENING_V2",
            "ANALYTICAL_SIMULATION_ONLY",
            "NO_ORDERS",
            "NO_IMPLICIT_RESUME",
            "SAFETY_KERNEL_REAL_EVALUATION_BOUND",
            "AI_LAYER_NON_AUTHORITY",
        ],
    }
    research_join = accumulate_max_age_research_evidence_record_from_cycle_v1(
        cycle,
        ledger_path=state.max_age_research_evidence_ledger_path,
        in_memory_ledger=state.max_age_research_evidence_ledger,
    )
    cycle["canonical_volatility_max_age_research_evidence_join"] = research_join.to_dict()
    # Productive accumulation is diagnostic-only: write failures must not mutate trading.
    if state.productive_evidence_accumulation_state is not None:
        from research.canonical_volatility_max_age_productive_research_evidence_accumulation_v1.productive_bridge_binding_v1 import (
            build_productive_bridge_cycle_authority_v1,
            iso_from_unix_v1,
            market_sample_id_from_identity_v1,
            stamp_productive_bridge_cycle_authority_v1,
        )

        acc_state = state.productive_evidence_accumulation_state
        sample_for_id = finalized_pt1m_mark_sample
        if sample_for_id is None:
            # Fail closed: productive accumulation requires typed MarketSampleIdentity.
            cycle["productive_research_evidence_accumulation"] = {
                "error": "productive_bridge_requires_market_sample_identity",
                "status": "EVIDENCE_WRITE_FAILURE",
                "trading_behavior_mutated": False,
            }
        else:
            market_sample_id = market_sample_id_from_identity_v1(sample_for_id)
            receive_time = None
            if finalized_pt1m_transport is not None:
                receive_time = iso_from_unix_v1(float(finalized_pt1m_transport.receive_time))
            campaign_id = acc_state.campaign_id or f"bridge_campaign_{session_id}"
            authority = build_productive_bridge_cycle_authority_v1(
                campaign_id=campaign_id,
                repository_sha=acc_state.repository_sha,
                session_id=session_id,
                market_sample_id=market_sample_id,
            )
            cycle = stamp_productive_bridge_cycle_authority_v1(
                cycle,
                authority=authority,
                venue=_DEFAULT_VOL_TYPED_BINDING_VENUE,
                venue_instrument_id=_DEFAULT_VOL_TYPED_BINDING_VENUE_INSTRUMENT_ID,
                receive_time=receive_time,
                market_sample=sample_for_id.to_dict(),
            )
            cycle["productive_research_evidence_accumulation"] = (
                accumulate_productive_research_evidence_from_cycle_v1(
                    cycle,
                    state=acc_state,
                    project_to_join_ledger=True,
                )
            )
    if cycle["execution_eligible"]:
        raise RuntimeError("EXECUTION_ELIGIBLE_MUST_REMAIN_FALSE")
    state.cycle_ledger.append(cycle)
    return cycle


def run_hardened_bridge_cycles_from_mids_v2(
    mid_prices: Sequence[float],
    *,
    start_ts_unix: float = 1_700_000_000.0,
    session_id: str = "hardening-v2-probe",
    instrument_id: str = PRODUCTION_INSTRUMENT_ID,
    portfolio_params: PortfolioEconomicsModelParamsV1 | None = None,
) -> tuple[HardenedBridgeSessionStateV2, list[dict[str, Any]]]:
    state = HardenedBridgeSessionStateV2(
        instrument_id=instrument_id,
        portfolio=IdempotentPortfolioV2.from_params(portfolio_params),
    )
    results: list[dict[str, Any]] = []
    for i, mid in enumerate(mid_prices):
        results.append(
            run_hardened_bridge_cycle_v2(
                state,
                mid_price=float(mid),
                event_ts_unix=start_ts_unix + float(i),
                session_id=session_id,
            )
        )
    return state, results
