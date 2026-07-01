"""
Offline Canonical Order Intent v1 (RUNBOOK STEP 29Q).

Pure, deterministic, fail-closed venue-neutral order intent contract built from
validated STEP-29P capital/risk/sizing output. No adapter compatibility,
submission, runtime authority, or venue effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, replace
from decimal import Decimal
from enum import Enum
from typing import Any, Mapping, Optional, Type

from src.governance.capital_risk_sizing_v1 import (
    AUTHORITY_EFFECT_NONE as SIZING_AUTHORITY_EFFECT_NONE,
)
from src.governance.capital_risk_sizing_v1 import (
    CapitalRiskSizingDecisionV1,
    CapitalRiskSizingInputV1,
    CapitalRiskSizingOutcome,
    SelectedSide,
)

CONTRACT_NAME = "canonical_order_intent_v1"
CONTRACT_VERSION = "v1"
SCHEMA_VERSION = "canonical_order_intent_schema_v1"
IMPLEMENTATION_DIGEST = "canonical_order_intent_v1_offline_slice"
DETERMINISTIC_SERIALIZATION_VERSION = "canonical_order_intent_deterministic_serialization_v1"
INTENT_VERSION = "canonical_order_intent_v1"

PACKAGE_MARKER = "CANONICAL_ORDER_INTENT_V1=true"
FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
SPOT_ALLOWED = False
SYNTHETIC_SPOT_ALLOWED = False

AUTHORITY_EFFECT_NONE = "NONE"
RUNTIME_EFFECT_NONE = "NONE"
NETWORK_EFFECT_NONE = "NONE"
CREDENTIAL_EFFECT_NONE = "NONE"

_FORBIDDEN_INSTRUMENT_MARKERS = frozenset({"btc", "xbt", "bitcoin"})
_FORBIDDEN_MARKET_TYPES = frozenset({"spot", "synthetic_spot", "synthetic-spot"})
_FORBIDDEN_ADAPTER_TYPE_NAMES = frozenset(
    {
        "OrderIntent",
        "OrderIntentV1",
        "OrderRequest",
        "Order",
        "AdapterRequest",
        "VenuePayload",
        "ExecutionIntent",
    }
)

REASON_PASS = "PASS"
REASON_MISSING_QUANTITY_PROVENANCE = "MISSING_QUANTITY_PROVENANCE"
REASON_INVALID_QUANTITY = "INVALID_QUANTITY"
REASON_SIZING_NOT_PASS = "SIZING_NOT_PASS"
REASON_MISSING_DECISION_REF = "MISSING_DECISION_REF"
REASON_MISSING_CAPITAL_ENVELOPE_REF = "MISSING_CAPITAL_ENVELOPE_REF"
REASON_MISSING_PRE_SIZING_RISK_REF = "MISSING_PRE_SIZING_RISK_REF"
REASON_MISSING_SIZING_RESULT_REF = "MISSING_SIZING_RESULT_REF"
REASON_MISSING_POST_SIZING_RISK_REF = "MISSING_POST_SIZING_RISK_REF"
REASON_INVALID_SIDE_ACTION_COMBINATION = "INVALID_SIDE_ACTION_COMBINATION"
REASON_EXIT_WITHOUT_REDUCE_ONLY = "EXIT_WITHOUT_REDUCE_ONLY"
REASON_REDUCE_EXPOSURE_INCREASE = "REDUCE_EXPOSURE_INCREASE"
REASON_ENTER_LONG_WRONG_POSITION_EFFECT = "ENTER_LONG_WRONG_POSITION_EFFECT"
REASON_ENTER_SHORT_WRONG_POSITION_EFFECT = "ENTER_SHORT_WRONG_POSITION_EFFECT"
REASON_IMPLICIT_REVERSAL = "IMPLICIT_REVERSAL"
REASON_NON_FUTURES_INSTRUMENT = "NON_FUTURES_INSTRUMENT"
REASON_BITCOIN_SPECIFIC_DIRECTION = "BITCOIN_SPECIFIC_DIRECTION"
REASON_INVALID_DIGEST = "INVALID_DIGEST"
REASON_NO_ACTION_NOT_SUBMITTABLE = "NO_ACTION_NOT_SUBMITTABLE"
REASON_DEFAULT_QUANTITY_FORBIDDEN = "DEFAULT_QUANTITY_FORBIDDEN"
REASON_ADAPTER_CAST_FORBIDDEN = "ADAPTER_CAST_FORBIDDEN"
REASON_DIRECT_SUBMISSION_FORBIDDEN = "DIRECT_SUBMISSION_FORBIDDEN"
REASON_TRANSFORMATION_REQUIRED = "TRANSFORMATION_REQUIRED"
REASON_VENUE_FIELD_IN_CANONICAL = "VENUE_FIELD_IN_CANONICAL"
REASON_MUTABLE_INTENT = "MUTABLE_INTENT"
REASON_MISSING_PROVENANCE = "MISSING_PROVENANCE"
REASON_INVALID_INPUT_TYPE = "INVALID_INPUT_TYPE"
REASON_INVALID_CANONICAL_INTENT_VERSION = "INVALID_CANONICAL_INTENT_VERSION"
REASON_UNSUPPORTED_SIDE = "UNSUPPORTED_SIDE"
REASON_UNSUPPORTED_ORDER_TYPE_POLICY = "UNSUPPORTED_ORDER_TYPE_POLICY"
REASON_UNSUPPORTED_TIME_IN_FORCE_POLICY = "UNSUPPORTED_TIME_IN_FORCE_POLICY"
REASON_UNBOUND_PRICE_POLICY = "UNBOUND_PRICE_POLICY"
REASON_MISSING_INSTRUMENT = "MISSING_INSTRUMENT"
REASON_QUANTITY_PRECISION_LOSS = "QUANTITY_PRECISION_LOSS"
REASON_QUANTITY_ROUNDING_INCREASES_RISK = "QUANTITY_ROUNDING_INCREASES_RISK"
REASON_CONTRADICTORY_REDUCE_ONLY_SEMANTICS = "CONTRADICTORY_REDUCE_ONLY_SEMANTICS"
REASON_UNBOUND_ADAPTER_FIELD = "UNBOUND_ADAPTER_FIELD"
REASON_UNBOUND_TRANSFORMATION = "UNBOUND_TRANSFORMATION"

TRANSFORMATION_ID = "canonical_order_intent_v1_to_adapter_order_intent_v1"
TRANSFORMATION_VERSION = "v1"
FIELD_MAPPING_VERSION = "canonical_to_adapter_order_intent_field_mapping_v1"
TARGET_CONTRACT_NAME = "adapter_order_intent_v1"
TARGET_CONTRACT_VERSION = "v1"
TARGET_OWNER_MODULE = "src.execution.adapters.base_v1"
TARGET_TYPE_NAME = "OrderIntentV1"

_ORDER_TYPE_POLICY_BINDINGS: dict[str, str] = {
    "MARKET_ONLY": "market",
    "LIMIT_ONLY": "limit",
}
_TIME_IN_FORCE_POLICY_BINDINGS: dict[str, str] = {
    "GTC": "gtc",
    "IOC": "ioc",
    "FOK": "fok",
}
_PRICE_POLICY_EXPLICIT_NONE = "EXPLICIT_NONE"
_PRICE_POLICY_EXPLICIT_PREFIX = "EXPLICIT_PRICE:"
_POST_ONLY_POLICY = "POST_ONLY"


class IntentAction(str, Enum):
    ENTER_LONG = "ENTER_LONG"
    ENTER_SHORT = "ENTER_SHORT"
    REDUCE = "REDUCE"
    EXIT = "EXIT"
    NO_ACTION = "NO_ACTION"


class PositionEffect(str, Enum):
    OPEN_OR_INCREASE = "OPEN_OR_INCREASE"
    REDUCE_ONLY = "REDUCE_ONLY"
    CLOSE_ONLY = "CLOSE_ONLY"


class IntentSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class ValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"


class CanonicalOrderIntentBuildOutcome(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class CanonicalOrderIntentBuildInputV1:
    sizing_input: CapitalRiskSizingInputV1
    sizing_decision: CapitalRiskSizingDecisionV1
    intent_id: str
    trading_epoch: str
    canonical_trading_logic_version: str
    intent_action: str
    policy_digest: str
    order_type_policy: str
    price_policy: str
    time_in_force_policy: str
    max_slippage_policy: str
    expected_position_side: str
    current_reconciled_exposure: Decimal
    current_open_side: Optional[str] = None


@dataclass(frozen=True)
class CanonicalOrderIntentV1:
    intent_id: str
    intent_version: str
    decision_id: str
    instrument_id: str
    trading_epoch: str
    canonical_trading_logic_version: str
    capital_envelope_ref: str
    pre_sizing_risk_ref: str
    sizing_result_ref: str
    post_sizing_risk_ref: str
    policy_digest: str
    config_digest: str
    implementation_digest: str
    provenance_digest: str
    side: str
    intent_action: str
    quantity: Decimal
    quantity_unit: str
    quantity_provenance: str
    reduce_only: bool
    position_effect: str
    order_type_policy: str
    price_policy: str
    time_in_force_policy: str
    max_slippage_policy: str
    expected_position_side: str
    instrument_metadata_ref: str
    execution_eligible: bool = False
    adapter_compatible: bool = False
    submission_authorized: bool = False
    runtime_effect: str = RUNTIME_EFFECT_NONE
    authority_effect: str = AUTHORITY_EFFECT_NONE
    network_effect: str = NETWORK_EFFECT_NONE
    credential_effect: str = CREDENTIAL_EFFECT_NONE
    transformation_required: bool = True
    validation_status: str = ValidationStatus.VALID.value
    reason_codes: tuple[str, ...] = (REASON_PASS,)
    semantic_digest: str = ""
    deterministic_serialization_version: str = DETERMINISTIC_SERIALIZATION_VERSION


@dataclass(frozen=True)
class CanonicalOrderIntentBuildResultV1:
    outcome: CanonicalOrderIntentBuildOutcome
    intent: Optional[CanonicalOrderIntentV1]
    reason_codes: tuple[str, ...]
    execution_eligible: bool = False
    adapter_compatible: bool = False
    submission_authorized: bool = False
    runtime_effect: str = RUNTIME_EFFECT_NONE
    authority_effect: str = AUTHORITY_EFFECT_NONE


@dataclass(frozen=True)
class AdapterCompatibilityFirewallResultV1:
    admissible: bool
    reason_codes: tuple[str, ...]
    target_type_name: str


class CanonicalOrderIntentError(ValueError):
    """Fail-closed canonical order intent contract error."""


class CanonicalOrderIntentTransformOutcome(str, Enum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class AdapterOrderIntentV1StructuralV1:
    """Offline structural mirror of adapter OrderIntentV1 — no submission effect."""

    symbol: str
    side: str
    qty: float
    order_type: str
    price: Optional[float]
    tif: str
    post_only: bool
    reduce_only: bool
    client_id: Optional[str]
    meta: Optional[tuple[tuple[str, str], ...]]


@dataclass(frozen=True)
class CanonicalOrderIntentTransformationDescriptorV1:
    source_contract: str
    source_version: str
    target_contract: str
    target_version: str
    transformation_id: str
    transformation_version: str
    field_mapping_version: str
    source_digest: str
    target_digest: str
    lossless_fields: tuple[str, ...]
    rejected_unbound_fields: tuple[str, ...]
    runtime_effect: bool
    order_effect: bool
    authority_effect: bool
    network_effect: bool
    adapter_submission_effect: bool
    transformation_required_acknowledged: bool
    source_quantity_provenance: str


@dataclass(frozen=True)
class CanonicalOrderIntentTransformResultV1:
    outcome: CanonicalOrderIntentTransformOutcome
    adapter_intent: Optional[AdapterOrderIntentV1StructuralV1]
    descriptor: Optional[CanonicalOrderIntentTransformationDescriptorV1]
    reason_codes: tuple[str, ...]
    runtime_effect: bool = False
    order_effect: bool = False
    authority_effect: bool = False
    network_effect: bool = False
    adapter_submission_effect: bool = False


def _sha256_hex(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _digest_ref(payload: Mapping[str, Any]) -> str:
    return _sha256_hex(payload)


def compute_capital_envelope_ref(decision: CapitalRiskSizingDecisionV1) -> str:
    envelope = decision.capital_envelope
    return _digest_ref(
        {
            "scope_capital_limit": str(envelope.scope_capital_limit),
            "account_equity": str(envelope.account_equity),
            "total_capital_limit": str(envelope.total_capital_limit),
            "within_envelope": envelope.within_envelope,
        }
    )


def compute_pre_sizing_risk_ref(decision: CapitalRiskSizingDecisionV1) -> str:
    pre = decision.pre_sizing_risk
    return _digest_ref(
        {
            "outcome": pre.outcome.value,
            "effective_trade_risk_budget": str(pre.effective_trade_risk_budget),
            "effective_scope_capital_limit": str(pre.effective_scope_capital_limit),
            "effective_total_capital_limit": str(pre.effective_total_capital_limit),
        }
    )


def compute_sizing_result_ref(decision: CapitalRiskSizingDecisionV1) -> str:
    provenance = decision.quantity_provenance
    sizing = decision.canonical_sizing
    if provenance is None or sizing is None:
        return ""
    return _digest_ref(
        {
            "final_quantity": str(provenance.final_quantity),
            "binding_cap": provenance.binding_cap,
            "output_digest": provenance.output_digest,
            "candidate_quantity": str(sizing.candidate_quantity),
            "binding_cap_kind": sizing.binding_cap.value,
        }
    )


def compute_post_sizing_risk_ref(decision: CapitalRiskSizingDecisionV1) -> str:
    post = decision.post_sizing_risk
    if post is None:
        return ""
    return _digest_ref(
        {
            "outcome": post.outcome.value,
            "projected_stop_loss": str(post.projected_stop_loss),
            "projected_notional": str(post.projected_notional),
            "projected_exposure": str(post.projected_exposure),
        }
    )


def _derive_position_effect(intent_action: str) -> str:
    if intent_action == IntentAction.ENTER_LONG.value:
        return PositionEffect.OPEN_OR_INCREASE.value
    if intent_action == IntentAction.ENTER_SHORT.value:
        return PositionEffect.OPEN_OR_INCREASE.value
    if intent_action == IntentAction.REDUCE.value:
        return PositionEffect.REDUCE_ONLY.value
    if intent_action == IntentAction.EXIT.value:
        return PositionEffect.CLOSE_ONLY.value
    return ""


def _derive_reduce_only(intent_action: str) -> bool:
    return intent_action in {
        IntentAction.REDUCE.value,
        IntentAction.EXIT.value,
    }


def _derive_side(intent_action: str, selected_side: str) -> str:
    if intent_action == IntentAction.ENTER_LONG.value:
        return IntentSide.LONG.value
    if intent_action == IntentAction.ENTER_SHORT.value:
        return IntentSide.SHORT.value
    return selected_side


def _blocked_result(reason_codes: tuple[str, ...]) -> CanonicalOrderIntentBuildResultV1:
    return CanonicalOrderIntentBuildResultV1(
        outcome=CanonicalOrderIntentBuildOutcome.BLOCKED,
        intent=None,
        reason_codes=reason_codes,
    )


def _validate_instrument_futures_only(inp: CapitalRiskSizingInputV1) -> tuple[str, ...]:
    reasons: list[str] = []
    instrument = inp.instrument
    market_type = (instrument.market_type if instrument else "").lower()
    if market_type in _FORBIDDEN_MARKET_TYPES or market_type != "futures":
        reasons.append(REASON_NON_FUTURES_INSTRUMENT)
    instrument_lower = inp.instrument_id.lower()
    if any(marker in instrument_lower for marker in _FORBIDDEN_INSTRUMENT_MARKERS):
        reasons.append(REASON_BITCOIN_SPECIFIC_DIRECTION)
    return tuple(dict.fromkeys(reasons))


def _validate_action_semantics(
    *,
    intent_action: str,
    selected_side: str,
    position_effect: str,
    reduce_only: bool,
    quantity: Decimal,
    current_reconciled_exposure: Decimal,
    current_open_side: Optional[str],
    expected_position_side: str,
    check_exposure: bool = True,
) -> tuple[str, ...]:
    reasons: list[str] = []

    if intent_action == IntentAction.NO_ACTION.value:
        reasons.append(REASON_NO_ACTION_NOT_SUBMITTABLE)

    side = _derive_side(intent_action, selected_side)

    if intent_action == IntentAction.ENTER_LONG.value:
        if side != IntentSide.LONG.value:
            reasons.append(REASON_INVALID_SIDE_ACTION_COMBINATION)
        if position_effect != PositionEffect.OPEN_OR_INCREASE.value:
            reasons.append(REASON_ENTER_LONG_WRONG_POSITION_EFFECT)
        if reduce_only:
            reasons.append(REASON_INVALID_SIDE_ACTION_COMBINATION)

    if intent_action == IntentAction.ENTER_SHORT.value:
        if side != IntentSide.SHORT.value:
            reasons.append(REASON_INVALID_SIDE_ACTION_COMBINATION)
        if position_effect != PositionEffect.OPEN_OR_INCREASE.value:
            reasons.append(REASON_ENTER_SHORT_WRONG_POSITION_EFFECT)
        if reduce_only:
            reasons.append(REASON_INVALID_SIDE_ACTION_COMBINATION)

    if intent_action == IntentAction.REDUCE.value:
        if not reduce_only:
            reasons.append(REASON_INVALID_SIDE_ACTION_COMBINATION)
        if position_effect != PositionEffect.REDUCE_ONLY.value:
            reasons.append(REASON_INVALID_SIDE_ACTION_COMBINATION)
        if check_exposure and quantity > current_reconciled_exposure:
            reasons.append(REASON_REDUCE_EXPOSURE_INCREASE)

    if intent_action == IntentAction.EXIT.value:
        if not reduce_only:
            reasons.append(REASON_EXIT_WITHOUT_REDUCE_ONLY)
        if position_effect != PositionEffect.CLOSE_ONLY.value:
            reasons.append(REASON_INVALID_SIDE_ACTION_COMBINATION)

    if (
        current_open_side is not None
        and current_open_side in {IntentSide.LONG.value, IntentSide.SHORT.value}
        and current_reconciled_exposure > 0
        and current_open_side != side
        and intent_action in {IntentAction.ENTER_LONG.value, IntentAction.ENTER_SHORT.value}
    ):
        reasons.append(REASON_IMPLICIT_REVERSAL)

    if expected_position_side not in {IntentSide.LONG.value, IntentSide.SHORT.value}:
        reasons.append(REASON_INVALID_SIDE_ACTION_COMBINATION)

    return tuple(dict.fromkeys(reasons))


def build_canonical_order_intent_v1(
    build_input: CanonicalOrderIntentBuildInputV1,
) -> CanonicalOrderIntentBuildResultV1:
    """Build a canonical order intent from validated STEP-29P sizing output."""

    inp = build_input.sizing_input
    decision = build_input.sizing_decision
    reasons: list[str] = []

    reasons.extend(_validate_instrument_futures_only(inp))

    if decision.outcome is not CapitalRiskSizingOutcome.PASS:
        reasons.append(REASON_SIZING_NOT_PASS)

    provenance = decision.quantity_provenance
    if provenance is None:
        reasons.append(REASON_MISSING_QUANTITY_PROVENANCE)
    else:
        quantity = provenance.final_quantity
        if quantity is None or quantity <= 0:
            reasons.append(REASON_INVALID_QUANTITY)
        if provenance.output_digest == "":
            reasons.append(REASON_MISSING_QUANTITY_PROVENANCE)

    if not inp.decision_id:
        reasons.append(REASON_MISSING_DECISION_REF)

    capital_envelope_ref = compute_capital_envelope_ref(decision)
    pre_sizing_risk_ref = compute_pre_sizing_risk_ref(decision)
    sizing_result_ref = compute_sizing_result_ref(decision)
    post_sizing_risk_ref = compute_post_sizing_risk_ref(decision)

    if not capital_envelope_ref:
        reasons.append(REASON_MISSING_CAPITAL_ENVELOPE_REF)
    if not pre_sizing_risk_ref:
        reasons.append(REASON_MISSING_PRE_SIZING_RISK_REF)
    if not sizing_result_ref:
        reasons.append(REASON_MISSING_SIZING_RESULT_REF)
    if not post_sizing_risk_ref:
        reasons.append(REASON_MISSING_POST_SIZING_RISK_REF)

    intent_action = build_input.intent_action
    position_effect = _derive_position_effect(intent_action)
    reduce_only = _derive_reduce_only(intent_action)
    side = _derive_side(intent_action, decision.selected_side)

    quantity = provenance.final_quantity if provenance is not None else Decimal("0")
    reasons.extend(
        _validate_action_semantics(
            intent_action=intent_action,
            selected_side=decision.selected_side,
            position_effect=position_effect,
            reduce_only=reduce_only,
            quantity=quantity,
            current_reconciled_exposure=build_input.current_reconciled_exposure,
            current_open_side=build_input.current_open_side,
            expected_position_side=build_input.expected_position_side,
        )
    )

    if not build_input.policy_digest or not inp.config_digest:
        reasons.append(REASON_MISSING_PROVENANCE)

    if reasons:
        return _blocked_result(tuple(dict.fromkeys(reasons)))

    provenance_digest = _digest_ref(
        {
            "capital_envelope_ref": capital_envelope_ref,
            "pre_sizing_risk_ref": pre_sizing_risk_ref,
            "sizing_result_ref": sizing_result_ref,
            "post_sizing_risk_ref": post_sizing_risk_ref,
            "policy_digest": build_input.policy_digest,
            "config_digest": inp.config_digest,
            "implementation_digest": IMPLEMENTATION_DIGEST,
            "input_digest": inp.input_digest,
        }
    )

    intent_without_digest = CanonicalOrderIntentV1(
        intent_id=build_input.intent_id,
        intent_version=INTENT_VERSION,
        decision_id=inp.decision_id,
        instrument_id=inp.instrument_id,
        trading_epoch=build_input.trading_epoch,
        canonical_trading_logic_version=build_input.canonical_trading_logic_version,
        capital_envelope_ref=capital_envelope_ref,
        pre_sizing_risk_ref=pre_sizing_risk_ref,
        sizing_result_ref=sizing_result_ref,
        post_sizing_risk_ref=post_sizing_risk_ref,
        policy_digest=build_input.policy_digest,
        config_digest=inp.config_digest,
        implementation_digest=IMPLEMENTATION_DIGEST,
        provenance_digest=provenance_digest,
        side=side,
        intent_action=intent_action,
        quantity=quantity,
        quantity_unit="CONTRACTS",
        quantity_provenance=provenance.output_digest,
        reduce_only=reduce_only,
        position_effect=position_effect,
        order_type_policy=build_input.order_type_policy,
        price_policy=build_input.price_policy,
        time_in_force_policy=build_input.time_in_force_policy,
        max_slippage_policy=build_input.max_slippage_policy,
        expected_position_side=build_input.expected_position_side,
        instrument_metadata_ref=provenance.instrument_metadata_ref,
    )

    semantic_digest = compute_semantic_digest(intent_without_digest)
    intent = replace(intent_without_digest, semantic_digest=semantic_digest)

    validation = validate_canonical_order_intent_v1(intent)
    if validation.validation_status != ValidationStatus.VALID.value:
        return _blocked_result(validation.reason_codes)

    return CanonicalOrderIntentBuildResultV1(
        outcome=CanonicalOrderIntentBuildOutcome.PASS,
        intent=intent,
        reason_codes=(REASON_PASS,),
    )


@dataclass(frozen=True)
class CanonicalOrderIntentValidationResultV1:
    validation_status: str
    reason_codes: tuple[str, ...]


def validate_canonical_order_intent_v1(
    intent: CanonicalOrderIntentV1,
) -> CanonicalOrderIntentValidationResultV1:
    """Fail-closed validation of a canonical order intent."""

    reasons: list[str] = []

    if intent.execution_eligible:
        reasons.append(REASON_DIRECT_SUBMISSION_FORBIDDEN)
    if intent.adapter_compatible:
        reasons.append(REASON_ADAPTER_CAST_FORBIDDEN)
    if intent.submission_authorized:
        reasons.append(REASON_DIRECT_SUBMISSION_FORBIDDEN)
    if not intent.transformation_required:
        reasons.append(REASON_TRANSFORMATION_REQUIRED)
    if intent.runtime_effect != RUNTIME_EFFECT_NONE:
        reasons.append(REASON_DIRECT_SUBMISSION_FORBIDDEN)
    if intent.authority_effect != AUTHORITY_EFFECT_NONE:
        reasons.append(REASON_DIRECT_SUBMISSION_FORBIDDEN)
    if intent.network_effect != NETWORK_EFFECT_NONE:
        reasons.append(REASON_DIRECT_SUBMISSION_FORBIDDEN)
    if intent.credential_effect != CREDENTIAL_EFFECT_NONE:
        reasons.append(REASON_DIRECT_SUBMISSION_FORBIDDEN)

    if intent.quantity <= 0:
        reasons.append(REASON_INVALID_QUANTITY)
    if not intent.quantity_provenance:
        reasons.append(REASON_MISSING_QUANTITY_PROVENANCE)

    if not intent.decision_id:
        reasons.append(REASON_MISSING_DECISION_REF)
    if not intent.capital_envelope_ref:
        reasons.append(REASON_MISSING_CAPITAL_ENVELOPE_REF)
    if not intent.pre_sizing_risk_ref:
        reasons.append(REASON_MISSING_PRE_SIZING_RISK_REF)
    if not intent.sizing_result_ref:
        reasons.append(REASON_MISSING_SIZING_RESULT_REF)
    if not intent.post_sizing_risk_ref:
        reasons.append(REASON_MISSING_POST_SIZING_RISK_REF)

    if intent.semantic_digest:
        expected = compute_semantic_digest(
            replace(intent, semantic_digest="", validation_status=ValidationStatus.VALID.value)
        )
        if intent.semantic_digest != expected:
            reasons.append(REASON_INVALID_DIGEST)

    reasons.extend(
        _validate_action_semantics(
            intent_action=intent.intent_action,
            selected_side=intent.side,
            position_effect=intent.position_effect,
            reduce_only=intent.reduce_only,
            quantity=intent.quantity,
            current_reconciled_exposure=Decimal("0"),
            current_open_side=None,
            expected_position_side=intent.expected_position_side,
            check_exposure=False,
        )
    )

    if reasons:
        return CanonicalOrderIntentValidationResultV1(
            validation_status=ValidationStatus.INVALID.value,
            reason_codes=tuple(dict.fromkeys(reasons)),
        )
    return CanonicalOrderIntentValidationResultV1(
        validation_status=ValidationStatus.VALID.value,
        reason_codes=(REASON_PASS,),
    )


def canonical_order_intent_to_semantic_dict(intent: CanonicalOrderIntentV1) -> dict[str, Any]:
    payload = {
        field.name: getattr(intent, field.name)
        for field in fields(CanonicalOrderIntentV1)
        if field.name not in {"semantic_digest", "validation_status", "reason_codes"}
    }
    payload["quantity"] = str(payload["quantity"])
    return payload


def compute_semantic_digest(intent: CanonicalOrderIntentV1) -> str:
    base = replace(intent, semantic_digest="", validation_status=ValidationStatus.VALID.value)
    return _sha256_hex(canonical_order_intent_to_semantic_dict(base))


def canonical_order_intent_to_json(intent: CanonicalOrderIntentV1) -> str:
    return json.dumps(
        canonical_order_intent_to_semantic_dict(intent),
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_order_intent_from_dict(payload: Mapping[str, Any]) -> CanonicalOrderIntentV1:
    quantity_raw = payload.get("quantity")
    intent = CanonicalOrderIntentV1(
        intent_id=str(payload["intent_id"]),
        intent_version=str(payload["intent_version"]),
        decision_id=str(payload["decision_id"]),
        instrument_id=str(payload["instrument_id"]),
        trading_epoch=str(payload["trading_epoch"]),
        canonical_trading_logic_version=str(payload["canonical_trading_logic_version"]),
        capital_envelope_ref=str(payload["capital_envelope_ref"]),
        pre_sizing_risk_ref=str(payload["pre_sizing_risk_ref"]),
        sizing_result_ref=str(payload["sizing_result_ref"]),
        post_sizing_risk_ref=str(payload["post_sizing_risk_ref"]),
        policy_digest=str(payload["policy_digest"]),
        config_digest=str(payload["config_digest"]),
        implementation_digest=str(payload["implementation_digest"]),
        provenance_digest=str(payload["provenance_digest"]),
        side=str(payload["side"]),
        intent_action=str(payload["intent_action"]),
        quantity=Decimal(str(quantity_raw)),
        quantity_unit=str(payload["quantity_unit"]),
        quantity_provenance=str(payload["quantity_provenance"]),
        reduce_only=bool(payload["reduce_only"]),
        position_effect=str(payload["position_effect"]),
        order_type_policy=str(payload["order_type_policy"]),
        price_policy=str(payload["price_policy"]),
        time_in_force_policy=str(payload["time_in_force_policy"]),
        max_slippage_policy=str(payload["max_slippage_policy"]),
        expected_position_side=str(payload["expected_position_side"]),
        instrument_metadata_ref=str(payload["instrument_metadata_ref"]),
        execution_eligible=bool(payload.get("execution_eligible", False)),
        adapter_compatible=bool(payload.get("adapter_compatible", False)),
        submission_authorized=bool(payload.get("submission_authorized", False)),
        runtime_effect=str(payload.get("runtime_effect", RUNTIME_EFFECT_NONE)),
        authority_effect=str(payload.get("authority_effect", AUTHORITY_EFFECT_NONE)),
        network_effect=str(payload.get("network_effect", NETWORK_EFFECT_NONE)),
        credential_effect=str(payload.get("credential_effect", CREDENTIAL_EFFECT_NONE)),
        transformation_required=bool(payload.get("transformation_required", True)),
        validation_status=str(payload.get("validation_status", ValidationStatus.VALID.value)),
        reason_codes=tuple(str(code) for code in payload.get("reason_codes", (REASON_PASS,))),
        semantic_digest=str(payload.get("semantic_digest", "")),
        deterministic_serialization_version=str(
            payload.get(
                "deterministic_serialization_version",
                DETERMINISTIC_SERIALIZATION_VERSION,
            )
        ),
    )
    if not intent.semantic_digest:
        intent = replace(intent, semantic_digest=compute_semantic_digest(intent))
    return intent


def assert_canonical_order_intent_immutable(intent: CanonicalOrderIntentV1) -> None:
    """Raise if the intent dataclass is not frozen/immutable."""

    if not getattr(intent, "__dataclass_fields__", None):
        raise CanonicalOrderIntentError(REASON_MUTABLE_INTENT)
    params = getattr(intent.__class__, "__dataclass_params__", None)
    if params is None or not getattr(params, "frozen", False):
        raise CanonicalOrderIntentError(REASON_MUTABLE_INTENT)


def evaluate_adapter_compatibility_firewall_v1(
    intent: CanonicalOrderIntentV1,
    *,
    target_type_name: str,
) -> AdapterCompatibilityFirewallResultV1:
    """Explicit fail-closed boundary against direct adapter/payload casting."""

    reasons: list[str] = []
    if target_type_name in _FORBIDDEN_ADAPTER_TYPE_NAMES:
        reasons.append(REASON_ADAPTER_CAST_FORBIDDEN)
    if intent.adapter_compatible:
        reasons.append(REASON_ADAPTER_CAST_FORBIDDEN)
    if not intent.transformation_required:
        reasons.append(REASON_TRANSFORMATION_REQUIRED)
    if intent.execution_eligible or intent.submission_authorized:
        reasons.append(REASON_DIRECT_SUBMISSION_FORBIDDEN)
    if reasons:
        return AdapterCompatibilityFirewallResultV1(
            admissible=False,
            reason_codes=tuple(dict.fromkeys(reasons)),
            target_type_name=target_type_name,
        )
    return AdapterCompatibilityFirewallResultV1(
        admissible=False,
        reason_codes=(REASON_TRANSFORMATION_REQUIRED,),
        target_type_name=target_type_name,
    )


def reject_direct_adapter_cast_v1(
    intent: CanonicalOrderIntentV1,
    target_type: Type[Any],
) -> None:
    """Raise CanonicalOrderIntentError on forbidden direct adapter cast."""

    result = evaluate_adapter_compatibility_firewall_v1(
        intent,
        target_type_name=target_type.__name__,
    )
    if not result.admissible:
        raise CanonicalOrderIntentError(",".join(result.reason_codes))


def reject_direct_submission_v1(intent: CanonicalOrderIntentV1) -> None:
    """Raise CanonicalOrderIntentError if submission is attempted."""

    if intent.execution_eligible or intent.submission_authorized:
        raise CanonicalOrderIntentError(REASON_DIRECT_SUBMISSION_FORBIDDEN)
    raise CanonicalOrderIntentError(REASON_TRANSFORMATION_REQUIRED)


def _blocked_transform_result(
    reason_codes: tuple[str, ...],
) -> CanonicalOrderIntentTransformResultV1:
    return CanonicalOrderIntentTransformResultV1(
        outcome=CanonicalOrderIntentTransformOutcome.BLOCKED,
        adapter_intent=None,
        descriptor=None,
        reason_codes=reason_codes,
    )


def _adapter_intent_to_semantic_dict(intent: AdapterOrderIntentV1StructuralV1) -> dict[str, Any]:
    payload: dict[str, Any] = {
        field.name: getattr(intent, field.name)
        for field in fields(AdapterOrderIntentV1StructuralV1)
    }
    if payload["meta"] is not None:
        payload["meta"] = list(payload["meta"])
    return payload


def compute_adapter_order_intent_structural_digest(
    intent: AdapterOrderIntentV1StructuralV1,
) -> str:
    return _sha256_hex(_adapter_intent_to_semantic_dict(intent))


def compute_transformation_descriptor_digest(
    descriptor: CanonicalOrderIntentTransformationDescriptorV1,
) -> str:
    payload = {
        field.name: getattr(descriptor, field.name)
        for field in fields(CanonicalOrderIntentTransformationDescriptorV1)
    }
    return _sha256_hex(payload)


def _validate_instrument_for_transform(intent: CanonicalOrderIntentV1) -> tuple[str, ...]:
    reasons: list[str] = []
    if not intent.instrument_id.strip():
        reasons.append(REASON_MISSING_INSTRUMENT)
    instrument_lower = intent.instrument_id.lower()
    if any(marker in instrument_lower for marker in _FORBIDDEN_INSTRUMENT_MARKERS):
        reasons.append(REASON_BITCOIN_SPECIFIC_DIRECTION)
    metadata_lower = intent.instrument_metadata_ref.lower()
    if any(marker in metadata_lower for marker in _FORBIDDEN_MARKET_TYPES):
        reasons.append(REASON_NON_FUTURES_INSTRUMENT)
    if "spot" in instrument_lower and "perp" not in instrument_lower:
        reasons.append(REASON_NON_FUTURES_INSTRUMENT)
    return tuple(dict.fromkeys(reasons))


def _validate_reduce_only_semantics(intent: CanonicalOrderIntentV1) -> tuple[str, ...]:
    reasons: list[str] = []
    reduce_expected = intent.intent_action in {
        IntentAction.REDUCE.value,
        IntentAction.EXIT.value,
    }
    if reduce_expected and not intent.reduce_only:
        reasons.append(REASON_CONTRADICTORY_REDUCE_ONLY_SEMANTICS)
    if not reduce_expected and intent.reduce_only:
        reasons.append(REASON_CONTRADICTORY_REDUCE_ONLY_SEMANTICS)
    if intent.intent_action == IntentAction.EXIT.value:
        if intent.position_effect != PositionEffect.CLOSE_ONLY.value:
            reasons.append(REASON_CONTRADICTORY_REDUCE_ONLY_SEMANTICS)
    if intent.intent_action == IntentAction.REDUCE.value:
        if intent.position_effect != PositionEffect.REDUCE_ONLY.value:
            reasons.append(REASON_CONTRADICTORY_REDUCE_ONLY_SEMANTICS)
    return tuple(dict.fromkeys(reasons))


def _adapter_side_for_intent(intent: CanonicalOrderIntentV1) -> Optional[str]:
    action = intent.intent_action
    if action == IntentAction.ENTER_LONG.value:
        return "buy"
    if action == IntentAction.ENTER_SHORT.value:
        return "sell"
    if action in {IntentAction.REDUCE.value, IntentAction.EXIT.value}:
        if intent.side == IntentSide.LONG.value:
            return "sell"
        if intent.side == IntentSide.SHORT.value:
            return "buy"
    return None


def _decimal_to_adapter_qty(quantity: Decimal) -> tuple[Optional[float], tuple[str, ...]]:
    if quantity <= 0:
        return None, (REASON_INVALID_QUANTITY,)
    as_float = float(quantity)
    roundtrip = Decimal(str(as_float))
    if roundtrip > quantity:
        return None, (REASON_QUANTITY_ROUNDING_INCREASES_RISK,)
    if roundtrip != quantity:
        return None, (REASON_QUANTITY_PRECISION_LOSS,)
    return as_float, ()


def _resolve_price_policy(
    *,
    order_type: str,
    price_policy: str,
) -> tuple[Optional[float], tuple[str, ...], tuple[str, ...]]:
    rejected_unbound: list[str] = []
    if order_type == "market":
        if price_policy == _PRICE_POLICY_EXPLICIT_NONE:
            return None, (), ()
        rejected_unbound.append("price")
        return None, (REASON_UNBOUND_PRICE_POLICY,), tuple(rejected_unbound)
    if order_type == "limit":
        if price_policy.startswith(_PRICE_POLICY_EXPLICIT_PREFIX):
            raw = price_policy[len(_PRICE_POLICY_EXPLICIT_PREFIX) :]
            try:
                price_decimal = Decimal(raw)
            except Exception:
                return None, (REASON_UNBOUND_PRICE_POLICY,), ("price",)
            if price_decimal <= 0:
                return None, (REASON_UNBOUND_PRICE_POLICY,), ("price",)
            price_float = float(price_decimal)
            if Decimal(str(price_float)) != price_decimal:
                return None, (REASON_QUANTITY_PRECISION_LOSS,), ("price",)
            return price_float, (), ()
        rejected_unbound.append("price")
        return None, (REASON_UNBOUND_PRICE_POLICY,), tuple(rejected_unbound)
    rejected_unbound.append("price")
    return None, (REASON_UNBOUND_ADAPTER_FIELD,), tuple(rejected_unbound)


def _build_adapter_meta(intent: CanonicalOrderIntentV1) -> tuple[tuple[str, str], ...]:
    pairs = (
        ("canonical_intent_id", intent.intent_id),
        ("canonical_semantic_digest", intent.semantic_digest),
        ("canonical_quantity_provenance", intent.quantity_provenance),
        ("canonical_provenance_digest", intent.provenance_digest),
        ("canonical_decision_id", intent.decision_id),
        ("transformation_id", TRANSFORMATION_ID),
        ("transformation_version", TRANSFORMATION_VERSION),
        ("field_mapping_version", FIELD_MAPPING_VERSION),
        ("transformation_required_acknowledged", "true"),
        ("structural_adapter_compatibility_only", "true"),
    )
    return tuple(sorted(pairs))


def transform_canonical_order_intent_v1_to_adapter_order_intent_v1(
    intent: CanonicalOrderIntentV1,
    *,
    transformation_id: str = TRANSFORMATION_ID,
) -> CanonicalOrderIntentTransformResultV1:
    """Explicit offline transformation from canonical intent to adapter OrderIntentV1 shape."""

    if not isinstance(intent, CanonicalOrderIntentV1):
        return _blocked_transform_result((REASON_INVALID_INPUT_TYPE,))
    if transformation_id != TRANSFORMATION_ID:
        return _blocked_transform_result((REASON_UNBOUND_TRANSFORMATION,))
    if intent.intent_version != INTENT_VERSION:
        return _blocked_transform_result((REASON_INVALID_CANONICAL_INTENT_VERSION,))

    validation = validate_canonical_order_intent_v1(intent)
    if validation.validation_status != ValidationStatus.VALID.value:
        return _blocked_transform_result(validation.reason_codes)

    reasons: list[str] = []
    reasons.extend(_validate_instrument_for_transform(intent))
    reasons.extend(_validate_reduce_only_semantics(intent))

    if not intent.quantity_provenance:
        reasons.append(REASON_MISSING_QUANTITY_PROVENANCE)

    adapter_side = _adapter_side_for_intent(intent)
    if adapter_side is None:
        reasons.append(REASON_UNSUPPORTED_SIDE)

    order_type = _ORDER_TYPE_POLICY_BINDINGS.get(intent.order_type_policy)
    if order_type is None:
        reasons.append(REASON_UNSUPPORTED_ORDER_TYPE_POLICY)

    tif = _TIME_IN_FORCE_POLICY_BINDINGS.get(intent.time_in_force_policy)
    if tif is None:
        reasons.append(REASON_UNSUPPORTED_TIME_IN_FORCE_POLICY)

    qty: Optional[float] = None
    qty_reasons: tuple[str, ...] = ()
    if not reasons:
        qty, qty_reasons = _decimal_to_adapter_qty(intent.quantity)
        reasons.extend(qty_reasons)

    price: Optional[float] = None
    rejected_unbound_fields: list[str] = []
    price_reasons: tuple[str, ...] = ()
    if not reasons and order_type is not None:
        price, price_reasons, rejected = _resolve_price_policy(
            order_type=order_type,
            price_policy=intent.price_policy,
        )
        reasons.extend(price_reasons)
        rejected_unbound_fields.extend(rejected)

    if intent.intent_action == IntentAction.NO_ACTION.value:
        reasons.append(REASON_NO_ACTION_NOT_SUBMITTABLE)

    if reasons:
        return _blocked_transform_result(tuple(dict.fromkeys(reasons)))

    assert adapter_side is not None
    assert order_type is not None
    assert tif is not None
    assert qty is not None

    post_only = intent.max_slippage_policy == _POST_ONLY_POLICY
    rejected_unbound_fields.extend(
        field_name
        for field_name in ("client_id", "venue", "account")
        if field_name not in {"client_id"}
    )

    adapter_intent = AdapterOrderIntentV1StructuralV1(
        symbol=intent.instrument_id,
        side=adapter_side,
        qty=qty,
        order_type=order_type,
        price=price,
        tif=tif,
        post_only=post_only,
        reduce_only=intent.reduce_only,
        client_id=None,
        meta=_build_adapter_meta(intent),
    )
    target_digest = compute_adapter_order_intent_structural_digest(adapter_intent)
    lossless_fields = (
        "instrument_id->symbol",
        "side/intent_action->side",
        "quantity->qty",
        "order_type_policy->order_type",
        "time_in_force_policy->tif",
        "reduce_only",
        "quantity_provenance->meta",
        "semantic_digest->meta",
        "provenance_digest->meta",
    )
    descriptor = CanonicalOrderIntentTransformationDescriptorV1(
        source_contract=CONTRACT_NAME,
        source_version=CONTRACT_VERSION,
        target_contract=TARGET_CONTRACT_NAME,
        target_version=TARGET_CONTRACT_VERSION,
        transformation_id=TRANSFORMATION_ID,
        transformation_version=TRANSFORMATION_VERSION,
        field_mapping_version=FIELD_MAPPING_VERSION,
        source_digest=intent.semantic_digest,
        target_digest=target_digest,
        lossless_fields=lossless_fields,
        rejected_unbound_fields=tuple(
            dict.fromkeys((*rejected_unbound_fields, "client_id", "venue", "account"))
        ),
        runtime_effect=False,
        order_effect=False,
        authority_effect=False,
        network_effect=False,
        adapter_submission_effect=False,
        transformation_required_acknowledged=intent.transformation_required,
        source_quantity_provenance=intent.quantity_provenance,
    )

    return CanonicalOrderIntentTransformResultV1(
        outcome=CanonicalOrderIntentTransformOutcome.PASS,
        adapter_intent=adapter_intent,
        descriptor=descriptor,
        reason_codes=(REASON_PASS,),
    )


def canonical_order_intent_transformation_schema_v1() -> dict[str, Any]:
    return {
        "transformation_id": TRANSFORMATION_ID,
        "transformation_version": TRANSFORMATION_VERSION,
        "field_mapping_version": FIELD_MAPPING_VERSION,
        "source_contract": CONTRACT_NAME,
        "source_version": CONTRACT_VERSION,
        "target_contract": TARGET_CONTRACT_NAME,
        "target_version": TARGET_CONTRACT_VERSION,
        "target_owner_module": TARGET_OWNER_MODULE,
        "target_type_name": TARGET_TYPE_NAME,
        "invariants": {
            "transformation_is_explicit": True,
            "transformation_is_deterministic": True,
            "transformation_is_side_effect_free": True,
            "transformation_is_fail_closed": True,
            "transformation_preserves_quantity_provenance": True,
            "transformation_must_not_increase_risk": True,
            "direct_cast_remains_forbidden": True,
            "runtime_effect": False,
            "order_effect": False,
            "authority_effect": False,
            "network_effect": False,
            "adapter_submission_effect": False,
            "structural_adapter_compatibility_only": True,
            "full_adapter_compatibility_proven": False,
        },
        "order_type_policy_bindings": dict(_ORDER_TYPE_POLICY_BINDINGS),
        "time_in_force_policy_bindings": dict(_TIME_IN_FORCE_POLICY_BINDINGS),
        "reason_codes": sorted(
            {
                REASON_PASS,
                REASON_INVALID_INPUT_TYPE,
                REASON_INVALID_CANONICAL_INTENT_VERSION,
                REASON_UNSUPPORTED_SIDE,
                REASON_UNSUPPORTED_ORDER_TYPE_POLICY,
                REASON_UNSUPPORTED_TIME_IN_FORCE_POLICY,
                REASON_UNBOUND_PRICE_POLICY,
                REASON_MISSING_INSTRUMENT,
                REASON_QUANTITY_PRECISION_LOSS,
                REASON_QUANTITY_ROUNDING_INCREASES_RISK,
                REASON_CONTRADICTORY_REDUCE_ONLY_SEMANTICS,
                REASON_UNBOUND_ADAPTER_FIELD,
                REASON_UNBOUND_TRANSFORMATION,
                REASON_MISSING_QUANTITY_PROVENANCE,
                REASON_INVALID_QUANTITY,
                REASON_ADAPTER_CAST_FORBIDDEN,
                REASON_TRANSFORMATION_REQUIRED,
                REASON_NON_FUTURES_INSTRUMENT,
                REASON_BITCOIN_SPECIFIC_DIRECTION,
            }
        ),
    }


def canonical_order_intent_schema_v1() -> dict[str, Any]:
    return {
        "contract_name": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "schema_version": SCHEMA_VERSION,
        "package_marker": PACKAGE_MARKER,
        "implementation_digest": IMPLEMENTATION_DIGEST,
        "deterministic_serialization_version": DETERMINISTIC_SERIALIZATION_VERSION,
        "invariants": {
            "futures_only": FUTURES_ONLY,
            "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
            "spot_allowed": SPOT_ALLOWED,
            "synthetic_spot_allowed": SYNTHETIC_SPOT_ALLOWED,
            "no_order_without_quantity_provenance": True,
            "execution_eligible": False,
            "adapter_compatible": False,
            "submission_authorized": False,
            "transformation_required": True,
            "authority_effect": AUTHORITY_EFFECT_NONE,
            "runtime_effect": RUNTIME_EFFECT_NONE,
            "network_effect": NETWORK_EFFECT_NONE,
            "credential_effect": CREDENTIAL_EFFECT_NONE,
            "no_default_quantity": True,
            "no_implicit_adapter_compatibility": True,
            "no_direct_submission": True,
        },
        "intent_actions": [action.value for action in IntentAction],
        "position_effects": [effect.value for effect in PositionEffect],
        "quantity_chain_upstream": [
            "canonical_trading_decision",
            "capital_envelope",
            "pre_sizing_risk",
            "canonical_position_sizing",
            "post_sizing_risk",
            "canonical_order_intent",
            "explicit_adapter_transformation",
        ],
        "reason_codes": sorted(
            {
                REASON_PASS,
                REASON_MISSING_QUANTITY_PROVENANCE,
                REASON_INVALID_QUANTITY,
                REASON_SIZING_NOT_PASS,
                REASON_MISSING_DECISION_REF,
                REASON_MISSING_CAPITAL_ENVELOPE_REF,
                REASON_MISSING_PRE_SIZING_RISK_REF,
                REASON_MISSING_SIZING_RESULT_REF,
                REASON_MISSING_POST_SIZING_RISK_REF,
                REASON_INVALID_SIDE_ACTION_COMBINATION,
                REASON_EXIT_WITHOUT_REDUCE_ONLY,
                REASON_REDUCE_EXPOSURE_INCREASE,
                REASON_ENTER_LONG_WRONG_POSITION_EFFECT,
                REASON_ENTER_SHORT_WRONG_POSITION_EFFECT,
                REASON_IMPLICIT_REVERSAL,
                REASON_NON_FUTURES_INSTRUMENT,
                REASON_BITCOIN_SPECIFIC_DIRECTION,
                REASON_INVALID_DIGEST,
                REASON_NO_ACTION_NOT_SUBMITTABLE,
                REASON_DEFAULT_QUANTITY_FORBIDDEN,
                REASON_ADAPTER_CAST_FORBIDDEN,
                REASON_DIRECT_SUBMISSION_FORBIDDEN,
                REASON_TRANSFORMATION_REQUIRED,
                REASON_VENUE_FIELD_IN_CANONICAL,
                REASON_MUTABLE_INTENT,
                REASON_MISSING_PROVENANCE,
                REASON_INVALID_INPUT_TYPE,
                REASON_INVALID_CANONICAL_INTENT_VERSION,
                REASON_UNSUPPORTED_SIDE,
                REASON_UNSUPPORTED_ORDER_TYPE_POLICY,
                REASON_UNSUPPORTED_TIME_IN_FORCE_POLICY,
                REASON_UNBOUND_PRICE_POLICY,
                REASON_MISSING_INSTRUMENT,
                REASON_QUANTITY_PRECISION_LOSS,
                REASON_QUANTITY_ROUNDING_INCREASES_RISK,
                REASON_CONTRADICTORY_REDUCE_ONLY_SEMANTICS,
                REASON_UNBOUND_ADAPTER_FIELD,
                REASON_UNBOUND_TRANSFORMATION,
            }
        ),
        "transformation_contract": canonical_order_intent_transformation_schema_v1(),
    }
