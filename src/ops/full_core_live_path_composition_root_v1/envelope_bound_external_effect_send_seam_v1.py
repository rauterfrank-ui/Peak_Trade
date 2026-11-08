"""Envelope-bound single-use Full-Core external-effect send seam.

Consume the permit on durable storage before invoking the injected transport.
Standing EXTERNAL_EFFECT_AUTHORIZED remains false. Host/autonomy loops are not
joined. Direct STEP-29Q submission remains forbidden.

This slice never opens a venue socket unless an exact envelope-bound
single-use permit authorizes a later actual-POST Owner-GO. Standing
REAL_VENUE_POST_ALLOWED remains false. Tests inject a non-networking
transport. The readiness Owner-GO is not send permission.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from src.ops.full_core_live_path_composition_root_v1.current_productive_post_safety_veto_v1 import (
    CurrentPostSafetyVetoError,
    resolve_current_post_safety_context_v1,
)
from .current_productive_post_venue_quantity_v1 import (
    CurrentPostVenueQuantityError,
    inspect_current_post_venue_quantity_v1,
)
from .current_productive_post_pending_observation_v1 import (
    CurrentPostPendingObservationError,
    inspect_current_post_pending_v1,
)

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from src.governance.canonical_order_intent_v1 import (
    CanonicalOrderIntentV1,
    reject_direct_submission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    REAL_VENUE_POST_ALLOWED,
    SUBMIT_UNLOCKED,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    TRADE_ORDER_PATH,
    evaluate_external_effect_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
    DURABLE_STATE_SENT_INITIATED,
    FullCoreExternalEffectDurableConsumeError,
    load_external_effect_durable_consume_v1,
    persist_external_effect_durable_consume_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    ExternalEffectPermitV1,
    FullCoreExternalEffectPermitError,
    assert_permit_matches_envelope_v1,
    permit_authorizes_one_shot_real_post_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    FullCoreFinalOrderEnvelopeError,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1 import (
    FullCorePostSubmitJoinResultV1,
    join_full_core_post_result_to_lifecycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreProductiveHttpPostError,
    FullCoreProductiveTradeOrderPostTransportV1,
    FullCoreTradeOrderPostResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    FullCoreSendCredentialHandleV1,
)


class FullCoreEnvelopeBoundSendSeamError(RuntimeError):
    """Fail-closed envelope-bound send-seam violation."""


@dataclass(frozen=True)
class EnvelopeBoundSendSeamResultV1:
    mocked_post_count: int
    real_post_count: int
    venue_live_contact: bool
    unknown_outcome: bool
    follow_on_submit_isolated: bool
    durable_consumed: bool
    transport_class: str
    outcome: str
    post_submit_join: FullCorePostSubmitJoinResultV1 | None = None


def _payload_from_envelope_v1(envelope: FinalOrderEnvelopeV1) -> dict[str, Any]:
    body: dict[str, Any] = {
        "clOrdId": envelope.client_order_id,
        "instId": envelope.instrument_id,
        "side": envelope.side,
        "ordType": envelope.order_type,
        "sz": envelope.quantity,
        "tdMode": envelope.td_mode,
    }
    if envelope.price:
        body["px"] = envelope.price
    if envelope.pos_side:
        body["posSide"] = envelope.pos_side
    if envelope.reduce_only is True:
        body["reduceOnly"] = True
    return body


def inspect_original_portfolio_execution_context_v1(
    *,
    envelope,
    portfolio_budget_owner=None,
    portfolio_reservation_id="",
    execution_identity=None,
    execution_plan_context=None,
    required_execution_environment=None,
):
    """Inspect original owner/hold/plan identity; never create or recover an owner."""
    if ":portfolio-reservation:" in envelope.admission_ref:
        bound_id = envelope.admission_ref.rsplit(":portfolio-reservation:", 1)[1]
        if portfolio_budget_owner is None or not bound_id or portfolio_reservation_id != bound_id:
            raise FullCoreEnvelopeBoundSendSeamError("HOST_PORTFOLIO_EXECUTION_CONTEXT_REQUIRED")
    if not any(
        (
            portfolio_budget_owner is not None,
            portfolio_reservation_id,
            execution_identity is not None,
            execution_plan_context is not None,
        )
    ):
        return None
    if (
        portfolio_budget_owner is None
        or not portfolio_reservation_id
        or (execution_identity is None and execution_plan_context is None)
    ):
        raise FullCoreEnvelopeBoundSendSeamError("PORTFOLIO_EXECUTION_CONTEXT_INCOMPLETE")
    if execution_identity is not None and execution_plan_context is not None:
        raise FullCoreEnvelopeBoundSendSeamError("PORTFOLIO_EXECUTION_CONTEXT_AMBIGUOUS")
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1,
    )

    if not isinstance(portfolio_budget_owner, PortfolioCapitalReservationBudgetOwnerV1):
        raise FullCoreEnvelopeBoundSendSeamError("ORIGINAL_PORTFOLIO_BUDGET_OWNER_REQUIRED")
    if (
        execution_plan_context is None
        and required_execution_environment is not None
        and (
            getattr(execution_identity, "execution_environment", None)
            != required_execution_environment
        )
    ):
        raise FullCoreEnvelopeBoundSendSeamError("PORTFOLIO_EXECUTION_ENVIRONMENT_MISMATCH")
    try:
        if execution_plan_context is not None:
            proof = portfolio_budget_owner.inspect_execution_plan_context_v1(
                portfolio_reservation_id, envelope, execution_plan_context
            )
            if (
                required_execution_environment is not None
                and proof["order_environment"] != required_execution_environment
            ):
                raise FullCoreEnvelopeBoundSendSeamError("PORTFOLIO_EXECUTION_ENVIRONMENT_MISMATCH")
            return proof
        return portfolio_budget_owner.inspect_execution_submit_context_v1(
            portfolio_reservation_id, envelope, execution_identity
        )
    except (ValueError, TypeError, AttributeError, KeyError) as exc:
        raise FullCoreEnvelopeBoundSendSeamError(str(exc)) from exc


def attempt_envelope_bound_external_effect_send_v1(
    *,
    envelope: FinalOrderEnvelopeV1,
    permit: Optional[ExternalEffectPermitV1],
    store_root: Path | str | None,
    transport: Optional[FullCoreProductiveTradeOrderPostTransportV1],
    handle: Optional[FullCoreSendCredentialHandleV1] = None,
    canonical_intent: Optional[CanonicalOrderIntentV1] = None,
    portfolio_budget_owner=None,
    portfolio_reservation_id: str = "",
    execution_identity=None,
    execution_plan_context=None,
    post_safety_context=None,
    post_quantity_context=None,
    post_pending_context=None,
) -> EnvelopeBoundSendSeamResultV1:
    if canonical_intent is not None:
        try:
            reject_direct_submission_v1(canonical_intent)
        except Exception as exc:
            raise FullCoreEnvelopeBoundSendSeamError(
                "DIRECT_STEP_29Q_SUBMISSION_FORBIDDEN"
            ) from exc
        raise FullCoreEnvelopeBoundSendSeamError("DIRECT_STEP_29Q_SUBMISSION_FORBIDDEN")
    if SUBMIT_UNLOCKED is True:
        raise FullCoreEnvelopeBoundSendSeamError("SUBMIT_UNLOCKED_ALONE_IS_NOT_SEND_PERMISSION")
    if EXTERNAL_EFFECT_AUTHORIZED is True:
        raise FullCoreEnvelopeBoundSendSeamError("STANDING_EXTERNAL_EFFECT_MUST_REMAIN_FALSE")
    standing = evaluate_external_effect_v1()
    if standing.external_effect_authorized is True:
        raise FullCoreEnvelopeBoundSendSeamError("STANDING_EXTERNAL_EFFECT_MUST_REMAIN_FALSE")
    if permit is None:
        raise FullCoreEnvelopeBoundSendSeamError("NO_PERMIT")
    try:
        assert_envelope_unmodified_v1(envelope)
        assert_permit_matches_envelope_v1(permit, envelope)
    except (FullCoreExternalEffectPermitError, FullCoreFinalOrderEnvelopeError) as exc:
        raise FullCoreEnvelopeBoundSendSeamError(str(exc) or "WRONG_PERMIT") from exc
    if store_root is None:
        raise FullCoreEnvelopeBoundSendSeamError("DURABLE_STORE_REQUIRED")
    if transport is None:
        raise FullCoreEnvelopeBoundSendSeamError("TRANSPORT_MISSING")
    if handle is None or handle.bound is not True:
        raise FullCoreEnvelopeBoundSendSeamError("CREDENTIAL_HANDLE_MISSING")
    if handle.material_loaded is True:
        raise FullCoreEnvelopeBoundSendSeamError("CREDENTIAL_MATERIAL_LOADED_FORBIDDEN")
    if ":portfolio-reservation:" in envelope.admission_ref:
        bound_id = envelope.admission_ref.rsplit(":portfolio-reservation:", 1)[1]
        if portfolio_budget_owner is None or not bound_id or portfolio_reservation_id != bound_id:
            raise FullCoreEnvelopeBoundSendSeamError("HOST_PORTFOLIO_EXECUTION_CONTEXT_REQUIRED")
    existing = load_external_effect_durable_consume_v1(store_root=store_root)
    if existing.get("durable_consumed") is True:
        record = existing.get("record") or {}
        if str(record.get("permit_id") or "") == permit.permit_id:
            raise FullCoreEnvelopeBoundSendSeamError("CONSUMED_PERMIT")
        if str(record.get("envelope_id") or "") == envelope.envelope_id:
            raise FullCoreEnvelopeBoundSendSeamError("REPLAYED_PERMIT")
        raise FullCoreEnvelopeBoundSendSeamError("FOLLOW_ON_SUBMIT_DENIED")
    context = inspect_original_portfolio_execution_context_v1(
        envelope=envelope,
        portfolio_budget_owner=portfolio_budget_owner,
        portfolio_reservation_id=portfolio_reservation_id,
        execution_identity=execution_identity,
        execution_plan_context=execution_plan_context,
    )
    owned_identity = None
    if post_pending_context is not None:
        try:
            inspect_current_post_pending_v1(
                post_pending_context,
                envelope=envelope,
                stage="BEFORE_BUDGET_SUBMIT",
                expected_account=context["account"] if context is not None else None,
            )
        except CurrentPostPendingObservationError as exc:
            raise FullCoreEnvelopeBoundSendSeamError(str(exc)) from exc
    if post_quantity_context is not None:
        try:
            inspect_current_post_venue_quantity_v1(
                post_quantity_context, envelope=envelope, stage="BEFORE_BUDGET_SUBMIT"
            )
        except CurrentPostVenueQuantityError as exc:
            raise FullCoreEnvelopeBoundSendSeamError(str(exc)) from exc
    if post_safety_context is not None:
        try:
            resolve_current_post_safety_context_v1(
                envelope, post_safety_context, stage="BEFORE_BUDGET_SUBMIT"
            )
        except CurrentPostSafetyVetoError as exc:
            raise FullCoreEnvelopeBoundSendSeamError(str(exc)) from exc
    if context is not None:
        # Both durable barriers precede any transport. A crash between them is
        # uncertain and must be reconciled; it never authorizes a resend.
        if execution_plan_context is not None:
            owned_identity = portfolio_budget_owner.begin_execution_submit_v2(
                portfolio_reservation_id,
                envelope,
                execution_plan_context,
                permit,
                transport_store_root=store_root,
            )
        else:
            portfolio_budget_owner.mark_execution_submit_boundary_v1(
                portfolio_reservation_id, execution_identity, external_effect_permit=permit
            )
    try:
        persist_external_effect_durable_consume_v1(
            store_root=store_root,
            permit=permit,
            envelope=envelope,
            durable_state=DURABLE_STATE_SENT_INITIATED,
            post_count=1,
            outcome="SENT_INITIATED_UNKNOWN_UNTIL_TRANSPORT",
            **({"execution_identity": owned_identity} if owned_identity is not None else {}),
        )
    except FullCoreExternalEffectDurableConsumeError as exc:
        raise FullCoreEnvelopeBoundSendSeamError(str(exc)) from exc
    payload = _payload_from_envelope_v1(envelope)
    if owned_identity is not None:
        readback = load_external_effect_durable_consume_v1(store_root=store_root)
        record = readback.get("record") or {}
        if not (
            readback.get("durable_consumed") is True
            and record.get("durable_state") == DURABLE_STATE_SENT_INITIATED
            and record.get("execution_identity") == owned_identity.to_dict()
            and record.get("execution_identity_digest") == owned_identity.identity_digest()
        ):
            raise FullCoreEnvelopeBoundSendSeamError("ORIGINAL_EXECUTION_PERMIT_READBACK_UNPROVEN")
        portfolio_budget_owner.inspect_started_execution_attempt_v2(
            portfolio_reservation_id, envelope, owned_identity, permit
        )
    one_shot = permit_authorizes_one_shot_real_post_v1(permit)
    if REAL_VENUE_POST_ALLOWED is True:
        raise FullCoreEnvelopeBoundSendSeamError("STANDING_REAL_VENUE_POST_FORBIDDEN")
    try:
        result = transport.post_trade_order(
            payload=payload,
            permit_id=permit.permit_id,
            envelope_id=envelope.envelope_id,
            envelope_digest=envelope.envelope_digest,
            one_shot_real_post=one_shot,
        )
    except FullCoreProductiveHttpPostError as exc:
        msg = str(exc)
        if msg.startswith(("POST_SAFETY", "POST_QUANTITY", "POST_PENDING")):
            raise FullCoreEnvelopeBoundSendSeamError(msg) from exc
        if msg in {
            "REDIRECT_OFF_HOST_FORBIDDEN",
            "HOST_NOT_EEA_OKX",
            "WWW_OKX_FORBIDDEN",
            "K1_SIGNING_HANDLE_UNAVAILABLE",
        }:
            raise FullCoreEnvelopeBoundSendSeamError(msg) from exc
        raise FullCoreEnvelopeBoundSendSeamError("UNKNOWN_OUTCOME") from exc
    except Exception as exc:
        raise FullCoreEnvelopeBoundSendSeamError("UNKNOWN_OUTCOME") from exc
    if not isinstance(result, FullCoreTradeOrderPostResultV1):
        raise FullCoreEnvelopeBoundSendSeamError("UNKNOWN_OUTCOME")
    if REAL_VENUE_POST_ALLOWED is True:
        raise FullCoreEnvelopeBoundSendSeamError("STANDING_REAL_VENUE_POST_FORBIDDEN")
    if result.venue_live_contact is True and one_shot is not True:
        raise FullCoreEnvelopeBoundSendSeamError("REAL_VENUE_POST_FORBIDDEN_IN_THIS_SLICE")
    if str(result.endpoint) != TRADE_ORDER_PATH:
        raise FullCoreEnvelopeBoundSendSeamError("TRADE_ORDER_PATH_DRIFT")
    mocked = 1 if result.post_attempted is True and result.venue_live_contact is not True else 0
    real = 1 if result.venue_live_contact is True and one_shot is True else 0
    follow_on = load_external_effect_durable_consume_v1(store_root=store_root)
    isolated = (
        follow_on.get("durable_consumed") is True and follow_on.get("resubmit_allowed") is not True
    )
    post_submit_join = join_full_core_post_result_to_lifecycle_v1(
        result=result,
        sent_clordid=str(envelope.client_order_id),
        submit_count=1,
    )
    return EnvelopeBoundSendSeamResultV1(
        mocked_post_count=mocked,
        real_post_count=real,
        venue_live_contact=bool(result.venue_live_contact),
        unknown_outcome=bool(result.unknown_outcome),
        follow_on_submit_isolated=isolated is True,
        durable_consumed=True,
        transport_class=str(result.transport_class),
        outcome=(
            "ONE_SHOT_REAL_POST_RECORDED" if real == 1 else "MOCKED_POST_RECORDED_NO_VENUE_CONTACT"
        ),
        post_submit_join=post_submit_join,
    )


def prove_follow_on_submit_isolated_v1(
    *,
    envelope: FinalOrderEnvelopeV1,
    permit: ExternalEffectPermitV1,
    store_root: Path | str,
    transport: FullCoreProductiveTradeOrderPostTransportV1,
    handle: FullCoreSendCredentialHandleV1,
    portfolio_budget_owner=None,
    portfolio_reservation_id: str = "",
    execution_identity=None,
    execution_plan_context=None,
) -> bool:
    try:
        attempt_envelope_bound_external_effect_send_v1(
            envelope=envelope,
            permit=permit,
            store_root=store_root,
            transport=transport,
            handle=handle,
            portfolio_budget_owner=portfolio_budget_owner,
            portfolio_reservation_id=portfolio_reservation_id,
            execution_identity=execution_identity,
            execution_plan_context=execution_plan_context,
        )
    except FullCoreEnvelopeBoundSendSeamError as exc:
        return str(exc) in {
            "CONSUMED_PERMIT",
            "REPLAYED_PERMIT",
            "FOLLOW_ON_SUBMIT_DENIED",
        }
    return False
