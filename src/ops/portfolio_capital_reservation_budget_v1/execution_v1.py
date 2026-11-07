"""Execution linkage inside the existing budget owner's durable transaction.

No second ledger, venue calls, permits, capital calculation or submit retries.
An uncertain submission remains an obligation until exact exchange evidence.
"""

from dataclasses import replace
from decimal import Decimal
from datetime import datetime
from hashlib import sha256
import json

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
    LocalSubmitOutcome,
    adjudicate_full_core_exchange_reconciliation_v1,
    OUTCOME_HALTED_UNRESOLVED,
    OUTCOME_CONFIRMED_CANCELED,
    OUTCOME_CONFIRMED_REJECTED,
)


def detached(value):
    return json.loads(json.dumps(value, allow_nan=False))


def validate_link_v1(owner, reservation_id, link):
    if set(link) - {"external_effect_permit"} != {
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
    if link["phase"] == "PLAN_BOUND":
        if (
            link["identity"] is not None
            or link["reconciliation"] is not None
            or "external_effect_permit" in link
        ):
            raise ValueError("EXECUTION_PLAN_STATE_INVALID")
        return
    if link["phase"] != "SUBMIT_MAY_HAVE_OCCURRED":
        raise ValueError("EXECUTION_LINK_PHASE_INVALID")
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
    raw = dict(link["identity"])
    raw.pop("contract_id", None)
    identity = FullCoreExchangeReconciliationIdentityV1(**raw)
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
        and identity.execution_environment in {"LIVE", "SHADOW", "PAPER", "TESTNET"}
        and all(
            isinstance(v, str) and v and v == v.strip()
            for k, v in raw.items()
            if k not in {"exchange_ord_id", "order_price"}
        )
    ):
        raise ValueError("EXECUTION_IDENTITY_MISMATCH")


def bind_plan_locked_v1(owner, reservation_id, envelope):
    if owner._store is None or owner._require_locked(reservation_id) is None:
        raise ValueError("EXECUTION_LINK_DURABLE_ADMITTED_OWNER_REQUIRED")
    link = {
        "envelope": envelope.to_runtime_json_v1(),
        "identity": None,
        "phase": "PLAN_BOUND",
        "reconciliation": None,
    }
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
    }


def mark_submit_locked_v1(owner, reservation_id, identity, *, external_effect_permit=None):
    link = _validated_submit_link_v1(owner, reservation_id, identity, external_effect_permit)
    owner._execution_links[reservation_id] = detached(link)
    owner._persist_locked()
    return detached(link)


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
    raw = dict(link["identity"])
    raw.pop("contract_id", None)
    identity = FullCoreExchangeReconciliationIdentityV1(**raw)
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
    decision = adjudicate_full_core_exchange_reconciliation_v1(
        identity=identity,
        snapshot=snapshot,
        local_submit_outcome=LocalSubmitOutcome.TRANSPORT_UNKNOWN,
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
