"""Execution linkage inside the existing budget owner's durable transaction.

No second ledger, venue calls, permits, capital calculation or submit retries.
An uncertain submission remains an obligation until exact exchange evidence.
"""

from dataclasses import replace
from decimal import Decimal
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
    assert_envelope_unmodified_v1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    ExternalEffectPermitV1,
    FullCoreExternalEffectPermitError,
    assert_permit_matches_envelope_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    FullCoreExchangeReconciliationIdentityV1,
    PortfolioExecutionReconciliationIdentityV2,
    parse_exchange_reconciliation_identity_v1,
    LocalSubmitOutcome,
    adjudicate_full_core_exchange_reconciliation_v1,
    OUTCOME_HALTED_UNRESOLVED,
    OUTCOME_CONFIRMED_CANCELED,
    OUTCOME_CONFIRMED_REJECTED,
)


def detached(value):
    return json.loads(json.dumps(value, allow_nan=False))


def validate_link_v1(owner, reservation_id, link, *, pending_attempt=False):
    if set(link) - {"external_effect_permit", "plan_origin", "transport_store_root"} != {
        "envelope",
        "identity",
        "phase",
        "reconciliation",
    }:
        raise ValueError("EXECUTION_LINK_SHAPE_INVALID")
    key = owner._by_id.get(reservation_id)
    sizing = owner._sizing_bindings.get(key)
    reservation = owner._by_key.get(key)
    if sizing is None or reservation is None:
        raise ValueError("EXECUTION_LINK_RESERVATION_MISSING")
    envelope = FinalOrderEnvelopeV1(**link["envelope"])
    assert_envelope_unmodified_v1(envelope)
    bound = owner._reservation_bindings[reservation_id]["bound"]
    if sizing.entry_cost_binding is not None:
        cost = sizing.entry_cost_binding.validate_v1(
            monetary_source=sizing.monetary_source,
            applied_input=sizing.applied_input,
            decision=sizing.decision,
        )
        observation = json.loads(sizing.entry_cost_binding.observation_json)
        record = owner._by_key[owner._by_id[reservation_id]]
        if (
            json.loads(observation["bound_instrument_json"]) != bound
            or cost["order_type"] != envelope.order_type
            or (cost["account_identity"], cost["slot_id"], cost["cycle_id"])
            != (owner._account_identity, str(record.slot_id), record.cycle_id)
        ):
            raise ValueError("EXECUTION_ENTRY_COST_CONTEXT_MISMATCH")
    if sizing.monetary_source is not None and (
        sizing.monetary_source.venue_native_id != bound["venue_native_id"]
        or sizing.monetary_source.canonical_instrument_id != bound["instrument_id"]
    ):
        raise ValueError("EXECUTION_MONETARY_SOURCE_INSTRUMENT_MISMATCH")
    side = sizing.decision.selected_side.upper()
    if not (
        envelope.instrument_id == bound["venue_native_id"]
        and Decimal(envelope.quantity) == sizing.decision.final_quantity
        and envelope.quantity_unit.upper() in {"CONTRACT", "CONTRACTS"}
        and envelope.side == ("buy" if side in {"LONG", "ENTER_LONG"} else "sell")
        and side in {"LONG", "SHORT", "ENTER_LONG", "ENTER_SHORT"}
        and envelope.reduce_only is False
    ):
        raise ValueError("EXECUTION_LINK_SIZING_MISMATCH")
    if sizing.risk_binding is not None:
        sizing.risk_binding.validate_v1(
            amount=reservation.amount, decision_id=reservation.decision_id
        )
        sizing.risk_binding.validate_envelope_v1(envelope)
    order_environment = None
    if "plan_origin" in link:
        from .plan_origin_v1 import validate_plan_origin_v1

        order_environment = validate_plan_origin_v1(
            link["plan_origin"],
            sizing=sizing,
            reservation=reservation,
            bound=bound,
            envelope=envelope,
        )
    if link["phase"] == "PLAN_BOUND":
        if (
            link["identity"] is not None
            or link["reconciliation"] is not None
            or "external_effect_permit" in link
            or "transport_store_root" in link
        ):
            raise ValueError("EXECUTION_PLAN_STATE_INVALID")
        return
    if link["phase"] != "SUBMIT_MAY_HAVE_OCCURRED":
        raise ValueError("EXECUTION_LINK_PHASE_INVALID")
    if "transport_store_root" in link and not (
        type(link["transport_store_root"]) is str
        and Path(link["transport_store_root"]).is_absolute()
        and str(Path(link["transport_store_root"]).resolve()) == link["transport_store_root"]
    ):
        raise ValueError("ORIGINAL_TRANSPORT_ROOT_INVALID")
    if "external_effect_permit" in link:
        # Separate send lineage, not a replacement for capital-guard authority
        # or proof that the later durable permit barrier has been consumed.
        payload = link["external_effect_permit"]
        if not isinstance(payload, dict) or set(payload) != set(
            ExternalEffectPermitV1.__dataclass_fields__
        ):
            raise ValueError("EXECUTION_SEND_PERMIT_SHAPE_INVALID")
        try:
            assert_permit_matches_envelope_v1(ExternalEffectPermitV1(**payload), envelope)
        except FullCoreExternalEffectPermitError as exc:
            raise ValueError("EXECUTION_SEND_PERMIT_INVALID") from exc
    identity = parse_exchange_reconciliation_identity_v1(link["identity"])
    raw = identity.to_dict()
    raw.pop("contract_id")
    modern = type(identity) is PortfolioExecutionReconciliationIdentityV2
    if not (
        identity.canonical_decision_id == reservation.decision_id
        and identity.account_identity == owner._account_identity
        and identity.instrument_id == bound["instrument_id"]
        and identity.native_id == envelope.instrument_id
        and identity.envelope_identity == envelope.envelope_id
        and identity.envelope_digest == envelope.envelope_digest
        and identity.clordid == envelope.client_order_id
        and Decimal(identity.final_quantity) == Decimal(envelope.quantity)
        and identity.quantity_unit.upper() in {"CONTRACT", "CONTRACTS"}
        and identity.order_type == envelope.order_type
        and identity.order_price == envelope.price
        and identity.selected_side.upper() == side
        and identity.venue.lower() == owner._capital_scope["bound_venue_identity"].lower()
        and envelope.td_mode == owner._capital_scope["bound_td_mode"]
        and (modern or identity.execution_environment in {"LIVE", "SHADOW", "PAPER", "TESTNET"})
        and (order_environment is None or identity.execution_environment == order_environment)
        and all(
            isinstance(v, str) and v and v == v.strip()
            for k, v in raw.items()
            if k
            not in {"exchange_ord_id", "order_price"}
            | ({"budget_source_sequence", "budget_submit_sequence"} if modern else set())
        )
    ):
        raise ValueError("EXECUTION_IDENTITY_MISMATCH")
    if modern:
        from .attempt_v2 import validate_attempt_locked_v2

        validate_attempt_locked_v2(owner, reservation_id, link, identity, pending=pending_attempt)


