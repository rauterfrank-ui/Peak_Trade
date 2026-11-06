from __future__ import annotations

import hashlib
from typing import Tuple

from research.multi_future_ghv_counterfactual_distance_lab_v2.cmc_builder_v2 import build_finalized_cmc_v2
from trading.master_v2.canonical_market_context_v1 import CanonicalMarketContextBindingStateV1
from trading.master_v2.canonical_scope_initialization_v1 import (
    CanonicalScopeInitializationPolicyV1,
    ScopeInitializationPrerequisitesV1,
    ScopeReinitializationGuardV1,
    SCOPE_INITIALIZATION_POLICY_VERSION,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
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

_CANONICAL_INSTRUMENT = "inst-eth-usdt-perp"


def default_policies_v2() -> IntegratedOfflineReplayPoliciesV1:
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


def component_versions_v2() -> dict[str, str]:
    return {"integrated_offline_trading_logic_replay": INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION}


def build_integrated_replay_input_v2(
    *,
    replay_id: str,
    instrument_id: str,
    mark_price: float,
    volatility_estimate: float,
    price_path: Tuple[float, ...],
    trading_epoch: int,
    side_state: SideState = SideState.LONG_ARMED,
    now_tick: int = 0,
    **overrides: object,
) -> IntegratedOfflineReplayInputV1:
    ctx = build_finalized_cmc_v2(
        instrument_id=instrument_id,
        mark_price=mark_price,
        volatility_estimate=volatility_estimate,
        trading_epoch=trading_epoch,
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
    base: dict = {
        "replay_id": replay_id,
        "instrument_id": instrument_id,
        "trading_epoch": trading_epoch,
        "canonical_market_context": ctx,
        "market_context_binding_state": CanonicalMarketContextBindingStateV1(),
        "scope_prerequisites": ScopeInitializationPrerequisitesV1(
            required_window_complete=True,
            instrument_metadata_valid=True,
            finalized_market_context=True,
        ),
        "scope_reinitialization_guard": ScopeReinitializationGuardV1(),
        "existing_scope": None,
        "scope_direction_state": ScopeDirectionState.LONG,
        "scope_confirmation_state": ScopeConfirmationStateV1(
            candidate_kind=None,
            candidate_count=1,
            last_evaluated_trading_epoch=trading_epoch - 1,
        ),
        "scope_cooldown_state": ScopeCooldownStateV1(
            active=False,
            remaining_epochs=0,
            policy_version=SCOPE_EVENT_GENERATOR_POLICY_VERSION,
        ),
        "up_distance": 200.0,
        "adverse_exit_distance": 80.0,
        "reversal_distance": 120.0,
        "confirmation_epochs": 2,
        "current_price": float(price_path[-1]),
        "price_path": price_path,
        "directional_confirmation_state": DirectionalConfirmationStateV1(
            candidate_count=1,
            last_evaluated_trading_epoch=trading_epoch - 1,
            last_signal_strength=0.02,
        ),
        "strategy_registry": registry,
        "regime_id": "trending",
        "regime_status": SuitabilityRegimeStatus.KNOWN,
        "previous_composition_direction_state": CompositionDirectionState.NEUTRAL,
        "position_management_context": PositionManagementContext.FLAT,
        "last_evaluated_trading_epoch": trading_epoch - 1,
        "side_state": side_state,
        "direction_state": EntryExitDirectionState.LONG_ARMED,
        "position_state": PositionState.FLAT_RECONCILED,
        "reconciliation_state": ReconciliationState.RECONCILED,
        "trading_gate": TradingGate.ENTRY_ALLOWED,
        "safety_mode": SafetyMode.NORMAL,
        "existing_position_side": ExistingPositionSide.NONE,
        "venue_flat": True,
        "cooldown_pass": True,
        "scope_adverse_exit_signal": PolicySignalV0(triggered=False),
        "profit_protection_signal": PolicySignalV0(triggered=False),
        "time_exit_signal": PolicySignalV0(triggered=False),
        "strategy_invalidation_signal": PolicySignalV0(triggered=False),
        "hard_risk_reduction_signal": PolicySignalV0(triggered=False),
        "safety_exit_signal": PolicySignalV0(triggered=False),
        "policies": default_policies_v2(),
        "component_versions": component_versions_v2(),
        "policy_versions": {"scope_event_generator": SCOPE_EVENT_GENERATOR_POLICY_VERSION},
        "config_digest": "c" * 64,
        "implementation_digest": "d" * 64,
        "input_digest": hashlib.sha256(replay_id.encode()).hexdigest(),
        "expected_component_contracts": component_versions_v2(),
        "context_reference": f"trading-context-epoch-{trading_epoch}",
        "now_tick": now_tick,
    }
    base.update(overrides)
    if instrument_id != _CANONICAL_INSTRUMENT:
        base["instrument_id"] = instrument_id
    return IntegratedOfflineReplayInputV1(**base)
