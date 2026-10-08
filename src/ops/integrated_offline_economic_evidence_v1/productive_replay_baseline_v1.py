"""Deterministic productive replay baseline input (B2+ completion). AUTHORITY=NONE."""

from __future__ import annotations

import hashlib

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
    ScopeInitializationPrerequisitesV1,
    ScopeReinitializationGuardV1,
    SCOPE_INITIALIZATION_POLICY_VERSION,
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
    IntegratedOfflineReplayInputV1,
    IntegratedOfflineReplayPoliciesV1,
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

CANONICAL_INSTRUMENT_ID = "ETH-USD_UM_XPERP-310404"
REPLAY_INSTRUMENT_ID = "inst-eth-usdt-perp"
BASELINE_EPOCH = 44
BASELINE_CONFIG_DIGEST = hashlib.sha256(b"productive-offline-economic-config-v1").hexdigest()
BASELINE_IMPL_BINDING_DIGEST = hashlib.sha256(
    b"productive-offline-economic-impl-bind-v1"
).hexdigest()
BASELINE_REGISTRY_SNAPSHOT_DIGEST = hashlib.sha256(
    b"productive-offline-economic-registry-v1"
).hexdigest()


def build_productive_replay_baseline_input_v1(
    *,
    trading_epoch: int = BASELINE_EPOCH,
    current_price: float = 3570.0,
) -> IntegratedOfflineReplayInputV1:
    ctx = with_computed_input_digest(
        CanonicalMarketContextV1(
            context_id=f"ctx-productive-offline-{trading_epoch}",
            instrument_id=REPLAY_INSTRUMENT_ID,
            market_type=FuturesMarketType.PERPETUAL,
            trading_epoch=trading_epoch,
            market_event_time="2026-06-30T12:00:00+00:00",
            decision_time="2026-06-30T12:00:01+00:00",
            bar_interval="1m",
            bar_finality_status=BarFinalityStatus.FINALIZED,
            mark_price=current_price,
            index_price=current_price - 0.5,
            best_bid=current_price - 0.2,
            best_ask=current_price + 0.2,
            spread=0.4,
            volume=1_250_000.0,
            open_interest=85_000_000.0,
            funding_rate=0.00012,
            volatility_estimate=0.38,
            trend_feature_set={"slope": 0.02, "strength": 0.71},
            momentum_feature_set={"rsi": 55.0, "roc": 0.015},
            liquidity_feature_set={"depth_score": 0.88},
            market_structure_feature_set={"range_ratio": 0.42},
            data_integrity_status=DataIntegrityStatus.TRUSTED,
            clock_trust_status=ClockTrustStatus.TRUSTED,
            warmup_status=WarmupStatus.WARMUP_COMPLETE,
            feature_contract_version=FEATURE_CONTRACT_VERSION,
            input_digest="",
        )
    )
    registry = SuitabilityStrategyRegistryV1(
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
    component_versions = {
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
    policy_versions = {
        "scope_initialization": SCOPE_INITIALIZATION_POLICY_VERSION,
        "scope_event_generator": SCOPE_EVENT_GENERATOR_POLICY_VERSION,
        "directional": DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
        "survival": SURVIVAL_ASSESSMENT_POLICY_VERSION,
        "suitability": SUITABILITY_RANKING_POLICY_VERSION,
        "composition": DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
        "entry_exit": ENTRY_EXIT_POLICY_VERSION,
    }
    return IntegratedOfflineReplayInputV1(
        replay_id=f"productive-offline-replay-{trading_epoch}",
        instrument_id=REPLAY_INSTRUMENT_ID,
        trading_epoch=trading_epoch,
        canonical_market_context=ctx,
        market_context_binding_state=CanonicalMarketContextBindingStateV1(),
        scope_prerequisites=ScopeInitializationPrerequisitesV1(
            required_window_complete=True,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
        scope_reinitialization_guard=ScopeReinitializationGuardV1(),
        existing_scope=None,
        scope_direction_state=ScopeDirectionState.LONG,
        scope_confirmation_state=ScopeConfirmationStateV1(
            candidate_kind=None,
            candidate_count=1,
            last_evaluated_trading_epoch=trading_epoch - 1,
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
        current_price=current_price,
        price_path=(3500.0, current_price),
        directional_confirmation_state=DirectionalConfirmationStateV1(
            candidate_count=1,
            last_evaluated_trading_epoch=trading_epoch - 1,
            last_signal_strength=0.02,
        ),
        strategy_registry=registry,
        registry_snapshot_digest=BASELINE_REGISTRY_SNAPSHOT_DIGEST,
        regime_id="trending",
        regime_status=SuitabilityRegimeStatus.KNOWN,
        previous_composition_direction_state=CompositionDirectionState.NEUTRAL,
        position_management_context=PositionManagementContext.FLAT,
        last_evaluated_trading_epoch=trading_epoch - 1,
        side_state=SideState.LONG_ARMED,
        direction_state=EntryExitDirectionState.LONG_ARMED,
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
        policies=IntegratedOfflineReplayPoliciesV1(
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
        ),
        component_versions=component_versions,
        policy_versions=policy_versions,
        config_digest=BASELINE_CONFIG_DIGEST,
        implementation_digest=BASELINE_IMPL_BINDING_DIGEST,
        input_digest=hashlib.sha256(b"productive-offline-replay-input-v1").hexdigest(),
        expected_component_contracts=component_versions,
        context_reference=f"trading-context-epoch-{trading_epoch}",
        now_tick=0,
    )
