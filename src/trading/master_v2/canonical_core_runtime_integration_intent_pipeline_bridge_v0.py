# src/trading/master_v2/canonical_core_runtime_integration_intent_pipeline_bridge_v0.py
"""
Canonical Core Runtime Integration Intent Pipeline Bridge v0 (Remediation Slice B).

Offline binding:
CanonicalTradingDecisionEvidenceV1
  → capital_risk_sizing_v1
  → canonical_order_intent_v1
  → intent_compatibility_firewall_v1
  → execution_pipeline plan-only boundary (submission blocked)

No runtime start, adapter calls, credentials, or submission authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping, Optional, Tuple

from src.execution_pipeline.contracts import ExecutionPlan, OrderPlan
from src.execution_pipeline.plan_only_boundary_v0 import (
    PLAN_ONLY_BOUNDARY_OWNER,
    validate_execution_plan_only_boundary_v0,
)
from src.governance.canonical_order_intent_v1 import (
    TRANSFORMATION_ID as CANONICAL_TO_ADAPTER_TRANSFORMATION_ID,
    CanonicalOrderIntentBuildInputV1,
    CanonicalOrderIntentBuildOutcome,
    CanonicalOrderIntentV1,
    IntentAction,
    IntentSide,
    build_canonical_order_intent_v1,
    evaluate_adapter_compatibility_firewall_v1,
    transform_canonical_order_intent_v1_to_adapter_order_intent_v1,
)
from src.governance.capital_risk_sizing_v1 import (
    CapitalRiskSizingDecisionV1,
    CapitalRiskSizingInputV1,
    CapitalRiskSizingOutcome,
    InstrumentQuantityConstraintsV1,
    SelectedSide,
    evaluate_capital_risk_sizing_v1,
)
from src.governance.intent_compatibility_firewall_v1 import (
    evaluate_explicit_canonical_to_adapter_transformation_firewall_v1,
)
from trading.master_v2.canonical_core_runtime_integration_bridge_v0 import (
    CanonicalCoreRuntimeIntegrationInputV0,
    CanonicalCoreRuntimeIntegrationResultV0,
    build_integrated_offline_replay_input_from_harness_v0,
    run_canonical_core_runtime_integration_bridge_v0,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CanonicalTradingDecisionEvidenceV1,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
    run_integrated_offline_trading_logic_replay_v1,
)

CANONICAL_CORE_RUNTIME_INTEGRATION_INTENT_PIPELINE_BRIDGE_LAYER_VERSION = "v0"
CANONICAL_CORE_RUNTIME_INTEGRATION_INTENT_PIPELINE_BRIDGE_OWNER = (
    "trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0"
)
PACKAGE_MARKER = "CANONICAL_CORE_RUNTIME_INTEGRATION_INTENT_PIPELINE_BRIDGE_V0=true"

INTEGRATION_STATUS_BOUND_NOT_ACTIVATED = "BOUND_NOT_ACTIVATED"
INTENT_COMPATIBILITY_FIREWALL_STATUS = "BOUND_OFFLINE"
CAPITAL_RISK_SIZING_BINDING_STATUS = "BOUND_OFFLINE"
EXECUTION_PIPELINE_PLAN_ONLY_BOUNDARY_STATUS_PASS = "PASS"
NEXT_REMEDIATION_SLICE = (
    "Slice C: Registry consolidation — dual strategy registries and legacy entrypoints"
)

_AUTHORITY_EFFECT_NONE = "NONE"
_RUNTIME_EFFECT_NONE = "NONE"
_ORDER_EFFECT_NONE = "NONE"
_NETWORK_EFFECT_NONE = "NONE"

REASON_PASS = "PASS"
REASON_CANONICAL_DECISION_NOT_ACTIONABLE = "CANONICAL_DECISION_NOT_ACTIONABLE"
REASON_QUANTITY_PROVENANCE_MISSING = "QUANTITY_PROVENANCE_MISSING"
REASON_RISK_BINDING_INCOMPLETE = "RISK_BINDING_INCOMPLETE"
REASON_INTENT_CONTRACT_INCOMPATIBLE = "INTENT_CONTRACT_INCOMPATIBLE"
REASON_EXECUTION_ELIGIBILITY_DENIED = "EXECUTION_ELIGIBILITY_DENIED"
REASON_ADAPTER_COMPATIBILITY_DENIED = "ADAPTER_COMPATIBILITY_DENIED"
REASON_ZERO_ORDER_SUBMISSION_BLOCKED = "ZERO_ORDER_SUBMISSION_BLOCKED"
REASON_LEGACY_INTENT_AUTHORITY_DENIED = "LEGACY_INTENT_AUTHORITY_DENIED"
REASON_NON_FUTURES_INSTRUMENT = "NON_FUTURES_INSTRUMENT"
REASON_BITCOIN_SPECIFIC_DIRECTION = "BITCOIN_SPECIFIC_DIRECTION"
REASON_PLAN_ONLY_REQUIRED = "PLAN_ONLY_REQUIRED"
REASON_INVALID_SIDE = "INVALID_SIDE"
REASON_MISSING_DECISION_REF = "MISSING_DECISION_REF"

_ACTIONABLE_DECISION_OUTCOMES = frozenset(
    {
        "enter_long",
        "enter_short",
        "reduce",
        "exit",
    }
)
_NON_ACTIONABLE_DECISION_OUTCOMES = frozenset(
    {
        "no_action",
        "observe",
        "hold",
        "blocked",
        "reconcile_only",
    }
)
_FORBIDDEN_INSTRUMENT_MARKERS = frozenset({"btc", "xbt", "bitcoin", "spot", "synthetic_spot"})

_DEFAULT_ORDER_TYPE_POLICY = "MARKET_ONLY"
_DEFAULT_PRICE_POLICY = "EXPLICIT_NONE"
_DEFAULT_TIME_IN_FORCE_POLICY = "GTC"
_DEFAULT_MAX_SLIPPAGE_POLICY = "NONE"
_DEFAULT_POLICY_VERSION = "capital_risk_sizing_policy_v1"
_DEFAULT_CANONICAL_TRADING_LOGIC_VERSION = "integrated_offline_trading_logic_replay_v1"
_BRIDGE_CONFIG_DIGEST = hashlib.sha256(
    b"canonical-core-runtime-integration-intent-pipeline-bridge-v0-config"
).hexdigest()
_BRIDGE_IMPL_DIGEST = hashlib.sha256(
    b"canonical-core-runtime-integration-intent-pipeline-bridge-v0-implementation"
).hexdigest()


@dataclass(frozen=True)
class CanonicalCoreRuntimeCapitalContextV0:
    reference_price: Decimal
    protective_stop_price: Optional[Decimal]
    account_equity: Decimal
    scope_capital_limit: Decimal
    per_trade_risk_limit: Decimal
    total_capital_limit: Decimal
    daily_loss_remaining_budget: Decimal
    current_reconciled_exposure: Decimal
    instrument: InstrumentQuantityConstraintsV1
    maximum_positions: int = 1
    current_open_positions_count: int = 0
    current_open_side: Optional[str] = None
    configured_quantity_cap: Optional[Decimal] = None
    leverage_ceiling: Optional[Decimal] = None
    reconciliation_status: str = "RECONCILED"
    policy_digest: str = _BRIDGE_CONFIG_DIGEST
    config_digest: str = _BRIDGE_CONFIG_DIGEST


@dataclass(frozen=True)
class CanonicalCoreRuntimeIntentPipelineInputV0:
    decision_evidence: CanonicalTradingDecisionEvidenceV1
    capital_context: CanonicalCoreRuntimeCapitalContextV0
    plan_only: bool = True
    legacy_intent_authority_active: bool = False


@dataclass(frozen=True)
class CanonicalCoreRuntimeIntentPipelineResultV0:
    integration_pass: bool
    fail_reasons: Tuple[str, ...]
    reason_codes: Tuple[str, ...]
    decision_actionable: bool
    sizing_outcome: str
    intent_outcome: str
    intent_semantic_digest: str
    firewall_admissible: bool
    pipeline_boundary_pass: bool
    submission_blocked: bool
    execution_eligible: bool
    adapter_compatible: bool
    authority_effect: str
    runtime_effect: str
    order_effect: str
    network_effect: str
    credential_requirement: bool
    private_endpoint_requirement: bool
    legacy_intent_authority_active: bool
    dual_intent_authority_possible: bool
    integration_status: str
    intent_compatibility_firewall_status: str
    capital_risk_sizing_binding_status: str
    execution_pipeline_plan_only_boundary_status: str
    canonical_order_intent_to_execution_pipeline_status: str
    sizing_decision: Optional[CapitalRiskSizingDecisionV1] = None
    canonical_intent: Optional[CanonicalOrderIntentV1] = None


def _valid_sha256_hex(value: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", value))


def map_decision_outcome_to_intent_action(decision_outcome: str) -> Optional[str]:
    """Map canonical decision outcome to canonical order intent action fail-closed."""
    normalized = decision_outcome.strip().lower()
    if normalized in _NON_ACTIONABLE_DECISION_OUTCOMES:
        return None
    if normalized == "enter_long":
        return IntentAction.ENTER_LONG.value
    if normalized == "enter_short":
        return IntentAction.ENTER_SHORT.value
    if normalized == "reduce":
        return IntentAction.REDUCE.value
    if normalized == "exit":
        return IntentAction.EXIT.value
    return None


def decision_outcome_is_actionable(decision_outcome: str) -> bool:
    return decision_outcome.strip().lower() in _ACTIONABLE_DECISION_OUTCOMES


def map_selected_side_to_sizing_side(selected_side: str) -> Optional[str]:
    normalized = selected_side.strip().upper()
    if normalized in {SelectedSide.LONG.value, SelectedSide.SHORT.value}:
        return normalized
    return None


def _instrument_forbidden(instrument_id: str) -> Tuple[str, ...]:
    lowered = instrument_id.lower()
    reasons: list[str] = []
    if any(marker in lowered for marker in _FORBIDDEN_INSTRUMENT_MARKERS):
        if any(marker in lowered for marker in {"btc", "xbt", "bitcoin"}):
            reasons.append(REASON_BITCOIN_SPECIFIC_DIRECTION)
        if "spot" in lowered or "synthetic" in lowered:
            reasons.append(REASON_NON_FUTURES_INSTRUMENT)
    return tuple(dict.fromkeys(reasons))


def build_capital_risk_sizing_input_from_decision_v0(
    *,
    decision: CanonicalTradingDecisionEvidenceV1,
    capital_context: CanonicalCoreRuntimeCapitalContextV0,
) -> Tuple[Optional[CapitalRiskSizingInputV1], Tuple[str, ...]]:
    """Build STEP-29P sizing input from canonical decision evidence without duplication."""
    reasons: list[str] = []
    if not decision.decision_id:
        reasons.append(REASON_MISSING_DECISION_REF)
    selected_side = map_selected_side_to_sizing_side(decision.selected_side)
    if selected_side is None:
        reasons.append(REASON_CANONICAL_DECISION_NOT_ACTIONABLE)
    reasons.extend(_instrument_forbidden(decision.instrument_id))
    instrument = capital_context.instrument
    if instrument.market_type.lower() != "futures":
        reasons.append(REASON_NON_FUTURES_INSTRUMENT)
    if reasons:
        return None, tuple(dict.fromkeys(reasons))

    input_material = json.dumps(
        {
            "bridge_version": CANONICAL_CORE_RUNTIME_INTEGRATION_INTENT_PIPELINE_BRIDGE_LAYER_VERSION,
            "decision_id": decision.decision_id,
            "decision_semantic_digest": decision.semantic_digest,
            "instrument_id": decision.instrument_id,
            "selected_side": selected_side,
            "reference_price": str(capital_context.reference_price),
        },
        sort_keys=True,
    )
    input_digest = hashlib.sha256(input_material.encode("utf-8")).hexdigest()

    sizing_input = CapitalRiskSizingInputV1(
        decision_id=decision.decision_id,
        instrument_id=decision.instrument_id,
        selected_side=selected_side,
        reference_price=capital_context.reference_price,
        protective_stop_price=capital_context.protective_stop_price,
        stop_distance=None,
        account_equity=capital_context.account_equity,
        scope_capital_limit=capital_context.scope_capital_limit,
        per_trade_risk_limit=capital_context.per_trade_risk_limit,
        total_capital_limit=capital_context.total_capital_limit,
        daily_loss_remaining_budget=capital_context.daily_loss_remaining_budget,
        current_reconciled_exposure=capital_context.current_reconciled_exposure,
        maximum_positions=capital_context.maximum_positions,
        current_open_positions_count=capital_context.current_open_positions_count,
        current_open_side=capital_context.current_open_side,
        configured_quantity_cap=capital_context.configured_quantity_cap,
        leverage_ceiling=capital_context.leverage_ceiling,
        reconciliation_status=capital_context.reconciliation_status,
        policy_version=_DEFAULT_POLICY_VERSION,
        config_digest=capital_context.config_digest,
        input_digest=input_digest,
        instrument=instrument,
    )
    return sizing_input, ()


def _expected_position_side(intent_action: str, selected_side: str) -> str:
    if intent_action == IntentAction.ENTER_LONG.value:
        return IntentSide.LONG.value
    if intent_action == IntentAction.ENTER_SHORT.value:
        return IntentSide.SHORT.value
    return selected_side


def _blocked_result(
    *,
    fail_reasons: Tuple[str, ...],
    reason_codes: Tuple[str, ...],
    decision_actionable: bool = False,
    sizing_outcome: str = "BLOCKED",
    intent_outcome: str = "BLOCKED",
) -> CanonicalCoreRuntimeIntentPipelineResultV0:
    return CanonicalCoreRuntimeIntentPipelineResultV0(
        integration_pass=False,
        fail_reasons=fail_reasons,
        reason_codes=reason_codes,
        decision_actionable=decision_actionable,
        sizing_outcome=sizing_outcome,
        intent_outcome=intent_outcome,
        intent_semantic_digest="",
        firewall_admissible=False,
        pipeline_boundary_pass=False,
        submission_blocked=True,
        execution_eligible=False,
        adapter_compatible=False,
        authority_effect=_AUTHORITY_EFFECT_NONE,
        runtime_effect=_RUNTIME_EFFECT_NONE,
        order_effect=_ORDER_EFFECT_NONE,
        network_effect=_NETWORK_EFFECT_NONE,
        credential_requirement=False,
        private_endpoint_requirement=False,
        legacy_intent_authority_active=False,
        dual_intent_authority_possible=False,
        integration_status=INTEGRATION_STATUS_BOUND_NOT_ACTIVATED,
        intent_compatibility_firewall_status=INTENT_COMPATIBILITY_FIREWALL_STATUS,
        capital_risk_sizing_binding_status=CAPITAL_RISK_SIZING_BINDING_STATUS,
        execution_pipeline_plan_only_boundary_status="FAIL",
        canonical_order_intent_to_execution_pipeline_status=INTEGRATION_STATUS_BOUND_NOT_ACTIVATED,
    )


def _build_execution_plan_from_canonical_intent_v0(
    intent: CanonicalOrderIntentV1,
) -> Tuple[Optional[ExecutionPlan], Tuple[str, ...]]:
    transform = transform_canonical_order_intent_v1_to_adapter_order_intent_v1(intent)
    if transform.outcome.value != "PASS" or transform.adapter_intent is None:
        return None, transform.reason_codes

    adapter_intent = transform.adapter_intent
    order_plan = OrderPlan(
        order_id=intent.intent_id,
        symbol=adapter_intent.symbol,
        side=adapter_intent.side,
        quantity=adapter_intent.qty,
        meta={
            "canonical_intent_id": intent.intent_id,
            "canonical_semantic_digest": intent.semantic_digest,
            "quantity_provenance": intent.quantity_provenance,
            "plan_only": True,
            "submission_blocked": True,
        },
    )
    return ExecutionPlan(orders=[order_plan]), ()


def run_canonical_core_runtime_integration_intent_pipeline_bridge_v0(
    inp: CanonicalCoreRuntimeIntentPipelineInputV0,
) -> CanonicalCoreRuntimeIntentPipelineResultV0:
    """Bind decision evidence through sizing, intent, firewall, and plan-only pipeline edge."""

    decision = inp.decision_evidence
    capital = inp.capital_context
    fail_reasons: list[str] = []
    reason_codes: list[str] = []

    if inp.legacy_intent_authority_active:
        return _blocked_result(
            fail_reasons=(REASON_LEGACY_INTENT_AUTHORITY_DENIED,),
            reason_codes=(REASON_LEGACY_INTENT_AUTHORITY_DENIED,),
        )

    if not inp.plan_only:
        fail_reasons.append(REASON_PLAN_ONLY_REQUIRED)

    if decision.execution_eligible:
        fail_reasons.append(REASON_EXECUTION_ELIGIBILITY_DENIED)
    if decision.adapter_compatible:
        fail_reasons.append(REASON_ADAPTER_COMPATIBILITY_DENIED)
    if decision.authority_effect != _AUTHORITY_EFFECT_NONE:
        fail_reasons.append(REASON_EXECUTION_ELIGIBILITY_DENIED)
    if decision.order_effect != _ORDER_EFFECT_NONE:
        fail_reasons.append(REASON_ZERO_ORDER_SUBMISSION_BLOCKED)
    if decision.runtime_effect != _RUNTIME_EFFECT_NONE:
        fail_reasons.append(REASON_EXECUTION_ELIGIBILITY_DENIED)

    intent_action = map_decision_outcome_to_intent_action(decision.decision_outcome)
    decision_actionable = intent_action is not None
    if not decision_actionable:
        reason_codes.append(REASON_CANONICAL_DECISION_NOT_ACTIONABLE)
        fail_reasons.append(REASON_CANONICAL_DECISION_NOT_ACTIONABLE)
        return _blocked_result(
            fail_reasons=tuple(dict.fromkeys(fail_reasons)),
            reason_codes=tuple(dict.fromkeys(reason_codes)),
            decision_actionable=False,
            sizing_outcome="NOT_APPLICABLE",
            intent_outcome="BLOCKED",
        )

    sizing_input, sizing_build_errors = build_capital_risk_sizing_input_from_decision_v0(
        decision=decision,
        capital_context=capital,
    )
    if sizing_input is None:
        fail_reasons.extend(sizing_build_errors)
        reason_codes.extend(sizing_build_errors)
        return _blocked_result(
            fail_reasons=tuple(dict.fromkeys(fail_reasons)),
            reason_codes=tuple(dict.fromkeys(reason_codes)),
            decision_actionable=True,
            sizing_outcome="BLOCKED",
        )

    sizing_decision = evaluate_capital_risk_sizing_v1(sizing_input)
    sizing_outcome = sizing_decision.outcome.value
    if sizing_decision.outcome is not CapitalRiskSizingOutcome.PASS:
        fail_reasons.extend(sizing_decision.reason_codes)
        reason_codes.append(REASON_RISK_BINDING_INCOMPLETE)
        return _blocked_result(
            fail_reasons=tuple(dict.fromkeys(fail_reasons)),
            reason_codes=tuple(dict.fromkeys(reason_codes)),
            decision_actionable=True,
            sizing_outcome=sizing_outcome,
        )

    provenance = sizing_decision.quantity_provenance
    if provenance is None or not provenance.output_digest:
        fail_reasons.append(REASON_QUANTITY_PROVENANCE_MISSING)
        reason_codes.append(REASON_QUANTITY_PROVENANCE_MISSING)
        return _blocked_result(
            fail_reasons=tuple(dict.fromkeys(fail_reasons)),
            reason_codes=tuple(dict.fromkeys(reason_codes)),
            decision_actionable=True,
            sizing_outcome=sizing_outcome,
        )

    assert intent_action is not None
    selected_side = map_selected_side_to_sizing_side(decision.selected_side)
    if selected_side is None:
        fail_reasons.append(REASON_INVALID_SIDE)
        return _blocked_result(
            fail_reasons=tuple(dict.fromkeys(fail_reasons)),
            reason_codes=tuple(dict.fromkeys(fail_reasons)),
            decision_actionable=True,
            sizing_outcome=sizing_outcome,
        )

    intent_build = build_canonical_order_intent_v1(
        CanonicalOrderIntentBuildInputV1(
            sizing_input=sizing_input,
            sizing_decision=sizing_decision,
            intent_id=f"intent-{decision.decision_id}",
            trading_epoch=str(decision.trading_epoch),
            canonical_trading_logic_version=_DEFAULT_CANONICAL_TRADING_LOGIC_VERSION,
            intent_action=intent_action,
            policy_digest=capital.policy_digest,
            order_type_policy=_DEFAULT_ORDER_TYPE_POLICY,
            price_policy=_DEFAULT_PRICE_POLICY,
            time_in_force_policy=_DEFAULT_TIME_IN_FORCE_POLICY,
            max_slippage_policy=_DEFAULT_MAX_SLIPPAGE_POLICY,
            expected_position_side=_expected_position_side(intent_action, selected_side),
            current_reconciled_exposure=capital.current_reconciled_exposure,
            current_open_side=capital.current_open_side,
        )
    )
    intent_outcome = intent_build.outcome.value
    if (
        intent_build.outcome is not CanonicalOrderIntentBuildOutcome.PASS
        or intent_build.intent is None
    ):
        fail_reasons.extend(intent_build.reason_codes)
        reason_codes.append(REASON_INTENT_CONTRACT_INCOMPATIBLE)
        return _blocked_result(
            fail_reasons=tuple(dict.fromkeys(fail_reasons)),
            reason_codes=tuple(dict.fromkeys(reason_codes)),
            decision_actionable=True,
            sizing_outcome=sizing_outcome,
            intent_outcome=intent_outcome,
        )

    intent = intent_build.intent
    if intent.execution_eligible or intent.adapter_compatible or intent.submission_authorized:
        fail_reasons.append(REASON_EXECUTION_ELIGIBILITY_DENIED)
        reason_codes.append(REASON_EXECUTION_ELIGIBILITY_DENIED)

    adapter_firewall = evaluate_adapter_compatibility_firewall_v1(
        intent,
        target_type_name="OrderIntentV1",
    )
    transform = transform_canonical_order_intent_v1_to_adapter_order_intent_v1(intent)
    transform_firewall = evaluate_explicit_canonical_to_adapter_transformation_firewall_v1(
        source_digest=intent.semantic_digest,
        target_digest=(
            transform.descriptor.target_digest if transform.descriptor is not None else ""
        ),
        transformation_id=CANONICAL_TO_ADAPTER_TRANSFORMATION_ID,
    )
    firewall_admissible = (
        transform_firewall.admissible
        and transform.outcome.value == "PASS"
        and not adapter_firewall.admissible
    )
    if not transform_firewall.admissible:
        fail_reasons.extend(transform_firewall.reason_codes)
        reason_codes.append(REASON_INTENT_CONTRACT_INCOMPATIBLE)

    execution_plan, plan_errors = _build_execution_plan_from_canonical_intent_v0(intent)
    if execution_plan is None:
        fail_reasons.extend(plan_errors)
        reason_codes.append(REASON_INTENT_CONTRACT_INCOMPATIBLE)
        return _blocked_result(
            fail_reasons=tuple(dict.fromkeys(fail_reasons)),
            reason_codes=tuple(dict.fromkeys(reason_codes)),
            decision_actionable=True,
            sizing_outcome=sizing_outcome,
            intent_outcome=intent_outcome,
        )

    boundary = validate_execution_plan_only_boundary_v0(
        execution_plan,
        plan_only=inp.plan_only,
        submission_blocked=True,
        execution_eligible=False,
    )

    safety_failures: list[str] = []
    if boundary.execution_eligible:
        safety_failures.append(REASON_EXECUTION_ELIGIBILITY_DENIED)
    if not boundary.submission_blocked:
        safety_failures.append(REASON_ZERO_ORDER_SUBMISSION_BLOCKED)
    if boundary.adapter_invoked:
        safety_failures.append(REASON_ZERO_ORDER_SUBMISSION_BLOCKED)
    if not inp.plan_only:
        safety_failures.append(REASON_PLAN_ONLY_REQUIRED)

    binding_failures = [
        *fail_reasons,
        *safety_failures,
    ]
    if not boundary.boundary_pass:
        binding_failures.append(REASON_INTENT_CONTRACT_INCOMPATIBLE)

    reason_codes = tuple(
        dict.fromkeys(
            (
                REASON_PASS,
                REASON_ZERO_ORDER_SUBMISSION_BLOCKED,
                REASON_EXECUTION_ELIGIBILITY_DENIED,
                REASON_ADAPTER_COMPATIBILITY_DENIED,
                *reason_codes,
                *boundary.reason_codes,
            )
        )
    )

    integration_pass = (
        not binding_failures
        and boundary.boundary_pass
        and boundary.submission_blocked
        and not boundary.execution_eligible
    )

    return CanonicalCoreRuntimeIntentPipelineResultV0(
        integration_pass=integration_pass,
        fail_reasons=tuple(dict.fromkeys(binding_failures)),
        reason_codes=reason_codes,
        decision_actionable=True,
        sizing_outcome=sizing_outcome,
        intent_outcome=intent_outcome,
        intent_semantic_digest=intent.semantic_digest,
        firewall_admissible=firewall_admissible,
        pipeline_boundary_pass=boundary.boundary_pass,
        submission_blocked=True,
        execution_eligible=False,
        adapter_compatible=False,
        authority_effect=_AUTHORITY_EFFECT_NONE,
        runtime_effect=_RUNTIME_EFFECT_NONE,
        order_effect=_ORDER_EFFECT_NONE,
        network_effect=_NETWORK_EFFECT_NONE,
        credential_requirement=False,
        private_endpoint_requirement=False,
        legacy_intent_authority_active=False,
        dual_intent_authority_possible=False,
        integration_status=INTEGRATION_STATUS_BOUND_NOT_ACTIVATED,
        intent_compatibility_firewall_status=INTENT_COMPATIBILITY_FIREWALL_STATUS,
        capital_risk_sizing_binding_status=CAPITAL_RISK_SIZING_BINDING_STATUS,
        execution_pipeline_plan_only_boundary_status=(
            EXECUTION_PIPELINE_PLAN_ONLY_BOUNDARY_STATUS_PASS if boundary.boundary_pass else "FAIL"
        ),
        canonical_order_intent_to_execution_pipeline_status=INTEGRATION_STATUS_BOUND_NOT_ACTIVATED,
        sizing_decision=sizing_decision,
        canonical_intent=intent,
    )


def run_canonical_core_runtime_integration_intent_pipeline_from_harness_v0(
    *,
    harness_input: CanonicalCoreRuntimeIntegrationInputV0,
    capital_context: CanonicalCoreRuntimeCapitalContextV0,
) -> Tuple[
    CanonicalCoreRuntimeIntegrationResultV0,
    CanonicalCoreRuntimeIntentPipelineResultV0,
]:
    """Chain Slice A decision consumption with Slice B intent pipeline binding."""

    slice_a = run_canonical_core_runtime_integration_bridge_v0(harness_input)
    if not slice_a.canonical_core_consumed or not slice_a.decision_semantic_digest:
        blocked = _blocked_result(
            fail_reasons=tuple(slice_a.fail_reasons) + ("slice_a_decision_not_consumed",),
            reason_codes=(REASON_CANONICAL_DECISION_NOT_ACTIONABLE,),
        )
        return slice_a, blocked

    replay_input, build_errors = build_integrated_offline_replay_input_from_harness_v0(
        harness_input
    )
    if replay_input is None:
        blocked = _blocked_result(
            fail_reasons=tuple(build_errors),
            reason_codes=tuple(build_errors),
        )
        return slice_a, blocked

    replay_result: IntegratedOfflineReplayResultV1 = run_integrated_offline_trading_logic_replay_v1(
        replay_input
    )
    slice_b = run_canonical_core_runtime_integration_intent_pipeline_bridge_v0(
        CanonicalCoreRuntimeIntentPipelineInputV0(
            decision_evidence=replay_result.evidence,
            capital_context=capital_context,
            plan_only=True,
            legacy_intent_authority_active=False,
        )
    )
    return slice_a, slice_b


def build_slice_b_evidence_fields_v0(
    result: CanonicalCoreRuntimeIntentPipelineResultV0,
) -> Mapping[str, object]:
    """Non-authorizing durable evidence fields for Slice B closeout bundles."""
    return {
        "slice_b_integration_pass": result.integration_pass,
        "slice_b_integration_status": result.integration_status,
        "canonical_order_intent_to_execution_pipeline_status": (
            result.canonical_order_intent_to_execution_pipeline_status
        ),
        "intent_compatibility_firewall_status": result.intent_compatibility_firewall_status,
        "capital_risk_sizing_binding_status": result.capital_risk_sizing_binding_status,
        "execution_pipeline_plan_only_boundary_status": (
            result.execution_pipeline_plan_only_boundary_status
        ),
        "canonical_intent_semantic_digest": result.intent_semantic_digest,
        "submission_blocked": result.submission_blocked,
        "execution_eligible": result.execution_eligible,
        "adapter_compatible": result.adapter_compatible,
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "order_effect": result.order_effect,
        "network_effect": result.network_effect,
        "credential_requirement": result.credential_requirement,
        "private_endpoint_requirement": result.private_endpoint_requirement,
        "legacy_intent_authority_active": result.legacy_intent_authority_active,
        "dual_intent_authority_possible": result.dual_intent_authority_possible,
        "plan_only_boundary_owner": PLAN_ONLY_BOUNDARY_OWNER,
        "intent_pipeline_bridge_owner": (
            CANONICAL_CORE_RUNTIME_INTEGRATION_INTENT_PIPELINE_BRIDGE_OWNER
        ),
        "intent_pipeline_bridge_version": (
            CANONICAL_CORE_RUNTIME_INTEGRATION_INTENT_PIPELINE_BRIDGE_LAYER_VERSION
        ),
        "runtime_rewire_status": "PARTIAL",
        "zero_order_runtime_ready": False,
        "zero_order_runtime_execution_suspended": True,
        "next_remediation_slice": NEXT_REMEDIATION_SLICE,
    }
