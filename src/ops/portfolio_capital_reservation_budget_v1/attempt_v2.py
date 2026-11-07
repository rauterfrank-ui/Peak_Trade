"""Owned submit-attempt creation in the original budget transaction.

No standalone attempt ledger, clock substitution, legacy identity relabelling,
permit issuance or transport. The source and submit revisions are actual rows
of this owner's existing history, not arbitrary caller version strings.
"""

from uuid import uuid4

from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    ExternalEffectPermitV1,
    assert_permit_matches_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    PortfolioExecutionReconciliationIdentityV2,
)

from .durable_store_v1 import digest
from .plan_origin_v1 import PortfolioExecutionPlanContextV1


def plan_context_locked_v1(owner, reservation_id, envelope):
    from .execution_v1 import validate_link_v1

    found = owner._require_locked(reservation_id)
    if (
        found is None
        or found[1].state.value != "COMMITTED"
        or owner._store is None
        or not owner._admitted
    ):
        raise ValueError("EXECUTION_SUBMIT_OWNER_FENCED")
    link = owner._execution_links.get(reservation_id)
    if link is None or link["phase"] != "PLAN_BOUND":
        raise ValueError("EXECUTION_SUBMIT_REPLAY_OR_UNBOUND")
    if "plan_origin" not in link:
        raise ValueError("ORIGINAL_EXECUTION_PLAN_ORIGIN_REQUIRED")
    validate_link_v1(owner, reservation_id, link)
    assert_envelope_unmodified_v1(envelope)
    if link["envelope"] != envelope.to_runtime_json_v1():
        raise ValueError("PORTFOLIO_EXECUTION_ENVELOPE_MISMATCH")
    return PortfolioExecutionPlanContextV1(
        root=str(owner._store.root),
        account=owner._account_identity,
        reservation_id=reservation_id,
        envelope_id=envelope.envelope_id,
        envelope_digest=envelope.envelope_digest,
        plan_origin_digest=link["plan_origin"]["digest"],
        order_environment=link["plan_origin"]["venue_plan"]["environment"],
    )


def inspect_plan_context_locked_v1(owner, reservation_id, envelope, context):
    if type(context) is not PortfolioExecutionPlanContextV1:
        raise ValueError("ORIGINAL_EXECUTION_PLAN_CONTEXT_TYPE_REQUIRED")
    actual = plan_context_locked_v1(owner, reservation_id, envelope)
    if actual != context:
        raise ValueError("ORIGINAL_EXECUTION_PLAN_CONTEXT_MISMATCH")
    return {
        "root": actual.root,
        "account": actual.account,
        "reservation_id": actual.reservation_id,
        "envelope_digest": actual.envelope_digest,
        "plan_origin_digest": actual.plan_origin_digest,
        "order_environment": actual.order_environment,
        "context_kind": "ORIGINAL_PLAN_BEFORE_SUBMIT_ATTEMPT",
        "scope": "ORIGINAL_COMMITTED_PLAN_CONTEXT_ONLY",
    }


def _identity_from_originals(owner, reservation_id, link, source, attempt_id):
    state = source["state"]
    reservation = next(r for r in state["reservations"] if r["reservation_id"] == reservation_id)
    origin = link["plan_origin"]
    intent, plan, envelope = (
        origin["canonical_order_intent"],
        origin["venue_plan"],
        link["envelope"],
    )
    permit = link["external_effect_permit"]
    return PortfolioExecutionReconciliationIdentityV2(
        canonical_decision_id=reservation["decision_id"],
        decision_outcome=intent["intent_action"],
        selected_side=intent["side"],
        instrument_id=reservation["binding"]["bound"]["instrument_id"],
        native_id=plan["instrument_id"],
        account_identity=state["account_identity"],
        execution_environment=plan["environment"],
        venue=state["capital_scope"]["bound_venue_identity"],
        envelope_identity=envelope["envelope_id"],
        envelope_digest=envelope["envelope_digest"],
        final_quantity=envelope["quantity"],
        quantity_unit=envelope["quantity_unit"],
        order_type=envelope["order_type"],
        order_price=envelope["price"],
        clordid=plan["clordid"],
        exchange_ord_id=None,
        canonical_intent_digest=intent["semantic_digest"],
        plan_origin_digest=origin["digest"],
        send_permit_id=permit["permit_id"],
        send_authority_ref=permit["authority_ref"],
        submit_attempt_id=attempt_id,
        budget_owner_root=str(owner._store.root),
        portfolio_reservation_id=reservation_id,
        slot_id=reservation["slot_id"],
        cycle_id=reservation["cycle_id"],
        reservation_binding_digest=digest(reservation["binding"]),
        budget_source_sequence=source["sequence"],
        budget_source_digest=source["digest"],
        budget_submit_sequence=source["sequence"] + 1,
    )


