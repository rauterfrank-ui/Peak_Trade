"""Hardened wallclock decision→economics cycle bridge v2."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from src.learning.deterministic_decision_outcome_v0.capture_v0 import DdoCaptureBindingV0
from src.governance.canonical_order_intent_v1 import canonical_order_intent_to_semantic_dict
from src.ops.bounded_futures_testnet_venue_binding_v0 import PRODUCTION_INSTRUMENT_ID
from src.ops.decision_config_ownership_and_consumer_closure_v1.canonical_values_v1 import (
    CANONICAL_CONFIRMATION_EPOCHS,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.constants_v1 import (
    CALL_GRAPH_CONFIG_BIND_STEP,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.host_binding_v1 import (
    HostDecisionConfigBindingV1,
    ensure_host_decision_config_binding_v1,
    require_bound_decision_config_v1,
)
from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
    CALL_GRAPH_EXIT_PRODUCER_STEP,
    FROZEN_PROFIT_PROTECTION_DISTANCE,
    SAFETY_PRODUCER_OWNER,
)
from src.ops.exit_policy_producer_binding_v1.host_binding_v1 import (
    HostExitPolicyBindingV1,
    ensure_host_exit_policy_binding_v1,
    evaluate_host_exit_policy_producers_v1,
    exit_policy_config_digest_v1,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import ExitPolicyProducerBundleV1
from src.ops.integrated_paper_shadow_observation_session_v1.portfolio_economics_model_v1 import (
    PortfolioEconomicsModelParamsV1,
    SimulatedFillV1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.constants_v2 import (
    AI_LAYER_CAN_OVERRIDE_DECISIONS,
    AI_LAYER_NON_AUTHORITY,
    AI_LAYER_ROLE,
    BRIDGE_SAFETY_ROLE,
    CANONICAL_REPLAY_SAFETY_OWNER,
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
    SafetyEvaluationV2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.intended_action_mapper_v1 import (
    IntendedAnalyticalActionV1,
    map_replay_result_to_intended_analytical_action_v1,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationAcceptanceResultV1,
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
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.models_v1 import (
    ObservationSourceClassV1,
)
from research.m9_s1_durable_market_session_evidence_accumulation_v1.passive_accumulation_v1 import (
    passive_accumulate_from_bridge_cycle_v1,
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
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    CANONICAL_SCOPE_INITIALIZATION_LAYER_VERSION,
    CanonicalScopeInitializationPolicyV1,
    SCOPE_INITIALIZATION_POLICY_INSTRUMENT_RELATIVE_VERSION,
    SCOPE_INITIALIZATION_POLICY_VERSION,
    ScopeInitializationPrerequisitesV1,
    ScopeReinitializationGuardV1,
    default_instrument_relative_scope_initialization_policy_v1,
)
from trading.master_v2.canonical_volatility_default_quarantine_v1 import (
    quarantine_explicit_replay_default_volatility_v1,
    require_admitted_legacy_volatility_float_v1,
)
from trading.master_v2.layer_c_scope_event_distance_binding_v1 import (
    layer_c_derived_exit_policy_adverse_config_digest_v1,
    resolve_layer_c_event_distances_from_canonical_market_context_v1,
    resolve_layer_c_event_distances_from_mark_and_volatility_v1,
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
from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
    DirectionalConfirmationSideStateCarrierV1,
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
    _side_state_to_entry_exit_direction,
    build_integrated_offline_replay_input_v1,
    run_integrated_offline_trading_logic_replay_v1,
    scope_direction_from_side_state_v1,
)
from trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategySuitabilityAgreementMaterialV1,
    serialize_strategy_suitability_agreement_material_v1,
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


def derive_required_window_complete_v2(*, warmup_complete: bool, features_ok: bool) -> bool:
    """Window-length completeness only; ``features_ok`` must not affect this flag.

    Matches Bridge-v1: ``required_window_complete = features.warmup_complete``.
    ``REGIME_UNCLASSIFIED_FAIL_CLOSED`` / ``features.ok`` remain a separate fail-closed path.
    """
    _ = features_ok  # intentional non-consumption (WIRING_GAP repair)
    return bool(warmup_complete)


_EXIT_REDUCE_ACTIONS = frozenset({"EXIT", "REDUCE"})
_EXIT_REDUCE_OUTCOMES = frozenset({"exit", "reduce"})
_NEW_EXPOSURE_GUARD_REASON = "DOWNSTREAM_NEW_EXPOSURE_NOT_ELIGIBLE"


def historical_exit_or_reduce_host_action_v2(
    *,
    intent_action: str,
    decision_outcome: str,
) -> bool:
    """True when host action is a historical EXIT/REDUCE, not new exposure."""
    action = str(intent_action or "").strip().upper()
    outcome = str(decision_outcome or "").strip().lower()
    if action in _EXIT_REDUCE_ACTIONS:
        return True
    if action.startswith("EXIT") or action.startswith("REDUCE"):
        return True
    return outcome in _EXIT_REDUCE_OUTCOMES


def apply_hardening_v2_downstream_new_exposure_guard_v2(
    intended: IntendedAnalyticalActionV1 | Mapping[str, Any],
    *,
    producer_safety_result: str,
    warmup_complete: bool,
) -> dict[str, Any]:
    """Fail-closed execution eligibility for new exposure only.

    Does not rewrite Replay decision_outcome, SideState, sizing, or CanonicalOrderIntent.
    Must not suppress historical EXIT/REDUCE mapped BUY/SELL.
    """
    intended_dict = (
        intended.to_dict() if isinstance(intended, IntendedAnalyticalActionV1) else dict(intended)
    )
    side = str(intended_dict.get("intended_side") or "")
    if side not in {"BUY", "SELL"}:
        return intended_dict
    if historical_exit_or_reduce_host_action_v2(
        intent_action=str(intended_dict.get("intent_action") or ""),
        decision_outcome=str(intended_dict.get("decision_outcome") or ""),
    ):
        return intended_dict
    if str(producer_safety_result) in {"BLOCKED", "EXIT_ONLY"} or not bool(warmup_complete):
        reasons = list(intended_dict.get("reason_codes") or [])
        if _NEW_EXPOSURE_GUARD_REASON not in reasons:
            reasons.append(_NEW_EXPOSURE_GUARD_REASON)
        return {
            **intended_dict,
            "intended_side": "HOLD",
            "intended_quantity": "0",
            "quantity_source": "downstream_new_exposure_execution_guard",
            "reason_codes": reasons,
        }
    return intended_dict


def _safety_evaluation_from_cap65_bundle_v2(
    bundle: ExitPolicyProducerBundleV1,
) -> SafetyEvaluationV2:
    """Adapt Cap 6.5 producer outputs to existing cycle evidence shape.

    Not a second Replay Safety evaluation. Bridge safety remains INPUT_PRODUCER_ONLY.
    """
    mode = str(bundle.safety_mode)
    if mode == SafetyMode.BLOCKED.value:
        safety_result = "BLOCKED"
    elif mode == SafetyMode.EXIT_ONLY.value:
        safety_result = "EXIT_ONLY"
    else:
        safety_result = "PASS"
    veto = str(bundle.safety_exit.reason_code or "")
    if not veto and safety_result == "EXIT_ONLY":
        veto = "WARMUP_OR_REGIME_INCOMPLETE"
    if not veto and safety_result == "BLOCKED":
        veto = str(bundle.hard_risk_reduction.reason_code or "")
    return SafetyEvaluationV2(
        safety_mode=mode,
        trading_gate=str(bundle.trading_gate),
        safety_exit_signal={
            "triggered": bool(bundle.safety_exit.triggered),
            "reason_code": str(bundle.safety_exit.reason_code or ""),
        },
        hard_risk_reduction_signal={
            "triggered": bool(bundle.hard_risk_reduction.triggered),
            "reason_code": str(bundle.hard_risk_reduction.reason_code or ""),
        },
        veto_reason=veto,
        safety_inputs={
            "evaluation_owner": SAFETY_PRODUCER_OWNER,
            "bridge_safety_role": BRIDGE_SAFETY_ROLE,
            "canonical_replay_safety_owner": CANONICAL_REPLAY_SAFETY_OWNER,
        },
        safety_result=safety_result,
        evaluation_bound=bool(bundle.evaluation_bound),
    )


def _portfolio_position_fields_v2(
    state: "HardenedBridgeSessionStateV2",
) -> tuple[bool, str, float | None]:
    snap = state.portfolio.snapshot()
    positions = (snap.get("state") or {}).get("positions") or {}
    pos = positions.get(state.instrument_id) or {}
    try:
        qty = Decimal(str(pos.get("quantity", "0")))
    except Exception:  # noqa: BLE001
        qty = Decimal("0")
    has_open = qty != 0
    if qty > 0:
        side = ExistingPositionSide.LONG.value
    elif qty < 0:
        side = ExistingPositionSide.SHORT.value
    else:
        side = ExistingPositionSide.NONE.value
    entry_raw = pos.get("avg_entry_price")
    entry_price: float | None
    try:
        entry_price = (
            float(entry_raw) if entry_raw is not None and Decimal(str(entry_raw)) != 0 else None
        )
    except Exception:  # noqa: BLE001
        entry_price = None
    if not has_open:
        entry_price = None
    return has_open, side, entry_price


CALL_GRAPH_V2: tuple[str, ...] = (
    "okx_public_market_data",
    CALL_GRAPH_CONFIG_BIND_STEP,
    "feature_pipeline",
    "regime_pipeline",
    "canonical_volatility_productive_runtime_cmc_typed_binding",
    CALL_GRAPH_EXIT_PRODUCER_STEP,
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

_HARDENING_V2_DECISION_CONFIG_REPOSITORY_SHA = "OFFLINE_HARDENING_V2_ANALYTICAL"

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
                venue_instrument_id=state.venue_instrument_id,
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
    expected_venue_inst = state.venue_instrument_id
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
        scope_initialization=default_instrument_relative_scope_initialization_policy_v1(),
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
            confirmation_epochs=int(CANONICAL_CONFIRMATION_EPOCHS),
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
        "scope_initialization": SCOPE_INITIALIZATION_POLICY_INSTRUMENT_RELATIVE_VERSION,
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
    venue_instrument_id: str = field(
        default=_DEFAULT_VOL_TYPED_BINDING_VENUE_INSTRUMENT_ID, kw_only=True
    )
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
    # Cap 6.3 / G07: typed canonical decision-runtime config binding (no local Cap-6.3 literals).
    decision_config_binding: HostDecisionConfigBindingV1 = field(
        default_factory=HostDecisionConfigBindingV1
    )
    decision_config_state_root: str | None = None
    decision_config_repository_sha: str = _HARDENING_V2_DECISION_CONFIG_REPOSITORY_SHA
    exit_policy_binding: HostExitPolicyBindingV1 = field(default_factory=HostExitPolicyBindingV1)
    # Optional: pre-bound authorized productive parameter seam (transport-only join).
    governed_authorized_productive_parameter_seam_record: Mapping[str, Any] | None = None
    last_f1_m9_threshold_consumer_wiring: dict[str, Any] | None = None
    offline_confirmation_progress: DirectionalConfirmationSideStateCarrierV1 | None = None

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


@dataclass(frozen=True)
class I17OfflineCandidateInputV2:
    artifact_digest: str
    entry: SuitabilityStrategyEntryV1
    material: StrategySuitabilityAgreementMaterialV1
    observation: ObservationAcceptanceResultV1

    def __post_init__(self) -> None:
        instrument_key = self.observation.state_before.bound_instrument_key
        if (
            not re.fullmatch(r"[a-f0-9]{64}", self.artifact_digest)
            or self.entry.disabled
            or self.entry.strategy_id != self.material.executed_strategy_id
            or self.entry.strategy_id != self.material.configured_strategy_id
            or self.observation.fail_closed
            or instrument_key is None
            or instrument_key.canonical_instrument_id != self.material.instrument_id
        ):
            raise ValueError("I17_CANDIDATE_PROFILE_MISMATCH")


def _candidate_receipt(candidate: I17OfflineCandidateInputV2, replay: Any) -> dict[str, Any]:
    suitability = {}
    if replay.intermediate is not None:
        for side, result in (
            ("long", replay.intermediate.bull_suitability),
            ("short", replay.intermediate.bear_suitability),
        ):
            if result is not None:
                suitability[side] = {
                    "status": result.status.value,
                    "eligible_strategy_ids": list(result.eligible_strategy_ids),
                    "selected_strategy_id": result.selected_strategy_id,
                    "reason_codes": list(result.reason_codes),
                }
    progress = (
        None
        if replay.intermediate is None
        else replay.intermediate.directional_confirmation_progress_after
    )
    return {
        "artifact_digest": candidate.artifact_digest,
        "material": serialize_strategy_suitability_agreement_material_v1(candidate.material),
        "market_observation_classification": candidate.observation.classification.value,
        "market_observation_epoch": candidate.observation.state_after.market_observation_epoch.value,
        "directional_confirmation_progress": None if progress is None else progress.to_dict(),
        "suitability": suitability,
    }


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
    # Next-cycle Entry/Exit cursor consumes the Replay mapping owner.
    # PENDING rows are not re-adjudicated here.
    state.direction_state = _side_state_to_entry_exit_direction(state.side_state)
    sel = str(inter.composition_result.selected_side.value).lower()
    if sel == "long":
        state.previous_composition_direction_state = CompositionDirectionState.LONG
    elif sel == "short":
        state.previous_composition_direction_state = CompositionDirectionState.SHORT
    else:
        state.previous_composition_direction_state = CompositionDirectionState.NEUTRAL
    # ScopeDirectionState is a SideState projection, not a composition overlay.
    state.scope_direction_state = scope_direction_from_side_state_v1(state.side_state)
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


_REPO_ROOT = Path(__file__).resolve().parents[3]

_HARDENING_V2_LAYER_C_VOL_QUARANTINE = quarantine_explicit_replay_default_volatility_v1(
    source_file_or_component=(
        "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2/"
        "hardening_cycle_bridge_v2.py:_HARDENING_V2_LAYER_C_VOL_QUARANTINE"
    ),
)


def _resolve_hardening_v2_layer_c_volatility_estimate_v1(raw_volatility_estimate: float) -> float:
    vol = float(raw_volatility_estimate)
    if vol > 0.0 and vol == vol:
        return vol
    return require_admitted_legacy_volatility_float_v1(_HARDENING_V2_LAYER_C_VOL_QUARANTINE)


def _resolve_governed_seam_record_for_hardening_v2_session_bind_v1(
    *,
    repo_root: Path,
    allow_bootstrap: bool = True,
) -> tuple[Mapping[str, Any] | None, str]:
    """Canonical F1/M9 runtime-applied seam for Hardening-V2 session bind (no parallel authority)."""
    from src.governance.f1_m9_productive_apply_durable_ledger_paths_v1 import (
        F1M9DurableLedgerPathsError,
        resolve_canonical_f1_m9_productive_apply_ledger_paths_v1,
        resolve_canonical_f1_m9_threshold_value_authorization_ledger_paths_v1,
    )
    from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
        consumer_wiring_authorized_v1,
    )
    from src.governance.governed_f1_m9_productive_runtime_threshold_consumer_wiring_real_mechanical_continuation_v1 import (
        GovernedF1M9ThresholdConsumerWiringRequestV1,
        resolve_runtime_applied_seam_for_consumer_wiring_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_f1_m9_canonical_durable_bootstrap_v1 import (
        ensure_canonical_f1_m9_runtime_applied_seam_materialized_v1,
    )

    if not consumer_wiring_authorized_v1(repo_root=repo_root):
        return None, ""
    try:
        apply_paths = resolve_canonical_f1_m9_productive_apply_ledger_paths_v1(repo_root=repo_root)
        threshold_paths = resolve_canonical_f1_m9_threshold_value_authorization_ledger_paths_v1(
            repo_root=repo_root
        )
    except F1M9DurableLedgerPathsError as exc:
        return None, str(exc)
    wiring_request = GovernedF1M9ThresholdConsumerWiringRequestV1(
        apply_ledger_paths=apply_paths,
        threshold_ledger_paths=threshold_paths,
        repo_root=repo_root,
    )
    seam = resolve_runtime_applied_seam_for_consumer_wiring_v1(wiring_request)
    if seam is None and allow_bootstrap:
        bootstrap = ensure_canonical_f1_m9_runtime_applied_seam_materialized_v1(
            repo_root=repo_root,
            apply_ledger_paths=apply_paths,
            threshold_ledger_paths=threshold_paths,
        )
        if bootstrap.status == "REJECTED":
            reason = (
                bootstrap.blocking_reasons[0]
                if bootstrap.blocking_reasons
                else "F1_M9_DURABLE_BOOTSTRAP_REJECTED"
            )
            return None, str(reason)
        seam = resolve_runtime_applied_seam_for_consumer_wiring_v1(wiring_request)
    if seam is None:
        return None, "RUNTIME_APPLIED_SEAM_UNAVAILABLE"
    return seam, ""


def ensure_hardened_bridge_session_governed_productive_parameter_seam_bound_v1(
    state: HardenedBridgeSessionStateV2,
    *,
    session_id: str,
    repo_root: Path | None = None,
    allow_bootstrap: bool = True,
) -> None:
    """Session-bind authorized productive parameter seam before F1/M9 consumer evaluation."""
    from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
        consumer_wiring_authorized_v1,
    )
    from src.governance.governed_productive_runtime_parameter_seam_session_bind_v1 import (
        STATUS_BOUND,
        bind_governed_authorized_productive_parameter_seam_to_hardened_bridge_session_v1,
        read_session_bound_seam_for_runtime_transport_v1,
    )

    root = repo_root or _REPO_ROOT
    if not consumer_wiring_authorized_v1(repo_root=root):
        return
    if read_session_bound_seam_for_runtime_transport_v1(state) is not None:
        return
    seam, fail_reason = _resolve_governed_seam_record_for_hardening_v2_session_bind_v1(
        repo_root=root, allow_bootstrap=allow_bootstrap
    )
    if seam is None:
        code = fail_reason or "GOVERNED_SEAM_RECORD_UNAVAILABLE"
        raise RuntimeError(f"HARDENING_V2_GOVERNED_SEAM_BIND_UNAVAILABLE:{code}")
    state, bind = bind_governed_authorized_productive_parameter_seam_to_hardened_bridge_session_v1(
        state,
        seam,
        session_id=session_id,
    )
    if bind.bind_status != STATUS_BOUND:
        raise RuntimeError(
            "HARDENING_V2_GOVERNED_SEAM_SESSION_BIND_DENIED:" + ":".join(bind.reason_codes)
        )


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
    ddo_capture_binding: DdoCaptureBindingV0 | None = None,
    ddo_repository_sha: str | None = None,
    offline_candidate: I17OfflineCandidateInputV2 | None = None,
    instrument_card_market: Any = None,
    instrument_card_budget: Any = None,
) -> dict[str, Any]:
    if instrument_card_market is not None:
        from src.ops.instrument_card_stream_v1 import validate_card_market_v1
        from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1

        bound = BoundInstrumentV1(
            instrument_id=state.instrument_id,
            venue_native_id=state.venue_instrument_id,
            ranking_snapshot_id="",
            ranking_integrity_digest="",
            universe_snapshot_id="",
            selection_id=session_id,
            selection_integrity_digest="",
            selection_state="SHADOW",
        )
        validate_card_market_v1(
            instrument_card_market,
            bound=bound,
            lane_id=instrument_card_market.slot.lane_id,
            now=event_ts_unix,
        )
        if mid_price != float(instrument_card_market.mark):
            raise ValueError("CARD_SHADOW_MARK_MISMATCH")
    if state.session_restart_policy != SESSION_RESTART_POLICY:
        raise RuntimeError("IMPLICIT_RESUME_FORBIDDEN")
    if state.session_id and state.session_id != session_id:
        raise RuntimeError("SESSION_ID_MUTATION_FORBIDDEN_NO_IMPLICIT_RESUME")
    if ddo_capture_binding is not None and ddo_repository_sha is None:
        raise ValueError("DDO_CAPTURE_REPOSITORY_SHA_REQUIRED")
    if offline_candidate is not None and (
        offline_candidate.material.instrument_id != state.instrument_id
        or offline_candidate.material.trading_epoch != state.trading_epoch
        or forced_actionable is not None
        or ddo_capture_binding is not None
        or state.decision_config_state_root is not None
        or state.typed_volatility_persistence_path is not None
        or state.max_age_research_evidence_ledger_path is not None
        or state.productive_evidence_accumulation_state is not None
    ):
        raise ValueError("I17_CANDIDATE_REQUIRES_ISOLATED_OFFLINE_CYCLE")
    if offline_candidate is not None:
        identity = offline_candidate.observation.observation_identity
        if (
            price_basis is None
            or identity is None
            or identity.venue_event_time != price_basis.event_ts_unix
            or identity.mark_price != mid_price
            or identity.mark_price != price_basis.mid_price
        ):
            raise ValueError("I17_CANDIDATE_MARK_OBSERVATION_MISMATCH")
    state.session_id = session_id
    ensure_hardened_bridge_session_governed_productive_parameter_seam_bound_v1(
        state,
        session_id=session_id,
        allow_bootstrap=offline_candidate is None,
    )
    state.cycle_index += 1
    state.append_mid(mid_price)
    cycle_id = make_scoped_id("cycle", session_id, state.cycle_index)

    # Capability 6.3 / G07 residual closeout: bind Cap-6.3 typed decision config before alpha.
    ensure_host_decision_config_binding_v1(
        state.decision_config_binding,
        repository_sha=str(
            state.decision_config_repository_sha or _HARDENING_V2_DECISION_CONFIG_REPOSITORY_SHA
        ),
        state_root=(
            Path(state.decision_config_state_root) if state.decision_config_state_root else None
        ),
        persist=bool(state.decision_config_state_root),
    )
    if state.decision_config_binding.alpha_blocked:
        raise RuntimeError(
            "DECISION_CONFIG_ALPHA_BLOCKED:" + state.decision_config_binding.alpha_block_reason
        )
    decision_cfg = require_bound_decision_config_v1(state.decision_config_binding)

    basis = price_basis or build_explicit_mid_price_basis_v2(
        mid_price=float(mid_price),
        event_ts_unix=float(event_ts_unix),
        receive_ts_unix=float(event_ts_unix),
    )
    card_closes = None
    if instrument_card_market is not None:
        from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
            extract_finalized_candle_closes_v1,
        )

        card_closes, _ = extract_finalized_candle_closes_v1(instrument_card_market.candles_payload)
    features = compute_feature_regime_from_mid_prices_v2(
        state.mid_prices if card_closes is None else card_closes
    )
    metrics0 = state.portfolio.economic_metrics()
    has_open_position, position_side, entry_price = _portfolio_position_fields_v2(state)

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
    if offline_candidate is not None:
        config_digest = hashlib.sha256(
            json.dumps(
                {
                    "bridge_config_digest": config_digest,
                    "artifact_digest": offline_candidate.artifact_digest,
                    "parameters_digest": offline_candidate.material.strategy_params_digest,
                    "strategy_version": offline_candidate.material.strategy_version,
                    "entry": asdict(offline_candidate.entry),
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()
    if state.config_digest and state.config_digest != config_digest:
        raise RuntimeError(f"CONFIG_DRIFT:{state.config_digest}:{config_digest}")
    state.config_digest = config_digest

    price_path = (
        tuple(state.mid_prices[-FEATURE_WINDOW_MIN:]) if card_closes is None else tuple(card_closes)
    )
    if len(price_path) < 2:
        price_path = (float(mid_price), float(mid_price))

    mark = (
        float(features.mark_price or basis.mid_price)
        if instrument_card_market is None
        else float(instrument_card_market.mark)
    )
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

    if offline_candidate is not None:
        input_digest = hashlib.sha256(
            json.dumps(
                {
                    "bridge_input_digest": input_digest,
                    "strategy_material_digest": offline_candidate.material.material_digest,
                    "market_observation": offline_candidate.observation.to_dict(),
                },
                sort_keys=True,
            ).encode()
        ).hexdigest()

    market_context = with_computed_input_digest(
        CanonicalMarketContextV1(
            context_id=f"ctx-{state.instrument_id}-epoch{state.trading_epoch}-hardening-v2",
            instrument_id=state.instrument_id,
            market_type=FuturesMarketType.PERPETUAL
            if instrument_card_market is None
            else FuturesMarketType.FUTURES,
            trading_epoch=state.trading_epoch,
            market_event_time=_iso_now(
                event_ts_unix
                if instrument_card_market is None
                else instrument_card_market.market_event_unix
            ),
            decision_time=_iso_now(event_ts_unix + 0.001),
            bar_interval="tick" if instrument_card_market is None else "1m",
            bar_finality_status=BarFinalityStatus.FINALIZED,
            mark_price=mark,
            index_price=mark
            if instrument_card_market is None
            else float(instrument_card_market.index_payload["data"][0]["idxPx"]),
            best_bid=basis.best_bid,
            best_ask=basis.best_ask,
            spread=basis.spread,
            volume=1_000_000.0
            if instrument_card_market is None
            else float(instrument_card_market.volume_contracts),
            open_interest=50_000_000.0
            if instrument_card_market is None
            else float(instrument_card_market.oi_contracts),
            funding_rate=0.0001
            if instrument_card_market is None
            else float(instrument_card_market.funding_rate),
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
        venue_instrument_id=state.venue_instrument_id,
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
    from src.governance.current_productive_activation_policy_v1 import (
        RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
    )
    from src.governance.f1_m9_productive_runtime_threshold_consumer_wiring_v1 import (
        consumer_wiring_authorized_v1,
        evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1,
    )

    require_governed_seam = consumer_wiring_authorized_v1()
    consumer_path = evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1(
        market_context=market_context,
        eligibility=typed_binding.typed_binding_eligibility,
        reuse_status=binding_reuse,
        restart_status=binding_restart,
        governed_seam_record=state.governed_authorized_productive_parameter_seam_record,
        require_governed_seam=require_governed_seam,
        runtime_surface=RUNTIME_SURFACE_F1_M9_HARDENING_V2_BRIDGE,
    )
    presence_gate = consumer_path.presence_gate
    if presence_gate is None:
        codes = consumer_path.reason_codes or (
            "PRODUCTIVE_THRESHOLD_CONSUMER_PRESENCE_GATE_UNAVAILABLE",
        )
        raise RuntimeError(f"F1_M9_THRESHOLD_CONSUMER_PATH_DENIED:{':'.join(codes)}")
    state.last_f1_m9_threshold_consumer_wiring = consumer_path.to_dict()

    # Window completeness ≠ regime acceptance. Keep features.ok / unclassified separate.
    required_window_complete = derive_required_window_complete_v2(
        warmup_complete=features.warmup_complete,
        features_ok=features.ok,
    )

    layer_c_event_distances = resolve_layer_c_event_distances_from_canonical_market_context_v1(
        market_context
    )
    if not layer_c_event_distances.ok:
        codes = tuple(layer_c_event_distances.failure_codes or ())
        if codes == ("volatility_non_positive",):
            layer_c_vol = _resolve_hardening_v2_layer_c_volatility_estimate_v1(
                float(features.volatility_estimate)
            )
            layer_c_event_distances = resolve_layer_c_event_distances_from_mark_and_volatility_v1(
                mark_price=float(market_context.mark_price),
                volatility_estimate=layer_c_vol,
            )
    if not layer_c_event_distances.ok:
        codes = ":".join(layer_c_event_distances.failure_codes or ("layer_c_binding_failed",))
        raise RuntimeError(f"LAYER_C_EVENT_DISTANCE_BINDING_FAILED:{codes}")
    cycle_up_distance = float(layer_c_event_distances.up_distance)
    cycle_adverse_exit_distance = float(layer_c_event_distances.adverse_exit_distance)
    cycle_reversal_distance = float(layer_c_event_distances.reversal_distance)

    ensure_host_exit_policy_binding_v1(
        state.exit_policy_binding,
        instrument_id=state.instrument_id,
        repository_sha=str(
            state.decision_config_repository_sha or _HARDENING_V2_DECISION_CONFIG_REPOSITORY_SHA
        ),
        config_digest=layer_c_derived_exit_policy_adverse_config_digest_v1(
            profit_protection_distance=float(FROZEN_PROFIT_PROTECTION_DISTANCE),
        ),
        state_root=None,
    )
    _exit_bundle, exit_signals, _exit_safety_mode, _exit_trading_gate = (
        evaluate_host_exit_policy_producers_v1(
            state.exit_policy_binding,
            mark_price=float(features.mark_price or basis.mid_price)
            if instrument_card_market is None
            else mark,
            event_ts_unix=float(event_ts_unix),
            observation_digest="",
            has_open_position=has_open_position,
            existing_position_side=position_side,
            entry_price=entry_price,
            entry_event_time=(
                float(state.exit_policy_binding.entry_event_time)
                if state.exit_policy_binding.entry_event_time is not None
                else float(event_ts_unix)
                if has_open_position
                else None
            ),
            entry_trading_epoch=(
                int(state.exit_policy_binding.entry_trading_epoch)
                if state.exit_policy_binding.entry_trading_epoch is not None
                else int(state.trading_epoch)
                if has_open_position
                else None
            ),
            data_integrity_trusted=True,
            adverse_exit_distance=cycle_adverse_exit_distance,
            separate_scope_adverse_exit=False,
            profit_protection_distance=float(FROZEN_PROFIT_PROTECTION_DISTANCE),
            killstate_active=bool(state.killstate_active),
            killstate_trigger=str(state.killstate_trigger or ""),
            warmup_complete=bool(features.warmup_complete),
            regime_ok=bool(features.ok),
            price_basis_ok=bool(basis.mid_price > 0),
            max_drawdown=float(metrics0.drawdown),
        )
    )
    _ = (_exit_safety_mode, _exit_trading_gate)
    safety = _safety_evaluation_from_cap65_bundle_v2(_exit_bundle)

    effective_trading_gate = safety.trading_gate_enum
    if not consumer_path.alpha_scope_entry_authority_allowed:
        effective_trading_gate = demote_trading_gate_for_typed_presence_failure_v1(
            safety.trading_gate_enum
        )
    if instrument_card_market is not None and (
        not instrument_card_budget
        or instrument_card_budget.get("status") != "BOUND"
        or Decimal(instrument_card_budget["available_for_new_entry"]) <= 0
        or not any(
            instrument_card_market.assess_opening_liquidity_v1(side=side)["risk_admitted"]
            for side in ("BUY", "SELL")
        )
    ):
        # New exposure needs current slot capital and executable native depth.
        # Preserve a stronger existing Safety gate and all original state owners.
        if effective_trading_gate not in (TradingGate.BLOCKED, TradingGate.EXIT_ONLY):
            effective_trading_gate = TradingGate.EXIT_ONLY

    decision_id = make_scoped_id("decision", session_id, cycle_id, state.trading_epoch)
    risk_decision_id = make_scoped_id("risk", decision_id, safety.safety_result)
    intent_id = make_scoped_id("intent", risk_decision_id, features.feature_digest)

    confirmation_inputs = {}
    if offline_candidate is not None:
        observation = offline_candidate.observation
        bound = observation.state_before.bound_instrument_key
        assert bound is not None  # checked by I17OfflineCandidateInputV2
        confirmation_inputs = {
            "observation_acceptance_result": observation,
            "directional_confirmation_progress": state.offline_confirmation_progress,
            "confirmation_progress_session_id": session_id,
            "confirmation_progress_venue": bound.venue,
            "confirmation_progress_instrument": bound,
        }
    replay_input = build_integrated_offline_replay_input_v1(
        replay_id=f"{session_id}-{cycle_id}",
        instrument_id=state.instrument_id,
        trading_epoch=state.trading_epoch,
        canonical_market_context=market_context,
        market_context_binding_state=CanonicalMarketContextBindingStateV1(),
        scope_prerequisites=ScopeInitializationPrerequisitesV1(
            required_window_complete=required_window_complete,
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
        up_distance=cycle_up_distance,
        adverse_exit_distance=cycle_adverse_exit_distance,
        reversal_distance=cycle_reversal_distance,
        confirmation_epochs=int(decision_cfg.confirmation_epochs),
        current_price=mark,
        price_path=price_path,
        directional_confirmation_state=DirectionalConfirmationStateV1(
            candidate_count=1 if features.ok else 0,
            last_evaluated_trading_epoch=state.last_evaluated_trading_epoch,
            last_signal_strength=float(features.momentum_features.get("roc", 0.0)),
        ),
        strategy_registry=(
            _strategy_registry()
            if offline_candidate is None
            else SuitabilityStrategyRegistryV1(entries=(offline_candidate.entry,))
        ),
        strategy_suitability_agreement_material=(
            None if offline_candidate is None else offline_candidate.material
        ),
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
        scope_adverse_exit_signal=exit_signals["scope_adverse_exit_signal"],
        profit_protection_signal=exit_signals["profit_protection_signal"],
        time_exit_signal=exit_signals["time_exit_signal"],
        strategy_invalidation_signal=exit_signals["strategy_invalidation_signal"],
        hard_risk_reduction_signal=exit_signals["hard_risk_reduction_signal"],
        safety_exit_signal=exit_signals["safety_exit_signal"],
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
        governed_authorized_productive_parameter_seam_record=(
            state.governed_authorized_productive_parameter_seam_record
        ),
        **confirmation_inputs,
    )

    if instrument_card_market is not None:
        from src.ops.instrument_card_input_observation_v1 import record_instrument_card_input_v1

        record_instrument_card_input_v1(replay_input)
    ddo_capture = None
    if ddo_capture_binding is not None and ddo_repository_sha is not None:
        # The full-core package also imports the wallclock entrypoint during startup.
        from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_ddo_learning_capture_join_v1 import (
            run_integrated_offline_replay_with_productive_ddo_capture_v1,
        )

        replay, ddo_capture = run_integrated_offline_replay_with_productive_ddo_capture_v1(
            replay_input,
            ddo_capture_binding=ddo_capture_binding,
            repository_sha=ddo_repository_sha,
            session_id=session_id,
            cycle_index=state.cycle_index,
            event_ts_unix=event_ts_unix,
            observation_acceptance_result=None,
            features=features,
            confirmation_binding=None,
        )
    else:
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
        intended_dict = apply_hardening_v2_downstream_new_exposure_guard_v2(
            intended,
            producer_safety_result=str(safety.safety_result),
            warmup_complete=bool(features.warmup_complete),
        )

    before_hash = portfolio_state_hash(state.portfolio.snapshot())
    fill_id = None
    fill_dict = None
    side = str(intended_dict["intended_side"])
    qty = Decimal(str(intended_dict["intended_quantity"]))
    card_execution_check = None
    new_exposure = False
    if instrument_card_market is not None and side in {"BUY", "SELL"} and qty > 0:
        position = (
            state.portfolio.snapshot()
            .get("state", {})
            .get("positions", {})
            .get(state.instrument_id, {})
        )
        current_base = Decimal(str(position.get("quantity", "0")))
        target_base = current_base + (qty if side == "BUY" else -qty)
        new_exposure = abs(target_base) > abs(current_base) or current_base * target_base < 0
    if instrument_card_market is not None and side in {"BUY", "SELL"} and qty > 0 and new_exposure:
        # This legacy analytical portfolio counts base units, not native
        # contracts. Never reinterpret its amount as a native order quantity.
        # The original replay decision remains intact; incompatible analytical
        # execution is held at this consumer boundary.
        from src.ops.instrument_card_budget_assessment_v1 import assess_instrument_budget_v1

        try:
            card_execution_check = assess_instrument_budget_v1(
                market=instrument_card_market,
                available_usdc=instrument_card_budget["available_for_new_entry"],
                side=side,
                quantity_contracts=qty / instrument_card_market.native_contract.contract_size,
            )
        except (ValueError, ArithmeticError) as exc:
            card_execution_check = {"measurement_admitted": False, "reason_codes": [str(exc)]}
        if not card_execution_check["measurement_admitted"]:
            intended_dict = {
                **intended_dict,
                "intended_side": "HOLD",
                "intended_quantity": "0",
                "reason_codes": [
                    *intended_dict["reason_codes"],
                    "CARD_EXACT_QUANTITY_NOT_ADMITTED",
                ],
            }
            side, qty = "HOLD", Decimal(0)
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
        # Diagnostic only: no decision/config/persistence/timing effect.
        "mid_prices_len": len(state.mid_prices),
        "feature_window_min": int(FEATURE_WINDOW_MIN),
        "required_window_complete": bool(required_window_complete),
        "required_window_complete_inputs": {
            "warmup_complete": bool(features.warmup_complete),
            "features_ok": bool(features.ok),
        },
        "regime_id": str(features.regime_id),
        "feature_blockers": list(features.blockers),
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
        "bridge_safety_role": BRIDGE_SAFETY_ROLE,
        "canonical_replay_safety_owner": CANONICAL_REPLAY_SAFETY_OWNER,
        "cap65_exit_producers": _exit_bundle.to_dict(),
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
        **(
            {"instrument_card_execution_check": card_execution_check}
            if instrument_card_market is not None
            else {}
        ),
        "fill": fill_dict,
        "portfolio_state_before_hash": before_hash,
        "portfolio_state_after_hash": after_hash,
        "portfolio_snapshot": dict(state.portfolio.snapshot()),
        "economic_metrics": econ,
        "reason_codes": list(replay.evidence.reason_codes),
        "blockers": list(features.blockers),
        "call_graph": list(CALL_GRAPH_V2),
        # Cap6.3 numeric fields: LEGACY_FROZEN_CONFIG_EVIDENCE in cycle payload — not Layer-C runtime authority.
        "decision_config_binding": {
            "initialized": bool(state.decision_config_binding.initialized),
            "config_version": str(decision_cfg.config_version),
            "schema_version": str(decision_cfg.schema_version),
            "config_digest": str(decision_cfg.config_digest()),
            "confirmation_epochs": int(decision_cfg.confirmation_epochs),
            "up_distance": float(decision_cfg.up_distance),
            "adverse_exit_distance": float(decision_cfg.adverse_exit_distance),
            "reversal_distance": float(decision_cfg.reversal_distance),
            "owner": str(decision_cfg.owner),
        },
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
            "BRIDGE_SAFETY_INPUT_PRODUCER_ONLY",
            "AI_LAYER_NON_AUTHORITY",
        ],
    }
    if offline_candidate is not None:
        cycle["offline_candidate"] = _candidate_receipt(offline_candidate, replay)
        seam = state.governed_authorized_productive_parameter_seam_record or {}
        cycle["offline_candidate"]["governed_seam_digest"] = seam.get("seam_digest")
        if replay.intermediate is not None:
            original_intent = replay.intermediate.canonical_order_intent
            if original_intent is not None:
                cycle["offline_candidate_canonical_order_intent"] = {
                    **canonical_order_intent_to_semantic_dict(original_intent),
                    "semantic_digest": original_intent.semantic_digest,
                }
            progress = replay.intermediate.directional_confirmation_progress_after
            if progress is not None:
                state.offline_confirmation_progress = progress
    if ddo_capture is not None:
        ddo_capture["cycle_id"] = ddo_capture_binding.capture_cycle_id
        ddo_capture["unpersisted_record_count"] = len(
            set(ddo_capture_binding.captured_ids) - set(ddo_capture_binding.persisted_ids)
        )
        cycle["ddo_capture"] = ddo_capture
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
                venue_instrument_id=state.venue_instrument_id,
                receive_time=receive_time,
                market_sample=sample_for_id.to_dict(),
            )
            m9_obs_ledger = (
                acc_state.productive_ledger_path.parents[1]
                / "m9_s1_durable_market_session_evidence_accumulation_v1"
                / "market_session_observations.jsonl"
            )
            cycle["productive_research_evidence_accumulation"] = (
                passive_accumulate_from_bridge_cycle_v1(
                    cycle,
                    state=acc_state,
                    source_class=ObservationSourceClassV1.SHADOW_OBSERVED,
                    m9_s1_observation_ledger_path=m9_obs_ledger,
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