def bind_plan_locked_v1(
    owner,
    reservation_id,
    envelope,
    *,
    canonical_intent=None,
    venue_plan=None,
    core_parent=None,
    core_cursor_root=None,
    entry_frame_required=False,
):
    if owner._store is None or owner._require_locked(reservation_id) is None:
        raise ValueError("EXECUTION_LINK_DURABLE_ADMITTED_OWNER_REQUIRED")
    link = {
        "envelope": envelope.to_runtime_json_v1(),
        "identity": None,
        "phase": "PLAN_BOUND",
        "reconciliation": None,
    }
    if entry_frame_required or any(
        x is not None for x in (canonical_intent, venue_plan, core_parent, core_cursor_root)
    ):
        from .plan_origin_v1 import bind_plan_origin_v1

        link["plan_origin"] = bind_plan_origin_v1(
            canonical_intent,
            venue_plan,
            core_parent=core_parent,
            core_cursor_root=core_cursor_root,
            entry_frame_required=entry_frame_required,
        )
    validate_link_v1(owner, reservation_id, link)
    if any(
        rid != reservation_id and old["envelope"]["client_order_id"] == envelope.client_order_id
        for rid, old in owner._execution_links.items()
    ):
        raise ValueError("EXECUTION_CLIENT_ORDER_ID_ALREADY_BOUND")
    old = owner._execution_links.get(reservation_id)
    if old is not None:
        if old["envelope"] != link["envelope"]:
            raise ValueError("EXECUTION_PLAN_CHANGED")
        if old.get("plan_origin") != link.get("plan_origin"):
            raise ValueError("EXECUTION_PLAN_ORIGIN_CHANGED")
        return detached(old)
    owner._execution_links[reservation_id] = detached(link)
    owner._persist_locked()
    return detached(link)


def _validated_submit_link_v1(owner, reservation_id, identity, external_effect_permit=None):
    found = owner._require_locked(reservation_id)
    if found is None or found[1].state.value != "COMMITTED":
        raise ValueError("EXECUTION_SUBMIT_OWNER_FENCED")
    old = owner._execution_links.get(reservation_id)
    if old is None or old["phase"] != "PLAN_BOUND":
        raise ValueError("EXECUTION_SUBMIT_REPLAY_OR_UNBOUND")
    if not isinstance(identity, FullCoreExchangeReconciliationIdentityV1):
        raise ValueError("EXECUTION_IDENTITY_TYPE_INVALID")
    link = {**old, "phase": "SUBMIT_MAY_HAVE_OCCURRED", "identity": identity.to_dict()}
    if external_effect_permit is not None:
        if not isinstance(external_effect_permit, ExternalEffectPermitV1):
            raise ValueError("EXECUTION_SEND_PERMIT_TYPE_INVALID")
        assert_permit_matches_envelope_v1(
            external_effect_permit, FinalOrderEnvelopeV1(**old["envelope"])
        )
        link["external_effect_permit"] = {
            "permit_id": external_effect_permit.permit_id,
            **external_effect_permit.to_canonical_payload_v1(),
        }
    validate_link_v1(owner, reservation_id, link)
    return link


