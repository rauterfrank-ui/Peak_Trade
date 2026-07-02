# src/trading/master_v2/canonical_core_runtime_integration_bridge_v0.py
"""
Canonical Core Runtime Integration Bridge v0 (Remediation Slice A).

Narrow offline binding from zero-order validation harness inputs to the canonical
``run_integrated_offline_trading_logic_replay_v1`` decision orchestrator.

No runtime start, orders, adapter submission, credentials, or legacy decision paths.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Mapping, Optional, Tuple

from trading.master_v2.canonical_market_context_v1 import (
    BarFinalityStatus,
    CanonicalMarketContextBindingStateV1,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    FEATURE_CONTRACT_VERSION,
    WarmupStatus,
    with_computed_input_digest,
)
from trading.master_v2.canonical_scope_initialization_v1 import (
    CanonicalScopeInitializationPolicyV1,
    ScopeInitializationPrerequisitesV1,
    ScopeReinitializationGuardV1,
    SCOPE_INITIALIZATION_POLICY_VERSION,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    serialize_canonical_trading_decision_evidence_canonical,
)
from trading.master_v2.deterministic_scope_event_generator_v1 import (
    ScopeConfirmationStateV1,
    ScopeCooldownStateV1,
    ScopeDirectionState,
    ScopeEventGeneratorPolicyV1,
    SCOPE_EVENT_GENERATOR_POLICY_VERSION,
)
from trading.master_v2.directional_assessment_v1 import (
    DirectionalAssessmentPolicyV1,
    DirectionalAssessmentSide,
    DirectionalConfirmationStateV1,
    DIRECTIONAL_ASSESSMENT_POLICY_VERSION,
)
from trading.master_v2.double_play_composition_matrix_v1 import (
    BothCandidateOutcome,
    BothInvalidOutcome,
    CompositionDirectionState,
    DoublePlayCompositionPolicyV1,
    DOUBLE_PLAY_COMPOSITION_MATRIX_POLICY_VERSION,
    PositionManagementContext,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DoublePlayEntryExitPolicyV0,
    EntryExitDirectionState,
    ExistingPositionSide,
    ENTRY_EXIT_POLICY_VERSION,
    PolicySignalV0,
    PositionState,
    ReconciliationState,
    SafetyMode,
    TradingGate,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType
from trading.master_v2.double_play_state import SideState
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
    IntegratedOfflineReplayInputV1,
    IntegratedOfflineReplayPoliciesV1,
    IntegratedOfflineReplayResultV1,
    run_integrated_offline_trading_logic_replay_v1,
)
from trading.master_v2.suitability_binding_v1 import (
    SuitabilityBindingStatus,
    SuitabilityRankingPolicyV1,
    SuitabilityRegimeStatus,
    SuitabilityStrategyEntryV1,
    SuitabilityStrategyRegistryV1,
    SUITABILITY_RANKING_POLICY_VERSION,
)
from trading.master_v2.survival_assessment_v1 import (
    SurvivalAssessmentPolicyV1,
    SURVIVAL_ASSESSMENT_POLICY_VERSION,
)

CANONICAL_CORE_RUNTIME_INTEGRATION_BRIDGE_LAYER_VERSION = "v0"
CANONICAL_CORE_RUNTIME_INTEGRATION_BRIDGE_OWNER = (
    "trading.master_v2.canonical_core_runtime_integration_bridge_v0"
)
PACKAGE_MARKER = "CANONICAL_CORE_RUNTIME_INTEGRATION_BRIDGE_V0=true"

INTEGRATION_STATUS_BOUND_NOT_ACTIVATED = "BOUND_NOT_ACTIVATED"
NEXT_REMEDIATION_SLICE = (
    "Slice B: Runtime rewire v1 — canonical_order_intent → execution pipeline adapter boundary"
)

_AUTHORITY_EFFECT_NONE = "NONE"
_RUNTIME_EFFECT_NONE = "NONE"
_ORDER_EFFECT_NONE = "NONE"

_FORBIDDEN_INSTRUMENT_SUBSTRINGS = frozenset(
    {"btc", "xbt", "bitcoin", "spot", "synthetic_spot", "synthetic-spot"}
)
_HARNESS_INSTRUMENT_CANONICAL_MAP: Mapping[str, str] = {
    "PF_ETHUSD": "inst-pf-ethusd-perp",
}

_DEFAULT_MARK_PRICE = 3500.0
_DEFAULT_PRICE_PATH: Tuple[float, ...] = (_DEFAULT_MARK_PRICE, 3570.0)
_DEFAULT_TRADING_EPOCH = 0
_CONFIG_DIGEST = hashlib.sha256(b"canonical-core-runtime-integration-bridge-v0-config").hexdigest()
_IMPL_DIGEST = hashlib.sha256(
    b"canonical-core-runtime-integration-bridge-v0-implementation"
).hexdigest()


@dataclass(frozen=True)
class CanonicalCoreRuntimeIntegrationInputV0:
    run_id: str
    harness_instrument: str
    market_type: str = "futures"
    trading_epoch: int = _DEFAULT_TRADING_EPOCH
    plan_only: bool = True
    bar_finality_status: BarFinalityStatus = BarFinalityStatus.FINALIZED
    warmup_status: WarmupStatus = WarmupStatus.WARMUP_COMPLETE


@dataclass(frozen=True)
class CanonicalCoreRuntimeIntegrationResultV0:
    integration_pass: bool
    fail_reasons: Tuple[str, ...]
    canonical_replay_pass: bool
    canonical_core_consumed: bool
    decision_semantic_digest: str
    decision_outcome: str
    execution_eligible: bool
    authority_effect: str
    runtime_effect: str
    order_effect: str
    legacy_decision_authority_active: bool
    integration_status: str
    dual_authority_possible: bool
    replay_owner: str
    reason_codes: Tuple[str, ...]
    adapter_submission: bool = False
    credentials_required: bool = False
    private_endpoint_required: bool = False


def _valid_sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _instrument_forbidden(harness_instrument: str) -> bool:
    lowered = harness_instrument.lower()
    return any(token in lowered for token in _FORBIDDEN_INSTRUMENT_SUBSTRINGS)


def map_harness_instrument_to_canonical_id(harness_instrument: str) -> str | None:
    """Map bounded harness instrument to canonical replay instrument_id fail-closed."""
    if not harness_instrument or not harness_instrument.strip():
        return None
    if _instrument_forbidden(harness_instrument):
        return None
    mapped = _HARNESS_INSTRUMENT_CANONICAL_MAP.get(harness_instrument)
    if mapped is not None:
        return mapped
    if harness_instrument.startswith("PF_") and not _instrument_forbidden(harness_instrument):
        suffix = harness_instrument.removeprefix("PF_").lower()
        return f"inst-pf-{suffix}-perp"
    return None


def validate_canonical_core_runtime_integration_input_v0(
    inp: CanonicalCoreRuntimeIntegrationInputV0,
) -> Tuple[str, ...]:
    """Fail-closed validation before canonical replay consumption."""
    reasons: list[str] = []
    if not inp.run_id or not inp.run_id.strip():
        reasons.append("run_id_missing")
    if inp.market_type != "futures":
        reasons.append("market_type_not_futures")
    if _instrument_forbidden(inp.harness_instrument):
        reasons.append("instrument_kind_forbidden")
    if map_harness_instrument_to_canonical_id(inp.harness_instrument) is None:
        reasons.append("harness_instrument_unmapped")
    if inp.bar_finality_status is BarFinalityStatus.UNFINALIZED:
        reasons.append("trading_epoch_unfinalized")
    if inp.warmup_status is WarmupStatus.WARMUP_REQUIRED:
        reasons.append("warmup_incomplete")
    if inp.warmup_status is WarmupStatus.WARMUP_INVALID:
        reasons.append("warmup_invalid")
    return tuple(reasons)


def _features(**kwargs: float) -> dict[str, float]:
    return dict(kwargs)


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


def _strategy_registry() -> SuitabilityStrategyRegistryV1:
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


def _market_context_for_harness(
    *,
    canonical_instrument_id: str,
    trading_epoch: int,
    bar_finality_status: BarFinalityStatus,
    warmup_status: WarmupStatus,
) -> CanonicalMarketContextV1:
    return with_computed_input_digest(
        CanonicalMarketContextV1(
            context_id=f"ctx-{canonical_instrument_id}-epoch{trading_epoch}-bridge-v0",
            instrument_id=canonical_instrument_id,
            market_type=FuturesMarketType.PERPETUAL,
            trading_epoch=trading_epoch,
            market_event_time="2026-07-02T00:00:00+00:00",
            decision_time="2026-07-02T00:00:01+00:00",
            bar_interval="1m",
            bar_finality_status=bar_finality_status,
            mark_price=_DEFAULT_MARK_PRICE,
            index_price=3499.5,
            best_bid=3499.8,
            best_ask=3500.2,
            spread=0.4,
            volume=1_250_000.0,
            open_interest=85_000_000.0,
            funding_rate=0.00012,
            volatility_estimate=0.38,
            trend_feature_set=_features(slope=0.02, strength=0.71),
            momentum_feature_set=_features(rsi=55.0, roc=0.015),
            liquidity_feature_set=_features(depth_score=0.88),
            market_structure_feature_set=_features(range_ratio=0.42),
            data_integrity_status=DataIntegrityStatus.TRUSTED,
            clock_trust_status=ClockTrustStatus.TRUSTED,
            warmup_status=warmup_status,
            feature_contract_version=FEATURE_CONTRACT_VERSION,
            input_digest="",
        )
    )


def build_integrated_offline_replay_input_from_harness_v0(
    inp: CanonicalCoreRuntimeIntegrationInputV0,
) -> Tuple[Optional[IntegratedOfflineReplayInputV1], Tuple[str, ...]]:
    """Deterministically map harness inputs to canonical offline replay input."""
    validation_errors = validate_canonical_core_runtime_integration_input_v0(inp)
    if validation_errors:
        return None, validation_errors

    canonical_instrument_id = map_harness_instrument_to_canonical_id(inp.harness_instrument)
    assert canonical_instrument_id is not None

    replay_id = f"zero-order-harness-{inp.run_id.strip()}"
    trading_epoch = int(inp.trading_epoch)
    price_path = _DEFAULT_PRICE_PATH
    input_material = json.dumps(
        {
            "bridge_version": CANONICAL_CORE_RUNTIME_INTEGRATION_BRIDGE_LAYER_VERSION,
            "harness_instrument": inp.harness_instrument,
            "canonical_instrument_id": canonical_instrument_id,
            "replay_id": replay_id,
            "trading_epoch": trading_epoch,
        },
        sort_keys=True,
    )
    input_digest = hashlib.sha256(input_material.encode("utf-8")).hexdigest()

    market_context = _market_context_for_harness(
        canonical_instrument_id=canonical_instrument_id,
        trading_epoch=trading_epoch,
        bar_finality_status=inp.bar_finality_status,
        warmup_status=inp.warmup_status,
    )

    replay_input = IntegratedOfflineReplayInputV1(
        replay_id=replay_id,
        instrument_id=canonical_instrument_id,
        trading_epoch=trading_epoch,
        canonical_market_context=market_context,
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
        current_price=float(price_path[-1]),
        price_path=price_path,
        directional_confirmation_state=DirectionalConfirmationStateV1(
            candidate_count=1,
            last_evaluated_trading_epoch=trading_epoch - 1,
            last_signal_strength=0.02,
        ),
        strategy_registry=_strategy_registry(),
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
        policies=_default_policies(),
        component_versions=_component_versions(),
        policy_versions=_policy_versions(),
        config_digest=_CONFIG_DIGEST,
        implementation_digest=_IMPL_DIGEST,
        input_digest=input_digest,
        expected_component_contracts=_component_versions(),
        context_reference=f"trading-context-epoch-{trading_epoch}",
        now_tick=0,
    )
    return replay_input, ()


def _blocked_integration_result(
    *,
    fail_reasons: Tuple[str, ...],
) -> CanonicalCoreRuntimeIntegrationResultV0:
    return CanonicalCoreRuntimeIntegrationResultV0(
        integration_pass=False,
        fail_reasons=fail_reasons,
        canonical_replay_pass=False,
        canonical_core_consumed=False,
        decision_semantic_digest="",
        decision_outcome="blocked",
        execution_eligible=False,
        authority_effect=_AUTHORITY_EFFECT_NONE,
        runtime_effect=_RUNTIME_EFFECT_NONE,
        order_effect=_ORDER_EFFECT_NONE,
        legacy_decision_authority_active=False,
        integration_status=INTEGRATION_STATUS_BOUND_NOT_ACTIVATED,
        dual_authority_possible=False,
        replay_owner=INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
        reason_codes=fail_reasons,
    )


def run_canonical_core_runtime_integration_bridge_v0(
    inp: CanonicalCoreRuntimeIntegrationInputV0,
) -> CanonicalCoreRuntimeIntegrationResultV0:
    """Consume canonical decision core from harness-shaped inputs (offline, no authority)."""
    replay_input, build_errors = build_integrated_offline_replay_input_from_harness_v0(inp)
    if replay_input is None:
        return _blocked_integration_result(fail_reasons=build_errors)

    replay_result: IntegratedOfflineReplayResultV1 = run_integrated_offline_trading_logic_replay_v1(
        replay_input
    )
    evidence = replay_result.evidence

    safety_failures: list[str] = []
    if evidence.execution_eligible:
        safety_failures.append("execution_eligible_must_remain_false")
    if evidence.authority_effect != _AUTHORITY_EFFECT_NONE:
        safety_failures.append("authority_effect_must_remain_none")
    if evidence.runtime_effect != _RUNTIME_EFFECT_NONE:
        safety_failures.append("runtime_effect_must_remain_none")
    if evidence.order_effect != _ORDER_EFFECT_NONE:
        safety_failures.append("order_effect_must_remain_none")
    if evidence.adapter_compatible:
        safety_failures.append("adapter_compatible_must_remain_false")

    fail_reasons = tuple(build_errors) + tuple(replay_result.fail_reasons) + tuple(safety_failures)
    integration_pass = not fail_reasons and replay_result.replay_pass

    return CanonicalCoreRuntimeIntegrationResultV0(
        integration_pass=integration_pass,
        fail_reasons=fail_reasons,
        canonical_replay_pass=replay_result.replay_pass,
        canonical_core_consumed=True,
        decision_semantic_digest=evidence.semantic_digest,
        decision_outcome=evidence.decision_outcome,
        execution_eligible=evidence.execution_eligible,
        authority_effect=evidence.authority_effect,
        runtime_effect=evidence.runtime_effect,
        order_effect=evidence.order_effect,
        legacy_decision_authority_active=False,
        integration_status=INTEGRATION_STATUS_BOUND_NOT_ACTIVATED,
        dual_authority_possible=False,
        replay_owner=INTEGRATED_OFFLINE_TRADING_LOGIC_REPLAY_OWNER,
        reason_codes=evidence.reason_codes,
    )


def build_zero_order_canonical_decision_evidence_fields_v0(
    result: CanonicalCoreRuntimeIntegrationResultV0,
) -> dict[str, object]:
    """Evidence fields for zero-order harness durable bundle (non-authorizing)."""
    return {
        "canonical_core_decision_consumed": result.canonical_core_consumed,
        "canonical_core_runtime_integration_pass": result.integration_pass,
        "canonical_core_runtime_integration_status": result.integration_status,
        "canonical_trading_decision_semantic_digest": result.decision_semantic_digest,
        "canonical_trading_decision_outcome": result.decision_outcome,
        "canonical_decision_authority_effect": result.authority_effect,
        "canonical_decision_runtime_effect": result.runtime_effect,
        "canonical_decision_order_effect": result.order_effect,
        "legacy_decision_authority_active": result.legacy_decision_authority_active,
        "dual_decision_authority_possible": result.dual_authority_possible,
        "canonical_replay_owner": result.replay_owner,
        "canonical_core_runtime_integration_bridge_version": (
            CANONICAL_CORE_RUNTIME_INTEGRATION_BRIDGE_LAYER_VERSION
        ),
        "adapter_submission": result.adapter_submission,
        "credentials_required": result.credentials_required,
        "private_endpoint_required": result.private_endpoint_required,
        "zero_order_runtime_ready": False,
        "zero_order_runtime_execution_suspended": True,
        "next_remediation_slice": NEXT_REMEDIATION_SLICE,
        "runtime_rewire_status": "FAIL",
    }


def canonical_decision_evidence_digest_from_replay_result(
    replay_result: IntegratedOfflineReplayResultV1,
) -> str:
    """Expose canonical decision digest for parity checks."""
    return replay_result.evidence.semantic_digest


def serialize_canonical_decision_evidence_for_parity(
    replay_result: IntegratedOfflineReplayResultV1,
) -> str:
    return serialize_canonical_trading_decision_evidence_canonical(replay_result.evidence)