def validate_attempt_locked_v2(owner, reservation_id, link, identity, *, pending=False):
    if (
        owner._store is None
        or identity.portfolio_reservation_id != reservation_id
        or identity.budget_owner_root != str(owner._store.root)
        or type(identity.budget_source_sequence) is not int
        or type(identity.budget_submit_sequence) is not int
        or identity.budget_submit_sequence != identity.budget_source_sequence + 1
        or len(identity.submit_attempt_id) != 32
        or any(c not in "0123456789abcdef" for c in identity.submit_attempt_id)
        or "plan_origin" not in link
        or "external_effect_permit" not in link
    ):
        raise ValueError("ORIGINAL_EXECUTION_ATTEMPT_SCOPE_INVALID")
    source = owner._store.read_revision_v1(
        identity.budget_source_sequence, identity.budget_source_digest
    )
    original = source["state"]["execution_links"].get(reservation_id)
    if not (
        isinstance(original, dict)
        and original["phase"] == "PLAN_BOUND"
        and original["identity"] is None
        and original["reconciliation"] is None
        and original["envelope"] == link["envelope"]
        and original.get("plan_origin") == link["plan_origin"]
        and "external_effect_permit" not in original
        and _identity_from_originals(
            owner, reservation_id, link, source, identity.submit_attempt_id
        )
        == identity
    ):
        raise ValueError("ORIGINAL_EXECUTION_ATTEMPT_SOURCE_MISMATCH")
    if pending:
        if (owner._store.sequence, owner._store.head) != (source["sequence"], source["digest"]):
            raise ValueError("ORIGINAL_EXECUTION_ATTEMPT_PARENT_CHANGED")
        return
    committed = owner._store.read_revision_v1(identity.budget_submit_sequence)
    actual = committed["state"]["execution_links"].get(reservation_id, {})
    if (
        committed["previous"] != source["digest"]
        or actual.get("phase") != "SUBMIT_MAY_HAVE_OCCURRED"
        or any(
            actual.get(key) != link.get(key)
            for key in ("identity", "envelope", "plan_origin", "external_effect_permit")
        )
    ):
        raise ValueError("ORIGINAL_EXECUTION_ATTEMPT_COMMIT_UNPROVEN")


def begin_submit_locked_v2(owner, reservation_id, envelope, context, permit):
    from .execution_v1 import detached, validate_link_v1

    inspect_plan_context_locked_v1(owner, reservation_id, envelope, context)
    if type(permit) is not ExternalEffectPermitV1:
        raise ValueError("EXECUTION_SEND_PERMIT_TYPE_INVALID")
    assert_permit_matches_envelope_v1(permit, envelope)
    source = owner._store.read_revision_v1(owner._store.sequence, owner._store.head)
    link = {
        **owner._execution_links[reservation_id],
        "phase": "SUBMIT_MAY_HAVE_OCCURRED",
        "external_effect_permit": {
            "permit_id": permit.permit_id,
            **permit.to_canonical_payload_v1(),
        },
    }
    identity = _identity_from_originals(owner, reservation_id, link, source, uuid4().hex)
    link["identity"] = identity.to_dict()
    validate_link_v1(owner, reservation_id, link, pending_attempt=True)
    owner._execution_links[reservation_id] = detached(link)
    owner._persist_locked()
    try:
        validate_link_v1(owner, reservation_id, link)
    except Exception as exc:
        # An acknowledged commit followed by failed readback never opens a retry.
        owner._admitted = False
        owner._recovery_required = owner._storage_failed = True
        raise ValueError("ORIGINAL_EXECUTION_ATTEMPT_READBACK_UNPROVEN") from exc
    return identity


def inspect_started_attempt_locked_v2(owner, reservation_id, envelope, identity, permit):
    from .execution_v1 import validate_link_v1

    found = owner._require_locked(reservation_id)
    if found is None or found[1].state.value != "COMMITTED" or not owner._admitted:
        raise ValueError("EXECUTION_SUBMIT_OWNER_FENCED")
    link = owner._execution_links.get(reservation_id)
    if (
        not link
        or link["phase"] != "SUBMIT_MAY_HAVE_OCCURRED"
        or link["identity"] != identity.to_dict()
    ):
        raise ValueError("ORIGINAL_EXECUTION_ATTEMPT_IDENTITY_MISMATCH")
    assert_permit_matches_envelope_v1(permit, envelope)
    if link["envelope"] != envelope.to_runtime_json_v1() or link["external_effect_permit"] != {
        "permit_id": permit.permit_id,
        **permit.to_canonical_payload_v1(),
    }:
        raise ValueError("ORIGINAL_EXECUTION_ATTEMPT_PERMIT_MISMATCH")
    validate_link_v1(owner, reservation_id, link)
    return identity.to_dict()