def inspect_submit_context_locked_v1(owner, reservation_id, envelope, identity):
    """Read the original submit predicates without advancing either barrier."""
    if owner._store is None:
        raise ValueError("EXECUTION_LINK_DURABLE_ADMITTED_OWNER_REQUIRED")
    link = _validated_submit_link_v1(owner, reservation_id, identity)
    assert_envelope_unmodified_v1(envelope)
    if link["envelope"] != envelope.to_runtime_json_v1():
        raise ValueError("PORTFOLIO_EXECUTION_ENVELOPE_MISMATCH")
    return {
        "root": str(owner._store.root),
        "account": owner._account_identity,
        "reservation_id": reservation_id,
        "envelope_digest": envelope.envelope_digest,
        "execution_identity_digest": identity.identity_digest(),
        "scope": "ORIGINAL_COMMITTED_PLAN_CONTEXT_ONLY",
        **(
            {
                "plan_origin_digest": link["plan_origin"]["digest"],
                "order_environment": link["plan_origin"]["venue_plan"]["environment"],
            }
            if "plan_origin" in link
            else {}
        ),
    }


def mark_submit_locked_v1(owner, reservation_id, identity, *, external_effect_permit=None):
    link = _validated_submit_link_v1(owner, reservation_id, identity, external_effect_permit)
    owner._execution_links[reservation_id] = detached(link)
    owner._persist_locked()
    return detached(link)


def _original_never_submitted_v1(link, identity):
    """Read only the transport root pinned in the original V2 submit revision.

    Missing/legacy/uncertain evidence cannot become a positive local outcome.
    This does not replace current exchange, pending or position admission.
    """
    from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_durable_consume_v1 import (
        load_external_effect_durable_consume_v1,
        DURABLE_STATE_ABORTED_BEFORE_TRANSPORT,
    )

    if (
        type(identity) is not PortfolioExecutionReconciliationIdentityV2
        or "transport_store_root" not in link
    ):
        return None
    root = link["transport_store_root"]
    try:
        loaded = load_external_effect_durable_consume_v1(store_root=root)
        record = loaded["record"]
        if not (
            loaded["durable_consumed"] is True
            and record["durable_state"] == DURABLE_STATE_ABORTED_BEFORE_TRANSPORT
            and record["execution_identity"] == identity.to_dict()
            and record["execution_identity_digest"] == identity.identity_digest()
            and record["permit_id"] == link["external_effect_permit"]["permit_id"]
            and record["authority_ref"] == link["external_effect_permit"]["authority_ref"]
            and record["envelope_id"] == link["envelope"]["envelope_id"]
            and record["envelope_digest"] == link["envelope"]["envelope_digest"]
            and record["transport_attempt"]["phase"] == "ABORTED"
        ):
            return None
        return {
            "store_root": root,
            "record_digest": sha256(json.dumps(record, sort_keys=True).encode()).hexdigest(),
            "record": detached(record),
        }
    except (ValueError, RuntimeError, OSError, KeyError, TypeError):
        return None


