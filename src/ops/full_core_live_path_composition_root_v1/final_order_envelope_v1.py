"""Immutable Full-Core final order envelope. Offline. No POST.

Binds submit-relevant parameters for later envelope-bound single-use
external-effect permits. Does not invent venue values. Does not submit.
STEP-29Q remains PLAN_ONLY; this object is the transformed execution
envelope, not a directly submittable CanonicalOrderIntent.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1

ENVELOPE_SCHEMA_VERSION = "full_core_final_order_envelope.v1"
ISSUED_FOR_EXACT_ACTION = "FULL_CORE_TRADE_ORDER_POST"
_SECRET_TOKENS = ("secret", "passphrase", "api_key", "apikey", "private_key")


class FullCoreFinalOrderEnvelopeError(RuntimeError):
    """Fail-closed envelope construction or identity violation."""


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _assert_no_secrets(payload: Mapping[str, Any]) -> None:
    blob = _canonical_json(payload).lower()
    for token in _SECRET_TOKENS:
        if token in blob:
            raise FullCoreFinalOrderEnvelopeError(f"SECRET_TOKEN_PRESENT:{token}")


def _require_text(value: Any, code: str) -> str:
    text = str(value or "").strip()
    if not text or text != str(value):
        raise FullCoreFinalOrderEnvelopeError(code)
    return text


@dataclass(frozen=True)
class FinalOrderEnvelopeV1:
    envelope_id: str
    envelope_digest: str
    instrument_id: str
    side: str
    order_type: str
    quantity: str
    quantity_unit: str
    price: str
    td_mode: str
    pos_side: str
    reduce_only: bool
    client_order_id: str
    path_kind: str
    venue_plan_clordid: str
    quantity_source: str
    side_source: str
    instrument_source: str
    admission_ref: str
    provenance_ref: str
    creation_epoch: str
    issued_for_exact_action: str = ISSUED_FOR_EXACT_ACTION
    schema_version: str = ENVELOPE_SCHEMA_VERSION

    def to_canonical_payload_v1(self) -> dict[str, Any]:
        return {
            "admission_ref": self.admission_ref,
            "client_order_id": self.client_order_id,
            "creation_epoch": self.creation_epoch,
            "instrument_id": self.instrument_id,
            "instrument_source": self.instrument_source,
            "issued_for_exact_action": self.issued_for_exact_action,
            "order_type": self.order_type,
            "path_kind": self.path_kind,
            "pos_side": self.pos_side,
            "price": self.price,
            "provenance_ref": self.provenance_ref,
            "quantity": self.quantity,
            "quantity_source": self.quantity_source,
            "quantity_unit": self.quantity_unit,
            "reduce_only": self.reduce_only is True,
            "schema_version": self.schema_version,
            "side": self.side,
            "side_source": self.side_source,
            "td_mode": self.td_mode,
            "venue_plan_clordid": self.venue_plan_clordid,
        }


def compute_final_order_envelope_digest_v1(payload: Mapping[str, Any]) -> str:
    _assert_no_secrets(payload)
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def build_final_order_envelope_v1(
    *,
    instrument_id: str,
    side: str,
    order_type: str,
    quantity: str,
    quantity_unit: str,
    td_mode: str,
    reduce_only: bool,
    client_order_id: str,
    path_kind: str,
    venue_plan_clordid: str,
    quantity_source: str,
    side_source: str,
    instrument_source: str,
    admission_ref: str,
    provenance_ref: str,
    creation_epoch: str,
    price: str = "",
    pos_side: str = "",
) -> FinalOrderEnvelopeV1:
    if reduce_only is not True and reduce_only is not False:
        raise FullCoreFinalOrderEnvelopeError("REDUCE_ONLY_MALFORMED")
    bound = {
        "admission_ref": _require_text(admission_ref, "ADMISSION_REF_MISSING"),
        "client_order_id": _require_text(client_order_id, "CLIENT_ORDER_ID_MISSING"),
        "creation_epoch": _require_text(creation_epoch, "CREATION_EPOCH_MISSING"),
        "instrument_id": _require_text(instrument_id, "INSTRUMENT_ID_MISSING"),
        "instrument_source": _require_text(instrument_source, "INSTRUMENT_SOURCE_MISSING"),
        "issued_for_exact_action": ISSUED_FOR_EXACT_ACTION,
        "order_type": _require_text(order_type, "ORDER_TYPE_MISSING"),
        "path_kind": _require_text(path_kind, "PATH_KIND_MISSING"),
        "pos_side": str(pos_side or ""),
        "price": str(price or ""),
        "provenance_ref": _require_text(provenance_ref, "PROVENANCE_REF_MISSING"),
        "quantity": _require_text(quantity, "QUANTITY_MISSING"),
        "quantity_source": _require_text(quantity_source, "QUANTITY_SOURCE_MISSING"),
        "quantity_unit": _require_text(quantity_unit, "QUANTITY_UNIT_MISSING"),
        "reduce_only": reduce_only is True,
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "side": _require_text(side, "SIDE_MISSING"),
        "side_source": _require_text(side_source, "SIDE_SOURCE_MISSING"),
        "td_mode": _require_text(td_mode, "TD_MODE_MISSING"),
        "venue_plan_clordid": _require_text(venue_plan_clordid, "VENUE_PLAN_CLORDID_MISSING"),
    }
    if bound["client_order_id"] != bound["venue_plan_clordid"]:
        raise FullCoreFinalOrderEnvelopeError("CLIENT_ORDER_ID_PLAN_MISMATCH")
    if bound["order_type"] == "limit" and not str(bound["price"]).strip():
        raise FullCoreFinalOrderEnvelopeError("LIMIT_ORDER_PX_REQUIRED")
    digest = compute_final_order_envelope_digest_v1(bound)
    envelope_id = f"env-{digest[:32]}"
    envelope = FinalOrderEnvelopeV1(
        envelope_id=envelope_id,
        envelope_digest=digest,
        instrument_id=str(bound["instrument_id"]),
        side=str(bound["side"]),
        order_type=str(bound["order_type"]),
        quantity=str(bound["quantity"]),
        quantity_unit=str(bound["quantity_unit"]),
        price=str(bound["price"]),
        td_mode=str(bound["td_mode"]),
        pos_side=str(bound["pos_side"]),
        reduce_only=bound["reduce_only"] is True,
        client_order_id=str(bound["client_order_id"]),
        path_kind=str(bound["path_kind"]),
        venue_plan_clordid=str(bound["venue_plan_clordid"]),
        quantity_source=str(bound["quantity_source"]),
        side_source=str(bound["side_source"]),
        instrument_source=str(bound["instrument_source"]),
        admission_ref=str(bound["admission_ref"]),
        provenance_ref=str(bound["provenance_ref"]),
        creation_epoch=str(bound["creation_epoch"]),
    )
    if compute_final_order_envelope_digest_v1(envelope.to_canonical_payload_v1()) != digest:
        raise FullCoreFinalOrderEnvelopeError("ENVELOPE_DIGEST_DRIFT")
    return envelope


def bind_final_order_envelope_from_venue_plan_v1(
    plan: VenuePlanCandidateV1,
    *,
    admission_ref: str,
    provenance_ref: str,
    creation_epoch: str,
    quantity_unit: str = "CONTRACTS",
    price: str = "",
    pos_side: str = "",
) -> FinalOrderEnvelopeV1:
    if plan is None or not isinstance(plan, VenuePlanCandidateV1):
        raise FullCoreFinalOrderEnvelopeError("VENUE_PLAN_MISSING")
    payload = plan.venue_native_payload if isinstance(plan.venue_native_payload, Mapping) else {}
    bound_price = str(price or payload.get("px") or "")
    bound_pos_side = str(pos_side or payload.get("posSide") or "")
    return build_final_order_envelope_v1(
        instrument_id=plan.instrument_id,
        side=plan.side,
        order_type=plan.order_type,
        quantity=plan.quantity,
        quantity_unit=quantity_unit,
        td_mode=plan.td_mode,
        reduce_only=bool(plan.reduce_only),
        client_order_id=plan.clordid,
        path_kind=plan.path_kind,
        venue_plan_clordid=plan.clordid,
        quantity_source=plan.quantity_source,
        side_source=plan.side_source,
        instrument_source=plan.instrument_source,
        admission_ref=admission_ref,
        provenance_ref=provenance_ref,
        creation_epoch=creation_epoch,
        price=bound_price,
        pos_side=bound_pos_side,
    )


def assert_envelope_unmodified_v1(
    envelope: FinalOrderEnvelopeV1,
    *,
    expected_id: Optional[str] = None,
    expected_digest: Optional[str] = None,
) -> None:
    if envelope is None or not isinstance(envelope, FinalOrderEnvelopeV1):
        raise FullCoreFinalOrderEnvelopeError("ENVELOPE_MISSING")
    digest = compute_final_order_envelope_digest_v1(envelope.to_canonical_payload_v1())
    if digest != envelope.envelope_digest:
        raise FullCoreFinalOrderEnvelopeError("ENVELOPE_DIGEST_MISMATCH")
    if expected_id is not None and envelope.envelope_id != expected_id:
        raise FullCoreFinalOrderEnvelopeError("ENVELOPE_ID_MISMATCH")
    if expected_digest is not None and envelope.envelope_digest != expected_digest:
        raise FullCoreFinalOrderEnvelopeError("ENVELOPE_DIGEST_MISMATCH")
    expected_id_from_digest = f"env-{digest[:32]}"
    if envelope.envelope_id != expected_id_from_digest:
        raise FullCoreFinalOrderEnvelopeError("ENVELOPE_ID_DIGEST_BINDING_MISMATCH")
