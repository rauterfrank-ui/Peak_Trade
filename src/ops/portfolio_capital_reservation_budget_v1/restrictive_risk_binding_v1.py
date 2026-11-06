"""Immutable risk evidence within the original sizing/reservation transaction."""

from dataclasses import dataclass
from decimal import Decimal
import json

from src.risk.decision_bound_model_adapters_v1 import (
    OfflineRiskRequestV1,
    encoded,
    evaluate_offline_risk_v1,
    number,
)
from .durable_store_v1 import canonical, digest


@dataclass(frozen=True)
class RiskAdmissionBindingV1:
    request_json: str
    owner_snapshot_json: str
    result_json: str
    original_sizing_request_digest: str
    final_quantity: str

    @property
    def request(self):
        from .sizing_binding_v1 import _decode

        return _decode(OfflineRiskRequestV1, json.loads(self.request_json))

    @property
    def owner_snapshot_digest(self):
        return json.loads(self.owner_snapshot_json)["digest"]

    def validate_v1(self, *, amount, decision_id):
        request, snapshot, result = (
            self.request,
            json.loads(self.owner_snapshot_json),
            json.loads(self.result_json),
        )
        if snapshot["digest"] != digest({k: v for k, v in snapshot.items() if k != "digest"}):
            raise ValueError("RISK_OWNER_SNAPSHOT_INTEGRITY_INVALID")
        quantity = number(Decimal(self.final_quantity), positive=True)
        actual = evaluate_offline_risk_v1(request, quantity=quantity, owner_snapshot=snapshot)
        if (
            actual != result
            or result["status"] != "PASS"
            or Decimal(result["notional_capital"]) != amount
            or request.decision_id != decision_id
        ):
            raise ValueError("RISK_RESERVATION_RESULT_BINDING_MISMATCH")
        if len(self.original_sizing_request_digest) != 64 or any(
            c not in "0123456789abcdef" for c in self.original_sizing_request_digest
        ):
            raise ValueError("RISK_ORIGINAL_SIZING_REQUEST_UNBOUND")

    def to_dict_v1(self):
        return {
            "schema": "reservation_risk_admission.v1",
            "request": json.loads(self.request_json),
            "owner_snapshot": json.loads(self.owner_snapshot_json),
            "result": json.loads(self.result_json),
            "original_sizing_request_digest": self.original_sizing_request_digest,
            "final_quantity": self.final_quantity,
        }

    @classmethod
    def from_dict_v1(cls, payload):
        if (
            not isinstance(payload, dict)
            or set(payload)
            != {
                "schema",
                "request",
                "owner_snapshot",
                "result",
                "original_sizing_request_digest",
                "final_quantity",
            }
            or payload["schema"] != "reservation_risk_admission.v1"
        ):
            raise ValueError("RISK_BINDING_SCHEMA_INVALID")
        return cls(
            canonical(payload["request"]),
            canonical(payload["owner_snapshot"]),
            canonical(payload["result"]),
            payload["original_sizing_request_digest"],
            payload["final_quantity"],
        )

    def validate_replay_v1(self, request, sizing_input):
        from .sizing_binding_v1 import request_digest_v1

        if (
            type(request) is not OfflineRiskRequestV1
            or canonical(encoded(request)) != self.request_json
            or request_digest_v1(sizing_input) != self.original_sizing_request_digest
        ):
            raise ValueError("RISK_REPLAY_CONTEXT_CHANGED_OR_MISSING")

    def validate_envelope_v1(self, envelope):
        request = self.request
        if (
            envelope.instrument_id != request.native_id
            or envelope.side != ("buy" if request.side == "LONG" else "sell")
            or Decimal(envelope.quantity) != Decimal(self.final_quantity)
            or envelope.quantity_unit.upper() not in {"CONTRACT", "CONTRACTS"}
            or envelope.order_type != request.order_type
            or envelope.reduce_only is not False
            or (Decimal(envelope.price) if envelope.price else None) != request.limit_price_quote
        ):
            raise ValueError("RISK_FINAL_ENVELOPE_BINDING_MISMATCH")


def bind_restrictive_risk_v1(
    *, request, owner_snapshot, original_input, applied_input, decision, slot_id, cycle_id, account
):
    from .sizing_binding_v1 import request_digest_v1

    if type(request) is not OfflineRiskRequestV1:
        raise ValueError("RISK_TYPED_COMPLETE_REQUEST_REQUIRED")
    if (
        request.decision_id,
        request.canonical_id,
        request.slot_id,
        request.cycle_id,
        request.side,
        request.data.account,
    ) != (
        original_input.decision_id,
        original_input.instrument_id,
        str(slot_id),
        cycle_id,
        original_input.selected_side.upper(),
        account,
    ):
        raise ValueError("RISK_SIZING_DECISION_OR_ACCOUNT_MISMATCH")
    instrument = next(
        (i for i in request.data.instruments if i.canonical_id == request.canonical_id), None
    )
    if (
        instrument is None
        or instrument.contract_multiplier != applied_input.instrument.contract_multiplier
        or instrument.price * instrument.quote_to_capital != applied_input.reference_price
    ):
        raise ValueError("RISK_SIZING_PRICE_FX_OR_CONTRACT_MISMATCH")
    result = evaluate_offline_risk_v1(
        request, quantity=decision.final_quantity, owner_snapshot=owner_snapshot
    )
    if result["status"] != "PASS":
        raise ValueError(result["reason_codes"][0])
    binding = RiskAdmissionBindingV1(
        canonical(encoded(request)),
        canonical(owner_snapshot),
        canonical(result),
        request_digest_v1(original_input),
        str(decision.final_quantity),
    )
    binding.validate_v1(
        amount=decision.canonical_position_sizing.resulting_notional,
        decision_id=decision.canonical_position_sizing.decision_id,
    )
    return binding