def reconcile_locked_v1(owner, reservation_id, *, snapshot, observed, account, now_unix):
    """Resolve evidence while fenced; capital admission is a separate fresh gate."""
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import ReservationStateV1
    from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
        PortfolioTruthSnapshotV1,
    )

    if owner._closed_owner or owner._storage_failed or owner._store is None:
        raise ValueError("EXECUTION_RECONCILIATION_WRITER_UNAVAILABLE")
    link = owner._execution_links.get(reservation_id)
    if link is None or link["phase"] != "SUBMIT_MAY_HAVE_OCCURRED":
        raise ValueError("EXECUTION_RECONCILIATION_SUBMIT_UNPROVEN")
    validate_link_v1(owner, reservation_id, link)
    identity = parse_exchange_reconciliation_identity_v1(link["identity"])
    if account != owner._account_identity or not isinstance(observed, PortfolioTruthSnapshotV1):
        raise ValueError("EXECUTION_RECONCILIATION_ACCOUNT_UNPROVEN")
    if (
        any((observed.missing, observed.stale, observed.duplicate, observed.writer_conflict))
        or observed.event_time_unix is None
        or observed.max_age_seconds is None
        or not 0 <= now_unix - observed.event_time_unix <= min(observed.max_age_seconds, 5)
    ):
        raise ValueError("EXECUTION_RECONCILIATION_FRESH_POSITION_REQUIRED")
    for item in snapshot.evidence_items:
        try:
            acquired = datetime.fromisoformat(item.received_at.replace("Z", "+00:00"))
            if acquired.tzinfo is None or not 0 <= now_unix - acquired.timestamp() <= 5:
                raise ValueError("age")
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError("EXECUTION_RECONCILIATION_FRESH_ORDER_REQUIRED") from exc
    local_evidence = _original_never_submitted_v1(link, identity)
    local_outcome = (
        LocalSubmitOutcome.NOT_SUBMITTED
        if local_evidence is not None
        else LocalSubmitOutcome.TRANSPORT_UNKNOWN
    )
    decision = adjudicate_full_core_exchange_reconciliation_v1(
        identity=identity,
        snapshot=snapshot,
        local_submit_outcome=local_outcome,
        proven_never_submitted=local_evidence is not None,
    )
    positions = [p for p in observed.positions if p.instrument_id == identity.instrument_id]
    quantity = positions[0].signed_quantity if len(positions) == 1 else Decimal(0)
    known = {row["bound"]["instrument_id"] for row in owner._lane_bindings.values()}
    if len(positions) > 1 or any(
        p.instrument_id not in known or not p.signed_quantity.is_finite()
        for p in observed.positions
    ):
        raise ValueError("EXECUTION_RECONCILIATION_POSITION_AMBIGUOUS")
    reasons = list(decision.reasons)
    matched = decision.outcome != OUTCOME_HALTED_UNRESOLVED
    release = False
    if decision.outcome != OUTCOME_HALTED_UNRESOLVED:
        filled = Decimal(decision.cumulative_filled_qty)
        expected = filled if identity.selected_side.upper() in {"LONG", "ENTER_LONG"} else -filled
        if quantity != expected:
            reasons.append("EXECUTION_FILL_POSITION_CONTRADICTION")
            matched = False
        else:
            release = (
                decision.outcome in {OUTCOME_CONFIRMED_CANCELED, OUTCOME_CONFIRMED_REJECTED}
                and filled == 0
            )
    if release:
        pending = snapshot.pending_orders_observation
        if not (
            isinstance(pending, dict)
            and pending.get("identity_digest") == identity.identity_digest()
            and pending.get("freshness_proven") is True
            and pending.get("response") == {"code": "0", "data": []}
        ):
            # Extra venue metadata is harmless, but missing/unknown rows are not.
            response = pending.get("response") if isinstance(pending, dict) else None
            release = bool(
                isinstance(response, dict)
                and response.get("code") == "0"
                and response.get("data") == []
                and pending.get("freshness_proven") is True
                and pending.get("identity_digest") == identity.identity_digest()
            )
            if not release:
                reasons.append("EXECUTION_PENDING_CUSTODY_UNPROVEN")
                matched = False
    evidence = {
        "local_submit_outcome": local_outcome.value,
        "local_submit_evidence": local_evidence,
        "identity_digest": identity.identity_digest(),
        "snapshot_digest": sha256(
            json.dumps(snapshot.to_dict(), sort_keys=True).encode()
        ).hexdigest(),
        "portfolio_digest": observed.digest(),
        "decision": decision.to_dict(),
        "matched": matched,
        "reason_codes": reasons,
        "reservation_released": release,
    }
    if release:
        key = owner._by_id[reservation_id]
        current = owner._by_key[key]
        if current.counts_against_budget:
            owner._by_key[key] = replace(
                current,
                state=ReservationStateV1.RELEASED,
                transition_trace=current.transition_trace + ("RELEASED",),
                terminal_reason="RECONCILED_ENTRY_NO_FILL",
            )
    owner._execution_links[reservation_id] = detached({**link, "reconciliation": evidence})
    owner._persist_locked()
    return detached(evidence)


def read_persisted_execution_reconciliation_v1(owner, reservation_id, *, revision_ref=None):
    """Read an owned reconciliation revision that still agrees with the current link."""
    with owner._lock:
        store = owner._store
        if owner._closed_owner or owner._storage_failed or store is None:
            raise ValueError("EXECUTION_RECONCILIATION_READBACK_UNAVAILABLE")
        sequence, checksum = (store.sequence, store.head) if revision_ref is None else revision_ref
        revision = store.read_revision_v1(sequence, checksum)
        link = revision["state"].get("execution_links", {}).get(reservation_id)
        if (
            not link
            or link != owner._execution_links.get(reservation_id)
            or link["phase"] != "SUBMIT_MAY_HAVE_OCCURRED"
            or link["reconciliation"] is None
        ):
            raise ValueError("EXECUTION_RECONCILIATION_READBACK_UNPROVEN")
        return revision["sequence"], revision["digest"], link
