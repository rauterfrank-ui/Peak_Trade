"""Original decision and venue plan retained by the existing budget writer.

This carrier is lineage, not a current admission, submit attempt or authority.
The original canonical validators and reference functions retain their meaning.
"""

from dataclasses import dataclass, fields
from decimal import Decimal, InvalidOperation

from src.governance.canonical_order_intent_v1 import (
    CanonicalOrderIntentV1,
    INTENT_VERSION,
    compute_capital_envelope_ref,
    compute_pre_sizing_risk_ref,
    compute_sizing_result_ref,
    compute_post_sizing_risk_ref,
    compute_quantity_provenance_ref,
    validate_canonical_order_intent_v1,
    _ORDER_TYPE_POLICY_BINDINGS,
    _PRICE_POLICY_EXPLICIT_NONE,
    _PRICE_POLICY_EXPLICIT_PREFIX,
    _TIME_IN_FORCE_POLICY_BINDINGS,
    _POST_ONLY_POLICY,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_td_mode_and_order_environment_authority_v1 import (
    resolve_current_productive_order_environment_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.okx_response_mapper_v1 import (
    build_venue_native_order_body_v1,
)

from .durable_store_v1 import digest
from .sizing_binding_v1 import _decode, _encode

SCHEMA = "portfolio_execution_plan_origin.v1"


@dataclass(frozen=True)
class PortfolioExecutionPlanContextV1:
    """Immutable original plan reference; no attempt, permission or admission."""

    root: str
    account: str
    reservation_id: str
    envelope_id: str
    envelope_digest: str
    plan_origin_digest: str
    order_environment: str


def bind_plan_origin_v1(canonical_intent, venue_plan):
    if (
        type(canonical_intent) is not CanonicalOrderIntentV1
        or type(venue_plan) is not VenuePlanCandidateV1
    ):
        raise ValueError("EXECUTION_PLAN_ORIGIN_TYPED_PRODUCERS_REQUIRED")
    payload = {
        "schema": SCHEMA,
        "canonical_order_intent": _encode(canonical_intent),
        "venue_plan": _encode(venue_plan),
    }
    return {**payload, "digest": digest(payload)}


def _validate_native_order_policy_v1(intent, plan, envelope):
    """Consume the original declarations at the native plan boundary.

    Ordinary market/limit plans cannot silently become IOC/FOK/post-only.
    Prices stay exact native decimals; no structural adapter float is used.
    This verifies the retained declaration, not its current risk admission.
    """
    order_type = _ORDER_TYPE_POLICY_BINDINGS.get(intent.order_type_policy)
    if order_type is None or order_type != plan.order_type:
        raise ValueError("EXECUTION_PLAN_ORIGIN_ORDER_TYPE_POLICY_MISMATCH")
    if (
        _TIME_IN_FORCE_POLICY_BINDINGS.get(intent.time_in_force_policy) != "gtc"
        or intent.max_slippage_policy == _POST_ONLY_POLICY
    ):
        raise ValueError("EXECUTION_PLAN_ORIGIN_NATIVE_EXECUTION_POLICY_UNREPRESENTED")
    if order_type == "market":
        if intent.price_policy != _PRICE_POLICY_EXPLICIT_NONE or envelope.price:
            raise ValueError("EXECUTION_PLAN_ORIGIN_MARKET_PRICE_POLICY_MISMATCH")
        return
    if not intent.price_policy.startswith(_PRICE_POLICY_EXPLICIT_PREFIX):
        raise ValueError("EXECUTION_PLAN_ORIGIN_LIMIT_PRICE_POLICY_UNBOUND")
    try:
        declared = Decimal(intent.price_policy[len(_PRICE_POLICY_EXPLICIT_PREFIX) :])
        actual = Decimal(envelope.price)
        if not (
            declared.is_finite() and actual.is_finite() and declared > 0 and actual == declared
        ):
            raise ValueError("EXECUTION_PLAN_ORIGIN_LIMIT_PRICE_POLICY_MISMATCH")
    except InvalidOperation as exc:
        raise ValueError("EXECUTION_PLAN_ORIGIN_LIMIT_PRICE_POLICY_MALFORMED") from exc


def validate_plan_origin_v1(origin, *, sizing, reservation, bound, envelope):
    if (
        not isinstance(origin, dict)
        or set(origin) != {"schema", "canonical_order_intent", "venue_plan", "digest"}
        or origin["schema"] != SCHEMA
        or origin["digest"] != digest({k: v for k, v in origin.items() if k != "digest"})
    ):
        raise ValueError("EXECUTION_PLAN_ORIGIN_SHAPE_OR_DIGEST_INVALID")
    intent = _decode(CanonicalOrderIntentV1, origin["canonical_order_intent"])
    raw_plan = origin["venue_plan"]
    if (
        not isinstance(raw_plan, dict)
        or set(raw_plan) != {f.name for f in fields(VenuePlanCandidateV1)}
        or type(raw_plan["reduce_only"]) is not bool
        or not isinstance(raw_plan["venue_native_payload"], dict)
        or any(
            type(v) is not str
            for k, v in raw_plan.items()
            if k not in {"reduce_only", "venue_native_payload"}
        )
    ):
        raise ValueError("EXECUTION_PLAN_ORIGIN_VENUE_PLAN_INVALID")
    plan = VenuePlanCandidateV1(**raw_plan)
    resolve_current_productive_order_environment_v1(execution_mode=plan.environment)
    decision = sizing.decision
    if not (
        intent.intent_version == INTENT_VERSION
        and len(intent.semantic_digest) == 64
        and validate_canonical_order_intent_v1(intent).validation_status == "VALID"
        and intent.decision_id == reservation.decision_id
        and intent.instrument_id == bound["instrument_id"]
        and intent.intent_action in {"ENTER_LONG", "ENTER_SHORT"}
        and decision.selected_side.upper() in {intent.side, intent.intent_action}
        and intent.quantity == decision.final_quantity
        and intent.quantity_unit == envelope.quantity_unit == "CONTRACTS"
        and intent.config_digest == sizing.applied_input.config_digest
        and intent.capital_envelope_ref == compute_capital_envelope_ref(decision)
        and intent.pre_sizing_risk_ref == compute_pre_sizing_risk_ref(decision)
        and intent.sizing_result_ref == compute_sizing_result_ref(decision)
        and intent.post_sizing_risk_ref == compute_post_sizing_risk_ref(decision)
        and intent.quantity_provenance
        == compute_quantity_provenance_ref(decision.quantity_provenance)
        and intent.instrument_metadata_ref == decision.quantity_provenance.instrument_metadata_ref
    ):
        raise ValueError("EXECUTION_PLAN_ORIGIN_DECISION_OR_SIZING_MISMATCH")
    expected = bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref=envelope.admission_ref,
        provenance_ref=envelope.provenance_ref,
        creation_epoch=envelope.creation_epoch,
    )
    body = build_venue_native_order_body_v1(
        client_order_id=plan.clordid,
        instrument=plan.instrument_id,
        order_type=plan.order_type,
        side=plan.side,
        quantity=plan.quantity,
        td_mode=plan.td_mode,
        px=envelope.price or None,
        reduce_only=plan.reduce_only,
    )
    if envelope.pos_side:
        body["posSide"] = envelope.pos_side
    if expected != envelope or body != plan.venue_native_payload:
        raise ValueError("EXECUTION_PLAN_ORIGIN_ENVELOPE_MISMATCH")
    _validate_native_order_policy_v1(intent, plan, envelope)
    return plan.environment
