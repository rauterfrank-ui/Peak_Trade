# src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py
"""
Integrated Offline Trading Logic Replay v1: pure orchestrator for STEP 29B–29H chain.

Orchestrates canonical component owners without duplicating component logic.
No I/O, runtime, orders, adapter, quantity, or authority effects.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import re
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Mapping, Optional, Tuple

from trading.master_v2.canonical_market_context_v1 import (
    CANONICAL_MARKET_CONTEXT_LAYER_VERSION,
    CanonicalMarketContextBindingOutcome,
    CanonicalMarketContextBindingStateV1,
    CanonicalMarketContextV1,
    bind_canonical_market_context_event,
    with_computed_input_digest,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    CANONICAL_SCOPE_INITIALIZATION_LAYER_VERSION,
    CanonicalScopeInitializationPolicyV1,
    CanonicalScopeInitializationResultV1,
    CanonicalScopeSnapshotV1,
    ScopeInitializationPrerequisitesV1,
    ScopeReinitializationGuardV1,
    initialize_canonical_scope,
)
from src.governance.capital_risk_sizing_v1 import CapitalRiskSizingDecisionV1
from src.governance.canonical_order_intent_v1 import CanonicalOrderIntentV1
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CANONICAL_TRADING_DECISION_EVIDENCE_LAYER_VERSION,
    CanonicalTradingDecisionEvidenceV1,
    derive_decision_id,
    with_computed_evidence_semantic_digest,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    DETERMINISTIC_SCOPE_EVENT_GENERATOR_LAYER_VERSION,
    CanonicalScopeEventType,
    ScopeConfirmationStateV1,
    ScopeCooldownStateV1,
    ScopeDirectionState,
    ScopeEventEvidenceV1,
    ScopeEventGeneratorInputV1,
    ScopeEventGeneratorPolicyV1,
    generate_deterministic_scope_event,
    with_computed_scope_event_digest,
)
from trading.master_v2.directional_assessment_v1 import (
    DIRECTIONAL_ASSESSMENT_LAYER_VERSION,
    DirectionalAssessmentInputV1,
    DirectionalAssessmentPolicyV1,
    DirectionalAssessmentSide,
    DirectionalAssessmentV1,
    DirectionalConfirmationStateV1,
    ScopeEventRefV1,
    evaluate_directional_assessment_v1,
    with_computed_directional_assessment_digest,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    DOUBLE_PLAY_COMPOSITION_MATRIX_LAYER_VERSION,
    CompositionDirectionState,
    CompositionSelectedSide,
    DoublePlayCompositionInputV1,
    DoublePlayCompositionPolicyV1,
    DoublePlayCompositionResultV1,
    PositionManagementContext,
    compute_composition_input_digest,
    evaluate_double_play_composition_matrix_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    ENTRY_EXIT_POLICY_LAYER_VERSION,
    DecisionOutcome,
    DoublePlayEntryExitPolicyInputV0,
    DoublePlayEntryExitPolicyV0,
    EntryExitDirectionState,
    EntryExitPolicyDecisionV0,
    ExistingPositionSide,
    PolicySignalV0,
    PositionState,
    ReconciliationState,
    SafetyMode,
    TradingGate,
    compute_entry_exit_policy_input_digest,
    evaluate_double_play_entry_exit_policy_v0,
)
from trading.master_v2.double_play_state import (
    DOUBLE_PLAY_STATE_LAYER_VERSION,
    ActiveSide,
    DynamicScopeRules,
    RuntimeEnvelope,
    RuntimeScopeState,
    ScopeEvent,
    SideState,
    StaticHardLimits,
    TransitionDecision,
    derive_active_side,
    transition_state,
    update_dynamic_boundaries,
)
from trading.master_v2.reversal_preparation_scenario_binding_adapter_v0 import (
    derive_reversal_preparation_position_context_v0,
    is_reversal_preparation_composition_v0,
    project_composition_for_reversal_preparation_entry_exit_v0,
)
from trading.master_v2.scope_event_generator_scenario_binding_adapter_v0 import (
    derive_scope_adverse_exit_signal_v0,
)
from trading.master_v2.suitability_binding_v1 import (
    SUITABILITY_BINDING_LAYER_VERSION,
    SuitabilityBindingInputV1,
    SuitabilityRankingPolicyV1,
    SuitabilityRegimeStatus,
    SuitabilityResultV1,
    SuitabilityStrategyRegistryV1,
    evaluate_suitability_binding_v1,
)
from trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategySuitabilityAgreementMaterialV1,
    fold_strategy_suitability_agreement_into_input_digest_v1,
)
from trading.master_v2.survival_assessment_v1 import (
    SURVIVAL_ASSESSMENT_LAYER_VERSION,
    SurvivalAssessmentInputV1,
    SurvivalAssessmentPolicyV1,
    SurvivalCostInputsV1,
    SurvivalMetricInputsV1,
    SurvivalResultV1,
    evaluate_survival_assessment_v1,
)

INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION = "v1"
INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1"
)

_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})

_DEFAULT_STATIC_LIMITS = StaticHardLimits(
    min_band_width=1.0,
    max_band_width=100.0,
)
_DEFAULT_RUNTIME_ENVELOPE = RuntimeEnvelope(static=_DEFAULT_STATIC_LIMITS, live_authorization=False)
_DEFAULT_SCOPE_RULES = DynamicScopeRules(
    min_band_width=1.0,
    max_band_width=50.0,
    min_switch_cooldown_ticks=0,
    max_switches_per_window=1_000_000,
    volatility_estimate=0.02,
)
# Seed template only — never fed into transition_state as per-cycle empty state.
_RUNTIME_SCOPE_SEED_TEMPLATE = RuntimeScopeState(
    anchor_price=0.0,
    current_downscope_boundary=0.0,
    current_upscope_boundary=0.0,
    current_hysteresis_band=0.0,
    last_switch_tick=-1_000_000,
    switches_in_window=0,
    window_start_tick=0,
    chop_latched=False,
    now_tick=0,
    last_completed_side_switch_tick=-1_000_000,
)

# CHOP remains NOT_BOUND in deterministic_scope_event_generator_v1 (no new heuristic).
CANONICAL_DYNAMIC_SCOPE_TRAILING_OWNER = "trading.master_v2.double_play_state.RuntimeScopeState"
CANONICAL_SCOPE_SNAPSHOT_IDENTITY_OWNER = (
    "trading.master_v2.canonical_scope_initialization_v1.CanonicalScopeSnapshotV1"
)
CHOP_BINDING_STATUS = "NOT_BOUND_FAIL_CLOSED_GAP"


@dataclass(frozen=True)
class IntegratedOfflineReplayPoliciesV1:
    scope_initialization: CanonicalScopeInitializationPolicyV1
    scope_event_generator: ScopeEventGeneratorPolicyV1
    directional: DirectionalAssessmentPolicyV1
    survival: SurvivalAssessmentPolicyV1
    suitability: SuitabilityRankingPolicyV1
    composition: DoublePlayCompositionPolicyV1
    entry_exit: DoublePlayEntryExitPolicyV0


@dataclass(frozen=True)
class IntegratedOfflineReplayInputV1:
    replay_id: str
    instrument_id: str
    trading_epoch: int
    canonical_market_context: CanonicalMarketContextV1
    market_context_binding_state: CanonicalMarketContextBindingStateV1
    scope_prerequisites: ScopeInitializationPrerequisitesV1
    scope_reinitialization_guard: ScopeReinitializationGuardV1
    existing_scope: Optional[CanonicalScopeSnapshotV1]
    scope_direction_state: ScopeDirectionState
    scope_confirmation_state: ScopeConfirmationStateV1
    scope_cooldown_state: ScopeCooldownStateV1
    up_distance: float
    adverse_exit_distance: float
    reversal_distance: float
    confirmation_epochs: int
    current_price: float
    price_path: Tuple[float, ...]
    directional_confirmation_state: DirectionalConfirmationStateV1
    strategy_registry: SuitabilityStrategyRegistryV1
    regime_id: str
    regime_status: SuitabilityRegimeStatus
    previous_composition_direction_state: CompositionDirectionState
    position_management_context: PositionManagementContext
    last_evaluated_trading_epoch: int
    side_state: SideState
    direction_state: EntryExitDirectionState
    position_state: PositionState
    reconciliation_state: ReconciliationState
    trading_gate: TradingGate
    safety_mode: SafetyMode
    existing_position_side: ExistingPositionSide
    venue_flat: bool
    cooldown_pass: bool
    scope_adverse_exit_signal: PolicySignalV0
    profit_protection_signal: PolicySignalV0
    time_exit_signal: PolicySignalV0
    strategy_invalidation_signal: PolicySignalV0
    hard_risk_reduction_signal: PolicySignalV0
    safety_exit_signal: PolicySignalV0
    policies: IntegratedOfflineReplayPoliciesV1
    component_versions: Mapping[str, str]
    policy_versions: Mapping[str, str]
    config_digest: str
    implementation_digest: str
    input_digest: str
    expected_component_contracts: Mapping[str, str]
    context_reference: str
    now_tick: int = 0
    strategy_suitability_agreement_material: Optional[StrategySuitabilityAgreementMaterialV1] = None
    # Trailing envelope carrier (SSOT for SCOPE(t)→SCOPE(t+1)); snapshot stays identity-only.
    runtime_scope_state: Optional[RuntimeScopeState] = None
    runtime_scope_bound_instrument_id: Optional[str] = None
    dynamic_scope_rules: Optional[DynamicScopeRules] = None
    explicit_runtime_scope_reset: bool = False


@dataclass(frozen=True)
class StateSwitchEvidenceV1:
    state_switch_id: str
    instrument_id: str
    trading_epoch: int
    previous_side_state: str
    next_side_state: str
    scope_event_type: str
    transition_allowed: bool
    transition_reason_code: str
    semantic_digest: str


@dataclass(frozen=True)
class IntegratedOfflineReplayIntermediateV1:
    market_context: CanonicalMarketContextV1
    scope_initialization: CanonicalScopeInitializationResultV1
    scope_event: ScopeEventEvidenceV1
    bull_assessment: DirectionalAssessmentV1
    bear_assessment: DirectionalAssessmentV1
    bull_survival: SurvivalResultV1
    bear_survival: SurvivalResultV1
    bull_suitability: SuitabilityResultV1
    bear_suitability: SuitabilityResultV1
    composition_result: DoublePlayCompositionResultV1
    entry_exit_decision: EntryExitPolicyDecisionV0
    capital_risk_sizing_decision: Optional[CapitalRiskSizingDecisionV1]
    canonical_order_intent: Optional[CanonicalOrderIntentV1]
    state_switch: StateSwitchEvidenceV1
    current_scope: CanonicalScopeSnapshotV1
    next_scope_ref: str
    runtime_scope_state_before: RuntimeScopeState
    runtime_scope_state_after: RuntimeScopeState
    runtime_scope_reinitialized: bool
    trailing_anchor_used: float
    chop_binding_status: str = CHOP_BINDING_STATUS


@dataclass(frozen=True)
class IntegratedOfflineReplayResultV1:
    replay_pass: bool
    fail_reasons: Tuple[str, ...]
    evidence: CanonicalTradingDecisionEvidenceV1
    intermediate: Optional[IntegratedOfflineReplayIntermediateV1] = None


def _valid_sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _builder_type_name_ok(value: object, *expected_type_names: str) -> bool:
    """Dual-import-safe class identity check (trading.* vs src.trading.*)."""
    return type(value).__name__ in expected_type_names


def _builder_enum_ok(value: object, enum_cls: type) -> bool:
    """Dual-import-safe enum membership by value (not class identity)."""
    try:
        return getattr(value, "value") in {member.value for member in enum_cls}
    except (AttributeError, TypeError):
        return False


def _builder_mapping_str_str_ok(value: object) -> bool:
    if not isinstance(value, Mapping):
        return False
    for key, item in value.items():
        if not isinstance(key, str) or not key:
            return False
        if not isinstance(item, str) or not item:
            return False
    return True


def _builder_finite_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return value == value and value not in (float("inf"), float("-inf"))


def build_integrated_offline_replay_input_v1(
    *,
    replay_id: str,
    instrument_id: str,
    trading_epoch: int,
    canonical_market_context: CanonicalMarketContextV1,
    market_context_binding_state: CanonicalMarketContextBindingStateV1,
    scope_prerequisites: ScopeInitializationPrerequisitesV1,
    scope_reinitialization_guard: ScopeReinitializationGuardV1,
    existing_scope: Optional[CanonicalScopeSnapshotV1],
    scope_direction_state: ScopeDirectionState,
    scope_confirmation_state: ScopeConfirmationStateV1,
    scope_cooldown_state: ScopeCooldownStateV1,
    up_distance: float,
    adverse_exit_distance: float,
    reversal_distance: float,
    confirmation_epochs: int,
    current_price: float,
    price_path: Tuple[float, ...],
    directional_confirmation_state: DirectionalConfirmationStateV1,
    strategy_registry: SuitabilityStrategyRegistryV1,
    regime_id: str,
    regime_status: SuitabilityRegimeStatus,
    previous_composition_direction_state: CompositionDirectionState,
    position_management_context: PositionManagementContext,
    last_evaluated_trading_epoch: int,
    side_state: SideState,
    direction_state: EntryExitDirectionState,
    position_state: PositionState,
    reconciliation_state: ReconciliationState,
    trading_gate: TradingGate,
    safety_mode: SafetyMode,
    existing_position_side: ExistingPositionSide,
    venue_flat: bool,
    cooldown_pass: bool,
    scope_adverse_exit_signal: PolicySignalV0,
    profit_protection_signal: PolicySignalV0,
    time_exit_signal: PolicySignalV0,
    strategy_invalidation_signal: PolicySignalV0,
    hard_risk_reduction_signal: PolicySignalV0,
    safety_exit_signal: PolicySignalV0,
    policies: IntegratedOfflineReplayPoliciesV1,
    component_versions: Mapping[str, str],
    policy_versions: Mapping[str, str],
    config_digest: str,
    implementation_digest: str,
    input_digest: str,
    expected_component_contracts: Mapping[str, str],
    context_reference: str,
    now_tick: int = 0,
    strategy_suitability_agreement_material: Optional[
        StrategySuitabilityAgreementMaterialV1
    ] = None,
    runtime_scope_state: Optional[RuntimeScopeState] = None,
    runtime_scope_bound_instrument_id: Optional[str] = None,
    dynamic_scope_rules: Optional[DynamicScopeRules] = None,
    explicit_runtime_scope_reset: bool = False,
) -> IntegratedOfflineReplayInputV1:
    """Single canonical productive constructor for IntegratedOfflineReplayInputV1.

    Source adapters must pass fully prepared field values. This builder validates
    contracts and constructs the dataclass exactly once. It does not invent
    source-specific defaults, policies, registries, digests, or distance/path values.
    """
    errors: list[str] = []

    if not isinstance(replay_id, str) or not replay_id.strip():
        errors.append("replay_id_invalid")
    if not isinstance(instrument_id, str) or not instrument_id.strip():
        errors.append("instrument_id_invalid")
    if not isinstance(trading_epoch, int) or isinstance(trading_epoch, bool):
        errors.append("trading_epoch_invalid")
    if not _builder_type_name_ok(canonical_market_context, "CanonicalMarketContextV1"):
        errors.append("canonical_market_context_type_invalid")
    else:
        ctx_instrument = getattr(canonical_market_context, "instrument_id", None)
        ctx_epoch = getattr(canonical_market_context, "trading_epoch", None)
        if instrument_id != ctx_instrument:
            errors.append("instrument_mismatch")
        if trading_epoch != ctx_epoch:
            errors.append("trading_epoch_mismatch")

    if not _builder_type_name_ok(
        market_context_binding_state, "CanonicalMarketContextBindingStateV1"
    ):
        errors.append("market_context_binding_state_type_invalid")
    if not _builder_type_name_ok(scope_prerequisites, "ScopeInitializationPrerequisitesV1"):
        errors.append("scope_prerequisites_type_invalid")
    if not _builder_type_name_ok(scope_reinitialization_guard, "ScopeReinitializationGuardV1"):
        errors.append("scope_reinitialization_guard_type_invalid")
    if existing_scope is not None and not _builder_type_name_ok(
        existing_scope, "CanonicalScopeSnapshotV1"
    ):
        errors.append("existing_scope_type_invalid")
    if not _builder_enum_ok(scope_direction_state, ScopeDirectionState):
        errors.append("scope_direction_state_invalid")
    if not _builder_type_name_ok(scope_confirmation_state, "ScopeConfirmationStateV1"):
        errors.append("scope_confirmation_state_type_invalid")
    if not _builder_type_name_ok(scope_cooldown_state, "ScopeCooldownStateV1"):
        errors.append("scope_cooldown_state_type_invalid")

    for name, distance in (
        ("up_distance", up_distance),
        ("adverse_exit_distance", adverse_exit_distance),
        ("reversal_distance", reversal_distance),
        ("current_price", current_price),
    ):
        if not _builder_finite_number(distance):
            errors.append(f"{name}_invalid")

    if not isinstance(confirmation_epochs, int) or isinstance(confirmation_epochs, bool):
        errors.append("confirmation_epochs_invalid")
    elif confirmation_epochs < 1:
        errors.append("confirmation_epochs_invalid")

    if not isinstance(price_path, tuple) or len(price_path) < 2:
        errors.append("price_path_invalid")
    else:
        if any(not _builder_finite_number(point) for point in price_path):
            errors.append("price_path_invalid")

    if not _builder_type_name_ok(directional_confirmation_state, "DirectionalConfirmationStateV1"):
        errors.append("directional_confirmation_state_type_invalid")
    if not _builder_type_name_ok(strategy_registry, "SuitabilityStrategyRegistryV1"):
        errors.append("strategy_registry_type_invalid")
    if not isinstance(regime_id, str) or not regime_id.strip():
        errors.append("regime_id_invalid")
    if not _builder_enum_ok(regime_status, SuitabilityRegimeStatus):
        errors.append("regime_status_invalid")
    if not _builder_enum_ok(previous_composition_direction_state, CompositionDirectionState):
        errors.append("previous_composition_direction_state_invalid")
    if not _builder_enum_ok(position_management_context, PositionManagementContext):
        errors.append("position_management_context_invalid")
    if not isinstance(last_evaluated_trading_epoch, int) or isinstance(
        last_evaluated_trading_epoch, bool
    ):
        errors.append("last_evaluated_trading_epoch_invalid")
    if not _builder_enum_ok(side_state, SideState):
        errors.append("side_state_invalid")
    if not _builder_enum_ok(direction_state, EntryExitDirectionState):
        errors.append("direction_state_invalid")
    if not _builder_enum_ok(position_state, PositionState):
        errors.append("position_state_invalid")
    if not _builder_enum_ok(reconciliation_state, ReconciliationState):
        errors.append("reconciliation_state_invalid")
    if not _builder_enum_ok(trading_gate, TradingGate):
        errors.append("trading_gate_invalid")
    if not _builder_enum_ok(safety_mode, SafetyMode):
        errors.append("safety_mode_invalid")
    if not _builder_enum_ok(existing_position_side, ExistingPositionSide):
        errors.append("existing_position_side_invalid")
    if not isinstance(venue_flat, bool):
        errors.append("venue_flat_invalid")
    if not isinstance(cooldown_pass, bool):
        errors.append("cooldown_pass_invalid")

    for name, signal in (
        ("scope_adverse_exit_signal", scope_adverse_exit_signal),
        ("profit_protection_signal", profit_protection_signal),
        ("time_exit_signal", time_exit_signal),
        ("strategy_invalidation_signal", strategy_invalidation_signal),
        ("hard_risk_reduction_signal", hard_risk_reduction_signal),
        ("safety_exit_signal", safety_exit_signal),
    ):
        if not _builder_type_name_ok(signal, "PolicySignalV0"):
            errors.append(f"{name}_type_invalid")

    if not _builder_type_name_ok(policies, "IntegratedOfflineReplayPoliciesV1"):
        errors.append("policies_type_invalid")
    if not _builder_mapping_str_str_ok(component_versions):
        errors.append("component_versions_invalid")
    if not _builder_mapping_str_str_ok(policy_versions):
        errors.append("policy_versions_invalid")
    if not _builder_mapping_str_str_ok(expected_component_contracts):
        errors.append("expected_component_contracts_invalid")
    else:
        for key, expected_version in expected_component_contracts.items():
            actual_version = (
                component_versions.get(key) if isinstance(component_versions, Mapping) else None
            )
            if actual_version != expected_version:
                errors.append(
                    f"component_version_mismatch:{key}:{actual_version}!={expected_version}"
                )

    if _builder_type_name_ok(policies, "IntegratedOfflineReplayPoliciesV1") and isinstance(
        policy_versions, Mapping
    ):
        policy_attr_map = {
            "scope_initialization": getattr(
                getattr(policies, "scope_initialization", None), "policy_version", None
            ),
            "scope_event_generator": getattr(
                getattr(policies, "scope_event_generator", None), "policy_version", None
            ),
            "directional": getattr(getattr(policies, "directional", None), "policy_version", None),
            "survival": getattr(getattr(policies, "survival", None), "policy_version", None),
            "suitability": getattr(getattr(policies, "suitability", None), "policy_version", None),
            "composition": getattr(getattr(policies, "composition", None), "policy_version", None),
            "entry_exit": getattr(getattr(policies, "entry_exit", None), "policy_version", None),
        }
        for key, expected_version in policy_versions.items():
            policy_attr = policy_attr_map.get(key)
            if policy_attr is not None and policy_attr != expected_version:
                errors.append(f"policy_version_mismatch:{key}:{policy_attr}!={expected_version}")

    for name, digest in (
        ("config_digest", config_digest),
        ("implementation_digest", implementation_digest),
        ("input_digest", input_digest),
    ):
        if not isinstance(digest, str):
            errors.append(f"{name}_invalid")
        elif digest and not _valid_sha256_hex(digest):
            errors.append(f"{name}_invalid")

    if not isinstance(context_reference, str) or not context_reference.strip():
        errors.append("context_reference_invalid")
    if not isinstance(now_tick, int) or isinstance(now_tick, bool) or now_tick < 0:
        errors.append("now_tick_invalid")

    if strategy_suitability_agreement_material is not None:
        if not _builder_type_name_ok(
            strategy_suitability_agreement_material,
            "StrategySuitabilityAgreementMaterialV1",
        ):
            errors.append("strategy_suitability_agreement_material_type_invalid")
        else:
            mat_instrument = getattr(strategy_suitability_agreement_material, "instrument_id", None)
            mat_epoch = getattr(strategy_suitability_agreement_material, "trading_epoch", None)
            if mat_instrument != instrument_id:
                errors.append("instrument_mismatch")
            if mat_epoch != trading_epoch:
                errors.append("trading_epoch_mismatch")

    if runtime_scope_state is not None and not _builder_type_name_ok(
        runtime_scope_state, "RuntimeScopeState"
    ):
        errors.append("runtime_scope_state_type_invalid")
    if runtime_scope_bound_instrument_id is not None and (
        not isinstance(runtime_scope_bound_instrument_id, str)
        or not runtime_scope_bound_instrument_id.strip()
    ):
        errors.append("runtime_scope_bound_instrument_id_invalid")
    if dynamic_scope_rules is not None and not _builder_type_name_ok(
        dynamic_scope_rules, "DynamicScopeRules"
    ):
        errors.append("dynamic_scope_rules_type_invalid")
    if not isinstance(explicit_runtime_scope_reset, bool):
        errors.append("explicit_runtime_scope_reset_invalid")

    if errors:
        raise ValueError(";".join(sorted(set(errors))))

    effective_input_digest = fold_strategy_suitability_agreement_into_input_digest_v1(
        input_digest,
        strategy_suitability_agreement_material,
    )

    return IntegratedOfflineReplayInputV1(
        replay_id=replay_id,
        instrument_id=instrument_id,
        trading_epoch=trading_epoch,
        canonical_market_context=canonical_market_context,
        market_context_binding_state=market_context_binding_state,
        scope_prerequisites=scope_prerequisites,
        scope_reinitialization_guard=scope_reinitialization_guard,
        existing_scope=existing_scope,
        scope_direction_state=scope_direction_state,
        scope_confirmation_state=scope_confirmation_state,
        scope_cooldown_state=scope_cooldown_state,
        up_distance=up_distance,
        adverse_exit_distance=adverse_exit_distance,
        reversal_distance=reversal_distance,
        confirmation_epochs=confirmation_epochs,
        current_price=current_price,
        price_path=price_path,
        directional_confirmation_state=directional_confirmation_state,
        strategy_registry=strategy_registry,
        regime_id=regime_id,
        regime_status=regime_status,
        previous_composition_direction_state=previous_composition_direction_state,
        position_management_context=position_management_context,
        last_evaluated_trading_epoch=last_evaluated_trading_epoch,
        side_state=side_state,
        direction_state=direction_state,
        position_state=position_state,
        reconciliation_state=reconciliation_state,
        trading_gate=trading_gate,
        safety_mode=safety_mode,
        existing_position_side=existing_position_side,
        venue_flat=venue_flat,
        cooldown_pass=cooldown_pass,
        scope_adverse_exit_signal=scope_adverse_exit_signal,
        profit_protection_signal=profit_protection_signal,
        time_exit_signal=time_exit_signal,
        strategy_invalidation_signal=strategy_invalidation_signal,
        hard_risk_reduction_signal=hard_risk_reduction_signal,
        safety_exit_signal=safety_exit_signal,
        policies=policies,
        component_versions=component_versions,
        policy_versions=policy_versions,
        config_digest=config_digest,
        implementation_digest=implementation_digest,
        input_digest=effective_input_digest,
        expected_component_contracts=expected_component_contracts,
        context_reference=context_reference,
        now_tick=now_tick,
        strategy_suitability_agreement_material=strategy_suitability_agreement_material,
        runtime_scope_state=runtime_scope_state,
        runtime_scope_bound_instrument_id=runtime_scope_bound_instrument_id,
        dynamic_scope_rules=dynamic_scope_rules,
        explicit_runtime_scope_reset=bool(explicit_runtime_scope_reset),
    )


def _instrument_allowed(instrument_id: str) -> bool:
    lowered = instrument_id.lower()
    return not any(token in lowered for token in _FORBIDDEN_INSTRUMENT_SUBSTRINGS)


def _canonical_scope_event_to_scope_event(event_type: CanonicalScopeEventType) -> ScopeEvent:
    mapping = {
        CanonicalScopeEventType.NOOP: ScopeEvent.NOOP,
        CanonicalScopeEventType.UPSCOPE_CANDIDATE: ScopeEvent.UPSCOPE_CANDIDATE,
        CanonicalScopeEventType.UPSCOPE_CONFIRMED: ScopeEvent.UPSCOPE_CONFIRMED,
        CanonicalScopeEventType.DOWNSCOPE_CANDIDATE: ScopeEvent.DOWNSCOPE_CANDIDATE,
        CanonicalScopeEventType.DOWNSCOPE_CONFIRMED: ScopeEvent.DOWNSCOPE_CONFIRMED,
        CanonicalScopeEventType.CHOP_DETECTED: ScopeEvent.CHOP_DETECTED,
    }
    if event_type in mapping:
        return mapping[event_type]
    return ScopeEvent.SCOPE_UNKNOWN


def scope_direction_from_side_state_v1(
    side: SideState,
    *,
    fallback: ScopeDirectionState = ScopeDirectionState.LONG,
) -> ScopeDirectionState:
    """Derive ScopeDirectionState from SideState for trailing / threshold orientation."""
    if side in (
        SideState.SHORT_ARMED,
        SideState.SHORT_ACTIVE,
        SideState.SHORT_BLOCKED,
        SideState.SWITCH_LONG_TO_SHORT_PENDING,
    ):
        return ScopeDirectionState.SHORT
    if side in (
        SideState.LONG_ARMED,
        SideState.LONG_ACTIVE,
        SideState.LONG_BLOCKED,
        SideState.SWITCH_SHORT_TO_LONG_PENDING,
    ):
        return ScopeDirectionState.LONG
    return fallback


def _seed_runtime_scope_from_snapshot_v1(
    *,
    snapshot: CanonicalScopeSnapshotV1,
    now_tick: int,
) -> RuntimeScopeState:
    """Initialize trailing envelope from identity snapshot — first cycle / reset only."""
    anchor = float(snapshot.trailing_anchor)
    band = max(float(snapshot.scope_band), float(snapshot.min_scope_band), 1.0)
    return RuntimeScopeState(
        anchor_price=anchor,
        current_upscope_boundary=float(snapshot.neutral_upper_boundary),
        current_downscope_boundary=float(snapshot.neutral_lower_boundary),
        current_hysteresis_band=band,
        last_switch_tick=-1_000_000,
        switches_in_window=0,
        window_start_tick=now_tick,
        chop_latched=False,
        now_tick=now_tick,
        last_completed_side_switch_tick=-1_000_000,
        scope_stability_ticks=0,
    )


def _resolve_runtime_scope_state_for_cycle_v1(
    *,
    instrument_id: str,
    current_scope: CanonicalScopeSnapshotV1,
    now_tick: int,
    prior_state: Optional[RuntimeScopeState],
    bound_instrument_id: Optional[str],
    explicit_reset: bool,
) -> tuple[RuntimeScopeState, bool]:
    """Return (state, reinitialized). Fail-closed reinit on instrument mismatch / reset / missing."""
    if explicit_reset or prior_state is None:
        return (
            _seed_runtime_scope_from_snapshot_v1(snapshot=current_scope, now_tick=now_tick),
            True,
        )
    if bound_instrument_id is None or bound_instrument_id != instrument_id:
        return (
            _seed_runtime_scope_from_snapshot_v1(snapshot=current_scope, now_tick=now_tick),
            True,
        )
    return prior_state, False


def _rules_for_cycle_v1(
    *,
    provided: Optional[DynamicScopeRules],
    snapshot: CanonicalScopeSnapshotV1,
) -> DynamicScopeRules:
    if provided is not None:
        return provided
    return DynamicScopeRules(
        downscope_band_multiplier=_DEFAULT_SCOPE_RULES.downscope_band_multiplier,
        upscope_band_multiplier=_DEFAULT_SCOPE_RULES.upscope_band_multiplier,
        min_band_width=max(float(snapshot.min_scope_band), _DEFAULT_SCOPE_RULES.min_band_width),
        max_band_width=min(float(snapshot.max_scope_band), _DEFAULT_SCOPE_RULES.max_band_width),
        min_switch_cooldown_ticks=_DEFAULT_SCOPE_RULES.min_switch_cooldown_ticks,
        volatility_estimate=max(float(snapshot.volatility_estimate), 1e-9),
        max_switches_per_window=_DEFAULT_SCOPE_RULES.max_switches_per_window,
    )


def _side_state_to_entry_exit_direction(side: SideState) -> EntryExitDirectionState:
    table = {
        SideState.NEUTRAL_OBSERVE: EntryExitDirectionState.NEUTRAL,
        SideState.LONG_ARMED: EntryExitDirectionState.LONG_ARMED,
        SideState.LONG_ACTIVE: EntryExitDirectionState.LONG_ACTIVE,
        SideState.LONG_BLOCKED: EntryExitDirectionState.NEUTRAL,
        SideState.SHORT_ARMED: EntryExitDirectionState.SHORT_ARMED,
        SideState.SHORT_ACTIVE: EntryExitDirectionState.SHORT_ACTIVE,
        SideState.SHORT_BLOCKED: EntryExitDirectionState.NEUTRAL,
        SideState.SWITCH_LONG_TO_SHORT_PENDING: EntryExitDirectionState.SHORT_ARMED,
        SideState.SWITCH_SHORT_TO_LONG_PENDING: EntryExitDirectionState.LONG_ARMED,
        SideState.CHOP_GUARD_BLOCK: EntryExitDirectionState.NEUTRAL,
        SideState.KILL_ALL: EntryExitDirectionState.NEUTRAL,
    }
    return table.get(side, EntryExitDirectionState.NEUTRAL)


def _scope_event_ref_from_evidence(evidence: ScopeEventEvidenceV1) -> ScopeEventRefV1:
    return ScopeEventRefV1(
        scope_event_id=evidence.scope_event_id,
        semantic_digest=evidence.semantic_digest,
        event_type=evidence.event_type.value,
        trading_epoch=evidence.trading_epoch,
    )


def _compute_state_switch_digest(
    *,
    state_switch_id: str,
    instrument_id: str,
    trading_epoch: int,
    previous_side_state: str,
    next_side_state: str,
    scope_event_type: str,
    transition_allowed: bool,
    transition_reason_code: str,
) -> str:
    payload = {
        "instrument_id": instrument_id,
        "next_side_state": next_side_state,
        "previous_side_state": previous_side_state,
        "scope_event_type": scope_event_type,
        "state_switch_id": state_switch_id,
        "trading_epoch": trading_epoch,
        "transition_allowed": transition_allowed,
        "transition_reason_code": transition_reason_code,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _derive_state_switch_id(instrument_id: str, trading_epoch: int, scope_event_id: str) -> str:
    material = f"{instrument_id}|{trading_epoch}|{scope_event_id}"
    return f"state-switch-{hashlib.sha256(material.encode('utf-8')).hexdigest()[:24]}"


def _default_component_versions() -> dict[str, str]:
    return {
        "canonical_market_context": CANONICAL_MARKET_CONTEXT_LAYER_VERSION,
        "canonical_scope_initialization": CANONICAL_SCOPE_INITIALIZATION_LAYER_VERSION,
        "deterministic_scope_event_generator": DETERMINISTIC_SCOPE_EVENT_GENERATOR_LAYER_VERSION,
        "directional_assessment": DIRECTIONAL_ASSESSMENT_LAYER_VERSION,
        "survival_assessment": SURVIVAL_ASSESSMENT_LAYER_VERSION,
        "suitability_binding": SUITABILITY_BINDING_LAYER_VERSION,
        "double_play_composition_matrix": DOUBLE_PLAY_COMPOSITION_MATRIX_LAYER_VERSION,
        "double_play_entry_exit_policy": ENTRY_EXIT_POLICY_LAYER_VERSION,
        "double_play_state": DOUBLE_PLAY_STATE_LAYER_VERSION,
        "integrated_offline_trading_logic_replay": INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_LAYER_VERSION,
        "canonical_trading_decision_evidence": CANONICAL_TRADING_DECISION_EVIDENCE_LAYER_VERSION,
    }


def _validate_contract_versions(inp: IntegratedOfflineReplayInputV1) -> Tuple[str, ...]:
    errors: list[str] = []
    expected = dict(inp.expected_component_contracts) if inp.expected_component_contracts else {}
    actual = (
        dict(inp.component_versions) if inp.component_versions else _default_component_versions()
    )
    for key, expected_version in sorted(expected.items()):
        actual_version = actual.get(key)
        if actual_version != expected_version:
            errors.append(f"component_version_mismatch:{key}:{actual_version}!={expected_version}")
    for key, expected_version in sorted(inp.policy_versions.items()):
        policy_attr = {
            "scope_initialization": inp.policies.scope_initialization.policy_version,
            "scope_event_generator": inp.policies.scope_event_generator.policy_version,
            "directional": inp.policies.directional.policy_version,
            "survival": inp.policies.survival.policy_version,
            "suitability": inp.policies.suitability.policy_version,
            "composition": inp.policies.composition.policy_version,
            "entry_exit": inp.policies.entry_exit.policy_version,
        }.get(key)
        if policy_attr is not None and policy_attr != expected_version:
            errors.append(f"policy_version_mismatch:{key}:{policy_attr}!={expected_version}")
    return tuple(errors)


def _blocked_evidence(
    inp: IntegratedOfflineReplayInputV1,
    *,
    fail_reasons: Tuple[str, ...],
    decision_outcome: str = "blocked",
) -> CanonicalTradingDecisionEvidenceV1:
    input_digest = (
        inp.input_digest
        if _valid_sha256_hex(inp.input_digest)
        else hashlib.sha256(
            json.dumps(
                {"replay_id": inp.replay_id, "trading_epoch": inp.trading_epoch},
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
    )
    decision_id = derive_decision_id(
        replay_id=inp.replay_id,
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        input_digest=input_digest,
    )
    evidence = CanonicalTradingDecisionEvidenceV1(
        decision_id=decision_id,
        replay_id=inp.replay_id,
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        market_context_ref="",
        scope_initialization_ref="",
        scope_event_ref="",
        bull_assessment_ref="",
        bear_assessment_ref="",
        state_switch_ref="",
        bull_survival_ref="",
        bear_survival_ref="",
        bull_suitability_ref="",
        bear_suitability_ref="",
        composition_result_ref="",
        entry_exit_policy_ref="",
        current_scope_ref="",
        next_scope_ref="",
        previous_direction_state=inp.direction_state.value,
        next_direction_state=inp.direction_state.value,
        selected_side=CompositionSelectedSide.NONE.value,
        selected_strategy_ref="",
        decision_outcome=decision_outcome,
        entry_or_exit_policy_ref="",
        reason_codes=tuple(sorted(fail_reasons)),
        decision_precedence_trace=(),
        component_versions=dict(inp.component_versions)
        if inp.component_versions
        else _default_component_versions(),
        policy_versions=dict(inp.policy_versions),
        config_digest=inp.config_digest,
        implementation_digest=inp.implementation_digest,
        input_digest=input_digest,
        semantic_digest="",
    )
    return with_computed_evidence_semantic_digest(evidence)


def _directional_input_for_side(
    inp: IntegratedOfflineReplayInputV1,
    side: DirectionalAssessmentSide,
    scope_event_ref: ScopeEventRefV1,
) -> DirectionalAssessmentInputV1:
    """Build side input from the shared long-convention market path.

    Both sides consume the same ``price_path``. Side orientation is applied only by
    ``compute_signal_strength`` (sign flip for SHORT). Do not mirror the shared path
    here: mirroring plus the SHORT sign flip would invent identical candidate strength
    on both sides from one directional impulse.
    """
    anchor = float(inp.canonical_market_context.mark_price)
    return DirectionalAssessmentInputV1(
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        side=side,
        price_path=inp.price_path,
        reference_price=anchor,
        feature_refs=("feat-momentum-v1",),
        scope_event_ref=scope_event_ref,
        survival_preconditions=("survival_precondition_ref_only",),
        confirmation_state=inp.directional_confirmation_state,
        data_integrity_status=inp.canonical_market_context.data_integrity_status,
        clock_trust_status=inp.canonical_market_context.clock_trust_status,
        bar_finality_status=inp.canonical_market_context.bar_finality_status,
        trusted_data=inp.canonical_market_context.data_integrity_status.value == "trusted",
        input_complete=True,
        explicit_hard_block_reasons=(),
        policy_version=inp.policies.directional.policy_version,
    )


def _survival_input_for_assessment(
    inp: IntegratedOfflineReplayInputV1,
    assessment: DirectionalAssessmentV1,
) -> SurvivalAssessmentInputV1:
    return SurvivalAssessmentInputV1(
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        side=assessment.side,
        directional_assessment=assessment,
        cost_inputs=SurvivalCostInputsV1(
            entry_fee=0.0005,
            expected_entry_slippage=0.0002,
            exit_fee=0.0005,
            expected_exit_slippage=0.0002,
            expected_funding_cost=0.0001,
            expected_gross_edge=0.02,
            funding_cost_required=True,
        ),
        metric_inputs=SurvivalMetricInputsV1(
            data_completeness_complete=True,
            volatility_survival_ratio=0.8,
            sequence_survival_ratio=0.8,
            drawdown_survival_ratio=0.8,
            liquidation_buffer_ratio=0.2,
        ),
        last_evaluated_trading_epoch=inp.last_evaluated_trading_epoch,
        input_complete=True,
        explicit_hard_fail_reasons=(),
        explicit_blocked_reasons=(),
        policy_version=inp.policies.survival.policy_version,
    )


def _suitability_input_for_assessment(
    inp: IntegratedOfflineReplayInputV1,
    assessment: DirectionalAssessmentV1,
    survival: SurvivalResultV1,
) -> SuitabilityBindingInputV1:
    return SuitabilityBindingInputV1(
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        side=assessment.side,
        directional_assessment=assessment,
        survival_result=survival,
        regime_id=inp.regime_id,
        regime_status=inp.regime_status,
        strategy_registry=inp.strategy_registry,
        last_evaluated_trading_epoch=inp.last_evaluated_trading_epoch,
        input_complete=True,
        explicit_hard_block_reasons=(),
        explicit_blocked_reasons=(),
        ranking_policy_version=inp.policies.suitability.policy_version,
        strategy_suitability_agreement_material=inp.strategy_suitability_agreement_material,
    )


def resolve_integrated_scope_adverse_exit_signal_v0(
    scope_event: ScopeEventEvidenceV1,
    passthrough_signal: PolicySignalV0,
) -> PolicySignalV0:
    """Derive adverse-exit signal from canonical scope evidence; passthrough only when not triggered."""
    derived = derive_scope_adverse_exit_signal_v0(scope_event)
    if derived.triggered:
        return derived
    return passthrough_signal


def resolve_integrated_reversal_preparation_entry_exit_binding_v0(
    composition_result: DoublePlayCompositionResultV1,
    inp: IntegratedOfflineReplayInputV1,
) -> Tuple[DoublePlayCompositionResultV1, ExistingPositionSide, PositionState, bool]:
    """Reuse reversal-preparation adapter projection at integrated replay consumer boundary."""
    composition_for_policy = composition_result
    existing_position_side = inp.existing_position_side
    position_state = inp.position_state
    venue_flat = inp.venue_flat

    if is_reversal_preparation_composition_v0(composition_result):
        reversal_ctx = derive_reversal_preparation_position_context_v0(composition_result)
        if reversal_ctx is not None:
            composition_for_policy = project_composition_for_reversal_preparation_entry_exit_v0(
                composition_result
            )
            existing_position_side = reversal_ctx.existing_position_side
            position_state = reversal_ctx.position_state
            venue_flat = reversal_ctx.venue_flat

    return composition_for_policy, existing_position_side, position_state, venue_flat


def run_integrated_offline_trading_logic_replay_v1(
    inp: IntegratedOfflineReplayInputV1,
) -> IntegratedOfflineReplayResultV1:
    """Execute the canonical STEP 29B–29H offline replay chain fail-closed."""
    fail_reasons: list[str] = []

    if not _instrument_allowed(inp.instrument_id):
        fail_reasons.append("instrument_kind_forbidden")
    if inp.instrument_id != inp.canonical_market_context.instrument_id:
        fail_reasons.append("instrument_mismatch")
    if inp.trading_epoch != inp.canonical_market_context.trading_epoch:
        fail_reasons.append("trading_epoch_mismatch")
    if inp.input_digest and not _valid_sha256_hex(inp.input_digest):
        fail_reasons.append("input_digest_invalid")

    material = inp.strategy_suitability_agreement_material
    if material is not None:
        if material.instrument_id != inp.instrument_id:
            fail_reasons.append("instrument_mismatch")
        if material.trading_epoch != inp.trading_epoch:
            fail_reasons.append("trading_epoch_mismatch")
        if material.instrument_id != inp.canonical_market_context.instrument_id:
            fail_reasons.append("instrument_mismatch")
        if material.trading_epoch != inp.canonical_market_context.trading_epoch:
            fail_reasons.append("trading_epoch_mismatch")
        cmc = inp.canonical_market_context
        trusted = getattr(cmc.data_integrity_status, "value", None) == "trusted"
        clock_ok = getattr(cmc.clock_trust_status, "value", None) == "trusted"
        final_ok = getattr(cmc.bar_finality_status, "value", None) == "finalized"
        if not (trusted and clock_ok and final_ok):
            fail_reasons.append("cmc_untrusted_or_nonfinal")

    contract_errors = _validate_contract_versions(inp)
    fail_reasons.extend(contract_errors)

    if fail_reasons:
        evidence = _blocked_evidence(inp, fail_reasons=tuple(fail_reasons))
        return IntegratedOfflineReplayResultV1(
            replay_pass=False,
            fail_reasons=tuple(fail_reasons),
            evidence=evidence,
        )

    context = (
        inp.canonical_market_context
        if inp.canonical_market_context.input_digest
        else with_computed_input_digest(inp.canonical_market_context)
    )

    binding = bind_canonical_market_context_event(
        context,
        inp.market_context_binding_state,
    )
    if binding.eligibility.binding_outcome is CanonicalMarketContextBindingOutcome.BLOCKED:
        reasons = tuple(r.value for r in binding.eligibility.block_reasons)
        evidence = _blocked_evidence(
            inp,
            fail_reasons=reasons or ("market_context_blocked",),
            decision_outcome="blocked",
        )
        return IntegratedOfflineReplayResultV1(
            False, reasons or ("market_context_blocked",), evidence
        )

    if not binding.context:
        evidence = _blocked_evidence(inp, fail_reasons=("missing_market_context_output",))
        return IntegratedOfflineReplayResultV1(False, ("missing_market_context_output",), evidence)

    bound_context = binding.context

    scope_init = initialize_canonical_scope(
        bound_context,
        inp.policies.scope_initialization,
        inp.scope_prerequisites,
        existing_scope=inp.existing_scope,
        reinitialization_guard=inp.scope_reinitialization_guard,
    )
    if scope_init.scope is None:
        reasons = tuple(r.value for r in scope_init.block_reasons) or (
            "scope_initialization_blocked",
        )
        decision_outcome = "observe" if any("warmup" in r for r in reasons) else "blocked"
        evidence = _blocked_evidence(inp, fail_reasons=reasons, decision_outcome=decision_outcome)
        return IntegratedOfflineReplayResultV1(False, reasons, evidence)

    current_scope = scope_init.scope

    rules = _rules_for_cycle_v1(
        provided=inp.dynamic_scope_rules,
        snapshot=current_scope,
    )
    runtime_scope_before, runtime_scope_reinitialized = _resolve_runtime_scope_state_for_cycle_v1(
        instrument_id=inp.instrument_id,
        current_scope=current_scope,
        now_tick=inp.now_tick,
        prior_state=inp.runtime_scope_state,
        bound_instrument_id=inp.runtime_scope_bound_instrument_id,
        explicit_reset=bool(inp.explicit_runtime_scope_reset),
    )
    active_for_trail = derive_active_side(inp.side_state)
    runtime_scope_pre = update_dynamic_boundaries(
        mark_price=float(inp.current_price),
        side=active_for_trail,
        st=runtime_scope_before,
        rules=rules,
        env=_DEFAULT_RUNTIME_ENVELOPE,
    )
    trailing_anchor_used = (
        float(runtime_scope_pre.anchor_price)
        if runtime_scope_pre.anchor_price > 0
        else float(current_scope.trailing_anchor)
    )
    effective_scope_direction = scope_direction_from_side_state_v1(
        inp.side_state,
        fallback=inp.scope_direction_state,
    )

    scope_event_inp = ScopeEventGeneratorInputV1(
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        market_context_id=bound_context.context_id,
        market_context_digest=bound_context.input_digest,
        current_scope=current_scope,
        current_direction_state=effective_scope_direction,
        reference_price=float(bound_context.mark_price),
        current_price=float(inp.current_price),
        trailing_anchor=trailing_anchor_used,
        up_distance=float(inp.up_distance),
        adverse_exit_distance=float(inp.adverse_exit_distance),
        reversal_distance=float(inp.reversal_distance),
        confirmation_epochs=int(inp.confirmation_epochs),
        confirmation_state=inp.scope_confirmation_state,
        cooldown_state=inp.scope_cooldown_state,
        cooldown_remaining_epochs=int(inp.scope_cooldown_state.remaining_epochs),
        data_integrity_status=bound_context.data_integrity_status,
        clock_trust_status=bound_context.clock_trust_status,
        bar_finality_status=bound_context.bar_finality_status,
        policy_version=inp.policies.scope_event_generator.policy_version,
    )
    scope_event = with_computed_scope_event_digest(
        generate_deterministic_scope_event(scope_event_inp, inp.policies.scope_event_generator)
    )

    scope_event_ref = _scope_event_ref_from_evidence(scope_event)
    bull_inp = _directional_input_for_side(inp, DirectionalAssessmentSide.LONG, scope_event_ref)
    bear_inp = _directional_input_for_side(inp, DirectionalAssessmentSide.SHORT, scope_event_ref)
    bull_assessment = with_computed_directional_assessment_digest(
        evaluate_directional_assessment_v1(bull_inp, inp.policies.directional)
    )
    bear_assessment = with_computed_directional_assessment_digest(
        evaluate_directional_assessment_v1(bear_inp, inp.policies.directional)
    )

    bull_survival = evaluate_survival_assessment_v1(
        _survival_input_for_assessment(inp, bull_assessment),
        inp.policies.survival,
    )
    bear_survival = evaluate_survival_assessment_v1(
        _survival_input_for_assessment(inp, bear_assessment),
        inp.policies.survival,
    )
    bull_suitability = evaluate_suitability_binding_v1(
        _suitability_input_for_assessment(inp, bull_assessment, bull_survival),
        inp.policies.suitability,
    )
    bear_suitability = evaluate_suitability_binding_v1(
        _suitability_input_for_assessment(inp, bear_assessment, bear_survival),
        inp.policies.suitability,
    )

    composition_inp = DoublePlayCompositionInputV1(
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        context_reference=inp.context_reference,
        bull_directional_assessment=bull_assessment,
        bear_directional_assessment=bear_assessment,
        bull_survival_result=bull_survival,
        bear_survival_result=bear_survival,
        bull_suitability_result=bull_suitability,
        bear_suitability_result=bear_suitability,
        previous_direction_state=inp.previous_composition_direction_state,
        position_management_context=inp.position_management_context,
        last_evaluated_trading_epoch=inp.last_evaluated_trading_epoch,
        input_complete=True,
        input_digest="",
        explicit_blocked_reasons=(),
        policy_version=inp.policies.composition.policy_version,
    )
    composition_inp = replace(
        composition_inp,
        input_digest=compute_composition_input_digest(composition_inp),
    )
    composition_result = evaluate_double_play_composition_matrix_v1(
        composition_inp,
        inp.policies.composition,
    )

    mapped_event = _canonical_scope_event_to_scope_event(scope_event.event_type)
    next_side_state, runtime_scope_after_switch, transition = transition_state(
        side_state=inp.side_state,
        event=mapped_event,
        scope_state=runtime_scope_pre,
        rules=rules,
        envelope=_DEFAULT_RUNTIME_ENVELOPE,
        now_tick=inp.now_tick,
    )
    runtime_scope_after = update_dynamic_boundaries(
        mark_price=float(inp.current_price),
        side=derive_active_side(next_side_state),
        st=runtime_scope_after_switch,
        rules=rules,
        env=_DEFAULT_RUNTIME_ENVELOPE,
    )
    state_switch_id = _derive_state_switch_id(
        inp.instrument_id, inp.trading_epoch, scope_event.scope_event_id
    )
    switch_digest = _compute_state_switch_digest(
        state_switch_id=state_switch_id,
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        previous_side_state=inp.side_state.value,
        next_side_state=next_side_state.value,
        scope_event_type=scope_event.event_type.value,
        transition_allowed=transition.allowed,
        transition_reason_code=transition.reason_code,
    )
    state_switch = StateSwitchEvidenceV1(
        state_switch_id=state_switch_id,
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        previous_side_state=inp.side_state.value,
        next_side_state=next_side_state.value,
        scope_event_type=scope_event.event_type.value,
        transition_allowed=transition.allowed,
        transition_reason_code=transition.reason_code,
        semantic_digest=switch_digest,
    )

    scope_adverse_exit_signal = resolve_integrated_scope_adverse_exit_signal_v0(
        scope_event,
        inp.scope_adverse_exit_signal,
    )
    (
        composition_for_policy,
        effective_existing_position_side,
        effective_position_state,
        effective_venue_flat,
    ) = resolve_integrated_reversal_preparation_entry_exit_binding_v0(
        composition_result,
        inp,
    )

    effective_direction = _side_state_to_entry_exit_direction(next_side_state)
    entry_exit_inp = DoublePlayEntryExitPolicyInputV0(
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        context_reference=inp.context_reference,
        composition_result=composition_for_policy,
        direction_state=effective_direction,
        position_state=effective_position_state,
        reconciliation_state=inp.reconciliation_state,
        trading_gate=inp.trading_gate,
        safety_mode=inp.safety_mode,
        data_integrity_state=bound_context.data_integrity_status,
        clock_trust_status=bound_context.clock_trust_status,
        clock_trust_valid=bound_context.clock_trust_status.value == "trusted",
        cooldown_pass=inp.cooldown_pass,
        existing_position_side=effective_existing_position_side,
        venue_flat=effective_venue_flat,
        scope_adverse_exit_signal=scope_adverse_exit_signal,
        profit_protection_signal=inp.profit_protection_signal,
        time_exit_signal=inp.time_exit_signal,
        strategy_invalidation_signal=inp.strategy_invalidation_signal,
        hard_risk_reduction_signal=inp.hard_risk_reduction_signal,
        safety_exit_signal=inp.safety_exit_signal,
        input_complete=True,
        input_digest="",
        explicit_blocked_reasons=(),
        policy_version=inp.policies.entry_exit.policy_version,
    )
    entry_exit_inp = replace(
        entry_exit_inp,
        input_digest=compute_entry_exit_policy_input_digest(entry_exit_inp),
    )
    entry_exit_decision = evaluate_double_play_entry_exit_policy_v0(
        entry_exit_inp,
        inp.policies.entry_exit,
    )

    next_scope_ref = current_scope.scope_id
    if scope_event.next_scope_effective_epoch is not None:
        next_scope_ref = f"{current_scope.scope_id}-next-{scope_event.next_scope_effective_epoch}"

    selected_strategy_ref = ""
    if composition_result.selected_side is CompositionSelectedSide.LONG:
        selected_strategy_ref = bull_suitability.selected_strategy_id or ""
    elif composition_result.selected_side is CompositionSelectedSide.SHORT:
        selected_strategy_ref = bear_suitability.selected_strategy_id or ""

    input_digest = (
        inp.input_digest
        or hashlib.sha256(
            json.dumps(
                {
                    "config_digest": inp.config_digest,
                    "implementation_digest": inp.implementation_digest,
                    "replay_id": inp.replay_id,
                    "trading_epoch": inp.trading_epoch,
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
    )

    decision_id = derive_decision_id(
        replay_id=inp.replay_id,
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        input_digest=input_digest,
    )

    evidence = CanonicalTradingDecisionEvidenceV1(
        decision_id=decision_id,
        replay_id=inp.replay_id,
        instrument_id=inp.instrument_id,
        trading_epoch=inp.trading_epoch,
        market_context_ref=bound_context.context_id,
        scope_initialization_ref=current_scope.scope_id,
        scope_event_ref=scope_event.scope_event_id,
        bull_assessment_ref=bull_assessment.assessment_id,
        bear_assessment_ref=bear_assessment.assessment_id,
        state_switch_ref=state_switch.state_switch_id,
        bull_survival_ref=bull_survival.survival_id,
        bear_survival_ref=bear_survival.survival_id,
        bull_suitability_ref=bull_suitability.suitability_id,
        bear_suitability_ref=bear_suitability.suitability_id,
        composition_result_ref=composition_result.composition_id,
        entry_exit_policy_ref=entry_exit_decision.policy_decision_id,
        current_scope_ref=current_scope.scope_id,
        next_scope_ref=next_scope_ref,
        previous_direction_state=inp.direction_state.value,
        next_direction_state=effective_direction.value,
        selected_side=composition_result.selected_side.value,
        selected_strategy_ref=selected_strategy_ref,
        decision_outcome=entry_exit_decision.decision_outcome.value,
        entry_or_exit_policy_ref=entry_exit_decision.policy_decision_id,
        reason_codes=entry_exit_decision.reason_codes,
        decision_precedence_trace=entry_exit_decision.decision_precedence_trace,
        component_versions=dict(inp.component_versions)
        if inp.component_versions
        else _default_component_versions(),
        policy_versions=dict(inp.policy_versions),
        config_digest=inp.config_digest,
        implementation_digest=inp.implementation_digest,
        input_digest=input_digest,
        semantic_digest="",
    )
    _crs_binding = importlib.import_module(
        "trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0"
    )
    capital_context = _crs_binding.default_offline_replay_capital_context_v0(
        instrument_id=inp.instrument_id,
        reference_price=Decimal(str(bound_context.mark_price)),
    )
    sizing_binding = _crs_binding.bind_capital_risk_sizing_offline_replay_evidence_v0(
        evidence,
        capital_context=capital_context,
    )
    evidence = sizing_binding.evidence
    capital_risk_sizing_decision = sizing_binding.sizing_decision

    _coi_binding = importlib.import_module(
        "trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0"
    )
    intent_binding = _coi_binding.bind_canonical_order_intent_offline_replay_evidence_v0(
        evidence,
        sizing_decision=capital_risk_sizing_decision,
        capital_context=capital_context,
    )
    evidence = intent_binding.evidence
    canonical_order_intent = intent_binding.canonical_intent

    _sk_binding = importlib.import_module(
        "trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0"
    )
    SafetyKernelOfflineReplayContextV0 = _sk_binding.SafetyKernelOfflineReplayContextV0
    killswitch_blocked = (
        inp.safety_mode is SafetyMode.BLOCKED
        or inp.safety_exit_signal.triggered
        or inp.side_state is SideState.KILL_ALL
    )
    safety_binding = _sk_binding.bind_safety_kernel_offline_replay_evidence_v0(
        evidence,
        context=SafetyKernelOfflineReplayContextV0(
            safety_mode=inp.safety_mode,
            safety_exit_signal=inp.safety_exit_signal,
            reconciliation_state=inp.reconciliation_state,
            position_state=inp.position_state,
            trading_gate=inp.trading_gate,
            killswitch_blocked=killswitch_blocked,
            safety_decision_allowed=inp.safety_mode is not SafetyMode.BLOCKED,
        ),
    )
    evidence = safety_binding.evidence

    _ruo_binding = importlib.import_module(
        "trading.master_v2.reconciliation_unknown_outcome_offline_replay_binding_adapter_v0"
    )
    ReconciliationUnknownOutcomeOfflineReplayContextV0 = (
        _ruo_binding.ReconciliationUnknownOutcomeOfflineReplayContextV0
    )
    reconciliation_binding = (
        _ruo_binding.bind_reconciliation_unknown_outcome_offline_replay_evidence_v0(
            evidence,
            context=ReconciliationUnknownOutcomeOfflineReplayContextV0(
                position_state=inp.position_state,
                reconciliation_state=inp.reconciliation_state,
                venue_flat=inp.venue_flat,
                existing_position_side=inp.existing_position_side,
            ),
        )
    )
    evidence = reconciliation_binding.evidence

    _ks_binding = importlib.import_module(
        "trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0"
    )
    KillSwitchBoundaryOfflineReplayContextV0 = _ks_binding.KillSwitchBoundaryOfflineReplayContextV0
    derive_killswitch_boundary_mode_v0 = _ks_binding.derive_killswitch_boundary_mode_v0
    ks_mode = derive_killswitch_boundary_mode_v0(
        safety_mode=inp.safety_mode,
        side_state=inp.side_state,
        trading_gate=inp.trading_gate,
        safety_exit_signal=inp.safety_exit_signal,
        hard_risk_reduction_signal=inp.hard_risk_reduction_signal,
        safety_decision_allowed=inp.safety_mode is not SafetyMode.BLOCKED,
    )
    killswitch_binding = _ks_binding.bind_killswitch_boundary_offline_replay_evidence_v0(
        evidence,
        context=KillSwitchBoundaryOfflineReplayContextV0(
            boundary_mode=ks_mode,
            killswitch_active=ks_mode.value != "normal",
            safety_mode=inp.safety_mode,
            side_state=inp.side_state,
            trading_gate=inp.trading_gate,
            reconciliation_state=inp.reconciliation_state,
            position_state=inp.position_state,
            safety_exit_signal=inp.safety_exit_signal,
            hard_risk_reduction_signal=inp.hard_risk_reduction_signal,
            safety_decision_allowed=inp.safety_mode is not SafetyMode.BLOCKED,
        ),
    )
    evidence = killswitch_binding.evidence

    intermediate = IntegratedOfflineReplayIntermediateV1(
        market_context=bound_context,
        scope_initialization=scope_init,
        scope_event=scope_event,
        bull_assessment=bull_assessment,
        bear_assessment=bear_assessment,
        bull_survival=bull_survival,
        bear_survival=bear_survival,
        bull_suitability=bull_suitability,
        bear_suitability=bear_suitability,
        composition_result=composition_result,
        entry_exit_decision=entry_exit_decision,
        capital_risk_sizing_decision=capital_risk_sizing_decision,
        canonical_order_intent=canonical_order_intent,
        state_switch=state_switch,
        current_scope=current_scope,
        next_scope_ref=next_scope_ref,
        runtime_scope_state_before=runtime_scope_before,
        runtime_scope_state_after=runtime_scope_after,
        runtime_scope_reinitialized=runtime_scope_reinitialized,
        trailing_anchor_used=trailing_anchor_used,
        chop_binding_status=CHOP_BINDING_STATUS,
    )

    boundary_ok = (
        not entry_exit_decision.execution_eligible
        and not entry_exit_decision.adapter_compatible
        and entry_exit_decision.quantity_status == "NOT_BOUND"
        and entry_exit_decision.authority_effect == "NONE"
        and entry_exit_decision.runtime_effect == "NONE"
        and entry_exit_decision.order_effect == "NONE"
        and entry_exit_decision.risk_sizing_effect == "NONE"
        and not evidence.execution_eligible
        and not evidence.adapter_compatible
        and evidence.authority_effect == "NONE"
        and evidence.runtime_effect == "NONE"
        and evidence.order_effect == "NONE"
    )
    replay_pass = boundary_ok
    if not boundary_ok:
        fail_reasons.append("runtime_order_boundary_violation")

    return IntegratedOfflineReplayResultV1(
        replay_pass=replay_pass,
        fail_reasons=tuple(fail_reasons),
        evidence=evidence,
        intermediate=intermediate,
    )
